import unittest
from core.collector import contains_keyword

class ExplicitDeveloperBenefitContracts(unittest.TestCase):
    def test_current_certification_fee_waiver(self):
        for text in [
            'The developer certification exam fee is now waived for verified students.',
            'Students: the software certification examination fee is waived for approved learners.',
        ]:
            with self.subTest(text=text):
                self.assertTrue(contains_keyword(text, ['developer perks']))

    def test_conditional_developer_event_support_is_only_a_lead(self):
        for text in [
            "Open-source AI community events: we're looking for hosts. Organizers will receive T-shirts and stickers. Apply to host a Fest.",
            "Developer hackathon: as a host, you'll receive participant swag. Your event may be eligible for food reimbursement. Applications are open.",
            "Open-source AI events: host a Fest. We'll provide funding to help cover food and drink.",
        ]:
            with self.subTest(text=text):
                self.assertTrue(contains_keyword(text,['developer perks']))

    def test_fee_and_event_counterexamples(self):
        for text in [
            'The developer certification exam fee is not waived for students.',
            'The developer certification exam fee was waived last year.',
            'The developer certification exam fee is now waived, but this offer has ended.',
            'Can we get the developer certification exam fee waived?',
            'Students pay an exam fee for the software certification.',
            'The parking exam fee is now waived for drivers.',
            'Developer hackathon: organizers will receive swag. Applications are closed.',
            'Developer hackathon: organizers will not receive swag. Apply to host.',
            "Developer hackathon: organizers won't receive funding. Apply to host.",
            'Can we get funding for our open-source event?',
            'Open-source meetup organizer story, with no offered support.',
            'Company picnic: hosts will receive T-shirts. Apply to host.',
        ]:
            with self.subTest(text=text):
                self.assertFalse(contains_keyword(text,['developer perks']))

    def test_keyword_toggle_remains_respected(self):
        self.assertFalse(contains_keyword('Developer certification exam fee is now waived for students.',[]))

    def test_independent_review_counterexamples(self):
        for name,text in [('closed-suffix', 'The software certification exam fee is now waived. This offer is over.'), ('question', 'Does anyone know whether the developer certification exam fee is now waived?'), ('paid-condition', 'The software certification exam fee is now waived only with a paid subscription.'), ('quoted-past', "Last year's announcement said: 'The developer certification exam fee is now waived for students'."), ('unrelated-certification-scope', 'Software industry news. The driving exam fee is now waived for motorists.'), ('unrelated-event-scope', 'Developer biography. Company picnic hosts will receive T-shirts. Apply to host a Fest.')]:
            with self.subTest(case=name):
                self.assertFalse(contains_keyword(text,['developer perks']))

    def test_technical_domain_review(self):
        for text,expected in [
            ('Driving certification examination fee is now waived for students.',False),
            ('Software hackathon: apply to host a Fest. Organizers will receive participant swag.',True),
        ]:
            with self.subTest(text=text):
                self.assertEqual(contains_keyword(text,['developer perks']),expected)

if __name__=='__main__': unittest.main()
