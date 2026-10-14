import unittest
from core.collector import row_allowed

TECH = r'\b(?:vps|hosting|cloud|api|developer|github|software|server|ai|saas|database|domain)\b|开发者|云服务|服务器|学生包|模型额度'
SOURCE = {'required_text_regex':TECH,'allowed_hosts':['www.reddit.com','reddit.com'],'allowed_schemes':['https']}


class RedditHotScopeTests(unittest.TestCase):
    def test_physical_free_sample_is_outside_technology_scope(self):
        row={'url':'https://www.reddit.com/r/freebies/comments/abc/sample/',
             'title':'Free sample of Grace & Tallow grass-fed tallow body cream (pre-launch trial)',
             'summary':'A body cream sample for skincare.'}
        self.assertFalse(row_allowed(row,SOURCE))

    def test_technology_offer_in_title_or_description_is_kept(self):
        row={'url':'https://www.reddit.com/r/freebies/comments/abc/offer/',
             'title':'Free student credits','summary':'Cloud API credits for developers'}
        self.assertTrue(row_allowed(row,SOURCE))
        row.update(title='免费模型额度',summary='学生福利')
        self.assertTrue(row_allowed(row,SOURCE))

    def test_required_host_rejects_relative_or_credential_free_non_web_links(self):
        for url in ['/r/freebies/comments/abc','javascript:alert(1)','https://unrelated.example/api',
                    'javascript://www.reddit.com/%0Aalert(1)','ftp://www.reddit.com/post',
                    '//www.reddit.com/post','https://user:password@www.reddit.com/post',
                    'http://www.reddit.com/post']:
            self.assertFalse(row_allowed({'url':url,'title':'Free API'},SOURCE))

    def test_existing_sources_without_text_boundary_keep_previous_behavior(self):
        self.assertTrue(row_allowed({'url':'https://feed.example/post','title':'Sample'},{}))
