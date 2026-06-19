# Routine manifest — claude.ai RemoteTrigger config

Byte-faithful snapshots of the live routine prompts (`*.md` beside this file), **except** the
fetch-proxy bearer is redacted to `Bearer ${FETCH_PROXY_TOKEN}` in the four writer prompts —
substitute the real value (the `fetch-proxy` Worker bearer; lives in the Worker secret +
`tools/fetch-proxy/.dev.vars`) when mirroring back to RemoteTrigger. All routines share
`environment_id = env_018zypSdRSdGdrZ8J5usqCWA`.

These are NOT auto-synced. To change a routine: edit the file here, mirror it to RemoteTrigger
(`RemoteTrigger update`, full `session_context` from below), then byte-verify (see `../CLAUDE.md`).

| Routine | file | trigger_id | cron | model | enabled |
|---|---|---|---|---|---|
| News: Morning Overview | `morning-overview.md` | `trig_012KfuF2Fc8KxNRS9KT1iuYb` | `30 4 * * *` (daily 04:30 UTC (06:30 CEST)) | `claude-opus-4-8` | True |
| News: AI/ML | `ai-ml.md` | `trig_01QVL6eSmHTUrmnSLHrpNN9Q` | `30 19 * * *` (daily 19:30 UTC (21:30 CEST)) | `claude-opus-4-8` | True |
| News: Cyber + Papers | `cyber-papers.md` | `trig_01YLiCr5YJ2XNh2QyPbkyzQP` | `0 17 * * *` (daily 17:00 UTC (19:00 CEST)) | `claude-opus-4-8` | True |
| News: Weekend Deep Read | `weekend.md` | `trig_01XKzge4DxP6wTjLwtkoYeqj` | `30 7 * * 6` (Saturdays 07:30 UTC (09:30 CEST)) | `claude-opus-4-8` | True |
| News: Weekly Evaluator | `weekly-evaluator.md` | `trig_01F5npsKTQTLKekAZ5BczKtG` | `30 9 * * 0` (Sundays 09:30 UTC (11:30 CEST)) | `claude-opus-4-8` | True |
| Watch | `watch.md` | `trig_01FgrFMfsreu597nKUXEEQMt` | `0 */4 * * *` (every 4h) | `claude-haiku-4-5-20251001` | True |

## Full `session_context` per routine (verbatim — required to reconstruct the update body)

### morning-overview
```json
{
  "allowed_tools": [
    "WebFetch",
    "WebSearch",
    "Read",
    "Write",
    "Bash",
    "Edit",
    "Glob",
    "Grep"
  ],
  "model": "claude-opus-4-8",
  "sources": [
    {
      "git_repository": {
        "url": "https://github.com/khalic-lab/claude-routines"
      }
    }
  ]
}
```

### ai-ml
```json
{
  "allowed_tools": [
    "WebFetch",
    "WebSearch",
    "Read",
    "Write",
    "Bash",
    "Edit",
    "Glob",
    "Grep"
  ],
  "model": "claude-opus-4-8",
  "sources": [
    {
      "git_repository": {
        "url": "https://github.com/khalic-lab/claude-routines"
      }
    }
  ]
}
```

### cyber-papers
```json
{
  "allowed_tools": [
    "WebFetch",
    "WebSearch",
    "Read",
    "Write",
    "Bash",
    "Edit",
    "Glob",
    "Grep"
  ],
  "model": "claude-opus-4-8",
  "sources": [
    {
      "git_repository": {
        "url": "https://github.com/khalic-lab/claude-routines"
      }
    }
  ]
}
```

### weekend
```json
{
  "allowed_tools": [
    "WebFetch",
    "WebSearch",
    "Read",
    "Write",
    "Bash",
    "Edit",
    "Glob",
    "Grep"
  ],
  "model": "claude-opus-4-8",
  "sources": [
    {
      "git_repository": {
        "url": "https://github.com/khalic-lab/claude-routines"
      }
    }
  ]
}
```

### weekly-evaluator
```json
{
  "allowed_tools": [
    "WebFetch",
    "WebSearch",
    "Read",
    "Write",
    "Bash",
    "Edit",
    "Glob",
    "Grep"
  ],
  "autofix_on_pr_create": false,
  "model": "claude-opus-4-8",
  "outcomes": [
    {
      "git_repository": {
        "git_info": {
          "branches": [
            "claude/admiring-edison"
          ],
          "repo": "khalic-lab/claude-routines"
        }
      }
    }
  ],
  "sources": [
    {
      "git_repository": {
        "url": "https://github.com/khalic-lab/claude-routines"
      }
    }
  ]
}
```

### watch
```json
{
  "allowed_tools": [
    "WebFetch",
    "WebSearch",
    "Read",
    "Write",
    "Bash",
    "Edit",
    "Glob",
    "Grep"
  ],
  "autofix_on_pr_create": false,
  "model": "claude-haiku-4-5-20251001",
  "outcomes": [
    {
      "git_repository": {
        "git_info": {
          "branches": [
            "claude/serene-mayer"
          ],
          "repo": "khalic-lab/claude-routines"
        }
      }
    }
  ],
  "sources": [
    {
      "git_repository": {
        "url": "https://github.com/khalic-lab/claude-routines"
      }
    }
  ]
}
```
