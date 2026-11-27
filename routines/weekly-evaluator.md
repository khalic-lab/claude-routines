Write the weekly evaluation review for my news brief pipeline and publish it via the git pipeline. Use today's date in Europe/Zurich (the most recent run day = Sunday).

Briefs now live in this repo at `_posts/{YYYY-MM-DD}-{slug}.md` where slug is one of: `news`, `ai-ml`, `science`, `weekend`, `sports`, `evaluator`. No Drive reads anywhere in this prompt.

# Fire-start: compute the mechanical state (run FIRST)

```bash
python3 tools/evaluator/metrics.py   # refreshes _data/source-health.json, then writes + prints _data/health.json
```

These two files ARE your mechanical dimensions — per-stream citations/anchors/repeat rates, feedback tallies, source diversity/saturation/waiver numbers, your own continuity **and (since 2026-07-18) the computed brief-text dimensions under `health.json` → `briefs`**: aggregator leakage (B), section vitality (D), single-source rate (F), tag counts (G), weekend paper balance (H), footer fetch ratios + per-feed reachability (K), word-count means incl. the previous week (L), the T1 share (`briefs.t1_share`, per stream under `by_stream`), walled feeds (`briefs.feeds_walled`), a source-lint replay (`briefs.lint`), the Weekend revisit measures (`briefs.weekend_revisits`), the reasoned reader votes still owed a disposition (`feedback.reasoned`), plus the off-main self-delivery guard under `continuity.off_main` and lost editions under `continuity.lost_editions`. **Do not hand-count anything they already report**; read the numbers and spend your word budget on the editorial judgment they cannot compute. If metrics.py crashes (it runs the source-health refresh itself), note it in the review, degrade to reading the briefs directly for that dimension, and continue — never abort the review.

# Pipeline-cold precheck (run BEFORE the analysis)

1. Use Glob (or `ls _posts/`) to enumerate files in `_posts/` whose dates fall in [today-6, today]. Count distinct (slug, date) pairs that have a file.
2. Also locate the most recent `_posts/*-weekend.md` (any date).

**If the total count of (slug, date) pairs with a file is 0**, the pipeline is cold. In that case, write ONLY this minimal review and stop — do NOT proceed to analysis dimensions, do NOT write a long meta-report. BUT still publish it with a cold-run teaser (per the Output section below), so the notification goes out.

```
# Weekly Brief Pipeline Review — {YYYY-MM-DD}

_Pipeline cold — no inputs in window._

Files checked under `_posts/` (all absent for {today-6} to {today}):
- *-news.md
- *-ai-ml.md
- *-science.md
- *-weekend.md (most recent)
- *-sports.md

Likely causes (for human investigation):
- Writer routines have not yet executed in this window (cron-paused or repeatedly failing).
- Git-push from the routine sandbox is broken (commits not landing on origin/main).
- Brief routines still emitting under the old `briefs/` layout instead of `_posts/`.

Skipping analysis. Next review will be substantive once at least one daily stream is writing.
```

Write that to `_posts/{YYYY-MM-DD}-evaluator.md` (body only — front matter is derived at publish), publish it with the cold-run teaser (per Output section), and stop.

**If at least one daily-stream (slug, date) pair has a file**, continue with the full analysis below.

# Mission

Mechanical analysis of the past 7 days of briefs across the current stream lineup plus the most recent weekend brief. Identify drift, source staleness, citation failures, structural problems. Propose specific patches to the six other prompts. The user reviews and applies manually — you do not and cannot modify any routine.

**Stream cadence (new as of 2026-06-29; News moved to midday 2026-07-03; Sports added 2026-07-17):** News fires daily (every day, midday); AI/ML fires twice a week (Tuesday & Friday midday); Science fires once a week (Wednesday afternoon); Weekend fires once a week (Saturday); Sports fires once a week (Monday morning — first-ever run 2026-07-20). This means the evaluator should expect up to 7 News briefs, ~2 AI/ML briefs, ~1 Science brief, 1 Weekend brief, and ~1 Sports brief in any 7-day window. AI/ML appearing only twice and Science/Sports appearing only once is the **expected cadence, not a failure** — Section D (vitality) and the cold-precheck must not penalize it.

A major axis of evaluation in this version is the **discovery recovery**: the writers now build their source plan from `sources/registry.yml` via `python3 tools/sources/preflight.py --slug {slug}` (their prompts carry no feed tables and no "confirmed unavailable" lists anymore), may cite a genuinely new primary source immediately when tagged `[new source]`, and end every brief with exactly one `- Discovery: met (…)` or `- Discovery: waived — <concrete reason>` footer line (lint-checked at publish, report-only for now). The mechanical numbers for all of this arrive computed in `_data/source-health.json` / `_data/health.json`; your job is to judge WHY a stream lags its targets and what to do about it — not to recount.

# Inputs to read from git

For each date D in the window [today-6, today-5, ..., today], use the Read tool on the following if they exist:

1. **News** (daily): `_posts/{D}-news.md` — expect up to 7 files (fires every day).
2. **AI/ML** (Tue & Fri): `_posts/{D}-ai-ml.md` — expect ~2 files per 7-day window; absence on other days is correct cadence, not a gap.
3. **Science** (Wed): `_posts/{D}-science.md` — expect ~1 file per 7-day window; absence on other days is correct cadence, not a gap.
4. **Sports** (Mon): `_posts/{D}-sports.md` — expect ~1 file per 7-day window (first-ever run 2026-07-20; before that date, absence is pre-launch, not a gap).

Up to ~11 distinct (slug, date) reads in the typical week. Today's may be partial — the evaluator runs Sunday morning, so News from Saturday is the latest daily brief; no same-day News yet. AI/ML, Science, and Sports do not fire on Sunday. Skip missing files without flagging as failures.

Plus:
5. **Most recent weekend brief**: glob `_posts/*-weekend.md`, sort, read the latest.
6. **Previous review (self-continuity)**: take it from `_data/health.json` → `continuity.previous_evaluator_path` — the most recent prior evaluator post, however long ago, script-computed — plus your own prior events in `index/ledger/` when present. Never re-derive "the post from exactly 7 days ago" by date arithmetic; that brittle offset broke continuity on 2 of 9 past runs. **Self-delivery guard (added 2026-07-10; computed since 2026-07-18 — the stranding class hit 4 of 9 past runs and the evaluator misdiagnosed it as "skipped Sundays" both times it noticed):** (a) if `continuity.previous_evaluator_path` is more than 8 days old, do not just proceed — flag "previous review is N days old" prominently in the Health summary and check whether a more recent review exists off-main; (b) read `health.json` → `continuity.off_main` (metrics.py runs the `git branch -r` / `git log --not origin/main` checks for you) — any `commits_not_on_main` entry means a routine (possibly a prior you) is being diverted off main by an `outcomes` key THIS window: flag it as a critical pipeline defect. The sandbox clone is shallow: when `off_main.shallow` is true, commits from before the clone's history boundary cannot be checked against main, so metrics.py counts them in `shallow_skipped` instead of listing them. A fire-start `git pull` printing "(forced update)" together with a non-zero `shallow_skipped` is the expected signature of the depth-limited fetch (the 2026-09-20/27 false positive) — do not flag it as stranding. The check cannot tell that apart from a genuine force-push that dropped commits from main, so if content is missing (an expected edition absent from `_posts/` on HEAD), say so as a possible rewrite. `remote_branches` is context only — old recovered `claude/*` branches linger there; a branch is a defect only when it also shows recent commits. (c) `continuity.lost_editions` (computed since 2026-11) lists editions a writer session measured in `index/usage/` that have no `_posts/` file. Each is a LOST edition — the run happened and its commit never reached main — never a "skipped fire" (2026-10-06 News was one; the 10-11 review called it skipped). Flag every entry in the Health summary with its `session_id` and `started`.
7. **Reader feedback — the ledger's folded state.** Feedback is folded continuously by the bridge (`tools/feedback/fold.py`): each vote lands as an `ev:"feedback"` event in `index/ledger/*.jsonl`, keyed to a durable story id (`st-…`), with last-write-wins per story and `vote: 0` an explicit retraction; fold.py marks the raw `feedback/*.jsonl` record `consumed: true` at fold time. **The old 7-day-window arithmetic over `feedback/*.jsonl` is RETIRED** — do not recount raw records, and do not set `consumed` flags yourself (fold.py owns consumption). Read the window's tallies from `health.json` → `feedback.by_stream` (raw up/down/retractions per stream); for per-story attribution read the ledger's `ev:"feedback"` events directly (each carries the story id, `brief`, `vote`, and optional `reason`) and resolve ids to headline/url/source_domain with `python3 -c "import sys; sys.path.insert(0, 'tools/store'); import store; s = store.materialize(days=130)['stories']; [print(i, *[(s.get(i) or {}).get(k) for k in ('date', 'headline', 'url', 'source_domain')], sep=' | ') for i in sys.argv[1:]]" st-… st-…` (one line per id; never read `index/ledger/.materialized.json` itself, a multi-megabyte single line) (or the story's own `seen`/`publish` events). One bookkeeping check remains yours: if `health.json` → `feedback.unconsumed_total` > 0, the bridge fold is lagging or broken — flag it as a pipeline defect.
8. **Reader profile (current state)**: `reader-profile.md` and `reader-profile/source-weights.yml` — the human-gated files the writers read at compose time. You PROPOSE edits to these (see Patch proposals), and append dated "Learned preferences" lines under the bounded grant described there; you never rewrite or remove anything in them.
9. **Reader brief-proposals**: every `proposals/*.jsonl` record in the window (readers suggesting topics via the front page's "Propose a brief" form; the directory may not exist yet — skip silently if absent). Surface `consumed: false` proposals verbatim in the review itself (a short section under Open questions) so Rafael sees them; if one maps cleanly onto an existing stream, fold it into a patch proposal. Mark folded/surfaced records `consumed: true` in their `proposals/*.jsonl` file and commit with the review — this consumption bookkeeping is still yours (fold.py owns only feedback).
10. **Homepage tagging quality**: `_data/homefeed.json` — the front-page story feed. Spot-check ~5 stories: do `topics` and `importance` match the tagging rubric the writers were given (newsroom-ethos: beat from the controlled set, importance 1–3 on real significance)? **Writer tags now flow** (every story recorded in DEDUP Step C carries both), so judge rubric drift like any other quality regression — a misfiled beat, or an edition with no 3 / several 3s, is the writer's error to flag. Keyword/position derivation survives only as the fallback for older records, so a pre-rollout post's odd tag is not a finding.

If files are missing, note which and continue. Don't fail.

When computing metrics, segment by stream.

# Reference: registry architecture (writers, for context)

Writers carry no feed tables and no "confirmed unavailable" lists in their prompts anymore. Their FIRST research action is `python3 tools/sources/preflight.py --slug {slug}`; the plan it prints from `sources/registry.yml` (fetch list, pressure notes, discovery quota + `candidates_to_try`) is the authority on what they fetch. Reachability truth is the registry's `reach:` field (`direct` | `proxy` | `search-only` | `blocked` | `blocked-paywall`) — never a prompt list. No probe job maintains it: drift is computed from the writers' own fetch telemetry (`health.json` → `briefs.reach_drift`, §K), and `registry.py sync` applies a direct → proxy flip by itself once it holds in two consecutive weekly windows (lifecycle `event: reach-flip`, note `(auto)`); you judge the exceptions. Novel primary sources may be cited immediately when tagged `[new source]` (the publish-time lint buffers the domain in `sources/candidates.jsonl`, and the same publish's `registry.py sync` folds it into `sources/registry.yml` as `status: candidate`, so the buffer is always empty when you fire); caps (max 2 stories per outlet domain per edition, hubs exempt, institutional at a 30% bar) and discovery quotas (news ≥1, ai-ml ≥1 non-hub, science ≥2, weekend ≥2, sports ≥1) ship **report-only** until Rafael arms them. Promotion is mechanical since 2026-11-27: sync moves a cited candidate to `probation`, and one with ≥5 citations in the index window to `established` (lifecycle `event: promoted`). Judgment transitions — `demoted`/`retired`, class/tier fixes, registrations, `→ blocked`, `proxy → direct` — go through YOUR proposals and Rafael's apply step; sync's mechanical folds (candidates, last_cited, promotions, two-week reach flips) are not trust transitions.

**Dropped feeds (security + markets pipeline removed 2026-06-18/2026-06-29):** NVD CVEs JSON 2.0, CISA KEV JSON, ECB FX XML — writers must not reference these; the bootstrap registry deliberately excludes those domains.

# Analysis dimensions

For each, compute a metric and flag if outside healthy range.

## A. Source diversity & discovery (computed — read, don't recount)
Per stream from `_data/source-health.json` (also embedded verbatim in `health.json` → `sources`): `stories`, `unique_domains`, `new_domains`, `top5_share` (outlet-class only — hubs and institutional excluded), `saturated` (domains over their bar), `waiver_rate`, `candidates_open` (registered candidates plus any unfolded buffer lines). Targets are tiered by cadence (SPIKE §3.4, tiered 2026-10-01): **news and ai-ml** (several editions a week) — top-5 outlet share ≤0.50 now / ≤0.35 steady; unique domains ≥30 per 30d; new domains ≥10/month (≈2–3/week). **science, sports, weekend** (one edition a week, ~4 per 30d) — unique domains ≥10 per 30d; new domains ≥3/month; top-5 share is reported but carries no status, because with ~10 domains the top five hold most citations by construction. Waiver rate ≤50% for every stream. Judge each stream against its own tier; "worst stream" in the Health summary means the furthest from its tier's target. Your judgment work:
- Name which streams lag which target and WHY (read their Gaps + Discovery footer lines — is discovery being waived honestly, or not attempted?).
- Turn deficits into scout targets (Sunday duty below) or patch proposals.
- Tier distribution (computed since 2026-11-27): `health.json` → `briefs.t1_share` (portfolio) and `briefs.by_stream.<slug>.t1_share` / `tiers`, summed from every footer's `Sources used` line (registry tier of each citation's first link; untiered = not yet in the registry). Never switch methods between weeks; this is the trend row. Healthy: T3 = 0% (per policy), T1 ≥40%. A low T1 share can be registry tiering (sync registers every new non-hub domain as T2), not sourcing: say which.
- Source lint (computed): `health.json` → `briefs.lint` replays the publish-time lint over the window (`by_category`, `by_stream`, `items`). A `discovery_quota` item means a footer claimed `met` that the lint does not verify: count that edition as not met. The lint accepts any tagged new domain, outlets included, so passing it does not prove `met`: the primary-only test ("What counts toward the quota" in the writers' source plan) stays yours. Report `outlet_cap` (anchors over the per-edition cap; a lab's own posts about its own releases are exempt in the AI/ML prompt, so an AI/ML cap hit on a first-party lab domain is not a finding) and `tag_false` / `tag_missing` counts per stream. For sports, also compare each Discovery waiver against that edition's `Feeds hit` line: a waiver naming no official host that appears there is a non-attempt.
- Linguistic: % non-English citations, portfolio-wide. Healthy: ≥10%. Geographic: distinct country-of-origin domains for news sections.

## B. Aggregator leakage (computed — read, don't recount)
`health.json` → `briefs.aggregator_leakage` lists every citation of news.ycombinator.com, lobste.rs, reddit.com, twitter.com, x.com, mastodon.social, threads.net, bsky.app — with post filename and URL. Any entry = policy violation; report each verbatim and name the section by reading that post.

## C. Link health (sampling computed; claim-checks yours)
- Run `python3 tools/evaluator/linkcheck.py --check` — it draws the week's deterministic 20-link sample and resolves each direct (this routine holds no proxy bearer, so most hosts answer with an egress refusal). It also ALWAYS checks every Weekend "Week in headlines" link (marked `[recap]`, on top of the 20, never drawn into them) on its own `recap` line. Each summary line splits the misses into **broken** (404/410: the page is gone), **blocked** (any other HTTP answer: the host refused, the page may exist) and **unreachable** (no answer at all), and gives the **measurable** pass rate. Paste both summary lines; the Health-summary row is the measurable rate.
- Every **broken** recap link is a fabrication candidate (the recap must cite only URLs fetched that run), and so is every link in a Weekend footer's computed `Recap links not fetched this run` line (summed in `briefs.by_stream.weekend.recap_unfetched`); count both under Fabrication unless the page demonstrably existed and was removed.
- For 8 of the resolved links: spot-check that the cited claim is actually in the source (this is the judgment half — fetch via curl/WebFetch and read).
- Report: links broken / fabrications detected / overall pass rate per stream.
- Report ⚪ **unmeasurable** only when unreachable exceeds half the sample; a broken link is a finding even then. The feed URLs (arXiv RSS, Nature RSS, bioRxiv JSON) should NOT 403, and if they do that's an egress regression.

## D. Section vitality + reading surface (computed — read, don't recount)
`health.json` → `briefs.by_stream.<slug>.sections` / `empty_sections` (per-post empty sections, named). Flag sections empty ≥3 times that week; your judgment call is WHY (dead beat, source gap, or honest omit-don't-fill).

**Reading surface.** The homepage feed is the only place a reader sees a story. Run `python3 tools/evaluator/surface.py` (read-only, no network: it parses `_posts/` with the feed builder's own parser and compares against the committed `_data/homefeed.json`). It prints, per edition, stories in the post / records kept in the index / cards on the feed / kept records that reached no card, then `FLAG` lines: `PARITY` (a kept record reached no card), `WARN` (no prose parsed — the card shows only its lede), `SHORT` (a desk's newest edition shows fewer cards than its floor), `OVERDUE` (a desk's newest edition is older than its cadence), `STALE-FEED`. Paste its summary line and every FLAG. Fewer cards than stories on an OLDER edition is the builder's age-out/cap, not a finding. Your judgment: for each PARITY/WARN, read the post and say whether the writer broke the format contract or the parser missed a legal shape (the latter is a builder defect — name the shape); for OVERDUE, cross-check the cadence note above before calling a desk dead. If the script prints `surface: unavailable`, say so and spot-check the feed against the newest post by hand.

## E. Coverage gap recurrence
Read the "Gaps" footer from each brief. Cluster recurring gaps. ≥3 times = structural. Flag and propose source additions.

## F. Triangulation rate (computed — read, don't recount)
`health.json` → `briefs.by_stream.<slug>.single_source_rate` (and the raw counts). Healthy: <20% portfolio-wide; <25% on any single stream.

## G. Tag discipline (counts computed; spot-checks yours)
Tag counts per stream are in `health.json` → `briefs.by_stream.<slug>.tags` — don't recount. Your judgment work:
- `[preprint]` on arXiv items? Sample 5, verify.
- `[vendor PR]` on vendor announcements? Sample 5.
- `[disputed]` used appropriately? (Judge the counted uses.)
- `[new source]` — the publish-time source lint recomputes tag integrity deterministically, so don't re-derive novelty; read the week's new registry candidates — `sources/registry.yml` entries whose `lifecycle` holds an `event: candidate` dated inside the window (`sources/candidates.jsonl` is a transit buffer that `registry.py sync` empties at every publish) — and spot-check 2: is the tagged domain a genuine primary source, or a junk anchor? Junk anchors are the failure mode to catch early.
- `[via snippet]` — read the per-stream count from the computed tags. With the wrapper's curl-first chain, via-snippet rates should be **dropping**; rising or flat-high rates by stream means feeds are failing in that stream's sandbox. Flag.

## H. Topic balance (weekend brief only; computed — read, don't recount)
`health.json` → `briefs.weekend_balance` (`ml_items` / `science_items` / `ml_share`, counted across the weekend paper sections). **Target (set 2026-07-10, making the long-assumed default explicit — three past reviews asked for one): ~50/50 📄 ML vs 🔭 fundamental-science papers (the entries under those two sections only; 🧬 Biology and the other desks move neither side — the split `metrics.py` counts and the Weekend prompt states), ±15 percentage points** — i.e. `ml_share` outside [0.35, 0.65] is a flag.

## I. Repetition detection (computed — read, don't recount)
`health.json` → `streams.<slug>.repeats` / `repeat_rate` (a 14-day story-id/thread-id lookback over the ledger). Don't re-cluster headlines by hand. For the Weekend, `repeats` includes the revisits of daily editions its prompt allows; `repeats_same_stream` is the re-run of a prior Weekend (the defect). Judge revisits from `briefs.weekend_revisits` instead: per section, `revisits` against the Weekend's budget (≤3 in the ML/AI papers section, ≤2 in fundamental science, ≤2 across models / Apple Silicon / biology / data science), and `containment_mean`, the share of a revisit's 5-word sequences copied from the daily (unrelated text ≈0.00, a summary rewritten from the source ≈0.15; above ~0.30 reads as a re-summary — provisional threshold). The recap row measures the recap's write-from-the-fetch rule the same way. Judgment work: for flagged repeats, check whether the re-run carried a genuinely new, dated fact (`[ongoing since]` discipline) or was a re-summary — the latter is the defect.

**Identity integrity (deterministic; added 2026-07-10):** run `python3 tools/store/reconcile.py --root .` and read its output. Any `RECONCILE: flagged` or `RECONCILE: edition file missing` line means a story id in a publish event is absent from its edition's index file — the anchor/feedback target and the dedup-canonical id have forked (the 2026-07-07 Cuba defect class). Report every flagged sid in the review; `resolved-by-merge` lines are informational.

## J. Cross-week trend (if previous review exists)
Write the trend once, in the "Cross-week trend" section of the output (source diversity, T1 share, T3 leakage, aggregator citations, section vitality, via-snippet and direct-fetch rates); §J has no separate subsection. **Method break on 2026-11-27:** 61 domains moved from `outlet` to `institutional`/`hub` (top-5 outlet share and the outlet cap shift with them), T1 share is computed from the footers for the first time, 101 entries went `reach: proxy` and 100 were promoted. Mark the first review after that date as a method break in the trend, not as a regression or a recovery.

## K. Feed reachability and direct-fetch rate (binding-constraint metric; computed — read, don't recount)

**Per-stream:** `health.json` → `briefs.by_stream.<slug>.direct_fetches` / `via_snippet` / `direct_fetch_ratio` (footer-derived; since 2026-07-18 the footers themselves are computed from the fetch log, so these are exact, not self-reported). A stream with no parseable footer shows nulls — mark it `pre-rollout`.

**Per-feed:** `health.json` → `briefs.feeds` aggregates every `Feeds hit` entry across the week (`ok_curl` / `ok_proxy` / `ok_webfetch` / `fail` per feed, both the legacy hand-written and the new computed footer formats). Your judgment work:
- Flag every feed in `health.json` → `briefs.feeds_walled` (failures beyond the curl-first miss outnumber all successes: the chain cannot reach it). The raw >50%-fail ratio is not a finding, because every proxy-only host fails curl once per success.
- **Method comparison:** if direct curl succeeds where only the proxy used to, or the proxy carries most of a stream's fetches, say so. If curl AND proxy both mostly fail on a feed, the egress proxy is the wall — escalate (probe routine, alternative feed source).
- **Reach drift (computed):** `health.json` → `briefs.reach_drift.flips` lists every registry domain recorded `reach: direct` whose hosts this window had 0 curl successes, at least one failure, and ≥`min_proxy` proxy successes (subdomain hosts fold into their registry domain). Flips that held two consecutive windows are applied by `registry.py sync` at the next writer publish: do NOT copy computed flips into `proposals/registry-{YYYY-MM-DD}.yml`. Report one line: N applied this week (lifecycle entries dated in the window whose note contains `(auto)`) and M single-window flips still pending. Propose `proxy → direct` (with telemetry) only for a flip that looks wrong. The reverse case — curl now succeeding on a `proxy` domain — is yours to spot in `briefs.feeds`, and goes into the proposals file as a judgment patch.

**Domains-that-shouldn't-be-cited check:**
Scan all citations against the registry (`sources/registry.yml`) and `reader-profile/source-weights.yml`: a domain with `reach: blocked` / `blocked-paywall` can ONLY appear `[via snippet]`; a `never:` domain must not appear at all; a `retired`/`demoted` domain appearing as a primary anchor deserves a flag. (The prompt-side "Confirmed unavailable" lists are retired — the registry is the truth.)

**Healthy ranges (post-feed-rollout):**
- News direct-fetch ratio ≥ 0.30 (SRF/Le Temps/Al Jazeera RSS via curl)
- AI/ML direct-fetch ratio ≥ 0.40 (arXiv RSS via curl is reliable)
- Science direct-fetch ratio ≥ 0.30 (Nature/bioRxiv/medRxiv via curl)
- Weekend direct-fetch ratio ≥ 0.30
- Sports direct-fetch ratio ≥ 0.30 (BBC Sport/SRF Sport RSS via curl; official league pages often need the proxy — that's expected, not a flag)

Flag streams below their range. The patch proposal is usually: add a feed source the writer is missing, or fix a feed URL that's wrong.

## L. Output volume (token-cost proxy; computed — read, don't recount)
`health.json` → `briefs.by_stream.<slug>.words_mean` / `words_mean_prev_week` / `calls_mean` (footer-derived; exact word counts since 2026-07-18). Flag any stream whose mean grew >25% week-over-week with no matching rise in story count (Opus output tokens scale with words — this is the spend proxy until real token accounting exists). Cross-reference §I repetition: a stream that is both repetitive and long is the prime candidate for the output-cap / quiet-day levers (see docs/SPIKE-writer-token-levers.md).

## M. Editorial shape (added 2026-07-10 — measures the operator's actual goals, which A–L never did)
Three spot-checks, each ~5 samples, judged against the mission in `reader-profile.md` + `routines/_shared/newsroom-ethos.md`:
- **Vendor-PR-lead share (AI/ML):** of the week's AI/ML news items, what fraction LEAD with a vendor's own announcement/framing rather than an independent result, benchmark, or analysis? Report the fraction; flag > ~40% (the level the 2026-05-02 review measured and nobody tracked since). `[vendor PR]`-tagged context items are fine; vendor framing as the *lead* is the defect. Report two numbers: vendor-led items (first link is the vendor's own post), and vendor-ONLY items (vendor-led with no independent check the brief read and named). A vendor-led item whose headline and significance come from a named independent check is not the defect. Flag vendor-ONLY above ~20%, and keep reporting vendor-led for trend.
- **Aggregator-shape check (all streams):** sample 5 leads across the week — does each cite a primary source (paper, filing, official release, wire report) and add framing the source itself doesn't contain? A lead that reads like a rewritten aggregator blurb (secondary source + no added judgment) is the failure the operator explicitly named ("not very different from just reading hackernews"). Report count of failures.
- **Personalization check:** sample 5 stories — is the Switzerland/tech-professional relevance framing present where it plausibly exists (CH angle, personal-impact angle, builder's angle)? Missing-where-available is the miss; forced-where-absent is also a miss (noise).
Report all three in the Health summary table; recurring failures (≥2 weeks) warrant a patch proposal against the offending stream's prompt.

## N. Affiliation element (papers streams; added 2026-07-10)
Two checks on the week's paper coverage (ai-ml, science, weekend — see the Affiliations block in the writer prompts and SPIKE-2026-07-10-affiliation-element):
- **Coverage rate:** across the week's paper bylines, what fraction read `(affiliation not listed)`? Target < ~20% now that the chain reads the paper's own HTML author block (2026-07-07 ran at 70% under the old API chain; 2026-07-10 hit 0% under the new one). Also spot-check 3 bylines against `"affiliations"` on the matching `index/stories/` records — a byline whose institutions never reached the record means the writer skipped the Step C field.
- **Halo audit (anti-prestige guard):** compare the `importance` scores of this week's `(affiliation not listed)` / independent-author papers against the big-lab-affiliated ones. Affiliations are recorded for the reader, never a selection signal — if unaffiliated papers systematically land at importance 1 while equivalent-content lab papers land at 2–3, that is the LLM prestige bias the guard exists to prevent (arXiv:2509.15122); flag it and propose a patch.
Report both in the Health summary table.

# Sunday source-scout duty (bounded — run AFTER the analysis, BEFORE the Output steps)

A bounded discovery pass that feeds the registry with vetted candidates. **Hard budget: ≤20 candidate fetches total across this whole section** (WebFetch or direct `curl` — count them, report the count in the review; when the budget is spent, stop). **This routine holds no fetch-proxy bearer by design — never call the fetch-proxy.** When a candidate looks genuinely primary but blocks direct fetch (403/anti-bot), do NOT drop it: append it to `sources/candidates.jsonl` anyway with `"reach": "proxy-needed"` in the JSON object — the writers, who do hold the bearer, vet it at first citation and lint/registry bookkeeping takes it from there.

1. **Pick the worst-deficit stream** from `_data/source-health.json`: lowest `new_domains` as a fraction of its tier's monthly target (§A: 10 for news/ai-ml, 3 for science/sports/weekend), tie-broken by highest `top5_share` among news/ai-ml, then lowest `candidates_open`. If every stream meets its target, pick the one with the lowest ratio anyway.
2. **Vet primary-source candidates for that stream** (most of the budget): hunt for genuine primary outlets the stream's registry affinity lacks — institutional newsrooms, journals, lab blogs, quality regional outlets; NOT aggregators. For each candidate confirm: it publishes primary material, it is reachable (direct or via proxy), and note its feed URL if it has one. Append each vetted candidate to `sources/candidates.jsonl` (append-only — never rewrite existing lines), one JSON object per line:
   `{"domain": "<host, no www>", "first_seen": "{YYYY-MM-DD}", "via": "scout", "stream": "<slug>", "url": "<the vetted page or feed URL>", "reach": "direct"}`
   Write `"reach": "direct"` only when you fetched the URL yourself and it returned the content: sync then installs it as the entry's probe. A `proxy-needed` URL is unverified and stays a note. **Before vetting any domain, grep `sources/registry.yml` for it (and its parent domain):** never propose a domain that is already registered (news.uzh.ch was proposed as "absent" on 2026-10-11 after two months on file).
3. **Registry changes are proposals only:** judgment changes (demotion, retirement, class/tier fixes, registrations, `→ blocked`, `proxy → direct`) go into `proposals/registry-{YYYY-MM-DD}.yml` (above). Computed direct → proxy flips and promotions are applied by `registry.py sync`; never propose them. You never edit `sources/registry.yml` yourself. (The old step that re-probed 5 stale `reach:` entries by direct curl is retired: from this egress it only ever measured the allowlist wall, and the writers' telemetry covers every cited host.)

Summarize the scout outcome in the review (stream picked, candidates appended, fetches used). If `source-health.json` is unavailable, skip the scout and note why.

# Output structure

```markdown
# Weekly Brief Pipeline Review — {YYYY-MM-DD}

_Coverage: briefs from {date 6 days ago} to {today}._
_Files read: N news, N AI/ML (expect ~2), N science (expect ~1), N sports (expect ~1), 1 weekend, prior review {found|not found}._

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains 30d (worst stream vs its tier, source-health) | | ≥30 news/ai-ml · ≥10 weekly | 🟢🟡🔴 |
| New domains this window (portfolio, source-health) | | ≥2–3/wk (≥10/mo) | 🟢🟡🔴 |
| Top-5 outlet share (worst of news/ai-ml, source-health) | | ≤0.50 (→0.35); weekly streams report only | 🟢🟡🔴 |
| Waiver rate (worst stream, source-health) |  | ≤50%   | 🟢🟡🔴 |
| Discovery footer present (every brief) |   | 100%   | 🟢🟡🔴 |
| T1 share (briefs.t1_share)      |       | ≥40%   | 🟢🟡🔴 |
| T3 leakage count                |       | 0      | 🟢🟡🔴 |
| Non-English citation % (portfolio) |    | ≥10%   | 🟢🟡🔴 |
| Link sample pass rate (measurable) |    | ≥90%   | 🟢🟡🔴⚪ |
| Fabrication count               |       | 0      | 🟢🟡🔴 |
| Single-source rate (portfolio)  |       | <20%   | 🟢🟡🔴 |
| Empty section instances         |       | <5     | 🟢🟡🔴 |
| Reading-surface flags (§D, surface.py) |  | 0      | 🟢🟡🔴 |
| Repeat rate (worst stream, health.json) |  | judge  | 🟢🟡🔴 |
| Direct-fetch ratio (portfolio)  |       | ≥0.35  | 🟢🟡🔴 |
| Feeds walled (briefs.feeds_walled) |    | 0      | 🟢🟡🔴 |
| Lost editions (continuity.lost_editions) | | 0  | 🟢🔴 |
| Source-lint violations (briefs.lint) |  | 0 quota / 0 cap | 🟢🟡🔴 |
| Citations on `reach: blocked` domains without [via snippet] | | 0 | 🟢🟡🔴 |
| Unconsumed feedback backlog (health.json) | | 0     | 🟢🟡🔴 |
| Vendor-ONLY share (AI/ML, §M; vendor-led for trend) | | ≤20% | 🟢🟡🔴 |
| Aggregator-shape failures (§M, of 5) |   | 0–1    | 🟢🟡🔴 |
| Personalization misses (§M, of 5) |      | 0–1    | 🟢🟡🔴 |

## A–N: Detailed findings

[A dimension whose Health-summary row is 🟢 gets NO subsection: the row is the finding. Write a subsection only for 🟡/🔴/⚪ rows and for the judgment checks (C claim checks, G spot-checks, M, N), and in those list only the mismatches ("8 checked, 8 consistent" is the whole report when all pass). Be specific — name the brief filename and section for any issue. Cite the health.json / source-health.json numbers rather than recounting.]

## Prior proposals status

[Every still-pending proposal across ALL prior `proposals/*` files (not only last week's), checked against the live target file, never the flag. One line each: id, first proposed date, weeks pending, "applied and verified" / "stamped but not landed" / "pending". Re-confirming evidence this week gets one clause, not a paragraph. Items applied this week (including sync's `(auto)` reach flips and promotions) are one count line. Omit the section if no prior files exist.]

## Source scout (Sunday duty)

[Stream picked and why (the deficit numbers), candidates appended to sources/candidates.jsonl, fetches used (≤20). Or the one-line skip reason.]

## Patch proposals (for human review)

For each issue identified, propose ONE specific edit to ONE specific prompt. Format each as a diff-style block:

### Patch 1 — [short title]
**Target file:** `routines/src/<slug>.md` (News / AI-ML / Science / Weekend / Sports) or a shared partial `routines/_shared/<name>.md` (all writers), with its current line number
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
- **Completeness first: every reasoned event gets a disposition.** Before any filtering, enumerate the window's reasoned feedback events — every `ev:"feedback"` event whose `reason` is a non-empty string (the fold writes `reason: ""` on bare votes; exclude only those), 👍 or 👎 — from `health.json` → `feedback.reasoned`: metrics.py lists every reasoned event of the last 120 days that no earlier review dispositioned `applied` or `rejected`. `carried: true` marks one dated before this window: a vote cast on a Sunday after the previous review ran (20 votes, 4 of them reasoned, fell between windows before 2026-11-27), or one deferred earlier (`prior: "deferred"`). Carried events count toward this week's bar on the same theme or source_domain. The list is exhaustive and nothing falls between two windows. Then give each one an explicit one-line disposition here: **applied** (name the proposal/patch id), **deferred** (name the threshold reason, e.g. "below the 2-distinct-stories bar"), or **rejected** (with the reason). No reasoned event may be silently omitted — the noise filter below decides what becomes a proposal, never what gets listed.
- **Noise filter, by kind of signal.** (a) A **correction**, meaning a reasoned vote that names an error in the brief's own text (a wrong fact, title, date or label, a missing attribution, a loaded word in the brief's voice), qualifies ALONE: the reader has caught an error, and that is not a taste to be confirmed. (b) A **preference** about selection, emphasis, length or sources needs ≥2 signals on DISTINCT stories, carried events (`feedback.reasoned` → `carried: true`) included. Two votes on one story are one signal; a bare tap is never a signal. Look for the same source_domain, section or recurring `reason` across stories at any distance in time, and quote the reasons verbatim. (c) Before proposing, read reader-profile.md "Learned preferences": a signal an existing line already covers is a **recurrence**. Do not append a line for it. Disposition it `applied` with `ref: "<that line's date> (recurrence)"` and report it in the review as a compliance failure, quoting the brief.
- Propose concrete edits, each as a Before/After block like the patches above:
  - to `reader-profile.md` — a dated line under its "Learned preferences" section, e.g. `- {today}: less SpaceX launch detail on weekends (3× 👎, "too long").` A 👍-sourced theme gets the same treatment phrased as reinforcement — e.g. `- {today}: more primary-source AI-safety papers (3× 👍, "exactly what I want more of").` — reinforcement wording ("more like this because X") for 👍, correction wording for 👎. **Bounded auto-apply (granted by Rafael 2026-07-10): you apply these yourself** — append the dated line at the END of the "Learned preferences" section, append-only. Never edit or remove an existing line, never touch any other section of the file, and only append when the signal is listed in `feedback.reasoned` and clears the noise filter above (never a single bare tap). Each auto-applied line still gets its machine-readable proposal entry, stamped `"applied": true, "applied_by": "evaluator"`.
  - to `reader-profile/source-weights.yml` — a domain for `reduce:` (low-signal / aggregator-heavy / PR-lead) or, ONLY for sources that repeatedly mislead, `never:`. Name the domain and the feedback that justifies it.
- The writers read these two files, so editing them changes the briefs. `reader-profile/source-weights.yml` and the judgment fields of `sources/registry.yml` (class, tier, demotion/retirement, registrations, `blocked`) remain STRICTLY human-gated — never edit them directly; propose only, Rafael applies. The auto-apply grant above covers exactly one thing: appending dated lines to reader-profile.md "Learned preferences". (No `consumed: true` bookkeeping either — the bridge's fold.py owns consumption now.)
- If there is no feedback in the window, write "No reader feedback this week." and propose nothing here.

## Machine-readable proposals (write BOTH files whenever you propose anything)

Every proposal above is also emitted machine-readable, so Rafael's apply step can stamp it and next week's run can verify it:

1. `proposals/reader-model-{YYYY-MM-DD}.json` — the reader-profile / source-weights / prompt-patch proposals:
   ```json
   {"date": "{YYYY-MM-DD}", "proposals": [
     {"id": "rm-1", "target": "reader-profile.md | reader-profile/source-weights.yml | routines/src/<slug>.md | routines/_shared/<name>.md",
      "action": "<the exact one-line edit proposed>", "evidence": "<the signals justifying it, reasons verbatim>",
      "applied": false}
   ], "dispositions": [
     {"fb_id": "<uuid>", "story_id": "st-...", "disposition": "applied | deferred | rejected", "ref": "rm-N | <learned-preference date> | <one-line reason>"}
   ]}
   ```
   Write one `dispositions` row for every event in `feedback.reasoned`, every week, even when `proposals` is empty: that row is what retires an event from next week's list.
2. `proposals/registry-{YYYY-MM-DD}.yml` — proposed `sources/registry.yml` patches (judgment changes only: demotion/retirement, class/tier fixes, registrations, `→ blocked`, `proxy → direct`):
   ```yaml
   date: {YYYY-MM-DD}
   applied: false
   patches:
     - domain: example.com
       from: probation
       to: established
       evidence: ">=3 anchored citations across >=2 editions, >=14 days, zero source-quality downvotes"
   ```

**`applied: true` stamp protocol:** you write `applied: false` for every proposal EXCEPT the reader-profile.md learned-preference lines you auto-applied under the bounded grant above — those you stamp `"applied": true, "applied_by": "evaluator"` in the same run. For everything else, Rafael's apply step is the ONLY thing that flips it to `applied: true` when a proposal lands. Every run, read every prior `proposals/*` file that still has unstamped items first: a stamped proposal → spot-check the target file actually changed (the loop's verification step — report "applied and verified" or "stamped but not landed"); an unstamped one → list it as **pending, not applied** in the review (do not silently re-propose it as if new). An item carrying `disposition: superseded | rejected` (with `decided_on`) is decided, not pending. When a stamped item has an `applied_note`, it landed in that modified form: verify the target against the note, not the original action. Skip both files (and this check's flags) if you proposed nothing and last week's files don't exist — except that the reader-model file is always written when `feedback.reasoned` is non-empty, for its `dispositions`.

## Cross-week trend (if applicable)

## Open questions for human review

[Each question once, with an id and the date first asked. A question carried from an earlier review is one line: "Q<id> (since {date}, week N): <one-sentence ask>". After 3 unanswered weeks, fold it into a single closing "Standing items:" line listing ids only. Settled, do not re-ask: registry.yml strict-YAML parsing (fixed 2026-11-27: the dumper quotes every hazardous scalar); the sandbox's chmod tests (they skip under root).]
```

# Constraints

- This task is read-only on the scheduler. Never instruct the user to blindly apply patches.
- Don't propose patches that conflict with the sourcing charter.
- If everything is healthy, say so and propose nothing.
- Length: 1500–4000 words, hard cap. Before publishing, run `wc -w _posts/{YYYY-MM-DD}-evaluator.md`; over 4000 → cut, in this order: 🟢 prose, passing spot-check detail, carried-item explanations, the trend narrative.
- PushNotification: call it once, and only if the review is still not on origin when you stop (`Evaluator {YYYY-MM-DD} NOT published: <the FAILED line>`). Never for anything else; the notification stub is the reader channel.
- Discovery recovery (dimension A's computed numbers vs the §3.4 targets) is the primary lens until those targets hold; spend the budget the scripts freed on editorial judgment, not recounting.

# Output: write the review to git + drop a notification stub

Let `{POST_URL} = https://khalic-lab.github.io/claude-routines/{YYYY}/{MM}/{DD}/evaluator/`.

This step runs on BOTH cold and full runs — the user should know the evaluator ran either way.

### 1. Write the review

Use the Write tool to write the review BODY to `_posts/{YYYY-MM-DD}-evaluator.md` — either the
cold-run minimal text from the precheck block, or the full analysis. The front matter is derived
at publish (including the `published: true` that keeps this the one post with its own page) —
don't write it yourself.

### 2. Publish — one command

```bash
python3 tools/publish.py --slug evaluator --date {YYYY-MM-DD} --notify-body "{teaser}"
```

`{teaser}` rules: ≤200 chars, passed as a plain shell argument (no quote-escaping).
- For full runs: headline finding (e.g. "2 streams lag discovery targets — scout vetted 3 candidates" or "All metrics green; registry flow delivering").
- For cold runs: "Pipeline cold — no inputs in 7-day window."

It ends `DONE`, or `FAILED (…)` — which needs a reaction: a commit failure means NOTHING was published (fix the reported error, rerun the same command); a push failure means the review is NOT on origin — if the log says `rebase left unmerged paths`, HEAD is origin's own tip and a bare push publishes nothing: resolve + `git add` each listed path and `git -c core.editor=true rebase --continue` first; otherwise retry `git push origin HEAD:refs/heads/main` before the session ends. Never write the stub or run the git steps by hand.

**Fallback — only if `publish.py` itself crashes before doing anything** (the writers have the same
escape hatch in `DEDUP.md`): note the error in the review, then ship it by hand so the week's review
is never lost. Nothing derived the front matter in this path, so prepend it yourself first:

```
---
layout: single
title: "Weekly Pipeline Review — {YYYY-MM-DD}"
date: {current Europe/Zurich time, ISO 8601 with offset}
categories: [evaluator]
published: true
---
```

```bash
git add _posts/ pending-notifications/ _data/ && git add proposals/ sources/ reader-profile.md 2>/dev/null || true
git -c user.email=routine@khalic-lab -c user.name="News Routine" -c commit.gpgsign=false \
  commit -m "Weekly Pipeline Review — {YYYY-MM-DD}"
git push origin HEAD:refs/heads/main || (git pull --rebase origin main && git push origin HEAD:refs/heads/main)
```

`reader-profile.md` belongs in that `git add` whenever you auto-applied a learned-preference line —
unstaged, the edit dies with the sandbox while your proposal still claims `applied: true`.
