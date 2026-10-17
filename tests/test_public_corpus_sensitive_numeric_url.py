"""Numeric secret-like identifiers may not survive in source URL or SPA route."""
import json
import tempfile
import unittest
from pathlib import Path
from core.public_corpus import _clean_url_identity, record_public_sample

SRC={'id':'synthetic-numeric-urls','auth':'public_feed','kind':'rss','platform':'synthetic'}

class SourceUrlNumericPrivacy(unittest.TestCase):
    def test_long_payment_looking_path_token_never_certified(self):
        for url in ('https://public.example.net/ref/9999888877776666',
                    'https://public.example.net/ref/9999-8888-7777-6666'):
            with self.subTest(url=url):
                safe,valid = _clean_url_identity(url)
                self.assertFalse(valid)
                self.assertNotIn('9999',safe)

    def test_spa_route_numeric_secret_is_not_persisted(self):
        url='https://public.example.net/#/offer/9999888877776666'
        with tempfile.TemporaryDirectory() as d:
            p=record_public_sample(Path(d),'rss',SRC,[{'url':url,'title':'Open grant','summary':'Public announcement'}],[False])
            saved=p.read_text(encoding='utf-8')
            self.assertNotIn('9999888877776666',saved)
            row=json.loads(saved)['rows'][0]
            self.assertFalse(row['url_identity_preserved'])

    def test_normal_short_public_numeric_selector_kept(self):
        url='https://public.example.net/2026/offer/12345'
        self.assertEqual(_clean_url_identity(url),(url,True))

if __name__=='__main__':unittest.main()
