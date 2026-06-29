# News Brief Pipeline — Architecture

> Written 2026-05-25; §3–§7 status updated 2026-06-22. §1 (current state) is read from live trigger
> configs, `bridge.sh`, the user crontab, `_config.yml`, and `_includes/head/custom.html` — not
> inferred. The two-plane design in §3–§7 is now **partially built**: **Phase 1 — the compose-time
> embeddings dedup (online plane)** is LIVE (`tools/dedup/dedup.py`, the `embed-proxy` Worker, the
> in-repo `index/stories/` index; calibrated 2026-05-31). **Phase 2 — the local pgvector analytical
> plane + S3 datalake** is NOT yet built and remains the target. Most §7 open questions are now
> RESOLVED (marked inline).

---

## 1. Current state (verified)

### 1.1 Components & data flow

```
╔════════════════════════════ ANTHROPIC CLOUD (routines) ════════════════════════════╗
║                                                                                      ║
║  env_018zypSdRSdGdrZ8J5usqCWA   (network settings changed 2026-05-25 → Custom)        ║
║  ┌────────────────────────────────────────────────────────────────────────────┐     ║
║  │ WRITERS (claude-opus-4-8)      cron (UTC)        output file          email     │    ║
║  │  • News (CH + world, eve)     0 17 * * *     _posts/{d}-news.md       weekday    │   ║
║  │  • AI/ML (+ arXiv papers)     0 10 * * 2,5   _posts/{d}-ai-ml.md      none       │   ║
║  │  • Science (non-AI, weekly)   0 15 * * 3     _posts/{d}-science.md    none       │   ║
║  │  • Weekend Deep Read          30 7 * * 6     _posts/{d}-weekend.md    digest     │   ║
║  │  WATCH (claude-haiku-4-5)     0 */4 * * *    pending-notifications/   —          │   ║
║  │      reads watches.yml → on match writes stub + updates last_fired              │    ║
║  │  EVALUATOR (claude-opus-4-8)  30 9 * * 0     _posts/{d}-evaluator.md  digest     │   ║
║  │  ⮑ all triggers (except Watch) are BOOTSTRAP SHIMS → git pull + read              │   ║
║  │     routines/<slug>.md at fire time (see routines/MANIFEST.md)                    │   ║
║  │      reads last 7d of _posts → Health table + Patch proposals (human-applied)   │    ║
║  └────────────────────────────────────────────────────────────────────────────┘     ║
║   MCP legend: D=Google-Drive  H=Hugging-Face  G=Gmail  Cal=Google-Calendar            ║
╚═══════════════════════════════════════╤══════════════════════════════════════════════╝
   per run: clone → git pull → WebSearch/curl/WebFetch + MCP → Write → commit → push main
                                         │   (+ Gmail create_draft → DRAFTS, never auto-sent)
                                         ▼
            ┌─────────────────────────────────────────────────────┐
            │  GitHub: khalic-lab/claude-routines (private)         │
            │  main = single source of truth                        │
            │  _posts/*.md · pending-notifications/*.json ·         │
            │  watches.yml · briefs/* (LEGACY May2-4, dead)         │
            └───────┬──────────────────────────────────┬───────────┘
          Pages build│                                   │ pull --rebase / commit / push
                     ▼                                   ▼
   ┌──────────────────────────────────┐   ┌──────────────────────────────────────────────┐
   │ GitHub Pages — Jekyll             │   │ LOCAL Mac                                      │
   │  minimal-mistakes (dark)          │   │  crontab: */10 7-22 * * *  bridge.sh           │
   │  khalic-lab.github.io/            │   │   1 git pull --rebase                          │
   │     claude-routines               │   │   2 each pending-notifications/*.json →        │
   │  permalink /:y/:m/:d/:title/      │   │       curl -d body  $NTFY_SERVER/$NTFY_TOPIC   │
   └──────────┬────────────────────────┘   │   3 git rm drained + commit "Drained N"        │
              │ browser                     │   4 push if ahead                              │
              ▼                             │  creds: store --file=git-credentials (600)     │
   ┌──────────────────────────────────┐   └───────────────────┬────────────────────────────┘
   │ custom.html JS (client-side)      │                       │ HTTP POST
   │  link → og-proxy worker →         │                       ▼
   │  og:image thumbnail;              │              ┌─────────────┐     ┌──────────────┐
   │  arxiv→PDF chip; else favicon;    │              │  ntfy.sh     │────▶│ phone (ntfy)  │
   │  sessionStorage cache             │              │  topic khalic│push └──────────────┘
   └──────────┬────────────────────────┘             └─────────────┘
              ▼                                        ┌────────────────────────────────────┐
   ┌──────────────────────────────────┐               │ Gmail (DRAFTS → rflnogueira@me.com)  │
   │ Cloudflare Worker (og-proxy)      │               │  evening digest + weekly review;     │
   │  fetch article HTML → og:image    │               │  user sends manually                 │
   │  30-day edge cache                │               └────────────────────────────────────┘
   └──────────────────────────────────┘
```

> **Removed 2026-06-18:** the dedicated Markets routine and all market content. The Markets
> routine (was `trig_01GBugAS5qw88yQK3tv8kKWx`, cron `30 18 * * 1-5`) had been disabled since
> 2026-05-30; on 2026-06-18 the Morning Overview's pre-open market snapshot section was dropped
> too, and the dedup snapshot-genre collapse machinery removed — so **no brief emits market
> content**. The consolidated evening email covers three streams (World/Switzerland, AI/ML,
> Cyber+Papers). Published May market briefs are kept as a frozen archive; the disabled trigger
> config is retained server-side (the RemoteTrigger API exposes no delete).

> **Redesigned 2026-06-29 (cadence + topics — `docs/SPIKE-2026-06-29-cadence-redesign.md`).** Replaced the
> old daily Overview + Cyber+Papers + AI/ML cadence with the per-topic lineup above: **News** (daily evening,
> CH+world — retargets the Morning Overview trigger), **AI/ML** (Tue+Fri midday, now also carries ALL arXiv
> ML papers + author affiliations), **Science** (NEW weekly Wed, non-AI science — retargets the Cyber+Papers
> trigger), **Weekend** (now the in-depth weekly revisit; dedup scoped to its own slug via `--only-slug`).
> **Security/cyber dropped pipeline-wide; the consolidated evening email is gone** (News = News-only weekday
> email; AI/ML + Science = none; Weekend keeps its digest). Trigger IDs are REUSED (no delete API); the
> `overview`/`cyber-papers` slugs are retired (old posts + index files kept as archive). **Triggers now run
> BOOTSTRAP SHIMS** (except Watch) that `git pull` + read `routines/<slug>.md` at fire time — so prompt edits
> are repo-only, no RemoteTrigger mirror (see `routines/MANIFEST.md` + CLAUDE.md "Editing a routine").
> Affiliations: Semantic Scholar `authors.affiliations` on AI/ML, Science, Weekend paper items.

> **Changed 2026-05-30:** Per-routine model tiers split by job (see `docs/SPIKE-model-tiering.md`):
> **writing** — the 4 writers (Overview, AI/ML, Cyber+Papers, Weekend) moved
> `claude-sonnet-4-6` → `claude-opus-4-8` (latest Opus) for reader-facing quality;
> **analysis** — the Weekly Evaluator moved `claude-opus-4-7` → `claude-opus-4-8` (weekly QA backstop);
> **polling** — Watch moved `claude-sonnet-4-6` → `claude-haiku-4-5` (high-frequency,
> mechanical snippet judgment — does not write or analyze briefs). Same date: the
> pedagogical-tone block's "hardest case" rule was tightened — pure-math / hep-th / quant-ph
> results must now be explained (stakes + concrete anchor + honest scope), not flagged-and-skipped.

### 1.2 Data model (what lives where)

| Artifact | Location | Shape | Producer → Consumer |
|---|---|---|---|
| Brief | `_posts/{YYYY-MM-DD}-{slug}.md` | front-matter (`layout,title,date,categories`) + body + Coverage footer | writer → Jekyll + Evaluator |
| Notification stub | `pending-notifications/{ts}-{slug}.json` | `{title, click, body, tags}` | writer/watch → bridge (then deleted) |
| Watch registry | `watches.yml` | `[{id, query, match_when, cooldown_days, last_fired}]` | user + Watch (writes `last_fired`) |
| Bridge config | `/usr/local/src/news-brief-ntfy-bridge/.env` | `NTFY_TOPIC, NTFY_SERVER, REPO, FEEDBACK_WORKER_URL, FEEDBACK_TOKEN` | bridge.sh |
| Git creds | `…/git-credentials` (mode 600) | `https://x-access-token:<tok>@github.com` | bridge git push |
| Legacy briefs | `briefs/{stream}/{date}.md` | pre-Pages layout, **only May 2–4, orphaned** | nothing — dead weight |
| Coverage footer | inside each brief | `Direct fetches: N \| via-snippet: M`, `Feeds hit`, `Gaps` | **the only health signal** |
| Reader feedback | `feedback/{YYYY-MM}.jsonl` | `{id, ts, reader, brief, story_id, vote±1, reason, surface, source_domain, consumed}` | widget→Worker→bridge → Evaluator |
| Reader profile | `reader-profile.md` + `reader-profile/source-weights.yml` (`never:`/`reduce:`) | NL editorial brief + domain lists | Evaluator proposes (human-gated) → writers read |

### 1.3 Dedup today

The compose-time embeddings dedup (`tools/dedup/dedup.py` + the `embed-proxy` Worker + the in-repo
`index/stories/*.jsonl`) is **live**: each writer embeds its candidate stories, compares them against
the recent index, and drops/threads repeats. See §3–§6 for the design and §6 for the verdict logic
+ calibration.

This superseded the **original** mechanism — a same-day, same-stream-pair, arXiv-ID-only
exact-string exclusion in the Cyber+Papers prompt ("read today's Overview brief, exclude any arXiv
IDs it already cited"). That spanned no days, no other streams, and matched only arXiv IDs (not
*stories*), which is why "Bilaterals III" ran every few days from May 3 → May 24 untouched.

### 1.4 Reader feedback loop (LIVE 2026-06-18)

Human-gated, web-widget-only, per-brief v1. Captures 👍/👎 + an optional free-text reason
and folds it into the writers' editorial guidance **through a human gate** (never auto-mutated
from a tap — the documented n=1 sycophancy trap).

```
brief page widget (_includes/head/custom.html, FEEDBACK_ENABLED=true)
  │  POST /submit (CORS, public)
  ▼
feedback-sink Worker (tools/feedback-sink/) ── Cloudflare KV   [khalic-lab CF acct;
  │                                                             bearer FEEDBACK_TOKEN on /drain+/ack]
  ▼  bridge tick: drain (GET /drain) → feedback/{YYYY-MM}.jsonl, commit, push, then ack (POST /ack)
GitHub main  ──┬─ RAW ungated: feedback/*.jsonl (append-only, dedup by id)
               │
               ├─ Weekly Evaluator: reads last 7d feedback → PROPOSES patches to
               │     reader-profile.md / source-weights.yml (Patch-proposals section); flips
               │     consumed:true. ◀── HUMAN GATE (Rafael applies)
               └─ Writers (Overview/AI-ML/Cyber/Weekend): read reader-profile.md +
                     source-weights.yml at compose time (favor/demote; never:/reduce:).
```

- **Worker:** `https://feedback-sink.khalic-lab.workers.dev` — `/submit` public (shape-capped,
  no bearer: a browser can't keep one), `/drain`+`/ack` bearer-gated (two-phase delete-on-ack so a
  missed bridge tick neither loses nor double-commits). Not on the env_018 allowlist — it's called
  by the *browser* and the *Mac bridge*, never the routine sandbox.
- **Bridge:** `feedback.py drain` before commit (rides the "Drained N" commit), `ack` after push.
  `feedback.py` sends an identifiable User-Agent — Cloudflare 403s the default `Python-urllib` UA.
- **Privacy:** reason text routes through the private Worker + private repo, never an ntfy topic.

**The dedup check must run inside the cloud sandbox, at compose time.** That is the only
moment a writer can decide "skip this story / thread it as ongoing." And the cloud sandbox:

- is **ephemeral** (no local disk persists between runs),
- has **HTTP/HTTPS egress only, through an allowlist proxy** (no raw TCP → no Postgres wire on :5432),
- can reach: the **git repo**, **allowlisted HTTPS hosts**, and its **MCP connectors**.

⇒ **A pgvector instance on the Mac is unreachable from the sandbox at compose time.**
`localhost` isn't routable from the cloud, and even a hosted Postgres needs its wire
protocol, which the HTTP proxy blocks. So the compute-time index must be one of:
**(a) the git repo, (b) an allowlisted HTTPS object store / API, or (c) an allowlisted HTTPS service.**

This does **not** kill the pgvector idea — it relocates it. See §3.

**Fetch-path quirk (why writers curl before WebFetch).** Inside the sandbox `WebFetch` 403s on
public feeds it should reach (arXiv RSS, Nature, …), while `Bash{curl -fsSL}` egresses
through a different path and usually succeeds. A 2026-05-03 audit found 0/18 direct fetches in a
Morning Overview run under HTML-first sourcing; the pipeline pivoted to **feed-first** (machine-
readable RSS/JSON on separate infra) and **curl-before-WebFetch**. The per-brief Coverage footer
(`Direct fetches: N | via-snippet: M`, `Feeds hit: {ok via curl | ok via WebFetch | fail — HTTP NNN}`)
is the only signal this still works — if curl *also* starts failing, the egress proxy is the wall.

**Fetch proxy (added 2026-06-18) — the real 403 fix.** The bulk of the chronic 403s (lab blogs,
CNBC/TechCrunch/Bloomberg/Fortune, etc.) were NOT the WebFetch quirk and NOT anti-bot — they were
simply hosts **not on the env_018 allowlist** (only the ~11 feed hosts in §7.1 are). The fix is
`tools/fetch-proxy/` — a Cloudflare Worker (`https://fetch-proxy.khalic-lab.workers.dev`, twin of
og-proxy/embed-proxy, bearer-gated) that fetches any public URL from Cloudflare's edge with a real
browser User-Agent. The sandbox reaches **one** allowlisted host (the worker) instead of enumerating
fifty news/lab domains, and the browser-UA-from-edge bypasses the datacenter-IP anti-bot 403s on
Cloudflare/Akamai-fronted sites. All 4 writers route non-allowlisted hosts through it (direct curl
stays for the feed hosts; arXiv stays direct per its rate-limit ask). The proxy mirrors upstream
status, so `curl -fsSL` keeps fail→snippet semantics; footers mark proxied fetches `{ok via proxy}`.
Hard Cloudflare Bot-Management / JS-challenge sites can still block even the proxy.

---

## 3. Target: two-plane hybrid

> **Status (2026-06-22):** Phase 1 — the online-plane compose-time dedup below — is **BUILT and
> LIVE** (`tools/dedup/dedup.py`, `embed-proxy`, `index/stories/`). The analytical plane (local
> pgvector + S3 datalake — the right-hand side here and §5.2) is **Phase 2, not built**. This
> resolves the §7 store/provider questions: store = **in-repo `index/stories/`** (option B);
> embeddings = **Workers-AI `bge-m3`** via the `embed-proxy` Worker.

Split the system into an **online plane** (compute-time, cloud, must be allowlisted) and an
**analytical plane** (offline, local Mac, where pgvector lives and gives the "superpowers").
The datalake (S3) is the seam between them.

```
                         ┌──────────────── ONLINE PLANE (cloud sandbox) ─────────────────┐
   writer routine ──┐    │  compose-time dedup:                                            │
   (after feed      │    │   1 assemble candidate stories (headline+summary+url+date)      │
    sweep)          ├───▶│   2 embed candidates  ───────────────▶ [EMBEDDINGS API]  (§4)   │
                    │    │   3 pull recent index slice (last N days) ◀── S3 / repo (§3.1)  │
                    │    │   4 cosine-sim candidates vs recent vectors                      │
                    │    │   5 tag: NEW | REPEAT(skip) | ONGOING(thread to first-seen)      │
                    │    │   6 compose brief; append new story-items + vectors back ───┐    │
                    └────┤                                                              │    │
                         └──────────────────────────────────────────────────────────┬─┴────┘
                                                                                      ▼
                                       ┌─────────────────────────────────────────────────────┐
                                       │  S3 DATALAKE  (the seam — allowlisted HTTPS)          │
                                       │   raw/briefs/{date}/{slug}.md      ← archived briefs   │
                                       │   stories/{date}/{slug}.jsonl      ← decomposed items  │
                                       │   index/embeddings.parquet         ← vectors + meta     │
                                       │   index/manifest.json              ← model ver, dims    │
                                       └───────────────────────────┬─────────────────────────┘
                                                                    │ sync (pull new partitions)
                          ┌──────────────── ANALYTICAL PLANE (local Mac) ─────────┴───────────┐
                          │  cron sync job (extend bridge, or new timer):                     │
                          │   load stories + embeddings → Postgres + pgvector                  │
                          │                                                                    │
                          │  SUPERPOWERS (local, fast, rich SQL + vector):                     │
                          │   • semantic search  "everything on Iran/Hormuz"                   │
                          │   • story threading  (cluster by cosine, order by date)            │
                          │   • coverage analytics → feed the Evaluator a real DB, not grep    │
                          │   • source/citation graph, tier/lang distribution over time        │
                          └────────────────────────────────────────────────────────────────┘
```

Key property: **embeddings are computed once** (online, at ingest) and stored in the parquet
index; the local plane just *loads* them into pgvector. No double-embedding, no drift.

### 3.1 Where the compute-time index lives — RESOLVED → B (§7 Q2)

> **RESOLVED (2026-06-22):** built on **option B** — the in-repo `index/stories/*.jsonl`. The A/B/C
> trade-offs below are retained as the original rationale; **A (S3) is the Phase-2 migration path**.

| Option | Cloud-reachable via | Pros | Cons |
|---|---|---|---|
| **A. S3 parquet** (matches your ask) | `*.amazonaws.com` (HTTPS) | scales, cheap, decouples from repo, natural datalake | needs AWS creds in env + allowlist; concurrent-write care |
| **B. In-repo embeddings file** (`index/embeddings.parquet` committed) | git (already allowlisted) | zero external infra, versioned, deterministic, free | repo grows (~few MB/yr at this volume); rebase contention on the file |
| **C. Hosted vector service behind a Worker** (e.g. a CF Worker fronting an index) | `*.workers.dev` | reuses og-proxy infra, no AWS | another service to run; cold-start |

Recommendation to debate: **B for v1** (simplest, deterministic, no new creds — get dedup
working), **migrate to A** once the datalake/analytics value is wanted. The two aren't
exclusive: the repo file can be mirrored to S3 by the local sync job.

---

## 4. Embeddings provider — RESOLVED → Workers-AI bge-m3 (§7 Q3)

> **RESOLVED (2026-06-22):** the pipeline uses **Workers-AI `@cf/baai/bge-m3`** (1024-dim) via the
> `embed-proxy` Worker — the table's middle row. Voyage / LLM-judgment were considered, not adopted.

The routines' existing **Hugging-Face MCP does NOT expose an embeddings endpoint** (it's
hub/papers/spaces queries). So compute-time embeddings need one of:

| Provider | Sandbox reach | Notes |
|---|---|---|
| **Voyage AI** (`api.voyageai.com`, `voyage-3`) | allowlist + API key in env | Anthropic-recommended; best retrieval quality; ~1024-dim |
| **Cloudflare Worker + Workers AI** (`@cf/baai/bge-*`) | `*.workers.dev` | reuses og-proxy pattern; cheap/free tier; one endpoint to own |
| **No cloud embeddings → LLM-judgment dedup** | none | writer pulls a *text* manifest of recent headlines and judges "already covered?" itself. Embeddings then live **only** in the local pgvector plane for search/analytics. Simplest cloud path; slightly less deterministic than a cosine threshold |

The third row is worth real consideration: it keeps the cloud side dead-simple (just a JSON
manifest of recent stories in the repo) and confines all embedding/vector machinery to the
local pgvector plane the user explicitly wants. Dedup precision at compose time comes from
the model's judgment over ~a few hundred recent headlines rather than a similarity score.

---

## 5. Schemas

### 5.1 Story item (the dedup unit) — `stories/{date}/{slug}.jsonl`, one per line

```json
{
  "id": "2026-05-24-cyber-bilaterals-iii",
  "date": "2026-05-24",
  "stream": "cyber-papers",
  "headline": "Federal Council publishes Bilaterals III ratification roadmap",
  "summary": "One-sentence neutral summary used for embedding + dedup.",
  "url": "https://...",
  "source_domain": "admin.ch",
  "tier": "T1",
  "tags": ["switzerland"],
  "thread_id": "bilaterals-iii",          // assigned when matched to a prior story
  "first_seen_date": "2026-05-03",          // earliest member of the thread (first COVERAGE)
  "event_date": "2026-05-02",               // when the event HAPPENED (nullable; ISO 8601 reduced
                                            //   precision YYYY|YYYY-MM|YYYY-MM-DD). Distinct from
                                            //   `date` (compose) and `first_seen_date` (coverage).
  "embedding_model": "bge-m3",
  "embedding": [0.01, -0.04, ...]           // omitted from jsonl if stored in parquet
}
```

### 5.2 Local pgvector

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE stories (
  id              text PRIMARY KEY,
  date            date NOT NULL,
  stream          text NOT NULL,
  headline        text NOT NULL,
  summary         text NOT NULL,
  url             text,
  source_domain   text,
  tier            text,
  tags            text[],
  thread_id       text,
  first_seen_date date,
  event_date      date,        -- when the event happened (nullable); != date/first_seen_date
  embedding       vector(1024)
);
CREATE INDEX ON stories USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON stories (date);
CREATE INDEX ON stories (thread_id);
```

---

## 6. Compose-time sequence (BUILT — `tools/dedup/dedup.py`)

```
writer fires
  ├─ git pull --ff-only
  ├─ feed sweep (egress now fixed) → candidate stories
  ├─ embed candidates                         [§4 provider]
  ├─ load recent index slice (last N days)    [§3.1 store]
  ├─ for each candidate:
  │     sim = max cosine vs recent vectors
  │     sim ≥ T_high → REPEAT  → skip, or one-line "[ongoing since {first_seen}]"
  │     T_low ≤ sim < T_high → ONGOING → thread_id = matched, write update framing
  │     sim < T_low → NEW → fresh thread_id
  ├─ compose _posts/{d}-{slug}.md (no dupes; ongoing stories threaded)
  ├─ write pending-notifications/{ts}-{slug}.json
  ├─ append new story-items + vectors to index store
  └─ git commit && push
        ↓ (later, local)
local sync cron → pull new partitions → upsert into pgvector
```

`check` decides in precedence order (see `decide_verdict`): **(1)** deterministic exact-source
match — same canonical URL or arXiv id as a recent story → REPEAT, cosine-independent; **(2)** cosine
vs the recent index → REPEAT/ONGOING/NEW. (A third snapshot-genre collapse layer, which dropped
recurring FX/index/session market snapshots, was removed 2026-06-18 with the Markets stream.)

`T_high`/`T_low` **calibrated 2026-05-31** against a 485-pair hand-labelled gold set: `T_high=0.945`,
`T_low=0.72`. Key finding: **cosine does not separate "same story restated" (REPEAT) from "same story
with a real update" (ONGOING)** — they overlap across 0.6–0.95 — so the cosine threshold alone catches
almost no reruns. Repeat-suppression therefore rests on the **deterministic (1) exact-source layer** (offline-replay:
78 cross-day reruns auto-dropped vs 6 cosine-only, `exact-url` dominating) **plus** the `DEDUP.md` Step-B
ONGOING-defaults-to-drop policy (writer judgment). Thread auto-linking in `record` is gated separately
at `AUTOLINK_MIN=0.93`, above the observed 0.914 DISTINCT ceiling, to avoid false merges. See
`tools/dedup/dedup.py`, `tools/dedup/test_dedup_calibration.py`, and `docs/archive/DEDUP-DIAGNOSIS-2026-05-31.md`.

**Added 2026-06-08 (see `docs/archive/REVIEW-2026-06-08-feedback-and-dates.md`).** Threading now also has an
**arXiv distinct-paper guard** (`_distinct_paper`): a candidate carrying an arXiv id the match is not
about is not threaded to it. It runs in three places — `cmd_record` **validates writer-supplied
`thread_id`s** (the load-bearing fix: the 2026-06-06 SASA "[ongoing since 2026-05-14]" was a *writer
hand-set* thread onto a distinct paper — cosine was only 0.71, so autolink never saw it), `autolink`
applies it as defense-in-depth, and `check`/`decide_verdict` strips the misleading continuation
(`continuation:false`, `first_seen_date:null`, `match_reason:distinct-paper`) so a writer is handed no
since-date. Restricted to arXiv (CVE/product sagas are left to editorial judgment); offline replay
confirms it touches exactly 2 historical index records. A new nullable **`event_date`** field records
when the event happened (deterministic `YYYY-MM` from arXiv ids, else writer-supplied day precision,
else null) — the date `[ongoing since]` should bind to. For a **scheduled** event (a future,
fixed date — vote/IPO/conference, detected as `event_date` after the thread's first coverage),
`record` **carries `event_date` forward** along the thread so later briefs read it instead of
re-deriving (the fix for the 2026-06-06 "vote this weekend" misdating — the 14-June vote was put on
"Sunday 7 June" twice). A `lint` subcommand flags adjacent weekday-vs-date slips (hard) and bare
relative framing of a dated event with no absolute date nearby — "votes this weekend" / "vote
tomorrow" (advisory). All deterministic + offline.

---

## 7. Open questions / preconditions (Phase 1 items RESOLVED — see inline)

1. **env_018 allowlist contents — RESOLVED (2026-06-18).** The Custom allowed-domains list is:
   `export.arxiv.org`, `services.nvd.nist.gov`, `www.cisa.gov`, `www.quantamagazine.org`,
   `embed-proxy.khalic-lab.workers.dev`, `www.nature.com`, `www.aljazeera.com`, `www.ecb.europa.eu`
   (now dead — markets removed; safe to drop), `api.semanticscholar.org`, `www.srf.ch`,
   `www.letemps.ch`, plus `fetch-proxy.khalic-lab.workers.dev` (added 2026-06-18). The chronic AI/ML
   403s were this list not covering lab/news hosts — now solved via the fetch-proxy (§2) rather than
   by enumerating every domain.
2. **Compute-time index store — RESOLVED (2026-06-22): option B**, the in-repo
   `index/stories/*.jsonl`; A (S3) is the Phase-2 migration path. §3.1.
3. **Embeddings provider — RESOLVED (2026-06-22): Workers-AI `@cf/baai/bge-m3`** (1024-dim) via the
   `embed-proxy` Worker. Voyage / LLM-judgment were considered but not adopted. §4.
4. **Evaluator env migration — RESOLVED (2026-05-30).** The Weekly Evaluator now runs on
   env_018 (model `claude-opus-4-8` as of 2026-05-30), alongside the writers + Watch. Its Sunday
   link-health probes run under the same network settings; the env_011 loose end is closed.
5. **Story decomposition: who writes the `stories/*.jsonl`?** Either the writer emits it as
   a side artifact during compose, or a post-commit job parses the markdown brief into
   story items. Former is cleaner (writer knows the structure); latter decouples but must
   re-parse prose.
6. **Backfill.** ~50 existing briefs in `_posts/` can be decomposed + embedded once to seed
   the index and the labeled dedup test set.

---

## 8. Out of scope (explicitly deferred)

- Closing the Evaluator loop (auto-PR of patches) — separate track.
- Migrating the legacy `briefs/` dir — it's dead; delete or ignore, not part of this.
- Replacing ntfy / Gmail-draft delivery — unchanged by this design.
