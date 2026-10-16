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
    return {'url':url,'title':'Public project','summary':'Public summary','accepted':True,**kwargs}
def sample(name, urls):
    return ({'schema_version':1,'public_only':True,'source_id':name,'rows':[row(u) for u in urls]},D)

class CleanSample(unittest.TestCase):
    def test_within_source_duplicate_removed_before_cap(self):
        out=freeze_public_sources([sample('alpha',['https://example.org/one?tracking=abc','https://EXAMPLE.org/one#ref','https://example.org/two'])],limit=8)
        self.assertEqual(len(out['rows']),2)
        self.assertEqual(out['sources'][0]['duplicate_within_source'],1)
        self.assertEqual(len({x['url'] for x in out['rows']}),2)
        self.assertTrue(all('tracking' not in x['url'] for x in out['rows']))
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
