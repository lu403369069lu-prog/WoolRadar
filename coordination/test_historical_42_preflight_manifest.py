"""Official immutable manifest must be checked BEFORE any work or test launch."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('frozen_manifest_preflight_runner', ROOT/'HISTORICAL_CODEX_42_JOB_EXECUTOR_20261017.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

class ImmutableManifestFirst(unittest.TestCase):
    def test_actual_guard_rejects_tampered_manifest_before_preflight_or_subprocess(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'jobs.json'
            path.write_text(json.dumps({'jobs': [], 'total_families': 50}))
            with patch.object(runner,'MANIFEST',path), \
                 patch.object(runner.contract,'EXPECTED',{'wool':runner.formal_guard.HEADS['wool']},create=True), \
                 patch.object(runner.contract,'validate_handoff_manifest',create=True) as basic, \
                 patch.object(runner.contract,'preflight',create=True) as preflight, \
                 patch.object(runner,'plan_jobs') as plan, \
                 patch.object(runner,'run_commands') as execute, \
                 patch('sys.argv',['runner','--project','wool','--repo',temp,
                                   '--expected-head',runner.formal_guard.HEADS['wool'],'--run']):
                with self.assertRaisesRegex(ValueError,'WRONG_IMMUTABLE_MANIFEST_BLOB'):
                    runner.main()
                basic.assert_not_called()
                preflight.assert_not_called()
                plan.assert_not_called()
                execute.assert_not_called()

    def test_dry_run_uses_exact_document_returned_by_formal_guard_not_reloaded_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'jobs.json'
            # The contents themselves are intentionally untrusted: the guard
            # returns the immutable document in this positive mock.
            path.write_text('"injected contents must not be used"')
            vetted={'jobs':[{'project':'WoolRadar','disposition':'READY_FOR_LOCAL_CODEX'}]}
            with patch.object(runner,'MANIFEST',path), \
                 patch.object(runner.contract,'EXPECTED',{'wool':runner.formal_guard.HEADS['wool']},create=True), \
                 patch.object(runner.formal_guard,'load_verified_manifest',return_value=vetted) as check, \
                 patch.object(runner.contract,'validate_handoff_manifest',create=True), \
                 patch.object(runner.contract,'preflight',return_value=runner.formal_guard.HEADS['wool'],create=True), \
                 patch.object(runner,'plan_jobs',return_value=([],[])) as plan, \
                 patch('sys.argv',['runner','--project','wool','--repo',temp,
                                   '--expected-head',runner.formal_guard.HEADS['wool']]):
                self.assertEqual(runner.main(),0)
                check.assert_called_once_with(path)
                self.assertIs(plan.call_args.args[2],vetted)

if __name__=='__main__':unittest.main()
