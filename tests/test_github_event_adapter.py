import unittest

from coordination.github_event_adapter import parse_pr_event, preview_pr_event

SHA = "b" * 40


def sample(**changes):
    doc = {"action": "opened",
           "repository": {"full_name": "lu403369069lu-prog/WoolRadar"},
           "pull_request": {"number": 6,
                            "head": {"sha": SHA, "repo": {"full_name": "lu403369069lu-prog/WoolRadar"}},
                            "base": {"ref": "chatgpt/handoff"}}}
    doc.update(changes)
    return doc


class GitHubEventAdapterTests(unittest.TestCase):
    def test_unverified_webhook_rejected(self):
        with self.assertRaisesRegex(ValueError, "UNVERIFIED"):
            parse_pr_event(sample(), signature_verified=False)

    def test_verified_pr_maps_to_advisory_event(self):
        event, = parse_pr_event(sample(), signature_verified=True)
        self.assertEqual(event["task_id"], "PR-6")
        self.assertEqual(event["event_type"], "evidence_ready")
        self.assertEqual(event["head_sha"], SHA)

    def test_forks_are_ignored(self):
        payload = sample()
        payload["pull_request"]["head"]["repo"]["full_name"] = "outsider/WoolRadar"
        self.assertEqual(parse_pr_event(payload, signature_verified=True), [])

    def test_unknown_repo_ignored(self):
        self.assertEqual(parse_pr_event(sample(repository={"full_name": "outsider/repo"}),
                                        signature_verified=True), [])

    def test_untrusted_action_ignored(self):
        self.assertEqual(parse_pr_event(sample(action="closed"), signature_verified=True), [])

    def test_bad_sha_rejected(self):
        payload = sample()
        payload["pull_request"]["head"]["sha"] = "bad"
        with self.assertRaisesRegex(ValueError, "SHA"):
            parse_pr_event(payload, signature_verified=True)

    def test_preview_not_authenticated(self):
        self.assertTrue(preview_pr_event(sample()))
        with self.assertRaisesRegex(ValueError, "UNVERIFIED"):
            parse_pr_event(sample(), signature_verified=False)

    def test_bad_pr_number_rejected(self):
        payload = sample()
        payload["pull_request"]["number"] = True
        with self.assertRaisesRegex(ValueError, "PR_METADATA"):
            parse_pr_event(payload, signature_verified=True)


if __name__ == "__main__":
    unittest.main()
