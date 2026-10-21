import copy
import hashlib
import json
import unittest
from datetime import datetime, timezone, timedelta
from consume_preview import UnsafePreview, validate, review_delta

NOW = datetime(2026, 10, 16, 0, 30, tzinfo=timezone.utc)
ROW = {'event_key':'a'*24, 'title':'Example public benefit', 'public_url':'https://example.org/offer',
       'reported_status':'CLAIMABLE','publication_lane':'independent_official_recheck_required',
       'personal_eligibility':'UNKNOWN','batch_key':None, 'published_at':None,
       'first_seen':'2026-10-16T00:00:00Z', 'official_evidence': []}


def payload(*rows):
    return {'schema_version':1,'source_type':'LOCAL_REDACTED_PREVIEW_NOT_PUBLISHED',
            'report_date':'2026-10-16','generated_at':'2026-10-16T00:00:00Z',
            'source_report_sha256':'b'*64,'runtime_provenance_verified':False,
            'public_application_live_verified':False,
            'requires_operator_review_before_sharing':True,
            'count':{'input_events':len(rows),'exported_events':len(rows),'skipped_or_duplicate':0},
            'events': list(rows)}


def check(p, digest=None, now=NOW):
    data=json.dumps(p, ensure_ascii=False).encode()
    return validate(data, digest if digest is not None else hashlib.sha256(data).hexdigest(), now=now)


class PreviewGuard(unittest.TestCase):
    def test_encoded_title_secrets_rejected_despite_approved_sha(self):
        for title in ('Contact bob%40example.org',
                      'C%3A%5CUsers%5CAlice%5Csecrets.txt',
                      'free%20token%20bonus',
                      'Contact bob%2540example.org',
                      'win path C%253A%255CUsers%255CAlice'):
            with self.subTest(title=title), self.assertRaises(UnsafePreview):
                check(payload(dict(ROW, title=title)))
        check(payload(dict(ROW, title='Public offer 20% off')))
    def test_plural_credential_containers_rejected_even_with_valid_digest(self):
        for path in ('/api/tokens/PRIVATE_CANARY', '/accounts/PRIVATE_CANARY',
                     '/sessions/PRIVATE_CANARY', '/credentials/PRIVATE_CANARY',
                     '/users/PRIVATE_CANARY', '/api-keys/PRIVATE_CANARY'):
            with self.subTest(path=path), self.assertRaises(UnsafePreview):
                check(payload(dict(ROW, public_url='https://example.org' + path)))

    def test_numeric_ipv4_aliases_rejected_with_approved_digest(self):
        for host in ('127.1', '127.0.1', '0177.0.0.1',
                     '0x7f.0.0.1', '1.2.3.256'):
            with self.subTest(host=host), self.assertRaises(UnsafePreview):
                check(payload(dict(ROW, public_url=f'https://{host}/free-offer')))

    def test_local_domain_suffixes_rejected_with_approved_digest(self):
        for host in ('service.localhost', 'device.local', 'router.home.arpa',
                     'service.localdomain', 'box.lan', 'host.internal'):
            with self.subTest(host=host), self.assertRaises(UnsafePreview):
                check(payload(dict(ROW, public_url=f'https://{host}/free-offer')))

    def test_rejects_invisible_bidirectional_title_even_with_approved_digest(self):
        for marker in ('\u202e', '\u2066', '\u200b', '\u0085', '\u2028'):
            with self.subTest(marker=repr(marker)):
                with self.assertRaises(UnsafePreview):
                    check(payload(dict(ROW, title='Free cloud ' + marker + 'benefit')))

    def test_rejects_invisible_unicode_in_public_urls_even_with_digest(self):
        for url in ('https://example.org/benefit\u202eoffer',
                    'https://example.org/benefit%E2%80%AEoffer',
                    'https://example.org/benefit%E2%80%8Boffer'):
            with self.subTest(url=repr(url)):
                with self.assertRaises(UnsafePreview):
                    check(payload(dict(ROW, public_url=url)))

    def test_baseline_not_new(self):
        self.assertEqual(review_delta(check(payload(ROW)))['candidate_keys'],[])

    def test_distinct_delta_only_ids(self):
        old=check(payload(ROW))
        newer = payload(ROW, dict(ROW,event_key='c'*24))
        newer['generated_at'] = '2026-10-16T00:15:00Z'
        new=check(newer)
        r=review_delta(new,old)
        self.assertEqual(r['candidate_keys'],['c'*24])
        self.assertNotIn('Example public benefit',json.dumps(r))
        self.assertNotIn('CLAIMABLE',json.dumps(r))

    def test_digest_needed(self):
        with self.assertRaises(UnsafePreview):check(payload(ROW), '0'*64)
        with self.assertRaises(UnsafePreview):check(payload(ROW), '')

    def test_stale_and_future(self):
        with self.assertRaises(UnsafePreview):check(payload(ROW),now=NOW+timedelta(hours=40))
        with self.assertRaises(UnsafePreview):check(payload(ROW),now=NOW-timedelta(hours=1))

    def test_field_injection_and_promotion(self):
        p=payload(ROW);p['notifications']=[{'token':'x'}]
        with self.assertRaises(UnsafePreview):check(p)
        p=payload(dict(ROW,personal_eligibility='ELIGIBLE'))
        with self.assertRaises(UnsafePreview):check(p)
        p=payload(ROW);p['public_application_live_verified']=True
        with self.assertRaises(UnsafePreview):check(p)

    def test_denies_duplicate_or_falsified_counts(self):
        with self.assertRaises(UnsafePreview):check(payload(ROW,ROW))
        p=payload(ROW);p['count']['exported_events']=2
        with self.assertRaises(UnsafePreview):check(p)

    def test_duplicate_root_key_rejected_even_if_last_value_safe(self):
        data = json.dumps(payload(ROW)).replace(
            '"runtime_provenance_verified": false',
            '"runtime_provenance_verified": true, "runtime_provenance_verified": false')
        self.assertIn('"runtime_provenance_verified": true', data)
        raw = data.encode()
        with self.assertRaises(UnsafePreview):
            validate(raw, hashlib.sha256(raw).hexdigest(), now=NOW)

    def test_duplicate_event_field_rejected(self):
        data = json.dumps(payload(ROW)).replace(
            '"title": "Example public benefit"',
            '"title": "PRIVATE LEAK", "title": "Example public benefit"')
        self.assertIn('"title": "PRIVATE LEAK"', data)
        raw = data.encode()
        with self.assertRaises(UnsafePreview):
            validate(raw, hashlib.sha256(raw).hexdigest(), now=NOW)

    def test_duplicate_nested_claim_field_rejected(self):
        p = payload(dict(ROW, official_evidence=[{
            'url': 'https://example.org/official',
            'checked_at': '2026-10-16T00:00:00Z',
            'claims': {'public': True}}]))
        data = json.dumps(p).replace('"public": true',
                                     '"public": false, "public": true')
        self.assertIn('"public": false', data)
        raw = data.encode()
        with self.assertRaises(UnsafePreview):
            validate(raw, hashlib.sha256(raw).hexdigest(), now=NOW)

    def test_nonfinite_claim_rejected(self):
        p = payload(dict(ROW, official_evidence=[{
            'url': 'https://example.org/official',
            'checked_at': '2026-10-16T00:00:00Z',
            'claims': {'amount': float('nan')}}]))
        raw = json.dumps(p, allow_nan=True).encode()
        self.assertIn(b'NaN', raw)
        with self.assertRaises(UnsafePreview):
            validate(raw, hashlib.sha256(raw).hexdigest(), now=NOW)

    def test_exponent_overflow_cannot_become_nonfinite_claim(self):
        p = payload(dict(ROW, official_evidence=[{
            'url': 'https://example.org/official',
            'checked_at': '2026-10-16T00:00:00Z',
            'claims': {'amount': 1.0}}]))
        data = json.dumps(p).replace('"amount": 1.0', '"amount": 1e9999')
        self.assertIn('1e9999', data)
        raw = data.encode()
        with self.assertRaises(UnsafePreview):
            validate(raw, hashlib.sha256(raw).hexdigest(), now=NOW)

    def test_pathological_nesting_is_rejected_with_unsafe_preview(self):
        raw = b'[' * 20000 + b'0' + b']' * 20000
        with self.assertRaises(UnsafePreview):
            validate(raw, hashlib.sha256(raw).hexdigest(), now=NOW)

    def test_rejects_utf8_bom_preview(self):
        raw = json.dumps(payload(ROW)).encode('utf-8-sig')
        with self.assertRaises(UnsafePreview):
            validate(raw, hashlib.sha256(raw).hexdigest(), now=NOW)

    def test_rejects_utf16_preview(self):
        raw = json.dumps(payload(ROW)).encode('utf-16')
        with self.assertRaises(UnsafePreview):
            validate(raw, hashlib.sha256(raw).hexdigest(), now=NOW)

    def test_rejects_utf32_preview(self):
        raw = json.dumps(payload(ROW)).encode('utf-32')
        with self.assertRaises(UnsafePreview):
            validate(raw, hashlib.sha256(raw).hexdigest(), now=NOW)

    def test_bad_evidence_payload(self):
        p=payload(dict(ROW,official_evidence=[{'url':'https://example.org/a','checked_at':'2026-10-16T00:00:00Z','claims':{}, 'raw_content':'secret'}]))
        with self.assertRaises(UnsafePreview):check(p)

if __name__=='__main__':unittest.main()
