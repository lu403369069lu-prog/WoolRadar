# P06 generic-year identity: isolated Windows verification (2026-10-20)

Owner: codex-woolradar. Draft PR #84; business-code commit `a2ca349a9c55b0ae416f9c2e2c79bda9c830abbb`, parent `1cbf1eab6dc5b1032b28d493a4439e51ef51e45f`.

## Bug and fix

An unbranded phrase such as `Get 2026 50 AI tokens for free` was hashed by title only if the number 2026 appeared, silently merging unrelated vendors. `core/dedup.py` now preserves the year in the normalized title but also uses the normalized URL for generic numeric benefits. Reviewed same-campaign metadata can still link cross-source members; named/brand-specific campaigns retain cross-source grouping. Four new synthetic year cases and three legacy contract reconciliations cover these semantics.

## Evidence (isolated writable copy; no production mutation)

- Before revision, independent PR #87 demonstrated year false merge; after source-rule revision but before legacy test-contract adjustment, local `test_generic*identity.py` failed one conflicting old assertion (exit 1), and coordinator independently found the second old assertion on its full run. Legacy assertions assumed unreviewed unbranded cross-site titles must merge; both were corrected and a reviewed-positive case added.
- `python -B -X utf8 -m unittest discover -s tests -p test_*.py -v`: **394/394 PASS**, zero failures, zero errors, zero skips, exit 0. Local logfile SHA-256 `42224c3cde05009679a42d7016b37a8f1c2e9e30ed61545d585e368c902982f0`.
- `python -B -X utf8 independent-quality/delivery-bridge-20261016/run_combined_tests.py`: **497/497 PASS**, zero failures, zero errors, zero skips, exit 0. Local logfile SHA-256 `06ab3f69200995cfe110ffd445daeaced1233b0931653b9137f996a3e016ae5c`.
- Existing pinned digest upstream version observed `3d527f7f7e68e1b3e20df4e2f1e20a5b445f6fcb`; no clean-room dependency install or GitHub CI claim. Logs remain on the Windows machine in the project `_outbox` and are **not published** because they contain local paths.

## Files verified on remote commit

- `core/dedup.py` Git blob `09ab88e64c6a9e000ad821f0f477c711a9dc50a4`
- `tests/test_generic_year_offer_identity.py` Git blob `08b7de10fba0337ff343976f100f539349d3b48f`
- `tests/test_generic_quantity_identity.py` Git blob `0b07f13fab30d2451bfca24129331d8f493d91c7`
- `tests/test_generic_identity_extension.py` Git blob `9353ade7048768ac698cd1b03c3807ea08475ac1`

## Still open

Original unseen quality holdout (prior independent recall 25% failed), source coverage/P06 five nodes, personal mainland/payment/deadline/stock conditions, 09:30 trusted delivery (**OUTPUT_NOT_CONNECTED**), physical Windows scheduler/restart proof, and three final independent acceptance rounds. This evidence update alone changes no executable code. No auto merge, production tasks, account changes, paid APIs or claim actions.
