# og-proxy — Cloudflare Worker

A ~150-line Worker that fetches a URL with a browser User-Agent, parses `<head>` for `og:image` / `twitter:image` / `link rel="image_src"`, and returns JSON. Used by `_includes/head/custom.html` on the Pages site to inject real thumbnails next to each citation link.

Free tier: 100k requests/day. Cold start ~25 ms. Per-URL responses cached for 30 days at the edge.

## API

```
GET https://og-proxy.<account>.workers.dev/?url=<URL-encoded article URL>
```

Response (always 200 unless input is malformed):

```json
{
  "image": "https://.../hero.jpg",   // or null
  "title": "Article title here"      // or null
}
```

CORS open (`Access-Control-Allow-Origin: *`). 30-day `Cache-Control: public, max-age=2592000`.

Errors:
- `400` — missing `?url=`, invalid URL, or target points at private/non-http(s) space.
- `405` — non-GET method.

Internal failures (timeout, non-html content, parse error) intentionally return `200 { image: null }` so the client's favicon fallback kicks in seamlessly.

## Deploy (one-time, ~3 minutes)

1. Create a free Cloudflare account at https://dash.cloudflare.com/sign-up (skip if you have one).
2. Install Wrangler globally if needed:
   ```
   npm i -g wrangler
   ```
3. From this directory, log in (opens a browser for OAuth):
   ```
   cd tools/og-proxy
   wrangler login
   ```
4. Deploy:
   ```
   wrangler deploy
   ```

   Wrangler will print the live URL, something like:

   ```
   https://og-proxy.your-account.workers.dev
   ```

5. Send that URL back to the assistant; it edits `_includes/head/custom.html` to point the site at it.

## Verify

```bash
WORKER=https://og-proxy.<account>.workers.dev

# Real article with a hero image — should return a real CDN URL.
curl -s "$WORKER/?url=https%3A%2F%2Fwww.aljazeera.com%2Fnews%2Fliveblog%2F2026%2F5%2F4%2Firan-war-live-tehran-says-trumps-hormuz-mission-violates-ceasefire" | jq

# arXiv abstract — site only exposes its logo as og:image, that's fine.
curl -s "$WORKER/?url=https%3A%2F%2Farxiv.org%2Fabs%2F2605.00414" | jq

# Bad input — 400 + plain text.
curl -i "$WORKER/?url=not-a-url" | head

# Second hit on the same URL — fast, cf-cache-status: HIT.
curl -i "$WORKER/?url=https%3A%2F%2Farxiv.org%2Fabs%2F2605.00414" | head
```

Watch live logs while testing from the browser:

```
wrangler tail
```

## Iterate

Edit `src/worker.js`, re-run `wrangler deploy`. The script is stateless; no migrations.

To roll back, `wrangler rollback` shows recent deployments and pins one.

## Cost

Free tier headroom for personal use is enormous: 100k requests/day, 10 ms CPU per request average (we use < 5 ms). The edge cache deflects repeat lookups for free. There is no DB, no KV, no R2 — just the Worker plus the built-in Cache API.
