# SAM Windows / POSIX historical acceptance split, 2026-10-17

**event_key:** `history-80-batch/SAM-platform-specific-glob-and-symlink/20261017`

## Independently verified current-code facts

This is a read-only static cross-check of all **19 distinct formal test files** named by the 21 `READY_FOR_LOCAL_CODEX` SAM family jobs in `HISTORICAL_80_PERCENT_CODEX_JOBS_20261017.json`, against SAM Draft PR15 exactly at commit `82bf36efa90cced8dafb56502812eb49f40515f3`. For each file the original GitHub blob was directly read; this is **not a Windows execution**.

1. `SAM-H06` → `SAM/independent-review/20261016/glob-ripgrep-572-matrix.test.ts` explicitly has `skip: process.platform === 'win32'`. It executes **572 comparisons** on POSIX (26 source globs × 22 fixture paths), but **zero of these comparisons** on Windows.
2. `SAM-H18` → `SAM/independent-review/20261016/glob-case-parity.test.ts` explicitly has `skip: process.platform === 'win32'`. The test's Linux case-distinct fixture tries both `private/` and `PRIVATE/`; they cannot be treated as independent case-distinct roots on typical default Windows case-insensitive filesystems.
3. `SAM/snapshot/test/canonical-fail-closed.test.ts` and `SAM/snapshot/test/source-qualified.test.ts` create junctions/symlinks; each may call `t.skip` when the OS test environment lacks the required permission. `rooted-source-authorization.test.ts` uses `junction` on Windows and `dir` on POSIX but does not otherwise explicitly skip in its source.
4. Source `SAM/snapshot/src/source-policy.ts` Git blob `0cb6ead5e4764aa8b7364ba92d3137b0b8171f5b` currently uses case-sensitive `RegExp` on POSIX and case-insensitive `RegExp` on Windows. This Windows behavior is still **assumed**, not verified against the actual Windows `ripgrep` version/filesystem. Previous Linux 572 comparisons pass and are **not** evidence for Windows.

## Required Codex handoff: two environments, never hide skips

**Windows native Node 24, then 26**: on disposable exact-SHA checkout:
- `node --version`, `rg --version`, `npm run build`, `npm test` and the 21 family targeted tests; preserve exit, tests passed/failed/skipped and exact build/tree SHA.
- Probe symlink/junction privileges in a disposable temp directory only, never operating-system production paths.
- **Do not claim all 21 SAM families Windows-PASS** from the original source: at least H06/H18 are explicitly skipped by current formal tests. Our strict family receipt guard intentionally returns NOT_ACCEPTED for such an incomplete platform suite.

**Linux or isolated WSL Node 24/26 (same immutable source SHA)**:
- Run `node --import tsx --test ../independent-review/20261016/glob-ripgrep-572-matrix.test.ts ../independent-review/20261016/glob-case-parity.test.ts` with cwd `SAM/snapshot`.
- Check real `rg --version` and log original **POSIX 572 comparisons** and case parity controls; any skip due missing ripgrep remains PARTIAL, not PASS.

**New Windows-native test needed, not yet implemented/green**:
- Create a new isolated synthetic Windows filesystem fixture that avoids simultaneous file names differing only by case. Test `secret.txt` against an actual `Secret.txt`, `private/**` against actual `PRIVATE/one.txt`, rooted `/path`, `? / [] / { } / **` grammar, and both nested and leaf patterns. For each pattern, compare actual `isExcluded` against installed `rg --files --hidden --no-ignore -g !<pattern>` in the exact same directory.
- If Windows rg behavior differs, propose a *minimal* correction to `source-policy.ts`, retain POSIX strictness and rerun all existing 572 comparisons. Never invent compatibility based on assumed Windows defaults or hand-edit private source gold.
- Commit code and exact red→green tests to an authorized independent Draft branch, not the Codex V3-owned main PR; keep the existing PR15 SHA baseline intact until independent integration review.

## Mechanical acceptance boundaries

- The **42-family target runner and guard** refuse `PASS` on skipped tests, full skipped suites and missing traceable log bytes. This is intentional and must not be removed to make Windows claim success.
- Local native Windows suite success is separate from Linux rg correctness, MCP direct/stdio correctness, semantic source-gold correctness and skill install/upgrade/rollback.
- Expected final evidence: `project | exact immutable SHA | environment (Windows/WSL) | Node/Python/rg versions | exact command | exit | pass/fail/skip | log SHA256 | family coverage | human reviewer`. If any item unavailable, mark it `NOT_VERIFIED`.
- No user personal PLC/TwinCAT source, production Windows installations, paid runners, credentials or GitHub merges. `historical_recovery_closed=false`.
