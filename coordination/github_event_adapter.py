"""Convert verified GitHub PR webhook envelopes to dispatcher input; no side effects.

Caller MUST validate X-Hub-Signature-256 before invoking parse_pr_event.
Never execute PR body, issue comment content, or event-supplied commands.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from coordination.dispatcher import PROJECTS, validate

ALLOWED_ACTIONS = {"opened", "reopened", "synchronize", "ready_for_review"}


def parse_pr_event(payload: dict, *, signature_verified: bool) -> list[dict]:
    """A trusted webhook receiver passes signature_verified=True only after HMAC verification.

    This function does not validate the signature itself or contact GitHub. It
    fails closed without verified provenance; a CLI caller cannot override this.
    """
    if not signature_verified:
        raise ValueError("UNVERIFIED_GITHUB_WEBHOOK")
    if not isinstance(payload, dict) or payload.get("action") not in ALLOWED_ACTIONS:
        return []
    repository = payload.get("repository")
    pr = payload.get("pull_request")
    if not isinstance(repository, dict) or not isinstance(pr, dict):
        raise ValueError("MALFORMED_GITHUB_EVENT")
    repo_name = repository.get("full_name")
    if not isinstance(repo_name, str):
        raise ValueError("MISSING_REPOSITORY_IDENTITY")
    projects = [(name, number) for name, (full, number) in PROJECTS.items()
                if full == repo_name]
    if not projects:
        return []
    project, issue = projects[0]
    number = pr.get("number", payload.get("number"))
    head = pr.get("head")
    base = pr.get("base")
    if type(number) is not int or number <= 0 or not isinstance(head, dict) or not isinstance(base, dict):
        raise ValueError("INVALID_PR_METADATA")
    head_repo = head.get("repo")
    if not isinstance(head_repo, dict) or head_repo.get("full_name") != repo_name:
        return []  # Do not trust fork PR code or refs
    head_sha = head.get("sha")
    if not isinstance(head_sha, str):
        raise ValueError("MISSING_HEAD_SHA")
    # A PR is evidence, not permission to run it, deploy, or approve anything.
    result = {"project": project, "repository": repo_name, "issue": issue,
              "task_id": f"PR-{number}", "head_sha": head_sha,
              "event_type": "evidence_ready",
              "evidence_url": f"https://github.com/{repo_name}/pull/{number}"}
    return [validate(result)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a captured GitHub PR event")
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    # A local JSON file cannot prove that a webhook was signed. CLI is
    # deliberately simulation-only: never sends authenticated=True.
    payload = json.loads(args.input.read_text(encoding="utf8"))
    print(json.dumps({"simulation_only": True, "events": parse_pr_event(
        payload, signature_verified=False)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
