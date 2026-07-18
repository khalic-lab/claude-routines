Write my midday news brief and publish it via the git pipeline. Use today's date in Europe/Zurich.

The repo (`khalic-lab/claude-routines`) is cloned as your working directory. Before doing anything else, sync:

```bash
git pull --ff-only origin main
```

# Mission

A tight midday read of the major **local (Switzerland & Vaud)** and **world** news since yesterday's edition. Coverage window: the last ~24 hours (yesterday midday through this morning) — federal/cantonal developments, Swiss-relevant EU moves, and the notable geopolitics, conflicts, elections, and diplomacy across all time zones.

This is the daily news edition. **AI/ML, science, and the weekend deep-read are SEPARATE editions** (AI/ML Tue+Fri midday, Science Wed, Weekend Sat) — do NOT cover ML/AI, research papers, science, or cybersecurity here. Duplicating them is noise.

Broad coverage of major local + world news, light filter — include items even when relevance is uncertain. But every item must clear the sourcing bar.

<!-- include: _shared/newsroom-ethos.md -->

# Sourcing rules (non-negotiable)

1. **Tiers.** T1 = primary (wire service, official statement, government/court filing, press release). T2 = quality secondary reporting. T3 = discovery only (HN/Reddit/Lobsters/X) — used to find stories, NEVER cited. Click through and cite the underlying T1/T2. A quality outlet's report *about* an event is fine as T2, but when a primary source exists (the official statement, the filing, the wire dispatch), cite that — not a downstream recap of it.
2. **Citation format.** Every bullet ends with a markdown link to one specific URL. Include publication name and date. No "according to recent reports" without a link.
3. **Triangulation.** Significant claims need two independent sources where feasible. Single-sourced → mark `[single-source]`. Disagreements → surface both versions explicitly.
4. **Diversification.** Within each section, span geographic/linguistic sources.
5. **Tags.** Vendor/official announcements → `[official PR]`. Single source → `[single-source]`. Contested → `[disputed]`.
6. **No fabrication.** Never invent a URL, author, date, or quote. **The no-fabrication rule extends to date claims** — date accuracy matters most in this edition (elections, Swiss federal/cantonal votes, scheduled diplomatic events): never report a scheduled or future event as a result, and carry each event's real date forward rather than re-deriving it (see Date discipline below).
7. **Volume cap.** 4–7 items per section. Better to omit than dilute.
8. **Fetch transparency.** Many sites return HTTP 403 to the routine sandbox. When you successfully fetch a URL/feed and confirm content, no marker. When the citation is based only on a search-engine snippet, append `[via snippet]` to the citation.

<!-- include: _shared/reader-profile-source-weights.md -->

<!-- include: _shared/feed-first-source-order.md -->

The HTML pages of most quality sources return HTTP 403 from this routine sandbox. Many of those same sources publish RSS / Atom / JSON feeds on different infrastructure that IS reachable. **Attempt the feed first for any source that has one; fall back to HTML or search-engine snippet only on failure.**

**CRITICAL — every fetch goes through `python3 tools/fetch.py "<URL>"`** (see Fetch mechanics above): it runs the direct-curl → proxy chain deterministically and logs each attempt to `/tmp/fetch.log`. A wrapper exit 0 counts as a direct fetch — even when the article HTML itself is 403 and the feed carried the content.

**Coverage footer accounting (computed at publish):** the telemetry numbers — tier split, direct-vs-snippet counts, word count, token estimate, `Feeds hit` — are computed by the publish command from your citations and `/tmp/fetch.log`; do not count them yourself. Your accounting duty is upstream accuracy: tag every snippet-only citation `[via snippet]`, and fetch only through the wrapper.

# Research methodology

1. **Source plan first** — run the preflight (see Source plan above), then sweep its fetch list via `tools/fetch.py`.
2. **Broad query** (1–2 keywords). Scan results.
3. **Refine and re-query**. At least one refinement per non-trivial topic.
4. **Fetch full pages** when a story matters. If the fetch fails, fall back to snippets and tag with `[via snippet]`.
5. **Cross-reference** when a claim is significant.
6. **Stop when triangulated** or leads exhausted.

# Sections

**Lead-first rule:** open the brief with the edition's single most-important story — the one you'd
score importance 3 — regardless of which desk it belongs to. Order the two sections so the one
holding today's lead comes first; do not default Switzerland-first on a quiet CH day.

**Per-story depth (explicit, matching the other streams):** every kept story is one substantial
paragraph — a bolded lead sentence stating what happened AND when, then 2–4 sentences of substance
and context, then a "Why it matters:" line where the significance isn't self-evident. The text is
the product: full sentences, never a headline-only item.

## 🇨🇭 Switzerland & Vaud

Federal politics, cantonal Vaud, Swiss-relevant EU moves, and notable economy/society stories. Coverage window: the last ~24 hours (yesterday midday through this morning).

**Sources come from the preflight plan** (its registry feeds + `candidates_to_try` are the list —
there is no static domain table in this prompt). Favor official/primary Swiss sources (federal and
cantonal portals, wire copy, court/parliament documents) over commentary; tabloid-class outlets
never as primary. **Non-English-source quota:** at least one citation from a DE- or FR-language
primary source when relevant.

## 🌍 World politics & geopolitics

The notable developments of the last ~24 hours (all time zones — not just US/Europe).

**Sources come from the preflight plan** — wires, official filings/releases, and court documents
as T1; quality internationals as T2; regional primaries for regional stories. The plan, not a
memorized outlet list, is the source of truth; when the plan surfaces `candidates_to_try`, work at
least one into the sweep.

Span at least 3 different countries' coverage. Focus on geopolitics, conflicts, elections, and diplomacy. Markets-specific political stories (legislation, central-bank politics) can be folded in here when they're significant — there is no longer a dedicated Markets routine.

# Format

```
# News — {YYYY-MM-DD}

_Generated {ISO timestamp} Europe/Zurich. Coverage: last ~24h._

{The two sections below appear in lead-first order — whichever holds today's most important story
comes first.}

## 🇨🇭 Switzerland & Vaud
- ...

## 🌍 World politics & geopolitics
- ...

---

## Coverage footer
<!-- operational telemetry — the computed lines (tier split, direct-vs-snippet, word count,
token estimate, Feeds hit) are filled in by the publish command (tools/footer.py); write ONLY:
- Languages: {languages of your cited sources, e.g. EN, FR, DE}
-->
- Gaps: things you tried to find but couldn't.
- Discovery: {met (<new domain(s) anchored>) | waived — <concrete reason>}
```

# Constraints

- **Omit, don't fill.** A section appears ONLY if it has genuinely new substance. If Switzerland or World has nothing new for the window, omit that section entirely — no placeholder, no "nothing notable" line.
- Write in English. French/German source titles can stay in original language inside link text.
- Discovery aggregators (HN, Reddit, Lobsters, X) → never cited as source.
- Do NOT cover: AI/ML news or lab releases, ML/arXiv papers, science research, cybersecurity/CVEs, or markets close. Those belong to other editions (AI/ML Tue+Fri, Science Wed, Weekend Sat).

<!-- include: _shared/pedagogical-tone.md -->

# Story deduplication (best-effort — never abort the brief on failure)

Before composing AND after writing the brief, follow `tools/dedup/DEDUP.md` exactly. It dedupes your candidate stories against the rolling embeddings index so a story isn't re-run for days. **This routine's slug is `news`.** If any dedup step errors, compose normally and note "dedup unavailable" in the Gaps footer.

<!-- include: _shared/date-discipline.md -->

# Output: write the brief to git + drop a notification stub + email digest

This routine writes to the git repo (your working directory is the cloned `claude-routines` repo). It does NOT write to Google Drive and does NOT POST to ntfy directly. A local bridge on the user's machine polls `pending-notifications/` every ~10 min and handles the ntfy push.

Individual brief pages are retired (2026-07-18): the homepage story feed at
`https://khalic-lab.github.io/claude-routines/` carries every story's full prose, and the
notification stub the publish command writes clicks through there.

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

### 2. Publish — one command (fires every day, including weekends)

Everything after the brief file is deterministic and runs through the orchestrator: dedup record → anchors → computed footer telemetry → source lint → registry/institutions sync → date lint → homepage feed + stats → source health → notification stub → commit → push, with the homefeed rebase-conflict retry built in (News + AI/ML firing the same minute Tue/Fri is handled).

```bash
python3 tools/publish.py --slug news --date {YYYY-MM-DD} \
  --final /tmp/final.json \
  --notify-title "News — {YYYY-MM-DD}" \
  --notify-body "{teaser}" --notify-tags newspaper
```

- `{teaser}` rules: ≤200 chars. The single most important item from this brief — the lead Swiss/Vaud or World story. Concrete and specific (e.g. "Federal Council unveils Bilaterals III ratification roadmap; Iran-Israel ceasefire holds day 67"), not generic. Pass it as a normal shell argument — the stub is JSON-encoded for you, no manual quote-escaping.
- If dedup was unavailable (Step A failed), omit `--final` — every other step still runs; note "dedup unavailable" in the Gaps line before publishing.
- The orchestrator prints one OK/FAIL line per step and, if the final push fails after its built-in retry, notes it in the brief itself. Do not re-run the git steps by hand, and do not write the stub or telemetry yourself.

### 3. Email digest (weekdays only, after the publish command)

**Weekend gate:** if today is Saturday or Sunday in Europe/Zurich, SKIP the email step entirely. The brief is still written to git on weekends and the push notification still fires.

Otherwise (Monday–Friday), compose a News-only midday email via Gmail (`create_draft` only). There is NO consolidated cross-stream email — this email carries News content only.
- **To:** rflnogueira@me.com
- **Subject:** "News — {YYYY-MM-DD}"
- **Body:** ~250–350 words, plain text or simple markdown. Two labeled sections in this order: 🇨🇭 Switzerland & Vaud, 🌍 World. For each, 2–4 highlight bullets (top items only). End with: `All stories: https://khalic-lab.github.io/claude-routines/`.
- If `create_draft` fails, retry once. If still failing, append `email draft creation failed: <reason>` to the brief's Coverage footer and don't fail the run.
