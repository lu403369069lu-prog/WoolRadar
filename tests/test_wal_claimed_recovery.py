"""WR-H03: include committed WAL notices in recoverable reindex snapshots.

Only disposable synthetic SQLite files; never restore over a production DB.
"""
import sqlite3
import tempfile
import unittest
from contextlib import closing, ExitStack
from pathlib import Path

from core.db import Database
from core.models import Candidate
from core.notify import NotificationQueue

TEST_ROOT = Path(__file__).resolve().parents[1] / ".test-tmp"
TEST_ROOT.mkdir(exist_ok=True)


class WALClaimedBackupTests(unittest.TestCase):
    def make_claimed_wal(self, root):
        db = Database(root / "radar.db")
        event = db.upsert_candidate(
            Candidate("walcase", "synthetic", "Free storage", "https://vendor.example/wal")
        ).event_id
        queue = NotificationQueue(db)
        self.assertTrue(queue.enqueue(event, "", "telegram", "synthetic WAL notice"))
        writer = sqlite3.connect(db.path)
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("PRAGMA wal_autocheckpoint=0")
        writer.execute("UPDATE notifications SET result='CLAIMED',attempts=3,"
                       "next_attempt=9999999999 WHERE event_id=?", (event,))
        writer.commit()
        self.assertTrue(Path(str(db.path) + "-wal").exists(),
                        "Expected a live WAL sidecar before SQLite backup")
        return db, event, writer

    def test_live_wal_claim_and_lease_included_in_reindex_backup(self):
        with ExitStack() as stack:
            td = stack.enter_context(tempfile.TemporaryDirectory(dir=TEST_ROOT))
            db, event, writer = self.make_claimed_wal(Path(td))
            stack.callback(writer.close)
            report = db.reindex()
            self.assertEqual(report["merged"], 0)
            backup = Path(report["backup"])
            self.assertTrue(backup.is_file())
            with closing(sqlite3.connect(backup)) as archive:
                record = archive.execute(
                    "SELECT result,attempts,next_attempt FROM notifications "
                    "WHERE event_id=?", (event,)).fetchone()
                self.assertEqual(record, ("CLAIMED", 3, 9999999999))
                self.assertEqual(archive.execute(
                    "PRAGMA foreign_key_check").fetchall(), [])
            with db.connect() as current:
                record = current.execute(
                    "SELECT result,attempts,next_attempt FROM notifications "
                    "WHERE event_id=?", (event,)).fetchone()
                self.assertEqual(tuple(record), ("CLAIMED", 3, 9999999999))

    def test_restored_backup_preserves_claim_and_blocks_duplicate_send(self):
        with ExitStack() as stack:
            root = Path(stack.enter_context(tempfile.TemporaryDirectory(dir=TEST_ROOT)))
            db, event, writer = self.make_claimed_wal(root)
            stack.callback(writer.close)
            backup = Path(db.reindex()["backup"])
            restored_path = root / "restored.db"
            with closing(sqlite3.connect(backup)) as source:
                with closing(sqlite3.connect(restored_path)) as target:
                    source.backup(target)
            restored = Database(restored_path)
            sends = []
            outcome = NotificationQueue(restored).flush(
                {"telegram_send_enabled": True},
                sender=lambda payload: sends.append(payload) or "SENT", retry_seconds=0)
            self.assertEqual(sends, [])
            self.assertEqual(outcome["sent"], 0)
            self.assertEqual(outcome["retry"], 0)
            with restored.connect() as conn:
                record = conn.execute(
                    "SELECT result,attempts,next_attempt FROM notifications "
                    "WHERE event_id=?", (event,)).fetchone()
                self.assertEqual(tuple(record), ("CLAIMED", 3, 9999999999))


if __name__ == "__main__":
    unittest.main()
