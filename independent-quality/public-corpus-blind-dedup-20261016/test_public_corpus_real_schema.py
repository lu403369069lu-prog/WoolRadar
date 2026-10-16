"""Synthetic source producer -> independent sampler, actual core/public_corpus schema."""
import json
import tempfile
import unittest
from pathlib import Path
from core.public_corpus import record_public_sample
from freeze_public_sample_dedup import main

class RealCorpusProducerCompatibility(unittest.TestCase):
    def test_official_producer_output_deduplicates_before_local_review(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            source={'id':'publicfeed','auth':'public_feed','kind':'rss','platform':'test'}
            rows=[{'url':'https://example.org/a?ref=1','title':'Public item A','summary':'Public summary'},
                  {'url':'https://example.org/a?ref=2','title':'Public item same URL','summary':'Public duplicate'},
                  {'url':'https://example.org/b','title':'Public item B','summary':'Independent URL'}]
            source_path=record_public_sample(root,'synthetic',source,rows,[True,False,False])
            self.assertIsNotNone(source_path)
            out=root/'private-new-review.json'
            self.assertEqual(main(['--input',str(source_path),'--output',str(out)]),0)
            sampled=json.loads(out.read_text(encoding='utf-8'))
            self.assertEqual(sampled['sources'][0]['input_rows'],3)
            self.assertEqual(sampled['sources'][0]['duplicate_within_source'],1)
            self.assertEqual(len(sampled['rows']),2)
            self.assertEqual({r['url'] for r in sampled['rows']},
                             {'https://example.org/a','https://example.org/b'})
            self.assertTrue(all('accepted' not in r for r in sampled['rows']))
            self.assertFalse((root/'raw-user-accounts.json').exists())

if __name__=='__main__':unittest.main()
