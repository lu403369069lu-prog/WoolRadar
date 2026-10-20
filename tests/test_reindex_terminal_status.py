"""Reindex must not resurrect a manually closed campaign during a merge."""
import tempfile
import unittest
from pathlib import Path

from core.db import Database
from core.models import Candidate, Evidence, Status
from core.notify import NotificationQueue


class ReindexTerminalStatusTests(unittest.TestCase):
    def test_merge_preserves_terminal_state_on_either_member(self):
        for state in (Status.REDEEMED, Status.EXPIRED, Status.FAILED, Status.CONFLICTED):
            for terminal_on_survivor in (True, False):
                with self.subTest(state=state, survivor=terminal_on_survivor), tempfile.TemporaryDirectory() as td:
                    db = Database(Path(td) / 'copy.db')
                    original = Candidate('a', 'fixture', 'Acme Grant 2026', 'https://acme.example/launch')
                    duplicate = Candidate('b', 'fixture', 'Acme Grant 2026', 'https://acme.example/offer')
                    first = db.upsert_candidate(original).event_id
                    with db.connect() as conn:
                        conn.execute("UPDATE events SET canonical_key='legacy-id' WHERE id=?", (first,))
                    second = db.upsert_candidate(duplicate).event_id
                    self.assertNotEqual(first, second)
                    db.add_evidence(first, Evidence('official', 'https://acme.example/terms', 'acme-terms',
                                                     claims={'open': True, 'public': True, 'card_required': False}))
                    db.set_status(first if terminal_on_survivor else second, state, 'manual close')
                    # The merged evidence is superficially claimable, and must not reopen a manual terminal.
                    db.reindex()
                    remaining = db.list_events()
                    self.assertEqual(len(remaining), 1)
                    self.assertEqual(remaining[0]['status'], state.value)
                    self.assertEqual(remaining[0]['claim_scope'], 'NONE')
                    queue = NotificationQueue(db)
                    self.assertTrue(queue.enqueue(remaining[0]['id'], '', 'telegram-verified', 'candidate'))
                    dispatched = []
                    outcome = queue.flush({'telegram_send_enabled': True},
                                          sender=lambda payload: dispatched.append(payload))
                    self.assertEqual(outcome['sent'], 0)
                    self.assertEqual(dispatched, [])
                    self.assertEqual(queue.pending(), [])

    def test_conflicting_terminal_members_need_review(self):
        with tempfile.TemporaryDirectory() as td:
            db = Database(Path(td) / 'copy.db')
            first = db.upsert_candidate(Candidate('a', 'fixture', 'Acme Launch 2026',
                                                   'https://acme.example/one')).event_id
            with db.connect() as conn:
                conn.execute("UPDATE events SET canonical_key='historical-id' WHERE id=?", (first,))
            second = db.upsert_candidate(Candidate('b', 'fixture', 'Acme Launch 2026',
                                                    'https://acme.example/two')).event_id
            db.set_status(first, Status.REDEEMED, 'manual redeemed')
            db.set_status(second, Status.EXPIRED, 'manual expired')
            db.reindex()
            row = db.list_events()[0]
            self.assertEqual(row['status'], Status.CONFLICTED.value)
            self.assertEqual(row['claim_scope'], 'NONE')
            with db.connect() as conn:
                reasons = [r[0] for r in conn.execute('SELECT reason FROM status_history')]
            self.assertTrue(any('人工核验' in reason for reason in reasons))

    def test_positive_reindex_still_revalidates_nonterminal_merge(self):
        with tempfile.TemporaryDirectory() as td:
            db = Database(Path(td) / 'copy.db')
            a = db.upsert_candidate(Candidate('a', 'fixture', 'Acme Public Grant 2026',
                                              'https://acme.example/one')).event_id
            with db.connect() as conn:
                conn.execute("UPDATE events SET canonical_key='historical-id' WHERE id=?", (a,))
            db.upsert_candidate(Candidate('b', 'fixture', 'Acme Public Grant 2026',
                                          'https://acme.example/two'))
            db.add_evidence(a, Evidence('official', 'https://acme.example/terms', 'acme-terms',
                                        claims={'open': True, 'public': True}))
            db.reindex()
            self.assertEqual(db.list_events()[0]['status'], Status.CLAIMABLE.value)


if __name__ == '__main__':
    unittest.main()
