Write my weekly science brief and publish it via the git pipeline. Use today's date (Wednesday) in Europe/Zurich.

# Mission

A weekly read on the most significant developments across the natural sciences — physics, math, quantum, astronomy/cosmology, biology/medicine/neuroscience, chemistry, climate/earth. Coverage window: the past 7 days.

This is NON-AI science. **EXCLUDE AI/ML and computer science** — arXiv `cs.*` / `stat.ML` and ML preprints belong to the AI/ML edition, not here. A result is in scope only if its primary contribution is to a natural science, not to machine learning or CS (a physics paper that *uses* an ML method is fine; an ML-methods paper applied to physics is not).

Three desks, deep over broad: pick the week's genuinely-new findings, read the primary papers, and decode them for a numerate non-specialist. Better to go deep on a handful of real results than to skim a feed.

<!-- include: _shared/newsroom-ethos.md -->

# Sourcing rules (non-negotiable)

1. **Tiers.** T1 = primary (preprint, journal research article, official lab/observatory/agency release). T2 = quality secondary. T3 = discovery only (HN/Reddit/Lobsters/X) — used to find stories, NEVER cited. Click through and cite the underlying T1/T2. **A quality outlet's news report or feature *about* a study is T2 secondary, never T1 — even when that outlet also publishes primary research.** Nature news/features (URLs of the form `nature.com/articles/d41586-…`) are journalism about papers, not the papers themselves; the primary source is the underlying paper (`nature.com/articles/s41586-…`) or its preprint. When you cover a study, locate and cite that **primary paper** — read its abstract — and use the news write-up only as a secondary pointer or for triangulation. A bullet whose sole citation is a `d41586` Nature-news piece (or any equivalent secondary report) is mis-sourced: find the paper, or if you genuinely cannot, frame it as 'as reported by …' and tag `[single-source]` — never present secondary journalism as the primary.
2. **Citation format.** Every item ends with a markdown link to one specific URL (DOI, arXiv abstract, or article landing). Include publication name and date. No "according to recent reports" without a link.
3. **Triangulation.** Significant claims need two independent sources where feasible. Single-sourced → mark `[single-source]`. Disagreements → surface both versions explicitly.
4. **Diversification.** Within each desk, span subfields and institutions; don't let one journal or one lab dominate.
5. **Tags.** Preprints → `[preprint]`. Single source → `[single-source]`. Contested → `[disputed]`.
6. **No fabrication.** Never invent a URL, author, date, or quote. **The no-fabrication rule extends to date claims**: a paper from last month is NOT "this week's." If you cannot verify a paper was submitted or published within the past 7 days, do not include it under a section that claims this week's content.
7. **Volume cap.** 4–8 items per desk. Quality is the cap — better to ship 3 strong findings in a desk than pad to 8.
8. **Fetch transparency.** A confirmed fetch gets no marker; a citation resting only on a search-engine snippet gets `[via snippet]`.

<!-- include: _shared/reader-profile-source-weights.md -->

<!-- include: _shared/feed-first-source-order.md -->

**arXiv mechanics:** use the non-CS RSS per category (`https://export.arxiv.org/rss/astro-ph`, also `math.*`, `physics.*`, `cond-mat`, `hep-ph`, `hep-th`, `gr-qc`, `quant-ph`, `q-bio.*`) and the date-filtered Atom API (`https://export.arxiv.org/api/query?search_query=cat:astro-ph.CO&start=0&max_results=30&sortBy=submittedDate&sortOrder=descending` — **swap the `cat:` filter** for any non-CS category; filter `<published>` to the past 7 days). For Nature journals, dig to the primary research (`s41586-…`), not the `d41586-…` news.

**Endpoints worth knowing (not in the plan's probe list):**
- bioRxiv / medRxiv JSON details API: `https://api.biorxiv.org/details/biorxiv/{YYYY-MM-DD}/{YYYY-MM-DD}/0` (swap `medrxiv`) — title, abstract, DOI and date per paper for the window; an ideal primary source for the Biology desk.
- Science.org — use its RSS feeds (e.g. `https://www.science.org/rss/news_current.xml`, plus journal feeds); the article HTML is unreachable, so cite the DOI / article landing URL.
- APS journals (`journals.aps.org` — PRL / PRX / PRX Quantum): the recent-articles RSS. Cite the article DOI / landing URL.

**Dormant-source activation — do this BEFORE waiving discovery.** The registry carries a stack of
science domains stuck at `candidate` status in the plan's `candidates_to_try` — Swiss and European
research institutions (ETH Zürich, EPFL, PSI, Empa, WSL, the cantonal universities), national labs,
agency newsrooms, society journals — never cited, or cited once and quiet since. Pick at least **two**
of them each week and actually attempt their newsroom/feed for the window. A domain in
`candidates_to_try` is ALREADY in the registry, so it can be neither tagged `[new source]` nor counted
toward `met` — probing it strengthens the edition and makes the waiver honest, it does not satisfy the
quota. The one path from a dormant-institution probe to a real discovery is landing on a host that is
not in the registry: an institution's newsroom subdomain is its own domain (`ai.ethz.ch` is registered
separately from `ethz.ch`), so tag and count that. If both probes come back empty or unreachable, name
the two you probed in the waiver reason.

**Nature-abstract fallback (Patch-4):** when a Nature primary research item (`s41586-…`) has no fetchable abstract from the sandbox, locate the matching arXiv cross-list preprint (search the title via the arXiv API / Semantic Scholar) and summarise *that*, tagged `[preprint]` — do NOT emit a title-only stub.

# Affiliations (the provenance element)

<!-- include: _shared/affiliations.md -->

# Research methodology

1. **Source plan first** — run the preflight (see Source plan above), then sweep its fetch list per desk. Use the arXiv API with date filters; the Nature / Quanta / Science RSS feeds are rolling — filter to the past 7 days client-side.
2. **Broad query** (1–2 keywords). Scan results.
3. **Refine and re-query** based on what surfaced.
4. **Fetch full pages / abstracts** for findings that matter (use the arXiv API for abstracts — the abstract HTML page 403s); on failure, snippet + tag.
5. **Cross-reference** significant claims; use Semantic Scholar to triangulate which results are getting attention this week.
6. **Stop when triangulated** or leads exhausted.

# Sections (in order — OMIT any desk with no genuinely-new content this week)

## 🔭 Physics, chemistry, math & quantum

**Sources come from the preflight plan** — the registry carries this desk's venue set (physics
journals, preprint servers, agency newsrooms, quality explainers); spread citations across it
instead of defaulting to the same two or three hosts every week. Where to look: nature.com primary
research is `s41586-…` (`nphys.rss` / `nchem.rss`) — the papers, NOT `d41586` news; **non-CS arXiv
via the Atom API** (`math.*`, `physics.*` incl. `physics.chem-ph` / `physics.ao-ph` /
`physics.geo-ph`, `cond-mat`, `hep-ph`, `hep-th`, `gr-qc`, `quant-ph` — swap the `cat:` filter);
science.org research RSS.
Coverage: particle physics, condensed matter, quantum information (quant-ph, PRX Quantum), gravity/GR, chemistry (physical / materials chemistry), earth & climate-system science, plus mathematics (major proofs, conjecture progress, notable surveys). Exclude anything whose home is `cs.*` / `stat.ML`.

## 🧬 Biology, medicine & neuroscience

**Sources come from the preflight plan** (journals, preprint servers, biotech/clinical outlets —
all registered). Where to look: the bioRxiv / medRxiv JSON details API, Nature Methods RSS
(`nm.rss`), `q-bio.*` arXiv via the Atom API, Quanta RSS (biology features).
Coverage: drug approvals and clinical-trial readouts, genomics, structural and molecular biology, neuroscience, biotech. Flag preliminary / small-sample / unreplicated results as such — don't upgrade them.

## 🌌 Astronomy & cosmology

**Sources come from the preflight plan** (agency newsrooms, journals, quality astro outlets — all
registered). Where to look: Nature Astronomy RSS (`natastron.rss`), `astro-ph.*`
(CO/GA/EP/HE/SR/IM) via the arXiv Atom API, Quanta RSS.
Coverage: JWST and other space telescopes, ESO/ALMA, exoplanets, cosmology, gravitational waves, solar-system science.

## 🧠 Why it matters (optional — only if warranted)

1–2 synthesis threads across the week's science: a connection between findings, a shifting consensus, a method that's spreading across fields. This is the one place to be opinionated. Omit entirely if no genuine cross-cutting thread emerged — do not manufacture one.

# Swiss/European relevance pass (after drafting, before publishing)

Reread the finished items and ask of each: does this have a real Swiss or European angle — a Swiss/EU
institution in the author list or funding it, a policy, regulatory or funding consequence that lands
here, a practical consequence for the reader? Where the angle is real, write it into that item (a
clause in the summary or the *Why it matters:* line is enough; do not add a section for it). Where it
is not, leave the item alone — a manufactured local hook is worse than none.

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
<!-- the telemetry lines are computed at publish; write ONLY:
- Items: N (filtered from M reviewed) — Physics/math/quantum: N, Biology/medicine/neuro: N, Astronomy/cosmology: N
- Languages: {languages of your cited sources, e.g. EN, FR, DE}
-->
- Gaps: things you tried to find but couldn't.
- Discovery: {met (<new domain(s) anchored>) | waived — <concrete reason>}
```

# Constraints

- **EXCLUDE AI/ML and CS.** No `cs.*` / `stat.ML` preprints, no ML-methods papers, no AI-lab releases — those are the AI/ML edition's. A natural-science result that merely uses ML is in scope; an ML result dressed in a science application is not.
- Numbers and identifiers matter: include arXiv IDs and DOIs, and the submission/publication date next to each item.
- Length: 1500–3000 words (weekly window, three focused desks). Don't pad — if a desk has 3 strong items, ship the 3.
- Write in English. French/German source titles can stay in original language inside link text.
- Discovery aggregators (HN, Reddit, Lobsters, X) → never cited as source.

<!-- include: _shared/pedagogical-tone.md -->

# Story deduplication (best-effort — never abort the brief on failure)

Before composing AND after writing the brief, follow `tools/dedup/DEDUP.md` exactly. It dedupes your candidate stories against the rolling embeddings index so a story isn't re-run for days. **This routine's slug is `science`.** If any dedup step errors, compose normally and note "dedup unavailable" in the Gaps footer.

<!-- include: _shared/date-discipline.md -->

# Output: write the brief to git + drop a notification stub

<!-- include: _shared/publish-step.md -->

- `{teaser}` rules: ≤200 chars. The single most striking finding in this brief — typically the headline physics/quantum result, a major astronomy discovery, or a notable clinical/biology readout. Concrete and specific (e.g. "JWST resolves the missing-baryon problem; PRX Quantum demo of below-threshold error correction on 105 qubits"), not generic. Pass it as a plain shell argument; no quote-escaping.
<!-- include: _shared/publish-outcomes.md -->
