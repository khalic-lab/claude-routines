# Architecture diagrams

Mermaid diagrams of the news-brief pipeline, grounded in the actual code (real file paths, class
names, trigger IDs, environment, Worker bindings). They render on GitHub and in any Mermaid-aware
viewer. Mutable facts (models, schedules) ultimately live in [`../ARCHITECTURE.md`](../ARCHITECTURE.md);
if a diagram and `ARCHITECTURE.md` disagree, the latter wins.

> **Last verified against the code: 2026-07-03** (01+02 refreshed for the 2026-06-29 cadence
> redesign + the News midday move). Diagrams drift silently between refreshes — check this date.

| # | File | What it shows |
|---|------|---------------|
| 01 | [system-overview](01-system-overview.md) | Components & end-to-end data flow (cloud → repo → Pages / bridge → phone) |
| 02 | [routines-and-schedules](02-routines-and-schedules.md) | The six triggers: IDs, models, crons, outputs, MCP connectors |
| 03 | [compose-time-dedup](03-compose-time-dedup.md) | `dedup.py` verdict logic, embed-proxy, thresholds, the index |
| 04 | [bridge-delivery-and-feedback](04-bridge-delivery-and-feedback.md) | Local bridge tick: ntfy delivery + two-phase feedback drain |
| 05 | [frontend-rendering](05-frontend-rendering.md) | Client-side passes in `_includes/head/custom.html` |

> Excluded from the published Jekyll site (`_config.yml`) — these reference the environment ID,
> trigger IDs and Worker URLs, which shouldn't ship to the public Pages site.
