"""Explicit official payment risks must not be advertised as ready benefits.

All data is synthetic, with a temporary SQLite DB and local files only.
"""

import tempfile
import unittest
from pathlib import Path

from core.db import Database
from core.models import Candidate, Evidence, Status
from core.notify import NotificationQueue
from core.report import ReportGenerator
from core.verifier import VerificationEngine


class OfficialPaymentGateTests(unittest.TestCase):
    def setUp(self):
        self.candidate = Candidate('synthetic', 'vendor', 'Free starter credits',
                                   'https://vendor.example/offer')

    def proof(self, **conditions):
        return Evidence('official', 'https://vendor.example/terms', 'vendor-terms',
                        claims={'open': True, 'public': True, **conditions})

    def test_explicit_card_requirement_needs_human_review(self):
        result = VerificationEngine().evaluate(
            self.candidate, [self.proof(card_required=True)])
        self.assertEqual((result.status, result.claim_scope),
                         (Status.OFFICIAL_VERIFIED, 'NONE'))

    def test_explicit_auto_renewal_needs_human_review(self):
        result = VerificationEngine().evaluate(
            self.candidate, [self.proof(auto_renew=True)])
        self.assertEqual((result.status, result.claim_scope),
                         (Status.OFFICIAL_VERIFIED, 'NONE'))

    def test_explicit_no_card_no_renewal_retains_public_application_scope(self):
        result = VerificationEngine().evaluate(
            self.candidate, [self.proof(card_required=False, auto_renew=False)])
        self.assertEqual((result.status, result.claim_scope),
                         (Status.CLAIMABLE, 'PUBLIC_APPLICATION'))

    def test_report_and_verified_outbox_recheck_payment_risk(self):
        with tempfile.TemporaryDirectory(prefix='wool-payment-gate-') as td:
            root = Path(td)
            db = Database(root / 'isolated.sqlite')
            event = db.upsert_candidate(self.candidate).event_id
            db.add_evidence(event, self.proof())
            db.set_status(event, Status.CLAIMABLE, 'earlier clean approval',
                          'PUBLIC_APPLICATION')
            queue = NotificationQueue(db)
            self.assertTrue(queue.enqueue(event, '', 'local-verified', 'synthetic offer'))
            # An official terms revision introduces a card requirement; a
            # previously stored positive decision must not bypass live checks.
            db.add_evidence(event, Evidence('official',
                'https://vendor.example/updated-terms', 'vendor-updated',
                claims={'open': True, 'public': True, 'card_required': True}))
            output = queue.flush({}, local_dir=root / 'outbox')
            self.assertEqual(output['local'], 0)
            self.assertFalse(list((root / 'outbox').glob('notification-*.json')))
            paths = ReportGenerator(db, root / 'reports').generate('2026-10-19')
            self.assertTrue(paths.json.exists())
            markdown = paths.markdown.read_text(encoding='utf-8')
            payment_risk = markdown.split('## 绑卡或自动续费风险：待人工核验\n')[1].split('## ')[0]
            self.assertIn('Free starter credits', payment_risk)
            self.assertIn('绑卡', payment_risk)
            claimable_section = markdown.split('## 官方已核实、正在开放的福利\n')[1].split('## ')[0]
            self.assertNotIn('Free starter credits', claimable_section)
            self.assertEqual(db.get_event(event)['status'], Status.OFFICIAL_VERIFIED.value)
            self.assertEqual(db.get_event(event)['claim_scope'], 'NONE')


if __name__ == '__main__':
    unittest.main()
