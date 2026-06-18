# CLAUDE.md — claude-routines

A Jekyll-published news-brief pipeline. Remote claude.ai routines research and write briefs
into `_posts/`, queue push notifications as `pending-notifications/*.json` (drained by a local
bridge → ntfy), and dedupe stories against a rolling embeddings index under `index/`.

## Docs — read in this order
- **`ARCHITECTURE.md`** — current verified state: components, per-routine **models** + schedules,
  data flow, data model. **Single source of truth for anything that changes.** Check it first.
- **`SPIKE-*.md`** — proposals and decisions (model tiering, writer token levers).

> Don't duplicate mutable facts (models, schedules) into this file — they live in
> `ARCHITECTURE.md` only. Past drift came from copies going stale.

## Editing a routine (`RemoteTrigger` tool) — read before any update
Use the `RemoteTrigger` tool (OAuth handled in-tool), never curl. The prompt + model live under
`job_config.ccr`.

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

For big prompts, delegate the GET→edit→update→verify to a sub-agent (one per trigger, fresh GET,
no stale temp files) rather than hand-escaping ~10 KB of JSON.

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
