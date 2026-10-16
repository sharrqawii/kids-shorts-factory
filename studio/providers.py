"""Adapter for an EXISTING free GPU bridge. No provisioning or billing API exists here."""
import base64
import json
from pathlib import Path
import time
import urllib.request
from urllib.parse import urlsplit


class FreeGpuProvider:
    def __init__(self, url, token, confirmed_free=False):
        parsed = urlsplit(url)
        if not confirmed_free:
            raise ValueError('No free GPU endpoint has been confirmed. Paid provisioning is disabled.')
        if not token or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError('A configured endpoint and private bearer token are required.')
        if parsed.scheme != 'https' and not (parsed.scheme == 'http' and parsed.hostname in ('127.0.0.1', 'localhost', '::1')):
            raise ValueError('Remote GPU connections require HTTPS.')
        self.url, self.token = url.rstrip('/'), token
        # Never forward credentials across redirects.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
        self.opener = urllib.request.build_opener(NoRedirect)

    def request(self, route, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(self.url + route, data=data, headers={
            'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json'})
        with self.opener.open(req, timeout=30) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise RuntimeError('GPU endpoint returned an oversized response.')
        return json.loads(raw)

    def run(self, spec, reference, output, report, cancelled, timeout):
        health = self.request('/api/capabilities')
        if not health.get('gpu_bridge') or health.get('budget') != 0 or not health.get('wangp_local'):
            raise RuntimeError('The free GPU bridge is unavailable or incompatible.')
        payload = dict(spec, provider='local')
        if reference:
            uploaded = self.request('/api/references', {'image': base64.b64encode(Path(reference).read_bytes()).decode()})
            payload['reference'] = uploaded['id']
        remote = self.request('/api/jobs', payload)
        job_id = remote['id']
        if not isinstance(job_id, str) or len(job_id) != 32 or any(c not in '0123456789abcdef' for c in job_id):
            raise RuntimeError('GPU endpoint returned an invalid job ID.')
        deadline = time.monotonic() + timeout
        complete = False
        try:
            while time.monotonic() < deadline:
                if cancelled():
                    raise InterruptedError('Cancelled')
                status = self.request('/api/jobs/' + job_id)
                report(int(status.get('progress', 0)), str(status.get('phase', 'GPU job')))
                if status['state'] == 'succeeded':
                    req = urllib.request.Request(self.url + '/api/jobs/' + job_id + '/video',
                                                 headers={'Authorization': 'Bearer ' + self.token})
                    with self.opener.open(req, timeout=30) as response, output.open('wb') as stream:
                        total = 0
                        while chunk := response.read(1024 * 1024):
                            total += len(chunk)
                            if cancelled():
                                raise InterruptedError('Cancelled')
                            if total > 256 * 1024 * 1024 or time.monotonic() > deadline:
                                raise RuntimeError('GPU output exceeded the download limit.')
                            stream.write(chunk)
                    complete = True
                    return output
                if status['state'] in ('failed', 'cancelled', 'interrupted'):
                    raise RuntimeError('Remote WanGP job failed. Check the GPU bridge history.')
                time.sleep(.5)
            raise TimeoutError('The GPU job exceeded its time limit.')
        finally:
            if not complete:
                try:
                    self.request('/api/jobs/' + job_id + '/cancel', {})
                except Exception:
                    pass
