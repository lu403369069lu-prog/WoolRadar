# R30: exact stage-pause commands were missing from R29

The original R29 eight-case suite did not include the explicit phrase
`阶段性停止`. A new isolated 14-case suite (original eight plus six) found
**four R29 mismatches**: direct stage pause, a `先` prefix, a `现在` prefix,
and stage pause with a short explanation all incorrectly blocked the stop.
The RED oracle expected exactly four mismatches and therefore exited 0;
this is not an R29 pass.

R30 is a separate, uninstalled candidate. It adds anchored exact
`阶段性停止` recognition and optional current-round prefixes. Questions and
future/conditional requests (`完成后阶段性停止`, quota at 45%) remain pending
until their conditions are established by the responsible coordinator.
The language matcher itself does not read account quota.

Fresh Windows Python3.14.5 commands, all observed exit0:

```text
python -I -B -X utf8 audit_stage_pause.py stop_verify_candidate.py --expect-mismatch 4 --report r29-stage-pause-red.json
# 14 cases, four expected R29 mismatches
python -I -B -X utf8 audit_stage_pause.py stop_verify_r30_candidate.py --expect-mismatch 0 --report r30-stage-pause-green.json
# 14/14 correct, zero mismatches
python -I -B -X utf8 legacy_suite.py stop_verify_r30_candidate.py
# 28/28 PASS, writable TEMP/TMP redirected into workspace
python -I -B -X utf8 audit_powershell_r30.py
# 14/14 real PowerShell child processes, synthetic stdin, exit0, empty stderr
```

The wrapper test copies the installed wrapper byte-identically beside the
R30 evaluator inside a temporary workspace. Installed global wrapper and R28
evaluator hashes were unchanged before/after. This tests actual PowerShell
process/UTF-8 stdin and script invocation, **not native Codex host Stop
dispatch**. Neither R29 nor R30 was installed globally. No product source,
production scheduler, quota reset credit, or account setting was changed.

The original V5 remains IN_PROGRESS; this is audit evidence, not full acceptance.
