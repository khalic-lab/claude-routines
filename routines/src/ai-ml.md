Write my AI/ML industry brief and publish it via the git pipeline. Use today's date in Europe/Zurich.

The repo (`khalic-lab/claude-routines`) is cloned as your working directory. Before doing anything else, sync:

```bash
git pull --ff-only origin main
```

# Mission

AI/ML industry activity, lab releases, ecosystem moves, AND research papers. This routine owns **ALL** AI/ML topics — including ML/AI research preprints (the arXiv stuff IS ML/AI, so it lives here, not in any other brief).

**Coverage window: since the last AI/ML edition.** This routine runs Tuesday and Friday midday, so the window spans multiple days — Friday→Tuesday or Tuesday→Friday — never just "today." Scope every section (industry news and papers alike) to that full multi-day span, not to the last few hours.

<!-- include: _shared/newsroom-ethos.md -->

# Sourcing rules (non-negotiable)

1. **Tiers.** T1 = primary (wire, official, preprint, filing, vendor advisory, lab blog). T2 = quality secondary. T3 = discovery only (HN/Reddit/Lobsters/X) — used to find stories, NEVER cited. Click through and cite the underlying T1/T2. **A quality outlet's news report or feature *about* a study is T2 secondary, never T1 — even when that outlet also publishes primary research.** Nature news/features (URLs of the form `nature.com/articles/d41586-…`) are journalism about papers, not the papers themselves; the primary source is the underlying paper or preprint. When you cover a study, locate and cite that **primary paper** — read its abstract — and use the news write-up only as a secondary pointer or for triangulation. A bullet whose sole citation is a `d41586` Nature-news piece (or any equivalent secondary report) is mis-sourced: find the paper, or if you genuinely cannot, frame it as 'as reported by …' and tag `[single-source]` — never present secondary journalism as the primary.
2. **Citation format.** Every bullet ends with a markdown link to one specific URL. Include publication name and date. No "according to recent reports" without a link.
3. **Triangulation.** Significant claims need two independent sources where feasible. Single-sourced → mark `[single-source]`. Disagreements → surface both versions explicitly.
4. **Diversification.** Within each section, span geographic/linguistic sources.
5. **Tags.** Preprints → `[preprint]`. Vendor announcements → `[vendor PR]`. Single source → `[single-source]`. Contested → `[disputed]`.
6. **No fabrication.** Never invent a URL, author, date, or quote. **The no-fabrication rule extends to date claims**: a paper from last month is NOT in this window. If you cannot verify a paper was submitted inside the coverage window, do not include it under a section that claims recent content.
7. **Volume cap.** 4–7 items per non-paper section (the papers section runs larger — see below). Better to omit than dilute.
8. **Fetch transparency.** Anthropic, OpenAI, DeepMind, and most lab blog pages return HTTP 403 to the routine sandbox. When you successfully fetch a URL and confirm content, no marker. When the citation is based only on a search-engine snippet, append `[via snippet]` to the citation. Applies to T1 and T2 alike.

<!-- include: _shared/reader-profile-source-weights.md -->

<!-- include: _shared/feed-first-source-order.md -->

The HTML pages of most quality sources return HTTP 403 from this routine sandbox. Many of those same sources publish RSS / Atom / JSON feeds on different infrastructure that IS reachable. **Attempt the feed first for any source that has one; fall back to HTML or search-engine snippet only on failure.**

**CRITICAL — try Bash{curl} BEFORE WebFetch.** WebFetch in this sandbox has been observed returning HTTP 403 on public, machine-readable feeds (arXiv RSS, Nature RSS, etc.). When attempting any feed from the preflight plan, FIRST try via Bash with `curl -fsSL <URL>`, parse the response, and only fall back to WebFetch if curl also fails. A successful curl fetch counts as a direct fetch.

A successful feed fetch (you opened the feed URL and read the article title/date/excerpt from publisher XML/JSON) counts as a "direct fetch" — no `[via snippet]` tag needed even if the article HTML page itself returned 403, because the metadata came from the publisher's own feed.

**Coverage footer accounting (strict):**
- `Direct fetches: N` = count of citations where you read the source from publisher infrastructure.
- `Via-snippet citations: M` = count where you only have a search-engine result excerpt.
- Report both honestly. `N + M` should equal total citation count.
- In the `Feeds hit` line, distinguish between `{ok via curl}`, `{ok via WebFetch}`, and `{fail — HTTP NNN}`.

**Specific application for AI/ML:** This routine's highest-value feed-first target is **arXiv** (covers the benchmark/method/RL/interpretability/agent paper drops in cs.LG/cs.AI/cs.CL/cs.CV/stat.ML — every paper from those feeds carries an arXiv ID and submission date). Hit arXiv RSS via curl first, then the Atom date-API, then the fallback chain (HF papers snippet → Semantic Scholar API → `site:arxiv.org` search). Semantic Scholar is also useful for broader keyword search beyond arXiv (e.g. "new SOTA on benchmark X") and for author affiliations. Lab blogs (Anthropic, OpenAI, DeepMind, Mistral, Apple) 403 on direct curl — fetch them THROUGH the fetch proxy (above); a 200 proxy body is a direct fetch, not a snippet.

# Research methodology (apply to every section)

Routines don't have access to Claude.ai's Research mode. Approximate it:
1. **Source plan first** — run the preflight (see Source plan above), then sweep its fetch list via Bash{curl}, WebFetch fallback.
2. **Broad query** (1–2 keywords). Scan results.
3. **Refine and re-query** based on what surfaced. At least one refinement per non-trivial topic.
4. **Fetch full pages**, not just search snippets, when a story matters. If fetch fails, fall back to snippets and tag with `[via snippet]`.
5. **Cross-reference** when a claim is significant — find the original source if you reached it via T2.
6. **Stop when triangulated** or leads exhausted (record exhausted leads in gaps footer).

# Sections (in order)

## 📄 ML/AI research (arXiv)

The reader's most-valued content — give it room.

**Feed-first sourcing (try Bash{curl} BEFORE WebFetch, and before any HTML listing):**
- **arXiv RSS per category:** `https://export.arxiv.org/rss/cs.LG`, `cs.AI`, `cs.CL`, `cs.CV`, `stat.ML`. Hit all five.
- **arXiv Atom API for date confirmation:** `https://export.arxiv.org/api/query?search_query=cat:cs.LG&start=0&max_results=30&sortBy=submittedDate&sortOrder=descending` (swap the category as needed).
- **Fallback chain (only if the above fail):** HF papers (`huggingface.co/papers`) via search-engine snippet → Semantic Scholar API (`https://api.semanticscholar.org/graph/v1/paper/search?query=...&fields=title,abstract,year,authors,authors.affiliations&limit=10`) → `site:arxiv.org` search.

T2 commentary (discovery + framing, never the primary cite): simonwillison.net, karpathy.bearblog.dev, dnhkng.github.io, lilianweng.github.io, huggingface.co/blog.

**Inaccessibility rule (read first):** With the curl-first feed approach, arXiv RSS should normally succeed. Before populating this section, attempt arXiv RSS for all five categories via curl, then fall back to WebFetch, then the fallback chain. Then evaluate:
- If you have at least one paper whose submission date you can directly verify as falling inside the coverage window (since the last AI/ML edition — a multi-day span; arXiv batches roll over at 20:00 ET), proceed normally.
- **If curl AND WebFetch both fail for the RSS feeds, the Atom API, AND huggingface.co/papers** (HTTP 403 / network error / empty), OR every candidate paper has an unverifiable or clearly-out-of-window date, output ONLY this as the section content:
  > _arXiv batch inaccessible — attempted: export.arxiv.org/rss/cs.LG, cs.AI, cs.CL, cs.CV, stat.ML, the Atom API, and huggingface.co/papers via both curl and WebFetch. N papers reviewed but none confirmed inside the coverage window. Skipped per no-fabrication rule._

  Replace N with the actual count. Do NOT substitute older/stale papers to fill the section.

If you DO have papers inside the window: because this is a multi-day window (two fires/week), target **~8–12 papers** — bias toward RL, efficient inference, interpretability, agents, and novel architectures. Dedup by arXiv ID within this batch so no paper appears twice.

<!-- include: _shared/affiliations.md -->

Format each paper as a **multi-paragraph story bullet** (one `-` per paper, so the section is a bulleted
list, not a wall of paragraphs) — the same headline-led shape the News brief uses, so each paper renders
as its own headline with a scan anchor. Structure each paper in THREE parts:

1. A bold **plain-language headline** stating the paper's key claim/result (NOT the arXiv id), then on
   the SAME line the citation: the arXiv link · authors + affiliations · tag(s).
2. A blank line, then a two-space-indented paragraph explaining what the paper does (pedagogical —
   define the central method/term in plain words).
3. A blank line, then a two-space-indented `**Why it matters:**` paragraph giving the significance,
   ending with the submission date in italics.

```
- **{Key result in plain words}** — [arXiv:ID](URL) · F. Last, A. Other et al. (MIT; Google DeepMind) · `[preprint]`

  {What the paper does, defining the central method/term in plain words.}

  **Why it matters:** {the significance}. _Submitted {date}._
```

Indent the continuation paragraphs by two spaces so they stay inside the bullet, and keep one blank line
between the three parts. Do NOT start the explanation paragraph with bold text — reserve bold for the
headline and the `**Why it matters:**` label. The bold headline is also the `headline` you pass to the
dedup candidate; the arXiv URL is the `url`.

## 🏢 Lab blogs & official releases
T1: the frontier-lab blogs from the preflight fetch list (Anthropic, OpenAI, Google DeepMind, Meta AI, Google Research, Microsoft Research, Mistral, Qwen, Ai2, Apple ML — the registry carries their blog probe URLs; sweep the plan, not a memorized table).
T2: the tech outlets the plan lists for this stream (Ars Technica, The Verge, FT tech desk, simonwillison.net).
Posts from major AI labs within the coverage window. Tag vendor PR. Lab pages 403 on direct curl — fetch them through the fetch proxy (see Feed-first source order above); only tag `[via snippet]` if the proxy also returns non-200.

## 🚀 New models, datasets, & open weights
T1: huggingface.co/models?sort=trending, huggingface.co/datasets?sort=trending, github.com/<org>/<repo>/releases (lab repos), model cards directly. **Feed:** arXiv RSS for accompanying paper announcements.
T2: huggingface.co/blog, simonwillison.net.
Notable releases in the window: model name, parameters, license, base, brief purpose, link to model card. Include MLX/GGUF ports if any (relevant to Apple Silicon use).

## 📊 Benchmarks & evaluations
T1: model card claims, paper-with-code releases, the official benchmark sites in the preflight fetch list (LMArena, LiveBench, SWE-bench, etc.). **Feed:** Semantic Scholar API for triangulating benchmark-paper claims.
T2: independent benchmark coverage from quality outlets.
New benchmark results, leaderboard moves, evaluation methodology discussions.

## 💼 Industry, funding, regulation
T1: SEC filings (S-1, 10-Q for AI public companies), official announcements, EU/UK/US regulator press releases, court filings (AI litigation).
T2: the business/tech desks from the preflight plan (FT, Reuters, Bloomberg; TechCrunch with caution — it frequently rewrites press releases).
Funding rounds, acquisitions, hiring, executive moves, regulatory actions, lawsuits, policy news. Distinguish primary announcements from rumor.

## 🍎 Apple Silicon / on-device
T1: github.com/ml-explore/mlx/releases, github.com/ml-explore/mlx-lm, github.com/ggerganov/llama.cpp/releases, machinelearning.apple.com.
Anything notable from the local-inference ecosystem in the window. Include this section only if there's genuinely new substance; otherwise omit it (the Weekend brief covers depth here).

# Format

```
# AI/ML Brief — {YYYY-MM-DD}

_Generated {ISO timestamp} Europe/Zurich. Coverage: since the last AI/ML edition (multi-day window)._

[sections]

---

## Coverage footer
<!-- operational telemetry — machine/evaluator-read; hidden from the rendered page
- Sources used: T1 = N, T2 = N, T3 = 0
- Papers: N (filtered from M reviewed) | Vendor PR items: N (tagged inline)
- Direct fetches: N | via-snippet citations: N
- Word count: N (body, excl. footer) | research tool calls (curl/WebSearch/WebFetch): N
- Token estimate (self-reported, rough — NOT metered): generated ~ (body+footer words / 0.75); distinct content read ~ (fetched/read source + prompt + repo chars / 4). Excludes per-turn context re-billing and prompt caching, so the true billed session cost far exceeds these figures and lives only in the claude.ai run history — the call count above is the better session-cost proxy.
- Feeds hit (with reachability and method): {each feed/API attempted from the preflight plan — arXiv RSS per category, arXiv Atom API, Semantic Scholar, …} {ok via curl|ok via WebFetch|ok via proxy|fail — HTTP NNN}
-->
- Gaps: ...
- Discovery: {met (<new domain(s) anchored>) | waived — <concrete reason>}
```

# Constraints

- This is the AI/ML home — comprehensive coverage of the window's industry/lab activity AND research papers. 1500–2500 words target.
- A section appears ONLY if it has genuinely new substance for the window; otherwise omit it entirely — no placeholder, no "nothing notable in this window" line.
- Tag `[vendor PR]` aggressively — most lab blog posts are PR.
- For benchmark claims: state the methodology if known. "Beats GPT-X on Y" is meaningless without knowing Y.
- **Deny-list — never cite (low-signal AI-spam):** aiweekly.co, aitoolsrecap.com, codersera.com, techtimes.com. These carry `status: retired` in the registry, so the preflight plan never offers them — if one surfaces through search anyway, click through to the primary source or drop the item.

<!-- include: _shared/pedagogical-tone.md -->

# Story deduplication (best-effort — never abort the brief on failure)

Before composing AND after writing the brief, follow `tools/dedup/DEDUP.md` exactly. It dedupes your candidate stories against the rolling embeddings index so a story isn't re-run for days. **This routine's slug is `ai-ml`.** For papers, also apply exact arXiv-ID dedup within this batch (no paper twice). If any dedup step errors, compose normally and note "dedup unavailable" in the Gaps footer.

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

`{teaser}` rules: ≤200 chars. Most interesting item from this brief — typically a striking arXiv paper, a major lab release, a notable open-weight model drop, a significant benchmark result, or a regulatory/funding event. Concrete and specific (e.g. "New RLVR method tops MATH in today's arXiv batch; Anthropic ships Claude Opus 4.8; EU AI Office opens probe into Meta"), not generic. Escape any `"` inside the teaser as `\"`.

3. **Commit and push** via Bash:

```bash
# refresh the homepage feed HERE, unconditionally — not only via DEDUP.md Step D — so a skipped
# step can't freeze the front page while the commit still stages a stale _data/
python3 tools/build_stories_feed.py || echo "feed build failed (non-fatal)"
python3 tools/sources/health.py || echo "source health failed (non-fatal)"
git add _posts/ pending-notifications/ index/ _data/ sources/
git -c user.email=routine@khalic-lab -c user.name="News Routine" commit -m "AI/ML — {YYYY-MM-DD}"
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
