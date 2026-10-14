import tempfile
import unittest
from pathlib import Path
from core.collector import build_candidate
from core.dedup import canonical_key
from core.db import Database

TEMP = Path(__file__).parents[1] / '.test-tmp'
TEMP.mkdir(exist_ok=True)


class BatchTests(unittest.TestCase):
    def test_amount_near_batch_marker_is_not_a_year(self):
        source = {'id': 'vendor', 'platform': 'Vendor', 'official': True}
        for currency in ('$', '$ ', '￥', 'EUR ', 'USD ', '£ '):
            with self.subTest(currency=currency):
                first = build_candidate({'title': f'Free credits {currency}2025 batch 1', 'url': 'https://vendor.example/promo'}, source, 'n')
                second = build_candidate({'title': f'Free credits {currency}2026 batch 1', 'url': 'https://vendor.example/promo'}, source, 'n')
                self.assertNotEqual(canonical_key(first), canonical_key(second))
                self.assertEqual(first.batch_id, second.batch_id)
                self.assertNotIn('year', first.metadata['batch_evidence'])

    def test_explicit_annual_batch_reuse_notifies_once_per_year(self):
        source = {'id': 'vendor', 'platform': 'Vendor', 'official': True}
        first = build_candidate({'title': 'Developer API credits 2025 batch 1', 'url': 'https://vendor.example/promo'}, source, 'n')
        second = build_candidate({'title': 'Developer API credits 2026 batch 1', 'url': 'https://vendor.example/promo'}, source, 'n')
        self.assertEqual(canonical_key(first), canonical_key(second))
        self.assertNotEqual(first.batch_id, second.batch_id)
        self.assertEqual(second.metadata['batch_evidence']['year'], '2026')
        with tempfile.TemporaryDirectory(dir=TEMP) as td:
            db = Database(Path(td) / 'radar.db')
            self.assertTrue(db.upsert_candidate(first).notify)
            self.assertFalse(db.upsert_candidate(first).notify)
            self.assertTrue(db.upsert_candidate(second).notify)
            self.assertFalse(db.upsert_candidate(second).notify)

    def test_chinese_explicit_annual_batch_preserves_capacity(self):
        source = {'id': 'vendor', 'platform': 'Vendor', 'official': True}
        one = build_candidate({'title': '开发者免费额度 2025年第1批 2000积分', 'url': 'https://vendor.example/promo'}, source, 'n')
        two = build_candidate({'title': '开发者免费额度 2026年第1批 2000积分', 'url': 'https://vendor.example/promo'}, source, 'n')
        different = build_candidate({'title': '开发者免费额度 2026年第1批 5000积分', 'url': 'https://vendor.example/promo'}, source, 'n')
        self.assertEqual(canonical_key(one), canonical_key(two))
        self.assertNotEqual(one.batch_id, two.batch_id)
        self.assertNotEqual(canonical_key(two), canonical_key(different))

    def test_published_year_does_not_create_annual_batch_identity(self):
        source = {'id': 'vendor', 'platform': 'Vendor', 'official': True}
        first = build_candidate({'title': 'Developer API credits batch 1', 'url': 'https://vendor.example/promo', 'published_at': '2025-10-11'}, source, 'n')
        second = build_candidate({'title': 'Developer API credits batch 1', 'url': 'https://vendor.example/promo', 'published_at': '2026-10-11'}, source, 'n')
        self.assertEqual(first.batch_id, second.batch_id)
        self.assertNotIn('year', second.metadata['batch_evidence'])

    def test_explicit_official_batch_is_new_and_repeated_batch_is_not(self):
        source = {'id': 'vendor', 'platform': 'Vendor', 'official': True}
        first = build_candidate({'title': 'Developer API credits batch 1', 'url': 'https://vendor.example/promo'}, source, 'n')
        second = build_candidate({'title': 'Developer API credits batch 2', 'url': 'https://vendor.example/promo'}, source, 'n')
        self.assertTrue(first.batch_id)
        self.assertNotEqual(first.batch_id, second.batch_id)
        self.assertEqual(canonical_key(first), canonical_key(second))
        with tempfile.TemporaryDirectory(dir=TEMP) as td:
            db = Database(Path(td) / 'radar.db')
            self.assertTrue(db.upsert_candidate(first).notify)
            self.assertFalse(db.upsert_candidate(first).notify)
            self.assertTrue(db.upsert_candidate(second).notify)

    def test_repost_batch_label_is_not_trusted(self):
        source = {'id': 'forum', 'platform': 'Forum', 'official': False}
        candidate = build_candidate({'title': '免费 API 第2批', 'url': 'https://forum.example/1'}, source, 'n')
        self.assertEqual(candidate.batch_id, '')

    def test_no_batch_is_invented_from_dates(self):
        source = {'id': 'vendor', 'platform': 'Vendor', 'official': True}
        candidate = build_candidate({'title': 'Free API credits', 'url': 'https://vendor.example/1',
            'published_at': '2026-10-11T00:00:00Z'}, source, 'n')
        self.assertEqual(candidate.batch_id, '')

    def test_chinese_official_batch_marker_is_saved_as_evidence(self):
        source = {'id': 'vendor', 'platform': 'Vendor', 'official': True}
        candidate = build_candidate({'title': '开发者免费额度 第3批', 'url': 'https://vendor.example/1'}, source, 'n')
        self.assertTrue(candidate.batch_id)
        self.assertEqual(candidate.metadata['batch_evidence']['marker'], '第3批')
