# SPIKE — Deterministic feed poller (deferred: wrong problem)

> Status: **deferred by Rafael, 2026-07-07** — "the goal is to make me watch less news, not
> another avenue." Kept as the reference analysis for if/when that calculus changes. Any revival
> must start from the *human aspect* (§4), not from this machinery.

## 1. Context

The continuous-news SPIKE (`SPIKE-2026-07-07-continuous-news.md` §3.6 step 7) made continuous
ingestion conditional after the adversarial review killed sub-day latency as a goal (zero reader
signal demanded it) and honestly repriced the LLM scout at **+8–13% weekly tokens** (84 Haiku
fires/wk), not the +1.4% first claimed. Rafael then set a harder constraint: **no LLM called all
day — paid API.** That kills the scout permanently, but a deterministic-only variant survives
technically. This spike records it.

## 2. The deterministic-only variant (no LLM anywhere)

- **Worker cron** (fetch-proxy or a sibling Worker, `*/15 * * * *`): fetch the RSS/Atom feeds from
  the registry's `probe:` blocks (the registry is the single source of truth — the review killed a
  second `feeds.yml` manifest), parse, canonicalize URLs with the same `norm_url` semantics,
  diff against a **seen-set in KV**, append new items to a KV queue. Single-blob feedstate — one
  KV write per cron invocation, not per feed (free tier allows 1,000 writes/day; naive per-feed
  writes die mid-afternoon; **confirm the account's plan before any build**).
- **Bridge drain** (pure code, existing pattern): the local bridge's 10-min tick drains the queue
  two-phase (drain → commit `index/inbox/{date}.jsonl` → ack), exactly like the feedback sink.
- **Writers consume the inbox**: at their normal fire time, the prompt's first fetch pass reads
  `index/inbox/` instead of re-crawling feeds — tokens shift from crawling to judgment; per-fire
  cost flat or slightly down. Feed-less sources are unaffected (HTML diff-polling was killed —
  nonce/ad-slot noise).

**What it gives:** writers never miss a feed item published between fires; less per-fire crawl
work; round-the-clock commits incidentally keep Pages deploys fresh.
**What it does NOT give:** intra-day surfacing. Nothing judges importance between fires — items
just wait, pre-fetched, for the next edition. No pushes, no new reading surface.

## 3. Why deferred anyway

Even LLM-free and cheap, the poller optimizes **supply and freshness** — and the operator's
stated goal is the opposite axis: **less time watching news, not more news arriving**. The
bulletins-as-product framing (continuous-news SPIKE §1, open question 1) stands: nothing in the
recorded reader signal has ever asked for faster or more. A supply-side optimization with no
demand signal is scope creep wearing an engineering costume.

## 4. Revival criteria — the human aspect first

Do not revive this from the machinery end. Revive it only after a deliberate design pass on the
**attention economics** of the pipeline — questions of the shape:
- What is the reader's news *time budget*, and does each surface respect it?
- Should the homepage/briefs *shrink* as stories are read (the read/unread state now exists)?
- Is the right metric "stories delivered" or "minutes-to-sufficiently-informed"?
- Would the poller let editions get *shorter* (fresher inputs → tighter curation), rather than
  let more items in?

If a future design makes "watch less news" the objective function and the poller demonstrably
serves it (e.g. it funds shorter, better-curated editions), build §2 as specced. Otherwise leave
this filed.

## 5. Preconditions (unchanged from the review)

- Cloudflare plan check (KV write budget) — blocks any build.
- Registry `probe:` blocks are the only feed manifest.
- Bridge stays the only git writer on the local side; two-phase drain/ack; `-c commit.gpgsign=false`.
