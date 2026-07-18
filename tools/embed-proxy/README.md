# embed-proxy — Cloudflare Worker (embeddings)

A small Worker that wraps Cloudflare **Workers AI** (`@cf/baai/bge-m3`, 1024-dim) and returns
embeddings as JSON. The news-brief routines call it at compose time to embed candidate story
summaries for deduplication (`tools/dedup/dedup.py`), because the routine sandbox has
HTTP/HTTPS-allowlist egress only and no embeddings MCP.

Twin of `tools/og-proxy`. Same account, same `wrangler` flow.

## API

```
POST https://embed-proxy.<account>.workers.dev/
Authorization: Bearer <EMBED_TOKEN>
Content-Type: application/json

{ "texts": ["headline + summary one", "headline + summary two"] }
```

Response:

```json
{ "model": "bge-m3", "dim": 1024, "embeddings": [[0.01, -0.04, ...], [...]] }
```

Errors:
- `401` — missing/wrong bearer token (the host is public; the token gates Workers-AI spend).
- `400` — bad JSON, empty/oversized `texts`, non-string elements.
- `405` — non-POST.
- `502` — Workers AI call failed or returned an unexpected shape.

CORS is open, but the token is still required — the browser site does **not** call this; only
the routines (and local `dedup.py`) do.

## Deploy (one-time, ~3 minutes)

From this directory (`tools/embed-proxy`):

1. `wrangler login` (skip if already logged in for og-proxy — same account).
2. Set the shared secret (pick a long random string; reuse it in `dedup.py --token` / the
   routine prompts):
   ```
   wrangler secret put EMBED_TOKEN
   ```
3. Deploy:
   ```
   wrangler deploy
   ```
   Wrangler prints the live URL, e.g. `https://embed-proxy.your-account.workers.dev`.
4. Send that URL back to the assistant. It then:
   - adds the host to the **env_018** routine allowlist,
   - wires the URL + token into the writer prompts and `dedup.py`.

> Workers AI needs to be enabled on the account (it is, for any account that can deploy a
> Worker). The `[ai]` binding in `wrangler.toml` provisions `env.AI` automatically.

## Verify

```bash
WORKER=https://embed-proxy.<account>.workers.dev
TOKEN=<the EMBED_TOKEN you set>

# Happy path — a 1024-float vector per text.
curl -s -XPOST "$WORKER/" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"texts":["Federal Council publishes Bilaterals III ratification roadmap"]}' \
  | jq '{model, dim, n: (.embeddings|length), got: (.embeddings[0]|length)}'
# expect: model "bge-m3", dim 1024, n 1, got 1024

# No / wrong token -> 401.
curl -s -o /dev/null -w "%{http_code}\n" -XPOST "$WORKER/" -d '{"texts":["x"]}'
```

Live logs while testing: `wrangler tail`.

## Cost

bge-m3 embeddings are a few neurons per call; a day's brief candidates (~tens of short strings)
is negligible against the free Workers-AI allocation. The bearer token prevents the public host
from being used as a free embedding endpoint by others.

## /plane/* — the analytical plane (added 2026-07-18)

This worker also hosts the Phase-2 analytical plane, BECAUSE the routine sandbox's egress
allowlist enumerates exact hostnames — a new `*.workers.dev` host would be unreachable from the
routines; this one already is. Same bearer for everything.

- `POST /plane/ingest` — the baked artifact (tools/plane/bake.py; pushed by the publish tail
  after every edition). Stored in KV (`PLANE_KV`, binding in wrangler.toml).
- `POST /plane/search {text, k?}` — embeds the query in-worker (one round trip) + cosine top-k.
- `POST /plane/related {key, k?}` / `thread {key}` / `entities|beats|sources {days?}` / `stats {}`.

The embed contract above is UNCHANGED — `/` never touches KV, so a missing/empty plane cannot
affect the dedup path (adversarially verified before deploy, 23-check smoke: `node test/smoke.mjs`).
