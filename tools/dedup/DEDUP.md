# Story deduplication procedure (for writer routines)

Each writer routine follows this on every run so a story isn't re-run for days (the
"same story for a month" problem). It is **best-effort**: if any step errors, compose the
brief normally and note "dedup unavailable" in the Gaps footer — never abort the brief.

The routine that invokes this passes its **slug** (one of `news`, `ai-ml`,
`science`, `weekend`) and today's date `{YYYY-MM-DD}` (Europe/Zurich).

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

`/tmp/verdicts.json` has one result per candidate: `verdict` (NEW | ONGOING | REPEAT), `score`,
an optional `match_reason` (`exact-url` | `exact-arxiv` | `distinct-paper`),
and for non-NEW a `matched` object with `id`, `date`, `headline`, `summary`, `url`, `thread_id`,
`first_seen_date`, `event_date`, and — when the match is a *different artifact* —
`continuation: false` with `first_seen_date: null`. (`matched.summary`/`matched.url` are the prior
coverage's own summary and source — lean on them when framing an ONGOING update.)

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
  `security`, `tech`, `world`), `importance` is 1–3 (**3** lead, **2** standard, **1** brief). Score
  on real significance to the reader (see the tagging rubric in your prompt). If you omit them,
  `record` stores them empty and `build_stories_feed.py` derives a fallback from position + keywords.
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

```bash
EMBED_WORKER_URL=https://embed-proxy.khalic-lab.workers.dev \
EMBED_TOKEN=b4bd10fc46e70315205b5aa4a4352d6d79f750d13cc4ef960928f8e6da5aae8a \
python3 tools/dedup/dedup.py record --stories /tmp/final.json --date {YYYY-MM-DD} --slug {SLUG} \
  || echo "dedup record failed (non-fatal)"
```

This writes `index/stories/{YYYY-MM-DD}-{SLUG}.jsonl` and prunes index files older than 40 days.

**`record` also dual-writes the story ledger** (`index/ledger/{YYYY-MM-DD}.jsonl`, SPIKE
§3.1) — one `ev:"seen"` and one `ev:"publish"` event per kept story, each keyed on the story's
own `st-{sha1(norm_url)[:12]}` id, with the classic `{date}-{slug}-…` id carried along as
`legacy_ids` so old feedback/feed records still join. **No writer action needed** — this happens
automatically inside the same `record` call above; the legacy `index/stories/` file it writes is
unaffected (byte-identical). It's the join key Step C.25 anchors the brief to.

## Step C.25 — anchor the brief + source-lint (report-only, no network)

Right after `record`, stamp the brief file itself with the same `st-…` ids the ledger just used, so
a reader's feedback click or a homefeed card can target one story instead of the whole brief:

```bash
python3 tools/store/anchor.py --index index/stories/{YYYY-MM-DD}-{SLUG}.jsonl _posts/{YYYY-MM-DD}-{SLUG}.md || echo "anchor failed (non-fatal)"
python3 tools/sources/lint.py _posts/{YYYY-MM-DD}-{SLUG}.md || echo "sources lint failed (non-fatal)"
```

`anchor.py` inserts `<a id="st-…" class="st-a"></a>` right after each story bullet's dash (or a
kramdown `{#st-…}` after a `### ` heading). `--index` points it at the edition's own
`index/stories/{YYYY-MM-DD}-{SLUG}.jsonl` (the file Step C's `record` just wrote): for each
bullet/heading block it matches ANY link in the block against that file's recorded urls and keys
the id on the MATCHED record's own url — so the anchor lines up with the same url the ledger's
`publish` events are keyed on, even when a bullet's first link is a background/corroborating
citation rather than the primary source. It falls back to the block's first URL only when nothing
in the block matches a recorded story (or when `--index` is omitted). Idempotent — safe to re-run
on an already-anchored post.

`sources/lint.py` is **report-only** (SPIKE §3.4/§4): caps, discovery quota, and `[new source]`-tag
integrity are checked deterministically so no model has to self-certify them. Like every other step
here, a violation goes in the brief's **Gaps** line — it never aborts the brief.

**Discovery footer contract:** per the writer prompt's own Coverage footer template, the brief's
`## Coverage footer` block ends with exactly one of these as its LAST line (after Sources/Gaps —
not, as this doc previously said, the last line *before* the `## Coverage footer` heading):

```
- Discovery: met (<what you found that wasn't already in the registry>)
- Discovery: waived — <concrete reason, e.g. "quiet news day, no off-list primaries found">
```

`lint.py` checks for exactly one such line. The waiver is free but counted (it feeds SPIKE §3.4's
waiver-rate target) — use it honestly rather than claiming `met` with nothing behind it.

## Step C.5 — lint the brief for date slips (optional, no network)

A deterministic backstop with two checks:
- **WEEKDAY (hard, non-zero exit):** a weekday named next to a date it doesn't match (e.g. "Wednesday
  11 June" — June 11 is a Thursday). Adjacent form only; a weekday and date split across distant
  sentences need the injected as-of dated-weekday block.
- **SCHEDULE (advisory):** relative framing of a dated event with no absolute date nearby ("votes
  **this weekend**", "vote **tomorrow**"). This is what misdated the 14-June vote to "Sunday 7 June".
  The lint can't tell you the right date — it refuses the bare framing so you **state the absolute
  date** (and read it from `matched.event_date`, never re-derive "which Sunday").

```bash
python3 tools/dedup/dedup.py lint --brief _posts/{YYYY-MM-DD}-{SLUG}.md || echo "fix the date flags above"
```

## Step D — refresh the homepage feed (AFTER record, BEFORE commit)

The front page renders individual stories as a masonry grid from a flattened feed. Regenerate it so
today's brief shows up:

```bash
python3 tools/build_stories_feed.py || echo "feed build failed (non-fatal)"
```

No network — it re-reads the recent `_posts/*.md` briefs (for each story's real prose) plus
`index/stories/*.jsonl` (for writer-supplied `topics`/`importance`, joined by canonical URL) and
writes `_data/homefeed.json` (the four live streams, most-recent stories, per-edition-capped for
the front page). It prints a join-rate line — `0/N carry writer-supplied topics/importance` is
expected only until recorded stories start carrying the Step C fields.

Every writer slug (`news`, `ai-ml`, `science`, `weekend`) runs this on every fire; the evaluator
does not (it never touches this procedure).

## Step E — commit everything

Your commit step must stage the brief, the index (legacy files **and** the ledger Step C just
dual-wrote to), and the regenerated feed:

```bash
git add _posts/ pending-notifications/ index/ index/ledger/ _data/
git add sources/ 2>/dev/null || true
```

`index/ledger/` is named explicitly even though `index/` already covers it — it's the append-only
ledger this step's dual-write and Step C.25's anchors key on, worth seeing called out in a `git
status`. The second line stages `sources/` (the credibility-registry + its append-only
`candidates.jsonl`/`last-cited.jsonl`) *only once that directory exists* — it lands with this
migration's registry step; kept on its own line and swallowed on failure so today's commit, before
that step ships, isn't broken by a `git add` on a path that doesn't exist yet.

If the later `git push` retry hits a rebase conflict on `_data/homefeed.json` (two editions firing
at the same minute both rewrite the whole file), the resolution is always: re-run
`python3 tools/build_stories_feed.py` on the merged tree, `git add _data/homefeed.json`, continue.
Your routine's publish step spells out the exact sequence.
