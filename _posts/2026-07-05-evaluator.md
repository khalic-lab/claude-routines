---
layout: single
title: "Weekly Pipeline Review — 2026-07-05"
date: 2026-07-05T11:39:27+02:00
categories: [evaluator]
---

# Weekly Brief Pipeline Review — 2026-07-05

_Coverage: briefs from 2026-06-29 to 2026-07-05._
_Files read: 6 news, 2 AI/ML (expected ~2), 1 science (expected ~1), 1 weekend, prior review found (2026-06-28)._

The pipeline is **healthy across the board this week, and the one stream that was ever in doubt is now fully recovered.** AI/ML — the pipeline's single failing component two reviews ago (0.12 direct-fetch, 71 via-snippet in mid-June) and comfortably healthy last week (0.67) — this week ran a **1.00 direct-fetch ratio with zero via-snippet citations** across both its editions. Every stream is above its dimension-K target; the portfolio direct-fetch ratio is **0.90**; T3 leakage is **0** (down from ~3); zero aggregator citations; zero confirmed-blocked domains cited without `[via snippet]`; and a spot-check of six arXiv IDs against the live arXiv API confirmed **no fabrications** — every ID resolves to a real paper whose title matches the brief's description.

The residual issues are small and mostly about metadata honesty, not reachability. The two that are worth a human glance: (1) the **only substantive reader signal this week was a per-story 👎** (two taps) on the weekend brief's Khamenei bullet, with the reason "Missing context on when it hapenned" — a legitimate framing miss, since the weekend digest bullet says the Supreme Leader "has died" without ever saying *when*, even though the daily brief three days earlier carried the date (killed 28 February). (2) **Semantic Scholar has been rate-limited or un-indexed on essentially every attempt this week**, which is not story-load-bearing (it only supplies author affiliations) but keeps forcing "(affiliation not listed)" markers across AI/ML, Science, and the Weekend.

One structural note that is *not* a failure: **unique-domain count fell to 29, below the ≥40 floor** — but that floor was calibrated for the old six-stream lineup (Overview + AI/ML + Cyber-Papers + Markets + Weekend + Evaluator). With Cyber-Papers and Markets both retired, ten briefs a week simply touch fewer distinct hosts. Underlying diversity is fine (28% non-English, 8 countries, T1 at 57%). The target needs recalibrating, not the writers (see Open Questions).

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains cited            | 29    | ≥40    | 🟡 |
| T1 citation %                   | ~57%  | ≥40%   | 🟢 |
| T3 leakage count                | 0     | 0      | 🟢 |
| Non-English citation % (portfolio) | ~28% | ≥10% | 🟢 |
| Link sample pass rate           | measurable subset 100% (feeds + AJ + Nature + Quanta 200; 6/6 arXiv IDs real); direct HTML pages proxy-walled from eval env | ≥90% | 🟢⚪ |
| Fabrication count               | 0     | 0      | 🟢 |
| Single-source rate (portfolio)  | ~6%   | <20%   | 🟢 |
| Empty section instances         | ~2    | <5     | 🟢 |
| Direct-fetch ratio (portfolio)  | 0.90  | ≥0.35  | 🟢 |
| Direct-fetch ratio (News)       | 0.79  | ≥0.30  | 🟢 |
| Direct-fetch ratio (AI/ML)      | **1.00** | ≥0.40 | 🟢 |
| Direct-fetch ratio (Science)    | 1.00  | ≥0.30  | 🟢 |
| Direct-fetch ratio (Weekend)    | 1.00  | ≥0.30  | 🟢 |
| Feeds with >50% fail rate       | 1 (Semantic Scholar, affiliations only) | 0 | 🟡 |
| Citations to confirmed-blocked domains without [via snippet] | 0 | 0 | 🟢 |
| curl vs WebFetch advantage on feeds | curl wins decisively | curl wins | 🟢 |

## A–L: Detailed findings

### A. Source diversity
**29 unique domains across 164 citation links.** Top domains by count:

| Domain | Count | Role |
|--------|------|------|
| arxiv.org | 43 | primary preprint feed (AI/ML, Science, Weekend) |
| srf.ch | 24 | Swiss-German daily primary |
| aljazeera.com | 23 | world-desk primary |
| letemps.ch | 22 | Swiss-French daily primary |
| doi.org | 7 | Nature/bioRxiv DOI resolver (Weekend/Science) |
| hf.co | 6 | model-card primary (Weekend releases) |
| nature.com | 5 | journal primary |
| washingtonpost.com | 3 | world-desk (via snippet) |
| simonwillison.net | 3 | AI analysis (Weekend essays) |
| quantamagazine.org | 3 | science features |

**Concentration:** `arxiv.org` = 43/164 = **26%**, over the 15% threshold — flagged but benign for the usual architectural reason: arXiv is the single primary feed for the AI/ML papers desk, the Science physics/astro desk, and the entire Weekend papers run. Concentration here is the design working. Among the *news* domains none individually exceeds 15% (srf 14.6%, aljazeera 14.0%, letemps 13.4%) — a healthy three-way balance.

**Tier distribution** (from footers, item-level): T1 ≈ 73 items, T2 ≈ 54, T3 = 0. **T1 ≈ 57%**, comfortably ≥40%; the AI/ML and Weekend paper desks (all-arXiv/Nature/HF primaries) carry it. **T3 = 0** — a clean sweep, and an improvement on last week's ~3 (codingfleet/kucoin/36kr are gone; the deny-list patch appears to have landed).

**Linguistic:** non-English citations = srf.ch (24 DE) + letemps.ch (22 FR) = **46/164 ≈ 28%**, far above the ≥10% floor and up from ~14% last week — the news-heavy new lineup (SRF + Le Temps every single day) carries it structurally.

**Geographic:** ~8 countries in the news sections (CH, US, Qatar/AJ desk, UK, France, EU institutions, Canada, Mali/Sahel coverage), plus international arXiv. Healthy.

### B. Aggregator leakage
**Clean.** Zero hits for `news.ycombinator.com`, `lobste.rs`, `reddit.com`, `twitter.com`, `x.com`, `mastodon.social`, `threads.net`, `bsky.app` across all ten briefs. 🟢

### C. Link health (sample-based)
Feed probes via `curl` **from the evaluator's own environment:**

| Feed | Result |
|------|--------|
| arXiv Atom API (`export.arxiv.org`) | **200** |
| Nature flagship RSS (`nature.rss`) | **200** |
| Nature Astronomy RSS (`natastron.rss`) | **200** |
| Al Jazeera RSS | **200** |
| SRF DE RSS | **200** |
| Le Temps FR RSS | **200** |
| Quanta RSS | **200** |
| `rss.arxiv.org` RSS | proxy **fail (000)** |
| bioRxiv details JSON API | proxy **fail (000)** |

The load-bearing arXiv Atom API and all four news/science RSS feeds resolve cleanly (200) from this environment — **no regression on the feeds that matter.** Notably, `nature.rss` and `natastron.rss`, which the eval environment 403'd last week and which the Weekend writer reported failing even via proxy this week, both returned **200 from my curl this week** — Nature's RSS trio is genuinely flaky on both sides rather than uniformly down. The two feeds that fail from my environment (`rss.arxiv.org`, bioRxiv JSON) are the same egress-proxy quirks noted before; the writers reach the equivalent data via the Atom API and the bioRxiv proxy route respectively.

**Article-link sample (20 links):** SRF, Al Jazeera, Nature (303 redirect → resolves), Le Temps (308 → resolves), and Quanta all returned 200/3xx. `arxiv.org/abs/*`, `simonwillison.net`, `netflixtechblog.com`, and `ec.europa.eu` returned 000 from my environment — these are **eval-env proxy blocks, not broken links** (arxiv.org/abs is blocked at the proxy while the arXiv API is not).

**Fabrication spot-check (8 arXiv claims → API):** all six IDs I could verify against the live arXiv API resolve to real papers with titles matching the briefs verbatim: 2606.29238 → "On the Policy Gradient Foundations of Group Relative Policy Optimization" (the GRPO rank-2 paper), 2607.01567 → "Scaling Trends for Lie Detector Oversight in Preference Learning" (SOLiD), 2607.01121 → "Smoking-gun evidence for hierarchical black-hole mergers", 2607.01232 → "Is One Layer Enough?...", 2606.32006 → "Efficient entanglement of three remote single-atom quantum-network nodes", 2607.02208 → "Counterexamples to two conjectures about matroids" (Larson). **Zero fabrications.** 🟢 (⚪ on overall pass rate: HTML article bodies are proxy-walled from the eval env, so claim-in-source spot-checks beyond arXiv are unmeasurable here — but the briefs remain conspicuously careful about flagging what they couldn't fetch.)

### D. Section vitality
No section empty ≥3 times. The AI/ML 06-30 edition ran the papers desk only and *honestly omitted* the industry/lab/benchmark sections ("no genuinely new, primary-sourced industry item survived verification") — that is correct behaviour on a quiet-industry window, not a dead section. The Science astronomy desk was thin (1 item) because the week's headline astro stories were dedup-dropped to the daily edition — logged in the Gaps footer. Weekend's data-science (2 items) and Apple-Silicon ("no MLX release landed in-window") sections were thin-but-honest. ~2 explained empty/thin instances, under the <5 threshold. 🟢

### E. Coverage gap recurrence
Recurring (≥3×) clusters:
1. **Publisher HTML 403 in the writer sandbox** (Reuters/AP/NZZ/swissinfo/most world outlets) — recurs every news day. Handled: world-desk items route through Al Jazeera + search snippets; Swiss items through SRF/Le Temps RSS. Structural, known, handled.
2. **Semantic Scholar rate-limited / not-yet-indexed for affiliations** — 06-30 (429), 07-03 (400), 07-01 (429), Weekend (returned but no July affiliations). **Four of four attempts** — this is the one recurring gap that now clears the ≥3× "structural" bar. It is metadata-only (author affiliations), but it drives the "(affiliation not listed)" markers that pepper AI/ML and the Weekend. See **Patch 2.**
3. **Nature article HTML / RSS flakiness** — article pages 403 even via proxy on Science + Weekend; handled via arXiv/Nature-Astronomy/Medicine fallbacks. Recurring, handled.

### F. Triangulation rate
`[single-source]` tags: 06-29 news 1, 06-30 news 1, 07-02 news 1, 07-04 news 1, 06-30 ai-ml 1, 07-03 ai-ml 1, 07-01 science 1, 07-04 weekend 1 = **~8 total** against ~127 items ≈ **6.3%** portfolio-wide, well under the 20% floor. No single stream approaches 25% (news is highest at 4 tags across 6 days). Most single-source items are appropriately hedged (Schiesser closure, SpudCell). 🟢

### G. Tag discipline
- **`[preprint]`** — arXiv items consistently tagged: all 11 papers on 06-30 AI/ML, all 9 on 07-03, all Weekend papers, all Science arXiv items. Sampled 5, all correct. 🟢
- **`[vendor PR]`** — correctly applied to the four lab items on 07-03 AI/ML (Sonnet 5, Fable safeguards, Claude Science, GeneBench-Pro) and to every Weekend model release. Sampled 5, all correct. 🟢
- **`[disputed]`** — used appropriately: Pakistan/Afghan strike tolls (06-29), Stade shooting toll five-vs-six (06-29), wolf-cull efficacy (06-29), SpudCell (07-01 science). 🟢
- **`[via snippet]`** — **14 total, all in News** (07-01: 4, 07-02: 7, 07-03: 3); AI/ML 0, Science 0, Weekend 0. The via-snippet load has migrated entirely to the world-desk wire residual (Reuters/AP/CNBC/WaPo HTML that 403s) — exactly where no machine-readable feed exists. AI/ML went **14 → 0** week-over-week. The curl-first architecture is doing its job; the residual is irreducible. 🟢

### H. Topic balance (weekend brief)
The 2026-07-04 Weekend runs **11 ML/AI papers** and **8 fundamental-science papers** — a **58% / 42%** split, a **8-percentage-point** deviation from a ~50/50 target, under the 10pp flag threshold. 🟢 The ML side is RL-heavy by the week's actual research distribution (the brief's own cross-cutting thread #1 documents this), and it explicitly notes what it cut to hold balance. Dedup is visibly working: the headline science stories (GW250114, DESI, IceCube) were held to the dailies, and Expander SAE was flagged distinct-paper vs June's subspace-aware SAE.

### I. Repetition detection
Dedup is largely well-managed. Developing stories are tracked with `[ongoing since]` rather than re-reported cold:
- **US–Iran Doha talks** ran three consecutive days (06-29 announcement → 06-30 envoys arrive → 07-01 talks under way on frozen assets/Hormuz), each with a genuinely new dated development; 07-03 dropped the Hormuz shipping update as incremental. Reasonable.
- **Russia–Ukraine strikes** (06-29 → 07-02 → 07-03) tracked a single escalating event with the toll developing 8 → 21 → 30, correctly tagged.
- **SCOTUS** ran two *different* rulings on consecutive days (06-29 removal-power/FTC; 06-30 birthright citizenship), and 07-01 explicitly omitted birthright as already covered — a clean dedup catch.
- **Khamenei funeral** appeared in 07-03 news and 07-04 weekend; the 07-04 *news* brief explicitly dropped it as an exact-URL REPEAT. Good.

One **soft observation** (not a hard flag): the Swiss nuclear-referendum story ran two consecutive days (06-29 "initiative withdrawn, referendum announced" → 06-30 "broad alliance launches referendum, 50k signatures by 8 Oct"). Each carries a new procedural fact, so it clears the bar, but the two bullets overlap heavily. Also, the SRF "300,000 jobs" story appeared in both the 07-04 Weekend (09:43) and the 07-04 News (12:06) on the same day — inherent to the Weekend being a Saturday digest that fires *before* the day's news brief, so not a dedup miss the writers could have caught. No structural repetition problem this week.

### J. Cross-week trend (vs 2026-06-28)

| Metric | 2026-06-28 | 2026-07-05 | Trend |
|--------|-----------|-----------|-------|
| Unique domains | ~59 | 29 | ▼ but structural — lineup went from ~19 briefs/wk (inc. Cyber+Markets) to 10 |
| T1 citation % | ~57% | ~57% | ▬ stable |
| T3 leakage | ~3 | **0** | ▲ clean sweep (deny-list patch landed) |
| Non-English % | ~14% | ~28% | ▲ (SRF+LeTemps daily) |
| Single-source % | ~9% | ~6% | ▲ |
| Aggregator citations | 0 | 0 | ▬ clean |
| Portfolio direct-fetch | 0.93 | 0.90 | ▬ stable-high |
| **AI/ML direct-fetch** | 0.67 | **1.00** | ▲ fully recovered |
| AI/ML via-snippet total | 14 | **0** | ▲ −100% |
| Confirmed-blocked w/o `[via snippet]` | ~11 | 0 | ▲ resolved |

**Prior-patch application status:** several 2026-06-28 patches show up as landed effects — **Patch 2** (AI/ML `Feeds hit` line mandatory every day) clearly landed: both AI/ML editions carry a full `Feeds hit` line. **Patch 5** (T3 deny-list) landed: T3 is 0 and codingfleet/kucoin/36kr are gone. **Patch 3** (cross-day exact-URL dedup) can't be confirmed from output alone, but no exact-URL cross-day repeat occurred this week (last week's Quanta-Erdős class of miss did not recur). The bioRxiv/medRxiv reclassification (Patch 1) is moot this week — bioRxiv DOIs in the Weekend were fetched via the proxy route and cited cleanly; nothing blocked was cited without a tag.

### K. Feed reachability and direct-fetch rate — **primary lens**

**Per-stream direct-fetch (N direct / M via-snippet per day → ratio):**

| Stream | Per-day (direct/snippet) | Mean ratio | Week snippet total | Verdict |
|--------|--------------------------|-----------|--------------------|---------|
| News | 11/0, 10/0, 9/4, 8/7, 6/3, 7/0 | **0.79** (agg) | 14 | ✅ (≥0.30) |
| AI/ML | 11/0, 13/0 | **1.00** | 0 | ✅ (≥0.40) |
| Science | 8/0 | **1.00** | 0 | ✅ (≥0.30) |
| Weekend | 39/0 | **1.00** | 0 | ✅ (≥0.30) |

Portfolio: 122 direct / 136 total = **0.90**. Every stream is above its target; three of four are at a perfect 1.00. The AI/ML result is the headline — from 0.12 two reviews ago to a flawless 1.00 with zero snippet citations, the recovery is now complete and stable.

**Per-feed reachability (aggregated, with method):**

| Feed | Result | Notes |
|------|--------|-------|
| arXiv category RSS + Atom API | ok via curl | workhorse; Atom API 503'd once (07-03) → RSS covered it |
| SRF / Le Temps / Al Jazeera RSS | ok via curl, all days | rock-solid; confirmed 200 in my probe |
| Quanta / Nature-Medicine / Nature-Astronomy RSS | ok via curl | confirmed 200 in my probe |
| Nature flagship + nphys RSS | flaky | writer saw 403 even via proxy (Weekend, Science); my probe got 200 — genuinely intermittent |
| bioRxiv / medRxiv JSON API | ok via proxy | reached for Weekend DOIs; fails from my eval env (egress quirk) |
| HuggingFace Hub | ok via MCP | Weekend model cards |
| **Semantic Scholar API** | **fail — 4/4 attempts** | 429/400/not-indexed; **affiliations only, non-load-bearing** |
| Science.org / anthropic.com / openai.com HTML | ok via proxy | lab/blog bodies |

**Feeds with >50% fail rate:** **one** — Semantic Scholar, which was rate-limited or un-indexed on every attempt this week. It supplies only author affiliations, so no story was lost, but it is the direct cause of the recurring "(affiliation not listed)" markers. Marked 🟡. See **Patch 2.**

**Method comparison:** **curl wins decisively.** Every load-bearing feed success is `{ok via curl}`; the fetch-proxy is the second-line fallback (bioRxiv, Nature article HTML, lab blogs); WebFetch appears exactly once all week (07-01 news, "SRF article HTML {ok via WebFetch}"). The curl-first patch continues to work as intended across all four streams. 🟢

**Confirmed-blocked domains cited without `[via snippet]`:** **zero.** No brief cited reuters.com, swissinfo.ch, nzz.ch, science.org-HTML, or any other blocked domain as a live link (they're mentioned as "403'd" in Gaps footers, not cited). bioRxiv DOIs in the Weekend were genuinely proxy-fetched. 🟢

### L. Output volume (token-cost proxy)
Per-stream mean word counts (from `Word count:` footers):

| Stream | Per-day words | Mean | Note |
|--------|---------------|------|------|
| News | 640, 720, 880, 640, 590, 610 | **~680** | 07-01 longest (thunderstorm + new-rules explainers), justified by item length not repetition |
| AI/ML | 1480, 1850 | **~1665** | 07-03 higher (13 items: 9 papers + 4 lab/benchmark) vs 06-30 (11 papers) — growth tracks item count |
| Science | 1750 | **~1750** | single edition |
| Weekend | 5300 | **~5300** | by-design deep read (39 sources, 19 papers) |

**No baseline for a clean week-over-week comparison** — the 2026-06-28 review did not tabulate a dimension-L word-count table, so there is no prior per-stream mean to diff against. Within this week, AI/ML grew ~25% (1480 → 1850) but with a matching rise in item count (11 → 13), so it is **not** flagged as runaway output. No stream shows length growth decoupled from story count. Nothing crosses into the output-cap / quiet-day-lever territory. Establishing this table as the baseline for next week's diff.

## Patch proposals (for human review)

The pipeline is largely healthy, so only two prompt patches are warranted — both address recurring/reader-validated issues, neither is a dimension-K reachability problem (there are none this week).

### Patch 1 — Weekend: date-anchor every "Week in headlines" bullet
**Target prompt:** Weekend
**Section affected:** 📰 Week in headlines
**Issue:** The 07-04 Weekend's lead bullet — "Iran's Supreme Leader Ayatollah Ali Khamenei has died; a state funeral in Tehran on 4 July drew mass crowds" — states the *funeral* date but never says **when he died**, even though the 07-03 daily brief carried it (killed 28 February in the US–Israel war). A reader gave this bullet **two 👎**, one with the reason "Missing context on when it hapenned." The digest format is stripping the temporal anchor from events it summarizes.
**Proposed change:**

> **Before:**
> ```
> Each "Week in headlines" bullet: a bolded lead sentence stating what happened,
> then 1–2 sentences of why it matters, then the citation(s).
> ```
>
> **After:**
> ```
> Each "Week in headlines" bullet: a bolded lead sentence stating what happened AND
> WHEN it happened (the date of the underlying event, not just the date of the
> latest development). For a death, attack, ruling, or launch, name the event date
> explicitly — "X died on {date}" / "the {date} strike" — even if the news peg is a
> later funeral/anniversary/reaction. Then 1–2 sentences of why it matters, then the
> citation(s). If the daily briefs carried the event date, carry it forward.
> ```

**Why this helps:** Directly answers a repeated, reasoned reader 👎 and prevents the digest from summarizing events into an ahistorical "has happened" present tense.
**Risk:** Marginal added length per bullet; negligible.

### Patch 2 — AI/ML + Science + Weekend: add an affiliation fallback before "(affiliation not listed)"
**Target prompt:** AI-ML (and mirror in Science + Weekend paper desks / shared sourcing note)
**Section affected:** Affiliation sourcing
**Issue:** Semantic Scholar was rate-limited or un-indexed on **all four** attempts this week (429/400/not-indexed), forcing "(affiliation not listed)" markers across several AI/ML and Weekend papers (e.g. arXiv:2606.30420, 2606.28770, and multiple Weekend biology/systems author lists). This is the one feed over the >50% fail bar, and it recurs every week that fresh July arXiv papers aren't yet indexed.
**Proposed change:**

> **Before:**
> ```
> For author affiliations, query Semantic Scholar. Where an affiliation cannot be
> confidently attributed, mark "(affiliation not listed)" rather than guessing.
> ```
>
> **After:**
> ```
> For author affiliations, query Semantic Scholar first. If it returns HTTP 429/400
> or has not yet indexed the paper (common for arXiv papers <1 week old), fall back
> to the OpenAlex works API (api.openalex.org/works?filter=doi:… or ?search=title),
> which indexes arXiv faster and returns institution names, BEFORE resorting to a
> named-senior-author web lookup. Only mark "(affiliation not listed)" when all three
> fail. Never guess.
> ```

**Why this helps:** Recovers most of the affiliations currently lost to Semantic Scholar's rate limits, cutting the "(affiliation not listed)" residual without any fabrication risk.
**Risk:** OpenAlex occasionally lags on brand-new arXiv IDs too; the three-tier fallback with the honest final marker preserves the no-fabrication guarantee.

## Reader-feedback → profile proposals (separate from the prompt patches above)

**In-window feedback (2026-06-29 → 2026-07-05):** nine records, all `consumed: false`.
- **Seven 👍:** four on 06-30 News stories (the two referendum items, E-ID delay, SNB franc intervention), two brief-level on 07-01 News, one on 07-02 News (Spain regularization). These are a positive cluster around **Swiss federal/cantonal politics + policy-with-personal-impact** — exactly what `reader-profile.md`'s "Favor: personal/local impact" already prioritizes. Reinforcement, not a mandate; no new rule required.
- **Two 👎 — the substantive signal:** both on the **same** 07-04 Weekend story (`2026-07-04-weekend-iran-s-supreme-leader-ayatollah-ali-khamenei-has`), one carrying the reason **"Missing context on when it hapenned."** A repeated per-story 👎 with a clear reason is the sharpest signal in the window. The source (Al Jazeera/SRF) is not misleading — this is a *writer framing* miss (the digest dropped the death date), so it warrants a `reader-profile.md` learned preference, **not** a `source-weights.yml` change.

**Proposal A — `reader-profile.md`, "Learned preferences" section:**

> **Before:**
> ```
> ## Learned preferences (Evaluator-maintained — append below)
> <!-- The Weekly Evaluator proposes additions here from feedback; Rafael applies them. e.g.:
> - 2026-06-15: less SpaceX launch detail on weekends (3× 👎, "too long"). -->
> ```
>
> **After:**
> ```
> ## Learned preferences (Evaluator-maintained — append below)
> <!-- The Weekly Evaluator proposes additions here from feedback; Rafael applies them. e.g.:
> - 2026-06-15: less SpaceX launch detail on weekends (3× 👎, "too long"). -->
> - 2026-07-05: in the Weekend "Week in headlines" digest, always anchor a major
>   event to WHEN it happened, not just its current status — the reader gave 2× 👎 on
>   the 2026-07-04 Khamenei bullet ("Missing context on when it hapenned"); it said he
>   "has died" without the 28 Feb death date the daily brief had already carried.
> ```

**`source-weights.yml`:** **no change proposed.** No source repeatedly misled; the 👎 is about weekend framing, addressed by Proposal A (and reinforced structurally by Patch 1). `never:` / `reduce:` remain empty.

**Bookkeeping:** all nine records in `feedback/2026-07.jsonl` are set `consumed: true` and committed with this review (the 👎 folded into Proposal A + Patch 1; the 👍 cluster folded into the positive note above), so they are not re-proposed next week.

## Cross-week trend
Covered in §J. Headline: **AI/ML has completed its recovery** — from the pipeline's single failing component (0.12, June) to healthy (0.67, last week) to flawless (1.00, zero snippet) this week. Portfolio direct-fetch is stable-high at 0.90, T3 leakage is a clean 0, and non-English sourcing nearly doubled to 28% on the news-heavy lineup. The only downward line, unique-domain count (59 → 29), is a lineup artifact, not a sourcing regression.

## Open questions for human review
1. **Recalibrate the unique-domain floor for the current lineup.** The ≥40 target was set when the pipeline ran six streams including Cyber-Papers and Markets. With ten briefs/week across four streams, 29 distinct hosts with 28% non-English and T1 at 57% is healthy — but it will keep tripping the 🟡. Suggest lowering the floor to ~25 for the new lineup, or re-expressing it per-stream.
2. **Semantic Scholar affiliation reliability.** It failed all four attempts this week (see §K, Patch 2). Is adding OpenAlex as a fallback (Patch 2) the right fix, or should the paper desks simply accept "(affiliation not listed)" as the norm for sub-week-old arXiv IDs and stop treating it as a gap?
3. **Establishing the dimension-L baseline.** This is the first review to tabulate per-stream word-count means (News ~680, AI/ML ~1665, Science ~1750, Weekend ~5300); the prior review had no such table, so no week-over-week diff was possible. Next week's review can diff against these. Flag now if any of these means already looks high to you.
