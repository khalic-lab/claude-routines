# Architecture diagrams

Mermaid diagrams of the news-brief pipeline, grounded in the actual code (real file paths, class
names, trigger IDs, environment, Worker bindings). They render on GitHub and in any Mermaid-aware
viewer. Mutable facts (models, schedules) ultimately live in [`../ARCHITECTURE.md`](../ARCHITECTURE.md);
if a diagram and `ARCHITECTURE.md` disagree, the latter wins.

> **Last verified against the code: 2026-07-03** (01+02 refreshed for the 2026-06-29 cadence
> redesign + the News midday move). Diagrams drift silently between refreshes — check this date.

Diagram 06 was separately verified against the implementation on **2026-07-20**.

| # | File | What it shows |
|---|------|---------------|
| 01 | [system-overview](01-system-overview.md) | Components & end-to-end data flow (cloud → repo → Pages / bridge → phone) |
| 02 | [routines-and-schedules](02-routines-and-schedules.md) | The six triggers: IDs, models, crons, outputs, MCP connectors |
| 03 | [compose-time-dedup](03-compose-time-dedup.md) | `dedup.py` verdict logic, embed-proxy, thresholds, the index |
| 04 | [bridge-delivery-and-feedback](04-bridge-delivery-and-feedback.md) | Local bridge tick: ntfy delivery + two-phase feedback drain |
| 05 | [frontend-rendering](05-frontend-rendering.md) | Client-side passes in `_includes/head/custom.html` |
| 06 | [public-how-it-works](06-public-how-it-works-wide.mmd) | Public-safe trust map used by the homepage modal; a narrow-screen source lives beside it |

> The `diagrams/` sources are excluded from the published Jekyll site (`_config.yml`). Diagrams
> 01–05 contain environment IDs, trigger IDs or Worker URLs; diagram 06 is the public-safe source
> whose generated SVGs are copied into the published asset tree.

## Homepage diagram assets

The `06-public-how-it-works-{wide,mobile}.mmd` sources deliberately omit private identifiers. Their
light and dark SVG renders are published from `assets/diagrams/`. Regenerate them with Mermaid CLI
11.12.0 and the matching `06-*.json` / `06-*.css` theme files:

```sh
export PUPPETEER_EXECUTABLE_PATH="${PUPPETEER_EXECUTABLE_PATH:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
for layout in wide mobile; do
  for theme in light dark; do
    bunx @mermaid-js/mermaid-cli@11.12.0 \
      -i "diagrams/06-public-how-it-works-${layout}.mmd" \
      -o "assets/diagrams/how-it-works-${layout}-${theme}.svg" \
      -c "diagrams/06-public-how-it-works-${theme}.json" \
      -C "diagrams/06-public-how-it-works-${theme}.css" \
      -b transparent
  done
done
perl -0pi -e 's/<text /<text xml:space="preserve" /g' assets/diagrams/how-it-works-*.svg
```

Native SVG text is intentional: the final pass preserves leading spaces in Mermaid's wrapped
`tspan` lines without relying on `foreignObject` support.
