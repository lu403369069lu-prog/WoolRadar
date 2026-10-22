# Independent integration-gate startup poisoning reproduction (2026-10-22)

This is a **review-only, synthetic** reproduction. It is not a business acceptance
or an authorization to merge/deploy the hardening candidate.

## Exact origin

- WoolRadar main commit: `e44589104585c4b2a93081d00a145263666f9264`.
- Copied `.github/relay/integration_gate.py` Git blob: `dcb39f1aca78649e8383c40c9ed7a08a1546102e`.
- Copied `.github/relay/worker.py` Git blob: `d2bf920f3ae5a60b257e0ef1e79327b3d717dfc8`.
- The YinQieJi main gate at `668e219569aff780621bf6a1e24aa8cbe5f4e806`
  uses the same environment inheritance pattern. This reproduction executes
  the WoolRadar copy's two `--repo` paths against synthetic test directories.

Run on Windows with Python, Node and npm installed:

```powershell
python -B -X utf8 reproduce_gate_pollution.py
```

The driver checks the exact original gate blob before running, generates a
separate hardening candidate, and uses disposable directories under this folder.
The driver restores process environment variables after each case; it does not
read or modify original project databases, credentials or workspaces.

## Observed results on Windows / Python 3.14.5

| Case | Real observed status |
| --- | --- |
| WoolRadar baseline intentionally failing unittest | FAIL, exit 1 |
| WoolRadar with `PYTHONPATH` pointing to external `sitecustomize.py` | **Forged PASS, exit 0** |
| WoolRadar filtered runner environment candidate | FAIL, exit 1 |
| Original SAM path invokes bare `npm` through Windows CreateProcess | BLOCKED, WinError 2 |
| SAM path with Windows-only `npm.cmd` portability change | FAIL, exit 1 |
| Same portability-only SAM path with external `NODE_OPTIONS=--require` | **Forged PASS, exit 0** |
| SAM with portability + filtered environment | FAIL, exit 1 |

All **9/9** script assertions matched, exit 0. A fake child was used **only**
for the two SAM environment-presence assertions; the four SAM status rows above
come from actual npm/Node subprocesses. See `gate-pollution-evidence.json` for
the exact observed statuses, original source fingerprint and candidate hash.

## Candidate and boundaries

`integration_gate_candidate.py` removes Python/Node/Git startup overrides from
the inherited child environment and chooses `npm.cmd` on Windows. It has **not**
been integrated into `.github/relay/integration_gate.py` in either repository.
The explicit whitelist will need real dependency testing to confirm it preserves
required CI environment values and other supported platforms. This does not
solve the independent mutable checkout, descendant-process, or hosted Actions
startup issues. All business acceptance and deployment gates remain open.
