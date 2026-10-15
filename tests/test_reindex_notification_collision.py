"""Notifications retain delivery/claim state when reviewed campaigns merge.

Runs only against temporary SQLite and does not deliver real notifications.
"""
import tempfile
import unittest
from pathlib import Path

from core.db import Database
from core.models import Candidate
from core.notify import NotificationQueue


A = 'https://publisher.example/a'
B = 'https://publisher.example/b'
TITLES = {A: 'First launch of cloud credit grant',
          B: 'Last chance for server credit grant'}
REVIEW = {'method': 'normal_browser_read',
          'campaign_url': 'https://gleam.io/Ab123',
          'member_urls': [A, B], 'member_titles': TITLES}


class NotificationCollisionMigrationTests(unittest.TestCase):
    def seed(self, root):
        db = Database(root / 'radar.db')
        first = db.upsert_candidate(Candidate('test', 'publisher', TITLES[A], A)).event_id
        second = db.upsert_candidate(Candidate('test', 'publisher', TITLES[B], B)).event_id
        self.assertNotEqual(first, second)
        return db, first, second

    def set_notice(self, db, event_id, state, payload, attempts=0, next_attempt=0):
        with db.connect() as conn:
            conn.execute(
                "INSERT INTO notifications(event_id,batch_id,channel,created_at,result,payload,attempts,next_attempt) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (event_id, '', 'local-verified', '2026-10-15T00:00:00Z',
                 state, payload, attempts, next_attempt))

    def merged_notice(self, db, first):
        with db.connect() as conn:
            return dict(conn.execute(
                "SELECT * FROM notifications WHERE event_id=? AND channel='local-verified'",
                (first,)).fetchone())

    def test_already_sent_loser_must_not_become_pending_again(self):
        with tempfile.TemporaryDirectory() as tmp:
            db, first, second = self.seed(Path(tmp))
            self.set_notice(db, first, 'PENDING', 'survivor pending')
            self.set_notice(db, second, 'SENT', 'already delivered', attempts=2)
            self.assertEqual(db.review_campaign(REVIEW)['merged'], 1)
            notice = self.merged_notice(db, first)
            self.assertEqual(notice['result'], 'SENT')
            self.assertEqual(notice['payload'], 'already delivered')
            self.assertGreaterEqual(notice['attempts'], 2)
            self.assertEqual(NotificationQueue(db).pending(), [])
            with db.connect() as conn:
                self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(), [])

    def test_in_flight_loser_cannot_be_reset_to_pending_by_merge(self):
        with tempfile.TemporaryDirectory() as tmp:
            db, first, second = self.seed(Path(tmp))
            self.set_notice(db, first, 'PENDING', 'survivor pending')
            self.set_notice(db, second, 'CLAIMED', 'in-flight notice',
                            attempts=3, next_attempt=9999999999)
            self.assertEqual(db.review_campaign(REVIEW)['merged'], 1)
            notice = self.merged_notice(db, first)
            self.assertEqual(notice['result'], 'CLAIMED')
            self.assertGreaterEqual(notice['next_attempt'], 9999999999)
            self.assertGreaterEqual(notice['attempts'], 3)

    def test_existing_sent_survivor_is_never_downgraded(self):
        with tempfile.TemporaryDirectory() as tmp:
            db, first, second = self.seed(Path(tmp))
            self.set_notice(db, first, 'SENT', 'survivor already delivered', attempts=1)
            self.set_notice(db, second, 'PENDING', 'old pending')
            self.assertEqual(db.review_campaign(REVIEW)['merged'], 1)
            notice = self.merged_notice(db, first)
            self.assertEqual(notice['result'], 'SENT')
            self.assertEqual(notice['payload'], 'survivor already delivered')
            self.assertEqual(NotificationQueue(db).pending(), [])

    def test_two_claimed_notices_keep_longest_lease_and_attempt_history(self):
        for first_deadline, second_deadline in [(0, 9999999999), (9999999999, 0),
                                                 (9999999999, 9999999998)]:
            with self.subTest(first=first_deadline, second=second_deadline):
                with tempfile.TemporaryDirectory() as tmp:
                    db, first, second = self.seed(Path(tmp))
                    self.set_notice(db, first, 'CLAIMED', 'first in-flight',
                                    attempts=2, next_attempt=first_deadline)
                    self.set_notice(db, second, 'CLAIMED', 'second in-flight',
                                    attempts=5, next_attempt=second_deadline)
                    self.assertEqual(db.review_campaign(REVIEW)['merged'], 1)
                    notice = self.merged_notice(db, first)
                    self.assertEqual(notice['result'], 'CLAIMED')
                    self.assertEqual(notice['next_attempt'], max(first_deadline, second_deadline))
                    self.assertEqual(notice['attempts'], 5)

    def test_merge_does_not_resend_while_either_claim_is_still_active(self):
        with tempfile.TemporaryDirectory() as tmp:
            db, first, second = self.seed(Path(tmp))
            self.set_notice(db, first, 'CLAIMED', 'first in-flight',
                            attempts=2, next_attempt=0)
            self.set_notice(db, second, 'CLAIMED', 'second in-flight',
                            attempts=5, next_attempt=9999999999)
            with db.connect() as conn:
                conn.execute("UPDATE notifications SET channel='telegram-discovery'")
            self.assertEqual(db.review_campaign(REVIEW)['merged'], 1)
            calls = []
            def fake_sender(payload):
                calls.append(payload)
                return 'SENT'
            result = NotificationQueue(db).flush({'telegram_send_enabled': True}, sender=fake_sender)
            self.assertEqual(calls, [])
            self.assertEqual(result['sent'], 0)
            with db.connect() as conn:
                self.assertEqual(conn.execute('SELECT result FROM notifications').fetchone()[0], 'CLAIMED')


if __name__ == '__main__':
    unittest.main()
