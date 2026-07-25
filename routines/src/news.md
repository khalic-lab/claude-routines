Write my midday news brief and publish it via the git pipeline. Use today's date in Europe/Zurich.

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
8. **Fetch transparency.** A confirmed fetch gets no marker; a citation resting only on a search-engine snippet gets `[via snippet]`.

<!-- include: _shared/reader-profile-source-weights.md -->

<!-- include: _shared/feed-first-source-order.md -->

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
<!-- the telemetry lines are computed at publish; write ONLY:
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

# Output: write the brief to git + drop a notification stub

<!-- include: _shared/publish-step.md -->

- `{teaser}` rules: ≤200 chars. The single most important item from this brief — the lead Swiss/Vaud or World story. Concrete and specific (e.g. "Federal Council unveils Bilaterals III ratification roadmap; Iran-Israel ceasefire holds day 67"), not generic. Pass it as a plain shell argument; no quote-escaping.
<!-- include: _shared/publish-outcomes.md -->
