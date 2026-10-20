"""A calendar year alone is not a vendor identity in generic benefit ads."""
import unittest

from core.dedup import canonical_key
from core.models import Candidate


def offer(title, url):
    return Candidate("source-node", "public-feed", title, url)


class GenericYearOfferIdentityTests(unittest.TestCase):
    def test_year_does_not_merge_unrelated_generic_token_offers(self):
        title = "Get 2026 50 AI tokens for free"
        self.assertNotEqual(canonical_key(offer(title, "https://vendor-one.example/offer")),
                            canonical_key(offer(title, "https://vendor-two.example/offer")))

    def test_same_vendor_tracking_noise_still_joins(self):
        title = "Get 2026 50 AI tokens for free"
        self.assertEqual(
            canonical_key(offer(title, "https://vendor-one.example/offer?utm_campaign=post")),
            canonical_key(offer(title, "https://vendor-one.example/offer#info")))

    def test_year_remains_part_of_campaign_identity_at_same_url(self):
        url = "https://vendor-one.example/offer"
        self.assertNotEqual(canonical_key(offer("Get 2026 50 AI tokens for free", url)),
                            canonical_key(offer("Get 2027 50 AI tokens for free", url)))

    def test_branded_year_campaign_still_joins_across_posts(self):
        title = "ExampleAI 2026 50 tokens launch"
        self.assertEqual(canonical_key(offer(title, "https://community-one.example/post/1")),
                         canonical_key(offer(title, "https://community-two.example/post/3")))


if __name__ == "__main__":
    unittest.main()
