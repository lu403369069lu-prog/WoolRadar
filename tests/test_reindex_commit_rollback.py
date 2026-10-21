"""Injected COMMIT failure must preserve original SQLite rows and recovery backup."""

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from core.db import Database
from core.models import Candidate


class ReindexCommitRollbackTests(unittest.TestCase):
    def test_failed_schema_commit_leaves_legacy_version_and_schema_untouched(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'legacy.db'
            with closing(sqlite3.connect(path)) as legacy:
                legacy.execute('CREATE TABLE existing_identity (value TEXT NOT NULL)')
                legacy.execute("INSERT INTO existing_identity VALUES ('keep')")
                legacy.commit()

            original_connect = sqlite3.connect
            failure_count = []

            class FailingSchemaCommit(sqlite3.Connection):
                def execute(self, sql, *args, **kwargs):
                    if sql == 'PRAGMA user_version=1':
                        self.version_published_in_transaction = True
                    return super().execute(sql, *args, **kwargs)

                def commit(self):
                    if getattr(self, 'version_published_in_transaction', False):
                        failure_count.append('before-schema-commit')
                        raise sqlite3.OperationalError('INJECTED_SCHEMA_COMMIT_FAILURE')
                    return super().commit()

            def injected_connect(database, *args, **kwargs):
                if Path(database) == path:
                    kwargs['factory'] = FailingSchemaCommit
                return original_connect(database, *args, **kwargs)

            with patch('core.db.sqlite3.connect', side_effect=injected_connect):
                with self.assertRaisesRegex(sqlite3.OperationalError,
                                            'INJECTED_SCHEMA_COMMIT_FAILURE'):
                    Database(path)

            self.assertEqual(failure_count, ['before-schema-commit'])
            with closing(sqlite3.connect(path)) as legacy:
                self.assertEqual(legacy.execute('PRAGMA user_version').fetchone()[0], 0)
                self.assertIsNone(legacy.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='events'").fetchone())
                self.assertEqual(legacy.execute('SELECT value FROM existing_identity').fetchone()[0], 'keep')
                self.assertEqual(legacy.execute('PRAGMA integrity_check').fetchone()[0], 'ok')

            Database(path)
            with closing(sqlite3.connect(path)) as upgraded:
                self.assertEqual(upgraded.execute('PRAGMA user_version').fetchone()[0], 1)
                self.assertEqual(upgraded.execute('SELECT value FROM existing_identity').fetchone()[0], 'keep')

    def test_failed_final_commit_rolls_back_reindex_and_keeps_restorable_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'events.db'
            db = Database(path)
            event_id = db.upsert_candidate(Candidate(
                'synthetic', 'synthetic', 'Temporary Credit Campaign',
                'https://example.test/credit')).event_id
            with db.connect() as conn:
                conn.execute('UPDATE events SET canonical_key=? WHERE id=?',
                             ('legacy-reindex-key', event_id))

            original_connect = sqlite3.connect
            injection_count = []

            class FailingCommit(sqlite3.Connection):
                def execute(self, sql, *args, **kwargs):
                    if 'UPDATE events SET canonical_key=' in sql:
                        self.reindex_mutated = True
                    return super().execute(sql, *args, **kwargs)

                def commit(self):
                    if getattr(self, 'reindex_mutated', False):
                        injection_count.append('before-final-commit')
                        raise sqlite3.OperationalError('INJECTED_REINDEX_COMMIT_FAILURE')
                    return super().commit()

            def injected_connect(database, *args, **kwargs):
                if Path(database) == path:
                    kwargs['factory'] = FailingCommit
                return original_connect(database, *args, **kwargs)

            with patch('core.db.sqlite3.connect', side_effect=injected_connect):
                with self.assertRaisesRegex(sqlite3.OperationalError,
                                            'INJECTED_REINDEX_COMMIT_FAILURE'):
                    db.reindex()

            self.assertEqual(injection_count, ['before-final-commit'])
            backups = list(path.parent.glob('events-before-reindex-*.db'))
            self.assertEqual(len(backups), 1, 'one validated pre-reindex recovery point')
            self.assertEqual(list(path.parent.glob('events-before-reindex-*.tmp')), [])

            with closing(sqlite3.connect(path)) as original, closing(sqlite3.connect(backups[0])) as recovery:
                for connection in (original, recovery):
                    self.assertEqual(connection.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
                    self.assertEqual(connection.execute('PRAGMA foreign_key_check').fetchall(), [])
                    self.assertEqual(connection.execute(
                        'SELECT canonical_key FROM events WHERE id=?', (event_id,)).fetchone()[0],
                        'legacy-reindex-key')
                self.assertEqual(original.execute('SELECT COUNT(*) FROM events').fetchone()[0],
                                 recovery.execute('SELECT COUNT(*) FROM events').fetchone()[0])

            # The failed transaction releases its writer lock: a subsequent clean
            # migration can safely complete from the original unmodified state.
            result = db.reindex()
            self.assertTrue(Path(result['backup']).is_file())
            self.assertNotEqual(db.get_event(event_id)['canonical_key'], 'legacy-reindex-key')


if __name__ == '__main__':
    unittest.main()
