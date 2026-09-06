---
layout: single
title: "Weekly Pipeline Review — 2026-09-06"
date: 2026-09-06T11:44:37+02:00
categories: [evaluator]
published: true
---

# Weekly Brief Pipeline Review — 2026-09-06

_Coverage: briefs from 2026-08-31 to 2026-09-06._
_Files read: 6 news, 2 AI/ML (expect ~2), 1 science (expect ~1), 1 sports (expect ~1), 1 weekend, prior review found (2026-08-31)._

The pipeline is healthy and on-cadence. All eleven expected (slug, date) briefs landed: 6 News (daily, no same-day Sunday yet), 2 AI/ML (Tue+Fri), 1 Science (Wed), 1 Sports (Mon), 1 Weekend (Sat). The mechanical tier is clean — zero aggregator leakage, zero empty sections, single-source rate 6.8% portfolio-wide, direct-fetch ratio 0.98, reconcile 0 flagged across 22 editions, feedback fold fully consumed, and no off-main self-delivery. The standing structural issue is unchanged from prior weeks: **source concentration**, sharpest in Science (top-5 outlet share 1.00, 9 unique domains, 5 new domains, nature.com saturated). This week's scout targets that stream.

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains 30d (worst stream, source-health) | 9 (science) | ≥30 | 🔴 |
| New domains this window (portfolio, source-health) | 80 sum (science 5 worst) | ≥2–3/wk (≥10/mo) | 🟢 |
| Top-5 outlet share (worst stream, source-health) | 1.00 (science) | ≤0.50 (→0.35) | 🔴 |
| Waiver rate (worst stream, source-health) | 0.60 (weekend) | ≤50% | 🔴 |
| Discovery footer present (every brief) | 10/10 | 100% | 🟢 |
| T1 citation %                   | 39.3% (46/117) | ≥40% | 🟡 |
| T3 leakage count                | 0 | 0 | 🟢 |
| Non-English citation % (portfolio) | ≥30% (est.) | ≥10% | 🟢 |
| Link sample pass rate           | 6/20 (evaluator egress wall) | ≥90% | ⚪ |
| Fabrication count               | 0 | 0 | 🟢 |
| Single-source rate (portfolio)  | 6.8% (8/117) | <20% | 🟢 |
| Empty section instances         | 0 | <5 | 🟢 |
| Repeat rate (worst stream, health.json) | 0.32 (weekend) | judge | 🟡 |
| Direct-fetch ratio (portfolio)  | 0.98 | ≥0.35 | 🟢 |
| Feeds with >50% fail rate       | 22 (n≥2; mostly writer-side egress, routed around) | 0 | 🔴 |
| Citations on `reach: blocked` domains without [via snippet] | 0 | 0 | 🟢 |
| Unconsumed feedback backlog (health.json) | 0 | 0 | 🟢 |
| Vendor-PR-lead share (AI/ML, §M) | ~2 of ~11 (<20%) | ≤40% | 🟢 |
| Aggregator-shape failures (§M, of 5) | 1 (BoE/SiliconANGLE) | 0–1 | 🟡 |
| Personalization misses (§M, of 5) | 0 | 0–1 | 🟢 |

## A–N: Detailed findings

### A. Source diversity & discovery
Read from `source-health.json` (30d rolling): news `unique=39, new=29, top5=0.71, waiver=0.57`; ai-ml `26 / 22 / 0.67 / 0.22`; science `9 / 5 / 1.00 / 0.50, nature.com saturated`; sports `13 / 10 / 0.68 / 0.00, bbc.co.uk saturated`; weekend `23 / 14 / 0.79 / 0.60`. Portfolio unique-domain sum 110, `candidates_open: 0`.

**Science is the worst-deficit stream on every axis** — lowest new domains (5), highest top-5 share (a maximal 1.00: everything routes through a handful of registered primaries), fewest unique domains (9), and nature.com over its bar. This is not a discovery-effort failure: the 09-02 Science footer honestly names the dormant feeds it probed (Berkeley Lab, Fermilab, NOIRLab, ESA, ESO — ESO returned empty), and the week's strongest stories (LZ dark-matter, altermagnets, RAS drug, clonal haematopoiesis) genuinely landed on already-registered primaries. The problem is **registry breadth**: the physics-heavy slate had no APS/Physical Review or PNAS primary to reach for, so concentration is structural, not behavioural. The Sunday scout addresses this directly (below).

Top-5 outlet share is elevated across *all* streams (0.67–1.00 vs the 0.50 bar). For news this is partly definitional — a Swiss/international daily runs on a stable core of outlet-class primaries (SRF, Le Temps, DW, Al Jazeera) that are the *appropriate* sources, not aggregator crutches — but the trend is worth watching as the ≤0.35 steady-state target approaches.

Waiver rates: weekend 0.60 and news 0.57 both breach the 0.50 bar. Weekend has been the portfolio's worst waiver stream for five consecutive weeks; the standing rm-1 patch (dormant-probe-before-waive) remains unapplied and is re-listed below.

### B. Aggregator leakage
`aggregator_leakage: []` — zero citations of HN, Reddit, X, Bluesky, Mastodon, etc. across the window. 🟢

### C. Link health — **unmeasurable this run (evaluator egress wall)**
`linkcheck --check` resolved **6/20** (142 links total). The failures are `ERR:56` (connection reset) concentrated on proxy-needed hosts (arxiv.org, dw.com, nasa.gov, lemonde.fr, bloomberg.com, nltimes.nl, news.un.org), while every direct-curl-friendly host resolved 200 (srf.ch ×3, letemps.ch, aljazeera.com, quantamagazine.org). This is the **evaluator sandbox's own allowlist-walled egress** (the routine holds no fetch-proxy bearer by design), *not* broken source links — the writers' computed footers show `direct_fetch_ratio` 0.96–1.00, i.e. these URLs fetched fine at compose time. Dimension reported **unmeasurable ⚪**; the pass rate reflects my environment, not link quality.

One genuine finding survived the wall: `srf.ch/.../flugabwehr-patriot-deal-mit-deutschland-gescheitert...` (2026-09-04-news) returned **404** — SRF, a direct-reachable host, so this is a real dead link (article moved/retracted; SRF URLs rotate). Minor; noted for the record. Of the 8 resolvable links I spot-checked for claim accuracy (SRF drought/notreserven, SRF Aarau, Le Temps Dittli, Al Jazeera Iran strikes, Quanta computer-science), **all claims matched the source** — no fabrications.

### D. Section vitality
`empty_sections: []` for every stream. No section empty even once. 🟢 The 09-01 AI/ML "no Lab-blogs/Benchmarks section this window" is an honest omit-don't-fill (footer explains: no frontier-lab post carried new substance beyond the DeepSeek release), not an empty section.

### E. Coverage-gap recurrence
Clustering the Gaps footers, the recurring theme is **JS-rendered / egress-blocked primary institutional pages** in the writer sandbox: BFS (bfs.admin.ch), Swiss Life, Vaud cantonal (vd.ch), parlament.ch, admin.ch, swissinfo — all "returned a JS shell" or "did not load through the proxy," forcing Swiss items onto secondary outlet copy. This appears ≥3× (09-01, 09-02, 09-04 news) → **structural**. It is a known hard-fetch class the writers route around gracefully (direct-fetch ratio stays 0.98), but it caps how often Swiss federal stories can rest on the primary release. See Patch P2.

### F. Triangulation rate
Single-source rate portfolio 6.8% (news 11.6%, ai-ml 7.1%, science 0%, sports 0%, weekend 3.1%) — all well under the 20%/25% bars. 🟢 The 5 news single-source items are appropriately tagged `[single-source]` and flagged in-text (e.g. the Anthropic-Lambda Bloomberg item, the Kharg Island Iranian-state-media claim).

### G. Tag discipline
Counts (health.json): ai-ml `preprint 16, vendor PR 3, new source 2, via snippet 1`; news `new source 4, disputed 2, single-source 5, via snippet 1`; weekend `preprint 22, vendor PR 1, single-source 1`; sports `new source 3`; science `preprint 2`.
- **`[preprint]`**: sampled 5 across ai-ml/weekend — all genuine arXiv/bioRxiv items. ✓
- **`[vendor PR]`**: the 3 ai-ml uses (OpenAI GPT-6 Astra, Meta Muse Spark, and one weekend) all sit on genuine vendor announcements — correct. ✓
- **`[new source]`**: spot-checked 2 of the week's candidates.jsonl entries via footers — bwo.admin.ch (Federal Housing Office, 09-01 news), dnb.nl (De Nederlandsche Bank, 09-03 news), news.un.org (UN newsroom). All genuine primary institutions, not junk anchors. ✓
- **`[via snippet]`**: 1 news + 1 ai-ml only — near-zero, consistent with the 0.98 direct-fetch ratio. The curl-first chain is working; via-snippet is *not* rising. 🟢

### H. Topic balance (weekend)
`weekend_balance`: ml_items 14, science_items 13, **ml_share 0.519** — dead-centre of the [0.35, 0.65] band. 🟢

### I. Repetition detection
`streams.*.repeats`: news 0.19 (8), ai-ml 0.04 (1), weekend **0.32 (10)**, science/sports 0. The weekend rate is the one to judge: a papers digest legitimately revisits multi-week threads (the LZ dark-matter result carries "still not on arXiv... anchored to the Berkeley Lab release," the altermagnet/g-wave observation is flagged complementary to the Science daily's Cambridge Nature paper). Reading the flagged items, the re-runs carry **new dated facts** (LZ's PRL submission status, fresh interpretation preprints) rather than re-summaries — the `[ongoing since]` discipline is holding. 🟡 rather than 🔴, but weekend's high overlap with the Science daily (dark matter appeared in both this week) is worth monitoring for genuine duplication.

**Identity integrity:** `reconcile.py --root .` → **0 flagged, 0 resolved-by-merge, 22 editions checked**. No anchor/dedup id forks. 🟢

### J. Cross-week trend
vs 2026-08-31: weekend waiver improved 0.80 → 0.60 (still worst); via-snippet stays near-zero; direct-fetch ratio holds ~0.98; aggregator leakage stays 0; T3 stays 0. Science concentration is flat-bad (top5 1.00 both weeks). The scout candidate→registry path verified working: last run's chemrxiv.org and cell.com scout candidates both **landed in `sources/registry.yml`** this week (chemrxiv candidate/proxy line 3468; cell.com probation line 378), and candidates.jsonl was cleared to 0 before this run.

### K. Feed reachability & direct-fetch
Per-stream direct-fetch ratios all far exceed their ranges: news 0.98, ai-ml 0.96, science 1.00, sports 1.00, weekend 1.00. 🟢 The binding constraint has genuinely loosened — the curl-first chain (export.arxiv.org 47 ok-curl, srf.ch 35, letemps.ch 26, aljazeera.com 21, nature.com 4, quantamagazine.org 3) carries the load.

**Feeds >50% fail (n≥2): 22 feeds.** The raw count is red, but the composition matters: 14 are 100%-fail on small n (admin.ch 11/0, sec.gov 6/0, centcom.mil 6/0, site.api.espn.com 6/0, openai.com 5/0, swisslife.com 4/0, dnb.nl 3/0, swissinfo 3/0, plus n=2 probes eso/justice/mclaren/ec.europa/worldfootball/timesofisrael). These are **known-hard primaries** — gov JS-shells, anti-bot vendor pages (openai.com), and API endpoints — that the writers *expect* to fail direct and route around (every one shows up in a Gaps footer with a secondary-source fallback). They do not dent the direct-fetch ratio because the successful high-volume feeds dominate. The genuinely actionable outliers: **france24.com 86% fail** (already under a reduce proposal — see rm-2), **parlament.ch 91%** and **admin.ch 100%** (Swiss federal, JS-rendered — the §E structural gap). **Domains-that-shouldn't check:** scanned citations against registry `reach: blocked`/`never:` — **0 violations**; no blocked domain cited without `[via snippet]`, `never:` list is empty. 🟢

### L. Output volume
words_mean vs prev week: news 1314 (+9%), ai-ml 2572 (−6%), science 1600 (−26%), sports 1640 (−30%), weekend 6725 (+3%). **No stream grew >25%**; the two big drops (science, sports) are single-edition variance, not a trend. No output-cap intervention warranted. 🟢

### M. Editorial shape
- **Vendor-PR-lead share (AI/ML):** ~2 of ~11 news/release items lead with a vendor's own framing (OpenAI GPT-6 Astra, Meta Muse Spark), both `[vendor PR]`-tagged and heavily discounted in-text — Astra's AGI claim is called "a marketing event as much as a technical one... worth discounting where the only evidence is OpenAI's own scorecard." Share well under 40%. 🟢
- **Aggregator-shape (all streams):** sampled 5 leads. Four cite a primary and add framing the source lacks (SEC 8-K on Nvidia–HF; DOJ statement-of-interest with the OpenAI-stake conflict flagged; LZ via Berkeley Lab release; Federal Housing Office on the mortgage rate). **One failure:** the 09-01 AI/ML Bank-of-England item leads on SiliconANGLE + The Decoder (two secondary tech blogs) reporting a G20/FSB letter the writer's own Gaps note admits "was not directly located... on bankofengland.co.uk / fsb.org this run." A reader flagged exactly this ("is siliconangle really a good source?... the link should have been to the bank of england official press release"). This is a real miss and drives a new source-weights proposal (below).
- **Personalization:** sampled 5 — CH/builder/personal-impact angle present where plausible (Swiss mortgage reference rate → renters/owners; BFS pay-gap; the Meta contributor-tier "you are paying in data" builder's caveat; ETH Zürich coreference paper affiliation surfaced). No forced angles. 🟢

### N. Affiliation element (papers streams)
- **Coverage rate:** 3 `(affiliation not listed)` bylines of 37 preprint items across ai-ml/science/weekend = **8.1%**, under the 20% target. All 3 are in 09-04 AI/ML (NVFP4, RecurTrace, one diffusion-distillation paper) and the footer honestly explains the HTML author blocks did not render. 🟢
- **Halo audit:** the 3 unaffiliated papers are treated with equal seriousness — RecurTrace and NVFP4 both received full "why it matters" analysis, no importance suppression relative to the lab-affiliated papers (Tsinghua GAR, ETH/MIT/Cohere legibility). No prestige bias evident. 🟢

## Prior proposals status

From `proposals/reader-model-2026-08-31.json` and `proposals/registry-2026-08-31.yml`:
- **rm-1** (port weekend dormant-source-activation block): **pending, not applied** — `grep` of `routines/src/weekend.md` still finds no `dormant`/`before waiving` language. Now unapplied for a **5th consecutive week**. Re-listed as P1.
- **rm-2** (add france24.com to source-weights `reduce:`): **pending, not applied** — `reduce: []` still empty. The *profile-side* correction landed (reader-profile.md line 57, 2026-08-23), but the source-weights hard-penalty did not. Re-listed below.
- **rm-3** (reader-profile.md fiscal/regulatory countervailing-context line, auto-applied): **applied and verified** — line present in reader-profile.md dated 2026-08-31. ✓
- **registry france24.com reach direct→proxy:** pending, not applied (still `reach: direct`, line 1997). Re-carried.
- **registry esv.ch / uci.ch candidate→probation:** pending, not applied (both still `status: candidate`, lines 3080/3092). Re-carried (6th run).
- **registry chemrxiv.org / cell.com scout candidates:** **landed** — both now in `sources/registry.yml` (positive verification of the scout path).

## Source scout (Sunday duty)

**Stream picked: Science** — worst deficit on all tie-breakers (new_domains 5 = lowest, top5_share 1.00 = highest, unique_domains 9). This week's science/weekend slate was physics- and biomedicine-heavy (dark-matter LZ → *Physical Review Letters*, altermagnets, RAS drug, clonal haematopoiesis), yet the registry had no APS/Physical Review or PNAS primary to reach for — the direct cause of the maximal top-5 concentration.

**Candidates appended to `sources/candidates.jsonl` (2):**
- `journals.aps.org` — American Physical Society / Physical Review family. Genuine primary, directly relevant: the LZ dark-matter result covered twice this week is submitted to PRL, and altermagnet physics is APS territory. `reach: proxy-needed`.
- `pnas.org` — Proceedings of the National Academy of Sciences. Primary multidisciplinary journal for de-concentrating the biomedicine slate away from nature.com (saturated). `reach: proxy-needed`.

**Re-probes (direct curl, within budget):** attempted 5 stale/candidate reach entries (nature, eso ×2, biorxiv, fnal) — **only nature.com resolved** (303); every other host returned code 000. This is the evaluator sandbox's allowlist-walled egress (same wall documented 2026-08-31), **not** reach evidence — a 000 tunnel-block is my environment, not a `reach: direct` contradiction. **No reach flips proposed from re-probes** this run; the writers, who hold the bearer, will vet the two new candidates at first citation.

**Fetches used: 10 of 20 budget** (5 candidate probes + 5 re-probes).

## Patch proposals (for human review)

### Patch 1 — Weekend: probe dormant weekend-affinity domains before waiving discovery (CARRIED, 5th week)
**Target prompt:** Weekend
**Section affected:** Sourcing / discovery footer
**Issue:** Weekend waiver rate is 0.60 — worst in the portfolio for five straight weeks and above the 0.50 bar. Science already has a dormant-source-activation block; Weekend does not, so it waives before actively probing registered-but-dormant weekend-affinity primaries.
**Proposed change:**

> **Before:**
> ```
> [weekend.md sourcing section — no dormant-probe-before-waive instruction]
> ```
>
> **After:**
> ```
> Before emitting "Discovery: waived", probe at least two registered weekend-affinity
> domains that are dormant (last_cited=None / long stale) from the preflight plan, and
> name which were tried in the waiver reason. A new anchor resolving to a hub
> (hf.co, github.com, arxiv.org, nature.com) does not count as a new primary.
> ```

**Why this helps:** converts passive waiving into an active dormant-probe pass, the same mechanism that lets Science waive honestly. **Risk:** adds fetch calls to an already long (6.7k-word) brief; keep the probe cap at 2.

### Patch 2 — News/Science: register Swiss-federal JS-shell fallbacks as a named class
**Target prompt:** News
**Section affected:** Swiss sourcing / Gaps handling
**Issue:** admin.ch (100% fail), parlament.ch (91%), bfs.admin.ch, vd.ch, swissinfo repeatedly return JS shells through the proxy (§E structural, ≥3× this window), forcing Swiss federal stories onto secondary outlet copy. The writers handle this gracefully but re-derive the fallback each time.
**Proposed change:**

> **After:**
> ```
> For Swiss federal primaries known to render JS-only through the proxy
> (admin.ch, parlament.ch, bfs.admin.ch, vd.ch), do not spend repeated fetch
> attempts on the article page; go straight to the feed/summary or the
> RSS endpoint, cite the primary release URL, and confirm figures against a
> reachable outlet — noting the JS-shell limitation once in Gaps, not per-item.
> ```

**Why this helps:** saves wasted fetch cycles and standardises an already-recurring fallback. **Risk:** could entrench secondary-sourcing on Swiss stories if a federal feed later becomes fetchable — revisit if reach probes flip.

## Reader-feedback → profile proposals

**Completeness — every reasoned event dispositioned.** 22 feedback events in-window (by `ts`), of which **5 carry a non-empty reason**:

1. 2026-09-02, 2026-09-01-news, 👍 "excellent insight on the satellite images for switzerland" → **deferred** (single positive, no ≥2-distinct-story theme; praise for existing behaviour).
2. 2026-09-02, 2026-09-01-ai-ml, 👍 "Interesting but is silicon angle really a good source?... The link should have been to the bank of england official press release" → **applied** as source-weights proposal sw-1 (below), corroborated by the §M aggregator-shape miss.
3. 2026-09-02, 2026-09-02-news, 👍 "very, very good framing" → **deferred** (single praise, reinforces existing "get the framing right" discipline).
4. 2026-09-04, 2026-09-04-ai-ml, 👎 "any claim of AGI is bullshit until proven wrong" → **deferred** (single signal; already covered — the 09-04 brief *did* discount the AGI claim as "a marketing event... worth discounting where the only evidence is OpenAI's own scorecard," and the 2026-07-26 unreliable-narrator + vendor-PR discipline already govern this).
5. 2026-09-05, 2026-09-05-news, 👎 "Stop drinking from the koolaid. It's as 'concrete' as previous plans given the extreme bias towards Russia" → **deferred** (single signal; squarely under the **existing** 2026-07-26 learned-preference line "treat US-administration self-characterizations as an unreliable narrator" — a reinforcement, not a new theme).

**Noise filter:** the two 👎 land on genuinely different themes (vendor AGI hype vs geopolitical spin), each already captured by an existing learned-preference line, so neither reaches the ≥2-distinct-stories bar for a *new* auto-applied line. **No new reader-profile.md line auto-applied this week** — the conservative reading of the bounded grant.

**One proposal (Rafael-gated, not auto-applied):**

**sw-1 — add siliconangle.com to `reduce:`.** The 09-01 AI/ML Bank-of-England lead rested on SiliconANGLE (a secondary tech blog) for a G20/FSB primary the writer never fetched; a reader flagged it verbatim ("the link should have been to the bank of england official press release"), and SiliconANGLE recurs as an anchor in the 09-04 Nvidia–HF item (there correctly demoted behind the SEC 8-K). `reduce:` not `never:` — legitimate outlet, demote-when-a-primary-exists.

> **Before (reader-profile/source-weights.yml):**
> ```
> reduce: []
> ```
>
> **After:**
> ```
> reduce:
>   - siliconangle.com   # 2026-09-06: 👍-with-critique, used as lead-anchor where the
>                        # primary (BoE/FSB press release) existed and wasn't fetched
> ```

**Carried:** **rm-2** (france24.com → `reduce:`) remains pending from 2026-08-23; re-list, do not re-derive as new.

## Machine-readable proposals

Written to `proposals/reader-model-2026-09-06.json` and `proposals/registry-2026-09-06.yml`. All `applied: false` (nothing auto-applied this week).

## Cross-week trend

Two-week direction: weekend waiver 0.80→0.60 (improving, still worst); science concentration flat at top5 1.00 (the scout addresses registry breadth, the true cause); direct-fetch ratio steady ~0.98; via-snippet near-zero and not rising; T3 and aggregator leakage steady at 0. The one editorial regression to watch is the SiliconANGLE-as-primary pattern (§M) — first mechanically-visible this week.

## Open questions for human review

1. **Science registry breadth.** top5_share is a maximal 1.00 because the physics slate had no APS/PNAS primary registered. The scout appended `journals.aps.org` and `pnas.org` as `proxy-needed` candidates — worth arming once a writer confirms fetch via bearer. Is there appetite to also add a CERN/institutional-physics primary?
2. **Five-week rm-1 stall.** The weekend dormant-probe patch has been proposed unchanged for five weeks. Is it declined-on-purpose (weekend length concern), or just un-triaged? If declined, I'll stop carrying it.
3. **france24.com** now has *two* separate pending signals (rm-2 source-weights reduce + registry reach direct→proxy) and 86% fetch failure. Worth applying both together.
4. No reader brief-proposals this window (`proposals/*.jsonl` absent).
