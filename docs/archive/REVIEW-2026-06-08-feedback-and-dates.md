# Review — Reader Feedback & Date Handling (2026-06-08)

Synthesis of four research/design tracks: a date-handling audit of `_posts/` (2026-06-01 → 06-08),
a threading / "ongoing since" verification against the story index, prior art on reader-feedback
loops + temporal grounding, and a feedback-mechanism design grounded in the live pipeline.

> **⚠ Correction (post-build verification, 2026-06-08).** During implementation, the SASA/SoftSAE
> "[ongoing since]" defect was re-checked against the real stored vectors and **the synthesis below
> was wrong about the mechanism.** It was **not** a "false cosine merge above 0.93": the two papers
> embed at only **0.7111** (below `T_LOW`), and SASA's best cosine to *any* recent record is 0.7258
> — so `autolink` (gate 0.93) never linked them and the check returned them as **NEW** (handed the
> writer no continuation at all). The thread came from the **writer hand-supplying `thread_id`**,
> manually placing a distinct paper into the SAE topic thread (its own process log: "kept as distinct
> new paper *in the SAE thread*"). Consequences for the fix, applied in code: (a) the real defect is
> **index integrity**, fixed by a **writer-supplied-thread validation** in `cmd_record` (reject a
> hand-set thread whose genesis is a distinct arXiv paper) — not by the autolink guard; (b) the
> autolink arXiv guard still ships as **defense-in-depth**; (c) the reader-facing prose tag was the
> writer *fabricating* a since-date on a NEW story — **only DEDUP.md policy** can prevent that, not
> any `dedup.py` change. Read §2.1 / §3.3 below through this correction. Offline replay confirms the
> shipped arXiv-only guard strips exactly **2** index records (SASA — correct; Poolside report —
> defensible), nothing else.

---

## 1. TL;DR

**Date handling is mostly sound — do not let this read as "dates are broken."**

- The writer derives "today" correctly on every brief from the machine-stamped
  `_Generated <ISO> Europe/Zurich_` header. Coverage windows are explicit and honest
  (weekend arXiv gaps, FX staleness, 403 walls are all disclosed, not hidden).
- The historical `first_seen_date` propagation bug (every record `thread_id == id`,
  `first_seen_date == date`, per `DEDUP-DIAGNOSIS-2026-05-31.md`) **is FIXED**. `autolink()`
  fires regularly: **87 / 1,260 index records (6.9%)** carry an inherited earlier `first_seen_date`.
- **Reader-actionable errors (corrected count — the audit UNDER-counted).** (1) `2026-06-07-ai-ml.md:113`
  the SPCX IPO "prices **11 June**" on "**Wednesday**" — June 11 is a **Thursday** (weekday arithmetic).
  (2) **The serious one the audit MISSED** (surfaced by Rafael 2026-06-08): both **June-6** briefs put
  the SVP "No 10-million Switzerland" federal vote on the wrong weekend —
  `2026-06-06-cyber-papers.md:20` "Federal vote **tomorrow** … votes **Sunday 7 June**" and
  `2026-06-06-weekend.md:19` "votes **this weekend** … result lands **Sunday**". **The vote is 14 June**
  (a Sunday), stated correctly in ~15 May briefs. June 6 = Sat, June 7 = Sun, June 14 = Sun: the writer
  re-derived "it's a Sunday vote + it's the weekend → this Sunday" instead of reading the established
  date. The weekday lint cannot catch this (June 7 *is* a Sunday — internally consistent, wrong event).
  See §2.5.
- **One wrong `[ongoing since]` tag** (`2026-06-06-weekend.md:73`), and it is **not** the old
  propagation bug — nor (per the Correction above) a cosine merge. It is a **writer-supplied
  mis-thread**: the writer hand-set `thread_id` to place a distinct paper (SASA, arXiv 2606.06333)
  into the May-14 SoftSAE topic thread. Index integrity is fixed in code; the prose tag is writer
  policy.

**Recommended path.**

| Track | v1 (now) | v2 (structural) |
|---|---|---|
| **Dates** | C+ as-of block **with a dated weekday calendar** injected every run; **distinct-source-ID guard** in `autolink()` | `event_date` schema field; deterministic backfill for ID-bearing records; window/days-since **lint** gated on `event_date` |
| **Feedback** | Web widget (`custom.html`) + ntfy companion → Worker+KV → bridge poll-and-commit → `feedback/*.jsonl`; Evaluator consumes; writer reads gated `reader-profile.md` | Per-story keying via source-anchored stable IDs (shared with dedup/threading) |

The single most important design choice for feedback: **a human gate (the existing Weekly
Evaluator's human-applied patch proposals) sits between noisy single-tap signal and anything the
writer reads.** Never auto-mutate the writer's instructions from a tap.

---

## 2. Date handling — audit findings

### 2.1 The "ongoing since" / `first_seen_date` verdict (foregrounded)

**The propagation bug is FIXED.** `tools/dedup/dedup.py` `cmd_record` (L514–517) calls
`autolink()`, which inherits `(thread_id, first_seen_date)` from the nearest historical match when
cosine ≥ `AUTOLINK_MIN_DEFAULT` (0.93), overriding the self-referential default. `cmd_backfill`
(L568–569) still self-stamps — **correct** for seeding, where cross-day links can't be recomputed
without embeddings. Empirically: the earliest backfilled files (2026-05-02) are 100% self-referential;
from ~2026-05-26 on, threading appears regularly; 87/1,260 records carry an inherited earlier date.
Confirmed working threads: Lebanon → 2026-05-18, US-Iran → 2026-05-04, Russia-Ukraine → 2026-05-20,
G7 → 2026-05-21.

**~24 of the checked "ongoing since" claims are CORRECT** — the index `first_seen_date` matches the
rendered tag exactly.

**The one WRONG tag — and why it matters.** `_posts/2026-06-06-weekend.md:73`:

> **[arXiv:2606.06333]** Subspace-Aware Sparse Autoencoders … `[ongoing since 2026-05-14]`

Index record `2026-06-06-weekend-subspace-aware-sparse-autoencoders-cut-feature-s` has
`thread_id = 2026-05-14-overview-softsae-…` and `first_seen_date = 2026-05-14`. But a paper with
arXiv ID `2606.#####` cannot have been submitted on 2026-05-14. **[Corrected]** This is **not** a
cosine merge: SASA↔SoftSAE cosine is **0.7111**, and SASA's max cosine to any recent record is
0.7258 — below `T_LOW`, so the check returned SASA as **NEW** and `autolink` never fired. The thread
was **writer-supplied** (`thread_id` hand-set in the record JSON). SoftSAE moreover carries **no
arXiv id** (its url is an arXiv *listing* page), so a "both papers have differing ids" guard could
never have caught it — the candidate-side arXiv id is the only discriminator.

**The strongest single piece of evidence in this whole review:** the writer's *own prose* got it
right and the index overrode it.

- `2026-06-06-weekend.md:76`: "(Continues the SAE-improvement thread from SoftSAE on 2026-05-14;
  **this is a distinct paper** with a new subspace formulation and complexity result.)"
- `2026-06-06-weekend.md:215` (process log): "Subspace-Aware SAEs **kept as distinct new paper** in
  the SAE thread."

The writer *explicitly judged it distinct* — yet `autolink()` merged it in the index and the
rendered tag came out `[ongoing since 2026-05-14]`. So the defect is unambiguously a **false cosine
merge of two different arXiv IDs**, not the (already-fixed) propagation bug, and the fix is a
**distinct-source-ID guard** (§3.3), not a date-arithmetic change.

Two non-bugs noted in the verification, for honesty:
- `2026-06-06-ai-ml.md:41` ChatGPT Lockdown Mode `[ongoing since 2026-02-09]` — **UNVERIFIABLE**.
  The index has no records before 2026-05-02 (backfill horizon); the date is writer-asserted, not
  index-propagated. Possibly correct, just not checkable from the repo.
- `2026-06-07-cyber-papers.md` "Iran war Day 100" / `[ongoing since 2026]` — degenerate
  writer-supplied vague tag, not an indexing bug.

### 2.2 Brief-prose date errors (the audit of `_posts/` text)

| # | File:line | Quoted | Wrong because | Class |
|---|---|---|---|---|
| **A** | `2026-06-07-ai-ml.md:113` | "prices **11 June**" on "**Wednesday**" | June 11 2026 is **Thursday**. Forward weekday count off by one. Source: CNBC snippet 2026-06-03. | Wrong event date — **the only reader-actionable error** |
| **B** | `2026-06-08-overview.md` | US-futures framing cites `[CNBC markets, 31 May 2026]` | 8-day-stale page anchors June-8 market framing (CNBC pre-markets returned **HTTP 403**). Disclosed in Gaps, but the stale citation still sits in the body. | Publish/event-date conflation (a *sourcing* problem, see §3.5) |
| **C** | `2026-06-04-ai-ml.md` | "OpenAI **shipped** …" / "the French lab **rebranded** Le Chat as Vibe" `[…, 2026-06-03]` | Both events were June 3; the June 4 brief's passive voice implies same-day currency. Dates visible in footnotes. | Prior-day events absorbed into "today" voice (minor / hygiene) |
| **D** | `2026-06-05-ai-ml.md` | "Holo3.1 … landed in the **last 72 hours**" | Holo3.1 released June 2; at generation (June 5, 21:42) it was **~94 h** old, not ≤72. | Relative-window arithmetic drift |

### 2.3 What is fine — do not manufacture problems

Verified-correct patterns (don't "fix" these):
- **Ongoing-event anchoring** with explicit `[ongoing since YYYY-MM-DD]` — recurring events aren't
  re-dated as new each day.
- **Weekend arXiv gap** explicitly disclosed (June 6/7 briefs name the June-4 batch being used).
- **FX/market staleness** labelled ("Friday's closes"; "5 Jun — Monday's fix isn't published this
  early").
- **All other day-names check out** — Tuesday (June 2 Cyber), Wednesday→Thursday Mogadishu (June 4),
  Thursday Kim plant tour (June 4), Friday (June 5).
- **Coverage-header vs body** mismatches are *disclosed*, not hidden.
- **"Stale as watch item"** correctly demoted (June 1 AI/ML flags Opus 4.8 / Gemini 3.5 Flash GA as
  out of window → context, not news).

**No instance** of the dangerous failure modes: no date fabricated without a cited source, no event
misdated to the wrong month, no coverage window claiming dates it manifestly doesn't cover.

### 2.5 Finding E — the audit's own miss (the scheduled-event re-derivation bug)

**Surfaced by Rafael (2026-06-08), not the audit.** Both **June-6** briefs misdated the SVP "No
10-million Switzerland" federal vote to **Sunday 7 June** ("votes tomorrow" / "this weekend") when the
vote is **14 June** — a date the pipeline had published correctly in ~15 May briefs (and which the
official État de Vaud / admin.ch pages confirm). June 6 = Saturday, June 7 = Sunday, June 14 = Sunday.

**Why the audit missed it, and why it changes the fix:**
- It is **not** an internal-consistency or weekday error — "Sunday 7 June" is *correct* as a weekday
  (June 7 is a Sunday). The weekday lint (§3.1 lever C+) passes it. So **no amount of as-of /
  dated-weekday-calendar injection prevents this** — the writer wasn't wrong about *today* or about
  what weekday the 7th is; it re-derived *which Sunday the vote is* and got it wrong.
- The only thing that prevents it is **carrying the event's established date** (14 June) so the writer
  reads it instead of re-deriving — i.e. **`event_date` (lever B), propagated along the thread**, plus a
  lint that flags scheduling language ("this weekend / tomorrow / Sunday N / next week") that
  contradicts the story's `event_date`.
- This **promotes `event_date` from "nice structural v2" to THE primary date fix**, and **demotes the
  C+ weekday block to secondary** (it only ever fixed the minor SPCX-class slip). It also exposes an
  audit blind spot: cross-checking a *scheduled event's* framing against the date the pipeline itself
  established (in-thread) is a check the audit did not run. The vote is a correctly-threaded ONGOING
  story (`[ongoing since 2026-05-23]`) whose continuity date was right but whose **event date was
  re-guessed each run** — exactly the conflation `event_date` exists to kill.

### 2.4 Root causes (mapped)

| Root cause | Findings | Note |
|---|---|---|
| Writer re-derives weekday by counting forward from the generation timestamp | A | June 11 is Thursday, not Wednesday — calendar slip, no external check |
| Mental arithmetic on a rolling window | D | Eyeballed "72 h" vs actual ~94 h |
| Prior-day events absorbed into today's voice | C | Cited dates visible; prose implies currency |
| Can't fetch primary source → stale snippet | B | 403 wall; disclosed but citation stays in body. **Sourcing, not date-handling** |
| **Re-derives a SCHEDULED event's date instead of reading the established one** | **E (vote)** | "Sunday vote + it's the weekend → this Sunday" ⇒ June 7 not June 14. The **dominant** failure mode; what the user actually feels. |
| Writer-supplied mis-thread (not cosine) | wrong `[ongoing since]` | Distinct paper hand-filed into a topic thread; writer prose correctly called it distinct; index overrode. See Correction banner. |

---

## 3. Date handling — recommended fix

Two corrections to the obvious framing first, because they re-target the whole fix:

1. **The writer is NOT getting "today" wrong.** Every day-name but one checks out. The real
   arithmetic errors are *forward-counting* (weekday of a future date — A) and *backward-window*
   (how old is X — D), **not** "what is today." A plain as-of block ("today is …") repairs **no
   finding** — it's insurance.
2. **The wrong `[ongoing since]` is not the propagation bug.** Propagation is fixed (§2.1). The
   wrong tag is a distinct-paper false merge. Different defect, different fix.

### 3.1 Levers mapped to findings

| Lever | What it is | Findings it fixes | Verdict |
|---|---|---|---|
| **C+ — as-of block + dated weekday calendar** | Inject `Today: 2026-06-08 (Mon)`, coverage window, **and a small dated weekday table for window ±7d** every run | **A** (weekday) | **Adopt now.** Cheapest high-value move. Plain C fixes nothing; the *dated table* converts weekday lookup from mental arithmetic into a table read. |
| **autolink distinct-source-ID guard** | Suppress the thread link when candidate and best match both carry stable IDs (arXiv/CVE/DOI) that **differ** | the wrong `[ongoing since]` | **Adopt now.** Few lines; `decide_verdict` already computes `exact_keys()` (`dedup.py:458`), so the machinery exists. |
| **B — `event_date` schema field** | Per-story "when the event occurred," distinct from `date` (compose) and `first_seen_date` (first coverage) | **C**; arms the non-ID guard; makes `[ongoing since]` semantically correct; **A's lint depends on it** (can't lint "is 94 h?" without the release date) | **Adopt as v2 structural.** Highest-leverage; everything leans on it. |
| **A — date-arithmetic helper** (`days_since`, `within_window`, `parse_relative`) | Arithmetic the LLM provably botches | **D** (and A's weekday role, but C+ already kills that) | **Adopt as a post-compose LINT, gated on B** — *not* a "call-me" tool. Reframing catches the real failure mode (the model not realizing it must check). |

**Reject** the threading audit's proposed "reject if candidate arXiv month postdates thread
`first_seen_date`" guard. A newer member postdating thread genesis is exactly *normal thread
growth* — that rule would kill legitimate continuations. The correct guard is distinct-IDs-differ
(§3.3).

### 3.2 The three dates

| Concept | Field | Meaning | Source |
|---|---|---|---|
| Event occurred | **`event_date`** (NEW, nullable) | when the described thing happened | deterministic for arXiv/CVE/filing; LLM best-effort for wire; `null` if unknown |
| Brief / compose | `date` (exists) | when this brief ran | routine `--date` |
| First coverage | `first_seen_date` (exists) | earliest brief in thread (genesis proxy) — **NOT the event date** | autolink inheritance |

`[ongoing since]` policy (state in `DEDUP.md`): bind to **thread-genesis `event_date` when known,
else `first_seen_date`**. Today it silently uses a *coverage* date — which is why the SoftSAE merge
produced a tag that was both wrong-thread *and* wrong-semantics.

### 3.3 The shipped fix (precise — supersedes the synth's symmetric-guard proposal)

The synth proposed a *symmetric* "both carry differing stable IDs" guard. That **cannot** catch the
real case (SoftSAE has no id) and over-broad variants break legitimate threads (the "Project
Glasswing" security thread, where the candidate merely *mentions* a CVE). The shipped design instead:

1. **`_distinct_paper(cand, match)`** — **arXiv-only, asymmetric**: true when the candidate carries an
   arXiv id that the match is not about. Restricted to arXiv (the genre where same-topic distinct
   artifacts get conflated); CVE/product sagas are left alone. Candidate without an arXiv id → never
   fires (news/CVE threading untouched). Shared arXiv id → not distinct (same-paper updates still
   thread).
2. **Writer-thread validation in `cmd_record`** *(the load-bearing fix)* — a hand-supplied `thread_id`
   whose genesis (in the recent window) is a `_distinct_paper` is rejected → fresh thread. This is
   what kills the real SASA mis-thread.
3. **autolink arXiv guard** *(defense-in-depth)* — `autolink(…, cand=s)` applies the same check so a
   *future* cosine-driven distinct-paper merge can't happen either.
4. **check-side** (`decide_verdict`) — an ONGOING that is a distinct paper keeps the verdict but sets
   `matched.continuation = false` and `first_seen_date = null`, so the writer is handed no since-date.

**Offline-replay proof:** the shipped arXiv-only validation strips exactly **2** index records — SASA
(correct) and the Poolside Laguna report (defensible: a report of an already-covered model → fresh
thread, no wrong data). All 5 CVE threads, including the legit Glasswing one, are untouched.
`event_date` (§3.2) is the complementary structural carrier for non-ID'd stories.

### 3.4 Change surface

- **`dedup.py`** — `autolink()`: distinct-source-ID guard (v1). `cmd_record()`: accept/derive
  `event_date`. `classify()`/`_matched_obj()`: surface `event_date` in the `matched` object.
  `cmd_backfill()`: keep self-stamping; add **deterministic** `event_date` parse from stored
  arXiv/CVE/url (no network). New helpers `days_since`/`within_window`/`parse_relative` for the lint.
- **`DEDUP.md`** — document `event_date`; the `[ongoing since]` binding policy; the distinct-ID
  guard rationale (cite the SoftSAE false-merge).
- **`ARCHITECTURE.md`** §5.1 / §5.2 — add nullable `event_date` to JSONL + pgvector mirror.
- **`session_context`** (via `RemoteTrigger`, per `CLAUDE.md`) — inject the C+ block every run.

### 3.5 Backfill

**Forward-only for LLM-supplied `event_date`** (can't reconstruct wire-event dates without
re-research). **One-shot deterministic backfill for ID-bearing records** (pure parse of stored
arXiv/CVE/url) — cheap, and it *retroactively arms* the distinct-ID guard.

### 3.6 Out of scope here

**Finding B** (stale May-31 CNBC under a 403 wall) is a *sourcing/freshness-disclosure* rule, not
date-handling: "a citation dated outside the coverage window must be flagged as background, not used
to anchor current-day framing." Note it; don't solve it in this track.

---

## 4. Reader feedback — design

Scope: thumbs ±1 + optional free-text reason from Rafael (n=1), on the briefs. Grounded in the live
pipeline (`bridge.sh`, `embed-proxy`/`og-proxy` workers, `custom.html`, the story index).

### 4.1 Capture surface

| Surface | Thumb | Reason text | Per-story key | New infra | Friction | Verdict |
|---|---|---|---|---|---|---|
| **A. Jekyll web widget** (`custom.html` JS → Worker) | ✓ | **✓** | ✓ (if anchors) | 1 Worker + KV | Medium | **Primary** — only surface that captures the *reason*, the load-bearing n=1 signal. Extends a surface that already runs JS + calls a Worker. |
| **B. ntfy action button** | ✓ | ✗ (ntfy hard limit) | brief-level | bridge inbound | **Lowest** | **Companion** — friction is the real enemy at n=1; he'll tap a phone button he won't open a laptop for. |
| C. Gmail reply parsing | inferred | ✓ | ✗ | mail parsing | Low | Fallback — prose→structured is brittle |
| D. Local CLI | ✓ | ✓ | ✓ | tiny script | High | Keep as manual override / v0 baseline |
| E. GitHub issue | inferred | ✓ | manual | none | High | Too heavyweight for a daily tap |

**Recommendation: A primary + B companion.** ntfy has 4 action types (view/http/broadcast/copy),
max 3, **none accept typed text**. So the 3-action trio is exactly: **👍** (http → sink) / **👎**
(http → sink) / **"Why? →"** (view → deep-link into the web widget's reason box).

### 4.2 Close-the-loop flow

```
Rafael taps 👍/👎 (+ optional reason)
  │  A: brief-page widget        │  B: ntfy button → deep-link to A for the reason
  ▼
Cloudflare Worker (feedback-sink, twin of embed-proxy; bearer on /drain, CORS on /submit, 400-on-bad-shape)
  │  validate shape → write 1 record to KV
  ▼
Cloudflare KV (private holding pen — not the repo yet)
  │  ⟵ bridge GET /drain (bearer) on the EXISTING */10 cron tick
  ▼
LOCAL BRIDGE  append → feedback/{YYYY-MM}.jsonl ; commit -c commit.gpgsign=false ; push main
  ▼
GitHub khalic-lab/claude-routines (private; main = source of truth)
  ├─▶ RAW, ungated: feedback/*.jsonl  (append-only, auditable)
  ├─▶ WEEKLY EVALUATOR (existing routine, opus-4-8): reads last 7d of feedback + briefs
  │       → proposes patches to reader-profile.md / source-weights.yml  ◀── THE HUMAN GATE
  └─▶ WRITER ROUTINES read at compose time (session_context.sources):
          reader-profile.md  (NL standing editorial brief)
          reader-profile/source-weights.yml  (never: / reduce: lists)
        ── change ONLY through the gated Evaluator path; never auto-mutated ──
```

**Transport correction (load-bearing).** The feedback prior-art claimed "the bridge already
subscribes to ntfy topics … no new inbound listener required." **This is false**, verified against
`bridge.sh`: the bridge is strictly **outbound-only** — a `*/10` cron that reads
`pending-notifications/*.json` *from* the repo and `curl`s them *out* to ntfy; it subscribes to
nothing. Inbound feedback is therefore **net-new** — but a cheap, natural extension: add **one
poll-and-commit step on the same cron tick** (GET Worker `/drain` → append `feedback/*.jsonl` →
existing commit/push). No new daemon, no public inbound listener, no GitHub token in Cloudflare.
The Worker `/drain` must be idempotent (cursor or delete-on-ack) so a missed tick neither loses nor
double-commits.

**Why human-gated, not a second auto-update path.** The prior art's own cautionary tale —
ChatGPT's July-2025 sycophancy regression, where optimizing on short-term thumbs diverged from
long-term satisfaction — is exactly the n=1 trap. A single tap is noisy; auto-mutating the writer's
instructions from it lets one annoyed 👎 reshape tomorrow's brief. So **`feedback/*.jsonl` is
ungated and auto-committed** (capture must be lossless), while **the writer-read files are gated**
through the Evaluator's existing human-applied patch proposals. The loop is *closed* (not
feedback-theater) the moment the Evaluator prompt references `feedback/*.jsonl` and the writers'
`session_context.sources` reference `reader-profile.md`.

### 4.3 Granularity

**Per-brief in v1, per-story in v2.**

| | Per-brief (v1) | Per-story (v2) |
|---|---|---|
| Key | post slug (`2026-06-07-overview`) — already stable, **zero writer change** | index `id` — requires writer to emit matching HTML anchors |
| Signal | coarse but, with a reason, already strong at n=1 | precise ("this item too long" / "more like this") |

The load-bearing constraint (verified, not assumed): the brief markdown has **no per-story anchors
today**, and the index `id` is a *normalized slug ≠ the prose headline*. In `2026-06-07-overview`:
index `id` `…-china-s-ev-adoption-averted-an-estimated-262-000` vs prose "China's
**electric-vehicle boom** averted…". So per-story keying needs the writer to emit an anchor per
bullet using **the same slugifier the index uses** — that alignment is the prize *and* the cost.
**Design the schema + Worker to accept a nullable `story_id` from day one** → v1 ships per-brief
with no writer change, v2 turns on per-story with no schema migration.

### 4.4 Feedback record schema

`feedback/{YYYY-MM}.jsonl`, one JSONL line per signal:

```jsonc
{
  "ts": "2026-06-08T07:14:32+02:00",   // ISO-8601 w/ offset (matches brief "Generated" stamps)
  "reader": "rafael",                   // constant at n=1; kept for forward-compat
  "brief": "2026-06-07-overview",       // post slug — stable v1 key (always present)
  "story_id": null,                     // index id when per-story (v2); null for per-brief (v1)
  "vote": -1,                           // +1 | -1  (binary; not stars — maps to weight arithmetic)
  "reason": "markets snapshot too long on weekends",  // optional free text; "" if thumb-only
  "surface": "web",                     // "web" | "ntfy" | "cli"
  "source_domain": null,                // set when feedback names a source → feeds source-weights.yml
  "consumed": false                     // Evaluator flips true when folded into a patch proposal
}
```

`consumed` makes loop-closure *auditable* — un-consumed records are the backlog. Binary ±1 (not
stars) maps cleanly onto the `reduce:`/`never:` arithmetic the writer applies.

**Writer-read files (gated outputs):**
- `reader-profile.md` — NL standing editorial brief (profile-as-text, updated-not-retrained).
- `reader-profile/source-weights.yml` — `never:` (hard pre-filter) + `reduce:` (soft penalty).

Both written **only** by Rafael applying Evaluator proposals — never by Worker or bridge.

### 4.5 Abuse / privacy (minimal, n=1)

- **A client-side widget cannot keep a bearer token secret** — `embed-proxy`'s bearer works *only
  because the browser never calls it*. Don't lean on bearer-auth for surface A. The real defense is
  **the human gate**: garbage in `feedback/*.jsonl` dies at the Evaluator. Cheap hardening: Worker
  size/shape caps (mirror embed-proxy's 400-on-bad-shape), an unguessable per-deploy widget key.
- **The bridge↔Worker `/drain` bearer token *is* a real secret** (lives on the Mac + Worker, never
  in a browser) — gate it like `EMBED_TOKEN`.
- **Sink choice = transport privacy.** A public ntfy topic is **world-readable**; reason-text is
  more sensitive than notification bodies → route it through the **private Worker+KV**, not an ntfy
  topic. (A bare ±1 thumb could ride ntfy, but one sink for both is simpler.)

### 4.6 Phased build

- **v0** — local CLI (surface D) appends to `feedback/*.jsonl` + commits. Validates the schema and
  the Evaluator-consumes-it loop before any Worker exists.
- **v1** — deploy `feedback-sink` Worker + KV; widget in `custom.html`; ntfy 3-action trio; one
  `/drain` step on the bridge cron; point Evaluator at `feedback/*.jsonl`; add `reader-profile.md`
  + `source-weights.yml` to writers' `session_context.sources`. **Closed loop, zero brief-writer
  prompt change beyond reading the profile.**
- **v2** — writer emits per-bullet anchors (index slugifier); widget sets `story_id`; Evaluator
  reasons per-story.
- **Later** — decay on stale `reduce:` weights, asymmetric weighting (👎 > 👍, Google Discover's
  documented choice). Still gated, still no fine-tuning.

---

## 5. Prior art — how others solve the AI-journalist conundrum

### 5.1 Reader-feedback loops

- **ChatGPT** — thumbs feed RLHF *across hundreds of millions of users* (a population mechanism,
  irrelevant at n=1). The n=1-relevant piece is **memory** (Apr 2025): key-value notes auto-extracted
  and injected into future context. The **July-2025 sycophancy regression** is the cautionary tale —
  optimizing on short-term approvals diverged from long-term satisfaction.
- **Netflix / Google Discover / YouTube** — three-register pattern that generalizes: item-level
  block (permanent) → topic-weight (probabilistic, decayable) → source-level block (pre-filter).
  Discover weights a dismissal **more** than a positive click (documented asymmetry). Netflix's 2024
  TechBlog: short-term clicks diverge from long-term retention.
- **Feedly Leo AI** — explicit mute/boost permanently overrides implicit engagement. The closest
  product analog to a per-user blocklist.
- **Artifact** (defunct 2024) — topics × sources × authors; shut down for market size, *not*
  personalization failure.
- **beehiiv polls / SparkLoop Reactions** — one-click email emoji → web page for free-text. Both
  capture and dashboard the signal; **neither documents an automatic rating→next-issue path.** The
  canonical **write-only gap**.
- **LLM personalization research** — GRAVITY (arXiv:2510.11952), RLPA Dynamic Profile (2505.15456),
  Persistent Memory + Profiles (2510.07925), Weak-Reward User Preference (2603.20939) converge on
  **profile-as-text, updated-not-retrained** — no per-user fine-tuning.
- **Martin Fowler, "Feedback Flywheel" (2025)** — names the failure: "most teams discard this
  signal … AI effectiveness flatlines." Loop closes only when captured signal → diff on a file the
  next writer run actually reads.

**The n=1 reality.** RLHF/DPO needs thousands of diverse preference pairs; six months of one
person's daily feedback is ~1,000 signals in one domain — insufficient for stable reward-model
training. What works at n=1, in increasing complexity: (1) explicit preference list (Feedly Leo),
(2) NL preference profile updated online (ChatGPT memory), (3) per-story feedback log →
standing preferences. **No fine-tuning at any tier.**

**ntfy free-text verdict (verified against primary docs).** ntfy has **exactly four action types**
(view, http, broadcast, copy), **max 3 per notification**, and **none accept user-typed text** —
`http` sends a *pre-defined fixed body* set at publish time. So: binary thumb = yes (two `http`
buttons); free-text reason = **no, not in ntfy** — it must live on a web page opened by a `view`
button. (Note: the prior art also cited ntfy GitHub issue #134's "listen on a determined topic for a
reply" pattern; the *design* track supersedes the topic-as-sink idea for reason-text on privacy
grounds — a public topic is world-readable — routing reason-text through the private Worker+KV
instead. Use ntfy only for the low-sensitivity outbound + the ±1 thumb if desired.)

### 5.2 Temporal grounding

- **Anchoring "now" — universal standard.** Anthropic's own *published* system prompts substitute a
  `{{currentDateTime}}` template variable on every call (Opus 4.8/4.7, Sonnet 4.6) — see
  `platform.claude.com/docs/en/release-notes/system-prompts`. OpenAI's cookbook injects
  `datetime.now().isoformat()`. **ISO 8601 with hyphens (`YYYY-MM-DD`)** is prescribed. For a
  compose-time routine (fires once, exits), a single injection at session start suffices — multi-turn
  drift doesn't apply.
- **Three-date model — concrete field names.** GDELT's codebook is the clearest authority:
  `SQLDATE` (event occurred) vs `DATEADDED` (ingestion), warning "news published today could add
  events from the distant past." TimeML/TIMEX3 (ISO 24617-1), schema.org
  (`datePublished`/`dateModified`/`startDate`), and temporal-RAG literature all converge. The current
  JSONL captures `date` (compose) + `first_seen_date` (first coverage) but is **missing `event_date`**.
- **Failure modes (with papers).** Knowledge-cutoff hallucination (universal); temporal blindness in
  agents (arXiv:2510.23853, TicToc — no model exceeded 65% timestamp alignment); **date-tokenization
  fragmentation** (arXiv:2505.16088, EMNLP 2025 — up to 10-pt accuracy drop for un-hyphenated strings
  like `20260312`, hence the hyphenated ISO rule); recency bias in reranking (arXiv:2509.11353 — up
  to 95-rank shifts, 4.78-yr mean date displacement across all 7 models).
- **Production systems.** Bloomberg AI Summary = explicitly timestamped point-in-time snapshot;
  Perplexity's API exposes six date params separating publish / modified / relative-recency; Reuters
  News Tracer separates detection time from event time via credibility scoring.

---

## 6. Cross-thread synergy

**One stable, source-anchored story `id` unifies three subsystems.** Prefer
`arxiv:NNNN.NNNNN` / `cve:CVE-YYYY-NNNNN` / canonical-URL-hash over the current
`{date}-{slug}-{slugify(headline)}` whenever a source ID exists (fall back to the current scheme
when none does). That single ID then serves:

| Consumer | Use |
|---|---|
| **Dedup** | the deterministic **exact key** (`decide_verdict`/`exact_keys`, `dedup.py:458-463`) |
| **Threading** | the **distinct-source-ID autolink guard** (§3.3) — the fix for the wrong `[ongoing since]` |
| **`event_date` metadata** | the natural carrier for the per-story event date |
| **Feedback keying** | the **per-story `story_id`** handle (§4.3, v2) — same identifier the index, thread, and event metadata already use |

The slug-vs-headline gap (§4.3) is exactly why per-story feedback isn't free today: the writer must
emit anchors with the **same slugifier the index uses** so anchor = `id` = `thread_id` =
event-metadata key = feedback handle. Adopting source-anchored IDs collapses that alignment problem
for every ID-bearing story at once — which is why this question rides inside the date-fix-scope
decision rather than standing alone.

---

## 7. Open decisions for Rafael

1. **Feedback capture surface** — web widget + ntfy companion *(rec)* / web-only / ntfy-only / CLI-only.
2. **Loop-closure path** — human-gated via the existing Evaluator *(rec)* / auto-mutate writer files / hybrid.
3. **Feedback granularity** — per-brief v1 → per-story v2 *(rec)* / per-story from the start.
4. **Date-fix scope** — full v1 + v2 incl. `event_date` schema + source-anchored IDs *(rec)* / v1 only (C+ block + autolink guard).

(Each is expanded with options + trade-offs in the structured output below.)

---

## 8. Out of scope / not now

- **Finding B** (stale-snippet citation under a 403 wall, `2026-06-08-overview.md`) — a
  sourcing/freshness-disclosure rule, not a date-handling change. Flagged, not fixed.
- **ChatGPT Lockdown Mode `[ongoing since 2026-02-09]`** — unverifiable (pre-dates the index
  backfill horizon of 2026-05-02); leave as writer-asserted.
- **Per-user fine-tuning / RLHF / DPO** — infeasible and unjustified at n=1 (≈1,000 signals from one
  person in one domain). Profile-as-text only.
- **A standalone "get today's date" tool** — the writer already gets "today" right; C+ subsumes the
  weekday role. Reject in favor of the C+ block + a post-compose lint.
- **Routing reason-text through a public ntfy topic** — world-readable; rejected on privacy grounds
  in favor of the private Worker+KV sink.
- **Auto-mutating `reader-profile.md` / `source-weights.yml` from raw taps** — rejected (sycophancy
  trap); changes flow only through the human-gated Evaluator.
