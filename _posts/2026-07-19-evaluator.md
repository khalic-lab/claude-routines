---
layout: single
title: "Weekly Pipeline Review — 2026-07-19"
date: 2026-07-19T11:45:00+02:00
categories: [evaluator]
published: true
---

# Weekly Brief Pipeline Review — 2026-07-19

_Coverage: briefs from 2026-07-13 to 2026-07-19._
_Files read: 5 news, 2 AI/ML (expect ~2), 1 science (expect ~1), 0 sports (first run 2026-07-20 — pre-launch, not a gap), 1 weekend, prior review found (2026-07-12)._

The pipeline is healthy and writing on cadence: 5 News, 2 AI/ML, 1 Science, 1 Weekend — exactly the expected shape for the window, with Sports still pre-launch. The editorial quality is high across the board (impartiality, primary-source discipline, personalization all land), and reader sentiment is strongly net-positive (25 👍 / 5 👎). The flags this week are **mechanical, not editorial**: two of them are false positives inside my own metrics scripts, one is an affiliation-coverage gap concentrated in same-day arXiv preprints, and the persistent structural weakness is Science's source concentration plus a cluster of feeds that fail at the point of use.

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains 30d (worst stream, source-health) | science 3 | ≥30 | 🔴 |
| New domains this window (portfolio, source-health) | ~9 tagged `[new source]` (news 5, ai-ml 3, weekend 1) | ≥2–3/wk | 🟢 |
| Top-5 outlet share (worst stream, source-health) | science 1.00 (news 0.87) | ≤0.50 | 🔴 |
| Waiver rate (worst stream, source-health) | science 0.67 | ≤50% | 🔴 |
| Discovery footer present (every brief) | 9/9 (100%) | 100% | 🟢 |
| T1 citation % | ~45% portfolio (news 0% by design — regional hubs are T2) | ≥40% | 🟢 |
| T3 leakage count | 0 | 0 | 🟢 |
| Non-English citation % (portfolio) | high (news heavily FR/DE: Le Temps, SRF) | ≥10% | 🟢 |
| Link sample pass rate | 5/20 — **unmeasurable** (evaluator egress allowlist) | ≥90% | ⚪ |
| Fabrication count | 0 detected | 0 | 🟢 |
| Single-source rate (portfolio) | 17.4% (weekend 25.7% stream-level) | <20% | 🟡 |
| Empty section instances | 1 (false positive — see §D) | <5 | 🟢 |
| Repeat rate (worst stream, health.json) | news 0.24 — honest `[ongoing since]` tracking | judge | 🟢 |
| Direct-fetch ratio (portfolio) | ~0.97 | ≥0.35 | 🟢 |
| Feeds with >50% fail rate | ~5 fully-walled (swissinfo, science.org, cell, HUDOC, euronews-HU) | 0 | 🟡 |
| Citations on `reach: blocked` domains without [via snippet] | 0 | 0 | 🟢 |
| Unconsumed feedback backlog (health.json) | 0 | 0 | 🟢 |
| Vendor-PR-lead share (AI/ML, §M) | ~25% | ≤40% | 🟢 |
| Aggregator-shape failures (§M, of 5) | 0 | 0–1 | 🟢 |
| Personalization misses (§M, of 5) | 0 | 0–1 | 🟢 |
| Affiliation not-listed rate (papers, §N) | ~30–40% (concentrated in same-day arXiv) | <20% | 🔴 |

## A–N: Detailed findings

### A. Source diversity & discovery
The portfolio discovery engine is working where the writers control it. **News** met its discovery quota on 4 of 5 editions (`genevasolutions.news`, `france24.com`, `jurist.org`, `globenewswire.com`, `hudoc.echr.coe.int` all anchored new-source stories), waiver rate 0.05 — excellent. The News `top5_share` of 0.87 is not a discovery failure but **hub-volume concentration**: the daily churn leans on SRF / Le Temps / Al Jazeera (all saturated this window) as the appropriate regional primaries, while new domains are added at the margins. This is honest and I would not penalize it.

**AI/ML** is in good shape (34 unique domains 30d, top5 0.52, waiver 0.07) and met discovery both editions (`kimi.com`, `thinkingmachines.ai`, `soofi.info`, `parlance-labs.com`). **Weekend** waived by one (anchored `parlance-labs.com`, fell one short of its 2-domain quota) with an honest reason and a documented probe of dormant candidates.

**Science remains the standing deficit** and the target of this week's scout: 3 unique domains, `top5_share` 1.00, waiver rate 0.67 — it sits almost entirely on `arxiv.org` + `nature.com`. Its discovery waiver this week was honest (bioRxiv/medRxiv/Cell all returned empty bodies; ESO/CAB press releases were secondary to Nature primaries already in hand), but the deficit is structural, not a one-off. The ETH/EPFL/PSI candidates entered organically last week (writers cited them → auto-candidate) but this week's Science edition didn't use them. Tier distribution is clean: **T3 = 0%** everywhere per policy; T1 ≈ 45% portfolio (News runs T1=0% by design — regional news hubs are classed T2).

### B. Aggregator leakage
`health.json → briefs.aggregator_leakage` is **empty**. Zero citations of HN / Reddit / X / Bluesky / Mastodon across all 9 briefs. 🟢

### C. Link health — UNMEASURABLE this run
`linkcheck.py --check`: **5/20 resolve (2xx/3xx), 142 links total**. This is not a fabrication signal — it is the evaluator sandbox's **egress allowlist**. The 5 passes are exactly the allowlisted news hosts (aljazeera.com, letemps.ch); every arXiv, Nature, the-decoder, thinkingmachines, doi.org, lesswrong URL returned `ERR:56 — CONNECT tunnel failed, response 403` (confirmed: `srf.ch`/`aljazeera.com` → 200, everything else → `connect_rejected` at the proxy). The writers reach these same feeds fine (their footers show `arxiv {ok via curl}`, `nature {ok via proxy}`, and direct-fetch ratios ~0.97), so this is **not** an egress regression in the writer path — it is the evaluator running without the fetch-proxy bearer by design. Reporting the dimension unmeasurable. Two *reachable* SRF links did 404 (`ukraine-trifft-raffinerie`, one weekend recap link), worth a spot-fix but not systemic. Claim spot-checks on the reachable AJ/Le Temps links matched the cited facts.

### D. Section vitality — 1 flagged, false positive
`empty_sections` = 1: weekend `🧠 Cross-cutting threads`. **This is a parser artifact.** That section (2026-07-18-weekend.md lines 26–34) contains four substantial bold-numbered synthesis paragraphs citing arXiv IDs inline — it is one of the richest parts of the brief. The vitality parser keys on story-anchor (`st-`) markup, which the threads section deliberately omits (it's analytical prose, not a story list). No real empty section anywhere this week. Patch proposed (rm-4) to stop the parser counting anchor-free synthesis sections as empty.

### E. Coverage gap recurrence
The recurring structural gap is **`swissinfo.ch` hard-blocking the sandbox**: 2026-07-13 (HTTP 403) and 2026-07-14 (connection refused direct + HTTP 410 proxy). It's recorded `reach: direct` but never yields — a dead discovery candidate on the News affinity. Registry reach-flip proposed. Other gaps were one-offs and handled honestly (HUDOC/echr.coe.int SPA-blocked 07-16, gov APIs 403-direct-but-proxy-ok 07-18, thin Swiss federal desk on a summer Monday 07-13).

### F. Triangulation rate
Portfolio single-source rate **17.4%** (19/109) — under target. Per stream: news 0.13, science 0.00, ai-ml 0.17, **weekend 0.26** — weekend nudges over the 0.25 stream threshold. Reading the weekend `[single-source]` items, they are genuine single-primary cases (individual preprints, one xeno-transplant Nature Medicine paper, one lab model card) honestly tagged, not lazy sourcing. 🟡, acceptable given the tags are truthful.

### G. Tag discipline
`[preprint]` on arXiv items: sampled 5 in ai-ml/weekend — all correct. `[vendor PR]`: 3 across ai-ml (OpenAI GPT-Red, Sakana Fugu, weekend Inkling) — all genuine vendor announcements, all carrying skeptical framing (see §M). `[via snippet]`: news 3, weekend 1, ai-ml 0 — **low and appropriate**, and each documents the specific feed failure (Airbnb blog 403, etc.); the curl-first chain is keeping via-snippet down as intended. `[new source]` novelty: candidates.jsonl had no new writer-tagged junk anchors this week (the domains cited new — kimi.com, thinkingmachines.ai, parlance-labs.com — are all genuine primaries). No tag-discipline defects.

### H. Topic balance (weekend)
`weekend_balance`: `ml_items` 20 / `science_items` 16, **`ml_share` 0.556** — inside the [0.35, 0.65] band. 🟢 Well-balanced.

### I. Repetition detection
`repeat_rate`: news 0.24 (8 repeats), weekend 0.21 (8), ai-ml 0.00, science 0.00. The News repeats are **honest ongoing-story tracking**, not re-summaries: the Iran-strikes and Swiss-heatwave threads recur daily but each carries a new dated fact and the `[ongoing since]` tag (07-18: "seventh strike wave", "water cut to villages"; heatwave: "Gotthard tailback", "fish dying"). This is the correct `[ongoing since]` discipline, not the defect the metric guards against. **Identity integrity:** `reconcile.py` → **0 flagged**, 1 resolved-by-merge (informational, the old st-51f4/Cuba-class merge standing down cleanly). 🟢

### J. Cross-week trend
Vs 2026-07-12: aggregator leakage 0 → 0 (steady). Science deficit persists (3 unique domains, top5 1.00 both weeks). Affiliation-not-listed improved from ~37% (07-11 weekend) to ~27% weekend / ~45% ai-ml this week — better on 1-day-old papers, still poor on same-day submissions. Via-snippet stayed low. Direct-fetch ratio remains ~0.97. Feedback swung strongly positive (last week's Iran elapsed-time 👎 did not recur — the 07-12 learned-preference line appears to be holding).

### K. Feed reachability & direct-fetch rate
Portfolio direct-fetch ratio **~0.97** (ai-ml 1.00, news 0.93, science 1.00, weekend 0.97) — every stream far above its floor. The curl-first chain is doing its job. **Method comparison:** several feeds fail direct-curl but succeed via proxy — `the-decoder.com/feed`, `arstechnica.com/feed`, `earthquake.usgs.gov`, `federalregister.gov` all show `direct-curl {fail}` + `{ok via proxy}`. That's the proxy correctly carrying JS/anti-bot hosts, not a wall. The genuinely-walled feeds (both methods fail) are: **swissinfo.ch** (2 fail / 0 ok), **science.org news_current.xml** (fail, empty), **cell.com current.rss** (fail, empty), **HUDOC** (fail), **euronews Hungary URL** (fail), **bioRxiv/medRxiv details API** (fail this run, though the JSON API worked for weekend). These directly thinned Science's biology desk to a single item on 07-15. `reach:blocked`-without-snippet violations: **0**. Reach-flip proposals filed for science.org, cell.com, swissinfo.ch (see registry proposal).

### L. Output volume
Word-count means vs prior week: news 794 (↑ from 739, +7%), ai-ml 2435 (↑ from 2050, +19%), science 1560 (↑ from 1520, +3%), weekend 5300 (↓ from 5600). All within the +25% guard; ai-ml's +19% tracks a genuinely denser release week (Kimi K3 + Inkling + an 11-paper batch), not padding. No stream is both repetitive and long. No output-cap lever needed this week.

### M. Editorial shape — all green
- **Vendor-PR-lead share (AI/ML):** ~25%. The vendor releases (Kimi K3, Inkling, GPT-Red, Sakana Fugu) *lead* with the announcement but immediately fold in independent Artificial Analysis evals, hallucination-rate caveats, and skeptical framing ("capability claims are vendor-reported", "the two numbers aren't necessarily comparable"). Gemma 4's silent update is framed as a reproducibility problem, not a feature. Well under the 40% flag.
- **Aggregator-shape (5 leads sampled):** 0 failures. Weekend Iran (SRF + framing), News Iran (SRF+AJ + "widening target set" analysis), News Ukraine (Le Temps doctrine-clash read), AI/ML Kimi (vendor blog + independent Elo + skeptic), AI/ML EU-Google (Ars + structural-remedy framing) — every lead adds judgment the source doesn't contain.
- **Personalization (5 sampled):** 0 misses. EU ETS → Swiss climate-policy link; cadmium vs France; Arctic/EPFL scientific-diplomacy; heatwave/1540 CH-historical; Kimi self-host sovereignty angle. Strong and never forced.

### N. Affiliation element — the week's real quality flag
- **Coverage rate:** ~30–40% `(affiliation not listed)` portfolio, above the <20% target. **Root cause is now clear:** it's concentrated in **same-day arXiv preprints**. AI/ML 07-17 ran ~5/11 not-listed (footer: 2607.15232 and 2607.14952 HTML author blocks returned empty; 2607.14888/15263/14682 same class), Weekend 07-18 ~6/22 — all from 2026-07-16 submissions whose arXiv HTML mirror hadn't rendered yet. By contrast **Science 07-15 ran 0/7** because its papers were a day old and the HTML had rendered. The writers are correctly refusing to guess (the anti-fabrication rule), but the coverage floor is being set by arXiv's 1–2-day HTML lag. Fix proposed (rm-2): fall back to the **PDF first page** (`arxiv.org/pdf/<id>`, available immediately) before marking unlisted. Note: last week's rm-4 (OpenAlex fallback) is effectively **superseded** — affiliations.md now documents that OpenAlex returns empty institutions for arXiv records, so the PDF route is the right next lever, not the API route.
- **Halo audit:** **no prestige bias.** The `(affiliation not listed)` / independent-author papers (Value Leakage, ExTernD, EcoSpec, LongStraw in weekend; the tokenizer and ideological-generalisation papers in ai-ml) *lead* their sections and get the same "why it matters" treatment as the Harvard/MIT/Microsoft-affiliated ones. Unaffiliated ≠ downranked. 🟢

## Prior proposals status

From 2026-07-12 (`proposals/reader-model-2026-07-12.json`, `registry-2026-07-12.yml`):
- **rm-1** (reader-profile elapsed-time line) — **applied and verified**: the dated line is present in `reader-profile.md` "Learned preferences" (auto-applied by the evaluator; the Iran elapsed-time 👎 did not recur this week).
- **rm-2** (weekend.md: cite only URLs actually fetched) — **pending, not applied**. The URL-verification guard is not in `routines/src/weekend.md`. Still relevant, though no 404-fabrication recurred this week.
- **rm-3** (weekend.md: compute elapsed intervals from carried dates) — **pending, not applied**. Not in the prompt; no elapsed-time error recurred.
- **rm-4** (affiliations.md: OpenAlex/Semantic Scholar fallback) — **pending, and now superseded**. `affiliations.md` explicitly documents that OpenAlex/Semantic Scholar return empty institutions for hours-old arXiv records, so this approach is closed out; replaced by rm-2 (PDF-first-page) this week.
- **registry-2026-07-12.yml** — **not applied** (still `applied: false`). The candidate promotions (ethz.ch, epfl.ch, psi.ch: candidate→probation) did not land — those domains sit at `status: candidate` (they entered organically via writer citation, reach recorded `direct`, not promoted). The re-probe flips (journals.aps.org, science.org, cern.ch: direct→re-probe) also did not land — science.org still `reach: direct` and **still failed this week**, so I've re-surfaced it with a second week of evidence.

## Source scout (Sunday duty)

**Stream picked: Science** — the worst active-deficit stream (new_domains 3, top5_share 1.00, waiver_rate 0.67, unique_domains 3). Sports shows new_domains 0 but has 0 stories (pre-launch, first run tomorrow), so it's degenerate rather than deficient; Science is the genuine chronic concentration.

**Candidates appended** to `sources/candidates.jsonl` (4) — genuine primary Swiss research publishers absent from the registry, chosen to break Science's arxiv+nature monopoly and double as personalization sources: **unige.ch** (University of Geneva communiqués), **empa.ch** (Swiss Federal Labs for Materials Science), **wsl.ch** (Forest/Snow/Landscape — cryosphere/climate, ties to the recurring heatwave coverage), **unibe.ch** (University of Bern). All appended `reach: proxy-needed`.

**Re-probe outcome — blocked by the evaluator egress allowlist.** All 9 direct-curl probes (4 candidates + 5 stale reach entries: science.org, cell.com, swissinfo.ch, journals.aps.org, home.cern) returned `CONNECT tunnel failed, response 403` — the evaluator sandbox allows only a small news-host allowlist (SRF/Le Temps/Al Jazeera reachable; science hosts not), and this routine holds no fetch-proxy bearer by design. So I could not direct-vet from here. Instead I used the **writers' own footers this week as the probe evidence** (they hold the bearer): science.org failed empty, cell.com failed empty, swissinfo.ch 403/410 — all recorded `reach: direct`. Those realized failures drive the reach-flip proposals in `registry-2026-07-19.yml`.

**Fetches used: ~11** (9 probes + 2 allowlist-confirmation), well under the ≤20 budget.

## Patch proposals (for human review)

### Patch 1 — Affiliation fallback: parse the arXiv PDF first page for same-day preprints
**Target prompt:** shared partial `routines/_shared/affiliations.md` (hits ai-ml, science, weekend)
**Section affected:** Affiliations block, arXiv-preprint branch
**Issue:** ~30–40% of this week's paper bylines read `(affiliation not listed)`, concentrated entirely in same-day arXiv submissions whose HTML author block hasn't rendered yet (arXiv's HTML mirror lags 1–2 days). Science's day-old papers ran 0% not-listed, confirming the lag as the cause.
**Proposed change:**

> **Before:**
> ```
> Do NOT use index APIs for preprints: Semantic Scholar has not indexed hours-old
> papers, and OpenAlex's arXiv records carry EMPTY institutions ... [if the HTML
> author block does not render, mark "(affiliation not listed)"].
> ```
>
> **After:**
> ```
> Do NOT use index APIs for preprints (Semantic Scholar/OpenAlex return empty
> institutions for hours-old arXiv records). If the arXiv HTML author block does
> not render — common for same-day submissions, whose HTML mirror lags 1–2 days —
> fall back to the PDF first page (arxiv.org/pdf/<id>, available immediately) and
> read the author/affiliation block there BEFORE marking "(affiliation not listed)".
> Never guess.
> ```

**Why this helps:** Closes the coverage gap on exactly the papers that miss today (same-day submissions) using a source that always exists at submission time.
**Risk:** PDF author-block parsing is messier than HTML; if it yields low-confidence output the writer must still mark unlisted rather than guess — keep the no-fabrication rule dominant.

### Patch 2 — Flip `reach:` for feeds that fail at the point of use
**Target prompt:** `sources/registry.yml` (human-gated; proposal in `registry-2026-07-19.yml`)
**Section affected:** reach fields for science.org, cell.com, swissinfo.ch
**Issue:** Three domains recorded `reach: direct` failed for the writers this week (science.org empty, cell.com empty, swissinfo.ch 403/410). science.org and cell.com thinned Science's biology desk to one item; swissinfo.ch has burned a discovery slot on News for two weeks. science.org was already flagged 2026-07-12 and went unapplied.
**Proposed change:** science.org `direct → search-only`; cell.com `direct → proxy`; swissinfo.ch `direct → blocked`. (Full evidence in the YAML.)
**Why this helps:** Stops writers spending fetches on feeds that never yield, and stops swissinfo.ch consuming a discovery attempt each News run.
**Risk:** If a flip is too aggressive (e.g. cell.com works via proxy), the writer's first-citation probe corrects it back — the registry stays writer-verified.

### Patch 3 — Fix the off-main self-delivery guard (metrics.py false positive)
**Target prompt:** `tools/evaluator/metrics.py` (`build_off_main`)
**Section affected:** the `git log --all --not main` computation
**Issue:** This run's `continuity.off_main` flagged 20 commits (including HEAD) as "not on main" — all provably on origin/main. The routine runs in detached HEAD after `git pull --ff-only`, which advances origin/main but leaves the local `main` ref 34 commits stale; comparing against local `main` therefore mislabels every pulled commit. The guard exists to catch real `outcomes`-stranding, and a false positive every detached-HEAD run erodes trust in it.
**Proposed change:** compare against `origin/main` instead of `main` (`git log --all --not origin/main`, or resolve `main` and fall back to `origin/main` when HEAD is detached).
**Why this helps:** Makes the self-delivery guard fire only on genuine off-main diversions.
**Risk:** Minimal — `origin/main` is the correct published-line reference; the check becomes accurate, not weaker.

### Patch 4 — Section-vitality parser shouldn't flag anchor-free synthesis sections
**Target prompt:** `tools/evaluator/metrics.py` (brief-text section parser)
**Section affected:** `empty_sections` detection
**Issue:** The weekend `🧠 Cross-cutting threads` section — four rich synthesis paragraphs — is counted "empty" because it carries no `st-` story anchors. Recurs every week the section runs.
**Proposed change:** detect emptiness by absence of body text, not absence of anchors; or whitelist known anchor-free synthesis sections (Cross-cutting threads).
**Why this helps:** Removes a recurring false positive from Section D.
**Risk:** None material — a text-presence check is strictly more accurate.

## Reader-feedback → profile proposals

Window sentiment (from the ledger's folded `ev:"feedback"` state; `unconsumed_total` = 0, fold is current): **25 👍 / 5 👎, 0 retractions.** By stream: ai-ml 10/0, science 4/0, news 4/3, weekend 3/2. AI/ML and Science are unambiguously landing.

**One real signal (≥2 votes on distinct stories, same theme):** two downvotes carry written reasons, on different stories in different streams, but name the *same* editorial issue — the brief adopting an actor's loaded word in its own voice:
1. Weekend 2026-07-18 Iran lead ("seventh and **final** strike wave"): _"'Final' should be in quotes, given their history of not following through with what they say."_
2. News 2026-07-18 ESA item ("species **merely** listed as 'threatened'"): _"'merely', this is the framing of the US admin, we need to stay impartial, 'merely' endangered is still significant."_

Both ask for the same thing: keep the brief's own voice impartial and attribute/quote an actor's self-characterization rather than stating it as fact. Two signals, distinct stories, verbatim reasons → qualifies for the bounded auto-apply.

**Auto-applied** (appended to `reader-profile.md` "Learned preferences", stamped `applied: true` in `reader-model-2026-07-19.json`):
> **Before:** _(end of Learned preferences section)_
> **After:**
> ```
> - 2026-07-19: keep the brief's own voice impartial — when an actor characterizes
>   their own action (a government calling a strike wave "final", a law's "merely
>   threatened" tier), attribute or put that word in quotes rather than stating it as
>   fact in the brief's voice (2× 👎 across distinct stories: weekend 2026-07-18 Iran;
>   news 2026-07-18 ESA "merely").
> ```

No `source-weights.yml` change proposed — the signal is an editorial-voice preference, not a source-quality problem. The other 3 downvotes were bare taps (no reason) → noise, no action.

## Cross-week trend

Steady-state healthy on the mechanical dimensions the writers control (leakage 0, direct-fetch ~0.97, T3 0%, single-source under target). The two persistent items across weeks are **Science source concentration** (unchanged; scout candidates filed) and **affiliation coverage on fresh preprints** (improved on day-old papers, still gapped on same-day — PDF-fallback patch filed). Reader sentiment improved markedly (25/5 vs a more mixed prior week), and last week's auto-applied elapsed-time line appears to be holding.

## Open questions for human review

1. **Science concentration** is now a multi-week structural item, not a fluctuation. Beyond promoting the scout candidates (unige/empa/wsl/unibe), is it worth arming the Science discovery quota (currently report-only at ≥2) once a few Swiss-institution feeds are proven reachable — or is arxiv+nature genuinely sufficient primary coverage for a weekly science brief?
2. **science.org has now failed two weeks running** while recorded `reach: direct` and last-applied-never. Apply the flip, or retire it from the Science affinity entirely?
3. The evaluator's **egress allowlist** blocks it from direct-vetting scout candidates and re-probing registry reach. That's by design (no bearer), but it means the scout can only *append* candidates, never confirm them. Acceptable, or worth giving the evaluator a read-only proxy path for probing?
