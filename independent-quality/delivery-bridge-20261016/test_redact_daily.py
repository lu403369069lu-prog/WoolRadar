import json
from itertools import product
import os
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from redact_daily import build_preview, main, public_claims, public_title, public_url

# The synthetic official check at 01:00 must precede snapshot generation.
NOW = datetime(2026, 10, 16, 2, tzinfo=timezone.utc)

def row(**kwargs):
    obj = {'id': 55, 'title': 'Public free VPS offer', 'primary_url': 'https://example.org/promo',
           'status': 'CLAIMABLE', 'claim_scope': 'PERSONAL_ACCOUNT', 'batch_id': 'b1',
           'metadata_json': '{"private": "SECRET"}', 'first_seen': '2026-10-16T01:00:00Z',
           'published_at': '2026-10-15T10:00:00Z',
           'evidence': [{'kind':'official', 'url':'https://example.org/promo',
                         'checked_at':'2026-10-16T01:00:00Z',
                         'excerpt':'private email user@example.org',
                         'claims':{'public':True, 'open':True, 'region':'CN', 'remaining':0,
                                   'card_required': True, 'private_account':'user@example.org'}}]}
    obj.update(kwargs)
    return obj

class Contract(unittest.TestCase):
    def preview(self, records):
        return build_preview({'date':'2026-10-16', 'events':records,
                              'notifications':[{'payload':'PRIVATE_NOTIFICATION'}],
                              'node_runs':[{'detail':'PRIVATE_PATH'}]}, 'a'*64, NOW)

    def test_invisible_direction_controls_are_not_exported_as_offer_titles(self):
        # Public snippets can contain bidirectional overrides and non-ASCII
        # control characters that change how the final brief appears.
        for marker in ('\u202e', '\u2066', '\u200b', '\u0085', '\u2028'):
            with self.subTest(marker=repr(marker)):
                poisoned = 'Free cloud ' + marker + 'benefit'
                self.assertIsNone(public_title(poisoned))
                self.assertEqual(self.preview([row(title=poisoned)])['events'], [])
        self.assertEqual(public_title('免费云资源 ☁️'), '免费云资源 ☁️')

    def test_whitelist_only_and_no_eligibility_promotion(self):
        p=self.preview([row()]); item=p['events'][0]
        self.assertEqual(item['publication_lane'], 'independent_official_recheck_required')
        self.assertEqual(item['personal_eligibility'],'UNKNOWN')
        self.assertFalse(p['public_application_live_verified'])
        self.assertEqual(item['official_evidence'][0]['claims']['remaining'],0)
        text=json.dumps(p)
        for secret in ('SECRET', 'PRIVATE_NOTIFICATION','PRIVATE_PATH','user@example.org','PERSONAL_ACCOUNT','private_account','"id": 55'):
            self.assertNotIn(secret,text)

    def test_unicode_controls_in_urls_and_encoded_routes_rejected(self):
        poison = (
            'https://example.org/benefit\u202eoffer',
            'https://example.org/benefit%E2%80%AEoffer',
            'https://example.org/benefit\u200boffer',
            'https://example.org/benefit%E2%80%8Boffer',
        )
        for url in poison:
            with self.subTest(url=repr(url)):
                self.assertIsNone(public_url(url))
                self.assertEqual(self.preview([row(primary_url=url)])['events'], [])
        self.assertEqual(public_url('https://example.org/normal%E4%B8%AD%E6%96%87'),
                         'https://example.org/normal%E4%B8%AD%E6%96%87')

    def test_query_credentials_and_account_routes_denied(self):
        for url in ['http://example.org/promo','https://me:pass@example.org/a','https://localhost/a',
                    'https://example.org/a?access_token=s','https://example.org/account/reset',
                    'https://example.org/checkout', 'https://127.0.0.1/a', 'https://example.org/a#x']:
            self.assertIsNone(public_url(url),url)
        self.assertEqual(self.preview([row(primary_url='https://example.org/checkout')])['count']['exported_events'],0)

    def test_titles_secrets_denied(self):
        for title in ['Reach bob@example.org today', 'my token secret', 'credit 1234567890123456', '123456789012345678']:
            self.assertIsNone(public_title(title))
            self.assertEqual(self.preview([row(title=title)])['count']['exported_events'],0)

    def test_official_evidence_requires_public_clean_https_url_and_time(self):
        p=self.preview([row(evidence=[{'kind':'official','url':'https://example.org/page?token=x','checked_at':'2026-10-16T01:00:00Z'},
                                     {'kind':'community','url':'https://example.org/foo','checked_at':'2026-10-16T01:00:00Z'},
                                     {'kind':'official','url':'https://example.org/safe','checked_at':'2026-10-16T01:00:00Z','claims':{'auto_renew':False,'region':'private detail','remaining': True}}])])
        self.assertEqual(len(p['events'][0]['official_evidence']),1)
        self.assertEqual(p['events'][0]['official_evidence'][0]['claims'],{'auto_renew':False})

    def test_distinct_batches_and_duplicate_events(self):
        p=self.preview([row(),row(),row(batch_id='b2')])
        self.assertEqual(p['count'],{'input_events':3,'exported_events':2,'skipped_or_duplicate':1})
        self.assertNotEqual(p['events'][0]['event_key'],p['events'][1]['event_key'])

    def test_invalid_dates_and_status_fail_closed(self):
        with self.assertRaises(ValueError):build_preview({'date':'2026-02-30','events':[]},'abc',NOW)
        self.assertEqual(self.preview([row(status='CLAIM_NOW')])['count']['exported_events'],0)
        self.assertEqual(self.preview([row(status=['CLAIMABLE'])])['count']['exported_events'],0)
        self.assertEqual(self.preview([row(status={'unexpected':'object'})])['count']['exported_events'],0)
        self.assertEqual(self.preview([row(first_seen='invalid')])['events'][0]['first_seen'],None)

    def test_invalid_unicode_surrogates_fail_closed_per_event(self):
        for field, value in (
            ('title', 'Unsafe ' + chr(0xD800) + ' free offer'),
            ('primary_url', 'https://example.org/' + chr(0xD800) + '/offer'),
            ('batch_id', 'bad-' + chr(0xD800)),
        ):
            with self.subTest(field=field):
                p = self.preview([row(**{field: value}), row(batch_id='legitimate')])
                self.assertEqual(p['count']['exported_events'], 1)
                self.assertEqual(p['count']['skipped_or_duplicate'], 1)
                json.dumps(p, ensure_ascii=False).encode('utf-8')

    def test_claim_types_are_strict(self):
        self.assertEqual(public_claims({'public':'true','remaining':False,'region':'sensitive@example.com','expires_at':'2026-10-16'}),{})

    def test_malformed_field_matrix_no_uncaught_errors(self):
        kinds = [None, False, 0, 2.4, [], {}, ['bad'], {'bad': 1}, 'bad', 'CLAIMABLE']
        checked = 0
        for status, title, url, batch, evidence in product(kinds, kinds, kinds[:9], kinds[:9], kinds[:9]):
            result = self.preview([row(status=status, title=title,
                                       primary_url=url, batch_id=batch, evidence=evidence)])
            self.assertEqual(result['source_type'], 'LOCAL_REDACTED_PREVIEW_NOT_PUBLISHED')
            checked += 1
        self.assertEqual(checked, 72900)

    def test_cli_explicit_local_new_file_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            src,dst=Path(d)/'raw.json',Path(d)/'only-local-preview.json'
            src.write_text(json.dumps({'date':'2026-10-16','events':[row()]}),encoding='utf-8')
            self.assertEqual(main(['--input',str(src),'--output',str(dst)]),0)
            self.assertTrue(dst.exists())
            self.assertEqual(json.loads(dst.read_text())['count']['exported_events'],1)
            if os.name=='posix':self.assertEqual(dst.stat().st_mode&0o777,0o600)
            with self.assertRaises(SystemExit):main(['--input',str(src),'--output',str(dst)])
            self.assertEqual(json.loads(dst.read_text())['source_type'],'LOCAL_REDACTED_PREVIEW_NOT_PUBLISHED')

if __name__=='__main__':unittest.main()
