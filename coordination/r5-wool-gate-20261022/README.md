# R5: unittest discovery must bind to the reviewed checkout

Date: 2026-10-22. Status: isolated review candidate, **not integrated or deployed**.

Reproduction expects the sibling R4 evidence directory with
`integration_gate_candidate_isolated.py` and `worker.py`. The guarded candidate
resolves `worker.py` from that R4 sibling, including the GitHub layout
`coordination/integration-gate-negative-20261022/`.

Input: R4 `integration_gate_candidate_isolated.py` with Python `-I`. On a
source snapshot without a local `tests/` directory, that candidate executes
test modules found under an unrelated Python installation `site-packages/tests`.
On the local Windows Python 3.14.5 environment the candidate reported 8
unrelated import errors. Because this is a different test corpus, neither a
PASS nor a FAIL would be valid evidence about the intended source checkout.

The guarded candidate uses `unittest discover -s <absolute-source>/tests
-t <absolute-source>` and explicitly blocks a missing, symlinked, or escaping
test directory. It also uses `-B` alongside `-I`: `-I` ignores the inherited
`PYTHONDONTWRITEBYTECODE` variable, and an earlier synthetic source contained
`__pycache__` after running the original candidate.

On Windows, from the coordination workspace:

```powershell
python -B -X utf8 _outbox/r5-wool-gate-20261022/make_guarded_discovery.py
python -B -X utf8 _outbox/r5-wool-gate-20261022/reproduce_absolute_discovery.py
```

Result: **5/5 assertions, exit 0**. Synthetic local FAIL/1, local PASS/1,
no Python cache creation, missing source test root BLOCKED, and original
discovered 8 foreign installed tests instead of zero local tests.
Machine evidence: `discovery-evidence.json`, with no transient root path.

An independent archived checkout at `4ff27457b3b1b68b64c7e01a21a800983df50213`
contained 23 exported source files but no tests directory. The original
candidate tested the unrelated environment: 8 errors, exit 0 for the gate
wrapper (inner test result FAIL/1). Baseline without `-I` also selected
the unrelated installed test package and reported 20 tests, failures=3,
errors=10, inner exit 1. This checkout is **not** PR #114 HEAD. Neither
the baseline nor candidate constitutes product acceptance.

The runner's exit status remains 0 even for inner FAIL/BLOCKED because this
review gate writes a status JSON; the authoritative decision must parse and
enforce `status` and expected test identity/count. This candidate only fixes
discovery-root provenance and pycache creation. It does not address mutable
same-user checkout, PATH/npm resolution, Git smudge filters or external
dependencies; full Windows/Linux business suite, CI and cross-end C1–C5
remain OPEN. PR remains draft and owner integration is still required.
