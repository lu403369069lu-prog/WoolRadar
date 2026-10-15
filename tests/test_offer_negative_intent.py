import unittest
from core.collector import contains_keyword

KEYWORDS = ['free VPS', 'giveaway', 'AI credits', 'free API', 'Cursor Pro',
            'Claude', 'Gemini', 'GitHub', 'developer perks', 'trial', 'promo code']


class OfferIntentBoundaryTests(unittest.TestCase):
    def test_denied_free_vps(self):
        self.assertFalse(contains_keyword('We do not offer a free VPS any more.', KEYWORDS))

    def test_request_is_not_available_offer(self):
        self.assertFalse(contains_keyword('I need a free VPS, where can I find one?', KEYWORDS))

    def test_promotion_ended(self):
        self.assertFalse(contains_keyword('The free VPS promotion has ended.', KEYWORDS))

    def test_giveaway_closed(self):
        self.assertFalse(contains_keyword('The free VPS giveaway is no longer available.', KEYWORDS))

    def test_paid_plan_not_free(self):
        self.assertFalse(contains_keyword('Free VPS access is included only with our paid plan.', KEYWORDS))

    def test_true_free_vps_stays_positive(self):
        self.assertTrue(contains_keyword('A free VPS is available for new registrations.', KEYWORDS))

    def test_new_offer_after_old_end(self):
        self.assertTrue(contains_keyword(
            'The earlier promotion ended. New free VPS offer is available now.', KEYWORDS))


if __name__ == '__main__':
    unittest.main()
