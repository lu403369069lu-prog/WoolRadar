import unittest
from core.developer_grants import is_developer_grant_lead, has_grant_application_denial

class PerProjectGrantEvidence(unittest.TestCase):
    def test_three_unrelated_project_paragraphs_cannot_form_one_grant(self):
        source = ('Project Cedar: Open-source maintainers are comparing funding programs.\n\n'
                  'Project Birch: Applications are open for a software contest.\n\n'
                  'Project Elm: Grant amount: $500 for local school organizers.')
        self.assertFalse(is_developer_grant_lead(source))

    def test_three_separate_bullets_cannot_form_one_grant(self):
        source = ('- Open-source developers discuss funding changes.\n'
                  '- Another community: applications are open for speakers.\n'
                  '- A separate nonprofit: grant amount: $750.')
        self.assertFalse(is_developer_grant_lead(source))

    def test_one_project_multiple_sentences_remains_an_unverified_lead(self):
        self.assertTrue(is_developer_grant_lead(
            'Open-source developer grants for maintainers. Applications are open. Grant amount: $500.'))

    def test_current_common_applications_are_now_open_phrase(self):
        self.assertTrue(is_developer_grant_lead(
            'Open-source developer grants for maintainers. Applications are now open. Grant amount: $500.'))

    def test_one_complete_project_paragraph_works_with_unrelated_plain_text(self):
        self.assertTrue(is_developer_grant_lead(
            'Office hours and routine updates.\n\n'
            'An open-source maintainer grant program. Applications are open. Funding: $900.'))

    def test_specific_no_application_fee_is_not_inferred_to_be_paid(self):
        self.assertTrue(is_developer_grant_lead(
            'Open-source developer grants. Applications are open. Grant amount: $500. No application fee is required.'))

    def test_closed_applications_are_not_current_open_leads(self):
        self.assertFalse(is_developer_grant_lead(
            'Open-source developers grant amount: $500. Applications are now closed. Applications are open in an unrelated activity.'))

    def test_negative_answer_does_not_bypass_application_denial(self):
        self.assertTrue(has_grant_application_denial(
            'Open-source developer grant applications are not accepting applications.'))

    def test_an_application_question_is_not_official_announcement(self):
        self.assertFalse(is_developer_grant_lead(
            'Can I apply to open-source developer grant applications now open? Grant amount: $500.'))

    def test_nonstring_and_oversized_input_are_not_leads(self):
        for bad in (None, 1, {}, [], 'foo'*2500):
            with self.subTest(value=str(type(bad))):
                self.assertFalse(is_developer_grant_lead(bad))

    def test_payment_requirements_block_false_free_grant_leads(self):
        self.assertFalse(is_developer_grant_lead(
            'Open-source developer grants: applications now open. Grant amount: $500. Application fee: $20.'))

if __name__=='__main__': unittest.main()
