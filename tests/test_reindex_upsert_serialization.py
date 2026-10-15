"""Real Database.upsert_candidate race against an IMMEDIATE review migration.

Runs on temporary WAL SQLite only. The synthetic migration uses the same
transaction boundary as Database.reindex; it never accesses production data.
"""
import json
import threading
import unittest
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from core.db import Database
from core.dedup import canonical_key, normalize_url
from core.models import Candidate


class _PausedConnection:
    def __init__(self, connection, ready, release):
        self.connection = connection
        self.ready = ready
        self.release = release

    def __getattr__(self, name):
        return getattr(self.connection, name)

    def execute(self, sql, params=()):
        cursor = self.connection.execute(sql, params)
        if (threading.current_thread().name == 'collector'
                and 'SELECT review_json FROM campaign_links WHERE url=?' in sql):
            self.ready.set()
            if not self.release.wait(timeout=10):
                raise TimeoutError('collector review lookup never resumed')
        return cursor


class _PausedReviewDatabase(Database):
    def __init__(self, path, ready, release):
        self.ready, self.release = ready, release
        super().__init__(path)

    @contextmanager
    def connect(self):
        with super().connect() as conn:
            yield _PausedConnection(conn, self.ready, self.release)


class ConcurrentReviewMigrationTests(unittest.TestCase):
    def test_review_migration_cannot_insert_stale_key_or_duplicate_alert(self):
        with TemporaryDirectory() as root:
            path = Path(root) / 'isolated.db'
            ready, release = threading.Event(), threading.Event()
            reader = _PausedReviewDatabase(path, ready, release)
            migration_db = Database(path)
            url = 'https://vendor.example/one'
            other_url = 'https://else.example/two'
            title = 'VendorOne VPS Giveaway'
            review = {
                'method': 'normal_browser_read',
                'campaign_url': 'https://gleam.io/aB123',
                'member_urls': [url, other_url],
                'member_titles': {url: title, other_url: 'VendorTwo VPS Giveaway'},
            }
            candidate = Candidate('collector1', 'synthetic', title, url)
            original = migration_db.upsert_candidate(candidate)
            self.assertTrue(original.notify)
            new_key = canonical_key(Candidate('n', 'synthetic', title, url,
                                              metadata={'campaign_review': review}))
            self.assertNotEqual(new_key, migration_db.get_event(original.event_id)['canonical_key'])

            results = {}
            migrated = threading.Event()

            def collector():
                try:
                    results['upsert'] = reader.upsert_candidate(
                        Candidate('collector2', 'synthetic', title, url))
                except BaseException as exc:
                    results['collector_error'] = exc

            def migration():
                try:
                    with migration_db.connect() as conn:
                        conn.execute('BEGIN IMMEDIATE')
                        conn.execute('INSERT INTO campaign_links(url,review_json) VALUES(?,?)',
                                     (normalize_url(url), json.dumps(review)))
                        conn.execute('UPDATE events SET canonical_key=? WHERE id=?',
                                     (new_key, original.event_id))
                except BaseException as exc:
                    results['migration_error'] = exc
                finally:
                    migrated.set()

            t_collector = threading.Thread(name='collector', target=collector)
            t_migration = threading.Thread(name='migration', target=migration)
            t_collector.start()
            try:
                self.assertTrue(ready.wait(timeout=10), 'collector did not reach review lookup')
                t_migration.start()
                # The fixed upsert holds the SQLite write reservation here.
                self.assertFalse(migrated.wait(timeout=0.15),
                                 'migration committed during an in-flight upsert')
            finally:
                release.set()
                t_collector.join(timeout=15)
                if t_migration.ident is not None:
                    t_migration.join(timeout=15)

            self.assertFalse(t_collector.is_alive())
            self.assertFalse(t_migration.is_alive())
            self.assertNotIn('collector_error', results)
            self.assertNotIn('migration_error', results)
            self.assertTrue(migrated.is_set())
            self.assertFalse(results['upsert'].notify)
            events = migration_db.list_events()
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]['canonical_key'], new_key)
            with migration_db.connect() as conn:
                sightings = conn.execute('SELECT node FROM sightings ORDER BY node').fetchall()
            self.assertEqual([row[0] for row in sightings], ['collector1', 'collector2'])


if __name__ == '__main__':
    unittest.main()
