# Windows fixture repair and candidate compatibility checkpoint

Base: PR19 c1c8adc2022ef634b266299d7d81a5e4d0353a68. Only two test-owned raw SQLite connections now close explicitly. The snapshot writer still enters its transaction context, preserving commit/rollback. Assertions remain unchanged.

Before: the isolated unmodified PR19 runtime reproduces 2 WinError32 cleanup errors among 6 migration tests. After: 6 pass, full PR19 runtime plus fixture repairs 208 pass. Separate temporary composition with PR13 collector and PR14 noise/CLI/report: 228 pass. Exact commands and exits are in JSON. This is not a Git merge, production deployment or 95% quality acceptance.

Independent compatibility review reproduces P1: per-candidate ingestion is not atomic after upsert; concurrent campaign review can delete the event before evidence insertion. New official zero-capacity proof may be lost. That application defect is not repaired by this test-only PR; a separately scoped candidate must follow. Independent review and before-failure evidence remain included.

Original P06 remains incomplete. No production database, scheduler, account, network policy or paid API changed. Historical snapshot manifest describes the original baseline only. Raw local temp paths are redacted from shared output. Source-vector JSON records the original temporary composition before the two fixture repairs; current fixture hashes are in delivery-manifest.json.
