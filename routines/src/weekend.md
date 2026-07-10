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

<!-- include: _shared/newsroom-ethos.md -->

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

<!-- include: _shared/reader-profile-source-weights.md -->

<!-- include: _shared/feed-first-source-order.md -->

The HTML pages of most quality sources return HTTP 403 from this routine sandbox. Many of those publishers also offer machine-readable feeds (RSS, Atom, JSON) that are reachable. **Always attempt the feed/API before the HTML page.**

**CRITICAL — try Bash{curl} BEFORE WebFetch.** WebFetch in this sandbox has been observed returning HTTP 403 on public, machine-readable feeds (arXiv RSS, arXiv Atom API, Nature RSS, etc.). When attempting any feed from the preflight plan, FIRST try via Bash with `curl -fsSL <URL>`, parse the response, and only fall back to WebFetch if curl also fails. A successful curl fetch counts as a direct fetch. This is the binding-constraint workaround for the 403 wall.

**Order of attempts per topic, in priority:**
1. Feed from the preflight plan (or arXiv/Semantic Scholar APIs) via Bash{curl}.
2. Same feed via WebFetch fallback.
3. The publisher's HTML page (proxy on 403).
4. Web search snippet (last resort, tag the citation `[via snippet]`).

**arXiv / Semantic Scholar mechanics:** the date-filtered arXiv Atom API (`https://export.arxiv.org/api/query?search_query=cat:cs.LG&start=0&max_results=30&sortBy=submittedDate&sortOrder=descending`) works for `math.*`, `physics.*`, `astro-ph.*` too — swap the `cat:` filter and window the `<published>` dates client-side. Semantic Scholar: `https://api.semanticscholar.org/graph/v1/paper/search?query=...&fields=title,abstract,year,authors,authors.affiliations` (triangulation, citation counts, affiliations).

**Reachable via the fetch-proxy (verified 2026-06-19) — USE these, don't skip them:** route through the proxy.
- bioRxiv / medRxiv → their JSON details API: `url=https://api.biorxiv.org/details/biorxiv/{YYYY-MM-DD}/{YYYY-MM-DD}/0` (swap `medrxiv`); returns title, abstract, DOI, and date per paper for the window — ideal for the Biology & Fundamental-science sections.
- Science.org → its RSS feeds (e.g. `https://www.science.org/rss/news_current.xml`, journal feeds); Science's article HTML 403s even through the proxy, so use the feed and cite the DOI / landing URL.

**Coverage footer accounting:**
- A citation that came from a feed/API fetch (curl OR WebFetch) counts as a **direct fetch**.
- A citation built from a search-engine snippet counts as **via-snippet** and must be tagged `[via snippet]`.
- In the `Feeds hit` line, distinguish between `{ok via curl}`, `{ok via WebFetch}`, and `{fail — HTTP NNN}`.

# Research methodology

The weekend brief warrants more aggressive iteration than the dailies. Per topic:
1. **Source plan first, then feed sweep.** Run the preflight (see Source plan above), then hit its fetch list via Bash{curl} for the past 7 days (use the arXiv API with date filters; the Nature RSS feeds are rolling). This is your primary content source.
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
- Title + arXiv ID + authors (first 3 + et al.) **with institutional affiliations when cheaply retrievable** — e.g. `F. Last, A. Other et al. (MIT; CERN)`. Order: arXiv `<arxiv:affiliation>` → Semantic Scholar `authors.affiliations` (ONE attempt; skip on 429/400/not-indexed) → OpenAlex works API (`api.openalex.org/works?search=<title>`). If all three miss, `(affiliation not listed)` and move on — never fabricate, never web-search individual authors.
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

For each paper, same format as ML papers section (including the best-effort affiliations chain — arXiv `<arxiv:affiliation>` → Semantic Scholar → OpenAlex, `(affiliation not listed)` if all miss, never fabricated). Math papers may need a 2-line "context" note.

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
<!-- operational telemetry — machine/evaluator-read; hidden from the rendered page
- Sources used: T1 = N, T2 = N, T3 = 0
- Languages: EN, FR, DE, ...
- Direct fetches: N | via-snippet citations: N
- Word count: N (body, excl. footer) | research tool calls (curl/WebSearch/WebFetch): N
- Feeds hit (with reachability and method): {each feed/API attempted from the preflight plan — arXiv RSS/API, Quanta RSS, Nature journals RSS, Al Jazeera, …} {ok via curl|ok via WebFetch|ok via proxy|fail — HTTP NNN}
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

<!-- include: _shared/pedagogical-tone.md -->

# Story deduplication (best-effort — never abort the brief on failure)

Before composing AND after writing the brief, follow `tools/dedup/DEDUP.md` exactly. It dedupes your candidate stories against the rolling embeddings index so a story isn't re-run for days. **This routine's slug is `weekend`.** If any dedup step errors, compose normally and note "dedup unavailable" in the Gaps footer.

**Weekend dedup is deliberately scoped to Weekend's own history.** Weekend exists to revisit the week's most important stories *in depth*, so a daily edition having already touched a story is expected — not a reason to drop it. Per `DEDUP.md` Step A, **append `--only-slug weekend` to the check command** so dedup compares your candidates ONLY against prior *Weekend* editions: a `news`/`ai-ml`/`science` story from earlier this week therefore never comes back as a REPEAT — it's exactly the story to revisit and go deeper than the daily did. Then apply the Step-B verdicts normally — with the flag, any REPEAT is a genuine prior-Weekend repeat to skip, so no special-casing is needed.

<!-- include: _shared/date-discipline.md -->

# Output: write the brief to git + drop a notification stub + email digest

This routine writes to the git repo (working directory is the cloned `claude-routines` repo). It does NOT write to Google Drive and does NOT POST to ntfy directly. A local bridge on the user's machine polls `pending-notifications/` every ~10 min and handles the ntfy push.

Let `{POST_URL} = https://khalic-lab.github.io/claude-routines/{YYYY}/{MM}/{DD}/weekend/`.

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

### 2. Write the notification stub

Use the Write tool to create `pending-notifications/{TIMESTAMP}-weekend.json` where `{TIMESTAMP} = $(date -u +%Y%m%dT%H%M%SZ)`. Content (all four fields required, valid JSON, no trailing content):

```json
{
  "title": "Weekend Deep Read — {YYYY-MM-DD}",
  "click": "{POST_URL}",
  "body": "{teaser}",
  "tags": "calendar"
}
```

`{teaser}` rules: ≤200 chars. Most interesting item of the week — typically the headline ML paper or a striking cross-cutting thread. Concrete and specific (e.g. "3 papers converge on test-time compute scaling; new RLVR method beats baselines"), not generic. Escape any `"` inside the teaser as `\"`.

### 3. Commit and push

Via Bash:

```bash
# refresh the homepage feed HERE, unconditionally — not only via DEDUP.md Step D — so a skipped
# step can't freeze the front page while the commit still stages a stale _data/
python3 tools/build_stories_feed.py || echo "feed build failed (non-fatal)"
python3 tools/sources/health.py || echo "source health failed (non-fatal)"
git add _posts/ pending-notifications/ index/ _data/ sources/
git -c user.email=routine@khalic-lab -c user.name="News Routine" commit -m "Weekend Deep Read — {YYYY-MM-DD}"
git push origin main || (
  # Concurrent editions (News + AI/ML fire the same minute Tue/Fri) both rewrite the whole
  # _data/homefeed.json, so the rebase can stop on a content conflict there. The resolution is
  # always: REGENERATE the feed from the merged tree (it now has both briefs), then continue.
  git pull --rebase origin main || true
  python3 tools/build_stories_feed.py || true
  python3 tools/sources/health.py || true
  git add _data/
  GIT_EDITOR=true git rebase --continue \
    || git -c user.email=routine@khalic-lab -c user.name="News Routine" commit --amend --no-edit \
    || true
  git push origin main
)
```

If `git push` still fails after the rebase retry, append `git push failed: <reason>` to the brief's Coverage footer and continue.

### 4. Email digest

Note: the Gmail MCP surface is `create_draft` only — there is no send tool.

- **To:** rflnogueira@me.com
- **Subject:** "Weekend Deep Read — {YYYY-MM-DD}"
- **Body:** ~500–700 words, plain text or simple markdown:
  - Top 3 ML papers (title + arXiv ID + 1-sentence why-it-matters)
  - Top 2 fundamental science papers (same format)
  - Most notable model/dataset release of the week (1–2 sentences)
  - Top essay/long-form (title, author, 1-sentence read)
  - The full Cross-cutting threads section verbatim if it's <300 words; else condense to 2–3 sentences
  - End with: `Full brief: {POST_URL}`
- If `create_draft` fails, retry once. If still failing, append `email draft creation failed: <reason>` to this brief's Coverage footer in git but don't fail the run.
