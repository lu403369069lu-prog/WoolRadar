import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from core.db import Database
from core.dedup import canonical_key
from core.models import Candidate, Evidence, Status
from core.verifier import VerificationEngine

TEST_TMP = Path(__file__).parents[1] / '.test-tmp'
TEST_TMP.mkdir(exist_ok=True)


class WoolRadarCoreTests(unittest.TestCase):
    def test_explicit_official_expiry_overrides_fresh_open_flag(self):
        candidate = Candidate('n', 'Vendor', 'Free credits', 'https://vendor.example/offer')
        evidence = Evidence('official', candidate.url, 'vendor', claims={'open': True, 'public': True, 'expires_at': '2020-01-01T00:00:00Z'})
        self.assertEqual(VerificationEngine().evaluate(candidate, [evidence]).status, Status.EXPIRED)

    def test_ambiguous_official_expiry_cannot_support_claimable(self):
        candidate = Candidate('n', 'Vendor', 'Free credits', 'https://vendor.example/offer')
        for expiry in ('2099-01-01', '2099-01-01T12:00:00', 'next Friday'):
            with self.subTest(expiry=expiry):
                evidence = Evidence('official', candidate.url, 'vendor', claims={'open': True, 'public': True, 'expires_at': expiry})
                self.assertEqual(VerificationEngine().evaluate(candidate, [evidence]).status, Status.OFFICIAL_VERIFIED)

    def test_community_expiry_does_not_close_verified_official_offer(self):
        candidate = Candidate('n', 'Vendor', 'Free credits', 'https://vendor.example/offer')
        official = Evidence('official', candidate.url, 'vendor', claims={'open': True, 'public': True, 'expires_at': '2099-01-01T00:00:00Z'})
        community = Evidence('community', 'https://forum.example/1', 'forum', claims={'expires_at': '2020-01-01T00:00:00Z'})
        self.assertEqual(VerificationEngine().evaluate(candidate, [official, community]).status, Status.CLAIMABLE)

    def test_more_specific_eligibility_text_is_not_a_contradiction(self):
        candidate = Candidate('n', 'MLH', 'Student free credits', 'https://mlh.example/benefits')
        evidence = [Evidence('official', candidate.url, 'mlh', claims={'eligibility': 'student status required'}),
                    Evidence('official', 'https://vendor.example/students', 'vendor', claims={'eligibility': 'verified student pack and age >=13', 'public': False})]
        self.assertEqual(VerificationEngine().evaluate(candidate, evidence).status, Status.OFFICIAL_VERIFIED)

    def test_structured_eligibility_conflict_is_retained(self):
        candidate = Candidate('n', 'MLH', 'Student free credits', 'https://mlh.example/benefits')
        evidence = [Evidence('official', candidate.url, 'mlh', claims={'eligibility_constraints': {'student_required': True}}),
                    Evidence('official', 'https://vendor.example/students', 'vendor', claims={'eligibility_constraints': {'student_required': False}})]
        self.assertEqual(VerificationEngine().evaluate(candidate, evidence).status, Status.CONFLICTED)

    def test_public_promo_flag_does_not_verify_personal_account(self):
        candidate = Candidate('a', 'official', 'Free credits', 'https://vendor.example/promo')
        result = VerificationEngine().evaluate(candidate, [Evidence(
            'official', candidate.url, 'vendor-promo',
            claims={'open': True, 'public': True, 'personal_eligible': True})])
        self.assertEqual(result.status, Status.CLAIMABLE)
        self.assertEqual(result.claim_scope, 'PUBLIC_APPLICATION')

    def test_repost_claims_plus_unrelated_feedback_do_not_corroborate(self):
        candidate = Candidate('a', 'forum', 'Free VPS', 'https://a.example/1')
        result = VerificationEngine().evaluate(candidate, [
            Evidence('community', candidate.url, 'same-promo', claims={'public': True}),
            Evidence('community', 'https://b.example/2', 'same-promo', claims={'public': True}),
            Evidence('community', 'https://c.example/3', 'independent-comment', claims={'comment': 'interesting'})])
        self.assertEqual(result.status, Status.UNKNOWN)

    def test_matching_claims_in_independent_groups_can_corroborate(self):
        candidate = Candidate('a', 'forum', 'Free VPS', 'https://a.example/1')
        result = VerificationEngine().evaluate(candidate, [
            Evidence('community', candidate.url, 'feedback-a', claims={'public': True}),
            Evidence('community', 'https://b.example/2', 'feedback-b', claims={'public': True})])
        self.assertEqual(result.status, Status.CROSS_CHECKED)

    def test_stale_open_claim_is_not_claimable(self):
        candidate = Candidate('a', 'rss', 'Free VPS', 'https://a.example/1')
        result = VerificationEngine().evaluate(candidate, [Evidence('official', candidate.url,
            'official', checked_at='2020-01-01T00:00:00Z', claims={'open': True, 'public': True})])
        self.assertNotEqual(result.status, Status.CLAIMABLE)

    def test_contradictory_official_open_claims_are_conflicted(self):
        candidate = Candidate('a', 'rss', 'Free VPS', 'https://a.example/1')
        result = VerificationEngine().evaluate(candidate, [
            Evidence('official', candidate.url, 'a', claims={'open': True, 'public': True}),
            Evidence('official', 'https://b.example/1', 'b', claims={'open': False})])
        self.assertEqual(result.status, Status.CONFLICTED)

    def test_different_capacity_is_not_merged(self):
        a = Candidate('a', 'rss', 'Free VPS 1 GB', 'https://a.example/1')
        b = Candidate('b', 'rss', 'Free VPS 2 GB', 'https://b.example/2')
        self.assertNotEqual(canonical_key(a), canonical_key(b))
    def test_cross_platform_reposts_share_canonical_key(self):
        a = Candidate(
            node='openmagpie', source='reddit', title='RackNerd x AdminBolt FREE VPS Giveaway!',
            url='https://reddit.example/post/1', published_at='2026-10-01T00:00:00Z')
        b = Candidate(
            node='linuxdo', source='linux.do', title='RackNerd × AdminBolt 免费 VPS 抽奖',
            url='https://linux.example/t/2', published_at='2026-10-01T00:00:00Z')
        self.assertEqual(canonical_key(a), canonical_key(b))

    def test_reposts_do_not_count_as_independent_evidence(self):
        candidate = Candidate('openmagpie', 'rss', 'Cursor Pro MLH 福利', 'https://forum-a.example/p/1')
        evidence = [
            Evidence('community', 'https://forum-a.example/p/1', 'same-promo'),
            Evidence('community', 'https://forum-b.example/p/2', 'same-promo'),
        ]
        result = VerificationEngine().evaluate(candidate, evidence)
        self.assertNotEqual(result.status, Status.CROSS_CHECKED)
        self.assertEqual(result.independent_evidence_count, 1)

    def test_real_racknerd_repost_titles_deduplicate(self):
        a = Candidate('linuxdo-monitor', 'LowEndTalk',
            "GIVEAWAY by AdminBolt & RackNerd! 100x FREE VPS FOR A YEAR + 20x LIFETIME LICENSES. LET'S TALK!",
            'https://lowendtalk.com/discussion/221872/example')
        b = Candidate('linuxdo-monitor', 'LowEndBox',
            'RackNerd & AdminBolt Are Giving Away 100 FREE VPS for a Year + 20 LIFETIME Licenses!',
            'https://lowendbox.com/blog/example/')
        self.assertEqual(canonical_key(a), canonical_key(b))

    def test_claimable_requires_official_evidence_and_scope(self):
        candidate = Candidate('digest-ai-agent', 'rss', 'Free API credits', 'https://community.example/post')
        no_official = VerificationEngine().evaluate(candidate, [
            Evidence('community', 'https://community.example/post', 'user-report')
        ])
        self.assertNotEqual(no_official.status, Status.CLAIMABLE)
        official = VerificationEngine().evaluate(candidate, [
            Evidence('official', 'https://vendor.example/promo', 'vendor-announcement',
                     claims={'open': True, 'public': True, 'personal_eligible': False})
        ])
        self.assertEqual(official.status, Status.CLAIMABLE)
        self.assertEqual(official.claim_scope, 'PUBLIC_APPLICATION')

    def test_unknown_capacity_stays_unknown(self):
        candidate = Candidate('clawradar', 'reddit', 'Limited giveaway', 'https://reddit.example/p')
        result = VerificationEngine().evaluate(candidate, [
            Evidence('official', 'https://vendor.example/promo', 'vendor-announcement',
                     claims={'open': True, 'public': True})
        ])
        self.assertTrue(result.unknown_capacity)

        explicit_unknown = VerificationEngine().evaluate(candidate, [
            Evidence('official', 'https://vendor.example/promo', 'vendor-announcement',
                     claims={'open': True, 'public': True, 'remaining': 'unknown'})
        ])
        self.assertTrue(explicit_unknown.unknown_capacity)

    def test_same_url_and_shared_campaign_form_one_evidence_group(self):
        candidate = Candidate('linuxdo-monitor', 'LowEndTalk', 'Free VPS', 'https://forum.example/thread')
        evidence = [
            Evidence('community', 'https://forum.example/thread', 'forum.example'),
            Evidence('official', 'https://forum.example/thread', 'campaign-1'),
            Evidence('community_repost', 'https://blog.example/repost', 'campaign-1'),
        ]
        result = VerificationEngine().evaluate(candidate, evidence)
        self.assertEqual(result.independent_evidence_count, 1)

    def test_new_batch_is_not_suppressed(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as td:
            db = Database(Path(td) / 'radar.db')
            first = Candidate('node1', 'rss', 'API credits batch', 'https://vendor.example/promo',
                              published_at='2026-09-01T00:00:00Z', batch_id='2026-09')
            second = Candidate('node1', 'rss', 'API credits batch', 'https://vendor.example/promo',
                               published_at='2026-10-01T00:00:00Z', batch_id='2026-10')
            self.assertTrue(db.upsert_candidate(first).notify)
            self.assertFalse(db.upsert_candidate(first).notify)
            self.assertTrue(db.upsert_candidate(second).notify)

    def test_http_barriers_are_explicit(self):
        engine = VerificationEngine()
        self.assertEqual(engine.classify_fetch_failure(403, ''), 'BLOCKED_403')
        self.assertEqual(engine.classify_fetch_failure(429, ''), 'RATE_LIMITED_429')
        self.assertEqual(engine.classify_fetch_failure(200, 'cf-chl-captcha'), 'CAPTCHA_REQUIRED')

    def test_database_records_status_history_and_evidence(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as td:
            db = Database(Path(td) / 'radar.db')
            candidate = Candidate('linuxdo', 'linux.do', '免费 API 额度', 'https://linux.do/t/1')
            stored = db.upsert_candidate(candidate)
            db.add_evidence(stored.event_id, Evidence('community', candidate.url, 'original-post'))
            db.set_status(stored.event_id, Status.UNKNOWN, reason='缺少官方证据')
            with closing(sqlite3.connect(db.path)) as conn:
                self.assertEqual(conn.execute('select count(*) from evidence').fetchone()[0], 1)
                self.assertEqual(conn.execute('select count(*) from status_history').fetchone()[0], 1)

    def test_security_policy_defaults_to_read_only(self):
        policy = json.loads((Path(__file__).parents[1] / 'config' / 'security-policy.json').read_text(encoding='utf-8'))
        self.assertFalse(policy['allow_claim'])
        self.assertFalse(policy['allow_payment'])
        self.assertFalse(policy['allow_posting'])
        self.assertFalse(policy['allow_cookie_export'])
        self.assertFalse(policy['allow_challenge_bypass'])

    def test_reindex_preserves_evidence_and_creates_backup(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as td:
            db = Database(Path(td) / 'radar.db')
            a = Candidate('a', 'forum', 'Free API credits', 'https://a.example/1')
            b = Candidate('b', 'forum', 'Free API credits', 'https://b.example/2')
            first = db.upsert_candidate(a).event_id
            with db.connect() as conn:
                conn.execute('UPDATE events SET canonical_key=? WHERE id=?', ('old-key', first))
            second = db.upsert_candidate(b).event_id
            db.add_evidence(second, Evidence('community', b.url, 'same-promo'))
            result = db.reindex()
            self.assertEqual(result['merged'], 1)
            self.assertTrue(Path(result['backup']).is_file())
            self.assertEqual(len(db.list_events()), 1)
            self.assertEqual(len(db.get_evidence(first)), 1)
            with db.connect() as conn:
                self.assertEqual(conn.execute('SELECT count(*) FROM sightings').fetchone()[0], 2)


if __name__ == '__main__':
    unittest.main()
