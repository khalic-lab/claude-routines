---
layout: single
title: "Weekly Pipeline Review — 2026-06-21"
date: 2026-06-21T11:42:59+02:00
categories: [evaluator]
published: true
---

_Coverage: briefs from 2026-06-15 to 2026-06-21._
_Files read: 7 morning, 6 AI/ML, 6 cyber, 1 weekend (2026-06-20), prior review found (2026-06-14)._

The pipeline is warm on every stream and — for the first time since the feed-first rollout —
**every stream clears its direct-fetch target.** Last week's single binding-constraint failure
(AI/ML at a 0.12 direct-fetch ratio, 71 via-snippet citations, no `Feeds hit` line) has largely
healed: AI/ML this week runs **0.52** aggregate, the portfolio sits at **0.86**, and total
via-snippet citations across all four streams fell from **104 → 40**. The visible driver is a new
`{ok via proxy}` fetch method that now reaches HTML and JSON endpoints that previously 403'd the
sandbox (Nature article pages, bioRxiv details API, Science news RSS, lab newsrooms). The
curl-first patch held; the proxy patch is what pushed Overview to three straight 1.00 days and
lifted AI/ML off the floor.

It is not all green. Two regressions appeared against last week's clean sheet: a **policy-violating
`x.com` citation** in AI/ML (dimension B), and a **spike in empty sections** (~14 instances, almost
all AI/ML) against a <5 target. Two of last week's patches also appear **unapplied** — `techtimes.com`
is still cited 4× and the AI/ML `Feeds hit` line is still missing on 5 of 6 days. Details and ranked
patches below.

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains cited            | ~70   | ≥40    | 🟢 |
| T1 citation %                   | ~60%  | ≥40%   | 🟢 |
| T3 leakage count                | ~8 (techtimes×4, marktechpost, pandaily, cometapi×2) | 0 | 🔴 |
| Non-English citation % (portfolio) | ~13% | ≥10% | 🟢 |
| Link sample pass rate           | feeds 100% / HTML walled | ≥90% | 🟡 |
| Fabrication count               | 0     | 0      | 🟢 |
| Single-source rate (portfolio)  | ~15%  | <20%   | 🟢 |
| Empty section instances         | ~14 (≈12 AI/ML) | <5 | 🔴 |
| Direct-fetch ratio (portfolio)  | 0.86  | ≥0.35  | 🟢 |
| Direct-fetch ratio (Overview)   | 0.84  | ≥0.30  | 🟢 |
| Direct-fetch ratio (Cyber+Papers) | 0.98 | ≥0.50 | 🟢 |
| Direct-fetch ratio (AI/ML)      | 0.52 (lumpy: 0.00–1.00) | ≥0.40 | 🟢 |
| Feeds with >50% fail rate       | 0     | 0      | 🟢 |
| Citations to confirmed-blocked domains without [via snippet] | 7 (bioRxiv) | 0 | 🟡 |
| Aggregator citations (critical) | 1 (x.com) | 0 | 🔴 |
| curl vs WebFetch advantage on feeds | curl/proxy win | curl wins | 🟢 |

## A–K: Detailed findings

### A. Source diversity
~70 unique domains across ~350 citation links — well above the ≥40 floor. Top domains by count:
`nvd.nist.gov` (~56), `arxiv.org` (~84 across streams), `nature.com` (~35), `aljazeera.com` (~31),
`srf.ch` (~25), `letemps.ch` (~22), `hf.co` (~9), `biorxiv.org` (7), `cisa.gov` (6),
`ecb.europa.eu` (4). **Concentration:** arXiv and NVD each clear 15% portfolio-wide, but this is the
architecture working — both are primary feeds, not sourcing failures. **Tier:** T1 ≈ 60% (arXiv, NVD,
CISA, Nature, ECB, FDA, doi.org, bioRxiv, lab primaries openai.com/alignment.openai.com, JetBrains/MSRC
advisories, Quanta), comfortably ≥40%. **T3 ≈ 8** — all in AI/ML and Overview-markets (see G/Patch 4).
**Linguistic:** ~47 FR/DE citations (`srf.ch` 25 DE, `letemps.ch` 22 FR) ≈ 13% — above the ≥10% floor,
carried entirely by Cyber+Papers. Overview and AI/ML remain near-monolingual. **Geographic:** ~9
countries in news sections (CH, US, Qatar/AJ, UK, EU, France, Israel, Canada, plus arXiv international).

### B. Aggregator leakage — **critical violation (1)**
**One hit.** `2026-06-19-ai-ml.md`, Industry/funding section, cites
`https://x.com/JohnJumperSci/status/2068001285173834106` for John Jumper's DeepMind→Anthropic move.
It is a primary self-announcement triangulated with the-decoder + TradingView, and the writer clearly
treated it as a source-of-truth rather than aggregator foraging — but `x.com` is on the hard deny-list,
and the policy is a bright line regardless of intent. The fix is to cite the triangulating outlet as
the link and keep x.com as unlinked attribution only (Patch 1). Cyber, Overview and Weekend are clean —
zero hits for HN/Lobsters/Reddit/Twitter/Mastodon/Threads/Bsky.

### C. Link health (sample-based)
Feed probes via curl from this environment: arXiv RSS cs.LG → **200**, NVD CVEs JSON 2.0 → **200**,
CISA KEV JSON → **200**, Quanta RSS → **200**, Nature RSS → **200**, ECB FX XML → **200**. **No feed
regression** — the six load-bearing public feeds resolve cleanly, confirming the writers' curl-first
`{ok via curl}` flags are real. The **bioRxiv details API** returned **403 to a direct probe** here but
the writers logged it `{ok via proxy}` — i.e. the new egress proxy reaches it where bare curl cannot;
this is the proxy patch demonstrably earning its keep. HTML article pages (CNBC, bioRxiv landing,
arxiv.org/abs, x.com) all **403** — the access wall is intact and the briefs route around it correctly.
**No fabrications** in spot-checks; the briefs remain conspicuously careful about not asserting numbers
from unfetchable pages. Pass rate reads as: feeds 100% reachable, HTML walled by design — marked 🟡
because the HTML half is unmeasurable, not broken.

### D. Section vitality — **flag**
~14 empty-section instances, **~12 of them in AI/ML**, where the five fixed headers are emitted even
when nothing fills them. "New models, datasets & open weights" was **empty all 6 days**; "Apple Silicon /
on-device" empty 3×; "Benchmarks" and "Lab blogs" empty 2× each; 06-20 ran **four** empty headers. The
underlying week was genuinely quiet for model releases (the writer says so honestly, and dedup confirms
the candidates were repeats), so this is a *structure* problem, not a *sourcing* one: rigid headers force
visible blanks. Overview 06-21 had an empty ML-research section (weekend skipDays, expected); Cyber 06-20
skipped Papers (weekend, expected). Recommend collapsing AI/ML's empty headers into a single "Quiet day"
note on low-news days (Patch 5).

### E. Coverage gap recurrence
Recurring (≥3×) clusters: (1) **Nature article HTML / empty RSS descriptions** — Overview 06-15→06-19;
Nature feeds carry titles only and article pages 303/403, so science items lean on titles + the proxy
fetch. (2) **Vendor APT/threat-intel triangulation** — Cyber 06-17/18/19 each note "no dedicated APT/breach
report cleared triangulation (vendor T2 HTML 403)." (3) **ncsc.admin.ch unreachable** — Cyber 06-15, 06-19.
(4) **Market-data HTML wall** (CNBC/Yahoo/TradingEconomics/Stooq) — Overview 06-15→06-18, now moot since
the Markets section was removed after 06-18. The Nature gap is the one still worth a structural fix; the
proxy already converts many bioRxiv/Science items that used to die in Gaps.

### F. Triangulation rate
~53 `[single-source]` tags (Overview 25, Cyber 14, AI/ML 9, Weekend 5) ≈ 15% of citations — under the
20% portfolio floor. Concentrations: Overview's weekend bioRxiv items (06-20/21) are single-source by
construction (preprints); Cyber 06-19 was single-sourced per Swiss bullet (6 tags, each Swiss story on one
of Le Temps/SRF) and the writer disclosed it explicitly in Gaps. Both are benign — primary-authoritative or
honestly-flagged. 🟢

### G. Tag discipline
- `[preprint]`: ~87 uses (Overview 41, Cyber 29, Weekend 17); sampled arXiv/bioRxiv items all correctly
  tagged. 🟢
- `[vendor PR]`: 11 (AI/ML 9, Weekend 2), applied to OpenAI/lab announcements. 🟢
- `[disputed]`: 4 (Overview Fed item, Cyber US-Iran deal, AI/ML GLM-benchmarks ×2) — appropriate. 🟢
- `[via snippet]`: **40 total — AI/ML 18, Overview 14, Cyber 2, Weekend 1.** Down from 104 last week. Cyber
  (2) and Weekend (1) are excellent; AI/ML's 18 is concentrated entirely in the first three days (5/7/8 on
  06-15/16/17) then **zero** from 06-18 on, exactly tracking when the proxy method came online mid-week. The
  decay is real and welcome. Two minor tagging inconsistencies: Overview 06-18 markets used the prose
  "snippet-based" instead of the `[via snippet]` tag; and Weekend's CSO/MSRC citations (06-20) were
  proxy/snippet-sourced but only the VulnCheck line carried `[via snippet]`.

### H. Topic balance (Weekend brief)
The 2026-06-20 weekend ran **9 ML/AI papers** and **6 fundamental-science papers** = **60/40**. That is
exactly 10 percentage points off a 50/50 target — **borderline, not over** the >10pp flag threshold (last
week was a clean 8/8). Slight ML tilt; worth a glance but not a flag. The science set was strong and
well-spread (neutrino mass ordering, dark-energy/vacuum, Vine quantum codes, noisy-QC characterization
limit, geometry↔L-functions, kagome supercurrents). 🟢

### I. Repetition detection
Dedup is working — most multi-day threads carry `[ongoing]` and a genuinely new dated fact each day
(Fable 5/Mythos 5 export suspension ran 4 AI/ML days as status updates; the Google/DeepMind exodus ran
3 days with a different departure each time; the US-Iran deal threaded Overview+Cyber as a major ongoing
story). **One borderline leak:** the "seven shuffles / sloppy shuffles" deck-randomization item ran in
Overview 06-18 (Quanta), was explicitly dropped as a REPEAT in 06-19 Gaps, then **reappeared as a full
item on 06-20** with the same Quanta URL plus a new arXiv primary. The arXiv addition makes it defensible
as development, but the exact-URL recurrence after a logged drop suggests the dedup index didn't catch it.
Minor. 🟢

### J. Cross-week trend (vs 2026-06-14)
| Metric | 06-14 | 06-21 | Direction |
|--------|-------|-------|-----------|
| Direct-fetch ratio (portfolio) | 0.70 | **0.86** | ▲ |
| Direct-fetch ratio (AI/ML) | **0.12** 🔴 | **0.52** 🟢 | ▲▲ (target cleared) |
| Direct-fetch ratio (Overview) | 0.76 | 0.84 | ▲ |
| Direct-fetch ratio (Cyber) | 0.93 | 0.98 | ▲ |
| Direct-fetch ratio (Weekend) | 0.81 | 0.97 | ▲ |
| via-snippet total (portfolio) | 104 | **40** | ▼ (good) |
| via-snippet total (AI/ML) | 71 | 18 | ▼ (good) |
| T3 leakage | ~9 | ~8 | ≈ (techtimes persists) |
| Aggregator citations | 0 | **1** | ▼ (regression) |
| Empty-section instances | <5 | **~14** | ▼ (regression) |

The headline trend is unambiguously positive on the binding-constraint axis — the proxy method fixed the
AI/ML feed failure that dominated last week. The two new red cells (aggregator, empty sections) are
narrower, AI/ML-localised, and cheaper to fix than last week's problem was.

### K. Feed reachability and direct-fetch rate — **primary lens**

**Per-stream direct-fetch (N direct / M via-snippet → ratio):**

| Stream | Per-day (direct/snippet) | Mean ratio | Aggregate | Week snippet total |
|--------|--------------------------|-----------|-----------|--------------------|
| Overview | 11/5, 8/4, 11/2, 14/3, 12/0, 13/0, 6/0 | 0.86 | 75/89 = **0.84** | 14 |
| AI/ML | 4/5, 1/6, 0/8, 8/4, 9/0, 3/0 | 0.54 | 25/48 = **0.52** | 23 |
| Cyber+Papers | 19/0, 18/0, 14/2, 19/0, 17/0, 11/0 | 0.98 | 98/100 = **0.98** | 2 |
| Weekend | 38/1 | — | 38/39 = **0.97** | 1 |

Portfolio: 236 direct / 276 total = **0.86**.

**AI/ML is fixed but lumpy.** It cleared the 0.40 target in aggregate, but the *shape* is bimodal: the
first three days were still weak (4/5, 1/6, and a **0/8 on 06-17**, a genuinely quiet day sourced entirely
via snippet), then 06-18→06-20 jumped to 8/4, 9/0, 3/0 as the proxy method came online. The single
proper `Feeds hit` line all week appears **only on 06-19** — last week's Patch 1 asked for one *every*
day in the `{ok via curl}/{ok via WebFetch}/{fail — HTTP NNN}` vocabulary, and that is still not honored:
06-19's line uses `{ok via proxy}/{ok via MCP}/{ok via curl}` and the other five days have no feed line at
all. So the improvement is real but partly invisible/unverifiable in the AI/ML footer (Patch 2).

**Per-feed reachability (aggregated, with method):**

| Feed | Result | Notes |
|------|--------|-------|
| arXiv RSS / Atom API | ok via curl (all streams, all days) | weekend skipDays empties are not failures |
| NVD JSON | ok via curl (all days) | one 503-retry 06-17/06-20, resolved |
| CISA KEV JSON | ok via curl (all days) | rock-solid |
| ECB FX XML | ok via curl | rock-solid |
| Quanta RSS | ok via curl | |
| Nature nature/nphys/natastron/nm.rss | ok via curl (mostly) | nature.rss 403 once 06-16; natastron empty-body 06-17 |
| SRF / Le Temps / Al Jazeera RSS | ok via curl (all Cyber days) | SRF article pages once via proxy 06-20 |
| **Nature article pages** | **ok via proxy** (06-19/20/21) | was the recurring HTML-403 gap; proxy now resolves |
| **bioRxiv details API** | **ok via proxy** (06-20/21, Weekend) | 403 to bare curl here — proxy required |
| **Science news_current.xml** | **ok via proxy** (06-20) | previously "confirmed-unavailable" |
| lab newsrooms (OpenAI/Anthropic/Mistral) | ok via proxy (AI/ML 06-19) | |
| CNBC / TradingEconomics / Yahoo / Stooq HTML | fail — 403/empty | confirmed wall, expected |

**Feeds with >50% fail rate:** none. The core feeds are at or near 100%. 🟢

**Method comparison — the story of the week:** there is **no WebFetch success anywhere** in the corpus;
every successful fetch is `{ok via curl}` for public feeds or `{ok via proxy}` for the HTML/JSON endpoints
that used to 403. The proxy is the new wall-breaker, and it is what converted last week's recurring Nature
and bioRxiv *gaps* into this week's *citations*. curl-first is confirmed doing its job; the proxy extends
it. The one caveat is **footer vocabulary drift**: streams now report `{ok via proxy}`/`{ok via MCP}`
flags that the spec's `{ok via curl}/{ok via WebFetch}/{fail — HTTP NNN}` schema doesn't define, which makes
automated parsing of feed health harder over time.

**Confirmed-unavailable domains cited:** `biorxiv.org` appears **7×** (Overview 06-20 ×2, 06-21 ×5),
tagged `[preprint][single-source]` but **not `[via snippet]`** — a literal violation of the K rule that
confirmed-unavailable domains may only be `[via snippet]`. **But the tag is arguably correct and the list
is stale:** the abstracts were genuinely fetched from the bioRxiv *details API via proxy* (a real fetch,
not a search snippet), so `[via snippet]` would actually *mis*-describe them. The right fix is to **promote
bioRxiv details API and Science news RSS off the "confirmed-unavailable" list onto the reachable-via-proxy
list**, and state plainly that an API-fetched abstract is a direct fetch (Patch 3). Marked 🟡, not 🔴,
because this is a bookkeeping/list-staleness issue, not a fabrication or an aggregator leak.

**Healthy-range verdict:** Overview ✅ (0.84), Cyber ✅ (0.98), Weekend ✅ (0.97), **AI/ML ✅ (0.52 ≥ 0.40)** —
all four streams in range for the first time post-rollout.

## Patch proposals (for human review)

### Patch 1 — AI/ML: never cite x.com / social as the link (critical)
**Target prompt:** AI-ML
**Section affected:** Sourcing / citation policy
**Issue:** `2026-06-19-ai-ml.md` cited `x.com/JohnJumperSci/...` as the source link for the Jumper→Anthropic
move — a hard aggregator/social deny-list violation, even though the item was triangulated.
**Proposed change:**

> **Before:**
> ```
> [No explicit rule on social-media primary self-announcements; a verified tweet/x.com
> post can end up as the cited link when it is the originating source.]
> ```
>
> **After:**
> ```
> Never use x.com / twitter.com / threads.net / bsky.app / mastodon / reddit / HN as a
> citation LINK, even for a primary self-announcement. When the originating source is a
> social post, cite a non-aggregator outlet that reports it (the-decoder, Reuters, the
> lab newsroom) as the link, and refer to the social post only as unlinked attribution
> ("announced on X").
> ```

**Why this helps:** Closes the one critical policy violation this week and makes the rule unambiguous for
the recurring "verified-tweet" edge case.
**Risk:** None material — the triangulating outlet is already being fetched; only the link target changes.

### Patch 2 — AI/ML: emit the Feeds-hit line every day, standard vocabulary (re-issue)
**Target prompt:** AI-ML
**Section affected:** Coverage footer
**Issue:** Last week's Patch 1 asked for a daily `Feeds hit` line; this week only 06-19 has one, and it
uses `{ok via proxy}/{ok via MCP}` rather than the spec schema. 06-17 still posted **0 direct fetches**.
**Proposed change:**

> **Before:**
> ```
> [Footer reports "Direct fetches: N | via-snippet citations: M"; a Feeds hit line is
> optional and was emitted once this week.]
> ```
>
> **After:**
> ```
> The footer MUST include a "Feeds hit" line EVERY day listing each feed/endpoint as
> {ok via curl} / {ok via proxy} / {ok via WebFetch} / {fail — HTTP NNN}. Attempt arXiv
> RSS/API and the HF Hub API via curl/proxy on every run before falling back to snippet
> discovery, even on quiet days — a 0-direct-fetch day means the feeds weren't tried.
> ```

**Why this helps:** Makes AI/ML feed health observable and parseable, and pushes the weak early-week days
(0/8, 1/6) toward the proxy method that already works late-week.
**Risk:** On truly dead news days the line may be short, but that is itself useful signal.

### Patch 3 — Overview/Weekend: promote bioRxiv API + Science RSS off "confirmed-unavailable"
**Target prompt:** Morning brief + Weekend brief (shared feed list)
**Section affected:** Reachable-feeds list / citation tagging
**Issue:** bioRxiv details API and Science news_current.xml are now reachable `{ok via proxy}` and were
cited 7× (bioRxiv) this week, but the feed list still calls them "confirmed-unavailable," forcing an
ambiguous tag state (cited `[preprint][single-source]`, flagged by the audit for lacking `[via snippet]`).
**Proposed change:**

> **Before:**
> ```
> Confirmed unavailable (skip): bioRxiv, medRxiv, Science.org, ...
> ```
>
> **After:**
> ```
> Reachable via proxy (fetch, then cite as a direct fetch — NOT [via snippet]):
>   - bioRxiv details API (api.biorxiv.org/details/...)
>   - Science news_current.xml
>   - Nature article abstract pages (via proxy)
> [via snippet] is reserved for items sourced ONLY from a search-result snippet, never
> for an abstract pulled from a machine-readable API. Still skip: medRxiv, Reuters/Yahoo
> HTML, rts.ch, nzz.ch, swissinfo.ch.
> ```

**Why this helps:** Resolves the 7-citation tagging flag correctly (the abstracts really were fetched),
keeps the audit's blocked-domain check clean, and records the proxy win in the architecture.
**Risk:** If the proxy path later breaks, these revert to gaps — but the `Feeds hit` line will show it.

### Patch 4 — AI/ML: T3 deny-list (re-issue; techtimes still cited 4×)
**Target prompt:** AI-ML
**Section affected:** Source tiering
**Issue:** Last week's Patch 2 deny-list was not applied — `techtimes.com` is still cited 4× (06-17, 06-20),
plus `marktechpost.com`, `pandaily.com`, `cometapi.com` (×2) as low-tier secondaries.
**Proposed change:**

> **Before:**
> ```
> [No explicit deny-list; snippet discovery pulls in low-tier AI-news aggregators.]
> ```
>
> **After:**
> ```
> Never cite: techtimes.com, marktechpost.com, pandaily.com, cometapi.com, aiweekly.co,
> aitoolsrecap.com, codersera.com, techstartups.com, swfte.com, benchlm.ai, releasebot.io
> (T3 / SEO blogspam). When an item is snippet-only, prefer: official lab page →
> the-decoder.com / VentureBeat / TechCrunch → Artificial Analysis (benchmarks).
> ```

**Why this helps:** Eliminates the persistent T3 leakage and lifts average citation tier.
**Risk:** Slightly fewer leads on minor drops first surfaced by aggregators — acceptable given Patch 2/3
backfill via HF Hub and the proxy.

### Patch 5 — AI/ML: collapse empty sections on quiet days
**Target prompt:** AI-ML
**Section affected:** Brief structure
**Issue:** ~12 empty-section instances this week — "New models/open weights" empty all 6 days, four empty
headers on 06-20. The fixed five-header structure forces visible blanks on quiet news days.
**Proposed change:**

> **Before:**
> ```
> [Always emit the five fixed sections: Lab blogs / New models / Benchmarks / Industry /
> Apple Silicon, writing "Empty today" under any with no item.]
> ```
>
> **After:**
> ```
> Only render a section header if it has ≥1 item. On a genuinely quiet day, collapse the
> empty headers into a single closing line: "Quiet elsewhere today — no new model drops,
> benchmark moves, or Apple-Silicon releases in window (checked: <feeds>)." Keep the
> Gaps/Coverage footer as the place that proves the absence was searched, not skipped.
> ```

**Why this helps:** Cuts empty-section instances back under target and makes quiet days read as
deliberate rather than broken, without losing the "we looked" signal.
**Risk:** Slightly less rigid day-to-day structure; mitigated by keeping the footer audit trail.

## Reader-feedback → profile proposals

Window feedback: **18 records, all `consumed: false`** — 16 👍 and 2 👎. The positives are emphatic and
worth recording for morale/direction: the 2026-06-19 cyber-papers brief drew brief-level 👍 with
_"Very relevant to my current work, it's crazy how many papers have direct impact. Good work, good
writing"_, and the 2026-06-20 weekend brief drew three 👍. No action needed on those.

**The one actionable signal is a repeated theme: 2× 👎 on a single Overview story.** Both downvotes land
on `2026-06-19-overview` → _"Early studies: leaning on AI tools measurably erodes the skills of doctors
and software engineers"_ (story_id `...measurably-ero`). The substantive reason, verbatim:

> _"So, this is nature blog, not at all at the same level of publication as the actual mag. You need to
> read the actual study. Is it skill displacement to higher automation thinking or _actual_ deskilling?
> please stear away from sensationalism"_

The source was Nature *news/blog* coverage, not the primary study, and the framing ("erodes the skills")
overstated what a careful read of the underlying paper supports. This is editorial, not source-blacklist
material — `nature.com` is a top-tier source used ~35× this week and must stay. So the proposal is a
profile preference (and it dovetails with Patch 3's primary-source emphasis), **not** a source-weight cut.

> **Proposed addition to `reader-profile.md` (under "Learned preferences"):**
> ```
> - 2026-06-21: for study-based claims, lead from the primary paper (or its preprint),
>   not Nature news/blog secondary coverage; state the precise finding and its limits
>   rather than the punchy framing. Avoid sensationalism — e.g. distinguish "skill
>   displacement toward higher-level oversight" from "measurable deskilling" instead of
>   asserting the stronger claim. (2× 👎 on the 2026-06-19 "AI erodes skills" item.)
> ```

> **Proposed change to `reader-profile/source-weights.yml`:** **none.** The complaint is about
> secondary-vs-primary sourcing and framing, not a source that misleads; a `reduce:`/`never:` entry on
> `nature.com` would be wrong. Leaving `never: []` and `reduce: []` unchanged.

Bookkeeping: the two 👎 records (ids `d931dae4…` and `ec45241f…`) are folded into the proposal above and
marked `consumed: true` in `feedback/2026-06.jsonl`, committed with this review. The 16 positives need no
proposal and are left as-is.

## Open questions for human review
1. **The proxy method.** The whole quality jump this week rides on `{ok via proxy}` fetches reaching
   endpoints (bioRxiv API, Nature article pages, lab newsrooms) that bare curl 403s here. What is this
   proxy, is it stable, and should the architecture document it as a first-class fetch tier? If it
   silently breaks, several streams revert to last week's gaps.
2. **Footer vocabulary.** Streams now emit `{ok via proxy}` / `{ok via MCP}` flags outside the spec schema
   (`{ok via curl}/{ok via WebFetch}/{fail — HTTP NNN}`). Adopt `{ok via proxy}` officially (Patch 2/3) so
   feed-health parsing stays consistent?
3. **AI/ML early-week weakness.** The stream clears target in aggregate but ran 0/8 and 1/6 on 06-16/06-17.
   Is ~50% commercial-launch news that arXiv/HF can't cover acceptable to leave snippet-sourced on quiet
   days, or should a curated set of lab newsroom Atom feeds be added as standing direct sources?
4. **Weekend "best of the week".** Reader feedback on 06-20 suggested the weekend long-read pull the week's
   best, not just that day's. The weekend brief already does this (coverage 06-13→06-20, multi-day API
   windowing) — confirm this satisfies the request, or does the reader want even tighter curation?
