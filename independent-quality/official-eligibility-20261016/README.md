# Independent primary-source eligibility seed (2026-10-16)

**Status: pre-registered 11-case seed, NOT an accepted holdout / NOT a recall or precision result.**

Source: `primary-source-seed.json` contains 11 short, hand-reviewed structured conditions from provider-authored, public terms. No account has been logged into, registered, verified, or charged. The records are intended to challenge WoolRadar's **report/eligibility truth**, not its headline collection recall or claim that the user personally qualifies.

## Review protocol

1. Independently review each provider primary page again, freeze exact URL/content/UTC retrieval timestamps if available and confirm date-sensitive terms. If an official page changed, mark the sample drifted rather than silently replacing the original label.
2. Independently adjudicate each expected gate (`identity_gate`, `card_required`, `cost_gate`, `time_gate`) and report lane. Record conflicts and unknowns explicitly; account-specific suitability is **unknown** absent authorized proof.
3. Freeze a separate evaluation manifest with exact WoolRadar PR/commit SHA, generator/schema SHA, seed blob SHA, and source labels **before** running or modifying predictions. Use a genuine frozen holdout sampled independently of the code-development fixtures; do not tune the classifier on this seed and then count this seed as unseen.
4. Run the real isolated report/ingestion pipeline with authorized public snapshots, compare reported statements/links and their event-specific evidence against original terms. A key test is the distinction between `PUBLIC_APPLICATION` and **individual account eligibility**, and between standing free tiers and newly released promotions.
5. Report FP/FN, precision/recall, false user-eligibility claims, wrongly missing account/card/region conditions, source sample size and uncertainty separately. Do not report 95% until an independently adjudicated sufficiently sized holdout actually meets the gate.
6. Continue full five-node/Windows field validation, P06, backup/notification/recovery and the three post-completion final rounds. These 11 seed records only address one business quality axis.

Examples of distinct boundary cases: GitHub/Copilot student benefits require verified status; Azure for Students differs from the regular new-customer trial; Oracle card-based identity check differs from Azure's student no-card claim; AWS promotional credits can entail billing; Vercel Hobby is a standing non-commercial free tier, not a one-time giveaway; selected Cloudflare Workers AI models require paid access even while other models have a daily free allocation.

No personal account information, source contents, cookies, card information or private databases are included. This branch is a standalone draft stacked on Codex PR23, with no production change and no automatic merge.
