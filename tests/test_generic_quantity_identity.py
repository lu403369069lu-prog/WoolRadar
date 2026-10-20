"""Synthetic regression for generic numeric/compact offers; no live data or network."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from core.db import Database
from core.dedup import canonical_key
from core.models import Candidate


def candidate(url: str, title: str) -> Candidate:
    return Candidate("synthetic", "fixture", title, url)


class GenericQuantityIdentityTests(unittest.TestCase):
    def test_cross_vendor_compact_memory_is_separate(self):
        self.assertNotEqual(
            canonical_key(candidate("https://one.example/vps", "Free VPS 1GB")),
            canonical_key(candidate("https://two.example/vps", "Free VPS 1GB")),
        )

    def test_cross_vendor_unbranded_credit_amount_is_separate(self):
        self.assertNotEqual(
            canonical_key(candidate("https://one.example/credits", "Free $100 API credits")),
            canonical_key(candidate("https://two.example/credits", "Free $100 API credits")),
        )

    def test_same_landing_url_distinct_credit_quantities_remain_separate(self):
        self.assertNotEqual(
            canonical_key(candidate("https://vendor.example/deals", "Free 100 API credits")),
            canonical_key(candidate("https://vendor.example/deals", "Free 200 API credits")),
        )

    def test_compact_size_tracking_variants_keep_identity(self):
        self.assertEqual(
            canonical_key(candidate("https://vendor.example/vps?utm_source=one#top", "Free VPS 1GB")),
            canonical_key(candidate("https://vendor.example/vps?utm_medium=two", "Free VPS 1GB")),
        )

    def test_branded_compact_size_still_unifies_public_reposts(self):
        self.assertEqual(
            canonical_key(candidate("https://forum-a.example/post", "RackNerd Free VPS 1GB")),
            canonical_key(candidate("https://forum-b.example/post", "RackNerd Free VPS 1GB")),
        )

    def test_unbranded_year_batch_is_not_proof_of_shared_vendor(self):
        self.assertNotEqual(
            canonical_key(candidate("https://forum-a.example/post", "Free VPS 2026 GB")),
            canonical_key(candidate("https://forum-b.example/post", "Free VPS 2026 GB")),
        )

    def test_temporary_sqlite_keeps_each_vendor_and_dedups_repeated_tracking(self):
        # Runs only on a temporary database; no production files are opened.
        temp_root = Path(__file__).parents[1] / ".test-tmp"
        temp_root.mkdir(exist_ok=True)
        with TemporaryDirectory(dir=temp_root) as folder:
            db = Database(Path(folder) / "synthetic.db")
            first = db.upsert_candidate(candidate("https://one.example/vps", "Free VPS 1GB"))
            second = db.upsert_candidate(candidate("https://two.example/vps", "Free VPS 1GB"))
            repeat = db.upsert_candidate(candidate("https://one.example/vps?utm_source=again", "Free VPS 1GB"))
            self.assertNotEqual(first.event_id, second.event_id)
            self.assertTrue(first.notify)
            self.assertTrue(second.notify)
            self.assertEqual(repeat.event_id, first.event_id)
            self.assertFalse(repeat.notify)
            self.assertEqual(len(db.list_events()), 2)


if __name__ == "__main__":
    unittest.main()
