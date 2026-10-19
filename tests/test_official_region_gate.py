"""Official geographic restrictions must not be advertised as CN-ready offers.

Only explicit structured country codes are authoritative; all fixtures are local.
"""

import tempfile
import unittest
from pathlib import Path

from core.db import Database
from core.models import Candidate, Evidence, Status
from core.notify import NotificationQueue
from core.report import ReportGenerator
from core.verifier import VerificationEngine


class MainlandEligibilityGateTests(unittest.TestCase):
    def setUp(self):
        self.candidate = Candidate('synthetic', 'official', 'Free credits',
                                   'https://vendor.example/offer')

    def proof(self, **conditions):
        return Evidence('official', 'https://vendor.example/terms', 'official-terms',
                        claims={'open': True, 'public': True, **conditions})

    def check(self, expected, **conditions):
        result = VerificationEngine().evaluate(self.candidate, [self.proof(**conditions)])
        self.assertEqual((result.status, result.claim_scope), expected)

    def test_explicit_single_country_us_cannot_be_presented_to_cn_as_claimable(self):
        self.check((Status.OFFICIAL_VERIFIED, 'NONE'), region='US')

    def test_explicit_allowed_country_list_excludes_cn(self):
        self.check((Status.OFFICIAL_VERIFIED, 'NONE'),
                   eligibility_constraints={'eligible_countries': ['US', 'CA']})

    def test_explicit_excluded_country_list_contains_cn(self):
        self.check((Status.OFFICIAL_VERIFIED, 'NONE'),
                   eligibility_constraints={'excluded_countries': ['CN']})

    def test_explicit_allow_list_includes_cn(self):
        self.check((Status.CLAIMABLE, 'PUBLIC_APPLICATION'),
                   eligibility_constraints={'eligible_countries': ['US', 'CN']})

    def test_explicit_cn_region_is_eligible_for_public_application(self):
        self.check((Status.CLAIMABLE, 'PUBLIC_APPLICATION'), region='CN')

    def test_bad_country_list_never_infers_an_exclusion(self):
        for allowed in ([], 'US', ['US', 'not a country'], [None, 'US']):
            with self.subTest(allowed=allowed):
                self.check((Status.CLAIMABLE, 'PUBLIC_APPLICATION'),
                           eligibility_constraints={'eligible_countries': allowed})

    def test_unknown_or_narrative_region_is_not_invented_exclusion(self):
        for region in ('unknown', 'global', 'US users should read the full terms'):
            with self.subTest(region=region):
                self.check((Status.CLAIMABLE, 'PUBLIC_APPLICATION'), region=region)

    def test_existing_approved_outbox_and_digest_revalidate_new_cn_exclusion(self):
        with tempfile.TemporaryDirectory(prefix='wool-cn-gate-') as td:
            root = Path(td)
            db = Database(root / 'synthetic.sqlite')
            event = db.upsert_candidate(self.candidate).event_id
            db.add_evidence(event, self.proof())
            db.set_status(event, Status.CLAIMABLE, 'previous open proof', 'PUBLIC_APPLICATION')
            queue = NotificationQueue(db)
            self.assertTrue(queue.enqueue(event, '', 'local-verified', 'synthetic message'))
            db.add_evidence(event, Evidence('official',
                'https://vendor.example/updated', 'official-updated',
                claims={'open': True, 'public': True,
                        'eligibility_constraints': {'excluded_countries': ['CN']}}))
            self.assertEqual(queue.flush({}, local_dir=root / 'out')['local'], 0)
            report = ReportGenerator(db, root / 'reports').generate('2026-10-19')
            md = report.markdown.read_text(encoding='utf-8')
            public = md.split('## 官方已核实、正在开放的福利\n')[1].split('## ')[0]
            self.assertNotIn('Free credits', public)
            self.assertIn('Free credits', md)
            region_section = md.split('## 中国大陆地域资格限制：待人工核验\n')[1].split('## ')[0]
            self.assertIn('Free credits', region_section)
            self.assertIn('地域资格：官方结构化条款限制中国大陆申请', region_section)
            self.assertEqual((db.get_event(event)['status'], db.get_event(event)['claim_scope']),
                             (Status.OFFICIAL_VERIFIED.value, 'NONE'))


if __name__ == '__main__':
    unittest.main()
