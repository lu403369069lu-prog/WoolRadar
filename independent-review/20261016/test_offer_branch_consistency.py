"""Fresh synthetic contract counterexamples, not an independent business holdout."""
import os,sys,unittest
sys.path.insert(0,os.environ['REVIEW_WOOL_ROOT'])
from core.collector import contains_keyword
KEYWORDS=['free VPS','giveaway','AI credits','free API','Cursor Pro','Claude','Gemini','GitHub','developer perks','trial','promo code']
class BranchConsistency(unittest.TestCase):
 def test_ended_monetary_grant_is_not_resurrected_by_award_fallback(self):
  self.assertFalse(contains_keyword('The startup grant offers $500 cloud credits but the program has ended.',KEYWORDS))
 def test_request_is_not_resurrected_by_award_fallback(self):
  self.assertFalse(contains_keyword('Is there any provider that offers $100 cloud credits?',KEYWORDS))
 def test_withdrawn_free_start_is_not_an_offer(self):
  self.assertFalse(contains_keyword('Start using for free is no longer available.',KEYWORDS))
 def test_closed_coupon_is_not_an_offer(self):
  self.assertFalse(contains_keyword('Use coupon code WELCOME; this campaign has ended.',KEYWORDS))
 def test_live_monetary_grant_is_still_a_lead(self):
  self.assertTrue(contains_keyword('Our startup grant offers $500 cloud credits for new applicants.',KEYWORDS))
 def test_optional_paid_upgrade_does_not_remove_free_base(self):
  self.assertTrue(contains_keyword('Our email testing tool is free; paid upgrades are optional.',KEYWORDS))
if __name__=='__main__':unittest.main(verbosity=2)
