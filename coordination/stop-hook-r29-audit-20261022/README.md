# Coordinator Stop hook R29 — independent pause/resume audit (2026-10-22)

Status: **isolated review evidence only**. No global hook was replaced. This branch contains a readable audit and a structured receipt. The executable fixtures/log files remain in the original local coordination workspace and have not been uploaded to this branch.

## Frozen sources and observed defects

The installed R28 Python hook is `C:/Users/lh/.codex/hooks/stop_verify.py` SHA256 `A3AA3707C401C227C82A620BF1B1BA21DA1445F1B862CB08273D3EE350C092FA`. The installed PowerShell wrapper is SHA256 `10D3A25753FE179D73FD1FA6472ADA688EEEA86239C6C5E916A36B3003FCEFF7`. Independent isolated R29 candidate `_outbox/hook-audit-r29-20261022/stop_verify_candidate.py` SHA256 `C2A7CDB6573D5046ADAE3B1B8D060F3A38E6A4C8F03BA56D20FFAB099C071B85`, with synthetic oracle `audit_stop_resume.py` SHA256 `5BE75A13DDFFEF781B5D72971B744B0340C20586B80DD7DD8DA7F301E8C4B3C3`.

The current installed R28 incorrectly **blocks** an active session after the latest user message `现在先别干了` or `先不要继续执行`, and incorrectly **allows** a paused session after the latest user message `继续干`. In the eight-case regression its outcome was **5/8 correct**, with three mismatches. RED runner exit 0 meant it correctly detected three expected mismatches, rather than proving R28 correct. Recheck report SHA256 `60D19D4882AF56CFF83C1085889BE0826ECFAF936F6E61ACC174125BF8CFAE30`.

The R29 candidate corrects these synthetic scenarios: **8/8 correct, zero mismatch, exit 0**; recheck report SHA256 `02F3EFED0F1065C5A0BA983775383136B3324FBDFF6DA7C4683E94CE62D75232`. Re-running the complete existing legacy `test_stop_candidate.py` suite yielded **R28 28/28 PASS exit 0** and **R29 28/28 PASS exit 0**, using isolated writable Windows TEMP/TMP. The two complete log SHA256 values respectively are `542A5A604588DACB0102D432299E8AA5B0C1E933D5A7686EABCE467101B38725` and `83F6F5DB4B5B800602D29234ADAA831A45E65A13AA99D843982C144C356BE1D3`.

## Reproduction boundary

Local working directory: `C:/Users/lh/Documents/ChatGPT/总协调/_outbox/hook-audit-r29-20261022/`. It contains the evaluator, isolated candidate, RED/GREEN JSON reports, complete logs, and original README SHA256 `9CF6FABAF7FB18754080B602797CB5C172F1F05F4B3B1F94B5FDC7893CE34B45`.

Example commands from that directory, using bundled Python:
```powershell
python -B -X utf8 audit_stop_resume.py C:/Users/lh/.codex/hooks/stop_verify.py --expect-mismatch 3 --report recheck-red.json
python -B -X utf8 audit_stop_resume.py stop_verify_candidate.py --expect-mismatch 0 --report recheck-green.json
```

**Unverified:** R29 wrapper behavior in an actual host Stop callback, all informal pause/resume phrases, and safe install/rollback. For acceptance, independently rerun the live PowerShell wrapper and host callback, retain a byte-for-byte backup and ensure the installed hash is rechecked. Do not promote this draft as a product test.

## Project interaction and remaining milestones

GitHub V3 `codex/relay-state-v3:state.json` blob `83970b58a9261a4b1bea3cbd92bfe206f001170c` revision 439. Shared SAM HISTORY-AUDIT and Wool COORD-SOURCE-PIN tasks have no current owner but disallow remote takeover, while SAM MILESTONE-INTEGRATION has its separate owner. This audit claims no shared owner or business source scope.

Wool PR91 and PR113 both modify worker.py and test_worker.py; owner-controlled integration is still required. Wool PR115 R7 source-check runner's `git status --porcelain` misses tracked flags `assume-unchanged` and `skip-worktree`; exact-source gate remains under review. Hosted Actions runs `39708146661` and `39708146668` returned two failed jobs each with zero step summaries; no defensible root-cause conclusion. SAM frozen history original-byte identity/Gold 61, Wool 09:30 same-SHA independent consumer ACK, cross-end C1–C5 and final V5 real E2E rounds remain **IN_PROGRESS**.

Remote coordination Issue #3 comment [6336096778](https://github.com/lu403369069lu-prog/WoolRadar/issues/3#issuecomment-6336096778) was written and reread with its id and marker. This branch is review-only; **no PR auto-merge, production write, hook installation, or device action**.
