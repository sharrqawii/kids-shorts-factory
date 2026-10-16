import json
import os
from pathlib import Path

reports=list(Path('build').glob('*/render-report.json'))
lines=['## Render verification']
for path in reports:
    data=json.loads(path.read_text())
    lines.append(f"- {path.parent.name}: **{data['actual_mode']}**, {data['duration']} seconds; {data['elapsed_seconds']:.1f}s wall time.")
    lines.append(f"  {data['note']}")
    lines.append(f"  Verification: {data['verification']}")
    if data['fallback_reasons']:lines.append(f"  Fallback reasons: {data['fallback_reasons']}")
if not reports:lines.append('No completed render report exists. Inspect the failed step; do not treat this run as a successful video.')
text='\n'.join(lines)+'\n'
print(text)
if os.environ.get('GITHUB_STEP_SUMMARY'):
    with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as file:file.write(text)
