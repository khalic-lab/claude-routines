# claude-routines

Automated news-brief pipeline. Remote claude.ai routines research and write daily/weekly briefs
into this repo, publish them as a Jekyll site, and push notifications through a local ntfy bridge.
Stories are deduped against a rolling embeddings index so the same item isn't re-run for days.

- **Site:** https://khalic-lab.github.io/claude-routines/
- **Briefs:** `_posts/{YYYY-MM-DD}-{slug}.md` (`news`, `ai-ml`, `science`, `weekend`, `evaluator`)
- **How it works / current state:** [`ARCHITECTURE.md`](ARCHITECTURE.md)
- **Working in this repo (for agents):** [`CLAUDE.md`](CLAUDE.md)
- **Design proposals & decisions:** `docs/SPIKE-*.md` · **Dated archive:** `docs/archive/`
