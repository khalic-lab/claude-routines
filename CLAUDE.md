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

## Editing a routine — read before any change (BOOTSTRAP-SHIM model, since 2026-06-29)
**The live triggers no longer hold the full prompt.** Each writer/evaluator trigger's
`events[0].data.message.content` is a small **bootstrap shim**: it tells the routine to `git pull` and read
its real prompt from `routines/<file>.md` in the cloned repo, then execute it, injecting the fetch-proxy
bearer wherever the file shows `${FETCH_PROXY_TOKEN}` (so the repo keeps the placeholder; the real token
lives only in the shim + the Worker secret). `routines/MANIFEST.md` documents the shim shape + each
trigger's id, cron, and full `session_context`.

**To change a routine's PROMPT (the common case): edit the repo, do NOT touch RemoteTrigger.**
- Writer prompts (`news`, `ai-ml`, `science`, `weekend`) are **generated**: edit the stream body in
  `routines/src/<slug>.md`, or a shared partial in `routines/_shared/*.md` (one edit hits all four), then
  `python3 routines/assemble.py` to regenerate `routines/<slug>.md`. `python3 routines/assemble.py check`
  is the drift guard (non-zero exit = a generated file no longer matches its sources).
- Evaluator (`routines/weekly-evaluator.md`) is **not** assembled — edit it directly. Watch is the only
  routine still NOT shimmed (full prompt inline in the trigger) — to change it you must use RemoteTrigger
  (below) and edit `routines/watch.md` to match.
- Then **commit + push** (the shim `git pull`s at fire time and reads the new file). That's the whole edit
  — no mirroring, no byte-diff, no token substitution.

**Use `RemoteTrigger update` ONLY to change a trigger's schedule (`cron_expression`), display `name`,
`session_context` (tools/model/sources), or the shim/injected-token itself.** Protocol:
1. `RemoteTrigger get <id>` first; copy the **full** `session_context` + `environment_id` (+ shim content if
   not changing it).
2. Update body: top-level `cron_expression` / `name` as needed, plus
   `{"job_config":{"ccr":{environment_id, events, session_context}}}`. Event shape:
   `{"data":{"type":"user","message":{"role":"user","content":"…"}}}`. Send the **complete**
   `session_context` — a partial clobbers omitted keys. The `update` response echoes the stored
   trigger, so it doubles as the verify. **Never add an `outcomes` key to a routine that must
   publish to main** — it silently diverts every run's push onto a fresh `claude/*` branch (this
   stranded four Evaluator reviews until 2026-07-03; see `routines/MANIFEST.md`).
3. Keep the shim **small** — full ~20 KB prompts CANNOT be inlined through the tool (the JSON body fails to
   parse / truncates around ~10–24 KB); the shim model exists precisely so trigger bodies stay tiny. Use
   ASCII-only in the shim to avoid unicode-escape issues.

`RemoteTrigger` is **main-session-only** — sub-agents can't load it. The re-GET/echo proves the value is
*stored*, not that the env *executes* it — that only shows at the next routine fire.

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
- Trigger IDs (names/targets after the 2026-06-29 redesign; IDs are stable — old streams retargeted;
  schedules live in ARCHITECTURE.md §1.1 + `routines/MANIFEST.md`, not here):
  - News (daily; ex–Morning Overview) — `trig_012KfuF2Fc8KxNRS9KT1iuYb`
  - AI/ML (Tue+Fri midday) — `trig_01QVL6eSmHTUrmnSLHrpNN9Q`
  - Science (weekly Wed; ex–Cyber+Papers, security dropped) — `trig_01YLiCr5YJ2XNh2QyPbkyzQP`
  - Weekend Deep Read (Sat) — `trig_01XKzge4DxP6wTjLwtkoYeqj`
  - Sports (weekly Mon; Swiss + global majors; added 2026-07-17) — `trig_01PfmuHXkgjhZREW6XfztZrb`
  - Weekly Evaluator (Sun) — `trig_01F5npsKTQTLKekAZ5BczKtG`
  - Watch (topic poll) — `trig_01FgrFMfsreu597nKUXEEQMt`
  - (Markets — `trig_01GBugAS5qw88yQK3tv8kKWx` — **removed 2026-06-18**; trigger left disabled
    server-side, all market content dropped from the pipeline. Do not revive without re-adding the
    snapshot machinery in `dedup.py`.)
- ntfy delivery is configured in the local bridge `.env` (`/usr/local/src/news-brief-ntfy-bridge/.env`).

## Layout
- Briefs: `_posts/{YYYY-MM-DD}-{slug}.md`; slugs `news`, `ai-ml`, `science`, `weekend`, `sports`,
  `evaluator`. (Old `overview`/`cyber-papers` slugs retired 2026-06-29; their posts kept as archive.
  Legacy top-level `briefs/` deleted 2026-07-03 — recoverable from git history.)
- Homepage feed: `_data/homefeed.json` ← `tools/build_stories_feed.py` (parses recent `_posts/`
  for story prose, overlays index `topics`/`importance` by URL; regenerated by each writer
  routine — DEDUP.md Step D).
- Notifications: `pending-notifications/{ts}-{slug}.json` → local bridge → ntfy (then deleted).
- Dedup: `tools/dedup/` (see its `DEDUP.md`); embeddings index under `index/`.
- Story store (2026-07-07): append-only event ledger `index/ledger/*.jsonl` + `tools/store/`
  (ids/materialize/anchor/backfill); source registry `sources/` + `tools/sources/`
  (preflight/lint/health); evaluator metrics `tools/evaluator/`; feedback fold
  `tools/feedback/fold.py` (bridge-side). Spec suite: `python3 -m unittest discover -s tools/tests`
  — run it before committing changes to any of these. Details: ARCHITECTURE.md §1.2 + the
  2026-07-07 SPIKE.
- Topic watches: `watches.yml` (user owns entries; the Watch routine writes only `last_fired`).
- Routine prompts: `routines/<slug>.md` (generated, == live) ← `routines/src/<slug>.md` + shared
  `routines/_shared/*.md`, composed by `routines/assemble.py`. Internal design docs live under
  `docs/` (proposals) and `docs/archive/` (dated). Both, plus `routines/`, are excluded from the
  published Jekyll site in `_config.yml`.
