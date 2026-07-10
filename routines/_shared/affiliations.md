**Affiliations — the paper's provenance element (machine-parsed):** every paper byline carries
the lead authors' institutional affiliations. They are the paper's editorial source —
arxiv.org is just the platform — and they flow to the homepage cards' institution-first source
label and the institutions ledger (`sources/institutions.yml`), so both the retrieval order and
the format below are load-bearing.

- **arXiv preprints — read the paper's own HTML author block.** Fetch
  `https://arxiv.org/html/<id>v1` THROUGH the fetch proxy and take the affiliations from the
  author block at the top of page 1 (~97% of new submissions render HTML; verified in
  production 2026-07-10, 10/10 papers). Do NOT use index APIs for preprints: Semantic Scholar
  has not indexed hours-old papers, and OpenAlex's arXiv records carry EMPTY institutions even
  once indexed (~6-day lag; measured 2026-07-10). If the HTML 404s (~3% of papers), write
  `(affiliation not listed)`.
- **bioRxiv / medRxiv preprints:** the details-API response you already fetch includes
  `author_corresponding_institution` — use it (no extra fetch).
- **Published papers (journal DOI) — OpenAlex:**
  `https://api.openalex.org/works?filter=doi:<doi>&select=authorships` returns resolved
  institution names (measured: complete for fresh Nature papers). On a miss, take them from
  the publisher/press page you are already reading; else the sentinel.
- **Budget: at most ONE extra fetch per selected paper.** Never web-search individual authors,
  never guess from an email domain or a lab's reputation — `(affiliation not listed)` is
  always the correct fallback; never fabricate.

**Byline format law** (parsed by `tools/dedup/dedup.py parse_affiliations` — deviations break
the join): after the author list, in parentheses — `AUTHORS (Inst1; Inst2; Inst3)`. `;`
separates institutions; `,` only qualifies within one name (`HKUST, Guangzhou`); at most 3
institutions, then `+N more`; canonical short names (`MIT`, `ETH Zürich`, `Google DeepMind` —
not full legal names); collective authors keep their name — `Gemma Team (Google DeepMind)`.
Example: `F. Last, A. Other et al. (MIT; CERN)`.

**Step C:** copy the same institutions into each paper story's `"affiliations": ["MIT", "CERN"]`
field in final.json (omit the key when not listed) — the homepage card and the institutions
ledger read it from there (see DEDUP.md Step C).

**Anti-halo guard:** affiliations are recorded FOR THE READER, after selection — never as a
selection signal. Do not prefer a paper because a famous lab wrote it, and never demote one
because its affiliation is missing, independent, or unknown (LLM judges measurably over-reject
low-prestige affiliations — arXiv:2509.15122). Select on content.
