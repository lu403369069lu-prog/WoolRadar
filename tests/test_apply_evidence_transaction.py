"""Keep supplemental evidence, verification and notice queue atomic during reindex.

All tests use a temporary SQLite database and make no external network calls.
"""
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from core.db import Database
from core.models import Candidate, Evidence
from core.pipeline import Pipeline


FIRST_URL = 'https://publisher.example/a'
SECOND_URL = 'https://publisher.example/b'
FIRST_TITLE = 'Launch Vendor credit grant'
SECOND_TITLE = 'Last chance Vendor credit grant'
REVIEW = {
    'method': 'normal_browser_read',
    'campaign_url': 'https://gleam.io/Ab123',
    'member_urls': [FIRST_URL, SECOND_URL],
    'member_titles': {FIRST_URL: FIRST_TITLE, SECOND_URL: SECOND_TITLE},
}


def official_proof():
    return Evidence('official', 'https://vendor.example/status', 'vendor-proof',
                    claims={'open': True, 'public': True, 'remaining': 0})


class ApplyEvidenceTransactionTests(unittest.TestCase):
    def seed(self, root):
        pipeline = Pipeline(root)
        other = Database(pipeline.db.path)
        one = other.upsert_candidate(Candidate('n', 'publisher', FIRST_TITLE, FIRST_URL)).event_id
        two = other.upsert_candidate(Candidate('n', 'publisher', SECOND_TITLE, SECOND_URL)).event_id
        self.assertNotEqual(one, two)
        return pipeline, other, one, two

    def test_review_waits_until_supplemental_evidence_and_status_are_committed(self):
        with tempfile.TemporaryDirectory() as name:
            pipeline, other, one, two = self.seed(Path(name))
            reached = threading.Event()
            release = threading.Event()
            attempted = threading.Event()
            finished = threading.Event()
            outcome = {}
            original = pipeline.db.get_event

            def paused_get_event(event_id):
                value = original(event_id)
                reached.set()
                if not release.wait(8):
                    raise TimeoutError('supplemental evidence was not released')
                return value

            def apply():
                try:
                    outcome['applied'] = pipeline.apply_evidence(two, [official_proof()])
                except BaseException as exc:
                    outcome['apply_error'] = repr(exc)

            def merge():
                attempted.set()
                try:
                    outcome['merged'] = other.review_campaign(REVIEW)
                except BaseException as exc:
                    outcome['merge_error'] = repr(exc)
                finally:
                    finished.set()

            with mock.patch.object(pipeline.db, 'get_event', side_effect=paused_get_event):
                t_apply = threading.Thread(target=apply, name='supplemental-evidence')
                t_merge = threading.Thread(target=merge, name='campaign-reindex')
                t_apply.start()
                try:
                    self.assertTrue(reached.wait(8))
                    t_merge.start()
                    self.assertTrue(attempted.wait(8))
                    self.assertFalse(finished.wait(.2),
                                     'campaign reindex committed between event lookup and evidence insert')
                finally:
                    release.set()
                    t_apply.join(15)
                    if t_merge.ident is not None:
                        t_merge.join(15)

            self.assertFalse(t_apply.is_alive())
            self.assertFalse(t_merge.is_alive())
            self.assertNotIn('apply_error', outcome)
            self.assertNotIn('merge_error', outcome)
            self.assertEqual(outcome['merged']['merged'], 1)
            self.assertEqual(len(other.list_events()), 1)
            self.assertEqual(other.list_events()[0]['id'], one)
            self.assertTrue(any(item.kind == 'official' and item.claims.get('remaining') == 0
                                for item in other.get_evidence(one)))
            self.assertEqual(other.get_event(one)['status'], 'OFFICIAL_VERIFIED')
            with other.connect() as conn:
                self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(), [])

    def test_verification_failure_rolls_back_every_supplemental_evidence_write(self):
        with tempfile.TemporaryDirectory() as name:
            pipeline, other, one, _ = self.seed(Path(name))
            with mock.patch.object(pipeline.verifier, 'evaluate',
                                   side_effect=RuntimeError('injected-verification-error')):
                with self.assertRaisesRegex(RuntimeError, 'injected-verification-error'):
                    pipeline.apply_evidence(one, [official_proof()])
            self.assertEqual(other.get_evidence(one), [])
            self.assertEqual(other.get_event(one)['status'], 'DISCOVERED')
            with other.connect() as conn:
                self.assertEqual(conn.execute('SELECT count(*) FROM status_history').fetchone()[0], 0)
                self.assertEqual(conn.execute('SELECT count(*) FROM notifications').fetchone()[0], 0)
            self.assertEqual(pipeline.apply_evidence(one, [official_proof()])['status'],
                             'OFFICIAL_VERIFIED')

    def test_merged_old_event_id_is_rejected_without_creating_orphan_evidence(self):
        with tempfile.TemporaryDirectory() as name:
            pipeline, other, _, two = self.seed(Path(name))
            other.review_campaign(REVIEW)
            with self.assertRaises(KeyError):
                pipeline.apply_evidence(two, [official_proof()])
            with other.connect() as conn:
                self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(), [])
                self.assertEqual(conn.execute('SELECT count(*) FROM notifications').fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()
