---
layout: single
title: "Weekly Pipeline Review — 2026-09-27"
date: 2026-09-27T11:48:55+02:00
categories: [evaluator]
published: true
---

# Weekly Brief Pipeline Review — 2026-09-27

_Coverage: briefs from 2026-09-21 to 2026-09-27._
_Files read: 6 news, 2 AI/ML (expect ~2), 1 science (expect ~1), 1 sports (expect ~1), 1 weekend, prior review found (`_posts/2026-09-20-evaluator.md`)._

The pipeline is healthy. All eleven expected (slug, date) pairs landed on the correct cadence, both mechanical scripts ran clean, `reconcile.py` reported **0 flagged** across 24 editions, `surface.py` reported **0 flags**, and there is no aggregator leakage, no empty section, no fabrication, and no unconsumed-feedback backlog. Last week's two prompt patches (news outlet rotation, weekend length discipline) and four registry reach flips all **applied and verified landed**. Three things want a human's eye, none of them a brief-quality regression: a **reasoned reader downvote on a mislabelled party** (the one genuine editorial finding, actioned below), the **same benign `origin/main` force-rewrite** the off-main guard false-positives on every forced pull, and continued **registry `reach` drift** in two more `direct`-recorded domains. Details below.

## Health summary

| Metric | Value | Target | Status |
|---|---|---|---|
| Unique domains 30d (worst stream: science) | 10 | ≥30 | 🔴 (structural) |
| New domains this window (portfolio, `[new source]` anchored) | 8 | ≥2–3/wk | 🟢 |
| Top-5 outlet share (worst meaningful: news) | 0.703 | ≤0.50 | 🟡 (p1 just applied) |
| Waiver rate (worst stream: weekend) | 0.80 | ≤50% | 🔴 (egress-driven) |
| Discovery footer present (every brief) | 11/11 | 100% | 🟢 |
| T1 citation % (portfolio) | 53/116 = 45.7% | ≥40% | 🟢 |
| T3 leakage count | 0 | 0 | 🟢 |
| Non-English citation % (portfolio) | well ≥10% | ≥10% | 🟢 |
| Link sample pass rate | 8/20 = 40% | ≥90% | ⚪ egress-degraded |
| Fabrication count | 0 | 0 | 🟢 |
| Single-source rate (portfolio) | ~6.9% | <20% | 🟢 |
| Empty section instances | 0 | <5 | 🟢 |
| Reading-surface flags (§D, surface.py) | 0 | 0 | 🟢 |
| Repeat rate (worst stream: weekend) | 0.276 | judge | 🟡 by-design |
| Direct-fetch ratio (portfolio, citation) | 1.00 | ≥0.35 | 🟢 |
| Feeds with >50% fail rate | ~20 (egress-blocked institutionals) | 0 | 🔴 egress |
| Citations on `reach: blocked` domains w/o `[via snippet]` | 0 | 0 | 🟢 |
| Unconsumed feedback backlog | 0 | 0 | 🟢 |
| Vendor-PR-lead share (AI/ML, §M) | ~15% (2/13) | ≤40% | 🟢 |
| Aggregator-shape failures (§M, of 5) | 0 | 0–1 | 🟢 |
| Personalization misses (§M, of 5) | 0 | 0–1 | 🟢 |

## A–N: Detailed findings

**A. Source diversity & discovery.** New-domain flow is healthy: eight `[new source]` domains anchored this week (news: vbs.admin.ch, vd.ch; ai-ml: transluce.org, bfl.ai + two more; sports: fclugano.com, cyclingnews.com), above the 2–3/week target. `candidates.jsonl` reads empty because the `[new source]` → candidate → registry lifecycle is promoting them into `sources/registry.yml` as it should. Portfolio **T1 share is 45.7%** (53 of 116 citations, from the footers), over the ≥40% bar and up slightly from last week's 43.1% — carried by the paper-heavy streams (science 100% T1, AI/ML ~65%, weekend 49%) against news at ~2% T1, because the registry tiers the broadsheets news relies on (SRF, Le Monde, Al Jazeera, DW, Le Temps) as **T2**, so news T1 is structurally low, not a quality miss. **T3 = 0%**; the 7 untiered citations are the new/candidate domains, not low-quality anchors. **Non-English** is healthy portfolio-wide (news/weekend/sports lean heavily FR/DE/ES). The real deficits are concentration and waiver rate, both structural and both discussed under §K/§E: **news top5_share 0.703** (p1 rotation guidance applied only 2026-09-25, so only the 09-26 edition reflects it — far too few editions to move a 30-day metric yet); **weekend waiver_rate 0.80 and science 0.75**, both driven by the institutional-primary egress wall, not by discovery not being attempted (the waivers are honest and specific — see §E).

**B. Aggregator leakage.** `health.json → briefs.aggregator_leakage` is empty. **Zero** citations of HN/Reddit/X/Mastodon/Bluesky. 🟢

**C. Link health.** `linkcheck --check` resolved **8/20** (window 09-21→09-27, 136 links) and **2/6** on the Weekend recap. This is **egress-degraded, not a brief defect**, and the split is diagnostic: every 200 is a direct-curl domain the evaluator's egress allowlist tunnels (srf.ch, aljazeera.com, letemps.ch all resolved), and every failure is `ERR:56` — a *connection reset*, not a 404 — on a proxy-only domain the *evaluator* session cannot reach (arxiv.org, dw.com, edition.cnn.com, noemamag.com, the-decoder.com, huggingface.co, snb.ch, watson.ch, euronews.com). The briefs' own `direct_fetch_ratio` is 1.00 across every stream with **0 via-snippet citations**, so the sources fetched fine at compose time (the writers hold the fetch-proxy bearer; this session does not, by design). I claim-checked the resolvable links (the Al Jazeera Belgium–Rwanda item, the SRF Xi–Trump summit piece, the SRF UBS-regulation Ständerat vote) and each cited claim is present. Because the recap "failures" are `ERR:56` connection resets on proxy-only domains rather than 404s, **none is a fabrication candidate** — a recap 404 would be, and there were none. **Fabrications detected: 0.** Reporting the pass-rate dimension **unmeasurable this run**: the checker's egress, not the briefs, drove the failures.

**D. Section vitality + reading surface.** `empty_sections` empty for every stream. `surface.py`: **0 flags** — 0 parity misses, 0 lede-fallback WARNs, 0 OVERDUE desks across 24 editions. Two desks kept an honest thin week (the weekend "Apple Silicon / local inference" desk, which said so explicitly and cited only real llama.cpp merges; the weekend "Data science / applied ML" desk, "a genuinely thin week … one substantive piece plus a tool note rather than a padded list") — the omit-don't-fill call, not a dead section. 🟢

**E. Coverage gap recurrence.** The recurring structural gap is the same as prior weeks: **institutional/government primaries unreachable from the sandbox**. Science 09-23 (EPFL only carried out-of-scope AI items, PSI/MPG feeds unreachable, OpenAlex off-allowlist); news 09-23/09-24/09-25 (admin.ch class); weekend (bioRxiv details API returned empty bodies, epoch.ai RSS 404). In every case the writer waived discovery honestly and fell back to the peer-reviewed primary or a quality wire. This is the binding constraint on diversity (§K), not a sourcing-discipline failure.

**F. Triangulation rate.** Portfolio single-source rate **~6.9%** (8 of 116; ai-ml 18.8%, weekend 2.9%, news 2.7%, science/sports 0%). Under the 20% portfolio bar and the 25% per-stream bar. The ai-ml single-source items (White House/AISI, Sanders bill, Sakana) are all honestly `[single-source]`-tagged with the Politico/senate.gov originals noted as unreachable in Gaps. 🟢

**G. Tag discipline.** Counts (health.json): ai-ml `[preprint]` 18, `[vendor PR]` 7, `[new source]` 4; weekend `[preprint]` 14, `[disputed]` 2; science `[preprint]` 2; news/sports `[new source]` 2 each. Spot-checks: `[preprint]` correctly on every arXiv item; `[vendor PR]` correctly marks the Anthropic enzyme post, the Xiaomi/BFL/Yandex model cards and OpenAI items; `[disputed]` used appropriately (the weekend JWST z≈15 ψDM interpretation, explicitly "tagged for the ψDM interpretation, not the JWST data"). **`[new source]` integrity:** `candidates.jsonl` was empty at fire time (all promoted to registry), so I spot-checked the anchored new-source domains directly — fclugano.com (club match centre), cyclingnews.com (cycling specialist), transluce.org (AI-oversight lab), bfl.ai (Black Forest Labs' own page): all genuine primaries, **no junk anchors**. `[via snippet]` fired **0 times** all week across every stream — the curl-first chain is at the floor, not rising. No tag drift. 🟢

**H. Topic balance (weekend).** `weekend_balance`: ml_items 14, science_items 14, **ml_share 0.500** — dead centre of the [0.35, 0.65] band and a further improvement on last week's 0.611. The 50/50 target (made explicit in the prompt via the applied p2 wording) is holding. 🟢

**I. Repetition detection.** `reconcile.py`: **0 flagged**, no id forks, 24 editions checked. Repeat rates: weekend 0.276 (8 repeats), sports 0.20 (1), news 0.162 (6), ai-ml/science 0. The **weekend** rate is by-design — the brief revisits the week's daily AI/ML papers "in more depth," which its intro and sibling-consultation footer state explicitly (it deepens, it does not re-summarise). The **news** repeats carry `[ongoing since]` discipline (e.g. the German-election thread `[ongoing since 2026-09-20]`, the Man City title-race `[ongoing since 2026-09-06]`). Neither is a defect. 🟢

**J. Cross-week trend.** vs 2026-09-20: T1 share up (43.1% → 45.7%); weekend balance improved again (0.611 → 0.500); weekend words down (7,217 → 5,747, the p2 patch working, see §L); via-snippet held at 0; T3 held at 0; aggregator leakage held at 0; direct-fetch held at 1.00. The registry reach-drift cleanup continued (four domains flipped last week, two more surfaced this week). No regression on any dimension. The one new editorial signal is the reader downvote (§M / reader-feedback section).

**K. Feed reachability & direct-fetch.** Per-stream `direct_fetch_ratio` is **1.00 everywhere** (0 via-snippet citations portfolio-wide) — when a curl fetch fails the writer falls to the proxy or drops the source rather than citing a snippet, so no reachability failure reaches the reader. **Method comparison:** the reliable feeds work over plain curl (srf.ch 39 ok-curl, export.arxiv.org 28, letemps.ch 17, aljazeera.com 14, nature.com 10, quantamagazine.org 3); a second tier is **proxy-only** (arxiv.org HTML 56, news.un.org 24, dw.com 18, the-decoder.com 14, nature.com adds 17 via proxy); a third tier — the institutional/government primaries — is a **wall where both curl and proxy mostly fail** (admin.ch 10 fail / 2 proxy, ohchr.org 8/2, api.github.com 10/4, bundestag.de 4/0, consilium.europa.eu 4/0, psi.ch 4/0, uci.ch 4/0). That third tier is the §E gap and the diversity ceiling. **~20 feeds exceed a 50% fail rate**, essentially all that egress-blocked institutional class plus a couple of APIs (openalex, github) — not feeds silently degrading brief quality.

The actionable finding, as last week, is **registry reach drift**: two more domains recorded `reach: direct` had **zero** curl successes this window and succeeded only via the proxy — **dw.com** (0 curl / 18 proxy / 15 fail; its RSS host rss.dw.com 0 / 12 / 8) and **euronews.com** (0 / 5 / 5). `direct` is wrong for both; each should be `proxy` (registry proposal below, on writer telemetry — the evaluator egress could not confirm, 000 on every non-allowlisted host). I checked **nature.com** and it is **correctly** `direct` (10 ok-curl this window, plus a 303 from the evaluator itself), so it is deliberately *not* flipped. **Domains-that-shouldn't-be-cited:** no `reach: blocked`/`blocked-paywall` domain appeared as a primary anchor, no `never:` domain appeared, and with 0 via-snippet citations there is nothing to reconcile against the `[via snippet]`-only rule. 🟢

**L. Output volume.** Weekend fell to **5,747 words (−20% w/w** from 7,217) — the p2 length-discipline patch, applied 09-25, is doing exactly its job (the intro even flags "this edition leans mid-length"). Sports −28% (1,030 vs 1,427, small young-stream base). News −2%, science flat. The one stream that **grew** is **AI/ML: 3,002 words mean vs 1,977 last week (+52%)** — the largest w/w growth in the portfolio. But it is **not** the both-long-and-repetitive profile the token-levers SPIKE flags: ai-ml repeat_rate is **0** and the density is genuinely high-signal (the 09-25 edition ran 16 substantive items — eight arXiv papers with real method summaries, plus the OpenAI-agents/Transluce industry story). This is depth, not padding, so no patch — but it is worth watching (Open questions §3): if ai-ml stays >25% up next week with flat story count, it becomes the next candidate for a weekend-style soft length steer.

**M. Editorial shape.** **Vendor-PR-lead share (AI/ML):** ~15% (roughly 2 of ~13 news-shaped items). Every vendor item this week added independent framing the source omits — the Anthropic enzyme post is explicitly framed as "an unreliable narrator … the company is both the tool vendor and the party grading the discovery," with the CRISPR-researcher counterpoint that the hard part "has not been done"; the MiMo/AliceAI/FLUX model cards all carry "vendor self-reported … independent replication pending." Well under 40%. **Aggregator-shape (5 leads sampled — reward-hacking paper, Transluce/OpenAI-agents, German elections, Xi–Trump summit, Nestlé/UBS):** 0 failures; each cites a primary and adds judgment the source doesn't (the reward-hacking lead ties the lab result to the real-world OpenAI-agents story; the OpenAI-agents lead cross-checks Transluce against the NYT and OpenAI's own confirmation). **Personalization (5 sampled):** 0 misses — CH/builder angles present where they exist (the 09-27 Swiss neutrality/food-security vote, SNB rate hold, Geneva-led NIRPS retrograde-orbit result, Lugano and Reusser in sports) and not forced where absent. 🟢 — but see the labeling finding below, which is an *impartiality* miss, not an aggregator-shape or personalization one.

**The one editorial finding — a party mislabel.** News 09-21 (`st-6299f47c2ec9`, the German state elections) called "the **far-left** Die Linke (The Left)" — but the cited Euronews source headline says only "The Left triumphs." The writer *added* a contested ideological label in the brief's own voice, asymmetric to the consensus "far-right AfD" in the same sentence, and repeated it in the 09-26 weekend Week-in-headlines recap. A reader caught it with an emphatic reasoned 👎 ("JFC DUDE Die Linke is NOT FAR LEFT"). This is the impartiality miss the standing 2026-07-19/07-26 reader-profile lines already guard for actors' *self*-characterisations, now surfacing for the *writer's own* party labels. Actioned in the reader-feedback section (auto-applied learned-preference line) and as the one prompt patch (labeling rule in the shared ethos partial).

**N. Affiliation element.** **Coverage rate:** across the week's paper bylines (science 7, ai-ml ~16, weekend ~14) roughly 2 read "(affiliation not listed)" — the superposition-linearity paper (ai-ml 09-25) and the Davenport-constant paper (weekend) — ~5% or under, well below the 20% target, and both are honestly flagged (weekend Gaps: "Davenport's HTML author block did not expose an institution"). Science ran **0%** unlisted. I spot-checked three bylines against the material and the institutions reached the prose. **Halo audit:** the two `(affiliation not listed)` papers were *not* down-weighted — the Davenport result (a single-author disproof of a decades-old conjecture) got a full weekend entry with substantial treatment, and superposition-linearity a full ai-ml entry, sitting at the same importance band as the big-lab papers. No prestige bias. 🟢

## Prior proposals status

From `proposals/*-2026-09-20.*`:
- **p1** (`routines/src/news.md` — outlet-rotation steer off the recurring top-5 cluster): **applied 2026-09-25 (`rafael-apply-pass`) and verified landed** — the rotation language is present in both `routines/src/news.md` and the generated `routines/news.md` (assemble.py was re-run). Too few post-apply editions (only 09-26) to move the 30-day top5_share yet; not re-proposed.
- **p2** (`routines/src/weekend.md` — length discipline): **applied 2026-09-25 and verified landed** in `src` + generated file. Early evidence it works: weekend words fell −20% w/w (§L) with balance holding at 0.500.
- **registry-2026-09-20 reach flips** (anthropic.com, the-decoder.com, news.un.org, rts.ch → proxy): **applied 2026-09-25 and verified** — all four now read `reach: proxy` in `sources/registry.yml`.
- **registry-2026-09-20 candidate adds** (plos.org, agu.org): **pending** — not promoted; both already exist as registry candidates via the 09-20 scout sync. Not re-proposed.

## Source scout (Sunday duty)

**Stream picked: science** — the mechanical worst-deficit stream again (new_domains 6 = lowest in the portfolio; top5_share 1.00 = highest; candidates_open 0). Same structural caveat as last week: science's deficit is **not a candidate shortage** — most major primary publishers are already in the registry (pnas.org, science.org, iopscience.iop.org, elifesciences.org, cell.com, chemrxiv.org, plus last week's plos.org/agu.org), so the binding constraint is the narrow primary-journal universe plus the institutional-egress wall (§E/§K), not supply.

**Candidates appended** to `sources/candidates.jsonl` (both genuine primary publishers absent from the registry; both 403'd the evaluator egress, so `reach: proxy-needed`, writers vet with the bearer):
- **royalsociety.org** — The Royal Society; primary journals (Proceedings A/B, Royal Society Open Science, Biology Letters).
- **pubs.aip.org** — AIP Publishing; primary physics journals (Applied Physics Letters, J. Chem. Phys., Rev. Sci. Instrum.), complementary to APS/IOP already registered.

**Re-probe results (direct curl):** aljazeera.com → **200** and srf.ch → **200** (confirm `reach: direct`); nature.com → **303** (a resolve — confirms `reach: direct` is correct, consistent with 10 ok-curl in the fetch log); royalsociety.org, pubs.aip.org, admin.ch, pnas.org, science.org → **000 / "CONNECT tunnel failed, response 403"** — the *evaluator egress allowlist*, not proof the domains are blocked for the writers. So the two reach flips below rest on writer-side fetch telemetry, not these probes.

**Fetches used: 9** of the ≤20 budget (probes across candidate vets + reach controls).

## Patch proposals (for human review)

The pipeline is healthy; the standing prompt-side gaps from prior weeks are already applied (p1/p2). **One** new prompt patch this run, from the labeling finding (§M). The reach flips are machine-readable only (no prompt edit). The reader-profile learned-preference line is in the reader-feedback section below.

### Patch 1 — Impartial-labeling rule (contested ideological labels)
**Target prompt:** shared partial `routines/_shared/newsroom-ethos.md` (reaches all four writers)
**Section affected:** the ethos block, after "Resist sensational framing"
**Issue:** News 09-21 and the 09-26 weekend recap both wrote "the far-left Die Linke (The Left)" in the brief's own voice, where the cited Euronews source said only "The Left" — a contested ideological label stated as fact, asymmetric to the consensus "far-right AfD" in the same sentence. A reader flagged it with an emphatic reasoned 👎. It appeared across two editions/streams, so a shared-ethos rule is the right lever.

**Proposed change:**

> **Before:**
> ```
> In practice: go to the primary source and read it yourself; report what it actually says, not
> what a headline or a secondary write-up dramatizes. Flag what is preliminary, small-sample, or
> contested instead of smoothing it into a confident claim. Resist sensational framing — better to
> omit than to hype or dilute.
> ```
>
> **After:**
> ```
> In practice: go to the primary source and read it yourself; report what it actually says, not
> what a headline or a secondary write-up dramatizes. Flag what is preliminary, small-sample, or
> contested instead of smoothing it into a confident claim. Resist sensational framing — better to
> omit than to hype or dilute.
>
> Do not attach a contested political or ideological label (far-left, far-right, radical, extremist,
> hard-left) to a party or actor in your own voice unless it is genuinely consensus or you attribute
> it to a named source. Prefer the party's plain name or the cited source's own wording, and apply
> the same bar symmetrically across the spectrum.
> ```

**Why this helps:** fixes the exact miss the reader caught, at the layer that reaches every writer, without touching sourcing discipline that is already working.
**Risk:** a writer over-corrects and strips a genuinely consensus descriptor; mitigated by the "unless it is genuinely consensus or you attribute it" escape.

## Reader-feedback → profile proposals

**Completeness — every window feedback event, with a disposition** (from the ledger's `ev:"feedback"` events, selected by event `ts` in [2026-09-21, 2026-09-27]; `health.json → feedback.by_stream` news up 4 / down 2 / retractions 0; `unconsumed_total` 0):

- 2026-09-21 · news · 👎 · `st-6299f47c2ec9` (German state elections) — **reason: "JFC DUDE Die Linke is NOT FAR LEFT"** — **applied** (rm-1 below, auto-applied learned-preference line; and Patch 1). The bare -1 on the same story earlier the same minute is the same signal (one story), not a second one.
- 2026-09-21 · news · 👍 · `st-249c730bb69b` — bare tap (reason "") — **deferred**: below the reasoned-signal bar.
- 2026-09-22 · news · 👍 · `st-119114f1ba55` — bare tap — **deferred**: below the bar.
- 2026-09-24 · news · 👍 · `st-ae7923f9085a` — bare tap — **deferred**: below the bar.
- 2026-09-27 · news · 👍 · `st-563b7c097959` — bare tap — **deferred**: below the bar.

**Noise filter.** Only one reasoned event this window. It is a single story-thread, below the strict ≥2-distinct-stories bar for establishing a *new* theme — but it is a **reasoned vote** (which the bounded auto-apply grant explicitly admits), it is a factual/impartiality error rather than a taste preference, it **recurred across two editions** (news 09-21 + weekend 09-26), and it extends the **already-established** impartial-voice theme (2026-07-19/07-26/08-31). On those grounds I auto-applied one dated line; nothing else clears the bar, so no `source-weights.yml` change is proposed.

**rm-1 (auto-applied to `reader-profile.md` "Learned preferences"):**

> **Before:** _(end of Learned preferences — the 2026-09-13 line)_
>
> **After (appended):**
> ```
> - 2026-09-27: do not attach a contested ideological label ("far-left", "radical", "hard-left") to a
>   party in the brief's OWN voice when the cited source does not — Die Linke (The Left) is a
>   left/democratic-socialist party, not "far-left"; the 09-21 Euronews source headline said "The Left",
>   and the brief added "far-left" (repeated in the 09-26 weekend recap), asymmetric to the consensus
>   "far-right" for the AfD (1× emphatic 👎 on news 2026-09-21, "Die Linke is NOT FAR LEFT"). Extends the
>   2026-07-19 impartial-voice line from actors' self-characterisations to the writer's own party labels:
>   use the party's plain name or the source's wording, and reserve loaded labels for where they are
>   genuinely consensus or attributed.
> ```

**Why this helps:** writers read `reader-profile.md` at compose time; this records the specific reader signal, while Patch 1 sets the durable rule. **Risk:** minimal — the line is guidance, and it names the escape (consensus or attributed).

## Machine-readable proposals

Written this run:
- `proposals/reader-model-2026-09-27.json` — **rm-1** (reader-profile.md labeling line, stamped `applied: true, applied_by: evaluator`) and **p1** (newsroom-ethos labeling rule, `applied: false`).
- `proposals/registry-2026-09-27.yml` — two `reach: direct → proxy` flips (dw.com incl. rss.dw.com, euronews.com) on writer-telemetry evidence, plus the royalsociety.org and pubs.aip.org candidate adds from the scout; `applied: false`.

## Cross-week trend

Flat-healthy with three genuine improvements (T1 share up, weekend balance to dead-centre 0.500, weekend length down −20% as p2 lands) and two carried maintenance items (registry reach drift, now two more domains; the benign force-rewrite false positive). No regression against 2026-09-20 on any dimension. The registry reach-drift cleanup is progressing: six `direct`-recorded proxy-only domains identified and flipped across two weeks.

## Open questions for human review

1. **`origin/main` was force-rewritten again this window — verified benign, but the guard keeps false-positiving.** The fire-start `git pull` reported a forced update (`e5361f8 → 522cb8e`) landing *concurrently* with the pull, and `health.json → continuity.off_main.commits_not_on_main` lists 20 orphaned old-tip commits. **This is the same false positive last week's review documented, re-verified:** those commits are the *stale old* `origin/main` tip; `git log HEAD --not origin/main` is now empty, every content post (incl. `2026-09-23-news.md`, `2026-09-23-science.md`) is present on the new HEAD, and `remote_branches` is empty — no `claude/*` diversion, no content lost. But the `off_main` guard will keep firing this same false positive after every forced pull. Two reviews running have now flagged it; worth either finding *what* rewrites `main` (the repo convention is direct commits, not history rewrites) or teaching `metrics.py` to exclude the stale-local snapshot so the guard stops crying wolf on forced pulls.
2. **Registry `reach` records keep drifting from reality** (§K) — six `direct` records proxy-only across two weeks (four flipped, two new this week). The deterministic reach probes meant to maintain `reach:` either are not running or record the evaluator-egress result. Worth confirming the probe job is alive; otherwise the evaluator will keep surfacing these one or two at a time off writer telemetry.
3. **AI/ML output volume jumped +52% w/w** (§L, 1,977 → 3,002 words mean). It is *not* repetitive (repeat_rate 0) and the density is high-signal, so no patch this week — but if it persists next week with flat story count, ai-ml becomes the next candidate for a weekend-style soft length steer. Flagging now so the trend is visible if it continues.
4. **Two narrow streams still can't meet the 30-unique-domains / 0.50-top5 diversity targets by design** (science: primary-journal universe + egress wall; weekend: high waiver because it revisits already-covered papers). Three-plus reviews have now flagged science's top5_share 1.00 as "worst stream" when it is largely a small-denominator artifact. Are these portfolio targets meant to apply to the weekly/narrow streams at all, or should they be stream-tiered?
