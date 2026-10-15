"""Copy-only legacy identity migration acceptance; never opens a production DB."""
import hashlib
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from core.db import Database
from core.dedup import normalize_title, normalize_url
from core.models import Candidate


class HistoricalKeyUpgradeTests(unittest.TestCase):
    def test_dry_run_then_copy_only_reindex_preserves_notification_history(self):
        with TemporaryDirectory() as root:
            db = Database(Path(root) / 'copied-historical-fixture.db')
            url = 'https://vendor.example/offer'
            first = db.upsert_candidate(Candidate('node-old', 'fixture', 'Free VPS 1GB', url))
            legacy = hashlib.sha256(
                (normalize_title('Free VPS 1 GB') + '|' + normalize_url(url)).encode()
            ).hexdigest()[:24]
            with db.connect() as conn:
                conn.execute('UPDATE events SET canonical_key=? WHERE id=?', (legacy, first.event_id))
            second = db.upsert_candidate(Candidate('node-new', 'fixture', 'Free VPS 1 GB', url))
            self.assertNotEqual(first.event_id, second.event_id)
            with db.connect() as conn:
                for event_id in (first.event_id, second.event_id):
                    conn.execute(
                        'INSERT INTO notifications(event_id,batch_id,channel,created_at,result) VALUES(?,?,?,?,?)',
                        (event_id, '', 'digest', '2026-10-15T00:00:00Z', 'sent')
                    )
            before = db.preview_reindex()
            self.assertEqual(before['total_events'], 2)
            self.assertEqual(before['changed_keys'], 1)
            self.assertEqual(before['would_merge_events'], 1)
            self.assertEqual(before['notification_conflict_count'], 1)

            result = db.reindex()
            self.assertEqual(result['merged'], 1)
            self.assertEqual(result['remaining'], 1)
            self.assertEqual(len(db.list_events()), 1)
            event_id = db.list_events()[0]['id']
            with db.connect() as conn:
                notifications = conn.execute(
                    'SELECT event_id,channel,result FROM notifications').fetchall()
                sightings = conn.execute('SELECT node FROM sightings ORDER BY node').fetchall()
            self.assertEqual([(n[0], n[1], n[2]) for n in notifications],
                             [(event_id, 'digest', 'sent')])
            self.assertEqual([row[0] for row in sightings], ['node-new', 'node-old'])
            self.assertFalse(db.upsert_candidate(
                Candidate('node-future', 'fixture', 'Free VPS 1GB', url)).notify)

            backup = Path(result['backup'])
            self.assertTrue(backup.exists())
            with sqlite3.connect(backup) as original:
                self.assertEqual(original.execute('SELECT count(*) FROM events').fetchone()[0], 2)
                self.assertEqual(original.execute('SELECT count(*) FROM notifications').fetchone()[0], 2)
