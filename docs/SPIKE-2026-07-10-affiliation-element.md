# SPIKE — Affiliation element for paper coverage

**Date:** 2026-07-10 · **Status:** SHIPPED 2026-07-10 (§6 decided: institution-first card
label; ledger now; names only — no class marker) · **Ask (Rafael):** "we need an affiliation
element added to the papers reading. Papers are great, but they're even better when they come
from reliable sources. It's harder than it looks."

---

## 1. Why it's harder than it looks

Seven distinct difficulties, each with evidence below:

1. **The freshness gap.** Every scholarly index lags arXiv by days-to-weeks; our AI/ML writer
   covers papers that are hours old. The only universal affiliation source for a fresh preprint
   is the paper itself.
2. **The arXiv metadata trap.** arXiv's Atom `<arxiv:affiliation>` field is author-optional and
   in practice never populated; the `/abs` page shows author names only. The metadata road is a
   dead end even though it looks like the obvious place.
3. **Extraction ambiguity.** Multi-affiliation authors, equal-contribution footnotes, campus
   qualifiers ("HKUST, Guangzhou"), 305-author collaborations, collective authors ("Gemma Team").
4. **Normalization.** "MIT" vs "Massachusetts Institute of Technology" vs "M.I.T."; without a
   canonical form, any downstream accrual (counts, lifecycle) fragments.
5. **Verification and gaming.** Affiliations are self-reported and unverified; affiliation-buying
   scandals (authors adding paid secondary affiliations to boost institutional rankings) are
   documented. An affiliation string is a claim, not a credential.
6. **The halo hazard.** A 2025 audit ([arXiv:2509.15122](https://arxiv.org/html/2509.15122v1))
   found LLM reviewers given identical papers reject the low-prestige-affiliation version
   significantly more often. If affiliation enters our writers' *selection* reasoning as a
   quality prior, we import that bias into a pipeline whose stated goal is primary-source
   discovery — the opposite of brand-following.
7. **Budget.** Affiliation lookups were mandatory until 2026-07-10 and burned fetch budget for
   near-zero yield (see §2); any new mechanism must be bounded per paper.

## 2. Evidence from our own runs (the strongest prior art we have)

| Edition | Method used | Yield |
|---|---|---|
| 2026-07-07 ai-ml | Semantic Scholar (mandatory chain) | **3/10** — "Semantic Scholar had not indexed these very-recent submissions and arXiv metadata carried no `<arxiv:affiliation>`" |
| 2026-07-04 weekend | S2 empty → writer web-searched senior authors | Partial, expensive, now banned ("that budget belongs to prose and sourcing") |
| 2026-07-01 science | S2 rate-limited → press releases | Partial; one institution unconfirmable |
| 2026-07-10 ai-ml | **arXiv HTML author blocks via fetch-proxy** (writer improvised — not in the prompt chain) | **10/10** |

Measured 2026-07-10 (this spike, live API probes):

- **OpenAlex lag:** Gemma 4 report (arXiv:2607.02770, submitted Jul 2) got its OpenAlex record
  on **Jul 8** (~6-day lag). HiLS (Jul 3) still unfindable by title after 7 days.
- **OpenAlex preprint affiliations are empty even when indexed:** the Gemma record has 100
  authorships, **0 institutions, 0 raw affiliation strings**. arXiv doesn't deposit affiliation
  strings, so OpenAlex has nothing to parse. OpenAlex is not merely laggy for preprints — it is
  *structurally empty* for them.
- **OpenAlex published-paper affiliations are excellent:** Nature s41586-026-10815-x (science
  stream, Jul-1 edition) returns fully-resolved institutions (MIT; University of Basel) via the
  DOI filter. The science stream's papers are published works — a different world.
- **arXiv HTML richness:** the LASR Labs paper's HTML author block carries *more* than our
  byline captured (University College London appears in the HTML; our byline had only
  "LASR Labs; Google DeepMind").

## 3. External prior art

### 3a. Data sources for affiliations

- **arXiv HTML (LaTeXML).** Since Dec 2023 every new TeX submission is converted;
  [~97% of submissions produce HTML](https://arxiv.org/html/2605.16562v1) (availability ceiling;
  ~25% have conversion glitches, ~3% fail outright — the author block, being page-1 plain text,
  survives essentially always). First-party, zero lag, fetchable through our fetch-proxy
  (verified `{ok via proxy}` in today's footer).
- **OpenAlex.** [Parses affiliation strings into ROR-backed institution entities]
  (https://docs.openalex.org/api-entities/institutions) — the right tool **for DOI'd published
  papers only** (see measurements above). Free, no auth, polite-pool via `mailto` UA.
- **Semantic Scholar.** Affiliations field is effectively dead for fresh papers (empty for every
  paper in our last three paper editions). Keep S2 for search/citation triangulation; drop it
  from the affiliation role.
- **Crossref.** Publisher-deposited affiliation strings, coverage patchy by publisher; redundant
  given OpenAlex resolves the same DOIs with normalization on top. Not needed. (Crossref stays
  relevant as the Retraction Watch host — see PRIOR-ART-2026-05-31 §A5.)
- **GROBID.** The standard ML extractor for header metadata (authors/affiliations) from
  scholarly PDFs — used inside the big indexes themselves. Its existence validates the design
  stance: *the artifact itself is the canonical affiliation source; everything else is a lagging
  cache of it.* We get GROBID's job done for free because our writer already reads the paper —
  an LLM reading the HTML author block **is** the extractor.
- **ROR (Research Organization Registry).** CC0 registry of ~110k research orgs with an
  affiliation-matching API — the normalization standard OpenAlex builds on. Overkill to call
  live for a single-reader pipeline; v1 adopts its *convention* (canonical short display names)
  via a small alias map in-repo, with ROR ids adoptable later if names fragment.

### 3b. Display prior art — who shows affiliations?

- **arXiv itself** (abs pages, listings): author names only. No affiliations anywhere.
- **[Hugging Face Daily Papers](https://huggingface.co/docs/hub/en/paper-pages):** author names,
  no affiliations; organizational identity only emerges when authors claim papers with accounts.
- **alphaXiv / Emergent Mind:** discussion/summary overlays; affiliation is not a first-class
  element.
- **Human newsletters (The Batch, Import AI):** institution routinely carried *in prose* —
  "researchers at DeepMind…" — because human editors know provenance is part of the story.
  Closest prior art to our editorial goal; none of them make it structured/filterable.

**Conclusion:** a structured affiliation element is a genuine differentiator — the aggregators
don't do it, and the newsletters that do it do it only as prose. It also matches the pipeline's
editorial direction (primary-source discovery + credibility lifecycle, not aggregator mimicry).

### 3c. Affiliation as credibility signal — what the literature warns

- Human peer-review evidence for prestige bias is **mixed** ([eLife 2021 preregistered
  experiment: weak evidence](https://elifesciences.org/articles/64561); [PLOS One systems-confs
  case study](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0264131)), but
  the [LLM audit (arXiv:2509.15122)](https://arxiv.org/html/2509.15122v1) found **strong,
  consistent institutional-prestige bias in LLM reviewers** — directly on point for us.
- Institution *rankings* (CSRankings, Nature Index, Leiden) were considered and **rejected** as
  a scoring prior: venue-weighted, slow-moving, and hard-coding them would bake in exactly the
  halo the audit warns about. Genesis Cortex AI (today's single-author paper) would be scored
  "nobody" by every ranking — and its selection was correct on content.
- Therefore the design principle: **affiliation is provenance to display and record, never a
  prior to select on.** "Reliable sources" gets built the way the domain registry built it —
  accrual and lifecycle from our own citation history — not imported brand rank.

## 4. Design

### D1. Writer prompts — new affiliation chain (papers streams: ai-ml, science, weekend)

Replace the current chain (arXiv Atom → S2 → OpenAlex) with a **fork on paper type**:

- **arXiv preprints:** fetch `https://arxiv.org/html/<id>v1` **through the fetch-proxy** and
  read the author block (page 1; plain text near the top — cheap even when the paper is long).
  Capture the distinct institutions of the listed authors (first ~3 authors + any flagged
  senior/last author). If HTML 404s (~3% of papers) → `(affiliation not listed)`.
- **Published papers (has a DOI):** OpenAlex `api.openalex.org/works?filter=doi:<doi>` —
  institutions arrive resolved. Miss → publisher/press page already being read → sentinel.
- **Drop Semantic Scholar from the affiliation role** (stays for search/citations).
- **Byline format law** (already the de-facto convention, now normative):
  `AUTHORS (Inst1; Inst2; Inst3)` — `;` separates institutions; `,` only *within* one name
  ("HKUST, Guangzhou"); **max 3** institutions then `+N more`; canonical short names
  (MIT, ETH Zürich, Google DeepMind); sentinel `(affiliation not listed)` unchanged; never
  fabricate, never author-google.
- **Anti-halo guard (new, explicit):** affiliations are recorded for the reader *after*
  selection; a missing or unknown affiliation must never demote a paper, and a prestigious one
  must never promote it — selection stays on content. (Grounds: LLM prestige-bias audit.)
- Factor the chain into one shared partial (`routines/_shared/affiliations.md`) so the three
  streams can't drift; `assemble.py check` guards it.

### D2. Store — structured field

`dedup.py record` parses the byline's affiliation parenthetical (the **last** parenthetical
after the first ` · `, skipping `incl.` fragments and pure counts like "(305 authors)") into
`affiliations: ["LASR Labs", "Google DeepMind"]` on the story record; sentinel → field absent.
Ledger materialize passes it through. **Backfill pass** over existing posts — parse-verified
2026-07-10 on all June–July posts: 82 bylines parse cleanly, 19 carry the sentinel, the
remainder are pre-convention June editions with no affiliation at all (backfill is partial
there, by design).

### D3. Feed + homepage element

`build_stories_feed.py` overlays `affiliations` by URL (same mechanism as topics/importance).
Card source line (`fcard__src`) becomes **institution-first, platform-second**:
`ETH Zürich · arXiv` / `MIT · nature.com`; two institutions shown, more → `ETH Zürich +2 · arXiv`;
no affiliations → today's plain domain. Posts themselves unchanged (the byline already carries
the data). Verified in the headless harness (GEOM overlap invariant + screenshot, both themes).

### D4. Institutions ledger — the "reliable sources" substrate

New `sources/institutions.yml`, mirroring `registry.yml`'s shape but keyed by canonical
institution name: `class` (frontier-lab / university / industry / government / independent),
`streams`, `first_seen`, `last_cited`, citation count, `lifecycle` (bootstrap → probation →
established, same vocabulary as domains). Bootstrapped from the D2 backfill; maintained by the
same writer step that runs `registry.py sync` (Step C.25b). **No displayed rank in v1** —
display is descriptive; the accrued history is what future credibility decisions (and the
evaluator) get to reason over. A small `aliases:` map handles normalization drift.

### D5. Evaluator hook

One added spot-check in the weekly review: affiliation coverage rate per papers stream (target:
sentinel rate < ~20% now that the chain works), plus a halo audit — verify "(affiliation not
listed)" papers were not systematically down-ranked in importance.

## 5. Verification & rollout

- Spec tests: byline parser edge cases (double parenthetical, `(305 authors)`, sentinel, comma
  -in-name, `+N more`), record passthrough, backfill idempotency, feed overlay. Suite green.
- `python3 routines/assemble.py check` (drift guard) after the partial refactor.
- Harness run for the card element; screenshot both themes.
- Rollout is **repo-only**: prompts are shimmed (commit+push = deploy), no RemoteTrigger edits,
  no Worker changes. First live fire: ai-ml Tue 2026-07-14 (news/science/weekend follow their
  crons); backfill + card element are visible on the homepage immediately.

## 6. Open questions (for Rafael)

1. **Card element shape** — institution *replaces* the domain as the primary source label
   (`ETH Zürich · arXiv`), or is *added* as a separate small chip next to the domain?
2. **Institutions ledger** — build `sources/institutions.yml` accrual now (D4), or ship
   display-only (D1–D3) first and add the ledger once a few weeks of structured data exist?
3. **Class labels** — should the card also show the institution *class* (e.g. a muted
   `independent` marker on unaffiliated/unknown papers), or names only in v1?
