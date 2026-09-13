// feedback-sink: capture reader feedback (thumbs +/- + optional reason) AND brief
// proposals from the published Jekyll site, hold them in Cloudflare KV, and let the
// local bridge drain them into the git repo on its cron tick. Since 2026-07-10 it is
// also the account backend: passkey (WebAuthn) auth + per-reader read-state sync.
//
// Routes:
//   POST /submit                 (session)   -- the home-grid widget posts one feedback record.
//   POST /propose                (session)   -- the home page form posts one brief proposal.
//   GET  /drain                  (bearer)    -- list queued records (does NOT delete). Bridge reads.
//   POST /ack                    (bearer)    -- delete the given KV keys. Bridge calls AFTER commit+push.
//   POST /auth/register-options  (invite)    -- WebAuthn registration options (invite-gated).
//   POST /auth/register          (invite)    -- verify attestation, store credential, issue session.
//   POST /auth/login-options     (public)    -- WebAuthn authentication options (discoverable cred).
//   POST /auth/login             (public)    -- verify assertion, issue session.
//   GET  /readstate              (session)   -- the reader's read-state map {sid:{ts,v}}.
//   POST /readstate              (session)   -- LWW-merge a read-state delta into KV.
//   GET  /prefs                  (session)   -- the reader's UI prefs {topics:[...], ts}.
//   POST /prefs                  (session)   -- whole-object LWW-by-ts of the topic selection.
//   POST /admin/actions          (session)   -- queue a source-registry action (retire/restore/add/set).
//   GET  /admin/actions          (session)   -- the queued (not-yet-applied) admin actions.
//   GET  /admin/snapshot         (session)   -- the bridge-pushed registry+usage snapshot the page reads.
//   PUT  /admin/snapshot         (bearer)    -- store the snapshot (the bridge pushes it every tick).
//   GET  /admin/drain            (bearer)    -- list queued admin actions (does NOT delete). Bridge reads.
//   POST /admin/ack              (bearer)    -- delete the given admin KV keys. Bridge calls AFTER apply+push.
//
// Writes (/submit, /propose) require a passkey session Bearer — the shared X-Widget-Key
// site password was retired 2026-07-25 (passkeys-only; the session also pins the reader
// identity, so the body `reader` field is ignored). Privileged reads/deletes (/drain,
// /ack) use the separate bearer FEEDBACK_TOKEN. Both write kinds share the `fb:` KV
// prefix so one drain/ack handles them; the bridge routes by `kind` on write
// (proposal -> proposals/).
//
// Passkeys: registration is gated by the Worker secret INVITE_TOKEN (fail closed if
// unset). Credentials (`cred:`), sessions (`session:`), single-use challenges (`chal:`),
// read state (`readstate:`), UI prefs (`prefs:`) and the source-admin queue + snapshot
// (`adm:`, `admin:`) all live in the same FEEDBACK_KV — none of those prefixes collide
// with `fb:` so the feedback drain/ack never sees them (and vice versa). Every
// session-carrying route (/auth/*, /submit, /propose, /readstate, /prefs) answers CORS
// only for the published site origin; the bridge routes (/drain, /ack) keep `*`.
//
// Twin of tools/embed-proxy. Needs KV bound as FEEDBACK_KV, secret FEEDBACK_TOKEN
// (drain/ack bearer) and secret INVITE_TOKEN (passkey registration invite). See README.

import {
  generateAuthenticationOptions,
  generateRegistrationOptions,
  verifyAuthenticationResponse,
  verifyRegistrationResponse,
} from "@simplewebauthn/server";
import { isoBase64URL } from "@simplewebauthn/server/helpers";

const MAX_REASON = 2000; // chars of free-text reason / proposal detail
const MAX_TOPIC = 300; // chars of a proposal topic line
const MAX_FIELD = 200; // chars for brief / story_id / surface
const DRAIN_LIMIT = 200; // records per drain (n=few: a day's writes are a handful)
const KEY_PREFIX = "fb:";

// WebAuthn relying party: github.io is on the Public Suffix List, so the subdomain
// khalic-lab.github.io IS the registrable domain and therefore a valid rpID.
const RP_ID = "khalic-lab.github.io";
const RP_NAME = "khalic news";
const SITE_ORIGIN = "https://khalic-lab.github.io";
const READER = "rafael"; // single-reader site: every credential maps to this identity
const READER_DISPLAY = "Rafael";

const CHALLENGE_TTL_S = 300; // single-use WebAuthn challenges
const SESSION_TTL_S = 90 * 24 * 3600; // session lifetime in KV
// Re-mint the TTL when the last roll is older than this. Daily granularity: KV's
// expirationTtl anchors to the last PUT, so the 90-day idle budget must run from the
// reader's LAST VISIT — the old 30-day threshold left a dead zone where weeks of daily
// visits extended nothing and the session died 90 days after the last ROLL instead.
const SESSION_ROLL_MS = 24 * 3600 * 1000;
const STATE_MAX_BYTES = 65536; // raw /readstate POST body cap
const STATE_MAX_ENTRIES = 2000; // entries per /readstate POST
const STATE_MAX_AGE_MS = 90 * 24 * 3600 * 1000; // merged entries older than this are dropped
const STATE_MAX_SKEW_MS = 86400000; // accept ts up to one day in the future
const SID_RE = /^st-[0-9a-f]{12}$/; // story ids from the story store
// /submit story ids: ledger sids, or the homepage's editorial cards (ed-<stream>-<date>).
const STORY_ID_RE = /^(st-[0-9a-f]{12}|ed-[a-z0-9-]{1,40}-\d{4}-\d{2}-\d{2})$/;
const PREFS_MAX_TOPICS = 50; // topic keys a reader can select (the vocab is ~a dozen)
const TOPIC_KEY_RE = /^[a-z0-9][a-z0-9-]{0,39}$/; // beat/topic filter keys (build_stories_feed TOPICS)

// Source-registry admin (2026-09-13). Queued mutations live under `adm:` (drained + applied by
// the Mac bridge, mirroring the feedback path); the registry+usage snapshot the /admin/ page reads
// lives under `admin:`. Both prefixes are disjoint from `fb:`, so neither drain sees the other's keys.
const ADMIN_KEY_PREFIX = "adm:";
const ADMIN_SNAPSHOT_KEY = "admin:snapshot";
const ADMIN_SNAPSHOT_META_KEY = "admin:snapshot_meta";
const ADMIN_MAX_ACTION_BYTES = 8192; // one queued action POST body cap (413 above)
const ADMIN_MAX_SNAPSHOT_BYTES = 4 * 1024 * 1024; // pushed snapshot cap, 4 MB (413 above)
const ADMIN_MAX_NOTE = 500; // chars of the optional per-action note
// Registrable-domain shape; the schema deliberately matches lowercase only, so the handler
// lowercases the input before testing (a typo'd `Example.org` normalizes, never 400s).
const DOMAIN_RE = /^(?=.{4,253}$)[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$/;
const ADMIN_TYPES = new Set(["retire", "restore", "add", "set"]);
const ADMIN_TIERS = new Set(["T1", "T2"]);
const ADMIN_STREAMS = new Set(["news", "ai-ml", "science", "weekend", "sports"]);
const ADMIN_REACH = new Set(["direct", "proxy", "search-only", "blocked", "blocked-paywall"]);
const ADMIN_STATUS_ADD = new Set(["candidate", "probation", "established"]);
const ADMIN_STATUS_SET = new Set(["candidate", "probation", "established", "demoted"]); // set: retire goes through `retire`
const ADMIN_CLASS = new Set(["outlet", "hub", "institutional"]);
const ADMIN_PROBE_METHODS = new Set(["curl", "proxy"]);
const ADMIN_SET_FIELDS = new Set(["tier", "reach", "streams", "status", "class"]);

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
  "Access-Control-Allow-Headers": "Authorization, Content-Type",
  "Access-Control-Max-Age": "86400",
};

// Every session-carrying route (/auth/*, /submit, /propose, /readstate, /prefs, /admin/actions,
// /admin/snapshot) answers CORS only for the published site: the site origin gets echoed back,
// any other origin gets NO Access-Control-Allow-Origin at all (the preflight still returns 204).
// The bridge routes (/drain, /ack, /admin/drain, /admin/ack) keep `*` — they are server-to-server.
// PUT /admin/snapshot is site-origin-conditional here too (the bridge is not a browser, so its
// CORS is moot), which makes it the one bearer route that does not carry `*`.
function corsFor(request, path) {
  if (path !== "/readstate" && path !== "/prefs" && path !== "/submit" && path !== "/propose" &&
      path !== "/admin/actions" && path !== "/admin/snapshot" &&
      !path.startsWith("/auth/")) return CORS;
  const headers = {
    // /admin/snapshot is GET (session) + PUT (bearer); every other site-origin route is GET/POST.
    "Access-Control-Allow-Methods": path === "/admin/snapshot" ? "GET, PUT, OPTIONS" : "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin",
  };
  if (request.headers.get("Origin") === SITE_ORIGIN) {
    headers["Access-Control-Allow-Origin"] = SITE_ORIGIN;
  }
  return headers;
}

function json(body, status = 200, extra = {}, cors = CORS) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", ...cors, ...extra },
  });
}

function text(body, status, extra = {}) {
  return new Response(body, {
    status,
    headers: { "Content-Type": "text/plain; charset=utf-8", ...CORS, ...extra },
  });
}

// length-guarded constant-ish compare (bridge bearer; drain/ack only)
function bearerOk(request, env) {
  const expected = env.FEEDBACK_TOKEN;
  if (!expected) return false; // fail closed if unset
  const got = (request.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  if (got.length !== expected.length) return false;
  let diff = 0;
  for (let i = 0; i < got.length; i++) diff |= got.charCodeAt(i) ^ expected.charCodeAt(i);
  return diff === 0;
}

// passkey-registration invite (body field, not header). Same length-guarded
// constant-ish compare as bearerOk; fail closed if INVITE_TOKEN is unset.
function inviteOk(invite, env) {
  const expected = env.INVITE_TOKEN;
  if (!expected) return false;
  if (typeof invite !== "string" || invite.length !== expected.length) return false;
  let diff = 0;
  for (let i = 0; i < invite.length; i++) diff |= invite.charCodeAt(i) ^ expected.charCodeAt(i);
  return diff === 0;
}

function clip(v, n) {
  return typeof v === "string" ? v.slice(0, n) : v;
}

async function putRecord(env, rec) {
  // Key sorts by time so /drain returns roughly chronological order.
  await env.FEEDBACK_KV.put(`${KEY_PREFIX}${rec.ts}:${rec.id}`, JSON.stringify(rec));
}

// ---------------------------------------------------------------------------
// Sessions (KV `session:{token}` = {reader, created}, TTL 90 days, rolling)

function newSessionToken() {
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  return [...bytes].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function issueSession(env, reader, cred) {
  const token = newSessionToken();
  await env.FEEDBACK_KV.put(
    `session:${token}`,
    JSON.stringify({ reader, created: Date.now(), cred: typeof cred === "string" ? cred : null }),
    { expirationTtl: SESSION_TTL_S },
  );
  return token;
}

// Resolve the session Bearer, if any. Returns {token, reader, created, cred} or null. `cred` is
// the WebAuthn credential id that minted the session (null for sessions minted before 2026-09-13).
async function getSession(request, env) {
  const m = (request.headers.get("Authorization") || "").match(/^Bearer\s+([0-9a-f]{64})$/i);
  if (!m) return null;
  const token = m[1];
  const raw = await env.FEEDBACK_KV.get(`session:${token}`);
  if (raw == null) return null;
  let sess;
  try {
    sess = JSON.parse(raw);
  } catch {
    return null;
  }
  if (!sess || typeof sess.reader !== "string") return null;
  return {
    token,
    reader: sess.reader,
    created: typeof sess.created === "number" ? sess.created : 0,
    cred: typeof sess.cred === "string" ? sess.cred : null,
  };
}

// THE ADMIN IS ONE PASSKEY, NOT ONE READER. Every credential on this single-reader site maps to
// the same reader identity, so "a valid session" would let any passkey registered with the invite
// token retire sources. ADMIN_CRED_IDS (a comma-separated list of WebAuthn credential ids, set in
// wrangler.toml [vars]) names the only credential(s) whose sessions may touch /admin/*. A session
// minted before the id was recorded on it carries no `cred` and is refused until the reader signs
// in again. Fails closed when the var is unset.
function adminOk(sess, env) {
  const allowed = String(env.ADMIN_CRED_IDS || "").split(",").map((v) => v.trim()).filter(Boolean);
  return !!(sess && typeof sess.cred === "string" && sess.cred && allowed.includes(sess.cred));
}

// Rolling renewal: any authed use more than SESSION_ROLL_MS after the last roll
// re-mints the TTL + created, so the idle budget runs from the reader's last visit.
async function rollSession(env, sess) {
  if (Date.now() - sess.created <= SESSION_ROLL_MS) return;
  await env.FEEDBACK_KV.put(
    `session:${sess.token}`,
    JSON.stringify({ reader: sess.reader, created: Date.now(), cred: sess.cred || null }),
    { expirationTtl: SESSION_TTL_S },
  );
}

// ---------------------------------------------------------------------------
// WebAuthn helpers

// Pull the base64url challenge out of a register/login response's clientDataJSON.
function challengeFrom(response) {
  try {
    const bytes = isoBase64URL.toBuffer(response.response.clientDataJSON);
    const client = JSON.parse(new TextDecoder().decode(bytes));
    return typeof client.challenge === "string" && client.challenge ? client.challenge : null;
  } catch {
    return null;
  }
}

// Single-use challenge check: present in KV -> consume it; missing/expired -> reject.
async function consumeChallenge(env, kind, challenge) {
  const key = `chal:${kind}:${challenge}`;
  const found = await env.FEEDBACK_KV.get(key);
  if (found == null) return false;
  await env.FEEDBACK_KV.delete(key);
  return true;
}

// ---------------------------------------------------------------------------
// Handlers

async function handleSubmit(request, env, cors) {
  const sess = await getSession(request, env);
  if (!sess) return json({ error: "no session" }, 401, {}, cors);
  let p;
  try {
    p = await request.json();
  } catch {
    return json({ error: "invalid JSON body" }, 400, {}, cors);
  }
  const brief = p && p.brief;
  const vote = p && p.vote;
  if (typeof brief !== "string" || !brief) {
    return json({ error: "body must include a non-empty `brief` (post slug)" }, 400, {}, cors);
  }
  // 0 = retraction: the reader un-toggled a thumb, cancelling their prior vote on this
  // brief/story. The sink stays append-only — consumers (evaluator) apply last-write-wins
  // per (reader, brief, story_id).
  if (vote !== 1 && vote !== -1 && vote !== 0) {
    return json({ error: "`vote` must be 1, -1 or 0 (retract)" }, 400, {}, cors);
  }
  const reason = typeof p.reason === "string" ? p.reason : "";
  if (reason.length > MAX_REASON) {
    return json({ error: `reason too long (max ${MAX_REASON})` }, 400, {}, cors);
  }
  const storyId = typeof p.story_id === "string" && p.story_id ? p.story_id : null;
  if (storyId !== null && !STORY_ID_RE.test(storyId)) {
    return json({ error: "malformed story_id" }, 400, {}, cors);
  }
  const rec = {
    id: crypto.randomUUID(),
    ts: new Date().toISOString(),
    reader: clip(sess.reader, MAX_FIELD),
    brief: clip(brief, MAX_FIELD),
    story_id: storyId,
    vote,
    reason,
    surface: clip(typeof p.surface === "string" && p.surface ? p.surface : "web", MAX_FIELD),
  };
  await putRecord(env, rec);
  await rollSession(env, sess);
  return json({ ok: true, id: rec.id }, 200, {}, cors);
}

async function handlePropose(request, env, cors) {
  const sess = await getSession(request, env);
  if (!sess) return json({ error: "no session" }, 401, {}, cors);
  let p;
  try {
    p = await request.json();
  } catch {
    return json({ error: "invalid JSON body" }, 400, {}, cors);
  }
  const topic = p && p.topic;
  if (typeof topic !== "string" || !topic.trim()) {
    return json({ error: "body must include a non-empty `topic`" }, 400, {}, cors);
  }
  if (topic.length > MAX_TOPIC) {
    return json({ error: `topic too long (max ${MAX_TOPIC})` }, 400, {}, cors);
  }
  const detail = typeof p.detail === "string" ? p.detail : "";
  if (detail.length > MAX_REASON) {
    return json({ error: `detail too long (max ${MAX_REASON})` }, 400, {}, cors);
  }
  const rec = {
    id: crypto.randomUUID(),
    ts: new Date().toISOString(),
    kind: "proposal",
    topic: clip(topic.trim(), MAX_TOPIC),
    detail,
    surface: clip(typeof p.surface === "string" && p.surface ? p.surface : "web", MAX_FIELD),
  };
  await putRecord(env, rec);
  await rollSession(env, sess);
  return json({ ok: true, id: rec.id }, 200, {}, cors);
}

async function handleDrain(env) {
  const listed = await env.FEEDBACK_KV.list({ prefix: KEY_PREFIX, limit: DRAIN_LIMIT });
  const records = [];
  for (const k of listed.keys) {
    const v = await env.FEEDBACK_KV.get(k.name);
    if (v == null) continue;
    let rec;
    try {
      rec = JSON.parse(v);
    } catch {
      rec = { id: null, raw: v };
    }
    records.push({ key: k.name, ...rec });
  }
  return json({ count: records.length, truncated: listed.list_complete === false, records });
}

async function handleAck(request, env) {
  let p;
  try {
    p = await request.json();
  } catch {
    return json({ error: "invalid JSON body" }, 400);
  }
  const keys = p && p.keys;
  if (!Array.isArray(keys)) {
    return json({ error: "body must be { keys: [string, ...] }" }, 400);
  }
  let deleted = 0;
  for (const k of keys) {
    if (typeof k === "string" && k.startsWith(KEY_PREFIX)) {
      await env.FEEDBACK_KV.delete(k);
      deleted++;
    }
  }
  return json({ ok: true, deleted });
}

async function handleRegisterOptions(request, env, cors) {
  let p;
  try {
    p = await request.json();
  } catch {
    return json({ error: "invalid JSON body" }, 400, {}, cors);
  }
  if (!inviteOk(p && p.invite, env)) return json({ error: "bad invite" }, 403, {}, cors);
  const options = await generateRegistrationOptions({
    rpName: RP_NAME,
    rpID: RP_ID,
    userName: READER,
    userID: new TextEncoder().encode(READER), // stable: single-reader site
    userDisplayName: READER_DISPLAY,
    attestationType: "none",
    authenticatorSelection: { residentKey: "required", userVerification: "required" },
  });
  await env.FEEDBACK_KV.put(`chal:reg:${options.challenge}`, "1", { expirationTtl: CHALLENGE_TTL_S });
  return json(options, 200, {}, cors);
}

async function handleRegister(request, env, cors) {
  let p;
  try {
    p = await request.json();
  } catch {
    return json({ error: "invalid JSON body" }, 400, {}, cors);
  }
  if (!inviteOk(p && p.invite, env)) return json({ error: "bad invite" }, 403, {}, cors);
  const response = p.response;
  const challenge = response && challengeFrom(response);
  if (!challenge) return json({ error: "malformed response" }, 400, {}, cors);
  if (!(await consumeChallenge(env, "reg", challenge))) {
    return json({ error: "unknown challenge" }, 403, {}, cors);
  }
  let verification;
  try {
    verification = await verifyRegistrationResponse({
      response,
      expectedChallenge: challenge,
      expectedOrigin: SITE_ORIGIN,
      expectedRPID: RP_ID,
      requireUserVerification: true,
    });
  } catch {
    return json({ error: "verification failed" }, 403, {}, cors);
  }
  if (!verification.verified || !verification.registrationInfo) {
    return json({ error: "verification failed" }, 403, {}, cors);
  }
  const cred = verification.registrationInfo.credential;
  await env.FEEDBACK_KV.put(
    `cred:${cred.id}`,
    JSON.stringify({
      reader: READER,
      publicKey: isoBase64URL.fromBuffer(cred.publicKey),
      counter: cred.counter,
      transports: cred.transports || [],
    }),
  );
  const session = await issueSession(env, READER, cred.id);
  return json({ ok: true, session, reader: READER }, 200, {}, cors);
}

async function handleLoginOptions(request, env, cors) {
  // No allowCredentials: discoverable credentials only — the authenticator offers
  // whatever passkey it holds for the rpID.
  const options = await generateAuthenticationOptions({
    rpID: RP_ID,
    userVerification: "required",
  });
  await env.FEEDBACK_KV.put(`chal:auth:${options.challenge}`, "1", { expirationTtl: CHALLENGE_TTL_S });
  return json(options, 200, {}, cors);
}

async function handleLogin(request, env, cors) {
  let p;
  try {
    p = await request.json();
  } catch {
    return json({ error: "invalid JSON body" }, 400, {}, cors);
  }
  const response = p && p.response;
  if (!response || typeof response.id !== "string" || !response.id) {
    return json({ error: "malformed response" }, 400, {}, cors);
  }
  const challenge = challengeFrom(response);
  if (!challenge) return json({ error: "malformed response" }, 400, {}, cors);
  if (!(await consumeChallenge(env, "auth", challenge))) {
    return json({ error: "unknown challenge" }, 403, {}, cors);
  }
  const credRaw = await env.FEEDBACK_KV.get(`cred:${response.id}`);
  if (credRaw == null) return json({ error: "unknown credential" }, 403, {}, cors);
  let stored;
  try {
    stored = JSON.parse(credRaw);
  } catch {
    return json({ error: "unknown credential" }, 403, {}, cors);
  }
  let verification;
  try {
    verification = await verifyAuthenticationResponse({
      response,
      expectedChallenge: challenge,
      expectedOrigin: SITE_ORIGIN,
      expectedRPID: RP_ID,
      credential: {
        id: response.id,
        publicKey: isoBase64URL.toBuffer(stored.publicKey),
        counter: stored.counter,
        transports: stored.transports,
      },
      requireUserVerification: true,
    });
  } catch {
    return json({ error: "verification failed" }, 403, {}, cors);
  }
  if (!verification.verified) return json({ error: "verification failed" }, 403, {}, cors);
  stored.counter = verification.authenticationInfo.newCounter;
  await env.FEEDBACK_KV.put(`cred:${response.id}`, JSON.stringify(stored));
  const session = await issueSession(env, stored.reader, response.id);
  return json({ ok: true, session, reader: stored.reader }, 200, {}, cors);
}

async function handleReadstateGet(request, env, cors) {
  const sess = await getSession(request, env);
  if (!sess) return json({ error: "no session" }, 401, {}, cors);
  await rollSession(env, sess);
  const raw = await env.FEEDBACK_KV.get(`readstate:${sess.reader}`);
  let state = {};
  if (raw != null) {
    try {
      state = JSON.parse(raw) || {};
    } catch {
      state = {};
    }
  }
  return json({ reader: sess.reader, state }, 200, {}, cors);
}

async function handleReadstatePost(request, env, cors) {
  const sess = await getSession(request, env);
  if (!sess) return json({ error: "no session" }, 401, {}, cors);
  const body = await request.arrayBuffer();
  if (body.byteLength > STATE_MAX_BYTES) {
    return json({ error: `body too large (max ${STATE_MAX_BYTES} bytes)` }, 413, {}, cors);
  }
  let p;
  try {
    p = JSON.parse(new TextDecoder().decode(body));
  } catch {
    return json({ error: "invalid JSON body" }, 400, {}, cors);
  }
  const state = p && p.state;
  if (typeof state !== "object" || state === null || Array.isArray(state)) {
    return json({ error: "body must include an object `state`" }, 400, {}, cors);
  }
  const entries = Object.entries(state);
  if (entries.length > STATE_MAX_ENTRIES) {
    return json({ error: `too many entries (max ${STATE_MAX_ENTRIES})` }, 400, {}, cors);
  }

  const now = Date.now();
  const raw = await env.FEEDBACK_KV.get(`readstate:${sess.reader}`);
  let merged = {};
  if (raw != null) {
    try {
      merged = JSON.parse(raw) || {};
    } catch {
      merged = {};
    }
  }

  // LWW merge: higher ts wins, tie keeps the existing entry. Invalid entries are
  // skipped (counted), never fatal — one bad sid must not lose the rest of the batch.
  let changed = 0;
  let skipped = 0;
  for (const [sid, entry] of entries) {
    if (
      !SID_RE.test(sid) ||
      !entry || typeof entry !== "object" || Array.isArray(entry) ||
      typeof entry.ts !== "number" || !Number.isFinite(entry.ts) ||
      entry.ts <= 0 || entry.ts > now + STATE_MAX_SKEW_MS ||
      (entry.v !== 0 && entry.v !== 1)
    ) {
      skipped++;
      continue;
    }
    const cur = merged[sid];
    if (cur && typeof cur.ts === "number" && cur.ts >= entry.ts) continue;
    merged[sid] = { ts: entry.ts, v: entry.v };
    changed++;
  }

  // Age out anything (including tombstones) older than 90 days.
  const cutoff = now - STATE_MAX_AGE_MS;
  for (const sid of Object.keys(merged)) {
    const cur = merged[sid];
    if (!cur || typeof cur.ts !== "number" || cur.ts < cutoff) delete merged[sid];
  }

  await env.FEEDBACK_KV.put(`readstate:${sess.reader}`, JSON.stringify(merged));
  await rollSession(env, sess);
  return json({ ok: true, total: Object.keys(merged).length, changed, skipped }, 200, {}, cors);
}

// ---------------------------------------------------------------------------
// UI prefs (KV `prefs:{reader}` = {topics:[...], rs:""|"unread"|"read", ts}). Unlike read
// state, the selection is ONE complete statement of intent, so it merges whole-object by ts
// (LWW) rather than per-entry — a POST replaces the stored object iff its ts is newer.
// `rs` (added 2026-07-18) is the read-state FILTER selection (All/Unread/Read segmented
// toggle), roaming with the topic chips; an invalid value coerces to "" (All), never rejects.

const READ_FILTERS = new Set(["", "unread", "read"]);
const readFilterOf = (v) => (typeof v === "string" && READ_FILTERS.has(v) ? v : "");

async function handlePrefsGet(request, env, cors) {
  const sess = await getSession(request, env);
  if (!sess) return json({ error: "no session" }, 401, {}, cors);
  await rollSession(env, sess);
  const raw = await env.FEEDBACK_KV.get(`prefs:${sess.reader}`);
  let prefs = { topics: [], rs: "", ts: 0 };
  if (raw != null) {
    try {
      const p = JSON.parse(raw);
      if (p && Array.isArray(p.topics)) {
        prefs = { topics: p.topics, rs: readFilterOf(p.rs), ts: typeof p.ts === "number" ? p.ts : 0 };
      }
    } catch {
      // fall through to the empty default
    }
  }
  return json({ reader: sess.reader, prefs }, 200, {}, cors);
}

async function handlePrefsPost(request, env, cors) {
  const sess = await getSession(request, env);
  if (!sess) return json({ error: "no session" }, 401, {}, cors);
  const body = await request.arrayBuffer();
  if (body.byteLength > STATE_MAX_BYTES) {
    return json({ error: `body too large (max ${STATE_MAX_BYTES} bytes)` }, 413, {}, cors);
  }
  let p;
  try {
    p = JSON.parse(new TextDecoder().decode(body));
  } catch {
    return json({ error: "invalid JSON body" }, 400, {}, cors);
  }
  if (!p || !Array.isArray(p.topics)) {
    return json({ error: "body must include an array `topics`" }, 400, {}, cors);
  }
  if (p.topics.length > PREFS_MAX_TOPICS) {
    return json({ error: `too many topics (max ${PREFS_MAX_TOPICS})` }, 400, {}, cors);
  }
  const now = Date.now();
  const ts = typeof p.ts === "number" && Number.isFinite(p.ts) && p.ts > 0 && p.ts <= now + STATE_MAX_SKEW_MS ? p.ts : now;
  // Keep only well-formed, deduped topic keys — one bad entry drops itself, never the batch.
  const seen = new Set();
  const topics = [];
  for (const t of p.topics) {
    if (typeof t === "string" && TOPIC_KEY_RE.test(t) && !seen.has(t)) {
      seen.add(t);
      topics.push(t);
    }
  }

  const raw = await env.FEEDBACK_KV.get(`prefs:${sess.reader}`);
  let stored = null;
  if (raw != null) {
    try {
      stored = JSON.parse(raw);
    } catch {
      stored = null;
    }
  }
  const rs = readFilterOf(p.rs);

  const storedTs = stored && typeof stored.ts === "number" ? stored.ts : 0;
  let applied = false;
  if (ts > storedTs) {
    await env.FEEDBACK_KV.put(`prefs:${sess.reader}`, JSON.stringify({ topics, rs, ts }));
    applied = true;
  }
  await rollSession(env, sess);
  const current = applied
    ? { topics, rs, ts }
    : { topics: (stored && stored.topics) || [], rs: readFilterOf(stored && stored.rs), ts: storedTs };
  return json({ ok: true, applied, prefs: current }, 200, {}, cors);
}

// ---------------------------------------------------------------------------
// Source-registry admin (2026-09-13). The page reads a bridge-pushed snapshot and queues
// mutations; the bridge drains, applies them to sources/registry.yml, commits/pushes, then
// acks — the same two-phase pattern as feedback. The Worker only validates shape (§2.2 of the
// plan) and assigns id/ts/reader; apply.py on the Mac re-validates and enforces registry rules.

// Validate one queued action against §2.2. Returns { action } (a clean object with only known
// keys, reader pinned from the session) or { error } (a 400 message). Unknown keys are dropped.
function validateAction(p, reader) {
  if (!p || typeof p !== "object" || Array.isArray(p)) return { error: "body must be an action object" };
  if (!ADMIN_TYPES.has(p.type)) return { error: "type must be retire, restore, add or set" };
  if (typeof p.domain !== "string") return { error: "domain required" };
  const domain = p.domain.toLowerCase(); // schema is lowercase-only; normalize a typo'd case rather than 400
  if (!DOMAIN_RE.test(domain)) return { error: "malformed domain" };
  const action = { type: p.type, domain, reader };
  if (p.note !== undefined) {
    if (typeof p.note !== "string") return { error: "note must be a string" };
    if (p.note.length > ADMIN_MAX_NOTE) return { error: `note too long (max ${ADMIN_MAX_NOTE})` };
    action.note = p.note;
  }
  if (p.type === "add") {
    if (!ADMIN_TIERS.has(p.tier)) return { error: "add requires tier T1 or T2" };
    action.tier = p.tier;
    if (!Array.isArray(p.streams) || p.streams.length === 0) return { error: "add requires a non-empty streams array" };
    const streams = [];
    for (const s of p.streams) {
      if (!ADMIN_STREAMS.has(s)) return { error: `unknown stream: ${s}` };
      if (!streams.includes(s)) streams.push(s);
    }
    action.streams = streams;
    const reach = p.reach === undefined ? "direct" : p.reach; // default direct
    if (!ADMIN_REACH.has(reach)) return { error: "invalid reach" };
    action.reach = reach;
    const status = p.status === undefined ? "probation" : p.status; // default probation
    if (!ADMIN_STATUS_ADD.has(status)) return { error: "invalid status for add (candidate|probation|established)" };
    action.status = status;
    if (p.class !== undefined) {
      if (!ADMIN_CLASS.has(p.class)) return { error: "invalid class" };
      action.class = p.class;
    }
    if (p.probe !== undefined) {
      const probe = p.probe;
      if (!probe || typeof probe !== "object" || Array.isArray(probe)) return { error: "probe must be an object" };
      // Plan §2.2 shows probe.url as an https URL; require https (the reach->method coupling is apply.py's REACH_METHOD).
      if (typeof probe.url !== "string" || !/^https:\/\//.test(probe.url)) return { error: "probe.url must be an https URL" };
      if (!ADMIN_PROBE_METHODS.has(probe.method)) return { error: "probe.method must be curl or proxy" };
      action.probe = { url: probe.url, method: probe.method };
    }
  } else if (p.type === "set") {
    if (!ADMIN_SET_FIELDS.has(p.field)) return { error: "set field must be tier, reach, streams, status or class" };
    action.field = p.field;
    if (p.field === "streams") {
      if (!Array.isArray(p.value) || p.value.length === 0) return { error: "streams value must be a non-empty array" };
      const streams = [];
      for (const s of p.value) {
        if (!ADMIN_STREAMS.has(s)) return { error: `unknown stream: ${s}` };
        if (!streams.includes(s)) streams.push(s);
      }
      action.value = streams;
    } else {
      const allowed = p.field === "tier" ? ADMIN_TIERS
        : p.field === "reach" ? ADMIN_REACH
        : p.field === "status" ? ADMIN_STATUS_SET
        : ADMIN_CLASS;
      if (typeof p.value !== "string" || !allowed.has(p.value)) return { error: `invalid value for field ${p.field}` };
      action.value = p.value;
    }
  }
  // retire / restore need only { type, domain, note? } — already captured above.
  return { action };
}

async function handleAdminActionsPost(request, env, cors) {
  const sess = await getSession(request, env);
  if (!sess) return json({ error: "no session" }, 401, {}, cors);
  if (!adminOk(sess, env)) return json({ error: "not the admin" }, 403, {}, cors);
  const body = await request.arrayBuffer();
  if (body.byteLength > ADMIN_MAX_ACTION_BYTES) {
    return json({ error: `body too large (max ${ADMIN_MAX_ACTION_BYTES} bytes)` }, 413, {}, cors);
  }
  let p;
  try {
    p = JSON.parse(new TextDecoder().decode(body));
  } catch {
    return json({ error: "invalid JSON body" }, 400, {}, cors);
  }
  const v = validateAction(p, sess.reader);
  if (v.error) return json({ error: v.error }, 400, {}, cors);
  const id = crypto.randomUUID();
  const ts = new Date().toISOString();
  const action = { id, ts, ...v.action };
  // Key sorts by time so drain/GET return roughly chronological order.
  await env.FEEDBACK_KV.put(`${ADMIN_KEY_PREFIX}${ts}:${id}`, JSON.stringify(action));
  await rollSession(env, sess);
  return json({ ok: true, id, action }, 200, {}, cors);
}

async function handleAdminActionsGet(request, env, cors) {
  const sess = await getSession(request, env);
  if (!sess) return json({ error: "no session" }, 401, {}, cors);
  if (!adminOk(sess, env)) return json({ error: "not the admin" }, 403, {}, cors);
  const listed = await env.FEEDBACK_KV.list({ prefix: ADMIN_KEY_PREFIX, limit: DRAIN_LIMIT });
  const actions = [];
  for (const k of listed.keys) {
    const val = await env.FEEDBACK_KV.get(k.name);
    if (val == null) continue;
    let rec;
    try {
      rec = JSON.parse(val);
    } catch {
      rec = { raw: val };
    }
    actions.push({ key: k.name, ...rec });
  }
  await rollSession(env, sess);
  return json({ count: actions.length, actions }, 200, {}, cors);
}

async function handleAdminSnapshotGet(request, env, cors) {
  const sess = await getSession(request, env);
  if (!sess) return json({ error: "no session" }, 401, {}, cors);
  if (!adminOk(sess, env)) return json({ error: "not the admin" }, 403, {}, cors);
  const raw = await env.FEEDBACK_KV.get(ADMIN_SNAPSHOT_KEY);
  await rollSession(env, sess);
  if (raw == null) return json({ error: "no snapshot yet" }, 404, {}, cors);
  // Serve the stored string verbatim (it was stored after a JSON.parse round-trip proved it valid).
  return new Response(raw, {
    status: 200,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", ...cors },
  });
}

async function handleAdminSnapshotPut(request, env) {
  const body = await request.arrayBuffer();
  if (body.byteLength > ADMIN_MAX_SNAPSHOT_BYTES) {
    return json({ error: `snapshot too large (max ${ADMIN_MAX_SNAPSHOT_BYTES} bytes)` }, 413);
  }
  const str = new TextDecoder().decode(body);
  try {
    JSON.parse(str); // round-trip only proves validity; we store the string exactly as received
  } catch {
    return json({ error: "invalid JSON body" }, 400);
  }
  const bytes = body.byteLength;
  await env.FEEDBACK_KV.put(ADMIN_SNAPSHOT_KEY, str);
  await env.FEEDBACK_KV.put(ADMIN_SNAPSHOT_META_KEY, JSON.stringify({ ts: new Date().toISOString(), bytes }));
  return json({ ok: true, bytes });
}

async function handleAdminDrain(env) {
  const listed = await env.FEEDBACK_KV.list({ prefix: ADMIN_KEY_PREFIX, limit: DRAIN_LIMIT });
  const records = [];
  for (const k of listed.keys) {
    const v = await env.FEEDBACK_KV.get(k.name);
    if (v == null) continue;
    let rec;
    try {
      rec = JSON.parse(v);
    } catch {
      rec = { id: null, raw: v };
    }
    records.push({ key: k.name, ...rec });
  }
  return json({ count: records.length, truncated: listed.list_complete === false, records });
}

async function handleAdminAck(request, env) {
  let p;
  try {
    p = await request.json();
  } catch {
    return json({ error: "invalid JSON body" }, 400);
  }
  const keys = p && p.keys;
  if (!Array.isArray(keys)) {
    return json({ error: "body must be { keys: [string, ...] }" }, 400);
  }
  // Only `adm:` keys are deletable here — an `fb:` key handed to this route is a no-op, so a
  // confused caller can never delete feedback records through the admin ack (and vice versa).
  let deleted = 0;
  for (const k of keys) {
    if (typeof k === "string" && k.startsWith(ADMIN_KEY_PREFIX)) {
      await env.FEEDBACK_KV.delete(k);
      deleted++;
    }
  }
  return json({ ok: true, deleted });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";
    const cors = corsFor(request, path);
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors });
    }

    if (path === "/submit") {
      if (request.method !== "POST") return json({ error: "method not allowed" }, 405, {}, cors);
      return handleSubmit(request, env, cors);
    }
    if (path === "/propose") {
      if (request.method !== "POST") return json({ error: "method not allowed" }, 405, {}, cors);
      return handlePropose(request, env, cors);
    }
    if (path === "/drain") {
      if (request.method !== "GET") return text("method not allowed", 405);
      if (!bearerOk(request, env)) return text("unauthorized", 401);
      return handleDrain(env);
    }
    if (path === "/ack") {
      if (request.method !== "POST") return text("method not allowed", 405);
      if (!bearerOk(request, env)) return text("unauthorized", 401);
      return handleAck(request, env);
    }
    if (path === "/auth/register-options") {
      if (request.method !== "POST") return json({ error: "method not allowed" }, 405, {}, cors);
      return handleRegisterOptions(request, env, cors);
    }
    if (path === "/auth/register") {
      if (request.method !== "POST") return json({ error: "method not allowed" }, 405, {}, cors);
      return handleRegister(request, env, cors);
    }
    if (path === "/auth/login-options") {
      if (request.method !== "POST") return json({ error: "method not allowed" }, 405, {}, cors);
      return handleLoginOptions(request, env, cors);
    }
    if (path === "/auth/login") {
      if (request.method !== "POST") return json({ error: "method not allowed" }, 405, {}, cors);
      return handleLogin(request, env, cors);
    }
    if (path === "/readstate") {
      if (request.method === "GET") return handleReadstateGet(request, env, cors);
      if (request.method === "POST") return handleReadstatePost(request, env, cors);
      return json({ error: "method not allowed" }, 405, {}, cors);
    }
    if (path === "/prefs") {
      if (request.method === "GET") return handlePrefsGet(request, env, cors);
      if (request.method === "POST") return handlePrefsPost(request, env, cors);
      return json({ error: "method not allowed" }, 405, {}, cors);
    }
    // Source-registry admin: session-gated actions/snapshot for the /admin/ page, bearer-gated
    // drain/ack/snapshot-push for the Mac bridge.
    if (path === "/admin/actions") {
      if (request.method === "GET") return handleAdminActionsGet(request, env, cors);
      if (request.method === "POST") return handleAdminActionsPost(request, env, cors);
      return json({ error: "method not allowed" }, 405, {}, cors);
    }
    if (path === "/admin/snapshot") {
      if (request.method === "GET") return handleAdminSnapshotGet(request, env, cors);
      if (request.method === "PUT") {
        if (!bearerOk(request, env)) return text("unauthorized", 401);
        return handleAdminSnapshotPut(request, env);
      }
      return json({ error: "method not allowed" }, 405, {}, cors);
    }
    if (path === "/admin/drain") {
      if (request.method !== "GET") return text("method not allowed", 405);
      if (!bearerOk(request, env)) return text("unauthorized", 401);
      return handleAdminDrain(env);
    }
    if (path === "/admin/ack") {
      if (request.method !== "POST") return text("method not allowed", 405);
      if (!bearerOk(request, env)) return text("unauthorized", 401);
      return handleAdminAck(request, env);
    }
    return text("not found", 404);
  },
};
