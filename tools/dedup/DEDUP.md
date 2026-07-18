# Story deduplication procedure (for writer routines)

Each writer routine follows this on every run so a story isn't re-run for days (the
"same story for a month" problem). It is **best-effort**: if any step errors, compose the
brief normally and note "dedup unavailable" in the Gaps footer — never abort the brief.

The routine that invokes this passes its **slug** (one of `news`, `ai-ml`,
`science`, `weekend`, `sports`) and today's date `{YYYY-MM-DD}` (Europe/Zurich).

Fixed endpoint (this is a low-value token — gates only Workers-AI embedding spend on our own
account; the repo is private and this file is excluded from the published site):

```
EMBED_WORKER_URL=https://embed-proxy.khalic-lab.workers.dev
EMBED_TOKEN=b4bd10fc46e70315205b5aa4a4352d6d79f750d13cc4ef960928f8e6da5aae8a
```

## Step A — check candidates (AFTER research, BEFORE composing)

Once you have the stories you're considering, write them to `/tmp/cand.json` (one entry per
candidate, across ALL sections of the brief):

```json
{"candidates":[
  {"id":"1","headline":"<the bold headline you plan to use>","summary":"<one neutral sentence>",
   "url":"<primary source URL — include it whenever you have one>"}
]}
```

**Always include `url`** when you have a primary source. The check uses an exact canonical-URL /
arXiv-id match as a deterministic REPEAT signal (zero judgment): if a candidate cites the same
paper or page already covered, it is dropped regardless of how the headline is worded.

Run the check:

```bash
EMBED_WORKER_URL=https://embed-proxy.khalic-lab.workers.dev \
EMBED_TOKEN=b4bd10fc46e70315205b5aa4a4352d6d79f750d13cc4ef960928f8e6da5aae8a \
python3 tools/dedup/dedup.py check --candidates /tmp/cand.json --since 30 \
  > /tmp/verdicts.json 2>/tmp/dedup.err && cat /tmp/verdicts.json \
  || echo "DEDUP UNAVAILABLE: $(cat /tmp/dedup.err)"
```

**Weekend edition only:** if your slug is `weekend`, append `--only-slug weekend` to the check
command above. Weekend revisits the week's most important stories *in depth*, so it must dedup
**only against prior `weekend` editions** — a story a daily edition (`news`/`ai-ml`/`science`)
already covered earlier this week is **not** a repeat for Weekend, it's exactly what Weekend
exists to go deeper on. Every other slug omits the flag (cross-edition dedup). With the flag, any
REPEAT verdict is by construction a prior-Weekend repeat, so Step B's "REPEAT → ALWAYS DROP" still
applies unchanged — no special-casing of the verdicts is needed.

**Then snapshot the verdicts (added 2026-07-11, feeds the homepage desk-stats panel):**

```bash
python3 tools/store/verdicts.py --candidates /tmp/cand.json --verdicts /tmp/verdicts.json \
  --date {YYYY-MM-DD} --slug {SLUG} || echo "verdict snapshot failed (non-fatal)"
```

This writes `index/verdicts/{YYYY-MM-DD}-{SLUG}.json` (idempotent — re-runs overwrite). Step E's
`git add index/` already stages it; skip silently if the check itself was unavailable.

`/tmp/verdicts.json` has one result per candidate: `verdict` (NEW | ONGOING | REPEAT), `score`,
an optional `match_reason` (`exact-url` | `exact-arxiv` | `distinct-paper`),
and for non-NEW a `matched` object with `id`, `date`, `headline`, `summary`, `url`, `thread_id`,
`first_seen_date`, `event_date`, and — when the match is a *different artifact* —
`continuation: false` with `first_seen_date: null`. (`matched.summary`/`matched.url` are the prior
coverage's own summary and source — lean on them when framing an ONGOING update.)

**ONGOING verdicts may also carry `thread` (added 2026-07-18): the story's ACTUAL coverage arc**
— up to the last 8 prior entries `{date, headline, event_date?}`, oldest first, fetched from the
analytical plane (embed-proxy `/plane/thread`). It is best-effort: absent when the plane is
unreachable, and its absence changes nothing else.

## Step B — apply verdicts while composing

- **REPEAT** → ALWAYS DROP the story. Already covered, no exceptions. (`match_reason` explains why:
  `exact-url`/`exact-arxiv` = same primary source already covered; absent = near-verbatim rerun by
  similarity.)
- **ONGOING** → **DEFAULTS TO DROP.** Include ONLY when there is a NAMED, dated, concrete new
  fact since `matched.first_seen_date` — a specific number, a ruling, a release, a benchmark
  result. A fresh angle, a new framing, or a re-summary of the same facts is explicitly **NOT**
  new development and must be dropped. When you do include it, frame it as an update, lead with
  the new fact, and append `[ongoing since {event_date or first_seen_date}]` (prefer
  `matched.event_date` when present — when the thing happened — else `first_seen_date`).
  **When the verdict carries `thread` (the arc's real timeline), ground every sequence claim in
  it**: counts ("seventh consecutive night", "third strike wave") must match the timeline's
  entries, the arc's start date comes from its first row — never re-derive either from memory —
  and one clause of arc context ("after three weeks of tit-for-tat strikes since {first date}")
  beats re-explaining the background the earlier entries already covered.
- **`match_reason: distinct-paper`** (or `matched.continuation: false`, `first_seen_date: null`) →
  the match is a DIFFERENT artifact that is merely on the same topic. **Treat as NEW**, not ongoing.
  **Do NOT emit any `[ongoing since …]` tag** (there is no valid since-date — never print
  "[ongoing since None]"). If you want to note the lineage, do it in **prose only** ("continues the
  SAE line from …, a *distinct* paper"). This is the SASA/SoftSAE lesson.
- **`[ongoing since]` means the SAME artifact developing — not the same topic.** Two different
  papers, two different CVEs, or two different filings are distinct threads even when closely
  related. Tag continuity only when the new item shares the prior's **arXiv id / canonical URL**;
  otherwise it is NEW and any "still developing" framing lives in prose.
- **Scheduled events (votes, IPO pricings, conferences, deadlines): state the ABSOLUTE date, and
  read it from `matched.event_date` — never re-derive it.** A 2026-06-06 brief put the SVP "No
  10-million Switzerland" federal vote on "**this weekend**" / "**Sunday 7 June**" when the vote is
  **14 June** — it re-guessed "which Sunday" instead of reading the date the pipeline had already
  established. `record` carries a scheduled (future) `event_date` forward along the thread, so once
  it's set, `matched.event_date` gives you the real date every run. Never write "this weekend" /
  "tomorrow" for a dated event without the absolute date next to it (the `lint` SCHEDULE check flags
  this). When you know a scheduled event's date, put it in the story's `event_date` (Step C).
- **NEW** → cover normally.
- **check unavailable** → compose normally; add "dedup unavailable" to the Gaps footer.

## Step C — record what you published (AFTER writing the brief file)

So future briefs dedup against today. Build `/tmp/final.json` from the stories you actually
kept. **`thread_id`/`first_seen_date` are now auto-assigned by `record`** (it re-embeds each
story and inherits the thread from its best recent match), so carrying them through by hand is a
safety net, not a requirement — supply them if you already have them, otherwise omit both and
`record` will link threads for you:

```json
{"stories":[
  {"headline":"...","summary":"<one sentence>","url":"<primary source url>",
   "tier":"T1","tags":["..."],
   "topics":["geopolitics"],"importance":3,
   "entities":["Iran","Strait of Hormuz"],
   "affiliations":["MIT","CERN"],
   "display_body":"<the story's explanatory paragraph EXACTLY as published in the brief>",
   "why":"<the story's 'Why it matters' text as published, if it has one; else omit>",
   "event_date":"<YYYY-MM-DD when the event actually happened, if known; else omit>",
   "thread_id":"<matched.thread_id — ONLY for a TRUE same-artifact continuation>",
   "first_seen_date":"<matched.first_seen_date — ONLY with a valid thread_id>"}
]}
```

- **`event_date`** is the date the thing *happened* (a paper's submission, a filing, an incident) —
  distinct from today's brief date. Supply it at day precision when the source gives it; `record`
  otherwise derives `YYYY-MM` from an arXiv id, else leaves it null. It is what `[ongoing since]`
  should anchor to.
- **`topics` / `importance`** feed the homepage grid: `topics` is a 1–2 item list from the controlled
  beat set (`switzerland`, `geopolitics`, `politics`, `economy`, `ai-ml`, `science`, `health`,
  `security`, `tech`, `sports`, `world`), `importance` is 1–3 (**3** lead, **2** standard, **1** brief). Score
  on real significance to the reader (see the tagging rubric in your prompt). If you omit them,
  `record` stores them empty and `build_stories_feed.py` derives a fallback from position + keywords.
- **`entities`** (added 2026-07-18; feeds the analytical plane's story graph): 2–5 proper-noun
  actors/places/artifacts the story is ABOUT — countries, organizations, named people, named
  systems/products, treaties, rulings (e.g. `["Iran","Strait of Hormuz"]`,
  `["UEFA","FC Basel"]`, `["CERN","LHC"]`). Canonical short names, consistent across editions
  (write "Iran", not "the Islamic Republic of Iran"). Omit the key when nothing qualifies —
  never pad with the beat name or generic words ("war", "AI").
- **`affiliations`** (papers only; SPIKE-2026-07-10): the institutions from the story's byline
  parenthetical, verbatim — same canonical short names, same order, ≤3 (`AUTHORS (Inst1; Inst2)`
  → `["Inst1","Inst2"]`). **Omit the key** for non-papers and for `(affiliation not listed)`.
  It feeds the homepage card's institution-first source label and `sources/institutions.yml`;
  the Affiliations block in your prompt has the retrieval chain and format law.
- **`display_body` / `why`** are the story's PUBLISHED prose, copied verbatim from the brief you just
  wrote (the explanatory paragraph, and the "Why it matters" line if the story has one) — plain text,
  no markdown links or bold. The homepage cards render these directly; when present they beat the
  feed builder's markdown re-parse, which is a fallback for older records only. Copy, don't rewrite —
  the reader must see on the front page exactly what the brief says.
- **Never hand-set `thread_id` to place a DISTINCT artifact into a topic thread.** A different paper
  / CVE / filing is its own thread even on the same subject — that exact mistake produced the wrong
  "[ongoing since 2026-05-14]" on the June SASA paper. `record` now **validates** writer-supplied
  threads and will reject a thread whose genesis is a different arXiv paper, but don't rely on it:
  omit `thread_id` unless the new item shares the prior's arXiv id / canonical URL.

**You do NOT invoke `record` directly — the publish orchestrator runs it for you** (with the
embed env injected). Build `/tmp/final.json`, then run the single publish command from your
prompt's Output section:

```bash
python3 tools/publish.py --slug {SLUG} --date {YYYY-MM-DD} --final /tmp/final.json \
  --notify-title "..." --notify-body "..." --notify-tags ...
```

## Steps C→E — the publish tail (ONE command since 2026-07-18: `tools/publish.py`)

`publish.py` executes, in order, everything this document previously spelled out as Steps
C.25/C.5/D/E — each PREPROCESSING step **non-fatal** (a crash degrades, it never costs the
edition), each printing an `[publish] <step>: OK/FAIL` line as it runs. The git tail (step 10)
is the exception since 2026-07-18: a failed commit or push ends the run with a `FAILED (...)`
line and exit 1, never a false `DONE` — see step 10 for how to react:

1. **`dedup.py record`** — writes `index/stories/{date}-{slug}.jsonl`, prunes >40-day files, and
   dual-writes the story ledger (`ev:"seen"` + `ev:"publish"` per kept story, keyed on
   `st-{sha1(norm_url)[:12]}` ids, classic ids carried as `legacy_ids`; the legacy per-edition
   file stays byte-identical).
2. **`store/anchor.py --index`** — stamps the brief's bullets/headings with the same `st-…` ids
   the ledger just used (link-matched against the recorded urls; idempotent on an
   already-anchored post).
3. **`footer.py`** — computes the Coverage-footer telemetry: registry tier split,
   direct-vs-snippet counts (from your `[via snippet]` tags), exact word count, token estimate,
   and `Feeds hit` from `/tmp/fetch.log`. Writer-authored comment lines (Languages,
   stream-specific items) are preserved; the visible Gaps/Discovery lines stay yours entirely.
4. **`sources/lint.py`** — report-only recheck of `[new source]` tag integrity, per-domain caps,
   and the **Discovery footer contract**: the footer ends with exactly one of
   `- Discovery: met (<what you found that wasn't already in the registry>)` or
   `- Discovery: waived — <concrete reason>`. The waiver is free but counted — use it honestly.
   Violations go in the brief's Gaps line, never abort the brief. Tagged novel domains are
   appended to `sources/candidates.jsonl`.
5. **`sources/registry.py sync`** — folds candidates into `sources/registry.yml` (the step whose
   omission starved news/science discovery from 2026-07-07 to 2026-07-10). When there is nothing
   to fold it leaves `registry.yml` byte-untouched (an unchanged file can't merge-conflict with a
   sibling edition) and just purges dead buffer entries.
6. **`sources/institutions.py sync`** — folds the `affiliations` you recorded into
   `sources/institutions.yml` (per-edition bookkeeping; re-running is a no-op).
7. **`dedup.py lint`** — the date-slip backstop: **WEEKDAY** (hard — a weekday named next to a
   date it doesn't match) and **SCHEDULE** (advisory — relative framing of a dated event with no
   absolute date nearby; state the absolute date and read it from `matched.event_date`, never
   re-derive "which Sunday").
8. **`build_stories_feed.py`** — regenerates `_data/homefeed.json` (front-page story grid) plus
   the `_data/stats.json` desk-stats piggyback — and **`sources/health.py`**
   (`_data/source-health.json`).
9. **Notification stub** — `pending-notifications/{ts}-{slug}.json` written with real JSON
   encoding and a computed UTC timestamp (your `--notify-body` teaser needs no quote-escaping).
   A bare front-matter `date:` in the post is also normalized to a full ISO timestamp here.
10. **Commit + push** — stages `_posts/ pending-notifications/ index/ _data/ sources/`, commits
    with the routine identity, and pushes with the homefeed rebase-conflict retry built in
    (rebase → regenerate the feed from the merged tree → continue → push; two editions firing
    the same minute both rewrite the whole homefeed, and this is always the resolution).
    **Outcomes (honest since 2026-07-18 — a failed commit used to print DONE):**
    - `DONE` + exit 0 — published; nothing more to do.
    - `FAILED (git commit errored ...)` + exit 1 — NOTHING was published. Fix the reported
      error and rerun the same publish command, or ship via the manual fallback below.
    - `FAILED (push ...)` + exit 1 — committed locally, not on origin; the failure note is
      already amended into the commit. Retry `git push origin main` before the session ends
      (an unpushed sandbox commit is lost when the session dies).

Every writer slug (`news`, `ai-ml`, `science`, `weekend`, `sports`) publishes this way on every
fire; the evaluator does not (it never touches this procedure).

**Fallback (if `publish.py` itself crashes before running its steps, or a commit failure can't
be fixed):** note "publish orchestrator failed: <error>" in Gaps, then ship the brief by hand so
the edition is never lost:

```bash
git add _posts/ pending-notifications/ index/ _data/ && git add sources/ 2>/dev/null || true
git -c user.email=routine@khalic-lab -c user.name="News Routine" commit -m "{Title} — {YYYY-MM-DD}"
git push origin main || (git pull --rebase origin main && git push origin main)
```
