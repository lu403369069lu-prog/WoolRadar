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
