// fetch-proxy: GET /?url=<urlencoded https URL> -> the upstream page body, fetched
// from Cloudflare's edge with a real browser User-Agent. The news-brief routine
// sandbox has HTTP/HTTPS-allowlist egress only AND egresses from datacenter IPs that
// Cloudflare/Akamai-fronted sites (lab blogs, CNBC/TechCrunch/Bloomberg, ...) 403 on
// sight. Routing the fetch through this Worker fixes both at once:
//   - the sandbox only needs ONE allowlisted host (fetch-proxy.<acct>.workers.dev),
//     not fifty news/lab domains;
//   - the request leaves from a Cloudflare edge IP with browser headers, so it isn't
//     auto-rejected as a robot.
//
// Transparent passthrough: the upstream HTTP status is mirrored, so a writer's
// `curl -fsSL` still *fails* (and falls back to a search snippet) when the origin
// genuinely blocks us — the proxy never fakes a 200.
//
// The host is public on *.workers.dev, so a shared bearer token (Worker secret
// FETCH_TOKEN) is required on every request. Twin of tools/og-proxy + tools/embed-proxy;
// same CORS/json/text/auth helper shape.

const MAX_BYTES = 5 * 1024 * 1024; // 5 MB cap on a fetched body
const TIMEOUT_MS = 20000;
// A current desktop-Chrome UA + the headers a real browser sends. This is the
// "don't announce we're a robot" part — low-volume personal reading of public pages.
const BROWSER_HEADERS = {
  "User-Agent":
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
  Accept:
    "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.9,*/*;q=0.8",
  "Accept-Language": "en-US,en;q=0.9,de;q=0.6,fr;q=0.5",
  "Accept-Encoding": "gzip, deflate, br",
};

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
  "Access-Control-Allow-Headers": "Authorization, Content-Type",
  "Access-Control-Max-Age": "86400",
};

function text(body, status, extraHeaders = {}) {
  return new Response(body, {
    status,
    headers: { "Content-Type": "text/plain; charset=utf-8", ...CORS, ...extraHeaders },
  });
}

function authorized(request, env) {
  const expected = env.FETCH_TOKEN;
  if (!expected) return false; // fail closed if the secret isn't configured
  const got = (request.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  if (got.length !== expected.length) return false;
  let diff = 0;
  for (let i = 0; i < got.length; i++) diff |= got.charCodeAt(i) ^ expected.charCodeAt(i);
  return diff === 0;
}

// Block obviously-internal targets even though the token gates the host (defense in
// depth + stops the proxy being pointed at cloud metadata / RFC1918).
function isBlockedHost(hostname) {
  const h = hostname.toLowerCase();
  if (h === "localhost" || h.endsWith(".localhost")) return true;
  if (h.endsWith(".internal") || h.endsWith(".local")) return true;
  // IPv4 literals in private / link-local / loopback ranges.
  const m = h.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/);
  if (m) {
    const [a, b] = [Number(m[1]), Number(m[2])];
    if (a === 127 || a === 10 || a === 0) return true;
    if (a === 169 && b === 254) return true; // link-local incl. 169.254.169.254 metadata
    if (a === 172 && b >= 16 && b <= 31) return true;
    if (a === 192 && b === 168) return true;
  }
  // IPv6 loopback / link-local / unique-local.
  if (h === "::1" || h.startsWith("fe80:") || h.startsWith("fc") || h.startsWith("fd")) return true;
  return false;
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS });
    }
    if (request.method !== "GET") {
      return text("method not allowed (GET only)", 405);
    }
    if (!authorized(request, env)) {
      return text("unauthorized", 401);
    }

    const target = new URL(request.url).searchParams.get("url");
    if (!target) {
      return text("missing ?url= parameter", 400);
    }

    let dest;
    try {
      dest = new URL(target);
    } catch {
      return text("invalid url", 400);
    }
    if (dest.protocol !== "http:" && dest.protocol !== "https:") {
      return text("only http/https targets allowed", 400);
    }
    if (isBlockedHost(dest.hostname)) {
      return text("target host not allowed", 403);
    }

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
    let upstream;
    try {
      upstream = await fetch(dest.toString(), {
        method: "GET",
        headers: { ...BROWSER_HEADERS, Referer: dest.origin + "/" },
        redirect: "follow",
        signal: controller.signal,
      });
    } catch (e) {
      clearTimeout(timer);
      return text(`upstream fetch failed: ${String((e && e.message) || e)}`, 502);
    }
    clearTimeout(timer);

    // Enforce the size cap by reading the body ourselves.
    let buf;
    try {
      buf = await upstream.arrayBuffer();
    } catch (e) {
      return text(`reading upstream body failed: ${String((e && e.message) || e)}`, 502);
    }
    if (buf.byteLength > MAX_BYTES) {
      return text(`upstream body too large (> ${MAX_BYTES} bytes)`, 502);
    }

    // Mirror the upstream status so `curl -fsSL` keeps its fail-on-block semantics.
    return new Response(buf, {
      status: upstream.status,
      headers: {
        "Content-Type": upstream.headers.get("Content-Type") || "application/octet-stream",
        "Cache-Control": "no-store",
        "X-Proxy-Final-Url": upstream.url || dest.toString(),
        "X-Proxy-Upstream-Status": String(upstream.status),
        ...CORS,
      },
    });
  },
};
