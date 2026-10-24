import copy
import unittest
from core.dedup import reviewed_campaign_url

FIRST = 'https://publisher.example/a'
SECOND = 'https://publisher.example/b'
TITLE1 = 'Launch Vendor credit grant'
TITLE2 = 'Last chance Vendor credit grant'

def review():
    return dict(method='normal_browser_read', campaign_url='https://gleam.io/Ab123',
                member_urls=[FIRST, SECOND], member_titles={FIRST: TITLE1, SECOND: TITLE2})

class ReviewedUrlControlTests(unittest.TestCase):
    def test_control_in_reviewed_member_url_is_denied(self):
        for bad in (FIRST+'\n', FIRST+'\t', 'https://publisher.example/\na', FIRST+'\u200b', FIRST+'\u202e'):
            with self.subTest(bad=repr(bad)):
                sample=review()
                sample['member_urls'][0]=bad
                sample['member_titles']={bad:TITLE1, SECOND:TITLE2}
                self.assertIsNone(reviewed_campaign_url(sample,bad))

    def test_control_in_supplied_member_identity_is_denied(self):
        for bad in (FIRST+'\n', 'https://publisher.example/\ta', FIRST+'\u200b'):
            with self.subTest(bad=repr(bad)):
                self.assertIsNone(reviewed_campaign_url(review(),bad))

    def test_control_in_campaign_url_is_denied(self):
        for bad in ('https://gleam.io/Ab123\n','https://gleam.io/Ab123\u200b', '\x01https://gleam.io/Ab123'):
            with self.subTest(bad=repr(bad)):
                sample=review()
                sample['campaign_url']=bad
                self.assertIsNone(reviewed_campaign_url(sample,FIRST))

    def test_plain_valid_review_and_unicode_title_remain_accepted(self):
        self.assertEqual(reviewed_campaign_url(review(),FIRST,TITLE1),'https://gleam.io/Ab123')
        self.assertEqual(reviewed_campaign_url(review(),SECOND,TITLE2),'https://gleam.io/Ab123')

if __name__=='__main__':
    unittest.main()

class ReviewOuterWhitespaceTests(unittest.TestCase):
    def test_space_tainted_member_and_campaign_urls_are_not_reviewed(self):
        for bad in (' '+FIRST,FIRST+' ','\u00a0'+FIRST):
            with self.subTest(member=repr(bad)):
                self.assertIsNone(reviewed_campaign_url(review(),bad))
        for bad in (' https://gleam.io/Ab123','\u00a0https://gleam.io/Ab123'):
            with self.subTest(campaign=repr(bad)):
                sample=review()
                sample['campaign_url']=bad
                self.assertIsNone(reviewed_campaign_url(sample,FIRST))

class ReviewTitleControlTests(unittest.TestCase):
    def test_spoofed_runtime_title_cannot_inherit_review_identity(self):
        for title in (TITLE1+'\u202e', TITLE1+'\u200b', TITLE1+'\n', TITLE1+'\t'):
            with self.subTest(title=repr(title)):
                self.assertIsNone(reviewed_campaign_url(review(), FIRST, title))

    def test_poisoned_reviewed_title_does_not_certify_original(self):
        for title in (TITLE1+'\u202e', TITLE1+'\u200b', TITLE1+'\n'):
            with self.subTest(title=repr(title)):
                candidate=review()
                candidate['member_titles'][FIRST]=title
                self.assertIsNone(reviewed_campaign_url(candidate, FIRST, TITLE1))

    def test_normal_multilingual_title_works(self):
        candidate=review()
        candidate['member_titles'][FIRST]='免费云服务 ☁️'
        self.assertEqual(reviewed_campaign_url(candidate,FIRST,'免费云服务 ☁️'),
                         'https://gleam.io/Ab123')
