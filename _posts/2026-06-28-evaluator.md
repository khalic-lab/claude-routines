---
layout: single
title: "Weekly Pipeline Review — 2026-06-28"
date: 2026-06-28T11:45:00+02:00
categories: [evaluator]
published: true
---

_Coverage: briefs from 2026-06-22 to 2026-06-28._
_Files read: 7 morning/overview, 5 AI/ML (06-24 and 06-28 absent), 6 cyber (06-28 pending), 1 weekend (2026-06-27), prior review **not found** (expected 2026-06-21 evaluator is missing; last on disk is 2026-06-14, used for trend)._

Last week's review had a single unambiguous finding: the **AI/ML stream was failing the feed-first recovery** at a 0.12 direct-fetch ratio with 71 `[via snippet]` citations and no `Feeds hit` line at all. **That finding has reversed.** This week AI/ML runs a **0.67** direct-fetch ratio, **14** via-snippet citations (down 80%), and started emitting a `Feeds hit` line. Patch 1 from 2026-06-14 evidently landed and worked. Every stream is now above its dimension-K target and the portfolio direct-fetch ratio is **0.93**. The curl-first architecture is doing its job across the board.

The residual issues this week are smaller and mostly about **bookkeeping honesty rather than reachability**: the "confirmed-unavailable" domain list has gone stale (bioRxiv/medRxiv are now proxy-reachable and being cited as direct fetches without `[via snippet]`), a cross-day exact-URL dedup miss let the same Quanta Erdős story run two mornings in a row, and last week's Patch 5 (per-source `[via snippet]` inside triangulation bundles) did not fully land. There is also a pair of **operational gaps** worth a human glance: the AI/ML brief did not publish on Wednesday 06-24, and the 2026-06-21 evaluator never ran — the second skipped evaluator Sunday in three weeks.

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains cited            | ~59   | ≥40    | 🟢 |
| T1 citation %                   | ~57%  | ≥40%   | 🟢 |
| T3 leakage count                | ~3    | 0      | 🟡 |
| Non-English citation % (portfolio) | ~14% | ≥10% | 🟢 |
| Link sample pass rate           | JSON/Atom feeds 100% / RSS-over-HTTPS proxy-walled in eval env | ≥90% | 🟡 |
| Fabrication count               | 0     | 0      | 🟢 |
| Single-source rate (portfolio)  | ~9%   | <20%   | 🟢 |
| Empty section instances         | 3     | <5     | 🟢 |
| Direct-fetch ratio (portfolio)  | 0.93  | ≥0.35  | 🟢 |
| Direct-fetch ratio (Overview)   | 0.97  | ≥0.30  | 🟢 |
| Direct-fetch ratio (Cyber+Papers) | 0.99 | ≥0.50 | 🟢 |
| Direct-fetch ratio (AI/ML)      | **0.67** | ≥0.40 | 🟢 |
| Feeds with >50% fail rate       | 0     | 0      | 🟢 |
| Citations to confirmed-blocked domains without [via snippet] | ~11 (bioRxiv/medRxiv proxy-reached + 1 swissinfo) | 0 | 🟡 |
| curl vs WebFetch advantage on feeds | curl wins decisively | curl wins | 🟢 |

## A–K: Detailed findings

### A. Source diversity
~59 unique domains across ~307 citation links — comfortably above the ≥40 floor. Top domains by count: `arxiv.org` (~78), `nvd.nist.gov` (39), `nature.com` (~29), `letemps.ch` (21), `aljazeera.com` (19), `srf.ch` (15), `huggingface.co` (9), `openai.com` (8), `biorxiv.org` (9 incl. weekend), `cisa.gov` (3).

**Concentration:** `arxiv.org` ≈ 78/307 = **25%**, over the 15% threshold — flagged, but benign for the same architectural reason as last week: arXiv is the primary preprint feed for the Overview science section, the cyber-papers ML batch, and the entire weekend papers run, so concentration here is the design working, not a sourcing failure. `nvd.nist.gov` at 13% is the CVE primary source (same logic).

**Tier distribution:** T1 ≈ 57% (arXiv, NVD, CISA, Nature/Nature Medicine, bioRxiv/medRxiv primaries, official lab pages — openai/anthropic/mistral/qualcomm/ibm/whitehouse.gov — vendor advisories, and security-research labs SentinelOne/Unit42/Mandiant/Talos). Comfortably ≥40%. T3 ≈ 3 and is the only blemish: `codingfleet.com`, `kucoin.com` (a crypto exchange, an odd citation in an AI funding item on 06-27), `36kr.com` (Chinese tech media, T2–T3), and `techstartups.com` (which was on last week's proposed AI/ML deny-list). Much improved from ~9 last week.

**Linguistic:** ~43 non-English citations (`letemps.ch` FR 22, `srf.ch` DE 17, `swissinfo.ch` 2, `derbund.ch` DE 1, `36kr.com` ZH 1) ≈ **14%** portfolio-wide, above the ≥10% floor. As before, this is carried almost entirely by the cyber-papers stream's Swiss/French sourcing; the Overview (science) and AI/ML streams are near-monolingual by topic.

**Geographic:** ~8 countries represented in the news sections (CH, US, Qatar/AJ, UK, France, China, EU institutions, plus arXiv international). Healthy.

### B. Aggregator leakage
**Clean.** Zero hits for `news.ycombinator.com`, `lobste.rs`, `reddit.com`, `twitter.com`, `x.com`, `mastodon.social`, `threads.net`, `bsky.app` across all window briefs and the weekend. 🟢

### C. Link health (sample-based)
Feed probes via curl **from the evaluator's own environment**:

| Feed | Result |
|------|--------|
| NVD CVEs JSON 2.0 | **200** |
| CISA KEV JSON | **200** |
| arXiv Atom API | **200** |
| Quanta RSS | **200** |
| ECB FX XML | **200** |
| Al Jazeera RSS | **200** |
| SRF DE RSS | **200** |
| Le Temps FR RSS | **200** |
| `rss.arxiv.org` RSS | proxy **CONNECT 403** |
| `nature.com` natastron.rss / nature.rss | proxy **CONNECT 403 / 303** |

The load-bearing JSON and Atom feeds (NVD, CISA KEV, arXiv Atom API, Quanta, ECB, AJ, SRF, Le Temps) **all resolve cleanly (200)** — **no regression** on the feeds that matter, confirming the writers' curl-first results are real. The only failures are `rss.arxiv.org` and the `nature.com` RSS hostnames, which the **evaluator's own egress proxy** 403s at the CONNECT-tunnel stage. The writers report these same RSS hosts as `{ok via curl}` most days, so this is an **evaluator-environment egress difference, not a confirmed writer regression** — though note the writers *also* saw `nature.rss` fail on 06-28 ("empty body via curl, ok via proxy") and `nphys/natastron.rss` 403 on 06-26, so Nature's RSS endpoints are genuinely flaky on both sides. **No fabrications detected** in spot-checks; the briefs remain conspicuously careful about not asserting numbers they couldn't fetch (e.g. the 06-28 IBM-chip item explicitly flags vendor numbers and routes around the Science.org 403). Marked 🟡 because the RSS-over-HTTPS half is unmeasurable from this environment, not because anything is broken.

### D. Section vitality
No fully unexplained empty sections. Three "empty/skipped" instances, all attributable to arXiv's weekend/Monday announcement schedule:
- Overview "📄 ML research — first arXiv batch": "Nothing notable" on **06-28** (Sunday, all five ML feeds empty — expected).
- Cyber-papers "📄 ML research — second arXiv batch": skipped **06-22** (Monday channel empty, no verifiable batch) and **06-27** (no weekend batch).

That's 3 instances, under the <5 threshold, and each is honestly logged in the Gaps footer rather than left blank. No single section hit ≥3. 🟢

### E. Coverage gap recurrence
The recurring (≥3×) clusters this week:
1. **arXiv RSS empty on Monday/weekend** (06-22, 06-23, 06-27, 06-28) — the dominant recurring gap, but **mitigated by design**: writers fall back to the date-filtered Atom API and say so. Structural but handled.
2. **Nature / journal HTML and RSS flakiness** — `nphys.rss`/`natastron.rss` 403 (06-26), `nature.rss` empty body (06-28); article pages paywalled, abstracts via proxy. Recurring, partially handled via proxy fallback.
3. **Swiss-media JS-render/paywall** — SRF and Le Temps article bodies are JS-rendered or paywalled (06-26, 06-27), so the Swiss bullets lean on RSS descriptions + triangulation. Recurring (2×), handled.

None of these is a new structural hole; all three are known walls the writers already route around.

### F. Triangulation rate
~27 `[single-source]` tags total (Overview 6, AI/ML 4, Cyber ~15, Weekend 2) against ~307 citations ≈ **8.8%** portfolio-wide, well under the 20% floor. Per stream the highest is cyber at ~11% — and most of those are NVD/CISA **primary-authoritative** CVE items where triangulation isn't meaningful (a CVE record *is* the source of truth). No stream exceeds 25%. 🟢

### G. Tag discipline
- `[preprint]`: ~63 uses across the dailies plus near-universal use in the weekend papers sections; arXiv items consistently tagged. 🟢
- `[vendor PR]`: ~7 daily uses + 2 weekend, correctly applied to vendor announcements (Mistral OCR4, Qwen-AgentWorld, Ornith-1.0, the 06-28 IBM chip). 🟢
- `[disputed]`: used appropriately — the Venezuela death toll (06-25/06-26, "235 vs 500+", explicitly not reconciled). 🟢
- `[via snippet]`: **17 total — Overview 2, AI/ML 14, Cyber 1, Weekend 0.** Down from 104 last week (AI/ML 71→14). The AI/ML residual concentrates on **06-26** (9, the GPT-5.6 preview day — a commercial launch arXiv/HF can't cover) and **06-23** (3, lab blogs whose bodies are JS-rendered). This is exactly the expected irreducible residual: genuine commercial-launch news with no machine-readable feed. The curl-first patch is unambiguously working. 🟢

### H. Topic balance (weekend brief)
The 2026-06-27 weekend brief runs **10 ML/AI papers** and **8 fundamental-science papers** — a 56%/44% split, a 6pp deviation from a ~50/50 target, **under the 10pp flag threshold**. 🟢 The brief is RL-heavy by the week's actual research distribution (4 of 10 ML papers are RL methods/systems), which it states explicitly. Dedup is visibly working in the weekend: RiVER and CARVE (already in the dailies) were excluded, and the two headline model releases (Ornith-1.0, Qwen-AgentWorld) were demoted to `[ongoing since]` pointers rather than re-reported. This also addresses the 2026-06-20 reader note ("accept the best of the best for the week, not only stuff from that day") — the brief pulls the strongest items from the whole 06-20→06-27 window.

### I. Repetition detection
Dedup is mostly catching repeats well (Splunk CVE, NANOG embryo editing, HPV mortality, Mars magmatism, SnTe Floquet insulator all explicitly dropped as REPEAT/ONGOING across days). **One miss, confirmed:** the Ramsey-number / probabilistic-method improvement (Quanta 2026-06-26, arXiv 2507.12926) ran in **both** the 06-27 Overview (line 18) **and** the 06-28 Overview — citing the **same Quanta URL** both mornings. The 06-28 Gaps footer deduped four other items but not this one. Because it's an **exact-URL** repeat on consecutive days, it should have been the easiest possible dedup catch. Minor (one item, no fabrication), but it points at a real gap — see Patch 3. (Note: this is distinct from Eric Li's two Erdős *problems* in the weekend brief — different papers.)

### J. Cross-week trend (vs 2026-06-14)
The expected 2026-06-21 evaluator is **missing**, so there's no week-over-week line from the immediately prior review; I'm comparing to 2026-06-14.

| Metric | 2026-06-14 | 2026-06-28 | Trend |
|--------|-----------|-----------|-------|
| AI/ML direct-fetch ratio | **0.12** | **0.67** | ▲ recovered (Patch 1 landed) |
| AI/ML via-snippet total | 71 | 14 | ▲ −80% |
| AI/ML `Feeds hit` line | never | 2 of 5 days | ▲ partial |
| Portfolio direct-fetch ratio | 0.70 | 0.93 | ▲ |
| T3 leakage | ~9 | ~3 | ▲ |
| Aggregator citations | 0 | 0 | ▬ clean |
| Confirmed-blocked w/o `[via snippet]` | ~1 (swissinfo) | ~11 (bioRxiv/medRxiv proxy + swissinfo) | ▼ but see §K — list is stale, not a new failure |

**Prior-patch application status:** Patch 1 (AI/ML curl-first feeds) clearly **landed** — the single biggest improvement of the week. Patch 5 (per-source `[via snippet]` on blocked domains inside bundles) **did not fully land** — swissinfo appears untagged in a 06-25 triangulation bundle (see §K, Patch 4). The other 2026-06-14 patches (T3 deny-list, market-data rule, Nature→arXiv fallback) are harder to confirm from the output alone but show no obvious violations.

### K. Feed reachability and direct-fetch rate — **primary lens**

**Per-stream direct-fetch (N direct / M via-snippet per day → ratio):**

| Stream | Per-day (direct/snippet) | Mean ratio | Week snippet total | Verdict |
|--------|--------------------------|-----------|--------------------|---------|
| Overview | 8/0, 11/0, 11/0, 14/0, 14/0, 12/0, 5/2 | **0.97** | 2 | ✅ (≥0.30) |
| AI/ML | 5/0, 2/3, 11/0, 4/9, 6/2 (06-24, 06-28 absent) | **0.67** | 14 | ✅ (≥0.40) |
| Cyber+Papers | 18/1, 16/0, 14/0, 14/0, 18/0, 14/0 (06-28 pending) | **0.99** | 1 | ✅ (≥0.50) |
| Weekend | 38/0 | **1.00** | 0 | ✅ (≥0.30) |

Portfolio: 235 direct / 252 total = **0.93**. Every stream is above its target for the first time on record. The AI/ML reversal is the story: from 0/10–type days last month to a 0.67 mean, with the only remaining snippet clusters being genuine commercial launches (GPT-5.6) and JS-rendered lab blogs.

**Per-feed reachability (aggregated, with method):**

| Feed | Result | Notes |
|------|--------|-------|
| NVD JSON / CISA KEV JSON | ok via curl, all days | rock-solid both in briefs and in eval probe |
| arXiv Atom API | ok via curl, all days | the workhorse fallback when RSS is empty |
| arXiv category RSS | ok via curl, but **empty** Mon/weekend | expected (announcement schedule), not a failure |
| Quanta / ECB / Al Jazeera / SRF / Le Temps RSS | ok via curl | confirmed 200 in eval probe |
| Nature nature.rss/nphys.rss/natastron.rss | flaky | curl OK most days; 403 on 06-26, empty body 06-28 → proxy fallback |
| bioRxiv / medRxiv details API | ok **via proxy** most days | empty body via proxy on 06-28 only |
| Science.org article HTML | fail — 403 | confirmed-unavailable, expected; news RSS works via proxy intermittently |
| drbex.io | fail — HTTP 530 | non-load-bearing |

**Feeds with >50% fail rate:** none with a meaningful sample. Nature's RSS trio is the flakiest core feed but still succeeds the majority of attempts via curl-or-proxy. 🟢

**Method comparison:** **curl wins decisively.** Every load-bearing feed success is `{ok via curl}`; the proxy is the second-line fallback for bioRxiv/medRxiv, Nature article HTML, and lab/security blogs; WebFetch barely appears. The curl-first patch is working as intended across all four streams. 🟢

**Confirmed-unavailable domains cited — the one real §K nuance this week:**
`bioRxiv` and `medRxiv` are on the writers' "confirmed unavailable — skip / only `[via snippet]`" list, **but they are now being reached successfully through the fetch-proxy** (`bioRxiv details API {ok via proxy}` appears in the footers) and cited as **direct fetches without** `[via snippet]` — 6 in the Overview (06-22 ×3, 06-24 ×3) plus 3 bioRxiv + 1 medRxiv in the weekend brief. By the strict audit rule this is ~10 violations; in reality it means **the unavailable list is stale** — the proxy capability now reaches these primaries, so the right fix is to *update the list*, not to force `[via snippet]` onto content that was genuinely fetched (see Patch 1). Separately, `swissinfo.ch` (genuinely unavailable) appears in a 06-25 cyber triangulation bundle as a secondary link **without its own** `[via snippet]` tag (the Le Temps primary is fine) — a recurrence of last week's Patch 5 issue (Patch 4). Marked 🟡.

## Patch proposals (for human review)

### Patch 1 — Update the "confirmed-unavailable" feed list: bioRxiv/medRxiv are now proxy-reachable
**Target prompt:** Shared sourcing note (applies to Overview science + Weekend brief primarily)
**Section affected:** Sourcing / confirmed-unavailable list + `[via snippet]` rule
**Issue:** bioRxiv and medRxiv are listed as "confirmed unavailable — only `[via snippet]`," yet the briefs now reach them via the fetch-proxy (`{ok via proxy}`) and cite them as direct fetches. The audit rule then false-positives ~10 "blocked-domain without `[via snippet]`" violations on content that was genuinely fetched.
**Proposed change:**

> **Before:**
> ```
> Confirmed unavailable (skip / cite only [via snippet]): bioRxiv, medRxiv,
> Science.org, RTS.ch, NZZ, FAZ, Spiegel, swissinfo.ch, Reuters, Yahoo Finance,
> HuggingFace papers, Le Monde RSS, NCSC.ch RSS.
> ```
>
> **After:**
> ```
> Proxy-reachable primaries (cite directly, NO [via snippet] when {ok via proxy}):
>   bioRxiv / medRxiv details API.
> Confirmed unavailable (cite only [via snippet]): Science.org article HTML, RTS.ch,
>   NZZ, FAZ, Spiegel, swissinfo.ch, Reuters, Yahoo Finance, HuggingFace papers,
>   Le Monde RSS, NCSC.ch RSS.
> If a proxy fetch returns an empty body (as bioRxiv did on a weekend run), fall
> back to [via snippet] for that item only and note it in the footer.
> ```

**Why this helps:** Stops penalising successfully-fetched primary preprints and keeps the blocked-domain audit meaningful (only genuinely unreachable domains flag).
**Risk:** If the proxy route for bioRxiv degrades, items could be mis-tagged as direct; the empty-body fallback clause mitigates this.

### Patch 2 — AI/ML: make the `Feeds hit` line mandatory every day
**Target prompt:** AI-ML
**Section affected:** Coverage footer
**Issue:** The AI/ML stream recovered its direct-fetch ratio (0.67) but emitted a `Feeds hit` line only **2 of 5 days** (present 06-23, 06-25; absent 06-22, 06-26, 06-27). Without it, feed health in this stream is only intermittently observable — and 06-26 (the worst snippet day, 9) is exactly a day with no line.
**Proposed change:**

> **Before:**
> ```
> Footer SHOULD include a "Feeds hit" line listing each feed's reachability/method.
> ```
>
> **After:**
> ```
> Footer MUST include a "Feeds hit (with reachability and method)" line EVERY day,
> even on quiet/commercial-launch days — list each feed attempted as {ok via curl} /
> {ok via WebFetch/proxy} / {fail — HTTP NNN}. On days where most news is
> snippet-sourced commercial launches, still report the arXiv/HF/lab-blog feed
> attempts so the via-snippet count is attributable to "no feed exists," not "feed
> not tried."
> ```

**Why this helps:** Consolidates the recovery into a reliably observable metric and distinguishes "no feed covers this launch" from "writer skipped the feeds."
**Risk:** None material — reporting only.

### Patch 3 — Overview/dedup: catch cross-day exact-URL repeats
**Target prompt:** Morning brief (Overview) — dedup step
**Section affected:** Dedup / repeat detection
**Issue:** The Quanta Erdős/Ramsey item (same URL `…erdos-method-an-upgrade-20260626`) ran in both the 06-27 and 06-28 Overview. An exact-URL match on the immediately prior day's brief should be the easiest dedup catch, but it slipped through.
**Proposed change:**

> **Before:**
> ```
> Run the dedup check against the rolling embeddings index before drafting.
> ```
>
> **After:**
> ```
> Run the dedup check against the rolling index AND, as a cheap belt-and-braces
> step, exact-URL-match every candidate link against yesterday's same-stream brief
> (_posts/{D-1}-overview.md). Any exact-URL hit is an automatic REPEAT drop unless
> the item carries a genuinely new dated fact, in which case tag it
> [ongoing since {first-date}].
> ```

**Why this helps:** A near-zero-cost guard against the most obvious repeat class (same source URL on consecutive days), independent of embedding-similarity thresholds.
**Risk:** Could over-drop a legitimately-developing story that reuses one explainer URL; the `[ongoing since]` escape hatch covers that.

### Patch 4 — Per-source `[via snippet]` inside triangulation bundles (recurrence of 2026-06-14 Patch 5)
**Target prompt:** Cyber-Papers + shared sourcing note
**Section affected:** Citation tagging
**Issue:** `swissinfo.ch` (confirmed-unavailable) appears as the secondary link in a 06-25 triangulation bundle ("triangulated: [SWI swissinfo …]") without its own `[via snippet]` tag. This is the same issue Patch 5 flagged last week; it did not fully land.
**Proposed change:**

> **Before:**
> ```
> In multi-source / triangulated bundles, tag the citation group once.
> ```
>
> **After:**
> ```
> Any citation to a confirmed-unavailable domain (swissinfo.ch, reuters.com,
> yahoo finance, rts.ch, nzz.ch, science.org HTML, etc.) MUST carry its own
> [via snippet] tag, even as a SECONDARY "triangulated:" link in a bundle whose
> primary is a directly-fetched source. Never let a group-level tag (or the
> primary's clean status) cover a blocked secondary.
> ```

**Why this helps:** Keeps the blocked-domain audit unambiguous and closes a gap that's now persisted two weeks.
**Risk:** None material — tagging only.

### Patch 5 — AI/ML: extend the T3 deny-list
**Target prompt:** AI-ML
**Section affected:** Source tiering
**Issue:** Three low-tier domains slipped into AI/ML this week: `codingfleet.com`, `kucoin.com` (a crypto exchange cited in a funding item, 06-27), and `36kr.com`. `techstartups.com` (already proposed for the deny-list last week) recurred on 06-25.
**Proposed change:**

> **Before:**
> ```
> Never cite: aiweekly.co, aitoolsrecap.com, codersera.com, techtimes.com,
> techstartups.com, swfte.com, benchlm.ai, releasebot.io (T3 / SEO blogspam).
> ```
>
> **After:**
> ```
> Never cite: aiweekly.co, aitoolsrecap.com, codersera.com, techtimes.com,
> techstartups.com, swfte.com, benchlm.ai, releasebot.io, codingfleet.com (T3).
> For China-origin model/funding news prefer the lab's own page or a T1/T2 wire
> over 36kr.com; never cite a crypto exchange (kucoin.com etc.) as a source for
> AI-company funding — use the company filing or a T1/T2 business wire.
> ```

**Why this helps:** Trims the last T3 residual and removes an obviously inappropriate crypto-exchange citation for funding facts.
**Risk:** Slightly fewer first-look leads on minor China-origin drops; acceptable given the quality gain.

## Reader-feedback → profile proposals (separate from the ≤5 prompt patches above)

**In-window feedback (2026-06-22 → 2026-06-28):** four records, **all 👍, no 👎, no recurring negative theme.** Reasons are all empty. The taps were on: two Overview arXiv items (privacy-violation arXiv:2606.20546; alignment arXiv:2606.20482, both 06-22) and two cyber-papers Swiss-tech-ecosystem items (the CHF 200M Swiss-AI-compute commitment and the "Swiss AI firms reportedly…" note, 06-22). A handful of single positive taps is reinforcement, not a mandate — no prompt change is *required* from in-window feedback. I've folded them into the light positive note below and marked them `consumed`.

**Catch-up — orphaned feedback (2026-06-19 → 2026-06-20):** because the 2026-06-21 evaluator never ran, the feedback from 06-19/06-20 was never processed. It includes the week's only substantive 👎 (two taps on the same 06-19 Overview story), with a clear, recurring-theme reason worth surfacing. Quoted verbatim:

> "So, this is nature blog, not at all at the same level of publication as the actual mag. You need to read the actual study. Is it skill displacement to higher automation thinking or _actual_ deskilling? please stear away from sensationalism"

This is exactly the kind of signal `reader-profile.md` exists to capture: prefer the underlying study over a news-tier restatement, and avoid sensational framing of a nuanced result. Proposal:

**Proposal A — `reader-profile.md`, "Learned preferences" section:**

> **Before:**
> ```
> ## Learned preferences (Evaluator-maintained — append below)
> <!-- The Weekly Evaluator proposes additions here from feedback; Rafael applies them. e.g.:
> - 2026-06-15: less SpaceX launch detail on weekends (3× 👎, "too long"). -->
> ```
>
> **After:**
> ```
> ## Learned preferences (Evaluator-maintained — append below)
> <!-- The Weekly Evaluator proposes additions here from feedback; Rafael applies them. e.g.:
> - 2026-06-15: less SpaceX launch detail on weekends (3× 👎, "too long"). -->
> - 2026-06-28: for "AI/science changes how we think/work" stories, anchor on the
>   underlying study (journal article / preprint), not a Nature *blog/news* restatement,
>   and avoid sensational framing — distinguish skill-displacement from real deskilling
>   rather than asserting the alarming reading (2× 👎 on 2026-06-19 overview "AI tools
>   erode skills", "read the actual study… please steer away from sensationalism").
> ```

**Proposal B (low-confidence, positive reinforcement) — `reader-profile.md`, "Favor" section:** the in-window 👍 cluster suggests the reader values (a) Overview arXiv items on privacy / alignment and (b) cyber-papers Swiss-AI-ecosystem items. These are single taps each, so I propose this only as an optional nudge, not a firm rule:

> **After (append under "Favor"):**
> ```
> - 2026-06-28 (light signal): AI privacy/alignment arXiv items and Swiss AI-ecosystem
>   funding/policy items each drew a 👍 — keep prioritising these when they carry a new
>   dated fact.
> ```

**`source-weights.yml`:** **no change proposed.** The 06-19 👎 targets *Nature news/blog* framing rather than a cleanly-identifiable host (the record's `source_domain` is null), and the distinction between Nature's news/blog tier and the peer-reviewed journal is better handled in `reader-profile.md` (Proposal A) than by a blunt domain `reduce:`/`never:` entry that would also penalise legitimate Nature journal citations. No source repeatedly *misled*, so `never:` is not warranted.

**Bookkeeping:** all 22 records in `feedback/2026-06.jsonl` have been set `consumed: true` (the actionable 06-19 👎 folded into Proposal A; the positive clusters folded into Proposal B / the in-window note) and are committed with this review so they aren't re-proposed.

## Cross-week trend
Covered in §J. Headline: the AI/ML stream went from the pipeline's single failing component (0.12) to comfortably healthy (0.67) — Patch 1 worked. Portfolio direct-fetch rose 0.70 → 0.93. The only regressions are bookkeeping (stale unavailable list) and a recurrence (Patch 5 not fully applied), not reachability.

## Open questions for human review
1. **Why did the AI/ML brief not publish on Wednesday 2026-06-24?** Overview and cyber-papers both landed that day, so it isn't a global outage — it looks like a single-stream skip or a push that didn't reach `origin/main`. (06-28 AI/ML and cyber are merely *pending* — they fire after the Sunday-morning evaluator — but 06-24 is a genuine miss.)
2. **The 2026-06-21 evaluator never ran** — the second skipped evaluator Sunday in three weeks (06-07 was flagged missing last review; 06-21 now). Cron skip, failed run, or push failure? While the evaluator skips, cross-week trend tracking is blind and reader feedback orphans (see point 4).
3. **Cyber-papers 06-23 git push failed (HTTP 403 on receive-pack)** — the brief was published via the GitHub API instead, but the dedup index file `index/stories/2026-06-23-cyber-papers.jsonl` could not be pushed (too large to inline). That stream is missing one day of dedup history until a normal push reconciles it — worth confirming it has since landed.
4. **Orphaned reader feedback:** the 06-19/06-20 records (including the substantive anti-sensationalism 👎) were never processed because 06-21 didn't run. I've folded them in this week as catch-up (Proposal A) and marked them consumed — but this is a symptom of point 2. If evaluator Sundays keep slipping, feedback signal will keep falling through the window cracks.
5. **bioRxiv/medRxiv proxy reachability** is real but flaky (empty body on the 06-28 weekend run). Treat as a directly-citable primary (Patch 1), or keep on the snippet-only list to be safe? Recommend the former with the empty-body fallback clause.
