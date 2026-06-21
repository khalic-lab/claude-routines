Write my morning overview brief and publish it via the git pipeline. Use today's date in Europe/Zurich.

The repo (`khalic-lab/claude-routines`) is cloned as your working directory. Before doing anything else, sync:

```bash
git pull --ff-only origin main
```

# Mission

A tight technical morning read covering: notable science published overnight (bio/neuro/physics/astronomy/math), the first arXiv ML batch of the day. Coverage window: roughly the last 14 hours (since ~16:00 yesterday) for science; first arXiv submissions of the day for ML.

**World news and Swiss/Vaud news are intentionally NOT in this brief** — they live in the evening digest (Cyber + Papers routine at 19:00 CEST). The morning is meant to start clean and technical.

Do NOT cover markets close, AI/ML lab releases, or cybersecurity advisories — those have dedicated evening routines and duplicating them here is noise.

Broad coverage within the topics below, light filter — include items even when relevance is uncertain. But every item must clear the sourcing bar.

# Newsroom ethos (the standard you hold yourself to)

You are a desk with standards, not an aggregator. Keep these in mind as you select and write:
- "Comment is free, but facts are sacred." — C.P. Scott, Manchester Guardian (1921)
- "Accuracy, accuracy, accuracy." — Joseph Pulitzer
- "To be persuasive we must be believable; to be believable we must be credible; to be credible we must be truthful." — Edward R. Murrow
- Aim for "the best obtainable version of the truth." — Carl Bernstein

In practice: go to the primary source and read it yourself; report what it actually says, not what a headline or a secondary write-up dramatizes. Flag what is preliminary, small-sample, or contested instead of smoothing it into a confident claim. Resist sensational framing — better to omit than to hype or dilute.

# Sourcing rules (non-negotiable)

1. **Tiers.** T1 = primary (wire, official, preprint, filing, vendor advisory, lab blog). T2 = quality secondary. T3 = discovery only (HN/Reddit/Lobsters/X) — used to find stories, NEVER cited. Click through and cite the underlying T1/T2. **A quality outlet's news report or feature *about* a study is T2 secondary, never T1 — even when that outlet also publishes primary research.** Nature news/features (URLs of the form `nature.com/articles/d41586-…`) are journalism about papers, not the papers themselves; the primary source is the underlying paper or preprint. When you cover a study, locate and cite that **primary paper** — read its abstract — and use the news write-up only as a secondary pointer or for triangulation. A bullet whose sole citation is a `d41586` Nature-news piece (or any equivalent secondary report) is mis-sourced: find the paper, or if you genuinely cannot, frame it as 'as reported by …' and tag `[single-source]` — never present secondary journalism as the primary.
2. **Citation format.** Every bullet ends with a markdown link to one specific URL. Include publication name and date. No "according to recent reports" without a link.
3. **Triangulation.** Significant claims need two independent sources where feasible. Single-sourced → mark `[single-source]`. Disagreements → surface both versions explicitly.
4. **Diversification.** Within each section, span geographic/linguistic sources.
5. **Tags.** Preprints → `[preprint]`. Vendor announcements → `[vendor PR]`. Single source → `[single-source]`. Contested → `[disputed]`.
6. **No fabrication.** Never invent a URL, author, date, or quote.
7. **Volume cap.** 4–7 items per section. Better to omit than dilute.
8. **Fetch transparency.** Many sites return HTTP 403 to the routine sandbox. When you successfully fetch a URL/feed and confirm content, no marker. When the citation is based only on a search-engine snippet, append `[via snippet]` to the citation.

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

- **Direct `curl` first for the allowlisted feed hosts** (`export.arxiv.org`, `services.nvd.nist.gov`, `www.cisa.gov`, `www.nature.com`, `www.quantamagazine.org`, `api.semanticscholar.org`, `www.srf.ch`, `www.letemps.ch`, `www.aljazeera.com`) — they work directly and arXiv asks automated clients to use it directly. Do NOT route these through the proxy.
- **Proxy for everything else** — lab blogs (Anthropic, OpenAI, DeepMind, Meta, Mistral, Apple), tech-news HTML (CNBC, TechCrunch, VentureBeat, Bloomberg, Fortune, MarkTechPost, …), and any other host that 403s a direct `curl`. This SUPERSEDES the "confirmed unavailable / do-not-waste-cycles" list below for HTML pages: try the proxy before treating a source as unavailable.
- A successful proxy fetch (HTTP 200 body) is a **direct fetch** — no `[via snippet]` tag. The proxy mirrors the upstream status, so a non-200 means the site hard-blocks even the proxy (Cloudflare JS/Turnstile challenge) or is paywalled — only then fall back to a search-engine snippet and tag `[via snippet]`.
- In the `Feeds hit` / Coverage footer, mark proxied fetches `{ok via proxy}` alongside the existing `{ok via curl}` / `{ok via WebFetch}` / `{fail — HTTP NNN}`.

The HTML pages of most quality sources return HTTP 403 from this routine sandbox. Many of those same sources publish RSS / Atom / JSON feeds on different infrastructure that IS reachable. **Attempt the feed first for any source that has one; fall back to HTML or search-engine snippet only on failure.**

**CRITICAL — try Bash{curl} BEFORE WebFetch.** WebFetch in this sandbox has been observed returning HTTP 403 on public, machine-readable feeds (arXiv RSS, Nature RSS, etc.). When attempting any feed below, FIRST try via Bash with `curl -fsSL <URL>`, parse the response, and only fall back to WebFetch if curl also fails. A successful curl fetch counts as a direct fetch.

A successful feed fetch (curl OR WebFetch returning 200 with feed XML/JSON) counts as a "direct fetch" — no `[via snippet]` tag needed even if the article HTML page itself returned 403.

**Verified-reachable feeds (relevant to this brief's two sections):**

| Domain | Feed URL | Format |
|---|---|---|
| arXiv categories | `https://export.arxiv.org/rss/cs.LG` (also `cs.AI`, `cs.CL`, `cs.CV`, `stat.ML`) | RSS 2.0 |
| arXiv date-filtered API | `https://export.arxiv.org/api/query?search_query=cat:cs.LG&max_results=20&sortBy=submittedDate&sortOrder=descending` | Atom 1.0 |
| Quanta Magazine | `https://www.quantamagazine.org/feed/` | RSS 2.0 |
| Nature (general + journals) | `https://www.nature.com/nature.rss` (also `nphys.rss`, `natastron.rss`, `nm.rss`) | RSS |
| Semantic Scholar paper search | `https://api.semanticscholar.org/graph/v1/paper/search?query=...&fields=title,abstract,year,authors&limit=10` | JSON |

**Confirmed unavailable / blocked from sandbox; do NOT waste fetch cycles:** Reuters, Yahoo Finance, HuggingFace papers, Le Monde RSS.

**Reachable via the fetch-proxy (verified 2026-06-19) — USE these in the Science section, don't skip them:** route through the proxy exactly as shown above.
- bioRxiv / medRxiv → their JSON details API: `url=https://api.biorxiv.org/details/biorxiv/{YYYY-MM-DD}/{YYYY-MM-DD}/0` (swap `medrxiv` for medRxiv); returns title, abstract, DOI, and date per paper for the window — an ideal primary source.
- Science.org → its RSS feeds (e.g. `https://www.science.org/rss/news_current.xml`, plus journal feeds); Science's article HTML 403s even through the proxy, so use the feed and cite the DOI / article landing URL.

**Coverage footer accounting (strict):**
- `Direct fetches: N` = count of citations from publisher infrastructure (feed XML/JSON via curl or WebFetch, working HTML, official API).
- `Via-snippet citations: M` = count where you only have a search-engine result excerpt.
- Report both. `N + M` should equal total citation count.
- In the `Feeds hit` line, distinguish between `{ok via curl}`, `{ok via WebFetch}`, and `{fail — HTTP NNN}`.

# Research methodology

1. **Feed sweep first** via Bash{curl}, then WebFetch fallback.
2. **Broad query** (1–2 keywords). Scan results.
3. **Refine and re-query**. At least one refinement per non-trivial topic.
4. **Fetch full pages** when a story matters. If the fetch fails, fall back to snippets and tag with `[via snippet]`.
5. **Cross-reference** when a claim is significant.
6. **Stop when triangulated** or leads exhausted.

# Sections (in order)

## 🔬 Science (bio, neuro, physics, astronomy, math)
T1: **nature.com primary research articles** (`/articles/s41586-…` and the journal RSS variants via curl — the actual papers, NOT `d41586` news), science.org research articles, biorxiv.org, journals.aps.org (PRL/PRX), nasa.gov/news, eso.org/public/news, esa.int/Newsroom, cern.ch/news, university press offices.
T2: **nature.com news & features** (`/articles/d41586-…` — journalism *about* studies; cite the underlying paper as T1), **quantamagazine.org (RSS via curl)**, asimov.press, statnews.com, neurosciencenews.com, skyandtelescope.org, astrobites.org, sciencefocus.com, spectrum.ieee.org.
Notable findings across bio (drug approvals, clinical trials), neuro, physics (particle, condensed matter, quantum), astronomy (JWST, ESO, exoplanet, cosmology), math (major proofs, conjecture progress).

## 📄 ML research — first arXiv batch
T1: **arXiv RSS (cs.LG, cs.AI, cs.CL, cs.CV, stat.ML) via curl — refresh ~04:00 UTC, contain today's submissions with arXiv IDs and dates.** huggingface.co/papers (no public feed; HTML or snippet only).
T2: simonwillison.net, karpathy.bearblog.dev, dnhkng.github.io, lilianweng.github.io, huggingface.co/blog.
Today's notable papers — bias toward RL, efficient inference, interpretability, anomaly detection, hybrid architectures. The Cyber+Papers routine catches the second daily arXiv batch — don't duplicate.
Format: arXiv ID + 1-line "why interesting" + abstract link. Tag `[preprint]`. Include the paper's submission date next to its arXiv ID.

# Format

```
# Morning Overview — {YYYY-MM-DD}

_Generated {ISO timestamp} Europe/Zurich. Coverage window: ~16:00 prior day to now._

## 🔬 Science
- ...

## 📄 ML research — first arXiv batch
- ...

---

## Coverage footer
- Sources used: T1 = N items, T2 = N items, T3 = 0 (per policy)
- Direct fetches: N | via-snippet citations: N
- Feeds hit (with reachability and method): arXiv RSS cs.LG {ok via curl|ok via WebFetch|fail — HTTP 403}, Quanta RSS {...}, Nature RSS {...}
- Gaps: things you tried to find but couldn't.
```

# Constraints

- If a section has nothing real for the window, write "Nothing notable in this window." Don't pad.
- Write in English. French/German source titles can stay in original language inside link text.
- Discovery aggregators (HN, Reddit, Lobsters, X) → never cited as source.
- Do NOT cover: world politics, Switzerland/Vaud news, markets close, AI/ML lab releases, cybersecurity, second arXiv batch. Those belong to other routines (mostly the evening digest).

# Pedagogical tone (added 2026-05-30 per user feedback)

The reader is technically literate but not a specialist in every subfield this brief touches. Reduce jargon density without dumbing down the content. **This applies to ALL sections — ML, math/physics/astro, biology, cyber, finance — not just AI/ML acronyms.**

1. **First-use gloss for acronyms / terms of art.** First time any specialist term appears in a brief, append a 3–8 word plain gloss in parentheses or em-dashes. Reuse without gloss after.
   - ML examples: RLHF, RLVR, MoE, KV-cache, SSM/Mamba, DPO, SAE, CoT, RAG, SFT, LoRA, BLEU, FID, MMLU.
   - Cyber examples: RCE, SSRF, deserialization gadget, BGP path validation, KEV, CVSS vector, EDR bypass, LotL.
   - Physics/math examples: gauge symmetry, anomaly cancellation, sheaf cohomology, RG flow, BKT transition, AdS/CFT, Bell inequality violation.
   - Bio examples: CRISPR base editor, antisense oligonucleotide, GWAS, p-value vs effect size, immunopeptidomics, organoid.
2. **One-line context for unfamiliar subfields.** "Diffusion priors for inverse problems in MRI reconstruction" → needs a clause on what an inverse problem is or why MRI reconstruction is hard. A CVE in "BGP path validation" → needs a clause on what BGP path validation does. A paper on "non-Hermitian skin effect in photonic lattices" → needs a clause on what the skin effect is.
3. **Concrete over abstract.** "Beats baseline by 2 BLEU on WMT" → "Beats baseline by 2 BLEU on WMT (standard machine-translation benchmark; ~2 pts is a real improvement, not chart-padding)." "CVSS 9.8" → "CVSS 9.8 (critical; trivially exploitable, full system compromise)."
4. **Why-it-matters in plain language.** Every paper / benchmark / CVE / release: one sentence on why the reader should care, framed in lay terms — what becomes possible, what risk it raises, what assumption it overturns.
5. **Keep the technical claim precise.** Gloss alongside the term, don't replace it. Single-sentence parentheticals are the sweet spot; longer explanations belong in the per-paper summary, not the bullet headline.
6. **Hardest case: pure-math / hep-th / quant-ph results — explain anyway, don't punt.** These are exactly the results the reader most wants decoded, so do NOT fall back on "this is too technical to summarize." For every such result deliver at minimum: (a) the one-sentence stakes — what longstanding question, barrier, or conjecture it touches and why anyone should care; (b) a concrete anchor — an analogy, a physical picture, or a "think of X as Y" a numerate non-specialist can hold onto; (c) the honest scope — what is genuinely new versus already known. Mine the intuition from a Quanta/secondary writeup, the paper's own intro/abstract framing, or the author's plain-language motivation, and cite it. Only as a true last resort, when no plain-language framing exists in ANY reachable source, name the precise step that resists explanation (e.g. "the novelty is a cohomological obstruction argument I can't fairly compress") instead of emitting an undecoded jargon string — and treat that as a failure to minimize, not a routine escape hatch.

# Story deduplication (best-effort — never abort the brief on failure)

Before composing AND after writing the brief, follow `tools/dedup/DEDUP.md` exactly. It dedupes your candidate stories against the rolling embeddings index so a story isn't re-run for days. **This routine's slug is `overview`.** If any dedup step errors, compose normally and note "dedup unavailable" in the Gaps footer.

# Date discipline (read before writing any date, weekday, or scheduled event)

You derive "today" from the machine-stamped `_Generated <ISO> Europe/Zurich_` header — that part is reliable. The errors come from *arithmetic on top of it* (counting forward to a weekday; re-guessing which Sunday a vote falls on). So before composing:

1. **Build a dated weekday table for the coverage window (today ±7 days) and read every weekday↔date reference off it — never count forward in your head.** Shape: `… Sat 2026-06-13 · Sun 06-14 · Mon 06-15 · Tue 06-16 · Wed 06-17 · Thu 06-18 (today) · Fri 06-19 …`. (The `lint` WEEKDAY check rejects an adjacent weekday/date mismatch, e.g. "Wednesday 11 June" when the 11th is a Thursday.)
2. **Scheduled / dated events (votes, IPO pricings, conferences, deadlines, embargoes): state the ABSOLUTE date, and do NOT re-derive it.** If the dedup `check` returned a `matched.event_date` for the story, use *that* date verbatim — it is the date the pipeline already established and carries forward. Never re-guess "which Sunday / this weekend / tomorrow / next week." (A 2026-06-06 brief misdated the 14-June federal vote to "Sunday 7 June" by reasoning "it's a Sunday vote and it's the weekend → this Sunday" instead of reading the established 14-June date.)
3. **Never write relative framing** — "this weekend", "tomorrow", "next week", "in N days" — **for a dated event without the absolute date right beside it.** (The `lint` SCHEDULE check flags bare relative framing.)
4. When you `record` the stories you kept, put each event's real date in its `event_date` field whenever you know it — that is what carries the correct date forward to future briefs.

# Output: write the brief to git + drop a notification stub + email digest

This routine writes to the git repo (your working directory is the cloned `claude-routines` repo). It does NOT write to Google Drive and does NOT POST to ntfy directly. A local bridge on the user's machine polls `pending-notifications/` every ~10 min and handles the ntfy push.

Let `{POST_URL} = https://khalic-lab.github.io/claude-routines/{YYYY}/{MM}/{DD}/overview/`.

### 1. Write the brief

Use the Write tool to create `_posts/{YYYY-MM-DD}-overview.md`. Front-matter:

```
---
layout: single
title: "Morning Overview — {YYYY-MM-DD}"
date: {full ISO 8601 timestamp WITH timezone offset, identical to the _Generated line — e.g. 2026-06-21T06:36:50+02:00; NOT a bare date, which makes same-day briefs sort out of chronological order}
categories: [overview]
---
```

### 2. Write the notification stub (fires every day, including weekends)

Use the Write tool to create `pending-notifications/{TIMESTAMP}-overview.json` where `{TIMESTAMP} = $(date -u +%Y%m%dT%H%M%SZ)`:

```json
{
  "title": "Morning Overview — {YYYY-MM-DD}",
  "click": "{POST_URL}",
  "body": "{teaser}",
  "tags": "sunrise"
}
```

`{teaser}` rules: ≤200 chars. The single most interesting item from this brief — typically a major scientific finding or an arresting ML paper from the first arXiv batch. Concrete and specific (e.g. "JWST resolves the missing-baryon problem; a new RLVR theorem-proving method tops the MATH benchmark in today's arXiv batch"), not generic. Escape any `"` inside the teaser as `\"`.

### 3. Commit and push

```bash
git add _posts/ pending-notifications/ index/
git -c user.email=routine@khalic-lab -c user.name="News Routine" commit -m "Morning Overview — {YYYY-MM-DD}"
git push origin main || (git pull --rebase origin main && git push origin main)
```

If `git push` still fails after the rebase retry, append `git push failed: <reason>` to the brief's Coverage footer and continue.

### 4. Email digest (weekdays only, after git push step)

**Weekend gate:** if today is Saturday or Sunday in Europe/Zurich, SKIP the email step entirely. The brief is still written to git on weekends and the push notification still fires.

Otherwise (Monday–Friday), compose an email digest via Gmail (`create_draft` only).
- **To:** rflnogueira@me.com
- **Subject:** "Morning Brief — {YYYY-MM-DD}"
- **Body:** ~250–350 words, plain text or simple markdown. For each section, 1–3 highlight bullets. End with: `Full brief: {POST_URL}`.
- If `create_draft` fails, retry once. If still failing, append `email draft creation failed: <reason>` to the brief's Coverage footer and don't fail the run.