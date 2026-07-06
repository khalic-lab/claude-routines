Write my weekly science brief and publish it via the git pipeline. Use today's date (Wednesday) in Europe/Zurich.

The repo (`khalic-lab/claude-routines`) is cloned as your working directory. Before doing anything else, sync:

```bash
git pull --ff-only origin main
```

# Mission

A weekly read on the most significant developments across the natural sciences — physics, math, quantum, astronomy/cosmology, biology/medicine/neuroscience, chemistry, climate/earth. Coverage window: the past 7 days.

This is NON-AI science. **EXCLUDE AI/ML and computer science** — arXiv `cs.*` / `stat.ML` and ML preprints belong to the AI/ML edition, not here. A result is in scope only if its primary contribution is to a natural science, not to machine learning or CS (a physics paper that *uses* an ML method is fine; an ML-methods paper applied to physics is not).

Three desks, deep over broad: pick the week's genuinely-new findings, read the primary papers, and decode them for a numerate non-specialist. Better to go deep on a handful of real results than to skim a feed.

<!-- include: _shared/newsroom-ethos.md -->

# Sourcing rules (non-negotiable)

1. **Tiers.** T1 = primary (preprint, journal research article, official lab/observatory/agency release). T2 = quality secondary. T3 = discovery only (HN/Reddit/Lobsters/X) — used to find stories, NEVER cited. Click through and cite the underlying T1/T2. **A quality outlet's news report or feature *about* a study is T2 secondary, never T1 — even when that outlet also publishes primary research.** Nature news/features (URLs of the form `nature.com/articles/d41586-…`) are journalism about papers, not the papers themselves; the primary source is the underlying paper (`nature.com/articles/s41586-…`) or its preprint. When you cover a study, locate and cite that **primary paper** — read its abstract — and use the news write-up only as a secondary pointer or for triangulation. A bullet whose sole citation is a `d41586` Nature-news piece (or any equivalent secondary report) is mis-sourced: find the paper, or if you genuinely cannot, frame it as 'as reported by …' and tag `[single-source]` — never present secondary journalism as the primary.
2. **Citation format.** Every item ends with a markdown link to one specific URL (DOI, arXiv abstract, or article landing). Include publication name and date. No "according to recent reports" without a link.
3. **Triangulation.** Significant claims need two independent sources where feasible. Single-sourced → mark `[single-source]`. Disagreements → surface both versions explicitly.
4. **Diversification.** Within each desk, span subfields and institutions; don't let one journal or one lab dominate.
5. **Tags.** Preprints → `[preprint]`. Single source → `[single-source]`. Contested → `[disputed]`.
6. **No fabrication.** Never invent a URL, author, date, or quote. **The no-fabrication rule extends to date claims**: a paper from last month is NOT "this week's." If you cannot verify a paper was submitted or published within the past 7 days, do not include it under a section that claims this week's content.
7. **Volume cap.** 4–8 items per desk. Quality is the cap — better to ship 3 strong findings in a desk than pad to 8.
8. **Fetch transparency.** When you successfully fetch a URL/feed and confirm content, no marker. When the citation is based only on a search-engine snippet, append `[via snippet]` to the citation.

<!-- include: _shared/reader-profile-source-weights.md -->

<!-- include: _shared/feed-first-source-order.md -->

The HTML pages of most quality sources return HTTP 403 from this routine sandbox. Always attempt the feed/API before the HTML page.

**CRITICAL — try Bash{curl} BEFORE WebFetch.** WebFetch in this sandbox has been observed returning HTTP 403 on public feeds. Try `curl -fsSL <URL>` first; fall back to WebFetch only on failure. Curl success counts as a direct fetch.

**Verified-reachable feeds (live 2026-05-04):**

| Domain | Feed URL | Format | Use case |
|---|---|---|---|
| arXiv non-CS categories | `https://export.arxiv.org/rss/astro-ph` (also `math.*`, `physics.*`, `cond-mat`, `hep-ph`, `hep-th`, `gr-qc`, `quant-ph`, `q-bio.*`) | RSS 2.0 | Latest non-CS preprints per category |
| arXiv API (date-filtered) | `https://export.arxiv.org/api/query?search_query=cat:astro-ph.CO&start=0&max_results=30&sortBy=submittedDate&sortOrder=descending` — **swap the `cat:` filter** for any non-CS category | Atom 1.0 | Date-confirmable queries; filter `<published>` to the past 7 days |
| Quanta Magazine | `https://www.quantamagazine.org/feed/` | RSS 2.0 | Math + fundamental-physics + biology features |
| Nature (flagship + journals) | `https://www.nature.com/nature.rss` (also `nphys.rss`, `natastron.rss`, `nm.rss`, `nchem.rss`) | RSS | Nature primary research (dig to `s41586-…`, not `d41586-…` news) |
| Semantic Scholar API | `https://api.semanticscholar.org/graph/v1/paper/search?query=...&fields=title,abstract,year,authors,authors.affiliations` | JSON | Paper triangulation + author affiliations |

**Reachable via the fetch-proxy (verified 2026-06-19) — USE these, don't skip them:** route through the proxy exactly as the include above shows.
- bioRxiv / medRxiv → their JSON details API: `url=https://api.biorxiv.org/details/biorxiv/{YYYY-MM-DD}/{YYYY-MM-DD}/0` (swap `medrxiv` for medRxiv); returns title, abstract, DOI, and date per paper for the window — an ideal primary source for the Biology desk.
- Science.org → its RSS feeds (e.g. `https://www.science.org/rss/news_current.xml`, plus journal feeds); Science's article HTML 403s even through the proxy, so use the feed and cite the DOI / article landing URL.

**APS journals** (`journals.aps.org` — PRL / PRX / PRX Quantum): try the recent-articles RSS via curl; if it 403s, proxy the recent-articles page. Cite the article DOI / landing URL.

**Nature-abstract fallback (Patch-4):** when a Nature primary research item (`s41586-…`) has no fetchable abstract from the sandbox, locate the matching arXiv cross-list preprint (search the title via the arXiv API / Semantic Scholar) and summarise *that*, tagged `[preprint]` — do NOT emit a title-only stub.

**Confirmed unavailable from this sandbox (do not waste cycles):** HuggingFace papers (no public feed), Reuters, Le Monde RSS. (bioRxiv/medRxiv and Science.org are reachable via the proxy / JSON API above — use them.)

**Coverage footer accounting:**
- A citation from a feed/API fetch (curl OR WebFetch OR proxy) = **direct fetch**.
- A citation from a search-engine snippet = **via-snippet**, tag `[via snippet]` in the item.
- In the `Feeds hit` line, distinguish `{ok via curl}` / `{ok via WebFetch}` / `{ok via proxy}` / `{fail — HTTP NNN}`.

# Affiliations (every paper / journal item)

For every paper, after the author list, surface the lead authors' institutional affiliations from the Semantic Scholar `authors.affiliations` field (fall back to the arXiv Atom `<author><arxiv:affiliation>` when populated). If no affiliation is retrievable, write `(affiliation not listed)` — never fabricate. Format: after the authors, in parentheses — e.g. `J. Doe, A. Smith et al. (ETH Zürich; CERN)`. The Semantic Scholar URL in the feed table already carries `&fields=…,authors,authors.affiliations`; use it as shown so the field is actually returned.

# Research methodology

1. **Feed sweep first** per desk, via curl then WebFetch then proxy. Use the arXiv API with date filters; the Nature / Quanta / Science RSS feeds are rolling — filter to the past 7 days client-side.
2. **Broad query** (1–2 keywords). Scan results.
3. **Refine and re-query** based on what surfaced.
4. **Fetch full pages / abstracts** for findings that matter (use the arXiv API for abstracts — the abstract HTML page 403s); on failure, snippet + tag.
5. **Cross-reference** significant claims; use Semantic Scholar to triangulate which results are getting attention this week.
6. **Stop when triangulated** or leads exhausted.

# Sections (in order — OMIT any desk with no genuinely-new content this week)

## 🔭 Physics, chemistry, math & quantum

T1: `journals.aps.org` (PRL / PRX / PRX Quantum), nature.com primary research (`s41586-…`, `nphys.rss` via curl — the papers, NOT `d41586` news), science.org research articles (RSS via proxy), **non-CS arXiv via the Atom API** (`math.*`, `physics.*` incl. `physics.chem-ph` / `physics.ao-ph` / `physics.geo-ph`, `cond-mat`, `hep-ph`, `hep-th`, `gr-qc`, `quant-ph` — swap the `cat:` filter), nature.com Nature Chemistry (`nchem.rss` via curl), cern.ch/news.
T2: **quantamagazine.org (RSS via curl — heavy weight for math + fundamental physics)**, terrytao.wordpress.com, scottaaronson.blog, spectrum.ieee.org.
Coverage: particle physics, condensed matter, quantum information (quant-ph, PRX Quantum), gravity/GR, chemistry (physical / materials chemistry), earth & climate-system science, plus mathematics (major proofs, conjecture progress, notable surveys). Exclude anything whose home is `cs.*` / `stat.ML`.

## 🧬 Biology, medicine & neuroscience

**Feed-first (curl/proxy first):** bioRxiv / medRxiv JSON details API via the proxy, Nature Methods RSS (`nm.rss` via curl), Quanta RSS (biology features).
T1: nature.com primary research, science.org research (RSS via proxy), cell.com, nejm.org, biorxiv.org / medrxiv.org (JSON API via proxy), `q-bio.*` arXiv.
T2: statnews.com, endpts.com, neurosciencenews.com, asimov.press.
Coverage: drug approvals and clinical-trial readouts, genomics, structural and molecular biology, neuroscience, biotech. Flag preliminary / small-sample / unreplicated results as such — don't upgrade them.

## 🌌 Astronomy & cosmology

**Feed-first (curl first):** Nature Astronomy RSS (`natastron.rss`), `astro-ph.*` via the arXiv Atom API, Quanta RSS.
T1: nasa.gov/news, eso.org/public/news, esa.int/Newsroom, nature.com primary, `astro-ph.*` arXiv (CO/GA/EP/HE/SR/IM).
T2: skyandtelescope.org, astrobites.org, quantamagazine.org.
Coverage: JWST and other space telescopes, ESO/ALMA, exoplanets, cosmology, gravitational waves, solar-system science.

## 🧠 Why it matters (optional — only if warranted)

1–2 synthesis threads across the week's science: a connection between findings, a shifting consensus, a method that's spreading across fields. This is the one place to be opinionated. Omit entirely if no genuine cross-cutting thread emerged — do not manufacture one.

# Format

```
# Science — {YYYY-MM-DD}

_Generated {ISO timestamp} Europe/Zurich. Coverage: {date 7 days ago} to {today}._

## 🔭 Physics, chemistry, math & quantum

### [Finding / paper title]
**[arXiv:2606.XXXXX](URL)** or **[Nature](DOI/landing URL)** · J. Doe, A. Smith et al. (ETH Zürich; CERN) · `[preprint]` (arXiv only)
2–4 sentence summary in your own words: what's new, the method, the key result. Math/hep-th/quant-ph results get the (a) stakes / (b) concrete anchor / (c) honest-scope treatment from the pedagogical-tone rules — don't punt.
*Why it matters:* one-line plain-language take.

## 🧬 Biology, medicine & neuroscience
[same item format]

## 🌌 Astronomy & cosmology
[same item format]

## 🧠 Why it matters
- ...

---

## Coverage footer
- Sources used: T1 = N, T2 = N, T3 = 0
- Items: N (filtered from M reviewed) — Physics/math/quantum: N, Biology/medicine/neuro: N, Astronomy/cosmology: N
- Languages: ...
- Direct fetches: N | via-snippet citations: N
- Word count: N (body, excl. footer) | research tool calls (curl/WebSearch/WebFetch): N
- Feeds hit (with reachability and method): Nature RSS {ok via curl|ok via WebFetch|ok via proxy|fail — HTTP NNN}, Nature Physics/Astronomy/Methods RSS {...}, Quanta RSS {...}, arXiv API astro-ph {...}, arXiv API math/physics {...}, APS PRL/PRX {...}, bioRxiv JSON {...}, Science.org RSS {...}, Semantic Scholar {...}
- Gaps: things you tried to find but couldn't.
```

# Constraints

- **EXCLUDE AI/ML and CS.** No `cs.*` / `stat.ML` preprints, no ML-methods papers, no AI-lab releases — those are the AI/ML edition's. A natural-science result that merely uses ML is in scope; an ML result dressed in a science application is not.
- Numbers and identifiers matter: include arXiv IDs and DOIs, and the submission/publication date next to each item.
- Length: 1500–3000 words (weekly window, three focused desks). Don't pad — if a desk has 3 strong items, ship the 3.
- Write in English. French/German source titles can stay in original language inside link text.
- Discovery aggregators (HN, Reddit, Lobsters, X) → never cited as source.

<!-- include: _shared/pedagogical-tone.md -->

# Story deduplication (best-effort — never abort the brief on failure)

Before composing AND after writing the brief, follow `tools/dedup/DEDUP.md` exactly. It dedupes your candidate stories against the rolling embeddings index so a story isn't re-run for days. **This routine's slug is `science`.** If any dedup step errors, compose normally and note "dedup unavailable" in the Gaps footer.

<!-- include: _shared/date-discipline.md -->

# Output: write the brief to git + drop a notification stub

This routine writes to the git repo (working directory is the cloned `claude-routines` repo). It does NOT write to Google Drive, does NOT POST to ntfy directly, and does NOT send email. A local bridge polls `pending-notifications/` every ~10 min and handles the ntfy push.

Let `{POST_URL} = https://khalic-lab.github.io/claude-routines/{YYYY}/{MM}/{DD}/science/`.

### 1. Write the brief

Use the Write tool to create `_posts/{YYYY-MM-DD}-science.md`. The file MUST start with this front-matter block, then a blank line, then the brief body:

```
---
layout: single
title: "Science — {YYYY-MM-DD}"
date: {full ISO 8601 timestamp WITH timezone offset, identical to the _Generated line — e.g. 2026-06-24T17:09:59+02:00; NOT a bare date, which makes same-day briefs sort out of chronological order}
categories: [science]
---
```

### 2. Write the notification stub

Use the Write tool to create `pending-notifications/{TIMESTAMP}-science.json` where `{TIMESTAMP} = $(date -u +%Y%m%dT%H%M%SZ)`:

```json
{
  "title": "Science — {YYYY-MM-DD}",
  "click": "{POST_URL}",
  "body": "{teaser}",
  "tags": "microscope"
}
```

`{teaser}` rules: ≤200 chars. The single most striking finding in this brief — typically the headline physics/quantum result, a major astronomy discovery, or a notable clinical/biology readout. Concrete and specific (e.g. "JWST resolves the missing-baryon problem; PRX Quantum demo of below-threshold error correction on 105 qubits"), not generic. Escape any `"` inside the teaser as `\"`.

### 3. Commit and push

```bash
# refresh the homepage feed HERE, unconditionally — not only via DEDUP.md Step D — so a skipped
# step can't freeze the front page while the commit still stages a stale _data/
python3 tools/build_stories_feed.py || echo "feed build failed (non-fatal)"
git add _posts/ pending-notifications/ index/ _data/
git -c user.email=routine@khalic-lab -c user.name="News Routine" commit -m "Science — {YYYY-MM-DD}"
git push origin main || (
  # Concurrent editions (News + AI/ML fire the same minute Tue/Fri) both rewrite the whole
  # _data/homefeed.json, so the rebase can stop on a content conflict there. The resolution is
  # always: REGENERATE the feed from the merged tree (it now has both briefs), then continue.
  git pull --rebase origin main || true
  python3 tools/build_stories_feed.py || true
  git add _data/homefeed.json
  GIT_EDITOR=true git rebase --continue \
    || git -c user.email=routine@khalic-lab -c user.name="News Routine" commit --amend --no-edit \
    || true
  git push origin main
)
```

If `git push` still fails after the rebase retry, append `git push failed: <reason>` to the brief's Coverage footer and continue.
