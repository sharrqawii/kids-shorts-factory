"""Runs ONLY in the separate WanGP environment. Contract: upstream docs/API.md."""
import argparse
import json
import os
from pathlib import Path
import sys
import threading


def generate(session, settings, emit, cancelled=lambda: False):
    """Small injectable boundary tested against documented WanGP response objects."""
    class Callbacks:
        def on_progress(self, update):
            emit({'kind': 'progress', 'progress': max(0, min(99, int(update.progress or 0))),
                  'phase': str(update.phase), 'step': update.current_step, 'steps': update.total_steps})

    # Preserve model-specific defaults; do not guess all the upstream settings.
    defaults = session.get_default_settings(settings['model_type'])
    defaults.update(settings)
    job = session.submit_task(defaults, callbacks=Callbacks())
    done = threading.Event()

    def watch():
        while not done.wait(.25):
            if cancelled():
                job.cancel()
                return

    watcher = threading.Thread(target=watch, daemon=True)
    watcher.start()
    try:
        result = job.result()
    finally:
        done.set()
        watcher.join(timeout=1)
    if not result.success:
        # Detailed upstream messages remain in the private worker log, never in browser responses.
        for error in result.errors:
            print(str(error.message), file=sys.stderr)
        raise RuntimeError('WanGP generation failed; inspect the private worker log.')
    videos = [str(p) for p in result.generated_files if Path(p).suffix.lower() == '.mp4']
    if not videos:
        raise RuntimeError('WanGP returned no MP4 output.')
    return videos[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root, out = args.root.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    settings = json.loads(args.request.read_text(encoding='utf-8'))
    os.chdir(root)
    sys.path.insert(0, str(root))
    # No models are downloaded until an operator deliberately enables it in this environment.
    if os.getenv('WANGP_ALLOW_MODEL_DOWNLOADS') != 'yes':
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
    from shared.api import init
    session = init(root=root, output_dir=out, cli_args=['--attention', 'sdpa', '--profile', '4'], console_output=True)

    def emit(value):
        with (out / 'events.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(value) + '\n')

    video = generate(session, settings, emit, lambda: (out / 'cancel').exists())
    (out / 'result.json').write_text(json.dumps({'video': video}), encoding='utf-8')


if __name__ == '__main__':
    main()
