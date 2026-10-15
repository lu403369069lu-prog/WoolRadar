import tempfile
import unittest
from pathlib import Path
from core.models import Candidate
from core.dedup import canonical_key
from core.db import Database

TEMP=Path(__file__).parents[1]/'.test-tmp'
TEMP.mkdir(exist_ok=True)

class GenericIdentityTests(unittest.TestCase):
    def candidate(self,url,title='Free API credits',**kwargs):
        return Candidate('test','public',title,url,**kwargs)

    def test_distinct_vendor_generic_titles_are_separate(self):
        a=self.candidate('https://a.example/offer');b=self.candidate('https://b.example/offer')
        self.assertNotEqual(canonical_key(a),canonical_key(b))

    def test_distinct_paths_are_not_assumed_same_campaign(self):
        a=self.candidate('https://vendor.example/alpha');b=self.candidate('https://vendor.example/beta')
        self.assertNotEqual(canonical_key(a),canonical_key(b))

    def test_chinese_generic_titles_are_separate(self):
        a=self.candidate('https://a.example/offer','免费 API 额度');b=self.candidate('https://b.example/offer','免费 API 额度')
        self.assertNotEqual(canonical_key(a),canonical_key(b))

    def test_tracking_fragment_variants_remain_one(self):
        a=self.candidate('https://vendor.example/offer?utm_source=rss#top')
        b=self.candidate('https://vendor.example/offer?utm_medium=feed')
        self.assertEqual(canonical_key(a),canonical_key(b))

    def test_specific_branded_reposts_keep_existing_behavior(self):
        a=self.candidate('https://forum-a.example/post','RackNerd Free VPS Giveaway')
        b=self.candidate('https://forum-b.example/article','RackNerd giveaway free VPS')
        self.assertEqual(canonical_key(a),canonical_key(b))

    def test_explicit_verified_campaign_overrides_generic_fallback(self):
        a='https://publisher.example/a';b='https://publisher.example/b';title='Free API credits'
        review={'method':'normal_browser_read','campaign_url':'https://gleam.io/Ab123','member_urls':[a,b],'member_titles':{a:title,b:title}}
        self.assertEqual(canonical_key(self.candidate(a,metadata={'campaign_review':review})),canonical_key(self.candidate(b,metadata={'campaign_review':review})))

    def test_specific_amounts_are_not_erased_by_url_fallback(self):
        a=self.candidate('https://vendor.example/offer','Free API credits 100')
        b=self.candidate('https://vendor.example/offer','Free API credits 200')
        self.assertNotEqual(canonical_key(a),canonical_key(b))

    def test_database_notifies_once_for_each_distinct_vendor(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as td:
            db=Database(Path(td)/'radar.db')
            first=db.upsert_candidate(self.candidate('https://a.example/offer'))
            second=db.upsert_candidate(self.candidate('https://b.example/offer'))
            self.assertNotEqual(first.event_id,second.event_id)
            self.assertTrue(first.notify);self.assertTrue(second.notify)
            self.assertFalse(db.upsert_candidate(self.candidate('https://a.example/offer?utm_source=second')).notify)
            self.assertEqual(len(db.list_events()),2)
