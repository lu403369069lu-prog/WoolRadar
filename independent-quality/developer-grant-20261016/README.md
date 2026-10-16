# Independent developer/OSS grant discovery candidate — 2026-10-16

**Base:** exact WoolRadar PR #23 HEAD `e3b31af746776bf976aba7418fce06ff2ae2ccde`.
**Status:** discovery-only, isolated draft, no merge or production deployment.

## Actual missed class and safe narrow change

The frozen public-source evaluation at `evidence/delivery-20261016/frozen-quality-evaluation.json`
reports TP0 FP0 FN2 TN47 unknown7 on 56 rows (recall0, precision undefined).
Both missed rows S046/S047 correspond to ONE source URL/campaign, namely
GitHub's official Secure Open Source Fund. The official program is a
conditional maintainer-security grant, **not** an unrestricted free
ChatGPT/API/cloud promotion. Its official page offers rolling applications
and selected project funding, but individual eligibility/region/card
requirements remain separate.

The existing `core/collector.py::contains_keyword` uses keywords such as
`developer perks`, and its money fallback mainly detects stated `$N cloud
credits`. Legitimate open-source maintainer grant applications that promise
selected projects a `$N` cash award can be missed.

New `core/developer_grants.py` requires all of: explicit open-source /
developer / maintainer scope, fund/grant program context, an actual
application-open CTA, a monetary award offered to eligible/selected people,
and absence of closed/paid/donation/request/historical negatives.
The `core/collector.py` hook runs ONLY when the existing opt-in
`developer perks` keyword is enabled, preserving disabled/default source
behavior. A match merely creates a *discovery candidate*. It is not
`OFFICIAL_VERIFIED`, `CLAIMABLE`, a guarantee of award, proof of card-free
entry or a user-specific China residency determination.

## Actual tests and limits

Executed Linux Python3.13 standard-library
`python -B -m unittest -v test_developer_grants.py`: **10/10 PASS, exit0**.
Cases cover active/rolling maintainer award, closed program, fee, donation,
historical award, generic article, question, generic startup investment
and open program with no cash award. GitHub and locally executed
`core/developer_grants.py` blob match `97da800bda098166b08394462ceb2d1831544dd3`; test
matches `3bafd60ab8866a3ba17e0d041706170d0c535af2`.

A further `tests/test_developer_grant_discovery.py` imports the real
`core.collector.contains_keyword` for five integration cases, including
on/off keyword behavior. It is **committed but not executed against
the complete private WoolRadar checkout in this ChatGPT environment**.
Before considering integration run the exact-HEAD full
`python -B independent-quality/delivery-bridge-20261016/run_combined_tests.py`
and `python -B -m unittest discover -s tests -v`, record exit/skip.

## Do not overclaim business quality

These ten constructed sentences are **development regression data**.
They are not the frozen 56 source snippets, a fresh independent holdout,
provider qualification, or false-positive assessment at scale.
Fixes informed by S046/S047 retire that frozen set for further *independent*
acceptance; a **new unseen** provider-mixed sample must be frozen before
recomputing recall/precision/dedup. Even then the program is only a
conditional funding application lead and does not prove claimability.

`DELIVERY_BRIDGE=OUTPUT_NOT_CONNECTED`: no local/private report was uploaded
and no authenticated ChatGPT daily brief consumption receipt exists.
Do not deploy, merge, auto-register, claim, pay, access X credentials
or modify the Windows runtime or SQLite.
