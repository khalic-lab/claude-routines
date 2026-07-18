---
layout: single
title: "Weekly Pipeline Review — 2026-07-12"
date: 2026-07-12T11:45:00+02:00
categories: [evaluator]
published: true
---

# Weekly Brief Pipeline Review — 2026-07-12

_Coverage: briefs from 2026-07-06 to 2026-07-12._
_Files read: 6 news, 2 AI/ML (expected ~2), 1 science (expected ~1), 1 weekend, prior review found (2026-07-05, 7 days old)._

The pipeline is **mechanically healthy but carries one real editorial defect this week**: the Weekend brief shipped **two Al Jazeera citations whose URLs do not resolve (HTTP 404)** — including its lead "Week in headlines" bullet, which a reader downvoted with a reason that turns out to be a genuine factual error. Everything the automated dimensions measure is green or structurally-explained-green (aggregator leakage 0, T3 leakage 0, direct-fetch 0.89, feedback backlog 0, reconcile clean, no off-main diversion, all four prior patches applied and verified). But dimension C caught something the scripts can't: fabricated-or-dead links in the one brief that synthesizes from memory rather than fetching fresh. That is the headline, and Patch 1 targets it.

The secondary story is **discovery health diverging by stream**. AI/ML is genuinely diverse (37 domains, top-5 share 0.46, 21 new domains/30d). News is discovering aggressively (19 new domains this month) but still anchors 88% of its citations on three workhorses (SRF, Le Temps, Al Jazeera) because those are the only feeds that curl cleanly. Science is the deficit stream — **3 unique domains, top-5 share 1.00** — and the Sunday scout picked it. The twist: the registry is *not* candidate-starved for science (it already lists esa.int, cern.ch, journals.aps.org, science.org, nasa.gov as `reach: direct`), yet the 08 July Science writer reported all of APS/Science.org/CERN returning HTTP 0. The constraint is a **recorded-vs-realized reachability gap**, not a missing-source gap.

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains 30d (worst stream, source-health) | science 3 | ≥30 | 🔴 (structural — weekly, 13 stories/30d) |
| New domains this window (portfolio, source-health) | ~9 `[new source]` tags | ≥2–3/wk | 🟢 |
| Top-5 outlet share (worst stream, source-health) | science 1.00 / news 0.88 | ≤0.50 | 🔴 |
| Waiver rate (worst stream, source-health) | science 0.50 | ≤50% | 🟡 |
| Discovery footer present (every brief) | 9/10 (07-06 news missing) | 100% | 🟡 |
| T1 citation %                   | ~46%  | ≥40%   | 🟢 |
| T3 leakage count                | 0     | 0      | 🟢 |
| Non-English citation % (portfolio) | ~27% | ≥10%   | 🟢 |
| Link sample pass rate           | feeds 100%; **2 weekend AJ links 404** | ≥90% | 🔴⚪ |
| Fabrication count               | **2** (weekend AJ dead links) | 0 | 🔴 |
| Single-source rate (portfolio)  | ~14%  | <20%   | 🟢 (news 25% 🟡) |
| Empty section instances         | 0 (≥3×) | <5    | 🟢 |
| Repeat rate (worst stream, health.json) | news 0.21 | judge | 🟢 (ongoing-tracking) |
| Direct-fetch ratio (portfolio)  | 0.89  | ≥0.35  | 🟢 |
| Feeds with >50% fail rate       | 1 (Semantic Scholar, affiliations only) | 0 | 🟡 |
| Citations on `reach: blocked` domains without [via snippet] | 0 | 0 | 🟢 |
| Unconsumed feedback backlog (health.json) | 0 | 0 | 🟢 |
| Vendor-PR-lead share (AI/ML, §M) | ~40%  | ≤40%   | 🟡 |
| Aggregator-shape failures (§M, of 5) | 1 (weekend fabricated lead) | 0–1 | 🟡 |
| Personalization misses (§M, of 5) | 0    | 0–1    | 🟢 |

## A–N: Detailed findings

### A. Source diversity & discovery (source-health.json)
Per-stream, computed:

| Stream | stories | unique_domains | new_domains | top5_share | waiver | saturated |
|--------|---------|----------------|-------------|-----------|--------|-----------|
| ai-ml | 116 | 37 | 21 | 0.459 | 0.05 | — |
| news | 108 | 19 | 19 | **0.877** | 0.00 | aljazeera.com, letemps.ch |
| science | 13 | **3** | 3 | **1.00** | 0.50 | nature.com |
| weekend | 171 | 29 | 22 | 0.604 | 0.20 | — |

**AI/ML is the model stream** — top-5 outlet share 0.46 is already inside the *steady-state* ≤0.35→0.50 band, 21 new domains over 30 days is 2× the ≥10/mo target, waiver rate 0.05. No action.

**News discovers well but concentrates by necessity.** 19 new domains this month (thenationalnews, euromaidanpress, apnews, state.gov, climate.copernicus.eu, thehill, timesofisrael, euronews, cbsnews, kyivindependent…) is healthy discovery. But top-5 outlet share sits at **0.88** and Al Jazeera + Le Temps are both flagged saturated. Reading the Gaps footers, this is honest and reachability-bound, not lazy: the world desk routes through Al Jazeera because Reuters/AP/NZZ/Korea Herald HTML 403s in the sandbox (07-10: "Korea Herald blocked even via proxy"; 07-08: "No Reuters /world feed reachable"), and the Swiss desk has only SRF (DE) and Le Temps (FR) as curl-able primaries. The new domains are landing as *second* anchors, not displacing the workhorses. The lever is reachability (Patch/registry), not writer effort.

**Science is the deficit stream and the scout target** — see the Source scout section. top-5 share 1.00 means *every* science citation is one of nature.com / arxiv.org / eso.org / quanta. The 08 July edition honestly waived its second discovery anchor because journals.aps.org, science.org and home.cern all returned HTTP 0 even via proxy.

**Tier distribution:** T1 ≈ 46% portfolio (AI/ML paper desks all-arXiv T1; Weekend 22 T1; Science 5 T1; News lighter — 07-06/07-07/07-10 ran T1=0 as the world+Swiss desks are wire/broadcaster T2). ≥40% target met. **T3 = 0** across all ten briefs — clean.
**Linguistic:** SRF (DE) + Le Temps (FR) anchor every News edition and the Weekend + Science carry FR/DE/EN; portfolio non-English ≈ 27%, well above the ≥10% floor.

### B. Aggregator leakage
**Clean — zero hits** for news.ycombinator.com, lobste.rs, reddit.com, twitter.com, x.com, mastodon.social, threads.net, bsky.app across all ten briefs (grepped). 🟢

### C. Link health (sample-based) — **the week's defect**
Feed probes via `curl` from the evaluator env: arXiv Atom API **200**, Nature RSS **303→resolves**, Al Jazeera RSS **200**, SRF RSS **200**. The load-bearing feeds are all reachable — no feed regression.

**Article-link sample (~20 links).** Non-resolving-from-eval-env-but-known-proxy-blocks (000, NOT counted as broken): arxiv.org/abs/*, euronews.com, euromaidanpress.com, huggingface.co, simonwillison.net, timesofisrael.com. Resolving cleanly: letemps.ch 200, quantamagazine.org 200, nature.com article 303, and **seven daily-brief Al Jazeera URLs 200** (typhoon, Indonesia, SK Hynix, Ebola, Khamenei-funeral, Apple-OpenAI…).

**But two Weekend-brief Al Jazeera URLs return a definitive 404** (confirmed via both `curl` GET and WebFetch — two independent egress paths):
- `st-dd9d52b17487` — the Weekend **lead**: `…/2026/7/11/are-the-us-and-iran-at-war-again` → **404**
- `st-05f2d24c2287` — `…/2026/7/11/zaporizhzhias-mayor-says-russian-advance-reaches-citys-outskirts` → **404**

The diagnosis is not link rot: every *daily-brief* Al Jazeera link from 07-08→07-11 resolves 200, and the Weekend's own third AJ link (Apple-OpenAI) resolves 200. Only the two Weekend headline-recap items with no corresponding daily-brief anchor 404. Both are tagged `[single-source]`. This matches the Weekend's method — its footer admits the world-desk headline recap was assembled from "the wire as the practical primary" with "no alternate outlet fetched for those exact items." The mechanism is the Weekend reconstructing plausible Al Jazeera slugs it never fetched. **Fabrication count: 2.** This is a real regression from last week's 0 and is Patch 1.

The lead's error is corroborated by the reader (see §Reader-feedback): the bullet says the US and Iran slid back toward conflict "**a year after their war**," but the pipeline's own dated fact is that the war opened **28 February 2026** — ~4.5 months ago, not a year. The reader downvoted it with exactly that objection.

### D. Section vitality
No section empty ≥3×. AI/ML 07-07 ran papers-only and *honestly* omitted lab-blog/new-models/benchmark desks ("nothing survived the omit-don't-fill bar") — correct behaviour on a quiet-release window, not a dead section. Science astronomy/physics desks each ran 2 items; Weekend's Apple-Silicon section was thin-but-honest ("MLX shipped no new release"). 🟢

### E. Coverage gap recurrence
Recurring (≥3×) clusters, all known/handled:
1. **Publisher HTML 403 in the writer sandbox** (Reuters/AP/NZZ/Korea Herald/most world outlets) — every news day; handled via Al Jazeera + snippets.
2. **Semantic Scholar not-indexed for <1-week-old arXiv** — recurs; now mitigated by the HTML-author-block chain (rm-3, see §N).
3. **APS/Science.org/CERN unreachable for Science** — the science-diversity blocker; see scout + registry proposal.

### F. Triangulation rate
`[single-source]` tags (grepped): news 4/1/0/0/1/6, ai-ml 1/3, science 0, weekend 2 = **18 total** against ~127 items ≈ **14%** portfolio — under the 20% floor. **But News runs ~25%** (12/48), right at the single-stream ceiling, driven by 07-11 (6 of 8 items single-source). Those six are genuinely narrow-coverage stories — three Swiss items only SRF/Le Temps carry (SVP ticket, Leontica explosion, MeteoSwiss heat) and two AJ-only world items (Typhoon Bavi, Indonesia graft). Honest single-sourcing, but the 07-11 concentration is worth a glance. 🟡

### G. Tag discipline
- **`[preprint]`** — every arXiv item tagged across AI/ML, Science, Weekend. Sampled 5, all correct. 🟢
- **`[vendor PR]`** — correctly on GPT-5.6, Grok 4.5, Mistral Robostral, GPT-Live, LongCat-2.0, Nemotron-Audex, Gemma 4. Sampled 5, all correct. 🟢
- **`[disputed]`** — used once, appropriately (Weekend exomoon candidate, arXiv:2607.05193). 🟢
- **`[new source]`** — tagged domains this week: thenationalnews, euronews, apnews, state.gov, climate.copernicus.eu, thehill, timesofisrael, euromaidanpress, primeintellect.ai, eso.org. Spot-checked 2 (euromaidanpress.com, primeintellect.ai) — both genuine primaries, not junk anchors. **But `sources/candidates.jsonl` is empty (0 lines)** despite the prompt's claim that the tag "auto-enters the domain in sources/candidates.jsonl." The auto-capture path is inert — see Open Questions.
- **`[via snippet]`** — news 07-06: 5, 07-07: 1, **ai-ml 07-10: 13** (footer declares 10 citations; multi-tag items inflate the raw grep), else 0. The AI/ML load is the irreducible lab-blog residual (OpenAI/xAI/Mistral serve JS-rendered SPAs); 07-07 ran 0. Not rising in the feed-backed streams. 🟢

### H. Topic balance (Weekend)
The 07-11 Weekend runs **9 ML/AI papers** vs **8 fundamental-science + 2 biology = 10** non-ML papers — a **47% / 53%** split, a **3-point** deviation from 50/50, comfortably inside the ±15pp band. 🟢 The brief openly documents what it cut to hold balance (LARES-2 to one line, several ML runners-up dropped to avoid re-running the daily).

### I. Repetition detection (health.json)
news repeat_rate **0.214** (9 repeats), weekend **0.143** (4); ai-ml and science 0.0. Reading the flagged repeats: every one is an `[ongoing since]`-tracked developing story carrying a *new dated fact* — the US–Iran escalation (07-08 truce-collapse → 07-09 second-day strikes → 07-11 "decimate" threat, each with new strikes/tolls/diplomatic moves), Russia–Ukraine strikes (tolls and target-sets developing daily), Typhoon Bavi (Philippines→Taiwan→China landfall), the heatwave (Copernicus record → MeteoSwiss rules). None is a cold re-summary. Judged healthy. 🟢
**Identity integrity:** `reconcile.py` → **0 flagged**, 1 resolved-by-merge (st-51f44833a0eb → merged into st-df6bde5fe934, informational). No id fork. 🟢

### J. Cross-week trend (vs 2026-07-05)

| Metric | 2026-07-05 | 2026-07-12 | Trend |
|--------|-----------|-----------|-------|
| Portfolio direct-fetch | 0.90 | 0.89 | ▬ stable-high |
| AI/ML direct-fetch | 1.00 | 0.67 | ▼ (07-10 vendor-blog week: 13 via-snippet on lab SPAs) — expected, not a regression |
| T3 leakage | 0 | 0 | ▬ clean |
| Aggregator citations | 0 | 0 | ▬ clean |
| **Fabrication count** | 0 | **2** | ▼ **regression** (weekend AJ dead links) |
| Non-English % | ~28% | ~27% | ▬ |
| Single-source % (portfolio) | ~6% | ~14% | ▼ (news 07-11 spike) |
| Affiliation `(not listed)` on paper desks | high | improving (07-07 ~70% → 07-10 ~15%) | ▲ rm-3 landing |

### K. Feed reachability & direct-fetch (binding constraint)
Per-stream direct/via-snippet (from Coverage footers):

| Stream | Per-edition (direct/snippet) | Agg ratio | Verdict |
|--------|------------------------------|-----------|---------|
| News | 6/3, 12/1, 10/0, 12/0, 7/0, 10/0 | **0.93** | ✅ (≥0.30) |
| AI/ML | 10/0, 10/10 | **0.67** | ✅ (≥0.40) |
| Science | 6/0 | **1.00** | ✅ (≥0.30) |
| Weekend | ~30/0 | **1.00** | ✅ (≥0.30) |

Portfolio ≈ **0.89**. Every stream clears its target. `curl` remains the workhorse across all four; the fetch-proxy is the second line (Nature article HTML, bioRxiv, lab blogs). Note the Weekend's high direct-fetch ratio is *not inconsistent* with the two dead AJ links — those two headline-recap items were counted as "wire primary" without an actual verified fetch, which is precisely the hole Patch 1 closes.
**Domains-that-shouldn't-be-cited:** zero `reach: blocked` domains cited without `[via snippet]`; no `never:` domain appears (the list is empty); no retired/demoted domain anchors. 🟢
**Feeds >50% fail:** Semantic Scholar only, and it is now off the critical path (affiliations moved to the HTML-author-block chain). 🟡

### L. Output volume (token-cost proxy)

| Stream | Per-edition words | Mean | vs 07-05 |
|--------|-------------------|------|----------|
| News | 600, 790, 760, 940, 560, 880 | ~755 | +11% (was ~680) — tracks item length, not repetition |
| AI/ML | 1950, 2150 | ~2050 | +23% (was ~1665) — but 07-10 ran 18 items vs 07-07's 10; growth tracks item count |
| Science | 1520 | ~1520 | −13% (was ~1750) |
| Weekend | ~5600 | ~5600 | +6% (was ~5300) |

No stream shows length growth **decoupled** from story count, so nothing crosses into output-cap territory. AI/ML's +23% is the one to watch, but 07-10 legitimately carried 10 papers + 5 lab items + 1 benchmark + 3 industry = 19 items. 🟢

### M. Editorial shape
- **Vendor-PR-lead share (AI/ML):** the 07-10 lab/benchmark/industry block leads with vendor announcements on ~5 of ~13 non-paper items (GPT-5.6, Grok 4.5, Robostral, GPT-Live, SWE-Bench-audit) ≈ **~40%** — at the flag boundary. Mitigant: each adds independent judgment rather than parroting (the Grok item foregrounds the *split* benchmark picture and "depends entirely on which harness you measure"; the SWE-Bench item notes "OpenAI is publishing this while also touting benchmark wins"). Acceptable end of the range, but watch it. 🟡
- **Aggregator-shape (5 leads sampled):** News-Iran (Times of Israel + Euronews + "ceasefire exists only on paper" judgment) ✓; News-IMF (WEO + Swiss-importer framing) ✓; AI/ML CoT-monitoring (arXiv primary + deep framing) ✓; Science 3I/ATLAS (ESO release + framing) ✓; **Weekend Iran-at-war lead ✗** (dead AJ link + factual error). **1 failure of 5.** 🟡
- **Personalization (5 sampled):** data-centre Schaffhausen (CH energy) ✓, MeteoSwiss heat ("rules for anyone in Switzerland next week") ✓, LongCat (Claude-Code/builder angle) ✓, Europe-critical-metals (Swiss-industry) ✓, SK Hynix (no forced CH angle — correct restraint) ✓. **0 misses.** 🟢

### N. Affiliation element (papers streams)
- **Coverage rate — improving, but Weekend still lags.** The affiliation chain was rewritten 07-10 (rm-3, now living in `routines/_shared/affiliations.md`: "read the paper's own HTML author block first"). The effect is visible across the week: **07-07 AI/ML ran ~70% `(affiliation not listed)`** (7 of 10, pre-rollout, Semantic Scholar un-indexed) while **07-10 AI/ML ran ~15%** (AWS, MBZUAI, Datacurve, EPFL, ETH Zürich, JHU/Rice, NVIDIA all resolved). But the **07-11 Weekend still ran ~37% unlisted** (7 of ~19 papers), because — per its footer — arXiv HTML author blocks didn't render for RL-compositional, sycophancy, KronQ, 3I/ATLAS, topology-from-decoherence, cryptochrome, exomoon. The shared partial's "~97% render HTML / 10-of-10 in production" claim held for the 07-10 daily set but not the Weekend's. The fallback needs to actually fire when the HTML block is absent — Patch 3. Over the <20% target on the Weekend. 🟡
- **Halo audit:** no prestige bias. The unaffiliated/independent papers get full prominence — RL-compositional (affiliation not listed) *leads* the Weekend ML-papers section; sycophancy, 3I/ATLAS, cryptochrome and the exomoon candidate all carry strong "why it matters" framing equal to the lab-affiliated papers. Affiliations are recorded, not used as a selection signal. 🟢

## Prior proposals status

Last week's `proposals/reader-model-2026-07-05.json` (backfilled by Rafael's 07-10 apply pass) carried four proposals, **all stamped `applied: true` — and all four verify as landed in their target files:**
- **rm-1** (reader-profile.md, Weekend Khamenei date-anchor learned pref) → **applied & verified** — present at reader-profile.md "Learned preferences," 2026-07-05 line.
- **rm-2** (`routines/src/weekend.md`, Week-in-headlines event-date rule) → **applied & verified** — present verbatim at weekend.md lines 82–85 ("state what happened AND WHEN… 'X died on {date}'"). *Caveat:* this patch is why the 07-11 Weekend added temporal framing to its lead — and the framing it added ("a year after their war") was factually wrong. The patch works; it now needs the accuracy guard of Patch 2.
- **rm-3** (affiliation chain → HTML author block / OpenAlex fallback) → **applied & verified with visible effect** — lives in `routines/_shared/affiliations.md`; drove the 70%→15% unlisted improvement on the AI/ML daily (§N).
- **rm-4** (reader-profile.md, 06-28 sensationalism backlog line) → **applied & verified** — present at reader-profile.md, 2026-06-28 line.

No pending/unstamped proposals carry over.

## Source scout (Sunday duty)

**Stream picked: Science** — the unambiguous worst-deficit (new_domains 3, top5_share 1.00, unique_domains 3). Fetch budget used: **~9** (6 candidate probes + 3 registry inspections; all other curls were dimension-C link-health, not scout).

**Finding — science is utilization-starved, not candidate-starved.** The registry already carries 23 science-affinity domains at `reach: direct`, including exactly the ones the 08 July writer couldn't reach: journals.aps.org, science.org, cern.ch, esa.int, nasa.gov (all last-stamped 2026-07-10). The gap is that the writer got **HTTP 0** on APS/Science.org/CERN even via proxy, while the registry records them `direct`. So the scout's value this week is *not* piling on more candidates — it is flagging that contradiction (registry proposal below), plus filling three genuine institutional gaps.

**Candidates appended** to `sources/candidates.jsonl` (all absent from the registry; all primary research-news publishers; all Swiss, so they double as personalization sources for a Zurich-based reader). This env holds no fetch-proxy bearer, so all three probed 000 here and are tagged `reach: proxy-needed` for the writers to vet at first citation:
- `ethz.ch` — ETH Zürich news (`https://ethz.ch/en/news-and-events/eth-news.html`)
- `epfl.ch` — EPFL Mediacom RSS (`https://actu.epfl.ch/feeds/rss/mediacom/en/`)
- `psi.ch` — Paul Scherrer Institut media corner (`https://www.psi.ch/en/media-corner`)

**Re-probe of stale `reach:` entries:** moot this week — a probe/apply pass re-stamped every registry entry to lifecycle date 2026-07-10, so there is no "oldest, undated" entry to re-probe. The actionable reach signal is instead the recorded-direct-but-writer-saw-HTTP-0 contradiction on APS/Science.org/CERN → registry proposal.

## Patch proposals (for human review)

### Patch 1 — Weekend: never cite a headline-recap URL you didn't fetch
**Target prompt:** Weekend
**Section affected:** 📰 Week in headlines
**Issue:** Two of the 07-11 Weekend's three Al Jazeera links (the Iran-at-war lead and the Zaporizhzhia bullet) return HTTP 404 — reconstructed slugs for wire items the brief summarized without fetching. Every daily-brief AJ link from the same window resolves 200, so this is Weekend-specific.
**Proposed change:**

> **Before:**
> ```
> The "Week in headlines" recap may summarize the week's biggest daily stories;
> cite the primary source for each.
> ```
>
> **After:**
> ```
> The "Week in headlines" recap may summarize the week's biggest daily stories.
> For each bullet, cite ONLY a URL you actually fetched this run (curl or proxy,
> 200/3xx confirmed) — never reconstruct a plausible outlet slug from memory. If
> the item came from a daily brief, reuse that brief's exact verified URL. If you
> cannot re-fetch a live primary for a recap item, drop the item rather than cite
> an unverified link.
> ```

**Why this helps:** Closes the fabrication path directly — the two dead links (and the aggregator-shape failure) come entirely from citing un-fetched recap URLs.
**Risk:** A few marginal recap items get dropped; acceptable — the Weekend is a deep-read, not a wire mirror.

### Patch 2 — Weekend: verify elapsed-time claims against the event date
**Target prompt:** Weekend
**Section affected:** 📰 Week in headlines
**Issue:** The 07-11 lead says the US and Iran slid back toward conflict "a year after their war," but the pipeline's own dated fact is the war opened 28 February 2026 (~4.5 months). A reader downvoted it: "The war hasn't started a year ago…". The rm-2 date-anchor patch made the writer *add* temporal framing; it now needs an accuracy check on that framing.
**Proposed change:**

> **Before:**
> ```
> If the daily briefs carried the event date, carry it forward.
> ```
>
> **After:**
> ```
> If the daily briefs carried the event date, carry it forward — and when you state
> an elapsed interval ("a year after", "months since", "on the anniversary of"),
> compute it from that carried date and sanity-check it. Do not assert a duration
> you have not derived from a dated fact in this pipeline.
> ```

**Why this helps:** Directly answers a reasoned reader 👎 and prevents the date-anchor patch from manufacturing a wrong interval.
**Risk:** Negligible; adds one verification step per temporal claim.

### Patch 3 — Papers desks: make the affiliation fallback actually fire when the HTML block is absent
**Target prompt:** AI-ML / Science / Weekend (shared `routines/_shared/affiliations.md`)
**Section affected:** Affiliation sourcing
**Issue:** The 07-10 rewrite ("read the paper's own HTML author block, ~97% render") cut AI/ML's `(affiliation not listed)` from ~70% to ~15% — but the 07-11 Weekend still ran ~37% unlisted because the HTML block didn't render for 7 papers, and the chain marked them unlisted instead of falling back.
**Proposed change:**

> **Before:**
> ```
> arXiv preprints — read the paper's own HTML author block. [...] If the block does
> not render, mark (affiliation not listed).
> ```
>
> **After:**
> ```
> arXiv preprints — read the paper's own HTML author block first. If the block does
> not render, query the OpenAlex works API (api.openalex.org/works?search=<title>)
> and, failing that, Semantic Scholar, BEFORE marking (affiliation not listed).
> Only mark unlisted when all three fail. Never guess.
> ```

**Why this helps:** Recovers the ~37% of Weekend bylines currently lost when a single method (HTML block) misses. rm-3 intended OpenAlex as the fallback; make it explicit in the chain rather than implicit.
**Risk:** OpenAlex occasionally lags brand-new arXiv IDs too; the honest final marker preserves the no-fabrication guarantee.

## Reader-feedback → profile proposals

**Window feedback (health.json → feedback.by_stream; unconsumed_total = 0 🟢):** ai-ml up 9 / down 1 / retractions 2; science up 3; news up 2; weekend up 1 / down 2. Resolving the ledger `ev:"feedback"` events to stories:
- **Positive cluster (no rule needed):** heavy 👍 on the 07-07 and 07-10 AI/ML paper items (super-weights, CoT-monitoring, SWE-Bench audit, Prime Intellect, knowing–using gap), all three 07-08 Science items, and two News stories. This reinforces the existing profile ("reads AI-ML and Science for signal") — reinforcement, not a mandate.
- **Gemma 4 toggle (non-signal):** st-bb82d8bcf7fd (07-07 AI/ML) was tapped up→0→up→down→0 by one reader — the two retractions health.json counts. Last-write-wins nets to a retraction; noise, not a signal.
- **The one substantive signal — a vote WITH a written reason:** st-dd9d52b17487, the 07-11 Weekend Iran lead, 👎 with reason **"The war hasn't started a year ago…"**. This is a real factual objection (the war opened 28 Feb 2026), it carries a written reason, and it is a *distinct* miss from last week's Khamenei date-anchor (that was a *missing* date; this is a *wrong* interval). Under the bounded auto-apply grant (a vote with a written reason qualifies), I have appended a dated learned-preference line.

**Auto-applied to `reader-profile.md` "Learned preferences" (stamped `applied: true, applied_by: evaluator`):**

> **After (appended):**
> ```
> - 2026-07-12: in the Weekend digest, get elapsed-time framing right — verify any
>   "a year after / months since / anniversary of" phrasing against the event's
>   dated fact from the daily briefs (1× 👎 with reason "The war hasn't started a
>   year ago…" on the 2026-07-11 Iran lead, which said "a year after their war"
>   when the war opened 28 Feb 2026).
> ```

**`reader-profile/source-weights.yml`:** no change. Al Jazeera is not misleading here — this is a Weekend *framing + citation-hygiene* miss (Patches 1–2), not a source-credibility problem. `never:` / `reduce:` stay empty.

## Machine-readable proposals

Written this run: `proposals/reader-model-2026-07-12.json` (rm-1 the auto-applied learned-preference line, stamped `applied: true`; rm-2/rm-3/rm-4 the three prompt patches, `applied: false`) and `proposals/registry-2026-07-12.yml` (the APS/Science.org/CERN reach re-probe + the three Swiss science candidate promotions, `applied: false`).

## Open questions for human review
1. **`[new source]` → `candidates.jsonl` auto-capture is inert.** Ten `[new source]` domains were tagged across the window, yet `sources/candidates.jsonl` is empty (0 lines) and `candidates_open = 0` for every stream. The prompt says the tag "auto-enters the domain in sources/candidates.jsonl as a candidate" — that path appears unwired (or is being drained without landing). This is a discovery-bookkeeping defect, not a writer problem. Worth checking the tooling that should append on `[new source]`.
2. **Recorded-vs-realized reachability for the Science registry.** journals.aps.org / science.org / cern.ch are stamped `reach: direct` (2026-07-10) but the 08 July writer got HTTP 0 on all three via proxy. Is the deterministic probe testing a feed path the writer doesn't use (e.g. an RSS URL that 200s while the article HTML 0s)? Until this reconciles, Science stays pinned at 3 domains regardless of how many candidates the scout adds. (Registry proposal filed.)
3. **News top-5 outlet share (0.88) is reachability-bound, not effort-bound.** The world desk leans on Al Jazeera because Reuters/AP/NZZ/Korea Herald 403 in the sandbox. Is the right lever a registry reach-flip / proxy path for one more world wire, or do we accept the AJ+SRF+LeTemps tripod as the structural floor for a curl-only daily?
