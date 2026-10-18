"""R2-013: an incompatible newer SQLite schema must fail closed, without writes.

All databases are synthetic disposable fixtures, never user/production data.
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from core.db import Database


class SchemaVersionGuardTests(unittest.TestCase):
    def test_future_database_version_rejected_before_schema_mutation(self):
        with tempfile.TemporaryDirectory(prefix="wr-schema-future-") as td:
            path = Path(td) / "future.db"
            with sqlite3.connect(path) as conn:
                conn.execute("CREATE TABLE sentinel (id INTEGER PRIMARY KEY, payload TEXT)")
                conn.execute("INSERT INTO sentinel(payload) VALUES ('preserve')")
                conn.execute("PRAGMA user_version=999")
            with sqlite3.connect(path) as conn:
                before = conn.execute("SELECT name,sql FROM sqlite_master ORDER BY name").fetchall()
                self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 999)
            with self.assertRaisesRegex(RuntimeError, "UNSUPPORTED_DATABASE_SCHEMA_VERSION"):
                Database(path)
            with sqlite3.connect(path) as conn:
                self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 999)
                self.assertEqual(conn.execute("SELECT payload FROM sentinel").fetchone()[0], "preserve")
                after = conn.execute("SELECT name,sql FROM sqlite_master ORDER BY name").fetchall()
                self.assertEqual(after, before)
                self.assertIsNone(conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='events'").fetchone())

    def test_legacy_zero_version_can_upgrade_once_and_reopen(self):
        with tempfile.TemporaryDirectory(prefix="wr-schema-legacy-") as td:
            path = Path(td) / "legacy.db"
            with sqlite3.connect(path) as conn:
                conn.execute("CREATE TABLE historical_marker (name TEXT NOT NULL)")
                conn.execute("INSERT INTO historical_marker VALUES ('preserved')")
                self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 0)
            Database(path)
            with sqlite3.connect(path) as conn:
                self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 1)
                self.assertEqual(conn.execute(
                    "SELECT name FROM historical_marker").fetchone()[0], "preserved")
                self.assertIsNotNone(conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='events'").fetchone())
            Database(path)
            with sqlite3.connect(path) as conn:
                self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
