"""Isolated interleaving checks; imports the synthetic probe, not WoolRadar package."""
import unittest
from woolradar_reindex_upsert_race_probe import run, fixed_interleaving

class ReindexUpsertAtomicityProbe(unittest.TestCase):
    def test_existing_two_connection_protocol_can_emit_duplicate(self):
        run()
    def test_single_immediate_transaction_prevents_stale_identity(self):
        fixed_interleaving()

if __name__ == '__main__':
    unittest.main()