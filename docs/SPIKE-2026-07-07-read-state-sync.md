# SPIKE — Cross-device read/unread sync (SHIPPED 2026-07-10, passkey auth)

> Status: **revived and shipped 2026-07-10.** Rafael asked for "some kind of user accounts to
> manage what's read/unread" and chose **passkey/WebAuthn** (§3 option 2) over the per-device
> bearer recommendation, with identity covering **read-state + feedback votes**. As-built:
> `@simplewebauthn/server` on the feedback-sink Worker (`/auth/register-options|register|
> login-options|login`, registration gated by an `INVITE_TOKEN` secret, discoverable credentials,
> UV required, rpID `khalic-lab.github.io`); 90-day rolling sessions in KV; `GET/POST /readstate`
> (session bearer, LWW tombstone map `{sid:{ts,v}}`, shape/size caps, CORS locked to the site
> origin); client sync engine merges remote into `homeRead:v1` via a `syncState:v1` shadow and
> pushes debounced (30s + visibility flush). Signed-out = the original local-only behavior;
> nothing leaves the browser without a session — the opt-in stance below is preserved. One
> registration ceremony covers all Apple devices via iCloud Keychain passkey sync; each device
> signs in with Face ID / Touch ID. The original analysis follows unchanged.
>
> _Deferred at ship time (2026-07-07 text below):_

## 1. What exists (local-only, by design)

`localStorage["homeRead:v1"]` on the homepage: `{ st-id: epoch_ms }`, keyed by the durable
`st-{sha1(norm_url)[:12]}` story ids, 45-day pruning, corrupted-value guard. Marks: explicit
✓ toggle; implicit on headline click/middle-click and on voting. Filter: All | Unread N | Read,
composed with the beat chips. Nothing leaves the browser.

Limitation: per-browser/per-device. Reading on the phone doesn't dim on the Mac.

## 2. The sync design, if wanted

Mechanically small — the feedback-sink Worker already has KV, CORS, and a drain pattern:

- `GET /readstate` → the reader's read-set (KV blob, `{sid: ts}`), `POST /readstate` → merge.
- Client merges remote into local at load (union, max(ts) per sid — reads are monotone except
  explicit unmark, so carry tombstones: `{sid: {ts, v: 1|0}}`, last-write-wins per sid).
- Offline-safe: local stays authoritative until a sync round-trip completes; retries idempotent.
- Volume: trivial (≤ a few KB per reader; one KV key per reader).

## 3. The actual blocker: identity

Everything above assumes the Worker can answer **"whose read-set?"** — and the current surfaces
have no real identity:

- The site is public GitHub Pages; the feedback widget's `X-Widget-Key` is a **shared** site key
  (drive-by deterrent, visible to any page reader — the Worker skill file calls it "not
  security"). Fine for appending votes a human reviews; NOT fine as the key to a personal,
  readable/writable state blob — anyone with the page could read or poison the read-set.
- The `reader` field is self-declared.

So sync requires a real auth decision, options in rough order of sanity for a one-reader system:
1. **Per-device bearer tokens** (generate once per device, paste into a small settings prompt,
   stored in localStorage; Worker maps token → reader). Cheapest; no accounts; revocable per
   device. Weakness: token lives in localStorage on a public site — acceptable for read-state,
   the least sensitive data in the system.
2. **Passkey/WebAuthn** on the Worker — proper, phishing-resistant, no shared secret; more Worker
   code (challenge flow, credential storage in KV) and a registration ceremony per device.
3. Cloudflare Access / OAuth in front of a `/sync` route — heaviest; pulls in an IdP for a
   pipeline with exactly one user.

Recommendation when revived: option 1, upgrade to 2 only if the threat model ever grows beyond
"one reader, low-sensitivity data".

## 4. Interaction with the human-aspect work

Read-state is the first *attention* signal the pipeline has (votes are *quality* signals). If the
"watch less news" objective gets designed (see `SPIKE-2026-07-07-deterministic-feed-poller.md`
§4), synced read-state becomes an input worth having — e.g. evaluator-visible read-rates per
stream/tier, editions that shrink to what's unread. That, not device convenience, is the stronger
reason to eventually build this — and it raises the same privacy question (read telemetry leaving
the browser), which must be an explicit opt-in decision, not a side effect.
