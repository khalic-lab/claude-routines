# Phase-2 analytical plane (ARCHITECTURE §3/§5.2 — built 2026-07-18)

Local Postgres + pgvector over the story ledger: one database answering both query families —
vector search (what's near this) and relational/graph queries (threads, entities, sources,
feedback). The cloud/online plane (compose-time dedup) is untouched; this is the Mac-side
"superpowers" half.

## Setup (already done on this Mac)

```bash
brew install postgresql@17 pgvector
brew services start postgresql@17          # persists across reboots
/opt/homebrew/opt/postgresql@17/bin/createdb claude_routines
```

## Sync (full idempotent upsert — seconds; run any time, cron optional)

```bash
python3 tools/plane/sync.py                # ledger -> Postgres; applies schema.sql itself
```

Source of truth is `index/ledger/*.jsonl` ONLY, folded by `tools/store/store.py materialize()`
(never re-implemented here). Embeddings ride along in the ledger's seen payloads (base64
float16), so a fresh clone rebuilds the whole database — no re-embedding, no git archaeology.

Optional crontab line (NOT installed — add if wanted; the bridge already pulls every 10 min):

```
15 * * * * cd ~/code/claude-routines && git pull -q --rebase && python3 tools/plane/sync.py >> /tmp/plane-sync.log 2>&1
```

## Queries

```bash
python3 tools/plane/query.py stats
python3 tools/plane/query.py search "iran strait of hormuz escalation"
python3 tools/plane/query.py related <sid|url>       # nearest stories, thread edges labeled
python3 tools/plane/query.py thread  <sid|thread_id> # a developing story line, oldest first
python3 tools/plane/query.py beats    --days 30      # per-beat per-week coverage map
python3 tools/plane/query.py entities --days 90      # entity graph (populates as writers emit)
python3 tools/plane/query.py sources  --days 30      # domain concentration + tier mix
```

`search` embeds the query through the embed-proxy Worker (same bge-m3 the stories carry);
everything else is offline SQL. Raw SQL: `psql -d claude_routines` — see `schema.sql` for the
`threads` and `entity_stories` views.

## The graph's edge types (and where they come from)

- `thread_id` — same artifact developing (dedup autolink + writer, validated) — the strongest edge.
- `entities[]` — writer-supplied actors/places/artifacts (DEDUP.md Step C, added 2026-07-18).
- `source_domain` / `tier` — joins against `sources/registry.yml`'s credibility lifecycle.
- `affiliations[]` — the institutions ledger's node set.
- `feedback.sid` — reader votes per story.

Deliberately NOT a dedicated graph database: at ~1.6k stories, Postgres joins + recursive CTEs
cover every graph query, and the 2026-05-31 calibration showed cosine gives nearness, never
relationship type — the typed edges above are where the "knowledge graph" actually lives.
