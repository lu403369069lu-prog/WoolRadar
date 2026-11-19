#!/usr/bin/env python3
"""Isolated reproduction of environment inherited by pinned integration_gate.py.

No production checkout, network, token, or long-running process is touched.
"""

import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest import mock


ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT / "integration_gate_original.py"
CANDIDATE = ROOT / "integration_gate_candidate.py"
RESULT = ROOT / "gate-pollution-evidence.json"

# Runner essentials. Intentionally exclude dynamic code/config injection variables
# such as PYTHONPATH, PYTHONHOME, NODE_OPTIONS, NODE_PATH and GIT_CONFIG_*.
RUNNER_ENV = frozenset({
    "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP",
    "TMPDIR", "HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA",
    "HOMEDRIVE", "HOMEPATH", "LANG", "LC_ALL", "LC_CTYPE", "TZ",
})


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def candidate_text(original):
    target = '    env = dict(os.environ)\n'
    assert original.count(target) == 1, 'source drift: unexpected env assignment'
    replacement = (
        '    # Explicit runner environment; inherited startup hooks/config are untrusted.\n'
        '    allowed = {' + ', '.join(repr(x) for x in sorted(RUNNER_ENV)) + '}\n'
        '    env = {k: v for k, v in os.environ.items() if k.upper() in allowed}\n'
    )
    fixed = original.replace(target, replacement)
    # Windows CreateProcess cannot directly resolve npm.CMD by its bare stem.
    return fix_windows_npm(fixed)


def fix_windows_npm(original):
    target = '        cmd = ["npm", "test"]\n'
    assert original.count(target) == 1
    return original.replace(target,
                            '        cmd = ["npm.cmd" if os.name == "nt" else "npm", "test"]\n')


def load_gate(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def invoke(gate, repo, source, dest, with_env=None, spy=False):
    args = SimpleNamespace(repo=repo, source=str(source), output=str(dest))
    changes = with_env or {}
    previous = {k: os.environ.get(k) for k in changes}
    try:
        for key, val in changes.items():
            os.environ[key] = val
        if spy:
            observed = {}

            def fake_child(cmd, **kwargs):
                env = kwargs['env']
                observed['unsafe_present'] = sorted(k for k in changes if k in env)
                observed['command'] = cmd
                # Only validate sanitization here. Fake child is not an acceptance test.
                return subprocess.CompletedProcess(cmd, 1, '', 'synthetic failure')

            with mock.patch.object(gate.subprocess, 'run', side_effect=fake_child), contextlib.redirect_stdout(io.StringIO()):
                gate.run(args)
            return {'unsafe_present': observed['unsafe_present'], 'command': observed['command']}
        with contextlib.redirect_stdout(io.StringIO()):
            gate.run(args)
        return json.loads(dest.read_text(encoding='utf-8'))
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def main():
    original = ORIGINAL.read_text(encoding='utf-8')
    CANDIDATE.write_text(candidate_text(original), encoding='utf-8', newline='\n')
    source_sha = subprocess.check_output(['git', 'hash-object', str(ORIGINAL)], text=True).strip()
    assert source_sha == 'dcb39f1aca78649e8383c40c9ed7a08a1546102e', source_sha
    PORTABLE = ROOT / 'integration_gate_portable_control.py'
    PORTABLE.write_text(fix_windows_npm(original), encoding='utf-8', newline='\n')
    org, hard = load_gate(ORIGINAL, 'gate_original'), load_gate(CANDIDATE, 'gate_candidate')
    portable = load_gate(PORTABLE, 'gate_portable_control')
    before_pythonpath = os.environ.pop('PYTHONPATH', None)
    try:
        with tempfile.TemporaryDirectory(prefix='r4-gate-', dir=ROOT) as temp:
            work = Path(temp)
            source = work / 'candidate'
            (source / 'tests').mkdir(parents=True)
            (source / 'tests' / 'test_truth.py').write_text(
                'import unittest\nclass Truth(unittest.TestCase):\n'
                '    def test_must_fail(self):\n        self.assertEqual(0, 1)\n', encoding='utf-8')
            malicious = work / 'external-startup'
            malicious.mkdir()
            (malicious / 'sitecustomize.py').write_text(
                'import os, sys\nsys.stdout.write("Ran 1 test in 0.000s\\n\\nOK\\n")\n'
                'sys.stdout.flush()\nos._exit(0)\n', encoding='utf-8')
            clean = invoke(org, 'WoolRadar', source, work / 'baseline.json')
            poisoned = invoke(org, 'WoolRadar', source, work / 'poisoned.json', {'PYTHONPATH': str(malicious)})
            fixed = invoke(hard, 'WoolRadar', source, work / 'hardened.json', {'PYTHONPATH': str(malicious)})
            # Both project codepaths are checked; npm invocation itself is not
            # simulated as a successful SAM business test.
            source_sam = work / 'candidate-sam'
            (source_sam / 'SAM' / 'snapshot').mkdir(parents=True)
            env_override = {'NODE_OPTIONS': '--require dummy-preload.cjs', 'NODE_PATH': str(malicious),
                            'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'core.hooksPath',
                            'GIT_CONFIG_VALUE_0': str(malicious), 'PYTHONPATH': str(malicious)}
            sam_before = invoke(org, 'YinQieJi', source_sam, work / 'sam-original.json', env_override, spy=True)
            sam_after = invoke(hard, 'YinQieJi', source_sam, work / 'sam-hardened.json', env_override, spy=True)
            sam_dir = source_sam / 'SAM' / 'snapshot'
            (sam_dir / 'package.json').write_text(
                '{"name":"r4-negative-only","version":"1.0.0","scripts":{"test":"node fail.cjs"}}',
                encoding='utf-8')
            (sam_dir / 'fail.cjs').write_text('process.stderr.write("intentional failure\\n");process.exit(1);', encoding='utf-8')
            (malicious / 'evil.cjs').write_text(
                'process.stdout.write("# tests 1\\n# pass 1\\n# fail 0\\n# skipped 0\\n# todo 0\\n# cancelled 0\\n");process.exit(0);',
                encoding='utf-8')
            baseline_sam_original = invoke(org, 'YinQieJi', source_sam, work / 'sam-original-run.json')
            baseline_sam = invoke(portable, 'YinQieJi', source_sam, work / 'sam-portable-baseline.json')
            poison_sam = invoke(portable, 'YinQieJi', source_sam, work / 'sam-portable-poison.json',
                                {'NODE_OPTIONS': '--require ' + str(malicious / 'evil.cjs')})
            fix_sam = invoke(hard, 'YinQieJi', source_sam, work / 'sam-hardened-run.json',
                             {'NODE_OPTIONS': '--require ' + str(malicious / 'evil.cjs')})
            checks = {
                'baseline_real_failure': clean['status'] == 'FAIL' and clean['exit_code'] != 0,
                'poisoned_false_pass': poisoned['status'] == 'PASS' and poisoned['exit_code'] == 0 and poisoned['total'] == 1,
                'candidate_real_failure': fixed['status'] == 'FAIL' and fixed['exit_code'] != 0,
                'original_sam_env_leaked': set(env_override).issubset(sam_before['unsafe_present']),
                'candidate_sam_env_stripped': sam_after['unsafe_present'] == [],
                'sam_original_windows_blocked_or_fails': baseline_sam_original['status'] in ('BLOCKED', 'FAIL'),
                'sam_portable_baseline_failed': baseline_sam['status'] == 'FAIL',
                'sam_portable_inherited_preload_false_pass': poison_sam['status'] == 'PASS' and poison_sam['exit_code'] == 0,
                'sam_candidate_restores_failure': fix_sam['status'] == 'FAIL',
            }
            report = {
                'kind': 'isolated_negative_reproduction', 'base_repo': 'lu403369069lu-prog/WoolRadar',
                'base_commit': 'e44589104585c4b2a93081d00a145263666f9264',
                'original_git_blob': source_sha, 'original_sha256': sha256(ORIGINAL),
                'candidate_sha256': sha256(CANDIDATE), 'python': sys.version,
                'tests': checks, 'all_expected': all(checks.values()),
                'actual_original_results': {'baseline': {'status': clean['status'], 'exit_code': clean['exit_code']},
                    'poisoned': {'status': poisoned['status'], 'exit_code': poisoned['exit_code']},
                    'candidate': {'status': fixed['status'], 'exit_code': fixed['exit_code']}},
                'sam_portability_control': 'Windows original bare npm returned BLOCKED (WinError 2); portable control changes only npm to npm.cmd; real npm/Node synthetic test',
                'sam_actual_results': {n: {'status': v['status'], 'exit_code': v.get('exit_code')} for n,v in
                    [('original',baseline_sam_original), ('portable_baseline',baseline_sam),
                     ('portable_poisoned',poison_sam), ('candidate',fix_sam)]},
                'constraints': [
                    'Synthetic isolated tests. No original SAM or WoolRadar business test acceptance.',
                    'Env filtering does not itself protect mutable checkouts or user-site startup hooks.',
                    'Candidate has not been integrated into a remote PR or deployed.',
                ],
            }
            RESULT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print(json.dumps(report, ensure_ascii=False, indent=2))
            if not report['all_expected']:
                raise SystemExit(1)
    finally:
        if before_pythonpath is not None:
            os.environ['PYTHONPATH'] = before_pythonpath


if __name__ == '__main__':
    main()
