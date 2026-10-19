import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from coordination import relay
from coordination.relay_git import GitStateStore


class ReturnSyncTests(unittest.TestCase):
    def test_repository_digits_do_not_turn_network_failure_into_http403(self):
        store=object.__new__(GitStateStore)
        error=b"fatal: unable to access 'https://github.com/lu403369069lu-prog/WoolRadar.git/': Failed to connect to github.com port 443 via 127.0.0.1: Could not connect to server"
        with self.assertRaises(relay.RemoteError) as raised:
            store._transport_failure(subprocess.CompletedProcess([],1,b'',error))
        self.assertEqual(raised.exception.status,0)
        for status in (403,429,500,502,503):
            with self.subTest(status=status),self.assertRaises(relay.RemoteError) as raised:
                store._transport_failure(subprocess.CompletedProcess([],1,b'',
                    ('fatal: The requested URL returned error: '+str(status)).encode()))
            self.assertEqual(raised.exception.status,status)

    def test_reject_business_git_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            business=root/'business'
            subprocess.run(['git','init',str(business)],check=True,capture_output=True)
            with self.assertRaisesRegex(ValueError,'DEDICATED_BARE'):
                GitStateStore(business/'.git',str(business))
            self.assertFalse((business/'.git'/'FETCH_HEAD').exists())

    def test_domain_conflict_is_persisted_and_stops_successors(self):
        with tempfile.TemporaryDirectory() as temp:
            queue=relay.Outbox(Path(temp))
            event=dict(project='WoolRadar',task_id='RETURN',head_sha='a'*40,event_type='claim',
                actor='codex',expected_version=0,lease_seconds=60,now=100,fencing_token=None,data={})
            queue.enqueue(event)
            queue.enqueue(dict(event,event_type='start',expected_version=1))
            def reject(_): raise ValueError('TASK_VERSION_CONFLICT')
            result=queue.replay(reject,now=100)
            self.assertEqual(result['blocked'],'conflict')
            self.assertEqual(queue.replay(lambda _:self.fail('successor executed'),now=200)['attempted'],0)
            entries=[relay.read_checkpoint(p) for p in Path(temp).glob('*.json')]
            first=min(entries,key=lambda x:x['sequence'])
            self.assertEqual(first['attempts'],1)
            self.assertEqual(first['last_error'],'TASK_VERSION_CONFLICT')

    def test_auth_failure_is_terminal_without_retry_loop(self):
        with tempfile.TemporaryDirectory() as temp:
            queue=relay.Outbox(Path(temp))
            event=dict(project='WoolRadar',task_id='AUTH',head_sha='a'*40,event_type='claim',
                actor='codex',expected_version=0,lease_seconds=60,now=100,fencing_token=None,data={})
            queue.enqueue(event)
            def reject(_): raise relay.RemoteError(401)
            self.assertEqual(queue.replay(reject,now=100)['blocked'],'BLOCKED_AUTH')
            self.assertEqual(queue.replay(reject,now=10000)['attempted'],0)

    def test_observe_ref_change_is_persistent_and_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            remote=root/'remote.git'
            subprocess.run(['git','init','--bare',str(remote)],check=True,capture_output=True)
            store=GitStateStore(root/'store',str(remote))
            ref='refs/heads/chatgpt/review'
            cache=root/'observed.cache'
            first=subprocess.CompletedProcess([],0,('a'*40+'\t'+ref+'\n').encode(),b'')
            second=subprocess.CompletedProcess([],0,('b'*40+'\t'+ref+'\n').encode(),b'')
            with patch.object(store,'git',return_value=first):
                self.assertEqual(len(store.observe([ref],cache)['changes']),1)
                self.assertEqual(store.observe([ref],cache)['changes'],[])
            with patch.object(store,'git',return_value=second):
                change=store.observe([ref],cache)['changes'][0]
                self.assertEqual((change['before'],change['after']),('a'*40,'b'*40))
            with self.assertRaises(ValueError): store.observe(['--upload-pack=bad'],cache)

    def test_expired_output_lease_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            remote=root/'remote.git'
            subprocess.run(['git','init','--bare',str(remote)],check=True,capture_output=True)
            store=GitStateStore(root/'store',str(remote))
            state=relay.empty_state()
            state['tasks']['SAM/CLOCK']=relay.new_task('SAM','CLOCK','a'*40,['SAM/'],'Clock regression')
            parent=store.initialize(state)
            event=dict(project='SAM',task_id='CLOCK',head_sha='a'*40,event_type='claim',actor='codex',
                expected_version=0,lease_seconds=60,now=1000,fencing_token=None,data={})
            stale,_=relay.apply_event(state,event)
            with patch('coordination.relay_git.time.time',return_value=2000):
                with self.assertRaisesRegex(ValueError,'EXPIRED_OUTPUT_LEASE'):
                    store.publish(parent,stale,event=event)
            self.assertEqual(store.read()[0],parent)

    def test_http401_is_blocked_auth_and_ref_race_is_conflict(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            remote=root/'remote.git'
            subprocess.run(['git','init','--bare',str(remote)],check=True,capture_output=True)
            store=GitStateStore(root/'store',str(remote))
            with self.assertRaises(relay.RemoteError) as raised:
                store._transport_failure(subprocess.CompletedProcess([],1,b'',b'fatal: HTTP 401 Unauthorized'))
            self.assertEqual(raised.exception.status,401)
            with patch.object(store,'git',return_value=subprocess.CompletedProcess([],1,b'',
                 b'remote: error: cannot lock ref: is at abc but expected def\n[remote rejected] failed to update ref')):
                with self.assertRaisesRegex(ValueError,'REMOTE_CONFLICT'):
                    store._push('a'*40)


if __name__=='__main__': unittest.main()
