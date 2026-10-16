"""Single-user local browser app, or token-authenticated GPU bridge behind HTTPS."""
import argparse
import base64
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import mimetypes
import re
import socket
from pathlib import Path
import uuid
from urllib.parse import urlsplit

from .config import Config, MODELS, ROOT, validate_job
from .engine import Worker
from .store import Store

MAX_BODY = 12 * 1024 * 1024


def save_reference(config, encoded):
    from PIL import Image, ImageOps
    if not isinstance(encoded, str) or len(encoded) > MAX_BODY:
        raise ValueError('Upload a PNG or JPEG under 8 MB.')
    raw = base64.b64decode(encoded, validate=True)
    if len(raw) > 8 * 1024 * 1024:
        raise ValueError('Image is too large. Maximum 8 MB.')
    with Image.open(io.BytesIO(raw)) as image:
        if image.format not in ('PNG', 'JPEG') or image.width * image.height > 16_000_000:
            raise ValueError('Use PNG or JPEG, up to 16 megapixels.')
        image.load()
        # Normalize and discard EXIF/location metadata and embedded content.
        clean = ImageOps.exif_transpose(image).convert('RGB')
        clean.thumbnail((2048, 2048))
        result = Image.new('RGB', clean.size)
        result.paste(clean)
    identifier = uuid.uuid4().hex
    folder = config.data / 'references'
    folder.mkdir(exist_ok=True)
    result.save(folder / (identifier + '.png'))
    return {'id': identifier, 'width': result.width, 'height': result.height}


def make_server(config, port=8765, host='127.0.0.1', start_worker=True):
    store = Store(config.data / 'jobs.sqlite3')
    worker = Worker(config, store)

    class Handler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def log_message(self, *_):
            pass  # No prompts, tokens, paths, or query strings in access logs.

        def authorized(self):
            if config.gpu_only:
                expected = 'Bearer ' + config.bridge_token
                return bool(config.bridge_token) and hmac.compare_digest(self.headers.get('Authorization', ''), expected)
            hostname = urlsplit('http://' + self.headers.get('Host', '')).hostname
            if hostname not in ('localhost', '127.0.0.1', '::1'):
                return False
            origin = self.headers.get('Origin')
            if origin and origin != 'http://' + self.headers.get('Host'):
                return False
            return self.headers.get('Sec-Fetch-Site', '') not in ('cross-site',)

        def send_headers(self, status, mime, size, extra=None):
            self.send_response(status)
            for key, value in {'Content-Type': mime, 'Content-Length': str(size), 'Cache-Control': 'no-store',
                               'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer',
                               'Content-Security-Policy': "default-src 'self'; img-src 'self' blob:; media-src 'self' blob:; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'",
                               **(extra or {})}.items():
                self.send_header(key, value)
            self.end_headers()

        def respond(self, status, value):
            raw = json.dumps(value).encode()
            self.send_headers(status, 'application/json', len(raw))
            self.wfile.write(raw)

        def file(self, path, attachment=False):
            if not path or not path.is_file():
                return self.respond(404, {'error': 'Output not found.'})
            size = path.stat().st_size
            start, end, status = 0, size - 1, 200
            extra = {'Accept-Ranges': 'bytes'}
            request_range = self.headers.get('Range')
            if request_range:
                match = re.fullmatch(r'bytes=(\d+)-(\d*)', request_range)
                if not match:
                    self.send_headers(416, 'application/octet-stream', 0, {'Content-Range': f'bytes */{size}'})
                    return
                start, end = int(match[1]), int(match[2]) if match[2] else size - 1
                if start >= size or end < start:
                    self.send_headers(416, 'application/octet-stream', 0, {'Content-Range': f'bytes */{size}'})
                    return
                end, status = min(end, size - 1), 206
                extra['Content-Range'] = f'bytes {start}-{end}/{size}'
            if attachment:
                extra['Content-Disposition'] = 'attachment; filename="studio-video.mp4"'
            self.send_headers(status, mimetypes.guess_type(path.name)[0] or 'application/octet-stream', end - start + 1, extra)
            try:
                with path.open('rb') as stream:
                    stream.seek(start)
                    remaining = end - start + 1
                    while remaining > 0:
                        chunk = stream.read(min(1024 * 1024, remaining))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        remaining -= len(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_GET(self):
            if not self.authorized():
                return self.respond(403, {'error': 'Access denied.'})
            route = urlsplit(self.path).path
            if route == '/api/capabilities':
                capabilities = config.capabilities()
                capabilities['gpu_generation_verified'] = any(j['state'] == 'succeeded' and j['spec']['engine'] == 'wangp'
                    and j['verification'].get('decode_passed') for j in store.list())
                return self.respond(200, dict(capabilities, models=MODELS, gpu_bridge=config.gpu_only))
            if route == '/api/jobs':
                return self.respond(200, store.list())
            match = re.fullmatch(r'/api/jobs/([a-f0-9]{32})(/video)?', route)
            if match:
                job = store.get(match[1])
                if not job:
                    return self.respond(404, {'error': 'Job not found.'})
                if match[2]:
                    path = store.output(match[1])
                    return self.file(Path(path) if path else None, 'download=1' in self.path)
                return self.respond(200, job)
            if not config.gpu_only:
                if route == '/api/sample':
                    return self.file(config.sample, 'download=1' in self.path)
                static = {'/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css', '/pip.jpg': 'pip.jpg'}
                if route in static:
                    return self.file(ROOT / 'studio/web' / static[route])
            return self.respond(404, {'error': 'Not found.'})

        def do_POST(self):
            if not self.authorized():
                self.close_connection = True
                return self.respond(403, {'error': 'Access denied.'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if length <= 0 or length > MAX_BODY or self.headers.get_content_type() != 'application/json':
                    self.close_connection = True
                    return self.respond(413, {'error': 'Use JSON with a maximum payload of 12 MB.'})
                payload = json.loads(self.rfile.read(length))
                route = urlsplit(self.path).path
                if route == '/api/references':
                    return self.respond(201, save_reference(config, payload['image']))
                if route == '/api/jobs':
                    spec = validate_job(payload)
                    if config.gpu_only and (spec['engine'] != 'wangp' or spec['provider'] != 'local'):
                        raise ValueError('GPU bridges only accept local WanGP jobs.')
                    if sum(j['state'] in ('queued', 'running', 'cancelling') for j in store.list()) >= 10:
                        raise ValueError('Queue is full. Wait for a job to finish.')
                    return self.respond(201, store.create(spec))
                match = re.fullmatch(r'/api/jobs/([a-f0-9]{32})/cancel', route)
                if match:
                    job = store.cancel(match[1])
                    return self.respond(200 if job else 404, job or {'error': 'Job not found.'})
                return self.respond(404, {'error': 'Not found.'})
            except (ValueError, KeyError, TypeError):
                return self.respond(400, {'error': 'Invalid request. Check the model, prompt, image and generation settings.'})
            except Exception:
                return self.respond(500, {'error': 'Studio could not process this request.'})

    class Server(ThreadingHTTPServer):
        daemon_threads = True

        def get_request(self):
            connection, address = super().get_request()
            connection.settimeout(30)
            return connection, address

        def server_close(self):
            worker.stop.set()
            if worker.thread.is_alive():
                worker.thread.join(timeout=30)
            super().server_close()

    if host not in ('localhost', '127.0.0.1', '::1') and (not config.gpu_only or len(config.bridge_token) < 32):
        raise ValueError('Remote binding requires GPU bridge mode and a token of at least 32 characters.')
    server = Server((host, port), Handler)
    server.store, server.worker = store, worker
    if start_worker:
        worker.thread.start()
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--data', type=Path)
    parser.add_argument('--gpu-bridge', action='store_true')
    args = parser.parse_args()
    config = Config(args.data)
    config.gpu_only = args.gpu_bridge
    with make_server(config, args.port, args.host) as server:
        print(f'Pip Studio: http://{args.host}:{server.server_port}', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
