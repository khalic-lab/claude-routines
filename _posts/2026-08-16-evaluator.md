---
layout: single
title: "Weekly Pipeline Review — 2026-08-16"
date: 2026-08-16T11:45:04+02:00
categories: [evaluator]
published: true
---

# Weekly Brief Pipeline Review — 2026-08-16

_Coverage: briefs from 2026-08-10 to 2026-08-16._
_Files read: 6 news, 2 AI/ML (expected ~2), 1 science (expected ~1), 1 sports (expected ~1), 1 weekend, prior review found (2026-08-09, 7 days old)._

This was a clean, high-functioning week. Every stream fired on its expected cadence, reader
feedback was unanimously positive (16 👍, 0 👎), and the deterministic dimensions — aggregator
leakage, empty sections, identity reconciliation, off-main self-delivery, feedback backlog — all
came back at zero. The single standing defect is old and structural: the weekend brief again
waived discovery 100% of the time, and the fix for it (rm-1) has now sat un-applied for a week.
Below, the numbers I read rather than recounted, the editorial judgment the scripts can't make,
and one carried patch.

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains 30d (worst stream, source-health) | science 11 | ≥30 | 🟡 |
| New domains this window (portfolio, source-health) | ~76 / 30d (≈18/wk) | ≥2–3/wk (≥10/mo) | 🟢 |
| Top-5 outlet share (worst stream, source-health) | ai-ml 0.84 | ≤0.50 (→0.35) | 🟡 |
| Waiver rate (worst stream, source-health) | weekend 1.00 | ≤50% | 🔴 |
| Discovery footer present (every brief) | 11/11 | 100% | 🟢 |
| T1 citation %                   | ~50%  | ≥40%   | 🟢 |
| T3 leakage count                | 0     | 0      | 🟢 |
| Non-English citation % (portfolio) | ~20% (FR/DE) | ≥10% | 🟢 |
| Link sample pass rate           | 4/20 (unmeasurable) | ≥90% | ⚪ |
| Fabrication count               | 0     | 0      | 🟢 |
| Single-source rate (portfolio)  | 14%   | <20%   | 🟢 |
| Empty section instances         | 0     | <5     | 🟢 |
| Repeat rate (worst stream, health.json) | sports 0.25 / news 0.21 | judge | 🟢 |
| Direct-fetch ratio (portfolio)  | ~0.98 | ≥0.35  | 🟢 |
| Feeds with >50% fail rate       | ~5 (mostly low-volume; 1 material) | 0 | 🟡 |
| Citations on `reach: blocked` domains without [via snippet] | 0 | 0 | 🟢 |
| Unconsumed feedback backlog (health.json) | 0 | 0 | 🟢 |
| Vendor-PR-lead share (AI/ML, §M) | ~10% | ≤40% | 🟢 |
| Aggregator-shape failures (§M, of 5) | 0 | 0–1 | 🟢 |
| Personalization misses (§M, of 5) | 0 | 0–1 | 🟢 |

## A–N: Detailed findings

**A. Source diversity & discovery.** 30-day source-health: news `unique=33 / new=26 / top5=0.759 /
waiver=0.448` (saturated: srf.ch); ai-ml `18 / 14 / 0.841 / 0.222`; science `11 / 8 / 0.800 /
0.750`; sports `12 / 12 / 0.588 / 0.500` (saturated: srf.ch); weekend `22 / 16 / 0.687 / 1.000`.
Portfolio new-domain flow is strong (≈76 over 30d). The two 🟡s are structural, not regressions:
- *Top-5 outlet share* trips its bar on every stream because the metric measures only the
  outlet-class slice after hubs/institutional are excluded, and the papers streams cite almost
  entirely hub primaries (arXiv, Nature, bioRxiv). ai-ml's 0.84 is the-decoder.com carrying nearly
  all of the *non-hub* secondary load — expected for an AI-news stream, and the T1 mix underneath
  it is healthy (11/18 T1 on 08-14). Not actionable as diversity failure.
- *Science unique=11* is a low-cadence artifact (24 stories/30d over ~4 editions); it is stable,
  not shrinking, and the registry behind it is rich (see scout).

The real deficit is **weekend waiver_rate=1.00** — discovery waived every edition. This week's
waiver was *honest* ("every source that survived verification this week resolved to an
already-registered hub"), and weekend is a papers brief where genuinely-new primaries are rare. But
the deficit is dormancy, not absence: the registry holds a stack of dormant weekend-affinity
primaries the writer isn't reactivating. That is exactly what rm-1 (below) fixes — and it landed for
*science* on 2026-08-02 but never for weekend.

Tier distribution (from footers): T1 ≈ 50% portfolio (papers streams 60–100% T1; news structurally
T2-outlet-heavy — SRF/Le Temps/Al Jazeera are quality-secondary, T1=1/7 on 08-15 is correct, not a
miss). T3 leakage = 0. Linguistic: FR+DE citations run ~20% portfolio (SRF, Le Temps, swissinfo,
NZZ, DW) — comfortably ≥10%. Geographic spread on news is wide (CH, Lebanon, Latvia, Korea, DRC).

**B. Aggregator leakage (computed).** `aggregator_leakage: []` — zero HN/Reddit/X/Bluesky/etc.
citations across all 11 posts. The weekend DeepSeek item narrates a "WeChat → deleted Reddit → HN
table" provenance chain but *cites Simon Willison* (registered T2) as the actual source and tags it
`[single-source]` — correct handling, not leakage.

**C. Link health — UNMEASURABLE this run.** `linkcheck --check` resolved **4/20** (ERR:56 on
arxiv, nature, biorxiv, dw, france24, nzz, openai, huggingface, un.org, sudantribune, foxnews,
inherentlabs). This is the evaluator sandbox's own egress wall, not broken links: the writers' Coverage
footers show `direct_fetch_ratio` 0.975–1.00 with `via_snippet`=0 across every stream — they fetched
these same hosts fine through the fetch-proxy bearer the evaluator deliberately lacks. Reporting the
dimension unmeasurable per the prompt's egress-regression clause. **One genuine finding survived:**
`letemps.ch/monde/afrique/face-a-une-epidemie-debola-…` (weekend, st-34b1caf1bc46, Ebola item)
returned **404** — Le Temps reachable, that path dead. Almost certainly URL rot between publish
(08-15) and now; the item is `[single-source]` and the same story is carried correctly in 08-15-news
under a different, live Le Temps URL. Low severity. Claim spot-checks were limited to the handful of
hosts that resolved (letemps, aljazeera, quanta); no fabrications detected in those.

**D. Section vitality (computed).** `empty_sections: []` on every stream. AI/ML appearing twice,
Science/Sports once, Weekend once — all correct cadence, not gaps. Nothing to flag.

**E. Coverage gap recurrence.** Reading the Gaps footers: the recurring cluster is
infrastructure-shaped, not beat-shaped — `api.openalex.org` not indexing fresh Nature/arXiv DOIs
(weekend + science, driving the affiliation gaps in §N), `link.aps.org` / APS *Physics* viewpoints
unreachable (science), HF/GitHub model-metadata APIs 403/429 (ai-ml + weekend). None recurred ≥3
times as a *content* gap; the writers routed around each honestly (fell back to article HTML author
blocks, Nature primaries, HF model cards). No structural content hole this week.

**F. Triangulation rate (computed).** Single-source portfolio 16/114 = **14%** (<20% 🟢). Per stream:
news 0.125, weekend 0.065, science 0.00, ai-ml 0.25, sports 0.25. ai-ml and sports sit *at* the 25%
per-stream bar — for ai-ml the single-source items are all vendor-release/IPO-rumor items correctly
tagged `[single-source]` (Grok 4.6, Anthropic IPO figure, GLM-5.3 vuln count, Gemini user count),
i.e. honest labeling of genuinely un-triangulable vendor claims, not lazy sourcing. Acceptable.

**G. Tag discipline.** `[preprint]` on every arXiv item (ai-ml 18, science 6, weekend 10) — correct.
`[vendor PR]` (ai-ml 7) on Gemini/Grok/DeepSeek/Zhipu/Ling/OpenAI-Cyber/Anthropic-watermark —
correct, and each carries independent framing (see §M). `[new source]` spot-check — all genuine
primaries, zero junk anchors: nvidianews.nvidia.com, inherentlabs.ai (ai-ml); nna-leb.gov.lb
(Lebanon state agency, news); arsenal.com, letourfemmes.fr (official race site, sports). `[via
snippet]` = 1 (news only), everything else direct — the curl-first chain is working, snippet rates
are floor-low. No `[disputed]` needed this week.

**H. Topic balance (weekend, computed).** `ml_items=16, science_items=10, ml_share=0.615` — inside
the [0.35, 0.65] band, leaning ML but within tolerance 🟢. The edition ran 8 ML papers vs 5
fundamental-science + 3 biology in the prose sections, a genuine ~50/50 at the paper level; the
0.615 counts models/datasets and data-science items on the ML side. No flag, but it is at the top of
the band — worth watching if it drifts past 0.65.

**I. Repetition (computed) + identity integrity.** `reconcile.py`: **0 flagged**, 0
resolved-by-merge, 24 editions checked — no forked ids (the 2026-07-07 Cuba class stays closed).
Repeat rates: news 0.205 (8/39), weekend 0.208, sports 0.25 (1/4). I checked the flagged news
recurrences — they are `[ongoing since]` threads carrying **new dated facts**, not re-summaries:
Ebola (st-…, [ongoing since 2026-06-22]) advanced from ~1,000 to 2,184 deaths with a fresh $30.5m UN
allocation and Fletcher's 14 Aug "Ebola is winning"; the Lebanon strike thread ([ongoing since
2026-08-05]) is a new 15 Aug Ansar event. Discipline is good — these are updates, not repeats.

**J. Cross-week trend.** Vs 2026-08-09: aggregator leakage 0→0, T3 0→0, empty sections 0→0, feedback
all-positive both weeks, off-main clean both weeks. Weekend waiver 1.00 unchanged (the un-applied
patch). Word-means down or flat everywhere (§L) — no cost creep. Healthy, stable trend.

**K. Feed reachability & direct-fetch (computed).** Portfolio direct-fetch ~0.98; every stream meets
its range (ai-ml 1.00, news 0.975, science 1.00, sports 1.00, weekend 1.00). The curl→proxy chain is
doing its job: export.arxiv.org (52 ok curl), aljazeera.com (35 curl), srf.ch (31 curl),
letemps.ch (22 curl), nature.com (6 curl + 10 proxy) all resolve. Feeds failing >50% of attempts are
mostly low-volume or curl-fails-then-proxy-recovers (dw.com 14 fail/8 proxy-ok, france24 20/7,
sana.sy 19/17 — the proxy carries them). The **one material fully-walled feed (0 ok on both curl and
proxy)** is `api.openalex.org` (0/6) — this is what forces the affiliation gaps in §N, since OpenAlex
is the byline-enrichment path. `link.aps.org` (0/4) and `api.github.com` (0/4) are the next two, both
worked around. Domains-that-shouldn't-be-cited check: no `reach: blocked` domain appeared without
`[via snippet]`; no `never:` domain appeared; no retired/demoted domain as a primary anchor. Clean.
`letour.fr` failed again in sports (0 ok, ERR:56 + 404) — reinforcing the carried uci.ch promotion.

**L. Output volume (computed).** Word-means all flat or **down** week-over-week: ai-ml 2352
(prev 2662), news 1155 (prev 1227), science 1459 (prev 1399, +4%), sports 1148 (prev 1152), weekend
5304 (prev 6912, −23%). No stream grew >25%; the token-cost proxy is trending the right way. Weekend
in particular tightened significantly without losing coverage (24 anchors). No output-cap lever
needed.

**M. Editorial shape.** All three checks pass cleanly this week:
- *Vendor-PR-lead share (AI/ML) ≈ 10%.* Both editions **lead with research**, not vendor framing —
  the through-lines are "efficiency by subtraction" (08-11) and "the field auditing its own
  autonomous-scientist ambitions" (08-14), and the vendor releases are demoted to release sections
  where each carries independent judgment ("as much about the competitive squeeze on inference
  margins as about the model"; "treat the head-to-head numbers as the authors' own until
  reproduced"; "independent benchmarks will tell"). Well under the 40% bar.
- *Aggregator-shape failures = 0/5.* Sampled leads (news forest-survey, Vaud procurement motion;
  weekend Faraday, floods; sports Lugano) all cite a primary and add framing the source doesn't
  contain. None reads like a rewritten blurb.
- *Personalization misses = 0/5.* Strong where available: the Vaud digital-sovereignty procurement
  motion is explicitly framed for Swiss software professionals; the CH forest/drought, Rhine-ferry,
  and Swissmedic cleanroom items all land the CH angle; ai-ml keeps the builder/local-inference lens
  (Apple Silicon ports, efficiency levers). No forcing where absent.

**N. Affiliation element (papers streams).** Coverage rate ≈ **16% `(affiliation not listed)`**
portfolio-wide (ai-ml 2/16, weekend ML 3/8, weekend science 0/5, weekend bio 0/3, science 1/7) —
under the 20% target 🟢, though the weekend-ML slice (37.5%) sits above it. The unlisted cases are
concentrated in fresh arXiv ML papers whose HTML author blocks don't render and whose DOIs OpenAlex
hasn't indexed yet (documented in both footers) — an infrastructure limit the writers handle
honestly by marking unlisted rather than guessing. **Halo audit: no prestige bias.** The
`(affiliation not listed)` / independent papers were *not* systematically scored down — Faraday
(unlisted affiliation) got the single biggest write-up and a "read three things" slot in both ai-ml
and weekend; the Devoteam single-author eval-probe papers earned prominent placement. Affiliations
are being recorded for the reader, not used as a selection signal. Good.

## Prior proposals status

From 2026-08-09:
- **rm-1** (weekend discovery dormancy → `routines/src/weekend.md`): **pending, not applied.** Grep of
  weekend.md finds no dormant-source / before-waiving language; the block exists only in science.md.
  Weekend waiver_rate is still 1.00, consistent with the patch never landing. Carried forward below.
- **registry-2026-08-09.yml** (`applied: false`, never stamped): esv.ch and uci.ch candidate→probation
  — both **still `status: candidate`** in `sources/registry.yml`, not applied. Carried again (they
  fill the Sports primary gap; uci.ch reinforced by letour.fr failing this week). The four reach
  flips noted as already-landed in that file (science.org/swissinfo.ch/cell.com/journals.aps.org →
  proxy) remain correct in the registry.

## Source scout (Sunday duty)

**Stream picked: science** — lowest `new_domains` (8), the tie-breaker path. Budget used: **3
candidate fetches** (cell.com, pnas.org, eurekalert.org), **all returned ERR:56** — the evaluator
sandbox's direct egress is fully walled this window (same wall as the 4/20 linkcheck), and this
routine holds no fetch-proxy bearer by design. So probing degrades to appending vetted candidates
with `reach: proxy-needed` for the writers to confirm at first citation.

Finding: science's registry is **not thin** — it already holds ethz.ch, epfl.ch, psi.ch, empa.ch,
unige.ch, unibe.ch, news.uzh.ch, mpg.de, esa.int, home.cern, eso.org, noirlab.edu, newscenter.lbl.gov,
elifesciences.org, pnas.org, scipost.org, wsl.ch, eawag.ch. The `new_domains=8` deficit is dormancy,
not absence; the 08-12 science edition probed two registered newsrooms (noirlab, eso) and honestly
waived when nothing new surfaced. Still, this week's heavy climate/forest/glacier/water science
surfaced three genuine primary Swiss bodies genuinely **absent** from the registry, appended to
`sources/candidates.jsonl` (all `reach: proxy-needed`):
- **slf.ch** — WSL Institute for Snow and Avalanche Research (glacier/snow/climate primary).
- **unil.ch** — University of Lausanne newsroom (Vaud science personalization primary).
- **scnat.ch** — Swiss Academy of Sciences (genuine primary science body).

Re-probe of 5 stale reach entries: **skipped** — direct curl is walled from this sandbox (0 successes
this run), so any 403/timeout would be an artifact of the evaluator's egress, not evidence about the
domain. No reach flips proposed; reach truth stays with the writers' bearer and the deterministic
probes.

## Patch proposals (for human review)

Only one, carried — the pipeline is otherwise healthy and I'm not manufacturing patches.

### Patch 1 — Weekend discovery dormancy (CARRIED from 2026-08-09, still un-applied)
**Target prompt:** Weekend (`routines/src/weekend.md`)
**Section affected:** Sourcing / Discovery footer block
**Issue:** Weekend waives discovery 100% of the time (waiver_rate=1.00). The deficit is dormancy, not
absence — the registry holds many dormant weekend-affinity primaries the writer doesn't reactivate
before waiving. The exact fix already exists in science.md (landed 2026-08-02, commit 7f8e440) and
demonstrably raised science's dormant-domain reactivation; weekend never received it.
**Proposed change:**

> **Before:**
> ```
> (weekend.md has no dormant-source-activation instruction; only the Tiers line and the
>  "- Discovery: {met | waived — <reason>}" footer spec)
> ```
>
> **After:**
> ```
> Dormant-source activation — do this BEFORE waiving discovery. The registry carries a stack of
> weekend-affinity domains you have not cited recently (institutional newsrooms, lab/engineering
> blogs, journal primaries). Before emitting "Discovery: waived", probe at least two of these
> dormant, registered domains from the preflight plan, plus any genuinely-new primary the week's
> reading surfaced; name which you tried in the waiver reason. A new anchor that resolves to a hub
> (hf.co, github.com, arxiv.org, nature.com) does NOT count as a new primary — only waive if the
> dormant probes and any new candidate are genuinely unreachable or off-topic.
> ```

**Why this helps:** turns weekend's honest-but-absolute waiver into an active reactivation pass, the
same lever that already works for science.
**Risk:** minimal — it adds a bounded probe step, not new fetch budget; worst case the writer probes
two dormant domains, finds nothing, and waives with a more specific reason than today.

## Reader-feedback → profile proposals

**No reasoned feedback this week — nothing to propose.** The window carried **16 feedback events,
all bare 👍 (`reason: ""`), zero 👎, zero retractions**, `unconsumed_total: 0` (bridge fold current).
Per the completeness rule, the set of *reasoned* events (non-empty `reason`) is **empty**, so there
are no dispositions to enumerate and nothing crosses the ≥2-distinct-stories noise bar with a
citable theme. The aggregate signal is strongly positive and worth noting — ai-ml drew 7 👍 (six of
them on distinct stories in the 08-11 edition), weekend 4, news 4, science 1 — but bare taps carry no
theme text, so under the bounded auto-apply grant (which requires a written reason or a repeated
vote with a decodable preference) there is nothing specific to reinforce into `reader-profile.md`. No
line appended; the "Learned preferences" section is unchanged.

## Cross-week trend

Stable and healthy (see §J): zero-defect dimensions held from last week, output volume flat-to-down,
the one carried structural item (weekend waiver) unchanged pending the patch. No new regressions.

## Open questions for human review

1. **rm-1 has been pending a full week.** It's a proven, low-risk fix already live in science.md.
   Worth applying to weekend.md before next Saturday, or is weekend's paper-hub sourcing considered
   acceptable as-is?
2. **`api.openalex.org` is fully walled (0/6, both curl and proxy).** It's the byline-enrichment path,
   and it's the sole cause of the weekend-ML affiliation gaps (§N). The writers work around it via
   article HTML author blocks, so it's not urgent — but if OpenAlex affiliations matter for the halo
   audit long-term, this feed needs an alternative (Crossref? Semantic Scholar?) or a proxy fix. Not
   a prompt patch; flagging for infra.
3. **Reader-brief proposals:** `proposals/*.jsonl` reader-suggestion directory does not exist — no
   reader topic proposals to surface this week.

_No brief-proposals directory, no unconsumed feedback, no forked ids, no off-main diversion — the
mechanical plane is quiet. The one thing worth a human's five minutes is applying rm-1._
