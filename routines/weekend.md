Write my weekend deep-read brief and publish it via the git pipeline. Use today's date (Saturday) in Europe/Zurich.

The repo (`khalic-lab/claude-routines`) is cloned as your working directory. Before doing anything else, sync:

```bash
git pull --ff-only origin main
```

# Mission

A long-form weekly digest. Coverage window: past 7 days. This is NOT a recap of dailies — it's a substantive read with deeper analysis, paper summaries, and connection-drawing across stories.

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

# Feed-first source order (apply to ALL sections)

**Fetch proxy — use it for any source that 403s a direct fetch.** A Cloudflare Worker at `https://fetch-proxy.khalic-lab.workers.dev` fetches a public URL from Cloudflare's edge with a real browser User-Agent and returns the page body; it is on the sandbox allowlist. The routine sandbox's own IP is 403'd on sight by Cloudflare/Akamai-fronted sites (lab blogs, most news HTML), so route those through the proxy:

    curl -fsSL -G "https://fetch-proxy.khalic-lab.workers.dev/" --data-urlencode "url=<TARGET URL>" -H "Authorization: Bearer ${FETCH_PROXY_TOKEN}"

- **Direct `curl` first for the allowlisted feed hosts** (`export.arxiv.org`, `services.nvd.nist.gov`, `www.cisa.gov`, `www.nature.com`, `www.quantamagazine.org`, `api.semanticscholar.org`, `www.srf.ch`, `www.letemps.ch`, `www.aljazeera.com`) — they work directly and arXiv asks automated clients to use it directly. Do NOT route these through the proxy.
- **Proxy for everything else** — lab blogs (Anthropic, OpenAI, DeepMind, Meta, Mistral, Apple), tech-news HTML (CNBC, TechCrunch, VentureBeat, Bloomberg, Fortune, MarkTechPost, …), and any other host that 403s a direct `curl`. This SUPERSEDES the "confirmed unavailable / do-not-waste-cycles" list below for HTML pages: try the proxy before treating a source as unavailable.
- A successful proxy fetch (HTTP 200 body) is a **direct fetch** — no `[via snippet]` tag. The proxy mirrors the upstream status, so a non-200 means the site hard-blocks even the proxy (Cloudflare JS/Turnstile challenge) or is paywalled — only then fall back to a search-engine snippet and tag `[via snippet]`.
- In the `Feeds hit` / Coverage footer, mark proxied fetches `{ok via proxy}` alongside the existing `{ok via curl}` / `{ok via WebFetch}` / `{fail — HTTP NNN}`.

The HTML pages of most quality sources return HTTP 403 from this routine sandbox. Many of those publishers also offer machine-readable feeds (RSS, Atom, JSON) that are reachable. **Always attempt the feed/API before the HTML page.**

**CRITICAL — try Bash{curl} BEFORE WebFetch.** WebFetch in this sandbox has been observed returning HTTP 403 on public, machine-readable feeds (NVD JSON, CISA KEV JSON, arXiv RSS, etc.). When attempting any feed below, FIRST try via Bash with `curl -fsSL <URL>`, parse the response, and only fall back to WebFetch if curl also fails. A successful curl fetch counts as a direct fetch. This is the binding-constraint workaround for the 403 wall.

**Order of attempts per topic, in priority:**
1. Verified-reachable feed below (or arXiv/NVD/CISA/Semantic Scholar APIs) via Bash{curl}.
2. Same feed via WebFetch fallback.
3. The publisher's HTML page.
4. Web search snippet (last resort, tag the citation `[via snippet]`).

**Verified-reachable feeds (live 2026-05-04):**

| Domain | Feed URL | Format | Use case |
|---|---|---|---|
| arXiv categories | `https://export.arxiv.org/rss/cs.LG` (also cs.AI, cs.CL, cs.CV, stat.ML) | RSS 2.0 | Latest ML papers per category |
| arXiv API (date-filtered) | `https://export.arxiv.org/api/query?search_query=cat:cs.LG&start=0&max_results=30&sortBy=submittedDate&sortOrder=descending` | Atom 1.0 | Date-confirmable paper queries; works for math.*, physics.*, astro-ph.* too — swap the cat filter |
| Quanta Magazine | `https://www.quantamagazine.org/feed/` | RSS 2.0 | Science features, math + fundamental physics |
| Nature flagship | `https://www.nature.com/nature.rss` | RSS | Nature general |
| Nature Physics | `https://www.nature.com/nphys.rss` | RSS | Physics journal |
| Nature Astronomy | `https://www.nature.com/natastron.rss` | RSS | Astronomy journal |
| Nature Methods | `https://www.nature.com/nm.rss` | RSS | Methods journal (biology-adjacent) |
| NVD CVEs (date-windowed) | `https://services.nvd.nist.gov/rest/json/cves/2.0?pubStartDate=...&pubEndDate=...` | JSON | Cybersecurity research section, CVE base |
| CISA KEV catalog | `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json` | JSON | Active-exploitation watch |
| Al Jazeera | `https://www.aljazeera.com/xml/rss/all.xml` | RSS | World politics (week-in-headlines) |
| Semantic Scholar API | `https://api.semanticscholar.org/graph/v1/paper/search?query=...` | JSON | Paper triangulation, citation counts (1000 req/sec free) |
| SRF (DE Swiss) | `https://www.srf.ch/news/bnf/rss/1646` | RSS 2.0 | DE-language Swiss |
| Le Temps (FR Swiss) | `https://www.letemps.ch/articles.rss` | RSS 2.0 | FR-language Swiss |

**Confirmed unavailable from this sandbox (do not waste cycles):** RTS.ch, NZZ (paywall 402), FAZ, Spiegel, swissinfo.ch, Reuters, Yahoo Finance, HuggingFace papers (no public feed), Le Monde RSS, NCSC.ch RSS.

**Reachable via the fetch-proxy (verified 2026-06-19) — USE these, don't skip them:** route through the proxy.
- bioRxiv / medRxiv → their JSON details API: `url=https://api.biorxiv.org/details/biorxiv/{YYYY-MM-DD}/{YYYY-MM-DD}/0` (swap `medrxiv`); returns title, abstract, DOI, and date per paper for the window — ideal for the Biology & Fundamental-science sections.
- Science.org → its RSS feeds (e.g. `https://www.science.org/rss/news_current.xml`, journal feeds); Science's article HTML 403s even through the proxy, so use the feed and cite the DOI / landing URL.

**Coverage footer accounting:**
- A citation that came from a feed/API fetch (curl OR WebFetch) counts as a **direct fetch**.
- A citation built from a search-engine snippet counts as **via-snippet** and must be tagged `[via snippet]`.
- In the `Feeds hit` line, distinguish between `{ok via curl}`, `{ok via WebFetch}`, and `{fail — HTTP NNN}`.

# Research methodology

The weekend brief warrants more aggressive iteration than the dailies. Per topic:
1. **Feed sweep first.** Hit the relevant feeds via Bash{curl} for the past 7 days (use the arXiv API with date filters; the Nature RSS feeds are rolling). This is your primary content source.
2. **Multi-pass search** for stories the feeds didn't surface. Start broad, refine 2–4 times, drill into specifics.
3. **Fetch full pages** liberally. arXiv abstracts (use the arXiv API — not the abstract HTML page, which 403s), full blog posts, GitHub READMEs, model cards. If fetch fails, fall back to snippets and tag with `[via snippet]`.
4. **Cross-reference rigorously.** For paper claims, locate the paper PDF if the abstract is ambiguous. Use Semantic Scholar API to triangulate citation/influence.
5. **Triangulate aggressively.** Significant findings should appear across at least 2 independent sources or be confirmable from primary docs.
6. **Don't trust your own first take.** Re-query with different framings to surface what your first query missed.
7. **Document exhausted leads** in the gaps footer.
8. **Sibling-brief consultation (do BEFORE tagging items `[single-source]`).** Read the daily briefs from the past 7 days, which now live in the local repo at `_posts/`. For each date D in {today-6, today-5, ..., today-1} (today=Saturday is the current run, so don't include it), check for `_posts/{D}-overview.md`, `_posts/{D}-ai-ml.md`, `_posts/{D}-cyber-papers.md` (the dedicated Markets brief has been retired). Use the Read tool on each that exists. If any sibling brief covered the same story with multiple independent sources, do NOT tag it `[single-source]` here. If sibling briefs are unavailable, proceed and note in Gaps.

# Sections (in order)

## 📰 Week in headlines (short)
Brief recap, ~5 bullets. World + Switzerland combined. Just the things that mattered structurally.

**Feed-first sources (curl first):** Al Jazeera RSS, SRF DE RSS, Le Temps FR RSS.

## 📄 ML / AI papers of the week (heaviest section)

**Feed-first sources (curl first):**
- **arXiv RSS per category**: `https://export.arxiv.org/rss/cs.LG`, `cs.AI`, `cs.CL`, `cs.CV`, `stat.ML`. Hit all five.
- **arXiv Atom API for week-window queries**: `https://export.arxiv.org/api/query?search_query=cat:cs.LG&start=0&max_results=100&sortBy=submittedDate&sortOrder=descending` — then filter the returned `<published>` dates client-side to the past 7 days.
- **Semantic Scholar** to triangulate which papers are getting attention this week.

T1 (HTML, often 403, fallback): arxiv.org listings, huggingface.co/papers, openreview.net.

Pull 8–12 ML/AI papers. Bias allocation:
- ~40% RL / agent / decision-making
- ~20% efficient inference, small models, on-device, MLX/quantization
- ~15% interpretability, mechanistic, alignment
- ~10% novel architectures (SSM/Mamba, hybrid, MoE)
- ~15% applied (anomaly detection, code, vision-language, multimodal)

For each paper:
- Title + arXiv ID + authors (first 3 + et al.)
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

Pull 5–8 papers across the fundamental sciences. Aim for breadth:
- ~30% physics (particle, condensed matter, hep, gravity)
- ~25% quantum (quant-ph, PRX Quantum)
- ~20% astronomy / astrophysics / cosmology
- ~15% mathematics (major proofs, conjecture progress, surveys)
- ~10% adjacent (chemistry, climate physics, computational)

For each paper, same format as ML papers section. Math papers may need a 2-line "context" note.

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

5–10 items.

## 📊 Data science / applied ML
T1: company engineering blogs (Netflix, Uber, Airbnb, Stripe, Spotify), papers with code releases.
T2: thegradient.pub, eugeneyan.com, chiphuyen.com, hamel.dev, fast.ai.

Real production ML, evaluation methodology, lessons from deployment, useful tools. Skip Medium / Towards Data Science.

## 📝 Essays & long-form
T1/T2: simonwillison.net, karpathy.bearblog.dev, dnhkng.github.io, lilianweng.github.io, gwern.net, distill.pub, quantamagazine.org features (RSS via curl), lesswrong.com (high-karma posts), acoup.blog, drbex.io.

Long-form pieces published this week. 5–10 items. Each: title, author, 2–3 sentence summary, your read on whether it's worth the time.

## 🛡️ Cybersecurity research of the week

**Feed-first sources (curl first):**
- **CISA KEV JSON**: filter `dateAdded` for the past 7 days.
- **NVD JSON 2.0** for high-CVSS CVEs from the week if needed (date-windowed query).

T1: published security research papers, vendor post-incident writeups.
T2: therecord.media, mandiant.com/resources, unit42.paloaltonetworks.com, research.checkpoint.com, sentinelone.com/labs.

Substantial threat research, novel TTPs, post-mortem writeups. Skip the daily CVE churn.

## 🧠 Cross-cutting threads
A short final section: 2–4 themes you noticed across this week's content. This is the section where synthesis adds real value beyond aggregation.

# Format

```
# Weekend Deep Read — {YYYY-MM-DD}

_Coverage: {date 7 days ago} to {today}. Generated {timestamp} Europe/Zurich._

## 📰 Week in headlines
- ...

## 📄 Papers of the week

### [Paper title]
**[arXiv:XXXX.XXXXX](URL)** · Authors et al. · `[preprint]`
3–5 sentence summary.
*Why this matters:* one-line take.

[... all sections ...]

---

## Coverage footer
- Sources used: T1 = N, T2 = N, T3 = 0
- Languages: EN, FR, DE, ...
- Direct fetches: N | via-snippet citations: N
- Feeds hit (with reachability and method): arXiv RSS cs.LG {ok via curl|ok via WebFetch|fail — HTTP NNN}, arXiv API {...}, Quanta RSS {...}, Nature RSS {...}, NVD {...}, CISA KEV {...}, Al Jazeera {...}, ...
- Sibling consultation: {performed | skipped — reason}
- Gaps: ...
- Things I deliberately cut: ...
```

# Constraints

- Length target: long. 4000–8000 words.
- Paper summaries in your own words. Never copy abstract text directly.
- If you'd cite an X/Twitter thread or HN comment, find the actual paper or blog post and cite that.
- The cross-cutting threads section is the one place you should be opinionated. Elsewhere stay descriptive.
- Don't pad. If a section has 3 strong items and 5 weak, ship the 3.

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

Before composing AND after writing the brief, follow `tools/dedup/DEDUP.md` exactly. It dedupes your candidate stories against the rolling embeddings index so a story isn't re-run for days. **This routine's slug is `weekend`.** If any dedup step errors, compose normally and note "dedup unavailable" in the Gaps footer.

# Date discipline (read before writing any date, weekday, or scheduled event)

You derive "today" from the machine-stamped `_Generated <ISO> Europe/Zurich_` header — that part is reliable. The errors come from *arithmetic on top of it* (counting forward to a weekday; re-guessing which Sunday a vote falls on). So before composing:

1. **Build a dated weekday table for the coverage window (today ±7 days) and read every weekday↔date reference off it — never count forward in your head.** Shape: `… Sat 2026-06-13 · Sun 06-14 · Mon 06-15 · Tue 06-16 · Wed 06-17 · Thu 06-18 (today) · Fri 06-19 …`. (The `lint` WEEKDAY check rejects an adjacent weekday/date mismatch, e.g. "Wednesday 11 June" when the 11th is a Thursday.)
2. **Scheduled / dated events (votes, IPO pricings, conferences, deadlines, embargoes): state the ABSOLUTE date, and do NOT re-derive it.** If the dedup `check` returned a `matched.event_date` for the story, use *that* date verbatim — it is the date the pipeline already established and carries forward. Never re-guess "which Sunday / this weekend / tomorrow / next week." (A 2026-06-06 brief misdated the 14-June federal vote to "Sunday 7 June" by reasoning "it's a Sunday vote and it's the weekend → this Sunday" instead of reading the established 14-June date.)
3. **Never write relative framing** — "this weekend", "tomorrow", "next week", "in N days" — **for a dated event without the absolute date right beside it.** (The `lint` SCHEDULE check flags bare relative framing.)
4. When you `record` the stories you kept, put each event's real date in its `event_date` field whenever you know it — that is what carries the correct date forward to future briefs.

# Output: write the brief to git + drop a notification stub + email digest

This routine writes to the git repo (working directory is the cloned `claude-routines` repo). It does NOT write to Google Drive and does NOT POST to ntfy directly. A local bridge on the user's machine polls `pending-notifications/` every ~10 min and handles the ntfy push.

Let `{POST_URL} = https://khalic-lab.github.io/claude-routines/{YYYY}/{MM}/{DD}/weekend/`.

### 1. Write the brief

Use the Write tool to create `_posts/{YYYY-MM-DD}-weekend.md`. The file MUST start with this front-matter block, then a blank line, then the brief body:

```
---
layout: single
title: "Weekend Deep Read — {YYYY-MM-DD}"
date: {YYYY-MM-DD}
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
git add _posts/ pending-notifications/ index/
git -c user.email=routine@khalic-lab -c user.name="News Routine" commit -m "Weekend Deep Read — {YYYY-MM-DD}"
git push origin main || (git pull --rebase origin main && git push origin main)
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