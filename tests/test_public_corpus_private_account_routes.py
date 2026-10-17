"""Public-only reviewer samples cannot expose account/profile personal route names."""
import json
import tempfile
import unittest
from pathlib import Path
from core.public_corpus import _clean_url_identity, record_public_sample

SOURCE = {'id':'synthetic-private-routes','auth':'public_feed','kind':'rss','platform':'synthetic'}

class PrivateAccountRoutes(unittest.TestCase):
    def test_direct_account_paths_are_not_public_identity(self):
        for url in (
            'https://events.public-example.net/account/syntheticusername',
            'https://events.public-example.net/users/syntheticusername',
            'https://events.public-example.net/profile/syntheticusername',
            'https://events.public-example.net/billing/syntheticusername',
            'https://events.public-example.net/dashboard/user-settings',
            'https://events.public-example.net/%75sers/syntheticusername',
        ):
            with self.subTest(url=url):
                display, preserved = _clean_url_identity(url)
                self.assertFalse(preserved)
                self.assertNotIn('syntheticusername', display)
                self.assertNotIn('dashboard', display)

    def test_spa_account_identity_not_stored(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows=[{'url':'https://events.public-example.net/#/profile/syntheticusername',
                   'title':'A public opportunity','summary':'Public announcement'}]
            p=record_public_sample(Path(tmp),'rss',SOURCE,rows,[False])
            raw=p.read_text(encoding='utf-8')
            self.assertNotIn('syntheticusername',raw)
            saved=json.loads(raw)['rows'][0]
            self.assertFalse(saved['url_identity_preserved'])

    def test_public_docs_and_offer_paths_remain(self):
        for url in ('https://events.public-example.net/docs/user-guide',
                    'https://events.public-example.net/grants/2026',
                    'https://events.public-example.net/offer/45678'):
            with self.subTest(url=url):
                self.assertEqual(_clean_url_identity(url),(url,True))

if __name__=='__main__': unittest.main()
