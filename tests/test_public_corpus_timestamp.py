"""Historical WR-H10: reject untrusted or time-zone-free public feed dates."""
import json
import tempfile
import unittest
from pathlib import Path
from core.public_corpus import record_public_sample

SRC={'id':'feed1','auth':'public_feed','kind':'rss','platform':'synthetic'}
URL='https://example.org/valid'

class PublicTimestamp(unittest.TestCase):
    def check(self, timestamp, expected):
        with tempfile.TemporaryDirectory() as root:
            p=record_public_sample(Path(root),'synthetic',SRC,[{'url':URL,'title':'Public','published_at':timestamp}],[False]);self.assertIsNotNone(p)
            r=json.loads(p.read_text(encoding='utf8'))['rows'][0]
            self.assertEqual(r['published_at'],expected)
    def test_iso_z(self):self.check('2026-10-16T08:45:09Z','2026-10-16T08:45:09Z')
    def test_iso_offset(self):self.check('2026-10-16T16:45:09+08:00','2026-10-16T08:45:09Z')
    def test_rfc_gmt(self):self.check('Fri, 16 Oct 2026 08:45:09 GMT','2026-10-16T08:45:09Z')
    def test_rfc_offset(self):self.check('Fri, 16 Oct 2026 16:45:09 +0800','2026-10-16T08:45:09Z')
    def test_naive_iso(self):self.check('2026-10-16T08:45:09','')
    def test_date_without_time(self):self.check('2026-10-16','')
    def test_email_is_not_date(self):self.check('person@example.org','')
    def test_token_is_not_date(self):self.check('session=secret-token-value','')
    def test_private_path_is_not_date(self):self.check('/Users/local/.config/private','')
    def test_invalid_calendar_date(self):self.check('2026-02-30T01:00:00Z','')
if __name__=='__main__':unittest.main()
