# Recovered original Scheduled engineering artifacts — Oct 15, 2026

These **four original historical files** were recovered from the user's saved Library (not recreated from a model summary), written by an authorized interactive ChatGPT conversation to a **private Draft PR**, and checked against `git hash-object` of the **original local raw bytes**. All four GitHub blob IDs below match their source file hashes exactly.

| File in this directory | Original artifact | Git blob, source = uploaded | Expected role |
|---|---|---|---|
| `old_sql_red_repro.py` | `woolradar_notification_precedence_red.py` | `91bee4d09bf2adb9496741f0e14b55577691fc92` | Demonstrates **old** SQL loses a SENT loser when survivor PENDING, expected **exit 1** |
| `notice_precedence_synthetic_green.py` | `woolradar_notification_precedence_green.py` | `fa92a1bfb30191b16fd6aad42b8fbfe49791e133` | Synthetic SQLite model of notice precedence, expected **6 tests / exit 0** |
| `DO_NOT_APPLY_obsolete_PR19.patch.txt` | `woolradar_pr19_notification_fix.patch` | `d2c43be7232c01760b9f11a5a3ed4297d9093f98` | Historical old-SQL patch. **DO NOT APPLY** on current main PR23 |
| `M1_checkpoint_20261015_1200Z.md` | `SAM_WoolRadar_M1_checkpoint_20261015_1200Z.md` | `1f31c96ff7d98266974ff9579d032e2b27e5543d` | Original Scheduled blocked-write research receipt with old source SHA and command scope |

### Re-executed from original saved bytes on Oct 17

Isolated Linux Python 3.13.5 / SQLite, without real user database:

```sh
python -B -m unittest -v old_sql_red_repro.py
# Exit 1, 1 expected assertion failure ('PENDING' != 'SENT')
python -B -m unittest -v notice_precedence_synthetic_green.py
# Exit 0, 6 tests passed, 0 failed/errors/skips
```

Both are **synthetic SQL miniature models**; neither is a successful formal regression against the **current real full WoolRadar Database/reindex implementation**. Red failure is **intentional** to document the historical bug, not a current regression failure.

### Current branch dedup and safe next gate

On current main integration [Draft PR23](https://github.com/lu403369069lu-prog/WoolRadar/pull/23) exact SHA `6babbe12727652e8626e0fe6f554eb01fecd4a30`, `core/db.py` Git blob `9773d91e1d903eba73dff945a4afaf5b6b04376e` already contains specific SENT/CLAIMED notice conflict logic and `BEGIN IMMEDIATE`. These old synthetic tests should be adapted to **new** public Database integration fixtures (temporary SQLite) to prove no delivery-state downgrade and no duplicate resend. They do not justify replaying the obsolete 2026-10-15 patch. Any modified-current code requires another exact-SHA formal suite + independent quality gate.

**No actual Scheduled GitHub write was achieved**: all restored artifacts were uploaded in a subsequent authorized interactive chat. No user's raw production SQLite, notification payloads, secrets or local Windows report were accessed. No auto-merge/runner/deploy/paid AI API.
