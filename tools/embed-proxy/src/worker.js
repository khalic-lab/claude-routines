// embed-proxy: embeddings + the Phase-2 analytical plane, one allowlisted hostname.
//
//   POST /               { texts: [...] } -> { model, dim, embeddings }   (UNCHANGED contract —
//                        the compose-time dedup path; tools/dedup/dedup.py calls this)
//   POST /plane/ingest   baked artifact (see FORMAT below) -> stored in KV  (publish tail pushes
//                        after every edition via tools/plane/bake.py --push)
//   POST /plane/search   { text, k? }  -> nearest stories (embeds the query in-worker: one call)
//   POST /plane/related  { key, k? }   -> nearest to an existing story (sid | url | legacy id)
//   POST /plane/thread   { key }       -> a developing story line, oldest -> newest
//   POST /plane/entities { days? }     -> entity graph nodes
//   POST /plane/beats    { days? }     -> stories per beat per ISO week
//   POST /plane/sources  { days? }     -> domain concentration
//   POST /plane/stats    {}            -> corpus totals
//
// Everything requires the same bearer (Worker secret EMBED_TOKEN): the host is public,
// the token gates Workers-AI spend and keeps the corpus quiet. The plane lives on THIS
// worker because the routine sandbox's egress allowlist enumerates exact hostnames — a new
// *.workers.dev host would be unreachable from the routines; this one already is reachable.
//
// FORMAT (built by tools/plane/bake.py, one KV value `plane:v1`):
//   bytes 0-7    magic "PLANEv1\0"
//   bytes 8-11   uint32 LE meta_len
//   then         meta JSON (utf8): { n, dim, ts, norms: [n floats], stories: [n compact records] }
//   then         n * dim float32 LE vectors, row-major, same order as meta.stories
//
// The parsed artifact is cached per isolate for 5 minutes (the corpus changes ~3x/day).

const MODEL = "@cf/baai/bge-m3";
const DIM = 1024;
const MAX_TEXTS = 128; // a day's candidates across any one brief is well under this
const MAX_TOTAL_CHARS = 64 * 1024; // guard against oversized bodies
const PLANE_KEY = "plane:v1";
const PLANE_MAGIC = "PLANEv1\0";
const PLANE_MAX_BYTES = 24 * 1024 * 1024; // KV value cap is 25MB; refuse before storing garbage
const PLANE_CACHE_MS = 5 * 60 * 1000;

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Authorization, Content-Type",
  "Access-Control-Max-Age": "86400",
};

function json(body, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      ...CORS,
      ...extraHeaders,
    },
  });
}

function text(body, status, extraHeaders = {}) {
  return new Response(body, {
    status,
    headers: { "Content-Type": "text/plain; charset=utf-8", ...CORS, ...extraHeaders },
  });
}

function authorized(request, env) {
  const expected = env.EMBED_TOKEN;
  if (!expected) return false; // fail closed if the secret isn't configured
  const got = (request.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  // length-guarded constant-ish comparison
  if (got.length !== expected.length) return false;
  let diff = 0;
  for (let i = 0; i < got.length; i++) diff |= got.charCodeAt(i) ^ expected.charCodeAt(i);
  return diff === 0;
}

// ---------------------------------------------------------------------------- embeddings ----
async function handleEmbed(request, env) {
  let payload;
  try {
    payload = await request.json();
  } catch {
    return json({ error: "invalid JSON body" }, 400);
  }

  const texts = payload && payload.texts;
  if (!Array.isArray(texts) || texts.length === 0) {
    return json({ error: "body must be { texts: [non-empty array of strings] }" }, 400);
  }
  if (texts.length > MAX_TEXTS) {
    return json({ error: `too many texts (max ${MAX_TEXTS})` }, 400);
  }
  if (!texts.every((t) => typeof t === "string")) {
    return json({ error: "all texts must be strings" }, 400);
  }
  const totalChars = texts.reduce((n, t) => n + t.length, 0);
  if (totalChars > MAX_TOTAL_CHARS) {
    return json({ error: `body too large (max ${MAX_TOTAL_CHARS} chars)` }, 400);
  }

  try {
    const result = await env.AI.run(MODEL, { text: texts });
    // Workers AI BGE models return { shape: [n, dim], data: number[][] }.
    const embeddings = result && result.data;
    if (!Array.isArray(embeddings) || embeddings.length !== texts.length) {
      return json({ error: "unexpected embedding response shape" }, 502);
    }
    return json({ model: "bge-m3", dim: DIM, embeddings });
  } catch (e) {
    return json({ error: "embedding failed", detail: String(e && e.message || e) }, 502);
  }
}

// ---------------------------------------------------------------------------- plane ---------
let PLANE = null; // per-isolate cache: { at, meta, vecs (Float32Array) }

function parseArtifact(buf) {
  const bytes = new Uint8Array(buf);
  if (bytes.length < 12) throw new Error("artifact too small");
  const magic = new TextDecoder().decode(bytes.slice(0, 8));
  if (magic !== PLANE_MAGIC) throw new Error("bad magic");
  const metaLen = new DataView(buf).getUint32(8, true);
  if (12 + metaLen > bytes.length) throw new Error("meta_len overruns artifact");
  const meta = JSON.parse(new TextDecoder().decode(bytes.slice(12, 12 + metaLen)));
  if (!meta || !Array.isArray(meta.stories) || !Array.isArray(meta.norms) ||
      meta.norms.length !== meta.stories.length) {
    throw new Error("meta missing/mismatched stories/norms");
  }
  const n = meta.stories.length;
  const dim = meta.dim || DIM;
  const vecBytes = bytes.length - 12 - metaLen;
  if (vecBytes !== n * dim * 4) throw new Error(`vector block is ${vecBytes} bytes, want ${n * dim * 4}`);
  // Float32Array needs 4-byte alignment; the meta JSON may leave us unaligned — slice copies.
  const aligned = buf.slice(12 + metaLen);
  return { meta, vecs: new Float32Array(aligned) };
}

async function loadPlane(env) {
  if (PLANE && Date.now() - PLANE.at < PLANE_CACHE_MS) return PLANE;
  const buf = await env.PLANE_KV.get(PLANE_KEY, "arrayBuffer");
  if (!buf) return null;
  const { meta, vecs } = parseArtifact(buf);
  PLANE = { at: Date.now(), meta, vecs };
  return PLANE;
}

function cosineTop(plane, qvec, k, excludeIdx = -1) {
  const { meta, vecs } = plane;
  const dim = meta.dim || DIM;
  let qnorm = 0;
  for (let i = 0; i < qvec.length; i++) qnorm += qvec[i] * qvec[i];
  qnorm = Math.sqrt(qnorm) || 1;
  const scored = [];
  for (let s = 0; s < meta.stories.length; s++) {
    if (s === excludeIdx || !meta.norms[s]) continue;
    const off = s * dim;
    let dot = 0;
    for (let i = 0; i < dim; i++) dot += qvec[i] * vecs[off + i];
    scored.push([dot / (qnorm * meta.norms[s]), s]);
  }
  scored.sort((a, b) => b[0] - a[0]);
  return scored.slice(0, k).map(([sim, s]) => ({ sim: Math.round(sim * 1000) / 1000, ...meta.stories[s] }));
}

function findIdx(meta, key) {
  for (let i = 0; i < meta.stories.length; i++) {
    const st = meta.stories[i];
    if (st.sid === key || st.url === key || (st.legacy_ids || []).includes(key)) return i;
  }
  return -1;
}

function sinceStr(days) {
  // coerce + clamp: NaN/overflow days would make toISOString throw (RangeError -> 500)
  const n = Number(days);
  const d = Number.isFinite(n) && n > 0 ? Math.min(n, 3.65e6) : 36500;
  return new Date(Date.now() - d * 864e5).toISOString().slice(0, 10);
}

async function handlePlane(path, request, env) {
  if (path === "/plane/ingest") {
    const buf = await request.arrayBuffer();
    if (buf.byteLength > PLANE_MAX_BYTES) {
      return json({ error: `artifact too large (max ${PLANE_MAX_BYTES} bytes)` }, 413);
    }
    let parsed;
    try {
      parsed = parseArtifact(buf);
    } catch (e) {
      return json({ error: "invalid artifact", detail: String(e && e.message || e) }, 400);
    }
    await env.PLANE_KV.put(PLANE_KEY, buf);
    PLANE = { at: Date.now(), meta: parsed.meta, vecs: parsed.vecs };
    return json({ ok: true, stories: parsed.meta.stories.length, ts: parsed.meta.ts || null });
  }

  let body = {};
  try {
    body = await request.json();
  } catch {
    // every read route tolerates an empty body
  }
  // JSON `null`/scalars/arrays parse successfully — normalize so body.* never throws
  if (!body || typeof body !== "object" || Array.isArray(body)) body = {};

  const plane = await loadPlane(env);
  if (!plane) return json({ error: "plane not ingested yet — run tools/plane/bake.py --push" }, 503);
  const { meta } = plane;
  const k = Math.min(Math.max(1, Number(body.k) || 10), 50);

  if (path === "/plane/search") {
    if (typeof body.text !== "string" || !body.text.trim()) {
      return json({ error: "body must include text" }, 400);
    }
    let qvec;
    try {
      const result = await env.AI.run(MODEL, { text: [body.text.slice(0, 2000)] });
      qvec = result && result.data && result.data[0];
    } catch (e) {
      return json({ error: "query embedding failed", detail: String(e && e.message || e) }, 502);
    }
    if (!Array.isArray(qvec)) return json({ error: "query embedding failed" }, 502);
    return json({ ts: meta.ts, hits: cosineTop(plane, qvec, k) });
  }

  if (path === "/plane/related") {
    const idx = findIdx(meta, body.key || "");
    if (idx < 0) return json({ error: `no story matches ${JSON.stringify(body.key || "")}` }, 404);
    const dim = meta.dim || DIM;
    const qvec = plane.vecs.subarray(idx * dim, (idx + 1) * dim);
    const anchorThread = meta.stories[idx].thread_id || null;
    const hits = cosineTop(plane, qvec, k, idx).map((h) => ({
      ...h,
      edge: anchorThread && h.thread_id === anchorThread ? "same-thread" : "",
    }));
    return json({ ts: meta.ts, anchor: meta.stories[idx], hits });
  }

  if (path === "/plane/thread") {
    const idx = findIdx(meta, body.key || "");
    const tid = (idx >= 0 && meta.stories[idx].thread_id) || body.key;
    const members = meta.stories
      .filter((s) => s.thread_id === tid)
      .sort((a, b) => (a.date || "").localeCompare(b.date || ""));
    return json({ ts: meta.ts, thread_id: tid, stories: members });
  }

  if (path === "/plane/entities") {
    const since = sinceStr(body.days || 90);
    // null prototype: an entity literally named "__proto__"/"toString" (they're LLM-written
    // strings) would otherwise resolve to an inherited truthy value and crash the aggregation
    const agg = Object.create(null);
    for (const s of meta.stories) {
      if ((s.date || "") < since) continue;
      for (const e of s.entities || []) {
        const a = (agg[e] = agg[e] || { entity: e, stories: 0, first: s.date, last: s.date, streams: new Set() });
        a.stories += 1;
        if (s.date < a.first) a.first = s.date;
        if (s.date > a.last) a.last = s.date;
        a.streams.add(s.stream || "");
      }
    }
    const rows = Object.values(agg)
      .sort((a, b) => b.stories - a.stories || (b.last || "").localeCompare(a.last || ""))
      .slice(0, 30)
      .map((a) => ({ ...a, streams: [...a.streams].sort() }));
    return json({ ts: meta.ts, entities: rows });
  }

  if (path === "/plane/beats") {
    const since = sinceStr(body.days || 30);
    const counts = Object.create(null);
    for (const s of meta.stories) {
      if ((s.date || "") < since || !s.date) continue;
      const d = new Date(s.date + "T00:00:00Z");
      if (isNaN(d.getTime())) continue; // malformed date in a crafted artifact must not 500
      d.setUTCDate(d.getUTCDate() - ((d.getUTCDay() + 6) % 7)); // monday of that week
      const week = d.toISOString().slice(5, 10);
      for (const b of s.topics || []) counts[`${week} ${b}`] = (counts[`${week} ${b}`] || 0) + 1;
    }
    const rows = Object.entries(counts)
      .map(([kk, n]) => ({ week: kk.split(" ")[0], beat: kk.split(" ")[1], stories: n }))
      .sort((a, b) => b.week.localeCompare(a.week) || b.stories - a.stories);
    return json({ ts: meta.ts, beats: rows });
  }

  if (path === "/plane/sources") {
    const since = sinceStr(body.days || 30);
    const agg = Object.create(null); // same prototype-name guard as /plane/entities
    for (const s of meta.stories) {
      if ((s.date || "") < since || !s.source_domain) continue;
      const a = (agg[s.source_domain] = agg[s.source_domain] || { source_domain: s.source_domain, stories: 0, streams: new Set() });
      a.stories += 1;
      a.streams.add(s.stream || "");
    }
    const rows = Object.values(agg)
      .sort((a, b) => b.stories - a.stories)
      .slice(0, 25)
      .map((a) => ({ ...a, streams: [...a.streams].sort() }));
    return json({ ts: meta.ts, sources: rows });
  }

  if (path === "/plane/stats") {
    const threads = Object.create(null); // thread ids are slugified strings — same guard
    let withVec = 0;
    for (let i = 0; i < meta.stories.length; i++) {
      if (meta.norms[i]) withVec += 1;
      const tid = meta.stories[i].thread_id;
      if (tid) threads[tid] = (threads[tid] || 0) + 1;
    }
    const dates = meta.stories.map((s) => s.date || "").filter(Boolean).sort();
    return json({
      ts: meta.ts,
      stories: meta.stories.length,
      with_vectors: withVec,
      threads_developing: Object.values(threads).filter((n) => n > 1).length,
      since: dates[0] || null,
      through: dates[dates.length - 1] || null,
    });
  }

  return text("not found", 404);
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS });
    }
    if (request.method !== "POST") {
      return text("method not allowed", 405);
    }
    if (!authorized(request, env)) {
      return text("unauthorized", 401);
    }
    const path = new URL(request.url).pathname.replace(/\/+$/, "") || "/";
    if (path === "/") return handleEmbed(request, env);
    if (path.startsWith("/plane/")) {
      if (!env.PLANE_KV) return json({ error: "PLANE_KV binding not configured" }, 503);
      return handlePlane(path, request, env);
    }
    return text("not found", 404);
  },
};
