# Source plan (registry-driven) + fetch mechanics (apply to ALL sections)

**FIRST research action — build today's source plan:**

    python3 tools/sources/preflight.py --slug {slug}

(your slug is the one named in your Story-deduplication section). It reads `sources/registry.yml` and prints the plan that is the AUTHORITY on what to fetch and what pressure applies today — not any table in this prompt:

- **Fetch list** — the domains/feeds affine to this stream, each with its probe URL and method (curl or proxy). Sweep these first.
- **Pressure** — per-domain rolling-30-day citation shares, with a `SATURATED` flag on any domain over its share bar (hubs like arXiv are exempt). The separate flat cap of 2 stories per outlet domain per edition is checked after writing by the source lint (DEDUP Step C.25), not printed here. Both are report-only — no story gets dropped for them — but when two sources carry the same story, prefer the unsaturated one.
- **Discovery** — this stream's discovery quota and `candidates_to_try` (registry candidates and dormant domains worth a probe this run). Work at least the quota's worth of genuinely new or dormant domains into your research; the Discovery footer line reports the outcome.

**EMERGENCY SLATE — degraded mode only (a floor, never the ceiling).** If preflight errors or prints `source-plan unavailable`, fall back to these known-good feeds and note `source-plan unavailable` in the Gaps footer:
- News desks: SRF `https://www.srf.ch/news/bnf/rss/1646`, Le Temps `https://www.letemps.ch/articles.rss`, Al Jazeera `https://www.aljazeera.com/xml/rss/all.xml`.
- Science streams: arXiv `https://export.arxiv.org/rss/{category}` + the Atom API, Nature `https://www.nature.com/nature.rss`.
Still research beyond this floor as the brief demands — the slate is where you start when the plan is missing, never a cap on where you look.

**New-source citation rule.** T3 aggregators (HN/Reddit/X) remain never-cited. But a **genuine primary source discovered through search or a T3 lead MAY be cited immediately even if it is absent from `sources/registry.yml`** — tag it with the literal marker `[new source]` next to the citation. Tag ONLY domains genuinely absent from the registry (grep `sources/registry.yml` for the domain first): the lint at DEDUP Step C.25 recomputes novelty itself, and both a missing tag on an unregistered domain and a `[new source]` tag on a registered one are violations. This is how the registry grows — a tagged citation auto-enters the domain as a `candidate`.

## Fetch mechanics

**Every research fetch goes through the logging wrapper `tools/fetch.py` — not raw `curl`, and WebFetch only as a last resort.** The wrapper runs the deterministic chain (direct curl first, then the fetch-proxy Worker — Cloudflare edge, real browser User-Agent — which bypasses the sandbox-IP 403s on Cloudflare/Akamai-fronted sites), and logs every attempt to `/tmp/fetch.log`. That log becomes the Coverage footer's exact `Feeds hit` line and research-call count at publish time — fetching around the wrapper makes the telemetry silently undercount, so don't.

Once, at the start of the session, export the proxy bearer so the wrapper's fallback works:

    export FETCH_PROXY_TOKEN='${FETCH_PROXY_TOKEN}'

Then, for every URL:

    python3 tools/fetch.py "<URL>"             # direct curl first, proxy fallback on failure
    python3 tools/fetch.py --proxy "<URL>"     # hosts the preflight plan marks `method: proxy`: skip the wasted direct attempt

- **Direct-first hosts** (registry `reach: direct` — e.g. `export.arxiv.org`, `www.nature.com`, `www.quantamagazine.org`, `www.srf.ch`, `www.letemps.ch`, `www.aljazeera.com`, plus API endpoints like `api.semanticscholar.org`) succeed on the wrapper's first attempt; the direct-first order also honors arXiv's ask that automated clients fetch it directly.
- **`--proxy` for everything the plan marks `method: proxy`** — lab blogs (Anthropic, OpenAI, DeepMind, Meta, Mistral, Apple), tech-news HTML (CNBC, TechCrunch, VentureBeat, Bloomberg, Fortune, …). The registry's `reach:` field (surfaced in the preflight plan) is the reachability truth; there is no static unavailable list.
- **Exit 0 with the body on stdout is a direct fetch** — no `[via snippet]` tag, whether it resolved direct or via proxy. A non-zero exit means the host hard-blocks even the proxy (Cloudflare JS/Turnstile challenge) or is paywalled — only then fall back to a search-engine snippet and tag the citation `[via snippet]`. (WebFetch remains a permitted last resort for a page the wrapper cannot reach; if a citation rests on WebFetch-only access, say so in the Gaps line, since the log will not show it.)
- **Do not hand-report fetch telemetry.** The footer's `Feeds hit`, direct-vs-snippet counts, and call count are computed from `/tmp/fetch.log` and your `[via snippet]` tags at publish time (`tools/footer.py`, run by the publish command). Your accounting duty is upstream: tag every snippet-only citation `[via snippet]`, and fetch through the wrapper.
