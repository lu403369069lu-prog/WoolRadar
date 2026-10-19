"""Synthetic-only file bridge; no network, installation or real daily report."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from redact_daily import build_preview
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
            # This CLI uses the real UTC clock; the daily report date must
            # track the local report day instead of a fixed historical day.
            report_day=datetime.now(timezone.utc).astimezone(ZoneInfo('Asia/Shanghai')).date().isoformat()
            src.write_text(json.dumps({'date':report_day,'events':[item],
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


    def test_two_approved_synthetic_snapshots_only_emit_changed_and_removed_ids(self):
        first = datetime(2026, 10, 16, 0, 0, tzinfo=timezone.utc)
        later = first + timedelta(minutes=30)
        base = {'title': 'Approved synthetic public lead',
                'primary_url': 'https://example.org/first',
                'status': 'CLAIMABLE', 'batch_id': 'r1',
                'evidence': []}
        other = dict(base, title='Another approved synthetic lead',
                     primary_url='https://example.org/second')
        old = {'date': '2026-10-16', 'noise_audit': {'visible': 1},
               'events': [dict(base, report_audit={'excluded': False})]}
        # A previously visible record vanishes after an audit change; that
        # is *not* proof it has expired and must never become a live offer.
        newer = {'date': '2026-10-16', 'noise_audit': {'visible': 1},
                 'events': [dict(base, report_audit={'excluded': True}),
                            dict(other, report_audit={'excluded': False})]}
        previous = build_preview(old, '1' * 64, first)
        current = build_preview(newer, '2' * 64, later)
        def checked(preview, now):
            raw = json.dumps(preview, ensure_ascii=False).encode('utf-8')
            return validate(raw, hashlib.sha256(raw).hexdigest(), now=now)
        result = review_delta(checked(current, later), checked(previous, later))
        self.assertEqual(result['status'], 'MANUAL_SOURCE_RECHECK_REQUIRED')
        self.assertEqual(result['candidate_keys'], [current['events'][0]['event_key']])
        self.assertEqual(result['withdrawn_keys'], [previous['events'][0]['event_key']])
        text = json.dumps(result, ensure_ascii=False)
        self.assertNotIn('CLAIMABLE', text)
        self.assertNotIn('Approved synthetic public lead', text)
        self.assertNotIn('EXPIRED', text)

if __name__ == '__main__':unittest.main()
