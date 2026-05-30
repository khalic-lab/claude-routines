# SPIKE — Tiering routines across model tiers to spare tokens

> Status: **investigation / proposal** (not implemented except the writer bump noted below).
> Written 2026-05-30. Decision owner: Rafael. Supersede or delete once decided.

## Question

We just moved the four writer routines to the latest Opus for reader-facing quality.
Opus is the most expensive tier. **Which routines actually need it, and where can a cheaper
tier (Sonnet / Haiku) cut token spend without hurting output the user sees?**

## Method

Numbers below are read from live trigger configs (cron + `session_context.model`), not
inferred. Per-run "weight" is a rough relative estimate of token volume per run (tool calls +
context + output), not a measurement. Tier cost multipliers are **order-of-magnitude
approximations of relative output-token price** — confirm against current pricing before
acting on absolute figures. They're here to rank levers, not to bill.

Assumed relative output-token cost (approx): **Opus ≈ 5 · Sonnet ≈ 20 · Haiku** → multipliers
`opus = 5`, `sonnet = 1`, `haiku = 0.25`.

## Current state

| Routine | Cron | Runs/wk | Model | Per-run weight | Nature of work |
|---|---|---|---|---|---|
| Morning Overview | `30 4 * * *` | 7 | **opus-4-8** | ~10 | Heavy: multi-source research, 2–4k-word brief |
| AI/ML | `30 19 * * *` | 7 | **opus-4-8** | ~10 | Heavy: research + brief |
| Cyber+Papers (Evening) | `0 17 * * *` | 7 | **opus-4-8** | ~10 | Heavy: research + brief + email digest |
| Weekend Deep Read | `30 7 * * 6` | 1 | **opus-4-8** | ~12 | Heaviest: long-form deep read |
| Watch poll | `0 */4 * * *` | 42 | sonnet-4-6 | ~1.5 | Light: snippet judgment over `watches.yml`, conservative match |
| Weekly Evaluator | `30 9 * * 0` | 1 | opus-4-7 | ~12 | Heavy: reads ~21 posts → health table + patch proposals |
| ~~Markets~~ | retired | 0 | — | — | Disabled 2026-05-30 |

Writers were `sonnet-4-6` until 2026-05-30; the user fixed them at the latest Opus
("always use the latest opus for writing"). That is a **constraint, not a variable** here.

## Where the spend actually is

Weekly cost units = `runs × weight × tier-multiplier`:

| Routine | Before writer bump | After writer bump (today) |
|---|---|---|
| 3 daily writers | 21 × 10 × 1 = 210 | 21 × 10 × 5 = **1050** |
| Weekend writer | 1 × 12 × 1 = 12 | 1 × 12 × 5 = **60** |
| Watch poll | 42 × 1.5 × 1 = 63 | 63 |
| Evaluator | 1 × 12 × 5 = 60 | 60 |
| **Total** | **~345** | **~1233** |

**Headline finding:** once the writers are on Opus they are ~90% of the bill. The writer bump
multiplied the dominant cost ~3.5×. Every support task combined (Watch + Evaluator) is now
only ~10% of spend. So **tiering the support tasks down yields modest absolute savings** — the
real knob is the writers themselves, which is exactly the knob the user chose to spend on.

## Recommendations

### 1. Watch poll: `sonnet-4-6` → `haiku-4-5` — do it
The highest-frequency routine (42 runs/wk, 65% of all runs) doing the lightest, most
mechanical work: it judges whether search snippets clearly satisfy a `match_when` predicate,
is told to be conservative ("a false positive burns `cooldown_days` of signal"), and writes a
tiny stub. This is a textbook Haiku task.
- **Saves** ~47 units/wk (63 → ~16) — small in the new total (~4%) but recurring and free-ish.
- **Risk:** Haiku is slightly likelier to misjudge a borderline snippet. Mitigations already in
  the prompt: conservative-by-default instruction + `cooldown_days` guard. **Pilot 2 weeks,
  then audit fired stubs** (false positives) and spot-check a couple of watches that *should*
  have fired (false negatives). Revert if quality drops.

### 2. Weekly Evaluator: **user decision** — keep on Opus (recommended)
Currently `opus-4-7`. Runs once a week, so its tier barely moves the bill (~60 units/wk either
way). It is the pipeline's QA backstop — it audits the writers and proposes patches, so
judgment quality matters.
- **Recommended:** keep it on an Opus tier. Optionally bump `opus-4-7` → `opus-4-8` for
  consistency with the writers (negligible cost delta, latest reasoning).
- **Alternative:** drop to `sonnet-4-6` if you're comfortable with a lighter weekly audit —
  saves ~48 units/wk. Given how little it runs, the savings aren't worth a weaker auditor.
- Left untouched today on purpose: maxing the auditor to the priciest model *in the same change
  that's about saving tokens* would be self-contradictory, and dropping the auditor is a
  judgment call that's yours, not mine.

### 3. Dedup embeddings: already off the LLM cost path — no action
Story dedup uses `bge-m3` via the Cloudflare Worker, not an LLM call. Not a tiering candidate;
noted so it isn't mistaken for a lever.

## The bigger levers (non-model — flagged, not recommended yet)

Because the writers dominate and are pinned to Opus, the largest remaining token reductions are
about **how much the writers do**, not which model runs the support tasks:

- **Cap writer output length.** 2–4k words × Opus × 22 runs/wk is the bill. Tightening the word
  target or section caps cuts proportionally.
- **Skip-on-empty.** If dedup finds nothing genuinely new for a stream, emit a short "quiet day"
  brief instead of a full Opus research pass. Biggest structural saving; needs care so the user
  still gets a signal.
- **Lower Watch frequency.** `every 4h` (6×/day) → `every 6–8h` cuts Watch runs ~25–33%. Only
  worth it if 4h granularity isn't valued.

These are out of scope for this spike (which is about model tiering) but are where the tokens
really are. Raise as a follow-up if cost is a live concern.

## Proposed end-state tier table

| Routine | Tier | Rationale |
|---|---|---|
| 4 writers | **Opus (latest)** | Reader-facing quality; user-fixed |
| Watch poll | **Haiku** | High-frequency, mechanical, conservative-guarded |
| Weekly Evaluator | **Opus (latest, 4-8)** | Weekly QA backstop; cost negligible at 1 run/wk |
| Dedup embeddings | n/a (`bge-m3`) | Not an LLM call |

## Decision needed from you

1. **Watch → Haiku?** (recommended yes, with a 2-week audit.)
2. **Evaluator: keep `opus-4-7`, bump to `opus-4-8`, or drop to `sonnet-4-6`?** (recommend keep/bump.)
3. **Want a follow-up spike on the real levers** (writer output caps / skip-on-empty)?

## Decisions taken (2026-05-30)

Split by job — polling, writing, and analysis are separate routines, so they tier independently:

- **Writing** (4 writers): `claude-opus-4-8`. Done.
- **Polling** (Watch): `claude-sonnet-4-6` → `claude-haiku-4-5-20251001`. Done. Mechanical
  snippet judgment, never writes/analyzes a brief — Haiku has no effect on output quality.
  2-week audit pending: check fired stubs for false positives + spot-check expected fires.
- **Analysis** (Weekly Evaluator): `claude-opus-4-7` → `claude-opus-4-8` (latest Opus, matching
  the writers; weekly run so the cost delta is negligible).
- **Follow-up spike** on writer output caps / skip-on-empty: approved → `SPIKE-writer-token-levers.md`.
