"""Statement-wide denials and explicit new-offer transitions, regression only."""
import unittest
from core.collector import contains_keyword
KEYWORDS=['free VPS','giveaway','AI credits','free API','Cursor Pro','Claude','Gemini','GitHub','developer perks','trial','promo code']
class OfferClauseConsistencyTests(unittest.TestCase):
    def test_direct_offer_cannot_ignore_closed_suffix(self):
        self.assertFalse(contains_keyword('Free API access; this campaign has ended.',KEYWORDS))
    def test_brand_offer_cannot_ignore_closed_suffix(self):
        self.assertFalse(contains_keyword('GitHub promotion; this campaign has ended.',KEYWORDS))
    def test_explicit_new_credit_offer_is_not_denied_by_old_closed_program(self):
        self.assertTrue(contains_keyword('The old program has ended; our new program offers $500 cloud credits to new developers.',KEYWORDS))
    def test_explicit_new_direct_offer_is_not_denied_by_old_program(self):
        self.assertTrue(contains_keyword('The old program has ended; our new program includes free API access.',KEYWORDS))
    def test_new_program_still_needs_to_be_available(self):
        self.assertFalse(contains_keyword('The old program has ended; our new program offers $500 cloud credits but is no longer available.',KEYWORDS))
    def test_free_base_optional_paid_clause_still_positive(self):
        self.assertTrue(contains_keyword('Free API access; paid upgrades are optional.',KEYWORDS))
if __name__=='__main__':unittest.main()
