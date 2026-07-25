# Source plan (registry-driven) + fetch mechanics (apply to ALL sections)

**FIRST research action — build today's source plan:**

    python3 tools/sources/preflight.py --slug {slug}

It reads `sources/registry.yml` and prints the plan that is the AUTHORITY on what to fetch and what pressure applies today — not any table in this prompt:

- **Fetch list** — the domains/feeds affine to this stream, each with its probe URL and method (curl or proxy). Sweep these first.
- **Pressure** — per-domain rolling-30-day citation shares, with a `SATURATED` flag on any domain over its share bar (hubs like arXiv are exempt). Report-only — no story is dropped for it — but when two sources carry the same story, prefer the unsaturated one, and cite no outlet domain more than twice in one edition (hubs exempt).
- **Discovery** — this stream's discovery quota and `candidates_to_try` (registry candidates and dormant domains worth a probe this run). Work at least the quota's worth of genuinely new or dormant domains into your research; the Discovery footer line reports the outcome.

**EMERGENCY SLATE — degraded mode only (a floor, never the ceiling).** If preflight errors or prints `source-plan unavailable`, fall back to these known-good feeds and note `source-plan unavailable` in the Gaps footer:
- News desks: SRF `https://www.srf.ch/news/bnf/rss/1646`, Le Temps `https://www.letemps.ch/articles.rss`, Al Jazeera `https://www.aljazeera.com/xml/rss/all.xml`.
- Science streams: arXiv `https://export.arxiv.org/rss/{category}` + the Atom API, Nature `https://www.nature.com/nature.rss`.
Still research beyond this floor as the brief demands — the slate is where you start when the plan is missing, never a cap on where you look.

**New-source citation rule.** T3 aggregators (HN/Reddit/X) remain never-cited. But a **genuine primary source discovered through search or a T3 lead MAY be cited immediately even if it is absent from `sources/registry.yml`** — tag it with the literal marker `[new source]` next to the citation. Tag ONLY domains genuinely absent from the registry (grep `sources/registry.yml` for the domain first): the source lint recomputes novelty itself at publish, and both a missing tag on an unregistered domain and a `[new source]` tag on a registered one are violations. This is how the registry grows — a tagged citation auto-enters the domain as a `candidate`.

## Fetch mechanics

**Feed first.** Most quality sources' HTML 403s this sandbox while the same publisher's RSS / Atom
/ JSON feed — served from different infrastructure — is reachable. Attempt the feed or API before
the HTML page for any source that has one.

**Every research fetch goes through `tools/fetch.py`** — never raw `curl`, and WebFetch only as a
last resort. Once, at the start of the session, export the proxy bearer:

    export FETCH_PROXY_TOKEN='${FETCH_PROXY_TOKEN}'

Then, for every URL:

    python3 tools/fetch.py "<URL>"             # direct first, proxy fallback on failure
    python3 tools/fetch.py --proxy "<URL>"     # hosts the plan marks `method: proxy`

The plan's `reach:` is the reachability truth — this prompt carries no unavailable list.

**Exit 0 is a real fetch — no marker, whichever way it resolved.** A non-zero exit means the host
blocks even the proxy, or is paywalled: only then fall back to a search-engine snippet and tag
that citation `[via snippet]`. If a citation rests on WebFetch instead, say so in the Gaps line —
it leaves no trace in the fetch log.

**Never hand-count fetch telemetry.** The footer's tier split, direct-vs-snippet counts, word
count and `Feeds hit` are computed at publish from your citations and the wrapper's log. Your
whole accounting duty is upstream: tag every snippet-only citation, and fetch through the wrapper
(fetching around it silently undercounts).
