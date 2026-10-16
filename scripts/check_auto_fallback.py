"""Integration test: simulate a failed native render and verify the real fallback MP4."""
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch
from factory.render import main

out=Path(sys.argv[1] if len(sys.argv)>1 else 'build/auto-failure-smoke')
with patch('factory.render.blender',side_effect=subprocess.CalledProcessError(1,'simulated-blender-failure')):
    with patch.object(sys,'argv',['factory.render','--mode','auto','--smoke','--out',str(out)]):
        main()
report=json.loads((out/'render-report.json').read_text())
assert report['actual_mode']=='fallback'
assert 'benchmark failed' in report['fallback_reasons'][0]
assert all(report['verification'].values())
print('PASS: simulated Blender failure produced an explicitly labeled, verified fallback MP4.')
