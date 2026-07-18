# `routines/` — the source of truth for the claude.ai routine prompts

**Since 2026-06-29 the live triggers are BOOTSTRAP SHIMS**: each writer/evaluator trigger's stored
prompt is a small shim that `git pull`s this repo and reads its real prompt from `routines/<slug>.md`
at fire time. The files here are not snapshots that can drift — they ARE the live prompts. See
`MANIFEST.md` for the shim shape and per-trigger config, and `../CLAUDE.md` → "Editing a routine".

## Files

- `news.md`, `ai-ml.md`, `science.md`, `weekend.md` — the four writer prompts, **generated**:
  edit `src/<slug>.md` (stream-specific body) or `_shared/*.md` (partials shared by all four),
  then run `python3 routines/assemble.py` to regenerate. Never hand-edit the generated files —
  `python3 routines/assemble.py check` is the drift guard (non-zero exit = generated file no
  longer matches its sources).
- `weekly-evaluator.md` — the Evaluator prompt; **not** assembled, edit directly.
- `watch.md` — the Watch prompt. **The one exception:** Watch is not shimmed; its full prompt
  lives inline in the trigger. To change it, use `RemoteTrigger update` AND edit `watch.md` to match.
- `MANIFEST.md` — per-routine `trigger_id`, cron, model, shim shape, and the **full
  `session_context`** (required to reconstruct a RemoteTrigger update body). Shared
  `environment_id = env_018zypSdRSdGdrZ8J5usqCWA`.
- `src/`, `_shared/`, `assemble.py` — the assembly layer for the four writer prompts.

## One redaction

The four writer prompts reference the `fetch-proxy` Worker bearer as the literal placeholder
`${FETCH_PROXY_TOKEN}`. The real value lives only in each trigger's shim (step 3) and the Worker
secret (also in the git-ignored `tools/fetch-proxy/.dev.vars`) — the repo never holds it, so
these files are safe to commit as-is.

## The edit workflow

1. Edit `src/<slug>.md` or `_shared/*.md` (or `weekly-evaluator.md` directly).
2. `python3 routines/assemble.py` (writers only), then `python3 routines/assemble.py check`.
3. **Commit + push.** Done — the shim reads the new file at the next fire. No RemoteTrigger call,
   no mirroring, no byte-verify.

`RemoteTrigger update` is needed ONLY for a trigger's schedule (`cron_expression`), display name,
`session_context`, or the shim text/token itself — see `MANIFEST.md` for the protocol and traps.

## Publication status (corrected 2026-07-18)

`routines` is in `_config.yml`'s `exclude:` list, so these files never render as pages — but the
public `/prompts/` page deliberately republishes the six live prompt bodies verbatim via Liquid
`include_relative` (a transparency feature, added knowingly). **Treat every routine file as
public content**: no secrets, no infra ids, and personal data only where the render-time
redaction in `prompts.html` covers it (currently the notification email). `tools/check_publish.py`
scans the `include_relative` targets for exactly this. What stays genuinely private is the
non-included material: `MANIFEST.md` (trigger ids/shims), `src/`, `_shared/`, `assemble.py`.
