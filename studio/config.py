import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WANGP_REVISION = 'af2ed29a83dbccc7f1c0571a73005648436b392e'
MODELS = {
    't2v_1.3B': {'name': 'Wan 2.1 · 1.3B', 'modes': ['text'], 'fps': 16,
                 'resolutions': ['480x832', '832x480', '480x480'], 'steps': 30},
    'i2v': {'name': 'Wan 2.1 · Image 14B', 'modes': ['image'], 'fps': 16,
            'resolutions': ['480x832', '832x480', '480x480'], 'steps': 30},
    'ltx2_22B_distilled': {'name': 'LTX-2 · Distilled 22B', 'modes': ['text', 'image'], 'fps': 24,
                         'resolutions': ['512x768', '768x512', '1280x704'], 'steps': 8},
}


class Config:
    def __init__(self, data=None):
        self.data = Path(data or os.getenv('STUDIO_DATA', ROOT / 'studio-data')).resolve()
        self.wangp_root = os.getenv('WANGP_ROOT', '')
        self.wangp_python = os.getenv('WANGP_PYTHON', '')
        self.blender_python = os.getenv('BLENDER_PYTHON', '')
        self.remote_url = os.getenv('FREE_GPU_URL', '')
        self.remote_token = os.getenv('FREE_GPU_TOKEN', '')
        self.remote_free = os.getenv('FREE_GPU_CONFIRMED_ZERO_COST') == 'yes'
        self.bridge_token = os.getenv('STUDIO_BRIDGE_TOKEN', '')
        self.sample = Path(os.environ['PIP_SAMPLE']).resolve() if os.getenv('PIP_SAMPLE') else None
        self.timeout = 3600
        self.gpu_only = False
        self.data.mkdir(parents=True, exist_ok=True)

    def capabilities(self):
        return {
            'wangp_local': bool(self.wangp_root and self.wangp_python),
            'wangp_cloud': bool(self.remote_url and self.remote_token and self.remote_free),
            'blender': bool(self.blender_python) and not self.gpu_only,
            'sample': bool(self.sample and self.sample.is_file()),
            'gpu_generation_verified': False,
            'budget': 0, 'uploads_enabled': False, 'recurring_enabled': False,
        }


def validate_job(value):
    if not isinstance(value, dict):
        raise ValueError('A job must be a JSON object.')
    workspace = value.get('workspace')
    engine = value.get('engine')
    if workspace not in ('kids', 'creator') or engine not in ('blender', 'wangp'):
        raise ValueError('Choose a workspace and explicitly choose an engine.')
    prompt = value.get('prompt', '')
    if not isinstance(prompt, str) or len(prompt) > 4000:
        raise ValueError('Prompt must be text, up to 4,000 characters.')
    job = {'workspace': workspace, 'engine': engine, 'prompt': prompt.strip()}
    if engine == 'blender':
        if workspace != 'kids' or value.get('episode') != 'strawberry':
            raise ValueError('Blender currently supports only Pip and the giant strawberry in Kids Factory.')
        quality = value.get('quality', 'economy')
        if quality not in ('economy', 'blender'):
            raise ValueError('Choose economy or native Blender. Automatic fallback is disabled in Studio.')
        return dict(job, episode='strawberry', quality=quality, duration=20, resolution='1080x1920', provider='local')
    model = value.get('model')
    if model not in MODELS:
        raise ValueError('Choose a supported WanGP model.')
    spec = MODELS[model]
    mode = value.get('mode', 'text')
    if mode not in spec['modes']:
        raise ValueError('This model does not support the selected input mode.')
    resolution = value.get('resolution')
    if resolution not in spec['resolutions']:
        raise ValueError('Choose a resolution supported by this model preset.')
    duration = value.get('duration', 4)
    steps = value.get('steps', spec['steps'])
    seed = value.get('seed', 42)
    for number, low, high, label in [(duration, 1, 20, 'Duration'), (steps, 1, 60, 'Steps'), (seed, 0, 2147483647, 'Seed')]:
        if type(number) is not int or not low <= number <= high:
            raise ValueError(f'{label} is outside its supported range.')
    if not prompt.strip():
        raise ValueError('Describe the video you want to create.')
    provider = value.get('provider', 'local')
    if provider not in ('local', 'free-cloud'):
        raise ValueError('Only local or an existing, confirmed-free GPU endpoint is supported.')
    reference = value.get('reference', '')
    if reference and (not isinstance(reference, str) or not re.fullmatch(r'[a-f0-9]{32}', reference)):
        raise ValueError('Invalid reference image ID.')
    if mode == 'image' and (not isinstance(reference, str) or not reference):
        raise ValueError('Upload a reference image first.')
    negative = value.get('negative_prompt', '')
    if not isinstance(negative, str) or len(negative) > 2000:
        raise ValueError('Negative prompt must be text, up to 2,000 characters.')
    return dict(job, model=model, mode=mode, resolution=resolution, duration=duration,
                steps=steps, seed=seed, provider=provider, reference=reference if mode == 'image' else '',
                negative_prompt=negative)


def wangp_settings(job, reference=None):
    settings = {'model_type': job['model'], 'prompt': job['prompt'],
                'negative_prompt': job['negative_prompt'], 'resolution': job['resolution'],
                'video_length': f"{job['duration']}s", 'duration_seconds': job['duration'],
                'force_fps': MODELS[job['model']]['fps'], 'num_inference_steps': job['steps'],
                'seed': job['seed'], 'prompt_enhancer': ''}
    if reference:
        settings['image_start'] = str(reference)
        settings['image_prompt_type'] = 'S'
    return settings
