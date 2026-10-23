# Historical WR-H07/H08/H09: real public-sample producer must never persist private hosts or malformed Unicode

**event_key** `history-first/WoolRadar/exact-producer-private-host-and-unicode-red-green/20261017`  
**Authorization and scope:** interactive user's explicit engineering request. Isolated Linux Python3.13.5 with synthetic temporary public feed input only; no network, personal/private user data, payments, registrations, Windows/PLC/SQLite, Codex/Work or paid runner. Own Draft PR39 only, no auto merge.

## Confirmed true OLD production defects, not a speculative checklist

Original complete actual PR39 producer `core/public_corpus.py` Git blob **`6768c5d1a2229c6b5410c70de270ef49dc65bc26`**, reconstituted with **byte-exact `git hash-object` identity** before invoking formal regression. It admitted raw local and metadata URLs `http://127.0.0.1:8181/admin`, `http://169.254.169.254/latest/meta-data`, RFC1918 IPs, IPv6 loopback/ULA and local DNS names into a sample whose payload says `public_only: true`, and also preserved those URLs in synthetic title/summary text. Its separate downstream sampler did reject nonpublic hosts; that **did not erase the upstream stored raw URL exposure**.

Run `PYTHONPATH=. python -B -m unittest discover -s tests -p test_public_corpus_nonpublic_urls.py -v` with **the exact original Git production file blob** `6768c5...` and **the exact new formal file blob** `5dc8307b2666c3ba670f7d04ee260c7ce7f02326`: real **6 test methods, exit1, 23 failed subtest assertions**. Raw local original-red output SHA256 `8cb0604043c3941cb435e4a99e40568c578b33749094907765efd0a7e12eba8c`. Subtest failures are NOT 23 separately defined unittest methods.

Second defect: even after adding private-host refusal, complete producer code blob `e8af07365010437802fa5042ff9ae727afdf6d1f` crashed when untrusted title/summary/URL/node/platform included a lone surrogate. A new exact formal **5 methods all errors/exit1** before fix, raw local output SHA256 `08ee43a2337b99b96a8f60b46d82a42901cda680573aa28a418b3b72b724d301`. The malformed values are synthetic and safe; no real secret values reproduced.

## Actual fixes committed to the current-base Draft PR39

Production `core/public_corpus.py` has a **byte-exact tested and GitHub-readback verified new blob `383f3ad38930863fe5311260f8869b1ca65564ef`**, two independent stages:
1. `_is_lexical_public_host` now requires an ordinary ASCII public DNS hostname, denies IP literals (including public IPs), RFC1918, loopback, link-local, single-label, reserved `.local`, `.internal`, `.home.arpa`, `.lan`, `.localhost`, `.onion`, `.invalid`, `.test`, `.example` and numeric suffixes. It returns `'[non-public host redacted]'` and **`url_identity_preserved=False`** before storing any raw URL. The rule intentionally matches the source expectations of the original actual downstream PR37 blind sampler. It is **lexical only**—no DNS/redirect/security guarantee; tests don't claim one. Code commits `c90978ced38e5bb7201b6212494988454baa6ecf` and corrective sampler-alignment `ff56f61d4f493bad6f6b1349cfd82c09f940c4bf`.
2. `_safe_public_text` removes malformed Unicode surrogate codepoints from public titles, summaries, node and platform metadata with a replacement character; malformed source URL identity is outright rejected before `urlsplit` so it cannot be admitted as a valid campaign or crash the producer's `ensure_ascii=False` UTF-8 serialization. Code commit `ec5ed00476d0224105a99303958f450cb560df37`.

**Original formal new files committed and exactly rehashed from executed test bytes:**
- `tests/test_public_corpus_nonpublic_urls.py`: **`5dc8307b2666c3ba670f7d04ee260c7ce7f02326`**; commit `8f517351be403d8ea6515a610649e5b82a91a144`. Six methods, including 19 distinct denied synthetic host examples, two embedded-text URLs, normal public DNS identity and tracking query preservation, 23 original-red failing subtests.
- `tests/test_public_corpus_invalid_unicode.py`: **`e26a0ba16033de49c8544c2b03093ad103787e83`**; commit `412d8337beb37189d3ff898b10bc7ffdfbf2abc3`. Five genuine temp-file methods for malformed title/summary/URL/node/platform.
- Existing original `tests/test_public_corpus_timestamp.py`: **`c90cb9eab13230d4c4086e51c9c1b3f6f034dd62`**; source unchanged, exact bytes reconstructed and verified. Ten distinct original date/time tests.

**Final current-GitHub production/tests all verified byte-identical with `git hash-object` and fetched live GitHub blobs, not merely semantically copied.** Isolated synthetic `core/models.py` stub used **only** for time-stamp `utc_now()` because this unit checkout has not reconstructed the full models project; the complete **actual `core/public_corpus.py` byte stream** was genuine.

```bash
cd /tmp/wool_real_oct17
PYTHONPATH=. python -B -m unittest discover -s tests -p 'test_*.py' -v
```

**TAP equivalent standard Python unittest: 21 distinct methods, 21/21 pass, 0fail/0errors/0skips, exit0**, raw isolated log SHA256 **`41fe1dedf0828743d347329bb2df35179f21338f925816f5e05ed61b7bffd144`**. This includes *new6+new5+previous10*, so don't add previously reported 16/16 to this count.

## Codex owner batch reconciliation and acceptance

This new PR39 head **must NOT** be mistaken for the earlier immutable 50-family handoff's Wool SHA `80c5ea18769c1312e5be5fd99a39e4f3d498c64f`. The existing reviewed batch runner hard-codes that older snapshot and refuses head changes; **do not weaken that fail-closed check, and don't silently alter the 50-family immutable manifest only**. Local Codex should either run original batch acceptance in a clean disposable checkout of the immutable snapshot **or** carry out an explicit coordinated runner+manifest+HEAD update in a reviewed new handoff. For the latest PR39 code, independently run a clean Windows full test suite and `python -B -m unittest discover -s tests -p 'test_public_corpus_*.py' -v`; record current head and log SHA256. This interactive session ran the exact producer and three exact formal files in Linux; it **did not run** the whole historic Windows 412+ suite or the full independent sampler/consumer on this newly changed head.

Unresolved: DNS rebinding, redirects and source ownership still require later verification; genuine independent new X/Reddit/Linux.do recall labels first frozen trial TP1/FN3 (25% recall), same-campaign cross-URL false split1, official public applicant requirements, and approved signed local 09:30 delivery remain unpassed. Draft not merged, no deployment, no real private activity. `historical_recovery_closed=false`.
