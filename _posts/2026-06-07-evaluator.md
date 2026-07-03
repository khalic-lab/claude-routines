---
layout: single
title: "Weekly Pipeline Review — 2026-06-07"
date: 2026-06-07T11:40:42+02:00
categories: [evaluator]
---

# Weekly Brief Pipeline Review — 2026-06-07

_Coverage: briefs from 2026-06-01 to 2026-06-07._
_Files read: 7 morning (06-01→07), 6 AI/ML (06-01→06), 6 cyber (06-01→06), 1 weekend (2026-06-06), prior review at exact −7 (2026-05-31) **not found** — used 2026-05-24-evaluator (13 days prior) for trend._

**One-line verdict:** The egress wall that defined the 2026-05-24 review is **gone**. Every machine-readable feed on the writers' "verified-reachable" list now returns HTTP 200 via curl — independently reproduced from this evaluator's own sandbox — and the curl-first patch is doing exactly what it was designed to do. Portfolio direct-fetch ratio jumped from **0.035 → 0.67**, via-snippet collapsed in three of four streams, non-English citation rose from <1% to ~12%, and the structurally-empty Cyber "Papers" section is now populated 5 of 6 days. The one stream left behind is **AI/ML (direct-fetch 0.18, target 0.40)** — not a feed regression but a structural property of its sources (lab blogs + tech press are HTML, still 403; AI/ML has almost no reachable RSS/JSON primary).

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains cited            | ~95+  | ≥40    | 🟢 |
| T1 citation %                   | ~62%  | ≥40%   | 🟢 |
| T3 leakage count                | 0     | 0      | 🟢 |
| Non-English citation % (portfolio) | ~12% | ≥10%  | 🟢 |
| Link sample pass rate           | feeds 200 (9/10); article-HTML 403 from sandbox | ≥90% | ⚪ |
| Fabrication count               | 0     | 0      | 🟢 |
| Single-source rate (portfolio)  | ~18%  | <20%   | 🟢 |
| Empty section instances         | 1 (weekend Cyber-Papers, by design) | <5 | 🟢 |
| Direct-fetch ratio (portfolio)  | 0.67  | ≥0.35  | 🟢 |
| Direct-fetch ratio (Overview)   | 0.76  | ≥0.30  | 🟢 |
| Direct-fetch ratio (Cyber+Papers) | 0.93 | ≥0.50 | 🟢 |
| Direct-fetch ratio (AI/ML)      | 0.18  | ≥0.40  | 🔴 |
| Feeds with >50% fail rate       | 1 (arXiv Atom API, redundant w/ RSS) | 0 | 🟡 |
| Citations to confirmed-blocked domains without [via snippet] | 3 (06-04 cyber) | 0 | 🔴 |
| curl vs WebFetch advantage on feeds | curl wins decisively | curl wins | 🟢 |

---

## A–K: Detailed findings

### A. Source diversity
- **Unique domains:** comfortably above the floor — roughly 95+ distinct domains across the week. Canonical primaries (nature.com, arxiv.org, nvd.nist.gov, cisa.gov, ecb.europa.eu, quantamagazine.org), Swiss/FR/DE outlets (srf.ch, letemps.ch, nzz.ch, watson.ch), wires (aljazeera.com, npr.org, france24.com), AI press (the-decoder.com, venturebeat.com, techcrunch.com, crunchbase.com), vendor/security advisories (access.redhat.com, cloudfoundry.org, certvde.com, patchstack.com, securitylab.github.com), and platform hosts (huggingface.co, github.com). 🟢
- **Concentration:** the most-cited single domain is **arxiv.org** (~80 citations across the daily ML batches + weekend's 17 papers), likely 15–18% of total citations. This nudges the >15% flag — but arXiv is the *canonical primary* for the preprint sections, not an aggregator, so it is policy-compliant concentration, not a diversity risk. nature.com and nvd.nist.gov are the next-heaviest, both canonical primaries. No aggregator or single news outlet approaches the ceiling. 🟢 (with the arXiv note.)
- **Tier distribution:** T3 = 0 in every footer (policy held). 🟢 **T1 ≈ 62%** (≈210 T1 items vs ≈129 T2 across all footers). Critically, unlike 2026-05-24 where "T1" was nominal (snippet-sourced), this week's T1 is *genuinely fetched* — NVD JSON, CISA KEV JSON, arXiv RSS, Nature RSS, ECB XML all pulled via curl. The T1 figure is now real, not inflated. 🟢
- **Linguistic:** ~12% non-English, driven almost entirely by Cyber+Papers' Switzerland section (SRF DE + Le Temps FR, ~45 citations across the week) plus DE-language SRF versions of world-politics items and a few weekend DE sources. This is the single most dramatic recovery: <1% → ~12%, because SRF/Le Temps RSS now return 200 (confirmed below). 🟢
- **Geographic:** US, CH, Qatar (AJ), DE, FR, UK, China (SCMP), South Korea (Korea Herald), Ireland, India, Turkey (USOM/siberguvenlik.gov.tr), Romania, Somalia coverage — well spread. 🟢

### B. Aggregator leakage (critical)
- **0 violations.** No citations to news.ycombinator.com, lobste.rs, reddit, twitter/x.com, mastodon, threads, or bsky in any brief. `reddit.com` appears only as a *named plaintiff* in the CNN-v-Perplexity copyright item (06-04 ai-ml), not as a source. `simonwillison.net` (personal blog, allowed) appears in weekend + 06-06 ai-ml. 🟢

### C. Link health (sample-based)
Probed 16 URLs from this evaluator's sandbox (curl `-sI`, Mozilla UA, 15 s):
- **Feeds — all healthy:** `export.arxiv.org/rss/cs.LG`, `services.nvd.nist.gov/.../cves/2.0`, `cisa.gov/.../known_exploited_vulnerabilities.json`, `ecb.europa.eu/.../eurofxref-daily.xml`, `quantamagazine.org/feed/`, `nature.com/nature.rss`, `srf.ch/.../rss`, `letemps.ch/articles.rss`, `aljazeera.com/.../all.xml` → **all 200**. `nature.com/natastron.rss` → **303** (a redirect, not a hard fail — see K and Patch 4).
- **Human-facing article/detail pages — still blocked:** `nvd.nist.gov/vuln/detail/CVE-…` (403), `arxiv.org/abs/…` (403), `nature.com/articles/…` (303 auth redirect), `cnbc.com/…` (403), `huggingface.co/<model>` HTML (403).
- **Reading:** the *data sources* (feeds) are fully reachable; the *citation target URLs* that point at HTML article/detail pages 403 from the sandbox. These URLs are structurally valid and resolve fine for real readers — the 403 is HTML bot-blocking, not a broken link or a feed regression. Cited-claim spot-checking against the **HTML** pages is therefore **unmeasurable (⚪)**, but the underlying data was correctly pulled from the corresponding feeds (the writers consistently cite the NVD detail page as the human link while sourcing the record from NVD JSON, etc.).
- **Regression check (the one the charter asks for):** the feed URLs (arXiv RSS, NVD JSON, CISA KEV JSON) do **NOT** 403 — they return 200. That is the explicit non-regression signal. The feed-first/curl-first recovery is intact. 🟢
- **No fabrication detected.** Where a batch was genuinely unavailable (06-06 cyber weekend ML batch), the writer emitted the no-fabrication skip note rather than inventing papers. 🟢

### D. Section vitality
- All daily streams kept their core sections populated. Overview Science/ML/Markets full every day; Cyber Switzerland/World/Cybersecurity full every day (5–8 items each).
- **Cyber "ML research — second arXiv batch":** populated 6/6/6/5/6 papers on 06-01→05, and correctly **skipped on 06-06** (Saturday — arXiv opens no weekend submission window; `skipDays` honored). That single empty is **by design**, not a failure. This is the section flagged 🔴 last cycle (empty 4/5 days); it is now healthy. 🟢
- AI/ML "Lab blogs / New models / Benchmarks" ran thin on quiet days (06-01, 06-06) but those are honest *news-driven* thin sections (no model dropped), correctly logged as gaps rather than padded. Not counted as structural empties.
- Non-by-design empty instances: **effectively 0**. 🟢

### E. Coverage-gap recurrence (≥3 = structural)
Clustered from Gaps footers:
1. **Nature/Quanta article *bodies* 403 (auth/redirect wall)** — overview 06-02, 06-04, 06-06; weekend. ~4×. *Structural but mitigated:* RSS titles/DOIs + secondary plain-language writeups carry the framing.
2. **Markets live data: CNBC HTML 403; no live intraday FX/index primary** — overview every day. ECB is the prior-day reference fix, Asian closes/US futures via CNBC snippet. ~7×. **Structural.**
3. **AI/ML lab pages + tech press 403** — every AI/ML day. **Structural** — this is the root cause of the failing AI/ML direct-fetch ratio (Dimension K).
4. **arXiv Atom API rate-limited (429) / errored** — cyber 06-02, 03, 04, 05. 4×. Structural but **redundant** (RSS pubDate + announce-type already substitutes cleanly).
5. **Nature Astronomy `natastron.rss` flapping (403 / empty)** — overview 06-01, 03, 04. 3×. Root cause now identified: it 303-redirects (see Patch 4).
6. **bioRxiv/medRxiv unreachable** — overview 06-02, 06-06; weekend. 3×. Expected (confirmed-unavailable list); embryo-editing story correctly routed via Nature/Science.

Gaps 3, 4, 5 have concrete patch proposals below. Gaps 1, 2, 6 are known sandbox/source limitations being handled honestly.

### F. Triangulation rate (`[single-source]`)
- **Portfolio ≈ 18%** — under the <20% target. 🟢
- By stream: Overview ~15%, AI/ML ~20%, Cyber ~19%, Weekend ~20%. **No stream exceeds its 25% per-stream cap.** The elevated streams (AI/ML, Cyber) are single-sourced mainly where a second wire is genuinely unreachable (AI funding rounds → one tech-press outlet; Swiss cantonal items → one of SRF/Le Temps; some Al Jazeera-only world items). A one-day spike worth noting: 06-03 overview ran 3 of 5 Science items as `[single-source]` (all Nature Physics, inherently single-paper). This is a large improvement over 2026-05-24's Markets stream at ~32%. 🟢

### G. Tag discipline
- **`[preprint]`:** consistently applied to every arXiv item (sampled overview 06-01 ×5, cyber 06-03 ×6, weekend ×17 — all tagged). 🟢
- **`[vendor PR]`:** consistently applied — Microsoft/MAI, Anthropic, NVIDIA Nemotron, OpenAI, Gemma, Mistral in AI/ML; MediaTek bulletin in cyber. 🟢
- **`[disputed]`:** used ~6× and appropriately — MiniMax M3 vendor benchmarks (06-02/03/04 ai-ml), Copilot model-name confusion (06-02), CADA industry pushback (06-03), embryo base-editing (06-06 overview), Chrome CVE NVD-vs-Google score divergence (06-05 cyber). 🟢
- **`[via snippet]` by stream (totals from footers):** Overview **25** (was 93), Cyber **8** (was 104), Weekend **5** (was 51), AI/ML **67** (was 119). Three of four streams collapsed — the clearest single confirmation the curl-first recovery took. **AI/ML remains snippet-dominated** because its sources aren't curl-reachable feeds. 🔴 for AI/ML only.

### H. Topic balance (weekend brief)
- Weekend 2026-06-06 carries **10 ML/AI papers** and **7 fundamental-science papers** (≈59% ML / 41% science in the paper sections), plus a separately-populated biology section (5 items) and security-research section. The split is reasonable and lightly ML-tilted.
- As in 2026-05-24, the *stated* ML-vs-science bias target is not visible in the inputs, so a precise ±10pp deviation flag still cannot be computed. No action proposed pending the target (carried as Open Question 3).

### I. Repetition detection
Dedup is clearly running and is well-documented in every footer (REPEAT/ONGOING verdicts, story counts 887–1,012). Multi-day threads all carried dated new facts:
- **NVIDIA Nemotron 3 Ultra** — ai-ml 06-03 (teaser) → 06-04 (weights live) → 06-06 (datasets + recipes + MLX ports). 4 touches; each adds a fact, though 06-06 re-explains the architecture at length. Minor note, not a flag.
- **MiniMax M3** (ai-ml 06-02/03/04), **Microsoft Build/MAI** (06-02/03/05), **Israel-Lebanon** (cyber 06-01/02/04/06), **US-Iran** (cyber/weekend/overview), **Vaud bouclier-fiscal/Dittli** (cyber 06-03/04/05/06), **G7 Geneva-Évian** (cyber 06-03/04/05) — all genuinely developing, correctly tagged `[ongoing]`, each with a named dated development. Justified.
- Repeats were actively dropped (Anthropic S-1, llama.cpp builds, PAN-OS KEV, base-editing across overview/weekend). 🟢

### J. Cross-week trend
The exact −7 anchor (`2026-05-31-evaluator.md`) does not exist; using `2026-05-24-evaluator.md` (13 days prior) as the most recent baseline. **The trend is a near-total recovery:**

| Metric | 2026-05-24 | 2026-06-07 | Δ |
|---|---|---|---|
| Direct-fetch ratio (portfolio) | 0.035 | 0.67 | ▲ ~19× |
| Direct-fetch (Overview) | 0.02 | 0.76 | ▲ |
| Direct-fetch (Cyber+Papers) | 0.00 | 0.93 | ▲ |
| Direct-fetch (AI/ML) | 0.085 | 0.18 | ▲ (still 🔴) |
| Non-English citation % | <1% | ~12% | ▲ |
| T1 % (genuine vs nominal) | 36% nominal | 62% real | ▲ |
| Empty Cyber-Papers instances | 4/5 | 0/6 (weekend by design) | ▲ |
| Feeds with 100% fail | 10+ | 0 | ▲ |
| curl vs WebFetch | both 403 | curl wins | ▲ |

The 2026-05-24 review's headline finding — "the egress proxy is the wall; curl-first is not bypassing it because the wall is not WebFetch" — has been resolved at the infrastructure layer. Either the egress policy was widened or the proxy relaxed; the feeds the writers were told are public are now actually reachable. **Open Question 1 from that review (widen the egress allowlist) appears answered.** The GitHub-mirror stopgaps (Patches 1–2 last cycle) are no longer required, though they remain harmless fallbacks.

### K. Feed reachability & direct-fetch rate (binding constraint — primary lens)

**Per-stream direct-fetch ratio** (direct ÷ (direct + via-snippet), from Coverage footers):

| Stream | Per-day direct/snippet | Total | Ratio | Target | Status |
|---|---|---|---|---|---|
| Overview | 12/2, 13/6, 11/2, 11/4, 12/4, 10/4, 10/3 | 79 / 104 | **0.76** | ≥0.30 | 🟢 |
| Cyber+Papers | 17/0, 11/4, 22/0, 19/2, 18/0, 11/2 | 98 / 106 | **0.93** | ≥0.50 | 🟢 |
| AI/ML | 5/6, 2/13, 2/15, 2/9, 0/16, 4/8 | 15 / 82 | **0.18** | ≥0.40 | 🔴 |
| Weekend | ~24/5 | 24 / 29 | **0.83** | ≥0.30 | 🟢 |
| **Portfolio** | | **216 / 321** | **0.67** | ≥0.35 | 🟢 |

Overview, Cyber+Papers and Weekend all clear their targets with wide margins — Cyber+Papers is essentially fully direct-fetched (NVD JSON + CISA KEV JSON + arXiv RSS + SRF/Le Temps/Al Jazeera RSS all via curl). **AI/ML is the lone failure (0.18 vs 0.40)** and the only 🔴 in Dimension K. Its day-by-day ratio (0.45, 0.13, 0.12, 0.18, 0.00, 0.33) shows the structural problem: AI/ML's news lives on lab blogs (openai.com, anthropic.com, blog.google, mistral.ai), Azure/Microsoft pages, and AI trade press (VentureBeat, The Decoder, CNBC) — **all HTML, all 403**. The only direct fetches AI/ML lands are GitHub release pages (llama.cpp, MLX) and HF Hub API calls (06-06's 4 direct fetches were all HF model-card/dataset metadata). The fix is sourcing-strategy, not infrastructure (Patch 1).

**Per-feed reachability (aggregated across the week, with method):**

| Feed | Result | Note |
|---|---|---|
| arXiv RSS (cs.LG/AI/CL/CV, stat.ML) | **ok via curl** (empty on weekends = skipDays, expected) | independently 200 |
| arXiv Atom API | **fail ~4/6** — HTTP 429 / curl-empty | redundant; RSS substitutes |
| NVD CVE JSON 2.0 | **ok via curl** every cyber day | independently 200 |
| CISA KEV JSON | **ok via curl** every cyber day | independently 200 |
| Nature RSS (nature/nphys/nm) | **ok via curl** (one nphys 403 on 06-02) | independently 200 |
| Nature Astronomy `natastron.rss` | **flap** — 403/empty 3×, ok 4× | 303-redirect; needs `-L` (Patch 4) |
| Quanta RSS | **ok via curl** every day | independently 200 |
| ECB FX XML | **ok via curl** every day | independently 200 |
| SRF (DE) / Le Temps (FR) / Al Jazeera RSS | **ok via curl** every cyber day | independently 200 — restores non-English quota |
| Semantic Scholar API | fail (429) on its one attempt (06-03) | not load-bearing |
| AI/ML lab blogs + tech press (HTML) | **fail — 403** every day | no feed equivalent (Patch 1) |
| CNBC / NVD-detail / arxiv-abs / Nature-article (HTML) | **fail — 403/303** | human-link pages; data taken from feeds |

- **Feeds with >50% fail rate:** **1** — arXiv Atom API (~4/6, all 429/transient). Because RSS already supplies the same batch dates, this is non-binding; the fix is to stop retrying it (Patch 2). 🟡
- **Method comparison (the critical test):** curl **wins decisively** — virtually every feed succeeds via curl; WebFetch is used only as a secondary for a few article-HTML bodies (e.g. Quanta article on 06-02/04/06). This is the exact inversion of 2026-05-24, where curl and WebFetch both 403'd on every feed. The curl-before-WebFetch patch is confirmed doing its job. 🟢
- **Domains-that-shouldn't-be-cited check:** mostly clean — bioRxiv/medRxiv (routed via Nature/Science), Science.org (06-06, tagged `[via snippet]`), Yahoo Finance (06-01, tagged `[via snippet]`) all handled correctly. **But 3 untagged exceptions on 2026-06-04 cyber:** `swissinfo.ch` ×2 (tariff-mechanics item; Jositsch item) and `nzz.ch` ×1 (Jositsch item) are cited as plain references with **no `[via snippet]` tag**. Both domains are on the writers' "confirmed unavailable" list, so any citation to them can only be snippet-sourced and must be tagged. 🔴 (low-severity but it is the metric — Patch 3.)

---

## Patch proposals (for human review)

Priority: Dimension-K binding-constraint first (Patch 1), then the honesty/efficiency fixes. None of these is a feed-outage fix — the outage is over — so all four are tractable prompt edits.

### Patch 1 — Make HF Hub API + GitHub the primary verification channel for AI/ML model/release items
**Target prompt:** AI/ML
**Section affected:** Lab blogs / New models / Benchmarks fetch logic + Coverage footer
**Issue:** AI/ML direct-fetch ratio is 0.18 vs 0.40 — the only Dimension-K failure. Root cause: lab blogs and AI trade press are HTML and 403 the sandbox, so model-release facts are cited via snippet. Yet the reachable primaries *do* exist for the most important AI/ML story type (open-weight drops): the Hugging Face Hub API/MCP and GitHub release pages both return 200. On 06-06 the writer already used HF Hub metadata for 4 genuine direct fetches (Nemotron card, datasets, MLX ports) — this just needs to become the default, not the exception.
**Proposed change:**

> **Before:**
> ```
> For a model release: cite the lab blog / model announcement, plus trade-press
> coverage (VentureBeat, The Decoder, CNBC) for benchmarks and context.
> Tag [via snippet] where the page 403s.
> ```
>
> **After:**
> ```
> For any model/dataset release, FIRST verify via the reachable primary:
>   - Hugging Face Hub API/MCP: model card, createdAt, license, config, downloads
>   - GitHub releases API (llama.cpp, mlx, vendor repos): tag, date, notes
> These count as Direct fetches and may drop [via snippet]. Pull the hard facts
> (params, license, context window, release date) from the Hub/GitHub, and use
> trade-press only for color/benchmark claims (still [via snippet], still [disputed]
> for vendor-run numbers). Target: lift AI/ML direct-fetch from snippet-bound.
> ```

**Why this helps:** Converts the highest-volume AI/ML story type (open-weight releases) from snippet-only to genuine direct fetches, attacking the one failing Dimension-K ratio at its root.
**Risk:** Lab/governance items with no Hub artifact (lawsuits, EU acts, funding rounds) stay snippet-bound — AI/ML will improve but may not fully reach 0.40 on governance-heavy days; that residual is honest, not a miss.

### Patch 2 — Stop retrying the arXiv Atom API; confirm batch dates from RSS
**Target prompt:** Cyber-Papers (and Overview ML batch)
**Section affected:** "ML research — arXiv batch" date-confirmation step
**Issue:** The arXiv Atom date-confirmation API failed ~4/6 days (HTTP 429 / curl-empty), and on every one of those days the writer fell back to RSS `pubDate` + `announce_type:new` and proceeded normally. The Atom retry is pure wasted budget — it never added information the RSS didn't already carry.
**Proposed change:**

> **Before:**
> ```
> Confirm submission dates via the arXiv Atom API (export.arxiv.org/api/query).
> If it fails, fall back to RSS channel pubDate / announce_type.
> ```
>
> **After:**
> ```
> Confirm submission/announce dates from the arXiv RSS channel pubDate +
> announce_type:new (already fetched). Only call the Atom API for a specific
> id_list lookup when an individual paper's date is ambiguous — do NOT use it as
> the routine date-confirmation sweep (it 429s most days and RSS already suffices).
> ```

**Why this helps:** Removes the one feed with a >50% fail rate from the critical path and reclaims run budget, with zero loss of information.
**Risk:** Minimal — RSS has been the de-facto date source on the 429 days already; this just makes it the explicit primary.

### Patch 3 — Enforce `[via snippet]` on confirmed-unavailable domains
**Target prompt:** Cyber-Papers (shared sourcing-charter tagging block)
**Section affected:** Switzerland / World-politics citation tagging
**Issue:** On 2026-06-04, `swissinfo.ch` (×2) and `nzz.ch` (×1) were cited as plain references with no `[via snippet]` tag, in the tariff and Jositsch items. Both are on the "confirmed unavailable" list — they cannot be fetched, so any citation is necessarily snippet-sourced and must be tagged. This is the only Dimension-K compliance miss this week.
**Proposed change:**

> **Before:**
> ```
> Tag [via snippet] when a citation comes from a search-engine excerpt rather
> than a fetched source.
> ```
>
> **After:**
> ```
> Tag [via snippet] for any search-excerpt citation. In particular, ANY citation
> to a domain on the "confirmed unavailable" list (swissinfo.ch, NZZ, Reuters,
> Science.org, Yahoo Finance, RTS, FAZ, Spiegel, Le Monde, bioRxiv/medRxiv,
> NCSC.ch, HF papers) is snippet-only BY DEFINITION and MUST carry [via snippet]
> — these cannot be direct-fetched, so an untagged citation to them is an error.
> ```

**Why this helps:** Closes the only confirmed-blocked-domain tagging gap and keeps the direct/snippet accounting honest.
**Risk:** None — purely a tagging-discipline tightening.

### Patch 4 — Follow the 303 redirect on Nature Astronomy (and sibling Nature feeds)
**Target prompt:** Overview (and Weekend) — science feed fetch
**Section affected:** Nature feed fetch logic + Coverage "Feeds hit"
**Issue:** `natastron.rss` was logged as 403/empty on 3 days (06-01, 03, 04), recurring as a "no fresh astronomy" gap. This evaluator's probe shows the URL actually returns **303** (a redirect), not a hard 403 — a bare curl without `-L` reports it as a non-200 "fail." `nature.com/articles/…` similarly 303-redirects. Following the redirect recovers the feed.
**Proposed change:**

> **Before:**
> ```
> curl -sS https://www.nature.com/natastron.rss   (log fail if non-200)
> ```
>
> **After:**
> ```
> curl -sSL https://www.nature.com/natastron.rss   # -L follows the 303 redirect
> # apply -L to all nature.com feeds; a 303 is a redirect to follow, not a fail.
> ```

**Why this helps:** Recovers the most frequently-empty science sub-feed and should reduce the recurring "no fresh astronomy in window" gap.
**Risk:** Low — `-L` only follows redirects; if the redirect target is itself an auth wall the feed still legitimately skips, but the probe suggests it resolves.

---

## Cross-week trend
Covered in Dimension J: a near-complete recovery from the 2026-05-24 total egress wall. Portfolio direct-fetch 0.035 → 0.67; non-English <1% → ~12%; T1 nominal-36% → genuine-62%; Cyber-Papers empties 4/5 → 0/6. The infrastructure fix the last review identified as "the single highest-value action, outside any writer prompt" has landed. The remaining work is the AI/ML sourcing strategy (Patch 1), which is a prompt-level fix, not an infrastructure one.

## Open questions for human review
1. **Egress appears restored — is it monitored?** The 2026-05-24 review asked for a probe/canary routine that curls 3–4 feeds daily and records HTTP codes, so the *next* outage is caught in a day instead of persisting ~3 weeks. The recovery makes this *more* worth adding, not less — there's now a healthy baseline to detect a future regression against. Does such a canary exist yet?
2. **AI/ML is structurally snippet-native.** Even with egress restored, AI/ML's core sources (lab blogs, Azure/MS pages, AI trade press) have no reachable feed and 403 as HTML. Patch 1 routes the model-release subset through HF/GitHub, but governance/funding items will stay snippet-bound. Is widening the allowlist to a few lab-blog domains feasible, or should AI/ML's direct-fetch target be set lower than 0.40 to reflect its source mix?
3. **Weekend topic-balance target still not supplied** (carryover from 2026-05-24 #5). The weekend split is ~59% ML / 41% science, but without the stated bias target Dimension H cannot be scored numerically. Please supply the intended ML-vs-science ratio.
4. **Confirm the `natastron.rss` 303 fix** (Patch 4) — the redirect interpretation is from this evaluator's probe; verify `-L` recovers the feed in the writer sandbox at the next astronomy-light run.
