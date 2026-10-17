"""Public feed title and summary should not preserve credential-like values."""
import json
import tempfile
import unittest
from pathlib import Path
from core.public_corpus import record_public_sample

SRC={'id':'synthetic-plain-secrets','auth':'public_feed','kind':'rss','platform':'synthetic'}

class PlainTextSecretRedaction(unittest.TestCase):
    def test_bearer_api_key_and_long_digits_not_persisted(self):
        with tempfile.TemporaryDirectory() as d:
            rows=[{'url':'https://public.example.net/developer-grants',
                   'title':'New credits api_key=SYNTHETIC_SECRET_abcdef123456',
                   'summary':'Use Bearer SYNTHETIC_ABCDEFGHIJKLMNOPQRSTUVWXYZ or id 9999888877776666'}]
            p=record_public_sample(Path(d),'rss',SRC,rows,[False])
            out=p.read_text(encoding='utf-8')
            for secret in ('SYNTHETIC_SECRET_abcdef123456','SYNTHETIC_ABCDEFGHIJKLMNOPQRSTUVWXYZ','9999888877776666'):
                self.assertNotIn(secret,out)
            row=json.loads(out)['rows'][0]
            self.assertTrue(row['text_url_redacted'])
            self.assertTrue(row['url_identity_preserved'])

    def test_spaced_card_number_is_redacted(self):
        with tempfile.TemporaryDirectory() as d:
            row={'url':'https://public.example.net/offer',
                 'title':'Contact', 'summary':'Synthetic payment number: 9999 8888 7777 6666'}
            p=record_public_sample(Path(d),'rss',SRC,[row],[False])
            self.assertNotIn('9999 8888 7777 6666',p.read_text(encoding='utf-8'))

    def test_benign_technical_copy_stays(self):
        with tempfile.TemporaryDirectory() as d:
            title='Free API key program for open-source developers — $500 cloud credits'
            row={'url':'https://public.example.net/offer','title':title,
                 'summary':'Applications open, no card required'}
            p=record_public_sample(Path(d),'rss',SRC,[row],[False])
            saved=json.loads(p.read_text(encoding='utf-8'))['rows'][0]
            self.assertEqual(saved['title'],title)
            self.assertFalse(saved['text_url_redacted'])

if __name__=='__main__':unittest.main()
