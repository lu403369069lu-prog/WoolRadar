"""Full-suite evidence decoding must retain the same UTF-8 boundary as subsets."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import integration_gate


class IntegrationByteIntegrity(unittest.TestCase):
    def exercise(self, invalid):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            (root / "tests").mkdir()
            body = "os.write(1,bytes([255]))" if invalid else "self.assertTrue(True)"
            (root / "tests" / "test_probe.py").write_text(
                "import os,unittest\nclass Evidence(unittest.TestCase):\n def test_one(self): " + body + "\n",
                encoding="utf-8")
            target = root / "report.json"
            with patch.object(integration_gate, "source_sha", return_value="a" * 40):
                integration_gate.run(SimpleNamespace(source=str(root), repo="WoolRadar", output=str(target)))
            return json.loads(target.read_text(encoding="utf-8"))

    def test_fullsuite_invalid_byte_output_is_blocked(self):
        report = self.exercise(True)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["error_kind"], "UnicodeDecodeError")
        self.assertNotIn("passed", report)

    def test_fullsuite_clean_utf8_still_passes(self):
        report = self.exercise(False)
        self.assertEqual((report["status"], report["total"], report["passed"]), ("PASS", 1, 1))
