"""R2-003: retry delay/attempt history survives a fresh process-like DB reopening.

Synthetic SQLite only; sender callback never makes network requests.
"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.db import Database
from core.models import Candidate
from core.notify import NotificationQueue


class RestartRetryTests(unittest.TestCase):
    def test_retry_deadline_and_attempts_survive_new_queue_instance(self):
        with tempfile.TemporaryDirectory(prefix="wr-retry-resume-") as td:
            path = Path(td) / "outbox.db"
            db = Database(path)
            event = db.upsert_candidate(Candidate(
                "local", "synthetic", "Retry", "https://example.test/backoff"
            )).event_id
            first = NotificationQueue(db)
            self.assertTrue(first.enqueue(event, "batch-a", "telegram", "synthetic message"))
            sent_messages = []
            with patch("core.notify.time.time", return_value=10000.0):
                report = first.flush({"telegram_send_enabled": True},
                                     sender=lambda s: sent_messages.append(s) or "FAILED",
                                     retry_seconds=60)
            self.assertEqual(report["retry"], 1)
            self.assertEqual(sent_messages, ["synthetic message"])
            with db.connect() as conn:
                row = conn.execute("SELECT result,attempts,next_attempt FROM notifications").fetchone()
                self.assertEqual((row["result"], row["attempts"], row["next_attempt"]),
                                 ("RETRY", 1, 10060.0))

            # Discard the original Database and Queue: all recovery information
            # must live on disk, not in a cached Python object.
            fresh = NotificationQueue(Database(path))
            suppressed = []
            with patch("core.notify.time.time", return_value=10059.0):
                report = fresh.flush({"telegram_send_enabled": True},
                                     sender=lambda s: suppressed.append(s) or "SENT")
            self.assertEqual(report, {"sent": 0, "retry": 0, "local": 0})
            self.assertEqual(suppressed, [])
            with patch("core.notify.time.time", return_value=10061.0):
                report = fresh.flush({"telegram_send_enabled": True},
                                     sender=lambda s: "SENT")
            self.assertEqual(report["sent"], 1)
            with Database(path).connect() as conn:
                row = conn.execute("SELECT result,attempts,next_attempt FROM notifications").fetchone()
                self.assertEqual((row["result"], row["attempts"], row["next_attempt"]),
                                 ("SENT", 2, 0.0))
            self.assertFalse(NotificationQueue(Database(path)).enqueue(
                event, "batch-a", "telegram", "already-delivered"))


if __name__ == "__main__":
    unittest.main()
