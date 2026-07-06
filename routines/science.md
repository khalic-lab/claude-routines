Write my weekly science brief and publish it via the git pipeline. Use today's date (Wednesday) in Europe/Zurich.

The repo (`khalic-lab/claude-routines`) is cloned as your working directory. Before doing anything else, sync:

```bash
git pull --ff-only origin main
```

# Mission

A weekly read on the most significant developments across the natural sciences — physics, math, quantum, astronomy/cosmology, biology/medicine/neuroscience, chemistry, climate/earth. Coverage window: the past 7 days.

This is NON-AI science. **EXCLUDE AI/ML and computer science** — arXiv `cs.*` / `stat.ML` and ML preprints belong to the AI/ML edition, not here. A result is in scope only if its primary contribution is to a natural science, not to machine learning or CS (a physics paper that *uses* an ML method is fine; an ML-methods paper applied to physics is not).

Three desks, deep over broad: pick the week's genuinely-new findings, read the primary papers, and decode them for a numerate non-specialist. Better to go deep on a handful of real results than to skim a feed.

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

1. **Tiers.** T1 = primary (preprint, journal research article, official lab/observatory/agency release). T2 = quality secondary. T3 = discovery only (HN/Reddit/Lobsters/X) — used to find stories, NEVER cited. Click through and cite the underlying T1/T2. **A quality outlet's news report or feature *about* a study is T2 secondary, never T1 — even when that outlet also publishes primary research.** Nature news/features (URLs of the form `nature.com/articles/d41586-…`) are journalism about papers, not the papers themselves; the primary source is the underlying paper (`nature.com/articles/s41586-…`) or its preprint. When you cover a study, locate and cite that **primary paper** — read its abstract — and use the news write-up only as a secondary pointer or for triangulation. A bullet whose sole citation is a `d41586` Nature-news piece (or any equivalent secondary report) is mis-sourced: find the paper, or if you genuinely cannot, frame it as 'as reported by …' and tag `[single-source]` — never present secondary journalism as the primary.
2. **Citation format.** Every item ends with a markdown link to one specific URL (DOI, arXiv abstract, or article landing). Include publication name and date. No "according to recent reports" without a link.
3. **Triangulation.** Significant claims need two independent sources where feasible. Single-sourced → mark `[single-source]`. Disagreements → surface both versions explicitly.
4. **Diversification.** Within each desk, span subfields and institutions; don't let one journal or one lab dominate.
5. **Tags.** Preprints → `[preprint]`. Single source → `[single-source]`. Contested → `[disputed]`.
6. **No fabrication.** Never invent a URL, author, date, or quote. **The no-fabrication rule extends to date claims**: a paper from last month is NOT "this week's." If you cannot verify a paper was submitted or published within the past 7 days, do not include it under a section that claims this week's content.
7. **Volume cap.** 4–8 items per desk. Quality is the cap — better to ship 3 strong findings in a desk than pad to 8.
8. **Fetch transparency.** When you successfully fetch a URL/feed and confirm content, no marker. When the citation is based only on a search-engine snippet, append `[via snippet]` to the citation.

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

Before composing AND after writing the brief, follow `tools/dedup/DEDUP.md` exactly. It dedupes your candidate stories against the rolling embeddings index so a story isn't re-run for days. **This routine's slug is `science`.** If any dedup step errors, compose normally and note "dedup unavailable" in the Gaps footer.

# Date discipline (read before writing any date, weekday, or scheduled event)

You derive "today" from the machine-stamped `_Generated <ISO> Europe/Zurich_` header — that part is reliable. The errors come from *arithmetic on top of it* (counting forward to a weekday; re-guessing which Sunday a vote falls on). So before composing:

1. **Build a dated weekday table for the coverage window (today ±7 days) and read every weekday↔date reference off it — never count forward in your head.** Shape: `… Sat 2026-06-13 · Sun 06-14 · Mon 06-15 · Tue 06-16 · Wed 06-17 · Thu 06-18 (today) · Fri 06-19 …`. (The `lint` WEEKDAY check rejects an adjacent weekday/date mismatch, e.g. "Wednesday 11 June" when the 11th is a Thursday.)
2. **Scheduled / dated events (votes, IPO pricings, conferences, deadlines, embargoes): state the ABSOLUTE date, and do NOT re-derive it.** If the dedup `check` returned a `matched.event_date` for the story, use *that* date verbatim — it is the date the pipeline already established and carries forward. Never re-guess "which Sunday / this weekend / tomorrow / next week." (A 2026-06-06 brief misdated the 14-June federal vote to "Sunday 7 June" by reasoning "it's a Sunday vote and it's the weekend → this Sunday" instead of reading the established 14-June date.)
3. **Never write relative framing** — "this weekend", "tomorrow", "next week", "in N days" — **for a dated event without the absolute date right beside it.** (The `lint` SCHEDULE check flags bare relative framing.)
4. When you `record` the stories you kept, put each event's real date in its `event_date` field whenever you know it — that is what carries the correct date forward to future briefs.

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
git add _posts/ pending-notifications/ index/ _data/
git -c user.email=routine@khalic-lab -c user.name="News Routine" commit -m "Science — {YYYY-MM-DD}"
git push origin main || (git pull --rebase origin main && git push origin main)
```

If `git push` still fails after the rebase retry, append `git push failed: <reason>` to the brief's Coverage footer and continue.
