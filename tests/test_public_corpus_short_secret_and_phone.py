"""Small credentials and mobile numbers remain private even when low-entropy."""
import json
import tempfile
import unittest
from pathlib import Path
from core.public_corpus import record_public_sample

SRC={'id':'synthetic-short-secrets','auth':'public_feed','kind':'rss','platform':'synthetic'}

class ShortSecretAndPhonePrivacy(unittest.TestCase):
    def save(self, title, summary):
        with tempfile.TemporaryDirectory() as d:
            p=record_public_sample(Path(d),'rss',SRC,[{'url':'https://public.example.net/grants', 'title':title,'summary':summary}],[False])
            return json.loads(p.read_text(encoding='utf-8'))['rows'][0]

    def test_short_api_key_assignment_still_private(self):
        row=self.save('New release api_key=abc','Access: password="xy"')
        self.assertNotIn('abc',row['title'])
        self.assertNotIn('xy',row['summary'])
        self.assertTrue(row['text_url_redacted'])

    def test_short_bearer_token_cannot_be_disclosed(self):
        row=self.save('API grant','Authorization: Bearer abc')
        self.assertNotIn('Bearer abc',row['summary'])

    def test_eleven_digit_mobile_number_is_not_public_offer_identity(self):
        row=self.save('Contact 13800138000 for the giveaway','A developer grant announcement')
        self.assertNotIn('13800138000',row['title'])
        self.assertTrue(row['text_url_redacted'])

    def test_benign_cost_and_year_still_readable(self):
        row=self.save('2026 Developer credits worth $500','No payment card required')
        self.assertEqual(row['title'],'2026 Developer credits worth $500')
        self.assertFalse(row['text_url_redacted'])

if __name__=='__main__':unittest.main()
