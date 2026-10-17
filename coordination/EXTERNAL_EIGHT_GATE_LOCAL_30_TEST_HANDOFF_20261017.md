# External eight historical gates — read-only local QA checkpoint (2026-10-17)

**Do not mark business acceptance or close historical recovery based on this document.**

The interactive chat independently reran the previously staged offline gate auditor on Linux, using:

```bash
cd /mnt/data/external_8_gate_work
python -B -m unittest discover -s coordination -p 'test_historical_external*.py' -v
```

Result: **30 tests run, 30 pass, zero skips, exit 0**. The test run included the original integrity cases, POSIX O_NOFOLLOW evidence traversal, JSON numeric overflow rejection, FIFO refusal, symlink-root refusal, and four CLI-envelope tests. Source/test exact Git blob IDs from `git hash-object`:

| Local file | Git blob SHA |
| --- | --- |
| coordination/historical_external_eight_gate_auditor.py | f5ef4ba31c50e4b5e054834d7b903a2fc1958907 |
| coordination/test_historical_external_eight_gate_auditor.py | b048841bdd0f6367d3fd98ec97af0349d9ad79f4 |
| coordination/test_historical_external_gate_cli_boundary.py | 0c13596d89d4df2c4366591fb5ece51b588f4abf |

**2026-10-17 verified correction:** All three source/test files above **are present on this Draft PR42 branch**. An authenticated GitHub HEAD fetch returned exactly the three Git blobs listed above, and these match local `git hash-object` values. The original raw Linux stdout remains local-only, with SHA256 `f3bfdf82561db33a6822298cafb13657a68ff063a8c2bdabf1a62ae0e66500fe`. The code has also been co-staged with the exact candidate executor/guard files (blobs `08af6d6304758399282d7b1799604089570c7b09` and `072ba64688fcd479795620b870a803ddb29dc78b`) and actually executed as **83/83 passing total selected coordination+gate methods** (53 earlier selected coordination cases + 30 gate/CLI cases; zero skips/fails, subprocess exit 0). Latest combined raw test log SHA256 `67ae2162993cacde1ea4df15e79e407db50d781b83a5b4ae3026282e792f1ee1`. Do not add 83 on top of the historical 223 selected methods without accounting for the overlapping 53.

Eight original external/policy-gated families: WR-H12 (user approval), WR-H13 (fresh gold), WR-H14 (scheduled writer safety), WR-H17 (maintainer approval), SAM-H08 (fresh 61-question gold), SAM-H11 (T009 human review), SAM-H24 (T031 human review), COORD-H07 (architecture review). Read-only file hashing cannot authenticate a user's consent, external source quality, independent gold or a native production receipt. All remain unaccepted until their own authorized acceptance evidence exists.

The previous 39-command frozen native batch remains separate: 10 partially reconstructed Linux commands executed, **29 without complete native receipts**. The formal whole-batch guard has not accepted the job. The draft PR remains unmerged; no production environment, PLC, paid CI or scheduler GitHub writes were touched.


## Verified current source upload and 32-test re-run

The three files listed above are **now confirmed present on this PR branch** with the exact local Git blob IDs from a fresh 2026-10-17 execution: `coordination/historical_external_eight_gate_auditor.py` = `3237eb61d54ec62927bb06a15c1ba056e8f8fb42`, `coordination/test_historical_external_eight_gate_auditor.py` = `253e05c0bb35ba5664794e967b68d30f7b4e0997`, `coordination/test_historical_external_gate_cli_boundary.py` = `0c13596d89d4df2c4366591fb5ece51b588f4abf`. The preceding text describing them as local-only and 30 tests is historical and **superseded**. Fresh command: `python -B -m unittest discover -s coordination -p 'test_historical_external*.py' -v` in the isolated source tree: **32 tests run, 32 passed, 0 skipped, exit 0**. Exact test coverage and Git Blob identities were rechecked after the previous note. This does not upgrade the external business gates, native Windows checks, or frozen 39-command acceptance.
