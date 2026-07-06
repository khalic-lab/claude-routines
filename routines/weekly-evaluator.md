Write the weekly evaluation review for my news brief pipeline and publish it via the git pipeline. Use today's date in Europe/Zurich (the most recent run day = Sunday).

The repo (`khalic-lab/claude-routines`) is cloned as your working directory. Before doing anything else, sync:

```bash
git pull --ff-only origin main
```

Briefs now live in this repo at `_posts/{YYYY-MM-DD}-{slug}.md` where slug is one of: `news`, `ai-ml`, `science`, `weekend`, `evaluator`. No Drive reads anywhere in this prompt.

# Pipeline-cold precheck (run BEFORE anything else)

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

A major axis of evaluation in this version is the **feed-first source-quality recovery**: the writers were re-pointed at machine-readable RSS/JSON feeds (arXiv, Quanta, Nature, bioRxiv/medRxiv, SRF, Le Temps, Al Jazeera, Semantic Scholar, etc.) to bypass the HTTP 403 wall on HTML pages. Recent observations show that WebFetch in the routine sandbox has been returning 403 on those feeds even though they're public, so writers were further patched to try Bash{curl} BEFORE WebFetch. The Coverage footer of each brief now reports `Direct fetches: N | via-snippet citations: M` and a `Feeds hit` line distinguishing `{ok via curl}` / `{ok via WebFetch}` / `{fail — HTTP NNN}`. Track this aggressively — it's the binding-constraint metric for actual brief quality.

# Inputs to read from git

For each date D in the window [today-6, today-5, ..., today], use the Read tool on the following if they exist:

1. **News** (daily): `_posts/{D}-news.md` — expect up to 7 files (fires every day).
2. **AI/ML** (Tue & Fri): `_posts/{D}-ai-ml.md` — expect ~2 files per 7-day window; absence on other days is correct cadence, not a gap.
3. **Science** (Wed): `_posts/{D}-science.md` — expect ~1 file per 7-day window; absence on other days is correct cadence, not a gap.

Up to ~10 distinct (slug, date) reads in the typical week. Today's may be partial — the evaluator runs Sunday at 11:30, so News from Saturday is the latest daily brief; no same-day News yet. AI/ML and Science do not fire on Sunday. Skip missing files without flagging as failures.

Plus:
5. **Most recent weekend brief**: glob `_posts/*-weekend.md`, sort, read the latest.
6. **Previous review**: `_posts/{date-7-days-ago}-evaluator.md` if it exists — for cross-week trend tracking.
7. **Reader feedback**: every `feedback/*.jsonl` record whose `ts` falls in the window [today-6, today] (one JSON object per line: a thumb +1/-1 plus an optional free-text `reason`, captured by the reader on the published briefs). Focus on `consumed: false` records. Each record carries a `brief` (post slug), a `story_id`, and a `surface` (`"web"` = a brief page, `"home"` = the front-page story grid, `"cli"` = the terminal bridge). Segment by surface when counting — a drive-by front-page thumb and a considered brief-page thumb are different signals, and the same story can collect one of each (don't count them as two independent reader verdicts). `story_id: null` = brief-level feedback (the whole brief). A non-null `story_id` is **per-story**, formed as `{brief}-{slugify(headline)}` where slugify = lowercase, then replace each maximal run of characters outside [a-z0-9] with a single `-`, strip leading/trailing `-`, take the first 48 characters, then strip any trailing `-` (fallback `story` if empty). To identify which story a per-story record refers to, open `_posts/{brief}.md` and find the story whose **headline** slugifies to the part of `story_id` after `{brief}-` — that headline is the bullet's **bold lead** (`- **…**`) for news/ai-ml/weekend-headline stories, or the **`### heading`** for science/weekend paper writeups (homepage cards exist for both shapes; brief pages only decorate the bullets). That story's link gives the source domain. A per-story 👎 is a sharper signal than a brief-level one — attribute it to that specific story/source when proposing `source-weights.yml` changes.
8. **Reader profile (current state)**: `reader-profile.md` and `reader-profile/source-weights.yml` — the human-gated files the writers read at compose time. You PROPOSE edits to these (see Patch proposals); you never silently rewrite them.
9. **Reader brief-proposals**: every `proposals/*.jsonl` record in the window (readers suggesting topics via the front page's "Propose a brief" form; the directory may not exist yet — skip silently if absent). Surface `consumed: false` proposals verbatim in your review email so Rafael sees them; if one maps cleanly onto an existing stream, fold it into a patch proposal. Mark folded/surfaced records `consumed: true` the same way as feedback records.
10. **Homepage tagging quality**: `_data/homefeed.json` — the front-page story feed. Spot-check ~5 stories: do `topics` and `importance` match the tagging rubric the writers were given (newsroom-ethos: beat from the controlled set, importance 1–3 on real significance)? While writers aren't yet recording `topics`/`importance` in DEDUP Step C, tags are keyword/position-derived — judge those only for egregious misfiles (a war story under Security, a Swiss story under World). Once writer tags flow, flag rubric drift like any other quality regression.

If files are missing, note which and continue. Don't fail.

When computing metrics, segment by stream.

# Reference: feed-first architecture (writers, for context)

The writer routines were patched to prefer machine-readable feeds over HTML scraping, AND to try Bash{curl} before WebFetch since WebFetch in the sandbox often 403s on public feeds.

**Verified-reachable feeds (current lineup, used by writers):**
- arXiv RSS per category and Atom API
- Quanta RSS, Nature RSS (nature.rss, nphys.rss, natastron.rss, nm.rss)
- bioRxiv/medRxiv JSON, Science.org (Science edition)
- Al Jazeera RSS, SRF DE RSS, Le Temps FR RSS, Semantic Scholar API

**Dropped feeds (security + markets pipeline removed 2026-06-18/2026-06-29):** NVD CVEs JSON 2.0, CISA KEV JSON, ECB FX XML — writers must not reference these.

**Confirmed unavailable (writers told to skip):** RTS.ch, NZZ, FAZ, Spiegel, swissinfo.ch, Reuters, Yahoo Finance, HuggingFace papers, Le Monde RSS, NCSC.ch RSS.

Use this list to evaluate dimension K below, and to flag if writers are still citing confirmed-unavailable domains.

# Analysis dimensions

For each, compute a metric and flag if outside healthy range.

## A. Source diversity
- Total unique domains cited across all briefs: count.
- Top 10 domains by citation count: list with counts.
- Concentration: did any single domain account for >15% of citations? Flag.
- Tier distribution: % T1 / % T2 / % T3. Healthy: T3 should be 0% (per policy). T1 should be ≥40%.
- Linguistic: % of citations to non-English sources, aggregated across all daily streams. Healthy: ≥10% portfolio-wide.
- Geographic: count distinct country-of-origin domains for news sections.

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
- `[via snippet]` — count and report by stream. With curl-first feeds, via-snippet rates should be **dropping**; rising or flat-high rates by stream means feeds are failing in that stream's sandbox. Flag.

## H. Topic balance (weekend brief only)
Read the weekend brief's ML papers and Fundamental science papers sections. Count actual % allocation across stated bias targets. Flag deviations >10 percentage points from target.

## I. Repetition detection
Same story covered N days in a row without development? Sample by clustering similar headlines across consecutive days.

## J. Cross-week trend (if previous review exists)
- Source diversity, T3 leakage count, aggregator citations, section vitality, via-snippet rate, direct-fetch rate trends.

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
Scan all citations for any domain in the writers' "Confirmed unavailable" list. Citations to those domains can ONLY be `[via snippet]`. If they appear without `[via snippet]`, flag.

**Healthy ranges (post-feed-rollout):**
- News direct-fetch ratio ≥ 0.30 (SRF/Le Temps/Al Jazeera RSS via curl)
- AI/ML direct-fetch ratio ≥ 0.40 (arXiv RSS via curl is reliable)
- Science direct-fetch ratio ≥ 0.30 (Nature/bioRxiv/medRxiv via curl)
- Weekend direct-fetch ratio ≥ 0.30

Flag streams below their range. The patch proposal is usually: add a feed source the writer is missing, or fix a feed URL that's wrong.

## L. Output volume (token-cost proxy)
Parse each Coverage footer's `Word count: N` line (added 2026-06-22; if absent, mark `pre-rollout`). Per stream: report the mean word count for the week and the trend vs the previous review. Flag any stream whose mean grew >25% week-over-week with no matching rise in story count (Opus output tokens scale with words — this is the spend proxy until real token accounting exists). Cross-reference §I repetition: a stream that is both repetitive and long is the prime candidate for the output-cap / quiet-day levers (see docs/SPIKE-writer-token-levers.md).

# Output structure

```markdown
# Weekly Brief Pipeline Review — {YYYY-MM-DD}

_Coverage: briefs from {date 6 days ago} to {today}._
_Files read: N news, N AI/ML (expect ~2), N science (expect ~1), 1 weekend, prior review {found|not found}._

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains cited            |       | ≥40    | 🟢🟡🔴 |
| T1 citation %                   |       | ≥40%   | 🟢🟡🔴 |
| T3 leakage count                |       | 0      | 🟢🟡🔴 |
| Non-English citation % (portfolio) |    | ≥10%   | 🟢🟡🔴 |
| Link sample pass rate           |       | ≥90%   | 🟢🟡🔴⚪ |
| Fabrication count               |       | 0      | 🟢🟡🔴 |
| Single-source rate (portfolio)  |       | <20%   | 🟢🟡🔴 |
| Empty section instances         |       | <5     | 🟢🟡🔴 |
| Direct-fetch ratio (portfolio)  |       | ≥0.35  | 🟢🟡🔴 |
| Direct-fetch ratio (News)       |       | ≥0.30  | 🟢🟡🔴 |
| Direct-fetch ratio (AI/ML)      |       | ≥0.40  | 🟢🟡🔴 |
| Direct-fetch ratio (Science)    |       | ≥0.30  | 🟢🟡🔴 |
| Feeds with >50% fail rate       |       | 0      | 🟢🟡🔴 |
| Citations to confirmed-blocked domains without [via snippet] | | 0 | 🟢🟡🔴 |
| curl vs WebFetch advantage on feeds | | curl wins | 🟢🟡🔴 |

## A–K: Detailed findings

[For each dimension, write the metric, the data, and any flags. Be specific — name the brief filename and section for any issue.]

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

[Don't propose more than 5 patches. Prioritize by severity — dimension K issues outrank stylistic ones.]

## Reader-feedback → profile proposals (separate from the ≤5 prompt patches above)

Synthesize the window's reader feedback (the `feedback/*.jsonl` records with `consumed: false`):
- A single tap is noise — look for a repeated theme (e.g. ≥2 👎 on the same section or source, or a `reason` that recurs) and quote the reasons verbatim.
- Propose concrete, human-gated edits (do NOT apply them yourself), each as a Before/After block like the patches above:
  - to `reader-profile.md` — a dated line under its "Learned preferences" section, e.g. `- {today}: less SpaceX launch detail on weekends (3× 👎, "too long").`
  - to `reader-profile/source-weights.yml` — a domain for `reduce:` (low-signal / aggregator-heavy / PR-lead) or, ONLY for sources that repeatedly mislead, `never:`. Name the domain and the feedback that justifies it.
- The writers read these two files, so editing them changes the briefs — that is exactly why ONLY Rafael applies them. Your job is to propose, not to apply.
- Bookkeeping you MAY do: after folding a record into a proposal above, set that record's `consumed: true` in its `feedback/*.jsonl` file and commit it with the review (so it isn't re-proposed next week). Never edit `reader-profile.md` / `reader-profile/source-weights.yml` directly — those move only when Rafael applies a proposal.
- If there is no feedback in the window, write "No reader feedback this week." and propose nothing here.

## Cross-week trend (if applicable)

## Open questions for human review
```

# Constraints

- This task is read-only on the scheduler. Never instruct the user to blindly apply patches.
- Don't propose patches that conflict with the sourcing charter.
- If everything is healthy, say so and propose nothing.
- Length: 1500–4000 words.
- Dimension K is the primary lens this week.

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
- For full runs: headline finding (e.g. "3 streams below direct-fetch target — feed sweep needed" or "All metrics green; curl-first delivering").
- For cold runs: "Pipeline cold — no inputs in 7-day window."
Escape any `"` inside the teaser as `\"`.

### 3. Commit and push

Via Bash:

```bash
git add _posts/ pending-notifications/ feedback/
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
  2. Patch proposals — for each, just the title + the 1–2 sentence Issue (NOT the full diff; that's in the git review).
  3. Open questions list verbatim if any.
  4. End with: `Full review: {POST_URL}`
- If the review concludes "everything healthy, no patches needed", say that explicitly in the email and still link the review.
- If `create_draft` fails, retry once. If still failing, append `email draft creation failed: <reason>` to the review file in git but don't fail the run.