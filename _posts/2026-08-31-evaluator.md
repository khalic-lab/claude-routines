---
layout: single
title: "Weekly Pipeline Review — 2026-08-31"
date: 2026-08-31T12:05:00+02:00
categories: [evaluator]
published: true
---

# Weekly Brief Pipeline Review — 2026-08-31

_Coverage: briefs from 2026-08-25 to 2026-08-31._
_Files read: 4 news, 2 AI/ML (expected ~2), 1 science, 1 sports, 1 weekend, prior review found (2026-08-23, 8 days old)._

A healthy week with one scheduling wrinkle and two familiar carried items. Every stream fired on
cadence, and the deterministic dimensions — aggregator leakage, empty sections, identity
reconciliation, off-main self-delivery, feedback backlog — all came back at **zero**. Portfolio
direct-fetch held at ~0.99 (one via-snippet citation across nine posts). The wrinkle: **this run
fired Monday 2026-08-31, not Sunday** — the Sunday 08-30 slot has no ledger file and produced no
evaluator post, so the window is 6 days of dailies rather than the usual 7 (4 News instead of ~6,
because Sun 08-30 and the same-day Mon 08-31 News aren't in scope). off_main is clean, so this is a
genuinely skipped/late Sunday, **not** an off-main stranding. The two live items are both carried:
weekend discovery waiver (now the portfolio's only structural amber, and its fix rm-1 is pending a
**fourth** week), and the France 24 demotion (rm-2, pending a second week, re-corroborated this week
by france24 failing 100% of fetch attempts). One new reader-feedback theme — two reasoned downvotes
asking the News stream for more fiscal-context skepticism — is auto-applied below.

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains 30d (worst stream, source-health) | science 8 | ≥30 | 🟡 |
| New domains this window (portfolio, source-health) | ~69 / 30d (≈16/wk) | ≥2–3/wk (≥10/mo) | 🟢 |
| Top-5 outlet share (worst stream, source-health) | science 1.00 | ≤0.50 (→0.35) | 🟡 |
| Waiver rate (worst stream, source-health) | weekend 0.60 | ≤50% | 🟡 |
| Discovery footer present (every brief) | 9/9 | 100% | 🟢 |
| T1 citation %                   | ~40% (papers streams carry it) | ≥40% | 🟢 |
| T3 leakage count                | 0     | 0      | 🟢 |
| Non-English citation % (portfolio) | ~20% (FR/DE) | ≥10% | 🟢 |
| Link sample pass rate           | 6/20 (unmeasurable — evaluator egress) | ≥90% | ⚪ |
| Fabrication count               | 0     | 0      | 🟢 |
| Single-source rate (portfolio)  | 12.5% (14/112) | <20% | 🟢 |
| Empty section instances         | 0     | <5     | 🟢 |
| Repeat rate (worst stream, health.json) | weekend 0.79 (by design) / news 0.14 | judge | 🟡 |
| Direct-fetch ratio (portfolio)  | ~0.99 | ≥0.35  | 🟢 |
| Feeds with >50% fail rate       | ~4 material (admin.ch/openalex/france24/espn); rest proxy-recovered | 0 | 🟡 |
| Citations on `reach: blocked` domains without [via snippet] | 0 | 0 | 🟢 |
| Unconsumed feedback backlog (health.json) | 0 | 0 | 🟢 |
| Vendor-PR-lead share (AI/ML, §M) | ~0% | ≤40% | 🟢 |
| Aggregator-shape failures (§M, of 5) | 0 | 0–1 | 🟢 |
| Personalization misses (§M, of 5) | 0 | 0–1 | 🟢 |
| Affiliation-not-listed rate (§N, papers) | ~19% | <20% | 🟡 |

## A–N: Detailed findings

**A. Source diversity & discovery.** 30-day source-health: news `unique=34 / new=22 / top5=0.740 /
waiver=0.571` (saturated: srf.ch); ai-ml `20 / 16 / 0.743 / 0.125`; science `8 / 5 / 1.00 / 0.500`
(saturated: nature.com); sports `16 / 13 / 0.621 / 0.00` (saturated: bbc.co.uk); weekend `24 / 13 /
0.773 / 0.600`. Portfolio new-domain flow stays strong (~69 over 30d, ~16/wk 🟢). The two structural
🟡s are unchanged and not regressions:
- *Top-5 outlet share* trips its bar on the papers streams because it measures only the outlet-class
  slice after hubs/institutional are excluded, and those streams cite almost entirely hub primaries
  (arXiv, Nature). **Science hits 1.00** on a single edition (08-26) with 10 citations — a
  small-n / low-cadence artifact, not lazy sourcing; the registry behind it is rich (see scout).
- *Science unique=8* is the same low-cadence artifact (33 stories/30d over ~4 editions), stable.

The real deficit remains **weekend waiver_rate=0.60** — improved from 0.80 last week and 1.00 the
week before, but still the portfolio's worst and above the 0.50 bar. This week's weekend "Discovery:
met" was again driven by two genuinely-new primaries the reading happened to surface
(anil.recoil.org, a Cambridge OCaml maintainer's technical note; ir.revmed.com, Revolution
Medicines' trial page) — luck of the slate, not the active dormant-domain probe pass rm-1 would
install. See rm-1 (now pending a fourth week). News waiver 0.571 is second-worst and also over bar,
but its discovery footers waive honestly (institutional primaries — bger.ch Incapsula-gated,
admin.ch/BAFU proxy-blocked, WHO shell-only — genuinely unreachable, and the other primaries in play
were cited within 30 days).

Tier distribution (from footers): T1 ~40% portfolio, carried entirely by the papers streams (ai-ml
60–64% T1, weekend 52%). **News runs T1=0** in both read editions — SRF, Le Temps, DW, Al Jazeera
all register T2, so news is structurally a T2 stream, not a miss. T3 leakage = 0 (untiered anchors
exist — z.ai, anil.recoil.org, digitaleconomy.stanford.edu — but these are first-party primaries not
yet tier-graded, not T3 aggregators). Linguistic: FR + DE citations run ~20% portfolio (SRF, Le
Temps, NZZ, DW, Le Monde) — comfortably ≥10%. Geographic spread on news is wide (Pakistan, Russia,
Haiti, DRC, Nepal/Tibet, Syria/Lebanon, France, Algeria, Switzerland).

**B. Aggregator leakage (computed).** `aggregator_leakage: []` — zero HN/Reddit/X/Bluesky citations
across all nine posts. Clean.

**C. Link health — UNMEASURABLE this run.** `linkcheck --check` resolved **6/20**. The six that came
back 200 are all the direct-curl-friendly hosts (aljazeera ×2, srf ×3, letemps). Everything else
(arxiv.org, dw.com, theguardian.com, nzz.ch, arstechnica.com, ir.revmed.com) returned ERR:56 — and
the Sunday scout confirms *why*: the evaluator sandbox's egress is **allowlist-walled at the proxy**
(`CONNECT tunnel failed, response 403` for every non-allowlisted host; only the allowlisted
quantamagazine.org resolved). This is the evaluator's own egress wall, not broken links — the
writers' Coverage footers show `direct_fetch_ratio` ≈ 1.00 with near-zero via-snippet across every
stream, i.e. they reached these same hosts fine through the fetch-proxy bearer the evaluator lacks.
Reporting the dimension unmeasurable per the prompt's egress clause. Claim spot-checks limited to the
resolvable sample (aljazeera Nepal-Tibet-floods and Ukraine-Kyiv items, srf Swiss-drought and
tornado items, letemps Trump-Canada-trade item) — each claim is present and accurately represented;
no fabrications detected in the resolvable sample.

**D. Section vitality (computed).** `empty_sections: []` on every stream. AI/ML twice, Science/Sports
once, Weekend once — all correct cadence. Nothing to flag.

**E. Coverage gap recurrence.** The recurring Gaps cluster is infrastructure-shaped, not
beat-shaped, and identical to prior weeks: admin.ch/BAFU/BFS proxy-blocked (Swiss federal releases →
routed to SRF), bger.ch Incapsula-gated (Federal Court ruling → SRF), bioRxiv/medRxiv details API
empty (weekend biology → three vetted primaries), Hugging Face trending API unreachable (ai-ml
open-weights → lab-primary announcements), api.openalex.org rate-limited (paper affiliations → HTML
author blocks). None recurred ≥3× as a *content* gap — each was routed around honestly. No
structural content hole.

**F. Triangulation rate (computed).** Single-source portfolio **14/112 = 12.5%** (<20% 🟢). Per
stream: news 0.034, weekend 0.083, ai-ml 0.172, sports 0.00, **science 0.50**. Science's 0.50 is the
one per-stream number over the 25% bar — but it is 5/10 on a single 10-citation edition (small-n),
and its single-source items are Nature-portfolio and preprint claims the writer correctly tags
`[single-source]`, i.e. honest labeling of un-triangulable primaries, not lazy sourcing. Not a
structural flag at one edition; worth watching if it persists across two.

**G. Tag discipline.** Counts (health.json): `[preprint]` ai-ml 18, weekend 19, science 7 — every
arXiv/preprint item tagged; news/sports correctly carry none. `[vendor PR]` ai-ml 5, weekend 3 — on
Wan3.0, GLM-5.3-Flash, Granite 4.2, Gemini 3.5 Transcribe, IBM — each demoted below the fold with
independent framing and caveats (see §M). `[disputed]` = 1 (weekend GJ 1132 b — a single-team
archival reanalysis leaning on excluding one contested JWST visit; appropriate). `[via snippet]` = 1
total (news 08-27 France 24 Algeria item) — floor-low, the curl-first chain is working. `[new source]`
this window: Stanford Digital Economy Lab, Pew, Cerebras (investors.cerebras.ai), z.ai,
anil.recoil.org, ir.revmed.com — spot-checked 2: **anil.recoil.org** (a Cambridge CS professor /
OCaml core maintainer's first-party technical note) and **z.ai** (Zhipu AI's own lab blog) — both
genuine primaries, zero junk anchors. Sports used `[new source]` ×3.

**H. Topic balance (weekend, computed).** `ml_items=22, science_items=12, ml_share=0.647` — inside
the [0.35, 0.65] band 🟢, though at the very top edge (a ~65/35 ML lean). Up from last week's 0.556;
the week's arXiv slate was ML-heavy (an unusually strong RL/eval-awareness batch), which the weekend
correctly followed. Still in band, but if it climbs past 0.65 next week it becomes a flag — worth a
glance rather than a patch.

**I. Repetition (computed) + identity integrity.** `reconcile.py`: **0 flagged**, 0
resolved-by-merge, 23 editions checked — no forked ids (the 2026-07-07 Cuba class stays closed).
Repeat rates: news 0.14 (4/29), **weekend 0.79 (23/29)**, others 0. I checked both:
- *News 0.14* is the `[ongoing since]` threads (Ukraine Black Sea ports, Haiti gang attack, DRC
  Ebola, Syria-Israel, Nepal-Tibet floods) each carrying **new dated facts** — the Ebola item
  advancing to WHO's 24 Aug social-distancing recommendation, the floods toll updating 270 → 470+
  across editions. Updates, not re-summaries. Good discipline.
- *Weekend 0.79* is **by design and disclosed**: the 08-29 "Sibling consultation" footer states it
  read the daily News (22–28 Aug), AI/ML (25, 28 Aug) and Science (26 Aug) editions and deliberately
  revisits their marquee results (the ES-vs-GRPO / weak-prefix / test-time-RL trio, eval-awareness,
  TwinKV, the fabricated-evidence agent study) at greater length, *plus* adds fresh finds the dailies
  missed. That is the weekend's stated job — deeper treatment + synthesis. The rate is much higher
  than last week's 0.36 only because this week's weekend overlapped the same ML-paper batch the two
  AI/ML dailies had just run; the treatment is genuinely deeper (full paragraph + "why it matters"
  per paper, four cross-cutting threads), not a re-summary. Intentional overlap, not a defect — but
  the 0.79 is worth noting as the high end of what "deep re-read" should produce.

**J. Cross-week trend.** Vs 2026-08-23: aggregator leakage 0→0, T3 0→0, empty sections 0→0, reconcile
0→0, off-main clean→clean, feedback backlog 0→0. Weekend waiver 0.80→0.60 (nominal improvement, still
luck-driven). Weekend word-mean 3112→6539 (+110% — see §L). Single-source 12%→12.5% (flat). One new
signal: a two-vote reader theme on fiscal-context skepticism (§ reader-feedback). Healthy, stable
trend with the same carried items.

**K. Feed reachability & direct-fetch (computed).** Portfolio direct-fetch ~0.99 (news 0.966, all
others 1.00); every stream meets its range. The curl→proxy chain is doing its job: export.arxiv.org
(68 ok curl), srf.ch (29 curl), letemps.ch (16 curl), aljazeera.com (11 curl), quantamagazine.org (6
curl) resolve direct; arxiv.org (43 proxy), nature.com (16 proxy + 6 curl), dw.com/the-decoder.com
(11 proxy each) recover via proxy. Feeds failing >50% split into:
- *Proxy-recovered* (not material): arxiv.org, the-decoder.com, dw.com, bbc.co.uk,
  theguardian.com, arstechnica.com — curl fails, proxy carries them, citations land.
- *Materially walled* (0 or near-0 ok on both paths): **api.openalex.org (4 fail / 0 ok)** — the
  byline-enrichment path, rate-limited again (→ §N); **admin.ch (5 fail / 0 ok, HTTP 403)** — Swiss
  federal primary, forcing the heat-package and other CH items onto SRF; **france24.com (4 fail / 0
  ok)** — now 0-for-anything (see rm-2 and the registry reach flip); **site.api.espn.com (6 fail / 0
  ok)** — a sports data endpoint. api.openalex.org and admin.ch are the two recurring weekly infra
  walls worth attention; neither is a prompt patch.

Domains-that-shouldn't-be-cited check: no `reach: blocked` / `blocked-paywall` domain appeared
without `[via snippet]`; `never:` is empty; no retired/demoted domain as a primary anchor. Clean.
One reach mismatch surfaced from writer telemetry (not a citation violation): france24.com is
recorded `reach: direct` but had 0 direct/proxy successes two weeks running and 403s in the writer
sandbox — proposed as a registry reach flip (direct → proxy) in registry-2026-08-31.yml.

**L. Output volume (computed).** Word-means: ai-ml 2744 (prev 2686, +2%), news 1206 (prev 1186,
+2%), science 2156 (prev 1632, **+32%**), sports 1640 (prev 2343, −30%), **weekend 6539 (prev 3112,
+110%)**. Two streams cross the +25% flag:
- *Weekend +110%* — 6,539 words is the standout. It is genuine content (40 anchors, four threads,
  ~12 ML papers + 6 science + 3 biology each given full treatment), not padding, and repetition §I
  shows the overlap is deliberate depth. But this is a doubling week-over-week on a stream that was
  praised last week for tightening to 3,112, and 6,539 is near the stream's historical high. It is
  the prime candidate for the output-cap / quiet-day levers (docs/SPIKE-writer-token-levers.md) *if*
  the pattern repeats — one big week on a rich slate is not yet a trend, but flag it for next run's
  cross-week check. Not a patch this week.
- *Science +32%* — 2,156 words on a single 10-citation edition; the growth tracks a denser
  astronomy/chemistry slate, not padding. Small-n; watch, don't patch.

**M. Editorial shape.** All three checks pass cleanly:
- *Vendor-PR-lead share (AI/ML) ≈ 0%.* Both editions **lead with research** — the papers section is
  first, and each edition's through-line is a research anxiety ("our evaluations may not measure what
  we think," "RLVR makes models sharper but narrower"). Every vendor release (Wan3.0, GLM-5.3-Flash,
  Granite 4.2, Gemini Transcribe) is demoted to a "New models" / "Lab blogs" section with independent
  judgment attached ("treat the consistency claims as vendor framing until independent tests land";
  "predictable deployment over headline benchmark wins"; "because it rewrites *what you meant to
  say*, the output can diverge from your literal words"). Well under 40%.
- *Aggregator-shape failures = 0/5.* Sampled leads (news Nepal-Tibet floods, news Federal-Court
  climate ruling, ai-ml fabricated-evidence paper, weekend RL-diversity thread, sports) each cite a
  primary/wire and add framing the source doesn't contain. No rewritten-blurb leads.
- *Personalization misses = 0/5.* Strong where available: the EU packaging burden framed for Swiss
  micro-exporters, the Zurich assisted-suicide ballot ("closer to French-speaking Switzerland's more
  permissive practice"), the SBB profit vs the 500M it says it needs ("reader-taxpayers ultimately
  underwrite"), the ai-ml Thomson-Reuters build-vs-rent item ("a viable enterprise recipe … the moat
  sits in the data"), and the weekend Nvidia–Hugging Face item framed as a European neutrality
  question. No forcing where absent.

**N. Affiliation element (papers streams).** Coverage rate ≈ **19% `(affiliation not listed)`**
portfolio-wide — right at the 20% target 🟡, up from last week's 9%. The unlisted cases cluster in
the ai-ml 08-25 edition (RL-credit, sparse-attention, data-poisoning, eval-awareness — 4/9) and a
few weekend papers (water-splitting, Zilber–Pink). These are overwhelmingly independent /
single-author / small-institution arXiv papers whose HTML author blocks didn't render and whose DOIs
OpenAlex hadn't indexed (429 again) — handled honestly by marking unlisted rather than guessing.
**Halo audit: no prestige bias — the opposite, if anything.** The single most-promoted paper of the
week, the fabricated-evidence agent study (P. Aggarwal, *Independent Researcher*), was the lead
"read three in full" pick in the 08-28 daily *and* "the cleanest, most disquieting result of the
week" in the weekend; the OR-algorithms paper (J. Baek, NYU singleton) was another top-three pick.
Unaffiliated/independent work landed at the *highest* prominence, not scored down. Affiliations are
being recorded for the reader, not used as a selection signal. Good. The 19% is an OpenAlex-egress
artifact, not an editorial regression — the fix is infra (an alternative to rate-limited OpenAlex),
not a prompt patch.

## Prior proposals status

From 2026-08-23:
- **rm-1** (weekend discovery dormancy → `routines/src/weekend.md`): **pending, not applied** — now a
  **fourth** consecutive week. Verified this run: grep of weekend.md finds no dormant-source /
  before-waiving language; the identical block is live in science.md (line 35). Weekend waiver is
  0.60. Carried forward.
- **rm-2** (France 24 → `reader-profile/source-weights.yml` `reduce:`): **pending, not applied** —
  source-weights.yml `reduce:` verified still `[]`. Carried forward, and re-corroborated this week
  (france24 0-for-fetches). Second week.
- **rm-3** (France 24 learned-preference line → `reader-profile.md`): **applied and verified** — the
  auto-applied 2026-08-23 line is present in reader-profile.md "Learned preferences" (lines 57–62).
- **registry-2026-08-23** (`applied: false`, never stamped): esv.ch and uci.ch candidate→probation —
  both **still `status: candidate`** in sources/registry.yml (verified lines 3080, 3092), not
  applied. Carried again. **Positive verification:** last week's two *scout candidates* (skao.int,
  aip.de) **did land** in sources/registry.yml (lines 3770, 3782), and candidates.jsonl was cleared
  to zero before this run — so the candidates.jsonl → registry scout path is working end-to-end, even
  while the lifecycle-transition proposals await Rafael's apply step.

## Source scout (Sunday duty)

**Stream picked: science** — lowest `new_domains` (5), no tie-break needed (top5_share also worst at
1.00). Budget used: **9 probe fetches.** All non-allowlisted probes returned the proxy's `CONNECT
tunnel failed, response 403` — the evaluator sandbox's egress is allowlist-walled this window (only
the pre-allowlisted quantamagazine.org resolved, 200), the same wall behind the 6/20 linkcheck. This
routine holds no fetch-proxy bearer by design, so direct verification isn't possible; candidates are
appended with `reach: proxy-needed` for the writers to vet at first citation.

Finding: science's registry is **not thin** — it already holds ethz.ch, epfl.ch, psi.ch, empa.ch,
eso.org, noirlab.edu, public.nrao.edu, home.cern, skao.int, aip.de, pnas.org, science.org,
elifesciences.org, feeds.aps.org, scnat.ch, unil.ch, slf.ch and more; the `new_domains=5` deficit is
dormancy, not absence (same diagnosis three weeks running, reinforced by last week's candidates
landing). This week's chemistry- and biomedicine-heavy science/weekend slate (sunlight→ammonia,
water-splitting, the RAS drug, shingles CV outcomes, clonal haematopoiesis) surfaced two genuine
primary publishers **absent** from the registry, appended to `sources/candidates.jsonl` (both
`reach: proxy-needed`):
- **chemrxiv.org** — Cambridge Open Engage chemistry preprint server (primary, non-aggregating;
  fills the chemistry-preprint gap the science stream currently routes through Nature).
- **cell.com** — Cell Press (genuine primary biomedical journal family for the biology beat).

Re-probe of stale reach entries: **inconclusive from the evaluator** — the five direct-curl probes
(eso.org, noirlab.edu, france24.com, esv.ch, uci.ch) all hit the same proxy allowlist 403, which is
an artifact of the evaluator's egress, not evidence about the domains. **One reach flip is proposed
anyway, from writer telemetry:** france24.com `reach: direct → proxy` (0 direct/proxy successes two
weeks running; 403s logged in the writer sandbox). No other flips.

## Patch proposals (for human review)

Two carried, plus one auto-applied reader-profile line and one registry reach flip (both in the
machine-readable files). The pipeline is otherwise healthy; I'm not manufacturing patches.

### Patch 1 (rm-1) — Weekend discovery dormancy (CARRIED, fourth week un-applied)
**Target prompt:** Weekend (`routines/src/weekend.md`)
**Section affected:** Sourcing / Discovery footer block
**Issue:** Weekend's 30-day waiver_rate is 0.60 (portfolio worst, over the 0.50 bar). Its "Discovery:
met" continues to be luck — new primaries the reading happens to surface — not an active
dormant-probe pass. The exact reactivation fix already lives in science.md (line 35, landed
2026-08-02); weekend never received it.
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
dormant domains, finds nothing, and waives with a more specific reason.

### Patch 2 (rm-2) — Demote France 24 in source weights (CARRIED, second week)
**Target file:** `reader-profile/source-weights.yml` (human-gated — propose only)
**Section affected:** `reduce:` list
**Issue:** Carried from 2026-08-23 (reasoned reader downvote naming France 24). Re-corroborated this
week: france24.com failed **100%** of fetch attempts (4 fail / 0 ok on any path; 403 in the writer
sandbox), and the 08-27 Algeria-wildfires item rested on a France 24 `[via snippet]` with no stronger
corroboration.
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
>                                   #   sources"; led/single-sourced when Le Monde/AFP existed;
>                                   #   0-for-fetches two weeks running
> ```

**Why this helps:** the writer prefers a stronger wire/primary (Le Monde, Reuters, AFP, Al Jazeera)
when one exists, and stops leading or single-sourcing on France 24.
**Risk:** low — `reduce:` is a soft penalty, not a hard `never:` drop; France 24 stays available when
it is the only source for a significant story.

_(Also filed, not counted against the 5-patch cap: the **france24.com reach flip** direct→proxy in
registry-2026-08-31.yml — the mechanical reach field, distinct from rm-2's editorial demotion.)_

## Reader-feedback → profile proposals

The window carried **12 feedback events**: 10 bare taps (`reason: ""`) and **2 reasoned**, with
`unconsumed_total: 0` (bridge fold current). Aggregate tally is positive — ai-ml 4 👍, news 4 👍 /
4 👎. Per the completeness rule, every reasoned event gets a disposition (both are edition-level —
`sid: null` — but the reasons pin the target story):

- **2026-08-27-news, 👎, _"You should have made the connection with the 17 million cut from a few
  weeks ago. Nothing new for the climate I'm afraid, just money for farmers"_**: **APPLIED** (rm-3).
  Targets the Federal Council 70M forest/farm heat package (st-f0d68f223570), which mixes 17.5M/yr
  climate-adaptation restoration with ~54M in farmer liquidity credits. The reader wants the
  spending framed against the earlier cut it merely restores, and the farmer-credit vs
  climate-money distinction drawn out — not the announcement's own framing relayed flat.
- **2026-08-26-news, 👎, _"Non issue peddled by anti-oversight crowd…"_**: **APPLIED** (rm-3, same
  theme). Targets the EU packaging-regulation burden item (st-2a7fec8db33b), which led with the
  aggrieved luthier and Le Temps's "aberrant et disproportionné" anti-regulation framing over a
  ~€260/yr cost. The reader reads this as amplifying a marginal anti-regulation grievance as a story.

These two are on **distinct stories, same News section, same theme** — the News stream relaying an
announcement's or an aggrieved party's framing without supplying the countervailing fiscal/regulatory
context — so they cross the ≥2-distinct-stories noise bar. It is also a natural extension of the
existing 2026-07-26 line (unreliable-narrator / add-the-missing-context) from US-administration
self-characterisations to domestic and EU fiscal/regulatory framing. **Auto-applied** under the
2026-07-10 bounded grant: one dated line appended at the END of reader-profile.md "Learned
preferences" (append-only, no other section touched), stamped `applied: true, applied_by: evaluator`
in proposals/reader-model-2026-08-31.json as rm-3.

The 10 bare taps (news 4 👍 net / ai-ml 4 👍) carry no theme text and don't cross the noise bar. No
`source-weights.yml` change proposed from feedback this week beyond the carried France 24 rm-2.

## Machine-readable proposals

Written: `proposals/reader-model-2026-08-31.json` (rm-1 carried `applied:false`; rm-2 carried
`applied:false`; rm-3 auto-applied `applied:true, applied_by:evaluator`) and
`proposals/registry-2026-08-31.yml` (`applied:false` — france24 reach flip direct→proxy; esv.ch +
uci.ch candidate→probation carried; chemrxiv.org + cell.com scout candidates noted).

## Cross-week trend

Stable and healthy (see §J): every zero-defect dimension held from last week, single-source flat,
direct-fetch ~1.00, editorial-shape checks all green. Two things moved worth watching next run:
weekend word-count doubled (3,112 → 6,539, §L) and weekend ml_share climbed to the top of its band
(0.556 → 0.647, §H) — both content-driven this week, neither yet a trend. The only new editorial
signal is the two-vote fiscal-context theme, now acted on. No new regressions.

## Open questions for human review

1. **rm-1 is pending a fourth week.** It's a proven, low-risk fix already live in science.md, and
   weekend's 0.60 waiver is the portfolio's only structural amber. Worth applying to weekend.md
   before next Saturday?
2. **rm-2 (France 24) is now double-evidenced** — reader reason *and* a 100% fetch-fail rate two
   weeks running. The two-line source-weights edit (plus the mechanical reach flip) closes it.
3. **This run fired Monday, not Sunday.** The 2026-08-30 Sunday slot produced no evaluator post and
   no ledger file, and off_main is clean (not an off-main stranding). Worth checking the Evaluator
   trigger's cron/last-fire — a silently skipped Sunday is the failure mode the self-delivery guard
   watches for, and this is the first missed slot in the recent record.
4. **api.openalex.org remains fully walled (0 ok, 429 again)** — the byline-enrichment path and the
   sole cause of the 19% affiliation-not-listed rate (§N). admin.ch (403) is the second recurring
   infra wall (Swiss federal primaries → SRF). Neither is a prompt patch; flagging for infra — an
   OpenAlex alternative (Crossref? Semantic Scholar?) would pull affiliation coverage back under 10%.
5. **Reader-brief proposals:** `proposals/*.jsonl` reader-suggestion directory does not exist — no
   reader topic proposals to surface this week.

_No brief-proposals directory, no unconsumed feedback, no forked ids, no off-main diversion — the
mechanical plane is quiet. The three things worth a human's five minutes: apply rm-1 (four weeks
pending) and the France 24 rm-2 the reader asked for, and check why the Sunday 08-30 evaluator slot
didn't fire._
