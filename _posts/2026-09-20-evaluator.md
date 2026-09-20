---
layout: single
title: "Weekly Pipeline Review — 2026-09-20"
date: 2026-09-20T11:48:38+02:00
categories: [evaluator]
published: true
---

# Weekly Brief Pipeline Review — 2026-09-20

_Coverage: briefs from 2026-09-14 to 2026-09-20._
_Files read: 6 news, 2 AI/ML (expect ~2), 1 science (expect ~1), 1 sports (expect ~1), 1 weekend, prior review found (`_posts/2026-09-13-evaluator.md`)._

The pipeline is healthy. All eleven expected (slug, date) pairs landed on the correct cadence (News daily Mon–Sat, AI/ML Tue+Fri, Science Wed, Sports Mon, Weekend Sat), both mechanical scripts ran clean, `reconcile.py` reported **0 flagged** across 24 editions, and there is no aggregator leakage, no empty section, no fabrication, and no unconsumed-feedback backlog. The three things worth a human's attention are all upstream of brief quality: a **force-rewrite of `origin/main` this window** (verified non-destructive), a set of **registry `reach: direct` records that writer telemetry now contradicts**, and the standing **structural diversity gap** in the two narrowest streams. Details below.

## Health summary

| Metric | Value | Target | Status |
|---|---|---|---|
| Unique domains 30d (worst stream: science) | 10 | ≥30 | 🔴 (structural) |
| New domains this window (portfolio, `[new source]` anchored) | ~8 | ≥2–3/wk | 🟢 |
| Top-5 outlet share (worst meaningful: news) | 0.708 | ≤0.50 | 🟡 |
| Waiver rate (worst stream: weekend) | 0.60 | ≤50% | 🟡 |
| Discovery footer present (every brief) | 11/11 | 100% | 🟢 |
| T1 citation % (portfolio) | 53/123 = 43.1% | ≥40% | 🟢 |
| T3 leakage count | 0 | 0 | 🟢 |
| Non-English citation % (portfolio) | well ≥10% | ≥10% | 🟢 |
| Link sample pass rate | 7/20 = 35% | ≥90% | ⚪ egress-degraded |
| Fabrication count | 0 | 0 | 🟢 |
| Single-source rate (portfolio) | ~4% | <20% | 🟢 |
| Empty section instances | 0 | <5 | 🟢 |
| Repeat rate (worst stream: weekend) | 0.371 | judge | 🟡 by-design |
| Direct-fetch ratio (portfolio, citation) | 122/123 = 99.2% | ≥0.35 | 🟢 |
| Feeds with >50% fail rate | ~20 (egress-blocked institutionals) | 0 | 🔴 egress |
| Citations on `reach: blocked` domains w/o `[via snippet]` | 0 | 0 | 🟢 |
| Unconsumed feedback backlog | 0 | 0 | 🟢 |
| Vendor-PR-lead share (AI/ML, §M) | ~18% (2/11) | ≤40% | 🟢 |
| Aggregator-shape failures (§M, of 5) | 0 | 0–1 | 🟢 |
| Personalization misses (§M, of 5) | 0 | 0–1 | 🟢 |

## A–N: Detailed findings

**A. Source diversity & discovery.** New-domain flow is strong: eight `[new source]` domains were anchored this week (news: parlament.ch, gov.wales, scp-ks.org, eneabaselgia.ch; ai-ml: elevenlabs.io, microsoft.ai, nex-agi.com; sports: worldathletics.org), comfortably above the 2–3/week target, and I spot-checked all: every one is a genuine primary (government/parliamentary portal, governing body, first-party academic or vendor publisher) — **no junk anchors**. Seven of the eight are already promoted into `sources/registry.yml` as `candidate`, so the `[new source]` → candidates → registry lifecycle is working (that is why `candidates.jsonl` reads empty). The one exception, nex-agi.com, was a secondary mention in the 09-15 AI/ML edition and did not land as a candidate — minor, not worth a patch. Portfolio **T1 share is 43.1%** (53 of 123 citations), just over the ≥40% bar, carried by the paper-heavy streams (weekend 62% T1, AI/ML 80%, science 100%) against news at ~2% T1 — the registry tiers the quality broadsheets news relies on (SRF, Le Monde, Al Jazeera, DW, Le Temps) as **T2**, so news T1 is structurally low, not a quality miss. **Non-English** representation is healthy portfolio-wide (news, weekend and sports lean heavily on FR/DE/ES sources; the 09-19 news edition is majority non-English). **Tier distribution: T3 = 0%** (the 12 "untiered" citations are the new/candidate domains above, not low-quality T3). The one real deficit is concentration — see the top-5 and waiver notes below and §K.

**B. Aggregator leakage.** `health.json → briefs.aggregator_leakage` is empty. **Zero** citations of HN/Reddit/X/Mastodon/Bluesky/etc. 🟢

**C. Link health.** `linkcheck --check` resolved **7/20** (window 2026-09-14→09-20, 134 links). This is **egress-degraded, not a brief defect**: the failures are `ERR:56` ("CONNECT tunnel failed, response 403") concentrated on arxiv.org/abs pages, huggingface.co, the-decoder.com, dw.com, simonwillison.net and lavuelta.es — hosts the *evaluator* session's egress allowlist does not tunnel. Allowlisted hosts resolved cleanly (aljazeera.com, srf.ch, letemps.ch, quantamagazine.org all 200). The briefs' own `direct_fetch_ratio` is ~1.0 across every stream, so the sources fetched fine at compose time (the writers hold the fetch-proxy bearer; this session does not). I claim-checked the resolvable links (the Al Jazeera Iran-war-powers vote, the SRF Nestlé external-administration piece, the Quanta ctenophore feature) and each cited claim is present in the source. **Fabrications detected: 0.** I am reporting the pass-rate dimension as **unmeasurable this run** because the checker's egress, not the briefs, drove the failures.

**D. Section vitality.** `empty_sections` is empty for every stream. No dead sections. The AI/ML "Apple Silicon / local inference" desk in the weekend brief was deliberately kept short with an honest "nothing else substantive landed, so this desk is deliberately short rather than padded" — the right call, not an empty section. 🟢

**E. Coverage gap recurrence.** The one recurring gap, appearing ≥3 times this week and structural, is **institutional/government primaries unreachable from the sandbox**: news 09-17 (OHCHR, congress.gov, seco.admin.ch all egress-blocked), news 09-19 (spi-sg.ch, stm.dk), science 09-16 (ICRAR, ESRF), weekend 09-19 (home.cern, eso.org JS-rendered/unreachable). In every case the writer waived discovery honestly and fell back to the peer-reviewed primary or a quality wire — but this is the binding constraint on diversity (see §K), not a sourcing-discipline failure.

**F. Triangulation rate.** Portfolio single-source rate ~4% (ai-ml 3.7%, news 8.5%, science/sports/weekend 0%). Well under the 20% bar. 🟢

**G. Tag discipline.** `[preprint]` is applied consistently on every arXiv item across AI/ML, science and weekend; `[vendor PR]` correctly marks the DeepSeek V4.1-Flash paper (vendor's own performance claims), the two OpenAI posts and the Ternary-Bonsai model card. `[disputed]` is used once, appropriately (news 09-19, the Houthi denial of targeting Mecca). `[via snippet]` fired once all week (09-18 news) — with the curl-first chain that rate is at the floor, not rising. `[new source]` integrity verified above (7/8 genuine primaries promoted to the registry). No tag drift. 🟢

**H. Topic balance (weekend).** `weekend_balance`: ml_items 22, science_items 14, **ml_share 0.611** — inside the [0.35, 0.65] band. This is a genuine improvement: last week's review flagged 0.714 (outside band) and proposed p4; the writer self-corrected this week (and flagged the RL/agents surge in the intro). 🟢

**I. Repetition detection.** `reconcile.py`: **0 flagged**, no id forks. Repeat rates: news 0.085 (4 repeats), weekend 0.371 (13 repeats), all others 0. I checked both: the four **news** repeats carry proper `[ongoing since]` discipline with genuinely new dated facts (Trump *signed* the Russia sanctions bill on 09-18 after Congress cleared it 09-16; a new 09-19 Riyadh strike in the ongoing Yemen escalation) — updates, not re-summaries. The **weekend** 0.371 is by-design: the Weekend brief revisits the week's AI/ML dailies' papers "in more depth" per its remit (its intro says so explicitly), adding full method and cross-paper synthesis rather than re-summarising. Neither is a defect. 🟢

**J. Cross-week trend.** vs the 2026-09-13 review: weekend ml_share improved (0.714 → 0.611, back in band); aggregator citations held at 0; via-snippet held at the floor (1 this week); T3 leakage held at 0; direct-fetch held at ~99%. The reach-record drift (§K) is new-surfaced this week from the fetch log.

**K. Feed reachability & direct-fetch.** Per-stream `direct_fetch_ratio` is 0.98–1.00 everywhere — every stream clears its range with huge margin, because when a curl fetch fails the writer falls to the proxy or drops the source rather than citing via-snippet, so no reachability failure reaches the reader. **Method comparison:** the reliable feeds work over plain curl (export.arxiv.org 49 ok, srf.ch 44, aljazeera.com 25, letemps.ch 17, quantamagazine.org 10); a second tier works **only via proxy** (arxiv.org HTML 48, nature.com 20, lemonde.fr 13, news.un.org 13, the-decoder.com 12, anthropic.com 39); and a third tier — the institutional/government primaries — is a **wall where both curl and proxy fail** (admin.ch 5/5, ohchr.org 8/8, esrf.fr 7/7, congress.gov 2/2, seco.admin.ch 4/4, spi-sg.ch 8/8, all HTTP 403/ERR:56). That third tier is the §E gap and the diversity ceiling. **~20 feeds exceed a 50% fail rate**, but essentially all are that egress-blocked institutional class plus a few proxy-only outlets — not feeds that are silently degrading brief quality.

The actionable finding here is **registry reach drift**: four domains recorded `reach: direct` had **zero** curl successes this window and succeeded only via the proxy — anthropic.com (0 curl / 39 proxy / 53 fail), the-decoder.com (0 / 12 / 12), news.un.org (0 / 13 / 17), rts.ch (0 / 2 / 7). `direct` is simply wrong for these; each should be `proxy`. I could not confirm from this session (the evaluator egress 403'd every non-allowlisted host, aljazeera.com being the one control that returned 200), so the flips rest on writer-side telemetry — see the registry proposal. **Domains-that-shouldn't-be-cited:** no `reach: blocked`/`blocked-paywall` domain appeared as a primary anchor without `[via snippet]`, and no `never:` domain appeared. 🟢

**L. Output volume.** Two streams grew >25% w/w. **Weekend: 7,217 words vs 5,429 (+33%)** — the largest, ~10.1k output tokens. It tracks a genuinely heavy paper week (35 anchors, four conjecture-level math results) and the writer cut honestly ("things I deliberately cut" lists five items), but Weekend is also the highest-repeat stream, so it is the both-long-and-repetitive profile the token-levers SPIKE names as the output-cap candidate — hence a soft length-discipline steer (Patch 2), not a hard cap. **Sports: 1,427 vs 1,017 (+40%)** — but off a tiny base on a young stream (first run 2026-07-20), at an absolute length in line with the other daily-ish desks; monitor, no action. News (+12%), science (down) and AI/ML (down 25%) are all fine.

**M. Editorial shape.** **Vendor-PR-lead share (AI/ML):** ~18% (2 of ~11 items — the two OpenAI posts on advertising and misalignment reporting lead with the company's own announcement), and *both* add independent framing the source omits ("take them as a governance gesture, not independent verification"; the ad-model's incentive "sits directly against the product's usefulness"). Well under 40%. **Aggregator-shape (5 leads sampled):** 0 failures — the Greenland accord lead cross-checks Trump's "permanent control" claim against Copenhagen's careful wording; the Nestlé lead adds the SRF correspondent's Carlsberg/Danone precedent; the OverclaimBench weekend lead adds the cross-paper trust synthesis. Each cites a primary and adds judgment. **Personalization (5 sampled):** 0 misses — CH/Vaud angles are present where they exist (Nestlé HQ in Vevey; the Dublin/Schengen asylum knock-on; Geneva Airport's China>US reversal; Werro and Basel/Shaqiri in sports) and not forced where absent (global AI/ML items carry a builder's angle instead). 🟢

**N. Affiliation element.** **Coverage rate:** roughly 5 of ~36 paper bylines read "(affiliation not listed)" (~14%) — under the 20% target. The unlisted ones are honestly flagged in each brief's Gaps (D-Quant and the LLM-consensus paper in AI/ML; the chromatic-number and PANXEON items in weekend). **Halo audit:** the `(affiliation not listed)` / independent-author papers were *not* systematically down-weighted — the single-author LLM-consensus paper (T. Shao) got substantial coverage in both the AI/ML daily and the weekend synthesis, and the affiliation-free items sit at the same importance band as the big-lab papers. No prestige bias detected. 🟢

## Prior proposals status

From `proposals/*-2026-09-13.*`:
- **rm-1** (reader-profile.md — anchor institutional stories on the official primary): stamped `applied: true, applied_by: evaluator`. **Verified landed** — the dated 2026-09-13 line is present at the end of reader-profile.md "Learned preferences". Early evidence it is helping: news met discovery on official primaries 4 of 6 days this week, and there were **zero** "press instead of primary" downvotes (last week's trigger).
- **p1** (routines/src/news.md — extend the primary-document rule to votes/government positions): **pending, not applied.** Still worth applying; not re-proposed as new.
- **p3** (routines/src/science.md — anchor at alternative primaries, nature.com saturated): **pending, not applied.** Recurs — science top5_share is still 1.00 this week. Not re-proposed as new; the new plos.org/agu.org candidate adds (below) attack the same deficit from the registry side.
- **p4** (routines/src/weekend.md — make the 50/50 balance target explicit): **pending, not applied.** The imbalance self-corrected this week (ml_share 0.611), but the target still is not stated in the prompt, so nothing guarantees it holds. Not re-proposed as new.
- **registry-2026-09-13** (admin.ch reach flip; europarl.europa.eu add): **pending, not applied.** admin.ch failed 5/5 again this window — the flip is still warranted.

## Source scout (Sunday duty)

**Stream picked: science** — the mechanical worst-deficit stream (new_domains 8 = lowest in the portfolio; top5_share 1.00 = highest). Caveat worth flagging for next week: science already carries a *deep* candidate bench in the registry (elifesciences, cell.com, chemrxiv, cnrs.fr, epfl.ch, empa.ch, eawag.ch, aasnova, astrobites, cerncourier, semanticscholar, earthquake.usgs.gov, and more), so its deficit is **not a candidate shortage** — it is (a) the narrow primary-journal universe a science stream inherently draws from and (b) the egress wall on institutional newsrooms (§E/§K). Sports (new_domains 11, official league sites JS-blocked) may be the higher-value scout target once science's bench is exhausted.

**Candidates appended** to `sources/candidates.jsonl` (both genuine primary publishers absent from the registry; both 403'd the evaluator egress, so `reach: proxy-needed`, writers vet with the bearer):
- **plos.org** — Public Library of Science, open-access primary journals; Atom feed at `journals.plos.org/plosone/feed/atom`.
- **agu.org** — American Geophysical Union, primary earth/space-science publisher & newsroom.

**Re-probe results (5 stale/suspect reach entries, direct curl):** aljazeera.com → **200** (confirms `reach: direct`); anthropic.com, esrf.fr, ohchr.org, congress.gov → **000 / "CONNECT tunnel failed, response 403"**. These four 403s are the *evaluator egress allowlist*, not proof the domains are blocked for the writers (who reach anthropic.com fine via the proxy), so I did **not** propose reach flips from them. The reach flips in the registry proposal instead rest on writer-side fetch telemetry (§K).

**Fetches used: 7** of the ≤20 budget (2 candidate vets + 5 re-probes).

## Patch proposals (for human review)

Only two new prompt patches this week — the pipeline is healthy and the prior-week p1/p3/p4 already cover the standing prompt-side gaps. The higher-value changes this run are the registry reach flips (machine-readable file below), which need no prompt edit.

### Patch 1 — Widen the news daily outlet base
**Target prompt:** News
**Section affected:** Source-selection step
**Issue:** news top-5 outlet-class share is 0.708 (30d) against the 0.50 target — the worst *meaningful* concentration in the portfolio. Discovery of new *primaries* is healthy (4 of 6 days met with official primaries), so the deficit is repeated reliance on the same five daily wires/broadsheets for the ordinary run of stories, not a discovery failure.

**Proposed change:**

> **Before:**
> ```
> [source-selection step — no outlet-rotation guidance]
> ```
>
> **After:**
> ```
> When a story is carried by several registered outlets, prefer one OUTSIDE the recurring
> top-5 daily cluster (srf.ch, lemonde.fr, aljazeera.com, dw.com, letemps.ch) where it is
> equally authoritative — especially a non-French/German-Swiss or non-European outlet — so
> the daily outlet base widens across the week.
> ```

**Why this helps:** directly attacks the top-5 concentration without touching the primary-source discipline that is already working.
**Risk:** over-rotation toward weaker outlets for the sake of a metric; mitigated by the "equally authoritative" qualifier.

### Patch 2 — Weekend length discipline
**Target prompt:** Weekend
**Section affected:** Paper-selection step
**Issue:** Weekend words_mean rose +33% w/w (7,217 words, ~10.1k output tokens) and Weekend is also the highest-repeat stream — the both-long-and-repetitive profile the token-levers SPIKE flags as the output-cap candidate.

**Proposed change:**

> **Before:**
> ```
> [paper-selection step — no length-discipline note]
> ```
>
> **After:**
> ```
> The Weekend brief targets depth on the week's strongest work, not exhaustiveness. When the
> paper pool is deep, tighten to the highest-signal items rather than extending each desk, and
> keep the total near the running mean unless the week genuinely warrants more — say so in the
> intro when it does.
> ```

**Why this helps:** curbs token spend on the priciest brief without a hard cap that would cost depth on a genuinely heavy week.
**Risk:** the writer trims a genuinely strong item; mitigated by the explicit "unless the week genuinely warrants more" escape and the existing "things I deliberately cut" footer that keeps the choice auditable.

## Reader-feedback → profile proposals

**No reasoned reader feedback this week.** The window carried three feedback events, all **bare up-votes** with `reason: ""` (health.json `feedback.by_stream`: ai-ml up 1, news up 1, science up 1; 0 down, 0 retractions, 0 unconsumed):

- 2026-09-15 · ai-ml · 👍 · `st-b0b4e37f2999` (the systematicity / "reasoning models fail logical twins" paper) — **deferred**: bare tap, below the reasoned-signal bar.
- 2026-09-16 · science · 👍 · `st-560c31d84281` (the UCSF speech+gesture BCI) — **deferred**: bare tap.
- 2026-09-19 · news · 👍 · `st-0e722578fca3` (the US–Denmark–Greenland accord) — **deferred**: bare tap.

All three landed on substantive primary-source stories — a mild positive reinforcement of the current direction — but a bare tap is noise, and none clears the ≥2-signals-on-distinct-stories bar, so **nothing is proposed** to reader-profile.md or source-weights.yml this run. The auto-apply grant is untouched (no dated line appended).

## Machine-readable proposals

Written this run:
- `proposals/reader-model-2026-09-20.json` — Patch 1 (news outlet rotation) and Patch 2 (weekend length), both `applied: false`. No reader-profile/source-weights entries (no reasoned feedback).
- `proposals/registry-2026-09-20.yml` — four `reach: direct → proxy` flips (anthropic.com, the-decoder.com, news.un.org, rts.ch) on writer-telemetry evidence, plus the plos.org and agu.org candidate adds from the scout; `applied: false`.

## Cross-week trend

The trajectory is flat-healthy with one genuine improvement (weekend balance back in band) and one newly-surfaced maintenance item (registry reach drift, which the computed footers made visible for the first time this week). No regression against 2026-09-13 on any dimension.

## Open questions for human review

1. **`origin/main` was force-rewritten this window.** The fire-start `git pull` reported a forced update (`a9446a8 → 3b1edc2`), and `health.json → continuity.off_main.commits_not_on_main` lists 17 commits (News/AI-ML/Usage/Drained for 09-14/09-15). **This is a false positive for the off-main stranding class, verified:** those "orphaned" commits are only reachable from the *stale local* `refs/heads/main` (the routine runs detached after the pull); the actual content — `_posts/2026-09-14-news.md`, `2026-09-15-news.md`, `2026-09-15-ai-ml.md` — is all tracked on the new `origin/main`, `remote_branches` is empty, and there is no `claude/*` diversion. **No content was lost.** But a history rewrite of `main` is unusual for this repo (the convention is direct commits to `main`), so it is worth knowing *what* rewrote it — a manual `git push --force`, a rebased reconcile, or something in the bridge. If it recurs, the `off_main` guard will keep firing this same false positive after every forced pull; consider whether metrics.py should exclude the stale local `main` ref (it compares `--all --not origin/main`, and `--all` re-admits local `main`).
2. **Registry `reach` records are drifting from reality** (§K). Four `direct` records are proxy-only in practice; the deterministic reach probes that are supposed to maintain the `reach:` field either are not running or are recording the evaluator-egress result. Worth confirming the probe job is alive.
3. **Two streams cannot reach the 30-unique-domains / 0.50-top5 diversity targets by design** (science: primary-journal universe; sports: young + JS-blocked league sites). Are those targets meant to apply to the weekly/narrow streams at all, or should the targets be stream-tiered? Three reviews running have now flagged science's top5_share 1.00 as "worst" when it is largely a small-denominator artifact.
