"""W3: one SQLite commit for a node-run audit and its health transition.

All state is synthetic, in disposable local SQLite. No network or real sends.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.pipeline import Pipeline


class NodeRunHealthAtomicityTests(unittest.TestCase):
    def test_health_write_failure_rolls_back_run_and_recovery_notice(self):
        with tempfile.TemporaryDirectory(prefix='wr-w3-node-') as temp:
            pipeline = Pipeline(Path(temp))
            self.assertTrue(pipeline.notifications.record_health(
                'synthetic', 'FAILED', 'NETWORK_TIMEOUT'))
            with pipeline.db.connect() as conn:
                before = [tuple(row) for row in conn.execute(
                    'SELECT id,event_id,batch_id,channel,result,payload FROM notifications ORDER BY id')]
            actual_record = pipeline.notifications.record_health

            def fail_after_health_writes(*args):
                self.assertTrue(actual_record(*args))
                raise RuntimeError('W3_INJECTED_AFTER_HEALTH_UPDATE')

            with patch.object(pipeline.notifications, 'record_health',
                              side_effect=fail_after_health_writes):
                with self.assertRaisesRegex(RuntimeError, 'W3_INJECTED_AFTER_HEALTH_UPDATE'):
                    pipeline.ingest_node('synthetic')

            with pipeline.db.connect() as conn:
                self.assertEqual(conn.execute('SELECT count(*) FROM node_runs').fetchone()[0], 0)
                self.assertEqual(conn.execute(
                    'SELECT fingerprint FROM node_health WHERE node=?', ('synthetic',)
                ).fetchone()[0], 'ISSUE:NETWORK_TIMEOUT')
                self.assertEqual([tuple(row) for row in conn.execute(
                    'SELECT id,event_id,batch_id,channel,result,payload FROM notifications ORDER BY id')], before)

            # A subsequent clean recovery must still produce one run and one
            # recovery notification, with no duplicate from the failed attempt.
            self.assertEqual(pipeline.ingest_node('synthetic')['status'], 'OK')
            with pipeline.db.connect() as conn:
                self.assertEqual(conn.execute('SELECT count(*) FROM node_runs').fetchone()[0], 1)
                self.assertEqual(conn.execute(
                    'SELECT fingerprint FROM node_health WHERE node=?', ('synthetic',)
                ).fetchone()[0], 'OK')
                self.assertEqual(conn.execute(
                    "SELECT count(*) FROM notifications WHERE channel='local-health'"
                ).fetchone()[0], len(before) + 1)


if __name__ == '__main__':
    unittest.main()
