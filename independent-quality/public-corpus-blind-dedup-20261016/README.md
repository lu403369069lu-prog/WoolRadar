# WoolRadar public-corpus selection for an independently reviewed *future* sample

**Base**: Main integration PR #23 exact SHA `e3b31af746776bf976aba7418fce06ff2ae2ccde`.
**Scope**: offline isolated review helper only; no change to production sampler,
sources, filters, scheduling, SQLite, GitHub uploads or user accounts.

## Why

Frozen evaluation evidence from 2026-10-16 has **56 rows but 53 distinct URLs**.
The true rows S046/S047 point to one underlying GitHub open-source funding
campaign. Existing `FUND_ADJUDICATION.json` documents a within-source
duplicate-URL queuing issue and says the historical `freeze_quality_sample.py`
must be corrected, while that original local sampler is not present on the
current main PR tree. Therefore **this code cannot claim to be an exact
patch to, or reconstruction of, the uncommitted historical sampler**.
Neither source/label file nor previously frozen output is modified.

## Offline selection procedure

`freeze_public_sample_dedup.py` accepts only explicitly named, public-only
JSON source files following the `core/public_corpus.py` schema.
It verifies source identity and raw file SHA, checks UTF-8/JSON syntax
strictly (duplicate object keys, nonfinite numbers, unexpected encoding and
reported row-count inconsistency fail closed), and reads up to 500 public
rows per source, 20 sources and 8 MiB per file.

Within each source, it canonicalizes URLs conservatively by lowercasing
host and removing queries/fragments/default ports. It discards malformed
URLs, credentials and rows missing public title/summary. All duplicate
URLs within a source are discarded *before* the per-source 8-row cap.
Cross-source URL ownership is established over the **whole source's unique
candidate URL set**, not only its chosen rows, so duplicates omitted due
to the first source's cap cannot reappear in another source.
Source ordering and URL hash ordering are deterministic and reproducible.

`accepted` classification from WoolRadar is deliberately **not** read to
choose candidates; no gold truth label or estimated precision/recall is
written. The output purpose is `LOCAL_ONLY_REVIEW_CANDIDATES_HOLDOUT_UNVERIFIED`:
being newly generated does NOT prove it is genuinely unseen, independent,
qualifying or that the classifier is accurate. Different URLs can belong
to the same campaign; human adjudication and a fresh held-out period are
required before any 95% business-quality claim.

## Local, explicitly approved usage

```sh
python -B independent-quality/public-corpus-blind-dedup-20261016/freeze_public_sample_dedup.py \
  --input APPROVED_PUBLIC_CORPUS_1.json --input APPROVED_PUBLIC_CORPUS_2.json \
  --per-source 8 --output NEW_LOCAL_REVIEW_CANDIDATES.json
python -B -m unittest discover \
  -s independent-quality/public-corpus-blind-dedup-20261016 -p 'test_*.py' -v
```

Creates a previously nonexistent local file using restrictive permissions
(0600 on POSIX); never overwrites an existing file or automatically publishes
source titles/snippets. Even a public feed can contain identifying details:
operator MUST review the resulting local file before any sharing.
Stdout prints aggregate candidate count only, not URLs or snippets.

## Actual executed isolated verification

Linux Python 3.13 standard-library unittest: **11/11 passed, exit 0**.
Cases cover within-source URL duplicates, cross-source duplicates despite
the cap, stable source ordering, never selecting on historical `accepted`
labels, malformed row quota, different-URL campaign caveat, invalid source
identity, credentialed URLs, bad UTF-8/nonfinite/duplicate source fields
and CLI non-overwrite/restrictive permissions.

Exact tested local Git object SHA matched GitHub after commit:

- selector: `03496b3a4067947e3ee5825303ae060abb369115`
- tests: `2104949658f54eaa009b186c83ba510cb4ef3012`

**Not tested**: real Windows public-corpus JSON/actual new unseen provider
samples, exact historical local sampler reproduction, real source live
eligibility or 09:30 ChatGPT brief handoff. Old 56 rows remain TP0/FN2/
TN47/unknown7 at their own exact old code SHA and never become a new
independent blind acceptance set. No deployment, PR merge, Work, Codex
quota, paid API, real account, source registration or data upload.
