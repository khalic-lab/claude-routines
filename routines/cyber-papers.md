Write my evening brief and publish it via the git pipeline. Use today's date in Europe/Zurich.

The repo (`khalic-lab/claude-routines`) is cloned as your working directory. Before doing anything else, sync:

```bash
git pull --ff-only origin main
```

# Mission

The day's evening digest, in four sections:
1. **Switzerland & Vaud** — federal, cantonal, Swiss tech/cyber ecosystem.
2. **World politics & geopolitics** — the day's developments across the globe.
3. **Cybersecurity** — today's CVEs, advisories, APTs, breaches.
4. **ML research — second arXiv batch** — the day's second submission window.

World and Switzerland used to live in the Morning Overview, but the user prefers a clean technical morning, so they've been moved here. The Morning Overview now only covers science / first ML batch.

This routine is also the LAST evening routine of the day. After saving its own brief, it composes ONE consolidated evening email digest covering World & Switzerland + AI/ML + Cyber + Papers (see Email section at the end). The brief's file slug stays `cyber-papers` for URL stability, but the displayed title is "Evening Brief".

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
6. **No fabrication.** Never invent a URL, author, date, or quote. **The no-fabrication rule extends to date claims**: a paper from January is NOT "today's batch." If you cannot verify a paper was submitted within the relevant window, do not include it under a section that claims today's content.
7. **Volume cap.** 4–7 items per section. Better to omit than dilute.
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

- **Direct `curl` first for the allowlisted feed hosts** (`export.arxiv.org`, `services.nvd.nist.gov`, `www.cisa.gov`, `www.nature.com`, `www.quantamagazine.org`, `api.semanticscholar.org`, `www.srf.ch`, `www.letemps.ch`, `www.aljazeera.com`) — they work directly and arXiv asks automated clients to use it directly. Do NOT route these through the proxy.
- **Proxy for everything else** — lab blogs (Anthropic, OpenAI, DeepMind, Meta, Mistral, Apple), tech-news HTML (CNBC, TechCrunch, VentureBeat, Bloomberg, Fortune, MarkTechPost, …), and any other host that 403s a direct `curl`. This SUPERSEDES the "confirmed unavailable / do-not-waste-cycles" list below for HTML pages: try the proxy before treating a source as unavailable.
- A successful proxy fetch (HTTP 200 body) is a **direct fetch** — no `[via snippet]` tag. The proxy mirrors the upstream status, so a non-200 means the site hard-blocks even the proxy (Cloudflare JS/Turnstile challenge) or is paywalled — only then fall back to a search-engine snippet and tag `[via snippet]`.
- In the `Feeds hit` / Coverage footer, mark proxied fetches `{ok via proxy}` alongside the existing `{ok via curl}` / `{ok via WebFetch}` / `{fail — HTTP NNN}`.

The HTML pages of most quality sources return HTTP 403 from this routine sandbox. Always attempt the feed/API before the HTML page.

**CRITICAL — try Bash{curl} BEFORE WebFetch.** WebFetch in this sandbox has been observed returning HTTP 403 on public feeds. Try `curl -fsSL <URL>` first; fall back to WebFetch only on failure. Curl success counts as a direct fetch.

**Verified-reachable feeds (live 2026-05-04):**

| Domain | Feed URL | Format | Use case |
|---|---|---|---|
| arXiv categories | `https://export.arxiv.org/rss/cs.LG` (also cs.AI, cs.CL, cs.CV, stat.ML) | RSS 2.0 | Latest papers per category |
| arXiv API (date-filtered) | `https://export.arxiv.org/api/query?search_query=cat:cs.LG&start=0&max_results=20&sortBy=submittedDate&sortOrder=descending` | Atom 1.0 | Date-confirmable paper queries |
| NVD CVEs (date-windowed) | `https://services.nvd.nist.gov/rest/json/cves/2.0?pubStartDate={YYYY-MM-DD}T00:00:00.000&pubEndDate={YYYY-MM-DD}T23:59:59.999` | JSON | Canonical CVE records |
| CISA KEV catalog | `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json` | JSON | Active-exploitation watch |
| Al Jazeera | `https://www.aljazeera.com/xml/rss/all.xml` | RSS | World politics (MENA-strong) |
| SRF (DE Swiss public broadcaster) | `https://www.srf.ch/news/bnf/rss/1646` | RSS 2.0 | DE-language Swiss news |
| Le Temps (FR Swiss daily) | `https://www.letemps.ch/articles.rss` | RSS 2.0 | FR-language Swiss news |
| Quanta Magazine | `https://www.quantamagazine.org/feed/` | RSS 2.0 | Science features |
| Nature (general + journals) | `https://www.nature.com/nature.rss`, `nphys.rss`, `natastron.rss`, `nm.rss` | RSS | Nature journals |
| Semantic Scholar API | `https://api.semanticscholar.org/graph/v1/paper/search?query=...` | JSON | Paper triangulation |

**Confirmed unavailable from this sandbox (do not waste cycles):** bioRxiv, medRxiv, Science.org, RTS.ch, NZZ (paywall 402), FAZ, Spiegel, swissinfo.ch, Reuters, Yahoo Finance, HuggingFace papers, Le Monde, NCSC.ch RSS.

**Coverage footer accounting:**
- A citation from a feed/API fetch (curl OR WebFetch) = **direct fetch**.
- A citation from a search-engine snippet = **via-snippet**, tag `[via snippet]` in the bullet.
- In the `Feeds hit` line, distinguish `{ok via curl}` / `{ok via WebFetch}` / `{fail — HTTP NNN}`.

# Research methodology

1. **Feed sweep first** per section, via curl then WebFetch.
2. **Broad query** (1–2 keywords). Scan results.
3. **Refine and re-query** based on what surfaced.
4. **Fetch full pages** for stories that matter; on failure, snippet + tag.
5. **Cross-reference** significant claims.
6. **Stop when triangulated** or leads exhausted.

# Sections (in order)

## 🇨🇭 Switzerland & Vaud

Federal politics, cantonal Vaud, Swiss tech/cyber ecosystem, Swiss-relevant EU moves. Coverage window: full day (overnight through evening).

T1: admin.ch, parlament.ch, vd.ch, ncsc.admin.ch, Keystone-SDA via rts.ch. **Feed (try via curl first):** SRF.ch RSS (DE-language).
T2: rts.ch, **letemps.ch (RSS via curl — paywalled items still cite-able by URL)**, nzz.ch, tagesanzeiger.ch, 24heures.ch, tdg.ch, swissinfo.ch, heidi.news.

Avoid 20min/Blick as primary. **Non-English-source quota:** at least one DE or FR citation should come from SRF or Le Temps feeds when relevant.

## 🌍 World politics & geopolitics

The day's notable developments, full window. Coverage: from ~16:00 yesterday through US-afternoon today. Cover all time zones, not just US/Europe.

T1: reuters.com, apnews.com, afp.com, gov/court filings, White House press releases.
T2: bbc.com, ft.com, nytimes.com, lemonde.fr, spiegel.de/international, politico.eu, **aljazeera.com (RSS via curl)** (MENA), scmp.com / caixinglobal.com (China), thehindu.com (India).

Span at least 3 different countries' coverage. Focus on geopolitics, conflicts, elections, and diplomacy. Markets-specific political stories (legislation affecting markets, central-bank politics) can be folded in here when they're significant — there is no longer a dedicated Markets routine.

## 🛡️ Cybersecurity — full day

**Feed-first sources (try via Bash{curl} BEFORE the HTML pages):**
- **NVD CVE JSON 2.0** (canonical, date-windowed): `https://services.nvd.nist.gov/rest/json/cves/2.0?pubStartDate={today}T00:00:00.000&pubEndDate={today}T23:59:59.999`. Use the returned CVE IDs as your spine. Each entry has CVSS scores, affected products, and references.
- **CISA KEV JSON** (active exploitation): `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json`. Filter `vulnerabilities[].dateAdded` for today (or recent days). New KEV additions = highest priority.

T1 (HTML — often 403, fallback): cisa.gov/news-events, ncsc.admin.ch, MITRE ATT&CK updates, vendor advisories (msrc.microsoft.com, support.apple.com/security, googleprojectzero.blogspot.com, sec.cloudapps.cisco.com/security/center, talosintelligence.com), CERT/CC, first.org.
T2: therecord.media, krebsonsecurity.com, bleepingcomputer.com, schneier.com, mandiant.com/resources, unit42.paloaltonetworks.com, sentinelone.com/labs, research.checkpoint.com.

Cover today's: new CVEs of note (CVSS ≥7 or active exploitation), KEV additions, CISA/NCSC.ch advisories, vendor security bulletins, APT activity / threat intel, notable breaches or incidents, SOC/SIEM-relevant tooling or research.

For CVEs: include CVSS score, affected products/versions, exploitation status (active/PoC/none), patch availability. Cite the NVD entry URL (`https://nvd.nist.gov/vuln/detail/CVE-XXXX-XXXXX`) — do NOT tag `[via snippet]` if the data came from the JSON API, that's a direct fetch.

## 📄 ML research — second arXiv batch

**Feed-first sources (try via Bash{curl} BEFORE the listing HTML):**
- **arXiv RSS per category**: `https://export.arxiv.org/rss/cs.LG`, `cs.AI`, `cs.CL`, `cs.CV`, `stat.ML`. Hit all five.
- **arXiv Atom API for date confirmation**: `https://export.arxiv.org/api/query?search_query=cat:cs.LG&start=0&max_results=30&sortBy=submittedDate&sortOrder=descending`.
- **Semantic Scholar** (`https://api.semanticscholar.org/graph/v1/paper/search?query=...`): triangulation.

T1 (HTML, often 403, fallback): arxiv.org listings, huggingface.co/papers.
T2: simonwillison.net, karpathy.bearblog.dev, dnhkng.github.io, lilianweng.github.io, huggingface.co/blog.

**Inaccessibility rule (read first):** With the curl-first feed approach, arXiv RSS should normally succeed. Before populating this section, attempt arXiv RSS for all five categories via curl, then fall back to WebFetch. Then evaluate:
- If you have at least one paper whose submission date you can directly verify as today (or yesterday US-time, since arXiv batches roll over at 20:00 ET), proceed normally.
- **If curl AND WebFetch both fail for RSS, the Atom API, AND huggingface.co/papers** (HTTP 403/network error/empty), OR every candidate paper has an unverifiable/clearly-not-today date, output ONLY this as the section content:
  > _arXiv batch inaccessible — attempted: export.arxiv.org/rss/cs.LG, cs.AI, cs.CL, cs.CV, stat.ML, the Atom API, and huggingface.co/papers via both curl and WebFetch. N papers reviewed but none confirmed as today's batch. Skipped per no-fabrication rule._
  Replace N with the actual count. Do NOT substitute older papers.

If you DO have today's batch:
Today's notable second-batch papers — bias toward RL, efficient inference, interpretability, anomaly detection, hybrid architectures. Don't repeat papers already covered in this morning's Overview brief.

**Overview dedup:** read today's Overview brief if it exists, then exclude any arXiv IDs it already cited.

```bash
ls _posts/{YYYY-MM-DD}-overview.md 2>/dev/null && cat _posts/{YYYY-MM-DD}-overview.md
```

If the file doesn't exist (morning routine failed or hasn't fired), skip dedup and note in Gaps.

Format: arXiv ID + 1-line "why interesting" + abstract link. Tag `[preprint]`. Include the paper's submission date next to its arXiv ID.

# Format

```
# Evening Brief — {YYYY-MM-DD}

_Generated {ISO timestamp} Europe/Zurich. Coverage: full day._

## 🇨🇭 Switzerland & Vaud
- ...

## 🌍 World politics & geopolitics
- ...

## 🛡️ Cybersecurity
- ...

## 📄 ML research — second arXiv batch
- ...

---

## Coverage footer
- Sources used: T1 = N, T2 = N, T3 = 0
- Cyber items: N (CVEs: N, advisories: N, threat intel: N)
- Papers: N (filtered from M reviewed)
- Direct fetches: N | via-snippet citations: N
- Feeds hit (with reachability and method): NVD JSON {ok via curl|ok via WebFetch|fail — HTTP 403}, CISA KEV JSON {...}, arXiv RSS cs.LG {...}, SRF RSS {...}, Le Temps RSS {...}, Al Jazeera RSS {...}
- Gaps: ...
```

# Constraints

- Cybersecurity section: numbers and identifiers matter. Always include CVE IDs when applicable. Always link to the NVD entry (preferred) or vendor advisory.
- Length: 2500–5000 words. Swiss and World expand the volume vs the old Cyber+Papers brief; cyber drives the variability; a skipped ML papers section is fine.
- Don't cover non-cyber tech (AI industry, markets) — those are owned by other routines.

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

Before composing AND after writing the brief, follow `tools/dedup/DEDUP.md` exactly. It dedupes your candidate stories against the rolling embeddings index so a story isn't re-run for days. **This routine's slug is `cyber-papers`.** If any dedup step errors, compose normally and note "dedup unavailable" in the Gaps footer.

# Date discipline (read before writing any date, weekday, or scheduled event)

You derive "today" from the machine-stamped `_Generated <ISO> Europe/Zurich_` header — that part is reliable. The errors come from *arithmetic on top of it* (counting forward to a weekday; re-guessing which Sunday a vote falls on). So before composing:

1. **Build a dated weekday table for the coverage window (today ±7 days) and read every weekday↔date reference off it — never count forward in your head.** Shape: `… Sat 2026-06-13 · Sun 06-14 · Mon 06-15 · Tue 06-16 · Wed 06-17 · Thu 06-18 (today) · Fri 06-19 …`. (The `lint` WEEKDAY check rejects an adjacent weekday/date mismatch, e.g. "Wednesday 11 June" when the 11th is a Thursday.)
2. **Scheduled / dated events (votes, IPO pricings, conferences, deadlines, embargoes): state the ABSOLUTE date, and do NOT re-derive it.** If the dedup `check` returned a `matched.event_date` for the story, use *that* date verbatim — it is the date the pipeline already established and carries forward. Never re-guess "which Sunday / this weekend / tomorrow / next week." (A 2026-06-06 brief misdated the 14-June federal vote to "Sunday 7 June" by reasoning "it's a Sunday vote and it's the weekend → this Sunday" instead of reading the established 14-June date.)
3. **Never write relative framing** — "this weekend", "tomorrow", "next week", "in N days" — **for a dated event without the absolute date right beside it.** (The `lint` SCHEDULE check flags bare relative framing.)
4. When you `record` the stories you kept, put each event's real date in its `event_date` field whenever you know it — that is what carries the correct date forward to future briefs.

# Output: write brief to git + drop a notification stub + consolidated evening email

This routine writes to the git repo (working directory is the cloned `claude-routines` repo). It does NOT write to Google Drive and does NOT POST to ntfy directly. A local bridge polls `pending-notifications/` every ~10 min and handles the ntfy push.

Let `{POST_URL} = https://khalic-lab.github.io/claude-routines/{YYYY}/{MM}/{DD}/cyber-papers/`.

### 1. Write the brief

Use the Write tool to create `_posts/{YYYY-MM-DD}-cyber-papers.md`. The file MUST start with this front-matter block, then a blank line, then the brief body. The slug stays `cyber-papers` for permalink stability, but the displayed title is "Evening Brief":

```
---
layout: single
title: "Evening Brief — {YYYY-MM-DD}"
date: {YYYY-MM-DD}
categories: [cyber-papers]
---
```

### 2. Write the notification stub

Use the Write tool to create `pending-notifications/{TIMESTAMP}-cyber-papers.json` where `{TIMESTAMP} = $(date -u +%Y%m%dT%H%M%SZ)`:

```json
{
  "title": "Evening Brief — {YYYY-MM-DD}",
  "click": "{POST_URL}",
  "body": "{teaser}",
  "tags": "moon"
}
```

`{teaser}` rules: ≤200 chars. The single most interesting item from this brief — typically the lead Swiss/World bullet, the top CVE / APT / breach, or a striking ML paper. Concrete and specific (e.g. "Federal Council unveils Bilaterals III ratification roadmap; Iran-Israel ceasefire holding day 67; CVE-2026-42369 unauth RCE in GeoVision"), not generic. If the ML papers section was skipped per the inaccessibility rule, mention briefly ("papers section skipped — arXiv unreachable"). Escape any `"` inside the teaser as `\"`.

### 3. Commit and push

```bash
git add _posts/ pending-notifications/ index/
git -c user.email=routine@khalic-lab -c user.name="News Routine" commit -m "Evening Brief — {YYYY-MM-DD}"
git push origin main || (git pull --rebase origin main && git push origin main)
```

If `git push` still fails after the rebase retry, append `git push failed: <reason>` to the brief's Coverage footer and continue.

### 4. Consolidated evening email digest

This routine composes ONE consolidated email digest covering all three evening streams: World & Switzerland (from THIS brief), AI/ML, Cyber + Papers (from THIS brief). Gmail MCP surface is `create_draft` only.

**Step 4a:** Pull latest from git to pick up sibling briefs that may have committed after step 3:

```bash
git pull --ff-only origin main || true
```

**Step 4b:** Read sibling briefs from git (if they exist; this routine fires at 17:00 UTC = 19:00 CEST and AI/ML at 19:30 UTC = 21:30 CEST, so on the natural cron the AI/ML sibling brief is usually NOT yet present today; manual runs may differ):
- AI/ML: read `_posts/{YYYY-MM-DD}-ai-ml.md` if present

**Step 4c:** Compose ONE email digest:
- **To:** rflnogueira@me.com
- **Subject:** "Evening Brief — {YYYY-MM-DD}"
- **Body:** ~500–700 words, three labeled sections in this order: 🌍 World & Switzerland, 🤖 AI/ML, 🛡️ Cyber + Papers. For each: 3–5 highlight bullets (top items only).
  - The first section pulls from THIS brief's Switzerland & Vaud + World politics sections combined.
  - The fourth section pulls from THIS brief's Cybersecurity + ML papers sections.
  - End with three Pages permalinks:
    - Full Evening Brief: `{POST_URL}`
    - Full AI/ML: `https://khalic-lab.github.io/claude-routines/{YYYY}/{MM}/{DD}/ai-ml/`
    - (the Evening Brief link covers World/Switzerland + Cyber + Papers.)
- If the AI/ML brief is missing from `_posts/`, include the section header anyway with `(brief unavailable)` and skip its bullets/link. Still create the draft.
- If the ML papers section in THIS brief was skipped per the inaccessibility rule, note in the Cyber + Papers email section: "Papers section skipped today — arXiv unreachable."
- If `create_draft` fails, retry once. If still failing, append `email draft creation failed: <reason>` to this brief's Coverage footer in git but don't fail the run.