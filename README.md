# WoolRadar

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

**WoolRadar** is an MIT-licensed **research-resource & technology-offer intelligence tracker** paired with a **deterministic, fail-closed multi-agent acceptance relay**.

WoolRadar tracks technology offers, developer/research grants, and engineering-resource announcements while enforcing strict, reproducible verification gates over agent-authored changes before any candidate can claim formal or native acceptance.

---

## Key Capabilities

- **Research-Resource & Offer Intelligence Tracking**: Collects, normalizes, deduplicates, and triages technology offers and research-resource announcements (with strict campaign URL canonicalization, tracker stripping, SQLite WAL durability, and monotonic delivery fencing).
- **Fail-Closed Acceptance Relay (`.github/relay/`)**: Coordinates multi-family regression checks across disposable checkouts:
  - Rejects silent false positives—tests that exit `0` with `skipped` or `expectedFailure` cases, zero executed tests, or mismatched run contexts are recorded as `FORMAL_CHECK_FAILED_OR_BLOCKED`.
  - Separates formal subset checks (`FORMAL_SUBSET_PASS_NATIVE_PENDING`) from native OS / live business acceptance (`strictly_complete=false` until native gates pass).
  - Enforces **idempotent receipt persistence**: replaying an already-processed receipt leaves the queue cursor, state revision, and append-only `history.jsonl` ledger unchanged.
- **Unprivileged Evaluation vs. Isolated State Persistence**: Evaluation runs without write credentials on disposable checkouts; receipt persistence writes strictly to an isolated state branch rather than mutating `main`.

---

## Repository Architecture & Audit Trail Design

WoolRadar intentionally separates the verification control plane on `main` from candidate source trees, live checkpoint ledgers, and historical audit PRs:

```text
WoolRadar/
├── .github/
│   ├── relay/                  # Fail-closed acceptance worker, integration gate, queue & unit tests
│   └── workflows/              # Unprivileged PR acceptance & relay verification workflows
├── coordination/               # Multi-agent handoff protocols & checkpoint schemas
├── examples/
│   └── relay_demo.py           # Zero-dependency offline verification demo (synthetic git fixture)
├── HANDOFF.md                  # Operational handoff & relay architecture notes
└── LICENSE                     # MIT License
```

- **`main` branch**: Hosts the durable verification & receipt-replay relay (`.github/relay/worker.py`, `.github/relay/integration_gate.py`, `.github/relay/queue.json`), relay unit tests, and the offline executable demo (`examples/relay_demo.py`).
- **Isolated candidate & state branches**: Candidate application snapshots and regression fixtures live on dedicated branches (with durable relay receipts persisted append-only to `chatgpt/actions-live-state-v1-20261018`) so automated evaluation never overwrites `main`.
- **Why ~110 Historical PRs Remain Open**: The open pull requests in this repository are **SHA-pinned historical relay & audit evidence** (covering the 19 historical verification families tracked in [Issue #40](https://github.com/lu403369069lu-prog/WoolRadar/issues/40) and Wave 1–4 hardening slices; see [`HANDOFF.md`](./HANDOFF.md)). By repository policy, historical candidate PRs are preserved open rather than auto-merged or bulk-closed so human reviewers and deterministic batch runners can inspect and replay exact commit trees reproducibly.

---

## Quickstart & Verification

### 1. Run the relay demo offline

You need Git and Python 3.9 or later. From the directory containing this README:

```bash
python3 -B examples/relay_demo.py
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

### 2. Run the relay unit test suite

```bash
python3 -B -m unittest discover -s .github/relay -p 'test_*.py' -v
```

---

## License

Original work in this repository is licensed under the [MIT License](./LICENSE).
