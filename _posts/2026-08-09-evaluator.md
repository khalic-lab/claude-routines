---
layout: single
title: "Weekly Pipeline Review — 2026-08-09"
date: 2026-08-09T11:45:38+02:00
categories: [evaluator]
published: true
---

# Weekly Brief Pipeline Review — 2026-08-09

_Coverage: briefs from 2026-08-03 to 2026-08-09._
_Files read: 6 news, 2 AI/ML (expect ~2), 1 science (expect ~1), 1 sports (expect ~1), 1 weekend, prior review found (2026-08-02, 7 days old)._

This was a quiet, healthy week for the pipeline — and, unusually, a week where nearly everything the previous evaluator flagged in code got fixed. The dominant story is not a regression: it is (a) the loop closing on four carried-over instrumentation defects and four registry reach flips, all now verifiably landed, and (b) a rough egress-proxy window that walled dozens of feeds at the CONNECT layer without dislodging a single stream's direct-fetch ratio, citation integrity, or discovery footer. The writers absorbed a bad-network week with honest gaps footers and reachable-source fallback. The one soft spot is discovery concentration (top-5 outlet share above target on every stream), which is largely downstream of the same egress wall.

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains 30d (worst stream: science/sports) | 10 | ≥30 | 🔴 |
| New domains this window (portfolio, [new source] tags) | 8 | ≥2–3/wk | 🟢 |
| Top-5 outlet share (worst stream: science) | 0.82 | ≤0.50 (→0.35) | 🔴 |
| Waiver rate (worst stream: weekend) | 1.00 | ≤50% | 🔴 |
| Discovery footer present (every brief) | 11/11 | 100% | 🟢 |
| T1 citation %                   | ≥40% (footer-sampled) | ≥40% | 🟢 |
| T3 leakage count                | 0     | 0      | 🟢 |
| Non-English citation % (portfolio) | ~20%+ (FR/DE Swiss+EU) | ≥10% | 🟢 |
| Link sample pass rate           | 5/20 (25%) | ≥90%   | ⚪ unmeasurable |
| Fabrication count               | 0     | 0      | 🟢 |
| Single-source rate (portfolio)  | ~6% (news 8.5%) | <20%   | 🟢 |
| Empty section instances         | 0     | <5     | 🟢 |
| Repeat rate (worst stream: news 0.17) | judge | judge | 🟡 |
| Direct-fetch ratio (portfolio)  | ~0.96 | ≥0.35  | 🟢 |
| Feeds with >50% fail rate       | ~15 (egress week) | 0 | 🔴 infra |
| Citations on `reach: blocked` domains w/o [via snippet] | 0 | 0 | 🟢 |
| Unconsumed feedback backlog     | 0     | 0      | 🟢 |
| Vendor-PR-lead share (AI/ML, §M) | ~10%  | ≤40%   | 🟢 |
| Aggregator-shape failures (§M, of 5) | 0 | 0–1    | 🟢 |
| Personalization misses (§M, of 5) | 0    | 0–1    | 🟢 |
| Identity reconcile (flagged sids) | 0/24 editions | 0 | 🟢 |
| Off-main self-delivery          | clean | clean  | 🟢 |

## A–N: Detailed findings

### A. Source diversity & discovery
Read from `_data/source-health.json` (30-day rolling). Per-stream: news `unique=33, new=26, top5=0.767, waiver=0.345, saturated=[letemps.ch, srf.ch]`; ai-ml `unique=23, new=20, top5=0.717, waiver=0.222`; science `unique=10, new=7, top5=0.818, waiver=0.75`; sports `unique=10, new=10, top5=0.615, waiver=0.667, saturated=[srf.ch]`; weekend `unique=22, new=16, top5=0.694, waiver=1.00`.

Two real signals here, and one that is not what it looks like:

- **Top-5 outlet share is above the ≤0.50 target on every stream** (science worst at 0.82). This is the window's main editorial-discovery deficit — but it is substantially *downstream of the egress wall* (dimension K). When the proxy 403s the diversity feeds (El País, France 24, DW, admin.ch, UN News), the streams fall back to the handful of **directly curl-reachable** anchors — SRF, Al Jazeera, Le Temps, arXiv, Nature — which mechanically inflates concentration. 08-03-news says this outright: "only srf.ch, aljazeera.com and letemps.ch were reachable… all three are flagged SATURATED, but no unsaturated source was reachable to substitute." The lever is not a diversity prompt patch (that would just generate waivers against a walled proxy); it is egress recovery plus continued dormant-domain pressure.
- **Science's `unique=10` is dormancy, not absence.** The registry carries **50+ science-affinity domains** — arXiv, Nature, Quanta, bioRxiv/medRxiv, eLife, PLOS, PNAS, LBL, Fermilab, NOIRLab, AAS Nova, ESO, MPG, plus a full Swiss block (ETHZ, EPFL, PSI, UNIGE, EMPA, WSL, UNIBE) and last week's landed scout candidates (physicsworld, symmetrymagazine, cerncourier). Only 10 were cited in 30 days. This is precisely the deficit **rm-1** (the 2026-08-02 science dormant-probe patch) was written to fix — and it **landed** (commit `7f8e440`). 08-05-science shows the new behavior working: it actively anchored three `last_cited=None` dormant registry domains (newscenter.lbl.gov, elifesciences.org, noirlab.edu) via proxy. 08-06-news did the same (reactivated dw.com and lemonde.fr, both dormant). Expect `unique_domains` to climb as the 30-day window rolls forward under the new probe discipline; keep monitoring rather than patching.
- **Tier distribution:** the computed footers sample heavily T1 (08-04-ai-ml: T1=10, T2=0, untiered=0). arXiv (hub, exempt) and Nature/journals dominate the papers streams; news leans T1/T2 wire and quality regional. T3 = 0% (policy holds). T1 ≥40% comfortably. 🟢
- **Linguistic/geographic:** news cited Le Temps, Le Monde, NZZ, DW, SRF (French/German), plus attempts at El País, ANSA, France 24. Non-English share is well above the 10% floor. Geographic origin spans CH/FR/DE/QA(AlJazeera)/US/UK. 🟢

### B. Aggregator leakage
`health.json → briefs.aggregator_leakage = []`. **Zero.** No HN/Reddit/X/Mastodon/Bluesky citations anywhere in the window. 🟢

### C. Link health
`linkcheck.py --check`: **5/20 resolve (2xx/3xx), 143 links total.** This is the direct-curl-vs-proxy artifact, not broken links or fabrication: the checker resolves only what direct curl reaches (letemps 200, srf 200, aljazeera 200, quanta 200), and ERR:56s everything proxy-gated — **every arXiv, Nature-article, doi.org, elife, noirlab, lemonde, forbes, axios, worldbank, bbc-sport URL** in the sample. Those are the exact domains the feeds table shows succeeding via `ok_proxy` (arxiv.org ok_proxy 45, api.biorxiv.org ok_proxy 64) or via curl only intermittently. I re-confirmed the wall directly: **7/7 direct-curl probes from this evaluator sandbox 403'd at the CONNECT tunnel** (eso, noirlab, aasnova, mpg, pnas, scipost, uzh — all `curl (56) CONNECT tunnel failed, response 403`). The evaluator holds no fetch-proxy bearer by design, so the automated claim-check half is **constrained to direct-reachable domains this run**. Of those I could reach and cross-read against the brief text (Le Temps Gaza-roadmap item in 08-07-news; SRF AHV item in 08-06-news; Al Jazeera Ukraine/Yemen items; Quanta neutrino/mantle item in weekend), the cited claims match the source framing — **no fabrications detected**. Reporting the dimension as **unmeasurable-by-automation this week** with a clean manual spot-check on the reachable subset. Not an egress *regression* in the writers' pipeline (their direct-fetch ratios are ≥0.91) — it is the evaluator's own bearer-less egress.

### D. Section vitality
`health.json → briefs.by_stream.*.empty_sections = []` across all streams. **Zero empty sections.** This is itself a fix landing: the 2026-08-02 **rm-4** false-positive class (anchor-free prose sections mis-flagged as empty) is gone — metrics.py now keys on non-whitespace body length (`_MIN_SECTION_CHARS = 200`, commit `4f6120e`). AI/ML omitting Lab-blogs / Benchmarks / Apple-Silicon on 08-07 is honest omit-don't-fill (no in-window substance), correctly not counted as empty. 🟢

### E. Coverage gap recurrence
Clustering the Gaps footers, the recurring gap is unambiguous and singular: **egress-proxy CONNECT failures**. 08-03-news ("proxy returned 403 for most feeds"), 08-04-news ("gateway 403 to elpais, France24, DW, UN News, AP…"), 08-07-ai-ml ("egress proxy blocked all non-arXiv hosts… WebFetch egress-blocked too"), 08-07-news ("connection-reset errors, curl ERR:56"), 08-08-news ("admin.ch and vd.ch feeds returned proxy errors"). This is ≥5 occurrences → structural, but it is **infrastructure, not a prompt-fixable content gap** (see Open questions). Secondary recurring gap: Swiss institutional portals (admin.ch, vd.ch, sfl.ch) served as JS shells / navigation-only — also not prompt-fixable.

### F. Triangulation rate
`single_source_rate`: news 0.085 (4/47), all other streams 0.000. Portfolio ≈ 6%. Well under the 20% target and the 25% per-stream ceiling. The 4 news single-source items are honestly tagged `[single-source]` (e.g. the Morocco/Spain AFP account, the Prince-Ali FIFA extortion allegation, the Bessent/Axios Hormuz claim) — appropriate use, not laziness. 🟢

### G. Tag discipline
Counts from `health.json → briefs.by_stream.*.tags`: ai-ml `{preprint:20, vendor PR:3, via snippet:5, new source:1}`; news `{new source:6, single-source:4, via snippet:4}`; weekend `{preprint:24, vendor PR:5}`; science `{preprint:1}`; sports `{new source:1}`.

- **`[preprint]`** on all arXiv items — verified on the 08-07-ai-ml sample (all 8 read carry it correctly).
- **`[vendor PR]`** correctly applied to vendor-authored papers (08-04-ai-ml DiffusionGemma/Google DeepMind, Qwen-CUA/Alibaba) — and crucially these are framed with *independent* explanation, not vendor copy (see §M).
- **`[via snippet]`** spiked to 5 in ai-ml — but all from the single egress-crippled 08-07 edition where "only export.arxiv.org was directly reachable" and industry items rested on WebSearch snippets. This is the proxy wall, not a structural feed failure; **not a rising trend** (the footer-derived `via_snippet` field reads 0, and prior weeks were low). Note, don't flag as regression.
- **`[new source]`** — 8 tags this window. Spot-check of 2 (nbcnews.com, balkaninsight.com): both genuine primary/quality outlets, not junk anchors. **But see the bookkeeping defect in Open questions**: `candidates.jsonl` is empty and 4 of the 8 tagged domains (pbs.org, worldbank.org, nystateofpolitics.com, aurora-lm-project.github.io) appear in neither `candidates.jsonl` nor `registry.yml` — the `[new source]` → candidate-capture funnel is not accumulating.

### H. Topic balance (weekend)
`health.json → briefs.weekend_balance`: `ml_items=20, science_items=16, ml_share=0.556`. Inside the [0.35, 0.65] band. Balanced. 🟢

### I. Repetition detection
`health.json → streams`: news `repeat_rate=0.170 (8 repeats / 14-day lookback)`, weekend `0.156 (5)`, all others 0. **Judgment:** the news repeats are the continuing Gaza/Israel-roadmap, Ukraine, and Yemen arcs — and they carry proper `[ongoing since …]` discipline (08-07-news Gaza item is tagged `[ongoing since 2026-07-30]` and advances with a genuinely new dated fact: Netanyahu's 5 Aug "not agreed" statement and the decoupling of disarmament from withdrawal). That is correct ongoing-story handling, not re-summary. Weekend's 0.156 is the 14-day lookback catching re-touched arXiv threads across editions — minor. 🟡 (acceptable, no action).

**Identity integrity:** `reconcile.py --root .` → **0 flagged, 0 resolved-by-merge, 24 editions checked**. No forked story ids (the 2026-07-07 Cuba class stays closed). 🟢

### J. Cross-week trend
Versus the 2026-08-02 review: the headline trend is **defect closure**. Last week reported 14 false-positive off-main commits and 3 false-positive empty sections; both are now **zero** (guards fixed). Push-failed-footer pollution (8 of 11 briefs last week) is **gone** — no brief this window carries a stale failure footer. Discovery is turning: science and news are now actively reactivating dormant registry domains rather than concentrating. Direct-fetch ratios remain excellent (all ≥0.91). The one flat-to-adverse trend is top-5 outlet share, held high by the egress wall rather than by writer behavior.

### K. Feed reachability & direct-fetch rate
**Per-stream direct-fetch ratio** (footer-derived, exact): news 0.915, ai-ml 1.00, science 1.00, sports 1.00, weekend 1.00 — **every stream above its ≥0.30–0.40 target**. The cited anchors are almost entirely direct-curl fetches; the proxy failures hit feeds the writers *tried* but then substituted away from. 🟢 on the binding per-stream metric.

**Per-feed (`health.json → briefs.feeds`), the sobering half.** ~15 feeds failed >50% of attempts this window. Fully walled (0 successes): **admin.ch (6 fail/0 ok), feeds.elpais.com (6/0), eso.org (4/0), swissinfo.ch (5/0), ansa.it (4/0), euronews.com (3/0), who.int (3/0), washingtonpost.com (3/0), worldbank.org (4/0)**. Heavily proxy-failing but partly reachable: theguardian.com (22 fail/15 ok_proxy), france24.com (15/1), news.un.org (15/6), huggingface.co (14/7), rss.dw.com (12/3), kyivindependent.com (11/1), timesofisrael.com (10/2), rts.ch (8/4), nzz.ch (6/5).

**Method comparison — the clear pattern:** the **direct-curl feeds are the reliable ones** (export.arxiv.org ok_curl 64, srf.ch 55, aljazeera.com 32, letemps.ch 14, quantamagazine.org 7, nature.com curl 7), while proxy-only domains carry high failure/retry counts (arxiv.org fail 42/ok_proxy 45, api.biorxiv.org fail 65/ok_proxy 64 — succeeds, just noisy on retries). Where curl AND proxy both fail (admin.ch, elpais, eso, swissinfo, ansa), **the egress proxy is the wall** — these need escalation, not a prompt patch (Open questions). No content was lost to it (writers substituted), but the diversity cost is real and shows up as §A concentration.

**Domains-that-shouldn't-be-cited check:** scanned the window's citations against registry `reach:` and `never:`. **Zero** citations of `reach: blocked`/`blocked-paywall` domains without a `[via snippet]` tag; no `never:` domain appeared; no retired/demoted domain as a primary anchor. 🟢

### L. Output volume
`words_mean` (footer-derived, exact) vs previous week: news 1250 (↑ from 1144, +9%), ai-ml 2662 (↓ from 2867), sports 1152 (↓ from 1348), weekend 6912 (↓ from 7077), **science 1399 (↑ from 1111, +25.9%)**. Only science crosses the +25% flag — but it is a **single post** with 7 healthy citations (not repetitive; repeat_rate 0), so the "growth" is single-sample variance, not a spend problem. No stream is both repetitive and long. No output-cap lever warranted. 🟢

### M. Editorial shape
- **Vendor-PR-lead share (AI/ML):** ~10%, well under the 40% flag. The `[vendor PR]`-tagged items (DiffusionGemma/Google, Qwen-CUA/Alibaba) are *research papers* framed with independent, reader-first explanation ("Google did not train it from scratch… spending fewer than 10% of that model's original training-token budget"), and the Industry section **leads with regulation** (EU AI Act enforcement from the European Commission's own release), not vendor announcements. Vendor framing is context, never the lead. 🟢
- **Aggregator-shape (5 leads sampled across streams):** 0 failures. Every lead cites a primary/wire source and adds judgment the source itself doesn't carry — the Yemen lead reconciles three conflicting tolls (government ≥30, pro-gov 45+, Houthi "hundreds") and says which can't be verified; the Meta/New Mexico lead adds the "template other states copy" framing; the Gaza lead states the contested characterization explicitly. Not "rewritten hackernews." 🟢
- **Personalization (5 stories sampled):** 0 misses. CH angle present where it exists (AHV pension-trust item in 08-06-news, Swiss desk on NZZ in 08-08-news, Schwingen/Super League in sports); no forced CH framing on genuinely global stories (Yemen, Thailand, PKK). 🟢

### N. Affiliation element
- **Coverage rate:** weekend 2 `(affiliation not listed)` / ~27 bylines ≈ 7% 🟢; science 1/7 ≈ 14% 🟢; ai-ml 6/24 ≈ 25% (08-04: 3, 08-07: 3) — a touch over the ~20% target, but every instance is footer-documented as *the source's own omission* ("MACRO and VaG rendered no institution text in their author blocks, so both are recorded (affiliation not listed) rather than guessed"), which is exactly the not-guessing discipline the element exists to enforce — not a skipped Step-C field. Acceptable; monitor if ai-ml stays >20%.
- **Halo audit (anti-prestige):** spot-comparing importance of unaffiliated/independent papers vs big-lab papers — the `(affiliation not listed)` MACRO layer-routing paper and the Aarhus/HKU/Berkeley agnostic-PAC theory paper both received full substantive treatment and prominent placement, while the vendor-lab papers carry `[vendor PR]` caveats. **No systematic downranking of unaffiliated work detected.** 🟢

## Prior proposals status

The 2026-08-02 proposal files (`reader-model-2026-08-02.json`, `registry-2026-08-02.yml`) are **all `applied: false` (unstamped)** — yet almost every one has **verifiably landed in code**. Rafael applied the fixes without stamping the proposal files, so I re-verified each against the source of truth:

- **rm-1** (science.md dormant-domain probe before waiving) — **APPLIED & VERIFIED.** Commit `7f8e440` ("science dormant-probe + Swiss pass"); confirmed by 08-05-science and 08-06-news actively reactivating `last_cited=None` domains.
- **rm-2** (publish.py re-verify HEAD against origin before writing push-failed footer) — **APPLIED & VERIFIED.** Commit `2f37ddb`; zero stale push-failed footers this window (was 8/11 last week).
- **rm-3** (metrics.py `--not origin/main` off-main guard) — **APPLIED & VERIFIED.** Commit `4f6120e`; `continuity.off_main.commits_not_on_main = []` this run (was 14 false positives, 3 weeks running).
- **rm-4** (metrics.py text-based section vitality) — **APPLIED & VERIFIED.** Same commit; `empty_sections = []` everywhere (was 3 false positives).
- **registry reach flips** (science.org, swissinfo.ch, cell.com, journals.aps.org → `proxy`) — **APPLIED & VERIFIED.** All four now show `reach: proxy` in `sources/registry.yml`.
- **Sports candidate promotions** (esv.ch, uci.ch → probation) — **NOT LANDED.** Both still `status: candidate`. Carried forward (see registry proposals).

This is the loop working — four multi-week-carried instrumentation defects finally closed. The only wrinkle: because the JSON/YAML stamps were never flipped, next week's evaluator would re-propose landed fixes as if new. See Open questions.

## Source scout (Sunday duty)

**Stream picked: science** (worst-deficit: lowest `new_domains` = 7; sports tied on `unique_domains`=10 but has higher `new_domains`=10). **Fetches used: 7** (all direct curl; ≤20 budget).

**Finding:** science's deficit is confirmed as **dormancy, not registry scarcity** — the registry already holds 50+ science-affinity domains (see §A), including last week's scout candidates (physicsworld, symmetrymagazine, cerncourier) which landed as `candidate`. So the high-value scout action was breadth at the edges plus a reach re-probe.

- **Re-probe of 5 stale science `reach: direct` domains** (eso.org, noirlab.edu, aasnova.org, mpg.de, pnas.org): all 5 returned `curl (56) CONNECT tunnel failed, response 403` from the evaluator sandbox. **I do NOT propose flipping these to `proxy`** — this sandbox holds no bearer, and the writers reached noirlab.edu / newscenter.lbl.gov / elifesciences.org fine via proxy in 08-05-science. The 403s are the evaluator's own egress wall, not the domains' truth. The finding is corroborating evidence for the egress-degradation flag, not a registry patch.
- **2 new candidates appended to `sources/candidates.jsonl`** (both `reach: proxy-needed`, direct-403 from this sandbox — writers vet at first citation): **scipost.org** (SciPost, community-run open-access peer-reviewed physics/science publisher; genuine primary, absent from registry) and **news.uzh.ch** (University of Zurich official newsroom; institutional primary for Swiss science personalization — registry has ETHZ/EPFL/UNIGE but not UZH).

## Patch proposals (for human review)

Given how clean the week is and how much just landed, only one prompt patch is warranted; everything else is egress-infra (Open questions) or already-fixed.

### Patch 1 — Weekend: probe dormant/institutional primaries before waiving discovery
**Target prompt:** Weekend
**Section affected:** Discovery / sourcing block
**Issue:** Weekend `waiver_rate = 1.00` — discovery was waived on the sole edition, with the honest reason that the week's new anchors were arXiv/bioRxiv/DOIs already in the registry and the one unregistered probe (`deepgrove`) resolved to the hf.co hub. But weekend leans on ~22 domains over 179 stories (top5 0.694), and its "Apple Silicon / local inference ecosystem" and "Cross-cutting threads" sections routinely discuss lab engineering blogs and institutional work that *are* citable primaries. This is the same dormancy pattern rm-1 fixed for science — where the identical patch is now demonstrably working.

**Proposed change:**

> **Before:**
> ```
> End with a Discovery footer: `- Discovery: met (…)` or `- Discovery: waived — <reason>`.
> ```
>
> **After:**
> ```
> Before waiving discovery, attempt at least two registered weekend-affinity domains with
> last_cited=None (dormant) from the preflight plan — institutional newsrooms, lab
> engineering blogs, and journal primaries — plus any genuinely-new primary the week's
> reading surfaced. Only waive if they are unreachable or off-topic, and name which were
> tried in the waiver reason. A new anchor that resolves to a hub domain (hf.co, github.com)
> does not count as a new primary. End with the Discovery footer as before.
> ```

**Why this helps:** the science version of this exact patch (rm-1) provably lifted dormant-domain reactivation; mirroring it on weekend should erode its 1.00 waiver rate and 0.69 concentration without fighting the egress wall.
**Risk:** low — if the dormant probes genuinely fail (egress week), the writer still waives honestly, just with named attempts; adds a small amount of research time.

## Reader-feedback → profile proposals

**Completeness (every reasoned event gets a disposition):** the window carries **17 feedback events** in the ledger (by `ts` in [2026-08-03, 2026-08-09]). **Zero are reasoned** — every one is a bare vote (`reason: ""`); there are no written reasons to enumerate. Aggregate tallies (`health.json → feedback.by_stream`): ai-ml 5 👍 / 0 👎, news 7 👍 / 0 👎 / 2 retractions, science 1 👍, sports 1 👍, weekend 1 👍. **Unconsumed backlog = 0** (bridge fold current). No downvotes anywhere.

Per the noise filter and the auto-apply grant (which explicitly excludes single bare taps and requires a repeated vote or a written reason), **none of this qualifies for a profile edit** — the 👍 signal is broad approval spread across distinct stories with no themeable source/section/reason, and the 2 news retractions are vote reversals, not directional signal. This is healthy positive reinforcement, not an instruction.

**No reader feedback (reasoned) this week.** No profile or source-weight edits proposed. `reader-profile.md` untouched this run.

## Machine-readable proposals

Written: `proposals/reader-model-2026-08-09.json` (Patch 1) and `proposals/registry-2026-08-09.yml` (carried sports candidate promotions; note reach flips already landed).

## Cross-week trend

Covered in §J. Net direction: **strongly positive** — the pipeline's instrumentation defects are closed, footer telemetry is now trustworthy (exact word counts, no false push-failed footers, no false empty-sections/off-main), and discovery discipline is spreading from science to news. The single adverse trend (top-5 concentration) is egress-bound and should recover with the proxy.

## Open questions for human review

1. **Egress-proxy degradation is the binding constraint — and it is not prompt-fixable.** ~15 feeds failed >50% this window; admin.ch, feeds.elpais.com, eso.org, swissinfo.ch, ansa.it were fully walled (0 successes, curl *and* proxy). The writers absorbed it cleanly (direct-fetch ratios stayed ≥0.91, honest gaps footers), but it inflates source concentration and cost source diversity. Is this a transient bad week or a tightening allowlist? Worth a dedicated egress-probe routine or an allowlist review — the same wall 403'd all 7 of my evaluator re-probes.
2. **`candidates.jsonl` is empty and the `[new source]` capture funnel isn't accumulating.** 4 of 8 domains tagged `[new source]` this week (pbs.org, worldbank.org, nystateofpolitics.com, aurora-lm-project.github.io) appear in neither `candidates.jsonl` nor `registry.yml`. The tag is supposed to auto-enter the domain as a candidate; either that write isn't firing or the file was reset without those domains promoting. Low severity (report-only machinery), but the discovery-candidate funnel is meant to accumulate, and right now it starts from empty each week. (I appended 2 scout candidates, so the file now has 2 lines.)
3. **Proposal stamps are lagging code reality.** Every 2026-08-02 fix landed in code but none of the proposal files were stamped `applied: true`. The stamp is the loop's verification handle; unstamped-but-landed forces the evaluator to re-verify by hand (as this run did) and risks re-proposing done work. Worth flipping the stamps on `reader-model-2026-08-02.json` (rm-1..rm-4) and `registry-2026-08-02.yml` (the four reach flips) so the loop stays honest.
