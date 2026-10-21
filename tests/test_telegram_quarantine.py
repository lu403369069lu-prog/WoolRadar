"""W1 external ambiguity guard. All sends are synthetic and use disposable SQLite."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.db import Database
from core.models import Candidate
from core.notify import NotificationQueue, TelegramRateLimited


class TelegramQuarantineTests(unittest.TestCase):
    def make(self, folder):
        db = Database(Path(folder) / "outbox.db")
        event = db.upsert_candidate(Candidate("local", "synthetic", "Guard", "https://example.test/guard")).event_id
        q = NotificationQueue(db)
        self.assertTrue(q.enqueue(event, "batch", "telegram", "safe"))
        return db, q

    def test_timeout_is_quarantined_without_auto_resend_across_restart(self):
        with tempfile.TemporaryDirectory() as td:
            db, q = self.make(td)
            calls = []
            def uncertain(message):
                calls.append(message)
                raise TimeoutError("PRIVATE_CANARY")
            with patch("core.notify.time.time", return_value=20000.0):
                first = q.flush({"telegram_send_enabled": True}, sender=uncertain, retry_seconds=1)
            self.assertEqual(first.get("uncertain"), 1)
            with db.connect() as conn:
                row = dict(conn.execute("SELECT * FROM notifications").fetchone())
            self.assertEqual(row["result"], "UNCERTAIN")
            self.assertNotIn("PRIVATE_CANARY", repr(row))
            with patch("core.notify.time.time", return_value=90000.0):
                second = NotificationQueue(Database(db.path)).flush(
                    {"telegram_send_enabled": True}, sender=lambda m: calls.append(m) or "SENT")
            self.assertEqual(calls, ["safe"])
            self.assertEqual(second["sent"], 0)
            with db.connect() as conn:
                self.assertEqual(conn.execute("SELECT result,attempts FROM notifications").fetchone()[:],
                                 ("UNCERTAIN", 1))

    def test_lease_expiry_does_not_takeover_possible_external_send(self):
        with tempfile.TemporaryDirectory() as td:
            db, q = self.make(td)
            with db.connect() as conn:
                conn.execute("UPDATE notifications SET result='CLAIMED',attempts=1,next_attempt=1")
            sends = []
            with patch("core.notify.time.time", return_value=50000.0):
                summary = NotificationQueue(Database(db.path)).flush(
                    {"telegram_send_enabled": True},
                    sender=lambda msg: sends.append(msg) or "SENT")
            self.assertEqual(sends, [])
            self.assertEqual(summary["sent"], 0)
            with db.connect() as conn:
                self.assertEqual(conn.execute("SELECT result,attempts FROM notifications").fetchone()[:],
                                 ("CLAIMED", 1))

    def test_callback_failed_is_ambiguous_but_definite_429_remains_retryable(self):
        with tempfile.TemporaryDirectory() as td:
            db, q = self.make(td)
            r = q.flush({"telegram_send_enabled": True}, sender=lambda _: "FAILED", retry_seconds=0)
            self.assertEqual(r.get("uncertain"), 1)
            with db.connect() as conn:
                self.assertEqual(conn.execute("SELECT result FROM notifications").fetchone()[0], "UNCERTAIN")
        with tempfile.TemporaryDirectory() as td:
            db, q = self.make(td)
            with patch("core.notify.time.time", return_value=30000.0):
                r = q.flush({"telegram_send_enabled": True},
                            sender=lambda _: (_ for _ in ()).throw(TelegramRateLimited(90)),
                            retry_seconds=5)
            self.assertEqual(r["retry"], 1)
            with db.connect() as conn:
                self.assertEqual(conn.execute("SELECT result,next_attempt FROM notifications").fetchone()[:],
                                 ("RETRY", 30090.0))


if __name__ == "__main__":
    unittest.main()
