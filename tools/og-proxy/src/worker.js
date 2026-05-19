// og-proxy: given ?url=<encoded URL>, fetch the page with a real-browser UA,
// stream-parse <head> for og:image / twitter:image / link rel=image_src, return
// { image, title } as JSON. All responses CORS-open. Failures return 200 with
// image: null so the client cascade stays simple.

const UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 " +
  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";

const FETCH_TIMEOUT_MS = 6000;
const MAX_BYTES = 512 * 1024; // 512 KB cap before parsing
const CACHE_TTL_SECONDS = 30 * 24 * 60 * 60; // 30 days
const CACHE_VERSION = "v2"; // bump to bust the edge cache

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
  "Access-Control-Allow-Headers": "*",
  "Access-Control-Max-Age": "86400",
};

function json(body, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": status === 200
        ? `public, max-age=${CACHE_TTL_SECONDS}`
        : "no-store",
      ...CORS,
      ...extraHeaders,
    },
  });
}

function text(body, status, extraHeaders = {}) {
  return new Response(body, {
    status,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      ...CORS,
      ...extraHeaders,
    },
  });
}

// Reject schemes other than http(s) and hostnames pointing at private space.
// Workers can't actually reach the user's LAN, but rejecting prevents the
// worker from being used as a generic open relay for non-public targets.
function isAllowedTarget(u) {
  if (u.protocol !== "http:" && u.protocol !== "https:") return false;
  const h = u.hostname.toLowerCase();
  if (h === "localhost" || h.endsWith(".localhost")) return false;
  if (h === "::1" || h === "[::1]") return false;
  // IPv4 literal? Quick prefix checks for the common private ranges.
  if (/^\d+\.\d+\.\d+\.\d+$/.test(h)) {
    const o = h.split(".").map(Number);
    if (o[0] === 10) return false;
    if (o[0] === 127) return false;
    if (o[0] === 169 && o[1] === 254) return false;
    if (o[0] === 172 && o[1] >= 16 && o[1] <= 31) return false;
    if (o[0] === 192 && o[1] === 168) return false;
    if (o[0] === 0) return false;
  }
  // IPv6 literal in brackets, link-local / ULA prefixes.
  if (h.startsWith("[fc") || h.startsWith("[fd")) return false;
  if (h.startsWith("[fe8") || h.startsWith("[fe9") || h.startsWith("[fea") || h.startsWith("[feb")) return false;
  return true;
}

function resolveMaybeRelative(candidate, base) {
  if (!candidate) return null;
  try {
    return new URL(candidate, base).toString();
  } catch {
    return null;
  }
}

// Stream-parse <head>. HTMLRewriter doesn't expose a "stop after </head>"
// primitive, so we rely on the byte cap upstream.
async function extractMeta(response, baseUrl) {
  const out = {
    ogSecure: null,
    og: null,
    twitter: null,
    linkImageSrc: null,
    title: null,
  };
  let inTitle = false;
  let titleBuf = "";

  const rewriter = new HTMLRewriter()
    .on("meta", {
      element(el) {
        const prop = (el.getAttribute("property") || "").toLowerCase();
        const name = (el.getAttribute("name") || "").toLowerCase();
        const content = el.getAttribute("content");
        if (!content) return;
        if (prop === "og:image:secure_url" && !out.ogSecure) out.ogSecure = content;
        else if ((prop === "og:image" || prop === "og:image:url") && !out.og) out.og = content;
        else if ((name === "twitter:image" || name === "twitter:image:src") && !out.twitter) out.twitter = content;
      },
    })
    .on('link[rel="image_src"]', {
      element(el) {
        const href = el.getAttribute("href");
        if (href && !out.linkImageSrc) out.linkImageSrc = href;
      },
    })
    .on("title", {
      element() {
        inTitle = true;
      },
      text(t) {
        if (inTitle) {
          titleBuf += t.text;
          if (t.lastInTextNode) inTitle = false;
        }
      },
    });

  // Consume the rewritten stream so handlers fire; we don't need the bytes.
  await rewriter.transform(response).arrayBuffer();
  if (titleBuf) out.title = titleBuf.trim() || null;

  const candidate =
    out.ogSecure || out.og || out.twitter || out.linkImageSrc;
  const image = resolveMaybeRelative(candidate, baseUrl);
  return { image, title: out.title };
}

// Cap a body stream at N bytes. Some sites serve multi-MB pages; we only need
// the head section. Returns a Response object with a truncated body but the
// original headers/status, so HTMLRewriter can still consume it.
function cappedResponse(resp, maxBytes) {
  const reader = resp.body.getReader();
  let total = 0;
  const stream = new ReadableStream({
    async pull(controller) {
      const { done, value } = await reader.read();
      if (done) {
        controller.close();
        return;
      }
      if (total + value.byteLength > maxBytes) {
        const remaining = maxBytes - total;
        if (remaining > 0) controller.enqueue(value.subarray(0, remaining));
        controller.close();
        try { await reader.cancel(); } catch {}
        return;
      }
      total += value.byteLength;
      controller.enqueue(value);
    },
    cancel(reason) {
      try { reader.cancel(reason); } catch {}
    },
  });
  return new Response(stream, { status: resp.status, headers: resp.headers });
}

async function handleLookup(targetUrl) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const upstream = await fetch(targetUrl, {
      method: "GET",
      redirect: "follow",
      signal: controller.signal,
      headers: {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en;q=0.9",
      },
      cf: {
        // Cache the upstream fetch at Cloudflare's edge too. The worker's own
        // response cache (further down) is the primary; this is just bonus.
        cacheTtl: CACHE_TTL_SECONDS,
        cacheEverything: true,
      },
    });
    clearTimeout(timeout);

    if (!upstream.ok || !upstream.body) {
      return { image: null, title: null };
    }
    const ct = (upstream.headers.get("Content-Type") || "").toLowerCase();
    if (!ct.includes("text/html") && !ct.includes("xhtml") && !ct.includes("application/xml")) {
      return { image: null, title: null };
    }
    const capped = cappedResponse(upstream, MAX_BYTES);
    return await extractMeta(capped, upstream.url || targetUrl);
  } catch {
    clearTimeout(timeout);
    return { image: null, title: null };
  }
}

export default {
  async fetch(request, env, ctx) {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS });
    }
    if (request.method !== "GET") {
      return text("method not allowed", 405);
    }

    const url = new URL(request.url);
    const raw = url.searchParams.get("url");
    if (!raw) return text("missing ?url= param", 400);

    let target;
    try { target = new URL(raw); }
    catch { return text("invalid url", 400); }

    if (!isAllowedTarget(target)) {
      return text("blocked target", 400);
    }

    // Edge-cache key normalised to just the target URL + cache version, so
    // bumping CACHE_VERSION busts everything cleanly.
    const cacheUrl = new URL(request.url);
    cacheUrl.search = `?v=${CACHE_VERSION}&url=${encodeURIComponent(target.toString())}`;
    const cacheKey = new Request(cacheUrl.toString(), { method: "GET" });
    const cached = await caches.default.match(cacheKey);
    if (cached) return cached;

    const result = await handleLookup(target.toString());
    const resp = json(result);
    // Persist to the edge cache asynchronously; don't block the response.
    ctx.waitUntil(caches.default.put(cacheKey, resp.clone()));
    return resp;
  },
};
