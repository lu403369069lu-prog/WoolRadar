"""Public corpus cannot retain plainly credential-bearing source URL paths."""
import json
import tempfile
import unittest
from pathlib import Path
from core.public_corpus import _clean_url_identity, record_public_sample

SOURCE={'id':'synthetic-secret-paths','auth':'public_feed','kind':'rss','platform':'synthetic'}

class SensitivePathProtection(unittest.TestCase):
    def test_explicit_secret_segments_reject_url_identity(self):
        urls=('https://example.org/token/abc123',
              'https://example.org/session/a1b2c3',
              'https://example.org/password/credential-value',
              'https://example.org/api-key/not-a-real-key',
              'https://example.org/api_key/fake-key',
              'https://example.org/secret/synthetic-value')
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(_clean_url_identity(url),
                                 ('[sensitive path redacted]',False))

    def test_public_noncredential_paths_remain_valid(self):
        for url in ('https://example.org/docs/session',
                    'https://example.org/docs/token-usage',
                    'https://example.org/open-source/funding'):
            with self.subTest(url=url):
                self.assertEqual(_clean_url_identity(url),(url,True))

    def test_producer_removes_secret_path_from_url_title_summary(self):
        with tempfile.TemporaryDirectory() as root:
            url='https://example.org/api-key/synthetic-not-real'
            row={'url':url,'title':'Use '+url,'summary':'Reference '+url}
            p=record_public_sample(Path(root),'synthetic',SOURCE,[row],[False])
            sample=json.loads(p.read_text('utf8'))['rows'][0]
            self.assertFalse(sample['url_identity_preserved'])
            self.assertEqual(sample['url'],'[sensitive path redacted]')
            self.assertTrue(sample['text_url_redacted'])
            self.assertNotIn('synthetic-not-real',json.dumps(sample))

    def test_nonpublic_host_takes_precedence(self):
        self.assertEqual(_clean_url_identity('http://127.0.0.1/token/test'),
                         ('[non-public host redacted]',False))

if __name__=='__main__':unittest.main()
