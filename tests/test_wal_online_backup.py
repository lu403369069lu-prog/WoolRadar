"""R2-011 / R2-012: online WAL backup contains committed uncheckpointed records
and can be restored as a standalone consistent SQLite database.

All input and output are temporary synthetic fixtures.
"""
import shutil
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from core.db import Database
from core.models import Candidate, Evidence
from core.notify import NotificationQueue


TABLES = ("events", "sightings", "evidence", "status_history",
          "notifications", "node_runs", "node_health", "campaign_links")


def snapshot(conn):
    return {
        name: [tuple(row) for row in conn.execute(
            "SELECT * FROM " + name + " ORDER BY rowid").fetchall()]
        for name in TABLES
    }


class OnlineWalBackupTests(unittest.TestCase):
    def test_backup_includes_uncheckpointed_wal_rows_while_reader_pinned(self):
        with tempfile.TemporaryDirectory(prefix="wr-wal-backup-") as td:
            path = Path(td) / "source.db"
            db = Database(path)
            with closing(sqlite3.connect(path, isolation_level=None)) as pinned:
                pinned.execute("PRAGMA journal_mode=WAL")
                pinned.execute("BEGIN")
                pinned.execute("SELECT COUNT(*) FROM events").fetchone()
                event = db.upsert_candidate(Candidate(
                    "local", "synthetic", "Committed in WAL",
                    "https://example.test/wal")).event_id
                db.add_evidence(event, Evidence(
                    "official", "https://example.test/wal", "synthetic",
                    claims={"public": True, "open": True}))
                self.assertTrue(NotificationQueue(db).enqueue(
                    event, "", "local", "from uncheckpointed WAL"))
                wal = Path(str(path) + "-wal")
                self.assertTrue(wal.is_file(), "No WAL file to prove online backup")
                self.assertGreater(wal.stat().st_size, 0)
                backup = Path(db.reindex()["backup"])
                self.assertTrue(backup.is_file())
                with closing(sqlite3.connect(backup)) as copy:
                    self.assertEqual(copy.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                    self.assertEqual(copy.execute(
                        "SELECT title FROM events WHERE id=?", (event,)).fetchone()[0],
                        "Committed in WAL")
                    self.assertEqual(copy.execute(
                        "SELECT COUNT(*) FROM evidence WHERE event_id=?", (event,)).fetchone()[0], 1)
                    self.assertEqual(copy.execute(
                        "SELECT COUNT(*) FROM notifications WHERE event_id=?", (event,)).fetchone()[0], 1)
                pinned.execute("ROLLBACK")

    def test_backup_restores_independently_with_same_rows_and_no_broken_fk(self):
        with tempfile.TemporaryDirectory(prefix="wr-wal-restore-") as td:
            root = Path(td)
            path = root / "source.db"
            db = Database(path)
            event = db.upsert_candidate(Candidate(
                "local", "synthetic", "Restorable",
                "https://example.test/restore")).event_id
            db.add_evidence(event, Evidence(
                "official", "https://example.test/restore", "synthetic",
                claims={"public": True}))
            self.assertTrue(NotificationQueue(db).enqueue(
                event, "", "local", "restore me"))
            db.record_node_run("local", "OK", items=1)
            with db.connect() as conn:
                expected = snapshot(conn)
            backup = Path(db.reindex()["backup"])
            restored = root / "restored.db"
            shutil.copy2(backup, restored)
            with closing(sqlite3.connect(restored)) as copy:
                copy.execute("PRAGMA foreign_keys=ON")
                self.assertEqual(copy.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                self.assertEqual(copy.execute("PRAGMA foreign_key_check").fetchall(), [])
                self.assertEqual(snapshot(copy), expected)
                self.assertGreater(len(snapshot(copy)["events"]), 0)


if __name__ == "__main__":
    unittest.main()
