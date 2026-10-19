"""Collector integration regression: developer-support cash grant discovery.
Requires full WoolRadar standard-library source checkout; no network or accounts.
"""
import unittest

from core.collector import contains_keyword

DEV_KEYWORDS = ["developer perks", "GitHub", "free VPS", "AI credits"]
NO_GRANT_KEYWORDS = ["GitHub", "free VPS", "AI credits"]


class OSSFundCollectorIntegration(unittest.TestCase):
    def test_explicit_current_fund_is_discoverable_unverified(self):
        text = ("GitHub Secure Open Source Fund is accepting applications from "
                "open-source maintainers; selected projects receive $10,000 in funding")
        self.assertTrue(contains_keyword(text, DEV_KEYWORDS))

    def test_disabling_developer_perks_disables_novel_grant_fallback(self):
        text = ("GitHub Secure Open Source Fund is accepting applications from "
                "open-source maintainers; selected projects receive $10,000 in funding")
        self.assertFalse(contains_keyword(text, NO_GRANT_KEYWORDS))

    def test_closed_application_does_not_resurface(self):
        text = ("GitHub open source fund applications have closed; "
                "selected maintainers received $10,000 last year")
        self.assertFalse(contains_keyword(text, DEV_KEYWORDS))

    def test_generic_github_security_article_is_not_promoted(self):
        text = "GitHub open source maintainers published the security fund annual report"
        self.assertFalse(contains_keyword(text, DEV_KEYWORDS))

    def test_paid_application_is_not_promoted(self):
        text = ("Open source developer fund accepting applications; selected developers "
                "receive $10,000 but an application fee is required")
        self.assertFalse(contains_keyword(text, DEV_KEYWORDS))


    def test_explicit_not_accepting_does_not_trigger_collector(self):
        text = ("GitHub open source developer fund is not accepting applications; "
                "selected maintainers receive $10,000")
        self.assertFalse(contains_keyword(text, DEV_KEYWORDS))

    def test_no_applications_are_open_does_not_trigger_collector(self):
        text = ("GitHub open source developer fund: no applications are open; "
                "Funding: $10,000 per project")
        self.assertFalse(contains_keyword(text, DEV_KEYWORDS))

    def test_applicant_question_does_not_trigger_collector(self):
        text = ("Can developers apply now for GitHub open source fund? "
                "Selected maintainers receive $10,000.")
        self.assertFalse(contains_keyword(text, DEV_KEYWORDS))

    def test_explicit_application_fee_waiver_is_not_a_paid_plan(self):
        text = ("GitHub open source developer grant is accepting applications. "
                "No application fee is required; selected maintainers receive $10,000.")
        self.assertTrue(contains_keyword(text, DEV_KEYWORDS))
        self.assertFalse(contains_keyword(text, NO_GRANT_KEYWORDS))


if __name__ == '__main__':
    unittest.main()
