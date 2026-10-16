# Delivery integration checkpoint — 2026-10-16

PR #23 incorporates PR #26 at 45237d1fa737e722acf6d4086e6c13b6c59c713f,
with independent privacy/revision fixes. No PR was merged, no production changed.
Exact original PR26 unified Windows suite: 299/0 failures/0 errors/0 skipped, exit0.
Latest combined source: 313/0 failures/0 errors/0 skipped, exit0, 18.516 test seconds.
This is one formal TestSuite, including database/grouping/notification/trace/
collection transactions and race tests plus the bridge. Counts are not added
from independent branch reports. Base HEAD plus manifest identifies tested changes.

Reproduce: `python -B independent-quality/delivery-bridge-20261016/run_combined_tests.py`
Red stages: 29 methods /26 subtest failures, then33 methods/4 failures; both exit1.
Fixes: decoded sensitive routes; consumer URL/title/typed-claim values; UTC
overflow; same-key semantic revisions; private path titles; no requeue for a
mere official checked_at refresh or proof list reordering. Independent reviewer
validated final producer/consumer SHA256 plus14 contracts and9 positive/negative controls.

Local real sanitized historical copy:110 events; latest ReportGenerator MD/JSON,
exporter CLI, SHA gate and consumer CLI verified.102 exportable before and101
after a deliberately SYNTHETIC noise exclusion. Baseline0, integrity ok, FK0,
source copy unchanged. No original database/report/preview uploaded. This is
historical-copy compatibility, not fresh production collection or human approval.

DELIVERY_BRIDGE=OUTPUT_NOT_CONNECTED. File digests are integrity, not approved
publication, signed runtime provenance, live availability or personal eligibility.
Next: obtain a controlled safe publication/consumer channel with actual receipt;
continue P06, primary-source checks and independently frozen holdout. Original
five-node/Windows physical recovery/notification gates and final three rounds
remain incomplete. Do not resume the old quota pause; user explicitly restored work.
V3 owner task WOOL-REPORT-DELIVERY-20261016; check fresh state before writing.
