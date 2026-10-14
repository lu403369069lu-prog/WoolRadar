import tempfile
import unittest
from pathlib import Path
from coordination.dispatcher import dispatch

SHA = 'a' * 40


def event(**kwargs):
    value = dict(project='SAM', repository='lu403369069lu-prog/YinQieJi', issue=1,
                 task_id='S-01', head_sha=SHA, event_type='evidence_ready',
                 evidence_url='https://github.com/lu403369069lu-prog/YinQieJi/issues/1')
    value.update(kwargs)
    return value


class DispatcherTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db = Path(tmp.name) / 'state.sqlite3'

    def test_duplicate_and_persistent_restart(self):
        self.assertEqual(dispatch(self.db, [event()])['decisions'][0]['result'], 'new')
        self.assertEqual(dispatch(self.db, [event()])['decisions'][0]['result'], 'duplicate_noop')
        self.assertEqual(dispatch(self.db, [event()])['decisions'][0]['result'], 'duplicate_noop')

    def test_rollback_on_conflicting_same_key(self):
        with self.assertRaisesRegex(ValueError, 'CONFLICTING_DUPLICATE'):
            dispatch(self.db, [event(), event(evidence_url=None)])
        self.assertEqual(dispatch(self.db, [event()])['decisions'][0]['result'], 'new')
        with self.assertRaisesRegex(ValueError, 'EVENT_KEY_PAYLOAD_CHANGED'):
            dispatch(self.db, [event(evidence_url=None)])

    def test_scope_validation_fails_closed(self):
        bad_cases = (event(issue=3), event(repository='evil/repo'), event(head_sha='short'),
                     event(task_id='../hack'), event(event_type='run_shell'),
                     event(evidence_url='https://attacker.example/secret'))
        for item in bad_cases:
            with self.subTest(item=item), self.assertRaises(ValueError):
                dispatch(self.db, [item])

    def test_quota_warning_blocks_and_untrusted_restore(self):
        result = dispatch(self.db, [event(event_type='quota_warning'),
                                    event(event_type='review_requested', task_id='S-02'),
                                    event(event_type='quota_restored', task_id='S-03')])
        self.assertTrue(result['quota_paused'])
        self.assertEqual(result['decisions'][1]['action'], 'defer_local_execution')
        self.assertEqual(result['decisions'][2]['state'], 'needs_approval')

    def test_project_isolation(self):
        wool = event(project='WoolRadar', repository='lu403369069lu-prog/WoolRadar',
                     issue=2, evidence_url='https://github.com/lu403369069lu-prog/WoolRadar/issues/2')
        self.assertEqual([x['result'] for x in dispatch(self.db, [event(), wool])['decisions']],
                         ['new', 'new'])

    def test_dry_run_does_not_persist(self):
        self.assertTrue(dispatch(self.db, [event()], dry_run=True)['dry_run'])
        self.assertEqual(dispatch(self.db, [event()])['decisions'][0]['result'], 'new')

    def test_batch_atomicity(self):
        with self.assertRaises(ValueError):
            dispatch(self.db, [event(), event(task_id='bad/unsafe')])
        self.assertEqual(dispatch(self.db, [event()])['decisions'][0]['result'], 'new')

    def test_unknown_denies_codex_by_default(self):
        result = dispatch(self.db, [event(event_type='review_requested')])
        self.assertTrue(result['quota_paused'])
        self.assertEqual(result['decisions'][0]['action'], 'defer_local_execution')


if __name__ == '__main__':
    unittest.main()
