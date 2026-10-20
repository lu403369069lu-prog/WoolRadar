"""A high-value badge cannot re-promote stopped or restricted offers."""

import tempfile
import unittest
from pathlib import Path

from core.db import Database
from core.models import Candidate, Evidence, Status
from core.report import ReportGenerator


class HighValueReportGateTests(unittest.TestCase):
    def test_expired_and_restricted_offers_do_not_reappear_as_high_value(self):
        with tempfile.TemporaryDirectory(prefix="wool-high-value-") as td:
            root = Path(td)
            db = Database(root / "sample.sqlite")

            def insert(title, status, official=None):
                candidate = Candidate(
                    "synthetic", "fixture", title,
                    "https://vendor.example/" + title.lower().replace(" ", "-"),
                    metadata={"high_value": True},
                )
                event = db.upsert_candidate(candidate).event_id
                if official:
                    db.add_evidence(event, Evidence(
                        "official", candidate.url + "/terms", title,
                        claims={"open": True, "public": True, **official},
                    ))
                db.set_status(event, status, "test fixture",
                              "PUBLIC_APPLICATION" if status == Status.CLAIMABLE else "NONE")

            insert("Expired Benefit", Status.EXPIRED)
            insert("Conflicted Benefit", Status.CONFLICTED)
            insert("Card Benefit", Status.CLAIMABLE, {"card_required": True})
            insert("Region Benefit", Status.CLAIMABLE,
                   {"eligibility_constraints": {"excluded_countries": ["CN"]}})
            insert("Clean Benefit", Status.CLAIMABLE)
            # The clean benefit requires an actual fresh official proof.
            clean_url = "https://vendor.example/clean-benefit"
            clean = next(e for e in db.list_events() if e["primary_url"] == clean_url)
            db.add_evidence(clean["id"], Evidence(
                "official", clean_url + "/terms", "clean",
                claims={"open": True, "public": True},
            ))
            paths = ReportGenerator(db, root / "reports").generate("2026-10-20")
            markdown = paths.markdown.read_text(encoding="utf-8")
            section = markdown.split("## 限时高价值活动\n", 1)[1].split("## ", 1)[0]
            self.assertIn("Clean Benefit", section)
            for title in ("Expired Benefit", "Conflicted Benefit",
                          "Card Benefit", "Region Benefit"):
                with self.subTest(title=title):
                    self.assertNotIn(title, section)
            self.assertIn("Card Benefit", markdown.split(
                "## 绑卡或自动续费风险：待人工核验\n", 1)[1].split("## ", 1)[0])
            self.assertIn("Region Benefit", markdown.split(
                "## 中国大陆地域资格限制：待人工核验\n", 1)[1].split("## ", 1)[0])


if __name__ == "__main__":
    unittest.main()
