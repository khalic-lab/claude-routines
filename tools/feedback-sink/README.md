# feedback-sink — Cloudflare Worker (reader feedback + passkey accounts)

> **Deployed 2026-06-18** → `https://feedback-sink.khalic-lab.workers.dev` (khalic-lab CF account;
> KV `FEEDBACK_KV`, secret `FEEDBACK_TOKEN`). Widget + bridge + writers/Evaluator all wired and
> verified — the loop is LIVE (see `feedback/FEEDBACK.md`). The steps below are the original
> one-time deploy guide, kept for reference / redeploy.
>
> **Extended 2026-07-10**: passkey (WebAuthn) accounts + cross-device read-state sync
> (`/auth/*`, `/readstate`). This made the worker its first **bundled dependency**
> (`@simplewebauthn/server`) — deploys now need `npm install` first — and one new secret,
> `INVITE_TOKEN`. See "Passkey accounts" below.

Captures reader thumbs (+1 / −1) and an optional free-text reason from the published Jekyll
briefs, holds them in **Cloudflare KV**, and lets the local bridge drain them into the git repo
(`feedback/*.jsonl`) on its existing cron tick. Twin of `tools/embed-proxy` / `tools/og-proxy`.
Since 2026-07-10 it is also the account backend: passkey auth + per-reader read-state sync for
the homepage's read/unread marks.

The loop is **human-gated**: raw feedback is committed losslessly, but the files the writers read
(`reader-profile.md`, `reader-profile/source-weights.yml`) change only via the Weekly Evaluator's
human-applied patch proposals — never auto-mutated from a tap. See `feedback/FEEDBACK.md`.

## API

```
POST /submit            (site key, CORS) body: {brief, vote, reason?, story_id?, surface?}
  -> {ok:true, id}                       writes one record to KV. No bearer (browser can't keep one);
                                         requires the X-Widget-Key header (fails closed with 403 if
                                         WIDGET_KEY is unset or wrong).
POST /propose           (site key, CORS) body: {topic, detail?, surface?}
  -> {ok:true, id}                       writes one kind:"proposal" record to KV (the home-page
                                         "Propose a brief" form); bridge routes it to proposals/.
GET  /drain             (Bearer)         -> {count, truncated, records:[{key, ...record}]}
                                         lists queued records; does NOT delete.
POST /ack               (Bearer)         body: {keys:[...]}  -> {ok, deleted}
                                         deletes the given KV keys (call AFTER commit+push).

POST /auth/register-options  (invite)    body: {invite} -> WebAuthn creation options.
POST /auth/register          (invite)    body: {invite, response} -> {ok, session, reader}
                                         verifies the attestation, stores the credential
                                         (cred:{id}), issues a session. 403 unless the body
                                         `invite` matches the INVITE_TOKEN secret (fails
                                         closed while unset).
POST /auth/login-options     (public)    -> WebAuthn request options (discoverable creds,
                                         user verification required, single-use challenge).
POST /auth/login             (public)    body: {response} -> {ok, session, reader}.
GET  /readstate              (session)   -> {reader, state:{sid:{ts,v}}}.
POST /readstate              (session)   body: {state:{sid:{ts,v}}} -> {ok,total,changed,skipped}
                                         LWW merge per sid (v:0 = unread tombstone); caps:
                                         64KB body (413), 2000 entries, sid ^st-[0-9a-f]{12}$,
                                         90-day age-out. Session = Bearer <64-hex> from
                                         /auth/*, KV TTL 90 days, rolling.
```

Two-phase drain/ack so a missed bridge tick neither loses nor double-commits records.

## Passkey accounts (2026-07-10)

Single-reader accounts for read/unread sync across devices (SPIKE-2026-07-07-read-state-sync).
Registration is invite-gated; one ceremony on any Apple device creates an iCloud-Keychain-synced
passkey usable everywhere. rpID is `khalic-lab.github.io` (valid: github.io is on the Public
Suffix List, so the subdomain is the registrable domain). `/auth/*` and `/readstate` answer CORS
only for `https://khalic-lab.github.io`; the older routes keep `*`. A signed-in browser also
sends the session Bearer on `/submit`, which pins the record's `reader` server-side.

Deploy delta for the 2026-07-10 extension (from `tools/feedback-sink/`):

```bash
npm install                              # bundles @simplewebauthn/server (wrangler builds it in)
openssl rand -hex 24                     # -> the invite code; keep it until registration is done
printf '%s' "<that value>" | wrangler secret put INVITE_TOKEN
wrangler deploy
```

Then register once from the live site: homepage → Sync → "First time? Set up" → paste the invite
code → Face ID / Touch ID. After that every device signs in via Sync → "Sign in with passkey".
The invite code stays live for future re-registrations (new credentials for the same reader);
rotate or unset it after use if that's unwanted — login and sync don't need it.

Smoke test (mock KV, no network — covers every non-crypto guard): `node test/smoke.mjs`.

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
   Set the shared site key — **required** (the Worker fails closed: /submit and /propose return
   403 for every request while WIDGET_KEY is unset). It must match the key visitors enter in the
   unlock modal (sent as the `X-Widget-Key` header; kept in the browser's localStorage):
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

# Submit (site key) — expect {ok:true,id:...}; without X-Widget-Key expect 403 (fail closed)
curl -s -XPOST "$WORKER/submit" -H 'Content-Type: application/json' \
  -H "X-Widget-Key: <the WIDGET_KEY you set>" \
  -d '{"brief":"2026-07-03-news","vote":-1,"reason":"too long"}'

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
