import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from core.orchestrator import run_all
from core.pipeline import Pipeline

TEST_TMP = Path(__file__).parents[1] / '.test-tmp'
TEST_TMP.mkdir(exist_ok=True)


class OrchestratorTests(unittest.TestCase):
    def test_child_timeout_does_not_stop_other_nodes_and_emits_health_notice(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as td:
            root = Path(td)
            replies = [subprocess.TimeoutExpired(['node'], 1, output=b'partial output'),
                *[SimpleNamespace(returncode=0, stdout='ok', stderr='') for _ in range(4)]]
            with patch('core.orchestrator.subprocess.run', side_effect=replies):
                results = run_all(root)
            self.assertEqual(len(results), 5)
            self.assertIsInstance(results[0].stdout, str)
            self.assertEqual(results[0].exit_code, 124)
            with Pipeline(root).db.connect() as conn:
                self.assertEqual(conn.execute('SELECT count(*) FROM notifications').fetchone()[0], 1)
            self.assertEqual(len(list((root / 'reports' / 'notifications').glob('*.json'))), 1)
