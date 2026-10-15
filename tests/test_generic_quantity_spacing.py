"""Same public promotion must not generate duplicate events for 1GB/1 GB title variants."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from core.dedup import canonical_key
from core.db import Database
from core.models import Candidate


def offer(title, url='https://vendor.example/promo'):
    return Candidate('synthetic', 'fixture', title, url)


class ResourceSpacingIdentityTests(unittest.TestCase):
    def test_same_url_compact_and_spaced_gb_share_key(self):
        self.assertEqual(canonical_key(offer('Free VPS 1GB')),
                         canonical_key(offer('Free VPS 1 GB')))

    def test_same_url_compact_and_spaced_mb_share_key(self):
        self.assertEqual(canonical_key(offer('Free VPS 512MB')),
                         canonical_key(offer('Free VPS 512 MB')))

    def test_same_url_compact_and_spaced_tb_share_key(self):
        self.assertEqual(canonical_key(offer('Free VPS 1TB')),
                         canonical_key(offer('Free VPS 1 tb')))

    def test_different_vendor_still_separate(self):
        self.assertNotEqual(canonical_key(offer('Free VPS 1GB', 'https://a.example/deal')),
                            canonical_key(offer('Free VPS 1 GB', 'https://b.example/deal')))

    def test_different_sizes_still_separate(self):
        self.assertNotEqual(canonical_key(offer('Free VPS 1 GB')),
                            canonical_key(offer('Free VPS 2GB')))

    def test_branded_cross_post_key_retains_historical_spelling(self):
        self.assertEqual(canonical_key(offer('RackNerd Free VPS 1GB', 'https://a.example/deal')),
                         canonical_key(offer('RackNerd Free VPS 1GB', 'https://b.example/deal')))
        self.assertNotEqual(canonical_key(offer('RackNerd Free VPS 1GB')),
                            canonical_key(offer('RackNerd Free VPS 1 GB')))

    def test_sqlite_same_offer_changes_title_spacing_no_duplicate_alert(self):
        with TemporaryDirectory() as root:
            db = Database(Path(root) / 'synthetic.db')
            a = db.upsert_candidate(offer('Free VPS 1GB'))
            b = db.upsert_candidate(offer('Free VPS 1 GB'))
            self.assertEqual(a.event_id, b.event_id)
            self.assertTrue(a.notify)
            self.assertFalse(b.notify)
            self.assertEqual(len(db.list_events()), 1)


if __name__ == '__main__':
    unittest.main()
