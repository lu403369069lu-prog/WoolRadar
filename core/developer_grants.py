"""Conservative developer/OSS grant discovery; an unverified lead, not a claimability verdict.

Only infer that an application announcement may deserve independent official
review. Never infer eligibility, payment/card terms, a selection or a payout.
"""
from __future__ import annotations

import re

_SCOPE = re.compile(r'\b(?:open[\s-]?source|maintainers?|developers?)\b', re.I)
_PROGRAM = re.compile(r'\b(?:fund|funding|grants?|fellowships?)\b', re.I)
_APPLY = re.compile(
    r'\b(?:accept(?:s|ing)?\s+applications?|applications?\s+(?:are\s+|now\s+|currently\s+)?'
    r'(?:open|accepted)|rolling\s+applications?|apply\s+(?:now|today|for)|'
    r'call\s+for\s+applications?)\b', re.I)
_AWARD = re.compile(
    r'\b(?:selected|eligible|approved|accepted|successful)\b.{0,90}'
    r'\b(?:receive|receives|get|gets|awarded|grant(?:ed)?)\b.{0,70}'
    r'\$\s*\d[\d,]*(?:\.\d{1,2})?\b', re.I | re.S)
_AMOUNT = re.compile(
    r'\b(?:funding|grant)(?:\s+amount)?\s*:\s*\$\s*\d[\d,]*(?:\.\d{1,2})?\b', re.I)
_DENY = re.compile(
    r'\b(?:applications?\s+(?:have\s+|are\s+)?(?:closed|ended|expired)|'
    r'(?:no\s+longer|not\s+currently|not\s+yet)\s+(?:open|accepting)|'
    r'(?:closed|expired|discontinued|cancelled)\s+(?:fund|grant|program)|'
    r'(?:paid|application\s+fee|pay\s+to\s+apply|donation|donations|subscription|'
    r'only\s+available\s+with\s+purchase))\b|'
    r'\b(?:is\s+there|does\s+anyone|where\s+can\s+i|looking\s+for|i\s+want|i\s+need)\b', re.I)


def is_developer_grant_lead(text: object) -> bool:
    """True only for an explicit current-sounding developer grant application lead."""
    if not isinstance(text, str) or not text or len(text) > 6000:
        return False
    normalized = ' '.join(text.split())
    if _DENY.search(normalized):
        return False
    return bool(_SCOPE.search(normalized) and _PROGRAM.search(normalized)
                and _APPLY.search(normalized)
                and (_AWARD.search(normalized) or _AMOUNT.search(normalized)))
