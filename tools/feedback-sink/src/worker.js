// feedback-sink: capture reader thumbs +/- and an optional free-text reason from the
// published Jekyll briefs, hold them in Cloudflare KV, and let the local bridge drain
// them into the git repo (feedback/*.jsonl) on its existing cron tick.
//
// Three routes:
//   POST /submit  (public, CORS)  -- the brief page widget posts one feedback record.
//                                    No bearer: a browser cannot keep one secret. The
//                                    real defense is shape caps + the downstream HUMAN
//                                    gate (the Weekly Evaluator). Optional WIDGET_KEY
//                                    deters drive-by bots (deterrence, not security).
//   GET  /drain   (bearer)        -- list queued records (does NOT delete). Bridge reads.
//   POST /ack     (bearer)        -- delete the given KV keys. Bridge calls AFTER it has
//                                    committed+pushed, so a missed tick neither loses nor
//                                    double-commits (two-phase, delete-on-ack).
//
// Twin of tools/embed-proxy; same CORS/json/text helper shape. Needs a KV namespace
// bound as FEEDBACK_KV and a secret FEEDBACK_TOKEN (see README).

const MAX_REASON = 2000; // chars of free-text reason
const MAX_FIELD = 200; // chars for brief / story_id / surface
const DRAIN_LIMIT = 200; // records per drain (n=1: a day's taps are a handful)
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

// length-guarded constant-ish compare (bridge bearer; a real secret on the Mac + Worker)
function bearerOk(request, env) {
  const expected = env.FEEDBACK_TOKEN;
  if (!expected) return false; // fail closed if unset
  const got = (request.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  if (got.length !== expected.length) return false;
  let diff = 0;
  for (let i = 0; i < got.length; i++) diff |= got.charCodeAt(i) ^ expected.charCodeAt(i);
  return diff === 0;
}

function clip(v, n) {
  return typeof v === "string" ? v.slice(0, n) : v;
}

async function handleSubmit(request, env) {
  // Optional deterrence key (not a secret; visible in the widget JS).
  if (env.WIDGET_KEY && (request.headers.get("X-Widget-Key") || "") !== env.WIDGET_KEY) {
    return text("forbidden", 403);
  }
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
  if (vote !== 1 && vote !== -1) {
    return json({ error: "`vote` must be 1 or -1" }, 400);
  }
  const reason = typeof p.reason === "string" ? p.reason : "";
  if (reason.length > MAX_REASON) {
    return json({ error: `reason too long (max ${MAX_REASON})` }, 400);
  }
  const id = crypto.randomUUID();
  const ts = new Date().toISOString();
  const rec = {
    id,
    ts,
    reader: clip(typeof p.reader === "string" && p.reader ? p.reader : "rafael", MAX_FIELD),
    brief: clip(brief, MAX_FIELD),
    story_id: typeof p.story_id === "string" && p.story_id ? clip(p.story_id, MAX_FIELD) : null,
    vote,
    reason,
    surface: clip(typeof p.surface === "string" && p.surface ? p.surface : "web", MAX_FIELD),
  };
  // Key sorts by time so /drain returns roughly chronological order.
  await env.FEEDBACK_KV.put(`${KEY_PREFIX}${ts}:${id}`, JSON.stringify(rec));
  return json({ ok: true, id });
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
