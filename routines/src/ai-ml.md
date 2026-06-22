Write my AI/ML industry brief and publish it via the git pipeline. Use today's date in Europe/Zurich.

The repo (`khalic-lab/claude-routines`) is cloned as your working directory. Before doing anything else, sync:

```bash
git pull --ff-only origin main
```

# Mission

Today's AI/ML industry activity, lab releases, and ecosystem moves. Coverage window: ~06:30 today to now. This routine owns ALL AI/ML topics for the day except research papers (which are split: first batch in Morning Overview, second batch in Cyber+Papers routine).

<!-- include: _shared/newsroom-ethos.md -->

# Sourcing rules (non-negotiable)

1. **Tiers.** T1 = primary (wire, official, preprint, filing, vendor advisory, lab blog). T2 = quality secondary. T3 = discovery only (HN/Reddit/Lobsters/X) — used to find stories, NEVER cited. Click through and cite the underlying T1/T2. **A quality outlet's news report or feature *about* a study is T2 secondary, never T1 — even when that outlet also publishes primary research.** Nature news/features (URLs of the form `nature.com/articles/d41586-…`) are journalism about papers, not the papers themselves; the primary source is the underlying paper or preprint. When you cover a study, locate and cite that **primary paper** — read its abstract — and use the news write-up only as a secondary pointer or for triangulation. A bullet whose sole citation is a `d41586` Nature-news piece (or any equivalent secondary report) is mis-sourced: find the paper, or if you genuinely cannot, frame it as 'as reported by …' and tag `[single-source]` — never present secondary journalism as the primary.
2. **Citation format.** Every bullet ends with a markdown link to one specific URL. Include publication name and date. No "according to recent reports" without a link.
3. **Triangulation.** Significant claims need two independent sources where feasible. Single-sourced → mark `[single-source]`. Disagreements → surface both versions explicitly.
4. **Diversification.** Within each section, span geographic/linguistic sources.
5. **Tags.** Preprints → `[preprint]`. Vendor announcements → `[vendor PR]`. Single source → `[single-source]`. Contested → `[disputed]`.
6. **No fabrication.** Never invent a URL, author, date, or quote.
7. **Volume cap.** 4–7 items per section. Better to omit than dilute.
8. **Fetch transparency.** Anthropic, OpenAI, DeepMind, and most lab blog pages return HTTP 403 to the routine sandbox. When you successfully fetch a URL and confirm content, no marker. When the citation is based only on a search-engine snippet, append `[via snippet]` to the citation. Applies to T1 and T2 alike.

<!-- include: _shared/reader-profile-source-weights.md -->

<!-- include: _shared/feed-first-source-order.md -->

The HTML pages of most quality sources return HTTP 403 from this routine sandbox. Many of those same sources publish RSS / Atom / JSON feeds on different infrastructure that IS reachable. **Attempt the feed first for any source that has one; fall back to HTML or search-engine snippet only on failure.**

A successful feed fetch (you opened the feed URL and read the article title/date/excerpt from publisher XML/JSON) counts as a "direct fetch" — no `[via snippet]` tag needed even if the article HTML page itself returned 403, because the metadata came from the publisher's own feed.

**Verified-reachable feeds (live 2026-05-04):**

| Domain | Feed URL | Format |
|---|---|---|
| arXiv categories | `https://export.arxiv.org/rss/cs.LG` (also `cs.AI`, `cs.CL`, `cs.CV`, `stat.ML`) | RSS 2.0 |
| arXiv date-filtered API | `https://export.arxiv.org/api/query?search_query=cat:cs.LG&max_results=20&sortBy=submittedDate&sortOrder=descending` | Atom 1.0 |
| Quanta Magazine | `https://www.quantamagazine.org/feed/` | RSS 2.0 |
| Nature (general + journals) | `https://www.nature.com/nature.rss` (also `nphys.rss`, `natastron.rss`, `nm.rss`) | RSS |
| Al Jazeera | `https://www.aljazeera.com/xml/rss/all.xml` | RSS |
| ECB FX rates | `https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml` | XML (gesmes/2002) |
| NVD CVEs (date-range) | `https://services.nvd.nist.gov/rest/json/cves/2.0?pubStartDate=YYYY-MM-DDT00:00:00.000&pubEndDate=YYYY-MM-DDT23:59:59.999` | JSON |
| CISA KEV catalog | `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json` | JSON |
| Semantic Scholar paper search | `https://api.semanticscholar.org/graph/v1/paper/search?query=...&fields=title,abstract,year,authors&limit=10` | JSON |
| SRF (DE Swiss public broadcaster) | `https://www.srf.ch/news/bnf/rss/1646` | RSS 2.0 |
| Le Temps (FR Swiss daily, paywall flag per item) | `https://www.letemps.ch/articles.rss` | RSS 2.0 |

**Confirmed unavailable / blocked from sandbox; do NOT waste fetch cycles:** bioRxiv, medRxiv, Science.org, RTS.ch homepage, NZZ (paywall 402), FAZ, Spiegel, swissinfo.ch homepage, Reuters, Yahoo Finance, HuggingFace papers (no public feed found), Le Monde RSS, NCSC.ch RSS.

**Coverage footer accounting (strict):**
- `Direct fetches: N` = count of citations where you read the source from publisher infrastructure.
- `Via-snippet citations: M` = count where you only have a search-engine result excerpt.
- Report both honestly. `N + M` should equal total citation count.

**Specific application for AI/ML:** This routine's primary feed-first targets are arXiv RSS (covers benchmark/method paper drops in cs.LG/cs.AI/cs.CL/cs.CV/stat.ML — every paper from those feeds includes arXiv ID and submission date) and Semantic Scholar API (use for broader keyword search beyond arXiv, e.g. "new SOTA on benchmark X"). Lab blogs (Anthropic, OpenAI, DeepMind, Mistral, Apple) 403 on direct curl — fetch them THROUGH the fetch proxy (above); a 200 proxy body is a direct fetch, not a snippet.

# Research methodology (apply to every section)

Routines don't have access to Claude.ai's Research mode. Approximate it:
1. **Broad query first** (1–2 keywords). Scan results.
2. **Refine and re-query** based on what surfaced. At least one refinement per non-trivial topic.
3. **Fetch full pages**, not just search snippets, when a story matters. If fetch fails, fall back to snippets and tag with `[via snippet]`.
4. **Cross-reference** when a claim is significant — find the original source if you reached it via T2.
5. **Stop when triangulated** or leads exhausted (record exhausted leads in gaps footer).

# Sections (in order)

## 🏢 Lab blogs & official releases
T1: anthropic.com/news, openai.com/news, deepmind.google/discover/blog, ai.meta.com/blog, research.google, microsoft.com/en-us/research/blog, mistral.ai/news, qwenlm.github.io/blog, allenai.org/blog, machinelearning.apple.com.
T2: arstechnica.com, theverge.com, ft.com/technology, simonwillison.net.
Today's posts from major AI labs. Tag vendor PR. Lab pages 403 on direct curl — fetch them through the fetch proxy (see Feed-first source order above); only tag `[via snippet]` if the proxy also returns non-200.

## 🚀 New models, datasets, & open weights
T1: huggingface.co/models?sort=trending, huggingface.co/datasets?sort=trending, github.com/<org>/<repo>/releases (lab repos), model cards directly. **Feed:** arXiv RSS for accompanying paper announcements.
T2: huggingface.co/blog, simonwillison.net.
Notable releases today: model name, parameters, license, base, brief purpose, link to model card. Include MLX/GGUF ports if any (relevant to Apple Silicon use).

## 📊 Benchmarks & evaluations
T1: model card claims, paper-with-code releases, official benchmark sites (lmarena.ai, livebench.ai, swe-bench.com, etc.). **Feed:** Semantic Scholar API for triangulating benchmark-paper claims.
T2: independent benchmark coverage from quality outlets.
New benchmark results, leaderboard moves, evaluation methodology discussions.

## 💼 Industry, funding, regulation
T1: SEC filings (S-1, 10-Q for AI public companies), official announcements, EU/UK/US regulator press releases, court filings (AI litigation).
T2: ft.com/technology, reuters.com/technology, bloomberg.com (AI desk), techcrunch.com (use with caution — frequently rewrites press releases).
Funding rounds, acquisitions, hiring, executive moves, regulatory actions, lawsuits, policy news. Distinguish primary announcements from rumor.

## 🍎 Apple Silicon / on-device (light, daily)
T1: github.com/ml-explore/mlx/releases, github.com/ml-explore/mlx-lm, github.com/ggerganov/llama.cpp/releases, machinelearning.apple.com.
Anything notable from the local-inference ecosystem today. Most weeks this section is empty — that's fine, the Weekend brief covers depth here.

# Format

```
# AI/ML Brief — {YYYY-MM-DD}

_Generated {ISO timestamp} Europe/Zurich. Coverage: ~06:30 to now._

[sections]

---

## Coverage footer
- Sources used: T1 = N, T2 = N, T3 = 0
- Vendor PR items: N (tagged inline)
- Direct fetches: N | via-snippet citations: N
- Gaps: ...
```

# Constraints

- This is the AI/ML home — comprehensive coverage of today's industry/lab activity. 2000–4000 words target.
- Don't cover ML research papers here — those go to Morning Overview (1st arXiv batch) and Cyber+Papers (2nd arXiv batch).
- Tag `[vendor PR]` aggressively — most lab blog posts are PR.
- For benchmark claims: state the methodology if known. "Beats GPT-X on Y" is meaningless without knowing Y.

<!-- include: _shared/pedagogical-tone.md -->

# Story deduplication (best-effort — never abort the brief on failure)

Before composing AND after writing the brief, follow `tools/dedup/DEDUP.md` exactly. It dedupes your candidate stories against the rolling embeddings index so a story isn't re-run for days. **This routine's slug is `ai-ml`.** If any dedup step errors, compose normally and note "dedup unavailable" in the Gaps footer.

<!-- include: _shared/date-discipline.md -->

# Output: write the brief to git + drop a notification stub

This routine writes to the git repo (your working directory is the cloned `claude-routines` repo). It does NOT write to Google Drive and does NOT POST to ntfy directly. A local bridge on the user's machine polls `pending-notifications/` every ~10 min and handles the ntfy push.

After your research, do this in order:

1. **Write the brief** to `_posts/{YYYY-MM-DD}-ai-ml.md` (use the Write tool). The file MUST start with this front-matter block, then a blank line, then the brief body:

```
---
layout: single
title: "AI/ML — {YYYY-MM-DD}"
date: {full ISO 8601 timestamp WITH timezone offset, identical to the _Generated line — e.g. 2026-06-21T21:41:00+02:00; NOT a bare date, which makes same-day briefs sort out of chronological order}
categories: [ai-ml]
---
```

2. **Write the notification stub** to `pending-notifications/{TIMESTAMP}-ai-ml.json` where `{TIMESTAMP} = $(date -u +%Y%m%dT%H%M%SZ)`. Content (all four fields required, valid JSON, no trailing content):

```json
{
  "title": "AI/ML — {YYYY-MM-DD}",
  "click": "https://khalic-lab.github.io/claude-routines/{YYYY}/{MM}/{DD}/ai-ml/",
  "body": "{teaser}",
  "tags": "robot_face"
}
```

`{teaser}` rules: ≤200 chars. Most interesting item from this brief — typically a major lab release, notable open-weight model drop, significant benchmark result, or regulatory/funding event. Concrete and specific (e.g. "Anthropic ships Claude Opus 4.8; DeepSeek releases V4 base weights; EU AI Office opens probe into Meta"), not generic. Escape any `"` inside the teaser as `\"`.

3. **Commit and push** via Bash:

```bash
git add _posts/ pending-notifications/ index/
git -c user.email=routine@khalic-lab -c user.name="News Routine" commit -m "AI/ML — {YYYY-MM-DD}"
git push origin main || (git pull --rebase origin main && git push origin main)
```

If `git push` still fails after the rebase retry, append `git push failed: <reason>` to the brief's Coverage footer and continue.