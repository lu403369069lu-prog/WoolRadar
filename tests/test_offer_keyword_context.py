import unittest
from core.collector import contains_keyword

KEYWORDS=['trial','GitHub','Gemini','free VPS','AI credits','giveaway']


class OfferKeywordContextTests(unittest.TestCase):
    def test_actual_lowendbox_free_service_and_coupon_announcements(self):
        self.assertTrue(contains_keyword("Let's Try ServerCrate! Restic-Based Backups You Can Start Using for FREE!",KEYWORDS))
        self.assertTrue(contains_keyword("Exclusive LowEndBox Pricing: 2GB KVM VPS. You'll need our special coupon code to get these deals!",['promo code']))

    def test_free_service_requests_and_coupon_technical_context_are_not_offers(self):
        self.assertFalse(contains_keyword('I am looking for backups I can start using for free',KEYWORDS))
        self.assertFalse(contains_keyword('How our coupon code parser handles syntax',['promo code']))
        self.assertFalse(contains_keyword('We do not offer a special coupon code',['promo code']))
        self.assertFalse(contains_keyword('No special coupon code is available',['promo code']))
        self.assertFalse(contains_keyword('I need a special coupon code for this VPS',['promo code']))

    def test_no_card_and_no_expiry_are_free_plan_benefits(self):
        for text in ["You don't need a credit card to start using for free",
                     'You don’t need a credit card to start using for free',
                     'The plan never expires, start using for free',
                     'No credit card needed, start using for free']:
            self.assertTrue(contains_keyword(text,KEYWORDS),text)

    def test_official_competition_cash_credits_are_an_offer_lead(self):
        text = ('Introducing The Cold Start: pitch your startup live at Cloudflare Connect. '
                'Cloudflare is launching The Cold Start, a startup competition giving five early-stage companies '
                'five minutes on stage at Cloudflare Connect. Grand Prize winner receives $500,000 in credits, '
                'a San Francisco billboard, and an invitation to our VIP speakers dinner.')
        self.assertTrue(contains_keyword(text,KEYWORDS))

    def test_cash_credit_discussion_without_an_offer_is_not_a_lead(self):
        for text in ['I need $500 in credits for my project',
                     'Can I get $500 in credits for my project?',
                     'We do not offer $500 in credits.',
                     'Our paid package offers $500 in credits for $500.',
                     'Our credit card has a $500 limit',
                     'The winner receives a trophy. We spent $500 buying credits yesterday']:
            self.assertFalse(contains_keyword(text,KEYWORDS),text)

    def test_free_ram_and_gemini_technical_help_is_not_an_offer(self):
        self.assertFalse(contains_keyword('No issues regarding free RAM metrics. With help from Gemini, I disabled virtio_balloon.',KEYWORDS))

    def test_request_for_a_provider_trial_is_not_an_announced_trial(self):
        self.assertFalse(contains_keyword('I need to purchase a GPU server. I would prefer companies that offer a trial period of a few hours.',KEYWORDS))

    def test_brand_and_promote_substring_do_not_establish_a_promotion(self):
        self.assertFalse(contains_keyword('GitHub project feedback: we are not looking to simply promote another product.',KEYWORDS))

    def test_real_trial_and_free_brand_offers_remain_candidates(self):
        for text in ['Try our free trial','Get a 30-day trial','Gemini free API access','GitHub coupon giveaway','Free VPS offer',
                     'Gemini credits for developers','GitHub developer perks']:
            self.assertTrue(contains_keyword(text,KEYWORDS),text)

    def test_additional_announced_trials_remain_candidates(self):
        for text in ['Get a 24-hour VPS trial', 'Launch offer: 3-month trial for developers',
                     'Introducing our 30-day premium trial']:
            with self.subTest(text=text):
                self.assertTrue(contains_keyword(text, KEYWORDS))

    def test_brand_promotions_and_mixed_language_remain_candidates(self):
        for text in ['GitHub promotion: 50% off for students', 'Gemini免费API访问',
                     'GitHub优惠券限时发放']:
            with self.subTest(text=text):
                self.assertTrue(contains_keyword(text, KEYWORDS))

    def test_plural_api_and_credits_remain_candidates(self):
        for text in ['Free APIs for developers', 'AI credits for students']:
            with self.subTest(text=text):
                self.assertTrue(contains_keyword(text, ['free API', 'AI credit']))

    def test_hardware_upgrade_and_specified_trials_remain_candidates(self):
        for text in ['GitHub Student Pack: free RAM upgrade on cloud servers',
                     'Get a 30-day 8GB GPU trial', 'GitHub promotions for students']:
            with self.subTest(text=text):
                self.assertTrue(contains_keyword(text, KEYWORDS))
