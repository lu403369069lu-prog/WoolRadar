"""Real subprocess crash/replay regressions; synthetic state, no remote writes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import test_worker as fixtures

HERE = Path(__file__).resolve().parent
worker = fixtures.worker


class CheckpointRecoveryTests(unittest.TestCase):
    def test_crash_after_engine_commit_repairs_history_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = '''import os,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import test_worker as fixtures
w=fixtures.worker
original=w.save
def interrupted(path,obj):
 original(path,obj)
 if Path(path).name=='engine.json' and obj.get('processed_run_keys'):
  os._exit(17)
w.save=interrupted
f=fixtures.RelaySafetyTests()
q=f.queue()
f.run_persist(Path(sys.argv[2]),q,f.receipt(q))
'''
            p = subprocess.run([sys.executable, '-c', code, str(HERE), tmp],
                               capture_output=True, timeout=30)
            self.assertEqual(p.returncode, 17, p.stderr.decode(errors='replace'))
            f = fixtures.RelaySafetyTests()
            q = f.queue()
            for _ in range(2):
                state = f.run_persist(Path(tmp), q, f.receipt(q))
                self.assertEqual(state['revision'], 1)
            history = Path(tmp) / 'history.jsonl'
            self.assertTrue(history.exists(), 'engine committed but history was permanently lost')
            self.assertEqual(len(history.read_text(encoding='utf-8').splitlines()), 1)

    def test_interrupted_json_save_preserves_last_valid_engine(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'engine.json'
            worker.save(path, {'revision': 1})
            original = path.read_bytes()
            with patch('os.replace', side_effect=OSError('synthetic disk failure')):
                with self.assertRaises(OSError):
                    worker.save(path, {'revision': 2})
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(json.loads(path.read_bytes())['revision'], 1)

    def test_same_run_key_different_content_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=fixtures.RelaySafetyTests();q=f.queue();root=Path(tmp)
            f.run_persist(root,q,f.receipt(q))
            altered=f.receipt(q);altered['source_commit']='b'*40
            with self.assertRaisesRegex(ValueError,'REPLAY_CONTENT_CONFLICT'):
                f.run_persist(root,q,altered,integration_sha='b'*40)

    def test_concurrent_same_cursor_has_one_winner(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            f = fixtures.RelaySafetyTests()
            q = f.queue()
            worker.save(root / 'engine.json', f.initial(q['repo']))
            code = '''import sys,os
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,sys.argv[1])
import test_worker as fixtures
os.environ['GITHUB_RUN_ID']=sys.argv[3].split('/')[0]
os.environ['GITHUB_RUN_ATTEMPT']='1'
try:
 fixtures.worker.persist(SimpleNamespace(state=sys.argv[2],receipt=sys.argv[4],repo=fixtures.RelaySafetyTests().queue()['repo']))
except ValueError as e:
 if 'STALE_RECEIPT' not in str(e): raise
 sys.exit(3)
'''
            # Separate immutable receipt paths avoid fixture-file races.
            processes=[]
            for key in ['901001/1', '901002/1']:
                d=root/key.split('/')[0];d.mkdir()
                with patch.object(worker,'persist'):
                    f.run_persist(d,q,f.receipt(q,run_key=key))
                processes.append(subprocess.Popen([sys.executable,'-c',code,str(HERE),str(root),key,str(d/'receipt.json')],stdout=subprocess.PIPE,stderr=subprocess.PIPE))
            results=[(p.wait(timeout=30),p.communicate()) for p in processes]
            self.assertEqual(sorted(r[0] for r in results),[0,3],repr(results))
            self.assertEqual(worker.load(root/'engine.json')['revision'],1)
            self.assertEqual(len((root/'history.jsonl').read_text(encoding='utf-8').splitlines()),1)


if __name__ == '__main__':
    unittest.main()
