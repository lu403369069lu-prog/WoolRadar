"""Synthetic-only secret-bearing URL path rejection at producer and sampler.

Does not use real tokens, users, external requests, account data, or DNS.
"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from core.public_corpus import _clean_url_identity, record_public_sample

HERE = Path(__file__).resolve().parents[1]
SAMPLER = HERE / 'independent-quality/public-corpus-blind-dedup-20261016/freeze_public_sample_dedup.py'
SPEC = importlib.util.spec_from_file_location('isolated_public_sampler', SAMPLER)
assert SPEC is not None and SPEC.loader is not None
sampler = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sampler)

SRC = {'id': 'path-check', 'auth': 'public_feed', 'kind': 'rss', 'platform': 'synthetic'}
PRIVATE = (
    'https://publisher.org/token/SYNTHETIC_ONLY',
    'https://publisher.org/%74oken/SYNTHETIC_ONLY',
    'https://publisher.org/account/person%40example.org',
    'https://publisher.org/offer/1234567890123456',
    'https://publisher.org/#/token/SYNTHETIC_ONLY',
    'https://publisher.org/#!/token/SYNTHETIC_ONLY',
)

class PublicSensitivePathBoundary(unittest.TestCase):
    def test_untrusted_producer_redacts_secret_path_and_disclaims_url_identity(self):
        for raw in PRIVATE:
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as root:
                result = record_public_sample(
                    Path(root), 'synthetic', SRC,
                    [{'url': raw, 'title': 'Open public grant at ' + raw,
                      'summary': 'Do not publish ' + raw}],
                    [False],
                )
                self.assertIsNotNone(result)
                doc = json.loads(result.read_text(encoding='utf-8'))
                row = doc['rows'][0]
                self.assertFalse(row['url_identity_preserved'])
                self.assertTrue(row['url_sanitized'])
                self.assertNotIn('SYNTHETIC_ONLY', result.read_text(encoding='utf-8'))
                self.assertNotIn('1234567890123456', result.read_text(encoding='utf-8'))
                self.assertNotIn('person%40example.org', result.read_text(encoding='utf-8'))
                self.assertNotIn('token/', row['url'].lower())
                self.assertEqual(sampler.freeze_public_sources([(doc, 'a' * 64)])['rows'], [])

    def test_independent_sampler_rejects_forged_identity_true_with_sensitive_url_path(self):
        for raw in PRIVATE:
            with self.subTest(raw=raw):
                self.assertIsNone(sampler.canonical_public_url(raw))
                forged = {'schema_version': 1, 'public_only': True, 'source_id': 'path-check',
                          'rows': [{'url': raw, 'title': 'Synthetic', 'summary': 'Synthetic',
                                    'url_identity_preserved': True, 'url_sanitized': False}]}
                report = sampler.freeze_public_sources([(forged, 'b' * 64)], limit=1)
                self.assertEqual(report['rows'], [])
                self.assertEqual(report['sources'][0]['invalid_rows'], 1)

    def test_non_sensitive_public_path_keeps_exact_identity(self):
        public = 'https://publisher.org/offer/batch-fall?id=17'
        self.assertEqual(_clean_url_identity(public), (public, True))
        self.assertEqual(sampler.canonical_public_url(public), public)

if __name__ == '__main__':
    unittest.main()
