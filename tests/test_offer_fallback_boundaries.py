"""Adversarial regression, not independently frozen holdout metrics."""
import unittest
from core.collector import contains_keyword

KEYWORDS=['free VPS','giveaway','AI credits','free API','Cursor Pro','Claude','Gemini','GitHub','developer perks','trial','promo code']

class OfferFallbackBoundaryTests(unittest.TestCase):
    def test_expired_credit_award_is_not_a_current_offer(self):
        self.assertFalse(contains_keyword('The startup grant offers $500 cloud credits but the program has ended.',KEYWORDS))
    def test_request_for_credit_provider_is_not_an_announcement(self):
        self.assertFalse(contains_keyword('Is there any provider that offers $100 cloud credits?',KEYWORDS))
    def test_closed_free_start_is_not_a_current_offer(self):
        self.assertFalse(contains_keyword('Start using for free is no longer available.',KEYWORDS))
    def test_coupon_closed_in_same_statement_is_not_available(self):
        self.assertFalse(contains_keyword('Use coupon code WELCOME; this campaign has ended.',KEYWORDS))
    def test_live_credit_award_is_kept(self):
        self.assertTrue(contains_keyword('The startup grant offers $500 cloud credits to new developers.',KEYWORDS))
    def test_free_base_with_optional_upgrade_is_kept(self):
        self.assertTrue(contains_keyword('Start using for free; paid upgrades are optional.',KEYWORDS))

if __name__=='__main__':unittest.main()
