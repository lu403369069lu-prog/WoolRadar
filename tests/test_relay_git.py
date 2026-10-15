import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from coordination import relay

try:
    from coordination.relay_git import GitStateStore
except ImportError:
    GitStateStore = None


class GitConcurrencyTests(unittest.TestCase):
    def test_cli_persist_queue_and_sync_without_model(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            remote=root/'remote.git'
            subprocess.run(['git','init','--bare',str(remote)],check=True,capture_output=True)
            initial=GitStateStore(root/'initial',str(remote))
            state=relay.empty_state()
            state['tasks']['SAM/CLI']=relay.new_task('SAM','CLI','a'*40,['SAM/tests/'],'CLI recovery')
            initial.initialize(state)
            e=dict(project='SAM',task_id='CLI',head_sha='a'*40,event_type='claim',actor='codex',
                   expected_version=0,lease_seconds=60,now=int(time.time()),fencing_token=None,data={})
            path=root/'event.json'
            path.write_text(json.dumps(e),encoding='utf-8')
            cmd=[sys.executable,'-m','coordination.relay_git','--workspace',str(root/'cli'),
                 '--remote',str(remote)]
            queued=subprocess.run(cmd+['enqueue','--event',str(path),'--outbox',str(root/'queue')],
                                  capture_output=True,text=True)
            self.assertEqual(queued.returncode,0,queued.stderr)
            synced=subprocess.run(cmd+['sync','--outbox',str(root/'queue')],capture_output=True,text=True)
            self.assertEqual(synced.returncode,0,synced.stderr)
            first=json.loads(synced.stdout)['last_confirmed_sha']
            replayed=subprocess.run(cmd+['sync','--outbox',str(root/'queue')],capture_output=True,text=True)
            self.assertEqual(replayed.returncode,0,replayed.stderr)
            self.assertEqual(json.loads(replayed.stdout)['attempted'],0)
            self.assertEqual(json.loads(replayed.stdout)['last_confirmed_sha'],first)
            receipt=relay.read_checkpoint(root/'queue'/'last-sync.json.cache')
            self.assertEqual(receipt['sha'],first)

    def test_synthetic_closed_loop_with_new_sha_and_local_conflict(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote = root / 'remote.git'
            subprocess.run(['git','init','--bare',str(remote)],check=True,capture_output=True)
            a = GitStateStore(root/'codex',str(remote))
            b = GitStateStore(root/'remote-python',str(remote))
            state=relay.empty_state()
            state['tasks']['WoolRadar/LOOP']=relay.new_task('WoolRadar','LOOP','a'*40,
                                                        ['coordination/reviews/'],'Synthetic loop')
            a.initialize(state)
            def send(store, kind, actor='codex', data=None):
                _, current=store.read()
                task=current['tasks']['WoolRadar/LOOP']
                e=dict(project='WoolRadar',task_id='LOOP',head_sha=task['head_sha'],
                       event_type=kind,actor=actor,expected_version=task['version'],
                       lease_seconds=300,now=int(time.time()),
                       fencing_token=task['fencing_token'],data=data or {})
                return store.deliver(e)
            send(a,'claim')
            paused=send(a,'quota_pause')['sha']
            send(b,'claim',actor='remote-python')
            send(b,'start',actor='remote-python')
            changed=send(b,'checkpoint',actor='remote-python',data={
                'new_head_sha':'b'*40,'changed_files':['coordination/reviews/synthetic.json'],
                'change_summary':'Synthetic artifact identity advance'})['sha']
            current, observed=a.read()
            self.assertNotEqual(current,paused)
            self.assertEqual(current,changed)
            self.assertEqual(observed['tasks']['WoolRadar/LOOP']['head_sha'],'b'*40)
            # A dirty/local result at the old version cannot overwrite remote progress.
            stale=dict(project='WoolRadar',task_id='LOOP',head_sha='a'*40,event_type='start',
                       actor='codex',expected_version=1,lease_seconds=60,now=int(time.time()),
                       fencing_token=1,data={})
            with self.assertRaisesRegex(ValueError,'VERSION|STALE'):
                a.deliver(stale)
            send(b,'evidence',actor='remote-python',data={'evidence':dict(
                command='synthetic regression',exit_code=0,passed=1,failed=0,
                head_sha='b'*40,artifact='coordination/reviews/synthetic.json')})
            send(b,'request_review',actor='remote-python')
            send(a,'review',actor='codex',data={'review':dict(head_sha='b'*40,
                 artifact='coordination/reviews/independent.json')})
            send(b,'done',actor='remote-python')
            self.assertEqual(a.read()[1]['tasks']['WoolRadar/LOOP']['status'],'done')

    def test_two_real_writers_and_crash_replay(self):
        self.assertIsNotNone(GitStateStore, 'Git state transport required')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote = root / 'remote.git'
            subprocess.run(['git', 'init', '--bare', str(remote)], check=True, capture_output=True)
            first = GitStateStore(root / 'one', str(remote))
            second = GitStateStore(root / 'two', str(remote))
            state = relay.empty_state()
            state['tasks']['WoolRadar/R-1'] = relay.new_task('WoolRadar', 'R-1', 'a'*40,
                                                          ['coordination/'], 'Review checkpoint')
            sha = first.initialize(state)
            self.assertEqual(second.read()[0], sha)
            event = dict(project='WoolRadar', task_id='R-1', head_sha='a'*40,
                         event_type='claim', actor='codex', expected_version=0,
                         lease_seconds=60, now=int(time.time()), fencing_token=None, data={})
            a, _ = relay.apply_event(state, event)
            b, _ = relay.apply_event(state, dict(event, actor='chatgpt'))
            accepted = first.publish(sha, a, event=event)
            with self.assertRaisesRegex(ValueError, 'CONFLICT'):
                second.publish(sha, b, event=dict(event,actor='chatgpt'))
            current, actual = second.read()
            self.assertEqual(current, accepted)
            self.assertEqual(actual['tasks']['WoolRadar/R-1']['owner'], 'codex')
            # Lost acknowledgement: resend after a successful commit, without a new commit.
            self.assertEqual(second.deliver(event)['result'], 'duplicate_noop')
            self.assertEqual(second.read()[0], accepted)
            # Checksum tampering is rejected before a state can be used.
            with self.assertRaises(ValueError):
                first.publish(accepted, dict(a, schema_version=5))
            forged = json.loads(json.dumps(a))
            forged['revision'] += 1
            forged['tasks'] = {}
            with self.assertRaisesRegex(ValueError, 'EVENT_REQUIRED|INVALID_TRANSITION_RESULT'):
                first.publish(accepted, forged)

    def test_publish_rejects_precomputed_progress_after_lease_expiry(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            remote=root/'remote.git'
            subprocess.run(['git','init','--bare',str(remote)],check=True,capture_output=True)
            store=GitStateStore(root/'store',str(remote))
            state=relay.empty_state()
            state['tasks']['SAM/EXPIRED']=relay.new_task('SAM','EXPIRED','a'*40,['SAM/'],'Expiry test')
            event=dict(project='SAM',task_id='EXPIRED',head_sha='a'*40,event_type='claim',
                       actor='codex',expected_version=0,lease_seconds=60,now=10,fencing_token=None,data={})
            state,_=relay.apply_event(state,event)
            # Historical fixture is initialized only in a synthesized local bare repository.
            state['revision']=0
            parent=store.initialize(state)
            event.update(event_type='start',expected_version=1,now=11,fencing_token=1)
            stale,_=relay.apply_event(state,event)
            with self.assertRaisesRegex(ValueError,'EXPIRED_OWNER'):
                store.publish(parent,stale,event=event)
            self.assertEqual(store.read()[0],parent)


if __name__ == '__main__':
    unittest.main()
