"""R2-008: HTTP 429 must respect server cooldown and preserve a durable retry.

Synthetic HTTPError only: no real Telegram, secrets, or network.
"""
import tempfile
import urllib.error
import unittest
from pathlib import Path
from unittest.mock import patch

from core.db import Database
from core.models import Candidate
from core.notify import NotificationQueue


class RateLimitRecoveryTests(unittest.TestCase):
    def test_http_429_retry_after_survives_restart_and_is_not_retried_early(self):
        with tempfile.TemporaryDirectory(prefix="wr-rate-limited-") as td:
            path = Path(td) / "outbox.db"
            db = Database(path)
            event = db.upsert_candidate(Candidate(
                "local", "synthetic", "429 response", "https://example.test/429"
            )).event_id
            queue = NotificationQueue(db)
            self.assertTrue(queue.enqueue(event, "", "telegram", "synthetic"))
            calls = []
            def throttled(_message):
                calls.append("429")
                raise urllib.error.HTTPError(
                    "https://example.test/telegram", 429, "Too Many Requests",
                    {"Retry-After": "120"}, None)
            with patch("core.notify.time.time", return_value=30000.0):
                result = queue.flush({"telegram_send_enabled": True},
                                     sender=throttled, retry_seconds=5)
            self.assertEqual(result["retry"], 1)
            self.assertEqual(calls, ["429"])
            with db.connect() as conn:
                row = dict(conn.execute("SELECT * FROM notifications").fetchone())
            self.assertEqual(row["result"], "RETRY")
            self.assertEqual(row["next_attempt"], 30120.0)
            self.assertEqual(row["attempts"], 1)
            self.assertNotIn("Too Many Requests", repr(row))

            restarted = NotificationQueue(Database(path))
            with patch("core.notify.time.time", return_value=30119.0):
                restarted.flush({"telegram_send_enabled": True}, sender=throttled)
            self.assertEqual(calls, ["429"])
            with patch("core.notify.time.time", return_value=30121.0):
                status = restarted.flush({"telegram_send_enabled": True},
                    sender=lambda _: "SENT")
            self.assertEqual(status["sent"], 1)
            with db.connect() as conn:
                row = dict(conn.execute("SELECT * FROM notifications").fetchone())
            self.assertEqual((row["result"], row["attempts"]), ("SENT", 2))

    def test_ordinary_disconnection_keeps_uncertain_delivery_state(self):
        with tempfile.TemporaryDirectory(prefix="wr-offline-") as td:
            db = Database(Path(td) / "outbox.db")
            event = db.upsert_candidate(Candidate(
                "local", "synthetic", "offline", "https://example.test/offline"
            )).event_id
            queue = NotificationQueue(db)
            self.assertTrue(queue.enqueue(event, "", "telegram", "synthetic"))
            status = queue.flush({"telegram_send_enabled": True},
                sender=lambda _: (_ for _ in ()).throw(ConnectionError("SECRET_MARKER")))
            self.assertEqual(status.get("uncertain"), 1)
            with db.connect() as conn:
                row = dict(conn.execute("SELECT * FROM notifications").fetchone())
            self.assertEqual(row["result"], "UNCERTAIN")
            self.assertNotIn("SECRET_MARKER", repr(row))


if __name__ == "__main__":
    unittest.main()
