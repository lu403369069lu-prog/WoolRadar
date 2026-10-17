"""Real cross-module receipt integration against the existing official guard.

Only synthetic ephemeral tests are executed; no historical source or production.
"""
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent

def load(name, filename):
    spec=importlib.util.spec_from_file_location(name,HERE/filename)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

runner=load('actual_batch_runner_bridge','HISTORICAL_CODEX_42_JOB_EXECUTOR_20261017.py')
guard=load('actual_batch_guard_bridge','HISTORICAL_CODEX_42_RECEIPT_GUARD_20261017.py')

class FormalGuardIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='synthetic-guard-bridge-')
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)

    def python_case(self):
        (self.root/'tests').mkdir(exist_ok=True)
        (self.root/'tests/test_synthetic_ok.py').write_text(
            'import unittest\nclass T(unittest.TestCase):\n def test_safe(self): self.assertTrue(True)\n')
        command='python -B -m unittest discover -s tests -p test_synthetic_ok.py -v'
        key=hashlib.sha256(command.encode()).hexdigest()
        item={'argv':[sys.executable,'-B','-m','unittest','discover','-s','tests','-p',
                      'test_synthetic_ok.py','-v'],
              'cwd':self.root,'cwd_contract':'.','command':command,'key_sha256':key}
        mapping=[{'family_id':'WR-SYNTHETIC','source_blob':'synthetic','command_key':key}]
        doc={'jobs':[{'project':'WoolRadar','disposition':'READY_FOR_LOCAL_CODEX',
                      'family_id':'WR-SYNTHETIC','run_command':command,'local_cwd':'.'}]}
        return item,mapping,doc

    def test_real_python_unittest_receipt_passes_real_family_guard(self):
        item,mapping,doc=self.python_case()
        rc,legacy,folder=runner.run_commands([item],mapping,guard.HEADS['wool'],'wool')
        self.addCleanup(lambda:shutil.rmtree(folder,ignore_errors=True))
        self.assertEqual(rc,0)
        formal=json.loads((folder/'receipt-guard-v1.json').read_text('utf8'))
        decision=guard.review(formal,doc,folder)
        self.assertTrue(decision['local_full_family_receipt_accepted'],decision['errors'])
        self.assertEqual(formal['tested_families'],1)
        self.assertEqual(formal['unique_commands'],1)
        self.assertEqual(formal['results'][0]['counts']['passed'],1)
        self.assertEqual(formal['source'],'disposable-local-codex')

    def test_guard_denies_modified_raw_log_even_if_legacy_receipt_unchanged(self):
        item,mapping,doc=self.python_case()
        rc,legacy,folder=runner.run_commands([item],mapping,guard.HEADS['wool'],'wool')
        self.addCleanup(lambda:shutil.rmtree(folder,ignore_errors=True))
        formal=json.loads((folder/'receipt-guard-v1.json').read_text('utf8'))
        raw=folder/formal['results'][0]['local_log']
        raw.write_bytes(raw.read_bytes()+b'\nFAKE EXTRA\n')
        outcome=guard.review(formal,doc,folder)
        self.assertFalse(outcome['local_full_family_receipt_accepted'])
        self.assertIn('LOG_SHA256_MISMATCH',outcome['errors'])

    def test_guard_denies_missing_family_or_changed_head(self):
        item,mapping,doc=self.python_case()
        rc,legacy,folder=runner.run_commands([item],mapping,guard.HEADS['wool'],'wool')
        self.addCleanup(lambda:shutil.rmtree(folder,ignore_errors=True))
        formal=json.loads((folder/'receipt-guard-v1.json').read_text('utf8'))
        formal['results'][0]['family_ids']=['WR-FAKE']
        formal['repo_sha']='0'*40
        outcome=guard.review(formal,doc,folder)
        self.assertFalse(outcome['local_full_family_receipt_accepted'])
        self.assertIn('HEAD_MISMATCH',outcome['errors'])
        self.assertIn('INCOMPLETE_FAMILY_COVERAGE',outcome['errors'])

    def test_non_utf8_test_output_is_preserved_but_not_certified(self):
        raw=b'\xff\xfe\nRan 1 test in 0.001s\nOK\n'
        key=hashlib.sha256(b'fake-test-command').hexdigest()
        item={'argv':[sys.executable,'-c',
                      'import sys;sys.stdout.buffer.write('+repr(raw)+')'],
              'cwd':self.root,'cwd_contract':'.','command':'fake-test-command',
              'key_sha256':key}
        mapping=[{'family_id':'WR-SYNTHETIC','source_blob':'synthetic','command_key':key}]
        rc,legacy,folder=runner.run_commands([item],mapping,guard.HEADS['wool'],'wool')
        self.addCleanup(lambda:shutil.rmtree(folder,ignore_errors=True))
        self.assertNotEqual(rc,0)
        self.assertEqual((folder/(key+'.log')).read_bytes(),raw)
        formal=json.loads((folder/'receipt-guard-v1.json').read_text('utf8'))
        self.assertNotEqual(formal['results'][0]['exit_code'],0)

    def test_real_node_tap_receipt_passes_real_guard_if_node_installed(self):
        import shutil as commands
        if commands.which('node') is None:
            self.skipTest('Node is required for SAM verification')
        project=self.root/'SAM/snapshot'
        project.mkdir(parents=True)
        (project/'synthetic.test.mjs').write_text(
            "import test from 'node:test';import assert from 'node:assert/strict';"
            "test('safe',()=>assert.ok(true));\n")
        command='node --test synthetic.test.mjs'
        key=hashlib.sha256(command.encode()).hexdigest()
        item={'argv':['node','--test','synthetic.test.mjs'],'cwd':project,
              'cwd_contract':'SAM/snapshot','command':command,'key_sha256':key}
        mapping=[{'family_id':'SAM-SYNTHETIC','source_blob':'synthetic','command_key':key}]
        doc={'jobs':[{'project':'YinQieJi-SAM','disposition':'READY_FOR_LOCAL_CODEX',
                      'family_id':'SAM-SYNTHETIC','run_command':command,
                      'local_cwd':'SAM/snapshot'}]}
        rc,legacy,folder=runner.run_commands([item],mapping,guard.HEADS['sam'],'sam')
        self.addCleanup(lambda:shutil.rmtree(folder,ignore_errors=True))
        self.assertEqual(rc,0,legacy)
        formal=json.loads((folder/'receipt-guard-v1.json').read_text('utf8'))
        result=guard.review(formal,doc,folder)
        self.assertTrue(result['local_full_family_receipt_accepted'],result['errors'])
        self.assertTrue(formal['runtime']['node'].startswith('v'))

    def test_zero_python_tests_cannot_pass_official_guard(self):
        item,mapping,doc=self.python_case()
        (self.root/'tests/test_synthetic_ok.py').unlink()
        rc,legacy,folder=runner.run_commands([item],mapping,guard.HEADS['wool'],'wool')
        self.addCleanup(lambda:shutil.rmtree(folder,ignore_errors=True))
        self.assertNotEqual(rc,0)
        formal=json.loads((folder/'receipt-guard-v1.json').read_text('utf8'))
        decision=guard.review(formal,doc,folder)
        self.assertFalse(decision['local_full_family_receipt_accepted'])
        self.assertIn('NONZERO_EXIT',decision['errors'])

    def test_one_skipped_python_test_blocks_technical_acceptance(self):
        item,mapping,doc=self.python_case()
        (self.root/'tests/test_synthetic_ok.py').write_text(
            'import unittest\nclass T(unittest.TestCase):\n'
            ' def test_good(self): self.assertTrue(True)\n'
            ' @unittest.skip("synthetic")\n def test_skip(self): pass\n')
        rc,legacy,folder=runner.run_commands([item],mapping,guard.HEADS['wool'],'wool')
        self.addCleanup(lambda:shutil.rmtree(folder,ignore_errors=True))
        self.assertNotEqual(rc,0)
        formal=json.loads((folder/'receipt-guard-v1.json').read_text('utf8'))
        decision=guard.review(formal,doc,folder)
        self.assertFalse(decision['local_full_family_receipt_accepted'])
        self.assertIn('NO_COMPLETE_GREEN_TESTS',decision['errors'])

    def test_multiple_families_share_one_actual_command_with_grouped_guard_receipt(self):
        item,mapping,doc=self.python_case()
        mapping.append({'family_id':'WR-SECOND','source_blob':'synthetic',
                        'command_key':item['key_sha256']})
        doc['jobs'].append({**doc['jobs'][0],'family_id':'WR-SECOND'})
        rc,legacy,folder=runner.run_commands([item],mapping,guard.HEADS['wool'],'wool')
        self.addCleanup(lambda:shutil.rmtree(folder,ignore_errors=True))
        self.assertEqual(rc,0)
        formal=json.loads((folder/'receipt-guard-v1.json').read_text('utf8'))
        self.assertEqual(formal['unique_commands'],1)
        self.assertEqual(formal['tested_families'],2)
        decision=guard.review(formal,doc,folder)
        self.assertTrue(decision['local_full_family_receipt_accepted'],decision['errors'])

if __name__=='__main__': unittest.main()
