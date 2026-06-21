---
layout: single
title: "Weekly Review — 2026-05-03"
date: 2026-05-03T12:00:00+02:00
categories: [evaluator]
---

# Weekly Brief Pipeline Review — 2026-05-03

_Coverage: briefs from 2026-04-27 to 2026-05-03._
_Files read: 2 Overview (05-02, 05-03), 1 Markets (05-02), 1 AI/ML (05-02), 1 Cyber+Papers (05-02), 1 Weekend (05-02), prior review not found._
_Drive duplicates encountered: 1 (Cyber+Papers/2026-05-02 had two versions; took the 20:46 modifiedTime over the 17:11 — older silently superseded)._

> **Deployment-week notice.** All five stream folders were created 2026-05-02 17:06 Europe/Zurich. There is exactly one full production day (Saturday 2026-05-02) plus today's partial Sunday (Overview only — Markets/AI-ML/Cyber-Papers fire later in the day). Cross-week trend analysis is skipped: no prior review exists for last Sunday 2026-04-26. Most metrics below are computed over a single full day; treat thresholds as directional, not statistical.

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains cited            | ~85   | ≥40    | 🟢 |
| T1 citation %                   | ~51% portfolio (range 32–69%) | ≥40% | 🟢 aggregate / 🟡 Overview 05-03 (32%) |
| T3 leakage count                | 0     | 0      | 🟢 |
| Aggregator citations (HN/Reddit/X/…) | 0 | 0    | 🟢 |
| Non-English citation % (portfolio) | ~3% | ≥10%  | 🔴 |
| Link sample pass rate           | unmeasurable (1/8 fetchable; 7/8 = 403) | ≥90% | ⚪ |
| Fabrication count               | 0 (1/1 verifiable claim confirmed) | 0 | 🟢 with caveat |
| Single-source rate (portfolio)  | ~25%  | <20%   | 🟡 / Markets 63% 🔴 |
| Empty section instances         | 1 (Cyber+Papers ML papers, 2026-05-02) | <5 | 🟢 |
| Via-snippet rate (portfolio)    | very high in Overview 05-03 (100%) and Cyber+Papers (≈10/11); tracked | tracked | 🟡 |

## A–J: Detailed findings

### A. Source diversity

Across the six briefs read, the deduplicated domain count is approximately 85 — comfortably above the ≥40 floor even on a deployment-week sample. Top by citation count:

1. arxiv.org — ~12 (mostly Weekend)
2. aljazeera.com — 8
3. nature.com — 6
4. cnbc.com — 6
5. swissinfo.ch — 5
6. sciencedaily.com — 5
7. quantamagazine.org — 4 (Weekend)
8. anthropic.com — 3 (AI/ML)
9. openai.com — 3 (AI/ML)
10. rts.ch — 3

No single domain is at >15% of total citations; arxiv.org is the heaviest at ~10%, almost entirely from the Weekend ML-papers section where high arxiv concentration is structurally expected. **No concentration flag.**

**Tier distribution by stream (from footers):**

| Brief | T1 | T2 | T3 | T1 % |
|---|---|---|---|---|
| Overview 05-02 | 11 | 10 | 0 | 52% |
| Overview 05-03 | 7  | 15 | 0 | 32% |
| Markets 05-02  | 5  | 9  | 0 | 36% |
| AI/ML 05-02    | 14 | 13 | 0 | 52% |
| Cyber+Papers 05-02 | 6 | 5 | 0 | 55% |
| Weekend 05-02  | ~22 | ~10 | 0 | 69% |

Aggregate T1 ≈ 51%, above the 40% target. T3 = 0 across the board, exactly as the policy demands. The single soft point is **Overview 2026-05-03 at 32% T1** — directly attributable to the 100% via-snippet wall hit that morning (see § Section A bottom and § B/C below). When a writer cannot fetch ECB/WHO/Nature/SCMP/AJ originals, it falls back to T2 secondaries; that is the system working as designed, but it is worth keeping eyes on.

**Geographic spread:** Switzerland (swissinfo, RTS, Le Temps, The Local, SNB, EDA, FedPol), Qatar (Al Jazeera), Hong Kong/China (SCMP), Indonesia (Jakarta Post), Thailand (Bangkok Post), Japan (Diplomat), US (CNBC, NBC, NPR, CNN, Fortune, SCOTUSblog, Federal Reserve, SEC), UK (AISI, The Register), EU (ECB, CERT-EU), France (Euronews). Roughly 12 distinct countries-of-origin in news sections — healthy.

**Linguistic diversity (the actual problem):** Only RTS (3 cites) and Le Temps (1 cite) provide non-English content. That is **~4 cites out of ~120 total ≈ 3.3%**, against the ≥10% target. No DE source (NZZ, Handelszeitung, FAZ, Spiegel, Der Standard) was cited; no IT (Corriere, Repubblica, Il Sole 24 Ore); no PT/ES; no JP/KR/CN despite heavy China and Iran coverage. The Markets footer explicitly notes "DE/FR consulted via search snippets only — no direct Handelszeitung/Le Temps/NZZ citations retrieved" — i.e., the writer is aware. This is a structural shortfall; see Patch 4.

### B. Aggregator leakage (critical violation)

Searched all six briefs for: news.ycombinator.com, lobste.rs, reddit.com, twitter.com, x.com, mastodon.social, threads.net, bsky.app.

**Hits: 0.** The Weekend brief explicitly notes "HN/Reddit used to surface topics only; all citations are T1/T2." Policy-clean. No patch needed in this dimension.

### C. Link health (sample-based)

Attempted 8 random fetches: 2 from Overview, 1 Markets, 1 AI/ML, 1 Cyber+Papers, 1 Weekend, plus 1 ECB and 1 arXiv link.

| URL | Result |
|---|---|
| swissinfo.ch (Overview 05-02) | HTTP 403 |
| arxiv.org/abs/2604.21751 (Overview 05-02) | HTTP 403 |
| aljazeera.com (Overview 05-03) | HTTP 403 |
| ecb.europa.eu press release (Markets) | HTTP 403 |
| mistral.ai news page (AI/ML) | HTTP 403 |
| microsoft.com/security/blog (Cyber+Papers) | **200 OK** |
| quantamagazine.org (Weekend) | HTTP 403 |
| simonwillison.net (Weekend) | HTTP 403 |

**Pass rate: 1/8 = 12.5%, but 7 of those 7 failures are HTTP 403, not 404 / not invalid URL / not server error.** This is the same infrastructure wall every writer flagged in their own gap footers. **Reporting as unmeasurable.** A 12.5% pass rate is not a quality signal — it is a sandbox-network signal.

**Per-stream pass rate:** all streams were uniformly hit; no stream's URLs were systematically broken vs another's.

**Fabrication spot-check:** the one fetch that succeeded — Microsoft's CVE-2026-31431 page — verbatim confirmed the cited claim (CVSS 7.8, AF_ALG mechanism, distros affected, CISA KEV addition, mitigation guidance). Sample is too small to draw a fabrication-rate, but the one anchor we have is clean. **No fabrication flag.**

### D. Section vitality

Items per section across the six briefs (rough count):

| Stream | Section | Items |
|---|---|---|
| Overview 05-02 | CH/Vaud | 4 |
| Overview 05-02 | World politics | 5 |
| Overview 05-02 | Science | 4 |
| Overview 05-02 | ML arXiv | 3 |
| Overview 05-02 | Markets pre-open | 3 |
| Overview 05-03 | CH/Vaud | 4 |
| Overview 05-03 | World politics | 3 |
| Overview 05-03 | Science | 4 |
| Overview 05-03 | ML arXiv | **1** |
| Overview 05-03 | Markets pre-open | 3 |
| Markets | Markets full day | 7 |
| Markets | US morning | 4 |
| AI/ML | Lab blogs | 6 |
| AI/ML | Models/datasets | 4 |
| AI/ML | Benchmarks | 5 |
| AI/ML | Industry/funding | 5 |
| AI/ML | Apple Silicon | 2 |
| Cyber+Papers | Cybersecurity | 5 |
| Cyber+Papers | ML papers | **0 (skipped)** |
| Weekend | Headlines | 5 |
| Weekend | ML papers | 9 |
| Weekend | Fundamental science | 5 |
| Weekend | Models released | 5 |
| Weekend | Apple Silicon | 3 |
| Weekend | Bio | 5 |
| Weekend | Data science | 3 |
| Weekend | Essays | 4 |
| Weekend | Cyber research | 4 |
| Weekend | Cross-cutting threads | 4 |

Two soft points worth flagging even on this small sample:

- **Overview 05-03 / ML arXiv batch — 1 item.** The brief itself explains: arXiv does not announce on weekends, and the visible Friday batch was further degraded by 403s on listing pages. Structural for Sunday morning brief. Not a writer fault; mention as "Sunday note" so the reader doesn't read it as failure.
- **Cyber+Papers 05-02 / ML papers — 0 items, section explicitly skipped.** Writer cited "arXiv list pages 403; HF papers feed empty." The skip is honest. But the Weekend brief covered ~9 ML papers in the same window using arXiv abstracts referenced via snippet — which means the discovery method exists and works, just not via the listing path. See Patch 3.

Neither section has been empty ≥3 times — there isn't enough data for that yet — but Cyber+Papers/Papers is the single highest-risk section to watch as the week progresses.

### E. Coverage gap recurrence

Clustering recurring gaps across the six gap footers:

1. **arxiv.org / huggingface.co/papers HTTP 403 on listing pages** — appears in Overview ×2, Cyber+Papers, AI/ML, Weekend. **5 of 6 briefs.** Universal.
2. **Major news sites (Reuters, AP, FT, BBC, Le Monde, Spiegel, NZZ) blocked** — explicit in Overview 05-03 and Markets footers; implicit elsewhere.
3. **Lab blog 403s** (anthropic.com, openai.com, deepmind.google, Mistral) — AI/ML footer.
4. **CISA, Quanta Magazine direct fetches 403** — Cyber+Papers, Weekend.
5. **Government / journal pages 403** (nature.com, science.org, who.int, snb.ch) — Overview ×2.

Every recurring gap cluster traces back to the same cause: the writers' fetch sandbox cannot reach most primary sources. They fall back to via-snippet citations or T2 coverage. This is **infrastructure, not prompt design**, with one interesting exception: AI/ML and Cyber+Papers respond differently to the wall (AI/ML still triangulates and fills sections; Cyber+Papers gives up on the Papers section entirely). See Patch 3.

### F. Triangulation rate

Counting `[single-source]` tags vs total items per stream:

| Stream | Single-source items | Total items | Rate |
|---|---|---|---|
| Overview 05-02 | 5 | 19 | 26% |
| Overview 05-03 | 2 | 15 | 13% |
| Markets 05-02  | **5** | **8** | **63%** |
| AI/ML 05-02    | 5 | 27 | 19% |
| Cyber+Papers 05-02 | 1 | 5 | 20% |
| Weekend 05-02  | ~7 | ~30 | ~23% |

Portfolio: ≈25/104 = **~24%** vs <20% target. Slightly over. The Weekend brief's 23% is borderline acceptable for a synthesis brief that includes by-design single-source items (essays, individual preprints).

**Markets is the outlier at 63%** — five of eight items carry `[single-source]`: SMI close, DAX/CAC close, FTSE close, USD/CHF, gold price. These are precisely the kinds of facts that should triangulate trivially against a second financial data feed (Reuters, FT, MarketWatch, Investing.com). The writer's footer concedes "EUR/CHF rate not directly verified via WebFetch (ECB page cited but not fetched); USD/CHF from single aggregator source; gold price from single aggregator." See Patch 1.

### G. Tag discipline

- **`[preprint]`** — used on every arXiv ID-bearing item across Overview, AI/ML, Weekend. Sampled 5 (2604.21751, 2604.12634, 2604.19775, 2604.19087, 2604.17931, 2604.23445): all genuinely arXiv preprints, all properly tagged. ✅
- **`[vendor PR]`** — used in AI/ML on Mistral, Anthropic ×3, OpenAI, Google DeepMind, DeepSeek docs, Mistral Medium 3.5, Ollama. Sampled 5: all genuine vendor announcement pages. ✅
- **`[disputed]`** — never used. Count: 0. Not an issue per se; nothing this week qualified.
- **`[via snippet]`** — **inconsistent across streams**:
  - Overview 05-02: 1 instance
  - Overview 05-03: ~22 instances (every citation tagged)
  - Markets 05-02: 0 instances (despite footer admitting "EUR/CHF rate not directly verified via WebFetch")
  - AI/ML 05-02: 0 inline instances (footer acknowledges 403s but does not tag inline)
  - Cyber+Papers 05-02: ~10 instances
  - Weekend 05-02: 0 inline instances (footer: "arxiv abstract pages 403... details sourced via search engine result snippets")

This is a real discipline gap: under identical 403 conditions, three writers tag inline (Overview 05-03 — exemplary, Cyber+Papers — good) and three do not. The reader can't tell from a clean Markets brief that the FX numbers are aggregator-snippet-derived without reading the footer. See Patch 2.

### H. Topic balance (Weekend brief only)

Weekend ML papers section (9 papers):

| Theme | Papers |
|---|---|
| RL methodology | LiteResearcher, PIRL, "Errors Beneficial", Pass@(k,T), Test-Time Compute Allocation = **5** |
| Architecture (SSM/Transformer) | Mamba-3, Attention-to-Mamba = **2** |
| Hardware/efficiency | Apple Silicon NPU MoE = **1** |
| Vision/applied | Industrial Anomaly Detection = **1** |

That is **56% RL** in this week's Weekend ML papers. Without sight of the prompt's stated bias targets I cannot measure deviation precisely, but if the target was "~40% RL" (a common framing for a balanced ML brief), this week is +16 percentage points — past the 10-point flag threshold. RL was unusually dominant in the actual research output this week (multiple independent RLVR / agent-RL / reward-model papers landed simultaneously), so this may reflect reality rather than writer bias. Worth checking against the prompt's stated mix.

Fundamental science (5 items): mathematics ×1, palaeontology ×1, condensed-matter physics ×1, neuroscience ×1, NeuroAI roadmap ×1. Spread is healthy; no flag.

### I. Repetition detection

Story clusters across consecutive days:

- **Iran / Hormuz blockade** — Overview 05-02 (UAE leaves OPEC, US troops Germany), Overview 05-03 (Trump "like pirates", Tehran proposal rejected), Markets 05-02 (war day 64), Weekend 05-02 (Hormuz contested, food emergency). Four mentions; **each adds development** (UAE OPEC exit → Tehran proposal → Trump rejection → food emergency). Healthy story progression, not stuck.
- **US troops withdraw from Germany** — Overview 05-02 (announced 5,000), Overview 05-03 (Trump signals deeper cuts; Germany +75K offset), Markets 05-02 (Pentagon confirmation, Democrats criticism), Weekend 05-02 (single mention as background). **Each adds development.** Healthy.
- **CVE-2026-31431 "Copy Fail"** — Cyber+Papers 05-02 (full CVE writeup), Weekend 05-02 (deeper analysis with mitigation script, threat-chain context). The Weekend treatment escalates with cross-cutting context (Cloudflare "logging in" thesis, Lightning supply chain). Good vertical depth.
- **Trump–Xi summit (May 14–15)** — Overview 05-03 only. No repetition.
- **Vaud Dittli affair** — Overview 05-02 (background, Nordmann appointment), Overview 05-03 (investigation findings, "trust compromised"). Two mentions, each new info.

**No stuck-story flags.** Repetition is appropriate vertical coverage, not idle restating.

### J. Cross-week trend

**Skipped — no prior review found.** The Reviews folder contains two files dated 2026-05-02 (both pre-deployment test runs of this evaluator) but no review for the previous Sunday 2026-04-26. First substantive cross-week trend will be possible at next week's run.

## Patch proposals (for human review)

Five patches in priority order.

### Patch 1 — Markets: require ≥2 sources for index closes and FX

**Target prompt:** Markets
**Section affected:** "Markets — full day" (and any pre-open snapshot in Overview)
**Issue:** Markets 05-02 ran 63% single-source — five of eight items, including SMI/DAX/CAC/FTSE closes, USD/CHF, and gold price. These are easily triangulated facts; the writer's own footer admits aggregator-only sourcing.
**Proposed change:**

> **Before:** _(approximate, based on the brief's behaviour)_
> ```
> Cite a representative source for each price quote.
> ```
>
> **After:**
> ```
> For every numeric price (index close, FX rate, commodity), cite at least
> two independent sources OR mark the item explicitly with `[single-aggregator]`
> in addition to `[single-source]`. The two sources must not both be aggregator
> redistributors of the same primary feed (e.g. Yahoo Finance + Investing.com
> both pulling Refinitiv counts as one). When only one source is available,
> downgrade the precision in the brief — write "SMI ~13,140 (+0.8%)" rather than
> "SMI 13,136.27 (+0.80%)".
> ```

**Why this helps:** Numeric precision in markets briefs implies a level of verification that single-aggregator sourcing cannot deliver. Either triangulate, or honestly de-precision.
**Risk:** Could empty the Markets section on holidays / closed-market weekends when only one feed is reachable. Mitigated by the explicit `[single-aggregator]` tag and de-precisioning escape hatch.

### Patch 2 — Uniform `[via snippet]` tagging across all five writers

**Target prompt:** Morning Overview, Markets, AI-ML, Cyber-Papers, Weekend (apply same clause to all)
**Section affected:** Citation rules / tag conventions
**Issue:** Overview 05-03 and Cyber+Papers tag `[via snippet]` inline on every snippet-derived citation, making degraded sourcing visible. Markets, AI/ML, and Weekend hit identical 403 walls but tag nothing inline (only acknowledge in the footer). The reader can't see citation quality from the brief body.
**Proposed change:**

> **Before:** _(absent in 3 of 5 prompts; present but underspecified in 2 of 5)_
> ```
> Note in the gap footer if direct fetches failed.
> ```
>
> **After:**
> ```
> Tag every citation that was NOT obtained from a successful direct fetch
> with the inline marker `[via snippet]`, immediately before the link.
> A "successful direct fetch" means an HTTP 200 response whose content was
> read end-to-end. Snippet-derived citations include search-engine result
> excerpts, cached fragments, MCP partial responses, and any case where the
> publishing URL itself returned 4xx/5xx.
>
> In the gap footer, also report two counts: "Direct fetches: N" and
> "Via-snippet citations: M".
> ```

**Why this helps:** Aligns the three lax writers with the two strict ones; gives the reader a one-glance signal of citation provenance and exposes degraded-mode runs.
**Risk:** Cosmetic noise in briefs where the wall happens to be 100% (every line gets the tag). Acceptable cost — that's exactly the day on which the reader most needs to see it.

### Patch 3 — Cyber+Papers: fallback discovery chain when arXiv listing 403s

**Target prompt:** Cyber-Papers
**Section affected:** "ML research — second arXiv batch"
**Issue:** Cyber+Papers/2026-05-02 skipped the entire ML papers section because arxiv.org/list/* returned 403. The Weekend brief, hitting the same 403 wall, surfaced ~9 papers via arXiv abstract URLs (referenced through search-engine snippets and HuggingFace papers feed). The discovery method works; Cyber+Papers' prompt evidently does not specify it.
**Proposed change:**

> **Before:** _(implied by behaviour)_
> ```
> Pull the second arXiv batch from arxiv.org/list/cs.LG, cs.AI, cs.CL, cs.CV, stat.ML.
> ```
>
> **After:**
> ```
> Pull the second arXiv batch from arxiv.org/list/{cs.LG,cs.AI,cs.CL,cs.CV,stat.ML}.
> If those listing pages return 4xx, fall back in order to:
>   1. huggingface.co/papers (daily feed)
>   2. Semantic Scholar API (api.semanticscholar.org/graph/v1/paper/search)
>   3. OpenReview recent submissions
>   4. Search-engine queries scoped to site:arxiv.org for the target date,
>      following snippet-derived arXiv IDs to abstract URLs.
> Do NOT skip the section unless all four fallbacks return zero results.
> If only fallbacks succeeded, mark the section header with
> "(via fallback discovery — not full batch)".
> ```

**Why this helps:** Removes the asymmetry between AI/ML + Weekend (which have informal fallbacks) and Cyber+Papers (which gives up). Empty-section preservation matters for weekly trends.
**Risk:** Fallback discovery is noisier than canonical listings — may surface stale or off-topic papers. Mitigated by the section header marker that flags the brief as fallback-derived.

### Patch 4 — Seed DE/IT/JP source list to lift portfolio non-English rate

**Target prompt:** Morning Overview (primary), Markets (secondary), Weekend (secondary)
**Section affected:** Source-discovery seed list / "Languages drawn from" footer
**Issue:** Portfolio non-English rate is ~3% (only RTS + Le Temps in FR). No DE outlet appears across any brief despite heavy Iran/Germany/EU/Switzerland coverage where DE-language primary sourcing exists (NZZ, Tages-Anzeiger, Handelszeitung, FAZ, Spiegel, Der Standard). Markets footer explicitly acknowledges "DE/FR consulted via search snippets only — no direct Handelszeitung/Le Temps/NZZ citations retrieved."
**Proposed change:**

> **Before:** _(implied)_
> ```
> Aim for ≥10% non-English citations.
> ```
>
> **After:**
> ```
> Aim for ≥10% non-English citations portfolio-wide. Seed the discovery
> step with these candidate outlets explicitly:
>
>   DE: nzz.ch, tagesanzeiger.ch, handelszeitung.ch, faz.net, spiegel.de,
>       derstandard.at, srf.ch
>   FR: rts.ch, letemps.ch, lemonde.fr, lefigaro.fr, latribune.fr
>   IT: corriere.it, repubblica.it, ilsole24ore.com, rsi.ch
>   JP: nikkei.com, asahi.com, japantimes.co.jp
>   PT/ES: elpais.com, eldiario.es, publico.pt
>
> When a Swiss/German/Iran/EU story is in scope, you MUST attempt at least
> one DE-language source before falling back to English coverage of the same
> story. If the DE source 403s, cite it [via snippet] rather than dropping it.
> ```

**Why this helps:** A seeded list is concrete enough to act on in the discovery step and survives the via-snippet wall.
**Risk:** Could push toward token-effort non-English citations (one DE link per brief regardless of relevance). Mitigated by the topical trigger ("when a Swiss/German/Iran/EU story is in scope").

### Patch 5 — Degraded-mode banner when via-snippet rate exceeds 70%

**Target prompt:** All five (consistent header rule)
**Section affected:** Top-of-brief banner / metadata block
**Issue:** Overview 05-03 ran on 100% via-snippet sourcing — no direct fetches succeeded. The footer reports it; the body reads as a normal brief. A reader skimming the body cannot tell that this morning's brief has materially weaker citation provenance than yesterday's.
**Proposed change:**

> **Before:** _(no degraded-mode signal)_
> ```
> _Generated {timestamp}. Coverage window: {start} to {end}._
> ```
>
> **After:**
> ```
> _Generated {timestamp}. Coverage window: {start} to {end}._
>
> {if via-snippet citations / total citations > 0.70:}
> > **⚠ Degraded sourcing — {N}% of citations via snippet only.**
> > Direct fetches blocked or unavailable this morning. Confidence in
> > numeric facts and quote attributions reduced; treat all figures as
> > snippet-paraphrased unless verified independently.
> {endif}
> ```

**Why this helps:** One-glance honesty about brief reliability on bad-network mornings. Pairs naturally with Patch 2 (inline `[via snippet]` tags).
**Risk:** None I can see — the threshold is conservative.

## Cross-week trend

Skipped — no prior review for last Sunday (2026-04-26). First trend deltas will be available next week.

## Open questions for human review

These the user resolves; I cannot decide them mechanically.

- **Weekend ML-papers RL share at 56%.** Reflects the actual research wave this week (multiple RLVR/agent-RL papers landed simultaneously) or writer drift toward RL preference? Worth checking the Weekend prompt's stated topic-bias percentages and deciding whether 56% RL was warranted by reality this week.
- **Cyber+Papers had two versions of 2026-05-02 (17:11 and 20:46) in Drive.** Re-run during deployment? If the writer routine ever re-runs intentionally same-day, the duplicate-handling rule continues to work; if not, it might indicate scheduler misconfiguration worth tracing.
- **AI/ML brand mix — 6 Anthropic mentions, 5 OpenAI, 2 Mistral, 2 Google, 1 DeepSeek, 1 Zhipu.** This is one day; across a week the mix may even out, but worth watching whether the AI/ML prompt's discovery is favouring Anthropic blog reads (which is what your fetch sandbox can probably reach least often, ironically).
- **Patches 1 and 4 expand the Markets and Overview prompts respectively.** If they conflict with the sourcing charter's brevity targets, Patch 4's DE/IT/JP/PT/ES list could be moved to a shared seed-list document referenced by the prompts rather than inlined.
- **Cyber+Papers ML papers section (Patch 3 fallback chain).** If the underlying intent of the section is "second batch as it actually appears on arXiv listing pages today", a fallback discovery chain changes the section's contract. You may prefer it to remain section-skipped on bad days rather than fallback-filled. Your call.

---

_Length: ~3,400 words. Coverage window included one Sunday partial run; full per-stream metrics will stabilise next week as the pipeline accumulates a full 7 days of data._
