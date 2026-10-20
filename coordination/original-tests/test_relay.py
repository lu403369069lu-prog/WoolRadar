"""Fault and ownership acceptance for the V3 handoff contract."""
import copy
import tempfile
import unittest
from pathlib import Path

try:
    from coordination import relay
except ImportError:
    relay = None


class RelayContractTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(relay, 'V3 relay engine is required')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = relay.empty_state()
        self.task = relay.new_task('SAM', 'S-RELAY', 'a'*40,
                                   ['SAM/tests/'], 'Run isolated synthetic regression')
        self.state['tasks']['SAM/S-RELAY'] = self.task

    def event(self, **changes):
        item = dict(project='SAM', task_id='S-RELAY', head_sha='a'*40,
                    event_type='claim', actor='codex-local', expected_version=0,
                    lease_seconds=60, now=1000, fencing_token=None, data={})
        item.update(changes)
        return item

    def claim(self):
        self.state, result = relay.apply_event(self.state, self.event())
        return result['fencing_token']

    def test_exclusive_claim_and_fenced_old_owner(self):
        token = self.claim()
        with self.assertRaisesRegex(ValueError, 'OWNED|VERSION'):
            relay.apply_event(self.state, self.event(actor='chatgpt', expected_version=1))
        expired = self.event(actor='chatgpt', expected_version=1, now=1100)
        with self.assertRaisesRegex(ValueError, 'RECOVERY'):
            relay.apply_event(self.state, expired)
        self.state, _ = relay.apply_event(self.state, dict(expired, event_type='recover',
                                                         data={'observed_head_sha':'a'*40}))
        self.state, _ = relay.apply_event(self.state, dict(expired, expected_version=2))
        with self.assertRaisesRegex(ValueError, 'OWNER|FENCE'):
            relay.apply_event(self.state, self.event(event_type='heartbeat', now=1101,
                              expected_version=3, fencing_token=token))

    def test_idempotency_survives_restart_and_changed_payload_denied(self):
        self.claim()
        p = self.root / 'checkpoint.json'
        relay.atomic_checkpoint(p, self.state)
        loaded = relay.read_checkpoint(p)
        actual, receipt = relay.apply_event(loaded, self.event())
        self.assertEqual(actual, loaded)
        self.assertEqual(receipt['result'], 'duplicate_noop')
        with self.assertRaisesRegex(ValueError, 'PAYLOAD_CHANGED'):
            relay.apply_event(loaded, self.event(lease_seconds=120))

    def test_unknown_schema_corruption_and_unknown_field_fail_closed(self):
        for bad in [dict(self.state, schema_version=99), dict(self.state, command='rm')]:
            with self.assertRaises(ValueError):
                relay.validate_state(bad)
        p = self.root / 'checkpoint.json'
        relay.atomic_checkpoint(p, self.state)
        p.write_text('{"schema_version":', encoding='utf-8')
        with self.assertRaises(ValueError):
            relay.read_checkpoint(p)

    def test_overlapping_file_claim_rejected(self):
        self.claim()
        other = relay.new_task('SAM', 'S-OTHER', 'a'*40,
                               ['SAM/tests/example.py'], 'Second task')
        self.state['tasks']['SAM/S-OTHER'] = other
        with self.assertRaisesRegex(ValueError, 'FILE_CONFLICT'):
            relay.apply_event(self.state, self.event(task_id='S-OTHER', actor='other'))

    def test_stale_code_wrong_scope_and_unsafe_paths_denied(self):
        token = self.claim()
        for data in [{'observed_head_sha':'b'*40},
                     {'changed_files':['SAM/src/private.py']},
                     {'changed_files':['../escape']}]:
            with self.assertRaises(ValueError):
                relay.apply_event(self.state, self.event(event_type='start',
                                  expected_version=1, fencing_token=token, data=data))
        for scope in [['../escape'], ['C:/private'], ['SAM/../data'], ['SAM\\data']]:
            with self.assertRaises(ValueError):
                relay.new_task('SAM', 'BAD', 'a'*40, scope, 'Rejected')

    def test_transition_needs_evidence_and_independent_review(self):
        token = self.claim()
        def change(kind, data=None, actor='codex-local'):
            self.state, _ = relay.apply_event(self.state, self.event(
                event_type=kind, actor=actor, expected_version=self.state['tasks']['SAM/S-RELAY']['version'],
                fencing_token=token, data=data or {}))
        with self.assertRaises(ValueError):
            change('done')
        change('start')
        with self.assertRaisesRegex(ValueError, 'EVIDENCE'):
            change('evidence')
        evidence = dict(command='python -m unittest', exit_code=0, passed=3, failed=0,
                        head_sha='a'*40, artifact='SAM/evidence/synthetic.json')
        change('evidence', {'evidence':evidence})
        change('request_review')
        with self.assertRaisesRegex(ValueError, 'INDEPENDENT'):
            change('review', {'review':{'head_sha':'a'*40,'artifact':'SAM/evidence/review.json'}})
        change('review', {'review':{'head_sha':'a'*40,'artifact':'SAM/evidence/review.json'}}, actor='chatgpt-reviewer')
        change('done')
        self.assertEqual(self.state['tasks']['SAM/S-RELAY']['status'], 'done')

    def test_quota_pause_release_and_resume_requires_fresh_claim(self):
        token = self.claim()
        self.state, _ = relay.apply_event(self.state, self.event(event_type='quota_pause',
                          expected_version=1, fencing_token=token))
        task = self.state['tasks']['SAM/S-RELAY']
        self.assertIsNone(task['owner'])
        self.assertEqual(task['status'], 'quota_paused')
        with self.assertRaisesRegex(ValueError,'QUOTA_RESTORATION'):
            relay.apply_event(self.state,self.event(expected_version=2))
        with self.assertRaises(ValueError):
            relay.apply_event(self.state, self.event(event_type='start',
                              expected_version=2, fencing_token=token))

    def test_replay_queue_retries_permission_rate_and_crash_after_ack(self):
        q = relay.Outbox(self.root / 'queue')
        q.enqueue(self.event())
        q.enqueue(self.event())
        calls = []
        def send(e):
            calls.append(e)
            if len(calls) == 1:
                raise relay.RemoteError(429, retry_after=7)
            return {'sha':'b'*40}
        self.assertEqual(q.replay(send, now=0)['pending'], 1)
        self.assertEqual(q.replay(send, now=6)['attempted'], 0)
        self.assertEqual(q.replay(send, now=7)['pending'], 0)
        self.assertEqual(q.replay(send, now=8)['attempted'], 0)
        self.assertEqual(len(calls), 2)
        q.enqueue(self.event(event_type='heartbeat'))
        def denied(e):
            raise relay.RemoteError(403)
        self.assertEqual(q.replay(denied, now=20)['blocked'], 'permission_denied')
        self.assertEqual(q.replay(send, now=200)['attempted'], 0)
        q.enqueue(self.event(event_type='start',expected_version=2))
        self.assertEqual(q.replay(send, now=300)['attempted'], 0)

    def test_retry_ceiling_and_changed_queue_content(self):
        q = relay.Outbox(self.root / 'queue', max_attempts=2)
        q.enqueue(self.event())
        with self.assertRaisesRegex(ValueError, 'PAYLOAD_CHANGED'):
            q.enqueue(self.event(lease_seconds=120))
        def broken(e):
            raise relay.RemoteError(503)
        q.replay(broken, now=0)
        result = q.replay(broken, now=100)
        self.assertEqual(result['blocked'], 'retry_exhausted')
        self.assertEqual(q.replay(broken, now=1000)['attempted'], 0)

    def test_outbox_preserves_causal_order(self):
        q = relay.Outbox(self.root / 'queue')
        received = []
        for version in range(12):
            q.enqueue(self.event(expected_version=version))
        q.replay(lambda e: received.append(e['expected_version']), now=0)
        self.assertEqual(received, list(range(12)))

    def test_outbox_stops_after_transient_failure(self):
        q = relay.Outbox(self.root / 'queue')
        q.enqueue(self.event())
        q.enqueue(self.event(expected_version=1))
        calls = []
        def broken(e):
            calls.append(e)
            raise relay.RemoteError(0)
        q.replay(broken, now=0)
        self.assertEqual(len(calls), 1)
        self.assertEqual(q.replay(broken, now=1)['attempted'], 0)

    def test_unknown_event_data_and_boolean_fence_denied(self):
        with self.assertRaises(ValueError):
            relay.apply_event(self.state, self.event(data={'shell':'whoami'}))
        token = self.claim()
        self.assertEqual(token, 1)
        with self.assertRaises(ValueError):
            relay.apply_event(self.state, self.event(event_type='start', expected_version=1,
                              fencing_token=True))

    def test_forged_done_state_denied(self):
        self.task['status'] = 'done'
        with self.assertRaises(ValueError):
            relay.validate_state(self.state)

    def test_checkpoint_advances_code_and_invalidates_old_evidence(self):
        token = self.claim()
        self.state, _ = relay.apply_event(self.state, self.event(event_type='start',
                          expected_version=1, fencing_token=token))
        self.state, _ = relay.apply_event(self.state, self.event(event_type='checkpoint',
                          expected_version=2, fencing_token=token,
                          data={'new_head_sha':'b'*40, 'changed_files':['SAM/tests/fixture.py'],
                                'change_summary':'Synthetic new revision'}))
        self.assertEqual(self.state['tasks']['SAM/S-RELAY']['head_sha'], 'b'*40)
        with self.assertRaisesRegex(ValueError, 'STALE'):
            relay.apply_event(self.state, self.event(event_type='heartbeat', expected_version=3,
                              fencing_token=token))

    def test_register_new_task_without_reinitializing_remote(self):
        task=relay.new_task('SAM','S-NEW','b'*40,['SAM/review/'],'New independently scoped task')
        proposed=dict(task,status='proposed')
        with self.assertRaisesRegex(ValueError,'INVALID_REGISTRATION'):
            relay.apply_event(self.state,self.event(task_id='S-NEW',head_sha='b'*40,
                              event_type='register',data={'task':proposed}))
        self.state,receipt=relay.apply_event(self.state,self.event(task_id='S-NEW',head_sha='b'*40,
                               event_type='register',data={'task':task}))
        self.assertEqual(receipt['version'],1)
        self.assertEqual(self.state['tasks']['SAM/S-RELAY']['version'],0)
        self.state,_=relay.apply_event(self.state,self.event(task_id='S-NEW',head_sha='b'*40,
                           expected_version=1,event_type='claim'))
        self.assertEqual(self.state['tasks']['SAM/S-NEW']['owner'],'codex-local')


if __name__ == '__main__':
    unittest.main()
