import unittest
from datetime import datetime, timezone
from redact_daily import build_preview

BASE = {'title': 'Free VPS official', 'primary_url': 'https://offer.example.org/promo',
        'status': 'CLAIMABLE', 'batch_id': 'v1', 'evidence': []}


class NoiseAuditSafety(unittest.TestCase):
    def test_reviewed_noise_does_not_reappear(self):
        report = {'date': '2026-10-16', 'noise_audit': {'excluded': 1, 'visible': 1}, 'events': [
            dict(BASE, report_audit={'excluded': True, 'reason': 'scam review'}),
            dict(BASE, primary_url='https://offer.example.org/real', report_audit={'excluded': False}),
            dict(BASE, primary_url='https://offer.example.org/malformed', report_audit={'excluded': 'false'}),
            dict(BASE, primary_url='https://offer.example.org/missing')
        ]}
        out = build_preview(report, 'f' * 64, datetime(2026, 10, 16, tzinfo=timezone.utc))
        self.assertEqual(out['count']['exported_events'], 1)
        self.assertEqual(out['events'][0]['public_url'], 'https://offer.example.org/real')

    def test_legacy_no_audit_allows_only_unflagged(self):
        report = {'date': '2026-10-16', 'events': [
            dict(BASE),
            dict(BASE, primary_url='https://offer.example.org/flag', report_audit={'excluded': True})
        ]}
        out = build_preview(report, 'f' * 64, datetime(2026, 10, 16, tzinfo=timezone.utc))
        self.assertEqual(out['count']['exported_events'], 1)


if __name__ == '__main__':
    unittest.main()
