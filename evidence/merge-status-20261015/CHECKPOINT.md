# Recompute status after evidence merge — isolated candidate

Date: 2026-10-15. Task WOOL-MERGE-STATUS-20261015, owner codex-woolradar. Formal claim/start state f8de04fc19ccb8b72521d71ec1cf0b7d6abf75b4/revision67. Re-read authoritative V3 state before any later mutation.

## Exact baseline and scope

This is stacked on the unmerged capacity-gate candidate PR15, commit0ddb3cb67718b7fe1c8212fc4d7baef9b561e126. It changes only core/db.py, tests/test_merge_status.py and its own evidence directory. It does not include PR13's diagnostic patch or PR14's noise audit. No automatic merge, production reindex, schema migration, notification, scheduled task, authentication or paid API action is performed.

## Reproduced defect and correction

Disposable SQLite contained two distinct article rows for a synthetically reviewed shared campaign. The retained row was UNKNOWN; the dropped row supplied fresh official open/public/positive-capacity proof. The original review_campaign merged the evidence but left the stored survivor UNKNOWN, while the existing verifier computed CLAIMABLE; generating a report did not repair UNKNOWN. Closed/conflicting/zero-capacity proof could likewise leave an obsolete retained status.

After a real merge, reindex now reads each affected survivor and its complete merged evidence through the same transaction/connection. The existing verifier computes the result. A changed status or claim scope is written with a status-history reason before committing. Untouched rows are not reevaluated; no new notifications are created. Exceptions roll back the entire merge, including campaign links and evidence movement; the preexisting SQLite backup remains available. It does not reopen another connection against uncommitted data.

## Actual tests

Six new contracts were run before implementation: five failures (promotion, expiry downgrade, conflict, zero-capacity result and injected verification exception); untouched-row control passed.

Windows/Python3.12.14 full command `python -X utf8 -m unittest discover -s tests`: **162 passed, exit0,10.157s**, zero skipped. This is capacity156 plus6; it is not all parallel PRs combined. Receipt contains exact output and executable SHA256. Contracts also check history, report visibility, no notification creation, and transaction rollback after a verifier exception. Independent review is recorded separately at the exact source hash.

## Remaining boundaries

The headline-only identity collision remains a separate, reproduced defect; this candidate does not change canonical keys or infer new campaign identities. Broader temporal-source conflicts and provenance are not redesigned. No production incidence or95% metric is inferred from synthetic SQLite.

PR5 Windows source preflight already passed155 tests with no dependency substitutes and91 remote blob identities checked; original system-TEMP errors are retained. Formal WOOL-HOLDOUT-WINDOWS was later claimed/blocked to conflict by another actor; this executor did not override that conflict. Prior CAS attempts that lost a concurrent state race returnedUNKNOWN, were read back and rebased without force or overwritten external changes.

Next: independent focused review of exact db/test hashes, draft PR on PR15 base, remote blob verification, V3 exact-SHA evidence and safe owner release. Other source/auth/full-stack/physical gates of original P06 remain incomplete.
