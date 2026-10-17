"""PR39 exact-source boundary: private-use home.arpa must not become blind gold.

Synthetic metadata only; no live DNS, personal eligibility, external publishing,
or Windows/SQLite business acceptance is claimed.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

from core.public_corpus import _clean_url_identity

SAMPLER_PATH = (
    Path(__file__).resolve().parents[1]
    / 'independent-quality/public-corpus-blind-dedup-20261016'
    / 'freeze_public_sample_dedup.py'
)
SPEC = importlib.util.spec_from_file_location('backlog_home_arpa_sampler', SAMPLER_PATH)
assert SPEC is not None and SPEC.loader is not None
SAMPLER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SAMPLER)


class PublicBlindRootDomainBoundary(unittest.TestCase):
    def test_home_arpa_root_is_not_public_even_with_untrusted_identity_claim(self):
        self.assertIsNone(SAMPLER.canonical_public_url('http://home.arpa/admin'))
        self.assertIsNone(SAMPLER.canonical_public_url('https://HOME.ARPA./offers?batch=1'))

    def test_children_and_private_ipv4_stay_rejected(self):
        for value in (
            'http://router.home.arpa/settings',
            'http://127.0.0.1/admin',
            'https://169.254.169.254/latest/meta-data',
        ):
            with self.subTest(value=value):
                self.assertIsNone(SAMPLER.canonical_public_url(value))

    def test_public_controls_do_not_overblock_similar_hostnames(self):
        for value in (
            'https://example.org/program?batch=2',
            'https://home.arpa.info/',
        ):
            with self.subTest(value=value):
                self.assertEqual(SAMPLER.canonical_public_url(value), value)

    def test_producer_and_sampler_agree_on_home_arpa_root(self):
        url, preserved = _clean_url_identity('http://home.arpa/admin')
        self.assertEqual(url, '[non-public host redacted]')
        self.assertFalse(preserved)
        self.assertIsNone(SAMPLER.canonical_public_url('http://home.arpa/admin'))

    def test_untrusted_corpus_identity_flag_cannot_admit_private_root(self):
        source = {
            'schema_version': 1,
            'public_only': True,
            'source_id': 'synthetic-public-only',
            'rows': [{
                'url': 'http://home.arpa/admin',
                'title': 'Synthetic private administrative page',
                'summary': 'Not an external public grant',
                'url_identity_preserved': True,
                'url_sanitized': False,
            }],
        }
        frozen = SAMPLER.freeze_public_sources([(source, 'a' * 64)], limit=1)
        self.assertEqual(frozen['rows'], [])
        self.assertEqual(frozen['sources'][0]['selected_rows'], 0)
        self.assertEqual(frozen['sources'][0]['invalid_rows'], 1)
        self.assertTrue(frozen['upstream_identity_fully_preserved'])


if __name__ == '__main__':
    unittest.main()
