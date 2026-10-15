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


if __name__ == '__main__':
    unittest.main()
