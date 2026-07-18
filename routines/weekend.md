Write my weekend deep-read brief and publish it via the git pipeline. Use today's date (Saturday) in Europe/Zurich.

The repo (`khalic-lab/claude-routines`) is cloned as your working directory. Before doing anything else, sync:

```bash
git pull --ff-only origin main
```

# Mission

A long-form weekly digest. Coverage window: past 7 days. **This is the in-depth revisit of the week's most important stories** — the place where the week's biggest items get the *deep* treatment. Select and go deep on the strongest items across the past 7 days regardless of which day they broke, **including stories the daily editions (News / AI/ML / Science) already flagged this week.** Do NOT avoid a story just because a daily edition mentioned it — this is exactly where it gets revisited: go deeper than the daily did, with fuller analysis, the complete paper summary, and connection-drawing across stories.

Bias the content toward:
1. **ML/AI research** (heaviest), with RL prioritized
2. **Fundamental science** (math, physics, astronomy, quantum) — papers, discoveries, conjecture progress
3. **Biology, biotech, neuroscience**
4. **Data science / applied ML**
5. **Long-form essays and analysis** that came out this week

Light news/politics — just a brief "what mattered this week" section at the top. The point is the deep read, not the headline recap.

# Newsroom ethos (the standard you hold yourself to)

You are a desk with standards, not an aggregator. Keep these in mind as you select and write:
- "Comment is free, but facts are sacred." — C.P. Scott, Manchester Guardian (1921)
- "Accuracy, accuracy, accuracy." — Joseph Pulitzer
- "To be persuasive we must be believable; to be believable we must be credible; to be credible we must be truthful." — Edward R. Murrow
- Aim for "the best obtainable version of the truth." — Carl Bernstein

In practice: go to the primary source and read it yourself; report what it actually says, not what a headline or a secondary write-up dramatizes. Flag what is preliminary, small-sample, or contested instead of smoothing it into a confident claim. Resist sensational framing — better to omit than to hype or dilute.

**Cite the source itself, never a write-up of it.** The study, filing, preprint, or advisory is the primary; a blog post or news article *about* it is secondary. Link the primary and read its abstract; never present the secondary as the primary, and never upgrade preliminary or mixed evidence into a firm finding.

**Omit, don't fill.** A section — or the whole brief — earns its place only with genuinely new substance. If a desk has nothing new since it last ran, leave it out entirely: no placeholder, no "nothing notable today" line, no restating something already covered. A short, honest brief beats a padded one.

**Tag every story you keep with a beat and an importance.** The homepage renders individual stories as a filterable, importance-sized grid, so each story you record (`DEDUP.md` Step C) carries these extra fields:
- `topics`: a list of 1–2 beats from this controlled set (lowercase, exact): `switzerland`, `geopolitics`, `politics`, `economy`, `ai-ml`, `science`, `health`, `security`, `tech`, `sports`, `world`. Pick the most specific that fits; use `world` only when none of the others do.
- `importance`: an integer 1–3 for how much the story matters — **3** = the edition's lead or a major development, **2** = a solid standard item, **1** = a brief or minor note. Judge genuine significance to the reader across the WHOLE edition, never section order — the brief's template puts the Swiss desk first, and a routine cantonal item that happens to open the file is NOT the lead when a war development sits two sections down. Exactly one 3 per edition unless the day genuinely has two majors; most stories are 1 or 2. Without your score the homepage guesses from position and gets exactly this wrong.
- `display_body` and `why`: the story's published prose, copied VERBATIM from the brief you just wrote — `display_body` is the explanatory paragraph, `why` is the "Why it matters" text when the story has one (else omit). Plain text, no markdown. These are what the homepage card shows the reader; copy, don't rewrite.

**Discovery footer contract (exactly one line, lint-verified).** Every brief's Coverage footer ends with exactly ONE of:
- `- Discovery: met (<the genuinely new domain(s) you anchored this edition, each tagged [new source]>)`
- `- Discovery: waived — <concrete reason>`
"met" is recomputed against your stream's discovery quota (stated in the preflight plan's discovery section) — never claim it without the tagged citations to back it; a false "met" is a violation, an honest waiver is not. The waiver is free but counted: give a real reason ("pursued X and Y, both paywalled"), not boilerplate. Zero lines, two lines, or any other wording all fail the lint.

# Sourcing rules (non-negotiable)

1. **Tiers.** T1 = primary (wire, official, preprint, filing, vendor advisory, lab blog). T2 = quality secondary. T3 = discovery only (HN/Reddit/Lobsters/X) — used to find stories, NEVER cited. Click through and cite the underlying T1/T2. **A quality outlet's news report or feature *about* a study is T2 secondary, never T1 — even when that outlet also publishes primary research.** Nature news/features (URLs of the form `nature.com/articles/d41586-…`) are journalism about papers, not the papers themselves; the primary source is the underlying paper or preprint. When you cover a study, locate and cite that **primary paper** — read its abstract — and use the news write-up only as a secondary pointer or for triangulation. A bullet whose sole citation is a `d41586` Nature-news piece (or any equivalent secondary report) is mis-sourced: find the paper, or if you genuinely cannot, frame it as 'as reported by …' and tag `[single-source]` — never present secondary journalism as the primary.
2. **Citation format.** Every bullet ends with a markdown link to one specific URL. Include publication name and date.
3. **Triangulation.** Significant claims need two independent sources where feasible. Single-sourced → mark `[single-source]`.
4. **Diversification.** Within each section, span geographic/linguistic sources.
5. **Tags.** Preprints → `[preprint]`. Vendor announcements → `[vendor PR]`. Single source → `[single-source]`. Contested → `[disputed]`.
6. **No fabrication.** Never invent a URL, author, date, or quote.
7. **Fetch transparency.** Many sites return HTTP 403 to the routine sandbox. When you successfully fetch a URL/feed and confirm content, no marker. When the citation is based only on a search-engine snippet, append `[via snippet]` to the citation.

**Volume rules for weekend brief:**
- Sections aren't capped at 4–7. Quality is the cap.
- Each paper covered gets a 3–5 sentence summary in your own words.
- Each essay gets 2–3 sentence summary + your read on whether it's worth the full read.

# Reader profile + source weights (read before selecting and ordering stories)

Before composing, read two human-gated files from the repo root and let them shape what you
SELECT and how you WEIGHT it — not just wording:
- `reader-profile.md` — a standing editorial brief for this specific reader (Rafael). Favor
  what it says to favor, demote/cut what it says to demote; it reflects the reader, not generic
  newsworthiness. Apply its "Learned preferences" section if present.
- `reader-profile/source-weights.yml` — two domain lists, matched on a story's primary source
  domain (lowercased host, leading "www." stripped):
  - `never:` — HARD filter: drop any story whose primary source is one of these domains.
  - `reduce:` — soft penalty: keep only if the story is clearly significant on its own; else
    demote or cut it.
These files are maintained via the Weekly Evaluator under a human gate — treat them as standing
editorial instruction. If a file is missing or empty, proceed normally.

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

The HTML pages of most quality sources return HTTP 403 from this routine sandbox. Many of those publishers also offer machine-readable feeds (RSS, Atom, JSON) that are reachable. **Always attempt the feed/API before the HTML page.**

**CRITICAL — every fetch goes through `python3 tools/fetch.py "<URL>"`** (see Fetch mechanics above): it runs the direct-curl → proxy chain deterministically and logs each attempt to `/tmp/fetch.log`. A wrapper exit 0 counts as a direct fetch. This is the binding-constraint workaround for the 403 wall.

**Order of attempts per topic, in priority:**
1. Feed from the preflight plan (or arXiv/Semantic Scholar APIs) via `tools/fetch.py`.
2. The publisher's HTML page via `tools/fetch.py --proxy` (or WebFetch as a last resort).
3. Web search snippet (last resort, tag the citation `[via snippet]`).

**arXiv / Semantic Scholar mechanics:** the date-filtered arXiv Atom API (`https://export.arxiv.org/api/query?search_query=cat:cs.LG&start=0&max_results=30&sortBy=submittedDate&sortOrder=descending`) works for `math.*`, `physics.*`, `astro-ph.*` too — swap the `cat:` filter and window the `<published>` dates client-side. Semantic Scholar: `https://api.semanticscholar.org/graph/v1/paper/search?query=...&fields=title,abstract,year,authors` (triangulation and citation counts — NOT affiliations; those follow the block below).

**Affiliations — the paper's provenance element (machine-parsed):** every paper byline carries
the lead authors' institutional affiliations. They are the paper's editorial source —
arxiv.org is just the platform — and they flow to the homepage cards' institution-first source
label and the institutions ledger (`sources/institutions.yml`), so both the retrieval order and
the format below are load-bearing.

- **arXiv preprints — read the paper's own HTML author block.** Fetch
  `https://arxiv.org/html/<id>v1` THROUGH the fetch proxy and take the affiliations from the
  author block at the top of page 1 (~97% of new submissions render HTML; verified in
  production 2026-07-10, 10/10 papers). Do NOT use index APIs for preprints: Semantic Scholar
  has not indexed hours-old papers, and OpenAlex's arXiv records carry EMPTY institutions even
  once indexed (~6-day lag; measured 2026-07-10). If the HTML 404s (~3% of papers), write
  `(affiliation not listed)`.
- **bioRxiv / medRxiv preprints:** the details-API response you already fetch includes
  `author_corresponding_institution` — use it (no extra fetch).
- **Published papers (journal DOI) — OpenAlex:**
  `https://api.openalex.org/works?filter=doi:<doi>&select=authorships` returns resolved
  institution names (measured: complete for fresh Nature papers). On a miss, take them from
  the publisher/press page you are already reading; else the sentinel.
- **Budget: at most ONE extra fetch per selected paper.** Never web-search individual authors,
  never guess from an email domain or a lab's reputation — `(affiliation not listed)` is
  always the correct fallback; never fabricate.

**Byline format law** (parsed by `tools/dedup/dedup.py parse_affiliations` — deviations break
the join): after the author list, in parentheses — `AUTHORS (Inst1; Inst2; Inst3)`. `;`
separates institutions; `,` only qualifies within one name (`HKUST, Guangzhou`); at most 3
institutions, then `+N more`; canonical short names (`MIT`, `ETH Zürich`, `Google DeepMind` —
not full legal names); collective authors keep their name — `Gemma Team (Google DeepMind)`.
Example: `F. Last, A. Other et al. (MIT; CERN)`.

**Canonical names** — when a paper's author block uses a name on the LEFT, write the name on
the RIGHT (this list mirrors `sources/institutions.yml` `aliases:`; the ledger folds strays,
but the byline the reader sees should be canonical from the start):
<!-- canonical-names:begin — GENERATED from sources/institutions.yml; edit aliases there, then run `python3 tools/sources/institutions.py sync-prompts && python3 routines/assemble.py` -->
- `Qwen Team` → **Alibaba**
- `AI2` / `Ai2` → **Allen Institute for AI**
- `AWS` → **Amazon Web Services**
- `CAIS` → **Center for AI Safety**
- `Cohere For AI` / `Cohere Labs` → **Cohere**
- `MosaicML` → **Databricks**
- `DeepMind` → **Google DeepMind**
- `Google Brain` → **Google Research**
- `FAIR` / `Meta FAIR` → **Meta AI**
- `MSR` → **Microsoft Research**
- `JPL` / `Jet Propulsion Laboratory` → **NASA JPL**
- `PSI` → **Paul Scherrer Institute**
- `Shanghai AI Lab` → **Shanghai AI Laboratory**
- `Tencent AI Lab` → **Tencent**
- `Univ. of Illinois Urbana-Champaign` → **UIUC**
- `UK AI Safety Institute` → **UK AI Security Institute**
- `Z.ai` → **Zhipu AI**
<!-- canonical-names:end -->

**Step C:** copy the same institutions into each paper story's `"affiliations": ["MIT", "CERN"]`
field in final.json (omit the key when not listed) — the homepage card and the institutions
ledger read it from there (see DEDUP.md Step C).

**Anti-halo guard:** affiliations are recorded FOR THE READER, after selection — never as a
selection signal. Do not prefer a paper because a famous lab wrote it, and never demote one
because its affiliation is missing, independent, or unknown (LLM judges measurably over-reject
low-prestige affiliations — arXiv:2509.15122). Select on content.

**Reachable via the fetch-proxy (verified 2026-06-19) — USE these, don't skip them:** fetch with `tools/fetch.py --proxy`.
- bioRxiv / medRxiv → their JSON details API: `url=https://api.biorxiv.org/details/biorxiv/{YYYY-MM-DD}/{YYYY-MM-DD}/0` (swap `medrxiv`); returns title, abstract, DOI, and date per paper for the window — ideal for the Biology & Fundamental-science sections.
- Science.org → its RSS feeds (e.g. `https://www.science.org/rss/news_current.xml`, journal feeds); Science's article HTML 403s even through the proxy, so use the feed and cite the DOI / landing URL.

**Coverage footer accounting (computed at publish):** the telemetry numbers — tier split, direct-vs-snippet counts, word count, token estimate, `Feeds hit` — are computed by the publish command from your citations and `/tmp/fetch.log`; do not count them yourself. Your accounting duty is upstream accuracy: tag every snippet-only citation `[via snippet]`, and fetch only through the wrapper.

# Research methodology

The weekend brief warrants more aggressive iteration than the dailies. Per topic:
1. **Source plan first, then feed sweep.** Run the preflight (see Source plan above), then hit its fetch list via `tools/fetch.py` for the past 7 days (use the arXiv API with date filters; the Nature RSS feeds are rolling). This is your primary content source.
2. **Multi-pass search** for stories the feeds didn't surface. Start broad, refine 2–4 times, drill into specifics.
3. **Fetch full pages** liberally. arXiv abstracts (use the arXiv API — not the abstract HTML page, which 403s), full blog posts, GitHub READMEs, model cards. If fetch fails, fall back to snippets and tag with `[via snippet]`.
4. **Cross-reference rigorously.** For paper claims, locate the paper PDF if the abstract is ambiguous. Use Semantic Scholar API to triangulate citation/influence.
5. **Triangulate aggressively.** Significant findings should appear across at least 2 independent sources or be confirmable from primary docs.
6. **Don't trust your own first take.** Re-query with different framings to surface what your first query missed.
7. **Document exhausted leads** in the gaps footer.
8. **Sibling-brief consultation (do BEFORE tagging items `[single-source]`).** Read the daily briefs from the past 7 days, which now live in the local repo at `_posts/`. For each date D in {today-6, today-5, ..., today-1} (today=Saturday is the current run, so don't include it), check for `_posts/{D}-news.md`, `_posts/{D}-ai-ml.md`, `_posts/{D}-science.md`. Use the Read tool on each that exists. If any sibling brief covered the same story with multiple independent sources, do NOT tag it `[single-source]` here. (Note: sibling coverage informs sourcing/triangulation only — it is NOT a reason to drop or skip a story; see the dedup-relaxation note below.) If sibling briefs are unavailable, proceed and note in Gaps.

# Sections (in order)

## 📰 Week in headlines (short)
Brief recap, ~5 bullets. World + Switzerland combined. Just the things that mattered structurally.
Every bullet states what happened AND WHEN it happened — the date of the underlying event, not just
the date of the latest development. For a death, attack, ruling, or launch, name the event date
explicitly ("X died on {date}" / "the {date} strike"), even when the news peg is a later
funeral/anniversary/reaction. If the daily briefs carried the event date, carry it forward.

**Feed-first sources (curl first):** Al Jazeera RSS, SRF DE RSS, Le Temps FR RSS.

## 📄 ML / AI papers of the week (heaviest section)

**Feed-first sources (curl first):**
- **arXiv RSS per category**: `https://export.arxiv.org/rss/cs.LG`, `cs.AI`, `cs.CL`, `cs.CV`, `stat.ML`. Hit all five.
- **arXiv Atom API for week-window queries**: `https://export.arxiv.org/api/query?search_query=cat:cs.LG&start=0&max_results=100&sortBy=submittedDate&sortOrder=descending` — then filter the returned `<published>` dates client-side to the past 7 days.
- **Semantic Scholar** to triangulate which papers are getting attention this week.

T1 (HTML, often 403, fallback): arxiv.org listings, huggingface.co/papers, openreview.net.

Up to ~10 ML/AI papers — **quality is the cap, not the quota**: a 6-paper week of genuinely significant work beats 12 with filler. Rough bias when choosing among candidates (a tiebreaker, not a floor to fill):
- ~40% RL / agent / decision-making
- ~20% efficient inference, small models, on-device, MLX/quantization
- ~15% interpretability, mechanistic, alignment
- ~10% novel architectures (SSM/Mamba, hybrid, MoE)
- ~15% applied (anomaly detection, code, vision-language, multimodal)

For each paper:
- Title + arXiv ID + authors (first 3 + et al.) **with institutional affiliations per the Affiliations block above** — e.g. `F. Last, A. Other et al. (MIT; CERN)`; `(affiliation not listed)` when the chain misses.
- 3–5 sentence summary in your own words: contribution, method, key result.
- One line: "why this is interesting".
- Direct link to abstract.
- Tag `[preprint]` always for arXiv.

## 🔭 Fundamental science papers of the week

**Feed-first sources (curl first):**
- **arXiv API per category**, week-windowed: math.AG, math.AT, math.CO, math.NT, math.PR, math.ST; physics (cond-mat, hep-ph, hep-th, gr-qc, quant-ph, nucl-th); astro-ph.*.
- **Quanta Magazine RSS** — heavy weight here, math + fundamental physics.
- **Nature journals RSS**: nature.rss, nphys.rss (Nature Physics), natastron.rss (Nature Astronomy).

T1 (HTML, often 403, fallback): journals.aps.org (PRL, PRX, PRX Quantum), science.org, cern.ch/news, eso.org/public/news, nasa.gov/news.
T2: terrytao.wordpress.com, scottaaronson.blog, astrobites.org.

Up to ~8 papers across the fundamental sciences — quality is the cap; skip a category with nothing genuinely notable. Rough bias when choosing among candidates (a tiebreaker, not a floor to fill):
- ~30% physics (particle, condensed matter, hep, gravity)
- ~25% quantum (quant-ph, PRX Quantum)
- ~20% astronomy / astrophysics / cosmology
- ~15% mathematics (major proofs, conjecture progress, surveys)
- ~10% adjacent (chemistry, climate physics, computational)

For each paper, same format as ML papers section (including the affiliations element — same rules as the Affiliations block above, `(affiliation not listed)` when the chain misses, never fabricated). Math papers may need a 2-line "context" note.

## 🚀 Models & datasets released this week
T1: huggingface.co/models?sort=trending&period=7day, huggingface.co/datasets, lab announcement blogs, GitHub release pages.

Cover: notable open-weight releases, new SOTA on benchmarks, new datasets. For each: name, size/parameters, license, brief summary, link to model card. Include MLX/GGUF ports if any.

## 🍎 Apple Silicon / local inference ecosystem
T1: github.com/ml-explore/mlx/releases, github.com/ml-explore/mlx-lm/releases, github.com/ggerganov/llama.cpp/releases, machinelearning.apple.com.
What changed this week in MLX, llama.cpp, on-device inference. New benchmarks on M-series silicon. New quantization techniques.

## 🧬 Biology, biotech, neuroscience

**Feed-first sources (curl first):**
- **Nature Methods RSS**: `https://www.nature.com/nm.rss`.
- **Quanta Magazine RSS** — covers biology features.

T1 (HTML, often 403, fallback): nature.com, science.org, cell.com, nejm.org. (bioRxiv/medRxiv: use their JSON API via the proxy — see "Reachable via the fetch-proxy" above; Science via its RSS.)
T2: asimov.press, statnews.com, endpts.com, neurosciencenews.com.

Up to ~8 items — only what's genuinely notable; a 3-item week is a valid week.

## 📊 Data science / applied ML
T1: company engineering blogs (Netflix, Uber, Airbnb, Stripe, Spotify), papers with code releases.
T2: thegradient.pub, eugeneyan.com, chiphuyen.com, hamel.dev, fast.ai.

Real production ML, evaluation methodology, lessons from deployment, useful tools. Skip Medium / Towards Data Science.

## 📝 Essays & long-form
T1/T2: simonwillison.net, karpathy.bearblog.dev, dnhkng.github.io, lilianweng.github.io, gwern.net, distill.pub, quantamagazine.org features (RSS via curl), lesswrong.com (high-karma posts), acoup.blog, drbex.io.

Long-form pieces published this week, up to ~8 — only pieces you'd actually recommend; skip the rest. Each: title, author, 2–3 sentence summary, your read on whether it's worth the time.

## 🧠 Cross-cutting threads (the payoff — give it real effort)
2–4 themes you noticed across this week's content, each developed in a substantial paragraph: what connects the items, what it implies, what to watch next. This synthesis is the single highest-value part of the Weekend brief — the one thing aggregation cannot do — and it renders near the top of the published brief, so write it like the lead it is, not an afterthought.

**Ground it in the analytical plane before writing** (same worker + bearer as the dedup check —
the `EMBED_WORKER_URL`/`EMBED_TOKEN` values in `tools/dedup/DEDUP.md` Step A; best-effort, skip
silently on failure):

```bash
curl -s -XPOST "$EMBED_WORKER_URL/plane/entities" -H "Authorization: Bearer $EMBED_TOKEN" \
  -H 'Content-Type: application/json' -d '{"days":10}'          # who/what recurred this week
curl -s -XPOST "$EMBED_WORKER_URL/plane/thread" -H "Authorization: Bearer $EMBED_TOKEN" \
  -H 'Content-Type: application/json' -d '{"key":"<thread_id>"}' # a candidate theme's real arc
```

An entity spanning multiple streams, or a thread that developed several times this week, is a
cross-cutting candidate the data can PROVE — use the timelines to anchor dates and sequence.
Your judgment still picks and develops the themes; the plane keeps the claims honest.

# Format

```
# Weekend Deep Read — {YYYY-MM-DD}

_Coverage: {date 7 days ago} to {today}. Generated {timestamp} Europe/Zurich._

## 📰 Week in headlines
- ...

## 📄 Papers of the week

### [Paper title]
**[arXiv:XXXX.XXXXX](URL)** · F. Last, A. Other et al. (MIT; CERN) · `[preprint]`
3–5 sentence summary.
*Why this matters:* one-line take.

[... all sections ...]

---

## Coverage footer
<!-- operational telemetry — the computed lines (tier split, direct-vs-snippet, word count,
token estimate, Feeds hit) are filled in by the publish command (tools/footer.py); write ONLY:
- Languages: {languages of your cited sources, e.g. EN, FR, DE}
-->
- Sibling consultation: {performed | skipped — reason}
- Gaps: ...
- Things I deliberately cut: ...
- Discovery: {met (<new domain(s) anchored>) | waived — <concrete reason>}
```

# Constraints

- Length target: long. 4000–8000 words.
- Paper summaries in your own words. Never copy abstract text directly.
- If you'd cite an X/Twitter thread or HN comment, find the actual paper or blog post and cite that.
- The cross-cutting threads section is the one place you should be opinionated. Elsewhere stay descriptive.
- Don't pad. If a section has 3 strong items and 5 weak, ship the 3.

# Pedagogical tone (added 2026-05-30 per user feedback)

The reader is technically literate but not a specialist in every subfield this brief touches. Reduce jargon density without dumbing down the content. **This applies to ALL sections — ML, math/physics/astro, biology, chemistry — not just AI/ML acronyms.**

1. **First-use gloss for acronyms / terms of art.** First time any specialist term appears in a brief, append a 3–8 word plain gloss in parentheses or em-dashes. Reuse without gloss after.
   - ML examples: RLHF, RLVR, MoE, KV-cache, SSM/Mamba, DPO, SAE, CoT, RAG, SFT, LoRA, BLEU, FID, MMLU.
   - Physics/math examples: gauge symmetry, anomaly cancellation, sheaf cohomology, RG flow, BKT transition, AdS/CFT, Bell inequality violation.
   - Bio examples: CRISPR base editor, antisense oligonucleotide, GWAS, p-value vs effect size, immunopeptidomics, organoid.
2. **One-line context for unfamiliar subfields.** "Diffusion priors for inverse problems in MRI reconstruction" → needs a clause on what an inverse problem is or why MRI reconstruction is hard. A CVE in "BGP path validation" → needs a clause on what BGP path validation does. A paper on "non-Hermitian skin effect in photonic lattices" → needs a clause on what the skin effect is.
3. **Concrete over abstract.** "Beats baseline by 2 BLEU on WMT" → "Beats baseline by 2 BLEU on WMT (standard machine-translation benchmark; ~2 pts is a real improvement, not chart-padding)." "CVSS 9.8" → "CVSS 9.8 (critical; trivially exploitable, full system compromise)."
4. **Why-it-matters in plain language.** Every paper / benchmark / release: one sentence on why the reader should care, framed in lay terms — what becomes possible, what risk it raises, what assumption it overturns.
5. **Keep the technical claim precise.** Gloss alongside the term, don't replace it. Single-sentence parentheticals are the sweet spot; longer explanations belong in the per-paper summary, not the bullet headline.
6. **Hardest case: pure-math / hep-th / quant-ph results — explain anyway, don't punt.** These are exactly the results the reader most wants decoded, so do NOT fall back on "this is too technical to summarize." For every such result deliver at minimum: (a) the one-sentence stakes — what longstanding question, barrier, or conjecture it touches and why anyone should care; (b) a concrete anchor — an analogy, a physical picture, or a "think of X as Y" a numerate non-specialist can hold onto; (c) the honest scope — what is genuinely new versus already known. Mine the intuition from a Quanta/secondary writeup, the paper's own intro/abstract framing, or the author's plain-language motivation, and cite it. Only as a true last resort, when no plain-language framing exists in ANY reachable source, name the precise step that resists explanation (e.g. "the novelty is a cohomological obstruction argument I can't fairly compress") instead of emitting an undecoded jargon string — and treat that as a failure to minimize, not a routine escape hatch.

# Story deduplication (best-effort — never abort the brief on failure)

Before composing AND after writing the brief, follow `tools/dedup/DEDUP.md` exactly. It dedupes your candidate stories against the rolling embeddings index so a story isn't re-run for days. **This routine's slug is `weekend`.** If any dedup step errors, compose normally and note "dedup unavailable" in the Gaps footer.

**Weekend dedup is deliberately scoped to Weekend's own history.** Weekend exists to revisit the week's most important stories *in depth*, so a daily edition having already touched a story is expected — not a reason to drop it. Per `DEDUP.md` Step A, **append `--only-slug weekend` to the check command** so dedup compares your candidates ONLY against prior *Weekend* editions: a `news`/`ai-ml`/`science` story from earlier this week therefore never comes back as a REPEAT — it's exactly the story to revisit and go deeper than the daily did. Then apply the Step-B verdicts normally — with the flag, any REPEAT is a genuine prior-Weekend repeat to skip, so no special-casing is needed.

# Date discipline (read before writing any date, weekday, or scheduled event)

You derive "today" from the machine-stamped `_Generated <ISO> Europe/Zurich_` header — that part is reliable. The errors come from *arithmetic on top of it* (counting forward to a weekday; re-guessing which Sunday a vote falls on). So before composing:

1. **Build a dated weekday table for the coverage window (today ±7 days) and read every weekday↔date reference off it — never count forward in your head.** Shape: `… Sat 2026-06-13 · Sun 06-14 · Mon 06-15 · Tue 06-16 · Wed 06-17 · Thu 06-18 (today) · Fri 06-19 …`. (The `lint` WEEKDAY check rejects an adjacent weekday/date mismatch, e.g. "Wednesday 11 June" when the 11th is a Thursday.)
2. **Scheduled / dated events (votes, IPO pricings, conferences, deadlines, embargoes): state the ABSOLUTE date, and do NOT re-derive it.** If the dedup `check` returned a `matched.event_date` for the story, use *that* date verbatim — it is the date the pipeline already established and carries forward. Never re-guess "which Sunday / this weekend / tomorrow / next week." (A 2026-06-06 brief misdated the 14-June federal vote to "Sunday 7 June" by reasoning "it's a Sunday vote and it's the weekend → this Sunday" instead of reading the established 14-June date.)
3. **Never write relative framing** — "this weekend", "tomorrow", "next week", "in N days" — **for a dated event without the absolute date right beside it.** (The `lint` SCHEDULE check flags bare relative framing.)
4. When you `record` the stories you kept, put each event's real date in its `event_date` field whenever you know it — that is what carries the correct date forward to future briefs.

# Output: write the brief to git + drop a notification stub + email digest

This routine writes to the git repo (working directory is the cloned `claude-routines` repo). It does NOT write to Google Drive and does NOT POST to ntfy directly. A local bridge on the user's machine polls `pending-notifications/` every ~10 min and handles the ntfy push.

Individual brief pages are retired (2026-07-18): the homepage story feed at
`https://khalic-lab.github.io/claude-routines/` carries every story's full prose, and the
notification stub the publish command writes clicks through there.

### 1. Write the brief

Use the Write tool to create `_posts/{YYYY-MM-DD}-weekend.md`. The file MUST start with this front-matter block, then a blank line, then the brief body:

```
---
layout: single
title: "Weekend Deep Read — {YYYY-MM-DD}"
date: {full ISO 8601 timestamp WITH timezone offset, identical to the _Generated line — e.g. 2026-06-21T09:39:44+02:00; NOT a bare date, which makes same-day briefs sort out of chronological order}
categories: [weekend]
---
```

### 2. Publish — one command

Everything after the brief file is deterministic and runs through the orchestrator: dedup record → anchors → computed footer telemetry → source lint → registry/institutions sync → date lint → homepage feed + stats → source health → notification stub → commit → push, with the homefeed rebase-conflict retry built in.

```bash
python3 tools/publish.py --slug weekend --date {YYYY-MM-DD} \
  --final /tmp/final.json \
  --notify-title "Weekend Deep Read — {YYYY-MM-DD}" \
  --notify-body "{teaser}" --notify-tags calendar
```

- `{teaser}` rules: ≤200 chars. Most interesting item of the week — typically the headline ML paper or a striking cross-cutting thread. Concrete and specific (e.g. "3 papers converge on test-time compute scaling; new RLVR method beats baselines"), not generic. Pass it as a normal shell argument — the stub is JSON-encoded for you, no manual quote-escaping.
- If dedup was unavailable (Step A failed), omit `--final` — every other step still runs; note "dedup unavailable" in the Gaps line before publishing.
- The orchestrator prints one OK/FAIL line per step and, if the final push fails after its built-in retry, notes it in the brief itself. Do not re-run the git steps by hand, and do not write the stub or telemetry yourself.

### 3. Email digest

Note: the Gmail MCP surface is `create_draft` only — there is no send tool.

- **To:** rflnogueira@me.com
- **Subject:** "Weekend Deep Read — {YYYY-MM-DD}"
- **Body:** ~500–700 words, plain text or simple markdown:
  - Top 3 ML papers (title + arXiv ID + 1-sentence why-it-matters)
  - Top 2 fundamental science papers (same format)
  - Most notable model/dataset release of the week (1–2 sentences)
  - Top essay/long-form (title, author, 1-sentence read)
  - The full Cross-cutting threads section verbatim if it's <300 words; else condense to 2–3 sentences
  - End with: `All stories: https://khalic-lab.github.io/claude-routines/`
- If `create_draft` fails, retry once. If still failing, append `email draft creation failed: <reason>` to this brief's Coverage footer in git but don't fail the run.
