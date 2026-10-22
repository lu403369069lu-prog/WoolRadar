#!/usr/bin/env python3
"""Windows-only isolated test: user-site Python startup under filtered APPDATA."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parent


def load_gate(name):
    spec = importlib.util.spec_from_file_location('r4_' + name, ROOT / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def execute(gate, source, output):
    with contextlib.redirect_stdout(io.StringIO()):
        gate.run(SimpleNamespace(repo='WoolRadar', source=str(source), output=str(output)))
    result = json.loads(output.read_text(encoding='utf-8'))
    return {'status': result['status'], 'exit_code': result.get('exit_code'), 'total': result.get('total')}


def main():
    if os.name != 'nt':
        raise SystemExit('Windows-only: APPDATA user-site behavior differs elsewhere')
    gate = load_gate('integration_gate_candidate.py')
    isolated_gate = load_gate('integration_gate_candidate_isolated.py')
    with tempfile.TemporaryDirectory(prefix='usersite-r4-', dir=ROOT) as dirname:
        temp = Path(dirname)
        source = temp / 'source'
        (source / 'tests').mkdir(parents=True)
        (source / 'tests' / 'test_truth.py').write_text(
            'import unittest\nclass Truth(unittest.TestCase):\n'
            '    def test_must_fail(self):\n        self.assertEqual(0, 1)\n', encoding='utf-8')
        appdata = temp / 'APPDATA'
        site_packages = appdata / 'Python' / f'Python{sys.version_info.major}{sys.version_info.minor}' / 'site-packages'
        site_packages.mkdir(parents=True)
        (site_packages / 'sitecustomize.py').write_text(
            'import os, sys\nsys.stdout.write("Ran 1 test in 0.000s\\n\\nOK\\n")\n'
            'sys.stdout.flush()\nos._exit(0)\n', encoding='utf-8')
        original_appdata = os.environ.get('APPDATA')
        original_no_user_site = os.environ.get('PYTHONNOUSERSITE')
        try:
            os.environ['APPDATA'] = str(appdata)
            os.environ.pop('PYTHONNOUSERSITE', None)
            # APPDATA stays allowed by the candidate; PYTHONNOUSERSITE is dropped.
            poisoned = execute(gate, source, temp / 'filtered-appdata.json')
            # Control uses an explicit isolated-Python candidate without monkeypatches.
            protected = execute(isolated_gate, source, temp / 'isolated-python.json')
        finally:
            if original_appdata is None:
                os.environ.pop('APPDATA', None)
            else:
                os.environ['APPDATA'] = original_appdata
            if original_no_user_site is None:
                os.environ.pop('PYTHONNOUSERSITE', None)
            else:
                os.environ['PYTHONNOUSERSITE'] = original_no_user_site
        checks = {
            'filtered_candidate_appdata_false_pass': poisoned['status'] == 'PASS' and poisoned['exit_code'] == 0,
            'python_isolated_flag_restores_failure': protected['status'] == 'FAIL' and protected['exit_code'] != 0,
        }
        report = {'kind': 'isolated_usersite_startup_negative', 'platform': sys.platform,
                  'python': sys.version.split()[0], 'checks': checks,
                  'observed': {'candidate': poisoned, 'python_I_control': protected},
                  'source': 'synthetic failing unittest and controlled temporary APPDATA only',
                  'business_acceptance': False}
        (ROOT / 'usersite-bypass-evidence.json').write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print(json.dumps(report, indent=2))
        if not all(checks.values()):
            raise SystemExit(1)


if __name__ == '__main__':
    main()
