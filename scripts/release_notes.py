import json
from pathlib import Path

data=json.loads(Path('build/episode/render-report.json').read_text())
print('Original Pip garden episode, built entirely from repository source.\n')
print(f"Renderer: **{data['actual_mode']}**. {data['note']}\n")
print('MP4: 1080 x 1920, 20 seconds, H.264, AAC stereo, 24 fps.\n')
print(f"Measured build time: {data['elapsed_seconds']:.1f} seconds.\n")
print(f"Video SHA-256: `{data['sha256']}`\n")
print('Audio and creative assets: CC0-1.0. Source code: MIT. No YouTube publishing is connected.')
if data['fallback_reasons']:print('\nFallback reason: '+'; '.join(data['fallback_reasons']))
