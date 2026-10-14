import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.db import Database
from core.models import Candidate, Evidence
from core.pipeline import Pipeline
from core.notify import TelegramNotifier


TEST_TMP = Path(__file__).parents[1] / '.test-tmp'
TEST_TMP.mkdir(exist_ok=True)


class PipelineTests(unittest.TestCase):
    def test_same_barrier_does_not_alert_again_when_other_sources_are_skipped(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as td:
            pipeline = Pipeline(Path(td))
            self.assertTrue(pipeline.notifications.record_health('openmagpie', 'PARTIAL', 'CAPTCHA_REQUIRED'))
            self.assertFalse(pipeline.notifications.record_health('openmagpie', 'PAUSED', 'CAPTCHA_REQUIRED'))
            self.assertTrue(pipeline.notifications.record_health('openmagpie', 'FAILED', 'NETWORK_TIMEOUT'))
            self.assertTrue(pipeline.notifications.record_health('openmagpie', 'OK', ''))

    def test_existing_health_fingerprint_does_not_generate_migration_alert(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as td:
            pipeline = Pipeline(Path(td))
            with pipeline.db.connect() as conn:
                conn.execute('INSERT INTO node_health VALUES(?,?,?)',
                    ('openmagpie', 'PARTIAL:CAPTCHA_REQUIRED', '2026-10-11T00:00:00Z'))
            self.assertFalse(pipeline.notifications.record_health('openmagpie', 'PAUSED', 'CAPTCHA_REQUIRED'))

    def test_enabled_official_tracing_is_bounded_per_node_run(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP, ignore_cleanup_errors=True) as td:
            root = Path(td)
            (root / 'config').mkdir()
            (root / 'data' / 'inbox').mkdir(parents=True)
            (root / 'config' / 'official-trace.json').write_text(json.dumps({'enabled': True, 'max_per_node_run': 1}), encoding='utf-8')
            candidates = [Candidate('openmagpie', 'MLH', f'Free credits {i}', f'https://news.mlh.io/{i}',
                source_kind='official', metadata={'official': True}) for i in range(2)]
            (root / 'data' / 'inbox' / 'openmagpie.jsonl').write_text('\n'.join(json.dumps(c.to_dict()) for c in candidates), encoding='utf-8')
            with patch('core.official_trace.OfficialTracer') as tracer:
                Pipeline(root).ingest_node('openmagpie')
                self.assertEqual(tracer.return_value.trace.call_count, 1)

    def test_health_alert_is_durable_and_not_repeated_each_scan(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP, ignore_cleanup_errors=True) as td:
            root = Path(td)
            pipeline = Pipeline(root)
            self.assertTrue(pipeline.notifications.record_health('linuxdo-monitor', 'PARTIAL', 'NETWORK_TIMEOUT'))
            self.assertFalse(Pipeline(root).notifications.record_health('linuxdo-monitor', 'PARTIAL', 'NETWORK_TIMEOUT'))
            self.assertFalse(pipeline.notifications.record_health('linuxdo-monitor', 'SKIPPED', ''))
            self.assertFalse(pipeline.notifications.record_health('linuxdo-monitor', 'PARTIAL', 'NETWORK_TIMEOUT'))
            self.assertTrue(pipeline.notifications.record_health('linuxdo-monitor', 'OK', ''))
            self.assertTrue(pipeline.notifications.record_health('linuxdo-monitor', 'PARTIAL', 'NETWORK_TIMEOUT'))
            self.assertEqual(len(pipeline.notifications.pending()), 3)

    def test_paused_source_with_successful_candidates_is_partial(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP, ignore_cleanup_errors=True) as td:
            root = Path(td)
            (root / 'data' / 'inbox').mkdir(parents=True)
            (root / 'data' / 'status').mkdir(parents=True)
            candidate = Candidate('openmagpie', 'RSS', 'Free API credits', 'https://vendor.example/offer')
            (root / 'data' / 'inbox' / 'openmagpie.jsonl').write_text(json.dumps(candidate.to_dict()), encoding='utf-8')
            (root / 'data' / 'status' / 'openmagpie.json').write_text(json.dumps({'sources': [
                {'status': 'OK'}, {'status': 'PAUSED', 'error_code': 'CAPTCHA_REQUIRED'}]}), encoding='utf-8')
            result = Pipeline(root).ingest_node('openmagpie')
            self.assertEqual(result['status'], 'PARTIAL')

    def test_ingest_deduplicates_two_nodes_and_keeps_two_sightings(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP, ignore_cleanup_errors=True) as td:
            root = Path(td)
            (root / 'config').mkdir()
            (root / 'data' / 'inbox').mkdir(parents=True)
            (root / 'data' / 'status').mkdir(parents=True)
            for node, source, url in [
                ('openmagpie', 'Reddit', 'https://reddit.example/1'),
                ('linuxdo-monitor', 'Linux.do', 'https://linux.example/2'),
            ]:
                candidate = Candidate(node, source, 'RackNerd x AdminBolt free VPS giveaway', url,
                                      metadata={'provenance_key': 'same-promo'})
                (root / 'data' / 'inbox' / f'{node}.jsonl').write_text(
                    json.dumps(candidate.to_dict(), ensure_ascii=False) + '\n', encoding='utf-8')
                (root / 'data' / 'status' / f'{node}.json').write_text(json.dumps({
                    'node': node, 'candidate_count': 1,
                    'sources': [{'source_id': source, 'status': 'OK', 'items': 1, 'error_code': '', 'detail': ''}],
                }), encoding='utf-8')
            pipeline = Pipeline(root)
            pipeline.ingest_node('openmagpie')
            pipeline.ingest_node('linuxdo-monitor')
            with pipeline.db.connect() as conn:
                self.assertEqual(conn.execute('select count(*) from events').fetchone()[0], 1)
                self.assertEqual(conn.execute('select count(*) from sightings').fetchone()[0], 2)
                self.assertEqual(conn.execute('select status from events').fetchone()[0], 'UNKNOWN')

    def test_telegram_is_disabled_without_explicit_config(self):
        notifier = TelegramNotifier({'telegram_send_enabled': False})
        result = notifier.send('test')
        self.assertEqual(result, 'DISABLED')

    def test_apply_evidence_updates_event_and_preserves_scope(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP, ignore_cleanup_errors=True) as td:
            pipeline = Pipeline(Path(td))
            stored = pipeline.db.upsert_candidate(Candidate(
                'linuxdo-monitor', 'LowEndTalk', 'Example free VPS batch',
                'https://forum.example/giveaway',
            ))
            result = pipeline.apply_evidence(stored.event_id, [Evidence(
                'official', 'https://vendor.example/offer', 'vendor.example',
                claims={'open': True, 'public': True, 'remaining': 'unknown'},
            )])
            self.assertEqual(result['status'], 'CLAIMABLE')
            event = pipeline.db.get_event(stored.event_id)
            self.assertEqual(event['claim_scope'], 'PUBLIC_APPLICATION')


if __name__ == '__main__':
    unittest.main()
