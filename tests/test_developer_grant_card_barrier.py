import unittest
from core.developer_grants import is_developer_grant_lead
from core.collector import contains_keyword


class GrantCardBarrierContracts(unittest.TestCase):
    def test_required_payment_method_cannot_be_advertised_as_free_grant(self):
        restrictions = (
            "Credit card required to apply.",
            "Applicants must provide a debit card to submit.",
            "Payment method is required to apply.",
            "Applicants must add a credit card before submitting.",
        )
        for restriction in restrictions:
            with self.subTest(restriction=restriction):
                text = ("GitHub free open-source developer grant. Applications are open. "
                        "Grant amount: $500. " + restriction)
                self.assertFalse(is_developer_grant_lead(text))
                self.assertFalse(contains_keyword(text, ['developer perks']))
                self.assertFalse(contains_keyword(text, ['GitHub']))

    def test_explicit_no_card_needed_remains_a_discovery_lead(self):
        safe = (
            "No credit card required.",
            "Without a credit card.",
            "A credit card is not required.",
        )
        for statement in safe:
            with self.subTest(statement=statement):
                text = ("GitHub free open-source developer grant. Applications are open. "
                        "Grant amount: $500. " + statement)
                self.assertTrue(is_developer_grant_lead(text))
                self.assertTrue(contains_keyword(text, ['developer perks']))

if __name__ == '__main__':
    unittest.main()
