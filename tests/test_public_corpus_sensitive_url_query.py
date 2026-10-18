"""Public-only sampler must not trust forged identity on nested-encoded query metadata."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from core.public_corpus import _clean_url_identity, record_public_sample

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / 'independent-quality/public-corpus-blind-dedup-20261016/freeze_public_sample_dedup.py'
SPEC = importlib.util.spec_from_file_location('query_guard_sampler', FILE)
sampler = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sampler)
SOURCE = {'id':'nested-query-check','auth':'public_feed','kind':'rss','platform':'synthetic'}

class NestedQueryCanary(unittest.TestCase):
    def test_sampler_rejects_private_nested_encoded_query_despite_forged_identity(self):
        cases = (
            'https://publisher.org/offer?batch=fall&%2574oken=SYNTHETIC_CANARY',
            'https://publisher.org/offer?ref=user%2540example.org',
            'https://publisher.org/offer?%2561pi_key=SYNTHETIC_CANARY',
            'https://publisher.org/offer?batch=fall#/?%2574oken=SYNTHETIC_CANARY',
        )
        for url in cases:
            with self.subTest(url=url), tempfile.TemporaryDirectory() as root:
                self.assertIsNone(sampler.canonical_public_url(url))
                cleaned, trusted = _clean_url_identity(url)
                self.assertFalse(trusted)
                self.assertNotIn('SYNTHETIC_CANARY', cleaned)
                item = {'schema_version':1,'public_only':True,'source_id':'nested-query-check',
                        'rows':[{'url':url,'title':'Synthetic grant','summary':'Synthetic only',
                                 'url_identity_preserved':True,'url_sanitized':False}]}
                result = sampler.freeze_public_sources([(item, 'a'*64)])
                self.assertEqual(result['rows'], [])
                self.assertEqual(result['sources'][0]['invalid_rows'], 1)

    def test_positive_query_selectors_remain_distinct_and_public(self):
        first = 'https://publisher.org/offer?batch=fall&utm_campaign=fall'
        second = 'https://publisher.org/offer?batch=winter&utm_campaign=winter'
        self.assertEqual(sampler.canonical_public_url(first), first)
        self.assertEqual(sampler.canonical_public_url(second), second)
        self.assertNotEqual(sampler.canonical_public_url(first), sampler.canonical_public_url(second))

if __name__ == '__main__':
    unittest.main()
