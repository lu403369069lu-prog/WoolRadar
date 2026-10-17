"""Public corpus cannot leak email identities hidden in URL paths or plain feed text."""
import json
import tempfile
import unittest
from pathlib import Path
from core.public_corpus import _clean_url_identity, record_public_sample

SRC={'id':'synthetic-email-path','auth':'public_feed','kind':'rss','platform':'synthetic'}
IDENTIFIERS=(
    'https://public.example.net/users/synthetic@example.net/profile',
    'https://public.example.net/u/synthetic%40example.net',
    'https://public.example.net/u/synthetic%2540example.net',
)

class PublicPathIdentities(unittest.TestCase):
    def test_email_path_forms_are_redacted_before_public_storage(self):
        for url in IDENTIFIERS:
            with self.subTest(url=url):
                value,preserved=_clean_url_identity(url)
                self.assertFalse(preserved)
                self.assertNotIn('synthetic',value.lower())
                self.assertNotIn('%40',value.lower())

    def test_email_path_and_title_does_not_leak_into_corpus(self):
        with tempfile.TemporaryDirectory() as d:
            url=IDENTIFIERS[1]
            rows=[{'url':url, 'title':'Write to synthetic@example.net for help',
                   'summary':'https://public.example.net/users/synthetic%40example.net/profile'}]
            p=record_public_sample(Path(d),'rss',SRC,rows,[False])
            body=p.read_text()
            self.assertNotIn('synthetic@example.net',body)
            self.assertNotIn('synthetic%40example.net',body)
            row=json.loads(body)['rows'][0]
            self.assertFalse(row['url_identity_preserved'])
            self.assertTrue(row['text_url_redacted'])

    def test_valid_public_nonpersonal_path_retains_identity(self):
        url='https://public.example.net/docs/developer-grants'
        self.assertEqual(_clean_url_identity(url),(url,True))

if __name__=='__main__':unittest.main()
