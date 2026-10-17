"""Decision types must be authentic booleans, never Python truthiness coercion."""
import json
import tempfile
import unittest
from pathlib import Path
from core.public_corpus import record_public_sample
SOURCE={'id':'synthetic-label-types','auth':'public_feed','kind':'rss','platform':'synthetic'}
ROWS=[{'url':'https://example.org/offer','title':'Synthetic','summary':'No reward'}]

class PublicDecisionTypeBoundary(unittest.TestCase):
    def test_string_false_and_zero_are_not_certified_as_authoritative_labels(self):
        for bad in ('false','True',0,1,None,[],{},object()):
            with self.subTest(type=str(type(bad)), value=str(bad)[:20]), tempfile.TemporaryDirectory() as d:
                with self.assertRaisesRegex(ValueError,'CORPUS_DECISION_TYPE_MISMATCH'):
                    record_public_sample(Path(d),'synthetic',SOURCE,ROWS,[bad])
                self.assertFalse((Path(d)/'data/public-corpus/synthetic-label-types.json').exists())

    def test_real_bool_values_are_retained_exactly(self):
        for verdict in (False,True):
            with self.subTest(verdict=verdict), tempfile.TemporaryDirectory() as d:
                p=record_public_sample(Path(d),'synthetic',SOURCE,ROWS,[verdict])
                self.assertIs(json.loads(p.read_text())['rows'][0]['accepted'], verdict)

    def test_invalid_decision_beyond_500_cap_still_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            decisions=[False]*501+['false']
            rows=ROWS*502
            with self.assertRaisesRegex(ValueError,'CORPUS_DECISION_TYPE_MISMATCH'):
                record_public_sample(Path(d),'synthetic',SOURCE,rows,decisions)

if __name__=='__main__':unittest.main()
