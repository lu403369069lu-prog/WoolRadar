# WoolRadar preview snapshot-order review (2026-10-16)

**Status:** independent draft regression candidate, not a verified publication channel.
**Base:** WoolRadar main integration PR #23 exact HEAD `e3b31af746776bf976aba7418fce06ff2ae2ccde`.
Only the isolated preview consumer and one new test file change; no production code, scheduler, SQLite or account access.

## Finding and fix

The preview validator checks each file is recent, but cannot infer which
of two individually valid files is chronologically newer. Old `review_delta`
did not compare `generated_at` or `report_date`: reversing the order of two
valid previews could queue an old promotional event as a *new* review candidate.
An event disappearing from a later approved preview was also completely
absent from the review queue, losing potential expiration, source outage or
noise-review changes.

The candidate compares generation timestamp and date before emitting a
changed or withdrawn event. When the 'current' file is older and there is
a semantic difference, it returns `OUT_OF_ORDER_IGNORED` with no candidate
or withdrawn keys. Normal chronological disappearance generates a
`withdrawn_keys` entry for **manual source recheck only**, never an
automatic `EXPIRED` or expired-stock assertion. A bare check-time refresh
or list-order change remains excluded from 'new' events, preserving the
existing 313-test compatibility requirement. Baseline remains empty.

## Independent execution evidence

New file: `independent-quality/delivery-bridge-20261016/test_snapshot_chronology.py`
has seven full-schema Python fixture tests that use `validate` and `review_delta`
from the repository. This exact repository test file was uploaded and its
Git blob read back. The **isolated extracted-function Python semantic harness**
was actually executed in Linux/Python 3.13:

- Before the patch: 7 test scenarios -> 2 failures, 2 errors, 3 passes.
- After the patch: 7/7 scenarios passed, exit 0.

**Limit of this execution:** The harness re-created the GitHub `review_delta`
function and a minimal validator stub. It is **not** a complete import of the
private repository's actual `consume_preview.py`, and no Windows full-suite
run happened in this session. The new formal test must still be run at the
exact draft HEAD together with the current 313 integrated methods.

Required isolated Windows check:

```sh
python -B -X utf8 -m unittest discover -s independent-quality/delivery-bridge-20261016 -p 'test_*.py' -v
python -B independent-quality/delivery-bridge-20261016/run_combined_tests.py
```

## Remaining acceptance gates

- Equal-second snapshots with distinct content remain ambiguous for backward
  compatibility; trustworthy publisher sequence/revision + signed provenance
  must be defined before real automatic ingestion.
- A disappearing event is not proof of official expiry; source outage,
  intentional noise exclusion, dedup and processing failure are possible.
- The live ChatGPT daily brief has **not** consumed a user-approved WoolRadar
  runtime export; retain `OUTPUT_NOT_CONNECTED`.
- The new 56 public-source frozen snippet holdout reports TP0 / FN2 / TN47
  / unknown7 at SHA `afc24c15…`, with the two missed rows one campaign.
  Frozen holdout has not reached the acceptance threshold and cannot be
  re-scored as an independent unseen set after tuning to those examples.
- P06, five-source field conditions, source identity, account/region/card
  qualification, SAM 61-positive/522-gold and all final three independent
  acceptance rounds remain incomplete.

No Codex, Work, paid API, local deployment, real account, merge or raw report upload.


## Newly reproduced: same-second conflicting publications

Even when each preview is a valid independently SHA-checked payload and its
date is fresh, two different snapshots may have identical `generated_at`
timestamps. Schema v1 has **no signed monotonic publication sequence**.
The previous PR28 candidate treated one as newer and emitted candidate
or withdrawn keys without an ordering proof. This is an actual logical
gap in the independent review queue, not proof of real source availability.

New red/green test cases use the **exact GitHub consumer source** and the
committed formal `test_snapshot_chronology.py`, with the exporter's pure
`public_url`, `public_title`, `public_claims` helper implementations
reconstructed from the main candidate (not a full production exporter).
Before the fix, 2 new same-second assertions failed; after the fix,
**all 9/9 formal chronology tests PASS, exit0** on Linux/Python3.13.
The locally executed `consume_preview.py` git object equals the new GitHub
blob `d139b07ecb427d16cde3cc6f6dfe96e3a8b2f428` and the formal
test file equals `abd6bd20b2cb8eabf7fbe21ed80d20f2c1f38193`.

Different snapshots with identical timestamps now return
`SNAPSHOT_ORDER_AMBIGUOUS`, no changed or withdrawn event keys. This
does not solve same-timestamp ordering; it refuses to guess until a
future trusted monotonic publisher sequence can prove a newer revision.

**Limit:** Only isolated 9-case consumer tests ran in this conversation;
the 313-test full Windows integration remains NOT_VERIFIED at this SHA,
and the daily ChatGPT brief is still OUTPUT_NOT_CONNECTED.