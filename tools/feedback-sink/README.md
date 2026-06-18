# feedback-sink — Cloudflare Worker (reader feedback)

Captures reader thumbs (+1 / −1) and an optional free-text reason from the published Jekyll
briefs, holds them in **Cloudflare KV**, and lets the local bridge drain them into the git repo
(`feedback/*.jsonl`) on its existing cron tick. Twin of `tools/embed-proxy` / `tools/og-proxy`.

The loop is **human-gated**: raw feedback is committed losslessly, but the files the writers read
(`reader-profile.md`, `reader-profile/source-weights.yml`) change only via the Weekly Evaluator's
human-applied patch proposals — never auto-mutated from a tap. See `feedback/FEEDBACK.md`.

## API

```
POST /submit            (public, CORS)  body: {brief, vote, reason?, story_id?, surface?}
  -> {ok:true, id}                       writes one record to KV. No bearer (browser can't keep one);
                                         optional X-Widget-Key header if WIDGET_KEY is set.
GET  /drain             (Bearer)         -> {count, truncated, records:[{key, ...record}]}
                                         lists queued records; does NOT delete.
POST /ack               (Bearer)         body: {keys:[...]}  -> {ok, deleted}
                                         deletes the given KV keys (call AFTER commit+push).
```

Two-phase drain/ack so a missed bridge tick neither loses nor double-commits records.

## Deploy (one-time, ~4 minutes)

From this directory (`tools/feedback-sink`):

1. `wrangler login` (skip if already logged in for embed-proxy/og-proxy — same account).
2. Create the KV namespace and paste the printed id into `wrangler.toml`:
   ```
   wrangler kv namespace create FEEDBACK_KV
   ```
3. Set the bridge bearer secret (a long random string — reuse it on the Mac bridge `.env` as
   `FEEDBACK_TOKEN`):
   ```
   wrangler secret put FEEDBACK_TOKEN
   ```
   Optionally set a widget deterrence key (must match the `FEEDBACK_KEY` constant in
   `_includes/head/custom.html`):
   ```
   wrangler secret put WIDGET_KEY
   ```
4. Deploy:
   ```
   wrangler deploy
   ```
   Wrangler prints the live URL, e.g. `https://feedback-sink.<account>.workers.dev`.
5. Send that URL back to the assistant. It then wires it into:
   - the widget in `_includes/head/custom.html` (the `FEEDBACK_URL` constant),
   - the bridge drain/ack step (`tools/feedback/feedback.py` env),
   - the **env_018** allowlist is NOT needed (the Worker is called by the *browser* and the *Mac
     bridge*, never the routine sandbox).

## Verify

```bash
WORKER=https://feedback-sink.<account>.workers.dev
TOKEN=<the FEEDBACK_TOKEN you set>

# Submit (public) — expect {ok:true,id:...}
curl -s -XPOST "$WORKER/submit" -H 'Content-Type: application/json' \
  -d '{"brief":"2026-06-07-overview","vote":-1,"reason":"weekend brief too long"}'

# Drain (bearer) — expect the record back with its KV key
curl -s "$WORKER/drain" -H "Authorization: Bearer $TOKEN" | jq

# Ack (bearer) — delete it
curl -s -XPOST "$WORKER/ack" -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"keys":["<key from drain>"]}'

# Bad bearer -> 401
curl -s -o /dev/null -w "%{http_code}\n" "$WORKER/drain"
```

Live logs while testing: `wrangler tail`.

## Privacy

The reason text is more sensitive than a notification body, so it is routed through this **private
Worker + KV** and the **private repo** — never an ntfy topic (world-readable). The `/submit` route
is public by necessity (a browser widget); the defense is shape caps in the Worker + the human gate
downstream, not the (un-hideable) widget key.
