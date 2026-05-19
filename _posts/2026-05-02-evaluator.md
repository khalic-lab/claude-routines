---
layout: single
title: "Weekly Review — 2026-05-02"
date: 2026-05-02
categories: [evaluator]
---

# Weekly Brief Pipeline Review — 2026-05-02

_Coverage: briefs from 2026-04-26 to 2026-05-02 (7-day target window)._
_Files read: 1 Overview, 1 Markets, 1 AI/ML, 1 Cyber+Papers, 1 Weekend; prior review **found** but is itself a "pipeline cold" stub written at 17:07 today, before the writer routines fired at 17:11–17:18 — so it carries no useful prior-week trend signal. **This review supersedes that stub** (no delete tool available, so both files coexist in the Reviews folder; clean up manually if desired)._

> **Deployment-day caveat.** Only today's daily-stream files exist; 2026-04-26 through 2026-05-01 are empty across all four streams. This is the first run after a deployment, and it shows. Every metric below is a single-day reading masquerading as weekly. Cross-day and cross-week analyses (dimensions I and J) are skipped. Patch proposals are kept conservative for the same reason — fixing problems on n=1 evidence is asking for whiplash next Sunday.

## Health summary

| Metric                          | Value                                                         | Target | Status |
|---------------------------------|---------------------------------------------------------------|--------|--------|
| Unique domains cited            | ~85                                                           | ≥40    | 🟢 |
| T1 citation %                   | ~52% (T1≈57, T2≈52)                                           | ≥40%   | 🟢 |
| T3 leakage count                | 0                                                             | 0      | 🟢 |
| Non-English citation %          | ~2% (2 FR cites in Overview only)                             | ≥10%   | 🔴 |
| Link sample pass rate           | n/a — 10/10 fetches 403'd from this env (see C)               | ≥90%   | ⚪ |
| Fabrication count               | 0 detected; couldn't verify under 403                         | 0      | ⚪ |
| Single-source rate              | ~28% aggregate; Markets ~45%, Weekend ~40%, OV/AIML ~23%, C+P ~10% | <20% | 🔴 |
| Empty section instances         | 0                                                             | <5     | 🟢 |

Headline read: **structurally healthy on tier discipline and source diversity, structurally weak on triangulation and language reach, link health unmeasurable from the evaluator side**.

---

## A–J: detailed findings

### A. Source diversity

Across the 5 briefs, ~85 unique domains were cited. Top concentrations: arxiv.org (~24 citations, ≈16% of total — driven entirely by Weekend's papers density and *just* at the 15% per-domain ceiling), aljazeera.com (~6), cnbc.com (~5), nature.com (~4), anthropic.com (~4), quantamagazine.org (~3), cisa.gov (~3), bleepingcomputer.com (~3).

Tier distribution from the briefs' own footers: T1 ≈ 57, T2 ≈ 52, T3 = 0. T1 share ≈ 52%, comfortably above the 40% floor. **T3 leakage is zero — clean across all five files.**

The single weakness is **language reach**. Across all five briefs I count two French citations (rts.ch and letemps.ch in the Vaud item) and zero German, Italian, or Spanish citations. The Markets brief's footer explicitly states "DE/FR consulted via search snippets only — no direct Handelszeitung/Le Temps/NZZ citations retrieved" — i.e., the writer tried, hit 403s, and gave up rather than cite via snippet. With Markets covering Switzerland and AI/ML covering a global model ecosystem, ~2% non-English is structurally too narrow.

Geographic spread of news sections looks healthier: Switzerland, US, UK, Qatar, Thailand, Indonesia, Russia/Ukraine, Iran, Myanmar, Germany, France/EU. ~10+ origin countries.

### B. Aggregator leakage (critical violation)

Searched all 5 briefs for direct citations to news.ycombinator.com, lobste.rs, reddit.com, twitter.com, x.com, mastodon.social, threads.net, bsky.app. **Zero hits.** The AI/ML brief explicitly notes "T3 used for discovery only (llm-stats.com, blog.mean.ceo aggregators) — not cited" and the weekend brief states "HN/Reddit used to surface topics only; all citations are T1/T2." Policy compliance on this dimension is clean. No patch needed here.

### C. Link health

I sampled 10 URLs (2 per stream + 2 weekend) and ran WebFetch on each. **Every fetch returned HTTP 403** — including swissinfo.ch, arxiv.org abstract page, ECB press release, scotusblog, huggingface.co, nist.gov, cisa.gov, nvd.nist.gov, and quantamagazine.org. This is the same 403 pattern the writer briefs flag in their own gap footers (4 of 5 footers cite 403 problems with the same hosts). The conclusion is **environmental, not editorial**: from inside the evaluator's network the link sample is unmeasurable. Per-stream pass rate is therefore reported as ⚪ rather than 0%; it would be wrong to claim 100% link breakage when the cause is upstream egress filtering / anti-scrape protection.

That said, **the fact that the writers and the evaluator hit the same wall** is itself the most important finding of this review. See Patch 4.

Spot-check of fabrication (8 claims): could not be performed for the same reason. Marked ⚪.

### D. Section vitality

Single-day window, so per-section run counts are 1 across the board. No empty sections. Specifically:

- Overview: 5/5 sections populated (Switzerland & Vaud, World politics, Science, ML research first batch, Markets pre-open).
- Markets: 2/2 sections populated.
- AI/ML: 5/5 sections populated (Lab blogs, Models/datasets, Benchmarks, Industry, Apple Silicon).
- Cyber+Papers: 2/2 populated (Cybersecurity, ML research second batch).
- Weekend: all sections populated.

Cannot flag "empty 3 days running" — there is no streak to detect. Re-evaluate next Sunday.

### E. Coverage gap recurrence

This is the dimension where the deployment-week makes the analysis still useful. Reading all five gap footers, the **single dominant pattern is HTTP 403 on direct origin fetches**. Hosts named:

- arxiv.org abstract pages (Cyber+Papers, Weekend)
- anthropic.com, openai.com, deepmind.google (AI/ML)
- nist.gov, nvd.nist.gov (AI/ML, Cyber+Papers)
- cisa.gov advisory listing (Cyber+Papers)
- quantamagazine.org (Weekend)
- bleepingcomputer.com (Cyber+Papers)
- ecb.europa.eu graph page (Markets)
- Major DE/FR financial press — Handelszeitung, Le Temps, NZZ (Markets)

In every case the writers fall back to one of: search-result snippets, secondary T2 reporting, or Google cache fragments. The current prompts allow this fallback but don't standardize how it's labelled. Two side-effects show up:

1. **False directness.** The Overview brief writes "Published in *Nature Physics* May 1. [Nature Physics, May 1](https://www.nature.com/articles/s41567-026-03222-6)" — the URL anchors a citation but the writer never actually fetched that page. The reader has no way to distinguish direct-from-source from snippet-paraphrase.
2. **Single-source inflation.** Markets cites EUR/CHF as "[ECB reference rates, 2 May 2026]" while the gap footer admits "EUR/CHF rate not directly verified via WebFetch (ECB page cited but not fetched)." That is a single-source-via-snippet item presented as a T1 attribution.

This is both A and F in one — recurring source-access friction creating a tier-discipline drift. See Patches 1 and 4.

A second recurring gap: **arXiv batch unavailability** in Cyber+Papers ("HF daily papers API returned empty arrays for 2026-05-02; all arXiv listing pages returned HTTP 403"). The brief responded by pulling from an older 2602–2603 corpus rather than the day's actual batch. Same failure mode — degraded coverage, presented without explicit downgrade signal beyond a footnote.

### F. Triangulation rate

Counted `[single-source]` tags vs total items, per stream:

- **Overview**: 5 single-source / ~22 items ≈ 23%
- **Markets**: 5 single-source / ~11 items ≈ **45%**
- **AI/ML**: 5 single-source / ~22 items ≈ 23% (per footer claim)
- **Cyber+Papers**: 1 single-source / 10 items ≈ 10%
- **Weekend**: ~12 single-source / ~30 items ≈ **40%**

Aggregate ≈ 28%. Target <20%. Markets and Weekend are the two outliers, and they are different problems:

- **Markets** has chronic single-sourcing on what should be the easiest things to triangulate — index closes, FX rates, gold price. The writer ends up citing rttnews.com, marketscreener.com, pantheregroup.com, exchange-rates.org.uk, newsx.com — a stack of secondary aggregators. Anyone covering the SMI close should be able to pull from SIX itself, Reuters, Bloomberg, Le Temps, Handelszeitung. The 403 wall is a real constraint, but the prompt could at least require *more* aggregator sources (3+) when T1 isn't reachable, instead of just one.
- **Weekend** is single-sourcing because it is downstream of the dailies and not consulting them. Two specific examples: the weekend brief tags "Pentagon withdraws ~5,000 troops from Germany" as `[single-source]` (democracynow.org) when the same-day Overview multi-sourced it (euronews + aljazeera). It tags Aung San Suu Kyi house-arrest as `[single-source]` (democracynow.org) when Overview multi-sourced it (aljazeera + thediplomat). The weekend brief is **not reading sibling briefs before tagging**.

### G. Tag discipline

- `[preprint]` on arXiv items: spot-checked 5 (`2604.21751` Overview, `2604.12634` Overview, `2602.08354` Cyber+Papers, `2604.17931` Weekend, `2603.15569` Mamba-3 Weekend) — all correctly tagged. ✓
- `[vendor PR]` on vendor announcements: AI/ML footer claims 9 inline tags; sample of 5 (Mistral Medium 3.5, Anthropic creative connectors, OpenAI GPT-5.5, Google Deep Research, Anthropic Mythos) — all correctly tagged. ✓ Cyber+Papers correctly tags the Unit 42 Iran APT brief as `[vendor PR]` as well.
- `[disputed]` usage: zero this week. Could be appropriate (no contested items surfaced), could be under-used. Not flaggable on n=1.

Tag discipline is the strongest dimension.

### H. Topic balance (weekend brief)

10 ML papers in weekend:

- RL: 5 (LiteResearcher, PIRL, When Errors Can Be Beneficial, Pass@(k,T), Adaptive Test-Time Compute) ≈ 50%
- Architecture / SSM / MoE: 3 (Mamba-3, Attention to Mamba, MoE-on-NPU) ≈ 30%
- Safety / alignment: 1 (AI safety training clinical harm) ≈ 10%
- Vision: 1 (industrial anomaly detection) ≈ 10%

The brief itself frames "RL is becoming a general-purpose optimisation tool — five independent examples this week" as a thread, so the 50% RL allocation is editorial, not drift. Without an explicit stated target in the prompts I have visibility into, deviation cannot be computed. Looks reasonable.

5 Fundamental science items: math foundations 1, paleontology 1, condensed matter (ice phases) 1, neuroscience 2, NeuroAI roadmap (cross-disciplinary) 1. Reasonable spread.

### I. Repetition detection

Cross-day repetition cannot be assessed (1 day of dailies). Cross-stream repetition: three stories appear in 2+ streams — Pentagon-Germany troops (Overview + Markets + Weekend), Iran war (Overview + Markets + Weekend), Aung San Suu Kyi (Overview + Weekend). In each case the streams are doing different things — Overview gives detailed analysis, Markets frames it as risk-feed, Weekend lists as a top-of-week headline. That's the design and not a bug. The bug is the dedup metadata (Weekend tagging items `[single-source]` despite Overview's multi-source coverage of the same story). Covered in F and patched below.

### J. Cross-week trend

Skipped. The "prior review" file at `News Briefs/Reviews/2026-05-02.md` is the cold-stub written at 17:07 today before the writer routines fired (17:11–17:18). It has no metric values to compare against. Re-attempt next Sunday with a real prior week.

---

## Patch proposals (for human review)

Five patches, ordered by severity. Each is a proposal — apply only if the underlying prompt actually contains the language I'm guessing at. The "Before" blocks are my reconstruction of likely current wording; verify before pasting.

### Patch 1 — Tighten Markets triangulation rule for index closes and FX

**Target prompt:** Markets
**Section affected:** Markets — full day
**Issue:** Markets had a 45% single-source rate, mostly on price data (SMI/DAX/CAC closes, EUR/CHF, USD/CHF, gold) that should be triangulable. Aggregator-of-aggregator citations (rttnews, marketscreener, pantheregroup, newsx) are being accepted as single-source attestation.

**Proposed change:**

> **Before (likely current):**
> ```
> Cite each price level with at least one source. If only one source is available, mark [single-source].
> ```
>
> **After:**
> ```
> Index closes and FX/commodity reference prices require either: (a) one T1 source (the exchange itself, central bank, Reuters, Bloomberg, FT) — direct fetch or via search snippet labelled [via snippet]; OR (b) two independent T2 aggregators citing concordant numbers. A single aggregator (rttnews, marketscreener, exchange-rates.org.uk, newsx, pantheregroup) is not sufficient even with the [single-source] tag. If neither (a) nor (b) is achievable, omit the price and note the gap rather than publish an unverified figure.
> ```

**Why this helps:** Lifts the triangulation floor on the data points that are most often quoted downstream. Forces aggregator stacking when T1 is blocked.
**Risk:** May produce more "price unavailable" gaps on slow news days. Acceptable tradeoff.

### Patch 2 — Weekend brief must read sibling daily briefs before tagging

**Target prompt:** Weekend brief
**Section affected:** "Week in headlines" and any item where a daily already covered it
**Issue:** Weekend tagged Pentagon-Germany troops and Aung San Suu Kyi as `[single-source]` when the same-day Overview multi-sourced both. Weekend is not consulting siblings, so its triangulation metadata is wrong.

**Proposed change:**

> **Before (likely current):**
> ```
> Cite each headline item. Mark [single-source] if only one source is available.
> ```
>
> **After:**
> ```
> Before tagging any headline as [single-source], read the daily briefs in News Briefs/{Overview,Markets,AI-ML,Cyber-Papers}/ for the coverage window and inherit their citations for any story they covered. The weekend brief is downstream of the dailies; do not re-source from scratch. If a daily already cited two T1/T2 sources for an item, the weekend should reference those sources rather than its own single-source find.
> ```

**Why this helps:** Eliminates the dedup miss. Lowers Weekend's single-source rate. Makes the brief stack coherent.
**Risk:** None significant — this is purely a coordination fix.

### Patch 3 — Fix Cyber+Papers sibling-brief lookup

**Target prompt:** Cyber+Papers
**Section affected:** Coverage footer / dedup logic
**Issue:** Cyber+Papers ran at 17:18 today and reported in its footer "Morning Overview brief absent — `News Briefs/Overview/2026-05-02.md` not found in Drive; dedup skipped." The Overview file *did* exist at 17:11 (id `1CkLVE5MsEMYtBdmZBcmmkcwNWiXOmkpb`), is owned by the same OAuth identity, and is in the right parent folder. Either the prompt is doing path-based lookup that doesn't exist in Drive, or the listing was cached, or the search query was wrong.

**Proposed change:**

> **Before (likely current):**
> ```
> Read News Briefs/Overview/{date}.md for dedup if it exists.
> ```
>
> **After:**
> ```
> Use search_files with parentId resolution: first search for the parent folder titled "Overview" inside News Briefs, then search for files titled exactly "{date}.md" with that parentId. If no result, fall back to title contains "{date}". If still absent, note explicitly which Drive identity was queried in the footer ("dedup skipped: Overview/{date}.md not found under OAuth {identity}").
> ```

**Why this helps:** Folder-name path lookup is fragile in Drive — Drive doesn't really have paths, it has parent IDs. Title-plus-parent search is more reliable. The diagnostic identity-note at the end catches the OAuth-mismatch failure mode if it ever arises.
**Risk:** Requires the writer routine to actually call search_files rather than a path translator, which may be a larger refactor than a prompt edit.

### Patch 4 — Standardize the 403-fallback labelling protocol across all four daily streams

**Target prompt:** Morning Overview, Markets, AI/ML, Cyber+Papers (apply identically)
**Section affected:** Sourcing rules / coverage footer
**Issue:** All four daily briefs hit 403 walls on major hosts (arxiv, anthropic, openai, deepmind, nist, nvd, cisa, quanta, bleepingcomputer, ecb graph page) and fall back to search snippets. Currently this fallback is inconsistent: some items get a `[via snippet]` hint, some get a plain citation that *looks* direct, some get a footer note like "page returned 403" while still anchoring a hyperlink in the body that reads as if confirmed. The reader cannot tell which is which.

**Proposed change:**

> **Before (likely current):**
> ```
> Cite the original source. If you cannot access it, note the gap.
> ```
>
> **After:**
> ```
> If the origin URL returned a non-200 status during this run, append a [via snippet] or [via cache] suffix to the citation in the body — do not silently anchor an unfetched URL. The hyperlink may stay (so readers can try themselves), but the labelling must reflect that the content was not directly verified during this run. Footer "Gaps" still lists the affected hosts, but inline labelling is now mandatory, not optional.
> ```

**Why this helps:** Restores the read-time ability to distinguish direct-from-source from snippet-paraphrase. Lowers misleading T1 attributions in Markets, reduces "false directness" in Overview science items. This is the single highest-leverage prompt change available.
**Risk:** Visual clutter — every brief will have more `[via snippet]` tags. That's the cost of honesty about the access wall.

### Patch 5 — Non-English minimum on Markets and AI/ML

**Target prompt:** Markets and AI/ML (two prompts, same edit)
**Section affected:** Sourcing charter / language reach
**Issue:** Aggregate non-English citation rate is ~2% (target ≥10%). Markets covers a Swiss financial centre and AI/ML covers a global model ecosystem — both should be reaching at least one DE or FR source per run. Markets explicitly tried and gave up at the 403 wall; AI/ML didn't try.

**Proposed change:**

> **Before (likely current):**
> ```
> Sources may be drawn from any language; English is preferred for accessibility.
> ```
>
> **After:**
> ```
> Each daily brief should include at least one citation from a non-English-language source per run.
>   - Markets candidates: NZZ, Le Temps, Handelszeitung, FT Deutschland, Les Echos, Börsen-Zeitung.
>   - AI/ML candidates: Le Monde tech, NZZ, Handelsblatt tech, Heise.
> If 403-blocked, attempt search-snippet citation with [via snippet] (per Patch 4). A run that ends without any non-English citation should explicitly flag the gap in the footer rather than silently produce English-only output.
> ```

**Why this helps:** Closes the language-reach gap toward the 10% target without requiring all streams to comply on every run.
**Risk:** May force a snippet-only citation when origin is blocked, which is now acceptable under Patch 4. Without Patch 4, this would push toward fabricated-looking attributions — so apply Patches 4 and 5 as a pair.

I have nothing for Cyber+Papers beyond Patches 3 and 4. That stream is otherwise the cleanest in the set (10% single-source rate, clean tag discipline, well-structured CVE citations).

---

## Cross-week trend

Skipped — see J above. The prior review is a same-day cold stub, not a previous-week comparison.

---

## Open questions for human review

Mechanical analysis cannot resolve these. They are yours.

1. **The 403 wall is structural, not editorial.** Every daily brief flags it; the evaluator hits the same wall on the same hosts. Is the writer (and evaluator) running through a sandbox or proxy that is getting bot-blocked by Cloudflare/anti-scrape? If yes, no prompt edit fixes it — the infrastructure layer needs different egress (residential IP, browser automation, paid scrape API). Worth investigating before next Sunday; until then Patch 4 is a coping mechanism, not a fix.

2. **The prior review at `News Briefs/Reviews/2026-05-02.md` is a cold-pipeline stub from 17:07 today**, written before the writer routines fired at 17:11–17:18. Two routines ran on the same day, and the first one fired before the writers were ready. The evaluator schedule should either trail the writer schedule by enough margin to never race, or the evaluator's own precheck should be aware of writer schedule windows. (Today: this review supersedes that stub; both files now coexist in Reviews because no delete tool was available — clean up manually.)

3. **Day-of-week assumption.** The prior cold review noted: 2026-05-02 is a Saturday in Europe/Zurich, but the prompt is written assuming Sunday execution. If the cron is firing one day early, the "Saturday's date" weekend-brief lookup would be off-by-one in normal operation. Worth confirming the cron schedule actually targets Sunday 11:30 Europe/Zurich, and updating the prompt's "today (Sunday)" wording to "today, the most recent execution day" to remove the silent misalignment.

4. **Markets aggregator-stacking.** Patch 1 is conservative — it requires either T1 or 2× T2 aggregators. Is that actually achievable on Friday-into-Saturday windows when most T1 sites are 403-blocked? If not, the alternative is to publish fewer prices but with stronger backing, which may be the right tradeoff but is a content-density decision you should make.

5. **Weekend brief's `[single-source primary]` formatting.** I see things like "Underlying peer-reviewed paper in review `[single-source primary]`" and "primary paper pending confirmation — single-source". This is more granular than the simple `[single-source]` tag the dailies use, and it's not clear whether this is meaningful internal structure or local drift. Worth deciding whether the weekend converges on the simpler tag or the dailies adopt the more granular variant.

6. **AI/ML's vendor-PR density.** The brief tagged 9 of ~22 items as `[vendor PR]` (~40%). That's faithful tagging on the brief's part — vendor announcements really are dominating coverage right now (Mistral, Anthropic ×3, OpenAI, Google, DeepSeek vendor docs). But it does prompt a slow-burn editorial question: is the AI/ML stream effectively a vendor newsfeed dressed up with `[vendor PR]` tags, and if so, is that what you want? No patch — design question for next month, not an n=1 issue.

7. **arXiv concentration.** Across the 5 briefs, arxiv.org is ≈16% of all citations, just at the per-domain concentration ceiling. Driven entirely by Weekend's papers density. Is the 15% rule meant to apply to news/general citations only (and exempt papers sections), or globally? If globally, the weekend brief structurally cannot comply on a heavy paper week. Worth clarifying in the policy.

---

_Next review: 2026-05-09 (assuming Sunday cadence; today is Saturday — see open question 3). With seven days of full daily output it will be possible to compute real per-stream metrics rather than the n=1 snapshots in this review._
