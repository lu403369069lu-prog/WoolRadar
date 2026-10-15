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

if __name__ == '__main__':
    unittest.main()
