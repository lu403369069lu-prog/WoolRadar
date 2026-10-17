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

These three source files and original raw stdout are **local-only**. Do not mistake this Markdown checkpoint for an uploaded source or a successful code review. Before a GitHub source upload, copy the exact local files, independently verify the three blobs and run the 30-test suite on the resulting candidate HEAD.

Eight original external/policy-gated families: WR-H12 (user approval), WR-H13 (fresh gold), WR-H14 (scheduled writer safety), WR-H17 (maintainer approval), SAM-H08 (fresh 61-question gold), SAM-H11 (T009 human review), SAM-H24 (T031 human review), COORD-H07 (architecture review). Read-only file hashing cannot authenticate a user's consent, external source quality, independent gold or a native production receipt. All remain unaccepted until their own authorized acceptance evidence exists.

The previous 39-command frozen native batch remains separate: 10 partially reconstructed Linux commands executed, **29 without complete native receipts**. The formal whole-batch guard has not accepted the job. The draft PR remains unmerged; no production environment, PLC, paid CI or scheduler GitHub writes were touched.
