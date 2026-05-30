# News Brief Pipeline — Historical Notes (superseded)

> Generated 2026-05-14. **For current state use `CLAUDE.md` + `ARCHITECTURE.md`, not this file.**
> The original operational sections (trigger/model/env tables, phase status, "open work", Key
> Paths/IDs, feed lists, Drive output) were removed 2026-05-30 because they had gone stale and
> misleading — back then briefs lived under `briefs/`, routines ran on `env_011` / Sonnet, and
> Markets was active; none of that is true now. What's kept below is only the historical
> *rationale* that isn't recorded elsewhere — the *why* behind how the pipeline fetches sources.

## Decisions worth remembering (rationale only)

### Feed-first, not HTML-first
Original design fetched article HTML directly. Audit 2026-05-03 found 0/18 direct fetches in
Morning Overview. Pivoted to feed endpoints (arXiv RSS, NVD JSON, CISA KEV, Quanta, Nature, ECB
FX, etc.). Direct HTML fetch from the routine sandbox is unreliable (widespread 403s); machine-
readable feeds on separate infrastructure are reachable. (Current feed lists live in the writer
prompts and `ARCHITECTURE.md`, not here.)

### curl before WebFetch
WebFetch inside the routine sandbox 403s on public feeds it should reach; `Bash{curl -fsSL}`
egresses through a different path and tends to succeed. Writers try curl first, WebFetch as
fallback. A successful curl/feed fetch counts as a "direct fetch."

### Coverage footer is the production health metric
The system has no other way to know if it's succeeding. The `Direct fetches: N | via-snippet: M`
line plus the per-feed `Feeds hit: {ok via curl | ok via WebFetch | fail — HTTP NNN}` line is what
signals escalation: if curl *also* starts failing, the egress proxy is the wall, not the feed.

## Still-true gotchas

- **WebFetch ≠ Bash{curl} from inside routines.** See "curl before WebFetch" above.
- **Cron is UTC.** Convert from Europe/Zurich (UTC+2 summer / UTC+1 winter).
- **Anthropic git proxy is configured**, so `git push` from inside routines works without extra auth.
- **ntfy topic is unguessable but unauthenticated** — anyone with it can publish/subscribe; don't share casually.
