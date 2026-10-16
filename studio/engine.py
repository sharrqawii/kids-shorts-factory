import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time

from .config import ROOT, wangp_settings
from .providers import FreeGpuProvider


def verify_video(path):
    probe = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)],
                           capture_output=True, check=True, timeout=30)
    data = json.loads(probe.stdout)
    video = next(s for s in data['streams'] if s['codec_type'] == 'video')
    duration = float(data['format']['duration'])
    if not 0 < duration < 120 or min(video['width'], video['height']) < 64:
        raise ValueError('Invalid video dimensions or duration')
    subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(path), '-f', 'null', '-'],
                   capture_output=True, check=True, timeout=180)
    return {'width': video['width'], 'height': video['height'], 'duration': duration,
            'codec': video['codec_name'], 'decode_passed': True,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def stop_process(process):
    if process.poll() is not None:
        return
    if os.name == 'nt':
        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True, timeout=20)
    else:
        import signal
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
    process.wait(timeout=20)


class Worker:
    def __init__(self, config, store):
        self.config, self.store = config, store
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.loop, daemon=True)

    def loop(self):
        while not self.stop.is_set():
            job = self.store.claim()
            if job:
                self.execute(job)
            else:
                self.stop.wait(.4)

    def execute(self, job):
        job_id, spec = job['id'], job['spec']
        out = self.config.data / 'jobs' / job_id
        out.mkdir(parents=True, exist_ok=True)

        def cancelled():
            return self.stop.is_set() or self.store.get(job_id)['state'] == 'cancelling'

        def report(progress, phase):
            # Only known phase names leave local logs. Never expose provider paths or credentials.
            known = {'loading_model', 'encoding_text', 'inference', 'decoding', 'Preparing', 'Rendering Blender', 'Verifying video'}
            self.store.update(job_id, progress=max(0, min(99, progress)), phase=phase if phase in known else 'Generating')

        try:
            if cancelled():
                raise InterruptedError()
            if spec['engine'] == 'blender':
                if not self.config.blender_python or self.config.gpu_only:
                    raise ValueError('Blender is not configured. Set BLENDER_PYTHON to the existing CPU environment.')
                report(0, 'Rendering Blender')
                cmd = [self.config.blender_python, '-m', 'factory.render', '--mode', spec['quality'], '--out', str(out), '--budget-seconds', str(self.config.timeout)]
                self.process(cmd, out, cancelled, report)
                video = out / 'pip-and-the-giant-strawberry.mp4'
            else:
                reference = self.config.data / 'references' / (spec['reference'] + '.png') if spec['reference'] else None
                if reference and not reference.is_file():
                    raise ValueError('Reference image is missing. Upload it again.')
                if spec['provider'] == 'free-cloud':
                    provider = FreeGpuProvider(self.config.remote_url, self.config.remote_token, self.config.remote_free)
                    video = provider.run(spec, reference, out / 'video.mp4', report, cancelled, self.config.timeout)
                else:
                    if not self.config.wangp_root or not self.config.wangp_python:
                        raise ValueError('WanGP is not configured. Connect a separate WanGP GPU environment. No engine fallback was used.')
                    request = out / 'request.json'
                    request.write_text(json.dumps(wangp_settings(spec, reference)), encoding='utf-8')
                    cmd = [self.config.wangp_python, '-u', str(ROOT / 'studio/wangp_worker.py'), '--root', self.config.wangp_root,
                           '--request', str(request), '--out', str(out)]
                    self.process(cmd, out, cancelled, report)
                    video = Path(json.loads((out / 'result.json').read_text(encoding='utf-8'))['video']).resolve()
                    if not video.is_relative_to(out):
                        raise RuntimeError('WanGP returned an output outside this job directory.')
            if cancelled():
                raise InterruptedError()
            report(99, 'Verifying video')
            verification = verify_video(video)
            if cancelled():
                raise InterruptedError()
            final = out / 'video.mp4'
            if video != final:
                shutil.copy2(video, final)
            self.store.update(job_id, state='succeeded', progress=100, phase='Verified', output=str(final), verification=verification)
        except InterruptedError:
            self.store.update(job_id, state='cancelled', phase='Cancelled')
        except Exception as error:
            with (out / 'controller.log').open('a', encoding='utf-8') as log:
                log.write(type(error).__name__ + ': ' + str(error) + '\n')
            # Configuration errors are deliberately authored strings, never external process stderr.
            message = str(error) if isinstance(error, ValueError) else 'Generation failed. See the private job logs for details. No engine fallback was used.'
            self.store.update(job_id, state='failed', phase='Needs attention', error=message)

    def process(self, cmd, out, cancelled, report):
        options = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {'start_new_session': True}
        with (out / 'worker.log').open('wb') as log:
            process = subprocess.Popen(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, **options)
            deadline = time.monotonic() + self.config.timeout
            cancel_started = None
            position = 0
            pending = ''
            try:
                while process.poll() is None:
                    if cancelled():
                        (out / 'cancel').touch()
                        cancel_started = cancel_started or time.monotonic()
                        if time.monotonic() - cancel_started > 5:
                            raise InterruptedError()
                    if time.monotonic() > deadline:
                        raise TimeoutError('Worker exceeded runtime limit')
                    events = out / 'events.jsonl'
                    if events.exists():
                        with events.open(encoding='utf-8') as stream:
                            stream.seek(position)
                            pending += stream.read()
                            position = stream.tell()
                        lines = pending.split('\n')
                        pending = lines.pop()
                        for line in lines:
                            event = json.loads(line)
                            report(event['progress'], event['phase'])
                    time.sleep(.25)
                if cancelled():
                    raise InterruptedError()
                if process.returncode:
                    raise RuntimeError('Worker exited with an error')
            finally:
                stop_process(process)
