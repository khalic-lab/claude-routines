---
layout: single
title: "Weekly Pipeline Review — 2026-07-26"
date: 2026-07-26T11:48:36+02:00
categories: [evaluator]
published: true
---

# Weekly Brief Pipeline Review — 2026-07-26

_Coverage: briefs from 2026-07-20 to 2026-07-26._
_Files read: 6 news, 2 AI/ML (expect ~2), 1 science (expect ~1), 1 sports (expect ~1), 1 weekend, prior review found (2026-07-19)._

The pipeline is healthy and writing exactly on cadence: 6 News, 2 AI/ML, 1 Science, 1 Sports (its second-ever edition), 1 Weekend — the expected shape for the window. Editorial quality holds high: impartiality, primary-source discipline, and personalization all land in the samples, aggregator leakage is zero, and reconcile/identity integrity is clean. **The one genuinely new flag this week is mechanical spend: output volume jumped sharply on the two densest streams — AI/ML +47% and News +27% week-over-week** — with no matching rise in story count. Alongside that sit two standing structural items (Science's source concentration, now multi-week; AI/ML's single-source rate creeping over threshold on The-Decoder-only industry items) and the two evaluator-script false positives that last week's patches would have fixed but which remain unapplied. Reader sentiment is thinner and more mixed than last week (9 👍 / 6 👎), with News net-negative on two pointed, actionable reasons.

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains 30d (worst stream, source-health) | science 5 (sports 4, young) | ≥30 | 🔴 |
| New domains this window (portfolio, source-health) | ~5 `[new source]` (news 3, ai-ml 2) | ≥2–3/wk | 🟢 |
| Top-5 outlet share (worst stream, source-health) | science 1.00 / sports 1.00 (news 0.83) | ≤0.50 | 🔴 |
| Waiver rate (worst stream, source-health) | sports 1.00 / science 0.75 | ≤50% | 🔴 |
| Discovery footer present (every brief) | 11/11 (100%) | 100% | 🟢 |
| T1 citation % | ~50% portfolio (news 0% by design — hubs are T2) | ≥40% | 🟢 |
| T3 leakage count | 0 (untiered = new-source candidates, not T3) | 0 | 🟢 |
| Non-English citation % (portfolio) | high (news FR/DE, sports DE) | ≥10% | 🟢 |
| Link sample pass rate | 3/20 — **unmeasurable** (evaluator egress) | ≥90% | ⚪ |
| Fabrication count | 0 detected | 0 | 🟢 |
| Single-source rate (portfolio) | 21.9% (**ai-ml 30.6% stream-level**) | <20% | 🟡 |
| Empty section instances | 2 (both false positives — see §D) | <5 | 🟢 |
| Repeat rate (worst stream, health.json) | news 0.19 — honest `[ongoing since]` | judge | 🟢 |
| Direct-fetch ratio (portfolio) | ~0.97 | ≥0.35 | 🟢 |
| Feeds with >50% fail rate | ~6 fully-walled (both methods, 0 ok) | 0 | 🟡 |
| Citations on `reach: blocked` domains without [via snippet] | 0 | 0 | 🟢 |
| Unconsumed feedback backlog (health.json) | 0 | 0 | 🟢 |
| Vendor-PR-lead share (AI/ML, §M) | ~28% | ≤40% | 🟢 |
| Aggregator-shape failures (§M, of 5) | 0 | 0–1 | 🟢 |
| Personalization misses (§M, of 5) | 0 | 0–1 | 🟢 |
| Affiliation not-listed rate (papers, §N) | ~19% (9/47) — improved from ~30–40% | <20% | 🟢 |
| **Output volume WoW (§L)** | **ai-ml +47%, news +27%** | ≤+25% | 🔴 |

## A–N: Detailed findings

### A. Source diversity & discovery
The discovery engine works where the writers control it. **News** met discovery on the strength of its regional-hub churn: `top5_share` 0.83 is hub concentration (SRF / Le Temps / Al Jazeera / DW all saturated, all the appropriate regional primaries), not a discovery failure, with 3 `[new source]` anchors at the margins and waiver rate 0.19 — honest. **AI/ML** is in good shape at the 30-day level (24 unique domains, top5 0.66, waiver 0.18) and met discovery on 07-24 (`aisi.gov.uk` `[new source]`, anchoring both benchmark items); 07-21 waived honestly (pursued theinformation.com and semianalysis.com as unregistered primaries, both paywalled/blocked). **Weekend** waived (worked dormant registry candidates cell.com and acoup.blog back in after 30+ days idle, but surfaced no genuinely unregistered domain worth citing over registered primaries).

**Two chronic-deficit streams:** **Science** remains the standing structural item — 5 unique domains, `top5_share` 1.00, waiver 0.75 — sitting on arXiv + Nature + a thin tail (Science.org, ESO). Its 07-22 waiver was honest (revived `eso.org` after two weeks dormant, fell one short of its 2-domain quota; ETH/PSI/APS/Cell RSS all sandbox-unreachable). **Sports** shows the lowest `new_domains` (4) and `waiver_rate` 1.00, but its deficit is a different animal: **reachability, not discovery effort** — see §K. Tier distribution is clean: T3 = 0% everywhere per policy; T1 ≈ 50% portfolio (Weekend ran 31/34 T1; News runs T1=0% by design, its regional hubs classed T2). The "untiered" counts in the AI/ML and Sports footers are new-source candidate domains awaiting a tier, not T3 leakage.

### B. Aggregator leakage
`health.json → briefs.aggregator_leakage` is **empty**. Zero citations of HN / Reddit / X / Bluesky / Mastodon / Threads across all 11 briefs. 🟢

### C. Link health — UNMEASURABLE this run
`linkcheck.py --check`: **3/20 resolve (2xx/3xx), 158 links total.** This is again the evaluator sandbox's egress allowlist, not a fabrication signal: the only passes were `aljazeera.com` and `srf.ch` (the allowlisted news hosts); every arXiv, Nature, DW, Guardian, the-decoder, lesswrong, huggingface, simonwillison URL returned `ERR:56 — CONNECT tunnel failed, 403`. The writers reach these same feeds fine (their footers show arXiv/Nature/DW all resolving via curl or proxy, direct-fetch ratio ~0.97), so this is **not** a writer-path egress regression — it is the evaluator running without the fetch-proxy bearer by design. Reporting the dimension unmeasurable. One *reachable* real breakage: `letemps.ch/economie/...stadler-rail-refuse-de-payer-une-rancon` (2026-07-21-news) returned **404** — a genuinely dead link worth a spot-fix, distinct from the egress noise. Claim spot-checks on the reachable AJ / Le Temps / SRF links matched the cited facts.

### D. Section vitality — 2 flagged, both false positives
`empty_sections` = 2, both in 2026-07-25-weekend.md: **`🧠 Cross-cutting threads`** (four substantial synthesis paragraphs, among the richest prose in the brief) and **`🍎 Apple Silicon / local inference ecosystem`** (a full paragraph on llama.cpp's web-UI render-cost cut, whose single citation uses a plain markdown link with no `st-` anchor). Neither is empty. This is the **same parser artifact I proposed fixing last week (rm-4, unapplied)** — the vitality parser keys on `st-` story-anchor markup, so any anchor-free prose section reads as empty. The false-positive class has now *grown* from one section type (Cross-cutting threads) to two (add the Apple desk), which strengthens the case for the fix. No genuinely empty section anywhere this week.

### E. Coverage gap recurrence
Gaps this week were mostly honest one-offs (contested Hodeida casualty figures; India "Cockroach" movement demands thin in reachable DW coverage; arXiv Atom date-API 429/502 forcing per-paper date confirmation). One **recurring structural gap** persists: **science's biology/physics desk thinned by walled journal feeds** — Science.org, APS, Cell, ETH, PSI all failed in the 07-22 sandbox, pushing the Earth's-core item to a `[via snippet]` secondary. Registry reach-flips filed (§K). A second recurrence worth naming is cosmetic but now ≥3 editions: the **stale "git push failed" footer note** (see Open questions).

### F. Triangulation rate
Portfolio single-source rate **21.9%** (28/128) — just over the <20% target, and up from last week's 17.4%. Per stream: news 0.21, weekend 0.15, science 0.17, sports 0.20, **ai-ml 0.31**. The driver is **AI/ML at 30.6%, over the 25% stream threshold** — and it is concentrated entirely in the 07-24 "New models / Industry" items (Poolside, Cisco, Flux 3, OpenAI-Health, AMD–Anthropic, Alphabet capex, Zenity), each cited to a single The-Decoder secondary because the vendor primaries were JS-rendered and yielded no text. The tags are honest and each item carries the standard skeptic framing ("vendor claim on a vendor benchmark; independent testing needed"), so this is not lazy sourcing — but it is exactly the pattern one reader downvoted this week (see reader-feedback). 🟡

### G. Tag discipline
`[preprint]` on arXiv items: sampled 5 across ai-ml/weekend — all correct. `[vendor PR]`: 2 (AI/ML Qwen 3.8 on 07-21, OpenAI "Health in ChatGPT" on 07-24) — both genuine vendor announcements carrying skeptical framing. `[new source]` novelty: the week's new `sources/candidates.jsonl` writer entry was `aisi.gov.uk` (UK AI Security Institute) — spot-checked, a genuine government primary, not a junk anchor. `[via snippet]`: science 1 (Earth's core, after Science.org 403), sports 3 (ESPN / Formula1.com / Cyclingnews, after official primaries were Cloudflare-walled), ai-ml/news/weekend 0 — low and each documenting a specific feed failure. `[single-source]` used truthfully throughout. No tag-discipline defects.

### H. Topic balance (weekend)
`weekend_balance`: `ml_items` 20 / `science_items` 16, **`ml_share` 0.556** — inside the [0.35, 0.65] band. 🟢 Well-balanced, essentially identical to last week (0.556 both weeks).

### I. Repetition detection
`repeat_rate`: news 0.19 (9 repeats), weekend 0.07 (3), ai-ml/science/sports 0.00. The News repeats are **honest ongoing-story tracking**, not re-summaries — the Iran/Hormuz war, the southern-Europe wildfires, and the Swiss heatwave/drought each recur across editions but every instance carries a new dated fact and the `[ongoing since]` tag (Hodeida front opening, evacuation totals quadrupling, fireworks bans extended). This is the correct discipline, not the defect the metric guards against. **Identity integrity:** `reconcile.py --root .` → **0 flagged, 0 resolved-by-merge, 22 editions checked.** No id forks. 🟢

### J. Cross-week trend (vs 2026-07-19)
- **Affiliation coverage improved:** ~30–40% not-listed → **~19%** (see §N). Aggregator leakage 0 → 0 (steady). Direct-fetch ratio ~0.97 → ~0.97 (steady). T3 0% → 0%.
- **Single-source worsened:** 17.4% → 21.9%, entirely from AI/ML's secondary-only industry items.
- **Science concentration unchanged:** 5 unique domains, top5 1.00, waiver 0.75 — a multi-week plateau; last week's four scout candidates (unige/empa/wsl/unibe) reached the registry but only as auto-candidates, never promoted, and Science didn't cite them on 07-22.
- **New this week: output-volume creep** on AI/ML (+47%) and News (+27%) — see §L.
- **Feedback cooled:** 25 👍 / 5 👎 → 9 👍 / 6 👎, with News net-negative.

### K. Feed reachability & direct-fetch rate
Portfolio direct-fetch (non-snippet) ratio **~0.97** — every stream far above its floor: news 1.00, ai-ml 1.00, weekend 1.00, science 0.83, **sports 0.40**. The curl-first chain is doing its job for the mature streams.

**Sports is the binding constraint this week.** At 0.40 it clears the 0.30 floor, but only because SRF (curl) carried the two Swiss items; the other three leads went `[via snippet]` because **every official sports primary was walled in the sports sandbox**: `fifa.com`, `letour.fr`, `formula1.com` served Cloudflare JS shells, and `feeds.bbci.co.uk` (BBC Sport) + `en.wikipedia.org` failed `ERR:56` on all four attempts each — even though `feeds.bbci.co.uk` succeeds via proxy in the *news* sandbox (health.json: `ok_proxy 5`). So a young stream with essentially one working direct feed (SRF) is leaning on secondaries by necessity, not choice. This is the deficit the Sunday scout targeted.

**Per-feed walls (both methods, 0 ok this week):** `kyivindependent.com` (9/0), `reuters.com` (3/0 — but `apnews.com` reaches via proxy as the substitute), `en.wikipedia.org` (4/0), `thenationalnews.com` (6/0), `cell.com` (2/0 direct — yet reached via proxy for the Weekend heart item), `axios.com` main (4/0 — `api.axios.com` reaches via proxy). Most have a working alternative already in rotation. `france24.com` looks alarming (31 fail / 6 ok) but the 6 proxy successes mean it is slow/flaky, not walled. **`reach: blocked`-without-snippet violations: 0.** Reach-flips filed for science.org, swissinfo.ch, cell.com, journals.aps.org — two of them *revising* last week's proposals, because this week's writer footers contradicted the earlier reach guesses (see Prior proposals status).

### L. Output volume — the week's real mechanical flag
Word-count means vs the prior week (footer-derived, exact since 2026-07-18):
- **AI/ML 3,572 → up from 2,435 = +47%.** Both editions ran long (07-21: 3,616 w; 07-24: 3,528 w) with ~10–11 full paper writeups plus 4–5 industry items each. AI/ML `repeat_rate` is 0.00, so this is **not** repetition — it is genuinely denser per-item prose (every paper gets a multi-sentence "why it matters"). But +47% with roughly flat story count is well past the +25% guard and is the clearest spend-growth signal in the portfolio.
- **News 1,034 → up from 811 = +27%.** Also over guard; the daily items have grown into denser multi-sentence paragraphs (07-25 ran 903 w across 7 items). Story count per edition is roughly stable (~7–8 citations), so the growth is length-per-item, not more coverage.
- Weekend 6,320 (+19%, under guard), Science 1,277 (−18%), Sports 1,293 (first full week, no prior).

No stream is *both* repetitive and long, so this isn't the classic re-summary-bloat case the levers were built for — but AI/ML at ~3,600 words twice a week is now the single largest recurring output line after Weekend, and it is growing. This is a candidate for a gentle output-cap or paper-count lever (see Patch 1 and `docs/SPIKE-writer-token-levers.md`), framed as a spend-control choice for Rafael, not a quality complaint.

### M. Editorial shape — all green
- **Vendor-PR-lead share (AI/ML):** ~28% (roughly 5 of ~18 news items across both editions lead with a vendor's framing — Qwen 3.8, Poolside, Cisco, Flux 3, OpenAI-Health). Each folds in independent evals or explicit "vendor claim, needs replication" caveats immediately; the HF-breach lead, the Axios US–China policy read, the AISI/CAISI government evaluations, and the Zenity disclosure are all independent-sourced. Under the 40% flag.
- **Aggregator-shape (5 leads sampled):** 0 failures. News Hodeida (DW + UN + chokepoint analysis), News wildfires (DW + SRF + "quadrupled in two days" + CH-heatwave link), AI/ML HF-breach (primary post-mortem + two operator lessons), Weekend Iran headline (AJ count + Brent-$100 framing), Sports World Cup (ESPN + "team of the era" verdict). Every lead adds judgment the source doesn't carry.
- **Personalization (5 sampled):** 0 misses. Swiss fireworks-ban → drought-in-daily-life; Russia-embassy communiqué → neutrality-vote context; US forced-labour tariff → Swiss 12.5% tier vs EU's 15%; Kimi/Qwen self-host → European sovereignty angle; Schwingen → "a genuine national event, not niche." Strong and never forced.

### N. Affiliation element (papers streams)
- **Coverage rate: ~19% `(affiliation not listed)`** across the week's paper bylines (AI/ML 4/21, Weekend 5/26, Science 0/6) — **under the <20% target and a real improvement** from last week's ~30–40%. Note this is organic (this week's picks skewed slightly older, so the arXiv HTML author blocks had rendered), **not** the effect of last week's rm-2 PDF-fallback patch, which remains unapplied — `affiliations.md` still carries no PDF branch. The same root cause is visible in the Weekend Gaps line (four same-day arXiv papers marked not-listed because their HTML author block hadn't rendered), so rm-2 stays relevant for weeks when the batch is fresher. Spot-checked 3 listed bylines against the prose — institutions carried through correctly.
- **Halo audit — no prestige bias.** The unaffiliated / independent-author papers *lead* their sections and get equal depth: H. Jo's "commits before it reasons" probe leads AI/ML 07-21; Intern-BioBreaker (bio red-team) gets the fullest, most sobering writeup in that edition; Relative Value Learning, HiQC and KATA (all "affiliation not listed") sit mid-list among the Google/EPFL/AMD papers with the same "why it matters" treatment. Unaffiliated ≠ downranked. 🟢

## Prior proposals status

From 2026-07-19 (`reader-model-2026-07-19.json`, `registry-2026-07-19.yml`):
- **rm-1** (reader-profile impartiality line) — **applied and verified**: the dated line is present in `reader-profile.md` "Learned preferences". Effectiveness partial, though — the "final"-class framing *recurred* this week (07-20 News 👎), which drives this week's sharpened auto-apply line.
- **rm-2** (affiliations.md: PDF-first-page fallback for same-day preprints) — **pending, not applied.** No PDF branch in `routines/_shared/affiliations.md`. Still relevant (Weekend still marked four fresh preprints not-listed), though the aggregate rate improved organically this week.
- **rm-3** (metrics.py: off-main guard should compare to origin/main) — **pending, not applied.** Confirmed by reproduction: this run again flagged 20 commits off-main (all provably on origin/main); after `git checkout -B main origin/main` the count fell to 0.
- **rm-4** (metrics.py: vitality parser shouldn't flag anchor-free prose) — **pending, not applied.** Confirmed: the parser flagged two false-positive empty sections this week (§D).
- **registry-2026-07-19.yml** — **not applied** (`applied: false`). science.org, cell.com, swissinfo.ch all still `reach: direct`. The four scout candidates (unige/empa/wsl/unibe) appear in `sources/registry.yml` but only as `status: candidate` (auto-created by the scout append / writer probe), **not promoted to probation** as proposed, and Science did not cite them on 07-22. Two of the reach-flips are **revised** in this week's registry proposal because the writer footers contradicted them — swissinfo.ch was cited successfully this week (so the proposed `→ blocked` would have been wrong; revised to `→ proxy`), and science.org succeeded via proxy (so `→ search-only` is revised to `→ proxy`).

## Source scout (Sunday duty)

**Stream picked: Sports** — the worst-deficit stream by the rule's primary key (`new_domains` 4, the lowest; tie-context: `top5_share` 1.00, `waiver_rate` 1.00, `unique_domains` 4). Unlike last week — when Sports was pre-launch with 0 stories and Science was picked instead — Sports now has a real, *addressable* deficit: its official primaries are Cloudflare/ERR:56-walled (§K), leaving SRF the only working direct feed. Science remains the chronic concentration case, but its unmet need is *promotion of last week's already-filed candidates*, not new scouting.

**Candidates appended** to `sources/candidates.jsonl` (4), all `reach: proxy-needed` (the evaluator holds no bearer; writers vet at first citation): **esv.ch** (Eidgenössischer Schwingerverband — the official Swiss wrestling federation, a true primary for the Schwingen coverage and Swiss personalization), **olympics.com** (IOC official newsroom), **uci.ch** (world cycling federation — primary for the Tour coverage where letemps/letour failed), **rts.ch** (RTS Sport — a second Swiss public-broadcaster desk, already proxy-reachable in the news sandbox per `rts.ch ok_proxy 5`).

**Re-probe outcome — blocked by the evaluator egress allowlist, again.** All 9 non-SRF direct probes (4 sports candidates + 5 stale reach entries: science.org, cell.com, swissinfo.ch, journals.aps.org, srf.ch) returned `CONNECT tunnel 403`; only `srf.ch` resolved (200). Identical to last week — the sandbox allows a tiny news-host allowlist and no science/sports hosts. So the reach evidence is again the **writers' own footers** this window, which is what drove the revised science.org/swissinfo.ch flips above.

**Fetches used: 10** (5 candidate probes + 5 stale-reach re-probes), under the ≤20 budget.

## Patch proposals (for human review)

### Patch 1 — Attach the primary URL even when only a secondary is fetchable (AI/ML single-source + reader 👎)
**Target prompt:** `routines/_shared/*.md` sourcing block (AI/ML + Weekend)
**Section affected:** citation / source-selection rule for vendor announcements
**Issue:** AI/ML's single-source rate hit 30.6% (over the 25% stream threshold), concentrated in 07-24 industry items cited to a lone The-Decoder secondary because the vendor primaries were JS-rendered. A reader downvoted the Poolside item specifically: _"this is a secondary source!!! the poolside announcement would be the correct source."_ The writer *did* try the primary; it yielded no text.
**Proposed change:**

> **Before:**
> ```
> When a primary vendor page is unreachable or JS-rendered, cite the reachable
> secondary and tag [single-source].
> ```
>
> **After:**
> ```
> When a primary vendor page is JS-rendered and yields no fetchable text, still
> attach its canonical URL (e.g. poolside.ai/blog/<slug>) as a second link
> alongside the reachable secondary — the reader wants the primary reference even
> when the summary text had to come from the secondary. Tag [single-source] only
> when no primary URL can be identified at all.
> ```

**Why this helps:** Gives the reader the primary link they explicitly asked for at zero extra fetch cost, and lets genuinely-two-source items shed the `[single-source]` tag.
**Risk:** Linking a page the writer couldn't read means the summary still rests on the secondary — keep the `[single-source]`/secondary attribution honest so the reader isn't misled about where the *text* came from.

### Patch 2 — Consider a gentle output-cap on AI/ML (spend control, §L)
**Target prompt:** AI/ML (`routines/src/ai-ml.md`)
**Section affected:** paper-selection / per-item length guidance
**Issue:** AI/ML output grew +47% WoW (3,572-word mean, twice weekly) with flat story count and zero repetition — genuinely dense, high-quality writeups, but the largest recurring spend line after Weekend and rising.
**Proposed change:**

> **Before:**
> ```
> Select the strongest ~10–11 papers; give each a full "why it matters".
> ```
>
> **After:**
> ```
> Select the strongest ~8 papers on a normal week (up to ~10 only on an unusually
> dense release week, and say so in the intro); keep each "why it matters" to a
> single tight paragraph.
> ```

**Why this helps:** Trims the fastest-growing output line toward the quiet-day lever without touching the editorial bar, and makes "dense week" an explicit, visible choice.
**Risk:** Over-tightening could drop a genuinely strong paper on a heavy week; the "up to ~10 when dense" escape hatch and the writer's judgment should govern. This is a spend lever, not a quality mandate — apply only if reducing AI/ML token cost is a priority.

### Patch 3 — (Deferred to human) Re-file the two unapplied metrics.py fixes
**Target:** `tools/evaluator/metrics.py` (rm-3 off-main guard; rm-4 vitality parser)
Both false positives reproduced this week exactly as predicted. These are evaluator-script fixes, not writer-prompt patches, and are carried in `reader-model-2026-07-26.json` (rm-3, rm-4) rather than restated here — flagging only that a second week of confirmed false positives has accrued.

## Reader-feedback → profile proposals

Window sentiment (from the ledger's folded `ev:"feedback"` state; `unconsumed_total` = 0, fold current): **9 👍 / 6 👎, 2 retractions.** By stream: ai-ml 4/2, news 2/4, weekend 3/0. Weekend and AI/ML land net-positive; News is net-negative this week on two pointed reasons.

**Signal 1 — admin-framing / unreliable-narrator (≥2 votes, distinct stories, qualifies for auto-apply).** Two News downvotes with written reasons on distinct stories name the same escalating theme:
1. News 2026-07-20 Iran "final" night: _"you said 'final' night and the US just continued… you need to assume an unreliable narrator from the trump administration."_
2. News 2026-07-21 Swiss forced-labour tariff: _"you forget to mention that there is no legal basis for these new tarifs… context… lying administration."_

This both **reinforces and extends** the 2026-07-19 impartiality line: the "final"-class framing recurred despite that line, and the tariff reason adds a new demand — proactively supply the missing legal/factual context, not merely attribute the loaded word.

**Auto-applied** (appended to `reader-profile.md` "Learned preferences", stamped `applied: true` in `reader-model-2026-07-26.json`):
> ```
> - 2026-07-26: treat US-administration self-characterizations as an unreliable
>   narrator — do not relay the claim flat; attribute/quote the loaded word AND
>   supply the missing legal or factual context the administration omits (2× 👎 on
>   distinct stories: news 2026-07-20 Iran "final" night; news 2026-07-21 Swiss
>   forced-labour tariff "no legal basis… lying administration"). Extends the
>   2026-07-19 impartiality line from attribution to actively adding context.
> ```

**Signal 2 — primary over secondary (1 story, written reason).** The AI/ML 07-24 Poolside 👎 (_"secondary source!!! the poolside announcement would be the correct source"_) is a single-story signal, so it does not clear the ≥2-distinct-stories bar for a learned-preference theme; instead it is folded into **Patch 1** above, which is the actionable fix (attach the primary URL). No `source-weights.yml` change proposed — the-decoder is a legitimate secondary; the issue is missing the primary *link*, not source quality.

The remaining 3 downvotes were bare taps (no reason) → noise, no action. The 2 retractions (one ai-ml, one news) net out prior taps and need nothing.

## Cross-week trend

Steady-state healthy on the dimensions the writers control (leakage 0, direct-fetch ~0.97, T3 0%, identity integrity clean, editorial shape all green). The persistent structural items carry over: **Science source concentration** (unchanged; last week's candidates filed but unpromoted) and **feed walls at the point of use** (now most visible on the young Sports stream). **Affiliation coverage improved** into target (~19%). The genuinely new item is **output-volume creep** on AI/ML (+47%) and News (+27%) — worth watching as a spend line even though quality is not implicated. Reader sentiment cooled and turned News-negative, but on specific, actionable reasons rather than diffuse dissatisfaction.

## Open questions for human review

1. **Output volume (§L).** AI/ML is now ~3,600 words twice a week and growing (+47% WoW), with no repetition — genuinely dense, not padded. Is trimming to ~8 papers / one-paragraph writeups (Patch 2) worth the small risk of dropping a strong paper, or is the current depth the intended product? This is a spend/quality trade only Rafael can set.
2. **Science candidates still unpromoted.** unige/empa/wsl/unibe reached the registry as `candidate` but were never promoted to `probation`, and Science didn't cite them on 07-22 — so the concentration is unchanged for a third week. Promote them (they're Swiss primaries that double as personalization), arm the Science discovery quota, or accept arXiv+Nature as sufficient for a weekly science brief?
3. **Sports reachability.** The stream's official primaries (FIFA, Tour, F1, BBC Sport, Wikipedia) are Cloudflare/ERR:56-walled in its sandbox; this week's scout candidates (esv.ch, olympics.com, uci.ch, rts.ch) need writer-side proxy vetting to confirm they clear that wall. Worth also confirming why `feeds.bbci.co.uk` reaches via proxy in the *news* sandbox but failed all four attempts in the *sports* sandbox — same wrapper, different result.
4. **Stale "git push failed" footers.** Three editions this week (Weekend 07-25, AI/ML 07-21, News 07-25) ended with a "git push failed — retry before session ends" note, yet all three are on origin/main; the News 07-23 commit already had to strip one such stale note manually. The publish path is emitting the note before a later drain/retry lands the push. Since posts are data-only (unpublished), it doesn't reach readers, but it pollutes the archive and the evaluator's own footer-reading — worth a `publish.py` fix to reconcile the note once the push succeeds.
5. The evaluator's **egress allowlist** still blocks direct scout vetting and reach re-probing (only srf.ch resolves). Third week running the scout can only *append* candidates for the writers to confirm. Acceptable, or worth a read-only proxy path for probing?
