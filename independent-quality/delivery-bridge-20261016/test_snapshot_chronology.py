"""Chronology and withdrawal contracts for independent draft review, synthetic only."""
import hashlib
import json
import unittest
from datetime import datetime, timezone

from consume_preview import review_delta, validate

NOW = datetime(2026, 10, 16, 3, 0, tzinfo=timezone.utc)
KEY_A = "a" * 24
KEY_B = "b" * 24


def event(key, status="CLAIMABLE"):
    return {
        "event_key": key, "title": "Synthetic public developer offer",
        "public_url": "https://example.org/public-offer", "reported_status": status,
        "publication_lane": "independent_official_recheck_required",
        "personal_eligibility": "UNKNOWN", "batch_key": None,
        "published_at": None, "first_seen": "2026-10-16T00:00:00Z",
        "official_evidence": [],
    }


def approved(stamp, events, day="2026-10-16"):
    value = {
        "schema_version": 1, "source_type": "LOCAL_REDACTED_PREVIEW_NOT_PUBLISHED",
        "report_date": day, "generated_at": stamp,
        "source_report_sha256": "c" * 64,
        "runtime_provenance_verified": False,
        "public_application_live_verified": False,
        "requires_operator_review_before_sharing": True,
        "count": {"input_events": len(events), "exported_events": len(events),
                  "skipped_or_duplicate": 0},
        "events": events,
    }
    raw = json.dumps(value).encode("utf-8")
    return validate(raw, hashlib.sha256(raw).hexdigest(), now=NOW)


class ChronologyWithdrawalTests(unittest.TestCase):
    def test_previous_later_snapshot_does_not_requeue_older_offer(self):
        earlier = approved("2026-10-16T01:00:00Z", [event(KEY_A)])
        later = approved("2026-10-16T02:00:00Z", [])
        result = review_delta(earlier, later)
        self.assertEqual(result["status"], "OUT_OF_ORDER_IGNORED")
        self.assertEqual(result["candidate_keys"], [])
        self.assertEqual(result["withdrawn_keys"], [])

    def test_previous_later_snapshot_does_not_fabricate_withdrawal(self):
        earlier = approved("2026-10-16T01:00:00Z", [])
        later = approved("2026-10-16T02:00:00Z", [event(KEY_A)])
        result = review_delta(earlier, later)
        self.assertEqual(result["status"], "OUT_OF_ORDER_IGNORED")
        self.assertEqual(result["withdrawn_keys"], [])

    def test_real_later_disappearance_produces_only_review_key(self):
        earlier = approved("2026-10-16T01:00:00Z", [event(KEY_A), event(KEY_B)])
        later = approved("2026-10-16T02:00:00Z", [event(KEY_B)])
        result = review_delta(later, earlier)
        self.assertEqual(result["candidate_keys"], [])
        self.assertEqual(result["withdrawn_keys"], [KEY_A])
        self.assertNotIn("EXPIRED", json.dumps(result))
        self.assertNotIn("CLAIMABLE", json.dumps(result))

    def test_later_status_change_remains_reviewable(self):
        earlier = approved("2026-10-16T01:00:00Z", [event(KEY_A)])
        later = approved("2026-10-16T02:00:00Z", [event(KEY_A, "EXPIRED")])
        result = review_delta(later, earlier)
        self.assertEqual(result["candidate_keys"], [KEY_A])
        self.assertEqual(result["withdrawn_keys"], [])

    def test_earlier_report_day_cannot_override_later_day(self):
        previous = approved("2026-10-16T01:00:00Z", [])
        current = approved("2026-10-16T02:00:00Z", [event(KEY_A)], "2026-10-15")
        result = review_delta(current, previous)
        self.assertEqual(result["status"], "OUT_OF_ORDER_IGNORED")
        self.assertEqual(result["candidate_keys"], [])

    def test_same_second_changed_snapshot_requires_order_proof(self):
        previous = approved("2026-10-16T01:00:00Z", [])
        current = approved("2026-10-16T01:00:00Z", [event(KEY_A)])
        result = review_delta(current, previous)
        self.assertEqual(result["status"], "SNAPSHOT_ORDER_AMBIGUOUS")
        self.assertEqual(result["candidate_keys"], [])
        self.assertEqual(result["withdrawn_keys"], [])

    def test_same_second_disappearance_does_not_assert_withdrawal(self):
        previous = approved("2026-10-16T01:00:00Z", [event(KEY_A)])
        current = approved("2026-10-16T01:00:00Z", [])
        result = review_delta(current, previous)
        self.assertEqual(result["status"], "SNAPSHOT_ORDER_AMBIGUOUS")
        self.assertEqual(result["candidate_keys"], [])
        self.assertEqual(result["withdrawn_keys"], [])

    def test_fractional_second_changed_snapshot_is_order_ambiguous(self):
        previous = approved("2026-10-16T01:00:00.100000Z", [])
        current = approved("2026-10-16T01:00:00.900000Z", [event(KEY_A)])
        result = review_delta(current, previous)
        self.assertEqual(result["status"], "SNAPSHOT_ORDER_AMBIGUOUS")
        self.assertEqual(result["candidate_keys"], [])
        self.assertEqual(result["withdrawn_keys"], [])

    def test_fractional_second_withdrawal_does_not_claim_disappearance(self):
        previous = approved("2026-10-16T01:00:00.100000Z", [event(KEY_A)])
        current = approved("2026-10-16T01:00:00.900000Z", [])
        result = review_delta(current, previous)
        self.assertEqual(result["status"], "SNAPSHOT_ORDER_AMBIGUOUS")
        self.assertEqual(result["candidate_keys"], [])
        self.assertEqual(result["withdrawn_keys"], [])

    def test_fractional_times_in_one_second_need_sequence_proof(self):
        for before,after in [([], [event(KEY_A)]),([event(KEY_A)],[]),([event(KEY_A)],[event(KEY_A,'EXPIRED')])]:
            with self.subTest(before=before,after=after):
                previous=approved('2026-10-16T01:00:00.100000Z',before)
                current=approved('2026-10-16T01:00:00.900000Z',after)
                result=review_delta(current,previous)
                self.assertEqual(result['status'],'SNAPSHOT_ORDER_AMBIGUOUS')
                self.assertEqual(result['candidate_keys'],[])
                self.assertEqual(result['withdrawn_keys'],[])
    def test_baseline_never_announces_old_offer(self):
        baseline = approved("2026-10-16T01:00:00Z", [event(KEY_A)])
        self.assertEqual(review_delta(baseline)["candidate_keys"], [])

    def test_unchanged_snapshot_with_clock_regression_remains_quiet(self):
        previous = approved("2026-10-16T02:00:00Z", [event(KEY_A)])
        current = approved("2026-10-16T01:00:00Z", [event(KEY_A)])
        result = review_delta(current, previous)
        self.assertEqual(result["status"], "OUT_OF_ORDER_IGNORED")
        self.assertEqual(result["candidate_keys"], [])
        self.assertEqual(result["withdrawn_keys"], [])


if __name__ == "__main__":
    unittest.main()
