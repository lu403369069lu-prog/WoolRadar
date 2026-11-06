# Scheduled backfill: syntactic public-host admission (2026-10-17)

## Provenance & scope
Recovery from hourly WoolRadar Scheduled report: the original offline candidate reported private/local-address admission bypass and **15/15 local checks** but could not write to GitHub. Those historical numbers are conversation evidence, **not** this interactive run's tests or an uploaded Scheduled commit.

This interactive chat independently read the full `freeze_public_sample_dedup.py` on main Draft PR23 commit `8023232586fd5d017981ea83ea0785cf381f7cc2`, original Git blob `c090c6885c22fe73b876de994a1c79714c0e7051`. It adds a *minimal fail-closed syntactic public-domain restriction* to the actual `canonical_public_url` implementation and augments `test_freeze_public_sample_dedup.py` with real formal coverage. No new source discovery, no user's local data, no UI or network probes.

## Actual code change
Reject raw IP literals (even global literal IPs), dotless intranet hosts, local/internal DNS suffixes (`.localhost`, `.local`, `.internal`, `.lan`, `.home.arpa`), nonpublic test/invalid/example/onion suffixes, and all-numeric terminal labels. Keep ordinary public `example.org`-style named hosts and distinct `batch` keys; retain known marketing tracker removal. This is a lexical classification. A public-looking hostname might still resolve to a private IP or redirect there; **DNS rebinding, redirect fetch safety, publisher identity and real-person claim eligibility remain unverified and require network-layer policy in any downloader**. No assertion of SSRF defense for downstream actual HTTP clients.

## Actually executed in isolated Python3.13.5
Read current candidate canonical function and transcribed its **complete actual function body** plus imports into a 2-method synthetic focused unittest, then ran:
`python -B /tmp/wool_scheduled_hosts/check.py`

Result **2 test methods, both pass, 0 failures/errors, exit0**, with **21 disallowed URL controls and 3 allowed canonical URL controls**. It includes localhost/sub.localhost, 127.0.0.1, RFC1918, 169.254, CGNAT, unspecified address, IPv6 ::1, dotless host, reserved suffixes and shorthand numeric IPv4; valid named hosts retain `batch` identities and UTM removal. This validates the exact transcribed source function, **NOT** an import/execution of full GitHub module, original 18-method formal tests, combined Windows 406 suite or an unseen public holdout. New formal full-module tests were committed but remain to be independently run in an authorized full checkout. No synthetic source is eligible as current official activity.

## Exact integration gate
Stage Draft PR on top of main Wool Draft PR23 `8023232586fd5d017981ea83ea0785cf381f7cc2`; main V3 task was owned by `codex-woolradar`, hence no owner/lease/fence/main-branch mutations. Main owner reviews current base and performs:
`python -B -m unittest discover -s independent-quality/public-corpus-blind-dedup-20261016 -p 'test_*.py' -v`, then latest unified Windows suite at the integrated SHA. Only after separate fresh unblinded-source-independent gold and actual delivery may acceptance change. OUTPUT_NOT_CONNECTED, NOT_RELEASED.


## Second smallest item: strict boolean identity proof (2026-10-17)
The later hourly Scheduled round independently reported that `url_identity_preserved` used truthiness and missing/forged JSON values could still enter new blind denominators. That task's 27/27 is **a historical isolated candidate** (unpublished), not a current main checkout test.

In this **separate interactive commit on the same isolated Draft branch**, replace old permissive condition with exactly `row.get('url_identity_preserved') is True` as the admission requirement; if a `url_sanitized` field is present, it must be an actual JSON boolean rather than numeric/string/object/array/null. Legacy corpus rows without independent producer-backed identity proof are now excluded from new blind review. The existing test helper has been updated to model the actual producer's always-present boolean; the legacy regression explicitly deletes that field to verify exclusion. This is a conservative schema-policy change and requires full checkout compatibility review.

Actual isolated Python3.13.5: copied the exact current `freeze_public_sources` body from the GitHub candidate and the preceding `canonical_public_url` function, ran `python -B /tmp/wool_scheduled_hosts/check_identity.py` — **5 test methods pass, 0 failures/errors, exit0**. Subcases exercised: 8 forged/nontrue proof values, 1 absent legacy proof, 7 forged `url_sanitized` markers, 3 valid boolean combinations and 1 private-host rejection (20 subcases). This confirms **transcribed full function behavior** only; it does not claim the committed full test file or actual repository's Windows 406 suite were executed by this isolated harness.

Uploaded formal `test_freeze_public_sample_dedup.py` now also includes three real `node`-independent Python `unittest` methods (forged/legacy marker, malformed sanitized marker, valid positive), on top of two public/private host tests. Exact new GitHub blobs and Draft HEAD should be re-read before final integration. Downstream local producer `core/public_corpus.py` emits a real boolean `url_identity_preserved` and does not require relaxing this policy. This hardening does not make public official eligibility or user claims real, and `OUTPUT_NOT_CONNECTED` remains unchanged.
