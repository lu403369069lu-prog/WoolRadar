# Original coordination formal integration / IN_PROGRESS

Base Wool PR77 4ff27457b3b1b68b64c7e01a21a800983df50213. Formal Actions39203525433 failed before tests because the combined relay branch omitted original source/tests; no local test may replace this failure.

Port ONLY reviewed coordination delta from PR11 27796df5f9847c1bb5d48d2a445e418dfb3d8e96: five modules plus six original test modules, byte-identical per original-tests/SOURCE_MANIFEST.json. Tests relocated under coordination/original-tests to avoid active business owner's tests/ scope. No business tree merge, merge unrelated histories, or business test modification.

RED original suite without modules:20 discovered,15 failures+5 import errors,exit1. Restoring actual source gives48/48 pass,exit0,0skip. Original HMAC, dry run, lease/fence/CAS, Git concurrent writers, process crash, network/auth/error classification and replay all executed with isolated temporary data. New manifest integrity tests4/4 pass; current relay24/24 remains pass. This is source integration verification, not business acceptance or physical power-loss certification.

Workflow verifies original file hashes, runs Windows/Linux original suite and current relay together, uses read-only contents and no persisted checkout credentials. On push uses github.sha rather than old PR11 ref; PR uses actual head and manual dispatch uses explicit candidate. Logs print checked out full SHA, run ID and attempt. Old queue source refs remain OPEN until canonical integrated business SHA is supplied by owner. No old passing run substituted for newer code.

Independent PR78 474d8501b84c4f4f6ff39aff6d05324431440a99: extracted four exact source/test files and executed7 test methods (one has100 adversarial mutation subtests),exit0. Preserves child stdout bytes and denies invalid UTF8 forged summary. Not yet integrated into this candidate, not a business milestone.

Remaining: await real native formal CI at exact final HEAD; then source-ref canonical alignment, business owner integration, missing genuine acceptance material/provenance, independent quality and output feed connection. W6 OUTPUT_NOT_CONNECTED; SAM original61 latest10/61;522 independent gold unaccepted. Original business goals and C1-C5 overall IN_PROGRESS. No production/account/PLC/paid API/auto merge/force push.
