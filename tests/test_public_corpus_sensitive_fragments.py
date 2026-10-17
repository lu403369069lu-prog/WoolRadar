"""Public blind samples must redact credentials encoded as fragment routes."""
import json
import tempfile
import unittest
from pathlib import Path
from core.public_corpus import _clean_url_identity, record_public_sample
SRC={'id':'synthetic-hash-routes','kind':'rss','auth':'public_feed','platform':'synthetic'}
class FragmentCredentialTest(unittest.TestCase):
    def test_hash_route_credential_path_is_not_admitted(self):
        for url in ('https://example.org/app#/token/SYNTHETIC-SECRET',
                    'https://example.org/app#!/api-key/SYNTHETIC-SECRET',
                    'https://example.org/app#/session/SYNTHETIC-SECRET'):
            with self.subTest(url=url):
                self.assertEqual(_clean_url_identity(url),('[sensitive fragment redacted]',False))
    def test_fragment_secret_does_not_escape_through_title_or_summary(self):
        url='https://example.org/app#/token/SYNTHETIC-SECRET'
        with tempfile.TemporaryDirectory() as d:
            row={'url':url,'title':'See '+url,'summary':'Use '+url}
            dest=record_public_sample(Path(d),'synthetic',SRC,[row],[False])
            sample=json.loads(dest.read_text())['rows'][0]
            self.assertNotIn('SYNTHETIC-SECRET',json.dumps(sample))
            self.assertEqual(sample['url'],'[sensitive fragment redacted]')
            self.assertFalse(sample['url_identity_preserved'])
    def test_harmless_fragment_route_still_preserves_identity(self):
        url='https://example.org/app#/docs/public'
        self.assertEqual(_clean_url_identity(url),(url,True))
if __name__=='__main__':unittest.main()
