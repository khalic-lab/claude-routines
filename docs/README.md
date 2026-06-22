# docs/ — internal design docs

Not published (the whole `docs/` tree is in `_config.yml` `exclude:`). These reference the
environment ID, trigger IDs and Worker URLs, so they stay off the public Pages site.

## Live design docs / decisions
- [`SPIKE-model-tiering.md`](SPIKE-model-tiering.md) — per-routine model tiers; why writers are
  on Opus, Watch on Haiku. **Decisions taken 2026-05-30.**
- [`SPIKE-writer-token-levers.md`](SPIKE-writer-token-levers.md) — the real token spend is the
  writers; output caps / skip-on-empty / instrumentation. **Proposed; not yet implemented.**

## `archive/` — dated point-in-time analysis (historical snapshots, not maintained)
- `AUDIT-2026-05-31-briefs.md` — 7-day brief audit (the 37% cross-day repeat finding).
- `DEDUP-DIAGNOSIS-2026-05-31.md` — dedup calibration diagnosis (T_HIGH/T_LOW; cosine can't
  separate rerun from update). Referenced by `tools/dedup/dedup.py` and `ARCHITECTURE.md` §6.
- `PRIOR-ART-2026-05-31-credibility-and-editor.md` — credibility-lifecycle + editor patterns.
- `PRIOR-ART-2026-06-08-reader-feedback-loops.md` — reader-feedback product patterns.
- `PRIOR-ART-2026-06-08-temporal-grounding.md` — anchoring LLMs to dates / temporal grounding.
- `REVIEW-2026-06-08-feedback-and-dates.md` — feedback loop + date-discipline design/rationale.

> Operational source of truth lives at the repo root: `ARCHITECTURE.md` (current state) and
> `CLAUDE.md` (working-in-this-repo). Architecture diagrams are in `diagrams/`.
