"""Concurrent collection must atomically group the same event without double notify."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
import unittest

from core.db import Database
from core.models import Candidate


class InsertBarrierConnection:
    def __init__(self, conn, barrier):
        self.conn = conn
        self.barrier = barrier

    def __getattr__(self, name):
        return getattr(self.conn, name)

    def execute(self, query, args=()):
        if 'INSERT INTO events(' in query:
            self.barrier.wait(timeout=10)
        return self.conn.execute(query, args)


class DatabaseWithInsertBarrier(Database):
    def __init__(self, path, barrier):
        self.barrier = barrier
        super().__init__(path)

    @contextmanager
    def connect(self):
        with super().connect() as conn:
            yield InsertBarrierConnection(conn, self.barrier)


class ConcurrentUpsertTests(unittest.TestCase):
    def test_two_nodes_same_event_insert_once_preserve_sightings(self):
        with TemporaryDirectory() as root:
            db = DatabaseWithInsertBarrier(Path(root) / 'synthetic.db', Barrier(2))

            def worker(index):
                return db.upsert_candidate(
                    Candidate(f'node{index}', 'fixture', 'Free VPS 1GB',
                              'https://vendor.example/promo'))

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = [pool.submit(worker, index) for index in range(2)]
                answers = [result.result(timeout=20) for result in results]

            self.assertEqual(answers[0].event_id, answers[1].event_id)
            self.assertEqual(sum(int(answer.notify) for answer in answers), 1)
            self.assertEqual(len(db.list_events()), 1)
            with db.connect() as conn:
                sightings = conn.execute('SELECT node FROM sightings ORDER BY node').fetchall()
            self.assertEqual([row[0] for row in sightings], ['node0', 'node1'])


    def test_concurrent_cross_vendor_generic_title_stays_separate(self):
        with TemporaryDirectory() as root:
            db = DatabaseWithInsertBarrier(Path(root) / 'synthetic.db', Barrier(2))

            def worker(index):
                return db.upsert_candidate(Candidate(f'node{index}', 'fixture',
                    'Free VPS 1GB', f'https://vendor{index}.example/promo'))

            with ThreadPoolExecutor(max_workers=2) as pool:
                answers = [f.result(timeout=20) for f in
                           [pool.submit(worker, n) for n in range(2)]]
            self.assertNotEqual(answers[0].event_id, answers[1].event_id)
            self.assertTrue(all(result.notify for result in answers))
            self.assertEqual(len(db.list_events()), 2)

    def test_concurrent_title_spacing_variants_do_not_alert_twice(self):
        with TemporaryDirectory() as root:
            db = DatabaseWithInsertBarrier(Path(root) / 'synthetic.db', Barrier(2))
            titles = ('Free VPS 1GB', 'Free VPS 1 GB')

            def worker(index):
                return db.upsert_candidate(Candidate(f'node{index}', 'fixture',
                    titles[index], 'https://vendor.example/promo'))

            with ThreadPoolExecutor(max_workers=2) as pool:
                answers = [f.result(timeout=20) for f in
                           [pool.submit(worker, n) for n in range(2)]]
            self.assertEqual(answers[0].event_id, answers[1].event_id)
            self.assertEqual(sum(result.notify for result in answers), 1)
            self.assertEqual(len(db.list_events()), 1)

    def test_separate_batches_keep_separate_notifications(self):
        with TemporaryDirectory() as root:
            db = Database(Path(root) / 'synthetic.db')
            a = db.upsert_candidate(Candidate('node1', 'fixture', 'Free VPS 1GB',
                'https://vendor.example/promo', batch_id='round-1'))
            b = db.upsert_candidate(Candidate('node1', 'fixture', 'Free VPS 1GB',
                'https://vendor.example/promo', batch_id='round-2'))
            self.assertNotEqual(a.event_id, b.event_id)
            self.assertTrue(a.notify and b.notify)
            self.assertEqual(len(db.list_events()), 2)


if __name__ == '__main__':
    unittest.main()
