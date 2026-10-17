"""Explain conservative developer-grant *leads* without changing selection.

Never reports user eligibility, public veracity, payment status, or official approval.
Returns Boolean gates only; does not persist or expose source snippets.
"""
from __future__ import annotations

import re
from . import developer_grants as rules


def diagnose_developer_grant_lead(text: object) -> dict[str, object]:
    """Explain the same decision as is_developer_grant_lead; no new positives."""
    if not isinstance(text, str) or not text:
        return {"selected": False, "reason": "invalid_or_empty_input",
                "sections_examined": 0, "best_section": None}
    if len(text) > 6000:
        return {"selected": False, "reason": "oversized_input",
                "sections_examined": 0, "best_section": None}

    normalized = " ".join(text.split())
    negated = bool(rules._NEGATED_APPLICATION.search(normalized))
    applicant_question = bool(rules._APPLICANT_QUESTION.search(normalized))
    fee_scoped = rules._NO_FEE.sub(" ", normalized)
    other_deny = bool(rules._DENY.search(fee_scoped))
    # Deliberately mirror the classifier's exact project separation.
    sections = [x for x in re.split(
        r"\r?\n[ \t]*\r?\n+|(?m:^[ \t]*(?:[-*•]|\d{1,3}[.)])[ \t]+)",
        text) if x.strip()]
    gates = []
    for section in sections:
        candidate = " ".join(section.split())
        row = {"scope": bool(rules._SCOPE.search(candidate)),
               "program": bool(rules._PROGRAM.search(candidate)),
               "application": bool(rules._APPLY.search(candidate)),
               "award": bool(rules._AWARD.search(candidate)),
               "named_amount": bool(rules._AMOUNT.search(candidate))}
        row["all_signals"] = (row["scope"] and row["program"] and row["application"]
                              and (row["award"] or row["named_amount"]))
        gates.append(row)

    # Tie-breaking uses input order. No source text/URLs are emitted.
    best = (max(gates, key=lambda g: sum(g[k] for k in
                  ("scope", "program", "application", "award", "named_amount")))
            if gates else None)
    canonical = rules.is_developer_grant_lead(text)
    if negated:
        reason = "negated_application"
    elif applicant_question:
        reason = "applicant_question"
    elif other_deny:
        reason = "closed_paid_or_personal_request"
    elif canonical:
        reason = "unverified_lead_candidate"
    else:
        reason = "no_self_contained_positive_section"
    return {"selected": canonical, "reason": reason,
            "sections_examined": len(sections), "best_section": best,
            "global_denial_flags": {
                "negated_application": negated,
                "applicant_question": applicant_question,
                "other_denial": other_deny,
            }}


def aggregate_diagnostics(texts) -> dict[str, object]:
    """Aggregate a frozen iterable; no raw lead text, URLs or account data leave."""
    from collections import Counter
    reasons = Counter()
    missing_gates = Counter()
    total = selected = 0
    for value in texts:
        total += 1
        r = diagnose_developer_grant_lead(value)
        reasons[r["reason"]] += 1
        selected += int(r["selected"])
        if r["reason"] == "no_self_contained_positive_section" and r["best_section"]:
            gates = r["best_section"]
            for signal in ("scope", "program", "application"):
                if not gates[signal]:
                    missing_gates[signal] += 1
            if not (gates["award"] or gates["named_amount"]):
                missing_gates["award_or_named_amount"] += 1
    return {"records": total, "candidate_leads": selected,
            "not_a_claimability_verdict": True,
            "reasons": dict(sorted(reasons.items())),
            "missing_signals_in_best_section": dict(sorted(missing_gates.items()))}


def main() -> int:
    """Consume explicitly supplied local JSONL via stdin; print AGGREGATES only.

    Each object supplies text or title+summary; URLs, identities and full
    messages are never printed, persisted or exported by this command.
    """
    import json
    import sys
    if len(sys.argv) != 1:
        print("Usage: python -m core.grant_lead_diagnostics < local_public.jsonl", file=sys.stderr)
        return 2
    def validated_records():
        # readline(limit) bounds allocation even before the JSON parser sees a
        # maliciously large record. Aggregate incrementally; never retain raw
        # source text or emit partial totals if a late record is malformed.
        line_number = 0
        while True:
            # Read raw bytes, not TextIOWrapper's permissive surrogateescape:
            # malformed UTF-8 must never become an accepted source snippet.
            raw = sys.stdin.buffer.readline(32769)
            if not raw:
                return
            line_number += 1
            if line_number > 10000:
                raise ValueError("INVALID_INPUT: too many diagnostic records")
            if len(raw) > 32768:
                raise ValueError(f"INVALID_INPUT: oversized JSONL record {line_number}")
            try:
                line = raw.decode('utf-8', errors='strict')
            except UnicodeDecodeError:
                raise ValueError(f"INVALID_INPUT: JSONL record {line_number}") from None
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                if not isinstance(data, dict):
                    raise ValueError('not an object')
                if isinstance(data.get('text'), str):
                    value = data['text']
                elif isinstance(data.get('title'), str) or isinstance(data.get('summary'), str):
                    if any(key in data and data[key] is not None and not isinstance(data[key], str)
                           for key in ('title', 'summary')):
                        raise ValueError('non-string public field')
                    value = (data.get('title') or '') + '\n' + (data.get('summary') or '')
                else:
                    raise ValueError('missing public text fields')
            except (ValueError, TypeError):
                # No parser exception or source fragment is ever returned.
                raise ValueError(f"INVALID_INPUT: JSONL record {line_number}") from None
            yield value

    try:
        totals = aggregate_diagnostics(validated_records())
    except ValueError as exc:
        # Only fixed, synthetic line-numbered errors are raised above.
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(totals, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
