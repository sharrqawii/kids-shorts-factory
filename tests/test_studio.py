import base64
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import urllib.error
import urllib.request

from PIL import Image
from studio.config import Config, validate_job, wangp_settings
from studio.engine import Worker, verify_video
from studio.providers import FreeGpuProvider
from studio.server import make_server, save_reference
from studio.store import Store
from studio.wangp_worker import generate


def spec(**changes):
    return dict(workspace='creator', engine='wangp', model='t2v_1.3B', mode='text',
                resolution='480x832', prompt='An original glass sculpture in soft light.', duration=2, **changes)


class StudioContractTests(unittest.TestCase):
    def test_explicit_engine_required(self):
        request = spec()
        request.pop('engine')
        with self.assertRaises(ValueError):
            validate_job(request)

    def test_settings_match_documented_api(self):
        settings = wangp_settings(validate_job(spec(seed=15)))
        self.assertEqual(settings['video_length'], '2s')
        self.assertEqual(settings['model_type'], 't2v_1.3B')
        self.assertEqual(settings['force_fps'], 16)
        self.assertEqual(settings['seed'], 15)
        self.assertEqual(settings['prompt_enhancer'], '')

    def test_model_and_resolution_validation(self):
        for name, value in [('model', '../weights'), ('resolution', '9999x9999'), ('duration', 1000), ('steps', True), ('provider', 'paid')]:
            request = spec()
            request[name] = value
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_job(request)

    def test_image_model_requires_reference(self):
        request = spec()
        request.update(model='i2v', mode='image')
        with self.assertRaises(ValueError):
            validate_job(request)
        request['reference'] = 'a'*32
        settings = wangp_settings(validate_job(request), '/private/reference.png')
        self.assertEqual(settings['image_start'], '/private/reference.png')
        self.assertEqual(settings['image_prompt_type'], 'S')

    def test_reference_path_traversal_rejected(self):
        with self.assertRaises(ValueError):
            validate_job(spec(reference='../../private'))

    def test_blender_template_has_fixed_story_and_explicit_quality(self):
        request = {'workspace':'kids','engine':'blender','episode':'strawberry','quality':'economy'}
        self.assertEqual(validate_job(request)['duration'], 20)
        for quality in ('auto', 'fallback'):
            with self.assertRaises(ValueError):
                validate_job(dict(request, quality=quality))
        with self.assertRaises(ValueError):
            validate_job(dict(request, workspace='creator'))

    def test_mocked_wangp_success_and_progress(self):
        session = Mock()
        session.get_default_settings.return_value = {'guidance_scale': 6}
        updates = []
        def submit(settings, callbacks):
            self.assertEqual(settings['guidance_scale'], 6)
            callbacks.on_progress(SimpleNamespace(progress=50, phase='inference', current_step=2, total_steps=4))
            return SimpleNamespace(result=lambda: SimpleNamespace(success=True, generated_files=['/job/result.mp4'], errors=[]))
        session.submit_task.side_effect = submit
        self.assertEqual(generate(session, wangp_settings(validate_job(spec())), updates.append), '/job/result.mp4')
        self.assertEqual(updates[0]['progress'], 50)

    def test_mocked_wangp_failure_not_successful(self):
        session = Mock()
        session.get_default_settings.return_value = {}
        session.submit_task.return_value.result.return_value = SimpleNamespace(success=False, generated_files=[], errors=[])
        with self.assertRaises(RuntimeError):
            generate(session, wangp_settings(validate_job(spec())), lambda _: None)

    def test_mocked_wangp_cancellation(self):
        session = Mock()
        session.get_default_settings.return_value = {}
        job = session.submit_task.return_value
        def result():
            time.sleep(.35)
            return SimpleNamespace(success=False, generated_files=[], errors=[])
        job.result.side_effect = result
        with self.assertRaises(RuntimeError):
            generate(session, wangp_settings(validate_job(spec())), lambda _: None, lambda: True)
        job.cancel.assert_called_once()

    def test_missing_mp4_rejected(self):
        session = Mock()
        session.get_default_settings.return_value = {}
        session.submit_task.return_value.result.return_value = SimpleNamespace(success=True, generated_files=['image.png'], errors=[])
        with self.assertRaises(RuntimeError):
            generate(session, wangp_settings(validate_job(spec())), lambda _: None)

    def test_no_paid_or_unencrypted_provider(self):
        with self.assertRaises(ValueError):
            FreeGpuProvider('https://example.com', 'token')
        with self.assertRaises(ValueError):
            FreeGpuProvider('http://example.com', 'token', True)
        with self.assertRaises(ValueError):
            FreeGpuProvider('https://token@example.com', 'token', True)


class StudioQueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config = Config(self.temp.name)
        self.config.wangp_root = self.config.wangp_python = self.config.blender_python = ''
        self.store = Store(self.config.data / 'jobs.sqlite3')

    def tearDown(self):
        self.temp.cleanup()

    def test_fifo_and_single_claim(self):
        first = self.store.create(validate_job(spec()))
        second = self.store.create(validate_job(spec()))
        self.assertEqual(self.store.claim()['id'], first['id'])
        self.assertEqual(self.store.claim()['id'], second['id'])
        self.assertIsNone(self.store.claim())

    def test_restart_marks_interrupted_but_keeps_queued(self):
        first = self.store.create(validate_job(spec()))
        self.store.claim()
        second = self.store.create(validate_job(spec()))
        recovered = Store(self.config.data / 'jobs.sqlite3')
        self.assertEqual(recovered.get(first['id'])['state'], 'interrupted')
        self.assertEqual(recovered.get(second['id'])['state'], 'queued')

    def test_queued_cancellation(self):
        job = self.store.create(validate_job(spec()))
        self.assertEqual(self.store.cancel(job['id'])['state'], 'cancelled')
        self.assertIsNone(self.store.claim())

    def test_unconfigured_gpu_fails_without_blender(self):
        self.store.create(validate_job(spec()))
        with patch('studio.engine.subprocess.Popen') as process:
            Worker(self.config, self.store).execute(self.store.claim())
            process.assert_not_called()
        result = self.store.list()[0]
        self.assertEqual(result['state'], 'failed')
        self.assertIn('No engine fallback', result['error'])
        self.assertIsNone(result['download'])

    def test_images_normalized_and_metadata_removed(self):
        raw = io.BytesIO()
        Image.new('RGB', (3000,1000), 'red').save(raw, format='JPEG', exif=b'Exif\0\0')
        ref = save_reference(self.config, base64.b64encode(raw.getvalue()).decode())
        with Image.open(self.config.data/'references'/(ref['id']+'.png')) as image:
            self.assertEqual(image.width, 2048)
            self.assertNotIn('exif', image.info)
        with self.assertRaises(Exception):
            save_reference(self.config, base64.b64encode(b'not an image').decode())


class StudioHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config = Config(self.temp.name)
        self.config.wangp_root = self.config.wangp_python = ''
        self.server = make_server(self.config, port=0, start_worker=False)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def request(self, route, payload=None, headers=None):
        return urllib.request.urlopen(urllib.request.Request(self.url+route,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={'Content-Type':'application/json', **(headers or {})}), timeout=5)

    def test_api_create_history_and_cancel(self):
        with self.request('/api/jobs', spec()) as response:
            job = json.load(response)
        with self.request('/api/jobs') as response:
            self.assertEqual(json.load(response)[0]['id'], job['id'])
        with self.request('/api/jobs/'+job['id']+'/cancel', {}) as response:
            self.assertEqual(json.load(response)['state'], 'cancelled')

    def test_csrf_dns_rebinding_and_traversal(self):
        for headers in [{'Origin':'https://evil.example'}, {'Host':'evil.example'}]:
            with self.subTest(headers=headers), self.assertRaises(urllib.error.HTTPError) as error:
                self.request('/api/jobs',spec(),headers)
            self.assertEqual(error.exception.code,403)
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request('/../../README.md')
        self.assertEqual(error.exception.code,404)

    def test_sample_range_and_download(self):
        self.config.sample = self.config.data/'sample.mp4'
        self.config.sample.write_bytes(b'0123456789')
        with self.request('/api/sample',headers={'Range':'bytes=2-5'}) as response:
            self.assertEqual(response.status,206)
            self.assertEqual(response.read(),b'2345')
        with self.request('/api/sample?download=1') as response:
            self.assertIn('attachment',response.headers['Content-Disposition'])
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request('/api/sample',headers={'Range':'bytes=99-'})
        self.assertEqual(error.exception.code,416)

    def test_bridge_auth_and_engine_restriction(self):
        self.config.gpu_only=True
        self.config.bridge_token='test-only-'+'x'*32
        with self.assertRaises(urllib.error.HTTPError):
            self.request('/api/capabilities')
        headers={'Authorization':'Bearer '+self.config.bridge_token}
        with self.request('/api/capabilities',headers=headers) as response:
            self.assertTrue(json.load(response)['gpu_bridge'])
        with self.assertRaises(urllib.error.HTTPError):
            self.request('/api/jobs',{'engine':'blender','workspace':'kids','episode':'strawberry'},headers)

    def test_remote_provider_roundtrip_with_mocked_gpu_output(self):
        self.config.gpu_only=True
        self.config.bridge_token='test-only-'+'x'*32
        self.config.wangp_root=self.config.wangp_python='mock-configured'
        provider = FreeGpuProvider(self.url,self.config.bridge_token,True)
        mock_video=self.config.data/'mock.mp4'
        mock_video.write_bytes(b'mocked GPU transport, not a real video')
        def finish():
            for _ in range(50):
                job=self.server.store.claim()
                if job:
                    self.server.store.update(job['id'],state='succeeded',output=str(mock_video))
                    return
                time.sleep(.02)
        finish_thread=threading.Thread(target=finish)
        finish_thread.start()
        output=self.config.data/'download.mp4'
        provider.run(validate_job(spec()),None,output,lambda *_:None,lambda:False,5)
        finish_thread.join()
        self.assertEqual(output.read_bytes(),mock_video.read_bytes())


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg required for real decoding test')
class StudioMediaTests(unittest.TestCase):
    def test_real_mp4_decode_and_invalid_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'real-cpu-test.mp4'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=green:s=64x96:d=1','-c:v','libx264','-pix_fmt','yuv420p',str(path)],check=True,timeout=30)
            report=verify_video(path)
            self.assertTrue(report['decode_passed'])
            self.assertEqual(report['height'],96)
            path.write_bytes(b'not a video')
            with self.assertRaises(subprocess.CalledProcessError):
                verify_video(path)


if __name__=='__main__':
    unittest.main()
