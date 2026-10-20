"""Synthetic interrupted render: a failed digest must not publish partial files."""

import tempfile
import unittest
from pathlib import Path

from core.db import Database
from core.models import Candidate
from core.report import ReportGenerator


class ReportRenderFailurePublicationTests(unittest.TestCase):
    def test_invalid_existing_metadata_does_not_publish_json_before_markdown(self):
        with tempfile.TemporaryDirectory(prefix="wool-report-render-") as td:
            root = Path(td)
            db = Database(root / "events.sqlite")
            event_id = db.upsert_candidate(Candidate(
                "synthetic", "synthetic", "Synthetic benefit", "https://example.org/offer",
            )).event_id
            with db.write_transaction() as conn:
                conn.execute(
                    "UPDATE events SET metadata_json=? WHERE id=?",
                    ('{"high_value":', event_id),
                )

            date = "2026-10-20"
            report_dir = root / "reports"
            report_dir.mkdir()
            json_path = report_dir / f"{date}-daily.json"
            md_path = report_dir / f"{date}-daily.md"
            json_path.write_text('previous-published-json', encoding="utf-8")
            md_path.write_text('previous-published-markdown', encoding="utf-8")

            with self.assertRaises(ValueError):
                ReportGenerator(db, report_dir).generate(date)

            self.assertEqual(json_path.read_text(encoding="utf-8"), 'previous-published-json')
            self.assertEqual(md_path.read_text(encoding="utf-8"), 'previous-published-markdown')


if __name__ == "__main__":
    unittest.main()
