# Reader feedback — data + loop

Thumbs (+1 / −1) and an optional free-text reason from Rafael on the briefs, captured on the
Jekyll site, landed in this directory, and folded into the writers' editorial guidance **through a
human gate**. Design + rationale: `docs/archive/REVIEW-2026-06-08-feedback-and-dates.md`.

## Status — LIVE (2026-06-18)

The whole loop is wired and verified end-to-end (was BUILT + DORMANT until then):
- **Worker deployed** → `https://feedback-sink.khalic-lab.workers.dev` (khalic-lab CF account; KV
  `FEEDBACK_KV`, secret `FEEDBACK_TOKEN`). All four routes verified (submit/drain/ack/401).
- **Widget enabled** → `_includes/head/custom.html` `FEEDBACK_ENABLED=true` (renders on every brief).
- **Bridge wired** → `.env` has `FEEDBACK_WORKER_URL`+`FEEDBACK_TOKEN`; `bridge.sh` drains before its
  commit and acks after push (and now commits feedback even on no-notification ticks).
- **Consumers wired** (RemoteTrigger, byte-verified) → Evaluator reads last-7d feedback and proposes
  profile patches; all 4 writers read `reader-profile.md` + `source-weights.yml` at compose time.
- Gotcha baked into `feedback.py`: Cloudflare 403s the default `Python-urllib` UA — it sends an
  identifiable UA instead.
- **Per-STORY feedback live (2026-06-19):** each brief story now carries its own inline 👍/👎
  (faint, brightens on hover; 👎 reveals an optional "why?" box). The bottom box stays as a
  brief-level "Overall" note (`story_id == null`). Per-story `story_id` = `{slug}-{slugify(bold
  lead)}` — the visible `<strong>` headline run through dedup's exact `slugify`. It is NOT the
  dedup index `id` (the writer curates a separate, shorter index `headline`), but both the widget
  and the Evaluator derive the key from the *same* source — the brief's bold leads — so they join
  deterministically. Frontend-only change in `_includes/head/custom.html`; Worker/bridge unchanged.

## Flow

```
Rafael taps 👍/👎 (+ optional reason) on a brief page
  │  _includes/head/custom.html widget  ──POST /submit──►  feedback-sink Worker ──► Cloudflare KV
  ▼
LOCAL BRIDGE (cron */10), per tick:
  1 git pull --rebase
  2 python3 tools/feedback/feedback.py drain     # KV -> feedback/{YYYY-MM}.jsonl (dedup by id)
  3 (existing) drain pending-notifications -> ntfy
  4 git add feedback/ pending-notifications/ ... && commit "Drained N" && push
  5 python3 tools/feedback/feedback.py ack        # delete drained KV keys AFTER a successful push
  ▼
GitHub khalic-lab/claude-routines (private; main = source of truth)
  ├─ RAW, ungated:  feedback/*.jsonl   (append-only, auditable, lossless)
  ├─ WEEKLY EVALUATOR (existing routine): reads last 7d of feedback + briefs
  │      → proposes patches to reader-profile.md / reader-profile/source-weights.yml   ◄── HUMAN GATE
  └─ WRITER ROUTINES read at compose time (session_context.sources):
         reader-profile.md                      (NL standing editorial brief)
         reader-profile/source-weights.yml      (never: / reduce: lists)
       ── changed ONLY by Rafael applying Evaluator proposals; never auto-mutated from a tap ──
```

**Why human-gated:** a single tap is noisy; auto-rewriting the writer's instructions from it is the
documented ChatGPT-2025 sycophancy trap at n=1. Capture is lossless and ungated; the *writer-read*
files move only through the Evaluator's human-applied patches.

## Record schema — `feedback/{YYYY-MM}.jsonl` (one JSON object per line)

```jsonc
{
  "id": "a1b2c3d4-…",                 // uuid (Worker-generated); dedup key for the bridge append
  "ts": "2026-06-08T07:14:32+02:00",  // ISO-8601 w/ offset (capture time)
  "reader": "rafael",                  // constant at n=1; kept for forward-compat
  "brief": "2026-06-07-overview",      // post slug — stable v1 key (always present)
  "story_id": "2026-06-07-overview-stem-cell-transplant-keeps-a-severe-autoimmune-d", // per-story
                                       // (v2, web): "{slug}-{slugify(bold lead)}"; null = brief-level
  "vote": -1,                          // +1 | -1
  "reason": "markets snapshot too long on weekends",  // optional free text; "" if thumb-only
  "surface": "web",                    // "web" | "cli"
  "source_domain": null,               // set when the reason names a source -> source-weights.yml
  "consumed": false                    // Evaluator flips true when folded into a patch proposal
}
```

`consumed: false` records are the backlog. Binary ±1 (not stars) maps cleanly onto the
`reduce:` / `never:` arithmetic in `source-weights.yml`.

## Bridge integration (the two added lines)

In the bridge script (`/usr/local/src/news-brief-ntfy-bridge/bridge.sh`), with these in its `.env`:

```sh
FEEDBACK_WORKER_URL=https://feedback-sink.<account>.workers.dev
FEEDBACK_TOKEN=<the bearer set via `wrangler secret put FEEDBACK_TOKEN`>
```

Add **drain before the commit** and **ack after the push** (so the new feedback/*.jsonl rides the
existing "Drained N" commit, and keys are deleted only once safely pushed):

```sh
# ... after `git pull --rebase`, before composing the commit:
python3 "$REPO/tools/feedback/feedback.py" drain || echo "feedback drain failed (non-fatal)"

# ensure the commit stages feedback/ (alongside pending-notifications/):
git -C "$REPO" add feedback/ pending-notifications/

# ... after a successful `git push`:
python3 "$REPO/tools/feedback/feedback.py" ack || echo "feedback ack failed (non-fatal)"
```

`drain`/`ack` are non-fatal and idempotent: a failed push means no ack, so the records stay in KV
and re-drain next tick; the append skips ids already on disk, so no duplicates.

## Consumers

- **Weekly Evaluator** (`trig_01F5npsKTQTLKekAZ5BczKtG`): add to its prompt — read the last 7 days of
  `feedback/*.jsonl`, and propose concrete patches to `reader-profile.md` /
  `reader-profile/source-weights.yml` (flipping the consumed records' `consumed: true`). Human-applied.
- **Writers** (Overview / AI-ML / Cyber+Papers / Weekend): add `reader-profile.md` and
  `reader-profile/source-weights.yml` to each routine's `session_context.sources` so they weight by
  the reader profile and honor the never/reduce lists at compose time.

These wiring changes are **live RemoteTrigger edits** — APPLIED 2026-06-18 (see Status above),
byte-verified against all five prompts.
