"""Untrusted source metadata cannot forge headings inside a Chinese digest."""

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.db import Database
from core.models import Candidate, Evidence
from core.report import ReportGenerator


class MarkdownFieldInjectionTests(unittest.TestCase):
    def test_untrusted_source_and_evidence_cannot_forge_report_sections(self):
        with tempfile.TemporaryDirectory(prefix="wool-md-fields-") as td:
            root = Path(td)
            db = Database(root / "events.sqlite")
            candidate = Candidate(
                "node\n## FORGED_NODE_HEADING",
                "feed\n## FORGED_SOURCE_HEADING",
                "Legitimate developer benefit",
                "https://vendor.example/benefit",
            )
            event = db.upsert_candidate(candidate).event_id
            db.add_evidence(event, Evidence(
                "community", "https://forum.example/post\n## FORGED_EVIDENCE_HEADING",
                "community-reference", claims={"source": "community"},
            ))
            # Freeze the report day to this stored event, not the test run date.
            first_seen = db.get_event(event)["first_seen"]
            report_day = datetime.fromisoformat(first_seen.replace("Z", "+00:00")).astimezone(
                timezone(timedelta(hours=8))
            ).date().isoformat()
            paths = ReportGenerator(db, root / "reports").generate(report_day)
            markdown = paths.markdown.read_text(encoding="utf-8")
            for forged in (
                "\n## FORGED_NODE_HEADING",
                "\n## FORGED_SOURCE_HEADING",
                "\n## FORGED_EVIDENCE_HEADING",
            ):
                with self.subTest(forged=forged):
                    self.assertNotIn(forged, markdown)
            self.assertIn("Legitimate developer benefit", markdown)
            self.assertIn("https://vendor.example/benefit", markdown)
            self.assertIn("来源：feed", markdown)


if __name__ == "__main__":
    unittest.main()
