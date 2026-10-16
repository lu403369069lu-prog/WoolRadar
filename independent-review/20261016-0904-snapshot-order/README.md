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

## 2026-10-16 follow-up: strict JSON decoding and full-suite fixture compatibility

The existing `consume_preview.validate` checked the exact top-level and event
field sets, SHA-256 and sanitized public claims **after** Python's ordinary
`json.loads`. Standard `json.loads` silently keeps the last duplicate
object field (including inside nested evidence claims), accepts `NaN` and
`Infinity`, and parses `1e9999` as an infinite float. Different consumers
may see different semantics, and a correctly hashed preview could still
be structurally ambiguous. Current PR28 candidate adds `object_pairs_hook`
to reject duplicate keys at all nesting levels, `parse_constant` for
non-JSON constants and `parse_float` to fail on float overflow.

Five formal new tests in `test_consume_preview.py` cover duplicate origin
flag, event title, nested evidence claim, NaN claim and exponent overflow.
A Linux/Python 3.13 independent **isolated strict-decoder reproduction**
ran five identical JSON classes: legacy `json.loads` accepted all five,
whereas the new strict decoder rejected all five; a valid finite JSON
nested dictionary remained accepted. That execution tested the parser
helpers in isolation, not the entire GitHub `validate` and reporter.

A separate already-committed consumer test expected changed events to be
returned when the old/new test reports shared the *same* generated-at
timestamp. This contradicts PR28's same-second ambiguity safety contract.
The synthetic test fixture was corrected to use a newer current preview
generation timestamp (00:15 versus 00:00 UTC on the same day). This
does not change original holdout labels, production runtime or criteria.

**NOT VERIFIED:** The full `python -m unittest discover` on exact newest
branch/head after these edits, Windows/Python version compatibility,
producer-to-consumer real approved transfer, authentication and 09:30
scheduled recipient delivery. Keep DELIVERY_BRIDGE=OUTPUT_NOT_CONNECTED.


## 2026-10-16 exact-source full bridge regression and privacy escalation

Independent offline reproduction in Linux Python 3.13.5; all seven
runtime/test source files in `independent-quality/delivery-bridge-20261016/`
were copied from this exact PR branch and compared by `git hash-object`
against the GitHub API blob SHA. No user Windows reports, accounts, SQLite
or live API calls were used. The test fixture now contains ONLY an
explicitly invalid synthetic payment-card-like digit sequence.

Command: `python -B -m unittest discover -s . -p 'test_*.py' -q`
executed from a self-contained directory containing the exact seven files.
Result **39 tests, 0 failures, 0 errors, exit0**, including:

- Exporter tests, including 72,900 malformed field combinations;
- the reviewed-noise filter and a genuine synthetic file
  `redact_daily.main` → disk → digest → `consume_preview.validate`
  → baseline check;
- chronological newer-activity and audit-withdrawn ID-only recheck;
- duplicate nested JSON field, nonfinite/exponent overflow, deeply
  nested JSON, UTF-8 BOM, UTF-16/32, and date/same-second replay rejection;
- malformed Unicode surrogate input in event title, primary URL and
  batch ID fails closed PER ROW, without losing a valid neighboring event.

Independent RED/GREEN detail: canonical UTF-8 tests were 3/3 failures
on earlier parser and 25/25 consumer-only green after fix. Invalid
surrogate row test was 1 assertion failure + 2 uncaught encoding errors
before exporter fix, then entire full bridge 38/38 green; one genuine
multi-snapshot two-batch exporter+consumer test then raised full suite
to **39/39**. All source blobs exactly match the current PR branch
(use latest HEAD rather than intermediate commit IDs).

Current Git blob IDs:

- consumer `71bdbd60ce8e4d70e525748b79954bdbd5a9251b`
- exporter `9da3b03349de01d3becb967f9f58f4fee4c43403`
- consumer tests `8d7364c041493a714c724a815dbb244071fa1d2b`
- exporter tests `8457e340fffdf1f40c12ff9d966a3c367562b5c3`
- noise audit tests `c9779ea9545a0b86072411386f4efeacfa3c4882`
- export/consume roundtrip tests `ecab7dda094929f8d4d217e4115353496420b6af`
- chronology tests `abd6bd20b2cb8eabf7fbe21ed80d20f2c1f38193`

**Sensitive-fixture escalation, no confidential value copied here:**
While restoring the exporter tests, independent review found a
payment-card-like numeric literal matching a previously user-supplied
payment credential in the Codex-owned parent PR23 test fixture.
This draft PR has replaced it with an intentionally invalid synthetic
test string, preserving the rejection test. The original base branch
and historical Git commits still contain the old literal. This is a
merge/release PRIVACY BLOCKER until an authorized maintainer coordinates
cleaning active branches and relevant reachable history, preventing
cached or forked copies from propagating. **Do not** put the value in
Issue comments, logs, PR descriptions or test failure output. Do not
force-push or rewrite collaborators' history without explicit
operator approval; replacing the working-tree string is not deletion
from Git history. If any underlying payment card is active, the cardholder
should arrange protective action with the issuer through a private channel.

**Release and daily brief remain blocked:** There is no operator-approved
live sanitized export, trusted writer identity, monotonic signed report
revision, private read channel or recipient's matching-SHA receipt.
Keep `DELIVERY_BRIDGE=OUTPUT_NOT_CONNECTED`; do not claim the 09:30
ChatGPT scheduled brief consumed WoolRadar production output. Whole
WoolRadar Windows integration suite, source P06 field validation and
post-tuning unseen holdout are NOT_EXECUTED for this head.
