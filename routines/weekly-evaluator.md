Write the weekly evaluation review for my news brief pipeline and publish it via the git pipeline. Use today's date in Europe/Zurich (the most recent run day = Sunday).

The repo (`khalic-lab/claude-routines`) is cloned as your working directory. Before doing anything else, sync:

```bash
git pull --ff-only origin main
```

Briefs now live in this repo at `_posts/{YYYY-MM-DD}-{slug}.md` where slug is one of: `news`, `ai-ml`, `science`, `weekend`, `evaluator`. No Drive reads anywhere in this prompt.

# Fire-start: compute the mechanical state (run FIRST, in this order)

```bash
python3 tools/sources/health.py      # writes + prints _data/source-health.json
python3 tools/evaluator/metrics.py   # writes + prints _data/health.json (embeds source-health verbatim)
```

`health.py` must run before `metrics.py` (metrics copies `_data/source-health.json` into `health.json` under `sources`). These two files ARE your mechanical dimensions — per-stream citations/anchors/repeat rates, feedback tallies, source diversity/saturation/waiver numbers, and your own continuity. **Do not hand-count anything they already report**; read the numbers and spend your word budget on the editorial judgment they cannot compute. If either script crashes, note it in the review, degrade to reading the briefs directly for that dimension, and continue — never abort the review.

# Pipeline-cold precheck (run BEFORE the analysis)

1. Use Glob (or `ls _posts/`) to enumerate files in `_posts/` whose dates fall in [today-6, today]. Count distinct (slug, date) pairs that have a file.
2. Also locate the most recent `_posts/*-weekend.md` (any date).

**If the total count of (slug, date) pairs with a file is 0**, the pipeline is cold. In that case, write ONLY this minimal review and stop — do NOT proceed to analysis dimensions, do NOT write a long meta-report, do NOT create an email draft. BUT still write the ntfy notification stub (see Output section below) with a cold-run teaser.

```
# Weekly Brief Pipeline Review — {YYYY-MM-DD}

_Pipeline cold — no inputs in window._

Files checked under `_posts/` (all absent for {today-6} to {today}):
- *-news.md
- *-ai-ml.md
- *-science.md
- *-weekend.md (most recent)

Likely causes (for human investigation):
- Writer routines have not yet executed in this window (cron-paused or repeatedly failing).
- Git-push from the routine sandbox is broken (commits not landing on origin/main).
- Brief routines still emitting under the old `briefs/` layout instead of `_posts/`.

Skipping analysis. Next review will be substantive once at least one daily stream is writing.
```

Write that to `_posts/{YYYY-MM-DD}-evaluator.md` (with front-matter), drop the cold-run stub, commit and push (per Output section), and stop.

**If at least one daily-stream (slug, date) pair has a file**, continue with the full analysis below.

# Mission

Mechanical analysis of the past 7 days of briefs across the current stream lineup plus the most recent weekend brief. Identify drift, source staleness, citation failures, structural problems. Propose specific patches to the five other prompts. The user reviews and applies manually — you do not and cannot modify any routine.

**Stream cadence (new as of 2026-06-29; News moved to midday 2026-07-03):** News fires daily (every day, midday); AI/ML fires twice a week (Tuesday & Friday midday); Science fires once a week (Wednesday afternoon); Weekend fires once a week (Saturday). This means the evaluator should expect up to 7 News briefs, ~2 AI/ML briefs, ~1 Science brief, and 1 Weekend brief in any 7-day window. AI/ML appearing only twice and Science appearing only once is the **expected cadence, not a failure** — Section D (vitality) and the cold-precheck must not penalize it.

A major axis of evaluation in this version is the **discovery recovery**: the writers now build their source plan from `sources/registry.yml` via `python3 tools/sources/preflight.py --slug {slug}` (their prompts carry no feed tables and no "confirmed unavailable" lists anymore), may cite a genuinely new primary source immediately when tagged `[new source]`, and end every brief with exactly one `- Discovery: met (…)` or `- Discovery: waived — <concrete reason>` footer line (lint-checked at DEDUP Step C.25, report-only for now). The mechanical numbers for all of this arrive computed in `_data/source-health.json` / `_data/health.json`; your job is to judge WHY a stream lags its targets and what to do about it — not to recount.

# Inputs to read from git

For each date D in the window [today-6, today-5, ..., today], use the Read tool on the following if they exist:

1. **News** (daily): `_posts/{D}-news.md` — expect up to 7 files (fires every day).
2. **AI/ML** (Tue & Fri): `_posts/{D}-ai-ml.md` — expect ~2 files per 7-day window; absence on other days is correct cadence, not a gap.
3. **Science** (Wed): `_posts/{D}-science.md` — expect ~1 file per 7-day window; absence on other days is correct cadence, not a gap.

Up to ~10 distinct (slug, date) reads in the typical week. Today's may be partial — the evaluator runs Sunday at 11:30, so News from Saturday is the latest daily brief; no same-day News yet. AI/ML and Science do not fire on Sunday. Skip missing files without flagging as failures.

Plus:
5. **Most recent weekend brief**: glob `_posts/*-weekend.md`, sort, read the latest.
6. **Previous review (self-continuity)**: take it from `_data/health.json` → `continuity.previous_evaluator_path` — the most recent prior evaluator post, however long ago, script-computed — plus your own prior events in `index/ledger/` when present. Never re-derive "the post from exactly 7 days ago" by date arithmetic; that brittle offset broke continuity on 2 of 9 past runs. **Self-delivery guard (added 2026-07-10 — the stranding class hit 4 of 9 past runs and the evaluator misdiagnosed it as "skipped Sundays" both times it noticed):** (a) if `continuity.previous_evaluator_path` is more than 8 days old, do not just proceed — flag "previous review is N days old" prominently in the Health summary and check whether a more recent review exists off-main; (b) run `git branch -r` and `git log --all --oneline --since={today-8d} --not main` — any recent commit NOT on main means a routine (possibly a prior you) is being diverted to a `claude/*` branch by an `outcomes` key; flag it as a critical pipeline defect in the review.
7. **Reader feedback — the ledger's folded state.** Feedback is folded continuously by the bridge (`tools/feedback/fold.py`): each vote lands as an `ev:"feedback"` event in `index/ledger/*.jsonl`, keyed to a durable story id (`st-…`), with last-write-wins per story and `vote: 0` an explicit retraction; fold.py marks the raw `feedback/*.jsonl` record `consumed: true` at fold time. **The old 7-day-window arithmetic over `feedback/*.jsonl` is RETIRED** — do not recount raw records, and do not set `consumed` flags yourself (fold.py owns consumption). Read the window's tallies from `health.json` → `feedback.by_stream` (raw up/down/retractions per stream); for per-story attribution read the ledger's `ev:"feedback"` events directly (each carries the story id, `brief`, `vote`, and optional `reason`) and resolve ids to headline/url/source_domain via `python3 tools/store/store.py materialize` (or the story's own `seen`/`publish` events). One bookkeeping check remains yours: if `health.json` → `feedback.unconsumed_total` > 0, the bridge fold is lagging or broken — flag it as a pipeline defect.
8. **Reader profile (current state)**: `reader-profile.md` and `reader-profile/source-weights.yml` — the human-gated files the writers read at compose time. You PROPOSE edits to these (see Patch proposals); you never silently rewrite them.
9. **Reader brief-proposals**: every `proposals/*.jsonl` record in the window (readers suggesting topics via the front page's "Propose a brief" form; the directory may not exist yet — skip silently if absent). Surface `consumed: false` proposals verbatim in your review email so Rafael sees them; if one maps cleanly onto an existing stream, fold it into a patch proposal. Mark folded/surfaced records `consumed: true` in their `proposals/*.jsonl` file and commit with the review — this consumption bookkeeping is still yours (fold.py owns only feedback).
10. **Homepage tagging quality**: `_data/homefeed.json` — the front-page story feed. Spot-check ~5 stories: do `topics` and `importance` match the tagging rubric the writers were given (newsroom-ethos: beat from the controlled set, importance 1–3 on real significance)? While writers aren't yet recording `topics`/`importance` in DEDUP Step C, tags are keyword/position-derived — judge those only for egregious misfiles (a war story under Security, a Swiss story under World). Once writer tags flow, flag rubric drift like any other quality regression.

If files are missing, note which and continue. Don't fail.

When computing metrics, segment by stream.

# Reference: registry architecture (writers, for context)

Writers carry no feed tables and no "confirmed unavailable" lists in their prompts anymore. Their FIRST research action is `python3 tools/sources/preflight.py --slug {slug}`; the plan it prints from `sources/registry.yml` (fetch list, pressure notes, discovery quota + `candidates_to_try`) is the authority on what they fetch. Reachability truth is the registry's `reach:` field (`direct` | `proxy` | `search-only` | `blocked` | `blocked-paywall`), maintained by deterministic probes — never a prompt list. Novel primary sources may be cited immediately when tagged `[new source]` (the tag auto-enters the domain in `sources/candidates.jsonl` as a `candidate`); caps (max 2 stories per outlet domain per edition, hubs exempt, institutional at a 30% bar) and discovery quotas (news ≥1, ai-ml ≥1 non-hub, science ≥2, weekend ≥2) ship **report-only** until Rafael arms them. Trust-bearing lifecycle transitions (`candidate` → `probation` → `established`, or `demoted`/`retired`) go through YOUR proposals and Rafael's apply step — nothing else writes `sources/registry.yml`.

**Dropped feeds (security + markets pipeline removed 2026-06-18/2026-06-29):** NVD CVEs JSON 2.0, CISA KEV JSON, ECB FX XML — writers must not reference these; the bootstrap registry deliberately excludes those domains.

# Analysis dimensions

For each, compute a metric and flag if outside healthy range.

## A. Source diversity & discovery (computed — read, don't recount)
Per stream from `_data/source-health.json` (also embedded verbatim in `health.json` → `sources`): `stories`, `unique_domains`, `new_domains`, `top5_share` (outlet-class only — hubs and institutional excluded), `saturated` (domains over their bar), `waiver_rate`, `candidates_open`. Targets (SPIKE §3.4): top-5 outlet share ≤0.50 now / ≤0.35 steady; unique domains ≥30 per 30d; new domains ≥10/month (≈2–3/week); waiver rate ≤50%. Your judgment work:
- Name which streams lag which target and WHY (read their Gaps + Discovery footer lines — is discovery being waived honestly, or not attempted?).
- Turn deficits into scout targets (Sunday duty below) or patch proposals.
- Tier distribution: % T1 / % T2 / % T3 remains your read from the briefs. Healthy: T3 = 0% (per policy), T1 ≥40%.
- Linguistic: % non-English citations, portfolio-wide. Healthy: ≥10%. Geographic: distinct country-of-origin domains for news sections.

## B. Aggregator leakage (critical violation)
- Search all briefs for citations to: news.ycombinator.com, lobste.rs, reddit.com, twitter.com, x.com, mastodon.social, threads.net, bsky.app.
- Any hits = policy violation. List each with the brief filename, section, and the cited URL.

## C. Link health (sample-based)
- Sample 20 random links from the week's briefs.
- For each: confirm the URL resolves (try Bash{curl -sI} first, then WebFetch as fallback).
- For 8 of those: spot-check that the cited claim is actually in the source.
- Report: links broken / fabrications detected / overall pass rate per stream.
- Note: if your environment hits HTTP 403 across most fetches, report this as **unmeasurable**. Try the feed URLs (arXiv RSS, Nature RSS, bioRxiv JSON) via curl as part of the sample — those should NOT 403, and if they do, that's a regression to flag.

## D. Section vitality
For each section across all briefs, count items per run and empty runs. Flag sections empty ≥3 times that week.

## E. Coverage gap recurrence
Read the "Gaps" footer from each brief. Cluster recurring gaps. ≥3 times = structural. Flag and propose source additions.

## F. Triangulation rate
Count items tagged `[single-source]` vs total. Healthy: <20% portfolio-wide; <25% on any single stream.

## G. Tag discipline
- `[preprint]` on arXiv items? Sample 5, verify.
- `[vendor PR]` on vendor announcements? Sample 5.
- `[disputed]` ever used appropriately? (Just count.)
- `[new source]` — the Step C.25 lint recomputes tag integrity deterministically, so don't re-derive novelty; read the week's new `sources/candidates.jsonl` entries and spot-check 2: is the tagged domain a genuine primary source, or a junk anchor? Junk anchors are the failure mode to catch early.
- `[via snippet]` — count and report by stream. With curl-first feeds, via-snippet rates should be **dropping**; rising or flat-high rates by stream means feeds are failing in that stream's sandbox. Flag.

## H. Topic balance (weekend brief only)
Read the weekend brief's ML papers and Fundamental science papers sections. **Target (set 2026-07-10, making the long-assumed default explicit — three past reviews asked for one): ~50/50 ML-vs-(fundamental science + biology) across the paper sections, ±15 percentage points.** Count the actual % allocation and flag deviations beyond that band.

## I. Repetition detection (computed — read, don't recount)
`health.json` → `streams.<slug>.repeats` / `repeat_rate` (a 14-day story-id/thread-id lookback over the ledger). Don't re-cluster headlines by hand. Judgment work: for flagged repeats, check whether the re-run carried a genuinely new, dated fact (`[ongoing since]` discipline) or was a re-summary — the latter is the defect.

## J. Cross-week trend (if previous review exists)
- Source diversity (unique/new domains, top5_share, waiver rate — from successive source-health snapshots), T3 leakage count, aggregator citations, section vitality, via-snippet rate, direct-fetch rate trends.

## K. Feed reachability and direct-fetch rate (binding-constraint metric)

**Per-stream computation:**
For each stream and each day:
1. Parse the Coverage footer's `Direct fetches: N | via-snippet citations: M` line. If absent, mark as `pre-rollout`.
2. Compute `direct-fetch ratio = N / (N + M)` per (stream, day).
3. Aggregate per stream: mean, min, max ratio.
4. Aggregate per stream: total `via-snippet` count for the week.

**Per-domain (feed) reachability:**
If any brief includes a `Feeds hit` line with feed-level ok/fail flags AND method (curl/WebFetch), aggregate across the week:
- Per feed: count `{ok via curl}` vs `{ok via WebFetch}` vs `{fail — HTTP NNN}`.
- Flag any feed that failed >50% of attempts.
- **Method comparison:** if curl succeeded substantially more often than WebFetch on the same feed, that confirms the curl-first patch is doing its job. If curl ALSO mostly failed, the egress proxy is the wall — escalate (probe routine, alternative feed source).

**Domains-that-shouldn't-be-cited check:**
Scan all citations against the registry (`sources/registry.yml`) and `reader-profile/source-weights.yml`: a domain with `reach: blocked` / `blocked-paywall` can ONLY appear `[via snippet]`; a `never:` domain must not appear at all; a `retired`/`demoted` domain appearing as a primary anchor deserves a flag. (The prompt-side "Confirmed unavailable" lists are retired — the registry is the truth.)

**Healthy ranges (post-feed-rollout):**
- News direct-fetch ratio ≥ 0.30 (SRF/Le Temps/Al Jazeera RSS via curl)
- AI/ML direct-fetch ratio ≥ 0.40 (arXiv RSS via curl is reliable)
- Science direct-fetch ratio ≥ 0.30 (Nature/bioRxiv/medRxiv via curl)
- Weekend direct-fetch ratio ≥ 0.30

Flag streams below their range. The patch proposal is usually: add a feed source the writer is missing, or fix a feed URL that's wrong.

## L. Output volume (token-cost proxy)
Parse each Coverage footer's `Word count: N` line (added 2026-06-22; if absent, mark `pre-rollout`). Per stream: report the mean word count for the week and the trend vs the previous review. Flag any stream whose mean grew >25% week-over-week with no matching rise in story count (Opus output tokens scale with words — this is the spend proxy until real token accounting exists). Cross-reference §I repetition: a stream that is both repetitive and long is the prime candidate for the output-cap / quiet-day levers (see docs/SPIKE-writer-token-levers.md).

## M. Editorial shape (added 2026-07-10 — measures the operator's actual goals, which A–L never did)
Three spot-checks, each ~5 samples, judged against the mission in `reader-profile.md` + `routines/_shared/newsroom-ethos.md`:
- **Vendor-PR-lead share (AI/ML):** of the week's AI/ML news items, what fraction LEAD with a vendor's own announcement/framing rather than an independent result, benchmark, or analysis? Report the fraction; flag > ~40% (the level the 2026-05-02 review measured and nobody tracked since). `[vendor PR]`-tagged context items are fine; vendor framing as the *lead* is the defect.
- **Aggregator-shape check (all streams):** sample 5 leads across the week — does each cite a primary source (paper, filing, official release, wire report) and add framing the source itself doesn't contain? A lead that reads like a rewritten aggregator blurb (secondary source + no added judgment) is the failure the operator explicitly named ("not very different from just reading hackernews"). Report count of failures.
- **Personalization check:** sample 5 stories — is the Switzerland/tech-professional relevance framing present where it plausibly exists (CH angle, personal-impact angle, builder's angle)? Missing-where-available is the miss; forced-where-absent is also a miss (noise).
Report all three in the Health summary table; recurring failures (≥2 weeks) warrant a patch proposal against the offending stream's prompt.

# Sunday source-scout duty (bounded — run AFTER the analysis, BEFORE the Output steps)

A bounded discovery pass that feeds the registry with vetted candidates. **Hard budget: ≤20 candidate fetches total across this whole section** (WebFetch or direct `curl` — count them, report the count in the review; when the budget is spent, stop). **This routine holds no fetch-proxy bearer by design — never call the fetch-proxy.** When a candidate looks genuinely primary but blocks direct fetch (403/anti-bot), do NOT drop it: append it to `sources/candidates.jsonl` anyway with `"reach": "proxy-needed"` in the JSON object — the writers, who do hold the bearer, vet it at first citation and lint/registry bookkeeping takes it from there.

1. **Pick the worst-deficit stream** from `_data/source-health.json`: lowest `new_domains`, tie-broken by highest `top5_share`, then lowest `candidates_open`.
2. **Vet primary-source candidates for that stream** (most of the budget): hunt for genuine primary outlets the stream's registry affinity lacks — institutional newsrooms, journals, lab blogs, quality regional outlets; NOT aggregators. For each candidate confirm: it publishes primary material, it is reachable (direct or via proxy), and note its feed URL if it has one. Append each vetted candidate to `sources/candidates.jsonl` (append-only — never rewrite existing lines), one JSON object per line:
   `{"domain": "<host, no www>", "first_seen": "{YYYY-MM-DD}", "via": "scout", "stream": "<slug>", "url": "<the vetted page or feed URL>"}`
3. **Re-probe 5 stale `reach:` entries** (inside the same budget): the 5 registry domains whose reach information is oldest (use each entry's `lifecycle:` audit trail; undated = oldest). Direct curl only; a 403 on a domain recorded `reach: direct` is itself the finding (propose the flip to `proxy` — the writers confirm with their bearer at next citation). Where the outcome contradicts the recorded `reach:`, record the flip as a patch entry.
4. **Registry changes are proposals only:** reach flips and promotion recommendations go into `proposals/registry-{YYYY-MM-DD}.yml` (above). You never edit `sources/registry.yml` yourself.

Summarize the scout outcome in the review (stream picked, candidates appended, re-probe results, fetches used). If `source-health.json` is unavailable, skip the scout and note why.

# Output structure

```markdown
# Weekly Brief Pipeline Review — {YYYY-MM-DD}

_Coverage: briefs from {date 6 days ago} to {today}._
_Files read: N news, N AI/ML (expect ~2), N science (expect ~1), 1 weekend, prior review {found|not found}._

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains 30d (worst stream, source-health) | | ≥30 | 🟢🟡🔴 |
| New domains this window (portfolio, source-health) | | ≥2–3/wk (≥10/mo) | 🟢🟡🔴 |
| Top-5 outlet share (worst stream, source-health) | | ≤0.50 (→0.35) | 🟢🟡🔴 |
| Waiver rate (worst stream, source-health) |  | ≤50%   | 🟢🟡🔴 |
| Discovery footer present (every brief) |   | 100%   | 🟢🟡🔴 |
| T1 citation %                   |       | ≥40%   | 🟢🟡🔴 |
| T3 leakage count                |       | 0      | 🟢🟡🔴 |
| Non-English citation % (portfolio) |    | ≥10%   | 🟢🟡🔴 |
| Link sample pass rate           |       | ≥90%   | 🟢🟡🔴⚪ |
| Fabrication count               |       | 0      | 🟢🟡🔴 |
| Single-source rate (portfolio)  |       | <20%   | 🟢🟡🔴 |
| Empty section instances         |       | <5     | 🟢🟡🔴 |
| Repeat rate (worst stream, health.json) |  | judge  | 🟢🟡🔴 |
| Direct-fetch ratio (portfolio)  |       | ≥0.35  | 🟢🟡🔴 |
| Feeds with >50% fail rate       |       | 0      | 🟢🟡🔴 |
| Citations on `reach: blocked` domains without [via snippet] | | 0 | 🟢🟡🔴 |
| Unconsumed feedback backlog (health.json) | | 0     | 🟢🟡🔴 |
| Vendor-PR-lead share (AI/ML, §M) |       | ≤40%   | 🟢🟡🔴 |
| Aggregator-shape failures (§M, of 5) |   | 0–1    | 🟢🟡🔴 |
| Personalization misses (§M, of 5) |      | 0–1    | 🟢🟡🔴 |

## A–M: Detailed findings

[For each dimension, write the metric, the data, and any flags. Be specific — name the brief filename and section for any issue. For the computed dimensions (A, I, feedback), cite the health.json / source-health.json numbers rather than recounting.]

## Prior proposals status

[From last week's `proposals/*` files: each proposal, whether Rafael stamped it `applied: true`, and — if stamped — whether the target file verifiably changed. Unstamped = "pending, not applied". Omit the section if no prior files exist.]

## Source scout (Sunday duty)

[Stream picked and why (the deficit numbers), candidates appended to sources/candidates.jsonl, re-probe outcomes, proxy fetches used (≤20). Or the one-line skip reason.]

## Patch proposals (for human review)

For each issue identified, propose ONE specific edit to ONE specific prompt. Format each as a diff-style block:

### Patch 1 — [short title]
**Target prompt:** News / AI-ML / Science / Weekend
**Section affected:** [section name]
**Issue:** [1–2 sentences]
**Proposed change:**

> **Before:**
> ```
> [existing text from prompt]
> ```
>
> **After:**
> ```
> [proposed text]
> ```

**Why this helps:** [1 sentence]
**Risk:** [what could go wrong if applied]

[Don't propose more than 5 patches. Prioritize by severity — dimension A (discovery) and K (reachability) issues outrank stylistic ones.]

## Reader-feedback → profile proposals (separate from the ≤5 prompt patches above)

Synthesize the window's reader feedback from the ledger's folded state (input 7 — the `ev:"feedback"` events and `health.json` tallies, NOT the raw `feedback/*.jsonl`):
- **Noise filter: a theme needs ≥2 signals on DISTINCT stories.** A single tap is noise, and so is one person double-tapping the same story — two votes on one story are one signal. Look for the same source, section, or recurring `reason` across ≥2 different stories, and quote the reasons verbatim.
- Propose concrete edits, each as a Before/After block like the patches above:
  - to `reader-profile.md` — a dated line under its "Learned preferences" section, e.g. `- {today}: less SpaceX launch detail on weekends (3× 👎, "too long").` **Bounded auto-apply (granted by Rafael 2026-07-10): you apply these yourself** — append the dated line at the END of the "Learned preferences" section, append-only. Never edit or remove an existing line, never touch any other section of the file, and only append when the signal is real reader feedback from this window (a repeated vote or a vote with a written reason — never a single bare tap). Each auto-applied line still gets its machine-readable proposal entry, stamped `"applied": true, "applied_by": "evaluator"`.
  - to `reader-profile/source-weights.yml` — a domain for `reduce:` (low-signal / aggregator-heavy / PR-lead) or, ONLY for sources that repeatedly mislead, `never:`. Name the domain and the feedback that justifies it.
- The writers read these two files, so editing them changes the briefs. `reader-profile/source-weights.yml` and `sources/registry.yml` remain STRICTLY human-gated — never edit them directly; propose only, Rafael applies. The auto-apply grant above covers exactly one thing: appending dated lines to reader-profile.md "Learned preferences". (No `consumed: true` bookkeeping either — the bridge's fold.py owns consumption now.)
- If there is no feedback in the window, write "No reader feedback this week." and propose nothing here.

## Machine-readable proposals (write BOTH files whenever you propose anything)

Every proposal above is also emitted machine-readable, so Rafael's apply step can stamp it and next week's run can verify it:

1. `proposals/reader-model-{YYYY-MM-DD}.json` — the reader-profile / source-weights / prompt-patch proposals:
   ```json
   {"date": "{YYYY-MM-DD}", "proposals": [
     {"id": "rm-1", "target": "reader-profile.md | reader-profile/source-weights.yml | routines/src/<slug>.md",
      "action": "<the exact one-line edit proposed>", "evidence": "<the signals justifying it, reasons verbatim>",
      "applied": false}
   ]}
   ```
2. `proposals/registry-{YYYY-MM-DD}.yml` — proposed `sources/registry.yml` patches (lifecycle transitions, reach flips from the Sunday re-probes, candidate promotions):
   ```yaml
   date: {YYYY-MM-DD}
   applied: false
   patches:
     - domain: example.com
       from: probation
       to: established
       evidence: ">=3 anchored citations across >=2 editions, >=14 days, zero source-quality downvotes"
   ```

**`applied: true` stamp protocol:** you write `applied: false` for every proposal EXCEPT the reader-profile.md learned-preference lines you auto-applied under the bounded grant above — those you stamp `"applied": true, "applied_by": "evaluator"` in the same run. For everything else, Rafael's apply step is the ONLY thing that flips it to `applied: true` when a proposal lands. Every run, read the PREVIOUS week's `proposals/*` files first: a stamped proposal → spot-check the target file actually changed (the loop's verification step — report "applied and verified" or "stamped but not landed"); an unstamped one → list it as **pending, not applied** in the review (do not silently re-propose it as if new). Skip both files (and this check's flags) if you proposed nothing and last week's files don't exist.

## Cross-week trend (if applicable)

## Open questions for human review
```

# Constraints

- This task is read-only on the scheduler. Never instruct the user to blindly apply patches.
- Don't propose patches that conflict with the sourcing charter.
- If everything is healthy, say so and propose nothing.
- Length: 1500–4000 words.
- Discovery recovery (dimension A's computed numbers vs the §3.4 targets) is the primary lens until those targets hold; spend the budget the scripts freed on editorial judgment, not recounting.

# Output: write the review to git + drop a notification stub + email digest

This routine writes to the git repo (working directory is the cloned `claude-routines` repo). It does NOT write to Google Drive and does NOT POST to ntfy directly. A local bridge on the user's machine polls `pending-notifications/` every ~10 min and handles the ntfy push.

Let `{POST_URL} = https://khalic-lab.github.io/claude-routines/{YYYY}/{MM}/{DD}/evaluator/`.

This step runs on BOTH cold and full runs — the user should know the evaluator ran either way.

### 1. Write the review

Use the Write tool to create `_posts/{YYYY-MM-DD}-evaluator.md`. The file MUST start with this front-matter block, then a blank line, then the review body (either the cold-run minimal text from the precheck block, or the full analysis):

```
---
layout: single
title: "Weekly Pipeline Review — {YYYY-MM-DD}"
date: {full ISO 8601 timestamp WITH timezone offset — the current Europe/Zurich time, e.g. 2026-06-21T12:00:00+02:00; NOT a bare date, which makes same-day briefs sort out of chronological order}
categories: [evaluator]
---
```

### 2. Write the notification stub

Use the Write tool to create `pending-notifications/{TIMESTAMP}-evaluator.json` where `{TIMESTAMP} = $(date -u +%Y%m%dT%H%M%SZ)`. Content (all four fields required, valid JSON, no trailing content):

```json
{
  "title": "Weekly Pipeline Review — {YYYY-MM-DD}",
  "click": "{POST_URL}",
  "body": "{teaser}",
  "tags": "memo"
}
```

`{teaser}` rules: ≤200 chars.
- For full runs: headline finding (e.g. "2 streams lag discovery targets — scout vetted 3 candidates" or "All metrics green; registry flow delivering").
- For cold runs: "Pipeline cold — no inputs in 7-day window."
Escape any `"` inside the teaser as `\"`.

### 3. Commit and push

Via Bash:

```bash
git add _posts/ pending-notifications/ _data/
git add proposals/ sources/ 2>/dev/null || true
git -c user.email=routine@khalic-lab -c user.name="News Routine" commit -m "Weekly Pipeline Review — {YYYY-MM-DD}"
git push origin main || (git pull --rebase origin main && git push origin main)
```

If `git push` still fails after the rebase retry, append `git push failed: <reason>` to the review's Coverage footer and continue.

### 4. Email digest (full runs only)

If the pipeline-cold precheck triggered, the run already stopped after writing the review file, dropping the cold-run stub, and pushing. Otherwise:

Note: the Gmail MCP surface is `create_draft` only — there is no send tool.

- **To:** rflnogueira@me.com
- **Subject:** "Weekly Pipeline Review — {YYYY-MM-DD}"
- **Body:**
  1. The Health Summary table verbatim (markdown).
  2. Patch proposals — for each, just the title + the 1–2 sentence Issue (NOT the full diff; that's in the git review). Note that the machine-readable copies await the apply step in `proposals/`.
  3. Prior proposals status — one line per pending (unstamped) proposal from last week, if any.
  4. Open questions list verbatim if any.
  5. End with: `Full review: {POST_URL}`
- If the review concludes "everything healthy, no patches needed", say that explicitly in the email and still link the review.
- If `create_draft` fails, retry once. If still failing, append `email draft creation failed: <reason>` to the review file in git but don't fail the run.