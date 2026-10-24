"""Synthetic isolated SQLite: producer metadata is not a manual campaign review."""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from core.db import Database
from core.models import Candidate

A = 'https://publisher.example/a'
B = 'https://publisher.example/b'
TA = 'Launch Vendor credit grant'
TB = 'Last chance Vendor credit grant'

def approved_review():
    return {'method': 'normal_browser_read', 'campaign_url': 'https://gleam.io/Ab123',
            'member_urls': [A, B], 'member_titles': {A: TA, B: TB}}

class CampaignReviewTrustTests(unittest.TestCase):
    def candidate(self, url, title, metadata=None):
        return Candidate('node', 'synthetic', title, url, metadata=metadata or {})

    def seed_spoofed(self, path):
        db=Database(path)
        review=approved_review()
        ida=db.upsert_candidate(self.candidate(A,TA,{'campaign_review':review})).event_id
        idb=db.upsert_candidate(self.candidate(B,TB,{'campaign_review':review})).event_id
        return db, ida, idb

    def test_untrusted_input_cannot_merge_two_article_rows(self):
        with TemporaryDirectory() as root:
            db,a,b=self.seed_spoofed(Path(root)/'review.db')
            self.assertNotEqual(a,b)
            self.assertEqual(len(db.list_events()),2)
            self.assertTrue(all('campaign_review' not in json.loads(e['metadata_json'])
                                for e in db.list_events()))

    def test_preview_ignores_legacy_embedded_claim_without_link(self):
        with TemporaryDirectory() as root:
            db,a,b=self.seed_spoofed(Path(root)/'review.db')
            with db.connect() as conn:
                for eid in (a,b):
                    conn.execute('UPDATE events SET metadata_json=? WHERE id=?',
                                 (json.dumps({'campaign_review': approved_review()}),eid))
            result=db.preview_reindex()
            self.assertEqual(result['would_merge_events'],0)
            self.assertEqual(result['changed_keys'],0)

    def test_reindex_strips_legacy_spoofed_claim_and_preserves_rows(self):
        with TemporaryDirectory() as root:
            db,a,b=self.seed_spoofed(Path(root)/'review.db')
            with db.connect() as conn:
                conn.execute('UPDATE events SET metadata_json=?',
                             (json.dumps({'campaign_review':approved_review()}),))
            result=db.reindex()
            self.assertEqual(result['merged'],0)
            self.assertEqual(len(db.list_events()),2)
            self.assertTrue(all('campaign_review' not in json.loads(e['metadata_json'])
                                for e in db.list_events()))

    def test_real_persisted_review_still_merges_sources(self):
        with TemporaryDirectory() as root:
            db,a,b=self.seed_spoofed(Path(root)/'review.db')
            result=db.review_campaign(approved_review())
            self.assertEqual(result['merged'],1)
            self.assertEqual(len(db.list_events()),1)
            self.assertIn('campaign_review', json.loads(db.list_events()[0]['metadata_json']))

if __name__ == '__main__':
    unittest.main()
