// feedback-sink: capture reader feedback (thumbs +/- + optional reason) AND brief
// proposals from the published Jekyll site, hold them in Cloudflare KV, and let the
// local bridge drain them into the git repo on its cron tick. Since 2026-07-10 it is
// also the account backend: passkey (WebAuthn) auth + per-reader read-state sync.
//
// Routes:
//   POST /submit                 (site key)  -- the brief page widget posts one feedback record.
//   POST /propose                (site key)  -- the home page form posts one brief proposal.
//   GET  /drain                  (bearer)    -- list queued records (does NOT delete). Bridge reads.
//   POST /ack                    (bearer)    -- delete the given KV keys. Bridge calls AFTER commit+push.
//   POST /auth/register-options  (invite)    -- WebAuthn registration options (invite-gated).
//   POST /auth/register          (invite)    -- verify attestation, store credential, issue session.
//   POST /auth/login-options     (public)    -- WebAuthn authentication options (discoverable cred).
//   POST /auth/login             (public)    -- verify assertion, issue session.
//   GET  /readstate              (session)   -- the reader's read-state map {sid:{ts,v}}.
//   POST /readstate              (session)   -- LWW-merge a read-state delta into KV.
//
// Public writes (/submit, /propose) require the shared SITE KEY in the `X-Widget-Key`
// header — the website password, set as the Worker secret WIDGET_KEY. It is a SHARED
// secret (no per-user identity): anyone given the password can write; rotate the secret
// to revoke. It is entered by the visitor and kept in their browser localStorage, never
// baked into the page source. Privileged reads/deletes (/drain, /ack) use the separate
// bearer FEEDBACK_TOKEN. Both write kinds share the `fb:` KV prefix so one drain/ack
// handles them; the bridge routes by `kind` on write (proposal -> proposals/).
//
// Passkeys: registration is gated by the Worker secret INVITE_TOKEN (fail closed if
// unset). Credentials (`cred:`), sessions (`session:`), single-use challenges (`chal:`)
// and read state (`readstate:`) all live in the same FEEDBACK_KV — none of those
// prefixes collide with `fb:` so drain/ack never sees them. /auth/* and /readstate
// answer CORS only for the published site origin; everything else keeps `*`.
//
// Twin of tools/embed-proxy. Needs KV bound as FEEDBACK_KV, secret FEEDBACK_TOKEN
// (drain/ack bearer), secret WIDGET_KEY (the shared site password), and secret
// INVITE_TOKEN (passkey registration invite). See README.

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
const SESSION_ROLL_MS = 30 * 24 * 3600 * 1000; // re-mint TTL when a used session is older than this
const STATE_MAX_BYTES = 65536; // raw /readstate POST body cap
const STATE_MAX_ENTRIES = 2000; // entries per /readstate POST
const STATE_MAX_AGE_MS = 90 * 24 * 3600 * 1000; // merged entries older than this are dropped
const STATE_MAX_SKEW_MS = 86400000; // accept ts up to one day in the future
const SID_RE = /^st-[0-9a-f]{12}$/; // story ids from the story store

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
  "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Widget-Key",
  "Access-Control-Max-Age": "86400",
};

// /auth/* and /readstate carry a real session, so they answer CORS only for the
// published site: the site origin gets echoed back, any other origin gets NO
// Access-Control-Allow-Origin at all (the preflight still returns 204).
function corsFor(request, path) {
  if (path !== "/readstate" && !path.startsWith("/auth/")) return CORS;
  const headers = {
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Widget-Key",
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

// shared site password for public writes (sent in X-Widget-Key). Fail closed if unset.
function keyOk(request, env) {
  const expected = env.WIDGET_KEY;
  if (!expected) return false;
  return (request.headers.get("X-Widget-Key") || "") === expected;
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

async function issueSession(env, reader) {
  const token = newSessionToken();
  await env.FEEDBACK_KV.put(
    `session:${token}`,
    JSON.stringify({ reader, created: Date.now() }),
    { expirationTtl: SESSION_TTL_S },
  );
  return token;
}

// Resolve the session Bearer, if any. Returns {token, reader, created} or null.
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
  return { token, reader: sess.reader, created: typeof sess.created === "number" ? sess.created : 0 };
}

// Rolling renewal: a session used for readstate after >30 days gets a fresh TTL + created.
async function rollSession(env, sess) {
  if (Date.now() - sess.created <= SESSION_ROLL_MS) return;
  await env.FEEDBACK_KV.put(
    `session:${sess.token}`,
    JSON.stringify({ reader: sess.reader, created: Date.now() }),
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

async function handleSubmit(request, env) {
  if (!keyOk(request, env)) return text("locked: site key required", 403);
  // A valid passkey session pins the reader identity; without one the behavior
  // is exactly the pre-accounts one (body `reader` field, default "rafael").
  const sess = await getSession(request, env);
  let p;
  try {
    p = await request.json();
  } catch {
    return json({ error: "invalid JSON body" }, 400);
  }
  const brief = p && p.brief;
  const vote = p && p.vote;
  if (typeof brief !== "string" || !brief) {
    return json({ error: "body must include a non-empty `brief` (post slug)" }, 400);
  }
  // 0 = retraction: the reader un-toggled a thumb, cancelling their prior vote on this
  // brief/story. The sink stays append-only — consumers (evaluator) apply last-write-wins
  // per (reader, brief, story_id).
  if (vote !== 1 && vote !== -1 && vote !== 0) {
    return json({ error: "`vote` must be 1, -1 or 0 (retract)" }, 400);
  }
  const reason = typeof p.reason === "string" ? p.reason : "";
  if (reason.length > MAX_REASON) {
    return json({ error: `reason too long (max ${MAX_REASON})` }, 400);
  }
  const rec = {
    id: crypto.randomUUID(),
    ts: new Date().toISOString(),
    reader: clip(sess ? sess.reader : typeof p.reader === "string" && p.reader ? p.reader : "rafael", MAX_FIELD),
    brief: clip(brief, MAX_FIELD),
    story_id: typeof p.story_id === "string" && p.story_id ? clip(p.story_id, MAX_FIELD) : null,
    vote,
    reason,
    surface: clip(typeof p.surface === "string" && p.surface ? p.surface : "web", MAX_FIELD),
  };
  await putRecord(env, rec);
  return json({ ok: true, id: rec.id });
}

async function handlePropose(request, env) {
  if (!keyOk(request, env)) return text("locked: site key required", 403);
  let p;
  try {
    p = await request.json();
  } catch {
    return json({ error: "invalid JSON body" }, 400);
  }
  const topic = p && p.topic;
  if (typeof topic !== "string" || !topic.trim()) {
    return json({ error: "body must include a non-empty `topic`" }, 400);
  }
  if (topic.length > MAX_TOPIC) {
    return json({ error: `topic too long (max ${MAX_TOPIC})` }, 400);
  }
  const detail = typeof p.detail === "string" ? p.detail : "";
  if (detail.length > MAX_REASON) {
    return json({ error: `detail too long (max ${MAX_REASON})` }, 400);
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
  return json({ ok: true, id: rec.id });
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
  const session = await issueSession(env, READER);
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
  const session = await issueSession(env, stored.reader);
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

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";
    const cors = corsFor(request, path);
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors });
    }

    if (path === "/submit") {
      if (request.method !== "POST") return text("method not allowed", 405);
      return handleSubmit(request, env);
    }
    if (path === "/propose") {
      if (request.method !== "POST") return text("method not allowed", 405);
      return handlePropose(request, env);
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
    return text("not found", 404);
  },
};
