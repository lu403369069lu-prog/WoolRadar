"""Source-bound scope guard for numbered and Unicode-bullet grant feeds.

Synthetic examples do not assert any real grant, eligibility, or live offer.
"""
import unittest

from core.developer_grants import is_developer_grant_lead, has_grant_application_denial


class NumberedAndUnicodeGrantScope(unittest.TestCase):
    def test_three_numbered_projects_cannot_stitch_one_false_grant(self):
        source = (
            "1. Project Cedar: Open-source developers are researching funding.\n"
            "2. Project Birch: Applications are now open for conference speakers.\n"
            "3. Project Elm: Grant amount: $500 for local students.")
        self.assertFalse(is_developer_grant_lead(source))

    def test_parenthesized_numbered_list_cannot_stitch(self):
        source = (
            "1) Developers ask about funding programs.\r\n"
            "2) Applications are open for an unrelated contest.\r\n"
            "3) Grant amount: $700 for local libraries.")
        self.assertFalse(is_developer_grant_lead(source))

    def test_unicode_bullet_list_cannot_stitch(self):
        source = (
            "• Open-source developer funding update.\n"
            "• Applications are now open for a separate event.\n"
            "• Grant amount: $900 for a separate project.")
        self.assertFalse(is_developer_grant_lead(source))

    def test_single_numbered_project_with_complete_cues_is_still_a_lead(self):
        self.assertTrue(is_developer_grant_lead(
            "1. Open-source maintainer grant. Applications are now open. Grant amount: $500.\n"
            "2. An unrelated conference schedule."))

    def test_global_denial_keeps_precedence_with_numbered_blocks(self):
        source = (
            "1. Open-source developer grant. Applications are now open. Grant amount: $500.\n"
            "2. Official update: grant applications are now closed.")
        self.assertFalse(is_developer_grant_lead(source))
        self.assertTrue(has_grant_application_denial(source))

    def test_synthetic_fee_required_is_still_not_free_grant(self):
        source = (
            "1) Open-source maintainer grant. Applications are now open. Grant amount: $600.\n"
            "2) Application fee: $20.")
        self.assertFalse(is_developer_grant_lead(source))


if __name__ == "__main__":
    unittest.main()
