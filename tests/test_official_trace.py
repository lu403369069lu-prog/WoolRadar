import tempfile
import unittest
import urllib.error
from pathlib import Path
from contextlib import closing
from unittest.mock import patch

from core.db import Database
from core.models import Candidate
from core.official_trace import OfficialTracer, validate_public_reference

TEST_TMP = Path(__file__).parents[1] / '.test-tmp'
TEST_TMP.mkdir(exist_ok=True)


class OfficialTraceTests(unittest.TestCase):
    def test_unbudgeted_reference_still_uses_pinned_public_transport(self):
        from core.official_trace import fetch_public_page
        with patch('core.official_trace.budgeted_read', return_value=b'<html>ok</html>') as read:
            result = fetch_public_page('https://cursor.com/changelog', {'cursor.com'})
            self.assertEqual(result, b'<html>ok</html>')
            self.assertIsNone(read.call_args.args[1])
            self.assertFalse(read.call_args.args[3]('https://127.0.0.1/admin'))
            self.assertFalse(read.call_args.args[3]('https://evil.example/'))

    def test_http_budget_rejection_is_skipped_without_permanent_pause(self):
        from core.collector import SourcePaused
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as td:
            root = Path(td)
            db = Database(root / 'data' / 'woolradar.db')
            event = db.upsert_candidate(Candidate('n', 'Cursor', 'Cursor free credits', 'https://cursor.com/changelog/promo', metadata={'official': True})).event_id
            tracer = OfficialTracer(root, {'cursor.com'})
            with patch('core.official_trace.fetch_public_page', side_effect=SourcePaused('REQUEST_BUDGET')):
                result = tracer.trace(event)
            self.assertEqual(result['references'][0]['status'], 'SKIPPED')
            import sqlite3
            with closing(sqlite3.connect(tracer.budget.db_path)) as conn:
                self.assertEqual(conn.execute("SELECT count(*) FROM budget WHERE until_epoch=0 AND pause_reason<>''").fetchone()[0], 0)

    def test_existing_429_cooldown_is_not_extended_without_a_request(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as td:
            root = Path(td)
            db = Database(root / 'data' / 'woolradar.db')
            event = db.upsert_candidate(Candidate('n', 'Cursor', 'Cursor free credits',
                'https://cursor.com/changelog/promo', metadata={'official': True})).event_id
            tracer = OfficialTracer(root, {'cursor.com'})
            with patch('core.collector.time.time', return_value=1000):
                tracer.budget.pause({'id': 'other-adapter', 'endpoint': 'https://cursor.com/feed'}, 'RATE_LIMITED_429', 100)
            with patch('core.collector.time.time', return_value=1010), patch('core.official_trace.fetch_public_page') as fetch:
                tracer.trace(event)
                self.assertEqual(fetch.call_count, 0)
            import sqlite3
            with closing(sqlite3.connect(tracer.budget.db_path)) as conn:
                self.assertEqual(conn.execute("SELECT until_epoch FROM budget WHERE key='host:cursor.com'").fetchone()[0], 1100)

    def test_reference_boundary_rejects_credentials_ports_and_untrusted_hosts(self):
        hosts = {'cursor.com', 'www.cursor.com'}
        self.assertTrue(validate_public_reference('https://cursor.com/changelog/promo', hosts))
        for url in ['http://cursor.com/promo', 'https://evil.example/', 'https://cursor.com.evil.example/',
                    'https://user:secret@cursor.com/', 'https://cursor.com:8443/',
                    'https://cursor.com/login', 'https://cursor.com/%6cogin', 'https://127.0.0.1/']:
            self.assertFalse(validate_public_reference(url, hosts))

    def test_official_source_after_community_discovery_is_still_traced(self):
        from core.models import Evidence
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as td:
            root = Path(td)
            db = Database(root / 'data' / 'woolradar.db')
            event = db.upsert_candidate(Candidate('n', 'Forum', 'Cursor free credits', 'https://forum.example/1')).event_id
            db.add_evidence(event, Evidence('official', 'https://cursor.com/changelog/promo', 'official-feed'))
            with patch('core.official_trace.fetch_public_page', return_value=b'<title>Cursor free credits public announcement</title>') as fetch:
                result = OfficialTracer(root, {'cursor.com'}).trace(event)
            self.assertEqual(fetch.call_count, 1)
            self.assertEqual(result['references'][0]['status'], 'FETCHED')

    def test_503_is_not_a_permanent_platform_barrier(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as td:
            root = Path(td)
            db = Database(root / 'data' / 'woolradar.db')
            event = db.upsert_candidate(Candidate('n', 'Cursor', 'Cursor free credits',
                'https://cursor.com/changelog/promo', metadata={'official': True})).event_id
            with patch('core.official_trace.fetch_public_page', side_effect=urllib.error.HTTPError(
                    'https://cursor.com/changelog/promo', 503, 'unavailable', {}, None)):
                tracer = OfficialTracer(root, {'cursor.com'})
                result = tracer.trace(event)
            self.assertEqual(result['references'][0]['status'], 'FAILED')
            import sqlite3
            with closing(sqlite3.connect(tracer.budget.db_path)) as conn:
                self.assertFalse(conn.execute("SELECT count(*) FROM budget WHERE pause_reason<>'' AND until_epoch=0").fetchone()[0])

    def test_trace_never_infers_personal_eligibility_or_current_open_from_marketing(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as td:
            root = Path(td)
            db = Database(root / 'data' / 'woolradar.db')
            event = db.upsert_candidate(Candidate('openmagpie', 'Cursor', 'Cursor free credits',
                'https://cursor.com/changelog/promo', source_kind='official',
                metadata={'official': True})).event_id
            with patch('core.official_trace.fetch_public_page', return_value=b'<title>Cursor free credits</title><p>Free! Apply now!</p>'):
                result = OfficialTracer(root, {'cursor.com'}).trace(event)
            self.assertEqual(result['status'], 'OFFICIAL_VERIFIED')
            saved = db.get_evidence(event)[0]
            self.assertEqual(saved.claims['open'], 'unknown')
            self.assertEqual(saved.claims['remaining'], 'unknown')
            self.assertNotIn('personal_eligible', saved.claims)

    def test_community_link_to_official_domain_remains_unverified_reference(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as td:
            root = Path(td)
            db = Database(root / 'data' / 'woolradar.db')
            event = db.upsert_candidate(Candidate('n', 'forum', 'Free credits', 'https://forum.example/1',
                metadata={'official_references': ['https://cursor.com/changelog/promo']})).event_id
            with patch('core.official_trace.fetch_public_page', return_value=b'<title>Cursor</title><p>General product announcement, campaign unknown.</p>'):
                result = OfficialTracer(root, {'cursor.com'}).trace(event)
            self.assertEqual(result['status'], 'UNKNOWN')
            self.assertEqual(db.get_evidence(event)[0].kind, 'official_reference')
