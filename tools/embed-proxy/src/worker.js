// embed-proxy: POST { "texts": ["...", ...] } -> { model, dim, embeddings }.
// Wraps Cloudflare Workers AI (@cf/baai/bge-m3, 1024-dim) so the routine
// sandbox -- which has HTTP/HTTPS-allowlist egress only and no embeddings MCP --
// can embed candidate story summaries at compose time for dedup.
//
// The host is public on *.workers.dev and Workers-AI neurons are metered, so a
// shared bearer token (Worker secret EMBED_TOKEN) is required on every request.
// Twin of tools/og-proxy; same CORS/json/text helper shape.

const MODEL = "@cf/baai/bge-m3";
const DIM = 1024;
const MAX_TEXTS = 128; // a day's candidates across any one brief is well under this
const MAX_TOTAL_CHARS = 64 * 1024; // guard against oversized bodies

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
  },
};
