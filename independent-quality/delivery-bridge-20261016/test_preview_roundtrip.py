"""Synthetic-only file bridge; no network, installation or real daily report."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone
from redact_daily import main as export_preview
from consume_preview import validate, review_delta

class FileRoundtrip(unittest.TestCase):
    def test_export_then_consume_remains_review_only(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            src=root/'synthetic-raw.json'
            out=root/'preview.json'
            item={'title':'Example cloud test offer','primary_url':'https://example.org/test-offer',
                  'status':'CLAIMABLE','batch_id':'test1','first_seen':'2026-10-16T00:00:00Z',
                  'evidence':[{'kind':'official','url':'https://example.org/terms',
                               'checked_at':'2026-10-16T00:00:00Z',
                               'claims':{'public':True,'open':True}}]}
            src.write_text(json.dumps({'date':'2026-10-16','events':[item],
                                       'notifications':[{'payload':'private'}]}),encoding='utf-8')
            self.assertEqual(export_preview(['--input',str(src),'--output',str(out)]),0)
            raw=out.read_bytes()
            digest=hashlib.sha256(raw).hexdigest()
            stamp=datetime.fromisoformat(json.loads(raw)['generated_at'].replace('Z','+00:00'))
            obj=validate(raw,digest,now=stamp)
            r=review_delta(obj)
            self.assertEqual(r['status'],'BASELINE_ONLY')
            self.assertEqual(r['candidate_keys'],[])
            self.assertNotIn('private',raw.decode())
            self.assertEqual(obj['events'][0]['personal_eligibility'],'UNKNOWN')
            self.assertFalse(obj['public_application_live_verified'])

if __name__ == '__main__':unittest.main()
