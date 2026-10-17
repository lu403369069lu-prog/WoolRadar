# Immutable historical 20% — 8 external-gate evidence adjudications

As of **2026-10-17**, reviewed against frozen manifest Git blob `96c71aad1e26e5bf7b0aa12ac1e4b62ddcb98744`. Eight entries are **all classified**; **zero external business approvals** are authenticated. Do not reinterpret the “20%” planning shorthand as a delivered-business percentage.

| Frozen family | Gate | Independently established | Still missing |
|---|---|---|---|
| WR-H12 | USER_APPROVAL | The daily bridge must publish only a separately authorized, whitelist-redacted export; current 09:30 brief explicitly states `OUTPUT_NOT_CONNECTED`. | Explicit approval for exact content/destination, independently trusted export SHA and same-SHA actual consumer receipt. |
| WR-H13 | FRESH_GOLD | Previous actual `evaluation.json` (blob `f326ec8ff80c83ddb68fcbc33b5b6bd860cee6d8`) covers **47** rows; TP=1, FN=3, FP=0, TN=40, UNKNOWN=3: recall **1/4=25%**. FN IDs: S0011 (github-education), S0027/S0031 (MLH). | A *new*, independent, unseen-source window with labels frozen before predictions and real recall/dedup results; original 47 rows are now development data. |
| WR-H14 | SCHEDULED_BLOCKED | Read-only inspection of in-product task settings: current 09:30 task's instructions prohibit GitHub writing and private Windows collection; historical engineering tasks shown disabled. | Authenticated execution logs across relevant schedulers/Windows services; prompts and task metadata alone cannot prove no writer exists. |
| WR-H17 | MAINTAINER_APPROVAL | GitHub repository read/write permission is present but is **not** blanket permission to export sensitive historical fixtures. | Named maintainer approval for *precisely scoped*, sanitized fixture list. |
| SAM-H08 | FRESH_GOLD | Old SAM evaluation reports **61** original questions, only **10** source-bound answers; refusal **34/40** and prior R5 **0/6** remain unaccepted. | Independent review of all 61 original cases and historical 522 source records, then actual direct + MCP behavior receipts. |
| SAM-H11 | HUMAN_SOURCE_REVIEW | T009 source provenance remains unresolved by available source hashes. | Human-audited source authority, span and expected T009 outcome; fresh direct/stdio comparison. |
| SAM-H24 | HUMAN_SOURCE_REVIEW | T031 Axis/FSM source-gold conflict remains unresolved. | Human adjudication against original engineering sources; immutable corrected gold before test runs. |
| COORD-H07 | REVIEW_ONLY | Offline review of `coordination/PROTOCOL_V3.md`, frozen blob `ed27151bc7a0a3b4511fe82112efc0bf663271bd`, covers CAS, lease/fence, persisted outbox, transport/billing constraints and issue ownership. **Document review only.** | Real owner/fence recovery and authenticated agent/test-change receipts; no autonomous collaboration signoff. |

## Read-only auditor and evidence status

Code: `coordination/historical_external_eight_gate_auditor.py`, Git blob `8d749b3183c442da3a81557f6e9c225c206b6d1d`. Test: `coordination/test_historical_external_eight_gate_auditor.py`, blob `b048841bdd0f6367d3fd98ec97af0349d9ad79f4`.

Actual isolated Linux / Python 3.13.5 run, `python -B -m unittest discover -s coordination -p test_historical_external_eight_gate_auditor.py -v`: **26/26 passed**, exit 0, zero skips; stdout/stderr log SHA256 `e4b8b5c8d9e68008535dda878a42e9c67e6536291ee78d6256d72f9745b39321`. This tests the auditor itself with synthetic gate receipts; it does **not** establish source approval or execution of the remaining frozen commands. Auditor's secure evidence opening is POSIX only and refuses unsupported platforms.

Older Wool quality checkpoint `evidence/pipeline-integration-20261016/oct17/QUALITY_CHECKPOINT.md`, frozen blob `835ef4b8ff5f20ff7c6ae7d5d7a212e3cf115675`, explicitly reports the 47-row replay later improved 4/4 on the same *development* rows but had a false campaign split. It is not new independent recall acceptance, and no fresh eligibility was verified.

Frozen runnable commands: 42 READY families → 39 unique command lines; ten previously ran on **partial** Linux reconstructions (not original full trees), 29 still have no full pinned-checkout receipts (17 SAM `tsx`, 12 Python); eight external families remain separate. Native instructions and exact commands are in `coordination/CODEX_FROZEN_FULL_39_NATIVE_HANDOFF_20261017.md` and `coordination/FIRST_CATEGORY_29_FROZEN_COMMANDS_NATIVE_GATE_MATRIX_20261017.json`.

**Status**: `historical_recovery_closed=false`, `all_external_business_gates_accepted=false`. Four candidate PRs stay Draft/unmerged, no production Windows/PLC/SAM release, no paid CI, no scheduled GitHub writer, no private-data sharing. Any claimed review approval must be independently authenticated; a JSON key or matching SHA alone never grants it.
