# Phase-2 analytical plane (ARCHITECTURE §3 — built 2026-07-18, serverless)

**The ledger is the database.** Every query folds `index/ledger/*.jsonl` in-process via
`tools/store/store.py materialize()` (the canonical event folding) and answers both query
families over it: brute-force cosine for vector search — at ~1.6k stories × 1024 dims that's
~0.2s, no index needed — and plain groupbys for the graph/relational side. No Postgres, no
service, no sync step, no state: a fresh clone answers every query with zero setup. Stdlib only.

(A first cut used local Postgres + pgvector per the original §5.2 sketch; replaced the same
evening — a resident database server fights the pipeline's zero-infra character, and at this
scale bought nothing. If the corpus ever outgrows brute force (~100×), the upgrade path is an
embedded FILE — DuckDB or sqlite-vec — never a server.)

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

Only `search` touches the network (it embeds the query through the embed-proxy Worker with the
same bge-m3 model the stories carry — apples-to-apples cosine). Everything else is offline.

## Why embeddings need no rebuild, ever

The ledger's `seen` payloads carry each story's embedding (base64 float16, written by
`dedup.py record`'s dual-write). The 40-day pruning of `index/stories/` is irrelevant here —
the ledger is append-only and complete back to 2026-05-27.

## The graph's edge types (and where they come from)

- `thread_id` — same artifact developing (dedup autolink + writer, validated) — the strongest edge.
- `entities[]` — writer-supplied actors/places/artifacts (DEDUP.md Step C, added 2026-07-18).
- `source_domain` / `tier` — joins against `sources/registry.yml`'s credibility lifecycle.
- `affiliations[]` — the institutions ledger's node set.
- per-story folded `feedback` — reader votes.

Deliberately NOT a graph database either: the 2026-05-31 calibration showed cosine gives
nearness, never relationship type — the typed edges above are where the "knowledge graph"
actually lives, and at this scale they're dict groupbys.

## Worker-hosted twin (added 2026-07-18): queryable from the ROUTINE SANDBOX

The same queries are served by the embed-proxy Worker (`/plane/*` on
`embed-proxy.khalic-lab.workers.dev` — mounted THERE because the env_018 allowlist enumerates
exact hostnames; a new host would be unreachable from the routines). `tools/plane/bake.py --push`
bakes the ledger into a 7.4MB artifact (magic + meta JSON + float32 vectors) and POSTs it to
`/plane/ingest`; the publish tail does this after every edition (publish.py `plane-push`,
non-fatal). Same bearer as embeddings (the DEDUP.md token), so every routine can already query:

    curl -s -XPOST "$EMBED_WORKER_URL/plane/search" -H "Authorization: Bearer $EMBED_TOKEN" \
      -H 'Content-Type: application/json' -d '{"text":"iran hormuz","k":5}'

Local CLI (this directory) and Worker answer identically (parity-verified at deploy). The local
CLI stays: it works offline from a bare clone and is the reference implementation.
