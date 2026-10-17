"""Unicode-local-part emails must never enter public-only reviewer JSON."""
import json
import tempfile
import unittest
from pathlib import Path
from core.public_corpus import _clean_url_identity, record_public_sample

SRC={'id':'synthetic-unicode-mail', 'auth':'public_feed','kind':'rss','platform':'synthetic'}

class UnicodeMailboxPrivateIdentity(unittest.TestCase):
    def test_unicode_local_part_in_path_is_private_even_after_percent_decoding(self):
        urls=[
            'https://public.example.net/users/用户@example.net/profile',
            'https://public.example.net/users/%E7%94%A8%E6%88%B7%40example.net/profile',
            'https://public.example.net/u/δοκιμή@example.net',
        ]
        for url in urls:
            with self.subTest(url=url):
                text,good=_clean_url_identity(url)
                self.assertFalse(good)
                self.assertNotIn('example.net',text)
                self.assertNotIn('用户',text)

    def test_unicode_mail_in_feed_title_and_summary_does_not_persist(self):
        with tempfile.TemporaryDirectory() as d:
            rows=[{'url':'https://public.example.net/docs/grants',
                   'title':'Contact 用户@example.net',
                   'summary':'Mail δοκιμή%40example.net for access'}]
            p=record_public_sample(Path(d),'rss',SRC,rows,[False])
            out=p.read_text(encoding='utf-8')
            self.assertNotIn('用户@example.net',out)
            self.assertNotIn('δοκιμή%40example.net',out)
            self.assertTrue(json.loads(out)['rows'][0]['text_url_redacted'])

    def test_normal_unicode_text_remains(self):
        with tempfile.TemporaryDirectory() as d:
            rows=[{'url':'https://public.example.net/docs/grants',
                   'title':'面向开源维护者的开发者补助', 'summary':'无需付费，公开申请'}]
            p=record_public_sample(Path(d),'rss',SRC,rows,[False])
            row=json.loads(p.read_text(encoding='utf-8'))['rows'][0]
            self.assertIn('开源维护者',row['title'])
            self.assertTrue(row['url_identity_preserved'])

if __name__=='__main__':unittest.main()
