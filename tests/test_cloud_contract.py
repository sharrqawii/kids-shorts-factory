import re
from pathlib import Path
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[1]


class CloudContractTests(unittest.TestCase):
    def test_workflows_stay_within_free_runner_contract(self):
        for path in (ROOT/'.github/workflows').glob('*.yml'):
            workflow=yaml.load(path.read_text(),Loader=yaml.BaseLoader)
            self.assertNotIn('schedule',workflow['on'])
            for job in workflow['jobs'].values():
                self.assertEqual(job['runs-on'],'ubuntu-24.04')
                self.assertEqual(job['if'],'github.event.repository.private == false')
                self.assertLessEqual(int(job['timeout-minutes']),100)
                for step in job['steps']:
                    if 'uses' in step:
                        self.assertRegex(step['uses'],r'@(\w{40})$')
                        self.assertNotIn('upload-artifact',step['uses'])
                        self.assertNotIn('cache',step.get('with',{}))

    def test_render_has_no_youtube_or_external_credentials(self):
        text=(ROOT/'.github/workflows/render.yml').read_text()
        self.assertNotIn('secrets.',text)
        self.assertNotIn('youtube',text.lower())
        self.assertIn('--budget-seconds 4500',text)
        self.assertIn('contents: write',text)
        self.assertIn('gh release create',text)

    def test_fallback_does_not_import_blender(self):
        # Bpy remains isolated so missing/failed native libraries cannot prevent fallback.
        for filename in ['render.py','graphics.py','audio.py','story.py','verify.py']:
            text=(ROOT/'factory'/filename).read_text()
            self.assertIsNone(re.search(r'^\s*(?:import bpy|from bpy)',text,re.MULTILINE))


if __name__=='__main__':unittest.main()
