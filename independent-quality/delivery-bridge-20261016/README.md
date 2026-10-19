# WoolRadar → daily ChatGPT brief: offline preview boundary

**Status:** isolated proposal / local-only synthetic tests passed. **Not** a real production export, published feed, verified live offer, user-specific eligibility, or completion of the DELIVERY_BRIDGE acceptance gate.

This proposal is stacked onto the exact WoolRadar integration PR #23 head `719d87719eef171dbcb8472743d38d5461b8c9ab`, without changing `core/`, production report generation, Windows scheduling, notification channels, SQLite files, or existing Codex working branches.

## Why this is necessary

`core/report.py` writes `reports/{date}-daily.json` including all events, evidence excerpts, raw metadata, node runs and notification rows. Never publish that raw file in GitHub, ChatGPT, a gist, or a workflow artifact.

`redact_daily.py` is a **human-invoked local preview only**. It imports no WoolRadar runtime modules; reads only an **explicitly supplied** daily JSON; never contacts a network service; never reads accounts/tokens/DB/notifications directly; does not modify the raw report; creates a new output file with no overwrite and restrictive local mode (0600 on POSIX); and prints only counts.

Example from the repository root, **only when a human deliberately chooses an already produced local report**:

```sh
python independent-quality/delivery-bridge-20261016/redact_daily.py --input path/to/2026-10-16-daily.json --output path/to/2026-10-16-redacted-PREVIEW.json
```

This example is **not** an instruction to install/deploy or automatically upload anything. The consumer endpoint and publication decision have not been implemented or approved.

## Output contract (schema v1)

- `source_type=LOCAL_REDACTED_PREVIEW_NOT_PUBLISHED`, `runtime_provenance_verified=false`, `public_application_live_verified=false`, `requires_operator_review_before_sharing=true`
- `report_date`, `generated_at`, raw-report SHA256 digest (integrity fingerprint, **not** a signed provenance attestation), exported/skipped counts
- Per event: derived stable URL+batch hash, public-facing title, HTTPS URL without query or fragment, original **reported** status (not an open-now assertion), `publication_lane=independent_official_recheck_required`, `personal_eligibility=UNKNOWN`, hashed batch ID, timestamps, narrow official evidence URLs/checked times, strict boolean/card/account/renewal flags, controlled region label, nonnegative integer remaining and parseable expiry
- No `metadata_json`, `node_runs`, `notifications`, `report_audit`, `sightings`, original event IDs, evidence excerpt/claims free text, account identifiers, cookie values, private filesystem paths, or backend error messages. Community evidence is not promoted to official evidence.
- **Noise-audit exclusion gate:** the production JSON retains all events for its internal evidence ledger, including rows excluded from the Markdown. If the report has a `noise_audit` summary, only event rows with an explicit `report_audit.excluded is false` boolean are exported. Missing, malformed, or excluded decisions are skipped. In older reports without a global audit summary, an explicit event-level exclusion is still respected. This prevents previously reviewed spam/scam/non-offers from reappearing in a downstream brief.
- Any unknown source field is silently discarded. Unsafe URL (query/fragment, credentials, local/IP, suspicious path), title containing common secret/email/phone markers, unrecognized status, bad batch, missing official timestamp or non-HTTPS evidence is skipped or degraded. Some legitimate deep links will be omitted intentionally.
- The stable hash distinguishes explicit batches for the same URL; **it is not** a campaign deduplication oracle across different URLs. Events which do not pass checks count as skipped.

**Never** infer a user's eligibility, remaining active inventory, or newly opened offer from `reported_status=CLAIMABLE`; this is historical reported data only. Every proposed item needs fresh primary-source review before appearing as a confirmed public application in the daily brief. `source_type` cannot be upgraded to a verified runtime export by renaming a file or adding an untrusted flag.

## Isolated tests

```sh
python -m unittest discover -s independent-quality/delivery-bridge-20261016 -p 'test_redact_daily.py' -v
```

Eleven standard-library unit tests cover: raw notification/metadata/excerpt non-disclosure, denial of sensitive URL forms and title markers, actual official evidence provenance field restriction, rejection of wrong types, duplicate and batch separation, invalid dates/status fail-closed, no personal eligibility upgrade, and explicit local CLI output with no overwrite. A deterministic malformed-input matrix additionally covers 72,900 combinations of odd status/title/URL/batch/evidence types without an uncaught exception. Two additional red/green regression tests cover global and per-event noise-audit exclusions (the unfixed exporter returned excluded rows). They use only synthetic fixture data. Test counts and the exact code blob hashes are recorded in the draft PR; **no Windows production report was read and no end-to-end ChatGPT consumption was executed**.

## Remaining release gates

1. Independent privacy/security review of title/path/URL leakage (heuristics are not a complete DLP guarantee); if necessary strengthen allowlists and operator approval.
2. Real read-only Windows test on a separately authorized, sanitized report copy; check schema compatibility and compare exact source report SHA. Do not upload raw data or produce GitHub artifacts that expose it.
3. Establish signed/verifiable runtime identity, controlled publication approval and a stable private read channel. Until then ChatGPT daily brief must explicitly say `OUTPUT_NOT_CONNECTED`.
4. Consumer validation: reject absent/future/stale/untrusted snapshots, repeat provider checks, preserve unknown region/card/account qualifiers, prevent duplicated campaigns and old batches from being presented as newly open.
5. Independent actual business-quality holdout, P06/five-source field operation and three post-acceptance reviews remain outstanding.

No paid API, Codex execution, Work, production deployment or account operation is required by these tests.


## Read-only consumer gate (not a published brief)

The additional `consume_preview.py` accepts only the local unverified preview schema.
It requires a precommitted SHA-256 digest supplied independently of the file; the
digest is not a runtime signature or proof of approved sharing. Production callers
MUST NOT just copy the digest out of the untrusted file itself.

Strict checks reject unknown/private extra fields, malformed counters, repeated
event keys, falsely promoted account or runtime verification flags, stale/future
generation times and invalid Asia/Shanghai report dates. No automatic network
read, upload, GitHub artifact publication or ChatGPT background ingestion occurs.

A first approved preview produces only `BASELINE_ONLY` with zero new candidates.
Comparing two individually verified previews produces only changed event keys
under `MANUAL_SOURCE_RECHECK_REQUIRED`; it deliberately never outputs
publication-ready offers or open-now/account-eligibility assertions.

Manual invocation on an already approved sanitized preview:

```sh
python independent-quality/delivery-bridge-20261016/consume_preview.py --input explicit-preview.json --sha256 INDEPENDENT_PRECOMMITTED_SHA256
```

Isolated validation: 19/19 Python standard-library tests passed, exit 0:
11 exporter checks (including 72,900 malformed-field combinations), seven
consumer guard tests, and one real synthetic file export-to-consumer roundtrip.
Three new GitHub file blobs matched the local tested files' git object hashes.
This is NOT a Windows production-data test or an authenticated trusted channel.
Until independent approval and a read-only source are in place, keep
`DELIVERY_BRIDGE=OUTPUT_NOT_CONNECTED` and continue verifying public links
independently for the daily ChatGPT brief.

## Integration verification on 2026-10-16

The exact PR #26 base (45237d1fa737e722acf6d4086e6c13b6c59c713f,
which contains PR #23) ran as one Windows unittest suite: 299 tests, exit 0.
Additional boundary contracts reproduced encoded account/login/token routes,
consumer value-validation gaps and missed same-key content revisions. The
producer now checks recursively decoded routes; the consumer independently
enforces the same safe URL/title/claim values. UTC conversion overflow is
rejected. Changed status, title or official evidence queues the same event key
for manual review; proof list order alone does not count as a revision.

A previously sanitized 110-event historical SQLite copy was cloned locally and
processed by the current real ReportGenerator, exporter CLI and consumer CLI.
102 records passed export before a deliberately synthetic exclusion, 101 after;
the first consumer snapshot emitted zero candidates. Integrity/FK checks passed.
The controlled exclusion is a test, not a human business approval. Raw reports,
databases and the actual preview remain local and are excluded from GitHub.

This supersedes the earlier synthetic-only test status above, but **does not**
establish production deployment, trusted publication, live source accuracy or
ChatGPT scheduled consumption. DELIVERY_BRIDGE remains OUTPUT_NOT_CONNECTED.
Shared evidence contains counts, commands and code hashes only.
