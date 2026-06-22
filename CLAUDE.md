# CLAUDE.md — claude-routines

A Jekyll-published news-brief pipeline. Remote claude.ai routines research and write briefs
into `_posts/`, queue push notifications as `pending-notifications/*.json` (drained by a local
bridge → ntfy), and dedupe stories against a rolling embeddings index under `index/`.

## Docs — read in this order
- **`ARCHITECTURE.md`** — current verified state: components, per-routine **models** + schedules,
  data flow, data model. **Single source of truth for anything that changes.** Check it first.
- **`docs/SPIKE-*.md`** — design proposals and decisions (model tiering, writer token levers).
- **`docs/archive/`** — dated point-in-time analysis (audits, prior-art, reviews); historical, not live.

> Don't duplicate mutable facts (models, schedules) into this file — they live in
> `ARCHITECTURE.md` only. Past drift came from copies going stale.

## Editing a routine (`RemoteTrigger` tool) — read before any update
Use the `RemoteTrigger` tool (OAuth handled in-tool), never curl. The prompt + model live under
`job_config.ccr`.

**The live prompts are mirrored in `routines/` — that directory is the source of truth.** The four
writer prompts (`overview`, `ai-ml`, `cyber-papers`, `weekend`) are **generated**: their
stream-specific bodies live in `routines/src/<slug>.md`, and the five byte-identical shared sections
(Newsroom ethos, Reader profile + source weights, Format, Pedagogical tone, Date discipline) live
once in `routines/_shared/*.md`, pulled in via `<!-- include: _shared/<name>.md -->` placeholders.
Edit the source (or the shared partial — a one-place edit now hits all four writers), run
`python3 routines/assemble.py` to regenerate `routines/<slug>.md`, then mirror that to RemoteTrigger.
`python3 routines/assemble.py check` is the drift guard (run before mirroring): non-zero exit means a
generated prompt no longer matches its sources. Watch and Evaluator are **not** assembled — edit
`routines/watch.md` / `routines/weekly-evaluator.md` directly. `routines/MANIFEST.md` holds each
trigger's id + full `session_context` (and notes the redacted fetch-proxy token to re-substitute).
After ANY RemoteTrigger edit, re-run `assemble.py` (or re-snapshot a non-assembled routine) so the
repo doesn't drift from live.

1. `RemoteTrigger get <id>` first. Copy `events[0].data.message.content`, the **full**
   `session_context`, and `environment_id`.
2. Send the update wrapped as `{"job_config":{"ccr":{environment_id, events, session_context}}}`.
   Event shape: `{"data":{"type":"user","message":{"role":"user","content":"…"}}}`.
   Send the **complete** `session_context` — every key (`allowed_tools`, `model`, `sources`, and
   any extras like `outcomes` / `autofix_on_pr_create`). A model change = swap only
   `session_context.model`, keep everything else verbatim.
3. **Verify with a follow-up `get`.** Traps: unwrapped top-level fields return HTTP 200 but
   silently no-op the prompt; a partial `session_context` clobbers the omitted keys. The re-GET
   proves the value is *stored*, not that the env *executes* it — that only shows at the next
   routine fire.

`RemoteTrigger` is **main-session-only** — sub-agents can't load it (it isn't in their tool grant),
so the GET→edit→update→verify must run in the main session. For a big prompt, don't hand-escape
~10 KB of JSON: pull the exact current content from the session transcript JSONL, edit it
programmatically (string-insert against a unique anchor), send the update, then re-GET and
**byte-diff** the stored content against the intended text — retry if it differs.

## Git conventions
- **Commit or push only when the user asks.** Direct commits to `main` are this repo's
  convention (the routines + bridge reconcile on `main`).
- **No Claude signature** in commit messages.
- Local/automation commits must pass `-c commit.gpgsign=false` (global `commit.gpgsign=true`
  breaks headless commits).

## Stable identifiers
- Repo `github.com/khalic-lab/claude-routines` (private), branch `main`. Site:
  `https://khalic-lab.github.io/claude-routines/`.
- Environment (all routines): `env_018zypSdRSdGdrZ8J5usqCWA`.
- Trigger IDs:
  - Morning Overview — `trig_012KfuF2Fc8KxNRS9KT1iuYb`
  - AI/ML — `trig_01QVL6eSmHTUrmnSLHrpNN9Q`
  - Cyber+Papers (Evening) — `trig_01YLiCr5YJ2XNh2QyPbkyzQP`
  - Weekend Deep Read — `trig_01XKzge4DxP6wTjLwtkoYeqj`
  - Weekly Evaluator — `trig_01F5npsKTQTLKekAZ5BczKtG`
  - Watch (topic poll) — `trig_01FgrFMfsreu597nKUXEEQMt`
  - (Markets — `trig_01GBugAS5qw88yQK3tv8kKWx` — **removed 2026-06-18**; trigger left disabled
    server-side, all market content dropped from the pipeline. Do not revive without re-adding the
    snapshot machinery in `dedup.py`.)
- ntfy delivery is configured in the local bridge `.env` (`/usr/local/src/news-brief-ntfy-bridge/.env`).

## Layout
- Briefs: `_posts/{YYYY-MM-DD}-{slug}.md`; slugs `overview`, `ai-ml`, `cyber-papers`, `weekend`,
  `evaluator`. (Legacy top-level `briefs/` is dead.)
- Notifications: `pending-notifications/{ts}-{slug}.json` → local bridge → ntfy (then deleted).
- Dedup: `tools/dedup/` (see its `DEDUP.md`); embeddings index under `index/`.
- Topic watches: `watches.yml` (user owns entries; the Watch routine writes only `last_fired`).
- Routine prompts: `routines/<slug>.md` (generated, == live) ← `routines/src/<slug>.md` + shared
  `routines/_shared/*.md`, composed by `routines/assemble.py`. Internal design docs live under
  `docs/` (proposals) and `docs/archive/` (dated). Both, plus `routines/`, are excluded from the
  published Jekyll site in `_config.yml`.
