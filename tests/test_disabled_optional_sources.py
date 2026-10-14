import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.collector import collect_for_node, write_collection
from core.pipeline import Pipeline

TEST_TMP = Path(__file__).parents[1] / '.test-tmp'
TEST_TMP.mkdir(exist_ok=True)
OAUTH = {'id': 'reddit-oauth', 'owner_node': 'clawradar', 'platform': 'Reddit',
         'kind': 'reddit_oauth', 'endpoint': 'https://oauth.reddit.com/search', 'enabled': False}
RSS = {'id': 'reddit-hot-rss', 'owner_node': 'clawradar', 'platform': 'Reddit',
       'kind': 'rss', 'endpoint': 'https://www.reddit.com/r/freebies/hot/.rss', 'enabled': True}

class DisabledOptionalSourceTests(unittest.TestCase):
    def test_disabled_auth_is_skipped_without_fetch_or_budget_acquisition(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP, ignore_cleanup_errors=True) as td:
            with patch('core.collector.load_sources', return_value=[OAUTH]), \
                 patch('core.collector.load_keywords', return_value=['free VPS']), \
                 patch('core.collector.fetch_reddit_oauth') as auth, \
                 patch('core.collector.RequestBudget.acquire') as acquire:
                result = collect_for_node(Path(td), 'clawradar')
                self.assertEqual(result.sources[0].status, 'SKIPPED')
                self.assertEqual(result.sources[0].error_code, 'SOURCE_DISABLED')
                auth.assert_not_called()
                acquire.assert_not_called()

    def test_public_success_is_not_degraded_by_disabled_auth(self):
        row = {'title': 'Free VPS offer', 'summary': 'Public offer', 'url': 'https://www.reddit.com/r/freebies/comments/test/offer'}
        with tempfile.TemporaryDirectory(dir=TEST_TMP, ignore_cleanup_errors=True) as td:
            root = Path(td)
            with patch('core.collector.load_sources', return_value=[OAUTH, RSS]), \
                 patch('core.collector.load_keywords', return_value=['free VPS']), \
                 patch('core.collector._fetch_source', return_value=[row]), \
                 patch('core.collector.fetch_reddit_oauth') as auth:
                result = collect_for_node(root, 'clawradar')
            write_collection(root, result)
            summary = Pipeline(root).ingest_node('clawradar')
            self.assertEqual(summary['status'], 'OK')
            self.assertEqual(summary['error_code'], '')
            self.assertEqual(summary['ingested'], 1)
            auth.assert_not_called()

    def test_all_disabled_does_not_claim_live_success_or_raise_health_fault(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP, ignore_cleanup_errors=True) as td:
            root = Path(td)
            with patch('core.collector.load_sources', return_value=[OAUTH]), \
                 patch('core.collector.load_keywords', return_value=[]):
                result = collect_for_node(root, 'clawradar')
            write_collection(root, result)
            summary = Pipeline(root).ingest_node('clawradar')
            self.assertEqual(summary['status'], 'SKIPPED')
            self.assertEqual(summary['error_code'], '')

    def test_enabled_auth_failure_remains_a_real_pause(self):
        from core.collector import SourcePaused
        with tempfile.TemporaryDirectory(dir=TEST_TMP, ignore_cleanup_errors=True) as td:
            with patch('core.collector.load_sources', return_value=[dict(OAUTH, enabled=True)]), \
                 patch('core.collector.load_keywords', return_value=[]), \
                 patch('core.collector.fetch_reddit_oauth', side_effect=SourcePaused('OAUTH_REQUIRED')):
                result = collect_for_node(Path(td), 'clawradar')
            self.assertEqual(result.sources[0].status, 'PAUSED')
            self.assertEqual(result.sources[0].error_code, 'OAUTH_REQUIRED')
