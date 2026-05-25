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
  {"id":"1","headline":"<the bold headline you plan to use>","summary":"<one neutral sentence>"}
]}
```

Run the check:

```bash
EMBED_WORKER_URL=https://embed-proxy.khalic-lab.workers.dev \
EMBED_TOKEN=b4bd10fc46e70315205b5aa4a4352d6d79f750d13cc4ef960928f8e6da5aae8a \
python3 tools/dedup/dedup.py check --candidates /tmp/cand.json --since 30 \
  > /tmp/verdicts.json 2>/tmp/dedup.err && cat /tmp/verdicts.json \
  || echo "DEDUP UNAVAILABLE: $(cat /tmp/dedup.err)"
```

`/tmp/verdicts.json` has one result per candidate: `verdict` (NEW | ONGOING | REPEAT), `score`,
and for non-NEW a `matched` object with `date`, `headline`, `thread_id`, `first_seen_date`.

## Step B — apply verdicts while composing

- **REPEAT** → DROP the story. Already covered with no material change.
- **ONGOING** → include ONLY if there is genuine *new development* since
  `matched.first_seen_date`. Frame it as an update and append `[ongoing since {first_seen_date}]`
  to the bullet. If there is no real new information, drop it.
- **NEW** → cover normally.
- **check unavailable** → compose normally; add "dedup unavailable" to the Gaps footer.

## Step C — record what you published (AFTER writing the brief file)

So future briefs dedup against today. Build `/tmp/final.json` from the stories you actually
kept (carry `thread_id`/`first_seen_date` through from the matched ONGOING result; omit both
for NEW stories):

```json
{"stories":[
  {"headline":"...","summary":"<one sentence>","url":"<primary source url>",
   "tier":"T1","tags":["..."],
   "thread_id":"<matched.thread_id, only if ONGOING>",
   "first_seen_date":"<matched.first_seen_date, only if ONGOING>"}
]}
```

```bash
EMBED_WORKER_URL=https://embed-proxy.khalic-lab.workers.dev \
EMBED_TOKEN=b4bd10fc46e70315205b5aa4a4352d6d79f750d13cc4ef960928f8e6da5aae8a \
python3 tools/dedup/dedup.py record --stories /tmp/final.json --date {YYYY-MM-DD} --slug {SLUG} \
  || echo "dedup record failed (non-fatal)"
```

This writes `index/stories/{YYYY-MM-DD}-{SLUG}.jsonl` and prunes index files older than 40 days.

## Step D — commit the index

Your existing commit step must also stage the index, e.g.:

```bash
git add _posts/ pending-notifications/ index/
```
