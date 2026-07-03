# Routine manifest — claude.ai RemoteTrigger config

**The live trigger prompts are BOOTSTRAP SHIMS, not full prompts (changed 2026-06-29).** Each
writer/evaluator trigger's `events[0].data.message.content` is a small shim that tells the routine to
`git pull` and read its real prompt from `routines/<file>.md` in the cloned repo, then execute it. The shim
also injects the fetch-proxy bearer, so the repo keeps the `${FETCH_PROXY_TOKEN}` placeholder and the real
token lives only in the trigger shim + the Worker secret.

**Consequence — to change a routine's PROMPT, just edit `routines/src/<slug>.md` (or a shared partial), run
`python3 routines/assemble.py`, and commit + push. NO `RemoteTrigger update` needed.** The routine reads the
latest file at fire time. A `RemoteTrigger update` is only needed to change a trigger's **schedule**
(`cron_expression`), **display name**, **session_context** (tools/model/sources), or the **shim text /
injected token** itself. All routines share `environment_id = env_018zypSdRSdGdrZ8J5usqCWA`.

The `*.md` files beside this manifest ARE the live prompts (read at runtime via the shim); the four writer
prompts are generated from `src/` + `_shared/` (see `assemble.py`). `watch.md` is the exception — Watch
still carries its full prompt inline in the trigger (not shimmed).

| Routine | prompt file | trigger_id | cron (UTC / CEST) | model | shim? |
|---|---|---|---|---|---|
| News | `news.md` | `trig_012KfuF2Fc8KxNRS9KT1iuYb` | `0 10 * * *` (10:00 / 12:00, daily — moved from `0 17` on 2026-07-03) | `claude-opus-4-8` | yes |
| AI/ML | `ai-ml.md` | `trig_01QVL6eSmHTUrmnSLHrpNN9Q` | `0 10 * * 2,5` (10:00 / 12:00, Tue+Fri) | `claude-opus-4-8` | yes |
| Science | `science.md` | `trig_01YLiCr5YJ2XNh2QyPbkyzQP` | `0 15 * * 3` (15:00 / 17:00, Wed) | `claude-opus-4-8` | yes |
| Weekend Deep Read | `weekend.md` | `trig_01XKzge4DxP6wTjLwtkoYeqj` | `30 7 * * 6` (07:30 / 09:30, Sat) | `claude-opus-4-8` | yes |
| Weekly Evaluator | `weekly-evaluator.md` | `trig_01F5npsKTQTLKekAZ5BczKtG` | `30 9 * * 0` (09:30 / 11:30, Sun) | `claude-opus-4-8` | yes |
| Watch | `watch.md` | `trig_01FgrFMfsreu597nKUXEEQMt` | `0 */4 * * *` (every 4h) | `claude-haiku-4-5-20251001` | no (full inline) |

> **Retired 2026-06-29** (trigger IDs REUSED above): `morning-overview.md` → retargeted to **News** (daily,
> CH+world — evening until 2026-07-03, midday since); `cyber-papers.md` → retargeted to **Science** (weekly Wed, non-AI science). Security
> dropped pipeline-wide; the old consolidated evening email and the AI/ML/science split are gone. The
> Markets trigger (`trig_01GBugAS5qw88yQK3tv8kKWx`) remains disabled.

## Bootstrap shim (the live trigger content, verbatim shape)

Each shimmed trigger's `content` is (Name/file vary per routine):

```
You are the {Name} routine for the claude-routines news pipeline. Your complete, authoritative
instructions live in the repo, not in this message.

1. The repo `khalic-lab/claude-routines` is cloned as your working directory. Run
   `git pull --ff-only origin main` to get the latest.
2. Read `routines/{file}.md` with the Read tool. That file is your FULL prompt for this run -- execute it
   exactly, top to bottom, as if its contents were this message. Do not summarize or describe it; follow it.
3. Wherever that file shows the literal placeholder ${FETCH_PROXY_TOKEN}, use this bearer token instead:
   <the fetch-proxy Worker bearer — in the Worker secret + tools/fetch-proxy/.dev.vars>

If `git pull` fails or `routines/{file}.md` is missing or unreadable, do NOT fabricate a brief: write a
short post (and a notification stub) noting the routine prompt was unreadable, then stop.
```

The **Weekly Evaluator** shim omits step 3's token line (it makes no fetch-proxy calls) and says "review"
rather than "brief".

## Full `session_context` per routine (verbatim — required to reconstruct a schedule/shim/session update)

### news (trigger `trig_012KfuF2Fc8KxNRS9KT1iuYb`)
```json
{
  "allowed_tools": ["WebFetch", "WebSearch", "Read", "Write", "Bash", "Edit", "Glob", "Grep"],
  "model": "claude-opus-4-8",
  "sources": [{"git_repository": {"url": "https://github.com/khalic-lab/claude-routines"}}]
}
```

### ai-ml (trigger `trig_01QVL6eSmHTUrmnSLHrpNN9Q`)
```json
{
  "allowed_tools": ["WebFetch", "WebSearch", "Read", "Write", "Bash", "Edit", "Glob", "Grep"],
  "model": "claude-opus-4-8",
  "sources": [{"git_repository": {"url": "https://github.com/khalic-lab/claude-routines"}}]
}
```

### science (trigger `trig_01YLiCr5YJ2XNh2QyPbkyzQP`)
```json
{
  "allowed_tools": ["WebFetch", "WebSearch", "Read", "Write", "Bash", "Edit", "Glob", "Grep"],
  "model": "claude-opus-4-8",
  "sources": [{"git_repository": {"url": "https://github.com/khalic-lab/claude-routines"}}]
}
```

### weekend (trigger `trig_01XKzge4DxP6wTjLwtkoYeqj`)
```json
{
  "allowed_tools": ["WebFetch", "WebSearch", "Read", "Write", "Bash", "Edit", "Glob", "Grep"],
  "model": "claude-opus-4-8",
  "sources": [{"git_repository": {"url": "https://github.com/khalic-lab/claude-routines"}}]
}
```

### weekly-evaluator (trigger `trig_01F5npsKTQTLKekAZ5BczKtG`)
```json
{
  "allowed_tools": ["WebFetch", "WebSearch", "Read", "Write", "Bash", "Edit", "Glob", "Grep"],
  "autofix_on_pr_create": false,
  "model": "claude-opus-4-8",
  "outcomes": [{"git_repository": {"git_info": {"branches": ["claude/admiring-edison"], "repo": "khalic-lab/claude-routines"}}}],
  "sources": [{"git_repository": {"url": "https://github.com/khalic-lab/claude-routines"}}]
}
```

### watch (trigger `trig_01FgrFMfsreu597nKUXEEQMt`)
```json
{
  "allowed_tools": ["WebFetch", "WebSearch", "Read", "Write", "Bash", "Edit", "Glob", "Grep"],
  "autofix_on_pr_create": false,
  "model": "claude-haiku-4-5-20251001",
  "outcomes": [{"git_repository": {"git_info": {"branches": ["claude/serene-mayer"], "repo": "khalic-lab/claude-routines"}}}],
  "sources": [{"git_repository": {"url": "https://github.com/khalic-lab/claude-routines"}}]
}
```
