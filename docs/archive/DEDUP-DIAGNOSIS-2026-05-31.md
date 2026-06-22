# Dedup-check failure — diagnosis (2026-05-31)

Audit (`AUDIT-2026-05-31-briefs.md`) found a **37% cross-day repeat rate** despite dedup infra
being built and running. This file captures the pre-fix diagnosis; the workflow appends results.

## What's built and working
- `tools/dedup/dedup.py` (check / record / backfill / selftest), `tools/embed-proxy/` Worker,
  `index/stories/*.jsonl`. **Records are written daily with embeddings present** → the embed
  path works → `check` (same embed path) can run.
- Writer prompts delegate dedup entirely to `tools/dedup/DEDUP.md` ("follow it exactly",
  best-effort). **So policy is fixable in the local `DEDUP.md` — no remote-prompt edit needed.**

## Root-cause hypotheses (evidence)
1. **`T_HIGH=0.92` sits ABOVE the rerun band.** The code's own calibration comment says
   paraphrased repeats score **0.76–0.87**. Offline reproduction from stored embeddings (cross-day
   best-match): ai-ml 116 records → **REPEAT=1, ONGOING=22, NEW=69**. Known reruns land in ONGOING,
   never REPEAT: "Anthropic releases Opus 4.8" (5-29) vs "...launches Opus 4.8" (5-28) = **0.814**;
   EU AI Act 5-27 vs 5-22 = 0.816; DeepSeek V4 5-23 vs 5-20 = 0.745. **Genuine reruns can essentially
   never auto-drop.**
2. **ONGOING is judgment-delegated and leaky.** `DEDUP.md` Step B says include ONGOING "ONLY if
   genuine new development." Opus writers reliably find an angle → reruns get published as "updates."
3. **Thread-linking never happens.** Every index record has `thread_id == id` and
   `first_seen_date == date` → the Step-C carry-through is not being applied, so continuity /
   `[ongoing since …]` framing never works. Depends on writer adherence; should be made automatic.

## Fix space (all local)
- Recalibrate `T_HIGH`/`T_LOW` against a hand-labeled gold set (caveat: cosine may not separate
  true-repeat from true-development — calibrate honestly, don't force it).
- Tighten `DEDUP.md` ONGOING policy (default DROP; require a named, dated new fact).
- Make `record` auto-assign `thread_id`/`first_seen` from its own index match (prompt-independent).
- Add an offline regression test (stored-vector fixture) so threshold drift is caught.

## Workflow results (diagnose → reproduce → calibrate → fix → retest)

**Dedup IS running in production** (not a silent no-op): brief footers cite live cosine scores
+ verdict counts, and index records carry backward-pointing `thread_id`s that resolve to real
prior ids. So the bug is behavioral, not "dedup never ran."

**Calibration killed the obvious fix.** 485 hand-labelled cross-day pairs (111 REPEAT / 141
ONGOING / 233 DISTINCT). **Cosine does NOT separate TRUE-REPEAT from TRUE-ONGOING** — REPEAT spans
0.635–0.952, ONGOING spans 0.605–0.944. The two highest-similarity ONGOING pairs (daily EUR/CHF
snapshots, 0.944) sit *above* almost all true repeats. So **no `T_high` can catch reruns without
silently dropping developing stories.** 84% of true repeats fall in the inseparable ONGOING band.

**What that means for the 37%:** the threshold is not the lever. Lowering `T_high` is a trap (it
converts the overlap into silent drops of developing stories). The repeat-suppression must come
from the **ONGOING policy** (writer judgment) or a **deterministic signal** (exact arxiv-ID /
canonical-URL match), not geometry.

### Fix applied (LOCAL, uncommitted)
1. `dedup.py` `T_HIGH 0.92→0.945` — sits just above the ONGOING ceiling (0.9443): zero
   ONGOING→REPEAT and zero DISTINCT→REPEAT. A *correctness* win (old 0.92 silently auto-dropped 2
   genuine developing FX stories) but **NOT the repeat fix**. Note: 0.945 protects daily FX
   snapshots from auto-drop — which is aggregator noise the user dislikes — so the direction is a
   user call (see open items).
2. `DEDUP.md` Step B tightened — **ONGOING now defaults to DROP**; included only with a named,
   dated, concrete new fact. This is the real (partial) repeat lever; it is writer-judgment and
   **not offline-testable**.
3. `dedup.py` `record` auto-links threads — but gated at **`AUTOLINK_MIN=0.93`**, above the
   observed 0.914 DISTINCT ceiling. (The workflow's first cut gated at the 0.72 verdict band,
   which would have falsely threaded ~23% of distinct stories — caught in review, fixed, and
   pinned by a regression test using the worst-case 0.914 markets pair.)
4. `test_dedup_calibration.py` — offline regression test (stored vectors), value-pins the
   thresholds + the autolink gate. Negative-tested: it fails if the gate regresses to 0.72.

`selftest` + `test_dedup_calibration.py` both pass. Before/after (offline, cross-day): auto-drop
REPEAT 6→2, NEW unchanged (681), ONGOING 229→233 — i.e. the threshold change does not reduce
repeats; it just stops 2 wrong silent drops.

### Verdict: PARTIAL
The diagnosis is thorough and the code is sound, but **the 37% repeat problem is substantially
still open** and is fundamentally **editorial** — cosine cannot judge "is this worth re-surfacing?"
This loops straight back to the editorial-direction redirect.

### Follow-up build (2026-05-31, applied) — the deterministic lever

Per the advisor's recommendation and the user's directive, two cosine-independent layers were added
to `check` (`decide_verdict`), in precedence order:

1. **Exact-source hard-REPEAT** — same canonical URL (permalink; bare hosts excluded) or same arXiv
   id as a recent story → REPEAT, regardless of how the headline is reworded. Zero writer judgment.
2. **Snapshot-genre collapse** — recurring FX/index/session snapshots (`is_snapshot_genre`) matching a
   prior snapshot ≥ `SNAPSHOT_T_HIGH=0.85` → REPEAT, even with a "new number" (the daily glance lives
   only in the dedicated pre-open section). This is the "treat FX snapshots specially" decision; it
   also removes the reason `T_high` had to be inflated to protect FX pairs.

**Offline replay over the index (78 vs 6):** cross-day auto-drops rose from 6 (cosine-only) to **78**:
`exact-url=55`, `snapshot-collapse=17`, `exact-arxiv=5`, cosine-REPEAT=1. Snapshot flagging is 50%
(markets) / 19% (overview) but **<1% on ai-ml/cyber-papers** and snapshot-collapse never fires there.
`DEDUP.md` Step A now asks writers to include `url`; Step B documents the new `match_reason`s. Tests
in `test_dedup_calibration.py` cover arXiv extraction, URL canonicalisation, the bare-host guard, the
exact-match path, and snapshot collapse. `selftest` + regression both pass.

**Net status upgrade: the 37% repeat problem is now substantially addressed by deterministic means**
(not just policy hope). The residual ONGOING band (163 pairs) still relies on the tightened writer
policy. Remaining ceiling is editorial: cosine can't judge "worth re-surfacing?", but exact-source +
snapshot genre now catch the clean reruns without judgment.

### Open items for the user
- **Deterministic hard-REPEAT rule** (recommended next lever): exact arxiv-ID / canonical-URL
  match → drop, zero writer judgment, fully testable. Catches the clean subset (same PAN-OS CVE
  across days; the Leuk petition restating an identical 14,550-signature figure).
- **Threshold direction**: 0.945 protects FX/snapshot noise; user may prefer to lean entirely on
  the URL rule + policy and not chase a threshold at all.
- **Two real adherence bugs found (separate from this fix):** (a) the writer treats footer
  verdicts as advisory — e.g. 2026-05-30-weekend footer says "REPEAT (dropped): macrophage
  therapy" yet it's published as a full bullet AND recorded as NEW; (b) `2026-05-31-overview.jsonl`
  was claimed "recorded locally" but is missing on disk after a GitHub-API publish fallback, so
  tomorrow's window is missing today's overview entries.
