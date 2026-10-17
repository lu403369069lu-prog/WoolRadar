"""Synthetic producer must deny alternate numeric IP host spellings and bad DNS labels."""
import json
import tempfile
import unittest
from pathlib import Path
from core.public_corpus import record_public_sample, _clean_url_identity

PUBLIC={'id':'alternate-numeric-hosts','auth':'public_feed','kind':'rss','platform':'synthetic'}
PRIVATE_ALIASES=(
  'http://0x7f.0x0.0x0.0x1/admin',
  'http://0x7f.1.2.3/secret',
  'http://169.254.169.0xfe/latest/meta-data',
  'http://0x0a.0x00.0x00.0x01/private',
  'https://0xa9.0xfe.0xa9.0xfe/metadata',
)
INVALID_DNS=(
  'https://.example.org/path',
  'https://bad-.example.org/path',
  'https://ok.-bad.example.org/path',
  'https://ok..example.org/path',
  'https://a.-.com/path',
)

class AlternateHostAdmission(unittest.TestCase):
    def test_numeric_ip_aliases_cannot_claim_public_url_identity(self):
        for url in PRIVATE_ALIASES:
            with self.subTest(url=url):
                cleaned, identity = _clean_url_identity(url)
                self.assertEqual(cleaned, '[non-public host redacted]')
                self.assertFalse(identity)

    def test_bad_dns_labels_cannot_claim_public_identity(self):
        for url in INVALID_DNS:
            with self.subTest(url=url):
                cleaned,identity=_clean_url_identity(url)
                self.assertEqual(cleaned,'[non-public host redacted]')
                self.assertFalse(identity)

    def test_actual_public_producer_redacts_numeric_ip_alias_in_all_fields(self):
        with tempfile.TemporaryDirectory() as d:
            url='http://169.254.169.0xfe/latest/meta-data'
            row={'url':url,'title':'Review '+url,'summary':'See '+url}
            path=record_public_sample(Path(d),'synthetic',PUBLIC,[row],[False])
            result=json.loads(path.read_text('utf8'))['rows'][0]
            self.assertNotIn('169.254.169.0xfe',json.dumps(result))
            self.assertFalse(result['url_identity_preserved'])
            self.assertTrue(result['text_url_redacted'])

    def test_valid_public_dns_and_numeric_subdomain_remain_accepted(self):
        for url in ('https://123.example.org/a','https://a-b.example.org/a',
                    'https://xn--bcher-kva.example.org/a','https://example.org/a'):
            with self.subTest(url=url):
                self.assertEqual(_clean_url_identity(url),(url,True))

if __name__=='__main__':unittest.main()
