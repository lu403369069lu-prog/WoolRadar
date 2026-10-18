"""R2-001: SENT outbox delivery is monotonic across independent SQLite connections.

This test uses only disposable SQLite storage and local notification files.
It never opens the network, accesses a real token, or changes production.
"""
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from core.db import Database
from core.models import Candidate
from core.notify import NotificationQueue


class SentMonotonicTests(unittest.TestCase):
    def test_sent_cannot_be_requeued_by_second_sqlite_connection(self):
        with tempfile.TemporaryDirectory(prefix="wr-sent-final-") as tmp:
            root = Path(tmp)
            db = Database(root / "outbox.db")
            event = db.upsert_candidate(Candidate(
                "local", "synthetic", "Receipt", "https://example.test/receipt"
            )).event_id
            queue = NotificationQueue(db)
            self.assertTrue(queue.enqueue(event, "", "local", "validated message"))
            self.assertEqual(queue.flush({}, local_dir=root / "outbox")["local"], 1)
            with db.connect() as conn:
                self.assertEqual(conn.execute("SELECT result FROM notifications").fetchone()[0], "SENT")
                with self.assertRaisesRegex(sqlite3.IntegrityError, "SENT_FINAL"):
                    conn.execute("UPDATE notifications SET result='RETRY',next_attempt=0 "
                                 "WHERE event_id=?", (event,))
            self.assertFalse(NotificationQueue(Database(db.path)).enqueue(
                event, "", "local", "duplicate"))
            self.assertEqual(len(list((root / "outbox").glob("notification-*.json"))), 1)

    def test_sent_cannot_downgrade_across_real_process(self):
        with tempfile.TemporaryDirectory(prefix="wr-sent-proc-") as tmp:
            root = Path(tmp)
            db = Database(root / "outbox.db")
            event = db.upsert_candidate(Candidate(
                "local", "synthetic", "Receipt", "https://example.test/process"
            )).event_id
            q = NotificationQueue(db)
            self.assertTrue(q.enqueue(event, "", "local", "confirmed"))
            self.assertEqual(q.flush({}, local_dir=root / "outbox")["local"], 1)
            code = (
                "import sqlite3,sys\n"
                "c=sqlite3.connect(sys.argv[1])\n"
                "try:\n"
                " c.execute(\"UPDATE notifications SET result='PENDING' WHERE result='SENT'\")\n"
                " c.commit()\n"
                " sys.exit(9)\n"
                "except sqlite3.IntegrityError as e:\n"
                " assert 'SENT_FINAL' in str(e), str(e)\n"
                " sys.exit(0)\n"
                "finally:\n"
                " c.close()\n"
            )
            proc = subprocess.run(
                [sys.executable, "-c", code, str(db.path)],
                capture_output=True, text=True, timeout=20, check=False)
            self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
            with db.connect() as conn:
                self.assertEqual(conn.execute("SELECT result FROM notifications").fetchone()[0], "SENT")


if __name__ == "__main__":
    unittest.main()
