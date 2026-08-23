---
layout: single
title: "Weekly Pipeline Review — 2026-08-23"
date: 2026-08-23T11:44:17+02:00
categories: [evaluator]
published: true
---

# Weekly Brief Pipeline Review — 2026-08-23

_Coverage: briefs from 2026-08-17 to 2026-08-23._
_Files read: 6 news, 2 AI/ML (expected ~2), 1 science (expected ~1), 1 sports (expected ~1), 1 weekend, prior review found (2026-08-16, 7 days old)._

Another clean, high-functioning week. Every stream fired on cadence, the deterministic dimensions
— aggregator leakage, empty sections, identity reconciliation, off-main self-delivery, feedback
backlog — all came back at zero, and portfolio direct-fetch held at **1.00** (zero via-snippet
citations across all 11 posts). The week's two live items are both familiar: the **weekend
discovery waiver** is still the portfolio's worst (0.80, down from last week's 1.00 but the fix,
rm-1, is now pending a third week), and a reader left the first **reasoned downvote in weeks** —
naming France 24 as an unreliable source, which the fetch data independently corroborates. I
auto-applied a reader-profile line for it and propose a source-weights demotion. Below, the
numbers I read rather than recounted, and the editorial judgment the scripts can't make.

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains 30d (worst stream, source-health) | science 9 | ≥30 | 🟡 |
| New domains this window (portfolio, source-health) | ~73 / 30d (≈18/wk) | ≥2–3/wk (≥10/mo) | 🟢 |
| Top-5 outlet share (worst stream, source-health) | science 1.00 | ≤0.50 (→0.35) | 🟡 |
| Waiver rate (worst stream, source-health) | weekend 0.80 | ≤50% | 🔴 |
| Discovery footer present (every brief) | 11/11 | 100% | 🟢 |
| T1 citation %                   | ~45%  | ≥40%   | 🟢 |
| T3 leakage count                | 0     | 0      | 🟢 |
| Non-English citation % (portfolio) | ~20% (FR/DE/IT) | ≥10% | 🟢 |
| Link sample pass rate           | 4/20 (unmeasurable) | ≥90% | ⚪ |
| Fabrication count               | 0     | 0      | 🟢 |
| Single-source rate (portfolio)  | 12% (16/133) | <20% | 🟢 |
| Empty section instances         | 0     | <5     | 🟢 |
| Repeat rate (worst stream, health.json) | weekend 0.36 / news 0.20 | judge | 🟢 |
| Direct-fetch ratio (portfolio)  | 1.00  | ≥0.35  | 🟢 |
| Feeds with >50% fail rate       | ~4 material (openalex/openai/france24/admin.ch); rest proxy-recovered | 0 | 🟡 |
| Citations on `reach: blocked` domains without [via snippet] | 0 | 0 | 🟢 |
| Unconsumed feedback backlog (health.json) | 0 | 0 | 🟢 |
| Vendor-PR-lead share (AI/ML, §M) | ~12% | ≤40% | 🟢 |
| Aggregator-shape failures (§M, of 5) | 0 | 0–1 | 🟢 |
| Personalization misses (§M, of 5) | 0 | 0–1 | 🟢 |

## A–N: Detailed findings

**A. Source diversity & discovery.** 30-day source-health: news `unique=40 / new=32 / top5=0.726 /
waiver=0.467` (saturated: srf.ch); ai-ml `21 / 15 / 0.786 / 0.111`; science `9 / 7 / 1.00 / 0.500`
(saturated: nature.com); sports `10 / 9 / 0.722 / 0.250` (saturated: bbc.co.uk, srf.ch); weekend
`21 / 10 / 0.761 / 0.800`. Portfolio new-domain flow stays strong (≈73 over 30d, ~18/wk 🟢). The
two structural 🟡s are unchanged from prior weeks and not regressions:
- *Top-5 outlet share* trips its bar on every stream because it measures only the outlet-class
  slice after hubs/institutional are excluded, and the papers streams cite almost entirely hub
  primaries. **Science hits 1.00 this week** for a specific, honestly-documented reason: OpenAlex
  was rate-limited (HTTP 429) all session and Science.org article pages were unreachable, so the
  19 Aug edition leaned entirely on the Nature portfolio (Nature / Nature Physics / Nature
  Astronomy) — the writer said so in its Gaps footer. That is an egress artifact, not lazy
  sourcing. ai-ml's 0.786 is the-decoder.com carrying the non-hub secondary load, expected for an
  AI-news stream with a healthy T1 mix underneath (62–75% T1 in the two editions).
- *Science unique=9* is a low-cadence artifact (27 stories/30d over ~4 editions); stable, not
  shrinking, and the registry behind it is rich.

The real deficit remains **weekend waiver_rate=0.80**. It improved from last week's 1.00, but read
the 2026-08-22 footer carefully: discovery was *met* this week only because the week's reading
happened to surface two genuinely-new institutional primaries (actu.epfl.ch and media.inaf.it, both
`[new source]`) — not because the writer ran an active dormant-domain probe pass before waiving.
That is luck of the week's arXiv/Nature slate, not the reactivation discipline rm-1 would install.
The 0.80 across the 30-day window confirms the underlying behaviour hasn't changed. See rm-1.

Tier distribution (from footers): T1 ≈ 45% portfolio — papers streams run high (ai-ml 62–75% T1,
weekend 48%), while news/science/sports are structurally T2 because their quality-secondary
primaries (SRF, Le Temps, Al Jazeera, Nature, BBC) register as T2, not a miss. T3 leakage = 0.
Linguistic: FR + DE + IT citations run ~20% portfolio (SRF, Le Temps, Le Monde, NZZ, DW, media.inaf.it,
letemps) — comfortably ≥10%. Geographic spread on news is wide (Japan, Syria, France, Switzerland,
Israel, DRC, Canada, Ukraine, Iran).

**B. Aggregator leakage (computed).** `aggregator_leakage: []` — zero HN/Reddit/X/Bluesky/etc.
citations across all 11 posts. Clean.

**C. Link health — UNMEASURABLE this run.** `linkcheck --check` resolved **4/20** (the four that
came back: quantamagazine, letemps ×1, aljazeera, srf 200; srf gave one 403; everything else
ERR:56 on arxiv, huggingface, the-decoder, france24, euronews, swissinfo, generalistai, newcomer).
This is the evaluator sandbox's own egress wall, not broken links: the writers' Coverage footers
show `direct_fetch_ratio` = **1.00** with `via_snippet` = 0 across *every* stream — they fetched
these same hosts fine through the fetch-proxy bearer the evaluator deliberately lacks, and only the
curl-direct-friendly hosts (quanta, letemps, aljazeera, srf) resolve from this sandbox. Reporting
the dimension unmeasurable per the prompt's egress-regression clause; the wall is the evaluator's,
not a writer regression. Claim spot-checks were limited to the handful of hosts that resolved
(letemps Le Locle watch-museum-robbery item, aljazeera Moscow-drones and E1-settlement items, srf
Iran and Kryvyi-Rih items, quanta discrepancy feature) — each claim is present and accurately
represented in the source; no fabrications detected in the resolvable sample.

**D. Section vitality (computed).** `empty_sections: []` on every stream. AI/ML twice, Science/Sports
once, Weekend once — all correct cadence. Nothing to flag.

**E. Coverage gap recurrence.** Reading the Gaps footers, the recurring cluster is
infrastructure-shaped, not beat-shaped, and identical to prior weeks: `api.openalex.org` rate-limited
(429) so paper affiliations were read from article HTML author blocks instead (weekend + science);
admin.ch / treasury.gov / state.gov unreachable so the Swiss air-defence credit and ICC-sanctions
items rested on SRF/NZZ and France 24/JPost/Le Monde respectively (news); official league/governing
sites (sfl.ch, uefa.com, formula1.com) JS-shells so sports leaned on BBC/SRF. None recurred ≥3 times
as a *content* gap — each was routed around honestly. No structural content hole.

**F. Triangulation rate (computed).** Single-source portfolio **16/133 = 12%** (<20% 🟢). Per stream:
news 0.098, weekend 0.091, science 0.00, ai-ml 0.212, sports 0.167. ai-ml sits highest — its
single-source items are vendor releases and sourced-reporting the writer correctly tags
`[single-source]` (EVIE benchmarks, Anthropic data-retention plan, Model Hypnosis single-lab
result), i.e. honest labeling of genuinely un-triangulable claims, not lazy sourcing. All streams
under the 25% per-stream bar. Acceptable.

**G. Tag discipline.** Counts (health.json): `[preprint]` ai-ml 18, weekend 12 — every arXiv item
tagged, and science correctly carries none (it cited Nature articles, not preprints). `[vendor PR]`
ai-ml 5, weekend 3 — on Nemotron, UI-Mate, EVIE, Google-Research-BMI, GEN-1.5, Ornith, Qwen,
LiquidAI; each carries independent framing (see §M). `[disputed]` = 1 (Nvidia–Poolside deal, no
first-party release) — appropriate. `[new source]` spot-check of 2: **research.nvidia.com**
(NVIDIA's first-party institutional research domain, Nemotron-3 technical report) and
**media.inaf.it** (INAF's own newsroom, the Milky-Way-merger release) — both genuine primaries,
zero junk anchors. Sports used `[unconfirmed]` ×2 (Rodri transfer "not yet official"; Djokovic
health disclosure in a depleted draw) — not in the formal rubric but exemplary honest labeling of
un-completed/un-triangulable claims. `[via snippet]` = **0 across all streams** — the curl-first
chain is working; snippet rates are floor-low.

**H. Topic balance (weekend, computed).** `ml_items=20, science_items=16, ml_share=0.556` — inside
the [0.35, 0.65] band 🟢, a genuine ~55/45 lean to ML. Down from last week's 0.615; healthy.

**I. Repetition (computed) + identity integrity.** `reconcile.py`: **0 flagged**, 0
resolved-by-merge, 24 editions checked — no forked ids (the 2026-07-07 Cuba class stays closed).
Repeat rates: news 0.20 (8/40), weekend 0.36 (12/33), others 0. I checked both flagged streams:
- *News 0.20* is the `[ongoing since]` threads (Iran war, DRC Ebola, Swiss drought, neutrality poll)
  each carrying **new dated facts** — the Ebola item advancing to 5,290 cases / 2,516 deaths with
  the 20 Aug vaccine allocation, the E1 tender opening 18 Aug and drawing the 20 Aug seven-government
  statement. Updates, not re-summaries. Good discipline.
- *Weekend 0.36* is **by design and disclosed**: the weekend brief's "Sibling consultation" footer
  explicitly states it revisits the 19 Aug science daily's marquee results (single-CuO₂ plane,
  e/3 antidot, skeletal editing, bottom-heavy IMF) at greater length *and* adds fresh finds the
  dailies missed (QWM, Test-Time-Scaling-in-the-Wild, S301/Sgr A*, CFT-on-atoms, atomic double-slit,
  Beyond-the-Trace). That is the weekend's stated job — deeper treatment + synthesis — not a
  re-run. The overlap is intentional, so 0.36 is not a defect here.

**J. Cross-week trend.** Vs 2026-08-16: aggregator leakage 0→0, T3 0→0, empty sections 0→0, reconcile
0→0, off-main clean→clean, feedback backlog 0→0. Weekend waiver 1.00→0.80 (nominal improvement, but
driven by luck not the pending patch). Weekend word-mean 5304→3112 (−41%, continuing the tightening
trend). One new signal this week absent last week: the first reasoned reader downvote in a month
(§ reader-feedback). Healthy, stable trend with the same one structural item carried.

**K. Feed reachability & direct-fetch (computed).** Portfolio direct-fetch **1.00**; every stream
meets its range (all at 1.00). The curl→proxy chain is doing its full job: export.arxiv.org (68 ok
curl this week), aljazeera.com (22 curl), srf.ch (35 curl), letemps.ch (21 curl), quantamagazine.org
(7 curl) resolve direct; nature.com (6 curl + 65 proxy), arxiv.org (40 proxy), huggingface.co
(82 proxy) recover via proxy. Feeds failing >50% of attempts split into two classes:
- *Proxy-recovered* (not material): huggingface.co (80 fail / 82 proxy-ok), theguardian.com (21/17),
  european-athletics.com (19/9), france24.com (26/6), techcrunch.com (9/9) — curl fails, proxy
  carries them, citations land fine.
- *Materially walled* (0 or near-0 ok on both paths): **`api.openalex.org` (23 fail / 0 ok)** — the
  byline-enrichment path, rate-limited (429) all week, the sole cause of any affiliation gaps (§N);
  **`openai.com` (21 fail / 1 proxy-ok)** — vendor blog, forcing OpenAI items to secondary reporting;
  **`admin.ch` (11 fail / 0 ok, HTTP 403)** — Swiss federal primary, forcing the air-defence credit
  onto SRF/NZZ; and a scatter of low-volume 0-ok domains (ai.meta.com, axios.com, eso.org). OpenAlex
  and admin.ch are the two worth infra attention (both recur weekly); neither is a prompt patch.

Domains-that-shouldn't-be-cited check: no `reach: blocked` / `blocked-paywall` domain appeared
without `[via snippet]`; `never:` is empty so nothing to violate; no retired/demoted domain as a
primary anchor. Clean.

**L. Output volume (computed).** Word-means: ai-ml 2686 (prev 2352, +14%), news 1205 (prev 1154,
+4%), science 1632 (prev 1459, +12%), sports 1418 (prev 1148, **+23.5%**), weekend 3112 (prev 5304,
−41%). No stream crossed the +25% flag; sports is closest but it ran a genuinely eventful week
(three Swiss Euro golds + a Guardiola-era-ends narrative) with 6 anchors, so the growth tracks
content, not padding. Weekend's continued −41% tightening is the standout — deep coverage at 3,112
words with 33 anchors and full cross-cutting synthesis. No output-cap lever needed.

**M. Editorial shape.** All three checks pass cleanly:
- *Vendor-PR-lead share (AI/ML) ≈ 12%.* Both editions **lead with research**: 08-18's through-line
  is "the stack getting more principled and cheaper / agents becoming objects of study," 08-21's is
  "does an agent's advertised ability survive a proper control." Vendor releases are demoted to a
  "New models" section, each with independent judgment ("adoption is negligible so far";
  "vendor-reported and await independent confirmation"; GEN-1.5's "ChatGPT moment for robotics"
  framing explicitly flagged as "a claim to verify, not a settled result"). Well under 40%.
- *Aggregator-shape failures = 0/5.* Sampled leads (news ICC-sanctions, weekend E1 settlement,
  ai-ml matrix-multiplication, science single-CuO₂-plane, sports Community Shield) each cite a
  primary and add framing the source doesn't contain. The one soft spot is the France-Iran
  diplomat-expulsion item (news 08-19) single-sourced to France 24 — see the reader feedback below;
  it still cites a wire, not an aggregator, so it isn't a formal §M failure, but it is exactly the
  weakness the reader flagged.
- *Personalization misses = 0/5.* Strong where available: the Swiss individual-taxation reform
  ("decides whether marriage carries a tax cost"), the 970M air-defence credit (post-neutrality
  rearmament), French assisted-dying (framed for Switzerland's own end-of-life rules), the
  neutrality-initiative poll, and the ai-ml Anthropic data-retention item ("a live procurement and
  compliance question for Swiss and EU enterprises") all land the CH / builder angle. No forcing
  where absent.

**N. Affiliation element (papers streams).** Coverage rate ≈ **9% `(affiliation not listed)`**
portfolio-wide (ai-ml 3/18 — all three in the 08-21 edition; weekend 0 in the paper sections;
science 0) — comfortably under the 20% target 🟢. The three unlisted cases (MemTrapBench,
SWE-bench-Science, adaptive-thinking-budget) are fresh 20 Aug arXiv ML papers whose HTML author
blocks didn't render and whose DOIs OpenAlex hadn't indexed (429 all session) — handled honestly by
marking unlisted rather than guessing. **Halo audit: no prestige bias.** The unlisted / independent
papers were *not* systematically scored down — SWE-bench-Science (affiliation not listed) was a
"read three in full" pick in the 08-21 edition, and the weekend gave prominent, full-length
treatment to papers regardless of lab prestige. Affiliations are being recorded for the reader, not
used as a selection signal. Good.

## Prior proposals status

From 2026-08-16:
- **rm-1** (weekend discovery dormancy → `routines/src/weekend.md`): **pending, not applied** — now a
  third consecutive week. Grep of weekend.md finds only the generic shared discovery-quota partial
  ("candidates_to_try … dormant domains worth a probe"), NOT the science.md "Dormant-source
  activation — do this BEFORE waiving discovery" probe block. Weekend waiver_rate is still 0.80.
  Carried forward below.
- **registry-2026-08-16.yml** (`applied: false`, never stamped): esv.ch and uci.ch
  candidate→probation — both **still `status: candidate`** in `sources/registry.yml` (verified lines
  3080, 3092), not applied. Carried again. **Positive verification:** last week's three *scout
  candidates* (slf.ch, unil.ch, scnat.ch) **did land** in `sources/registry.yml` (lines
  3686/3698/3710) — so the candidates.jsonl → registry scout path is working end-to-end, even though
  the lifecycle-transition proposals still await Rafael's apply step.

## Source scout (Sunday duty)

**Stream picked: science** — lowest `new_domains` (7), no tie-break needed. Budget used: **3 probe
fetches** (mpe.mpg.de, home.cern, leibniz-gemeinschaft.de), **all returned ERR:56** — the evaluator
sandbox's direct egress is fully walled this window (same wall as the 4/20 linkcheck), and this
routine holds no fetch-proxy bearer by design. So probing degrades to appending vetted candidates
with `reach: proxy-needed` for the writers to confirm at first citation.

Finding: science's registry is **not thin** — it already holds ethz.ch, epfl.ch, psi.ch, empa.ch,
unige.ch, unibe.ch, mpg.de, esa.int, home.cern, eso.org, noirlab.edu, elifesciences.org, pnas.org,
scnat.ch, unil.ch, slf.ch and more; the `new_domains=7` deficit is dormancy, not absence (same
diagnosis as last week, now reinforced by three of last week's candidates having landed). This
week's astronomy-heavy slate (S301/Sgr A*, bottom-heavy IMF, Milky-Way merger, Deimos) surfaced two
genuine primary astrophysics bodies genuinely **absent** from the registry, appended to
`sources/candidates.jsonl` (both `reach: proxy-needed`):
- **skao.int** — SKA Observatory (radio-astronomy primary / official newsroom).
- **aip.de** — Leibniz Institute for Astrophysics Potsdam (genuine primary astrophysics body).

Re-probe of stale reach entries: **skipped** — direct curl is walled from this sandbox (0 successes
this run), so any 403/timeout would be an artifact of the evaluator's egress, not evidence about the
domain. No reach flips proposed; reach truth stays with the writers' bearer and the deterministic
probes.

## Patch proposals (for human review)

Two — one carried, one new from reader feedback. The pipeline is otherwise healthy; I'm not
manufacturing patches.

### Patch 1 (rm-1) — Weekend discovery dormancy (CARRIED from 2026-08-09/-16, still un-applied)
**Target prompt:** Weekend (`routines/src/weekend.md`)
**Section affected:** Sourcing / Discovery footer block
**Issue:** Weekend's 30-day waiver_rate is 0.80 (portfolio worst). This week's "Discovery: met" was
luck — two new institutional primaries happened to surface in the reading — not an active
dormant-probe pass. The exact reactivation fix already exists in science.md (landed 2026-08-02,
commit 7f8e440) and demonstrably raised science's dormant-domain reactivation; weekend never
received it.
**Proposed change:**

> **Before:**
> ```
> (weekend.md carries only the generic shared discovery-quota partial — "candidates_to_try …
>  dormant domains worth a probe" — with no BEFORE-waiving probe requirement.)
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

**Why this helps:** turns weekend's luck-dependent waiver into an active reactivation pass, the same
lever that already works for science.
**Risk:** minimal — a bounded probe step, not new fetch budget; worst case the writer probes two
dormant domains, finds nothing, and waives with a more specific reason than today.

### Patch 2 (rm-2) — Demote France 24 in source weights (NEW, from reader feedback)
**Target file:** `reader-profile/source-weights.yml` (human-gated — propose only)
**Section affected:** `reduce:` list
**Issue:** A reader left a reasoned downvote (st-d03f80975246, 2026-08-19-news ICC-sanctions lead):
*"france 24 as source is brutally out of touch, you should have found more reliable sources."* The
downvoted item **led** with France 24 ahead of Jerusalem Post and Le Monde, and the same edition
**single-sourced** the France–Iran diplomat-expulsion item to France 24 alone (st-a54c31f0b12f) when
Le Monde / AFP / Reuters carried the same story. Mechanically corroborated: france24.com failed ~81%
of fetch attempts this window (26 fail / 6 ok via proxy).
**Proposed change:**

> **Before:**
> ```
> reduce: []
> ```
>
> **After:**
> ```
> reduce:
>   - france24.com                  # 2026-08-19: 1× 👎 "brutally out of touch, find more reliable
>                                   #   sources"; led/single-sourced when Le Monde/AFP existed
> ```

**Why this helps:** the writer will prefer a stronger wire/primary (Le Monde, Reuters, AFP,
Al Jazeera) when one exists, and stop leading or single-sourcing on France 24.
**Risk:** low — `reduce:` is a soft penalty, not a hard `never:` drop; France 24 is a legitimate
state-funded international broadcaster and stays available when it's the only source for a
significant story. Over-demotion could cost a genuine France-desk exclusive, but the soft-penalty
semantics guard against that.

## Reader-feedback → profile proposals

The window carried **12 feedback events**: 10 bare taps (`reason: ""`) and **2 reasoned**, with
`unconsumed_total: 0` (bridge fold current). Aggregate tally is positive — ai-ml 5 👍, news 4 👍 /
2 👎, weekend 1 👍. Per the completeness rule, every reasoned event gets a disposition:

- **st-d03f80975246** (2026-08-19-news, 👎, *"france 24 as source is brutally out of touch, you
  should have found more reliable sources"*): **APPLIED.** Auto-applied a dated line to
  reader-profile.md "Learned preferences" (a vote with a written reason qualifies under the
  2026-07-10 bounded grant) *and* proposed the source-weights `reduce: france24.com` demotion (rm-2
  above). Corroborated by the 81% france24 fetch-fail rate and the same edition's France-24
  single-sourcing.
- **st-d2de83c4e4be** (2026-08-18-ai-ml, 👍, *"very, very important"*): **DEFERRED.** Positive
  reinforcement on the AlphaEvolve matrix-multiplication paper (an AI system nudging a 60-year-old
  theoretical-CS constant) — squarely the "primary sources / new developments over aggregator
  restatements" the reader profile already favours. But it is a single 👍 on one story with no
  decodable *new* preference beyond the existing profile line, so it falls below the
  ≥2-distinct-stories noise bar for a new proposal. Noted as reinforcement of the current direction;
  nothing new appended.

The 10 bare taps carry no theme text and don't cross the noise bar. The auto-applied line and both
prompt-patch proposals are emitted machine-readable in `proposals/reader-model-2026-08-23.json`
(rm-3 stamped `applied: true, applied_by: evaluator`; rm-1, rm-2 `applied: false`).

## Cross-week trend

Stable and healthy (see §J): every zero-defect dimension held from last week, output volume flat or
down, weekend waiver nominally improved but still driven by luck rather than the pending rm-1. The
only new signal is the France 24 reasoned downvote — now acted on. No new regressions.

## Open questions for human review

1. **rm-1 is pending a third week.** It's a proven, low-risk fix already live in science.md, and
   weekend's 0.80 waiver is the portfolio's only 🔴. This week's "Discovery: met" was luck, not
   discipline — worth applying to weekend.md before next Saturday?
2. **rm-2 (France 24 demotion) is the first source-quality complaint in a month** and is
   double-corroborated (reader reason + 81% fetch-fail). Worth the two-line source-weights edit?
3. **`api.openalex.org` remains fully walled (0 ok, 429 all week)** — the byline-enrichment path and
   sole cause of any affiliation gap. Writers work around it via article HTML author blocks (which
   held affiliation-unlisted to 9% this week), so it's not urgent — but if OpenAlex affiliations
   matter long-term, an alternative (Crossref? Semantic Scholar?) or a proxy fix is the fix.
   `admin.ch` (403, forcing the Swiss air-defence credit onto SRF/NZZ) is the second recurring
   infra wall. Neither is a prompt patch; flagging for infra.
4. **Reader-brief proposals:** `proposals/*.jsonl` reader-suggestion directory does not exist — no
   reader topic proposals to surface this week.

_No brief-proposals directory, no unconsumed feedback, no forked ids, no off-main diversion — the
mechanical plane is quiet. The two things worth a human's five minutes are applying rm-1 (three
weeks pending) and the one-line France 24 demotion the reader explicitly asked for._
