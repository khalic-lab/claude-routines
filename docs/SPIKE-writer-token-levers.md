# SPIKE — Writer token levers (the real spend)

> Status: **investigation / proposal** (nothing implemented). Written 2026-05-30.
> Follow-up to `SPIKE-model-tiering.md`, which found the writers are ~90% of the token bill
> once they're on Opus. Model tier is now fixed (writing = latest Opus, user constraint), so
> the only remaining reductions are about **how much the writers do per run** and **how often
> they run at full depth**. Decision owner: Rafael.

## Why this spike

`SPIKE-model-tiering.md` showed tiering support tasks (Watch → Haiku) saves only ~4% — the
3 daily writers + Weekend on Opus dominate. To move the bill you have to touch the writers
themselves, without changing the model and without hurting what the user reads.

Caveat up front: **we don't currently measure per-run tokens.** Estimates below are relative.
Prerequisite for acting: get a proxy metric (see "Instrumentation" last).

## Levers, ranked by saving × ease

### Lever 1 — Skip-on-empty ("quiet day" mode) — biggest structural saving
On a slow news day a writer still runs a full Opus research + 2–4k-word compose even if dedup
finds nothing materially new. Proposal: after the dedup `check`, if the stream has fewer than
**N genuinely-new stories** (e.g. N=2 NEW, ignoring REPEAT/ONGOING-without-development), emit a
short "quiet day" brief (3–5 bullets: the ONGOING threads + a one-line "nothing materially new
since {date}") instead of the full pass — and skip the heavy research loop.
- **Saves:** the entire compose + most of the research on quiet days. Potentially the single
  largest reduction, concentrated exactly where the full brief adds least value.
- **Risk:** user loses the daily signal / habit; a "quiet day" that wasn't actually quiet
  (dedup miss) suppresses real news. Mitigations: keep a minimum 3-bullet digest so a brief
  always ships; tune N conservatively; the Evaluator already watches repetition, have it also
  flag over-frequent quiet days.
- **Where:** writer prompts, in the dedup-preflight block that already exists.

### Lever 2 — Output length caps — easy, proportional
Current target is 2000–4000 words/brief; Opus *output* tokens are the priciest part. Tightening
to e.g. 1500–2500, or hard per-section item caps (sections already say 4–7 items — enforce the
low end on thin days), cuts output roughly proportionally.
- **Saves:** ~25–40% of output tokens if the target drops ~1/3. Linear, predictable.
- **Risk:** less depth. The user reads these — trim modestly and watch for "feels thin"
  feedback. Weekend Deep Read is explicitly long-form; exempt or trim least.
- **Where:** the "Constraints" word-target line in each writer prompt.

### Lever 3 — Cap research tool-call volume — moderate
Input tokens come from many WebSearch/WebFetch calls + large fetched pages held in context. The
"Research methodology" block invites broad→refine→fetch per topic. Cap refinements per section
(e.g. ≤1 refinement, ≤N full fetches) and prefer feed reads (already cheap) over full HTML.
- **Saves:** input-side; smaller than 1–2 but real on heavy-research days.
- **Risk:** thinner sourcing / weaker triangulation. The Evaluator's source-diversity and
  triangulation metrics would catch over-trimming.

### Lever 4 — Watch frequency — low priority now
`0 */4 * * *` = 6 polls/day. Now that Watch is Haiku its per-run cost is small, so this is the
weakest lever. Only revisit if 4-hour granularity isn't valued; `every 6–8h` cuts ~25–33% of
Watch runs.

## Recommended experiment order

1. **Lever 2 (output caps)** first — lowest risk, immediate, reversible, and gives a baseline
   on how much trimming the user tolerates.
2. **Lever 1 (skip-on-empty)** next — biggest structural win, but needs the dedup signal to be
   trustworthy and a careful N threshold; run it for a week and review with the Evaluator.
3. Hold Levers 3 & 4 unless the first two don't move the bill enough.

Change ONE lever at a time, one week each, and read the Evaluator review between changes.

## Instrumentation (prerequisite)

We can't tune what we can't see. Cheapest proxy without new infra: have each writer append a
word count (and ideally a tool-call count) to its Coverage footer, and have the Weekly Evaluator
report per-stream mean word count + trend. That's a usable stand-in for output-token spend until
(or unless) real token accounting is wired in. Recommend doing this before Lever 1/2 so the
effect is measurable.

## Decision needed from you

1. Approve Lever 2 (output caps) as the first experiment? If so, what word target — keep
   2000–4000, or drop to ~1500–2500?
2. Approve adding the word-count footer + Evaluator word-count metric (instrumentation) first?
3. Appetite for Lever 1 (skip-on-empty), or is a full daily brief non-negotiable regardless of
   how quiet the day is?
