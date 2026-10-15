# Bounded generic-title identity guard — isolated candidate

Date2026-10-15. BasePR16 `64889e48638137a84efe0e292d7f5f2a9f580b88`. This branch stacks on the unmerged PR15→PR16 candidates; it does not include parallel PR13/14. No production key migration, reindex, deploy or automatic merge.

## Executed finding and finite correction

Two distinct vendor URLs with headline `Free API credits` were assigned one event_id; the second upsert notification signal was false. That synthetic database behavior was reproduced, not merely inferred. Production frequency remains unknown.

The existing empty-title fallback uses the normalized URL. This candidate extends that fallback only when all normalized title tokens belong to a finite generic-benefit vocabulary. Different URLs with these uninformative titles stay separate; tracking/fragment variants of one URL still share identity. Explicit validated campaign_review remains higher priority. Existing specific RackNerd/AdminBolt cross-platform titles, numbers/specifications and annual/batch contracts preserve their prior behavior. No general title model, database schema or new notification algorithm is introduced.

This is intentionally bounded. Three independently reproduced residual collisions remain outside this vocabulary/policy: `Free AI credits`, `免费服务器优惠` and same-spec `Free VPS 1 GB` at different vendors. More generally, arbitrary branded/qualified identical headlines and unknown repost aliases are not solved. Unknown cross-site generic reposts may stay separate until a validated campaign review supplies identity. Do not describe this as all deduplication fixed or95% accepted.

## Tests, review and the legacy fixture

Eight new contracts first produced four failures: distinct vendors, distinct same-vendor paths, Chinese generic titles and per-vendor notification signals. After the guard, a full170-test run had one failure: the old backup/evidence preservation fixture itself required two unrelated-domain generic headlines to merge. Its actual failed output is retained at unit-tests-legacy-fixture-failure.json.

The fixture was corrected to use the specific synthetic same-campaign title `RackNerd StudentPack Launch 2026` for both entries. All original merged-count, backup, evidence, row-count and sightings assertions remain. Independent AST comparison confirmed only two title constants plus comments changed; generic non-merge is explicitly tested elsewhere. This is a fixture truth alignment, not a relaxation of product assertions or restoration of the bad merge.

Final real Windows/Python3.12.14 command `python -X utf8 -m unittest discover -s tests`: **170 passed, exit0,10.297s**, zero skipped. Source/test hashes are in unit-tests.json and the separate independent review, including the modified legacy test hash. Independent44 methods plus7 additional checks passed; the earlier43/1 review result is retained. Digest bridge uses the already installed local upstream environment; no Linux/full-upstream/real accuracy assertion.

## Ownership and remaining work

Original task WOOL-GENERIC-IDENTITY-20261015 claimed at994ae908e0627b8aa3cab63bbde9f922de80670c/revision76 omitted tests/test_core.py. Before touching that file, validated V3 events released the old owner with conflict status and registered/claimed/started WOOL-GENERIC-IDENTITY-2 with the extra fixture scope. Remote state5d0ee88fd619c5da8a577f2db1fb624f01a31d83/revision81 was read back; old owner null, only new task owned. Other tasks unchanged. This continues one candidate; it does not duplicate development or bypass a lock.

Phase exit must checkpoint exact candidate SHA/evidence and release the new owner for independent review. WholeP06 remains incomplete. WOOL-HOLDOUT-WINDOWS is conflict/unowned under the other actor's update; preserve its155-test read-only preflight instead of claiming through conflict or rebuilding its evaluator. Future production key migration requires separate review and authorization; existing live history is untouched.
