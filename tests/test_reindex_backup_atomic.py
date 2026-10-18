"""A reindex backup must be complete and recoverable before it is published."""

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest import mock

from core.db import Database
from core.models import Candidate


class ReindexBackupAtomicTests(unittest.TestCase):
    def test_backup_failure_does_not_publish_corrupt_or_misleading_backup(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parents[1] / '.test-tmp') as folder:
            path = Path(folder) / 'events.db'
            db = Database(path)
            event_id = db.upsert_candidate(Candidate('node', 'forum', 'Free VM Offer',
                                                      'https://example.com/offer')).event_id
            real_connect = sqlite3.connect

            class InterruptedBackup(sqlite3.Connection):
                def backup(self, target, *args, **kwargs):
                    super().backup(target, *args, **kwargs)
                    raise OSError('INJECTED_BACKUP_INTERRUPTION')

            def connect_with_failure(database, *args, **kwargs):
                if Path(database) == path:
                    kwargs['factory'] = InterruptedBackup
                return real_connect(database, *args, **kwargs)

            with mock.patch('core.db.sqlite3.connect', side_effect=connect_with_failure):
                with self.assertRaisesRegex(OSError, 'INJECTED_BACKUP_INTERRUPTION'):
                    db.reindex()

            self.assertEqual(list(path.parent.glob('events-before-reindex-*.db')), [])
            self.assertEqual(list(path.parent.glob('events-before-reindex-*.tmp')), [])
            with db.connect() as conn:
                self.assertEqual(conn.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
                self.assertEqual(conn.execute('SELECT id FROM events').fetchone()[0], event_id)

    def test_backup_restores_pre_reindex_wal_commits(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parents[1] / '.test-tmp') as folder:
            path = Path(folder) / 'events.db'
            db = Database(path)
            event_id = db.upsert_candidate(Candidate('node', 'forum', 'Free VM Offer',
                                                      'https://example.com/offer')).event_id
            with db.connect() as conn:
                conn.execute('UPDATE events SET canonical_key=? WHERE id=?', ('legacy-key', event_id))
            result = db.reindex()
            backup = Path(result['backup'])
            self.assertTrue(backup.is_file())
            with closing(sqlite3.connect(backup)) as snapshot:
                self.assertEqual(snapshot.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
                self.assertEqual(snapshot.execute('SELECT canonical_key FROM events WHERE id=?',
                                                  (event_id,)).fetchone()[0], 'legacy-key')
                with closing(sqlite3.connect(Path(folder) / 'restored.db')) as restored:
                    snapshot.backup(restored)
                    self.assertEqual(restored.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
                    self.assertEqual(restored.execute('SELECT canonical_key FROM events WHERE id=?',
                                                      (event_id,)).fetchone()[0], 'legacy-key')
            self.assertNotEqual(db.get_event(event_id)['canonical_key'], 'legacy-key')


if __name__ == '__main__':
    unittest.main()
