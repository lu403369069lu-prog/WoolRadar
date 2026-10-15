"""Verify GitHub webhook payload HMAC before converting PR event into advisory work.

Transport, secret storage, replay prevention and execution remain outside scope.
No network access, comments, credentials, or runnable tasks are performed here.
"""
from __future__ import annotations

import hashlib
import hmac
import json

from coordination.github_event_adapter import parse_pr_event


def receive_pr_event(body: bytes, signature: str, secret: bytes, github_event: str) -> list[dict]:
    if github_event != "pull_request":
        return []
    if not isinstance(body, bytes) or not isinstance(secret, bytes) or not secret:
        raise ValueError("INVALID_WEBHOOK_INPUT")
    if not isinstance(signature, str) or len(signature) != 71 or not signature.startswith("sha256="):
        raise ValueError("INVALID_WEBHOOK_SIGNATURE")
    actual = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(actual, signature):
        raise ValueError("WEBHOOK_SIGNATURE_MISMATCH")
    payload = json.loads(body)
    return parse_pr_event(payload, signature_verified=True)
