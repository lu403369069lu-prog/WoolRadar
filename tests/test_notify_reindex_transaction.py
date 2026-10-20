"""Outbox snapshots must survive campaign reindex without aborting node delivery.

Temporary SQLite only; no real HTTP, Telegram, production DB or scheduler.
"""
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from core.db import Database
from core.models import Candidate, Evidence
from core.notify import NotificationQueue


A = 'https://publisher.example/a'
B = 'https://publisher.example/b'
TITLES = {A: 'Vendor public grant', B: 'Last chance Vendor public grant'}
REVIEW = {'method': 'normal_browser_read', 'campaign_url': 'https://gleam.io/Ab123',
          'member_urls': [A, B], 'member_titles': TITLES}


class VerifiedOutboxReindexTests(unittest.TestCase):
    def seed(self, root):
        db = Database(root / 'isolated.db')
        one = db.upsert_candidate(Candidate('n', 'rss', TITLES[A], A)).event_id
        two = db.upsert_candidate(Candidate('n', 'rss', TITLES[B], B)).event_id
        self.assertNotEqual(one, two)
        db.add_evidence(two, Evidence('official', 'https://vendor.example/offer',
            'vendor-direct', claims={'open': True, 'public': True}))
        queue = NotificationQueue(db)
        self.assertTrue(queue.enqueue(two, '', 'local-verified', 'synthetic verified grant'))
        return db, queue, one, two

    def test_reindex_after_verified_local_claim_recovers_same_flush(self):
        """A transferred local claim must not wait five minutes for a dead owner."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db, queue, survivor, obsolete = self.seed(root)
            original_write = Path.write_text
            merges = []

            def merge_after_preparing_receipt(path, text, *args, **kwargs):
                result = original_write(path, text, *args, **kwargs)
                if path.suffix == '.tmp' and not merges:
                    merges.append(db.review_campaign(REVIEW))
                return result

            with mock.patch.object(Path, 'write_text', new=merge_after_preparing_receipt):
                summary = queue.flush({}, local_dir=root / 'out')
            self.assertEqual(len(merges), 1)
            self.assertEqual(merges[0]['merged'], 1)
            self.assertEqual(summary['local'], 1)
            files = list((root / 'out').glob('notification-*.json'))
            self.assertEqual(len(files), 1)
            with db.connect() as conn:
                row = conn.execute('SELECT event_id,result FROM notifications').fetchone()
                self.assertEqual((row['event_id'], row['result']), (survivor, 'SENT'))
                self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(), [])
            self.assertFalse(queue.pending())

    def test_reindex_collision_never_reclaims_another_active_local_owner(self):
        """Matching payload/time/deadline do not confer ownership of a survivor."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db, queue, survivor, obsolete = self.seed(root)
            with db.connect() as conn:
                original = conn.execute('SELECT * FROM notifications WHERE event_id=?',
                                        (obsolete,)).fetchone()
                # Deliberately identical payload, creation time and claim fence:
                # only the distinct notification ID identifies the real owner.
                conn.execute('''INSERT INTO notifications(event_id,batch_id,channel,
                    created_at,result,payload,attempts,next_attempt)
                    VALUES(?,?,?,?,?,?,?,?)''',
                    (survivor, original['batch_id'], original['channel'],
                     original['created_at'], 'CLAIMED', original['payload'],
                     1, 1300.0))
            original_write = Path.write_text
            merges = []

            def merge_during_staging(path, content, *args, **kwargs):
                result = original_write(path, content, *args, **kwargs)
                if path.suffix == '.tmp' and not merges:
                    merges.append(db.review_campaign(REVIEW))
                return result

            with mock.patch('core.notify.time.time', return_value=1000.0), \
                 mock.patch.object(Path, 'write_text', new=merge_during_staging):
                result = queue.flush({}, local_dir=root / 'out')
            self.assertEqual([m['merged'] for m in merges], [1])
            self.assertEqual(result['local'], 0)
            self.assertEqual(list((root / 'out').glob('notification-*.json')), [])
            with db.connect() as conn:
                rows = conn.execute('SELECT id,event_id,result,next_attempt FROM notifications').fetchall()
                self.assertEqual(len(rows), 1)
                self.assertEqual((rows[0]['event_id'], rows[0]['result'],
                                  rows[0]['next_attempt']), (survivor, 'CLAIMED', 1300.0))
                self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(), [])

    def test_old_pending_snapshot_after_merge_does_not_abort_outbox(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db, queue, one, two = self.seed(root)
            original = queue.pending

            def pending_then_merge():
                snapshot = original()
                self.assertEqual(snapshot[0]['event_id'], two)
                self.assertEqual(db.review_campaign(REVIEW)['merged'], 1)
                return snapshot

            with mock.patch.object(queue, 'pending', side_effect=pending_then_merge):
                first = queue.flush({}, local_dir=root / 'out')
            self.assertEqual(first['local'], 0)
            self.assertEqual(len(db.list_events()), 1)
            self.assertEqual(db.list_events()[0]['id'], one)
            with db.connect() as conn:
                migrated = [dict(row) for row in conn.execute(
                    "SELECT event_id,result FROM notifications WHERE channel='local-verified'")]
            self.assertEqual(len(migrated), 1)
            self.assertEqual(migrated[0]['event_id'], one)
            self.assertEqual(migrated[0]['result'], 'PENDING')
            second = queue.flush({}, local_dir=root / 'out')
            self.assertEqual(second['local'], 1)
            self.assertEqual(len(list((root / 'out').glob('*.json'))), 1)
            self.assertEqual(queue.pending(), [])

    def test_verified_revalidation_blocks_merging_until_claim_is_decided(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db, queue, _, two = self.seed(root)
            reached, release, started, finished = (
                threading.Event() for _ in range(4))
            errors = []
            observed = []
            original = db.get_event

            def slow_read(event_id):
                result = original(event_id)
                reached.set()
                if not release.wait(10):
                    raise TimeoutError('verified revalidation never resumed')
                return result

            def send():
                try:
                    observed.append(queue.flush({}, local_dir=root / 'out'))
                except BaseException as e:
                    errors.append(repr(e))

            def merge():
                started.set()
                try:
                    db.review_campaign(REVIEW)
                except BaseException as e:
                    errors.append(repr(e))
                finally:
                    finished.set()

            with mock.patch.object(db, 'get_event', side_effect=slow_read):
                sender = threading.Thread(target=send, name='verified-outbox')
                migrator = threading.Thread(target=merge, name='review-migration')
                sender.start()
                try:
                    self.assertTrue(reached.wait(10))
                    migrator.start()
                    self.assertTrue(started.wait(10))
                    self.assertFalse(finished.wait(.15),
                        'reindex completed before revalidation/claim transaction')
                finally:
                    release.set()
                    sender.join(15)
                    if migrator.ident is not None:
                        migrator.join(15)
            self.assertFalse(sender.is_alive())
            self.assertFalse(migrator.is_alive())
            self.assertEqual(errors, [])
            self.assertEqual(observed[0]['local'], 1)
            self.assertNotIn('uncertain', observed[0])
            self.assertEqual(len(db.list_events()), 1)
            with db.connect() as conn:
                self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(), [])



class ReusedNotificationIdTests(unittest.TestCase):
    def seed(self, root, channel):
        db = Database(root / 'isolated.db')
        first = db.upsert_candidate(Candidate('n', 'rss', 'Old grant',
            'https://publisher.example/old')).event_id
        second = db.upsert_candidate(Candidate('n', 'rss', 'New grant',
            'https://publisher.example/new')).event_id
        queue = NotificationQueue(db)
        self.assertTrue(queue.enqueue(first, '', channel, 'OLD payload'))
        return db, queue, second

    def recycle(self, db, old_id, second, channel):
        with db.connect() as conn:
            conn.execute('DELETE FROM notifications WHERE id=?', (old_id,))
            conn.execute('INSERT INTO notifications(event_id,batch_id,channel,created_at,result,payload) '
                         'VALUES(?,?,?,?,?,?)',
                         (second, '', channel, '2026-10-15T00:00:01Z', 'PENDING', 'NEW payload'))
            row = conn.execute('SELECT id,result,payload FROM notifications').fetchone()
            self.assertEqual(row['id'], old_id)  # SQLite rowid reuse

    def test_recycled_id_after_pending_snapshot_cannot_claim_unrelated_notice(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db, queue, second = self.seed(root, 'local-discovery')
            original = queue.pending
            def pending_then_recycle():
                snapshot = original()
                self.recycle(db, snapshot[0]['id'], second, 'local-discovery')
                return snapshot
            with mock.patch.object(queue, 'pending', side_effect=pending_then_recycle):
                result = queue.flush({}, local_dir=root / 'out')
            self.assertEqual(result['local'], 0)
            with db.connect() as conn:
                self.assertEqual(conn.execute('SELECT result FROM notifications').fetchone()[0], 'PENDING')
            self.assertFalse(list((root / 'out').glob('*.json')))

    def test_recycled_id_during_send_cannot_mark_new_notice_sent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db, queue, second = self.seed(root, 'telegram')
            old_id = queue.pending()[0]['id']
            def sender(payload):
                self.assertEqual(payload, 'OLD payload')
                self.recycle(db, old_id, second, 'telegram')
                return 'SENT'
            result = queue.flush({'telegram_send_enabled': True}, sender=sender)
            # The external send happened, but the original outbox row was
            # replaced before the confirmation CAS. Never report it as a
            # durably confirmed delivery (nor mark the replacement as sent).
            self.assertEqual(result['sent'], 0)
            self.assertEqual(result['uncertain'], 1)
            with db.connect() as conn:
                self.assertEqual(conn.execute('SELECT result FROM notifications').fetchone()[0], 'PENDING')



class LocalReceiptIdReuseTests(unittest.TestCase):
    def test_recycled_sqlite_id_never_replaces_existing_local_receipt(self):
        # The filesystem is a durable delivery artifact; database row IDs
        # alone are not globally unique after a campaign reindex/deletion.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db = Database(root / 'outbox.db')
            queue = NotificationQueue(db)
            target = root / 'receipts'
            self.assertTrue(queue.record_health('node-one', 'FAILED', 'FIRST'))
            self.assertEqual(queue.flush({}, local_dir=target)['local'], 1)
            previous = sorted(target.glob('notification-*.json'))
            self.assertEqual(len(previous), 1)
            first_receipt = previous[0].read_bytes()
            with db.connect() as conn:
                conn.execute('DELETE FROM notifications')
            # INTEGER PRIMARY KEY is reused on the newly empty table.
            self.assertTrue(queue.record_health('node-two', 'FAILED', 'SECOND'))
            with db.connect() as conn:
                self.assertEqual(
                    [row[0] for row in conn.execute('SELECT id FROM notifications')],
                    [1])
            self.assertEqual(queue.flush({}, local_dir=target)['local'], 1)
            receipts = sorted(target.glob('notification-*.json'))
            self.assertEqual(len(receipts), 2)
            self.assertEqual(previous[0].read_bytes(), first_receipt)
            self.assertEqual(
                {json.loads(path.read_text(encoding='utf-8'))['batch_id']
                 for path in receipts}, {'node-one', 'node-two'})


if __name__ == '__main__':
    unittest.main()
