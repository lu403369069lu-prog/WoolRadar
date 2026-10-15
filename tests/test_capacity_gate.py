import unittest
from datetime import datetime,timedelta,timezone
from core.models import Candidate,Evidence,Status
from core.verifier import VerificationEngine

class CapacityGateTests(unittest.TestCase):
    def setUp(self):
        self.engine=VerificationEngine()
        self.candidate=Candidate('test','vendor','Free API credits','https://vendor.example/offer')

    def proof(self,remaining,**kwargs):
        return Evidence('official','https://vendor.example/offer','vendor',claims={'open':True,'public':True,'remaining':remaining},**kwargs)

    def test_fresh_zero_capacity_is_not_claimable(self):
        result=self.engine.evaluate(self.candidate,[self.proof(0)])
        self.assertNotEqual(result.status,Status.CLAIMABLE)
        self.assertEqual(result.claim_scope,'NONE')
        self.assertFalse(result.unknown_capacity)

    def test_float_zero_is_also_exhausted(self):
        self.assertNotEqual(self.engine.evaluate(self.candidate,[self.proof(0.0)]).status,Status.CLAIMABLE)

    def test_positive_and_unknown_capacity_keep_public_scope(self):
        for remaining in [1,100,None,'unknown']:
            result=self.engine.evaluate(self.candidate,[self.proof(remaining)])
            self.assertEqual(result.status,Status.CLAIMABLE)
            self.assertEqual(result.claim_scope,'PUBLIC_APPLICATION')

    def test_boolean_false_is_not_a_numeric_capacity(self):
        result=self.engine.evaluate(self.candidate,[self.proof(False)])
        self.assertEqual(result.status,Status.CLAIMABLE)
        self.assertTrue(result.unknown_capacity)

    def test_stale_zero_does_not_override_fresh_positive(self):
        old=(datetime.now(timezone.utc)-timedelta(hours=48)).isoformat()
        fresh=self.proof(1);fresh.url='https://vendor.example/current'
        self.assertEqual(self.engine.evaluate(self.candidate,[self.proof(0,checked_at=old),fresh]).status,Status.CLAIMABLE)

    def test_unconfirmed_community_zero_does_not_override_official(self):
        community=Evidence('community','https://forum.example/thread','community',claims={'remaining':0})
        self.assertEqual(self.engine.evaluate(self.candidate,[self.proof(1),community]).status,Status.CLAIMABLE)

    def test_closed_official_offer_remains_expired(self):
        proof=self.proof(0);proof.claims['open']=False
        self.assertEqual(self.engine.evaluate(self.candidate,[proof]).status,Status.EXPIRED)

    def test_other_fresh_positive_does_not_silently_ignore_zero(self):
        positive=self.proof(1);positive.url='https://vendor.example/status'
        self.assertNotEqual(self.engine.evaluate(self.candidate,[self.proof(0),positive]).status,Status.CLAIMABLE)
