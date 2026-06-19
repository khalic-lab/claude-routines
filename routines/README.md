# `routines/` — the source of truth for the claude.ai routine prompts

The remote claude.ai routines (Morning Overview, AI/ML, Cyber+Papers/Evening, Weekend, Weekly
Evaluator, Watch) run prompts that live in each trigger's `job_config.ccr` **server-side**. The
claude.ai RemoteTrigger API has no bulk export and no version history, so until now the actual
editorial content of this pipeline was untracked — one bad edit or a lost environment and there
was no recovering it. These files fix that: they are **byte-faithful snapshots of the live
prompts**, version-controlled here, so the repo is the canonical record and a backup.

## Files

- `morning-overview.md`, `ai-ml.md`, `cyber-papers.md`, `weekend.md`, `weekly-evaluator.md`,
  `watch.md` — one file per routine, containing that routine's full prompt verbatim.
- `MANIFEST.md` — per-routine `trigger_id`, cron, model, `enabled`, and the **full
  `session_context`** (required to reconstruct a RemoteTrigger update body). Shared
  `environment_id = env_018zypSdRSdGdrZ8J5usqCWA`.

## One redaction

The four writer prompts embed the `fetch-proxy` Worker bearer in a `curl` example. It is redacted
here to `Bearer ${FETCH_PROXY_TOKEN}`. The real value is the Worker secret (also in the git-ignored
`tools/fetch-proxy/.dev.vars`). Substitute it back when mirroring a writer prompt to RemoteTrigger.
The Evaluator and Watch prompts carry no secret and are fully verbatim.

## Not auto-synced — the workflow

There is no automatic repo→claude.ai push. These snapshots and the live config can drift if someone
edits one without the other. The convention (see `../CLAUDE.md`):

1. **Edit the prompt here first** (the repo file is the source of truth).
2. **Mirror it to RemoteTrigger** with `RemoteTrigger update`, wrapped in `job_config.ccr`, sending
   the **complete** `session_context` from `MANIFEST.md` (substitute the real fetch-proxy token in
   writer prompts).
3. **Byte-verify** the stored result against the file (re-GET, diff) — RemoteTrigger silently no-ops
   unwrapped fields and clobbers an omitted `session_context` key.
4. Commit the repo change.

When in doubt about whether the repo matches live, re-snapshot: `RemoteTrigger get` each trigger and
overwrite the file (re-applying the token redaction).

## Excluded from Jekyll

`routines` is in `_config.yml`'s `exclude:` list — these are private editorial config and must never
be published to the public GitHub Pages site.
