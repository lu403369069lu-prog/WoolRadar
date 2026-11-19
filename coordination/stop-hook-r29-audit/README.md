# Stop hook R29: paused/resumed session boundary audit (2026-10-22)

Scope: executable regression against the **currently installed** `C:/Users/lh/.codex/hooks/stop_verify.py`, followed by an **isolated copy** of that module in this folder. No installed hook or project production code was modified.

Installed module at audit: SHA-256 `A3AA3707C401C227C82A620BF1B1BA21DA1445F1B862CB08273D3EE350C092FA` (R28). The installed PowerShell wrapper `stop_verify.ps1` remains unchanged. The cases use synthetic `Stop` events, handoff JSON and local rollout JSONL files under workspace-safe temporary directories, with an exact session binding, pending requirement and actionable next step.

## Reproduced defects

1. Active session, earlier `继续干`, latest user `现在先别干了`: installed gate returned **block** (violates newest explicit pause).
2. Active session, earlier `继续干`, latest user `先不要继续执行`: installed gate returned **block** (same error).
3. Paused session with retained `pending_requirements`, latest user `继续干`: installed gate returned **allow** (old persisted `paused` disposition wrongly wins over latest explicit resume).

Original module: **8 cases, 3 mismatches**, RED oracle runner exit 0 after asserting exactly three mismatches, `baseline-red.json` SHA-256 `60D19D4882AF56CFF83C1085889BE0826ECFAF936F6E61ACC174125BF8CFAE30`.

The separate R29 candidate expands direct pause-command recognition with explicit whole-task boundaries and detects a latest resume before honoring persisted `paused` disposition. Same script and synthetic fixtures: **8/8 expectations met, 0 mismatches, exit 0**, `candidate-green.json` SHA-256 `02F3EFED0F1065C5A0BA983775383136B3324FBDFF6DA7C4683E94CE62D75232`.

## Reproducible files

| File | SHA-256 |
| --- | --- |
| `audit_stop_resume.py` | `5BE75A13DDFFEF781B5D72971B744B0340C20586B80DD7DD8DA7F301E8C4B3C3` |
| `stop_verify_candidate.py` | `C2A7CDB6573D5046ADAE3B1B8D060F3A38E6A4C8F03BA56D20FFAB099C071B85` |

Windows Python from `C:/Users/lh/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`:

```powershell
python -B -X utf8 audit_stop_resume.py C:/Users/lh/.codex/hooks/stop_verify.py --expect-mismatch 3 --report baseline-red.json
python -B -X utf8 audit_stop_resume.py stop_verify_candidate.py --expect-mismatch 0 --report candidate-green.json
```

Both successful invocations returned exit 0. An initial attempt failed with `WinError 5` because Windows' sandbox TEMP directory was not writable; the fixture generator was then changed to use the writable workspace. The failed first invocation is not counted as a successful test.

## Handoff / limits

Candidate remains an isolated review artifact, not deployed as the active global hook. Test oracle covers these eight synthetic scenarios, not all colloquial pause/resume phrases, all Codex transcript encodings, or real native host Stop dispatch. Before installation, run the current full R28 suite, live wrapper tests with writable TEMP and a real host Stop event; preserve backup/rollback and re-read the installed SHA afterward. The prior R28 report establishes only its own 28-case coverage and four wrapper cases.

The WoolRadar PR #115 independent review finding about `git status --porcelain` missing `assume-unchanged` / `skip-worktree` is separate and likewise requires its responsible owner to reproduce, repair and rerun exact-HEAD tests before promoting R7 proof.

## R29 independent rerun and legacy-suite compatibility

2026-10-22 rerun on the unchanged installed R28 SHA and isolated R29 candidate:

- New eight-case oracle: installed R28 **5/8 correct (three expected mismatches)**; R29 **8/8 correct**. Both commands exited 0 because the installed-control runner explicitly expects three mismatches and the candidate runner expects zero. Reports are `recheck-red.json` and `recheck-green.json`, same content digests as the original reports.
- Existing `hook-candidate-20261022/test_stop_candidate.py` complete regression suite, with Windows `TEMP`/`TMP` redirected to a writable audit scratch directory: **installed R28 28/28 PASS/exit 0**, log SHA256 `542A5A604588DACB0102D432299E8AA5B0C1E933D5A7686EABCE467101B38725`; **R29 candidate 28/28 PASS/exit 0**, log SHA256 `83F6F5DB4B5B800602D29234ADAA831A45E65A13AA99D843982C144C356BE1D3`.
- PowerShell wrapper re-read unchanged at SHA256 `10D3A25753FE179D73FD1FA6472ADA688EEEA86239C6C5E916A36B3003FCEFF7`. Running the legacy suite against Python evaluator does not establish full real-host Stop callback coverage or a live R29 wrapper test. Global installation and operational sign-off remain deferred.

The same host has owner-owned WoolRadar and SAM active sessions. Global hook deployment requires independent review of ambiguous natural-language commands, backup, wrapper/host-level verification, and rollback. This folder is an executable **candidate plus review evidence**, with no live hook replacement.

SAM/WoolRadar V5 original requirements remain **IN_PROGRESS**. No V3 lease was claimed, no PR merged, no production or global script overwritten.

## New isolated PowerShell process verification (2026-10-22)

`python -I -B -X utf8 audit_powershell_wrapper.py` ran the same eight scenarios
through eight actual `powershell.exe` processes, using synthetic JSON stdin.
It copied the installed wrapper byte-for-byte into a disposable workspace
folder next to the R29 evaluator named `stop_verify.py`. **8/8 correct, exit 0**;
every child exited 0 with empty stderr. `r29-wrapper-results.json` records
installed wrapper and evaluator hashes before/after, both unchanged. This
supersedes the earlier untested-wrapper limitation for this isolated process
path only; **real Codex host Stop dispatch remains unverified**. No global
installation, replacement, or operational sign-off.

For remote reproducibility, the unchanged prior 28-case unittest file is also
included as `legacy_suite.py`; invoke `python -B -X utf8 legacy_suite.py
stop_verify_candidate.py` with a writable TEMP/TMP. The two historical 28-case
logs remain the actual prior runs, not results of this new eight-case wrapper
invocation. This audit contains synthetic pause/resume strings only, no private
conversation excerpts or credentials.
