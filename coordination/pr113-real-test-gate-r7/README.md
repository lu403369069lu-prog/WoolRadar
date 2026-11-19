# R7: exact PR113 test roots, verified locally

This is review-only evidence for frozen WoolRadar PR113 source 396ce94e3510d4f09f951b0a973716c3c343bc93. It is not a production workflow replacement and does not certify V5 business acceptance.

The earlier R5 discovery guard correctly blocked nonexistent top-level tests/. The actual PR113 source has 16 tracked test_*.py spread across .github/relay, coordination and the frozen coordination/original-tests suite. R7 runs three real suites with -I -B -X utf8, verifies the frozen eleven-file manifest, pins the exact source HEAD, enforces a clean source checkout before and after, and exact test totals for that SHA.

Verified Windows result under a sandbox grant limited to local synthetic Git repositories: relay 72/72 PASS, coordination integrity 4/4 PASS, original coordination 48/48 PASS; combined 124/124 PASS, exit 0. Repeat with a clean PR113 checkout and provide --source, --expected-sha, and --output to r7_verified_roots.py. For Git fixtures, set TEMP/TMP/TMPDIR to a writable scratch directory and core.autocrlf=false for Git subprocesses. Run only against a reviewed, isolated checkout: the suite executes source tests.

Negative cases: a deliberately wrong expected SHA and a missing source directory both returned BLOCKED / exit 1. No tracked source changed.

An earlier default-sandbox attempt had five Git push fixture errors because MSYS could not create a Windows named object, and another attempt used a temp location with WinError 5. These local environment failures are preserved as evidence, and the successful elevated run does not establish hosted Actions compatibility.

This evidence intentionally declares business_acceptance=false and hosted_actions_accepted=false. The same-SHA 09:30 WoolRadar consumer ACK, real C1-C5 cross-executor checks, hosted CI startup and three V5 E2E rounds remain unverified. No PR merge, production data write or scheduler changes.