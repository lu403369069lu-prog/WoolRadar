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
    return {'url':url,'title':'Public project','summary':'Public summary','accepted':True,'url_identity_preserved':True,**kwargs}
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
    def test_private_hosts_never_enter_public_blind_candidates(self):
        blocked = [
            'http://localhost/offer', 'http://sub.localhost/offer',
            'http://127.0.0.1/offer', 'http://10.2.3.4/offer',
            'http://172.16.9.9/offer', 'http://192.168.0.10/offer',
            'http://169.254.1.1/offer', 'http://100.64.1.1/offer',
            'http://0.0.0.0/offer', 'http://[::1]/offer',
            'http://intranet/offer', 'http://nas.local/offer',
            'http://staging.internal/offer', 'http://lab.lan/offer',
            'http://router.home.arpa/offer', 'http://preview.test/offer',
            'http://sample.invalid/offer', 'http://example.example/offer',
            'http://hidden.onion/offer', 'http://127.1/offer',
            'http://2130706433/offer',
        ]
        for url in blocked:
            with self.subTest(url=url):
                self.assertIsNone(canonical_public_url(url))
        result=freeze_public_sources([sample('alpha',blocked+['https://example.org/offer'])],limit=8)
        self.assertEqual(len(result['rows']),1)
        self.assertEqual(result['sources'][0]['invalid_rows'],len(blocked))

    def test_home_arpa_apex_is_never_public_review_identity(self):
        blocked = [
            'http://home.arpa/offer',
            'https://home.arpa/private?batch=alpha',
            'http://router.home.arpa/offer',
        ]
        for url in blocked:
            with self.subTest(url=url):
                self.assertIsNone(canonical_public_url(url))
        self.assertEqual(canonical_public_url('https://home.arpa.info/offer'),
                         'https://home.arpa.info/offer')
        result = freeze_public_sources([sample('alpha', blocked + ['https://home.arpa.info/offer'])])
        self.assertEqual(len(result['rows']), 1)
        self.assertEqual(result['sources'][0]['invalid_rows'], len(blocked))

    def test_public_named_domains_still_keep_round_identity(self):
        self.assertEqual(canonical_public_url('https://example.org/claim?batch=1'),
                         'https://example.org/claim?batch=1')
        self.assertEqual(canonical_public_url('https://sub.example.org/claim?batch=2'),
                         'https://sub.example.org/claim?batch=2')
        self.assertEqual(canonical_public_url('https://example.org/claim?utm_source=x&batch=2'),
                         'https://example.org/claim?batch=2')

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
    def test_contact_identifiers_are_not_preserved_in_public_review(self):
        for key in ('email','phone'):
            with self.subTest(key=key):
                self.assertIsNone(canonical_public_url('https://example.org/join?'+key+'=PRIVATE_CANARY'))
    def test_upstream_query_loss_makes_blind_identity_unverified(self):
        a=sample('alpha',['https://example.org/claim'])
        a[0]['rows'][0]['url_sanitized']=True
        a[0]['rows'][0].pop('url_identity_preserved')
        result=freeze_public_sources([a])
        self.assertEqual(result['rows'],[])
        self.assertEqual(result['sources'][0]['upstream_url_identity_lost'],1)
        self.assertFalse(result['upstream_identity_fully_preserved'])
    def test_legacy_unproven_url_cannot_enter_new_blind_denominator(self):
        a=sample('alpha',['https://example.org/offer?batch=alpha'])
        a[0]['rows'][0].pop('url_identity_preserved')
        result=freeze_public_sources([a])
        self.assertEqual(result['rows'],[])
        self.assertEqual(result['sources'][0]['upstream_url_identity_lost'],1)

    def test_identity_proof_rejects_truthy_and_nonboolean_json_values(self):
        for forged in (None,1,0,'true','false',[],{},False):
            with self.subTest(forged=str(forged)):
                a=sample('alpha',['https://example.org/offer?batch=alpha'])
                a[0]['rows'][0]['url_identity_preserved']=forged
                result=freeze_public_sources([a])
                self.assertEqual(result['rows'],[])
                self.assertEqual(result['sources'][0]['upstream_url_identity_lost'],1)
        valid=freeze_public_sources([sample('alpha',['https://example.org/offer?batch=alpha'])])
        self.assertEqual(len(valid['rows']),1)

    def test_ambiguous_sanitized_marker_cannot_borrow_valid_identity_proof(self):
        for forged in (None,1,0,'true','false',[],{}):
            with self.subTest(forged=str(forged)):
                a=sample('alpha',['https://example.org/offer?batch=alpha'])
                a[0]['rows'][0]['url_sanitized']=forged
                result=freeze_public_sources([a])
                self.assertEqual(result['rows'],[])
                self.assertEqual(result['sources'][0]['upstream_url_identity_lost'],1)
        clean=sample('alpha',['https://example.org/offer?batch=alpha'])
        clean[0]['rows'][0]['url_sanitized']=False
        self.assertEqual(len(freeze_public_sources([clean])['rows']),1)

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

if __name__=='__main__':unittest.main()
