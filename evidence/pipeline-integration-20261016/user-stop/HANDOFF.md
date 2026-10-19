# Explicit user stop — upload then stop

User latest instruction: 上传工作内容后停止任务. No automatic resume, new
implementation, test run, source collection or deployment after upload.

Work saved on existing PR23, based on053fdfec1ffc22ead89928304b2ae9d3262ebac9.
Reuses PR32 latest4255b8f, PR33 b6529d0, PR34 2276d61; does not repeat their
development. Preserves the prior local fractional-timestamp regression. PR35
scheduling proposal was read only and NOT installed/merged/enabled.

Implemented before stop: fractional-second ambiguity fix; PR33 grant denial/
fee-waiver improvements; semantic-query sampler; real core/public_corpus.py
producer now preserves allowlisted structured batch/offer/ref/program selectors
and safe SPA routes. Known tracking parameters removed; unknown/private values
or conflicting selectors mark url_identity_preserved=False. Sampler excludes
those and legacy sanitized rows without new identity metadata. This metadata
is not signed runtime attestation, publication approval or business truth.

Real tests before stop: candidate combination390pass exit0;6 actual producer
to sampler methods initially failed9 subcases; implementation and updated old
schema positive-control eventually gave full396pass0fail0error0skip exit0,
16.887s. The old schema test expected information loss, so it now asserts3
retained ref identities while separate legacy-loss negatives remain. Logs and
Git source-blob manifests are saved; no branch totals added together.

IMPORTANT current candidate is NOT all-green: after that396 run,2 formal grant
negation methods were added. Fee-waiver positive passes, negative method has3
subcase failures (does not accept / will not accept / not being accepted).
Full combined suite after these additions was NOT rerun. The proposed
fix_grant_base_negation.py was NOT executed: automatic approval correctly
rejected further code modification after the user's stop instruction. Do not
claim the latest whole candidate passes396 or that this denial was fixed.

Independent review also reproduced a separate UNFIXED identity bug: URL longer
than2048 is truncated by producer, still marked identity-preserved; distinct
long URLs can collapse downstream. Review source fingerprints were not captured
before the stop, so its exact-version limits are explicit. followup_checks.py
is a saved unexecuted reproduction definition, not passing test evidence.

If user later explicitly resumes: cold-read newest PR23/Issue2/3/V3, claim a
fresh fence legally, first fix negated base/passive application states using
existing red tests, then mark truncated URL identity lost and add regression.
Keep privacy and legacy-loss gates. Full new exact-SHA regression required.
Then freeze corrected code/new unseen real public window with source/URL
dedup and independent cross-URL campaign adjudication BEFORE predictions.
Old56rows53URLs is development data; no new blind accuracy was measured.

OUTPUT_NOT_CONNECTED remains: no approved real data publication/channel/human
review and no matching09:30Asia/Shanghai ChatGPT consumer receipt. Raw SQLite,
reports, real previews, private evidence, accounts and caches were NOT uploaded.
P06/five originals, official/mainland/card/account/expiry/stock, notification/
backup/recovery and final3 rounds remain incomplete. No production/Work/paid
API/PR merge/force push/history rewrite. This is a user-requested STOP, not a
quota barrier or project completion. Do not auto-wake from older continuity.
