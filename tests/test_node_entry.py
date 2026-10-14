import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.collector import CollectionResult, SourceRun
from core.db import Database
from core.models import Candidate
from nodes.run_node import main

TEST_TMP = Path(__file__).parents[1] / '.test-tmp'
TEST_TMP.mkdir(exist_ok=True)


class NodeEntryTests(unittest.TestCase):
    def test_scheduled_entry_ingests_candidates_into_database(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as td:
            root = Path(td)
            result = CollectionResult('openmagpie', [Candidate(
                'openmagpie', 'RSS', 'Free API credits', 'https://example.org/promo',
            )], [SourceRun('example', 'OK', items=1)])
            with patch.object(sys, 'argv', ['run.py', '--root', td]), patch(
                    'core.collector.collect_for_node', return_value=result):
                self.assertEqual(main('openmagpie'), 0)
            self.assertEqual(len(Database(root / 'data' / 'woolradar.db').list_events()), 1)
