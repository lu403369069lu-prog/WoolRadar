"""Official tracing must record stale merged IDs without claiming verification.

Temporary SQLite only: no HTTP requests, production database or credentials.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core.db import Database
from core.models import Candidate
from core.official_trace import OfficialTracer


A = 'https://publisher.example/a'
B = 'https://publisher.example/b'
TITLES = {A: 'Launch Vendor credit grant', B: 'Last chance Vendor credit grant'}
REVIEW = {'method': 'normal_browser_read',
          'campaign_url': 'https://gleam.io/Ab123',
          'member_urls': [A, B], 'member_titles': TITLES}


class StaleOfficialTraceTests(unittest.TestCase):
    def seed(self, root):
        db = Database(root / 'data' / 'woolradar.db')
        first = db.upsert_candidate(Candidate('n', 's', TITLES[A], A)).event_id
        second = db.upsert_candidate(Candidate('n', 's', TITLES[B], B)).event_id
        self.assertNotEqual(first, second)
        return db, first, second

    def report(self, root, event_id):
        return json.loads((root / 'evidence' / 'official-trace' /
                           f'{event_id}.json').read_text(encoding='utf-8'))

    def test_trace_starting_after_merge_returns_auditable_stale_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db, _, second = self.seed(root)
            self.assertEqual(db.review_campaign(REVIEW)['merged'], 1)
            with mock.patch('core.official_trace.fetch_public_page',
                            side_effect=AssertionError('no network allowed')):
                result = OfficialTracer(root, hosts=set()).trace(second)
            self.assertEqual(result['status'], 'STALE_EVENT_ID')
            self.assertEqual(result['error_code'], 'EVENT_MERGED_OR_REMOVED')
            self.assertEqual(result['references'], [])
            self.assertEqual(result, self.report(root, second))

    def test_trace_finishing_after_merge_marks_status_stale_not_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, first, _ = self.seed(root)
            tracer = OfficialTracer(root, hosts=set())
            original = tracer.pipeline.db.get_event
            calls = []

            def read_then_disappear(event_id):
                calls.append(event_id)
                if len(calls) == 2:
                    raise KeyError(event_id)
                return original(event_id)

            with mock.patch.object(tracer.pipeline.db, 'get_event',
                                   side_effect=read_then_disappear):
                with mock.patch('core.official_trace.fetch_public_page',
                                side_effect=AssertionError('no network allowed')):
                    result = tracer.trace(first)
            self.assertEqual(len(calls), 2)
            self.assertEqual(result['status'], 'STALE_EVENT_ID')
            self.assertEqual(result['error_code'], 'EVENT_MERGED_OR_REMOVED')
            self.assertEqual(result, self.report(root, first))

    def test_existing_event_with_no_references_retains_current_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, first, _ = self.seed(root)
            result = OfficialTracer(root, hosts=set()).trace(first)
            self.assertEqual(result['status'], 'DISCOVERED')
            self.assertNotIn('error_code', result)
            self.assertEqual(result['references'], [])
            self.assertEqual(result, self.report(root, first))


if __name__ == '__main__':
    unittest.main()
