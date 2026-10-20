"""A failed JSON replacement must preserve the last durable consumer report.

Runs against a disposable database and report directory; no external delivery.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.db import Database
from core.models import Candidate
from core.report import ReportGenerator


class AtomicReportPublicationTests(unittest.TestCase):
    def test_json_replace_failure_keeps_last_complete_json(self):
        with tempfile.TemporaryDirectory(prefix="wool-report-publish-") as td:
            root = Path(td)
            db = Database(root / "synthetic.sqlite")
            db.upsert_candidate(Candidate(
                "synthetic", "synthetic", "Synthetic benefit", "https://example.org/benefit",
            ))
            report_dir = root / "reports"
            date = "2026-10-20"
            json_path = report_dir / f"{date}-daily.json"
            generator = ReportGenerator(db, report_dir)
            generator.generate(date)
            baseline_bytes = json_path.read_bytes()
            self.assertEqual(json.loads(baseline_bytes)["date"], date)

            import os
            actual_replace = os.replace

            def fail_json_commit(src, dst):
                if Path(dst) == json_path:
                    raise OSError("synthetic disk / sharing failure")
                return actual_replace(src, dst)

            with patch("os.replace", side_effect=fail_json_commit):
                with self.assertRaisesRegex(OSError, "synthetic disk"):
                    generator.generate(date)

            self.assertEqual(json_path.read_bytes(), baseline_bytes)
            self.assertFalse(list(report_dir.glob(".*.tmp")), "staged report was not cleaned")


if __name__ == "__main__":
    unittest.main()
