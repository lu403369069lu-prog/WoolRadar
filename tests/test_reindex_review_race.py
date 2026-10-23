"""Campaign review ownership must remain stable across precheck/reindex races.

All scenarios use temporary SQLite and synthetic URLs. No production DB,
external network, notification delivery, or scheduler is touched.
"""
import json
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from core.db import Database
from core.models import Candidate


FIRST = 'https://publisher.example/a'
SECOND = 'https://publisher.example/b'
TITLES = {FIRST: 'Launch Vendor credit grant',
          SECOND: 'Last chance Vendor credit grant'}


def review(code):
    return {
        'method': 'normal_browser_read',
        'campaign_url': 'https://gleam.io/' + code,
        'member_urls': [FIRST, SECOND],
        'member_titles': TITLES,
    }


class ConcurrentCampaignReviewTests(unittest.TestCase):
    def seed(self, path):
        winner = Database(path)
        challenger = Database(path)
        winner.upsert_candidate(Candidate('node-one', 'synthetic', TITLES[FIRST], FIRST))
        winner.upsert_candidate(Candidate('node-two', 'synthetic', TITLES[SECOND], SECOND))
        return winner, challenger

    def test_direct_writer_rejects_unqualified_review_before_backup(self):
        with TemporaryDirectory() as temporary:
            db, _ = self.seed(Path(temporary) / 'review.db')
            base = review('Ab123')
            invalid = [
                {**base, 'member_urls': [FIRST]},
                {**base, 'member_urls': [FIRST, FIRST]},
                {**base, 'method': 'self_asserted'},
                {**base, 'member_titles': {FIRST: TITLES[FIRST]}},
            ]
            for candidate in invalid:
                with self.subTest(candidate=candidate):
                    with self.assertRaises(ValueError):
                        db.reindex(campaign_review=candidate)
                    with db.connect() as conn:
                        self.assertEqual(conn.execute(
                            'SELECT COUNT(*) FROM campaign_links').fetchone()[0], 0)
                        self.assertEqual(conn.execute(
                            'SELECT COUNT(*) FROM evidence WHERE provenance_key LIKE ?',
                            ('reviewed-campaign:%',)).fetchone()[0], 0)
                    self.assertEqual(
                        list(Path(temporary).glob('review-before-reindex-*.db')), [])
            self.assertEqual(len(db.list_events()), 2)

    def test_direct_writer_refuses_changed_same_url_review_content(self):
        with TemporaryDirectory() as temporary:
            db, _ = self.seed(Path(temporary) / 'review.db')
            accepted = review('Ab123')
            db.review_campaign(accepted)
            previous = {}
            with db.connect() as conn:
                for name in ('campaign_links', 'evidence'):
                    previous[name] = [tuple(row) for row in conn.execute(
                        'SELECT * FROM ' + name + ' ORDER BY 1')]
            original_backups = list(Path(temporary).glob('review-before-reindex-*.db'))
            changed = review('Ab123')
            changed['member_titles'] = {**TITLES, FIRST: 'Altered assertion'}
            with self.assertRaisesRegex(ValueError, '^CAMPAIGN_REVIEW_CONFLICT
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / 'review.db'
            winner, challenger = self.seed(path)
            reached, release = threading.Event(), threading.Event()
            outcome = {}
            original = challenger.reindex

            def paused_reindex(*args, **kwargs):
                reached.set()
                if not release.wait(10):
                    raise TimeoutError('second review not released')
                return original(*args, **kwargs)

            def competing_review():
                try:
                    outcome['competing'] = challenger.review_campaign(review('Bc234'))
                except BaseException as exc:
                    outcome['error'] = exc

            with mock.patch.object(challenger, 'reindex', side_effect=paused_reindex):
                thread = threading.Thread(target=competing_review)
                thread.start()
                try:
                    self.assertTrue(reached.wait(10), 'second reviewer never completed precheck')
                    accepted = winner.review_campaign(review('Ab123'))
                    self.assertEqual(accepted['merged'], 1)
                finally:
                    release.set()
                    thread.join(20)

            self.assertFalse(thread.is_alive())
            self.assertNotIn('competing', outcome)
            self.assertIsInstance(outcome.get('error'), ValueError)
            self.assertEqual(str(outcome['error']), 'CAMPAIGN_REVIEW_CONFLICT')
            with winner.connect() as conn:
                links = [json.loads(row[0])['campaign_url'] for row in
                         conn.execute('SELECT review_json FROM campaign_links')]
                self.assertEqual(len(links), 2)
                self.assertEqual(set(links), {'https://gleam.io/Ab123'})
                self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(), [])
            self.assertEqual(len(winner.list_events()), 1)
            self.assertEqual(len(list(Path(temporary).glob('review-before-reindex-*.db'))), 1)

    def test_two_reindexes_in_same_second_have_distinct_valid_backups(self):
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / 'review.db'
            db, _ = self.seed(path)
            with mock.patch('core.db.utc_now', return_value='2026-10-16T00:00:00Z'):
                first = db.reindex()
                second = db.reindex()
            self.assertNotEqual(first['backup'], second['backup'])
            self.assertTrue(Path(first['backup']).is_file())
            self.assertTrue(Path(second['backup']).is_file())
            self.assertEqual(len(db.list_events()), 2)


if __name__ == '__main__':
    unittest.main()
):
                db.reindex(campaign_review=changed)
            with db.connect() as conn:
                for name in ('campaign_links', 'evidence'):
                    self.assertEqual([tuple(row) for row in conn.execute(
                        'SELECT * FROM ' + name + ' ORDER BY 1')], previous[name])
            self.assertEqual(
                len(list(Path(temporary).glob('review-before-reindex-*.db'))),
                len(original_backups))

    def test_valid_direct_writer_still_migrates(self):
        with TemporaryDirectory() as temporary:
            db, _ = self.seed(Path(temporary) / 'review.db')
            outcome = db.reindex(campaign_review=review('Ab123'))
            self.assertEqual(outcome['merged'], 1)
            with db.connect() as conn:
                self.assertEqual(
                    conn.execute('SELECT COUNT(*) FROM campaign_links').fetchone()[0],
                    2)
                self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(), [])

    def test_wrapper_refuses_changed_same_url_review_content(self):
        with TemporaryDirectory() as temporary:
            db, _ = self.seed(Path(temporary) / 'review.db')
            accepted = review('Ab123')
            db.review_campaign(accepted)
            changed = review('Ab123')
            changed['member_titles'] = {**TITLES, FIRST: 'Altered assertion'}
            with self.assertRaisesRegex(ValueError, '^CAMPAIGN_REVIEW_CONFLICT
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / 'review.db'
            winner, challenger = self.seed(path)
            reached, release = threading.Event(), threading.Event()
            outcome = {}
            original = challenger.reindex

            def paused_reindex(*args, **kwargs):
                reached.set()
                if not release.wait(10):
                    raise TimeoutError('second review not released')
                return original(*args, **kwargs)

            def competing_review():
                try:
                    outcome['competing'] = challenger.review_campaign(review('Bc234'))
                except BaseException as exc:
                    outcome['error'] = exc

            with mock.patch.object(challenger, 'reindex', side_effect=paused_reindex):
                thread = threading.Thread(target=competing_review)
                thread.start()
                try:
                    self.assertTrue(reached.wait(10), 'second reviewer never completed precheck')
                    accepted = winner.review_campaign(review('Ab123'))
                    self.assertEqual(accepted['merged'], 1)
                finally:
                    release.set()
                    thread.join(20)

            self.assertFalse(thread.is_alive())
            self.assertNotIn('competing', outcome)
            self.assertIsInstance(outcome.get('error'), ValueError)
            self.assertEqual(str(outcome['error']), 'CAMPAIGN_REVIEW_CONFLICT')
            with winner.connect() as conn:
                links = [json.loads(row[0])['campaign_url'] for row in
                         conn.execute('SELECT review_json FROM campaign_links')]
                self.assertEqual(len(links), 2)
                self.assertEqual(set(links), {'https://gleam.io/Ab123'})
                self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(), [])
            self.assertEqual(len(winner.list_events()), 1)
            self.assertEqual(len(list(Path(temporary).glob('review-before-reindex-*.db'))), 1)

    def test_two_reindexes_in_same_second_have_distinct_valid_backups(self):
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / 'review.db'
            db, _ = self.seed(path)
            with mock.patch('core.db.utc_now', return_value='2026-10-16T00:00:00Z'):
                first = db.reindex()
                second = db.reindex()
            self.assertNotEqual(first['backup'], second['backup'])
            self.assertTrue(Path(first['backup']).is_file())
            self.assertTrue(Path(second['backup']).is_file())
            self.assertEqual(len(db.list_events()), 2)


if __name__ == '__main__':
    unittest.main()
):
                db.review_campaign(changed)
            with db.connect() as conn:
                saved = [json.loads(item[0]) for item in conn.execute(
                    'SELECT review_json FROM campaign_links')]
            self.assertEqual(len(saved), 2)
            self.assertTrue(all(item == accepted for item in saved))

    def test_conflicting_review_cannot_replace_commit_after_precheck(self):
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / 'review.db'
            winner, challenger = self.seed(path)
            reached, release = threading.Event(), threading.Event()
            outcome = {}
            original = challenger.reindex

            def paused_reindex(*args, **kwargs):
                reached.set()
                if not release.wait(10):
                    raise TimeoutError('second review not released')
                return original(*args, **kwargs)

            def competing_review():
                try:
                    outcome['competing'] = challenger.review_campaign(review('Bc234'))
                except BaseException as exc:
                    outcome['error'] = exc

            with mock.patch.object(challenger, 'reindex', side_effect=paused_reindex):
                thread = threading.Thread(target=competing_review)
                thread.start()
                try:
                    self.assertTrue(reached.wait(10), 'second reviewer never completed precheck')
                    accepted = winner.review_campaign(review('Ab123'))
                    self.assertEqual(accepted['merged'], 1)
                finally:
                    release.set()
                    thread.join(20)

            self.assertFalse(thread.is_alive())
            self.assertNotIn('competing', outcome)
            self.assertIsInstance(outcome.get('error'), ValueError)
            self.assertEqual(str(outcome['error']), 'CAMPAIGN_REVIEW_CONFLICT')
            with winner.connect() as conn:
                links = [json.loads(row[0])['campaign_url'] for row in
                         conn.execute('SELECT review_json FROM campaign_links')]
                self.assertEqual(len(links), 2)
                self.assertEqual(set(links), {'https://gleam.io/Ab123'})
                self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(), [])
            self.assertEqual(len(winner.list_events()), 1)
            self.assertEqual(len(list(Path(temporary).glob('review-before-reindex-*.db'))), 1)

    def test_two_reindexes_in_same_second_have_distinct_valid_backups(self):
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / 'review.db'
            db, _ = self.seed(path)
            with mock.patch('core.db.utc_now', return_value='2026-10-16T00:00:00Z'):
                first = db.reindex()
                second = db.reindex()
            self.assertNotEqual(first['backup'], second['backup'])
            self.assertTrue(Path(first['backup']).is_file())
            self.assertTrue(Path(second['backup']).is_file())
            self.assertEqual(len(db.list_events()), 2)


if __name__ == '__main__':
    unittest.main()
