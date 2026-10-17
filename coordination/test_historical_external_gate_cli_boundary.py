"""CLI glue tests with a stubbed loader, NOT official frozen-manifest acceptance."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import historical_external_eight_gate_auditor as auditor


class SyntheticCliEnvelope(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.manifest = self.root / 'synthetic-manifest.json'
        self.manifest.write_text('{"synthetic":true}', encoding='utf-8')
        self.receipt = self.root / 'receipt.json'
        jobs = [{'family_id': family, 'project': p, 'external_constraint': kind,
                 'disposition': 'EXTERNAL_OR_POLICY_GATED'}
                for family, (p, kind) in auditor.GATES.items()]
        self.fake_guard = types.ModuleType('HISTORICAL_CODEX_42_RECEIPT_GUARD_20261017')
        self.fake_guard.load_verified_manifest = lambda path: {'jobs': jobs}

    def invoke(self):
        argv = ['gate_audit', '--manifest', str(self.manifest),
                '--receipt', str(self.receipt), '--evidence-root', str(self.root)]
        out, err = io.StringIO(), io.StringIO()
        with patch.dict(sys.modules, {self.fake_guard.__name__: self.fake_guard}), \
             patch.object(sys, 'argv', argv), \
             contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            exit_code = auditor.main()
        return exit_code, out.getvalue(), err.getvalue()

    def valid(self):
        return {'schema_version': 1, 'gates': [
            {'family_id': id, 'project': p, 'gate': kind,
             'state': 'BLOCKED', 'evidence': None}
            for id, (p, kind) in auditor.GATES.items()]}

    def test_valid_but_unapproved_receipt_stays_unaccepted(self):
        self.receipt.write_text(json.dumps(self.valid()), encoding='utf-8')
        code, stdout, stderr = self.invoke()
        self.assertEqual(code, 0, stderr)
        result = json.loads(stdout)
        self.assertEqual(result['families_evaluated'], 8)
        self.assertFalse(result['historical_recovery_closed'])
        self.assertFalse(result['all_historical_business_gates_accepted'])

    def test_massive_receipt_refused_before_loading_all_bytes(self):
        self.receipt.write_bytes(b'{' + b' '* (auditor.MAX_BYTES + 1) + b'}')
        code, stdout, stderr = self.invoke()
        self.assertEqual(code, 2)
        self.assertEqual(stderr, '')
        self.assertEqual(json.loads(stdout)['status'], 'INVALID_OR_INCOMPLETE')

    def test_receipt_symlink_to_unrelated_file_not_followed(self):
        other = self.root / 'unrelated_private_mock.txt'
        other.write_text('SYNTHETIC_SECRET_NOT_TO_READ')
        self.receipt.symlink_to(other)
        code, stdout, stderr = self.invoke()
        self.assertEqual(code, 2)
        self.assertNotIn('SYNTHETIC_SECRET_NOT_TO_READ', stdout + stderr)

    def test_duplicate_approval_row_refused_without_echo(self):
        receipt = self.valid()
        receipt['gates'][0]['state'] = 'APPROVED'
        self.receipt.write_text(json.dumps(receipt), encoding='utf-8')
        code, stdout, stderr = self.invoke()
        self.assertEqual(code, 2)
        self.assertEqual(stderr, '')
        self.assertFalse(json.loads(stdout)['historical_recovery_closed'])


if __name__ == '__main__':
    unittest.main()
