"""W3: the event state observed by the audit writer must be writer-reserved.

Runs only against temporary SQLite databases. Never opens the user's production db.
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.db import Database
from core.models import Candidate, Status


class ReservedStatusConnection(sqlite3.Connection):
    def execute(self, sql, parameters=()):
        if str(sql).lstrip().upper().startswith("SELECT STATUS FROM EVENTS") and not self.in_transaction:
            raise AssertionError("W3_STATUS_READ_WITHOUT_WRITER_RESERVATION")
        return super().execute(sql, parameters)


class CommitFailureConnection(sqlite3.Connection):
    def commit(self):
        raise sqlite3.OperationalError("W3_INJECTED_COMMIT_FAILURE")


class StatusAuditAtomicityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="wr-w3-audit-")
        self.db = Database(Path(self.temp.name) / "audit.db")
        self.event_id = self.db.upsert_candidate(
            Candidate("w3", "rss", "Audit candidate", "https://example.test/w3")
        ).event_id

    def tearDown(self):
        self.temp.cleanup()

    def test_status_history_read_occurs_under_writer_reservation(self):
        real_connect = sqlite3.connect

        def guarded(*args, **kwargs):
            return real_connect(*args, factory=ReservedStatusConnection, **kwargs)

        with patch("core.db.sqlite3.connect", side_effect=guarded):
            self.db.set_status(self.event_id, Status.CROSS_CHECKED, "verified")

        with self.db.connect() as conn:
            event = conn.execute("SELECT status FROM events WHERE id=?", (self.event_id,)).fetchone()
            audit = conn.execute(
                "SELECT old_status, new_status FROM status_history WHERE event_id=?", (self.event_id,)
            ).fetchall()
        self.assertEqual(event["status"], Status.CROSS_CHECKED.value)
        self.assertEqual([(a["old_status"], a["new_status"]) for a in audit],
                         [(Status.DISCOVERED.value, Status.CROSS_CHECKED.value)])

    def test_commit_failure_rolls_back_state_and_audit_together(self):
        real_connect = sqlite3.connect

        def broken_commit(*args, **kwargs):
            return real_connect(*args, factory=CommitFailureConnection, **kwargs)

        with patch("core.db.sqlite3.connect", side_effect=broken_commit):
            with self.assertRaisesRegex(sqlite3.OperationalError, "W3_INJECTED_COMMIT_FAILURE"):
                self.db.set_status(self.event_id, Status.OFFICIAL_VERIFIED, "injected")
        with self.db.connect() as conn:
            self.assertEqual(
                conn.execute("SELECT status FROM events WHERE id=?", (self.event_id,)).fetchone()[0],
                Status.DISCOVERED.value,
            )
            self.assertEqual(conn.execute(
                "SELECT COUNT(*) FROM status_history WHERE event_id=?", (self.event_id,)
            ).fetchone()[0], 0)

    def test_nested_candidate_transaction_remains_atomic(self):
        with self.assertRaisesRegex(RuntimeError, "INJECTED_OUTER_FAILURE"):
            with self.db.candidate_transaction():
                self.db.set_status(self.event_id, Status.CLAIMABLE, "inside outer txn")
                with self.db.connect() as conn:
                    self.assertEqual(conn.execute(
                        "SELECT COUNT(*) FROM status_history WHERE event_id=?", (self.event_id,)
                    ).fetchone()[0], 1)
                raise RuntimeError("INJECTED_OUTER_FAILURE")
        with self.db.connect() as conn:
            self.assertEqual(conn.execute(
                "SELECT status FROM events WHERE id=?", (self.event_id,)
            ).fetchone()[0], Status.DISCOVERED.value)
            self.assertEqual(conn.execute(
                "SELECT COUNT(*) FROM status_history WHERE event_id=?", (self.event_id,)
            ).fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
