import tempfile
import unittest
from pathlib import Path

from core.db import Database
from core.models import Candidate, Evidence
from core.verifier import VerificationEngine
from core.pipeline import Pipeline
import json


ROOT = Path(__file__).parents[1]
A = 'https://lowendbox.com/blog/last-day-ugreen/'
B = 'https://lowendbox.com/blog/last-bonus-code-ugreen/'
REVIEW = {'method': 'normal_browser_read', 'campaign_url': 'https://gleam.io/Isp30', 'member_urls': [A, B],
          'member_titles': {A: 'Last day to enter UGREEN NAS giveaway', B: 'New bonus code for UGREEN NAS'}}


class CampaignReviewTests(unittest.TestCase):
    def test_equal_time_conflicting_evidence_stays_visible(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as folder:
            db = Database(Path(folder) / 'radar.db')
            one = db.upsert_candidate(Candidate('n', 'LEB', REVIEW['member_titles'][A], A))
            two = db.upsert_candidate(Candidate('n', 'LEB', REVIEW['member_titles'][B], B))
            for event_id, opened in ((one.event_id, False), (two.event_id, True)):
                db.add_evidence(event_id, Evidence('official', 'https://vendor.example/status', 'vendor',
                    checked_at='2026-10-12T00:00:00Z', claims={'open': opened}))
            db.review_campaign(REVIEW)
            evidence = db.get_evidence(one.event_id)
            result = VerificationEngine().evaluate(Candidate('n', 'LEB', 'NAS', A), evidence)
            self.assertEqual(result.status.value, 'CONFLICTED')

    def test_evidence_recency_compares_timezone_offsets(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as folder:
            db = Database(Path(folder) / 'radar.db')
            one = db.upsert_candidate(Candidate('n', 'LEB', REVIEW['member_titles'][A], A))
            two = db.upsert_candidate(Candidate('n', 'LEB', REVIEW['member_titles'][B], B))
            db.add_evidence(one.event_id, Evidence('official', 'https://vendor.example/status', 'vendor',
                checked_at='2026-01-01T01:00:00+02:00', claims={'open': False}))
            db.add_evidence(two.event_id, Evidence('official', 'https://vendor.example/status', 'vendor',
                checked_at='2025-12-31T23:30:00Z', claims={'open': True}))
            db.review_campaign(REVIEW)
            current = next(e for e in db.get_evidence(one.event_id) if e.provenance_key == 'vendor')
            self.assertTrue(current.claims['open'])

    def test_tracking_variants_and_future_scans_remain_one_evidence_group(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as folder:
            root = Path(folder)
            pipeline = Pipeline(root)
            db = pipeline.db
            tracked_a = A + '?utm_source=rss'
            one = db.upsert_candidate(Candidate('n', 'LEB', REVIEW['member_titles'][A], tracked_a))
            two = db.upsert_candidate(Candidate('n', 'LEB', REVIEW['member_titles'][B], B))
            db.add_evidence(one.event_id, Evidence('community', tracked_a, 'first', claims={'public': True}))
            db.add_evidence(two.event_id, Evidence('community', B, 'second', claims={'public': True}))
            db.review_campaign(REVIEW)
            evidence = db.get_evidence(one.event_id)
            self.assertEqual(VerificationEngine().evaluate(Candidate('n', 'LEB', 'NAS', tracked_a), evidence).independent_evidence_count, 1)
            inbox = root / 'data/inbox'
            inbox.mkdir(parents=True)
            candidate = Candidate('openmagpie', 'LEB', REVIEW['member_titles'][A], A + '?utm_source=new')
            (inbox / 'openmagpie.jsonl').write_text(json.dumps(candidate.to_dict()) + '\n')
            pipeline.ingest_node('openmagpie')
            self.assertEqual(VerificationEngine().evaluate(candidate, db.get_evidence(one.event_id)).independent_evidence_count, 1)

    def test_migration_keeps_newer_evidence_and_archives_collision(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as folder:
            db = Database(Path(folder) / 'radar.db')
            one = db.upsert_candidate(Candidate('n', 'LEB', REVIEW['member_titles'][A], A))
            two = db.upsert_candidate(Candidate('n', 'LEB', REVIEW['member_titles'][B], B))
            url = 'https://vendor.example/status'
            older = Evidence('official', url, 'vendor', checked_at='2025-01-01T00:00:00Z', claims={'open': False})
            newer = Evidence('official', url, 'vendor', claims={'open': True, 'public': True})
            db.add_evidence(one.event_id, older)
            db.add_evidence(two.event_id, newer)
            db.review_campaign(REVIEW)
            current = next(e for e in db.get_evidence(one.event_id) if e.provenance_key == 'vendor')
            self.assertEqual(current.claims, newer.claims)
            with db.connect() as conn:
                archive = [json.loads(row[0]) for row in conn.execute('SELECT payload_json FROM migration_evidence_archive')]
            self.assertTrue(any(item['claims_json'] == json.dumps(older.claims, ensure_ascii=False) for item in archive))
            self.assertTrue(any(item['claims_json'] == json.dumps(newer.claims, ensure_ascii=False) for item in archive))

    def test_reviewed_shared_campaign_merges_and_future_scans_do_not_notify_again(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as folder:
            db = Database(Path(folder) / 'radar.db')
            first = Candidate('n', 'LEB', 'Last day to enter UGREEN NAS giveaway', A)
            second = Candidate('n', 'LEB', 'New bonus code for UGREEN NAS', B)
            one, two = db.upsert_candidate(first), db.upsert_candidate(second)
            db.add_evidence(one.event_id, Evidence('community', A, 'publisher-one', claims={'open': 'unknown'}))
            db.add_evidence(two.event_id, Evidence('community', B, 'publisher-two', claims={'open': 'unknown'}))
            unrelated = db.upsert_candidate(Candidate('n', 'LEB', 'Halloween cash giveaway', 'https://lowendbox.com/blog/halloween/'))
            result = db.review_campaign(REVIEW)
            self.assertEqual(result['merged'], 1)
            self.assertTrue(Path(result['backup']).exists())
            self.assertEqual(len(db.list_events()), 2)
            stored = db.upsert_candidate(second)
            self.assertFalse(stored.notify)
            self.assertEqual(stored.event_id, one.event_id)
            evidence = db.get_evidence(one.event_id)
            self.assertTrue({'publisher-one', 'publisher-two'} <= {item.provenance_key for item in evidence})
            self.assertEqual(VerificationEngine().evaluate(first, evidence).independent_evidence_count, 1)
            self.assertIsNotNone(db.get_event(unrelated.event_id))
            self.assertTrue(db.review_campaign(REVIEW)['unchanged'])
            changed = db.upsert_candidate(Candidate('n', 'LEB', 'New 2027 cash prize replaces old NAS campaign', B))
            self.assertNotEqual(changed.event_id, one.event_id)

    def test_unseen_or_unreviewed_campaign_links_do_not_mutate_events(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.test-tmp') as folder:
            db = Database(Path(folder) / 'radar.db')
            db.upsert_candidate(Candidate('n', 'LEB', 'UGREEN NAS', A))
            for review in [
                {'method': 'rss', 'campaign_url': 'https://gleam.io/Isp30', 'member_urls': [A, B]},
                {'method': 'normal_browser_read', 'campaign_url': 'https://evil.example/Isp30', 'member_urls': [A, B]},
                {'method': 'normal_browser_read', 'campaign_url': 'https://gleam.io/Isp30', 'member_urls': [A, B]},
            ]:
                with self.assertRaises(ValueError):
                    db.review_campaign(review)
            self.assertEqual(len(db.list_events()), 1)
