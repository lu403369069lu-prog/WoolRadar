# R4 follow-on: Windows Python user-site bypass of the first allowlist candidate

2026-10-22. In an isolated Windows Python 3.14.5 execution, the candidate
`integration_gate_candidate.py` strips `PYTHONPATH` and `PYTHONHOME` but still
passes `APPDATA` into the child process, as expected for compatibility. On
Windows, Python uses `APPDATA/Python/Python314/site-packages` as a user-site
startup directory. A temporary, controlled `sitecustomize.py` in that directory
can emit a fake passing unittest summary and terminate the test child before the
real failing test runs. The gate then reports a false PASS/exit0.

`reproduce_usersite_bypass.py` builds an intentionally failing synthetic
unittest under a temporary source root and controls APPDATA for the child.
It writes `usersite-bypass-evidence.json` and removes the temporary test files
when finished. `make_isolated_candidate.py` derives
`integration_gate_candidate_isolated.py` by adding Python's `-I` flag to the
test runner command; this second isolated candidate correctly reports FAIL/1.

Windows reproducing command:

```powershell
python -B -X utf8 make_isolated_candidate.py
python -B -X utf8 reproduce_usersite_bypass.py
```

Actual result: candidate false PASS/0; the isolated Python `-I` control
restores FAIL/1; both synthetic assertions true and the script exit0. The
independent original 9/9 R4 assertions also reran successfully after this
change. The source paths and user-site path are disposable. No project checkout,
production SQLite, real user site, or installed Python configuration changed.

The `-I` proposal can affect third-party dependencies installed in user-site
packages. Before integration, run the exact original WoolRadar test suite and
validate Linux and Windows interpreters, dependencies and environment.
The same-user checkout mutation and untrusted `PATH`/`npm.cmd` resolution
remain separate concerns; `-I` does not solve them. This addendum is review
evidence only and never constitutes hosted CI or cross-end business acceptance.
