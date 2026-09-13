---
layout: single
title: "Weekly Pipeline Review — 2026-09-13"
date: 2026-09-13T11:46:55+02:00
categories: [evaluator]
published: true
---

# Weekly Brief Pipeline Review — 2026-09-13

_Coverage: briefs from 2026-09-07 to 2026-09-13._
_Files read: 6 news, 2 AI/ML (expect ~2), 1 science (expect ~1), 1 sports (expect ~1), 1 weekend, prior review found (2026-09-06)._

Cadence this week was textbook: News fired all six days (07–12, no same-day Sunday, correct), AI/ML on Tuesday and Friday, Science on Wednesday, Sports on Monday, Weekend on Saturday. No cold streams, no missed fires, no off-main diversion. The pipeline's mechanical spine is sound; the editorial story this week is a single, well-evidenced thread that ties three dimensions together — reader feedback, source-tier mix, and one broken feed — and points at the same fix.

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains 30d (worst stream, source-health) | science 10 | ≥30 | 🔴 |
| New domains this window (portfolio, source-health) | news 30 / ai-ml 23 / weekend 15 / sports 11 / science 7 | ≥2–3/wk (≥10/mo) | 🟢 |
| Top-5 outlet share (worst stream, source-health) | science 1.00 | ≤0.50 (→0.35) | 🔴 |
| Waiver rate (worst stream, source-health) | weekend 0.60 | ≤50% | 🔴 |
| Discovery footer present (every brief) | 11/11 | 100% | 🟢 |
| T1 citation % | ~39% (news 9.8%, sports 0%) | ≥40% | 🟡 |
| T3 leakage count | 0 | 0 | 🟢 |
| Non-English citation % (portfolio) | ~15% | ≥10% | 🟢 |
| Link sample pass rate | 8/20 (40%) | ≥90% | ⚪ |
| Fabrication count | 0 | 0 | 🟢 |
| Single-source rate (portfolio) | 15.4% (news 22%) | <20% | 🟢 |
| Empty section instances | 0 | <5 | 🟢 |
| Repeat rate (worst stream, health.json) | weekend 0.53 | judge | 🟡 |
| Direct-fetch ratio (portfolio) | ≥0.80 all streams | ≥0.35 | 🟢 |
| Feeds with >50% fail rate | ~15 (material: admin.ch, iaea.org) | 0 | 🔴 |
| Citations on `reach: blocked` domains without [via snippet] | 0 | 0 | 🟢 |
| Unconsumed feedback backlog (health.json) | 0 | 0 | 🟢 |
| Vendor-PR-lead share (AI/ML, §M) | ~30% | ≤40% | 🟢 |
| Aggregator-shape failures (§M, of 5) | 2 | 0–1 | 🟡 |
| Personalization misses (§M, of 5) | 0 | 0–1 | 🟢 |

## A–N: Detailed findings

**A. Source diversity & discovery.** The 30-day source-health numbers show two streams pulling their weight and three that are structurally thin *because they fire weekly*. News (194 stories/30d, 40 unique domains, 30 new) and AI/ML (139 stories, 28 unique, 23 new) are healthy on volume. Science (30 stories, 10 unique, top5_share 1.00, nature.com saturated) and sports (25 stories, 12 unique, bbc.co.uk saturated) sit below the ≥30-unique target, but that is arithmetic: one edition a week over 30 days is ~4 editions and ~20 citations, and the outlet-class top-5 share is computed over a tiny denominator. This week's *actual* science edition was well-diversified across five distinct primaries (arXiv/OpenAI, ApJ/NOIRLab, AJ/NASA, Lasker Foundation, NEJM/AstraZeneca) — the 30-day top5=1.00 is a small-sample artifact of nature.com being the only recurring outlet-class domain, not a live editorial monoculture. The real, addressable point is that science leans on nature.com as its default journal anchor; the scout below adds three absent primary publishers to widen it. Tier mix: T3 = 0% (policy-clean). T1 ≈ 39% portfolio, dragged down by news (9.8%) and sports (0%) — see the tier discussion under the feedback finding, because it is not independent of it.

**B. Aggregator leakage.** `health.json → aggregator_leakage` is empty. Zero citations to HN/Reddit/X/Bluesky/Mastodon across all 11 briefs. Clean.

**C. Link health — ⚪ unmeasurable from the evaluator sandbox this run.** `linkcheck.py --check` resolved 8/20 (40%), but every one of the 12 failures is `ERR:56` (connection reset), not a 4xx/5xx, and every failing host is a proxy-needed domain: lemonde.fr, dw.com, arxiv.org/abs, the-decoder.com, vd.ch, cuimc.columbia.edu, terrytao.wordpress.com. These are exactly the domains the *writers* fetched successfully this week — every stream reports `direct_fetch_ratio` ≥ 0.80 and `via_snippet` ≈ 0, and the footers log these hosts as `ok via proxy`. The evaluator holds no fetch-proxy bearer by design and its egress is allowlist-walled (a direct probe of pnas.org, journals.aps.org, europarl.europa.eu etc. all returned code 000 / CONNECT-blocked). So the 40% is the evaluator's own ceiling, not link rot — same condition flagged in the 2026-09-06 review. The eight that *did* resolve (srf.ch, letemps.ch, aljazeera.com, quantamagazine.org) I spot-checked; the Quanta Millennium-Prize page confirms the Navier–Stokes/blowup/OpenAI claims carried in the Science and Weekend briefs verbatim. **Fabrications detected: 0** (sample egress-constrained). This dimension will stay unmeasurable until the evaluator gets a read-only bearer or the sample is drawn only from allowlisted hosts — worth a mechanical fix, not a prompt patch.

**D. Section vitality.** `empty_sections` is empty for every stream. No dead sections this week. 🟢

**E. Coverage-gap recurrence.** The Gaps footers cluster on one recurring theme: **client-rendered official sites the sandbox can't parse.** OpenAI's `openai.com/index/*` pages (Science, AI/ML both note it), admin.ch federal-council feeds (News 09-12: "all URLs tried returned empty"), formula1.com/fia.com JS shells (Sports), Swiss-publisher HTML (Weekend). This is the same structural gap three weeks running and it is the root of the feedback finding below.

**F. Triangulation.** Portfolio single-source rate 15.4% (16/104). News is highest at 22% (9/41) — over the 20% portfolio line but under the 25% per-stream bar, so acceptable. Weekend 8.3%, science and sports 0%, ai-ml 16.7%. 🟢

**G. Tag discipline.** Counts read clean: `[preprint]` 18 (ai-ml) / 13 (weekend), all on arXiv items (spot-checked five — genuine preprints). `[vendor PR]` 4 (ai-ml) / 1 (weekend), correctly on DeepSeek, OpenAI Agents API, GPT-Live-1, Mistral. `[disputed]` used well (the Navier–Stokes priority dispute, the Mistral lead-investor ambiguity, the Zelensky "near-miss" characterisation). `[new source]` this window: 10 across streams (cuimc.columbia.edu, science.nasa.gov, laskerfoundation.org, ulam.ai, riksdagen.se, turkishminute.com among them) — the two I spot-checked (ulam.ai anchoring the ErdosBench result, riksdagen.se for the Swedish election) are genuine primaries, not junk anchors. `[via snippet]` count is 1, portfolio-wide (the OpenAI Navier–Stokes item in Science, correctly tagged because openai.com is unfetchable). Via-snippet rates are essentially zero — the curl-first chain is working. 🟢

**H. Topic balance (weekend).** `weekend_balance` = 20 ML items / 8 science items, **ml_share 0.714 — outside the [0.35, 0.65] band.** 🔴 The writer flagged it honestly in the intro ("Bias this week runs heavily toward RL and agents, which is where the genuinely new work clustered") and the science side was genuinely thinner (arXiv's RL/agents surge vs a quiet fundamental-science week). This is honest reflection, not lazy filling — but it is the target the 2026-07-10 spike set explicitly, and it is now worth watching for recurrence rather than force-correcting a single honest week. See Patch 4.

**I. Repetition.** `reconcile.py`: **0 flagged, 0 resolved-by-merge, 23 editions checked** — identity integrity clean, no forked ids. Repeat rates: ai-ml 0.03, news 0.17, science 0, sports 0.25 (1 story), **weekend 0.53 (10/19)** 🟡. The weekend number looks alarming but is by-design: the Weekend deep-read deliberately revisits the week's AI/ML daily items (PCC, T1, TRACE, FlexComp, dropout, quantization, molecular-déjà-vu, the uncensored-weights audit) in fuller depth with cross-paper synthesis — its "Sibling consultation" footer documents exactly this, and its "Things I deliberately cut" footer shows real `[ongoing]` discipline (GLM-5.3, the RISE/OPD cluster dropped as already-covered with no new fact). Each revisit adds substantial new analysis, not a re-summary. Judged acceptable for the stream's role.

**J. Cross-week trend.** Vs 2026-09-06: continuity clean (see below), off-main empty both weeks, aggregator leakage 0 both weeks, via-snippet ≈0 both weeks. Weekend waiver improved 0.80 → 0.60 (and the dormant-source patch that targets it just landed 09-12 — should move further next week). News single-source steady. No regressions.

**K. Feed reachability & direct-fetch.** Direct-fetch ratios are excellent: news 1.0, ai-ml 1.0, science 0.80, sports 1.0, weekend 1.0 — all well above their ranges. The curl-first chain carries the reliable feeds directly (srf.ch 27 ok-curl, export.arxiv.org 37, aljazeera.com 17, letemps.ch 12, quantamagazine.org 9, nature.com 6) and the proxy picks up the JS-heavy/blocked ones (lemonde.fr, dw.com, arxiv.org/abs, the-decoder.com — all ~50%-curl-fail but proxy-carried, which is the expected split, not a flag). **The one material failure is admin.ch: 13 attempts, 13 failures (403), zero successes on either curl *or* proxy** — plus news.admin.ch 1/1 fail and bfs.admin.ch 1/1 fail. iaea.org (8/8 fail) and centcom.mil (5/5 fail) are the other total-fail feeds but they carry little of the week's load. The admin.ch wall is the one that hurt: it is the Swiss Federal Council's own release channel, and its unreachability is the direct mechanical cause of the reader feedback below. **Domains-that-shouldn't-be-cited check: clean** — openai.com (effectively blocked) appears only `[via snippet]`; no `never:` or `retired` domain surfaced as a primary anchor.

**L. Output volume.** No stream grew >25% week-over-week; every stream held or shrank: news 1146 (was 1312), ai-ml 2632 (was 2572, +2%), science 1624 (was 1600), sports 1017 (was 1640), weekend 5429 (was 6725). No output-cap concern. 🟢

**M. Editorial shape.** *Vendor-PR-lead (AI/ML):* ~30% — OpenAI's Agents API and GPT-Live-1 items do lead with the company's own announcement, and DeepSeek/Mistral/MiniCPM are release items, but all carry `[vendor PR]` and independent caveats ("treat the head-to-head coding claim as the vendor's own figure"; the Mistral lead-investor ambiguity flagged `[disputed]`). Under the 40% line. 🟢 *Aggregator-shape (all streams, 5 leads):* **2 failures** 🟡 — both the 2026-09-10 news items that drew reader downvotes (the Bilaterals III AFET committee vote and the "Lex On" Federal Council recommendation) lead on Le Temps (quality secondary) where the official primary — the European Parliament vote record / the Federal Council communiqué — existed and was the thing the reader wanted. The other three leads sampled add genuine framing. *Personalization:* 0 misses — the Swiss/CH angle is present and unforced throughout (Lausanne student-poverty survey, Vaud unemployment, Bilaterals III framed for people who live and work in CH, the UBS AI-hiring item framed for a Swiss software reader). 🟢

**N. Affiliation element (papers streams).** Coverage rate is strong: across ~35 papers this week, ~5 read "(affiliation not listed)" (~14%, under the 20% target). Every one is explained in a Gaps footer as an arXiv author-block that rendered emails but no institution text (the no-guess-from-email rule) — honest omission, not a skipped Step C field. The 09-08 AI/ML edition ran higher at 3/10, all documented. *Halo audit:* no prestige bias detectable — the independent-author TRACE paper (R. Sun et al.) is given full weight and shown overtaking Claude Opus 5; the "(affiliation not listed)" generalised-semi-Clifford paper is treated as a substantive negative result "with practical bite," not demoted. Unaffiliated/independent work is not systematically landing at lower importance than lab work.

## Prior proposals status

Last week's proposals (`proposals/reader-model-2026-09-06.json`, `proposals/registry-2026-09-06.yml`) were all stamped `applied: true` (dated 2026-09-12) and **all four verifiably landed**:
- **rm-1** (weekend.md dormant-source-activation block, carried 5 weeks) — **applied and verified**: `routines/src/weekend.md` now contains the "dormant"/"before waiving" language (4 matches). This is the patch that should keep pulling the weekend waiver rate down.
- **rm-2** (france24.com → source-weights `reduce:`) — **applied and verified**: present in `reader-profile/source-weights.yml` with the full rationale.
- **sw-1** (siliconangle.com → source-weights `reduce:`) — **applied and verified**: present in the same file.
- **registry** (france24.com reach `direct` → `proxy`; esv.ch + uci.ch `candidate` → `probation`) — **applied and verified**: `sources/registry.yml` shows `france24.com: reach: proxy`; esv.ch and uci.ch carry the probation note (with the honest correction that their `proxy-needed` claim was wrong — both answer 200 direct). The apply step's self-correction here is exactly the loop working as intended.

Nothing pending, nothing stamped-but-not-landed.

## Source scout (Sunday duty)

**Stream picked: Science** — the clear worst-deficit stream: lowest new_domains (7), highest top5_share (1.00), nature.com saturated, unique_domains 10. **Fetches used: 12** (all probes; budget ≤20).

The evaluator sandbox is egress allowlist-walled again this week — every non-allowlisted host (pnas.org, journals.aps.org, cell.com, science.org, phys.org, europarl.europa.eu) returned code 000 / CONNECT-block — so no candidate could be *directly* vetted here; all are appended with `reach: proxy-needed` for the writers to confirm at first citation. Checking the registry first, the obvious primaries (pnas.org, journals.aps.org, cell.com, science.org, phys.org) and the Swiss institutions (ethz.ch, epfl.ch, psi.ch, empa.ch, unibe.ch, mpg.de) are **already registered** — so science's thinness is not a missing-registry problem, it is over-reliance on nature.com as the default anchor. Four genuine primary science publishers are still absent, and I appended them to `sources/candidates.jsonl`:
- **iop.org** — IOP Publishing / IOPscience (Environmental Research Letters open-access, New Journal of Physics)
- **pubs.aip.org** — AIP Publishing (Applied Physics Letters, J. Chem. Phys.)
- **royalsocietypublishing.org** — Royal Society (Proceedings A/B, Biology Letters)
- **cnrs.fr** — CNRS press (francophone/EU science primary, CH-adjacent)

No stale-reach re-probes were possible (egress wall) — none proposed from evaluator evidence, consistent with last week.

## Patch proposals (for human review)

### Patch 1 — News: extend the primary-document rule to votes and government positions
**Target prompt:** News (`routines/src/news.md`, §9 "Primary document rule")
**Section affected:** Sourcing / tiers
**Issue:** The two 2026-09-10 news items that drew reasoned reader downvotes — a European Parliament committee *vote* and a Federal Council *recommendation* — both led on Le Temps rather than the official primary. The existing primary-document rule enumerates "court ruling, bill, law, regulator's decision, official report, legal opinion" but not a *parliamentary/committee vote* or a *government's stated position/recommendation*, so neither downvoted story was squarely covered by it. News T1 share is 9.8% this week; this is the compliance gap.

**Proposed change:**

> **Before:**
> ```
> 9. **Primary document rule.** When the story IS a document — a court ruling, a bill or law,
> a regulator's decision, an official report, a published legal opinion — go find the document
> itself (the court's, parliament's, regulator's, ministry's or party's own site) and cite it
> alongside the outlet, before settling for outlet-only sourcing.
> ```
>
> **After:**
> ```
> 9. **Primary document rule.** When the story IS a document OR an official act — a court ruling,
> a bill or law, a regulator's decision, an official report, a published legal opinion, a
> parliamentary or committee VOTE (cite the roll-call / result page or the body's own press
> release), or a government's stated position, recommendation or motion (cite the ministry's or
> Federal Council's own communiqué) — go find the primary itself (the court's, parliament's,
> regulator's, ministry's or party's own site) and cite it alongside the outlet, before settling
> for outlet-only sourcing. If the official primary is unreachable this run, say so in Gaps and
> name where it lives, rather than letting the press recap stand as the anchor.
> ```

**Why this helps:** names the exact two story-shapes the reader flagged, closing the enumeration gap that let press coverage lead.
**Risk:** low — reinforces an existing rule; worst case the writer spends a few extra fetches chasing a primary that turns out unreachable (in which case the Gaps clause covers it).

### Patch 2 — Registry: mark admin.ch reach honestly and add europarl.europa.eu
**Target prompt:** registry (`sources/registry.yml`, via `proposals/registry-2026-09-13.yml`)
**Section affected:** reach fields / EU-institution primaries
**Issue:** admin.ch failed 13/13 this week (403 on both curl and proxy) — the Federal Council's own channel is effectively unreachable, which is *why* the Lex On story fell back to Le Temps. And europarl.europa.eu (the primary for the AFET Bilaterals III vote) is absent from the registry entirely, so the writer had no registered path to it.
**Proposed change:** flip admin.ch (and news.admin.ch) reach to reflect the 403 wall so the writer stops burning fetches on a dead path and reaches for an alternative sooner; add europarl.europa.eu as an EU-institution primary (`reach: proxy-needed`, writers confirm with bearer). Machine-readable in the registry proposal file.
**Why this helps:** removes the mechanical blocker behind the feedback finding; a registered EU-parliament primary gives Patch 1 something to cite.
**Risk:** the admin.ch 403 may be a transient egress/WAF issue rather than a permanent block — the reach flip is reversible and the writers re-probe with the bearer, so worst case is one wasted probation cycle.

### Patch 3 — Science: rotate the journal anchor off nature.com
**Target prompt:** Science (`routines/src/science.md`, sourcing/preflight section)
**Section affected:** Physics/chemistry/math primary sourcing
**Issue:** Science top5_share is 1.00 with nature.com saturated over 30 days; the stream defaults to Nature as its journal anchor even though APS/IOP/AIP/Royal Society/Cell/PNAS are all registered (and four more primaries were just scouted).
**Proposed change:** add a one-line steer in the sourcing block: *"When Nature already carries a story, check whether the underlying result also has a primary home at another registered publisher (journals.aps.org, iop.org, pubs.aip.org, cell.com, pnas.org, royalsocietypublishing.org, science.org) and anchor there to spread the outlet base — nature.com is saturated."*
**Why this helps:** directly attacks the top5=1.00 / nature-saturation number with anchors the writer already has access to.
**Risk:** low — Nature remains available; this only nudges away from over-reliance, and for genuinely Nature-only results the writer still cites Nature.

### Patch 4 — Weekend: make the 50/50 balance target explicit in the paper-selection step
**Target prompt:** Weekend (`routines/src/weekend.md`, paper-selection section)
**Section affected:** ML vs fundamental-science paper balance
**Issue:** ml_share 0.714 this week, outside the [0.35, 0.65] band set 2026-07-10. Honest this week (ML genuinely surged), but the target isn't stated in the prompt, so nothing pulls the writer back when the arXiv ML firehose dominates.
**Proposed change:** add to the paper-selection guidance: *"Aim for roughly 50/50 ML vs (fundamental science + biology) across the paper sections, ±15 points. When the ML pool is deep, actively widen the fundamental-science/biology net (physics, chemistry, math, life-sciences primaries) before adding a fourth or fifth ML paper; if the split still lands outside 35–65%, say so and why in the intro (as this week did)."*
**Why this helps:** encodes the long-standing target so it self-corrects, while preserving the honest-imbalance escape hatch.
**Risk:** could push toward force-filling a thin science week — mitigated by the explicit "say so and why" clause that legitimises an honest imbalance.

## Reader-feedback → profile proposals

**Completeness — every reasoned event in the window gets a disposition.** Nine `ev:"feedback"` events landed with `ts` in [2026-09-07, 2026-09-13]; `health.json` tallies (news 4👎/2👍/1 retraction, ai-ml 2👍, unconsumed_total 0) match exactly. Seven are bare votes (`reason: ""`) and are excluded from proposal-making by rule:
- 2026-09-08-ai-ml 👍 (st-bc03703a7af7, Mistral raise) — bare, **deferred** (no reason).
- 2026-09-09-news 👍 (st-1aaa16a501ff) — bare, **deferred**.
- 2026-09-10-news 👎 (st-80b1b8331f25) — bare, but see the reasoned event on the same story below.
- 2026-09-10-news 👎 (st-fa5a401a3aa7) — bare, ditto.
- 2026-09-10-news 👍 then vote=0 (st-cb89576854d9, Moldova/Zelensky drone) — an up-vote **retracted** the same minute; net zero, **deferred**.
- 2026-09-11-ai-ml 👍 (st-1d424f5d642a, DeepSeek V4.1-Flash) — bare, **deferred**.

Two are **reasoned**, and they are the signal:
- 2026-09-10-news 👎 (st-80b1b8331f25, Bilaterals III AFET committee vote): _"You should have used the main source, the vote, a press release, a primary source."_
- 2026-09-10-news 👎 (st-fa5a401a3aa7, Lex On / Federal Council recommendation): _"Again, press instead of official communication…"_

**Noise filter — theme meets the ≥2-distinct-stories bar.** Two reasoned downvotes, on two *distinct* stories, same edition, identical theme: cite the official primary (the vote record, the government communiqué) rather than press coverage of it. This is a real, repeated signal — and it corroborates the §M aggregator-shape failures and the 2026-09-06 SiliconANGLE/BoE feedback. **Disposition: applied** (rm-1 below, auto-applied to reader-profile.md; also reinforced by prompt Patch 1).

**Auto-applied** (bounded grant — appended, append-only, to reader-profile.md "Learned preferences"):

> **Before:** _(end of Learned preferences, last line 2026-08-31)_
>
> **After:** _(appended)_
> ```
> - 2026-09-13: for institutional / government / parliamentary stories, anchor on the official
>   primary — the vote record, the ministry / Federal-Council communiqué, the press release —
>   not press coverage of it (2× reasoned 👎 on distinct 2026-09-10 news stories: Bilaterals III
>   AFET committee vote, "You should have used the main source, the vote, a press release, a
>   primary source"; Lex On Federal Council recommendation, "Again, press instead of official
>   communication"). Where the official source is unreachable this run (admin.ch 403 this window),
>   say so in Gaps rather than leading on the secondary. Sharpens the standing primary-over-
>   aggregator line for the specific vote/recommendation case.
> ```

No `source-weights.yml` change proposed this week — the theme is a sourcing-discipline correction (favour the primary), not a bad-outlet demotion; Le Temps is a quality secondary that should stay available, just not lead an official-act story.

## Machine-readable proposals

Written to `proposals/reader-model-2026-09-13.json` (rm-1 auto-applied and stamped; patches p1/p3/p4 `applied: false`) and `proposals/registry-2026-09-13.yml` (admin.ch reach + europarl.europa.eu, `applied: false`).

## Cross-week trend

Healthy and stable vs 2026-09-06: continuity intact, off-main clean, aggregator leakage 0, via-snippet ≈0, direct-fetch ratios uniformly high, no output-volume creep, identity reconcile clean. Weekend waiver improved (0.80 → 0.60) with the dormant-source patch now landed — expect further improvement next week. The one persistent structural item across weeks is client-rendered official sites (admin.ch, openai.com, formula1.com) the sandbox can't parse; this week that surfaced as a concrete editorial cost (the Swiss-federal sourcing downvotes), which is why Patch 2 escalates it.

## Open questions for human review

1. **Evaluator link-check is unmeasurable without a read-only bearer.** Dimension C has now degraded to the evaluator's egress ceiling two weeks running (8/20, all failures `ERR:56` on proxy-needed hosts the writers reach fine). Options: give the evaluator a read-only fetch-proxy bearer for link-checking only, or restrict `linkcheck.py`'s sample to allowlisted-reachable hosts so the pass rate means something. Not a prompt patch — a mechanical decision for you.
2. **admin.ch 403 — transient or a real block?** 13/13 fail on both curl and proxy this week. If it's a WAF/egress regression it's worth fixing centrally; if permanent, the Swiss-federal desk needs a different primary path (parlament.ch/curia vote pages, cantonal portals). Patch 2 assumes the latter conservatively.
3. **No reader `proposals/*.jsonl` directory exists yet** — no brief-proposals to surface this week.
