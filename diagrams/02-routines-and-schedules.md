# 02 · Routines — triggers, models, schedules, outputs

Every routine runs in the same environment (`env_018zypSdRSdGdrZ8J5usqCWA`). Since 2026-06-29 each
trigger (except Watch) holds a small bootstrap shim that reads its real prompt from `routines/*.md`
at fire time — the repo files ARE the live prompts. Model tiers are split by job (see `docs/SPIKE-model-tiering.md`): writers
and analysis on Opus, high-frequency polling on Haiku. Cron is UTC.

```mermaid
flowchart LR
  subgraph env["env_018zypSdRSdGdrZ8J5usqCWA — all routines (bootstrap shim → routines/*.md)"]
    direction TB
    subgraph writers["Writers · claude-opus-4-8"]
      direction TB
      NW["News (CH + world) · routines/news.md<br/>trig_012KfuF2Fc8KxNRS9KT1iuYb<br/>cron 0 10 * * * (daily midday, since 2026-07-03)<br/>→ _posts/{d}-news.md · weekday email<br/>MCP: Drive, HuggingFace, Gmail"]
      AM["AI/ML (+ arXiv papers) · routines/ai-ml.md<br/>trig_01QVL6eSmHTUrmnSLHrpNN9Q<br/>cron 0 10 * * 2,5 (Tue+Fri)<br/>→ _posts/{d}-ai-ml.md<br/>MCP: Drive, HuggingFace"]
      SC["Science (non-AI, weekly) · routines/science.md<br/>trig_01YLiCr5YJ2XNh2QyPbkyzQP<br/>cron 0 15 * * 3 (Wed)<br/>→ _posts/{d}-science.md<br/>MCP: Drive, HuggingFace"]
      WK["Weekend Deep Read · routines/weekend.md<br/>trig_01XKzge4DxP6wTjLwtkoYeqj<br/>cron 30 7 * * 6 (Sat)<br/>→ _posts/{d}-weekend.md<br/>MCP: Drive, HuggingFace, Gmail"]
    end
    subgraph poll["Polling · claude-haiku-4-5"]
      WT["Watch (topic poll) · routines/watch.md<br/>trig_01FgrFMfsreu597nKUXEEQMt<br/>cron 0 */4 * * * (every 4h)<br/>reads watches.yml → pending-notifications/<br/>writes only last_fired<br/>MCP: Drive, HuggingFace, Gmail, Calendar"]
    end
    subgraph analysis["Analysis · claude-opus-4-8"]
      WE["Weekly Evaluator · routines/weekly-evaluator.md<br/>trig_01F5npsKTQTLKekAZ5BczKtG<br/>cron 30 9 * * 0 (Sun)<br/>reads 7d _posts + feedback → _posts/{d}-evaluator.md<br/>proposes patches (human-gated)<br/>MCP: Drive, Gmail"]
    end
  end

  RM["Markets — REMOVED 2026-06-18<br/>trig_01GBugAS5qw88yQK3tv8kKWx (disabled server-side)<br/>no brief emits market content"]:::dead

  classDef dead stroke-dasharray:5 5,color:#999,fill:#f7f7f7;
```

**Grounded in:** `CLAUDE.md` (stable identifiers — env + all trigger IDs), `ARCHITECTURE.md` §1.1
(crons, models), `routines/MANIFEST.md`, `routines/*.md` (the live prompts, read via the bootstrap shim).
The RemoteTrigger API exposes no delete, so the Markets trigger config is retained but disabled.
