Write my evening news brief and publish it via the git pipeline. Use today's date in Europe/Zurich.

The repo (`khalic-lab/claude-routines`) is cloned as your working directory. Before doing anything else, sync:

```bash
git pull --ff-only origin main
```

# Mission

A tight evening read of the day's major **local (Switzerland & Vaud)** and **world** news. Coverage window: the full day (overnight through evening) — federal/cantonal developments, Swiss-relevant EU moves, and the day's notable geopolitics, conflicts, elections, and diplomacy across all time zones.

This is the daily news edition. **AI/ML, science, and the weekend deep-read are SEPARATE editions** (AI/ML Tue+Fri midday, Science Wed, Weekend Sat) — do NOT cover ML/AI, research papers, science, or cybersecurity here. Duplicating them is noise.

Broad coverage of major local + world news, light filter — include items even when relevance is uncertain. But every item must clear the sourcing bar.

# Newsroom ethos (the standard you hold yourself to)

You are a desk with standards, not an aggregator. Keep these in mind as you select and write:
- "Comment is free, but facts are sacred." — C.P. Scott, Manchester Guardian (1921)
- "Accuracy, accuracy, accuracy." — Joseph Pulitzer
- "To be persuasive we must be believable; to be believable we must be credible; to be credible we must be truthful." — Edward R. Murrow
- Aim for "the best obtainable version of the truth." — Carl Bernstein

In practice: go to the primary source and read it yourself; report what it actually says, not what a headline or a secondary write-up dramatizes. Flag what is preliminary, small-sample, or contested instead of smoothing it into a confident claim. Resist sensational framing — better to omit than to hype or dilute.

**Cite the source itself, never a write-up of it.** The study, filing, preprint, or advisory is the primary; a blog post or news article *about* it is secondary. Link the primary and read its abstract; never present the secondary as the primary, and never upgrade preliminary or mixed evidence into a firm finding.

**Omit, don't fill.** A section — or the whole brief — earns its place only with genuinely new substance. If a desk has nothing new since it last ran, leave it out entirely: no placeholder, no "nothing notable today" line, no restating something already covered. A short, honest brief beats a padded one.

# Sourcing rules (non-negotiable)

1. **Tiers.** T1 = primary (wire service, official statement, government/court filing, press release). T2 = quality secondary reporting. T3 = discovery only (HN/Reddit/Lobsters/X) — used to find stories, NEVER cited. Click through and cite the underlying T1/T2. A quality outlet's report *about* an event is fine as T2, but when a primary source exists (the official statement, the filing, the wire dispatch), cite that — not a downstream recap of it.
2. **Citation format.** Every bullet ends with a markdown link to one specific URL. Include publication name and date. No "according to recent reports" without a link.
3. **Triangulation.** Significant claims need two independent sources where feasible. Single-sourced → mark `[single-source]`. Disagreements → surface both versions explicitly.
4. **Diversification.** Within each section, span geographic/linguistic sources.
5. **Tags.** Vendor/official announcements → `[official PR]`. Single source → `[single-source]`. Contested → `[disputed]`.
6. **No fabrication.** Never invent a URL, author, date, or quote. **The no-fabrication rule extends to date claims** — date accuracy matters most in this edition (elections, Swiss federal/cantonal votes, scheduled diplomatic events): never report a scheduled or future event as a result, and carry each event's real date forward rather than re-deriving it (see Date discipline below).
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

- **Direct `curl` first for the allowlisted feed hosts** (`export.arxiv.org`, `www.nature.com`, `www.quantamagazine.org`, `api.semanticscholar.org`, `www.srf.ch`, `www.letemps.ch`, `www.aljazeera.com`) — they work directly and arXiv asks automated clients to use it directly. Do NOT route these through the proxy.
- **Proxy for everything else** — lab blogs (Anthropic, OpenAI, DeepMind, Meta, Mistral, Apple), tech-news HTML (CNBC, TechCrunch, VentureBeat, Bloomberg, Fortune, MarkTechPost, …), and any other host that 403s a direct `curl`. This SUPERSEDES the "confirmed unavailable / do-not-waste-cycles" list below for HTML pages: try the proxy before treating a source as unavailable.
- A successful proxy fetch (HTTP 200 body) is a **direct fetch** — no `[via snippet]` tag. The proxy mirrors the upstream status, so a non-200 means the site hard-blocks even the proxy (Cloudflare JS/Turnstile challenge) or is paywalled — only then fall back to a search-engine snippet and tag `[via snippet]`.
- In the `Feeds hit` / Coverage footer, mark proxied fetches `{ok via proxy}` alongside the existing `{ok via curl}` / `{ok via WebFetch}` / `{fail — HTTP NNN}`.

The HTML pages of most quality sources return HTTP 403 from this routine sandbox. Many of those same sources publish RSS / Atom / JSON feeds on different infrastructure that IS reachable. **Attempt the feed first for any source that has one; fall back to HTML or search-engine snippet only on failure.**

**CRITICAL — try Bash{curl} BEFORE WebFetch.** WebFetch in this sandbox has been observed returning HTTP 403 on public, machine-readable feeds. When attempting any feed below (SRF RSS, Le Temps RSS, Al Jazeera RSS, etc.), FIRST try via Bash with `curl -fsSL <URL>`, parse the response, and only fall back to WebFetch if curl also fails. A successful curl fetch counts as a direct fetch.

A successful feed fetch (curl OR WebFetch returning 200 with feed XML/JSON) counts as a "direct fetch" — no `[via snippet]` tag needed even if the article HTML page itself returned 403.

**Verified-reachable feeds (relevant to this brief's two sections):**

| Domain | Feed URL | Format | Use case |
|---|---|---|---|
| SRF (DE Swiss public broadcaster) | `https://www.srf.ch/news/bnf/rss/1646` | RSS 2.0 | DE-language Swiss news |
| Le Temps (FR Swiss daily) | `https://www.letemps.ch/articles.rss` | RSS 2.0 | FR-language Swiss news |
| Al Jazeera | `https://www.aljazeera.com/xml/rss/all.xml` | RSS | World politics (MENA-strong) |

**Confirmed unavailable from this sandbox (do not waste cycles on the HTML; try the fetch proxy per the source-order note before giving up):** RTS.ch, NZZ (paywall 402), FAZ, Spiegel, swissinfo.ch, Reuters, Le Monde.

**Coverage footer accounting (strict):**
- `Direct fetches: N` = count of citations from publisher infrastructure (feed XML/JSON via curl or WebFetch, working HTML, official API, fetch proxy).
- `Via-snippet citations: M` = count where you only have a search-engine result excerpt.
- Report both. `N + M` should equal total citation count.
- In the `Feeds hit` line, distinguish `{ok via curl}` / `{ok via WebFetch}` / `{ok via proxy}` / `{fail — HTTP NNN}`.

# Research methodology

1. **Feed sweep first** via Bash{curl}, then WebFetch fallback.
2. **Broad query** (1–2 keywords). Scan results.
3. **Refine and re-query**. At least one refinement per non-trivial topic.
4. **Fetch full pages** when a story matters. If the fetch fails, fall back to snippets and tag with `[via snippet]`.
5. **Cross-reference** when a claim is significant.
6. **Stop when triangulated** or leads exhausted.

# Sections (in order)

## 🇨🇭 Switzerland & Vaud

Federal politics, cantonal Vaud, Swiss-relevant EU moves, and notable economy/society stories. Coverage window: full day (overnight through evening).

T1: admin.ch, parlament.ch, vd.ch, Keystone-SDA via rts.ch. **Feed (try via curl first):** SRF.ch RSS (DE-language).
T2: rts.ch, **letemps.ch (RSS via curl — paywalled items still cite-able by URL)**, nzz.ch, tagesanzeiger.ch, 24heures.ch, tdg.ch, swissinfo.ch, heidi.news.

Avoid 20min/Blick as primary. **Non-English-source quota:** at least one DE or FR citation should come from SRF or Le Temps feeds when relevant.

## 🌍 World politics & geopolitics

The day's notable developments, full window (overnight through this evening, all time zones — not just US/Europe).

T1: reuters.com, apnews.com, afp.com, gov/court filings, White House press releases.
T2: bbc.com, ft.com, nytimes.com, lemonde.fr, spiegel.de/international, politico.eu, **aljazeera.com (RSS via curl)** (MENA), scmp.com / caixinglobal.com (China), thehindu.com (India).

Span at least 3 different countries' coverage. Focus on geopolitics, conflicts, elections, and diplomacy. Markets-specific political stories (legislation, central-bank politics) can be folded in here when they're significant — there is no longer a dedicated Markets routine.

# Format

```
# News — {YYYY-MM-DD}

_Generated {ISO timestamp} Europe/Zurich. Coverage: full day._

## 🇨🇭 Switzerland & Vaud
- ...

## 🌍 World politics & geopolitics
- ...

---

## Coverage footer
- Sources used: T1 = N items, T2 = N items, T3 = 0 (per policy)
- Direct fetches: N | via-snippet citations: N
- Word count: N (body, excl. footer) | research tool calls (curl/WebSearch/WebFetch): N
- Feeds hit (with reachability and method): SRF RSS {ok via curl|ok via WebFetch|fail — HTTP 403}, Le Temps RSS {...}, Al Jazeera RSS {...}
- Gaps: things you tried to find but couldn't.
```

# Constraints

- **Omit, don't fill.** A section appears ONLY if it has genuinely new substance. If Switzerland or World has nothing new for the window, omit that section entirely — no placeholder, no "nothing notable" line.
- Write in English. French/German source titles can stay in original language inside link text.
- Discovery aggregators (HN, Reddit, Lobsters, X) → never cited as source.
- Do NOT cover: AI/ML news or lab releases, ML/arXiv papers, science research, cybersecurity/CVEs, or markets close. Those belong to other editions (AI/ML Tue+Fri, Science Wed, Weekend Sat).

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

Before composing AND after writing the brief, follow `tools/dedup/DEDUP.md` exactly. It dedupes your candidate stories against the rolling embeddings index so a story isn't re-run for days. **This routine's slug is `news`.** If any dedup step errors, compose normally and note "dedup unavailable" in the Gaps footer.

# Date discipline (read before writing any date, weekday, or scheduled event)

You derive "today" from the machine-stamped `_Generated <ISO> Europe/Zurich_` header — that part is reliable. The errors come from *arithmetic on top of it* (counting forward to a weekday; re-guessing which Sunday a vote falls on). So before composing:

1. **Build a dated weekday table for the coverage window (today ±7 days) and read every weekday↔date reference off it — never count forward in your head.** Shape: `… Sat 2026-06-13 · Sun 06-14 · Mon 06-15 · Tue 06-16 · Wed 06-17 · Thu 06-18 (today) · Fri 06-19 …`. (The `lint` WEEKDAY check rejects an adjacent weekday/date mismatch, e.g. "Wednesday 11 June" when the 11th is a Thursday.)
2. **Scheduled / dated events (votes, IPO pricings, conferences, deadlines, embargoes): state the ABSOLUTE date, and do NOT re-derive it.** If the dedup `check` returned a `matched.event_date` for the story, use *that* date verbatim — it is the date the pipeline already established and carries forward. Never re-guess "which Sunday / this weekend / tomorrow / next week." (A 2026-06-06 brief misdated the 14-June federal vote to "Sunday 7 June" by reasoning "it's a Sunday vote and it's the weekend → this Sunday" instead of reading the established 14-June date.)
3. **Never write relative framing** — "this weekend", "tomorrow", "next week", "in N days" — **for a dated event without the absolute date right beside it.** (The `lint` SCHEDULE check flags bare relative framing.)
4. When you `record` the stories you kept, put each event's real date in its `event_date` field whenever you know it — that is what carries the correct date forward to future briefs.

# Output: write the brief to git + drop a notification stub + email digest

This routine writes to the git repo (your working directory is the cloned `claude-routines` repo). It does NOT write to Google Drive and does NOT POST to ntfy directly. A local bridge on the user's machine polls `pending-notifications/` every ~10 min and handles the ntfy push.

Let `{POST_URL} = https://khalic-lab.github.io/claude-routines/{YYYY}/{MM}/{DD}/news/`.

### 1. Write the brief

Use the Write tool to create `_posts/{YYYY-MM-DD}-news.md`. Front-matter:

```
---
layout: single
title: "News — {YYYY-MM-DD}"
date: {full ISO 8601 timestamp WITH timezone offset, identical to the _Generated line — e.g. 2026-06-29T19:09:59+02:00; NOT a bare date, which makes same-day briefs sort out of chronological order}
categories: [news]
---
```

### 2. Write the notification stub (fires every day, including weekends)

Use the Write tool to create `pending-notifications/{TIMESTAMP}-news.json` where `{TIMESTAMP} = $(date -u +%Y%m%dT%H%M%SZ)`:

```json
{
  "title": "News — {YYYY-MM-DD}",
  "click": "{POST_URL}",
  "body": "{teaser}",
  "tags": "newspaper"
}
```

`{teaser}` rules: ≤200 chars. The single most important item from this brief — the lead Swiss/Vaud or World story. Concrete and specific (e.g. "Federal Council unveils Bilaterals III ratification roadmap; Iran-Israel ceasefire holds day 67"), not generic. Escape any `"` inside the teaser as `\"`.

### 3. Commit and push

```bash
git add _posts/ pending-notifications/ index/
git -c user.email=routine@khalic-lab -c user.name="News Routine" commit -m "News — {YYYY-MM-DD}"
git push origin main || (git pull --rebase origin main && git push origin main)
```

If `git push` still fails after the rebase retry, append `git push failed: <reason>` to the brief's Coverage footer and continue.

### 4. Email digest (weekdays only, after git push step)

**Weekend gate:** if today is Saturday or Sunday in Europe/Zurich, SKIP the email step entirely. The brief is still written to git on weekends and the push notification still fires.

Otherwise (Monday–Friday), compose a News-only evening email via Gmail (`create_draft` only). There is NO consolidated cross-stream email — this email carries News content only.
- **To:** rflnogueira@me.com
- **Subject:** "News — {YYYY-MM-DD}"
- **Body:** ~250–350 words, plain text or simple markdown. Two labeled sections in this order: 🇨🇭 Switzerland & Vaud, 🌍 World. For each, 2–4 highlight bullets (top items only). End with: `Full brief: {POST_URL}`.
- If `create_draft` fails, retry once. If still failing, append `email draft creation failed: <reason>` to the brief's Coverage footer and don't fail the run.
