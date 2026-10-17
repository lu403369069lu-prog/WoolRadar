"""Encoded semantic selectors may have origin-specific identity; never gold-equate them."""
import json
import tempfile
import unittest
from pathlib import Path
from core.public_corpus import _clean_url_identity, record_public_sample

SOURCE = {'id':'query-identity','auth':'public_feed','kind':'rss','platform':'synthetic'}

class EncodedSelectorIdentity(unittest.TestCase):
    def test_percent_encoded_unreserved_selector_loses_resource_identity(self):
        url, same = _clean_url_identity('https://example.org/offers?batch=%41')
        self.assertEqual(url, 'https://example.org/offers?batch=A')
        self.assertFalse(same)

    def test_encoded_tilde_selector_loses_resource_identity(self):
        url, same = _clean_url_identity('https://example.org/offers?promo=%7ealpha')
        self.assertEqual(url, 'https://example.org/offers?promo=~alpha')
        self.assertFalse(same)

    def test_percent_encoded_fragment_selector_loses_identity(self):
        url, same = _clean_url_identity('https://example.org/#!/view?batch=%41')
        self.assertFalse(same)
        self.assertFalse('batch=A' in url)

    def test_encoded_tracking_value_is_still_safe_to_drop(self):
        self.assertEqual(_clean_url_identity('https://example.org/offers?batch=A&utm_source=%41'),
                         ('https://example.org/offers?batch=A', True))

    def test_literal_functional_selector_stays_preserved(self):
        self.assertEqual(_clean_url_identity('https://example.org/offers?batch=A'),
                         ('https://example.org/offers?batch=A', True))

    def test_badly_encoded_selector_key_is_already_rejected(self):
        self.assertFalse(_clean_url_identity('https://example.org/offers?b%61tch=A')[1])

    def test_actual_producer_marks_canonicalized_encoded_query_ineligible(self):
        with tempfile.TemporaryDirectory() as root:
            doc = record_public_sample(Path(root), 'synthetic', SOURCE,
                [{'url':'https://example.org/offers?batch=%41','title':'Synthetic','summary':'No real data'}], [True])
            row=json.loads(doc.read_text('utf8'))['rows'][0]
            self.assertEqual(row['url'], 'https://example.org/offers?batch=A')
            self.assertFalse(row['url_identity_preserved'])

if __name__ == '__main__': unittest.main()
