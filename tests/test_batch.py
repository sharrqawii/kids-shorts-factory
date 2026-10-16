import json
from pathlib import Path
import unittest
from factory.batch import plan

ROOT=Path(__file__).resolve().parents[1]


class BatchPlannerTests(unittest.TestCase):
    def setUp(self):self.catalog=json.loads((ROOT/'episodes/catalog.json').read_text())

    def test_five_unique_deterministic_jobs(self):
        first=plan('2026-10-13',self.catalog)
        self.assertEqual(first,plan('2026-10-13',self.catalog))
        self.assertEqual(len({job['job_id'] for job in first['jobs']}),5)
        self.assertEqual(len({job['story_id'] for job in first['jobs']}),5)

    def test_unimplemented_stories_cannot_claim_batch_is_ready(self):
        result=plan('2026-10-13',self.catalog)
        self.assertFalse(result['ready_for_batch_test'])
        self.assertTrue(result['blockers'])
        self.assertFalse(result['automatic_execution'])
        self.assertFalse(result['youtube_uploads'])

    def test_completed_stories_are_not_repeated(self):
        result=plan('2026-10-14',self.catalog,['001-giant-strawberry'])
        self.assertNotIn('001-giant-strawberry',{job['story_id'] for job in result['jobs']})
        self.assertEqual(len(result['jobs']),4)
        self.assertFalse(result['ready_for_batch_test'])

    def test_duplicate_story_ids_are_rejected(self):
        with self.assertRaises(ValueError):plan('2026-10-13',self.catalog+self.catalog[:1])

    def test_production_and_uploads_are_disabled(self):
        config=json.loads((ROOT/'config/production.json').read_text())
        self.assertFalse(config['enabled']);self.assertFalse(config['youtube_uploads_enabled'])
        self.assertIsNone(config['schedule_utc'])
        self.assertEqual(config['max_parallel_renders'],1)


if __name__=='__main__':unittest.main()
