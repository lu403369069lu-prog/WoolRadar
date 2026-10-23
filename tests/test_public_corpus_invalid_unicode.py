"""Fail-closed validation of malformed surrogate characters from public feeds."""
import json
import tempfile
import unittest
from pathlib import Path
from core.public_corpus import record_public_sample

SOURCE = {'id': 'unicode-feed', 'auth': 'public_feed', 'kind': 'rss', 'platform': 'rss'}

class MalformedPublicUnicode(unittest.TestCase):
    def produce(self, *, url='https://example.org/item', title='A', summary='B', node='public', platform='rss'):
        with tempfile.TemporaryDirectory() as d:
            source = dict(SOURCE, platform=platform)
            p=record_public_sample(Path(d),node,source,[{'url':url,'title':title,'summary':summary}],[False])
            result=p.read_bytes().decode('utf-8', errors='strict')
            return json.loads(result)

    def test_invalid_title_surrogate_cannot_crash_public_sampling(self):
        record=self.produce(title='Public\ud800Title')
        self.assertNotIn('\\ud800', json.dumps(record))
        self.assertIn('Public', record['rows'][0]['title'])
        self.assertTrue(record['rows'][0]['text_url_redacted'])

    def test_invalid_summary_surrogate_is_scrubbed(self):
        record=self.produce(summary='Summary\udfffTail')
        self.assertNotIn('\\udfff', json.dumps(record))
        self.assertIn('Tail', record['rows'][0]['summary'])
        self.assertTrue(record['rows'][0]['text_url_redacted'])

    def test_invalid_url_surrogate_must_lose_identity(self):
        record=self.produce(url='https://example.org/p\ud800th?batch=1')
        self.assertFalse(record['rows'][0]['url_identity_preserved'])
        self.assertNotIn('\\ud800', json.dumps(record))

    def test_invalid_node_surrogate_is_not_written_raw(self):
        record=self.produce(node='collector\ud800agent')
        self.assertNotIn('\\ud800', json.dumps(record))
        self.assertTrue(record['node'].startswith('collector'))

    def test_invalid_platform_surrogate_is_not_written_raw(self):
        record=self.produce(platform='rss\udfffproduction')
        self.assertNotIn('\\udfff', json.dumps(record))
        self.assertTrue(record['platform'].startswith('rss'))

if __name__=='__main__': unittest.main()
