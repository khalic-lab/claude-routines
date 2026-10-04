---
layout: single
title: "Weekly Pipeline Review — 2026-10-04"
date: 2026-10-04T11:52:21+02:00
categories: [evaluator]
published: true
---

# Weekly Brief Pipeline Review — 2026-10-04

_Coverage: briefs from 2026-09-28 to 2026-10-04._
_Files read: 6 news, 2 AI/ML (expect ~2), 1 science (expect ~1), 1 sports (expect ~1), 1 weekend, prior review found (2026-09-27, 7 days old)._

The pipeline is in good health. Every writer stream fired on cadence, all eleven briefs carry a Discovery footer with honest waivers, aggregator leakage is zero, identity reconciliation is clean, and the four proposals from last week all applied and verifiably landed. The one materially actionable finding is **reach drift**: thirteen registry domains still recorded `reach: direct` have gone proxy-only in practice, and this run proposes flipping all of them (§K). The Sunday scout picked science again — its deficit is structural (a narrow primary-journal universe behind an institutional egress wall, not a candidate shortage) — and added the two missing peer-reviewed chemistry publishers to the bench. No reader-profile or prompt patches this week: the only reasoned signal would come from feedback, and all three votes in the window were bare taps.

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains 30d (worst stream vs its tier) | science 5 (ai-ml 29) | ≥30 news/ai-ml · ≥10 weekly | 🔴 |
| New domains this window (portfolio) | 7 `[new source]` tags; 30d counts all ≥ tier | ≥2–3/wk (≥10/mo) | 🟢 |
| Top-5 outlet share (worst of news/ai-ml) | news 0.695 (ai-ml 0.544) | ≤0.50 (→0.35); weekly report-only | 🔴 |
| Waiver rate (worst stream) | weekend 1.00 (science 0.75) | ≤50% | 🔴 |
| Discovery footer present (every brief) | 11/11 | 100% | 🟢 |
| T1 citation %                   | 34% (36/106; +12 untiered primaries ≈ 45%) | ≥40% | 🟡 |
| T3 leakage count                | 0 | 0 | 🟢 |
| Non-English citation % (portfolio) | ~19% | ≥10% | 🟢 |
| Link sample pass rate           | 5/20 — **unmeasurable** (egress wall) | ≥90% | ⚪ |
| Fabrication count               | 0 | 0 | 🟢 |
| Single-source rate (portfolio)  | 13.2% (14/106) | <20% | 🟢 |
| Empty section instances         | 0 | <5 | 🟢 |
| Reading-surface flags (§D, surface.py) | 1 (lede-fallback WARN) | 0 | 🟡 |
| Repeat rate (worst stream)      | weekend 0.47 (by construction) | judge | 🟡 |
| Direct-fetch ratio (portfolio)  | 1.00 (via-snippet 0 everywhere) | ≥0.35 | 🟢 |
| Feeds with >50% fail rate       | 4 high-volume (+ low-attempt tail) | 0 | 🟡 |
| Citations on `reach: blocked` domains w/o `[via snippet]` | 0 | 0 | 🟢 |
| Unconsumed feedback backlog     | 0 | 0 | 🟢 |
| Vendor-PR-lead share (AI/ML, §M) | ~0% of leads | ≤40% | 🟢 |
| Aggregator-shape failures (§M, of 5) | 0 | 0–1 | 🟢 |
| Personalization misses (§M, of 5) | 0 | 0–1 | 🟢 |

## A–N: Detailed findings

### A. Source diversity & discovery
Read from `source-health.json` (30-day windows, segmented by stream):

- **news** — unique 46, new 39, top5 0.695, waiver 0.467, saturated none. Diversity breadth is excellent (46 domains, 39 new in 30d); the amber is **top-5 share 0.695**, well above the 0.50 "now" bar. The concentration is the daily reliance on a small set of reliably-reachable primaries (SRF, Le Temps, Al Jazeera, DW, The Guardian). This is the same signal the prior-week outlet-rotation patch (p1, applied 2026-09-25) targets; it is only ~9 days old, so I am **holding** rather than re-patching — see Prior proposals and Cross-week.
- **ai-ml** — unique 29, new 24, top5 0.544, waiver 0.222, saturated none. Unique domains are **one short of the ≥30 bar** (🟡) and top-5 share is a hair over 0.50; both are close and trending the right way (24 new domains in 30d is healthy). No action.
- **science** — unique 5, new 3, top5 1.00, waiver 0.75. The portfolio's worst stream on every axis, and the scout target. new_domains 3 exactly meets the weekly-tier floor but is the lowest ratio of any stream. This is **structural, not a sourcing-prompt defect**: the science writer this window probed a wide set (ESO, NOIRLab, NASA, Fermilab, CERN, APS Physics, OpenAlex, Crossref) and most 403/404/ERR:56'd or carried nothing dated to the window (see §K and the brief's own Gaps). The registry's science roster is otherwise comprehensive; the binding constraint is reachability and the narrow universe of dated weekly primaries, not candidate supply.
- **sports** — unique 13, new 8, top5 0.636 (report-only), waiver 0.25, `bbc.co.uk` saturated. Healthy for a weekly stream; the single edition (2026-09-28) leaned on BBC, hence the one saturation flag — not structural on one data point.
- **weekend** — unique 16, new 12, top5 0.796 (report-only), **waiver 1.00**. The 100% waiver rate is the eye-catcher but is honest: this week's two strongest finds (SynthIDBio, Clef) both resolved to already-registered hubs (nature.com, huggingface.co) rather than a new primary, and the writer said so plainly in the Discovery footer. A weekly deep-read over a handful of curated papers will frequently have nothing genuinely-new to anchor; the waiver is doing its job rather than hiding a gap.

**Tier distribution:** T1 36 / T2 58 / untiered 12 of 106 (T1% = 34%). Below the ≥40% target, but the 12 untiered citations are overwhelmingly genuine first-party institutional primaries pending registry tier-classification — IEA, GLAMOS, FINMA, the Federal Chancellery vote-data platform, FIA WEC, CASP, AMD newsroom — all entered this window as `[new source]`. Counting those as the primaries they are puts the effective primary share around 45%. The honest read is amber-not-red: no low-trust-tier citations appeared (**T3 leakage 0**); T1 looks soft only because this week's fresh institutional primaries haven't been tiered yet.

**Linguistic/geographic:** EN/FR/DE across news and weekend; ai-ml and science are English-only by nature (arXiv/Nature). Portfolio non-English share ≈19% (Swiss/French/German primaries — SRF, Le Temps, NZZ, Le Monde, admin.ch, parlament.ch, finma.ch, auto.swiss, voteinfo), comfortably above the ≥10% floor.

### B. Aggregator leakage
`health.json → briefs.aggregator_leakage`: **empty.** No citations of HN, Reddit, X, Mastodon, Bluesky, etc. across the week. 🟢

### C. Link health — unmeasurable this run (egress wall), no fabrication
`linkcheck --check` resolved **5/20** of the deterministic sample and **2/5** of the Weekend recap links. This is **not a quality regression** — it is the evaluator's own egress. Every failure was `ERR:56` (connection reset), and every one landed on a proxy-reachable host (arxiv.org, nature.com, dw.com, lemonde.fr, theguardian.com, huggingface.co, arstechnica.com, the-decoder.com, admin.ch, euronews.com, casp.ac). The links that *did* resolve 200 are exactly the curl-direct hosts on the sandbox allowlist (aljazeera.com, letemps.ch, srf.ch, quantamagazine.org). The evaluator holds no fetch-proxy bearer by design, so proxy-only URLs are unreachable from here — the writers fetched these same URLs successfully via proxy (their footers show `ok via proxy` for dw.com, lemonde.fr, nature.com, etc.). I spot-checked the claims behind the four resolvable Weekend/news links (Parmelin resignation → SRF; Swiss EV >⅓ share → Le Temps; Sept abstimmung overview → SRF; 4th-dimension podcast → Quanta) and each claim is present in the source. **Recap fabrication: 0** — the two recap ERR:56 hits (dw.com ×1, lemonde.fr) are demonstrably proxy-reachable (writer footer: dw.com 2 ok via proxy, lemonde.fr 1 ok via proxy), not missing pages. Dimension reported ⚪ unmeasurable; this is the recurring, known limitation (same as 2026-09-20/27), not an egress *regression* — the curl-direct hosts still resolve.

### D. Section vitality + reading surface
`health.json` reports **zero empty sections** across all eleven briefs. 🟢 AI/ML, Science, Sports and Weekend appearing once/twice is correct cadence, not a gap.

`surface.py`: window [2026-09-20, 2026-10-04], **0 parity misses, 0 overdue desks, 1 WARN.** The WARN is story `st-5b5761c99f32` on 2026-10-03-weekend (the Cloudflare Clef release item): "no body parsed, card shows its lede." Reading the post, the Clef entry is a `🚀 Models & datasets` bullet in the `<a id>…**bold headline.**` shape — a long multi-sentence paragraph after the bold lede. The feed builder parsed the bold lede but split off no additional body prose, so the card shows the one-line lede ("Cloudflare open-sources Clef, a 27B decision model") rather than a fuller snippet. This is a **minor parser/format edge**, not a writer contract break: the writer followed the standard release-bullet shape used elsewhere, and the story still reached a card. It is the feed builder's paragraph-splitting on that bullet shape, not a routine-prompt issue — noted under Open questions for the builder, not a prompt patch.

### E. Coverage gap recurrence
Gaps footers cluster on two recurring, already-understood themes: **JavaScript-rendered official pages** (parlament.ch vote records, auto.swiss releases, bger.ch judgments — the news writer correctly falls back to SRF/Le Temps and says so) and **institutional-science egress** (ESO, CERN, APS Physics, Crossref/OpenAlex failing). Neither is new; both are reachability, not sourcing-discipline. Nothing crossed the ≥3-recurrence structural bar that isn't already tracked in the registry/reach layer.

### F. Triangulation rate
Portfolio single-source **13.2%** (14/106). Per stream: news 16.7%, ai-ml 15.2%, science 0%, sports 14.3%, weekend 5.3% — all under the 25% per-stream ceiling and the <20% portfolio target. The ai-ml 09-29 edition carried five single-source items (CASP report, two Ars-sourced and two Decoder-sourced industry/regulation items), each correctly `[single-source]`-tagged; fast-moving industry/legal items single-sourced to a reliable secondary are inherent to that section, not a discipline slip. 🟢

### G. Tag discipline
Counts from `health.json` (not recounted): ai-ml — preprint 19, vendor PR 7, new source 2, single-source 5; news — new source 4, official PR 1, single-source 7; science — preprint 3; sports — new source 1, single-source 1, unconfirmed 1; weekend — preprint 7, single-source 1. Spot-checks:
- **`[preprint]` on arXiv:** sampled 5 (2609.40221, 2609.38879, 2609.31121, 2610.01035, 2609.38003) — all genuine arXiv preprints, correctly tagged. ✓
- **`[vendor PR]`:** sampled Gemini 4 Argon, Flux 3, Microsoft speech, Anthropic Sonnet 5.5, OpenAI safety-cases — all are vendor announcements, correctly tagged, and each pairs the tag with an explicit "treat as vendor-reported until replicated" framing. ✓
- **`[new source]`:** candidates.jsonl was empty at run start despite 7 `[new source]` citations this week; the tagged domains (iea.org, glamos.ch, finma.ch, ogd-static.voteinfo-app.ch, newsroom.amd.com, casp.ac, fiawec.com) are all unambiguously genuine first-party primaries — **zero junk anchors.** The empty candidates.jsonl is flagged under Open questions (the `[new source]` → auto-enter path may not be writing).
- **`[via snippet]`:** 0 across every stream — via-snippet has been driven to zero by the curl-first chain. ✓ (The healthy direction; see §K.)

### H. Topic balance (weekend)
`health.json → briefs.weekend_balance`: ml_items 8, science_items 8, **ml_share 0.50.** Dead-centre of the 50/50 target (flag band is outside [0.35, 0.65]). The writer even called the split out in the intro ("four papers each side of the 📄/🔭 line"). 🟢

### I. Repetition detection
`health.json → streams`: news repeat_rate 0.095 (4), **weekend 0.474 (9)**, all others 0. `reconcile.py --root .`: **0 flagged, 0 resolved-by-merge, 24 editions checked** — no id forks (the 2026-07-07 Cuba defect class stays clean). The weekend 0.47 repeat rate is **by construction and legitimate**: the Weekend deep-read deliberately revisits the week's strongest daily items (Monitor Jailbreaking, Fold2Reason, PhantomEnvironments, Ataraxos) and takes them deeper than the dailies did — the sibling-consultation footer states this explicitly, and the treatments carry genuinely new synthesis (the three cross-cutting threads) rather than re-summary. Not a defect; it is the format working. 🟡 only as a "watch the ratio" note.

### J. Cross-week trend
Against 2026-09-27: aggregator citations hold at 0; via-snippet holds at 0; empty sections hold at 0; reconcile clean both weeks. Reach-drift cleanup is **continuing and widening** — 09-20 flipped 4 domains, 09-27 flipped 2 more, and this run surfaces 13 (the backlog of long-direct-recorded domains curl no longer succeeds on). News top5-share is the one metric to watch: the outlet-rotation patch landed 09-25 but the window's news still concentrates on SRF/Le Temps/Al Jazeera/DW/Guardian — give it another cycle before judging the patch.

### K. Feed reachability & direct-fetch rate
**Per-stream direct-fetch ratio** (non-via-snippet): **1.00 for every stream** — no citation this week was sourced to a snippet rather than a fetched page. All above their floors. 🟢

**Per-feed** (`health.json → briefs.feeds`): the method picture is clear and healthy. Curl carries the direct hosts well — export.arxiv.org (58 ok curl), srf.ch (31), letemps.ch (20), aljazeera.com (15), nature.com (10), quantamagazine.org (9) — while the proxy carries everything else. High-volume feeds over 50% fail: **api.crossref.org** (19 fail / 13 ok-proxy, 59%), **openai.com** (9 fail / 2 ok-proxy, 82%), **glamos.ch** (9 fail / 5 ok-proxy, 64%), **feeds.apnews.com** (6/6, 100%). A long tail of institutional-science hosts failed every (low-count) attempt — eso.org, home.cern, physics.aps.org, link.aps.org, api.openalex.org, mfa.gov.et, mnd.gov.tw — which is the science egress wall, not a feed-URL error. None resolved curl-AND-proxy-failing on a feed a stream depends on except within science, where it's structural.

**Reach drift (computed):** `briefs.reach_drift.flips` lists **13 domains** recorded `reach: direct` with 0 curl successes, ≥1 failure, and ≥3 proxy successes this window: arxiv.org, arstechnica.com, lemonde.fr, parlament.ch, finma.ch, glamos.ch, theguardian.com, blog.google, huggingface.co, newsroom.amd.com, nzz.ch, rfi.fr, simonwillison.net. **All 13 are copied into `proposals/registry-2026-10-04.yml`** as `field: reach, from: direct, to: proxy` patches with their counts as evidence. One judgment caveat recorded there: the flip is for the abstract host **arxiv.org only** — the RSS/API host `export.arxiv.org` is a separate registry entry and is correctly `direct` (58 ok-curl), so it must not be flipped. No reverse flips (curl newly succeeding on a `proxy` domain) were visible in `briefs.feeds` this week.

**Domains-that-shouldn't-be-cited:** scanned citations against `reach: blocked`/`blocked-paywall`, `never:`, and retired/demoted status — **0 violations.** via-snippet is 0 everywhere, so no blocked domain appeared outside a snippet; no `never:` domain (france24.com, siliconangle.com are `reduce:`, not `never:`) appeared; no retired/demoted domain anchored a story.

### L. Output volume
Word-count means vs previous week: news 1,168 (prev 1,195, −2%), ai-ml 2,932 (prev 3,002, −2%), science 1,109 (prev 1,442, −23%), weekend 3,631 (prev 5,747, −37%), **sports 1,386 (prev 1,030, +35%)**. Only sports grew >25%. On a single-edition stream a 35% swing is noise from one week's story mix (7 citations across 5 sections vs the prior week's lighter card), not a drift signal — and sports is neither repetitive (repeat_rate 0) nor long in absolute terms. No action. Weekend's 37% *drop* is the welcome direction (the length-discipline patch from two weeks ago holding).

### M. Editorial shape
- **Vendor-PR-lead share (AI/ML):** ~0% of leads. Both editions led with an independent research result (09-29: the skeptical reasoning-audit batch / Monitor Jailbreaking; 10-02: the academic Stratego result). Every vendor item is tagged `[vendor PR]` and framed critically ("treat the numbers as the vendor's own until independent evals land"; "the feature to verify once weights ship"). Vendor framing never *leads* an edition. 🟢
- **Aggregator-shape (5 leads across streams):** Parmelin → SRF primary + reshuffle framing; Monitor Jailbreaking → arXiv primary + safety synthesis; Paris-emissions heatwave → GRL primary + CH-relevance framing; Bilaterals III → SRF + "vote of no confidence" analysis; Swiss EV share → Le Temps + China-reshaping framing. **0 failures** — each cites a primary and adds judgment the source doesn't contain.
- **Personalization (5 samples):** Bilaterals III (CH stakes), Swiss EV/BYD (CH market), BFL "few frontier image labs outside the US" (European builder angle), Paris-emissions "the region the reader lives in" (CH climate), Ukraine-reconstruction Swiss-firm tender (CH industry). **0 misses** — CH/builder framing is present where it plausibly exists, and not forced where absent. 🟢

### N. Affiliation element (papers streams)
- **Coverage rate:** of ~32 paper bylines across ai-ml (19), science (5), weekend (8), only **2 read `(affiliation not listed)`** — both on 2026-09-29-ai-ml (2609.31093 PISA, 2609.30950 hybrid-quant), plausibly thin HTML author blocks. ≈6% unlisted, well under the <20% target (and far below the 70% of the old API chain). 🟢 Spot-checked 3 bylines (Ataraxos → CMU/NYU/Stanford; zeta-moment → EPFL/Courant; tau-prion → MRC LMB/Tokyo Met) — all carry institutions through to the prose.
- **Halo audit:** no prestige bias visible — in fact the counter-evidence is strong. The 09-29 edition's #1-ranked paper is Monitor Jailbreaking from *Meridian Cambridge* (a small org, single author), ranked above big-lab work; the Weekend's landmark is an academic Stratego result explicitly praised for being done "not to a hyperscaler's budget but to an academic group for a few thousand dollars." Unaffiliated/independent papers are not being systematically parked at importance 1. 🟢

## Prior proposals status

From `proposals/*-2026-09-27.*` — **all four applied and verified landed:**
- **rm-1** (reader-profile.md — contested-label discipline, "Die Linke is not far-left"): auto-applied by the evaluator; **verified** present at `reader-profile.md` line 80. ✓ applied and verified.
- **p1** (routines/_shared/newsroom-ethos.md — impartial-labeling rule): stamped `applied_by: rafael-apply-pass` 2026-10-01; **verified** present at `routines/_shared/newsroom-ethos.md` line 11. ✓ applied and verified.
- **registry dw.com → proxy** and **euronews.com → proxy**: stamped applied 2026-10-01; **verified** — both now read `reach: proxy` in `sources/registry.yml`. ✓ applied and verified.
- **registry royalsociety.org / pubs.aip.org candidate adds**: stamped applied as no-ops (already present as registry candidates via scout sync); confirmed still present. ✓ (no-op, as recorded.)

Nothing from 09-27 is left pending.

## Source scout (Sunday duty)

**Stream picked: science** — the worst-deficit stream by the §A tie-break (new_domains 3 ÷ weekly target 3 = ratio 1.00, the lowest of any stream; unique_domains 5 vs the ≥10 target; top5_share 1.00; waiver_rate 0.75). This is the third consecutive week science is the scout target, and the diagnosis is unchanged: the deficit is **structural** (a narrow universe of dated weekly primaries behind an institutional egress wall), not a candidate shortage.

**Candidates appended** to `sources/candidates.jsonl` (2, both `reach: proxy-needed`): **pubs.acs.org** (American Chemical Society — JACS, Nano Letters, J. Phys. Chem.) and **pubs.rsc.org** (Royal Society of Chemistry — Chemical Science [gold OA], Chem. Commun., Energy & Environmental Science). These fill a genuine gap: the registry covers physics (APS/AIP/IOP), biology (Cell/eLife/PLOS/bioRxiv), multidisciplinary (Nature/Science/PNAS), geoscience (AGU) and chemistry *preprints* (chemrxiv) — but has **no peer-reviewed chemistry primary**. Both are promoted into `proposals/registry-2026-10-04.yml` as candidate adds for a probation cycle.

**Re-probe results:** 5 fetches used (pubs.acs.org, pubs.rsc.org, eso.org, home.cern, physics.aps.org) — **all returned code 000** ("CONNECT tunnel failed"), the evaluator's allowlist-walled egress, the same signature as 2026-09-20/27. So the reach evidence this run rests entirely on **writer-side fetch telemetry** (`briefs.reach_drift`), with the 13 flips above; the evaluator probes are only a spot-check and confirm nothing new. **Fetches used: 5 of the ≤20 budget.**

## Patch proposals (for human review)

**No routine-prompt patches this week.** The pipeline is healthy on A–N, and the one materially-actionable finding — reach drift on 13 domains — is a registry change, not a prompt change (it lives in `proposals/registry-2026-10-04.yml`). The two ambers that aren't structural:

- **news top-5 share 0.695** is the only quality metric clearly over target that isn't reachability-bound, but the news outlet-rotation patch (prior-week p1) applied only 2026-09-25 — re-patching the same thing nine days later is premature. **Held for one more cycle**; if top5-share hasn't eased by 2026-10-11, a reinforcing patch is warranted.
- **science diversity** is structural and already addressed by the scout's registry proposals; no prompt wording would move it.

Proposing nothing here is the honest call, per the mission's "if everything is healthy, propose nothing."

## Reader-feedback → profile proposals

**Completeness — every window feedback event, with disposition:**
- news 2026-09-30, `vote: 1`, `reason: ""` — **deferred** (bare tap, no reason; below the proposal bar and outside the auto-apply grant).
- ai-ml 2026-10-02, `vote: 1`, `reason: ""` — **deferred** (bare tap).
- news 2026-10-02, `vote: 1`, `reason: ""` — **deferred** (bare tap).

All three window events are **bare taps with `reason: ""`** (three 👍, zero 👎, zero retractions; matches `health.json → feedback.by_stream` news up 2 / ai-ml up 1). There are **no reasoned events** this window, so nothing clears the noise filter (≥2 signals on distinct stories) and the bounded auto-apply grant does not fire. `feedback.unconsumed_total` is 0 — the bridge fold is current. **No reader-profile or source-weights proposals this week.** (The three 👍 are a mild positive signal on the news and ai-ml streams, consistent with the healthy editorial-shape readings above, but carry no actionable theme.)

## Machine-readable proposals

- `proposals/registry-2026-10-04.yml` — 13 reach flips (direct→proxy, all from `briefs.reach_drift`) + 2 chemistry candidate adds (pubs.acs.org, pubs.rsc.org). `applied: false`.
- `proposals/reader-model-2026-10-04.json` — empty `proposals` array with a continuity note (no reasoned feedback; reach drift handled in the registry file; prior-week verification recorded). `applied: false` n/a (nothing to stamp).

## Cross-week trend

Zero-holds across the board: aggregator citations 0, via-snippet 0, empty sections 0, reconcile clean. Reach-drift remediation is the live program — 4 flips (09-20) → 2 (09-27) → 13 (this run) — clearing a backlog of registry entries where curl quietly stopped working. Weekend word-count continues to fall (5,747 → 3,631) as the length-discipline patch holds. The one metric to watch is news top5-share against the recently-landed rotation patch.

## Open questions for human review

1. **`sources/candidates.jsonl` is empty despite 7 `[new source]` citations this week.** The architecture note says a `[new source]` tag "auto-enters the domain in `sources/candidates.jsonl` as a candidate," yet the file was 0 bytes at run start while iea.org, glamos.ch, finma.ch, voteinfo, newsroom.amd.com, casp.ac and fiawec.com were all tagged `[new source]`. Either the auto-enter path isn't wired/running, or entries are consumed/relocated elsewhere. Worth confirming the publish-time source lint is actually writing candidates — otherwise the candidate bench never fills from writer discovery, only from the Sunday scout. (My scout appends for pubs.acs.org/pubs.rsc.org are now the only two lines in the file.)
2. **Feed-builder lede-fallback on release bullets (surface.py WARN).** The Cloudflare Clef item (2026-10-03-weekend, `st-5b5761c99f32`) parsed to a lede-only card. The writer used the standard `<a id>…**bold.**` release-bullet shape; the builder split no body prose from the long paragraph after the bold lede. A builder-side fix to the paragraph parser (not a prompt change) would let these release items show a fuller snippet. Low severity — the card still renders.
3. **Science egress wall (standing).** As every prior science review notes: ESO, CERN, APS Physics, Crossref and OpenAlex are not reliably reachable even via proxy, which caps science diversity regardless of how many candidates the registry holds. The ACS/RSC adds broaden the chemistry bench, but the binding constraint remains reachability. If science diversity matters, the lever is a reachability probe/alternative-feed program, not more candidates.
