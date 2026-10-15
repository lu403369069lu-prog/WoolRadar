import unittest
from core.collector import contains_keyword

KEYWORDS=['free VPS','giveaway','AI credits','free API','Cursor Pro','Claude','Gemini','GitHub','developer perks','trial','promo code']

class FreeHostingDiagnosticTests(unittest.TestCase):
    def test_explicit_free_diagnostic_announcement(self):
        self.assertTrue(contains_keyword('We built a free email testing tool for self-hosted mail servers.',KEYWORDS))

    def test_dns_free_diagnostic_without_brand(self):
        self.assertTrue(contains_keyword('A free DNS diagnostic tool for VPS operators.',KEYWORDS))

    def test_declared_free_price(self):
        self.assertTrue(contains_keyword('Our email testing tool is free. No credit card required.',KEYWORDS))

    def test_request_not_offer(self):
        self.assertFalse(contains_keyword('I want a free email testing tool for my VPS.',KEYWORDS))
        self.assertFalse(contains_keyword('Can I get a free DNS diagnostic tool?',KEYWORDS))
        self.assertFalse(contains_keyword('Is there a free email testing tool for my VPS?',KEYWORDS))
        self.assertFalse(contains_keyword('Does anyone know a free DNS diagnostic tool?',KEYWORDS))

    def test_negated_offer(self):
        self.assertFalse(contains_keyword('We do not provide a free email testing tool.',KEYWORDS))
        self.assertFalse(contains_keyword('Our email testing tool is not free.',KEYWORDS))
        self.assertFalse(contains_keyword('A free email testing tool is not something we offer.',KEYWORDS))

    def test_withdrawn_free_tool_is_not_current_offer(self):
        self.assertFalse(contains_keyword('Our free email testing tool is no longer available.',KEYWORDS))
        self.assertFalse(contains_keyword('The free DNS diagnostic tool has been discontinued.',KEYWORDS))

    def test_paid_bundle_is_not_standalone_free_plan(self):
        self.assertFalse(contains_keyword('Buy our paid plan for $20 with a free email testing tool.',KEYWORDS))
        self.assertFalse(contains_keyword('Our free email testing tool requires a paid subscription.',KEYWORDS))
        self.assertFalse(contains_keyword('A free DNS diagnostic tool is included only with our paid plan.',KEYWORDS))

    def test_optional_paid_upgrade_keeps_free_base(self):
        self.assertTrue(contains_keyword('Our email testing tool is free; paid upgrades are optional.',KEYWORDS))

    def test_diagnostic_extension_requires_developer_perks_scope(self):
        for keywords in [[],['photo coupon'],['free VPS']]:
            self.assertFalse(contains_keyword('A free DNS diagnostic tool for VPS operators.',keywords))

    def test_generic_tool_or_consumer_freebie_not_added(self):
        self.assertFalse(contains_keyword('A free photo testing tool for editing selfies.',KEYWORDS))
        self.assertFalse(contains_keyword('We launched an email testing tool.',KEYWORDS))
        self.assertFalse(contains_keyword('Free DNS hosting service.',KEYWORDS))
