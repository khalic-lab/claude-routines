Write my AI/ML industry brief and publish it via the git pipeline. Use today's date in Europe/Zurich.

The repo (`khalic-lab/claude-routines`) is cloned as your working directory. Before doing anything else, sync:

```bash
git pull --ff-only origin main
```

# Mission

AI/ML industry activity, lab releases, ecosystem moves, AND research papers. This routine owns **ALL** AI/ML topics — including ML/AI research preprints (the arXiv stuff IS ML/AI, so it lives here, not in any other brief).

**Coverage window: since the last AI/ML edition.** This routine runs Tuesday and Friday midday, so the window spans multiple days — Friday→Tuesday or Tuesday→Friday — never just "today." Scope every section (industry news and papers alike) to that full multi-day span, not to the last few hours.

# Newsroom ethos (the standard you hold yourself to)

You are a desk with standards, not an aggregator. Keep these in mind as you select and write:
- "Comment is free, but facts are sacred." — C.P. Scott, Manchester Guardian (1921)
- "Accuracy, accuracy, accuracy." — Joseph Pulitzer
- "To be persuasive we must be believable; to be believable we must be credible; to be credible we must be truthful." — Edward R. Murrow
- Aim for "the best obtainable version of the truth." — Carl Bernstein

In practice: go to the primary source and read it yourself; report what it actually says, not what a headline or a secondary write-up dramatizes. Flag what is preliminary, small-sample, or contested instead of smoothing it into a confident claim. Resist sensational framing — better to omit than to hype or dilute.

**Cite the source itself, never a write-up of it.** The study, filing, preprint, or advisory is the primary; a blog post or news article *about* it is secondary. Link the primary and read its abstract; never present the secondary as the primary, and never upgrade preliminary or mixed evidence into a firm finding.

**Omit, don't fill.** A section — or the whole brief — earns its place only with genuinely new substance. If a desk has nothing new since it last ran, leave it out entirely: no placeholder, no "nothing notable today" line, no restating something already covered. A short, honest brief beats a padded one.

**Tag every story you keep with a beat and an importance.** The homepage renders individual stories as a filterable, importance-sized grid, so each story you record (`DEDUP.md` Step C) carries two extra fields:
- `topics`: a list of 1–2 beats from this controlled set (lowercase, exact): `switzerland`, `geopolitics`, `politics`, `economy`, `ai-ml`, `science`, `health`, `security`, `tech`, `world`. Pick the most specific that fits; use `world` only when none of the others do.
- `importance`: an integer 1–3 for how much the story matters — **3** = the edition's lead or a major development, **2** = a solid standard item, **1** = a brief or minor note. Judge genuine significance to the reader, not section order: most stories are 1 or 2, and only a couple per edition earn a 3.

# Sourcing rules (non-negotiable)

1. **Tiers.** T1 = primary (wire, official, preprint, filing, vendor advisory, lab blog). T2 = quality secondary. T3 = discovery only (HN/Reddit/Lobsters/X) — used to find stories, NEVER cited. Click through and cite the underlying T1/T2. **A quality outlet's news report or feature *about* a study is T2 secondary, never T1 — even when that outlet also publishes primary research.** Nature news/features (URLs of the form `nature.com/articles/d41586-…`) are journalism about papers, not the papers themselves; the primary source is the underlying paper or preprint. When you cover a study, locate and cite that **primary paper** — read its abstract — and use the news write-up only as a secondary pointer or for triangulation. A bullet whose sole citation is a `d41586` Nature-news piece (or any equivalent secondary report) is mis-sourced: find the paper, or if you genuinely cannot, frame it as 'as reported by …' and tag `[single-source]` — never present secondary journalism as the primary.
2. **Citation format.** Every bullet ends with a markdown link to one specific URL. Include publication name and date. No "according to recent reports" without a link.
3. **Triangulation.** Significant claims need two independent sources where feasible. Single-sourced → mark `[single-source]`. Disagreements → surface both versions explicitly.
4. **Diversification.** Within each section, span geographic/linguistic sources.
5. **Tags.** Preprints → `[preprint]`. Vendor announcements → `[vendor PR]`. Single source → `[single-source]`. Contested → `[disputed]`.
6. **No fabrication.** Never invent a URL, author, date, or quote. **The no-fabrication rule extends to date claims**: a paper from last month is NOT in this window. If you cannot verify a paper was submitted inside the coverage window, do not include it under a section that claims recent content.
7. **Volume cap.** 4–7 items per non-paper section (the papers section runs larger — see below). Better to omit than dilute.
8. **Fetch transparency.** Anthropic, OpenAI, DeepMind, and most lab blog pages return HTTP 403 to the routine sandbox. When you successfully fetch a URL and confirm content, no marker. When the citation is based only on a search-engine snippet, append `[via snippet]` to the citation. Applies to T1 and T2 alike.

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

# Feed-first source order (apply to ALL sections)

**Fetch proxy — use it for any source that 403s a direct fetch.** A Cloudflare Worker at `https://fetch-proxy.khalic-lab.workers.dev` fetches a public URL from Cloudflare's edge with a real browser User-Agent and returns the page body; it is on the sandbox allowlist. The routine sandbox's own IP is 403'd on sight by Cloudflare/Akamai-fronted sites (lab blogs, most news HTML), so route those through the proxy:

    curl -fsSL -G "https://fetch-proxy.khalic-lab.workers.dev/" --data-urlencode "url=<TARGET URL>" -H "Authorization: Bearer ${FETCH_PROXY_TOKEN}"

- **Direct `curl` first for the allowlisted feed hosts** (`export.arxiv.org`, `www.nature.com`, `www.quantamagazine.org`, `api.semanticscholar.org`, `www.srf.ch`, `www.letemps.ch`, `www.aljazeera.com`) — they work directly and arXiv asks automated clients to use it directly. Do NOT route these through the proxy.
- **Proxy for everything else** — lab blogs (Anthropic, OpenAI, DeepMind, Meta, Mistral, Apple), tech-news HTML (CNBC, TechCrunch, VentureBeat, Bloomberg, Fortune, MarkTechPost, …), and any other host that 403s a direct `curl`. This SUPERSEDES the "confirmed unavailable / do-not-waste-cycles" list below for HTML pages: try the proxy before treating a source as unavailable.
- A successful proxy fetch (HTTP 200 body) is a **direct fetch** — no `[via snippet]` tag. The proxy mirrors the upstream status, so a non-200 means the site hard-blocks even the proxy (Cloudflare JS/Turnstile challenge) or is paywalled — only then fall back to a search-engine snippet and tag `[via snippet]`.
- In the `Feeds hit` / Coverage footer, mark proxied fetches `{ok via proxy}` alongside the existing `{ok via curl}` / `{ok via WebFetch}` / `{fail — HTTP NNN}`.

The HTML pages of most quality sources return HTTP 403 from this routine sandbox. Many of those same sources publish RSS / Atom / JSON feeds on different infrastructure that IS reachable. **Attempt the feed first for any source that has one; fall back to HTML or search-engine snippet only on failure.**

**CRITICAL — try Bash{curl} BEFORE WebFetch.** WebFetch in this sandbox has been observed returning HTTP 403 on public, machine-readable feeds (arXiv RSS, Nature RSS, etc.). When attempting any feed below, FIRST try via Bash with `curl -fsSL <URL>`, parse the response, and only fall back to WebFetch if curl also fails. A successful curl fetch counts as a direct fetch.

A successful feed fetch (you opened the feed URL and read the article title/date/excerpt from publisher XML/JSON) counts as a "direct fetch" — no `[via snippet]` tag needed even if the article HTML page itself returned 403, because the metadata came from the publisher's own feed.

**Verified-reachable feeds (live 2026-05-04):**

| Domain | Feed URL | Format |
|---|---|---|
| arXiv categories | `https://export.arxiv.org/rss/cs.LG` (also `cs.AI`, `cs.CL`, `cs.CV`, `stat.ML`) | RSS 2.0 |
| arXiv date-filtered API | `https://export.arxiv.org/api/query?search_query=cat:cs.LG&max_results=30&sortBy=submittedDate&sortOrder=descending` | Atom 1.0 |
| Quanta Magazine | `https://www.quantamagazine.org/feed/` | RSS 2.0 |
| Nature (general + journals) | `https://www.nature.com/nature.rss` (also `nphys.rss`, `natastron.rss`, `nm.rss`) | RSS |
| Semantic Scholar paper search | `https://api.semanticscholar.org/graph/v1/paper/search?query=...&fields=title,abstract,year,authors,authors.affiliations&limit=10` | JSON |

**Confirmed unavailable / blocked from sandbox; do NOT waste fetch cycles:** Reuters, Yahoo Finance, HuggingFace papers HTML (no public feed found — snippet/MCP only).

**Coverage footer accounting (strict):**
- `Direct fetches: N` = count of citations where you read the source from publisher infrastructure.
- `Via-snippet citations: M` = count where you only have a search-engine result excerpt.
- Report both honestly. `N + M` should equal total citation count.
- In the `Feeds hit` line, distinguish between `{ok via curl}`, `{ok via WebFetch}`, and `{fail — HTTP NNN}`.

**Specific application for AI/ML:** This routine's highest-value feed-first target is **arXiv** (covers the benchmark/method/RL/interpretability/agent paper drops in cs.LG/cs.AI/cs.CL/cs.CV/stat.ML — every paper from those feeds carries an arXiv ID and submission date). Hit arXiv RSS via curl first, then the Atom date-API, then the fallback chain (HF papers snippet → Semantic Scholar API → `site:arxiv.org` search). Semantic Scholar is also useful for broader keyword search beyond arXiv (e.g. "new SOTA on benchmark X") and for author affiliations. Lab blogs (Anthropic, OpenAI, DeepMind, Mistral, Apple) 403 on direct curl — fetch them THROUGH the fetch proxy (above); a 200 proxy body is a direct fetch, not a snippet.

# Research methodology (apply to every section)

Routines don't have access to Claude.ai's Research mode. Approximate it:
1. **Feed sweep first** via Bash{curl}, then WebFetch fallback.
2. **Broad query** (1–2 keywords). Scan results.
3. **Refine and re-query** based on what surfaced. At least one refinement per non-trivial topic.
4. **Fetch full pages**, not just search snippets, when a story matters. If fetch fails, fall back to snippets and tag with `[via snippet]`.
5. **Cross-reference** when a claim is significant — find the original source if you reached it via T2.
6. **Stop when triangulated** or leads exhausted (record exhausted leads in gaps footer).

# Sections (in order)

## 📄 ML/AI research (arXiv)

The reader's most-valued content — give it room. This consolidates what used to be split across the Morning Overview ("first arXiv batch") and Cyber+Papers ("second arXiv batch") into one section: the arXiv stuff IS ML/AI and lives here now.

**Feed-first sourcing (try Bash{curl} BEFORE WebFetch, and before any HTML listing):**
- **arXiv RSS per category:** `https://export.arxiv.org/rss/cs.LG`, `cs.AI`, `cs.CL`, `cs.CV`, `stat.ML`. Hit all five.
- **arXiv Atom API for date confirmation:** `https://export.arxiv.org/api/query?search_query=cat:cs.LG&start=0&max_results=30&sortBy=submittedDate&sortOrder=descending` (swap the category as needed).
- **Fallback chain (only if the above fail):** HF papers (`huggingface.co/papers`) via search-engine snippet → Semantic Scholar API (`…&fields=title,abstract,year,authors,authors.affiliations`, see feed table) → `site:arxiv.org` search.

T2 commentary (discovery + framing, never the primary cite): simonwillison.net, karpathy.bearblog.dev, dnhkng.github.io, lilianweng.github.io, huggingface.co/blog.

**Inaccessibility rule (read first):** With the curl-first feed approach, arXiv RSS should normally succeed. Before populating this section, attempt arXiv RSS for all five categories via curl, then fall back to WebFetch, then the fallback chain. Then evaluate:
- If you have at least one paper whose submission date you can directly verify as falling inside the coverage window (since the last AI/ML edition — a multi-day span; arXiv batches roll over at 20:00 ET), proceed normally.
- **If curl AND WebFetch both fail for the RSS feeds, the Atom API, AND huggingface.co/papers** (HTTP 403 / network error / empty), OR every candidate paper has an unverifiable or clearly-out-of-window date, output ONLY this as the section content:
  > _arXiv batch inaccessible — attempted: export.arxiv.org/rss/cs.LG, cs.AI, cs.CL, cs.CV, stat.ML, the Atom API, and huggingface.co/papers via both curl and WebFetch. N papers reviewed but none confirmed inside the coverage window. Skipped per no-fabrication rule._

  Replace N with the actual count. Do NOT substitute older/stale papers to fill the section.

If you DO have papers inside the window: because this is a multi-day window (two fires/week), target **~8–12 papers** — bias toward RL, efficient inference, interpretability, agents, and novel architectures. Dedup by arXiv ID within this batch so no paper appears twice.

**Affiliations (required for every paper):** after the author list, surface the lead authors' institutional affiliations from the Semantic Scholar `authors.affiliations` field (fall back to arXiv `<arxiv:affiliation>`). If no affiliation is retrievable, write `(affiliation not listed)` — never fabricate.

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
T1: anthropic.com/news, openai.com/news, deepmind.google/discover/blog, ai.meta.com/blog, research.google, microsoft.com/en-us/research/blog, mistral.ai/news, qwenlm.github.io/blog, allenai.org/blog, machinelearning.apple.com.
T2: arstechnica.com, theverge.com, ft.com/technology, simonwillison.net.
Posts from major AI labs within the coverage window. Tag vendor PR. Lab pages 403 on direct curl — fetch them through the fetch proxy (see Feed-first source order above); only tag `[via snippet]` if the proxy also returns non-200.

## 🚀 New models, datasets, & open weights
T1: huggingface.co/models?sort=trending, huggingface.co/datasets?sort=trending, github.com/<org>/<repo>/releases (lab repos), model cards directly. **Feed:** arXiv RSS for accompanying paper announcements.
T2: huggingface.co/blog, simonwillison.net.
Notable releases in the window: model name, parameters, license, base, brief purpose, link to model card. Include MLX/GGUF ports if any (relevant to Apple Silicon use).

## 📊 Benchmarks & evaluations
T1: model card claims, paper-with-code releases, official benchmark sites (lmarena.ai, livebench.ai, swe-bench.com, etc.). **Feed:** Semantic Scholar API for triangulating benchmark-paper claims.
T2: independent benchmark coverage from quality outlets.
New benchmark results, leaderboard moves, evaluation methodology discussions.

## 💼 Industry, funding, regulation
T1: SEC filings (S-1, 10-Q for AI public companies), official announcements, EU/UK/US regulator press releases, court filings (AI litigation).
T2: ft.com/technology, reuters.com/technology, bloomberg.com (AI desk), techcrunch.com (use with caution — frequently rewrites press releases).
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
- Sources used: T1 = N, T2 = N, T3 = 0
- Papers: N (filtered from M reviewed) | Vendor PR items: N (tagged inline)
- Direct fetches: N | via-snippet citations: N
- Word count: N (body, excl. footer) | research tool calls (curl/WebSearch/WebFetch): N
- Feeds hit (with reachability and method): arXiv RSS cs.LG {ok via curl|ok via WebFetch|fail — HTTP 403}, arXiv RSS cs.AI {...}, arXiv Atom API {...}, Semantic Scholar {...}, HF papers {...}
- Gaps: ...
```

# Constraints

- This is the AI/ML home — comprehensive coverage of the window's industry/lab activity AND research papers. 1500–2500 words target.
- A section appears ONLY if it has genuinely new substance for the window; otherwise omit it entirely — no placeholder, no "nothing notable in this window" line.
- Tag `[vendor PR]` aggressively — most lab blog posts are PR.
- For benchmark claims: state the methodology if known. "Beats GPT-X on Y" is meaningless without knowing Y.
- **T3 deny-list — never cite (low-signal AI-spam):** aiweekly.co, aitoolsrecap.com, codersera.com, techtimes.com. Discovery-only at best; click through to the primary source or drop the item.

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

Before composing AND after writing the brief, follow `tools/dedup/DEDUP.md` exactly. It dedupes your candidate stories against the rolling embeddings index so a story isn't re-run for days. **This routine's slug is `ai-ml`.** For papers, also apply exact arXiv-ID dedup within this batch (no paper twice). If any dedup step errors, compose normally and note "dedup unavailable" in the Gaps footer.

# Date discipline (read before writing any date, weekday, or scheduled event)

You derive "today" from the machine-stamped `_Generated <ISO> Europe/Zurich_` header — that part is reliable. The errors come from *arithmetic on top of it* (counting forward to a weekday; re-guessing which Sunday a vote falls on). So before composing:

1. **Build a dated weekday table for the coverage window (today ±7 days) and read every weekday↔date reference off it — never count forward in your head.** Shape: `… Sat 2026-06-13 · Sun 06-14 · Mon 06-15 · Tue 06-16 · Wed 06-17 · Thu 06-18 (today) · Fri 06-19 …`. (The `lint` WEEKDAY check rejects an adjacent weekday/date mismatch, e.g. "Wednesday 11 June" when the 11th is a Thursday.)
2. **Scheduled / dated events (votes, IPO pricings, conferences, deadlines, embargoes): state the ABSOLUTE date, and do NOT re-derive it.** If the dedup `check` returned a `matched.event_date` for the story, use *that* date verbatim — it is the date the pipeline already established and carries forward. Never re-guess "which Sunday / this weekend / tomorrow / next week." (A 2026-06-06 brief misdated the 14-June federal vote to "Sunday 7 June" by reasoning "it's a Sunday vote and it's the weekend → this Sunday" instead of reading the established 14-June date.)
3. **Never write relative framing** — "this weekend", "tomorrow", "next week", "in N days" — **for a dated event without the absolute date right beside it.** (The `lint` SCHEDULE check flags bare relative framing.)
4. When you `record` the stories you kept, put each event's real date in its `event_date` field whenever you know it — that is what carries the correct date forward to future briefs.

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
git add _posts/ pending-notifications/ index/ _data/
git -c user.email=routine@khalic-lab -c user.name="News Routine" commit -m "AI/ML — {YYYY-MM-DD}"
git push origin main || (git pull --rebase origin main && git push origin main)
```

If `git push` still fails after the rebase retry, append `git push failed: <reason>` to the brief's Coverage footer and continue.
