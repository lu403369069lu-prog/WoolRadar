"""A previously opened Database must not mutate a future-version SQLite file."""

import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from contextlib import closing
from pathlib import Path

from core.db import Database


class StaleSchemaVersionTests(unittest.TestCase):
    def test_external_process_migration_wins_writer_lock(self):
        """The stale writer must recheck after a separate process commits v2."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "isolated.db"
            started, release = Path(folder) / 'started', Path(folder) / 'release'
            database = Database(path)
            child = '''import sqlite3,sys,time
from pathlib import Path
db,started,release = map(Path,sys.argv[1:])
with sqlite3.connect(db,timeout=10) as conn:
    conn.execute('BEGIN IMMEDIATE')
    conn.execute('PRAGMA user_version=2')
    started.write_text('locked',encoding='utf-8')
    until=time.monotonic()+10
    while not release.exists() and time.monotonic()<until: time.sleep(.01)
    if not release.exists(): raise RuntimeError('test release timed out')
'''
            process = subprocess.Popen(
                [sys.executable, '-B', '-c', child, str(path), str(started), str(release)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                deadline = time.monotonic() + 8
                while not started.exists() and process.poll() is None and time.monotonic() < deadline:
                    time.sleep(.01)
                self.assertTrue(started.exists(), 'migration process failed to acquire SQLite writer lock')

                finished = threading.Event()
                results = []
                def old_writer():
                    try:
                        database.record_node_run('synthetic', 'SUCCESS', 1)
                    except BaseException as exc:
                        results.append(exc)
                    finally:
                        finished.set()

                worker = threading.Thread(target=old_writer)
                worker.start()
                try:
                    self.assertFalse(finished.wait(.12), 'stale writer bypassed the competing process')
                finally:
                    release.write_text('continue', encoding='utf-8')
                stdout, stderr = process.communicate(timeout=10)
                self.assertEqual(process.returncode, 0, (stdout, stderr))
                self.assertTrue(finished.wait(10), 'stale writer did not unblock')
                self.assertEqual(len(results), 1)
                self.assertIsInstance(results[0], RuntimeError)
                self.assertEqual(str(results[0]), 'UNSUPPORTED_DATABASE_SCHEMA_VERSION')
                with closing(sqlite3.connect(path)) as check:
                    self.assertEqual(check.execute('PRAGMA user_version').fetchone()[0], 2)
                    self.assertEqual(check.execute('SELECT COUNT(*) FROM node_runs').fetchone()[0], 0)
            finally:
                release.write_text('continue', encoding='utf-8')
                if process.poll() is None:
                    try:
                        process.communicate(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.communicate()

    def test_stale_database_object_rejects_writes_after_external_upgrade(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "isolated.db"
            database = Database(path)
            with closing(sqlite3.connect(path)) as external:
                external.execute("PRAGMA user_version=2")
                external.commit()

            with self.assertRaisesRegex(RuntimeError, "UNSUPPORTED_DATABASE_SCHEMA_VERSION"):
                database.record_node_run("synthetic", "SUCCESS", 1)
            with self.assertRaisesRegex(RuntimeError, "UNSUPPORTED_DATABASE_SCHEMA_VERSION"):
                with database.candidate_transaction():
                    pass

            with closing(sqlite3.connect(path)) as check:
                self.assertEqual(check.execute("PRAGMA user_version").fetchone()[0], 2)
                self.assertEqual(check.execute("SELECT COUNT(*) FROM node_runs").fetchone()[0], 0)

    def test_new_object_still_rejects_future_schema(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "isolated.db"
            Database(path)
            with closing(sqlite3.connect(path)) as external:
                external.execute("PRAGMA user_version=2")
                external.commit()
            with self.assertRaisesRegex(RuntimeError, "UNSUPPORTED_DATABASE_SCHEMA_VERSION"):
                Database(path)


if __name__ == "__main__":
    unittest.main()
