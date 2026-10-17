"""Red/green: URL path encoding must not launder secrets into public blind corpus."""
import json
import tempfile
import unittest
from pathlib import Path
from core.public_corpus import _clean_url_identity, record_public_sample

SRC={'id':'encoded-paths','auth':'public_feed','kind':'rss','platform':'synthetic'}
SENSITIVE=[
    'https://example.org/%74oken/synthetic-secret-42',
    'https://example.org/a%2ftoken/synthetic-secret-42',
    'https://example.org/%61pi%2dkey/synthetic-secret-42',
    'https://example.org/%2574oken/synthetic-secret-42',
    'https://example.org/a%252ftoken/synthetic-secret-42',
    'https://example.org/%73ession/synthetic-secret-42',
]

class EncodedPathLeak(unittest.TestCase):
    def test_encoded_secret_paths_redacted(self):
        for url in SENSITIVE:
            with self.subTest(url=url):
                self.assertEqual(_clean_url_identity(url),('[sensitive path redacted]',False))

    def test_encoded_secret_paths_not_written_in_any_public_field(self):
        url=SENSITIVE[0]
        with tempfile.TemporaryDirectory() as d:
            row={'url':url,'title':'Offer '+url,'summary':'Follow '+url}
            p=record_public_sample(Path(d),'rss',SRC,[row],[False])
            result=json.loads(p.read_text('utf-8'))['rows'][0]
            self.assertFalse(result['url_identity_preserved'])
            self.assertTrue(result['text_url_redacted'])
            self.assertNotIn('synthetic-secret-42',json.dumps(result))

    def test_benign_percent_encoded_path_is_not_scrubbed(self):
        url='https://example.org/docs/%65xamples'
        self.assertEqual(_clean_url_identity(url),(url,True))

if __name__=='__main__':unittest.main()
