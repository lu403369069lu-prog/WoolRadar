"""Unseen synthetic reason codes; NEVER qualify real grants from diagnostics."""
import json
import unittest
from core.developer_grants import is_developer_grant_lead
from core.grant_lead_diagnostics import (
    diagnose_developer_grant_lead, aggregate_diagnostics)

TRUE='Open-source developer grants for maintainers. Applications are now open. Grant amount: $500.'
CLOSED='Open-source developer grants for maintainers. Applications are now closed. Grant amount: $500.'
QUESTION='Can I apply to an open-source developer grant? Applications are open. Grant amount: $500.'
SEPARATE=('- Open-source developers researching funding.\n'
          '- Applications are now open to separate event speakers.\n'
          '- Grant amount: $900 for school organizations.')

class GrantDiagnosticParity(unittest.TestCase):
    def test_positive_unverified_lead_is_not_called_eligibility(self):
        row=diagnose_developer_grant_lead(TRUE)
        self.assertEqual(row['selected'],is_developer_grant_lead(TRUE))
        self.assertTrue(row['selected'])
        self.assertEqual(row['reason'],'unverified_lead_candidate')
        self.assertTrue(row['best_section']['all_signals'])
        self.assertNotIn('eligible',json.dumps(row).lower())

    def test_closed_program_denial_preserved(self):
        row=diagnose_developer_grant_lead(CLOSED)
        self.assertFalse(row['selected'])
        self.assertEqual(row['reason'],'negated_application')

    def test_applicant_question_not_official_program(self):
        row=diagnose_developer_grant_lead(QUESTION)
        self.assertFalse(row['selected'])
        self.assertEqual(row['reason'],'applicant_question')

    def test_unrelated_bullets_do_not_stitch_one_grant(self):
        row=diagnose_developer_grant_lead(SEPARATE)
        self.assertFalse(row['selected'])
        self.assertEqual(row['reason'],'no_self_contained_positive_section')
        self.assertEqual(row['sections_examined'],3)

    def test_no_application_fee_exception_does_not_make_a_paid_grant(self):
        text=TRUE+' No application fee is required.'
        row=diagnose_developer_grant_lead(text)
        self.assertTrue(row['selected'])
        self.assertFalse(row['global_denial_flags']['other_denial'])

    def test_real_payment_requirement_still_denied(self):
        row=diagnose_developer_grant_lead(TRUE+' Application fee: $20.')
        self.assertFalse(row['selected'])
        self.assertEqual(row['reason'],'closed_paid_or_personal_request')

    def test_invalid_empty_and_oversize_fail_closed(self):
        for value in (None,{},[],0,'','x'*6001):
            with self.subTest(kind=type(value).__name__):
                row=diagnose_developer_grant_lead(value)
                self.assertFalse(row['selected'])
                self.assertEqual(row['sections_examined'],0)

    def test_aggregate_counts_without_revealing_any_source_sentence(self):
        texts=[TRUE,CLOSED,QUESTION,SEPARATE,'private looking token=synthetic-not-secret']
        result=aggregate_diagnostics(texts)
        self.assertEqual(result['records'],5)
        self.assertEqual(result['candidate_leads'],1)
        self.assertEqual(sum(result['reasons'].values()),5)
        serialized=json.dumps(result)
        for value in ('synthetic-not-secret','Open-source','Can I apply'):
            self.assertNotIn(value,serialized)

    def test_diagnostics_never_change_canonical_selection(self):
        samples=[TRUE,CLOSED,QUESTION,SEPARATE,TRUE+' No application fee is required.',
                 TRUE+' Application fee: $20.']
        for source in samples:
            with self.subTest(source_length=len(source)):
                self.assertEqual(diagnose_developer_grant_lead(source)['selected'],
                                 is_developer_grant_lead(source))

if __name__=='__main__':unittest.main()
