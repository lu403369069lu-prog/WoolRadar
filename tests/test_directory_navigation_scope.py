import unittest
from core.collector import row_allowed

class DirectoryNavigationScopeTests(unittest.TestCase):
    def test_exclude_directory_host_retains_external_offer_links(self):
        source={'exclude_hosts':['devhunt.org','www.devhunt.org']}
        for url in ['https://devhunt.org/perks','https://DEVHUNT.org/free-apis#list','https://www.devhunt.org/free-apis']:
            self.assertFalse(row_allowed({'url':url},source),url)
        for url in ['https://ai.google.dev/gemini-api/docs/pricing','https://vendor.example/perks','https://otherdevhunt.org/perks']:
            self.assertTrue(row_allowed({'url':url},source),url)
        self.assertTrue(row_allowed({'url':'https://devhunt.org/perks'},{}))
