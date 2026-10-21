import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from freeze_public_sample_dedup import freeze_public_sources, canonical_public_url, parse_source_json, main

D='a'*64
def row(url, **kwargs):
    return {'url':url,'title':'Public project','summary':'Public summary','accepted':True,
            'url_identity_preserved':True,**kwargs}
def sample(name, urls):
    return ({'schema_version':1,'public_only':True,'source_id':name,'rows':[row(u) for u in urls]},D)

class CleanSample(unittest.TestCase):
    def test_within_source_duplicate_removed_before_cap(self):
        out=freeze_public_sources([sample('alpha',['https://example.org/one?utm_source=alpha','https://EXAMPLE.org/one#ref','https://example.org/two'])],limit=8)
        self.assertEqual(len(out['rows']),2)
        self.assertEqual(out['sources'][0]['duplicate_within_source'],1)
        self.assertEqual(len({x['url'] for x in out['rows']}),2)
        self.assertTrue(all('tracking' not in x['url'] for x in out['rows']))
    def test_distinct_campaign_batches_are_not_silently_merged(self):
        a=sample('alpha',['https://example.org/claim?batch=october',
                          'https://example.org/claim?batch=november'])
        result=freeze_public_sources([a])
        self.assertEqual(len(result['rows']),2)
        self.assertEqual(result['sources'][0]['duplicate_within_source'],0)
    def test_distinct_spa_offer_routes_are_not_silently_merged(self):
        a=sample('alpha',['https://example.org/#/offer/one',
                          'https://example.org/#/offer/two'])
        result=freeze_public_sources([a])
        self.assertEqual(len(result['rows']),2)
        self.assertEqual(result['sources'][0]['duplicate_within_source'],0)
    def test_only_explicit_marketing_params_are_stripped(self):
        self.assertEqual(canonical_public_url('https://example.org/claim?utm_source=a&batch=one&gclid=x'),
                         'https://example.org/claim?batch=one')
        self.assertEqual(canonical_public_url('https://example.org/claim?ref=inviteA'),
                         'https://example.org/claim?ref=inviteA')
        self.assertIsNone(canonical_public_url('https://example.org/claim?access_token=secret'))
    def test_utm_campaign_may_encode_real_round_and_is_retained(self):
        first='https://example.org/apply?utm_campaign=fall'
        second='https://example.org/apply?utm_campaign=winter'
        out=freeze_public_sources([sample('alpha',[first,second])])
        self.assertEqual(len(out['rows']),2)
        self.assertEqual(out['sources'][0]['duplicate_within_source'],0)
    def test_generic_token_and_oauth_code_are_never_written_into_review(self):
        for key in ('token','secret','auth','code','signature','sig','sessionid','api-key'):
            with self.subTest(key=key):
                self.assertIsNone(canonical_public_url('https://example.org/join?'+key+'=PRIVATE_CANARY'))
    def test_nested_encoded_query_credentials_are_dropped(self):
        for query in ('%2574oken=PRIVATE_CANARY',
                      '%252574oken=PRIVATE_CANARY',
                      'access%255ftoken=PRIVATE_CANARY',
                      'token%3DPRIVATE_CANARY',
                      'batch%26token=PRIVATE_CANARY'):
            with self.subTest(query=query):
                self.assertIsNone(canonical_public_url('https://example.org/join?'+query))
        self.assertEqual(canonical_public_url('https://example.org/claim?batch=october'),
                         'https://example.org/claim?batch=october')
    def test_nested_encoded_spa_fragment_credentials_are_dropped(self):
        for fragment in ('/claim?%2574oken=PRIVATE_CANARY',
                         '/claim?%252574oken=PRIVATE_CANARY',
                         '/claim?batch=2026&%2563ode=PRIVATE_CANARY',
                         '/claim?batch%26%2574oken=PRIVATE_CANARY'):
            with self.subTest(fragment=fragment):
                url = 'https://example.org/#' + fragment
                self.assertIsNone(canonical_public_url(url))
                frozen = freeze_public_sources([sample('alpha', [url])])
                self.assertEqual(frozen['rows'], [])
                self.assertEqual(frozen['sources'][0]['invalid_rows'], 1)
        self.assertEqual(canonical_public_url('https://example.org/#/claim?batch=2026'),
                         'https://example.org/#/claim?batch=2026')
    def test_contact_identifiers_are_not_preserved_in_public_review(self):
        for key in ('email','phone'):
            with self.subTest(key=key):
                self.assertIsNone(canonical_public_url('https://example.org/join?'+key+'=PRIVATE_CANARY'))
    def test_legacy_public_urls_with_credentials_in_routes_are_rejected(self):
        for url in ('https://example.org/reset/token/PRIVATE_CANARY',
                    'https://example.org/reset/%74oken/PRIVATE_CANARY',
                    'https://example.org/apply/%2574oken/PRIVATE_CANARY',
                    'https://example.org/#/reset/token/PRIVATE_CANARY'):
            with self.subTest(url=url):
                self.assertIsNone(canonical_public_url(url))
                result=freeze_public_sources([sample('alpha',[url])])
                self.assertEqual(result['rows'],[])
                self.assertEqual(result['sources'][0]['invalid_rows'],1)
    def test_upstream_query_loss_makes_blind_identity_unverified(self):
        a=sample('alpha',['https://example.org/claim'])
        a[0]['rows'][0].pop('url_identity_preserved')
        a[0]['rows'][0]['url_sanitized']=True
        result=freeze_public_sources([a])
        self.assertEqual(result['rows'],[])
        self.assertEqual(result['sources'][0]['upstream_url_identity_lost'],1)
        self.assertFalse(result['upstream_identity_fully_preserved'])
    def test_legacy_unmarked_identity_cannot_enter_fresh_blind_denominator(self):
        for legacy in ({}, {'url_sanitized':False}, {'url_sanitized':True}):
            with self.subTest(legacy=legacy):
                a=sample('alpha',['https://example.org/claim'])
                a[0]['rows'][0].pop('url_identity_preserved')
                a[0]['rows'][0].update(legacy)
                result=freeze_public_sources([a])
                self.assertEqual(result['rows'],[])
                self.assertEqual(result['sources'][0]['upstream_url_identity_lost'],1)
                self.assertFalse(result['upstream_identity_fully_preserved'])
    def test_duplicate_cross_sources_and_order_independent(self):
        a=sample('alpha',['https://example.org/campaign'])
        b=sample('beta',['https://example.org/campaign','https://example.org/new'])
        x=freeze_public_sources([b,a])
        y=freeze_public_sources([a,b])
        self.assertEqual(x,y)
        self.assertEqual(len(x['rows']),2)
        self.assertEqual(x['sources'][1]['duplicate_across_source'],1)
    def test_dont_launder_duplicate_in_later_source_if_not_selected_earlier(self):
        a=sample('alpha',['https://example.org/a','https://example.org/b','https://example.org/c'])
        b=sample('beta',['https://example.org/a','https://example.org/b','https://example.org/c'])
        x=freeze_public_sources([a,b],limit=1)
        self.assertEqual(len(x['rows']),1)
        self.assertEqual(x['sources'][1]['duplicate_across_source'],3)
    def test_clamped_benefit_status_does_not_select_for_truth(self):
        a=sample('alpha',['https://example.org/a'])
        a[0]['rows'][0]['accepted']=False
        x=freeze_public_sources([a])
        self.assertEqual(len(x['rows']),1)
        self.assertNotIn('accepted',x['rows'][0])
        self.assertEqual(x['purpose'],'LOCAL_ONLY_REVIEW_CANDIDATES_HOLDOUT_UNVERIFIED')
    def test_malformed_row_cannot_steal_sample_quota(self):
        a=sample('alpha',['https://example.org/a','https://example.org/b'])
        a[0]['rows'][0]['title']=None
        x=freeze_public_sources([a],limit=1)
        self.assertEqual(len(x['rows']),1)
        self.assertEqual(x['rows'][0]['url'],'https://example.org/b')
        self.assertEqual(x['sources'][0]['invalid_rows'],1)
    def test_no_auto_dedup_different_urls_into_a_campaign(self):
        x=freeze_public_sources([sample('alpha',['https://example.org/a','https://example.org/b'])])
        self.assertEqual(len(x['rows']),2)
        self.assertTrue(x['exact_url_dedup_only'])
    def test_reject_bad_source_identity_public_only(self):
        a=sample('alpha',['https://example.org/a'])
        b=sample('alpha',['https://example.org/b'])
        with self.assertRaises(ValueError):freeze_public_sources([a,b])
        a[0]['public_only']=False
        with self.assertRaises(ValueError):freeze_public_sources([a])
    def test_url_userinfo_removed_not_republished(self):
        self.assertIsNone(canonical_public_url('https://user:password@example.org/path'))
        self.assertIsNone(canonical_public_url('ftp://example.org/x'))
    def test_duplicate_public_source_metadata_cannot_override_identity(self):
        with self.assertRaises(ValueError):
            parse_source_json(b'{"schema_version":1,"public_only":false,"public_only":true,"source_id":"alpha","rows":[]}')
    def test_bad_source_encoding_and_counts_are_rejected(self):
        for raw in (b'{"source_id":"\xff"}', b'{"stored_count":4,"rows":[]}', b'{"source_id":NaN}'):
            with self.subTest(raw=raw[:20]), self.assertRaises(ValueError):
                parse_source_json(raw)
    def test_local_cli_creates_new_private_file_no_overwrite(self):
        with tempfile.TemporaryDirectory() as p:
            source=Path(p)/'public.json'; dest=Path(p)/'review.json'
            source.write_text(json.dumps(sample('alpha',['https://example.org/a'])[0]))
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(main(['--input',str(source),'--output',str(dest)]),0)
            self.assertTrue(dest.exists()); self.assertIn('NOT PUBLISHED',out.getvalue())
            if os.name=='posix': self.assertEqual(dest.stat().st_mode&0o777,0o600)
            with self.assertRaises(SystemExit):main(['--input',str(source),'--output',str(dest)])

    def test_prior_review_exclusion_happens_before_source_cap(self):
        a=sample('alpha',['https://example.org/seen?utm_source=old',
                          'https://example.org/new'])
        result=freeze_public_sources([a],limit=1,
                 excluded_urls={'https://example.org/seen'})
        self.assertEqual([r['url'] for r in result['rows']], ['https://example.org/new'])
        self.assertEqual(result['sources'][0]['excluded_prior_url'],1)
        self.assertEqual(result['prior_url_exclusions'],1)

    def test_cli_excludes_legacy_and_new_prior_blind_samples_without_truth_labels(self):
        with tempfile.TemporaryDirectory() as d:
            directory=Path(d)
            source=directory/'source.json'
            legacy=directory/'legacy.json'
            prior=directory/'prior.json'
            output=directory/'new.json'
            source.write_text(json.dumps(sample('alpha',[
                'https://example.org/seen?utm_source=old',
                'https://example.org/seen2',
                'https://example.org/new'])[0]),encoding='utf-8')
            legacy.write_text(json.dumps([{'url':'https://example.org/seen'}]),encoding='utf-8')
            prior.write_text(json.dumps({'rows':[{'url':'https://example.org/seen2'}]}),encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()):
                status=main(['--input',str(source),'--output',str(output),
                             '--exclude-prior',str(legacy),'--exclude-prior',str(prior)])
            self.assertEqual(status,0)
            selected=json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual([r['url'] for r in selected['rows']],['https://example.org/new'])
            self.assertEqual(len(selected['prior_sha256']),2)
            self.assertNotIn('accepted',json.dumps(selected))

if __name__=='__main__':unittest.main()
