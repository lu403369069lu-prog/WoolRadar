"""Explicit reviewed official campaigns; no automatic title-similarity grouping."""
import unittest
from core.models import Candidate
from core.dedup import canonical_key,reviewed_campaign_url

class ReviewedOfficialCampaignContracts(unittest.TestCase):
    def review(self):
        a,b='https://news.example/announcement','https://news.example/host-guide'
        return {'method':'normal_browser_read','review_kind':'official_campaign_v2',
                'reviewer':'synthetic-reviewer','reviewed_at':'2026-10-17T00:00:00Z',
                'reason':'Both publisher articles explicitly link the same annual program.',
                'campaign_url':'https://campaign.example/2026/host-support',
                'official_hosts':['campaign.example'],
                'member_urls':[a,b],'member_titles':{a:'Developer event announcement',b:'Developer community host guide'}}

    def test_explicit_review_joins_different_titles(self):
        r=self.review();keys=[]
        for u in r['member_urls']:
            keys.append(canonical_key(Candidate('test','public',r['member_titles'][u],u,metadata={'campaign_review':r})))
        self.assertEqual(keys[0],keys[1])

    def test_no_review_preserves_separation(self):
        r=self.review();a,b=r['member_urls']
        self.assertNotEqual(canonical_key(Candidate('test','public',r['member_titles'][a],a)),canonical_key(Candidate('test','public',r['member_titles'][b],b)))

    def test_explicit_identity_does_not_accept_missing_audit(self):
        for field in ['reviewer','reviewed_at','reason','official_hosts']:
            r=self.review();r.pop(field)
            with self.subTest(field=field):self.assertIsNone(reviewed_campaign_url(r,r['member_urls'][0]))

    def test_unapproved_host_or_ambiguous_identity_rejected(self):
        for url in ['http://campaign.example/2026/host-support','https://other.example/2026/host-support','https://campaign.example/','https://campaign.example/2026/host-support?batch=2','https://campaign.example/2026/host-support#other','https://user:password@campaign.example/2026/host-support']:
            r=self.review();r['campaign_url']=url
            with self.subTest(url=url):self.assertIsNone(reviewed_campaign_url(r,r['member_urls'][0]))

    def test_legacy_gleam_review_remains_supported(self):
        r=self.review();r['campaign_url']='https://gleam.io/Ab123'
        self.assertEqual(reviewed_campaign_url(r,r['member_urls'][0]),'https://gleam.io/Ab123')
