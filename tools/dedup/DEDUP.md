# Story deduplication procedure (for writer routines)

Each writer routine follows this on every run so a story isn't re-run for days (the
"same story for a month" problem). It is **best-effort**: if any step errors, compose the
brief normally and note "dedup unavailable" in the Gaps footer — never abort the brief.

The routine that invokes this passes its **slug** (one of `overview`, `markets`, `ai-ml`,
`cyber-papers`, `weekend`) and today's date `{YYYY-MM-DD}` (Europe/Zurich).

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

`/tmp/verdicts.json` has one result per candidate: `verdict` (NEW | ONGOING | REPEAT), `score`,
an optional `match_reason` (`exact-url` | `exact-arxiv` | `snapshot-collapse` | `distinct-paper`),
and for non-NEW a `matched` object with `date`, `headline`, `thread_id`, `first_seen_date`,
`event_date`, and — when the match is a *different artifact* — `continuation: false` with
`first_seen_date: null`.

## Step B — apply verdicts while composing

- **REPEAT** → ALWAYS DROP the story. Already covered, no exceptions. (`match_reason` explains why:
  `exact-url`/`exact-arxiv` = same primary source already covered; `snapshot-collapse` = a
  recurring market snapshot — see below; absent = near-verbatim rerun by similarity.)
- **`match_reason: snapshot-collapse`** → this was a recurring FX/index/session snapshot. The daily
  market glance belongs ONLY in the dedicated pre-open snapshot section, never as a standalone
  repeated story — so dropping it here is correct even though "the number changed."
- **ONGOING** → **DEFAULTS TO DROP.** Include ONLY when there is a NAMED, dated, concrete new
  fact since `matched.first_seen_date` — a specific number, a ruling, a release, a benchmark
  result. A fresh angle, a new framing, or a re-summary of the same facts is explicitly **NOT**
  new development and must be dropped. When you do include it, frame it as an update, lead with
  the new fact, and append `[ongoing since {event_date or first_seen_date}]` (prefer
  `matched.event_date` when present — when the thing happened — else `first_seen_date`).
- **`match_reason: distinct-paper`** (or `matched.continuation: false`, `first_seen_date: null`) →
  the match is a DIFFERENT artifact that is merely on the same topic. **Treat as NEW**, not ongoing.
  **Do NOT emit any `[ongoing since …]` tag** (there is no valid since-date — never print
  "[ongoing since None]"). If you want to note the lineage, do it in **prose only** ("continues the
  SAE line from …, a *distinct* paper"). This is the SASA/SoftSAE lesson.
- **`[ongoing since]` means the SAME artifact developing — not the same topic.** Two different
  papers, two different CVEs, or two different filings are distinct threads even when closely
  related. Tag continuity only when the new item shares the prior's **arXiv id / canonical URL**;
  otherwise it is NEW and any "still developing" framing lives in prose.
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
   "event_date":"<YYYY-MM-DD when the event actually happened, if known; else omit>",
   "thread_id":"<matched.thread_id — ONLY for a TRUE same-artifact continuation>",
   "first_seen_date":"<matched.first_seen_date — ONLY with a valid thread_id>"}
]}
```

- **`event_date`** is the date the thing *happened* (a paper's submission, a filing, an incident) —
  distinct from today's brief date. Supply it at day precision when the source gives it; `record`
  otherwise derives `YYYY-MM` from an arXiv id, else leaves it null. It is what `[ongoing since]`
  should anchor to.
- **Never hand-set `thread_id` to place a DISTINCT artifact into a topic thread.** A different paper
  / CVE / filing is its own thread even on the same subject — that exact mistake produced the wrong
  "[ongoing since 2026-05-14]" on the June SASA paper. `record` now **validates** writer-supplied
  threads and will reject a thread whose genesis is a different arXiv paper, but don't rely on it:
  omit `thread_id` unless the new item shares the prior's arXiv id / canonical URL.

```bash
EMBED_WORKER_URL=https://embed-proxy.khalic-lab.workers.dev \
EMBED_TOKEN=b4bd10fc46e70315205b5aa4a4352d6d79f750d13cc4ef960928f8e6da5aae8a \
python3 tools/dedup/dedup.py record --stories /tmp/final.json --date {YYYY-MM-DD} --slug {SLUG} \
  || echo "dedup record failed (non-fatal)"
```

This writes `index/stories/{YYYY-MM-DD}-{SLUG}.jsonl` and prunes index files older than 40 days.

## Step C.5 — lint the brief for date slips (optional, no network)

A deterministic backstop that flags a weekday named next to a date it doesn't match (e.g. "Wednesday
11 June" when June 11 is a Thursday). It only catches the **adjacent** form — a weekday and date in
the same clause; it cannot catch a weekday and date split across distant sentences (use the injected
as-of dated-weekday block for those). Run it on the brief you just wrote and fix any flag:

```bash
python3 tools/dedup/dedup.py lint --brief _posts/{YYYY-MM-DD}-{SLUG}.md || echo "fix the date flags above"
```

## Step D — commit the index

Your existing commit step must also stage the index, e.g.:

```bash
git add _posts/ pending-notifications/ index/
```
