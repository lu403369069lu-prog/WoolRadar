from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


class Status(StrEnum):
    DISCOVERED = 'DISCOVERED'
    CROSS_CHECKED = 'CROSS_CHECKED'
    OFFICIAL_VERIFIED = 'OFFICIAL_VERIFIED'
    CLAIMABLE = 'CLAIMABLE'
    UNKNOWN = 'UNKNOWN'
    CONFLICTED = 'CONFLICTED'
    EXPIRED = 'EXPIRED'
    FAILED = 'FAILED'
    REDEEMED = 'REDEEMED'


@dataclass(slots=True)
class Candidate:
    node: str
    source: str
    title: str
    url: str
    published_at: str = ''
    discovered_at: str = field(default_factory=utc_now)
    author: str = ''
    summary: str = ''
    source_kind: str = 'community'
    batch_id: str = ''
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> 'Candidate':
        allowed = cls.__dataclass_fields__.keys()
        return cls(**{key: value[key] for key in allowed if key in value})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Evidence:
    kind: str
    url: str
    provenance_key: str
    checked_at: str = field(default_factory=utc_now)
    excerpt: str = ''
    claims: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class VerificationResult:
    status: Status
    reason: str
    independent_evidence_count: int
    claim_scope: str = 'NONE'
    unknown_capacity: bool = True

