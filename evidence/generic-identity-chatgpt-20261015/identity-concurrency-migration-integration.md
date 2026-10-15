# WoolRadar PR #19: identity, concurrency, migration-preview integration

2026-10-15 — ChatGPT interactive continuation, **not** a Scheduled run.

## Scope and test provenance

The fixed branch is `chatgpt/wool-generic-compact-quantity-20261015` (draft PR #19, stacked on draft PR #18). This changes only source code, synthetic tests, and this evidence file. No production database, Windows scheduler, or real user accounts were accessed.

Local isolation: Linux Python 3.13.5, standard library `unittest`, temporary SQLite. Repo source was retrieved via the authorized GitHub connector. The unchanged `core/dedup.py`, `core/models.py` and original seven-test `tests/test_generic_quantity_identity.py` were copied byte-exact and validated using `git hash-object` before local execution. For testing SQLite, `core/db.py` was **not cloned in full**; its real schema, connection, `upsert_candidate`, `get_event`, `list_events` and proposed `preview_reindex` implementations were copied into a restricted isolated harness, leaving unrelated methods out. Consequently, the result **is not a whole-project/complete-repository test**.

Commands:
```
python -m unittest discover -s tests -p 'test_generic_quantity*.py' -v
python -m unittest discover -s tests -p 'test_concurrent_upsert.py' -v
python -m unittest discover -s tests -p 'test_reindex_preview.py' -v
python -m unittest discover -s tests -p 'test_*.py' -q
```

## Independently reproduced faults / actual fixes

1. **Compact vs spaced resource sizes**: Same vendor and exact landing URL, `Free VPS 1GB` vs `Free VPS 1 GB`, previously produced different keys and duplicate `notify=True` events. Additional seven-case suite **before 3/7, four failures, exit1; after 7/7, exit0**. Only generic-sized headings canonicalize 1GB/1 GB, 512MB/512 MB, and 1TB/1 TB. Branded historical title keys are deliberately not globally rewritten; different vendors and quantities remain separate.
2. **Concurrent collectors**: Existing `Database.upsert_candidate` performed an initial SELECT followed by an INSERT. Synchronizing two independent SQLite threads to reach the second-stage INSERT for the same `(canonical_key,batch_id)` reliably raised `sqlite3.IntegrityError: UNIQUE constraint failed: events.canonical_key, events.batch_id`. Replaced this check-then-insert with `INSERT ... ON CONFLICT(canonical_key,batch_id) DO NOTHING`, then fetches the event ID; only `cursor.rowcount==1` results in initial notification. New concurrency suite **four scenarios passed after repair, exit0**: same campaign concurrent insert, different vendor separation, simultaneous 1GB/1 GB title formats, distinct batch notifications. One true event, both sightings retained, exactly one `notify=True`.
3. **Historical canonical-key upgrade risk**: A synthetic database retaining the **prior** spaced-size key `813ccccaf9c4ebe91f9c11b4` while new processing produces `aee5f5d2516f94ebeec92f41` yielded **two events and two initial notifications** without explicit migration. This is an **unresolved deployment compatibility issue**, not a fixed historical DB. Added `Database.preview_reindex()` as read-only URI `mode=ro` inspection reporting event counts, changed keys, would-be merges, collision groups and overlapping notification keys. The three preview tests **3/3, exit0**, verifying no mutation and detecting an overlapping historical notification. **Preview cannot reconstruct already-wrongly-merged old events** or predict a new manual campaign review not yet registered.

## End-of-round isolated result

**21/21 pass, exit0**: 7 pre-existing PR#19 regressions + 7 compact/spaced tests + 4 concurrency tests + 3 migration-preview tests. The remote `tests/test_reindex_preview.py` blob is `50b8d6b9f408d6db68a17cb55246e1ebd161d6ac`, matching local tested bytes. Remote modified `core/dedup.py` blob `61f8f6eee57f2c8f4472ef7707851a5109788e6c` also matches local tested bytes. The remote `core/db.py` contains additional unrelated production methods; **the complete updated file is not byte-identical to the extracted test harness**, and has not been imported/run in a complete checkout.

## Hard acceptance gates / next exact action

- Get a complete isolated checkout of exact PR#19 head (including `core/db.py`, `core/verifier.py` and test dependencies) and run `python -X utf8 -m unittest discover -s tests -v` on Windows (plus available Linux). Log exact exit, denominator, skips, stdout, SHA.
- Create and test an approved **copy-only** historical database migration/rollback exercise. Use `preview_reindex` on the copy, compare predictions with actual `reindex`, verify `events/sightings/evidence/status_history/notifications` and notification idempotency; do not mutate the live DB. Provide policy for historical cross-vendor rows whose original distinction may already have been lost.
- Audit PR #15→#16→#17→#18→#19 as a single dependency chain and compare with separate PR #13/#14 work before any integration. Existing V3 `needs_approval` and `remote_takeover_allowed=false` states on Codex-owned tasks must not be overwritten or mistaken for authorization to deploy/merge.
- This is a **draft implementation awaiting broader tests and safety approval**, not a claim of product release or 95% quality certification.

Original evidence is in the source/test code commits and isolated receipts; no Scheduled-origin marker is claimed.

## Continuation: consistent migration preview under concurrent WAL writers

`Database.preview_reindex()` originally used separate SELECT statements without an explicit read transaction. Even with URI `mode=ro`, a concurrent writer can commit between `events`, `campaign_links` and `notifications` reads; preview then attributes **different moments** to one migration plan. This can over/underestimate duplicate historical notifications and makes rollback planning unreliable.

Isolated Linux Python 3.13.5/SQLite actual source-method reproduction used a test-installed SQLite connection subclass. After the initial events SELECT, a second real WAL connection committed a notification for a colliding legacy/new event; no network or real user data was involved. Added `with closing(sqlite3.connect(...))` and explicit `BEGIN` before the first SELECT so all three queries share one reader snapshot, while allowing WAL writer commits.

Actual before/after on the same isolated fixture:
- Before (`test_reindex_snapshot.ReindexSnapshotTests.test_concurrent_writer_not_visible_halfway_through_preview`): **1 test / 1 failure, exit1**; `notification_conflict_count` unexpectedly observed 1 from a later transaction while event rows belonged to earlier snapshot.
- After: **1/1 passed, exit0**; preview sees coherent historical state while actual database ends with both notification rows.
- With all isolated tests, **22/22 passed, exit0**, command `python -m unittest discover -s tests -p 'test_*.py' -q`, elapsed 0.053s.
- GitHub test file `tests/test_reindex_snapshot.py` remote blob `3854fcc4e003dfc54974427d66bd084acbd7941d` is **identical to the locally executed test file** (`git hash-object`).
- Updated full GitHub `core/db.py` remote blob `6a72fd385f4db9c5b8188d05aa0bb8dadd243371`. **Full DB module is still not imported by this isolated harness**, which copies the actual schema/connection/upsert/get/list/preview methods; unrelated DB methods are not tested or claimed working.

This is still only a read-only PREVIEW and **does not perform an actual copy-only historical reindex**, a release or a full-Windows suite. Next check must compare preview against `Database.reindex` on an isolated copy, including evidence, sightings, status_history, notification records, backups and rollback, then merge/acceptance decisions through existing draft chain.
