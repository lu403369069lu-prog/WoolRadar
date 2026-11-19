# WoolRadar

WoolRadar tracks technology offers and research-resource announcements. The GitHub relay shown here coordinates the project's acceptance checks for proposed changes. It picks work from a queue, runs the mapped checks on a disposable checkout, and records a receipt that can be replayed without advancing the queue twice.

## Run the relay demo offline

You need Git and Python 3.9 or later. From the directory containing this README:

```text
python -B examples/relay_demo.py
```

The demo creates a temporary source repository and runs two small test fixtures through WoolRadar's actual relay. The first runs successfully. The second exits with code zero because its only test was skipped, so the relay records a failed or blocked formal check. Both results are stored in the local receipt history. Reprocessing the same receipt leaves the history and queue cursor unchanged.

Look for these outcomes in the output:

```text
WR-H01  FORMAL_SUBSET_PASS_NATIVE_PENDING
WR-H02  FORMAL_CHECK_FAILED_OR_BLOCKED
DEMO_OK
```

The demo uses synthetic fixtures. It requires no accounts, network services or local WoolRadar installation. A successful formal check leaves native and business acceptance pending. The demo does not run a live collection task or send notifications.

The demo was verified against the [MIT-licensed relay worker](https://github.com/lu403369069lu-prog/WoolRadar/blob/a3e5058543b62cb3c5af8047487648a98e228446/.github/relay/worker.py) at commit `a3e50585`.
