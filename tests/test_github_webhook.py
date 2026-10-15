import hashlib
import hmac
import json
import unittest
from coordination.github_webhook import receive_pr_event

SECRET = b"synthetic-test-secret"


def packet(action="opened"):
    return json.dumps({"action": action,
      "repository": {"full_name": "lu403369069lu-prog/WoolRadar"},
      "pull_request": {"number": 6,
        "head": {"sha": "a" * 40, "repo": {"full_name": "lu403369069lu-prog/WoolRadar"}},
        "base": {"ref": "chatgpt/handoff"}}}).encode()


def signature(body):
    return "sha256=" + hmac.new(SECRET, body, hashlib.sha256).hexdigest()


class WebhookTests(unittest.TestCase):
    def test_correct_signed_event(self):
        body = packet()
        self.assertEqual(receive_pr_event(body, signature(body), SECRET, "pull_request")[0]["task_id"], "PR-6")

    def test_tampered_payload_rejected(self):
        body = packet()
        with self.assertRaisesRegex(ValueError, "MISMATCH"):
            receive_pr_event(body + b" ", signature(body), SECRET, "pull_request")

    def test_unsigned_rejected(self):
        with self.assertRaises(ValueError):
            receive_pr_event(packet(), "", SECRET, "pull_request")

    def test_empty_secret_rejected(self):
        body = packet()
        with self.assertRaisesRegex(ValueError, "INVALID_WEBHOOK_INPUT"):
            receive_pr_event(body, signature(body), b"", "pull_request")

    def test_non_pr_event_ignored(self):
        body = packet()
        self.assertEqual(receive_pr_event(body, signature(body), SECRET, "push"), [])

    def test_unrecognized_action_ignored(self):
        body = packet("closed")
        self.assertEqual(receive_pr_event(body, signature(body), SECRET, "pull_request"), [])


if __name__ == "__main__":
    unittest.main()
