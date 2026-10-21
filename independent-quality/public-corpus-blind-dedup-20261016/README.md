# WoolRadar public-corpus selection for an independently reviewed *future* sample

## 2026-10-21 producer identity proof requirement

The sampler now accepts a source row into a **future blind review candidate**
only when the producer explicitly emits `url_identity_preserved: true`.
Legacy rows without the field are excluded under `upstream_url_identity_lost`,
even when `url_sanitized` is false. That old flag alone does not prove that
query parameters or SPA route identity survived an earlier producer.
This is a conservative sampling rule, not a finding that legacy items are
ineligible offers. Keep already-labeled 2026-10-16/17 batches as development
evidence; run a new source collection and independent labeling to claim a fresh
business-quality denominator. Current `core/public_corpus.py` emits the
explicit flag and preserves known functional selectors while redacting risky
ones; private titles/snippets still require manual review before publication.

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
To prevent an apparently new batch from reusing earlier development/review
URLs, supply each prior blinded review JSON with `--exclude-prior PATH`.
Both legacy top-level row arrays and `{"rows": [...]}` review envelopes are
supported. Only URL identities are read; previous labels, scores and collector
`accepted` flags never influence selection. Previous review SHA256 fingerprints
are written to the output, while previous raw URLs are not. Exclusions apply
before per-source sampling limits. Malformed or credential-bearing prior URLs
fail closed instead of silently reducing the exclusion set.
It verifies source identity and raw file SHA, checks UTF-8/JSON syntax
strictly (duplicate object keys, nonfinite numbers, unexpected encoding and
reported row-count inconsistency fail closed), and reads up to 500 public
rows per source, 20 sources and 8 MiB per file.

Within each source, it canonicalizes hosts/default ports but strips only
explicit marketing tracking parameters. It preserves query-based campaign/batch
identifiers and route-like SPA fragments to avoid merging different promotions.
If the original producer has already sanitized away some URL identity, that
row is excluded and counted as lost identity, not called a unique blind lead. All duplicate
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
  --exclude-prior PREVIOUS_BLINDED_REVIEW.json \
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


## Additional actual source-to-sampler compatibility regression

An exact standalone copy of WoolRadar main PR23's
`core/public_corpus.py` (Git blob
`fb1921e5935660eaa29b53a6f8033e7b4b52febf`) and its real
`core/models.py` dependency (Git blob
`f471c178d6adbad1ad85ee4ac3f99a47b231d861`) were executed in a
separate temporary Python3.13 worktree; the two local git object hashes
matched the GitHub blobs.

The producer generated a real on-disk `data/public-corpus/publicfeed.json`
from 3 **synthetic** public source rows: two feed URLs to the same
campaign (differing query parameters) and one distinct URL.
The independent selector read that producer-created file via its CLI and
wrote a new local-only JSON review file on the PRIOR code HEAD:
source input_rows=3, duplicate_within_source=1, retained URLs=2.
**CORRECTION:** The actual core/public_corpus producer had already removed
business query parameters before sampling. Two distinct batches may thus be
mistaken for duplicates. The old test was green but not a trustworthy
business-identity acceptance. Latest code now excludes the two ambiguous
upstream-sanitized rows (and retains the one plain URL) in the same synthetic
roundtrip fixture. No platform request occurred.

Committed formal `test_public_corpus_real_schema.py`, verified local
git blob = GitHub blob
`4de99ac9fa494f6e7f14a0ed29622042534058df`.
Combined isolated standard-library suite now **12/12 PASS, exit0**
(11 selector tests + 1 actual-producer/CLI roundtrip).

**No new real public-source sample was obtained in this test.**
The old source duplicates and old TP0/FN2/TN47/unknown7 remain
historical evidence at their original SHA. New file is only a
candidate data selection mechanism; do not call it an independent
held-out evaluation without a fresh source period, separate human
labeling, and frozen input/label/sampler manifests.


## 2026-10-16 correction: batch identity must not disappear during URL dedup

The old selector removed *all* URL query parameters and fragments.
An isolated Python reproduction using its exact URL-normalizer body found
that two different `?batch=` links became the same key, and two SPA
`#/offer/` routes likewise collapsed. The real production
`core/public_corpus.py::_clean_url` also deletes all queries/fragments
before writing the JSON source sample. No downstream review selector
can recover a missing campaign identifier from that JSON artifact.

Current PR32 update keeps meaningful `batch`, `offer`, `ref` and `utm_campaign` query
pairs, plus route-like `#/offer/...` fragments; strips only recognized
marketing trackers such as `utm_source`, `utm_medium`, `utm_term`, `utm_content`, `fbclid`, and `gclid`; preserve `utm_campaign`; and rejects
known auth-bearing query parameters and unpaired Unicode.
When `url_sanitized=true` indicates the upstream recorder has already
removed some URL identity, the row is excluded from the blind sample
and counted under `upstream_url_identity_lost`. A global
`upstream_identity_fully_preserved` flag stays false until fixed.
This is a conservative *incomplete input* marker, not an assertion
that the omitted opportunities are false or unimportant.

Actual follow-up executed: six targeted Python URL properties passed
on the patched normalizer; before-fix and upstream-producer example
confirmed business-batch collision. Formal updated tests have now been independently EXECUTED on the exact current sampler/test blobs (17/17 PASS exit0); see the latest exact-source verification section below.
The prior 12/12 PASS was on a different older SHA and must not be
reused as a current regression result.

Codex owner action: fix the actual source recorder `core/public_corpus.py`
to preserve sanitized but business-significant query and SPA-route
identifiers, without leaking tokens or raw userinfo, then test real
producer -> independent selector on two DISTINCT campaigns and
marketing-only tracking duplicates. Until then a new truly independent
56+-row or 95%-quality benchmark cannot be certified from this source.


## Verified newest candidate: exact-source 17/17 bridge tests

**Actual 2026-10-16 test run after conservative batch-identity updates:**
Isolated Linux Python **3.13.5**, `python3 -B -m unittest discover
-s . -p 'test_*.py' -v`, **17 tests, 17 pass, 0 fail, 0 error,
exit0**. 16 direct selector/privacy/URL identity assertions plus one
real `core.public_corpus.record_public_sample` producer-to-selector
synthetic on-disk roundtrip. No network, genuine customer data, or
production Windows files used.

All five local test inputs exactly matched current GitHub git blobs:

- `freeze_public_sample_dedup.py`: `725bea4b20ae0d38b76781a25a02447026908380`
- `test_freeze_public_sample_dedup.py`: `b5df1465e200360692bd3df5e2220fdc66f0705b`
- `test_public_corpus_real_schema.py`: `8358e448da69a8ec01dcbf7c2f0ef3d7052d383b`
- Main producer `core/public_corpus.py`: `fb1921e5935660eaa29b53a6f8033e7b4b52febf`
- Main dependency `core/models.py`: `f471c178d6adbad1ad85ee4ac3f99a47b231d861`

The completed producer-level synthetic test intentionally used two
different `?ref=` offer identity links plus one plain URL. The producer
irreversibly removed the first two query values and marked the source
rows `url_sanitized=true`; the revised reviewer excluded both, kept the
unambiguous plain URL and reported `upstream_url_identity_lost=2`,
`upstream_identity_fully_preserved=false`.

**This is a verified fail-closed diagnostic, not a fix to the actual
upstream producer.** Codex main still needs a privacy-reviewed
producer-level semantic query/batch identity fix plus a fresh real
source period and separate gold labeling. No benchmark acceptance
or same-hash 09:30 real brief delivery is proven.


## Current-HEAD exact execution checkpoint — security query red/green

After the earlier 12/12 source-to-sampler run, new business-identity rules
were added, and then the **complete updated formal 17/17 suite** was
actually executed in Linux Python 3.13.5 against exact current PR32
selector/test/integration files (Git blob matches known GitHub hashes):

- selector before adding privacy denial: `725bea4b20ae0d38b76781a25a02447026908380`
- unit tests: `b5df1465e200360692bd3df5e2220fdc66f0705b`
- real core producer synthetic roundtrip test: `8358e448da69a8ec01dcbf7c2f0ef3d7052d383b`
- result: 17/17 PASS, exit 0, 0 failures / errors.

A further privacy counterexample found that the new semantic-query
preservation would also retain common `token`, `auth`, `code`, `sig`,
`email` and `phone` query keys, which can carry credentials or contact
details into the local review candidate file. Before correction, **10/10
sensitive-key subcases failed** their non-disclosure assertion. Rejected
all such named parameters (including fragment forms), while keeping
business-significant `batch`, `offer`, `ref`, `utm_campaign`. The revised
formal suite **19/19 PASS, exit 0**, exact files:

- selector `4ecf0bed60c7f3edd45fd8c17638fafcda085455`
- selector tests `50d3b039aea26e494cec4330dcac64d2ba64d1e0`
- producer roundtrip test `8358e448da69a8ec01dcbf7c2f0ef3d7052d383b`.

GitHub remote file blob equality is verified. This is a **real isolated
Python suite with synthetic inputs**, including exact `core/public_corpus.py`
and `core/models.py` dependencies already blob verified against main PR23.
It is NOT an end-to-end Windows, 09:30 ChatGPT, real independent new
corpus, unknown-credential-field privacy certification, or true distinct
campaign metric. A human still needs to inspect even public snippets for
personal content; new samplers never auto-upload.

Important: Codex main PR23 integrated an OLDER sampler revision (blob
`03496b3a4067947e3ee5825303ae060abb369115`). Current PR32 is
a DIVERGED review-only delta on an outdated base, not a PR that can
blindly replace Codex's branch. The main owner must selectively integrate
the new safe URL changes AND separately fix real `core/public_corpus.py`
producer query/fragment identity erasure under the active V3 lease.
Until that upstream fix, the new sampler excludes any previously
`url_sanitized=true` records rather than inventing distinct counts.
