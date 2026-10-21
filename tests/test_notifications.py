import json
import sqlite3
import tempfile
import threading
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from core.db import Database
from core.models import Candidate, Evidence
from core.pipeline import Pipeline
from core.notify import NotificationQueue

TEMP = Path(__file__).parents[1] / '.test-tmp'
TEMP.mkdir(exist_ok=True)


class NotificationTests(unittest.TestCase):
    def test_local_receipt_survives_commit_failure_without_second_publish(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as td:
            root = Path(td)
            db = Database(root / 'radar.db')
            event_id = db.upsert_candidate(Candidate('n', 'rss', 'Notice', 'https://vendor.example/notice')).event_id
            queue = NotificationQueue(db)
            self.assertTrue(queue.enqueue(event_id, '', 'local', 'notice'))
            outbox = root / 'outbox'
            original_connect = db.connect
            original_replace = Path.replace
            fail_once = [True]
            published = []

            @contextmanager
            def failing_commit():
                with original_connect() as conn:
                    yield conn
                    if (fail_once[0] and list(outbox.glob('notification-*.json'))
                            and conn.execute("SELECT result FROM notifications WHERE id=1").fetchone()['result'] == 'SENT'):
                        fail_once[0] = False
                        raise sqlite3.OperationalError('injected COMMIT failure before durability')

            def track_replace(source, destination):
                if Path(destination).name.startswith('notification-') and Path(destination).suffix == '.json':
                    published.append(Path(destination))
                return original_replace(source, destination)

            with patch.object(db, 'connect', failing_commit), patch.object(Path, 'replace', track_replace):
                self.assertEqual(queue.flush({}, local_dir=outbox, retry_seconds=0)['retry'], 1)
                self.assertEqual(len(list(outbox.glob('notification-*.json'))), 1)
                self.assertEqual(queue.flush({}, local_dir=outbox, retry_seconds=0)['local'], 1)
            self.assertEqual(len(published), 1, 'a durable identical receipt must not be published again')
            with original_connect() as conn:
                self.assertEqual(conn.execute('SELECT result FROM notifications WHERE id=1').fetchone()['result'], 'SENT')

    def test_expired_local_worker_cannot_publish_after_reclaim(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as td:
            root = Path(td)
            db = Database(root / 'radar.db')
            event_id = db.upsert_candidate(Candidate('n', 'rss', 'Notice', 'https://vendor.example/notice')).event_id
            queue = NotificationQueue(db)
            queue.enqueue(event_id, '', 'local', 'old payload')
            entered, release = threading.Event(), threading.Event()
            errors = []
            original_write = Path.write_text

            def pause_old_writer(path, *args, **kwargs):
                if threading.current_thread().name == 'stale-local-worker' and path.suffix == '.tmp':
                    entered.set()
                    if not release.wait(5):
                        raise AssertionError('replacement worker did not finish')
                return original_write(path, *args, **kwargs)

            def old_worker():
                try:
                    queue.flush({}, local_dir=root / 'outbox')
                except BaseException as exc:
                    errors.append(exc)

            with patch.object(Path, 'write_text', pause_old_writer):
                thread = threading.Thread(target=old_worker, name='stale-local-worker')
                thread.start()
                try:
                    self.assertTrue(entered.wait(5))
                    with db.connect() as conn:
                        conn.execute("UPDATE notifications SET next_attempt=0,payload='new payload' WHERE result='CLAIMED'")
                    replacement = NotificationQueue(Database(db.path))
                    self.assertEqual(replacement.flush({}, local_dir=root / 'outbox')['local'], 1)
                finally:
                    release.set()
                    thread.join(5)
            self.assertFalse(thread.is_alive())
            self.assertEqual(errors, [])
            receipts = list((root / 'outbox').glob('notification-*.json'))
            self.assertEqual(len(receipts), 1)
            self.assertEqual(json.loads(receipts[0].read_text(encoding='utf-8'))['message'], 'new payload')
            with db.connect() as conn:
                state = conn.execute('SELECT result,attempts FROM notifications').fetchone()
            self.assertEqual((state['result'], state['attempts']), ('SENT', 2))

    def test_passed_official_deadline_suppresses_queued_verified_notice(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as td:
            root = Path(td)
            pipeline = Pipeline(root)
            event = pipeline.db.upsert_candidate(Candidate('n', 'rss', 'Free API', 'https://vendor.example/api')).event_id
            pipeline.db.add_evidence(event, Evidence('official', 'https://vendor.example/api', 'vendor',
                claims={'public': True, 'open': True, 'expires_at': '2020-01-01T00:00:00Z'}))
            pipeline.notifications.enqueue(event, '', 'local-verified', 'expired claim')
            pipeline.notifications.flush({}, local_dir=root / 'notices')
            self.assertEqual(list((root / 'notices').glob('*.json')), [])
            with pipeline.db.connect() as conn:
                self.assertEqual(conn.execute('SELECT result FROM notifications').fetchone()[0], 'STALE')

    def test_expired_delivery_lease_with_stale_evidence_can_leave_claimed_state(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as td:
            db = Database(Path(td) / 'radar.db')
            event = db.upsert_candidate(Candidate('n', 'rss', 'Free API', 'https://vendor.example/api')).event_id
            queue = NotificationQueue(db)
            queue.enqueue(event, '', 'local-verified', 'old claim')
            with db.connect() as conn:
                conn.execute("UPDATE notifications SET result='CLAIMED',next_attempt=0")
            queue.flush({}, local_dir=Path(td) / 'outbox')
            with db.connect() as conn:
                self.assertEqual(conn.execute('SELECT result FROM notifications').fetchone()[0], 'STALE')

    def test_unsent_stale_notice_can_resume_after_fresh_verification(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as td:
            root = Path(td)
            pipeline = Pipeline(root)
            event = pipeline.db.upsert_candidate(Candidate('n', 'rss', 'Free API', 'https://vendor.example/api')).event_id
            pipeline.db.add_evidence(event, Evidence('official', 'https://vendor.example/api', 'vendor',
                checked_at='2020-01-01T00:00:00Z', claims={'public': True, 'open': True}))
            pipeline.notifications.enqueue(event, '', 'local-verified', 'old claim')
            pipeline.notifications.flush({}, local_dir=root / 'notices')
            pipeline.apply_evidence(event, [Evidence('official', 'https://vendor.example/api', 'vendor',
                claims={'public': True, 'open': True})])
            self.assertEqual(len(pipeline.notifications.pending()), 1)
            pipeline.notifications.flush({}, local_dir=root / 'notices')
            self.assertFalse(pipeline.notifications.enqueue(event, '', 'local-verified', 'repeat sent notice'))
            self.assertEqual(len(list((root / 'notices').glob('*.json'))), 1)

    def test_local_delivery_recovers_after_file_failure(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as td:
            root = Path(td)
            db = Database(root / 'radar.db')
            event = db.upsert_candidate(Candidate('n', 'rss', 'Free API', 'https://vendor.example/api')).event_id
            queue = NotificationQueue(db)
            queue.enqueue(event, '', 'local', 'notice')
            blocked = root / 'blocked'
            blocked.write_text('file, not directory', encoding='utf-8')
            queue.flush({}, local_dir=blocked, retry_seconds=0)
            self.assertEqual(len(queue.pending()), 1)
            NotificationQueue(Database(db.path)).flush({}, local_dir=root / 'outbox', retry_seconds=0)
            self.assertEqual(len(list((root / 'outbox').glob('*.json'))), 1)
            self.assertEqual(len(queue.pending()), 0)
    def test_queue_is_persistent_and_unique_per_batch(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as td:
            db = Database(Path(td) / 'radar.db')
            event = db.upsert_candidate(Candidate('n', 'rss', 'Free VPS', 'https://vendor.example/offer')).event_id
            queue = NotificationQueue(db)
            self.assertTrue(queue.enqueue(event, '', 'local', 'new candidate'))
            self.assertFalse(queue.enqueue(event, '', 'local', 'duplicate'))
            self.assertTrue(queue.enqueue(event, 'batch-2', 'local', 'new batch'))
            self.assertEqual(len(NotificationQueue(Database(db.path)).pending()), 2)

    def test_disabled_telegram_does_not_attempt_delivery(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as td:
            db = Database(Path(td) / 'radar.db')
            event = db.upsert_candidate(Candidate('n', 'rss', 'Free API', 'https://vendor.example/api')).event_id
            queue = NotificationQueue(db)
            queue.enqueue(event, '', 'telegram', 'notice')
            calls = []
            queue.flush({'telegram_send_enabled': False}, sender=lambda text: calls.append(text))
            self.assertEqual(calls, [])
            self.assertEqual(len(queue.pending()), 1)

    def test_failed_delivery_retries_without_duplicate_enqueue(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as td:
            db = Database(Path(td) / 'radar.db')
            event = db.upsert_candidate(Candidate('n', 'rss', 'Free API', 'https://vendor.example/api')).event_id
            queue = NotificationQueue(db)
            queue.enqueue(event, '', 'telegram', 'notice')
            queue.flush({'telegram_send_enabled': True, 'telegram_delivery_mode': 'at_least_once'}, sender=lambda text: 'FAILED', retry_seconds=0)
            self.assertEqual(len(queue.pending()), 1)
            queue.flush({'telegram_send_enabled': True, 'telegram_delivery_mode': 'at_least_once'}, sender=lambda text: 'SENT', retry_seconds=0)
            self.assertEqual(len(queue.pending()), 0)
            self.assertFalse(queue.enqueue(event, '', 'telegram', 'duplicate'))

    def test_sender_exception_does_not_leak_credentials(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as td:
            db = Database(Path(td) / 'radar.db')
            event = db.upsert_candidate(Candidate('n', 'rss', 'Free API', 'https://vendor.example/api')).event_id
            queue = NotificationQueue(db)
            queue.enqueue(event, '', 'telegram', 'notice')
            def sender(text):
                raise RuntimeError('https://api.telegram.org/botSECRET/sendMessage')
            queue.flush({'telegram_send_enabled': True, 'telegram_delivery_mode': 'at_least_once'}, sender=sender)
            with db.connect() as conn:
                record = dict(conn.execute('SELECT * FROM notifications').fetchone())
            self.assertNotIn('SECRET', json.dumps(record))

    def test_pipeline_queues_verified_activity(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as td:
            root = Path(td)
            (root / 'config').mkdir()
            (root / 'config' / 'security-policy.json').write_text('{"telegram_send_enabled":false}', encoding='utf-8')
            pipeline = Pipeline(root)
            event = pipeline.db.upsert_candidate(Candidate('n', 'rss', 'Free VPS', 'https://vendor.example/vps')).event_id
            pipeline.apply_evidence(event, [Evidence('official', 'https://vendor.example/vps', 'vendor',
                claims={'public': True, 'open': True})])
            self.assertEqual(len(NotificationQueue(pipeline.db).pending()), 1)

    def test_stale_verified_notice_is_not_delivered(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as td:
            db = Database(Path(td) / 'radar.db')
            event = db.upsert_candidate(Candidate('n', 'rss', 'Free API', 'https://vendor.example/api')).event_id
            db.add_evidence(event, Evidence('official', 'https://vendor.example/api', 'vendor',
                checked_at='2020-01-01T00:00:00Z', claims={'public': True, 'open': True}))
            queue = NotificationQueue(db)
            queue.enqueue(event, '', 'telegram-verified', 'old current-open claim')
            calls = []
            queue.flush({'telegram_send_enabled': True, 'telegram_delivery_mode': 'at_least_once'}, sender=lambda text: calls.append(text))
            self.assertEqual(calls, [])
