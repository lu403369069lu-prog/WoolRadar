"""Explicit unverified fee-waiver and community-host support leads.

Discovery never establishes an award, current availability or personal eligibility.
"""
import re

_SCOPE = re.compile(r'\b(?:developers?|software|certifications?|open[ -]source|hackathons?)\b', re.I)
_DENIAL = re.compile(
    r'\b(?:not\s+(?:now\s+)?waived|no\s+longer|has\s+ended|have\s+ended|expired|'
    r'applications?\s+(?:are\s+|have\s+)?closed|cancelled|canceled|is\s+over|are\s+over)\b|'
    r'\b(?:will\s+not|won[\x27’]t|do\s+not|don[\x27’]t)\s+(?:receive|provide|offer)\b|'
    r'\b(?:can|could|may|would)\s+(?:i|we)\b|\b(?:looking\s+for|need)\s+(?:funding|swag)\b|'
    r'\b(?:does?\s+anyone\s+know|is\s+there|are\s+there)\b|'
    r'\bonly\s+(?:available\s+)?with\b.{0,40}\bpaid\b|'
    r'\blast\s+year[\x27’]s\s+(?:announcement|offer|program)\b', re.I)
_WAIVER = re.compile(
    r'\b(?:exam|examination|certification)\s+fees?\s+(?:is|are)\s+'
    r'(?:(?:now|currently)\s+)?waived\b', re.I)
_HOST = re.compile(r'\b(?:hosts?|organizers?)\b', re.I)
_INVITATION = re.compile(r'\b(?:apply\s+to\s+host|host\s+a\s+fest|looking\s+for\s+hosts|'
                         r'applications?\s+(?:are\s+)?open)\b', re.I)
_SUPPORT = re.compile(
    r'\b(?:will\s+receive|you[\x27’]ll\s+receive|we[\x27’]ll\s+provide|we\s+will\s+provide)\b'
    r'[^.!?]{0,100}\b(?:t-shirts?|stickers?|swag|funding|reimbursement)\b', re.I)
_TECH_EXAM = re.compile(r'\b(?:developer|software|github)\b',re.I)
_TECH_EVENT = re.compile(r'\bhacktoberfest\b|\b(?:developer|software|open[ -]source)\s+'
                         r'(?:(?:ai|community)\s+){0,2}(?:events?|meetups?|hackathons?)\b',re.I)

def is_explicit_developer_benefit(text: str) -> bool:
    if not isinstance(text,str) or not text or len(text)>16000:
        return False
    normalized=' '.join(text.split())
    if not _SCOPE.search(normalized) or _DENIAL.search(normalized):
        return False
    # Scope must be in the fee's own sentence, not unrelated technical news.
    if any(_WAIVER.search(part) and _TECH_EXAM.search(part)
           for part in re.split(r'[.!?;]',normalized)):
        return True
    return bool(_TECH_EVENT.search(normalized) and _HOST.search(normalized) and _INVITATION.search(normalized)
                and _SUPPORT.search(normalized))
