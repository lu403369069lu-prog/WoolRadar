import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from core.db import Database
from core.models import Candidate, Evidence, Status
from core.report import ReportGenerator

TEST_TMP = Path(__file__).parents[1] / '.test-tmp'
TEST_TMP.mkdir(exist_ok=True)


class ReportTests(unittest.TestCase):
    def test_report_revalidates_passed_official_deadline(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as td:
            root = Path(td)
            db = Database(root / 'data/woolradar.db')
            event = db.upsert_candidate(Candidate('n', 'rss', 'Free VPS', 'https://vendor.example/promo')).event_id
            db.add_evidence(event, Evidence('official', 'https://vendor.example/promo', 'vendor',
                claims={'public': True, 'open': True, 'expires_at': '2020-01-01T00:00:00Z'}))
            db.set_status(event, Status.CLAIMABLE, 'old decision', 'PUBLIC_APPLICATION')
            paths = ReportGenerator(db, root / 'reports').generate('2026-10-12')
            payload = json.loads(paths.json.read_text(encoding='utf-8'))
            self.assertEqual(payload['events'][0]['status'], 'EXPIRED')
            section = paths.markdown.read_text(encoding='utf-8').split('## 官方已核实、正在开放的福利', 1)[1].split('## ', 1)[0]
            self.assertNotIn('Free VPS', section)

    def test_unknown_qualification_does_not_imply_account_login_required(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as td:
            root = Path(td)
            db = Database(root / 'data' / 'woolradar.db')
            event = db.upsert_candidate(Candidate('n', 'rss', 'Unverified free VPS', 'https://forum.example/1',
                discovered_at='2026-10-11T10:00:00Z')).event_id
            db.set_status(event, Status.UNKNOWN, 'unknown')
            paths = ReportGenerator(db, root / 'reports').generate('2026-10-11')
            text = paths.markdown.read_text(encoding='utf-8')
            account_section = text.split('## 需要账号核验的活动', 1)[1].split('## ', 1)[0]
            self.assertNotIn('Unverified free VPS', account_section)
            self.assertIn('发现时间', text)
            self.assertIn('原帖发布时间', text)

    def test_report_revalidates_stale_claimable_state(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as td:
            root = Path(td)
            db = Database(root / 'data' / 'woolradar.db')
            event = db.upsert_candidate(Candidate('n', 'rss', 'Free VPS', 'https://vendor.example/promo')).event_id
            db.add_evidence(event, Evidence('official', 'https://vendor.example/promo', 'vendor',
                checked_at='2020-01-01T00:00:00Z', claims={'public': True, 'open': True}))
            db.set_status(event, Status.CLAIMABLE, 'old decision', 'PUBLIC_APPLICATION')
            paths = ReportGenerator(db, root / 'reports').generate('2026-10-11')
            payload = json.loads(paths.json.read_text(encoding='utf-8'))
            self.assertNotEqual(payload['events'][0]['status'], 'CLAIMABLE')
    def test_generates_markdown_and_json_with_required_sections(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as td:
            root = Path(td)
            db = Database(root / 'data' / 'woolradar.db')
            candidate = Candidate('openmagpie', 'hn', 'Free API credits', 'https://example.org/promo')
            stored = db.upsert_candidate(candidate)
            db.add_evidence(stored.event_id, Evidence('official', 'https://example.org/promo', 'vendor'))
            db.set_status(stored.event_id, Status.OFFICIAL_VERIFIED, 'official page checked')
            paths = ReportGenerator(db, root / 'reports').generate('2026-10-11')
            self.assertTrue(paths.markdown.exists())
            self.assertTrue(paths.json.exists())
            text = paths.markdown.read_text(encoding='utf-8')
            for heading in ['今日新发现', '官方已核实、正在开放的福利', '限时高价值活动',
                            '需要账号核验的活动', '已结束或存在风险的活动', '采集节点故障与漏报情况']:
                self.assertIn(heading, text)
            official_open = text.split('## 官方已核实、正在开放的福利', 1)[1].split('## 限时高价值活动', 1)[0]
            self.assertNotIn('Free API credits', official_open)
            payload = json.loads(paths.json.read_text(encoding='utf-8'))
            self.assertEqual(payload['date'], '2026-10-11')
            self.assertEqual(payload['events'][0]['status'], 'OFFICIAL_VERIFIED')


if __name__ == '__main__':
    unittest.main()
