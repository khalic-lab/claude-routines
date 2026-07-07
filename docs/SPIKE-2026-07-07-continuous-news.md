# SPIKE — Story-centric redesign: identity, feedback, discovery (2026-07-07)

> Proposal. Synthesized from a full-pipeline factual dossier (5 maps), a batch-assumption critique,
> two design tracks (continuous ingestion; source diversification), and a binding adversarial review.
> **Not yet implemented; no live RemoteTrigger edits made.** Only proposals that survived the review
> appear in the target architecture; kills are recorded in §7. The review's central reframe is
> adopted throughout: **the evidence funds an identity/feedback repair and a discovery mechanism —
> it does not fund a latency machine.**

## 1. Verdict & summary

**What is wrong with bulletin-batch.** The story is the real-world unit the reader cares about, but
in this pipeline the story exists only as an anonymous substructure inside an edition. Every
identifier, file, cap, window, notification, vote, and review is keyed to `{date}-{stream}` — and
story identity is minted **four times independently** (dedup index, homefeed, feedback, plus the
brief itself carrying no id at all), from different source text each time. Three demonstrated
defect classes follow:

1. **Identity failure.** The id join between index and homefeed succeeds ~28% of the time; canonical
   URL had to be adopted as the real join key. `thread_id` — the only cross-edition story concept —
   is an inert promoted edition id that no consumer reads. The 2026-07-04 Khamenei downvote is
   structurally unlinkable to the daily edition three days earlier that had the date the reader
   asked for.
2. **Feedback loss.** ~27% of all reader feedback ever captured (9 of 33 distinct signals) fell
   through the Evaluator's 7-day window arithmetic and sits `consumed: false` today, never surfaced
   by anyone. The Evaluator's own continuity broke on 2 of 9 runs. The designed "≥2 same-theme
   signals" noise filter has never once been satisfiable as designed — every ≥2 cluster on record is
   one person double-tapping one story within seconds.
3. **Discovery collapse.** New-domain discovery fell **81 → 8 per month** (June → July, like-for-like
   on the four live streams); live top-5 domain concentration is **72–74%**. The causal chain is
   structural: hard egress allowlist ≈ the top-5 list; one shared prompt partial templates the same
   7-host feed set into all four streams; volume caps + "stop when triangulated" end research the
   moment the guaranteed feeds fill quota; and the T3 rule forces every novel find back onto the
   closed T1/T2 lists.

**What we change.** (a) One durable, deterministic story id (`st-{sha1(norm_url)[:12]}`) and an
append-only **event ledger** under `index/ledger/`, with briefs/homefeed/notifications becoming
projections; (b) feedback keyed to that id and **folded continuously by the bridge**, so window-gap
orphaning becomes impossible; (c) a **source registry with a credibility lifecycle**
(`sources/registry.yml`) plus deterministic preflight/lint/health tooling that converts discovery
pressure from decayed prompt exhortation into measured, enforced numbers; (d) the Evaluator's
mechanical dimensions computed by script, its proposals machine-readable with an `applied: true`
verification stamp, and the source-scout duty absorbed into its existing Sunday fire.

**What we deliberately do not change:** writer cadences, models, the bulletin format, the human
gate on preferences and source trust, or any trigger — steps 1–6 of the migration are **zero
RemoteTrigger operations**. Continuous ingestion (Worker feed poller + Watch→Scout conversion +
per-story push) survives review only as a **conditional final phase**, gated on the discovery
metrics still lagging after the registry is armed, or on Rafael explicitly asking for intra-day
surfacing — nothing in the recorded reader signal says he wants it.

## 2. What the evidence says

**Source concentration (recomputed deterministically from `index/stories/*.jsonl`, 1,456 records,
2026-05-27 → 2026-07-06).** Top domains: `arxiv.org` 415, `aljazeera.com` 171, `nvd.nist.gov` 155,
`nature.com` 135, `letemps.ch` 114, `srf.ch` 104. Headline top-5 share 68% — but `nvd.nist.gov` is
100% historical (the security pipeline was deleted 2026-06-29 and is decaying out of the 40-day
index); **excluding it, live top-5 share is 72.2%**. Like-for-like on the four current streams:
June ran 94 unique domains / 81 new; July ran **21 unique / 8 new**, top-5 at 73.7%. The collapse is
ongoing under the current prompt regime, not an artifact of the lineup shrink. Note: `arxiv.org` at
28.5% is a *hub* hosting thousands of independent primary artifacts — host concentration there is
not source concentration, and the mechanism in §3.4 exempts it.

**Latency (from the process-flow analysis).** Worst-case story-breaks→reader-sees is dominated
entirely by wait-for-next-fire: News ~24h, AI/ML ~4 days, Science ~7 days; writer runtime, Pages
build, and the bridge poll are minutes (measured drain latencies 47s–3m26s in-window). **But — the
review's load-bearing finding — no reader signal supports spending against this column.** Verbatim
from the signals dossier: *"No evaluator ever flagged a timeliness problem in the sense of 'this
story is old news by the time it's published.'"* 31 of 33 distinct feedback signals are upvotes on
the bulletins as they are. The monolith's *demonstrated* costs are different: the quota-driven
discovery collapse, atomic edition loss (AI/ML published nothing on 06-24 — one failed fire = a
4-day content hole), and cross-day repetition (AI/ML's 53% repeat rate drove the cadence *down*).

**The reader's own words** — the entire corpus of reasoned feedback, four sentences:

1. 👎 2026-06-19: *"this is nature blog, not at all at the same level of publication as the actual
   mag. You need to read the actual study… please stear away from sensationalism"* — primary-source
   rigor, sub-domain credibility (Nature `d41586-` news vs `s41586-` research).
2. 👍 2026-06-19: *"Very relevant to my current work, it's crazy how many papers have direct
   impact"* — work relevance of papers.
3. 👍 2026-06-20: *"We should probably accept the 'best of the best' for this week in the weekend
   long read, not only stuff from that day"* — curation window (already shipped 2026-06-29).
4. 👎 2026-07-04: *"Missing context on when it hapenned"* (Khamenei) — **date anchoring**, not
   staleness. He complained the digest omitted *when*; he did not complain he learned it late.

**Evaluator loop pathologies (9 reviews).** The human-gated weekly patch loop has multi-week,
unverified latency: the AI/ML feed fix took four review cycles to stick; the T3 deny-list took two
reissues; no mechanism verifies a Before/After patch was ever applied; the same open question was
asked four times and never closed; reference lists (the "confirmed unavailable" domains) lagged
reality by ≥2 cycles, producing false-positive violations. The Evaluator's word budget is burned on
hand-counting citations rather than editorial judgment. Prompt exhortations demonstrably decay —
which is why §4 puts everything countable on the deterministic side of the line.

## 3. Target architecture

### 3.1 Story-centric data model

**Identity.** `st-{sha1(norm_url)[:12]}` — a pure function of the canonical URL (the existing
`norm_url()` scheme/www/fragment/utm-insensitive canonicalization). No date prefix: the review
killed `st-{YYYYMMDD}-…` because two actors encountering the same URL across a midnight/stale-pull
boundary would mint two ids; a URL-pure id collapses that race into a duplicate the materializer
dedupes. 12 hex chars (≥8 needed at this corpus size; 12 is free insurance). `thread_id` keeps its
semantics (the cross-edition real-world story) but is genesis-minted; the calibrated auto-link
machinery (`AUTOLINK_MIN=0.93`, exact-URL/arXiv-id hard gate, `_distinct_paper`) is reused
unchanged.

**Primary store: `index/ledger/{YYYY-MM-DD}.jsonl`** — append-only, one event per line, partitioned
by *ingest* day. `.gitattributes` (new file): `index/ledger/*.jsonl merge=union`. Event types:

```jsonc
{"ev":"seen",    "ts":"…","actor":"news",  "story":{ /* full record below */ }}
{"ev":"update",  "ts":"…","actor":"news",  "id":"st-…","rev":2,"fields":{…},"note":"…"}
{"ev":"publish", "ts":"…","actor":"news",  "id":"st-…","edition":"2026-07-08-news",
                 "fields":{"display_body":"…","why":"…","importance":3,"status":"settled"}}
{"ev":"status",  "ts":"…","actor":"news",  "id":"st-…","status":"superseded","superseded_by":"st-…"}
{"ev":"feedback","ts":"…","actor":"bridge","id":"st-…","vote":-1,"reason":"…"}
{"ev":"notify",  "ts":"…","actor":"…",     "id":"st-…","channel":"…"}   // only if push ever ships (§3.6 step 7)
```

**Materialized snapshot — never committed.** `tools/store/store.py materialize` folds the last 60
days into a thread map at fire time (<1s at this corpus size); every consumer regenerates it after
`git pull`. Committing only the append-only ledger eliminates a whole merge-conflict class.
**Materializer invariants (review-mandated, with tests):** sort events by `(ts, actor)`; dedupe by
`(ev, id, rev)`; fold genesis events sharing a `norm_url` into one story. `store.py selftest`
includes a two-branch merge test proving union merge actually engaged — a missed gitattribute
otherwise surfaces as a raw merge conflict inside a routine session.

**Full story record** (superset of the current §5.1 schema; every current field survives):

```jsonc
{
  "id": "st-a3f9c2d1e07b",            // NEW construction (was {date}-{stream}-{slug})
  "thread_id": "st-77e01b4c9a2f",     // genesis-minted; same concept as today
  "status": "developing",              // NEW: candidate | developing | settled | superseded | dropped
  "revision": 2, "history": [ … ],     // NEW (history derived by materializer)
  "first_seen": "2026-07-08T06:12:44Z",// NEW full timestamp (was day-grained first_seen_date)
  "updated": "2026-07-08T11:40:02Z",   // NEW
  "event_date": "2026-07-07",          // unchanged (when it HAPPENED, nullable)
  "headline": "…", "summary": "…",     // unchanged roles
  "display_body": "", "why": "",       // unchanged (filled at publish)
  "url": "https://…", "alt_urls": [],  // alt_urls NEW: corroborations folded on update
  "source_domain": "srf.ch",
  "tier": "T2", "tags": ["single-source"],
  "topics": ["switzerland"],           // unchanged controlled vocabulary
  "importance": 2,                     // RESCOPED story-absolute: 3=interrupt-worthy, 2=homepage-today, 1=brief-only
  "source_status": "established",      // NEW: registry status at citation time (§3.4)
  "origin": "writer:news",             // NEW provenance: writer:{slug} | watch:{id} | (worker-feed:{id} if step 7 ships)
  "streams": [], "editions": ["2026-07-08-news"],   // NEW projection bookkeeping
  "feedback": {"up":0,"down":0,"last_reason":null}, // NEW: folded thumbs (fact, not preference)
  "legacy_ids": ["2026-07-08-news-…"], // migration join for old feedback/feed records
  "emb": "…", "embedding_model": "bge-m3"           // unchanged
}
```

`importance` re-scoping requires rewriting `routines/_shared/newsroom-ethos.md`'s "Exactly one 3
per edition" rubric **in the same commit** as the first stream that adopts it (review B3 fix);
"one lead per edition" moves to projection time. `metrics.py` treats the rubric version as
per-stream until rollout completes.

**Migration posture.** `index/stories/{date}-{slug}.jsonl` is demoted to byte-identical dual-write
during migration, retired at the end; `tools/dedup/fixtures/` stay frozen for the calibration
suite. `_posts/*.md` remain forever — as rendered artifacts of publish events.

### 3.2 Fire topology — unchanged crons, one conditional exception

| Component | Trigger / substrate | Cron | Model | Change |
|---|---|---|---|---|
| News | `trig_012KfuF2Fc8KxNRS9KT1iuYb` | `0 10 * * *` | opus-4-8 | prompt only (§3.3) |
| AI/ML | `trig_01QVL6eSmHTUrmnSLHrpNN9Q` | `0 10 * * 2,5` | opus-4-8 | prompt only |
| Science | `trig_01YLiCr5YJ2XNh2QyPbkyzQP` | `0 15 * * 3` | opus-4-8 | prompt only |
| Weekend | `trig_01XKzge4DxP6wTjLwtkoYeqj` | `30 7 * * 6` | opus-4-8 | prompt only |
| Evaluator | `trig_01F5npsKTQTLKekAZ5BczKtG` | `30 9 * * 0` | opus-4-8 | prompt only — gains metrics.py, machine proposals, **source-scout duty** |
| Watch | `trig_01FgrFMfsreu597nKUXEEQMt` | `0 */4 * * *` | haiku-4-5 | **unchanged in steps 1–6**; converted to Scout only if step 7 fires |
| Bridge | Mac cron | `*/10 7-22 * * *` | none | gains `fold.py` (+ `-c commit.gpgsign=false`) |
| Worker poller | fetch-proxy cron + KV | `*/15 * * * *` | none | **step 7 only, conditional** |

No collision-grid changes in steps 1–6. If step 7 ships: Scout at `20 */2 * * *` (`:20` avoids every
writer minute; nearest gap 20 min from News/AI-ML 10:00), and the RemoteTrigger update follows the
CLAUDE.md protocol — full `session_context` echo, bootstrap shim pointing at `routines/scout.md`
with the token injected shim-side, **no `outcomes` key** (the documented stranded-reviews trap).

### 3.3 Writer flow deltas (all repo-side prompt edits via `routines/src/` + `assemble.py`)

1. **First research action:** `python3 tools/sources/preflight.py --slug {slug}` → the plan (not any
   prompt table) is the authority on what to fetch, how, and what pressure applies today (§3.4).
   **Emergency slate (review C8 fix):** the shared partial keeps a ~5-line degraded-mode floor
   ("if preflight fails: SRF/LeTemps/AlJazeera/arXiv/Nature feeds; note `source-plan unavailable`
   in Gaps") — a floor, explicitly labeled, never the ceiling.
2. **New-source citation rule (the single highest-leverage change):** T3 aggregators (HN/Reddit/X)
   remain never-cited — but a **genuine primary source discovered through search or a T3 lead may be
   anchored immediately even if absent from the registry**, tagged `[new source]` (lint-checked).
   `registry.py sync` auto-enters it as `candidate`. This unblocks the mechanism most responsible
   for the 95→7 discovery collapse.
3. **Per-story anchors:** emit `<a id="st-…"></a>` before each bullet/`###` heading — what lets
   feedback and the homefeed key on the store id.
4. **Publish events:** Step C appends `ev:"publish"` per kept story (dual-writing the legacy index
   file during migration); Step C.25 runs `lint.py` (§4).
5. **Discovery footer contract:** exactly one of `- Discovery: met (…)` / `- Discovery: waived —
   <concrete reason>` (lint-verified; the waiver is free but counted).
6. Research methodology, volume caps, ethos, `[ongoing since]` framing, homefeed rebuild,
   commit/rebase-retry, email: unchanged. (If step 7 ships, writers gain a store-shortlist-first
   step with a **fallback lane**: "if the store working set is below N items or the last scout
   commit is >12h old, fall back to feed-first research as before" — review B9 fix.)

### 3.4 Source registry + credibility lifecycle

**`sources/registry.yml`** — the credibility-lifecycle source of truth. Per domain: `class`
(`outlet` | `hub` | `institutional`), `tier` (T1/T2/T3), `status` (lifecycle below), `reach`
(`direct` | `proxy` | `search-only` | `blocked` | `blocked-paywall`), `probe:` block (feed URL +
method — doubling as the polling manifest if step 7 ever ships), `streams:` affinity, `last_cited`,
`feedback` notes, and an append-only `lifecycle:` audit trail. **`subsources`** carry path-prefix
tier splits — e.g. `nature.com` `/articles/d` (news blog) = T2 vs the journal's `s41586-` = T1,
mechanizing the reader's most articulate complaint.

**Write-contention fix (review C1 — the fallback becomes the default):** high-frequency machine
writes go to append-only `sources/candidates.jsonl` and `sources/last-cited.jsonl` (union-merge
safe; `last_cited` folds as `max()`). `registry.yml` itself is written only by humans and one
low-frequency fire (the Evaluator's Sunday scout duty), which folds accumulated appends into the
YAML. This avoids same-minute Tue/Fri YAML merge conflicts and comment-destroying round-trips.

**Lifecycle:** `candidate` → (first clean anchored citation, automatic bookkeeping) → `probation` →
(≥3 anchored citations across ≥2 editions, ≥14 days, zero source-quality 👎 — **Evaluator proposes,
Rafael applies**) → `established`; reasoned source-quality 👎 ×2 **on distinct stories** (the
noise-filter amendment fixing the double-tap hole) or misattribution → `demoted` → `retired`.
`demoted`/`retired` regenerate `reader-profile/source-weights.yml` deterministically (`reduce:` /
`never:`) — one-way generation with a "GENERATED — do not hand-edit" header. Every trust-bearing
transition stays behind the existing human gate; the n=1 sycophancy guard is untouched.

**Pressure mechanisms (teeth staged — review C5/C6 fix):**
- *Push:* max **2** stories anchored to the same `outlet` domain per edition (hubs exempt —
  forcing AI/ML off arXiv would be mission damage; `institutional` gets a higher 30% saturation
  bar); a domain over 20% of its stream's rolling-30d stories is `saturated` → cap 1.
- *Pull:* per-edition discovery quota (news ≥1, ai-ml ≥1 non-hub, science ≥2, weekend ≥2)
  novel-or-dormant anchor domains, with the waived-but-counted footer escape.
- **Both ship report-only.** By the July numbers, `srf.ch` and `letemps.ch` both trip saturation on
  day one — armed caps would gut the reader's most-upvoted beat (Switzerland) before replacement
  supply exists, and an unmeetable quota normalizes waiving. The revise-loop teeth arm only after
  `candidates_to_try` has been non-empty per stream for 2 consecutive weeks — a data-gated flag
  flip, not a redesign.

**Reachability truth:** deterministic re-probes (curl exit codes, then proxy) maintain `reach:`,
replacing the four prompts' "Confirmed unavailable — do not waste cycles" fossil lists — the
documented tier-inversion vector where reachability, not the declared T1>T2 ranking, decided what
got cited. The feed tables and unavailable-lists are deleted from all four `routines/src/*.md`;
`routines/_shared/feed-first-source-order.md` (the 4×-identical concentrator) shrinks to a
fetch-mechanics note.

**Measurement:** `tools/sources/health.py` → `_data/source-health.json`, regenerated at every
writer Step D **and added to the rebase-retry regenerate list** (review C2 fix). Recalibrated
4-stream targets: top-5 outlet-class share ≤0.50 in 4 weeks (≤0.35 steady); unique domains 30d ≥30
(≥35); new domains/month ≥10 (≥25); waiver rate ≤50% (≤30%).

**Bootstrap** (`registry.py bootstrap`, from the live index): ≥5 citations → `established`, 1–4 →
`probation`, the 7 allowlisted feed hosts get `probe:` blocks — **excluding the retired streams'
domains** (`nvd.nist.gov`, `cisa.gov`, `ecb.europa.eu` are still inside the 40-day window and would
otherwise fossilize the deleted security pipeline into the founding registry), and backfilling
`last_cited` across the full index (review C18 fix).

### 3.5 Feedback + Evaluator as machine-readable state at every fire

**Feedback repair (the review's "single best proposal in either design").**
- The widget (brief include + homefeed cards) submits the anchored store id as `story_id`, with a
  legacy-slug fallback for pre-anchor posts. Worker and `feedback/*.jsonl` schema unchanged.
- **`tools/feedback/fold.py`, bridge-side**, runs after `feedback.py drain`: resolves `story_id`
  (store id directly; legacy slugs via `legacy_ids`), applies last-write-wins, appends
  `ev:"feedback"` to the ledger, sets `consumed: true`. Consumption is keyed on the ledger, not any
  review's 7-day window — **the 27%-orphaning class becomes structurally impossible.** Named
  migration task: fold the 9 orphaned records at `feedback/2026-06.jsonl` lines 23–31.
- `feedback.py drain` also populates the reserved `source_domain` field at drain time (URL-first
  join), wiring reasoned votes into the registry lifecycle.
- A vote adjusts **that thread's** handling as folded fact; preference-level generalization stays
  human-gated through Evaluator proposals, exactly as today.

**Evaluator.**
- `tools/evaluator/metrics.py` → `_data/health.json` computes dimensions A/C/G/I/K/L
  deterministically at fire start; Opus tokens go to judgment and the editorial dimensions the word
  budget currently starves.
- Proposals emitted machine-readable (`proposals/reader-model-{date}.json`,
  `proposals/registry-{date}.yml` patches) alongside the prose review; Rafael's apply script stamps
  `applied: true` — the loop's first-ever verification that a patch landed.
- Self-continuity from its own prior ledger events instead of globbing `_posts/` — a nearly-free
  fix for the 2-of-9 "predecessor not found" failures.
- **Absorbs the source-scout duty** (review C7): a bounded Sunday section — ≤20 proxy fetches —
  vetting primary-source candidates for the worst-deficit stream and re-probing 5 stale `reach:`
  entries. Opus doing Sonnet work 2×-monthly-equivalent costs a few units more than a dedicated
  trigger saves, and eliminates a standing trigger + prompt + collision-grid entry.

### 3.6 Surfacing policy

Steps 1–6: **surfacing is unchanged** — briefs, edition notifications, weekday News email, homefeed
of published stories (now store-id-keyed with per-story anchor permalinks
`/YYYY/MM/DD/{stream}/#st-…`). Homefeed v2 reads the materialized store but **keeps `parse_post()`
as a per-story fallback** for stories lacking a publish event (zero records carry `display_body`
today; a hard cutover would render the 14-day window bodyless — review B14 fix), and **ports the
existing `MIN_LATEST_EDITION` floor logic unchanged** (the "Weekend erased Science" guard).

Step 7, if it ships, adds exactly one lane: **immediate push** for scout-triaged importance-3
stories (`tags:"zap"`, `click` → primary source, Watch-precedent) — behind a **hard shadow-mode
gate**: pushes ship disabled (threshold 99); the Evaluator reports "would-have-pushed" counts from
the ledger for ≥2 weeks; Rafael reviews precision before enabling. Push policy invariants
(`max_per_day`, `thread_cooldown_hours`, quiet hours) are **enforced by `store.py`, not the Haiku
prompt** — it refuses the `ev:"notify"` append, deterministic teeth. `reader-model.json`
(machine-readable topic weights + push thresholds, human-gated, no `source_weights` key, no
duplicated prose preferences) ships only with this step — a config file nothing reads is drift
waiting to happen. It is entirely possible the post-shadow answer is "leave pushes off"; the step
is valuable without them (ledger ingestion feeding writer curation, and round-the-clock scout
commits accidentally fixing the sparse-SHA Pages wedge). The `POST /notify` Worker relay (B7) is
independent of all this and ships in step 6 — it helps today's edition/watch stubs written after
22:00.

## 4. Deterministic tooling vs prompt requests

The dossier's central behavioral finding: prompt exhortations decay (T3 deny-list: 2 reissues;
`Feeds hit` line: landed 1 day in 6; snippet-tagging patch: failed twice). The line is drawn so
that **everything countable or checkable is never asked of a model**:

| Concern | Side | Mechanism | Why |
|---|---|---|---|
| Usage counting, concentration, saturation | deterministic | `health.py` from the index | models miscount; evaluator hand-counting burned its budget and still missed things |
| Caps, discovery quota, `[new source]` tag integrity | deterministic | `lint.py` at Step C.25; hard-fail (report-only until armed) | recomputes novelty/dormancy itself — the model cannot self-certify a known domain as new |
| Ledger integrity (dedupe, ordering, URL-fold) | deterministic | `store.py` invariants + selftest incl. union-merge engagement test | union merge preserves duplicates and guarantees no order |
| Push policy (if step 7) | deterministic | `store.py` refuses violating `ev:"notify"` | fail-loud channel handed to the weakest model — bookkeeping must not be prompt-carried |
| Reachability truth | deterministic | probes → registry `reach:` | fossil lists lagged reality ≥2 cycles |
| `last_cited`, candidate auto-entry | deterministic | `registry.py sync` → append-only jsonl | the consumed-flag orphans show bookkeeping slips |
| Feedback consumption | deterministic | bridge-side `fold.py`, ledger-keyed | window arithmetic lost 27% |
| Evaluator metrics A/C/G/I/K/L | deterministic | `metrics.py` → `_data/health.json` | frees Opus for judgment |
| Story selection, anchoring, tiering judgment, waiver justification | prompt | writer prompts | genuine editorial judgment |
| Whether an ONGOING item carries a materially new fact | prompt | writer prompts (unchanged) | judgment |
| Trust transitions, preference generalization | human gate | Evaluator proposes → Rafael applies | the n=1 sycophancy guard, by design |

**Failure-semantics contract preserved:** a *tool crash* degrades to a Gaps note ("compose the
brief normally — never abort the brief"); a *detected violation* is corrected (max 2 revise loops)
or made permanently visible (`- Diversity: FAILED <rule>` footer, counted and trended).

## 5. Phased migration

Each step independently shippable and reversible; bulletins never break. **Steps 1–6 are repo
commits + one bridge edit — zero RemoteTrigger operations.** Commit gate per repo convention:
stage, commit only on explicit go-ahead, `-c commit.gpgsign=false`, no signature.

**Step 1 — Identity + feedback repair + ledger dual-write.**
*Files:* `tools/store/store.py` (new), `.gitattributes` (new), `dedup.py::cmd_record` dual-write
(legacy files byte-identical AND ledger events with `st-` ids + `legacy_ids`), backfill script over
the 40-day index, per-story anchors (one `routines/_shared/` output-partial edit + `assemble.py`),
feedback widget include + `_layouts/home.html` id submission with legacy fallback,
`tools/feedback/fold.py` wired into `bridge.sh`, fold the 9 orphaned June records.
*Prompt/trigger:* prompt-partial edit only.
*Verify:* `store.py selftest` (sort/dedupe/URL-fold invariants + two-branch union-merge test);
materialize round-trips the current index; legacy index files byte-identical (diff vs `git HEAD`);
a test tap lands as `ev:"feedback"` on the right thread.
*Rollback:* delete the ledger dir; nothing else read it.

**Step 2 — New-source citation rule + fossil-list deletion.**
*Files:* the `[new source]` rule into the shared sourcing partial; delete "Confirmed unavailable"
lists from all four `routines/src/*.md`; report-only lint of the tag. `assemble.py && assemble.py
check` (exit 0).
*Verify:* next fires cite off-list primary sources tagged `[new source]`; watch for junk anchors.
*Rollback:* one revert.

**Step 3 — Registry + preflight + lint + health, teeth staged.**
*Files:* `sources/registry.yml` (bootstrapped, retired-stream domains excluded, `last_cited`
backfilled), `sources/{candidates,last-cited}.jsonl`, `tools/sources/{preflight,lint,health,registry}.py`,
Step C.25 in `DEDUP.md`, `routines/_shared/source-registry.md` replacing `feed-first-source-order.md`
in the include lists (emergency slate included), feed tables stripped from the four srcs, `health.py`
added to the rebase-retry regenerate list, `source-weights.yml` generation.
*Verify:* preflight output sane per stream; lint report-only footers appear; `assemble.py check`;
health.json numbers match an independent recount.

**Step 4 — Evaluator upgrade.**
*Files:* `tools/evaluator/metrics.py`, `routines/weekly-evaluator.md` (edited directly): consume
`health.json` + `source-health.json`, machine-readable proposals + apply script with `applied: true`
stamp, ledger-based self-continuity, source-scout duty section, distinct-stories noise-filter
amendment.
*Verify:* next Sunday run — metrics table matches script output; proposals parse; scout section
stays inside its fetch budget.

**Step 5 — Arm the diversification teeth.** Data-gated flag flip: revise-loop enforcement for
caps + quota once `candidates_to_try` is non-empty per stream for 2 consecutive weeks.
*Verify:* Swiss-desk volume does not drop; waiver rate trends per §3.4 targets.

**Step 6 — Worker `/notify` relay.** `tools/fetch-proxy/` route addition; secrets via
`wrangler secret put` (never in-repo); stub fallback preserved.
*Verify:* a post-22:00 edition stub arrives without waiting for the 07:00 bridge tick.

**Step 7 — CONDITIONAL: continuous ingestion.** Fires only if (a) discovery metrics still lag §3.4
targets with the registry armed, or (b) Rafael explicitly wants intra-day surfacing. Contents, with
all review fixes: fetch-proxy Worker cron + KV queue reading the **registry's probe projection**
(`probe-list.json`, bridge-mirrored to KV — no second manifest), single-blob feedstate (one KV
write per cron invocation; confirm the account's KV plan first — free tier's 1,000 writes/day dies
mid-afternoon under naive per-feed writes), Watch→Scout conversion (**the one RemoteTrigger
update**, protocol per §3.2), cosine thresholds recalibrated for feed-snippet register before any
auto-ack (uncertain band passes through as `candidate` — a false REPEAT is a story silently dropped
forever), pushes shadow-gated, `store.py`-enforced policy, `reader-model.json`, homefeed v2
candidate handling per §3.6, writer store-shortlist step with the fallback lane.
*Rollback:* re-point the shim (repo commit); the trigger needn't be touched again.

## 6. Costs

**Tokens/fires.**
- Steps 1–6: **zero new fires.** Writer per-fire cost ± noise (preflight/lint add tool calls;
  deleted feed-table re-derivation and evaluator hand-counting give some back). Evaluator gains the
  bounded scout section — a few units/wk on the ~1,233-unit baseline (<1%).
- Step 7, honest number (review B16): the Scout at `20 */2` is **~100–170 units/wk (+8–13%)**, not
  the +1.4% originally claimed — 84 Haiku fires with 15–25 tool calls each and context re-sent per
  call. Priced against a latency benefit no reader signal demands, which is exactly why it is
  conditional.

**Maintenance surface.**
- Added (steps 1–6): `store.py`, `fold.py`, ledger dir + archive policy, 4 `tools/sources/*.py`,
  `metrics.py`, registry + 2 append-only jsonl files, 2 bridge duties. Roughly half the combined
  original designs' 12+ components.
- Removed/simplified to pay for it: four per-stream feed tables + four unavailable-lists + the
  shared feed-order partial (the staleness vectors); the Evaluator's hand-computed dimensions;
  hand-maintained `source-weights.yml`; eventually the legacy per-edition index files and the
  homefeed `parse_post()` recovery apparatus (retired at the end, not before publish events cover
  the feed window); the entire class of window-arithmetic feedback bookkeeping.
- Deferred with step 7: Worker RSS parsing across real-world feeds (a genuine standing surface —
  encoding bugs, format drift), KV queue ops, scout prompt.

## 7. Considered and rejected

| Proposal | Verdict | One-line reason |
|---|---|---|
| **Sub-day latency as the design goal** | KILL (reframed) | Zero reader signal demands it — no timeliness complaint in 9 evaluator reviews or 40 feedback records; the Khamenei 👎 was date-anchoring, not staleness; 31/33 signals upvote the bulletins as they are. |
| **Homepage `candidate` cards ("spotted")** | KILL | Machine-selected unverified headlines linking out = an RSS reader — aggregator-shape output, which the mission defines as failure; the Watch precedent covers user-authored queries, not the pipeline's own unvetted picks. |
| **Update re-push lane** | KILL for now | Highest false-positive class (Haiku judging "materially new fact" from a snippet), zero evidenced demand; revisit only if immediate push graduates from shadow mode. |
| **Dedicated Sonnet source-scout RemoteTrigger** (Mon+Thu) | KILL as trigger | Trigger creation is the pipeline's highest-risk, least-reversible operation (the `outcomes` trap, create-shape iterations); the job fits inside the Evaluator's existing Sunday fire for a few units more. |
| **`feeds.yml` as a separate feed manifest** | KILL | A second source-of-truth beside the registry's `probe:` blocks would drift; "add a source" must have exactly one home. |
| **Date-prefixed story id `st-{YYYYMMDD}-{hash}`** | KILL (fixed) | Breaks its own determinism claim: concurrent actors across a date/stale-pull boundary mint two ids for one story; the URL-pure id collapses the race. |
| **HTML diff-polling of feed-less lab blogs** | KILL | Non-deterministic HTML (nonces, ad slots) fires on every fetch, flooding the queue with noise Haiku pays to dismiss; feed-less beats stay with the writers' deepening pass. |
| **`reader-model.json` `source_weights` key + duplicated `preferences` prose** | KILL (trimmed) | The registry lifecycle owns source weights (auditable, sub-domain-capable); preferences must not live in three dual-authored places. |
| **Immediate arming of caps + discovery quota** | REJECTED as sequenced | `srf.ch`/`letemps.ch` both trip saturation on day one — armed caps would gut the most-upvoted beat before candidate supply exists; ship report-only, arm data-gated. |
| **Hard cutover of homefeed v2 / deleting `parse_post()` early** | REJECTED as sequenced | Zero records carry `display_body` today; cutover before publish events cover the 14-day window visibly degrades the homepage. |
| **Auto-suppression of downvoted-thread re-pushes as "fact-level"** | REJECTED | "Safe to automate" is the line that widens; if push ever ships, suppression goes through the gated `reader-model.json` path. |
| **Widening the env_018 egress allowlist** | DEFERRED | fetch-proxy already gives universal reach; env changes are awkward out-of-band admin — revisit only if proxy volume becomes a concern. |

## 8. Open questions for Rafael

1. **Do you want intra-day surfacing at all?** Nothing in your recorded feedback asks for it. Step 7
   exists behind that question — if the answer is "the bulletins are the product," it never fires
   and the design is complete at step 6.
2. **Report-only period for the diversification teeth:** is 2 consecutive weeks of non-empty
   `candidates_to_try` the right arming gate, or do you want to flip it manually?
3. **Paywalled T1** (`nzz.ch` 402, `ft.com`, Reuters): fund subscriptions, or accept snippet-tier
   for these outlets permanently? The registry can represent either (`reach: blocked-paywall`); the
   money question is yours.
4. **Evaluator scope creep:** absorbing the source-scout duty adds a bounded section to its Sunday
   fire. If its reviews start starving the editorial dimensions again, the fallback is a dedicated
   trigger (the rejected C7) — flag it if you see the word budget suffering.
5. **Discovery-quota calibration** (news ≥1, ai-ml ≥1 non-hub, science ≥2, weekend ≥2; waiver
   target ≤50%): first-guess values sized against the July histogram — recalibrate from 4 weeks of
   `discovery_quota_compliance` / `waiver_rate` data. The metrics exist so this is a data decision
   next month, not a debate.
6. **Cloudflare plan check (blocks step 7 only):** confirm whether the account is Workers Free
   (1,000 KV writes/day — insufficient under naive per-feed state) or Paid before any poller work.
7. **RemoteTrigger cron floor (step 7 only):** nothing has ever fired tighter than 4h; `20 */2`
   must be validated empirically after the conversion. Degradation at a 4h platform floor is
   graceful.
8. ~~**Concentration recount.**~~ **Resolved 2026-07-07** — recomputed deterministically from
   `index/stories/*.jsonl`, live streams only (news/ai-ml/science/weekend): July = 99 stories,
   **21 unique domains, 7 first-seen, top-5 share 73.7%**; June = 316 stories, 94 unique, 75
   first-seen. Map 3's figures confirmed (±1 on new-domain count, method noise). §3.4 targets can
   be calibrated against these numbers as-is.
