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


_NO_FEE = re.compile(
    r'\b(?:no|zero)\s+application\s+fees?(?:\s+is\s+required)?\b|'
    r'\bapplication\s+fees?\s+(?:is\s+|are\s+)?(?:not\s+required|waived)\b|'
    r'\bwithout\s+(?:an?\s+)?application\s+fee\b', re.I)
_NEGATED_APPLICATION = re.compile(
    r'\b(?:not\s+accepting\s+applications?|'
    r'no\s+applications?\s+(?:are\s+)?(?:open|accepted)|'
    r'applications?\s+(?:are\s+)?not\s+(?:open|accepted)|'
    r'not\s+open\s+for\s+applications?|'
    r'applications?\s+(?:(?:have|are|were)\s+)?(?:closed|ended|expired)|'
    r'(?:fund|grant|program)\s+(?:(?:is|was)\s+|has\s+been\s+)?'
    r'(?:closed|cancelled|canceled|discontinued|expired)|'
    r'(?:do|does|did|will|would|can|could|should|may)\s+not\s+accept\s+applications?|'
    r"(?:don|doesn|didn|won|wouldn|can|couldn|shouldn)['\u2019]t\s+accept\s+applications?|"
    r"(?:(?:isn|aren|wasn|weren)['\u2019]t|(?:is|are|was|were)\s+not)\s+accepting\s+applications?|"
    r"applications?\s+(?:(?:is|are|was|were)\s+not\s+being|"
    r"(?:isn|aren|wasn|weren)['\u2019]t\s+being|"
    r"(?:will|would)\s+not\s+be)\s+accepted)\b", re.I)
_APPLICANT_QUESTION = re.compile(
    r'(?:^|[.!?]\s+)(?:can|could|should|may|would)\b[^.!?]{0,140}'
    r'\b(?:apply|application)\b', re.I)


def is_developer_grant_lead(text: object) -> bool:
    """True only for an explicit current-sounding developer grant application lead."""
    if not isinstance(text, str) or not text or len(text) > 6000:
        return False
    normalized = ' '.join(text.split())
    if _NEGATED_APPLICATION.search(normalized) or _APPLICANT_QUESTION.search(normalized):
        return False
    # Explicit fee-waiver terms are not paid-application requirements.
    fee_scoped = _NO_FEE.sub(' ', normalized)
    if _DENY.search(fee_scoped):
        return False
    return bool(_SCOPE.search(normalized) and _PROGRAM.search(normalized)
                and _APPLY.search(normalized)
                and (_AWARD.search(normalized) or _AMOUNT.search(normalized)))


def has_grant_application_denial(text: object) -> bool:
    """Flag explicit closed applications even if brand/free words appear elsewhere.

    This is deliberately conservative for a combined source item: it prevents
    another positive cue from reviving a denied grant. A separate newly opened
    program should be recorded as its own independently reviewed source.
    """
    if not isinstance(text, str) or not text:
        return False
    normalized = ' '.join(text.split())
    return bool(_SCOPE.search(normalized) and _PROGRAM.search(normalized)
                and _NEGATED_APPLICATION.search(normalized))
