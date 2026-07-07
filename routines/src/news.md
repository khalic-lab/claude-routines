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

**CRITICAL — try Bash{curl} BEFORE WebFetch.** WebFetch in this sandbox has been observed returning HTTP 403 on public, machine-readable feeds. When attempting any feed from the preflight plan (SRF RSS, Le Temps RSS, Al Jazeera RSS, etc.), FIRST try via Bash with `curl -fsSL <URL>`, parse the response, and only fall back to WebFetch if curl also fails. A successful curl fetch counts as a direct fetch.

A successful feed fetch (curl OR WebFetch returning 200 with feed XML/JSON) counts as a "direct fetch" — no `[via snippet]` tag needed even if the article HTML page itself returned 403.

**Coverage footer accounting (strict):**
- `Direct fetches: N` = count of citations from publisher infrastructure (feed XML/JSON via curl or WebFetch, working HTML, official API, fetch proxy).
- `Via-snippet citations: M` = count where you only have a search-engine result excerpt.
- Report both. `N + M` should equal total citation count.
- In the `Feeds hit` line, distinguish `{ok via curl}` / `{ok via WebFetch}` / `{ok via proxy}` / `{fail — HTTP NNN}`.

# Research methodology

1. **Source plan first** — run the preflight (see Source plan above), then sweep its fetch list via Bash{curl}, WebFetch fallback.
2. **Broad query** (1–2 keywords). Scan results.
3. **Refine and re-query**. At least one refinement per non-trivial topic.
4. **Fetch full pages** when a story matters. If the fetch fails, fall back to snippets and tag with `[via snippet]`.
5. **Cross-reference** when a claim is significant.
6. **Stop when triangulated** or leads exhausted.

# Sections (in order)

## 🇨🇭 Switzerland & Vaud

Federal politics, cantonal Vaud, Swiss-relevant EU moves, and notable economy/society stories. Coverage window: the last ~24 hours (yesterday midday through this morning).

T1: admin.ch, parlament.ch, vd.ch, Keystone-SDA via rts.ch. **Feed (try via curl first):** SRF.ch RSS (DE-language).
T2: rts.ch, **letemps.ch (RSS via curl — paywalled items still cite-able by URL)**, nzz.ch, tagesanzeiger.ch, 24heures.ch, tdg.ch, swissinfo.ch, heidi.news.

Avoid 20min/Blick as primary. **Non-English-source quota:** at least one DE or FR citation should come from SRF or Le Temps feeds when relevant.

## 🌍 World politics & geopolitics

The notable developments of the last ~24 hours (all time zones — not just US/Europe).

T1: reuters.com, apnews.com, afp.com, gov/court filings, White House press releases.
T2: bbc.com, ft.com, nytimes.com, lemonde.fr, spiegel.de/international, politico.eu, **aljazeera.com (RSS via curl)** (MENA), scmp.com / caixinglobal.com (China), thehindu.com (India).

Span at least 3 different countries' coverage. Focus on geopolitics, conflicts, elections, and diplomacy. Markets-specific political stories (legislation, central-bank politics) can be folded in here when they're significant — there is no longer a dedicated Markets routine.

# Format

```
# News — {YYYY-MM-DD}

_Generated {ISO timestamp} Europe/Zurich. Coverage: last ~24h._

## 🇨🇭 Switzerland & Vaud
- ...

## 🌍 World politics & geopolitics
- ...

---

## Coverage footer
- Sources used: T1 = N items, T2 = N items, T3 = 0 (per policy)
- Direct fetches: N | via-snippet citations: N
- Word count: N (body, excl. footer) | research tool calls (curl/WebSearch/WebFetch): N
- Feeds hit (with reachability and method): {each feed/API attempted from the preflight plan} {ok via curl|ok via WebFetch|ok via proxy|fail — HTTP NNN}
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
# refresh the homepage feed HERE, unconditionally — not only via DEDUP.md Step D — so a skipped
# step can't freeze the front page while the commit still stages a stale _data/
python3 tools/build_stories_feed.py || echo "feed build failed (non-fatal)"
python3 tools/sources/health.py || echo "source health failed (non-fatal)"
git add _posts/ pending-notifications/ index/ _data/ sources/
git -c user.email=routine@khalic-lab -c user.name="News Routine" commit -m "News — {YYYY-MM-DD}"
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

### 4. Email digest (weekdays only, after git push step)

**Weekend gate:** if today is Saturday or Sunday in Europe/Zurich, SKIP the email step entirely. The brief is still written to git on weekends and the push notification still fires.

Otherwise (Monday–Friday), compose a News-only midday email via Gmail (`create_draft` only). There is NO consolidated cross-stream email — this email carries News content only.
- **To:** rflnogueira@me.com
- **Subject:** "News — {YYYY-MM-DD}"
- **Body:** ~250–350 words, plain text or simple markdown. Two labeled sections in this order: 🇨🇭 Switzerland & Vaud, 🌍 World. For each, 2–4 highlight bullets (top items only). End with: `Full brief: {POST_URL}`.
- If `create_draft` fails, retry once. If still failing, append `email draft creation failed: <reason>` to the brief's Coverage footer and don't fail the run.
