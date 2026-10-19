"""Raw daily report parsing must not override audited exclusions via JSON ambiguity."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone
from redact_daily import parse_daily_json, build_preview, main


RAW = {'date':'2026-10-16', 'noise_audit':{'excluded':1,'visible':0},
       'events':[{'title':'Approved example offer',
                  'primary_url':'https://example.org/offer',
                  'status':'DISCOVERED',
                  'report_audit':{'excluded':True},
                  'evidence':[]}]}


def checked(raw):
    return build_preview(parse_daily_json(raw),hashlib.sha256(raw).hexdigest(),
                         datetime(2026,10,16,0,0,tzinfo=timezone.utc))


class RawSourceAmbiguityTests(unittest.TestCase):
    def test_unambiguous_reviewed_exclusion_stays_excluded(self):
        obj=checked(json.dumps(RAW).encode('utf-8'))
        self.assertEqual(obj['count']['exported_events'],0)

    def test_duplicate_row_audit_flag_rejected_before_export(self):
        raw=json.dumps(RAW).replace(
            '"report_audit": {"excluded": true}',
            '"report_audit": {"excluded": true}, "report_audit": {"excluded": false}')
        self.assertIn('"report_audit": {"excluded": false}',raw)
        with self.assertRaises(ValueError): checked(raw.encode('utf-8'))

    def test_duplicate_global_noise_audit_rejected(self):
        raw=json.dumps(RAW).replace(
            '"noise_audit": {"excluded": 1, "visible": 0}',
            '"noise_audit": {"excluded": 1, "visible": 0}, "noise_audit": {"excluded": 0, "visible": 1}')
        with self.assertRaises(ValueError):checked(raw.encode('utf-8'))

    def test_duplicate_root_events_rejected(self):
        raw=json.dumps(RAW).replace('"events": [','"events": [], "events": [')
        with self.assertRaises(ValueError):checked(raw.encode('utf-8'))

    def test_invalid_nonfinite_and_large_exponent_rejected(self):
        for v in ('NaN','Infinity','-Infinity','1e9999','-1e9999'):
            with self.subTest(number=v),self.assertRaises(ValueError):
                parse_daily_json(('{"date":"2026-10-16","metric":'+v+'}').encode())

    def test_non_utf8_and_bom_rejected(self):
        for encoding in ('utf-8-sig','utf-16','utf-32'):
            with self.subTest(encoding=encoding),self.assertRaises(ValueError):
                parse_daily_json(json.dumps(RAW).encode(encoding))

    def test_too_deep_structure_rejected_consistently(self):
        raw=b'['*20000+b'0'+b']'*20000
        with self.assertRaises(ValueError):parse_daily_json(raw)

    def test_cli_never_creates_output_on_ambiguous_input(self):
        with tempfile.TemporaryDirectory() as folder:
            src=Path(folder)/'synthetic-raw.json'
            dst=Path(folder)/'never-created.json'
            raw=json.dumps(RAW).replace(
                '"report_audit": {"excluded": true}',
                '"report_audit": {"excluded": false}, "report_audit": {"excluded": true}')
            src.write_text(raw,encoding='utf-8')
            with self.assertRaises(ValueError):main(['--input',str(src),'--output',str(dst)])
            self.assertFalse(dst.exists())


if __name__=='__main__':unittest.main()