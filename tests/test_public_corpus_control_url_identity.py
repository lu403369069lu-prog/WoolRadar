"""URL parse normalization must not turn untrusted control bytes into valid gold."""
import json
import tempfile
import unittest
from pathlib import Path
from core.public_corpus import _clean_url_identity, record_public_sample

SOURCE={'id':'synthetic-controls','auth':'public_feed','kind':'rss','platform':'synthetic'}

class UrlControlByteIdentity(unittest.TestCase):
    def test_tabs_newlines_and_carriage_returns_never_have_public_identity(self):
        for raw in ('https://example.org/a\rb','https://example.org/a\nb',
                    'https://example.org/a\tb','https://example.org/\x00x',
                    'https://example.org/x\x7fy'):
            with self.subTest(raw=repr(raw)):
                cleaned,preserved=_clean_url_identity(raw)
                self.assertEqual(cleaned,'[invalid URL redacted]')
                self.assertFalse(preserved)

    def test_leading_and_trailing_spaces_are_not_silently_trimmed(self):
        for raw in (' https://example.org/a','https://example.org/a ',
                    '\t https://example.org/a'):
            with self.subTest(raw=repr(raw)):
                self.assertEqual(_clean_url_identity(raw),('[invalid URL redacted]',False))

    def test_benign_public_url_remains_unchanged(self):
        self.assertEqual(_clean_url_identity('https://example.org/a?batch=A'),
                         ('https://example.org/a?batch=A',True))

    def test_sample_output_contains_no_unsafe_original_control_url(self):
        with tempfile.TemporaryDirectory() as root:
            raw='https://example.org/a\nb'
            rows=[{'url':raw,'title':'Text','summary':'No URL in summary'}]
            file=record_public_sample(Path(root),'synthetic',SOURCE,rows,[False])
            record=json.loads(file.read_text('utf8'))['rows'][0]
            self.assertEqual(record['url'],'[invalid URL redacted]')
            self.assertFalse(record['url_identity_preserved'])
            self.assertNotIn(raw,json.dumps(record))
            self.assertTrue(record['url_sanitized'])

if __name__=='__main__':unittest.main()
