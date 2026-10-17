"""A user/affiliate referral selector is not anonymous public opportunity identity."""
import unittest
from core.public_corpus import _clean_url_identity

class PrivateReferralSelectors(unittest.TestCase):
    def test_query_referral_must_be_removed_and_disqualify_identity(self):
        for url in ('https://events.public-example.net/offer?ref=syntheticperson42',
                    'https://events.public-example.net/offer?offer=2026&ref=syntheticperson42'):
            with self.subTest(url=url):
                cleaned,preserved=_clean_url_identity(url)
                self.assertNotIn('syntheticperson42',cleaned)
                self.assertFalse(preserved)
                self.assertIn('/offer',cleaned)

    def test_spa_referral_does_not_survive(self):
        cleaned,preserved=_clean_url_identity('https://events.public-example.net/#/offer?ref=syntheticperson42')
        self.assertNotIn('syntheticperson42',cleaned)
        self.assertFalse(preserved)

    def test_resource_id_remains_an_admissible_selector(self):
        self.assertEqual(_clean_url_identity('https://events.public-example.net/offer?offer=2026'),
                         ('https://events.public-example.net/offer?offer=2026',True))

if __name__=='__main__':unittest.main()
