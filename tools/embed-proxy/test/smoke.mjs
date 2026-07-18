// Smoke tests for embed-proxy v2 (embeddings + /plane/*). Node stdlib only:
//   node test/smoke.mjs
// Stubs env.AI (deterministic vectors) and env.PLANE_KV (in-memory Map). The embed route's
// contract is pinned UNCHANGED — it is the live compose-time dedup path.
import worker from "../src/worker.js";

let failures = 0;
let n = 0;
function check(name, ok, detail) {
  n += 1;
  console.log(`${ok ? "ok" : "NOT OK"} ${n} - ${name}${ok ? "" : "  " + (detail || "")}`);
  if (!ok) failures += 1;
}

const TOKEN = "test-token-0123456789";
const AUTH = { Authorization: `Bearer ${TOKEN}` };

function vec(seed) {
  const v = new Array(1024).fill(0);
  v[seed % 1024] = 1;
  v[(seed + 1) % 1024] = 0.5;
  return v;
}

const kvStore = new Map();
const env = {
  EMBED_TOKEN: TOKEN,
  AI: {
    async run(model, { text }) {
      // deterministic: text "q:<n>" embeds as vec(n); anything else vec(7)
      return { shape: [text.length, 1024], data: text.map((t) => {
        const m = /^q:(\d+)$/.exec(t);
        return vec(m ? +m[1] : 7);
      }) };
    },
  },
  PLANE_KV: {
    async get(key, type) {
      const v = kvStore.get(key);
      if (!v) return null;
      return type === "arrayBuffer" ? v : v;
    },
    async put(key, value) {
      kvStore.set(key, value instanceof ArrayBuffer ? value : value.buffer);
    },
  },
};

function req(path, { method = "POST", headers = {}, body } = {}) {
  const init = { method, headers: { "Content-Type": "application/json", ...headers } };
  if (body !== undefined) {
    init.body = body instanceof ArrayBuffer || ArrayBuffer.isView(body) ? body : JSON.stringify(body);
  }
  return new Request(`https://embed-proxy.test${path}`, init);
}

function bakeArtifact(stories, vectors) {
  const norms = vectors.map((v) => (v ? Math.sqrt(v.reduce((s, x) => s + x * x, 0)) : 0));
  const meta = new TextEncoder().encode(JSON.stringify({ n: stories.length, dim: 1024, ts: "T", norms, stories }));
  const buf = new ArrayBuffer(12 + meta.length + stories.length * 1024 * 4);
  const bytes = new Uint8Array(buf);
  bytes.set(new TextEncoder().encode("PLANEv1\0"), 0);
  new DataView(buf).setUint32(8, meta.length, true);
  bytes.set(meta, 12);
  const f32 = new Float32Array(stories.length * 1024);
  vectors.forEach((v, i) => { if (v) f32.set(v, i * 1024); });
  bytes.set(new Uint8Array(f32.buffer), 12 + meta.length);
  return buf;
}

const STORIES = [
  { sid: "st-aaa", date: "2026-07-01", stream: "news", headline: "Alpha", url: "https://x/a",
    thread_id: "t-iran", topics: ["geopolitics"], entities: ["Iran"], legacy_ids: ["2026-07-01-news-alpha"] },
  { sid: "st-bbb", date: "2026-07-05", stream: "news", headline: "Beta", url: "https://x/b",
    thread_id: "t-iran", topics: ["geopolitics"], entities: ["Iran", "CAS"] },
  { sid: "st-ccc", date: "2026-07-10", stream: "sports", headline: "Gamma", url: "https://x/c",
    topics: ["sports"], entities: ["CAS"] },
];
const VECTORS = [vec(0), vec(100), null]; // st-ccc has no vector (norm 0)

// --- embed route: contract UNCHANGED ---------------------------------------------------------
{
  const res = await worker.fetch(req("/", { body: { texts: ["x"] } }), env);
  check("POST / without bearer -> 401", res.status === 401);
}
{
  const res = await worker.fetch(req("/", { method: "GET" }), env);
  check("GET -> 405", res.status === 405);
}
{
  const res = await worker.fetch(req("/", { headers: AUTH, body: { texts: [] } }), env);
  check("POST / empty texts -> 400", res.status === 400);
}
{
  const res = await worker.fetch(req("/", { headers: AUTH, body: { texts: ["q:5", "other"] } }), env);
  const body = await res.json();
  check("POST / embeds -> {model, dim, embeddings}",
    res.status === 200 && body.model === "bge-m3" && body.dim === 1024 &&
      body.embeddings.length === 2 && body.embeddings[0][5] === 1,
    JSON.stringify([res.status, body.model, body.dim]));
}
{
  const res = await worker.fetch(req("/", { headers: AUTH, body: "not json" }), env);
  check("POST / invalid JSON -> 400", res.status === 400);
}

// --- plane routes ----------------------------------------------------------------------------
{
  const res = await worker.fetch(req("/plane/stats", { headers: AUTH, body: {} }), env);
  check("stats before ingest -> 503", res.status === 503);
}
{
  const res = await worker.fetch(req("/plane/ingest", { headers: AUTH, body: new TextEncoder().encode("BADMAGIC....") }), env);
  check("ingest bad magic -> 400", res.status === 400);
}
{
  const res = await worker.fetch(req("/plane/stats", { body: {} }), env);
  check("plane route without bearer -> 401", res.status === 401);
}
{
  const res = await worker.fetch(
    req("/plane/ingest", { headers: { ...AUTH, "Content-Type": "application/octet-stream" },
                           body: bakeArtifact(STORIES, VECTORS) }), env);
  const body = await res.json();
  check("ingest valid artifact -> ok + count", res.status === 200 && body.ok === true && body.stories === 3,
    JSON.stringify(body));
}
{
  const res = await worker.fetch(req("/plane/search", { headers: AUTH, body: { text: "q:0", k: 2 } }), env);
  const body = await res.json();
  check("search ranks the matching vector first, k respected",
    res.status === 200 && body.hits.length === 2 && body.hits[0].sid === "st-aaa" && body.hits[0].sim > 0.99,
    JSON.stringify(body.hits && body.hits.map((h) => [h.sid, h.sim])));
}
{
  const res = await worker.fetch(req("/plane/related", { headers: AUTH, body: { key: "2026-07-01-news-alpha" } }), env);
  const body = await res.json();
  check("related resolves legacy id, excludes anchor, labels thread edge",
    res.status === 200 && body.anchor.sid === "st-aaa" &&
      body.hits.every((h) => h.sid !== "st-aaa") &&
      body.hits.find((h) => h.sid === "st-bbb").edge === "same-thread",
    JSON.stringify(body));
}
{
  const res = await worker.fetch(req("/plane/thread", { headers: AUTH, body: { key: "st-bbb" } }), env);
  const body = await res.json();
  check("thread returns members oldest->newest",
    res.status === 200 && body.thread_id === "t-iran" &&
      body.stories.map((s) => s.sid).join(",") === "st-aaa,st-bbb",
    JSON.stringify(body));
}
{
  const res = await worker.fetch(req("/plane/entities", { headers: AUTH, body: { days: 36500 } }), env);
  const body = await res.json();
  const cas = body.entities.find((e) => e.entity === "CAS");
  check("entities aggregates across streams",
    res.status === 200 && cas && cas.stories === 2 && cas.streams.join("/") === "news/sports",
    JSON.stringify(body.entities));
}
{
  const res = await worker.fetch(req("/plane/sources", { headers: AUTH, body: { days: 36500 } }), env);
  const body = await res.json();
  check("sources handles missing source_domain rows", res.status === 200 && Array.isArray(body.sources));
}
{
  const res = await worker.fetch(req("/plane/stats", { headers: AUTH, body: {} }), env);
  const body = await res.json();
  check("stats counts vectors + developing threads",
    res.status === 200 && body.stories === 3 && body.with_vectors === 2 && body.threads_developing === 1,
    JSON.stringify(body));
}
{
  const envNoKv = { ...env, PLANE_KV: undefined };
  const res = await worker.fetch(req("/plane/stats", { headers: AUTH, body: {} }), envNoKv);
  check("plane route without KV binding -> 503", res.status === 503);
}
{
  const res = await worker.fetch(req("/nope", { headers: AUTH, body: {} }), env);
  check("unknown path -> 404", res.status === 404);
}

// --- adversarial regressions (pre-deploy review 2026-07-18: four verified 500s) --------------
{
  const res = await worker.fetch(req("/plane/stats", { headers: AUTH, body: null }), env);
  check("JSON null body -> 200, not 500", res.status === 200, String(res.status));
}
{
  const res = await worker.fetch(req("/plane/entities", { headers: AUTH, body: { days: "abc" } }), env);
  check("non-numeric days -> 200 (default window), not RangeError",
    res.status === 200, String(res.status));
  const res2 = await worker.fetch(req("/plane/sources", { headers: AUTH, body: { days: 1e20 } }), env);
  check("overflow days -> 200 (clamped), not RangeError", res2.status === 200, String(res2.status));
}
{
  const evil = [
    { sid: "st-evil1", date: "2026-07-01", stream: "news", headline: "P", entities: ["__proto__", "toString"], topics: ["x"] },
    { sid: "st-evil2", date: "9999-99-99", stream: "news", headline: "D", topics: ["x"] },
  ];
  const res = await worker.fetch(
    req("/plane/ingest", { headers: { ...AUTH, "Content-Type": "application/octet-stream" },
                           body: bakeArtifact(evil, [vec(3), vec(4)]) }), env);
  check("adversarial artifact ingests", res.status === 200);
  const ent = await worker.fetch(req("/plane/entities", { headers: AUTH, body: { days: 36500 } }), env);
  const entBody = await ent.json();
  check("prototype-name entities aggregate safely",
    ent.status === 200 && entBody.entities.find((e) => e.entity === "__proto__")?.stories === 1,
    JSON.stringify(entBody));
  const beats = await worker.fetch(req("/plane/beats", { headers: AUTH, body: { days: 36500 } }), env);
  check("malformed story date skipped in beats, not 500", beats.status === 200, String(beats.status));
  // restore the main fixture for anything that runs after
  await worker.fetch(req("/plane/ingest", { headers: { ...AUTH, "Content-Type": "application/octet-stream" },
                                            body: bakeArtifact(STORIES, VECTORS) }), env);
}

console.log(failures === 0 ? `PASS: all ${n} checks passed` : `FAIL: ${failures}/${n} checks failed`);
process.exit(failures === 0 ? 0 : 1);
