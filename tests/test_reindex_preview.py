"""Historical identity migration can be inspected without modifying data."""
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from core.db import Database
from core.dedup import normalize_title, normalize_url
from core.models import Candidate


class ReindexPreviewTests(unittest.TestCase):
    def test_current_keys_require_no_changes(self):
        with TemporaryDirectory() as root:
            db = Database(Path(root) / 'x.db')
            db.upsert_candidate(Candidate('n', 's', 'Free VPS 1GB', 'https://a.example/vps'))
            db.upsert_candidate(Candidate('n', 's', 'Free VPS 1GB', 'https://b.example/vps'))
            result = db.preview_reindex()
            self.assertEqual(result['total_events'], 2)
            self.assertEqual(result['changed_keys'], 0)
            self.assertEqual(result['would_merge_events'], 0)

    def test_legacy_spacing_key_detected_without_mutation(self):
        with TemporaryDirectory() as root:
            db = Database(Path(root) / 'x.db')
            url, title = 'https://a.example/vps', 'Free VPS 1 GB'
            first = db.upsert_candidate(Candidate('n', 's', title, url))
            legacy = hashlib.sha256((normalize_title(title) + '|' + normalize_url(url)).encode()).hexdigest()[:24]
            with db.connect() as conn:
                conn.execute('UPDATE events SET canonical_key=? WHERE id=?', (legacy, first.event_id))
            before = db.get_event(first.event_id)['canonical_key']
            result = db.preview_reindex()
            after = db.get_event(first.event_id)['canonical_key']
            self.assertEqual(result['changed_keys'], 1)
            self.assertEqual(result['would_merge_events'], 0)
            self.assertEqual(before, after)
            self.assertEqual(before, legacy)

    def test_legacy_key_conflict_with_new_row_reports_merge_and_notification_collision(self):
        with TemporaryDirectory() as root:
            db = Database(Path(root) / 'x.db')
            url = 'https://a.example/vps'
            a = db.upsert_candidate(Candidate('n1', 's', 'Free VPS 1GB', url))
            b = db.upsert_candidate(Candidate('n2', 's', 'Free VPS 1 GB', url))
            self.assertEqual(a.event_id, b.event_id)
            legacy = hashlib.sha256((normalize_title('Free VPS 1 GB')+'|'+normalize_url(url)).encode()).hexdigest()[:24]
            with db.connect() as conn:
                # Freeze two legacy-state rows to reproduce an upgrade dry run.
                conn.execute('UPDATE events SET canonical_key=? WHERE id=?', (legacy, a.event_id))
                new_key = hashlib.sha256((normalize_title('Free VPS 1GB')+'|'+normalize_url(url)).encode()).hexdigest()[:24]
                conn.execute('INSERT INTO events(canonical_key,batch_id,title,primary_url,source,node,first_seen,last_seen) VALUES(?,?,?,?,?,?,?,?)',
                             (new_key,'','Free VPS 1GB',url,'s','n2','2026-01-01','2026-01-01'))
                second = conn.execute('SELECT id FROM events WHERE canonical_key=?',(new_key,)).fetchone()[0]
                for event_id in (a.event_id, second):
                    conn.execute('INSERT INTO notifications(event_id,batch_id,channel,created_at,result) VALUES(?,?,?,?,?)',
                                 (event_id,'','digest','2026-01-01','sent'))
            result = db.preview_reindex()
            self.assertEqual(result['total_events'], 2)
            self.assertEqual(result['would_merge_events'], 1)
            self.assertEqual(result['notification_conflict_count'], 1)
            self.assertEqual(len(db.list_events()), 2)

if __name__ == '__main__':
    unittest.main()
