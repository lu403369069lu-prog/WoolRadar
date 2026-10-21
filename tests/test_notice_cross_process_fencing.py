"""W1: real OS processes contend for one durable notification lease.

All messages and SQLite files are synthetic; no external transport is used.
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from core.db import Database
from core.models import Candidate
from core.notify import NotificationQueue


CHILD = r'''
import json
import sys
import time
from pathlib import Path

from core.db import Database
from core.notify import NotificationQueue

mode, database, folder, worker = sys.argv[1:]
root = Path(folder)
queue = NotificationQueue(Database(Path(database)))

def sender(message):
    (root / ('sent-' + worker)).write_text(message, encoding='utf-8')
    if mode == 'stale':
        (root / 'inflight').write_text('yes', encoding='utf-8')
        until = time.monotonic() + 15
        while not (root / 'release').exists():
            if time.monotonic() > until:
                raise RuntimeError('stale worker release timeout')
            time.sleep(.01)
        return 'FAILED'
    return 'SENT'

if mode == 'contend':
    original_pending = queue.pending
    def synchronized_pending():
        snapshot = original_pending()
        (root / ('ready-' + worker)).write_text(str(len(snapshot)), encoding='utf-8')
        until = time.monotonic() + 15
        while not ((root / 'ready-A').exists() and (root / 'ready-B').exists()):
            if time.monotonic() > until:
                raise RuntimeError('contention barrier timeout')
            time.sleep(.01)
        return snapshot
    queue.pending = synchronized_pending

result = queue.flush({'telegram_send_enabled': True, 'telegram_delivery_mode': 'at_least_once'}, sender=sender, retry_seconds=0)
print(json.dumps(result), flush=True)
'''


class CrossProcessNotificationFencingTests(unittest.TestCase):
    @staticmethod
    def wait_for(path: Path, processes, timeout: float = 15):
        deadline = time.monotonic() + timeout
        while not path.exists():
            if any(process.poll() is not None for process in processes):
                raise AssertionError('worker exited before reaching ' + path.name)
            if time.monotonic() > deadline:
                raise AssertionError('worker never reached ' + path.name)
            time.sleep(.01)

    @staticmethod
    def spawn(mode: str, database: Path, root: Path, label: str):
        return subprocess.Popen(
            [sys.executable, '-B', '-X', 'utf8', '-c', CHILD,
             mode, str(database), str(root), label],
            cwd=str(Path(__file__).resolve().parents[1]),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
        )

    @staticmethod
    def collect(process):
        output, error = process.communicate(timeout=20)
        if process.returncode:
            raise AssertionError(f'child exit={process.returncode}: {error}')
        return json.loads(output.strip())

    def make_queue(self, root):
        path = root / 'notice.db'
        database = Database(path)
        event = database.upsert_candidate(Candidate(
            'synthetic', 'synthetic', 'Claim competition',
            'https://example.test/claim-competition')).event_id
        self.assertTrue(NotificationQueue(database).enqueue(
            event, 'batch', 'telegram', 'safe synthetic content'))
        return database

    def test_two_ready_processes_compete_but_only_one_sends(self):
        with tempfile.TemporaryDirectory(prefix='wool-w1-process-') as folder:
            root = Path(folder)
            database = self.make_queue(root)
            children = [self.spawn('contend', database.path, root, label)
                        for label in ('A', 'B')]
            try:
                self.wait_for(root / 'ready-A', children)
                self.wait_for(root / 'ready-B', children)
                self.assertEqual((root / 'ready-A').read_text(), '1')
                self.assertEqual((root / 'ready-B').read_text(), '1')
                results = [self.collect(process) for process in children]
                self.assertEqual(sum(item['sent'] for item in results), 1)
                self.assertEqual(len(list(root.glob('sent-*'))), 1)
                with database.connect() as conn:
                    row = conn.execute('SELECT result,attempts FROM notifications').fetchone()
                    self.assertEqual((row['result'], row['attempts']), ('SENT', 1))
            finally:
                for process in children:
                    if process.poll() is None:
                        process.kill()
                    process.communicate()

    def test_stale_process_cannot_downgrade_successor_sent(self):
        with tempfile.TemporaryDirectory(prefix='wool-w1-takeover-') as folder:
            root = Path(folder)
            database = self.make_queue(root)
            stale = self.spawn('stale', database.path, root, 'old')
            processes = [stale]
            try:
                self.wait_for(root / 'inflight', processes)
                # Synthetic deadline expiry: preserve the old attempt while
                # allowing another independent process to acquire the row.
                with database.connect() as conn:
                    conn.execute("UPDATE notifications SET next_attempt=0 "
                                 "WHERE result='CLAIMED'")
                successor = self.spawn('takeover', database.path, root, 'new')
                processes.append(successor)
                new_result = self.collect(successor)
                self.assertEqual(new_result['sent'], 1)
                (root / 'release').write_text('yes', encoding='utf-8')
                old_result = self.collect(stale)
                self.assertEqual(old_result.get('uncertain'), 1)
                with database.connect() as conn:
                    row = conn.execute('SELECT result,attempts FROM notifications').fetchone()
                    self.assertEqual((row['result'], row['attempts']), ('SENT', 2))
                # Re-delivery after genuine lease expiry remains at-least-once.
                self.assertEqual(len(list(root.glob('sent-*'))), 2)
            finally:
                (root / 'release').touch(exist_ok=True)
                for process in processes:
                    if process.poll() is None:
                        process.kill()
                    process.communicate()


if __name__ == '__main__':
    unittest.main()
