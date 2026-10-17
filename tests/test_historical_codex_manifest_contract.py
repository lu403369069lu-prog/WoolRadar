"""Offline 50-job contract guard: synthetic manifest only, no subprocess/production."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'coordination' / 'HISTORICAL_CODEX_BATCH_RUNNER_20261017.py'
SPEC = importlib.util.spec_from_file_location('historical_batch_runner', SCRIPT)
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)

EXPECTED = RUNNER.EXPECTED
REPOS = {'W':'lu403369069lu-prog/WoolRadar',
         'S':'lu403369069lu-prog/YinQieJi',
         'C':'lu403369069lu-prog/WoolRadar'}
PROJECTS = {'W':'WoolRadar','S':'YinQieJi-SAM','C':'WoolRadar-Coord'}


def sample():
    refs = {k: {'sha': EXPECTED[p], 'repo': REPOS[k]}
            for k,p in [('W','wool'),('S','sam'),('C','coord')]}
    jobs = []
    for i,k in enumerate(['W'] * 20 + ['S'] * 24 + ['C'] * 6):
        ready = i < 42
        jobs.append({
            'family_id': 'SYN-%02d' % i,
            'project': PROJECTS[k],
            'required_head_sha': refs[k]['sha'],
            'repo': refs[k]['repo'],
            'disposition': 'READY_FOR_LOCAL_CODEX' if ready else 'EXTERNAL_OR_POLICY_GATED',
            'run_command': 'python -m unittest' if ready else None,
            'verified_test_path': 'tests/test_synthetic.py' if ready else None,
            'verified_test_blob': 'a' * 40 if ready else None,
        })
    return {'total_families': 50, 'jobs': jobs, 'immutable_refs': refs,
            'ready_for_local_codex': 42, 'external_or_policy_gated': 8}


class HistoricalCodexManifestGuard(unittest.TestCase):
    def check(self, doc, expected_error=None, project='sam'):
        with tempfile.TemporaryDirectory(prefix='hist-manifest-') as directory:
            manifest = Path(directory) / 'jobs.json'
            if doc is not None:
                manifest.write_text(json.dumps(doc), encoding='utf-8')
            if expected_error:
                with self.assertRaisesRegex(RuntimeError, expected_error):
                    RUNNER.validate_handoff_manifest(manifest, project, EXPECTED[project])
            else:
                self.assertEqual(RUNNER.validate_handoff_manifest(
                    manifest, project, EXPECTED[project])['families'], 50)

    def test_valid_manifest(self): self.check(sample())
    def test_all_three_projects(self):
        for project in EXPECTED:
            with self.subTest(project=project): self.check(sample(), project=project)
    def test_missing_manifest(self): self.check(None, 'Missing adjacent')
    def test_short_manifest(self):
        m=sample(); m['jobs'].pop(); self.check(m, 'family count')
    def test_wrong_manifest_head(self):
        m=sample(); m['immutable_refs']['S']['sha']='f'*40; self.check(m, 'source SHA mismatch')
    def test_wrong_job_head(self):
        m=sample(); m['jobs'][25]['required_head_sha']='e'*40; self.check(m, 'not pinned')
    def test_duplicate_family(self):
        m=sample(); m['jobs'][25]['family_id']=m['jobs'][0]['family_id']; self.check(m, 'repeated')
    def test_missing_runnable_command(self):
        m=sample(); m['jobs'][2]['run_command']=None; self.check(m, 'missing required')
    def test_wrong_repo(self):
        m=sample(); m['jobs'][21]['repo']='other/repository'; self.check(m, 'not pinned')
    def test_unknown_disposition(self):
        m=sample(); m['jobs'][48]['disposition']='PASS'; self.check(m, 'Unknown')
    def test_wrong_ready_count(self):
        m=sample(); m['ready_for_local_codex']=41; self.check(m, '42/8')
    def test_unregistered_project(self):
        m=sample(); m['jobs'][1]['project']='SAM'; self.check(m, 'not pinned')


if __name__=='__main__':
    unittest.main()
