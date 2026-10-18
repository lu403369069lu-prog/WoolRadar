"""A failed schema upgrade must leave the pre-upgrade database intact."""

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from core.db import Database


ROOT = Path(__file__).parents[1]


class SchemaMigrationAtomicTests(unittest.TestCase):
    def test_failed_legacy_column_upgrade_rolls_back_and_retry_preserves_rows(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as folder:
            path = Path(folder) / 'historical.sqlite'
            with closing(sqlite3.connect(path)) as conn:
                conn.execute('''CREATE TABLE notifications (
                    id INTEGER PRIMARY KEY, event_id INTEGER, batch_id TEXT NOT NULL,
                    channel TEXT NOT NULL, created_at TEXT NOT NULL,
                    result TEXT NOT NULL, UNIQUE(event_id, batch_id, channel))''')
                conn.execute('''INSERT INTO notifications
                    (event_id,batch_id,channel,created_at,result)
                    VALUES (NULL,'batch','telegram','now','pending')''')
                conn.commit()

            original_connect = sqlite3.connect

            class InterruptedMigration(sqlite3.Connection):
                def execute(self, sql, *args, **kwargs):
                    if sql.strip().upper().startswith('ALTER TABLE NOTIFICATIONS ADD COLUMN ATTEMPTS'):
                        raise sqlite3.OperationalError('INJECTED_SCHEMA_MIGRATION_FAILURE')
                    return super().execute(sql, *args, **kwargs)

            def connect_with_failure(*args, **kwargs):
                return original_connect(*args, **kwargs, factory=InterruptedMigration)

            with patch('core.db.sqlite3.connect', side_effect=connect_with_failure):
                with self.assertRaisesRegex(sqlite3.OperationalError, 'INJECTED_SCHEMA_MIGRATION_FAILURE'):
                    Database(path)

            with closing(sqlite3.connect(path)) as conn:
                columns = {row[1] for row in conn.execute('PRAGMA table_info(notifications)')}
                self.assertNotIn('payload', columns, 'failed migration committed a partial schema')
                self.assertNotIn('attempts', columns)
                self.assertNotIn('next_attempt', columns)
                self.assertEqual(conn.execute('SELECT batch_id FROM notifications').fetchone()[0], 'batch')
                self.assertEqual(conn.execute('PRAGMA integrity_check').fetchone()[0], 'ok')

            Database(path)
            with closing(sqlite3.connect(path)) as conn:
                columns = {row[1] for row in conn.execute('PRAGMA table_info(notifications)')}
                self.assertTrue({'payload', 'attempts', 'next_attempt'} <= columns)
                self.assertEqual(conn.execute('SELECT batch_id FROM notifications').fetchone()[0], 'batch')
                self.assertEqual(conn.execute('PRAGMA integrity_check').fetchone()[0], 'ok')


if __name__ == '__main__':
    unittest.main()
