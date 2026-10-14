import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.collector import collect_for_node

TMP = Path(__file__).parents[1] / '.test-tmp'
PUBLIC = {'id':'public-feed','owner_node':'openmagpie','kind':'rss','auth':'public_feed',
          'platform':'Test public feed','endpoint':'https://public.example/feed','enabled':True}
ROWS = [{'title':'Free VPS for developers','url':'https://public.example/offer','summary':'A trial offer'},
        {'title':'Server memory metrics','url':'https://public.example/question','summary':'A technical question'}]

class PublicCorpusTests(unittest.TestCase):
    def test_unmatched_public_rows_are_retained_without_extra_fetch(self):
        with tempfile.TemporaryDirectory(dir=TMP, ignore_cleanup_errors=True) as td:
            root = Path(td)
            with patch('core.collector.load_sources',return_value=[PUBLIC]), \
                 patch('core.collector.load_keywords',return_value=['free VPS']), \
                 patch('core.collector._fetch_source',return_value=ROWS) as fetch:
                result = collect_for_node(root,'openmagpie')
            self.assertEqual(len(result.candidates),1)
            path = root/'data/public-corpus/public-feed.json'
            self.assertTrue(path.is_file(),'Need unmatched public rows to assess false negatives')
            sample = json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(sample['fetched_count'],2)
            self.assertEqual(len(sample['rows']),2)
            self.assertEqual([row['accepted'] for row in sample['rows']],[True,False])
            fetch.assert_called_once()

    def test_authenticated_rows_are_not_persisted_as_public_corpus(self):
        from core.public_corpus import record_public_sample
        with tempfile.TemporaryDirectory(dir=TMP) as td:
            root = Path(td)
            result = record_public_sample(root,'clawradar',dict(PUBLIC,auth='oauth_required'),ROWS,[True,False])
            self.assertIsNone(result)
            self.assertFalse((root/'data/public-corpus').exists())

    def test_authenticated_kind_cannot_be_mislabeled_public(self):
        from core.public_corpus import record_public_sample
        with tempfile.TemporaryDirectory(dir=TMP) as td:
            root = Path(td)
            for kind in ['browser','reddit_oauth']:
                self.assertIsNone(record_public_sample(root,'clawradar',dict(PUBLIC,kind=kind),ROWS,[True,False]))
            self.assertFalse((root/'data/public-corpus').exists())

    def test_source_id_cannot_escape_corpus_directory(self):
        from core.public_corpus import record_public_sample
        with tempfile.TemporaryDirectory(dir=TMP) as td:
            root = Path(td)
            self.assertIsNone(record_public_sample(root,'openmagpie',dict(PUBLIC,id='../escape'),ROWS,[True,False]))
            self.assertFalse((root/'data/escape.json').exists())

    def test_snapshot_is_bounded_and_sanitizes_link_credentials(self):
        from core.public_corpus import record_public_sample
        with tempfile.TemporaryDirectory(dir=TMP) as td:
            root = Path(td)
            rows = [{'title':'Free API','url':'https://user:secret@public.example/a?token=secret','summary':'x'*21000}] * 501
            path = record_public_sample(root,'openmagpie',PUBLIC,rows,[True]*501)
            sample = json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(sample['fetched_count'],501)
            self.assertLessEqual(sample['stored_count'],500)
            self.assertGreater(sample['stored_count'],0)
            self.assertTrue(sample['rows_truncated'])
            self.assertTrue(sample['rows'][0]['content_truncated'])
            self.assertNotIn('secret',path.read_text(encoding='utf-8'))

    def test_urls_inside_text_also_redact_credentials_and_tokens(self):
        from core.public_corpus import record_public_sample
        with tempfile.TemporaryDirectory(dir=TMP) as td:
            link='HtTpS://alice:TESTONLYPASSWORD@public.example/private?access_token=TESTONLYTOKEN'
            rows=[{'title':'Offer '+link,'url':'https://public.example/post','summary':'See '+link}]
            path=record_public_sample(Path(td),'openmagpie',PUBLIC,rows,[True])
            content=path.read_text(encoding='utf-8')
            self.assertNotIn('TESTONLYPASSWORD',content)
            self.assertNotIn('TESTONLYTOKEN',content)
            self.assertTrue(json.loads(content)['rows'][0]['text_url_redacted'])

    def test_url_and_final_utf8_bytes_have_hard_limits(self):
        from core.public_corpus import record_public_sample
        with tempfile.TemporaryDirectory(dir=TMP) as td:
            rows=[{'title':'Free API','url':'https://public.example/'+'x'*10000,
                   'summary':'汉'*20000}]*500
            path=record_public_sample(Path(td),'openmagpie',PUBLIC,rows,[True]*500)
            self.assertLessEqual(path.stat().st_size,8000000)
            sample=json.loads(path.read_text(encoding='utf-8'))
            self.assertTrue(sample['rows_truncated'])
            self.assertTrue(sample['rows'][0]['content_truncated'])
            self.assertLessEqual(len(sample['rows'][0]['url']),2048)
