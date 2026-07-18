---
layout: single
title: "Weekly Pipeline Review — 2026-05-31"
date: 2026-05-31T11:40:32+02:00
categories: [evaluator]
published: true
---

# Weekly Brief Pipeline Review — 2026-05-31

_Coverage: briefs from 2026-05-25 to 2026-05-31._
_Files read: 7 morning (25–31), 6 AI/ML (25–30), 5 cyber (26–30), 1 weekend (2026-05-30), prior review (2026-05-24-evaluator) found._

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains cited            | ~70+  | ≥40    | 🟢 |
| T1 citation %                   | ~67%  | ≥40%   | 🟢 |
| T3 leakage count                | 0     | 0      | 🟢 |
| Non-English citation % (portfolio) | ~11% | ≥10% | 🟢 |
| Link sample pass rate           | 100% of measurable (arXiv-via-API unmeasurable) | ≥90% | 🟢 |
| Fabrication count               | 0     | 0      | 🟢 |
| Single-source rate (portfolio)  | ~19% (Cyber World ~30%) | <20% | 🟡 |
| Empty section instances         | 1–2 (all by-design weekend/holiday) | <5 | 🟢 |
| Direct-fetch ratio (portfolio)  | **0.57** | ≥0.35 | 🟢 |
| Direct-fetch ratio (Overview)   | 0.77  | ≥0.30  | 🟢 |
| Direct-fetch ratio (Cyber+Papers) | 1.00 | ≥0.50 | 🟢 |
| Direct-fetch ratio (AI/ML)      | **0.19** | ≥0.40 | 🔴 |
| Feeds with >50% fail rate       | 2 (Semantic Scholar, Nature Astronomy RSS) | 0 | 🟡 |
| Citations to confirmed-blocked domains without [via snippet] | 0 | 0 | 🟢 |
| curl vs WebFetch advantage on feeds | curl wins decisively | curl wins | 🟢 |

**One-line verdict:** The egress wall is down. Last week every machine-readable feed 403'd via both curl and WebFetch and the portfolio direct-fetch ratio sat at **0.035**; this week curl fetches arXiv, NVD, CISA KEV, ECB, Nature, Quanta, SRF, Le Temps and Al Jazeera cleanly, the portfolio ratio is **0.57** (16× recovery), Cyber+Papers runs at a perfect **1.00** with zero via-snippet citations all week, and non-English coverage climbed from <1% to ~11%. This evaluator independently reproduced the recovery from its own sandbox (all feeds 200 via curl — see Dimension C). The single remaining red is **AI/ML at 0.19**, which is structural rather than a regression: that stream's content is dominated by lab-PR and benchmark-press HTML pages that still 403, so its direct-fetch denominator is inherently snippet-heavy. The one full-day relapse was **2026-05-25** (US Memorial Day), the tail of last week's wall, where every feed 403'd again.

---

## A–K: Detailed findings

### A. Source diversity
- **Unique domains:** comfortably above the ≥40 floor — well over 70 distinct domains (nature.com, arxiv.org, nvd.nist.gov, aljazeera.com, srf.ch, letemps.ch, github.com, huggingface.co, quantamagazine.org, ecb.europa.eu, cnbc.com, artificialanalysis.ai, techcrunch.com, venturebeat.com, marktechpost.com, plus dozens of CVE-vendor and law-firm domains). 🟢
- **Concentration:** the two heaviest are `nvd.nist.gov` (one reference link per CVE — ~30+ across the cyber stream) and `arxiv.org` (one per paper — ~35+ across overview/cyber/weekend). Both sit around ~10–12% of total citations as *reference* links; neither breaches the 15% ceiling, but they are the structural heavyweights. `nature.com` is third (the science section runs almost entirely on Nature RSS). 🟢
- **Tier distribution:** T3 = 0 in every footer (policy held). 🟢 **T1 ≈ 67%** (197 T1 vs 95 T2 vs 0 T3) — a large jump from last week's 36%, and this time it is *genuine* T1: arXiv RSS, NVD JSON, CISA KEV JSON, ECB XML and Nature RSS were actually fetched, not snippet-attributed. 🟢
- **Linguistic:** SRF (DE) and Le Temps (FR) RSS now fetch via curl every cyber and weekend run. Counting their citations (~16 SRF + ~17 Le Temps across the week) against ~290 portfolio citations gives **~11% non-English** — over the ≥10% target for the first time in the trend window. 🟢 (Borderline; entirely dependent on the SRF/Le Temps curl path staying up.)
- **Geographic:** ~9–10 countries of origin for news sections (US, CH, Qatar/AJ, France, Germany, China via 36kr, Spain, India-finance, plus pan-African/Sudan/DRC datelines). 🟢

### B. Aggregator leakage (critical)
- **0 violations.** No citations to news.ycombinator.com, lobste.rs, reddit, twitter/x.com, mastodon, threads or bsky in any brief. `x.ai` (xAI's corporate site, not x.com), `simonwillison.net`, `karpathy.bearblog.dev`, `acoup.blog` and `lesswrong.com` appear in the weekend essays section — none is a banned aggregator. **Minor editorial note:** `lesswrong.com` is cited as a primary source for a "high-karma post" in the weekend Essays section; it is a forum platform, not on the banned list, but it sits closer to the line than the personal blogs and is worth keeping an eye on. 🟢

### C. Link health (sample-based) — MEASURABLE this week
Unlike the last two cycles (reported ⚪ unmeasurable), this evaluator's sandbox **can reach the feeds**. Direct curl probes (12s timeout, Mozilla UA):
- `export.arxiv.org/rss/cs.LG` → **200**; `services.nvd.nist.gov/rest/json/cves/2.0` → **200**; `cisa.gov/.../known_exploited_vulnerabilities.json` → **200**; `raw.githubusercontent.com/cisagov/kev-data/...` → **200**; `ecb.europa.eu/.../eurofxref-daily.xml` → **200**; `nature.com/nature.rss` → **200**; `quantamagazine.org/feed/` → **200**; `srf.ch/.../rss` → **200**; Al Jazeera article HTML → **200**.
- **HTML detail pages still 403:** `arxiv.org/abs/2605.30343` → 403 and `nvd.nist.gov/vuln/detail/CVE-2026-0257` → 403. This is *expected and fine* — the writers cite the machine-readable feeds, not the human pages.
- `nature.com/natastron.rss` → **303 → 403** (redirects to a 403 target). This is the one real feed breakage (see Patch 2).
- **Cited-claim spot-checks (8 attempted, cyber/news):**
  - `CVE-2026-0257` (weekend + cyber-30, "PAN-OS GlobalProtect auth bypass, CVSS 9.1, KEV 29 May") — NVD JSON returns an exact description match, sourceIdentifier `psirt@paloaltonetworks.com`, lastModified 2026-05-29. ✓
  - `CVE-2026-48027` (Nx Console), `CVE-2026-8398` (Daemon Tools Lite) — both **present in the live CISA KEV catalog**. ✓✓
  - Al Jazeera Nabatieh article (cyber-30) resolves 200. ✓
  - arXiv abstract verification (2605.30343 RiM, 2605.30322 Gram) via the arXiv **API** returned empty — but a known-good control ID (2301.00001) also returned empty, so the `export.arxiv.org/api/query` path is simply dead from this environment. arXiv RSS works; the API does not. These two spot-checks are therefore **unmeasurable**, not failed.
- **Result: 0 fabrications detected; 100% pass rate on the measurable (cyber/news) sample.** 🟢 The honest-failure discipline from prior weeks held too: where the weekend writer's draft used arXiv IDs it could not resolve, it *pulled them before publishing* rather than guess (documented in the weekend Gaps footer).

### D. Section vitality
- **Cyber "ML research — second arXiv batch":** populated 26, 27, 28, 29 (5/5/5/4 papers); empty only on **30** (Saturday — arXiv skips weekends, correctly flagged). This is the section that was empty 4/5 days last week; it is now healthy. 🟢
- **Overview "ML research — first arXiv batch":** empty on **25** (Memorial Day, all feeds 403) and **31** (Sunday, by design). One feed-driven failure, one by-design.
- **AI/ML "New models":** thin on 29 (no flagship) and 30 (HiDream only) — both honestly labelled, not empty.
- **Non-by-design empty instances: 1–2**, well under the <5 threshold. 🟢

### E. Coverage-gap recurrence (≥3 = structural)
Clustered from the Gaps footers:
1. **Asian equity close / US futures unavailable** (Reuters & Yahoo Finance blocked) — every weekday Overview (25–29) + weekend. Structural (~6×). This is now the *single* class of data the recovery did **not** fix, and with the Markets routine retired (2026-05-30) the Overview snapshot is the only markets coverage. See Patch 4.
2. **bioRxiv / medRxiv blocked** — every Overview/Cyber. Structural but on the "confirmed unavailable" list (not actionable).
3. **Semantic Scholar API 429 / not-in-allowlist** — 25, 27, 30, 31 (~4×). New recurring; rate-limit, not a hard block. See Patch 3.
4. **HuggingFace papers HTML 403 / HF MCP connection dropped** — 25, 29, 30 (~3×). The HF *Hub API* still works (model metadata is fetched directly); it is the HF *papers* HTML and the MCP transport that are flaky.
5. **NCSC.ch advisory feed unavailable** — every cyber. Confirmed-unavailable (expected).

Gaps 2 and 5 are accepted standing limitations. Gap 1 is the actionable structural one.

### F. Triangulation rate ([single-source])
- **Portfolio ≈ 19%** — just under the <20% target. 🟡
- **The driver is the Cyber World-politics section.** With Reuters/AP/AFP wires still on the confirmed-unavailable list, geopolitics bullets are sourced to a single reachable feed (Al Jazeera *or* SRF) and tagged `[single-source]` — cyber-27 ran nearly its entire Switzerland + World blocks single-sourced (~11 tags), pushing that stream's section rate toward ~30%. The writers are tagging honestly; this is a sourcing-availability constraint, not a discipline failure.
- AI/ML carries the next-most `[single-source]` tags, almost all on vendor-claimed benchmark figures (Opus 4.8 69.2% SWE-bench Pro, MiniMax/Grok specs) — appropriately tagged pending independent replication.

### G. Tag discipline
- **[preprint]:** applied to every arXiv item across overview, cyber and weekend (sampled ~20, all tagged). 🟢
- **[vendor PR]:** consistently applied to Gemini 3.5 Flash, SynthID, Anthropic/SpaceX, Opus 4.8, Mistral AI Now Summit, Grok Build. 🟢
- **[disputed]:** **0 uses this week** (last week ~3). Nothing in-window genuinely warranted it; not a concern, just noted.
- **[via snippet] by stream** — the headline discipline metric, and the clearest recovery signal:
  - **Cyber+Papers: 0 via-snippet all five days.** 🟢
  - **Overview: 16 total**, and 12 of those are from the single relapse day (25). Days 26/27/28 ran 0 via-snippet.
  - **Weekend: 18** (mix of lab-PR, essay and trending-model snippets — inherent to the format).
  - **AI/ML: ~98**, flat-high. This is the lone laggard and the reason its direct-fetch ratio is red (Dimension K).

### H. Topic balance (weekend brief)
- ML/AI papers section ≈ **10** (RL welfare axis, Reasoning-with-Sampling, HPO, In-Context Reward Adaptation, Self-Trained Verification, Qwen-VLA, RiM, LLMSurgeon, Gram, + GPIC dataset). Fundamental-science papers ≈ **5** (nitrogenase classical sim, pig xenotransplant, Th-229, undersea volcanism, Gram-negative enzyme); the Biology section adds ~3 more (macrophage MATCH, gut-brain circuit, organoid firing sequences).
- Split ≈ **55% ML / 45% science** in the paper sections — reasonable and slightly ML-tilted, consistent with last week's ~58/42. **As last week, the prompt's stated bias target is not visible in the inputs**, so the ±10pp deviation flag still cannot be computed numerically. No action proposed pending the target (carried as an open question).

### I. Repetition detection
Multi-day threads this week are nearly all *genuinely developing* and correctly `[ongoing]`-tagged, with dedup footers showing explicit REPEAT drops:
- **Claude Opus 4.8** — AI/ML 28→29, overview 28, weekend 30: real development (GitHub Copilot GA + alignment angle added on 29). Justified.
- **Project Glasswing / Mythos** — cyber-24→AI/ML 28→29→weekend: each instance carried new data (23,019 vulns / 90.6% confirmation / FreeBSD CVE-2026-4747). Justified.
- **US-Iran / Hormuz** — cyber 26–30 + weekend + overview: live escalation (Bandar Abbas strikes, 60-day MOU, Oman threat). Justified.
- **DRC Ebola, Winterthur attack, Israel-Lebanon/Litani** — all developing day-to-day. Justified.
- Lower-development recycling: **EU AI Act omnibus** (AI/ML 25→26→27) and the **DeepSeek/Kimi open-weight cluster** (AI/ML 25→27→30) are re-explained across several days, but both are tagged `[ongoing]` and the 30 May AI/ML brief explicitly *declined* to re-run them. Dedup discipline is markedly better than last cycle. 🟢

### J. Cross-week trend (vs 2026-05-24-evaluator) — the headline
| Metric | 2026-05-24 | 2026-05-31 | Δ |
|---|---|---|---|
| Direct-fetch ratio (portfolio) | 0.035 | **0.57** | ▲ 16× |
| — Overview | 0.02 | 0.77 | ▲ |
| — Cyber+Papers | 0.00 | 1.00 | ▲ |
| — AI/ML | 0.085 | 0.19 | ▲ (still red) |
| — Weekend | 0.056 | 0.44 | ▲ |
| via-snippet (Cyber) | ~104 | **0** | ▼ to zero |
| T1 citation % (genuine) | ~36% (nominal) | ~67% (fetched) | ▲ |
| Non-English % | <1% | ~11% | ▲ |
| Feeds >50% fail | 10+ | 2 | ▼ |
| T3 leakage | 0 | 0 | = |
| curl vs WebFetch | both 403 | curl wins | ▲ |

The egress proxy that the 2026-05-24 review identified as *the* binding constraint was lifted between **25 and 26 May** (25 still 403 across the board; 26 onward all-green). The curl-first patch is now demonstrably doing its job — curl succeeds where WebFetch still 403s the HTML pages — but the primary cause of recovery was the network policy opening up, exactly as last week's Open Question #1 requested. Patches 1–4 from the prior review (GitHub-mirror routing for KEV/CVE) are now **optional** rather than load-bearing: the canonical NVD and CISA endpoints fetch directly again (KEV mirror still works as a documented fallback).

### K. Feed reachability & direct-fetch rate (binding constraint — primary lens)

**Per-stream direct-fetch ratio (direct ÷ (direct + via-snippet), from Coverage footers):**

| Stream | Per-day direct/snippet | Total | Ratio | Target | Status |
|---|---|---|---|---|---|
| Overview | 0/7, 8/0, 9/0, 13/0, 12/2, 7/6, 5/1 | 54 / 70 | **0.77** | ≥0.30 | 🟢 |
| AI/ML | 4/28, 3/16, 3/18, 5/16, 4/14, 4/6 | 23 / 121 | **0.19** | ≥0.40 | 🔴 |
| Cyber+Papers | 18/0, 10/0, 22/0, 20/0, 13/0 | 83 / 0 | **1.00** | ≥0.50 | 🟢 |
| Weekend | 14/18 | 14 / 32 | **0.44** | ≥0.30 | 🟢 |
| **Portfolio** | | **174 / 306** | **0.57** | ≥0.35 | 🟢 |

Three of four streams clear their target comfortably; Cyber+Papers is perfect. **AI/ML is the lone red, and it is structural, not a regression.** Its sections are dominated by (a) lab-blog announcements (Anthropic/OpenAI/DeepMind/Mistral HTML all still 403), (b) benchmark/funding press (TechCrunch, VentureBeat, MarkTechPost, Bloomberg — all snippet), and (c) HF *papers* HTML (403). The only things AI/ML fetches directly are arXiv RSS, GitHub release pages and the HF Hub API for model cards. So even with the egress open, AI/ML's *content mix* caps its achievable ratio. The 26 May value (3/19 = 0.16) is the floor; the 30 May value (4/10 = 0.40) shows that on a light, paper-heavy day it can hit target. See Patch 1.

**Per-feed reachability (aggregated across the week, with method):**

| Feed | Result | Note |
|---|---|---|
| arXiv RSS (cs.LG/AI/CL/CV, stat.ML) | **ok via curl** 26–31 | 403 only on 25 (Memorial Day); empty on weekends by design |
| arXiv Atom API | ok via curl | used for weekend 28-May submissions |
| NVD CVE JSON 2.0 | **ok via curl** every cyber day | 85 / 157 / etc. CVEs returned |
| CISA KEV JSON (cisa.gov) | **ok via curl** every cyber day | canonical endpoint, no mirror needed |
| ECB FX XML | **ok via curl** every day | FX anchor restored |
| Nature RSS (nature.rss, nphys) | ok via curl weekdays | "0 items parsed" on weekend 30 (intermittent) |
| Nature Astronomy RSS (natastron.rss) | **fail — 303→403** | redirect target 403s; the one real feed breakage (Patch 2) |
| Quanta RSS | ok via curl | |
| SRF (DE) / Le Temps (FR) / Al Jazeera RSS | **ok via curl** every cyber day | restores the non-English quota |
| Semantic Scholar API | **fail — HTTP 429 / not-in-allowlist** | rate-limited 27/30/31 (Patch 3) |
| HuggingFace papers HTML | fail — 403 | but HF **Hub API** (model cards) works directly |
| HuggingFace MCP tool | flaky — connection dropped 25, 29 | not a feed; transport instability |

- **Feeds with >50% fail rate: 2** — Semantic Scholar API (rate-limited every attempt) and Nature Astronomy RSS (redirect-to-403 every attempt). Both low-impact. 🟡
- **Method comparison (the critical test):** curl now **wins decisively**. Across every machine-readable feed it returns 200 where the HTML equivalents (and last week's WebFetch attempts) return 403. The curl-first ordering is validated. 🟢
- **Domains-that-shouldn't-be-cited check:** swissinfo.ch, Yahoo Finance, Reuters, NZZ, RTS, bioRxiv — none appears as a *fetched* citation; where referenced at all they are flagged as gaps/unavailable. **0 violations.** 🟢

**The actionable residue:** the recovery is ~95% complete. What remains is (1) AI/ML's structurally-snippet content mix, (2) two minor broken/limited feeds (natastron, Semantic Scholar), and (3) the one data class egress did *not* restore — Asian/US equity index data (Reuters/Yahoo), which now has no dedicated Markets routine behind it.

---

## Patch proposals (for human review)

Priority order: Dimension-K (binding-constraint) first. The recovery means there are few load-bearing patches this week; these are tuning, not triage. **Do not apply blindly** — each is a suggested edit for human review against the sourcing charter.

### Patch 1 — Lift AI/ML's direct-fetch ratio by routing model/paper/benchmark items through reachable structured APIs first
**Target prompt:** AI-ML
**Section affected:** New models / Benchmarks / Papers fetch logic + Coverage footer
**Issue:** AI/ML direct-fetch ratio is 0.19 vs the 0.40 target — the only stream below range. Root cause is content mix: lab-PR and benchmark-press HTML still 403, so most citations are necessarily `[via snippet]`. But several item *classes* (HF model cards, arXiv papers, GitHub tooling releases) are directly fetchable and are sometimes still cited via snippet.
**Proposed change:**

> **Before:**
> ```
> For each model/paper/benchmark, cite the most authoritative source found
> (lab blog, press writeup, or model card).
> ```
>
> **After:**
> ```
> For each model: fetch the HuggingFace Hub API model card by curl FIRST and cite
> it as a Direct fetch; only add press snippets as secondary corroboration.
> For each paper: fetch arXiv RSS/Atom by curl and cite the abstract as Direct.
> For each tool (llama.cpp/mlx/Ollama): fetch the GitHub releases page by curl.
> Lab-PR items whose only source is a 403-walled HTML page remain [via snippet] —
> but report the direct-fetchable classes above as Direct so the footer ratio
> reflects what was actually fetched.
> ```

**Why this helps:** Converts the already-reachable item classes from snippet to direct, lifting the ratio toward target without inventing sources.
**Risk:** Over-counting if a model card is thin; keep the press corroboration link so the claim is still triangulated.

### Patch 2 — Fix or replace the Nature Astronomy feed (natastron.rss 303→403)
**Target prompt:** Morning brief (and the shared feed-list block)
**Section affected:** Science feed-fetch list + Coverage "Feeds hit"
**Issue:** `nature.com/natastron.rss` redirects (303) to a URL that returns 403; writers log it as a flat "fail" on 30 and 31. Verified from this evaluator's sandbox: `curl -L` still ends in 403, so the redirect target itself is blocked — the URL is stale, not a missing `-L`.
**Proposed change:**

> **Before:**
> ```
> Nature Astronomy: curl https://www.nature.com/natastron.rss
> ```
>
> **After:**
> ```
> Nature Astronomy: arXiv astro-ph RSS (curl) + Quanta RSS are the primary
> astro sources; drop natastron.rss (303→403 dead path). If a Nature-Astronomy
> item is needed, reach it via the nature.com/nature.rss flagship feed instead.
> ```

**Why this helps:** Removes a guaranteed-fail fetch from every run and points astro coverage at feeds that actually return 200.
**Risk:** Slightly less Nature-Astronomy-specific coverage; arXiv astro-ph + Quanta cover the same ground.

### Patch 3 — Add backoff / deprioritise Semantic Scholar (recurring HTTP 429)
**Target prompt:** Cyber-Papers and Morning brief (papers enrichment)
**Section affected:** Paper-metadata enrichment
**Issue:** Semantic Scholar API returned HTTP 429 on 27, 30 and 31 (and "not in allowlist" on 25). It is being hit every run and rate-limited every time, wasting budget.
**Proposed change:**

> **Before:**
> ```
> Enrich paper metadata via Semantic Scholar API.
> ```
>
> **After:**
> ```
> arXiv RSS/Atom is the primary paper-metadata source. Query Semantic Scholar
> ONCE per run at most, with a single retry after 5s on 429; if still 429, skip
> and note "Semantic Scholar rate-limited" in Gaps. Do not loop.
> ```

**Why this helps:** Stops the repeated 429 churn and makes arXiv (which works) the authority.
**Risk:** Marginally fewer citation-count enrichments; arXiv already carries the needed fields.

### Patch 4 — Give the Overview markets snapshot a reachable equity-index source
**Target prompt:** Morning brief
**Section affected:** "Markets pre-open snapshot"
**Issue:** Asian equity close and US futures are unavailable every weekday (Reuters & Yahoo Finance on the confirmed-unavailable list), so index levels are snippet-only (CNBC/TheStreet) or absent. With the Markets routine retired (2026-05-30), the Overview snapshot is now the *only* markets coverage, and it is the one data class the egress recovery did not fix. ECB FX already fetches cleanly.
**Proposed change:**

> **Before:**
> ```
> Asian close / US futures: from market aggregators if reachable; else note gap.
> ```
>
> **After:**
> ```
> Index closes: try a machine-readable CSV/JSON endpoint by curl FIRST
> (e.g. stooq.com CSV: https://stooq.com/q/l/?s=^nkx&f=sd2t2c&e=csv for Nikkei,
> ^hsi Hang Seng, ^spx S&P 500). Verify reachability before relying on it; if it
> 403s like Reuters/Yahoo, fall back to a single tagged [via snippet] aggregator
> and mark [single-source]. ECB XML remains the FX anchor (already direct).
> ```

**Why this helps:** Restores a *direct* index-close source for the orphaned markets section, reducing its snippet/single-source dependence.
**Risk:** Stooq may itself be outside the egress allowlist — the patch tells the writer to verify-then-use, not assume; if it 403s, behaviour is unchanged.

_(No fifth patch. The Cyber World-politics single-sourcing (Dimension F) is a wire-availability constraint, not a discipline fault — addressed as Open Question 4 rather than a prompt edit, since the charter already mandates honest `[single-source]` tagging, which the writers are doing.)_

---

## Cross-week trend
Fully computable this cycle (the 2026-05-24 baseline exists). See Dimension J table: portfolio direct-fetch ratio 0.035 → 0.57, Cyber via-snippet → 0, non-English <1% → ~11%, genuine T1 36% → 67%, feeds-failing 10+ → 2. The single regression-shaped item (AI/ML 0.19 red) is structural and improved on the absolute (0.085 → 0.19). Continuity is established — next week can chart whether AI/ML responds to Patch 1 and whether the non-English quota holds.

## Open questions for human review
1. **2026-05-25 Cyber+Papers brief is absent** — no `_posts/2026-05-25-cyber-papers.md` exists (Memorial Day, and the day every feed 403'd). Did the evening routine fail to fire, fail to push, or skip by design? Worth confirming it is firing on US holidays.
2. **Push-path instability on 2026-05-31.** The 31 May Overview footer reports the session's local git HTTP endpoint returned a non-fast-forward (split-cache) and the brief was published via the GitHub API instead — and crucially that **`index/stories/2026-05-31-overview.jsonl` was recorded locally but not pushed**. Unpushed dedup-index entries risk silent dedup drift next run. Recommend investigating the routine sandbox's git push path.
3. **AI/ML's 0.40 direct-fetch target may be structurally unreachable** given its lab-PR/benchmark-press content mix (the HTML lives behind 403). Either Patch 1 lifts it, or the target should be re-baselined (e.g. ≥0.25) with the understanding that vendor-announcement items are inherently snippet. Which do you prefer?
4. **Geopolitics triangulation is capped by the wire blocklist.** Reuters/AP/AFP remain unreachable, so Cyber World-politics is single-sourced to Al Jazeera or SRF (~30% single-source on that section). Is there an allowlisted or GitHub-mirrored wire substitute, or should the <25%-per-section cap be relaxed *for that section only* with a documented rationale?
5. **Weekend topic-balance target still not visible in the inputs** (carried from last week) — supply the prompt's stated ML-vs-science bias target so Dimension H can be scored numerically rather than described.
