# Historical noise audit (opt-in candidate)

This implements the existing P06 report-audit TODO. It does not collect new data,
change notifications, delete database events/evidence, or infer claim eligibility.
The current production installation is unchanged. Review this isolated candidate
before integration; it is parallel to the collector/holdout work in PR13.

## Explicit operations

Use an existing isolated database copy. The mutating audit command requires an
explicit `--root`, and refuses to initialize a missing database. Replace the sample
event ID with an event that was actually reviewed. The reviewer name is an audit
label entered by a trusted operator, not cryptographic identity.

```powershell
python -m core.cli --root C:\WoolRadar-Review audit-noise 1 --decision exclude --reason "Reviewed diagnostic discussion, no offer" --reviewer "reviewer-name"
python -m core.cli --root C:\WoolRadar-Review report --date 2026-10-15 --noise-audit C:\WoolRadar-Review\data\noise-audit.json
```

To correct a review, append a restore decision; original audit history is retained:

```powershell
python -m core.cli --root C:\WoolRadar-Review audit-noise 1 --decision restore --reason "Review correction" --reviewer "reviewer-name"
```

Reports without `--noise-audit` retain existing behavior. No automatic production
activation, service installation or scheduled-task change is part of this patch.

## What is excluded and what is preserved

- Only a matching event/batch identity and substantive evidence fingerprint can be
  excluded from Markdown activity sections. The audit section still shows the item,
  event ID, reason, reviewer and review time.
- JSON retains **all** original events and evidence, with `report_audit` per event,
  a filtering summary and the exact audit-snapshot SHA-256. JSON consumers must check
  `report_audit.excluded` when selecting visible activities; records are not erased.
- Event identity includes canonical key, batch and primary URL. New campaign batches
  are not covered by a prior exclusion.
- New evidence kind/URL/provenance/excerpt/claims or changed event metadata makes an
  old decision stale, restoring visibility conservatively. Merely changing observation
  or evidence-check timestamps does not prove a new offer or genuine reopening.
- A real reopening needs substantive evidence, a new batch, or an explicit reviewed
  restore. The system does not infer reopening from a rescan timestamp alone.
- Identical repeated decisions are no-ops; corrections append records. The sidecar
  is separate from the database and the API does not delete or rewrite evidence.

## Persistence and concurrency

Ledger schema version 1 is validated before a filtered report starts. Corrupt input
stops generation instead of silently dropping the exclusions. Writes use a kernel
lock and fsynced temporary-file replacement. Process exit releases the writer lock;
a live writer yields `NOISE_AUDIT_BUSY` rather than concurrent overwrite.

The `.lock` file normally remains on disk; its existence does not mean it is locked.
Do not unlink a live lock file to bypass contention. A report uses one validated
in-memory ledger snapshot, so concurrent reviews cannot mix two audit versions in
one report. Windows/local filesystem behavior is tested; network-share semantics
and production long-term operation are not claimed.

## Evidence

Implementation commit: `c633cd88e45be2b4a14cccd0306ed5572159d8f6`.
Windows command: `python -X utf8 -m unittest discover -s tests -v`:
158 tests, exit 0, zero skipped, including 10 new audit regressions. Real CLI and
temporary SQLite tests cover evidence retention, restore, fresh substantive evidence,
same-content repeat ingest, new batches, corrupt ledgers, crash locks, live-writer
exclusion and one-snapshot reports. Later documentation-only commits do not change
the tested Python implementation.

See `evidence/noise-audit-20261015/` for logs, exact SHAs, V3 sync receipts, review and
before/excluded/fresh-evidence synthetic reports. These reports are illustrative,
not real campaign judgments or production precision/recall measurements.

## V3 continuity

Every active continuation cold-reads the project/coordination Issues, current PRs,
state SHA, owner, lease, fence and scope. Significant code and test results are saved
on this independent branch and state checkpoints are acknowledged remotely.
After an interruption, an expired own lease was explicitly recovered before new
publication. No other Agent's scope is taken over. At exit, evidence and next review
are recorded and ownership released. No model call after quota exhaustion is needed
to reconstruct already saved code or replay saved events.
