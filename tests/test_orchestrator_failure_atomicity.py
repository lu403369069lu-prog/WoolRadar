import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from core.notify import NotificationQueue
from core.orchestrator import run_all
from core.pipeline import Pipeline


TEST_TMP = Path(__file__).parents[1] / '.test-tmp'
TEST_TMP.mkdir(exist_ok=True)


class OrchestratorFailureAtomicityTests(unittest.TestCase):
    def test_child_failures_roll_back_run_health_and_notice_together(self):
        failures = (
            ('timeout', subprocess.TimeoutExpired(['node'], 1), 124, 'TIMEOUT'),
            ('start_error', OSError('synthetic start failure'), 127, 'PROCESS_START_FAILED'),
            ('unexpected_exit', SimpleNamespace(returncode=7, stdout='', stderr='synthetic stderr'), 7, 'synthetic stderr'),
        )
        for label, child_failure, exit_code, stderr in failures:
            with self.subTest(label=label), tempfile.TemporaryDirectory(dir=TEST_TMP) as td:
                root = Path(td)
                original_record_health = NotificationQueue.record_health

                def fail_after_health_sql(queue, node, status, error_code):
                    original_record_health(queue, node, status, error_code)
                    raise RuntimeError('INJECTED_HEALTH_POST_WRITE_FAILURE')

                with patch('core.orchestrator.subprocess.run', side_effect=[child_failure]), \
                        patch.object(NotificationQueue, 'record_health', fail_after_health_sql):
                    with self.assertRaisesRegex(RuntimeError, 'INJECTED_HEALTH_POST_WRITE_FAILURE'):
                        run_all(root)

                db = Pipeline(root).db
                with db.connect() as conn:
                    for table in ('node_runs', 'node_health', 'notifications'):
                        self.assertEqual(conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0], 0, table)
                self.assertFalse(list((root / 'reports' / 'notifications').glob('*.json')))

                successes = [SimpleNamespace(returncode=0, stdout='', stderr='') for _ in range(4)]
                with patch('core.orchestrator.subprocess.run', side_effect=[child_failure, *successes]):
                    results = run_all(root)
                self.assertEqual([r.exit_code for r in results], [exit_code, 0, 0, 0, 0])
                self.assertEqual(results[0].stderr, stderr)
                with db.connect() as conn:
                    runs = conn.execute('SELECT node,status,error_code FROM node_runs').fetchall()
                    health = conn.execute('SELECT node,fingerprint FROM node_health').fetchall()
                    notices = conn.execute('SELECT batch_id,channel,result,payload FROM notifications').fetchall()
                self.assertEqual([tuple(row) for row in runs], [('twitter-monitor', 'FAILED', 'PROCESS_FAILED')])
                self.assertEqual([tuple(row) for row in health], [('twitter-monitor', 'ISSUE:PROCESS_FAILED')])
                self.assertEqual(len(notices), 1)
                self.assertEqual(notices[0]['channel'], 'local-health')
                self.assertEqual(notices[0]['batch_id'], 'twitter-monitor')
                self.assertEqual(notices[0]['result'], 'SENT')
                self.assertEqual(len(list((root / 'reports' / 'notifications').glob('*.json'))), 1)
