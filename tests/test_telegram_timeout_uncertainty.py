"""R2-002: an ambiguous Telegram timeout cannot become a definite failed/SENT receipt.

This uses a synthetic sender and a disposable SQLite database; no real network call.
"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.db import Database
from core.models import Candidate
from core.notify import NotificationQueue


class UnknownDeliveryTests(unittest.TestCase):
    def test_timeout_is_durably_uncertain_and_retry_remains_at_least_once(self):
        with tempfile.TemporaryDirectory(prefix="wr-unknown-send-") as td:
            path = Path(td) / "store.db"
            db = Database(path)
            event = db.upsert_candidate(Candidate(
                "local", "synthetic", "Unknown send", "https://example.test/unknown"
            )).event_id
            q = NotificationQueue(db)
            self.assertTrue(q.enqueue(event, "", "telegram", "synthetic body"))
            with patch("core.notify.time.time", return_value=20000.0):
                report = q.flush({"telegram_send_enabled": True},
                    sender=lambda _text: (_ for _ in ()).throw(
                        TimeoutError("synthetic_time_out__never_store_me")),
                    retry_seconds=60)
            self.assertEqual(report.get("uncertain"), 1)
            self.assertEqual(report["sent"], 0)
            with db.connect() as conn:
                row = dict(conn.execute("SELECT * FROM notifications").fetchone())
            self.assertEqual(row["result"], "UNCERTAIN")
            self.assertEqual(row["attempts"], 1)
            self.assertEqual(row["next_attempt"], 20060.0)
            self.assertNotIn("synthetic_time_out__never_store_me", repr(row))

            # A fresh process-like instance must retain uncertainty and delay.
            restarted = NotificationQueue(Database(path))
            self.assertEqual(len(restarted.pending()), 1)
            sends = []
            with patch("core.notify.time.time", return_value=20059.0):
                restarted.flush({"telegram_send_enabled": True},
                    sender=lambda message: sends.append(message) or "SENT")
            self.assertEqual(sends, [])
            with patch("core.notify.time.time", return_value=20061.0):
                result = restarted.flush({"telegram_send_enabled": True},
                    sender=lambda message: sends.append(message) or "SENT")
            self.assertEqual(sends, ["synthetic body"])
            self.assertEqual(result["sent"], 1)
            with Database(path).connect() as conn:
                row = dict(conn.execute("SELECT * FROM notifications").fetchone())
            self.assertEqual((row["result"], row["attempts"]), ("SENT", 2))


if __name__ == "__main__":
    unittest.main()
