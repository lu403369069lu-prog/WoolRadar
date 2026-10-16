import unittest
from core.developer_grants import is_developer_grant_lead

class GrantLeadTests(unittest.TestCase):
    def test_realistic_open_maintainer_fund(self):
        self.assertTrue(is_developer_grant_lead('GitHub Secure Open Source Fund is accepting applications from open-source maintainers; selected projects receive $10,000 in funding'))
    def test_rolling_fund(self):
        self.assertTrue(is_developer_grant_lead('Open source maintainer security grants: rolling applications are open; approved maintainers receive $5,000 per project'))
    def test_official_faq_benefit_table_wording(self):
        self.assertTrue(is_developer_grant_lead('GitHub Secure Open Source Fund for maintainers: rolling applications are open; Funding: $10,000 per project'))
    def test_closed_fund(self):
        self.assertFalse(is_developer_grant_lead('GitHub open source fund applications have closed. Selected projects received $10,000.'))
    def test_paid_application(self):
        self.assertFalse(is_developer_grant_lead('Developer fund is accepting applications, approved applicants receive $10,000, but there is a paid application fee'))
    def test_donation_not_free_grant(self):
        self.assertFalse(is_developer_grant_lead('GitHub open source fund is accepting donations of $10,000, become a sponsor today'))
    def test_historical_award(self):
        self.assertFalse(is_developer_grant_lead('The open source security fund awarded developers $10,000 in 2022'))
    def test_security_project_no_benefit(self):
        self.assertFalse(is_developer_grant_lead('Open source developer funding project publishes its annual security report'))
    def test_application_question(self):
        self.assertFalse(is_developer_grant_lead('Is there an open source fund accepting applications offering $10,000 for selected developers?'))
    def test_bare_fund_open_without_cash_benefit(self):
        self.assertFalse(is_developer_grant_lead('GitHub maintainer fund applications are open. The dashboard includes a security scanner'))
    def test_ineligible_generic_startup_funding(self):
        self.assertFalse(is_developer_grant_lead('Startup Series A funding $10,000: applications are open for any company'))

if __name__=='__main__': unittest.main()
