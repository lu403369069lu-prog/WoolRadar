"""Synthetic-only DNS-label regressions for public-only producer and blind sampler.

No network, DNS authority, external eligibility or private user data.
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
SPEC = importlib.util.spec_from_file_location('dns_label_sampler', SAMPLER_PATH)
assert SPEC is not None and SPEC.loader is not None
SAMPLER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SAMPLER)

INVALID = (
    '.example.org', 'a-.example.org', 'a.-b.example.org',
    'example..org', 'example.org.abc-.net',
    'a' * 64 + '.org', 'a.' * 126 + 'org',
)
PUBLIC = (
    'example.org', 'sub.example.org', 'a-b.example.org',
    'a.' + 'b' * 63 + '.org', 'home.arpa.info',
)
PRIVATE = (
    'home.arpa', 'router.home.arpa', 'localhost', 'svc.internal',
    '127.0.0.1', '169.254.169.254',
)


class ProducerAndSamplerHostnameBoundary(unittest.TestCase):
    def test_malformed_dns_labels_are_not_public_producer_identity(self):
        for host in INVALID:
            with self.subTest(host=host):
                url, preserved = _clean_url_identity('https://' + host + '/offers')
                self.assertFalse(preserved)
                self.assertEqual(url, '[non-public host redacted]')

    def test_malformed_dns_labels_cannot_enter_sampler(self):
        for host in INVALID:
            with self.subTest(host=host):
                self.assertIsNone(SAMPLER.canonical_public_url('https://' + host + '/offers'))

    def test_public_hostnames_still_keep_offer_identity(self):
        for host in PUBLIC:
            with self.subTest(host=host):
                url = 'https://' + host + '/offers?batch=fall'
                self.assertEqual(_clean_url_identity(url), (url, True))
                self.assertEqual(SAMPLER.canonical_public_url(url), url)

    def test_private_names_stay_excluded_by_both_gates(self):
        for host in PRIVATE:
            with self.subTest(host=host):
                url = 'https://' + host + '/offers'
                clean, preserved = _clean_url_identity(url)
                self.assertFalse(preserved)
                self.assertEqual(clean, '[non-public host redacted]')
                self.assertIsNone(SAMPLER.canonical_public_url(url))

    def test_untrusted_identity_claim_cannot_launder_malformed_host(self):
        source = {
            'schema_version': 1, 'public_only': True, 'source_id': 'synthetic',
            'rows': [{'url': 'https://a-.example.org/apply', 'title': 'Synthetic',
                      'summary': 'No real campaign',
                      'url_identity_preserved': True, 'url_sanitized': False}],
        }
        frozen = SAMPLER.freeze_public_sources([(source, 'a' * 64)], limit=1)
        self.assertEqual(frozen['rows'], [])
        self.assertEqual(frozen['sources'][0]['invalid_rows'], 1)


if __name__ == '__main__':
    unittest.main()
