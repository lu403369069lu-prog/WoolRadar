"""Regression contracts for SPA fragment marketing trackers."""
import unittest
from freeze_public_sample_dedup import canonical_public_url


class SpaFragmentTrackerTests(unittest.TestCase):
    def test_strip_marketing_keys_without_changing_business_identity(self):
        url = 'https://example.org/#/claim?batch=2026&utm_source=ad&fbclid=TRACKING_CANARY&campaign=alpha'
        self.assertEqual(canonical_public_url(url),
                         'https://example.org/#/claim?batch=2026&campaign=alpha')

    def test_only_marketing_keys_leave_plain_spa_route(self):
        self.assertEqual(
            canonical_public_url('https://example.org/#/claim?utm_medium=email&gclid=TRACKING_CANARY'),
            'https://example.org/#/claim')

    def test_plain_query_and_spa_query_strip_trackers_independently(self):
        self.assertEqual(
            canonical_public_url('https://example.org/join?batch=2&utm_term=TRACKER#/claim?phase=3&mc_eid=TRACKER'),
            'https://example.org/join?batch=2#/claim?phase=3')

    def test_reject_nested_encoded_secrets_and_keep_business_query(self):
        self.assertIsNone(canonical_public_url('https://example.org/#/claim?%2574oken=SECRET'))
        self.assertEqual(canonical_public_url('https://example.org/#/claim?batch=2026'),
                         'https://example.org/#/claim?batch=2026')


if __name__ == '__main__':
    unittest.main()

class UrlControlIdentityTests(unittest.TestCase):
    def test_raw_controls_and_invisible_format_cannot_change_url_identity(self):
        for url in (
            'https://example.org/cl\naim?batch=2',
            'https://example.org/cl\taim',
            '\x01https://example.org/claim',
            'https://example.org/claim\x7f?batch=2',
            'https://example.org/#/cl\naim?batch=2',
            'https://example.org/#/claim?batch=\x00X',
            'https://example.org/claim\u202eoffer',
            'https://example.org/#/claim\u200b?batch=2',
        ):
            with self.subTest(url=repr(url)):
                self.assertIsNone(canonical_public_url(url))

    def test_legitimate_unicode_query_remains_usable(self):
        self.assertEqual(canonical_public_url('https://example.org/#/claim?region=中国'),
                         'https://example.org/#/claim?region=中国')

class UrlOuterWhitespaceIdentityTests(unittest.TestCase):
    def test_leading_and_trailing_whitespace_cannot_change_public_identity(self):
        for url in (' https://example.org/claim', 'https://example.org/claim ',
                    '\u00a0https://example.org/claim'):
            with self.subTest(url=repr(url)):
                self.assertIsNone(canonical_public_url(url))
