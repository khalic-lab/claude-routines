---
layout: single
title: "Weekly Pipeline Review — 2026-06-14"
date: 2026-06-14T12:00:00+02:00
categories: [evaluator]
published: true
---

_Coverage: briefs from 2026-06-08 to 2026-06-14._
_Files read: 7 morning, 6 AI/ML, 6 cyber, 1 weekend (2026-06-13), prior review not found (last evaluator 2026-05-24)._

The pipeline is warm and producing on every stream. The portfolio-level numbers are
healthy — but they **mask one badly broken stream**. This week's binding-constraint finding
(dimension K) is unambiguous: the **AI/ML brief is failing the feed-first recovery**. It runs a
mean direct-fetch ratio of **0.12** against a 0.40 target, leans on 71 `[via snippet]` citations
across six days, and is the *only* stream that emits no `Feeds hit` line at all — even though
arXiv RSS/Atom is proven reachable via curl every single day in the Overview and Cyber streams.
Everything else (Overview 0.76, Cyber+Papers 0.93, Weekend 0.81) is comfortably above target and
the curl-first patch is clearly doing its job there.

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains cited            | ~85   | ≥40    | 🟢 |
| T1 citation %                   | ~50%  | ≥40%   | 🟢 |
| T3 leakage count                | ~9    | 0      | 🔴 |
| Non-English citation % (portfolio) | ~12.5% | ≥10% | 🟢 |
| Link sample pass rate           | feeds 100% / HTML walled | ≥90% | 🟡 |
| Fabrication count               | 0     | 0      | 🟢 |
| Single-source rate (portfolio)  | ~17% of citations (item-level higher) | <20% | 🟡 |
| Empty section instances         | <5    | <5     | 🟢 |
| Direct-fetch ratio (portfolio)  | 0.70  | ≥0.35  | 🟢 |
| Direct-fetch ratio (Overview)   | 0.76  | ≥0.30  | 🟢 |
| Direct-fetch ratio (Cyber+Papers) | 0.93 | ≥0.50 | 🟢 |
| Direct-fetch ratio (AI/ML)      | **0.12** | ≥0.40 | 🔴 |
| Feeds with >50% fail rate       | 0 (with caveats) | 0 | 🟢 |
| Citations to confirmed-blocked domains without [via snippet] | ~1 (swissinfo, bundled) | 0 | 🟡 |
| curl vs WebFetch advantage on feeds | curl wins decisively | curl wins | 🟢 |

## A–K: Detailed findings

### A. Source diversity
~85 unique domains cited across 425 citation links — well above the ≥40 floor. Top 10 by count:
`arxiv.org` (81), `nvd.nist.gov` (60), `nature.com` (41), `aljazeera.com` (36), `letemps.ch` (27),
`srf.ch` (26), `hf.co` (10), `cnbc.com` (10), `github.com` (7), `ecb.europa.eu` (7).

**Concentration:** arXiv accounts for 81/425 = **19%**, over the 15% threshold — flag, but benign:
it's the primary preprint feed feeding both Cyber+Papers and the Weekend science sections, so
concentration here is the architecture working, not a sourcing failure. `nvd.nist.gov` at 14% is
similar (CVE primary source).

**Tier distribution:** T1 ≈ 50% (arXiv, NVD, Nature, ECB, CISA, admin.ch, gov.uk, consilium.europa,
anthropic.com, vendor advisories — Broadcom/Oracle/Red Hat/Fortinet/Ivanti/Apache), comfortably ≥40%.
T3 ≈ 9 citations and is the problem: `aiweekly.co` (2), `aitoolsrecap.com`, `codersera.com`,
`techtimes.com`, `techstartups.com`, `swfte.com`, `benchlm.ai`, `releasebot.io` — **all in the AI/ML
stream**, all symptoms of the same snippet-dependence (see K). T3 should be 0%.

**Linguistic:** ~53 non-English citations (`letemps.ch` FR 27, `srf.ch` DE 26) ≈ 12.5% portfolio-wide,
above the ≥10% floor — entirely carried by Cyber+Papers' Swiss/French sourcing. Overview and AI/ML are
near-monolingual.

**Geographic:** ~9 countries represented in news sections (CH, US, Qatar/AJ, UK, EU institutions,
France, Ireland, plus arXiv international). Healthy.

### B. Aggregator leakage
**Clean.** Zero hits for `news.ycombinator.com`, `lobste.rs`, `reddit.com`, `twitter.com`, `x.com`,
`mastodon.social`, `threads.net`, `bsky.app` across all window briefs. 🟢

### C. Link health (sample-based)
Feed probes via curl from this environment: arXiv RSS `cs.LG` → **200**, NVD CVEs JSON 2.0 → **200**,
CISA KEV JSON → **200**. **No feed regression** — the public feeds resolve cleanly here, confirming
the writers' curl-first results are real, not sandbox artifacts. Article-page sample:
`aljazeera.com` 200, `srf.ch` 200, `arxiv.org/abs/...` 403, `nature.com` 303, `cnbc.com` 403.
The 403/303 pages are access-walled HTML, not broken links — the content exists and the briefs
correctly route around them. **No fabrications detected** in spot-checks; the briefs are
conspicuously careful ("where a number isn't in a source I can fetch, I don't state one"). Pass rate
is therefore best read as: feeds 100% reachable, HTML article pages consistently walled — marked 🟡
because the HTML half is unmeasurable by design, not because anything is broken.

### D. Section vitality
No fully empty sections observed. On quiet days the writers push held items into the Gaps footer
rather than leaving a section blank (e.g. AI/ML 06-09 "a genuinely quiet day," 06-13 "no major
foundation-model drop"). Empty-section instances <5. 🟢

### E. Coverage gap recurrence
Three structural (≥3×) clusters:
1. **Market-data HTML wall** — by far the largest: CNBC (12), generic "market"/"intraday"/"CHF"
   (13), Reuters (3), Yahoo (2), TradingEconomics (2). Intraday equity/FX figures are blocked nearly
   every Overview run because providers 403. Structural — needs a reachable market source or a firm
   "ECB-fix + `[via snippet]`" rule (see Patch 3).
2. **Nature article HTML / missing abstracts** — `Nature article` (4), `abstract` (5), plus
   `natastron.rss` (7) and `nphys.rss` (6) intermittent failures. Nature *feeds* are reachable but
   carry no abstracts and the article pages 403, so Nature items stay title-level. The Weekend brief
   already mitigates by leaning on arXiv astro-ph/physics cross-lists.
3. **MLX/GitHub release staleness** (3) — release pages return stale snapshots to the sandbox.

### F. Triangulation rate
74 `[single-source]` tags (Overview 16, AI/ML 18, Cyber 30, Weekend ~10). As a fraction of citations
that's ~17% (under 20%), but item-level it runs higher. The Cyber concentration (30) is mostly NVD/CISA
**primary-authoritative** items where triangulation isn't meaningful (a CVE *is* the source of truth) —
so the cyber number is benign. The AI/ML 18 is more concerning because it compounds the snippet
problem: snippet-sourced *and* single-sourced. Marked 🟡 overall.

### G. Tag discipline
- `[preprint]`: 86 uses; Weekend sample 8/8 arXiv items correctly tagged. 🟢
- `[vendor PR]`: 13 uses — present and applied to vendor announcements. 🟢
- `[disputed]`: 10 uses, appropriately (oil-price direction 06-12, Ticino gold processor, an
  unwritten executive order flagged pending the full text). 🟢
- `[via snippet]`: **104 total — Overview 20, AI/ML 71, Cyber 8.** This is the tell. With curl-first
  feeds, via-snippet should be *dropping*. Cyber (8, mostly 0/run) and Overview (20) are fine; AI/ML's
  71 is flat-high and rising — proof that feeds are simply not being used in that stream. 🔴 (AI/ML).

### H. Topic balance (Weekend brief)
The 2026-06-13 weekend brief runs **8 ML/AI papers** and **8 fundamental-science papers** — a clean
~50/50 split (science covers sphere packings, Elekes–Rónyai, high-z CO detection, Hubble tension,
primordial black holes, high-frequency GW, quantum-logic codes, nonlocality-without-entanglement). No
deviation >10pp from a balanced target. Dedup is visibly working: the six strongest 06-11 ML papers
already run in the dailies were deliberately excluded and logged in Gaps. 🟢

### I. Repetition detection
Dedup is catching repeats well. The **MiniMax-M3** thread ran three consecutive AI/ML days (06-10
"no repo yet" → 06-11 "org tops out at M2.7" → 06-12 "card appeared, MXFP8 + GGUF") — borderline, but
each day carried a genuinely new fact, so it reads as development not repetition. SpaceX/xAI IPO and
several CVEs (Check Point, LiteLLM, Ivanti Sentry) were explicitly flagged REPEAT and dropped via
dedup. 🟢

### J. Cross-week trend
**No prior review in window** — the expected 2026-06-07 evaluator does not exist; the last evaluator
on disk is 2026-05-24. So no quantitative trend line this week. Worth noting on its own: the evaluator
itself appears to have skipped at least one scheduled Sunday (2026-06-07), which is a pipeline-health
signal independent of the briefs.

### K. Feed reachability and direct-fetch rate — **primary lens**

**Per-stream direct-fetch (N direct / M via-snippet per day → ratio):**

| Stream | Per-day (direct/snippet) | Mean ratio | Min | Max | Week snippet total |
|--------|--------------------------|-----------|-----|-----|--------------------|
| Overview | 12/2, 12/2, 12/2, 7/6, 8/6, 10/2, 7/2 | **0.76** | 0.54 | 0.86 | 22 |
| AI/ML | 0/10, 2/11, 1/8, 1/13, 4/6, 0/7 | **0.12** 🔴 | 0.00 | 0.40 | 55 |
| Cyber+Papers | 25/0, 18/0, 27/0, 13/7, 11/0, 13/1 | **0.93** | 0.65 | 1.00 | 8 |
| Weekend | 30/7 | **0.81** | — | — | 7 |

Portfolio: 213 direct / 305 total = **0.70**.

The AI/ML stream is the entire story. It posted **0 direct fetches on 06-08 and 06-13**, and its only
direct fetches all week were Hugging Face Hub API queries (MiniMax-M3 card existence checks, a couple
of model cards) plus one arXiv abstract on 06-12. It is sourcing the *actual AI news* (model releases,
benchmarks, policy) almost entirely from the-decoder, AI Weekly, Artificial Analysis, VentureBeat and
assorted T3 blogspam via snippet. Critically, **the AI/ML footer never includes a `Feeds hit` line**,
so the writer isn't even attempting (or isn't reporting) feed fetches — unlike Overview and Cyber,
which both pull arXiv RSS/Atom via curl every day successfully.

**Per-feed reachability (aggregated, with method):**

| Feed | Result | Notes |
|------|--------|-------|
| arXiv RSS / Atom API | ok via curl (all days) | occasional "empty — weekend skipDays" (not a failure) |
| NVD JSON | ok via curl (all days) | rock-solid |
| CISA KEV JSON | ok via curl (all days) | rock-solid |
| Quanta RSS | ok via curl | one article via WebFetch fallback |
| Nature nature.rss / nphys.rss / nm.rss | ok via curl (mostly) | nphys/nm 303→403 once (06-11) |
| Nature natastron.rss | flaky | failed 06-11 and Weekend (2 attempts); ok-but-empty 06-13 |
| ECB FX XML | ok via curl (all days) | rock-solid |
| Semantic Scholar API | ok via curl | |
| simonwillison.net Atom | fail — 403 (06-14) | single attempt |
| APS PRL RSS | fail — 403 (06-11) | single attempt |
| CNBC / TradingEconomics / Yahoo / Nature article HTML | fail — 403/303 | confirmed HTML wall, expected |

**Feeds with >50% fail rate:** none with meaningful sample size. `natastron.rss` is the flakiest core
feed (~2 fails of ~8 attempts, still <50%); `simonwillison.net` and `APS PRL` each failed their single
attempt but aren't load-bearing. 🟢 with a watch on natastron.

**Method comparison:** **curl wins decisively.** Essentially every feed success this week is
`{ok via curl}`; WebFetch appears only as a fallback for article HTML (Quanta article, two Al Jazeera
articles). The curl-first patch is unambiguously doing its job in Overview, Cyber and Weekend. The
AI/ML failure is **not** an egress-proxy problem — the same feeds work for the other streams — it is
that the AI/ML *prompt* isn't pointed at the feeds.

**Confirmed-unavailable domains cited:** `swissinfo.ch` (4) and `finance.yahoo.com` (1). The Yahoo cite
is correctly `[via snippet]`. The swissinfo cites are mostly tagged `[via snippet]`, but at least one
appears inside a multi-source bundle without its own explicit tag — minor, flagged 🟡 (Patch 5).

**Healthy-range verdict:** Overview ✅ (0.76 ≥ 0.30), Cyber+Papers ✅ (0.93 ≥ 0.50),
Weekend ✅ (0.81 ≥ 0.30), **AI/ML ❌ (0.12 ≪ 0.40)**.

## Patch proposals (for human review)

### Patch 1 — AI/ML: adopt curl-first feeds + emit a Feeds-hit line
**Target prompt:** AI-ML
**Section affected:** Sourcing / Coverage footer
**Issue:** AI/ML runs a 0.12 direct-fetch ratio with 71 via-snippet citations and emits no
`Feeds hit` line, despite arXiv RSS/Atom and the HF Hub API being proven curl-reachable daily in the
other streams. This is the single highest-severity finding.
**Proposed change:**

> **Before:**
> ```
> [AI/ML sourcing section — currently relies on news/snippet discovery for model
> releases and benchmarks; no explicit feed-fetch step; footer reports only
> "Direct fetches: N | via-snippet citations: M".]
> ```
>
> **After:**
> ```
> Before drafting, fetch these via Bash{curl} FIRST (WebFetch only as fallback):
>   - arXiv Atom API + RSS: cs.LG, cs.CL, cs.AI, cs.CV, stat.ML
>   - Hugging Face Hub API for any model release you intend to report
>   - Semantic Scholar API for paper metadata
> Cite the feed item directly; reserve [via snippet] for items no feed/API covers.
> Footer MUST include a "Feeds hit (with reachability and method)" line listing
> each feed as {ok via curl} / {ok via WebFetch} / {fail — HTTP NNN}, same format
> as the Overview and Cyber+Papers briefs.
> ```

**Why this helps:** Brings AI/ML to parity with the streams where curl-first already works, directly
lifting the binding-constraint metric and making the stream's feed health observable.
**Risk:** arXiv/HF coverage of *commercial* model releases (OpenAI/Anthropic launches) is thin, so some
genuine news will still be snippet-sourced — the ratio won't hit 0.93 like Cyber, but 0.40 is reachable.

### Patch 2 — AI/ML: T3 source deny-list + preferred fallbacks
**Target prompt:** AI-ML
**Section affected:** Source tiering
**Issue:** All ~9 T3 citations this week (`aiweekly.co`, `aitoolsrecap.com`, `codersera.com`,
`techtimes.com`, `techstartups.com`, `swfte.com`, `benchlm.ai`, `releasebot.io`) are in AI/ML —
a side effect of snippet-foraging when feeds aren't used.
**Proposed change:**

> **Before:**
> ```
> [No explicit deny-list; snippet discovery pulls in low-tier AI-news aggregators.]
> ```
>
> **After:**
> ```
> Never cite: aiweekly.co, aitoolsrecap.com, codersera.com, techtimes.com,
> techstartups.com, swfte.com, benchlm.ai, releasebot.io (T3 / SEO blogspam).
> When an item is snippet-only, prefer in this order: official lab page →
> the-decoder.com / VentureBeat / TechCrunch → Artificial Analysis (benchmarks).
> ```

**Why this helps:** Eliminates T3 leakage at the source and raises average citation tier.
**Risk:** Slightly fewer leads on minor model drops first surfaced by aggregators; acceptable given the
quality gain (and Patch 1 should backfill via HF Hub).

### Patch 3 — Overview: market-data HTML wall rule
**Target prompt:** Morning brief
**Section affected:** Markets / US futures
**Issue:** Intraday equity/FX figures are the #1 recurring gap (CNBC/Reuters/Yahoo/TradingEconomics
403 nearly every run); 06-08 even cited CNBC as `[single-source]` against a URL that 403s.
**Proposed change:**

> **Before:**
> ```
> [Markets section attempts live intraday quotes from CNBC/Reuters/Yahoo HTML and
> tags the result [single-source] when only one provider is reachable.]
> ```
>
> **After:**
> ```
> Market HTML providers (CNBC, Reuters, Yahoo, TradingEconomics) 403 the sandbox.
> Do NOT tag a 403'd-source figure [single-source]; if a number comes only from a
> search snippet, tag it [via snippet]. Anchor FX on the ECB reference XML (curl)
> and state the as-of time. If no figure is verifiable, say "direction unconfirmed"
> rather than asserting one.
> ```

**Why this helps:** Stops mislabelling unfetchable figures as authoritative and sets honest
expectations for the markets line.
**Risk:** The markets section becomes thinner/more hedged on volatile days — but more accurate.

### Patch 4 — Weekend/Overview: Nature science fallback to arXiv cross-lists
**Target prompt:** Weekend brief (and mirror into Morning brief science)
**Section affected:** Fundamental science / Nature items
**Issue:** Nature feeds are reachable but carry no abstracts and article pages 403; natastron.rss is
intermittently down — Nature items recur in Gaps as title-only.
**Proposed change:**

> **Before:**
> ```
> [Science items attempt Nature article HTML for detail; when it fails the item
> stays title-level and is logged in Gaps.]
> ```
>
> **After:**
> ```
> When a Nature feed item has no fetchable abstract, locate the corresponding
> arXiv preprint (astro-ph / cond-mat / quant-ph cross-list via curl) and summarise
> from there with [preprint], rather than leaving a title-only Nature stub. If
> natastron.rss fails, fall back to the arXiv astro-ph sweep directly.
> ```

**Why this helps:** Converts title-only Nature stubs into substantive, fetch-backed science items —
the Weekend brief already does this ad hoc; make it the rule.
**Risk:** arXiv version may predate the peer-reviewed Nature version; mitigated by the `[preprint]` tag.

### Patch 5 — All streams: enforce [via snippet] on confirmed-unavailable domains
**Target prompt:** Cyber-Papers (primary offender) + shared sourcing note
**Section affected:** Citation tagging
**Issue:** `swissinfo.ch` (confirmed-unavailable) appears in at least one multi-source citation bundle
without its own `[via snippet]` tag.
**Proposed change:**

> **Before:**
> ```
> [In multi-source bundles, a single [via snippet] tag at the end is applied to the
> group, which can leave a blocked-domain source effectively untagged.]
> ```
>
> **After:**
> ```
> Any citation to a confirmed-unavailable domain (swissinfo.ch, reuters.com,
> finance.yahoo, rts.ch, nzz.ch, science.org, biorxiv/medrxiv, etc.) MUST carry its
> own [via snippet] tag, even inside a multi-source bundle — never rely on a
> group-level tag to cover it.
> ```

**Why this helps:** Keeps the blocked-domain audit clean and unambiguous.
**Risk:** None material — cosmetic/tagging only.

## Cross-week trend
Not computable — the prior (2026-06-07) evaluator is missing; the last on disk is 2026-05-24. The
absence is itself worth a human glance: it suggests the evaluator routine skipped at least one Sunday.

## Open questions for human review
1. Why did the 2026-06-07 evaluator not land? Cron skip, a failed run, or a push that didn't reach
   `origin/main`? If the evaluator is silently skipping, cross-week trend tracking is blind.
2. AI/ML feed access: the feeds work for Overview/Cyber, so is the AI/ML prompt simply not asking for
   them (most likely, → Patch 1), or is there a per-routine sandbox difference worth probing?
3. Is the ~50% commercial-launch share of AI/ML news (which arXiv/HF can't cover) acceptable to remain
   snippet-sourced, or should a curated set of official lab newsroom/Atom feeds be added as direct
   sources?
4. natastron.rss is the flakiest core feed — keep retrying with the arXiv fallback (Patch 4), or drop
   it from the feed list entirely?
