import json,tempfile,unittest,sys
from pathlib import Path
from core.public_corpus import record_public_sample
sys.path.insert(0,str(Path(__file__).parents[1]/'independent-quality/public-corpus-blind-dedup-20261016'))
from freeze_public_sample_dedup import freeze_public_sources
PUBLIC={'id':'identity-feed','auth':'public_feed','kind':'rss','platform':'test'}
def produce(urls):
    with tempfile.TemporaryDirectory() as d:
        path=record_public_sample(Path(d),'synthetic',PUBLIC,[{'title':'Public developer grant','url':u,'summary':'Review conditions'} for u in urls],[False]*len(urls))
        return json.loads(path.read_text(encoding='utf-8'))
class PublicCorpusIdentityTests(unittest.TestCase):
    def test_real_producer_sampler_keeps_two_batches_and_dedups_trackers(self):
        data=produce(['https://example.org/view?batch=1&utm_source=one','https://example.org/view?batch=2&utm_source=two','https://example.org/view?utm_source=three&batch=1'])
        sampled=freeze_public_sources([(data,'a'*64)],limit=8)
        self.assertEqual(len(sampled['rows']),2)
        self.assertEqual({r['url'] for r in sampled['rows']},{'https://example.org/view?batch=1','https://example.org/view?batch=2'})
        self.assertTrue(all(r['url_identity_preserved'] for r in data['rows']))
        self.assertEqual(sampled['sources'][0]['upstream_url_identity_lost'],0)
    def test_unknown_query_identity_loss_never_becomes_blind_gold(self):
        data=produce(['https://example.org/view?unknown_selector=private-value'])
        self.assertFalse(data['rows'][0].get('url_identity_preserved',True))
        self.assertNotIn('private-value',json.dumps(data))
        self.assertEqual(freeze_public_sources([(data,'a'*64)])['rows'],[])
    def test_credential_contact_and_encoded_query_values_never_survive(self):
        for suffix in ['token=SYNTHETIC_ONLY','%74oken=SYNTHETIC_ONLY','email=synthetic%40example.org','batch=synthetic%40example.org','batch=1234567890123456']:
            with self.subTest(suffix=suffix):
                data=produce(['https://example.org/view?'+suffix]);text=json.dumps(data)
                self.assertFalse(data['rows'][0].get('url_identity_preserved',True))
                self.assertEqual(data['rows'][0]['url'],'https://example.org/view')
                self.assertNotIn('SYNTHETIC_ONLY',text);self.assertNotIn('synthetic@',text)
    def test_spa_batch_routes_remain_distinct_without_auth_fragment(self):
        data=produce(['https://example.org/#/offers?batch=1','https://example.org/#/offers?batch=2'])
        self.assertEqual(len(freeze_public_sources([(data,'a'*64)])['rows']),2)
        blocked=produce(['https://example.org/#/offers?token=SYNTHETIC_ONLY'])
        self.assertFalse(blocked['rows'][0].get('url_identity_preserved',True))
        self.assertNotIn('SYNTHETIC_ONLY',json.dumps(blocked))
    def test_legacy_sanitized_flag_without_new_proof_remains_excluded(self):
        data=produce(['https://example.org/view']);row=data['rows'][0]
        row.pop('url_identity_preserved',None);row['url_sanitized']=True
        self.assertEqual(freeze_public_sources([(data,'a'*64)])['rows'],[])
    def test_truncated_distinct_long_urls_must_not_claim_identity(self):
        prefix='https://example.org/'+'x'*2048
        data=produce([prefix+'/batch-alpha',prefix+'/batch-beta'])
        self.assertEqual(data['rows'][0]['url'],data['rows'][1]['url'])
        self.assertTrue(all(row['content_truncated'] for row in data['rows']))
        self.assertTrue(all(row['url_sanitized'] for row in data['rows']))
        self.assertTrue(all(row['url_identity_preserved'] is False for row in data['rows']))
        selected=freeze_public_sources([(data,'a'*64)],limit=8)
        self.assertEqual(selected['rows'],[])
        self.assertEqual(selected['sources'][0]['upstream_url_identity_lost'],2)

    def test_long_tracker_removed_without_losing_resource_identity(self):
        data=produce(['https://example.org/offer?batch=1&utm_source='+'x'*3000])
        row=data['rows'][0]
        self.assertEqual(row['url'],'https://example.org/offer?batch=1')
        self.assertTrue(row['url_sanitized'])
        self.assertTrue(row['url_identity_preserved'])
        self.assertEqual(len(freeze_public_sources([(data,'a'*64)])['rows']),1)

    def test_case_folded_functional_selectors_never_claim_blind_identity(self):
        data=produce(['https://example.org/view?Batch=alpha',
                      'https://example.org/view?batch=alpha'])
        self.assertEqual(data['rows'][0]['url'],data['rows'][1]['url'])
        self.assertTrue(data['rows'][0]['url_sanitized'])
        self.assertFalse(data['rows'][0]['url_identity_preserved'])
        self.assertTrue(data['rows'][1]['url_identity_preserved'])
        selected=freeze_public_sources([(data,'a'*64)],limit=8)
        self.assertEqual(len(selected['rows']),1)
        self.assertEqual(selected['sources'][0]['upstream_url_identity_lost'],1)

    def test_case_changed_marketing_tracker_is_still_safely_removed(self):
        data=produce(['https://example.org/view?batch=beta&UTM_SOURCE=news'])
        self.assertEqual(data['rows'][0]['url'],'https://example.org/view?batch=beta')
        self.assertTrue(data['rows'][0]['url_identity_preserved'])

    def test_duplicate_equal_campaign_selectors_are_not_safe_blind_identity(self):
        data=produce(['https://example.org/view?batch=alpha&batch=alpha',
                      'https://example.org/view?batch=alpha'])
        self.assertEqual(data['rows'][0]['url'],data['rows'][1]['url'])
        self.assertFalse(data['rows'][0]['url_identity_preserved'])
        self.assertTrue(data['rows'][1]['url_identity_preserved'])
        selected=freeze_public_sources([(data,'a'*64)],limit=8)
        self.assertEqual(len(selected['rows']),1)
        self.assertEqual(selected['sources'][0]['upstream_url_identity_lost'],1)

    def test_conflicting_functional_query_keys_do_not_become_blind_gold(self):
        data=produce(['https://example.org/view?batch=1&batch=2'])
        self.assertFalse(data['rows'][0].get('url_identity_preserved',True))
        self.assertEqual(freeze_public_sources([(data,'a'*64)])['rows'],[])
