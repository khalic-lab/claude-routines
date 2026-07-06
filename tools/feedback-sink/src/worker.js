// feedback-sink: capture reader feedback (thumbs +/- + optional reason) AND brief
// proposals from the published Jekyll site, hold them in Cloudflare KV, and let the
// local bridge drain them into the git repo on its cron tick.
//
// Routes:
//   POST /submit   (site key)  -- the brief page widget posts one feedback record.
//   POST /propose  (site key)  -- the home page form posts one brief proposal.
//   GET  /drain    (bearer)    -- list queued records (does NOT delete). Bridge reads.
//   POST /ack      (bearer)    -- delete the given KV keys. Bridge calls AFTER commit+push.
//
// Public writes (/submit, /propose) require the shared SITE KEY in the `X-Widget-Key`
// header — the website password, set as the Worker secret WIDGET_KEY. It is a SHARED
// secret (no per-user identity): anyone given the password can write; rotate the secret
// to revoke. It is entered by the visitor and kept in their browser localStorage, never
// baked into the page source. Privileged reads/deletes (/drain, /ack) use the separate
// bearer FEEDBACK_TOKEN. Both write kinds share the `fb:` KV prefix so one drain/ack
// handles them; the bridge routes by `kind` on write (proposal -> proposals/).
//
// Twin of tools/embed-proxy. Needs KV bound as FEEDBACK_KV, secret FEEDBACK_TOKEN
// (drain/ack bearer), and secret WIDGET_KEY (the shared site password). See README.

const MAX_REASON = 2000; // chars of free-text reason / proposal detail
const MAX_TOPIC = 300; // chars of a proposal topic line
const MAX_FIELD = 200; // chars for brief / story_id / surface
const DRAIN_LIMIT = 200; // records per drain (n=few: a day's writes are a handful)
const KEY_PREFIX = "fb:";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
  "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Widget-Key",
  "Access-Control-Max-Age": "86400",
};

function json(body, status = 200, extra = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", ...CORS, ...extra },
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

function clip(v, n) {
  return typeof v === "string" ? v.slice(0, n) : v;
}

async function putRecord(env, rec) {
  // Key sorts by time so /drain returns roughly chronological order.
  await env.FEEDBACK_KV.put(`${KEY_PREFIX}${rec.ts}:${rec.id}`, JSON.stringify(rec));
}

async function handleSubmit(request, env) {
  if (!keyOk(request, env)) return text("locked: site key required", 403);
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
    reader: clip(typeof p.reader === "string" && p.reader ? p.reader : "rafael", MAX_FIELD),
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

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS });
    }
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";

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
    return text("not found", 404);
  },
};
