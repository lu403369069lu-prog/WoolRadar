"""W1: an expired local-delivery worker may not overwrite its successor's receipt.

Only disposable synthetic SQLite files; no Telegram send or production target.
"""
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from core.db import Database
from core.models import Candidate
from core.notify import NotificationQueue


class StaleLocalNotificationWriterTests(unittest.TestCase):
    def test_expired_worker_cannot_replace_newer_committed_receipt(self):
        with tempfile.TemporaryDirectory(prefix="wr-w1-local-") as td:
            root = Path(td)
            db = Database(root / "notifications.db")
            event = db.upsert_candidate(Candidate(
                "local", "synthetic", "Local notice", "https://example.test/notice",
            )).event_id
            queue = NotificationQueue(db)
            self.assertTrue(queue.enqueue(event, "", "local", "newer valid content"))
            outbox = root / "outbox"
            claimed_before_write = threading.Event()
            release_old = threading.Event()
            original_write_text = Path.write_text
            old_summary = []
            old_errors = []

            def controlled_write(target, text, *args, **kwargs):
                if (threading.current_thread().name == "stale-local-worker"
                        and "notification-" in target.name and target.name.endswith(".tmp")):
                    claimed_before_write.set()
                    if not release_old.wait(timeout=20):
                        raise AssertionError("W1 successor did not release old writer")
                    # Simulate a stale writer that has obsolete/corrupt data.
                    data = json.loads(text)
                    data["message"] = "STALE_WRITER_MUST_NOT_REPLACE_VALID_RECEIPT"
                    text = json.dumps(data)
                return original_write_text(target, text, *args, **kwargs)

            def stale_flush():
                try:
                    old_summary.append(queue.flush({}, local_dir=outbox))
                except BaseException as exc:
                    old_errors.append(exc)

            with patch.object(Path, "write_text", controlled_write):
                stale = threading.Thread(target=stale_flush, name="stale-local-worker")
                stale.start()
                try:
                    self.assertTrue(claimed_before_write.wait(timeout=15),
                                    "W1 old worker never reached its claimed write")
                    # Expire the old claim; a new worker takes ownership and commits.
                    with db.connect() as conn:
                        conn.execute(
                            "UPDATE notifications SET next_attempt=0 "
                            "WHERE result='CLAIMED'"
                        )
                    successor = NotificationQueue(Database(db.path))
                    newer = successor.flush({}, local_dir=outbox)
                    self.assertEqual(newer["local"], 1)
                finally:
                    release_old.set()
                    stale.join(timeout=20)
                    self.assertFalse(stale.is_alive(), "W1 old worker remained blocked")

            self.assertEqual(old_errors, [], repr(old_errors))
            self.assertEqual(len(old_summary), 1)
            receipts = list(outbox.glob("notification-*.json"))
            self.assertEqual(len(receipts), 1)
            self.assertEqual(json.loads(receipts[0].read_text(encoding="utf-8"))["message"],
                             "newer valid content", "stale worker overwrote successor receipt")
            with db.connect() as conn:
                self.assertEqual(
                    conn.execute("SELECT result FROM notifications").fetchone()[0], "SENT")


if __name__ == "__main__":
    unittest.main()
