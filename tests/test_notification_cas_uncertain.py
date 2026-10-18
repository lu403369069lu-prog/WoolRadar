"""WR-H18: sent-delivery acknowledgement must fail closed on CAS races.

All cases use disposable synthetic SQLite and stub senders. No real delivery.
"""
import tempfile
import unittest
from pathlib import Path

from core.db import Database
from core.models import Candidate
from core.notify import NotificationQueue

ROOT = Path(__file__).resolve().parents[1]
TEMP = ROOT / ".test-tmp"
TEMP.mkdir(exist_ok=True)


class SentCASUncertainTests(unittest.TestCase):
    def make_queue(self, root):
        db = Database(root / "radar.db")
        event = db.upsert_candidate(
            Candidate("h18", "rss", "Synthetic offer", "https://vendor.example/h18")
        ).event_id
        queue = NotificationQueue(db)
        self.assertTrue(queue.enqueue(event, "", "telegram", "synthetic notification"))
        return db, event, queue

    def test_external_sent_state_wins_over_older_sender_completion(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as td:
            db, event, queue = self.make_queue(Path(td))
            calls = []
            def sender(_message):
                calls.append(1)
                with db.connect() as conn:
                    conn.execute(
                        "UPDATE notifications SET result='SENT' WHERE event_id=?",
                        (event,))
                return "SENT"
            result = queue.flush({"telegram_send_enabled": True},
                                 sender=sender, retry_seconds=0)
            self.assertEqual(calls, [1])
            self.assertEqual(result.get("uncertain"), 1)
            self.assertEqual(result["sent"], 0)
            self.assertEqual(result["retry"], 0)
            with db.connect() as conn:
                self.assertEqual(
                    conn.execute(
                        "SELECT result FROM notifications WHERE event_id=?",
                        (event,)).fetchone()[0], "SENT")
            self.assertFalse(queue.enqueue(
                event, "", "telegram", "must not requeue delivered notice"))

    def test_payload_replacement_blocks_stale_success_cas(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as td:
            db, event, queue = self.make_queue(Path(td))
            def sender(_message):
                with db.connect() as conn:
                    conn.execute(
                        "UPDATE notifications SET payload='replacement' WHERE event_id=?",
                        (event,))
                return "SENT"
            result = queue.flush({"telegram_send_enabled": True},
                                 sender=sender, retry_seconds=0)
            self.assertEqual(result.get("uncertain"), 1)
            self.assertEqual(result["sent"], 0)
            with db.connect() as conn:
                row = conn.execute(
                    "SELECT result,payload FROM notifications WHERE event_id=?",
                    (event,)).fetchone()
                self.assertEqual(row["result"], "CLAIMED")
                self.assertEqual(row["payload"], "replacement")


if __name__ == "__main__":
    unittest.main()
