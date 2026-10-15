"""Real process interruption and offline fault injection; never calls an AI."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from coordination import relay


class FaultRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = relay.empty_state()
        self.state['tasks']['SAM/FAULT'] = relay.new_task('SAM','FAULT','a'*40,
                                                       ['SAM/tests/'],'Run isolated recovery')

    def test_process_exit_preserves_last_checkpoint_and_queue(self):
        checkpoint = self.root / 'checkpoint.json'
        relay.atomic_checkpoint(checkpoint, self.state)
        code = "from pathlib import Path; import os; p=Path(__import__('sys').argv[1]); (p.parent/'checkpoint.json.interrupted').write_text('{'); os._exit(17)"
        run = subprocess.run([sys.executable,'-c',code,str(checkpoint)], capture_output=True)
        self.assertEqual(run.returncode,17)
        self.assertEqual(relay.read_checkpoint(checkpoint), self.state)
        # Cold-reader process needs only files and ordinary Python, no transcript/model.
        cold = subprocess.run([sys.executable,'-c',
            "from coordination.relay import read_checkpoint,validate_state; import sys; s=validate_state(read_checkpoint(sys.argv[1])); print(s['tasks']['SAM/FAULT']['next_action'])",
            str(checkpoint)], capture_output=True, text=True)
        self.assertEqual(cold.returncode,0,cold.stderr)
        self.assertIn('isolated recovery',cold.stdout)

    def test_quota_unavailable_cold_recovery_uses_no_model(self):
        event = dict(project='SAM',task_id='FAULT',head_sha='a'*40,event_type='claim',
                     actor='codex',expected_version=0,lease_seconds=60,now=1000,
                     fencing_token=None,data={})
        state, receipt = relay.apply_event(self.state,event)
        event.update(event_type='quota_pause',expected_version=1,fencing_token=receipt['fencing_token'])
        state,_ = relay.apply_event(state,event)
        p = self.root/'state.json'
        relay.atomic_checkpoint(p,state)
        loaded = relay.read_checkpoint(p)
        event.update(event_type='claim',expected_version=2,actor='chatgpt',fencing_token=None,now=1001)
        taken,_ = relay.apply_event(loaded,event)
        self.assertEqual(taken['tasks']['SAM/FAULT']['owner'],'chatgpt')
        self.assertEqual(taken['tasks']['SAM/FAULT']['previous_owner'],'codex')

    def test_retries_403_rate_limit_429_5xx_and_network(self):
        for status, limited in [(0,False),(403,True),(429,False),(503,False)]:
            with self.subTest(status=status):
                q=relay.Outbox(self.root/str(status))
                event=dict(project='SAM',task_id='FAULT',head_sha='a'*40,event_type='claim',
                           actor='codex',expected_version=0,lease_seconds=60,now=1000,
                           fencing_token=None,data={})
                q.enqueue(event)
                def failed(e):
                    raise relay.RemoteError(status,retry_after=10,rate_limited=limited)
                self.assertEqual(q.replay(failed,now=0)['pending'],1)
                self.assertEqual(q.replay(lambda e: {},now=9)['attempted'],0)
                self.assertEqual(q.replay(lambda e: {'sha':'b'*40},now=10)['pending'],0)

    def test_windows_aliases_and_stale_recovered_evidence_denied(self):
        for value in ['src/config.py.','src/config.py ','src/NUL.txt','src/COM1','src/*']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                relay.safe_path(value)
        task = self.state['tasks']['SAM/FAULT']
        task.update(status='reviewed',owner='codex',lease_until=2000,fencing_token=1,
                    evidence=[dict(command='python test',exit_code=0,passed=1,failed=0,
                              head_sha='b'*40,artifact='SAM/evidence.json')],
                    reviews=[dict(reviewer='codex',head_sha='b'*40,artifact='../escape')])
        with self.assertRaises(ValueError):
            relay.validate_state(self.state)

    def test_local_version_retention_and_failed_replace(self):
        p=self.root/'state.json'
        relay.atomic_checkpoint(p,self.state)
        first=p.read_bytes()
        changed=json.loads(json.dumps(self.state))
        changed['revision']=1
        relay.atomic_checkpoint(p,changed)
        versions=list((self.root/'.versions'/'state.json').glob('*.json'))
        self.assertTrue(any(x.read_bytes()==first for x in versions))


if __name__ == '__main__':
    unittest.main()
