"""Outbox snapshots must survive campaign reindex without aborting node delivery.

Temporary SQLite only; no real HTTP, Telegram, production DB or scheduler.
"""
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
            self.assertEqual(result['sent'], 1)  # external send did occur
            with db.connect() as conn:
                self.assertEqual(conn.execute('SELECT result FROM notifications').fetchone()[0], 'PENDING')



if __name__ == '__main__':
    unittest.main()
