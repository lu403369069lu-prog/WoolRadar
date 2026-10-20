# P06 new-window public-corpus sampling / prior review exclusion

Date: 2026-10-20 (Asia/Shanghai). Scope: isolated Windows engineering only.

An eight-source, public-only local production-corpus snapshot from 2026-10-20
was consumed **read only** by the existing offline freezer. Source files were
SHA256-checked before and after the initial capture and were unchanged. The
initial 60 candidate rows had 18 exact-URL matches against the older 47-row
October 17 review and 2 against the October 16 legacy 56-row review. These
overlaps show why a newly sampled file is not automatically an unseen holdout.

The freezer now accepts repeatable `--exclude-prior` JSON inputs; it rejects
unsafe/malformed prior review URLs, reduces them to canonical URL identities,
keeps only SHA256 fingerprints of the prior input files, excludes old URLs before
sampling caps, and records per-source exclusion counts. Neither labels nor
upstream acceptance decisions are used for choosing candidates.

Using the same unchanged eight source files, and both prior blinded reviews,
the new private candidate sample contains **54 rows, 54 unique URLs, zero
exact-URL overlap** with the two earlier blinded sets. The two prior sets
contained 100 distinct canonical URLs. Source audits also report **76 upstream
URL-identity-loss rows**; the global `upstream_identity_fully_preserved` value
remains `false`. Different URLs may still be the same campaign, and source
availability and mainland-China eligibility require independent adjudication.

Windows isolated test command (with isolated writable TEMP, pinned read-only
Digest upstream and project PYTHONPATH):

`python -B -X utf8 independent-quality/delivery-bridge-20261016/run_combined_tests.py`

Result: **499 tests / 0 failures / 0 errors / 0 skips / exit 0**.
The local test log SHA256 is
`06c41dc0f9113d43b410994c2e2cb439cfc1c510a66998263eccf409ce4a641b`.

Local-only evidence: `_outbox/p06-new-window-20261020-1545/` contains the
source fingerprint manifest, two raw-free aggregate audit files, the source
selection implementation tests, and private candidate output. The private
candidate JSON, original public-corpus JSON, and complete command logs were
**not published to GitHub**. The new output is `NO_LABELS`, not a human-reviewed
independent gold set. No raw SQLite, production reports, credentials, external
notifications, system tasks, API registrations, Work sessions or PR merges.

Outstanding business gates: new 54-row independent human labeling and
official proof of offer, date, quantity, payment, country and qualification;
five-node P06 recall including upstream identity-loss exclusions; verified
09:30 real consumer receipt (`OUTPUT_NOT_CONNECTED`); W1–W7/final three rounds.
