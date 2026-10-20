"""Unbranded numeric AI-token offers cannot identify a common vendor."""

import unittest

from core.dedup import canonical_key
from core.models import Candidate


def make(url, title):
    return Candidate("source-node", "public-feed", title, url)


class GenericTokenOfferIdentityTests(unittest.TestCase):
    def test_numeric_generic_tokens_are_distinct_across_vendors(self):
        title = "Get 50 AI tokens for free"
        one = make("https://one.example/offer", title)
        two = make("https://two.example/offer", title)
        self.assertNotEqual(canonical_key(one), canonical_key(two))

    def test_tracking_noise_does_not_split_same_vendor_offer(self):
        title = "Get 50 AI tokens for free"
        one = make("https://one.example/offer?utm_source=newsletter", title)
        two = make("https://one.example/offer#info", title)
        self.assertEqual(canonical_key(one), canonical_key(two))

    def test_branded_same_campaign_still_joins_cross_source(self):
        title = "ExampleAI free 50 tokens launch"
        one = make("https://forum-one.example/post/1", title)
        two = make("https://forum-two.example/post/42", title)
        self.assertEqual(canonical_key(one), canonical_key(two))


if __name__ == "__main__":
    unittest.main()
