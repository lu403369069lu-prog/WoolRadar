import unittest
from core.developer_grants import is_developer_grant_lead
from core.collector import contains_keyword
class GrantNegationContracts(unittest.TestCase):
    def test_negated_base_verb_and_passive_acceptance_cannot_become_leads(self):
        for phrase in ['This fund does not accept applications.','This program will not accept applications.','Applications are not being accepted.', 'This fund did not accept applications.',
                       'The developer program would not accept applications.']:
            text=phrase+' Open-source maintainers grant. Apply today. Selected projects receive $750.'
            with self.subTest(phrase=phrase):
                self.assertFalse(is_developer_grant_lead(text))
                self.assertFalse(contains_keyword(text,['developer perks']))
    def test_active_application_with_fee_waiver_remains_a_lead(self):
        text='Open-source maintainers grant applications are open. No application fee is required. Selected projects receive $750.'
        self.assertTrue(is_developer_grant_lead(text))
        self.assertTrue(contains_keyword(text,['developer perks']))
