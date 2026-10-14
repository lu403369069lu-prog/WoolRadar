import tempfile
import unittest
from pathlib import Path
from core.review_import import import_public_review
from core.db import Database

TEMP = Path(__file__).parents[1] / '.test-tmp'
TEMP.mkdir(exist_ok=True)


class ReviewImportTests(unittest.TestCase):
    def test_public_review_is_idempotent_and_unknown_open_is_not_claimable(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as td:
            root = Path(td)
            payload = {'method': 'normal_browser_read', 'checked_at': '2026-10-11T15:00:00Z',
                'url': 'https://www.mlh.com/events/prizes', 'records': [{
                    'title': 'MLH free cloud credits', 'excerpt': 'Public official page mentions credits.',
                    'claims': {'open': 'unknown', 'remaining': 'unknown'}}]}
            result = import_public_review(root, payload)
            self.assertEqual(result[0]['status'], 'OFFICIAL_VERIFIED')
            import_public_review(root, payload)
            db = Database(root / 'data' / 'woolradar.db')
            self.assertEqual(len(db.list_events()), 1)
            with db.connect() as conn:
                self.assertEqual(conn.execute('SELECT count(*) FROM notifications').fetchone()[0], 1)
