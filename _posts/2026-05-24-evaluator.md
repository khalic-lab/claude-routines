---
layout: single
title: "Weekly Pipeline Review — 2026-05-24"
date: 2026-05-24
categories: [evaluator]
---

# Weekly Brief Pipeline Review — 2026-05-24

_Coverage: briefs from 2026-05-18 to 2026-05-24._
_Files read: 7 morning, 5 markets (Mon–Fri), 5 AI/ML, 5 cyber, 1 weekend (2026-05-23), prior review (2026-05-17-evaluator) not found._

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains cited            | ~150+ | ≥40    | 🟢 |
| T1 citation %                   | ~36%  | ≥40%   | 🟡 |
| T3 leakage count                | 0     | 0      | 🟢 |
| Non-English citation % (portfolio) | <1% | ≥10%  | 🔴 |
| Link sample pass rate           | unmeasurable | ≥90% | ⚪ |
| Fabrication count               | 0     | 0      | 🟢 |
| Single-source rate (portfolio)  | ~21% (Markets ~32%) | <20% | 🟡 |
| Empty section instances         | 4 (all Cyber "Papers") | <5 | 🟡 |
| Direct-fetch ratio (portfolio)  | 0.035 | ≥0.35  | 🔴 |
| Direct-fetch ratio (Overview)   | 0.02  | ≥0.30  | 🔴 |
| Direct-fetch ratio (Cyber+Papers) | 0.00 | ≥0.50 | 🔴 |
| Direct-fetch ratio (AI/ML)      | 0.085 | ≥0.40  | 🔴 |
| Feeds with >50% fail rate       | 10+ (all listed feeds) | 0 | 🔴 |
| Citations to confirmed-blocked domains without [via snippet] | 0 | 0 | 🟢 |
| curl vs WebFetch advantage on feeds | none — both 403 | curl wins | 🔴 |

**One-line verdict:** The feed-first / curl-first recovery has failed at the infrastructure layer. Every machine-readable feed on the writers' "verified-reachable" list now returns HTTP 403 via *both* curl and WebFetch, in every stream, every day. This evaluator independently reproduced the wall (see Dimension C/K) — and found that the sandbox egress allowlist still passes `github.com` / `raw.githubusercontent.com`, which gives two immediately actionable fixes for the cyber feeds.

---

## A–K: Detailed findings

### A. Source diversity
- **Unique domains:** well above the ≥40 floor — over 150 distinct domains across the week (news, journals, security press, vendor blogs, HF/GitHub). 🟢
- **Concentration:** no single domain exceeds ~4% of citations. The heaviest are `thehackernews.com`, `cnbc.com`, `swissinfo.ch`, `sciencedaily.com`, `nvd.nist.gov` (mostly as reference links), `huggingface.co`, `artificialanalysis.ai`, `aljazeera.com`, `npr.org`, `phys.org` — none near the 15% ceiling. 🟢
- **Tier distribution:** T3 = 0 in every footer (policy held). 🟢 T1 ≈ 36% (144 T1-attributed items vs 258 T2 vs 0 T3). 🟡 — and note this is *nominal* T1: the vast majority of "T1" items (ESA, WHO, NVD, CISA, ECB, arXiv abstracts) were retrieved via search snippet, not fetched. True fetched-T1 is near zero.
- **Linguistic:** essentially EN-only. The only non-English citation all week is Heise Online (DE) in cyber-21 and weekend. SRF (DE) and Le Temps (FR) RSS 403 every attempt. Portfolio non-English <1% vs ≥10% target. 🔴
- **Geographic:** ~6–8 countries of origin (US, CH, Qatar/AJ, Israel, UK, DE, India-finance). English-dominated but geographically varied.

### B. Aggregator leakage (critical)
- **0 violations.** No citations to news.ycombinator.com, lobste.rs, reddit, twitter/x.com, mastodon, threads, or bsky in any brief. `simonwillison.net` (personal blog) and `gjopen.com` (forecasting platform) appear but are not banned aggregators. 🟢

### C. Link health (sample-based)
- **Unmeasurable (⚪).** Per the standing rule: this evaluator's own environment hits HTTP 403 across essentially all external fetches. Direct probes (curl, `Mozilla` UA, 12s timeout):
  - `export.arxiv.org/rss/cs.LG` → **403**
  - `services.nvd.nist.gov/rest/json/cves/2.0` → **403**
  - `cisa.gov/.../known_exploited_vulnerabilities.json` → **403**
  - `quantamagazine.org/feed/`, `nature.com/nature.rss`, `ecb.europa.eu/.../eurofxref-daily.xml` → **403**
  - Sample article links `who.int/...ebola...`, `nvd.nist.gov/vuln/detail/CVE-2026-42945`, `arxiv.org/abs/2605.16787` → **all 403**
  - **Reachable:** `github.com/ggml-org/llama.cpp/releases` → **200**; `raw.githubusercontent.com/...` → **200** (see K).
- Cited-claim spot-checks therefore could not be performed against live sources. **This is itself the headline regression** (Dimension K): the feeds the writers were told are public and reachable are 403 from the evaluator too, confirming the block is the egress proxy / network policy — not WebFetch, and not a writer-side bug.
- No fabrication signal detected in the prose: where a batch was unverifiable, the writers correctly emitted "Skipped per no-fabrication rule" rather than inventing papers (cyber Papers section, multiple days). Honest failure, not confabulation. 🟢

### D. Section vitality
- All daily streams kept their core sections populated (Science, Markets, Lab blogs, New models, Benchmarks, Industry, Apple Silicon, Switzerland, World politics, Cybersecurity).
- **Structural empty: Cyber+Papers "ML research — second arXiv batch" was empty 4 of 5 days** (19, 20, 21, 23 — "0 papers, skipped per no-fabrication rule"). Only 22 May carried 3 papers (and those via abstract-page snippets, not the feed). This is the section to flag. 🟡→🔴 for that section.
- Overview "ML research" on 24 May was empty by design (Sunday, no arXiv announcement) — not a failure.
- Total non-by-design empty instances = 4, just under the <5 threshold, but all concentrated in one section driven entirely by the arXiv block.

### E. Coverage-gap recurrence (≥3 = structural)
Clustered from the Gaps footers:
1. **arXiv batch unconfirmable / all feeds 403** — every brief, every day (structural, ~23×).
2. **ECB canonical EUR/CHF reference rate unavailable** — every Markets brief + most Overviews (structural, ≥10×).
3. **NVD CVE count unconfirmed / CISA KEV status only via T2 press** — every Cyber brief (structural, 5×).
4. **FR/DE source content blocked** — Overview 18, Markets 20, Cyber 23, Weekend (structural, ≥4×).
5. **SPI (Swiss Performance Index) close unavailable** — Markets 18, 20, 21, 22 (structural, 4×).
6. **US pre-open / live futures** — Overview 18, Markets several.
Gaps 1–4 all collapse to the same root cause (egress). Gap 5 (SPI) and the FX gaps are partly data-availability, partly egress.

### F. Triangulation rate ([single-source])
- Portfolio ≈ 21% — just over the <20% target. 🟡
- **Markets is the clear offender:** single-source rate 20% / 31% / 50% / 23% / 36% on 18–22 May (avg ~32%, three of five days above the 25% per-stream cap). The writer's own footers flag this and attribute it to the dead ECB feed forcing FX, gold, and oil onto single aggregators. 🔴 for Markets.
- Overview 22 May ran all four Science items as `[single-source]` simultaneously — a one-day spike worth noting.

### G. Tag discipline
- **[preprint]:** consistently applied to every arXiv item (sampled weekend ×11, overview ×4 — all tagged). 🟢
- **[vendor PR]:** consistently applied to Gemini/Anthropic/OpenAI/Cohere/Gemma announcements. 🟢
- **[disputed]:** used ~3× and appropriately (Markets-21 SMI ^SSMI vs CH20 discrepancy; Markets-22 DAX direction outlier; Cyber-19 Lebanon ceasefire).
- **[via snippet] by stream:** Overview 93, Markets 71, AI/ML 119, Cyber 104, Weekend 51 — i.e. **near-100% of all citations**. The curl-first rollout was supposed to make this *drop*; instead it is flat-high across every stream, confirming feeds are failing in every sandbox. 🔴 This is the single clearest symptom that the recovery did not take.

### H. Topic balance (weekend brief)
- Weekend ML/AI papers ≈ 11 (Unlearnability, Beyond-Reasoning, Own-Critic, DASH, TIM, MARLIN, Emergent-Misalignment, ExpThink, SDAR, Spec-Decoding latency, +). Fundamental-science papers ≈ 8 (Talagrand, Erdős/OpenAI, Condensed sets, Area-law, Q-CTRL, JWST cosmic web, TOI-199b, white hydrogen). Split ≈ 58% ML / 42% science in the paper sections; biology runs as a separate well-populated section.
- The exact stated bias target for the weekend prompt is not visible in these inputs, so a precise ±10pp deviation flag cannot be computed. The split looks reasonable and slightly ML-tilted; no action proposed pending the target.

### I. Repetition detection
Several stories ran for many consecutive days with thinning new information — largely because no fresh fetchable inputs were available, so writers re-litigated older events:
- **Google I/O 2026 / Gemini 3.5 Flash** — AI/ML 19, 20, 21, 22, 23 (5 consecutive days; by 22–23 it is "wrap" recycling of the same May-19 numbers).
- **EU AI Act omnibus (the May-7 event)** — AI/ML 20, 21, 22, 23 (4×, re-explained each time).
- **Swiss Bilaterals III / SVP "10 million" initiative** — Cyber Switzerland section 19, 20, 21, 22, 23 (5×, low development).
- **NCSC annual report (64,733 reports)** — Cyber 20, 22, 23 (3×, same figures).
- Justified multi-day threads (genuinely developing): Iran/Hormuz, TanStack/TeamPCP supply-chain worm, NGINX CVE-2026-42945 → nginx-poolslip.
The repetition is a *downstream symptom* of the feed outage, not an independent editorial fault.

### J. Cross-week trend
- **Not computable** — the 7-day-prior anchor `2026-05-17-evaluator.md` does not exist. (Evaluator files exist only for 2026-05-02 and 2026-05-03, both outside the trend window.) No trend lines for direct-fetch rate, via-snippet rate, or T3 leakage this cycle. Recommendation: ensure the evaluator routine itself is firing weekly so next week has a baseline.

### K. Feed reachability & direct-fetch rate (binding constraint — primary lens)

**Per-stream direct-fetch ratio (direct ÷ (direct + via-snippet), from Coverage footers):**

| Stream | Per-day direct/snippet | Total | Ratio | Target | Status |
|---|---|---|---|---|---|
| Overview | 0/18, 1/17, 0/11, 0/14, 1/11, 0/13, 0/9 | 2 / 95 | **0.02** | ≥0.30 | 🔴 |
| Markets | 0/13, 0/16, 0/13, 0/13, 0/16 | 0 / 71 | **0.00** | ≥0.20 | 🔴 |
| AI/ML | 1/22, 6/24, 1/24, 3/22, 0/27 | 11 / 130 | **0.085** | ≥0.40 | 🔴 |
| Cyber+Papers | 0/21, 0/21, 0/23, 0/22, 0/17 | 0 / 104 | **0.00** | ≥0.50 | 🔴 |
| Weekend | 3/51 | 3 / 54 | **0.056** | ≥0.30 | 🔴 |
| **Portfolio** | | **16 / 454** | **0.035** | ≥0.35 | 🔴 |

Every stream is below range; the portfolio sits ~10× under target. Note the few "direct fetches" that exist are **not** the intended feeds — they are HuggingFace **MCP** calls (paper/hub metadata) and `github.com/ggml-org/llama.cpp/releases`. No arXiv, NVD, CISA, ECB, Nature, or Quanta feed was fetched successfully **even once** all week.

**Per-feed reachability (aggregated across the week, with method):**

| Feed | Result | Note |
|---|---|---|
| arXiv RSS (cs.LG/AI/CL/CV, stat.ML) | **fail 100%** — 403 curl + 403 WebFetch | every day, every category |
| arXiv Atom API | fail 100% — 403 curl + WebFetch | |
| NVD CVE JSON 2.0 | fail 100% — 403 curl / empty body (TLS-inspection zero-byte) | |
| CISA KEV JSON (cisa.gov) | fail 100% — 403 curl + WebFetch | |
| Nature RSS (nature.rss, nphys, etc.) | fail 100% — 403 curl | |
| Quanta RSS | fail 100% — 403 curl + WebFetch | |
| ECB FX XML | fail 100% — 403 curl + WebFetch | |
| SRF (DE) / Le Temps (FR) / Al Jazeera RSS | fail 100% — 403 curl + WebFetch | kills non-English quota |
| Semantic Scholar API | fail — 403 WebFetch | |
| HuggingFace papers (HTML) | fail — 403 | but HF **MCP** worked intermittently |
| **HuggingFace MCP tool** | **ok** (when connected; lost on 19/23/24) | not a feed — MCP transport |
| **github.com / llama.cpp releases** | **ok — 200 via curl** | only public HTTP that worked |

- **Feeds with >50% fail rate: all of them** (≥10 distinct feeds at 100% fail). 🔴
- **Method comparison (the critical test):** curl did **not** outperform WebFetch on a single feed — both return 403 on the same URLs. The curl-first patch therefore is **not** doing its job, because the wall is not WebFetch; it is the sandbox egress proxy. **Escalate.** This evaluator independently confirmed the same 403s from its own environment (Dimension C), which rules out a writer-side configuration error.
- **Domains-that-shouldn't-be-cited check:** swissinfo.ch, Yahoo Finance, and Reuters (all on the "confirmed unavailable" list) appear only ever tagged `[via snippet]`. **0 violations.** 🟢 Tag discipline here is good.

**The actionable discovery:** the egress allowlist passes `github.com` and `raw.githubusercontent.com` (both 200). The official CISA KEV and CVE data are mirrored there and are reachable from this sandbox **right now**:
- `https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json` → **200**
- `https://raw.githubusercontent.com/CVEProject/cvelistV5/main/cves/delta.json` → **200**

That single channel can move Cyber+Papers from 0.00 toward its 0.50 target without any infrastructure change. See Patches 1–2.

---

## Patch proposals (for human review)

Priority order: Dimension-K (binding-constraint) fixes first. **Patches 1 and 2 are validated by live 200-responses from this sandbox.** Patches 3–5 are honesty/discipline fixes that work regardless of egress. None of these can substitute for the real remedy, which is restoring egress or expanding the allowlist (see Open Questions).

### Patch 1 — Route CISA KEV through the reachable GitHub mirror
**Target prompt:** Cyber-Papers
**Section affected:** Cybersecurity / feed-fetch preamble + Coverage "Feeds hit"
**Issue:** `cisa.gov/.../known_exploited_vulnerabilities.json` returns 403 from the sandbox on every attempt (5/5 days). The official KEV data is mirrored on GitHub, which the egress allowlist passes (verified 200).
**Proposed change:**

> **Before:**
> ```
> Fetch CISA KEV JSON:
>   curl https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
>   (fallback: WebFetch same URL)
> ```
>
> **After:**
> ```
> Fetch CISA KEV JSON (GitHub mirror — egress-allowlisted):
>   curl -sSL https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json
>   (only if that fails, try cisa.gov canonical, then WebFetch)
> Items confirmed from this mirror count as Direct fetches and may drop [via snippet].
> ```

**Why this helps:** Restores genuine direct fetches for the most reliable cyber feed; should lift Cyber direct-fetch ratio off 0.00 toward target.
**Risk:** The mirror's branch/path could change; keep the cisa.gov canonical as a documented fallback and re-verify the raw path monthly.

### Patch 2 — Route CVE lookups through the CVEProject GitHub mirror instead of NVD JSON
**Target prompt:** Cyber-Papers (and the Overview ML/science CVE references)
**Section affected:** Cybersecurity / CVE enrichment
**Issue:** `services.nvd.nist.gov/rest/json/cves/2.0` returns 403 / zero-byte body every day; CVE details are currently sourced entirely from T2 security press. The official CVE List V5 is on GitHub (verified 200).
**Proposed change:**

> **Before:**
> ```
> Enrich CVEs via NVD JSON 2.0 API (services.nvd.nist.gov). If 403, cite vendor/T2.
> ```
>
> **After:**
> ```
> Enrich CVEs via the CVE List V5 GitHub mirror (egress-allowlisted):
>   https://raw.githubusercontent.com/CVEProject/cvelistV5/main/cves/<YEAR>/<sub>/CVE-YYYY-NNNNN.json
>   (delta feed: .../main/cves/delta.json for the day's new/updated records)
> Fall back to NVD JSON, then T2 press, only if the mirror lacks the record.
> ```

**Why this helps:** Replaces snippet-only CVE sourcing with authoritative direct fetches for the canonical record; improves both direct-fetch ratio and citation quality.
**Risk:** CVE List V5 carries the CNA record but not the NVD-enriched CVSS/CPE; keep citing NVD as the canonical reference link even when the data body comes from the mirror, and note CVSS provenance.

### Patch 3 — Make HuggingFace MCP the primary ML-paper channel; stop burning the run on dead arXiv routes
**Target prompt:** AI/ML and Cyber-Papers (ML batch sections)
**Section affected:** "ML research — arXiv batch" fetch logic
**Issue:** arXiv RSS/Atom/HTML are 403 100% of the time via curl *and* WebFetch; the routines retry all of them every run and then fall back to snippets. The only thing that ever returned paper data is the HuggingFace MCP tool. The Cyber Papers section was empty 4/5 days as a result.
**Proposed change:**

> **Before:**
> ```
> 1. Try arXiv RSS (cs.LG, cs.AI, cs.CL, cs.CV, stat.ML) via curl, then WebFetch.
> 2. Try arXiv Atom API. 3. Try HTML listings. 4. Fall back to HuggingFace.
> ```
>
> **After:**
> ```
> 1. Query HuggingFace MCP (paper_search / daily papers) FIRST — it is the only
>    paper source currently reachable; treat returned IDs+dates as the batch.
> 2. Make ONE arXiv RSS attempt purely to log reachability for the evaluator,
>    then stop — do not re-try Atom/HTML once the 403 pattern is seen.
> 3. If HF MCP connection is lost, emit the no-fabrication skip note (current behaviour).
> ```

**Why this helps:** Spends the run's budget on the channel that works, reduces the empty-Papers instances, and stops the misleading "tried everything" churn.
**Risk:** HF MCP coverage is narrower than full arXiv and its connection dropped on 19/23/24; on those days the section legitimately skips. Acceptable given the alternative is zero either way.

### Patch 4 — Correct the stale "Verified-reachable feeds (live 2026-05-04)" block in every writer prompt
**Target prompt:** All five (shared sourcing-charter block)
**Section affected:** Feed-first reference list
**Issue:** The prompt asserts arXiv, NVD, CISA KEV, Quanta, Nature, ECB, SRF, Le Temps, Al Jazeera, Semantic Scholar are "verified-reachable (live 2026-05-04)." As of 2026-05-18→24 every one of them is 403 from both the writer sandbox and this evaluator. The list is now false and is causing wasted retries and nominal-T1 inflation.
**Proposed change:**

> **Before:**
> ```
> Verified-reachable feeds (live 2026-05-04): arXiv RSS/Atom, NVD JSON, CISA KEV
> JSON, Quanta RSS, Nature RSS, Al Jazeera RSS, ECB FX XML, SRF/Le Temps RSS,
> Semantic Scholar API. Prefer curl before WebFetch.
> ```
>
> **After:**
> ```
> Reachability (re-verified 2026-05-24): the sandbox egress proxy 403s ALL public
> RSS/JSON/HTML feeds via BOTH curl and WebFetch. curl-first does NOT bypass it.
> Currently reachable: github.com + raw.githubusercontent.com (200), and MCP tools
> (HuggingFace). Prefer GitHub-hosted mirrors of canonical data (CISA KEV, CVE List
> V5, llama.cpp releases). Everything else is snippet-only until egress is restored;
> tag accordingly and do not report snippet-sourced items as fetched T1.
> ```

**Why this helps:** Stops the routines from chasing dead feeds, makes the [via snippet]/T1 accounting honest, and points them at the channel that works.
**Risk:** If egress is restored, this block must be reverted; date-stamp it so the next evaluator catches staleness.

### Patch 5 — Tighten Markets single-source discipline given the dead FX feed
**Target prompt:** Markets
**Section affected:** FX / commodities bullets + Coverage footer
**Issue:** Markets single-source rate hit 50% (20 May) and 31–36% on three of five days, above the 25% cap. Root cause: ECB FX XML 403 forces EUR/CHF, gold, and oil onto one aggregator each. Several runs also reported aggregator-sourced ECB rates as nominal T1.
**Proposed change:**

> **Before:**
> ```
> FX: report EUR/CHF, USD/CHF from ECB reference; if ECB feed unavailable, use a
> market aggregator. Tag [single-source] where only one source is found.
> ```
>
> **After:**
> ```
> FX/commodities: with ECB XML unreachable, require >=2 independent aggregators
> (e.g. exchange-rates.org + tradingeconomics + xe) before stating a level; only
> then may the [single-source] tag be dropped. Never label an aggregator-sourced
> EUR/CHF as T1 — it is T2 [via snippet] until the ECB feed is fetched directly.
> ```

**Why this helps:** Brings the Markets single-source rate under the cap honestly and stops T1 inflation on FX.
**Risk:** Slightly fewer FX data points on quiet days; acceptable trade for accuracy.

---

## Cross-week trend
Not applicable this cycle — no `2026-05-17-evaluator.md` baseline exists. Establish weekly evaluator continuity so the 2026-05-31 review can chart direct-fetch ratio and via-snippet trends.

## Open questions for human review
1. **Egress is the binding constraint, not the prompts.** The single highest-value action is outside any writer prompt: restore the sandbox's outbound network policy, or expand the egress allowlist to include arXiv, NVD/NIST, CISA, ECB, Nature, and the FR/DE news hosts. Patches 1–2 are a stopgap via GitHub mirrors, not a substitute. Can the network policy for the routine sandbox be widened?
2. **Is there a probe/canary routine?** A tiny daily job that curls 3–4 feeds and records HTTP codes would have flagged this regression on ~2026-05-05 instead of it persisting silently for ~3 weeks. Worth adding.
3. **Non-English quota (RED, <1%).** SRF and Le Temps RSS both 403 and I found no reachable FR/DE substitute. Is there a GitHub-mirrored or otherwise allowlisted Swiss FR/DE source we can point the writers at? Without one, the ≥10% non-English target is unreachable and should perhaps be suspended (with a note) rather than chronically failed.
4. **arXiv has no obvious GitHub mirror.** HF MCP is the only working paper channel and it is flaky (connection lost 3 of 7 days). Is a more stable arXiv mirror (e.g. a Kaggle/GitHub metadata dump, or arxiv.org proxied through an allowlisted host) worth wiring in?
5. **Weekend topic-balance target** is not visible in the briefs; supply the stated ML-vs-science bias target so Dimension H can be scored numerically next week.
