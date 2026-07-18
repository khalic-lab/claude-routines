# News Brief Pipeline — Architecture

> Written 2026-05-25; §3–§7 status updated 2026-06-22. §1 (current state) is read from live trigger
> configs, `bridge.sh`, the user crontab, `_config.yml`, and `_includes/head/custom.html` — not
> inferred. The two-plane design in §3–§7 is now **partially built**: **Phase 1 — the compose-time
> embeddings dedup (online plane)** is LIVE (`tools/dedup/dedup.py`, the `embed-proxy` Worker, the
> in-repo `index/stories/` index; calibrated 2026-05-31). **Phase 2 — the analytical plane — is
> BUILT (2026-07-18: `tools/plane/query.py`, SERVERLESS — the ledger is the database, folded
> in-process; supersedes the §5.2 pgvector sketch)**; the S3 datalake half remains unbuilt and
> optional. Most §7 open questions are now RESOLVED (marked inline).

---

## 1. Current state (verified)

### 1.1 Components & data flow

```
╔════════════════════════════ ANTHROPIC CLOUD (routines) ════════════════════════════╗
║                                                                                      ║
║  env_018zypSdRSdGdrZ8J5usqCWA   (network settings changed 2026-05-25 → Custom)        ║
║  ┌────────────────────────────────────────────────────────────────────────────┐     ║
║  │ WRITERS (claude-opus-4-8)      cron (UTC)        output file          email     │    ║
║  │  • News (CH + world, noon)    0 10 * * *     _posts/{d}-news.md       weekday    │   ║
║  │  • AI/ML (+ arXiv papers)     0 10 * * 2,5   _posts/{d}-ai-ml.md      none       │   ║
║  │  • Science (non-AI, weekly)   0 15 * * 3     _posts/{d}-science.md    none       │   ║
║  │  • Weekend Deep Read          30 7 * * 6     _posts/{d}-weekend.md    digest     │   ║
║  │  • Sports (Swiss+global)      0 7 * * 1      _posts/{d}-sports.md     none       │   ║
║  │  WATCH (claude-haiku-4-5)     0 */4 * * *    pending-notifications/   —          │   ║
║  │      reads watches.yml → on match writes stub + updates last_fired              │    ║
║  │  EVALUATOR (claude-opus-4-8)  30 9 * * 0     _posts/{d}-evaluator.md  digest     │   ║
║  │  ⮑ all triggers (except Watch) are BOOTSTRAP SHIMS → git pull + read              │   ║
║  │     routines/<slug>.md at fire time (see routines/MANIFEST.md)                    │   ║
║  │      reads last 7d of _posts → Health table + Patch proposals (human-applied)   │    ║
║  └────────────────────────────────────────────────────────────────────────────┘     ║
╚═══════════════════════════════════════╤══════════════════════════════════════════════╝
   per run: clone → git pull → WebSearch/curl/WebFetch + MCP → Write → commit → push main
                                         │   (+ Gmail create_draft → DRAFTS, never auto-sent)
                                         ▼
            ┌─────────────────────────────────────────────────────┐
            │  GitHub: khalic-lab/claude-routines (private)         │
            │  main = single source of truth                        │
            │  _posts/*.md · pending-notifications/*.json ·         │
            │  watches.yml · feedback/*.jsonl · index/              │
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
              │ browser                     │   4 push if ahead / Pages self-heal            │
              ▼                             │  creds: store --file=git-credentials (600)     │
   ┌──────────────────────────────────┐   └───────────────────┬────────────────────────────┘
   │ home.html JS (homepage cards)     │                       │ HTTP POST
   │  card → og-proxy worker →         │                       ▼
   │  og:image thumbnail (lazy,        │              ┌─────────────┐     ┌──────────────┐
   │  sessionStorage cache); custom.   │              │  ntfy.sh     │────▶│ phone (ntfy)  │
   │  html = skin + unlock + propose   │              │  topic khalic│push └──────────────┘
   └──────────┬────────────────────────┘             └─────────────┘
              ▼                                        ┌────────────────────────────────────┐
   ┌──────────────────────────────────┐               │ Gmail (DRAFTS → rflnogueira@me.com)  │
   │ Cloudflare Worker (og-proxy)      │               │  News weekday + Weekend/Eval digests │
   │  fetch article HTML → og:image    │               │  user sends manually                 │
   │  30-day edge cache                │               └────────────────────────────────────┘
   └──────────────────────────────────┘
```

> **Fixed 2026-07-18 (night, latest): editorial sections restored to the homepage.** Retiring
> the brief pages orphaned the briefs' SECTION-level synthesis prose — Weekend's "Cross-cutting
> threads" and the Science/Sports "Why it matters" roundups are not per-story content, so the
> homefeed never carried them and they became unreachable anywhere on the site.
> `build_stories_feed.py` now extracts those sections (heading-matched, emoji/hyphen-tolerant;
> latest edition per stream, ≤3, sanitized inline HTML — links/bold/em rebuilt from escaped
> text) into `feed.editorials`; the homepage renders them as 2-col **Editorial** cards (panel
> background, inverted chip, italic title) placed at the top of the grid. Editorial cards have
> no read state (excluded from the unread count) and hide under beat filters. Two landed on
> rebuild: Weekend 07-18 (5 paras) + Science 07-08 (2 paras). One self-inflicted bug caught by
> the suite mid-build: a duplicate `_MONTHS` constant shifted every card's date label by a
> month — the goldens flagged it instantly.

> **Added 2026-07-18 (night, later): writers WIRED to the plane — continuity gets real data.**
> Two hooks, both live at the next fires: **(1)** `dedup.py check` now enriches every ONGOING
> verdict with `thread` — the matched story's ACTUAL coverage arc (last ≤8 entries
> `{date, headline, event_date?}`) fetched from `/plane/thread` (same host + bearer the check
> already uses; best-effort, ≤10 distinct threads, a plane outage degrades to prior behavior).
> DEDUP.md Step B binds the writers to it: sequence claims ("seventh consecutive night") must
> match the timeline's entries, the arc's start date comes from its first row, and one clause
> of arc context replaces re-explained background. Zero new prompt steps — the enrichment rides
> the verdicts JSON the writers already read. **(2)** The Weekend cross-cutting-threads section
> now grounds itself in `/plane/entities` (the week's recurring actors, cross-stream) +
> `/plane/thread` (a candidate theme's real arc) before writing — the data proves a theme
> cross-cuts; judgment still picks and develops it. Live-verified end to end: a crafted
> Iran/Hormuz candidate came back ONGOING (0.820) with its thread's 6-row timeline attached;
> an unrelated control stayed NEW/bare. Spec suite 364 → 366.

> **Added 2026-07-18 (night): the plane is now SANDBOX-REACHABLE — mounted on embed-proxy.**
> The analytical plane's queries are served by the embed-proxy Worker as `/plane/*` (search /
> related / thread / entities / beats / sources / stats + bearer-gated `ingest`), same
> hostname, same `EMBED_TOKEN`. Mounted THERE deliberately: the env_018 egress allowlist
> enumerates EXACT hostnames (not `*.workers.dev`) and cannot be edited programmatically — a
> new worker host would be unreachable from the routines; embed-proxy already is. Data path:
> `tools/plane/bake.py` bakes the ledger into a 7.4MB artifact (magic + meta JSON + float32
> vectors + precomputed norms, KV `plane:v1`); the publish tail refreshes it after every
> edition (`publish.py` `plane-push`, non-fatal). The `POST /` embed contract is UNCHANGED and
> never touches KV. Pre-deploy adversarial review (2 Opus agents) confirmed embed-route
> byte-equivalence and caught four real 500s in the new routes (JSON-null body, NaN/overflow
> `days`, `__proto__`-named entities crashing the aggregation, malformed artifact dates) — all
> fixed + pinned in the 23-check smoke (`tools/embed-proxy/test/smoke.mjs`). Live-verified:
> fresh embed of a stored story cosines 1.0000 against its ledger vector; remote search
> parity-IDENTICAL to the local CLI (241ms); Iran thread = 11 stories via the Worker. The
> local CLI remains the offline reference. Routines can now query the plane at compose time —
> prompt wiring (thread-aware continuity framing) is the deliberate next step, not yet done.

> **Added 2026-07-18 (evening): Phase 2 analytical plane BUILT (`tools/plane/`) — SERVERLESS.**
> **The ledger is the database**: `query.py` folds `index/ledger/*.jsonl` in-process via
> `store.py materialize()` (the canonical folding, never re-implemented) on every invocation —
> brute-force cosine for vector search (~1.6k × 1024-dim ≈ 0.2s, no index needed), dict
> groupbys for the graph side. No database, no service, no sync step, no state; stdlib only; a
> fresh clone answers every query with zero setup. Key realization: the ledger's `seen`
> payloads carry the embeddings (base64 f16) — 1,625 stories 2026-05-27→present, ALL with
> vectors, no re-embedding, and the 40-day `index/stories/` pruning is irrelevant. Queries:
> semantic `search` (embeds via embed-proxy, same bge-m3), `related`, `thread` timelines (the
> Iran/Hormuz thread reads as an 11-story line across two streams), `beats`, `entities`,
> `sources`, `stats`. *(A first cut used local Postgres 17 + pgvector per the original §5.2
> sketch — built, loaded, verified, then replaced and uninstalled the SAME evening at Rafael's
> call: a resident server fights the pipeline's zero-infra character and bought nothing at
> this scale. Upgrade path if the corpus ever outgrows brute force: an embedded FILE —
> DuckDB/sqlite-vec — never a server.)* **Graph decision:** no graph DB either — the
> 2026-05-31 calibration showed cosine gives nearness, never relationship type, so the typed
> edges live in fields + groupbys (thread_id, entities, source_domain, affiliations, feedback).
> **Writers now emit `entities`** (DEDUP.md Step C, 2–5 canonical actors/places/artifacts,
> only-when-present like affiliations — old payloads stay byte-identical) as the graph's node
> vocabulary. **Plus a data bug the plane exposed on day one:** the 2026-07-18 weekend run
> recorded 6 stories with BLANK headlines → all six shared legacy id `2026-07-18-weekend-story`
> and one degenerate thread. `record` now has a deterministic backstop (`url_headline()`:
> blank headline → readable URL-derived fallback, distinct ids guaranteed); the six historical
> records are left as-is (homepage recovered their prose via the URL join). Spec suite
> 353 → 363. The plane is read-only and optional: nothing in the publish path depends on it.

> **Changed 2026-07-18 (latest): homepage frontend review → slim-down + packing/table fixes.**
> A 4-agent specialist review (css-layout, js-state, architecture reviewers + adversarial Opus
> synthesis; 24 findings verified against source, 2 struck as factually wrong) drove two commits:
> **(1) Slim-down (`e7c8745`)** — `_includes/head/custom.html` 842 → 301 lines. The brief-page
> machinery that outlived the retired pages (story-tagger, og-image/arXiv article-preview loader,
> per-story + overall feedback widgets and their CSS, the `__BRIEF` injection) had silently
> re-targeted the one remaining `single`-layout post — the evaluator review, where it restyled
> review bullets as story headlines with 👍/👎 thumbs posting into the Evaluator's own feedback
> ledger — and is now deleted (recoverable from git). Kept, verified individually: `window.__FB`
> config (homepage grid + propose form read it), the `.page__content` theme stub, unlock modal +
> propose form incl. the shared `.fb-btn` chrome (a cross-use the synthesis missed), Folio tokens,
> and the dark-mode `.page__title a` fix. Evaluator bullets render as plain prose. Two real bugs
> fixed en route: `home_harness.py` had embedded only the FIRST `<script>` block since 2026-07-11
> (the 620-line folio engine went completely untested — one-line `re.findall` fix), and the "How
> this works" modal's focus trap made its `/prompts/` link keyboard-unreachable (two-stop trap
> now). Plus `home.html` consolidation: 11 one-off `:focus-visible` rules → 3 grouped, duplicate
> button rules merged, dead link styling dropped from the now-span beat chip.
> **(2) Packing + tables (`97cbc8c`)** — the fixed harness immediately exposed real masonry holes
> (maxGap 383px at 3 cols, 645px at 2 cols — every large gap an unfilled notch above a 2-col
> lead). Three additions to the folio engine's notch machinery: **eager tallest-fit backfill**
> from the whole remaining queue at notch creation (first-fit-by-arrival was the main culprit);
> **waste-aware lead pair choice** (score top + waste, full-weight penalty for a notch nothing
> left in the queue can ever fill); and a **bottom-steal pass** (residual notches absorb
> bottom-of-column cards — the only cards that move without leaving a hole — with a ≤100px
> shift-steal fallback that trades a 600px+ hole for a small seam on near-miss fits). Measured:
> 1440px 383→187, 800px 645→157, mobile 20 (= the grid gap); zero overlaps at every width; sync
> checks green both signed-out and signed-in. Separately, the theme's light-palette table skin
> rendered the evaluator's Health-Summary header near-invisible on dark paper — post tables are
> re-skinned variable-driven in custom.html (th/td ink-on-panel, hairline borders, striping off).
> All verified live by screenshot: homepage, a filtered re-layout, and the evaluator table.
> **(3) Read-filter roaming** — the All/Unread/Read segmented toggle now roams across devices
> with the beat chips: the `/prefs` object gains a validated `rs` field (`""|"unread"|"read"`,
> invalid coerces to All; feedback-sink Worker + 3 new smoke checks, 46 total), `topicPrefs:v1`
> carries `rs` in the same whole-object LWW shadow (side benefit: the filter persists across
> reloads even signed out — it used to reset to All every load), and the harness stubs
> `GET /prefs` + asserts the roamed filter lands signed-in and zero prefs traffic flows
> signed-out. Worker redeployed same-day.

> **Changed 2026-07-18 (later): individual brief pages retired.** The homepage story feed carries
> every story's full prose (never trimmed, since 2026-07-10), so the per-edition pages at
> `/{y}/{m}/{d}/{slug}/` were redundant — `_config.yml` now sets `published: false` on all posts
> by default. **The `_posts/*.md` files stay** (they remain the data source for
> `build_stories_feed`, `build_stats`, and the Evaluator); only the rendered pages are gone.
> The **Evaluator review keeps its page** (its content is not on the homepage) via a required
> `published: true` in its front matter — template updated, 10 historical reviews backfilled.
> Ripples: brief notification stubs now click through to the site root (`publish.py`), the News +
> Weekend emails end with an `All stories:` homepage link instead of `Full brief:`, and the
> homepage card's beat chip is a plain span (it used to link the edition page). Old ntfy/email
> links to brief pages 404 by design. The brief-page feedback widget path in `custom.html` is
> inert (pages gone, homepage voting unaffected).

> **Added 2026-07-18: determinization of the mechanical tier (less AI, same quality).** Five
> surfaces where a model was replaying deterministic procedure moved into tools; the editorial core
> (research, story selection, writing, ONGOING keep/drop, teasers, evaluator judgment) is untouched.
> **(1) `tools/fetch.py`** — the curl→proxy fallback chain as a logging wrapper (one JSON line per
> attempt to `/tmp/fetch.log`; `--proxy` skips the direct attempt; no bearer in env → proxy step
> auto-skipped, so the Evaluator degrades to direct-only). The prompt-prose fetch dance is gone.
> **(2) `tools/footer.py`** — Coverage-footer telemetry is COMPUTED at publish (registry tier
> split, direct-vs-snippet from `[via snippet]` tags, exact word count + token estimate, `Feeds
> hit` aggregated from the fetch log); writer-authored lines (Languages, Gaps, Discovery,
> stream-specific) preserved. The pipeline's "only health signal" stops being self-reported
> (this supersedes the same-morning self-reported token-estimate footer line, `581dba3`).
> **(3) `tools/publish.py`** — the whole writer publish tail is ONE call: record → anchor →
> footer → source lint → registry/institutions sync → date lint → feed+stats → source health →
> notification stub (real JSON encoding, computed UTC timestamp) → commit/push with the homefeed
> rebase retry; bare front-matter dates normalized to full ISO timestamps. DEDUP.md Steps C.25–E
> collapsed to its step list; the skipped-step failure class (the 07-07→07-10 registry-sync gap)
> is structurally closed. **(4) Evaluator determinized further**: `metrics.py` computes dimensions
> B/D/F/G/H/K/L into `health.json → briefs` plus the off-main self-delivery guard
> (`continuity.off_main`), and `tools/evaluator/linkcheck.py` does dimension C's deterministic
> 20-link sample + curl resolution — "read, don't recount" now covers every countable dimension;
> Opus keeps claim spot-checks, editorial shape (M), halo audit (N), synthesis, proposals.
> **(5) Watch gate**: `tools/watch/due.py` (cooldown arithmetic; quiet ticks stop after one Bash
> call printing `NONE DUE`) + `tools/watch/fire.py match|push` (stub + targeted `last_fired`
> rewrite preserving YAML formatting + commit/push) — Haiku's only remaining job is the
> WebSearch-snippet `match_when` judgment; trigger prompt updated in place (still un-shimmed,
> `routines/watch.md` mirrors it). Spec suite 317 → 353.

> **Added 2026-07-17: Sports stream + topic-selection sync.** (1) **Sports** — a fifth writer
> (`claude-opus-4-8`, weekly Monday `0 7 * * 1`, `_posts/{d}-sports.md`, no email). Scope: Swiss +
> global majors (Super League/Swiss NT, UEFA + big-5 football, F1, tennis, alpine skiing, NL/NHL
> hockey). Primary-source discipline mapped to sport: T1 = official results/standings + federation
> announcements + CAS/WADA rulings; the transfer-rumour exception (official confirmation is the
> fact, everything earlier tagged `[rumour]`); anti-commodity mandate (lead with what a result
> *means*, never the score). `routines/src/sports.md` → `assemble.py`; single-topic beat `sports`
> (`build_stories_feed` TOPICS `#c26b2e` + stream guard); `sports` added to every stream
> enumeration (build_stories_feed, build_stats, sources/{registry,health,lint,preflight},
> dedup, store/verdicts) and the shared beat vocab; registry seeded with 16 sports sources
> (15 official T1 + BBC Sport, plus SRF gains a `sports` stream). Trigger id: `trig_01PfmuHXkgjhZREW6XfztZrb`
> (weekly Mon `0 7 * * 1`; first run 2026-07-20; see `routines/MANIFEST.md`). (2) **Topic-selection sync** — the homepage beat-chip
> selection now roams across devices via the feedback Worker's new `GET|POST /prefs` route
> (`prefs:{reader}` KV, whole-object LWW-by-ts; the selection is one statement of intent, so it
> replaces rather than merges). Frontend mirrors read-state's local-first model (`topicPrefs:v1`,
> debounced push, pull+merge on login). CORS restricted to the site origin like `/readstate`.

> **Added 2026-07-10: whole-system evaluation fixes + passkey accounts (plan
> `go-ahead-i-trust-memoized-cray`).** A 9-agent read-only sweep found three criticals; all fixed
> same-day. **(1) Bridge v2** (`bridge.sh`, local): `pages_selfheal` now polls
> `repos/…/pages/builds/latest` (the 2026-07-03 version read `GET /pages` `.status`, which reflects
> the *served* deploy — it missed the Jul-9 wedge for ~23h) and also detects a **built-but-stale
> SHA** vs `origin/main` (push/build race → `POST /pages/builds` rebuild, rate-limited via a state
> file); dirty-tree resilience (auto-`stash --include-untracked` → `pull --rebase` → `stash apply`;
> a stray local edit no longer kills the tick — 31 prior silent aborts); timestamped ticks,
> self-rotating log at `~/Library/Logs/news-brief-bridge.log`. **(2) Source diversification
> unblocked**: `registry.py sync` was never invoked anywhere (candidates.jsonl grew, registry
> starved, `candidates_to_try` = 0 for news/science) — now DEDUP **Step C.25b** (every writer, right
> after `lint.py`); registry seeded to 137 domains (18 probation science venue seeds +
> retired-stream backfill); fossil T1/T2 domain tables deleted from writer prompts (sources come
> from the preflight plan); `lint.py append_candidates` made idempotent. **(3) Story identity**:
> `dedup.py record` re-runs now **converge** on the first run's sids (norm_url → cited-urls overlap
> → cosine ≥0.93); `tools/store/reconcile.py` is a report-only publish-sid⁄edition-index integrity
> lint; the 2026-07-07 Cuba fork healed via a `merged-into:` ledger status event. **Evaluator loop
> closed before the Sunday fire**: `proposals/reader-model-2026-07-05.json` backfilled + stamped,
> two reader-validated preferences applied to `reader-profile.md`, **bounded auto-apply granted**
> (evaluator may append dated "Learned preferences" lines itself — append-only, real-feedback-only;
> registry/source-weights stay human-gated), new dimension M (editorial shape: vendor-PR-lead share,
> aggregator-shape, personalization), self-delivery guard (stale continuity + `claude/*` branch
> check), weekend ~50/50±15pp bias target. **Writer prompts**: News gains lead-first rule +
> per-story depth spec; affiliations mandatory-Semantic-Scholar → best-effort chain (arXiv native →
> S2 one-attempt → OpenAlex → omit); operational telemetry footers moved into HTML comments
> (evaluator still reads them in raw markdown); Weekend quotas → quality-capped ceilings.
> **Homepage**: story text is never trimmed (`_trim` deleted from `build_stories_feed.py` — the text
> is the whole point); Brief-tier cards render folded (headline-only, click-to-expand — presentation
> only, full text always in the DOM). **Passkey accounts + read-state sync** (SPIKE
> 2026-07-07-read-state-sync, SHIPPED): feedback-sink Worker gains WebAuthn auth
> (`@simplewebauthn/server` — first bundled-dep worker; invite-gated registration via new secret
> `INVITE_TOKEN`, discoverable credentials, UV required, rpID `khalic-lab.github.io`) + 90-day
> rolling KV sessions + `GET/POST /readstate` (per-reader `{sid:{ts,v}}` LWW tombstone map, 64KB/
> 2000-entry caps, 90-day age-out; CORS on `/auth/*`+`/readstate` locked to the site origin);
> homepage client syncs `homeRead:v1` through a `syncState:v1` shadow (debounced 30s push +
> visibility flush, keepalive fetch; signed-out = zero sync traffic); votes carry the session
> bearer → server-pinned `reader`. Spec suite now 274 tests; harness gained SYNCCHECK headless
> assertions.

> **Added 2026-07-10 (later): the affiliation element**
> (`docs/SPIKE-2026-07-10-affiliation-element.md` — prior-art + live-API measurements behind
> every choice below; supersedes the "best-effort chain" wording in the block above).
> **Principle: affiliation is the paper's provenance, displayed and recorded — never a
> selection signal** (LLM judges measurably over-reject low-prestige affiliations,
> arXiv:2509.15122; every papers prompt now carries an explicit anti-halo guard).
> **Retrieval** (measured 2026-07-10): index APIs cannot do this for preprints — S2 has
> nothing for hours-old papers, and OpenAlex's arXiv records carry EMPTY institutions even
> once indexed (~6-day lag) — so arXiv preprints read the paper's own HTML author block via
> the fetch-proxy (~97% of new submissions; the 2026-07-10 ai-ml fire went 10/10 this way),
> bioRxiv/medRxiv use the details-API's `author_corresponding_institution`, and journal DOIs
> use OpenAlex (institutions resolved — verified on fresh Nature papers). Shared partial
> `routines/_shared/affiliations.md` (byline format law `AUTHORS (Inst1; Inst2; Inst3)`,
> ≤3 then `+N more`, sentinel `(affiliation not listed)`, ONE extra fetch per paper max).
> **Data:** Step C final.json gains `"affiliations": [...]` → persisted on index records
> (only-when-present; old payloads stay byte-identical) → ledger via the verbatim dual-write;
> `dedup.py parse_affiliations` + `affil-backfill` patched 52 historical records from post
> bylines (idempotent, ledger untouched; the parser rejects link targets, author-count/
> author-annotation fragments, paper-name-before-`et al.` parens, and anything after the
> first backtick tag — every trap the June single-line bylines actually contained). **Display:** homepage card source line is
> institution-first — `ETH Zurich · arxiv.org` (`affiliation_label`, ≤2 names then `+N`;
> proper case inside the lowercased src line; wraps, never ellipsized). **Ledger:**
> `sources/institutions.yml` (`tools/sources/institutions.py sync`, DEDUP Step C.25c) — the
> registry's twin keyed by canonical institution name: citations/streams/first_seen/
> last_cited/lifecycle, probation→established at the same ≥5 floor, hand-curated `aliases:`
> fold variants self-healingly; bootstrapped from the backfilled citations, then hand-seeded
> to 167 entries with every `class` set (39 frontier-lab, 39 university, 36 government,
> 22 industry, 31 independent — the big-lab catalog spans US/EU/CN/JP/KR frontier labs,
> big-tech research arms, AI-safety orgs, and national labs). The `aliases:` map is mirrored
> into the writer prompts as a generated canonical-names block in
> `routines/_shared/affiliations.md` (`institutions.py sync-prompts` + `assemble.py`;
> `sync-prompts --check` runs inside the spec suite, so an alias edit that skips the mirror
> fails the tests) — bylines are canonical at the source, the ledger fold is the backstop.
> NO imported prestige rank (CSRankings/Nature Index considered and rejected).
> **Evaluator:** new dimension N — affiliation coverage rate (target <20% sentinel; was 70%
> on 2026-07-07 under the API chain) + halo audit (unaffiliated papers must not
> systematically score importance 1). Spec suite 274 → 304.

> **Added 2026-07-07: story-store migration, steps 1–4 (`docs/SPIKE-2026-07-07-continuous-news.md`).**
> The story (not the edition) is now the durable unit. **Identity:** `st-{sha1(norm_url)[:12]}`
> (`tools/store/store.py`). **Primary store:** an append-only event ledger
> `index/ledger/{ingest-day}.jsonl` (`seen/update/publish/status/feedback` events; `.gitattributes`
> `merge=union`; materialized snapshot `.materialized.json` is git-ignored, regenerated per consumer).
> `dedup.py record` **dual-writes**: the legacy per-edition `index/stories/*.jsonl` stays byte-identical
> (retire at end of migration) + `seen`/`publish` ledger events (non-fatal on failure — a broken ledger
> never costs an edition). History backfilled (`tools/store/backfill.py`, 1456 records → 1411 stories
> after URL-fold). **Anchors:** Step C.25 runs `tools/store/anchor.py --index <edition file>` (bullet
> `<a id="st-…">` / H3 kramdown IAL) so brief-page votes and homefeed votes (`sid` in `homefeed.json`)
> share the store id. **Feedback:** folded continuously by the bridge (`tools/feedback/fold.py` after
> drain) — resolution direct/legacy/url, `ev:"feedback"` appended BEFORE `consumed:true` flips; the
> Evaluator's 7-day window arithmetic is retired (the 27%-orphaning class is structurally impossible).
> **Sources:** `sources/registry.yml` (bootstrapped citation-driven from live streams, retired-pipeline
> domains excluded; credibility lifecycle candidate→probation→established, human-gated transitions;
> machine appends go to `sources/{candidates,last-cited}.jsonl`, folded by `registry.py sync`).
> Writers' first research action = `tools/sources/preflight.py --slug {slug}`; `lint.py` checks
> `[new source]` tags / Discovery footer / caps at Step C.25; `health.py` → `_data/source-health.json`
> at Step D. **Caps + discovery quota are REPORT-ONLY** until armed (SPIKE step 5, data-gated).
> **Evaluator:** `tools/evaluator/metrics.py` → `_data/health.json` computes the mechanical dimensions;
> proposals also machine-readable (`proposals/*-{date}.{json,yml}`, `applied:true` stamp protocol);
> Sunday source-scout duty (≤20 fetches, WebFetch-based — the evaluator holds no fetch-proxy token by
> design). Spec suite: `python3 -m unittest discover -s tools/tests` (212+ tests, RED/GREEN-committed).

> **Added 2026-07-03: Pages deploy self-heal + News moved to midday.** *(Self-heal superseded
> 2026-07-10 — see the block above: it now polls `pages/builds/latest` and catches stale-SHA races.)*
> News trigger cron `0 17 * * *`
> → `0 10 * * *` (UTC) — 19:00 → 12:00 Bern (summer; fixed-UTC cron, so 11:00 Bern in winter). See the
> writers table above. Separately: a transient GitHub Pages deploy failure poisons the current commit
> SHA (Pages deployments are keyed by SHA, and **nothing retries a failed Pages build**), freezing the
> site on the last good deploy — this stranded 2026-07-02's brief for ~15h because no later commit was
> pushed overnight to advance the SHA. The **bridge now self-heals** (`bridge.sh` step 4): after its
> normal push, on a *quiet* tick (nothing else advanced the SHA) it queries the Pages status API and, if
> `errored`, pushes an empty commit to mint a fresh deployment ID (rate-limited to ≤1 retry / 25 min;
> pings ntfy). The manual fix is the same — a **new commit**; rebuilding the *same* SHA (`POST
> /pages/builds` or a workflow rerun) just re-collides with the failed record ("Deployment failed, try
> again later"). Caveat: the bridge runs 07–22h, so a post-22:00 Pages failure heals at 07:00. See the
> `pages-deploy-wedge` memory for the full diagnosis.

> **Fixed 2026-07-03: Evaluator + Watch `outcomes` stranding.** Both triggers carried a
> `session_context.outcomes.git_repository.branches` key the writers don't have; it silently diverted
> each run's output onto a fresh `claude/{admiring-edison,serene-mayer}-*` branch while the session
> believed its `git push origin main` succeeded. Every Sunday review since 2026-05-31 (except 06-14)
> stranded that way — the Evaluator wasn't dead, its delivery was hijacked — along with one 06-17
> Watch fire. The four reviews + their `consumed:true` feedback flips were recovered to main and the
> `outcomes` / `autofix_on_pr_create` keys removed from both triggers (see `routines/MANIFEST.md`).

> **Removed 2026-06-18:** the dedicated Markets routine and all market content. The Markets
> routine (was `trig_01GBugAS5qw88yQK3tv8kKWx`, cron `30 18 * * 1-5`) had been disabled since
> 2026-05-30; on 2026-06-18 the Morning Overview's pre-open market snapshot section was dropped
> too, and the dedup snapshot-genre collapse machinery removed — so **no brief emits market
> content**. The consolidated evening email covers three streams (World/Switzerland, AI/ML,
> Cyber+Papers). Published May market briefs are kept as a frozen archive; the disabled trigger
> config is retained server-side (the RemoteTrigger API exposes no delete).

> **Redesigned 2026-06-29 (cadence + topics — `docs/SPIKE-2026-06-29-cadence-redesign.md`).** Replaced the
> old daily Overview + Cyber+Papers + AI/ML cadence with the per-topic lineup above: **News** (daily midday,
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
| Brief | `_posts/{YYYY-MM-DD}-{slug}.md` | front-matter (`layout,title,date,categories`) + body + Coverage footer | writer → homefeed/stats + Evaluator (data-only since 2026-07-18 — pages unpublished; only evaluator posts render, via `published: true`) |
| Notification stub | `pending-notifications/{ts}-{slug}.json` | `{title, click, body, tags}` | writer/watch → bridge (then deleted) |
| Watch registry | `watches.yml` | `[{id, query, match_when, cooldown_days, last_fired}]` | user + Watch (writes `last_fired`) |
| Bridge config | `/usr/local/src/news-brief-ntfy-bridge/.env` | `NTFY_TOPIC, NTFY_SERVER, REPO, FEEDBACK_WORKER_URL, FEEDBACK_TOKEN` | bridge.sh |
| Git creds | `…/git-credentials` (mode 600) | `https://x-access-token:<tok>@github.com` | bridge git push |
| Legacy briefs | `briefs/{stream}/{date}.md` | pre-Pages layout, only May 2–4 | **deleted 2026-07-03** (recoverable from git history) |
| Coverage footer | inside each brief | `Direct fetches: N \| via-snippet: M`, `Feeds hit`, `Gaps` | **the only health signal** — COMPUTED by `tools/footer.py` at publish since 2026-07-18 (writer authors only Languages/Gaps/Discovery + stream-specific lines) |
| Reader feedback | `feedback/{YYYY-MM}.jsonl` | `{id, ts, reader, brief, story_id, vote 1/-1/0, reason, surface, source_domain, consumed}` | widget→Worker→bridge → `fold.py` → ledger → Evaluator |
| Reader profile | `reader-profile.md` + `reader-profile/source-weights.yml` (`never:`/`reduce:`) | NL editorial brief + domain lists | Evaluator proposes (human-gated) → writers read |
| Story ledger | `index/ledger/{YYYY-MM-DD}.jsonl` (ingest day, append-only, merge=union) | `{ev: seen\|update\|publish\|status\|feedback\|notify, ts, actor, …}` — record schema in SPIKE 2026-07-07 §3.1 | dedup.py dual-write + backfill + fold.py → `store.py materialize` (all consumers) |
| Source registry | `sources/registry.yml` (+ `sources/{candidates,last-cited}.jsonl` machine appends) | per-domain `{class, tier, status, reach, probe, streams, last_cited, subsources, lifecycle}` | `registry.py bootstrap/sync` + human → `preflight.py`/`lint.py`/writers |
| Source health | `_data/source-health.json` | per-stream 30d `{stories, unique_domains, new_domains, top5_share, saturated, waiver_rate}` | `health.py` (writer Step D) → Evaluator + homepage-adjacent tooling |
| Evaluator metrics | `_data/health.json` | `{week, streams, feedback, sources, continuity}` | `tools/evaluator/metrics.py` (evaluator fire start) → Evaluator |
| Machine proposals | `proposals/{name}-{date}.json` | `[{id, dimension, target, change, evidence, applied, applied_by?}]` | Evaluator emits → human/auto applies + stamps → next Evaluator verifies |
| Read state (sync) | Cloudflare KV `readstate:{reader}` (not in repo) | `{sid: {ts, v: 0\|1}}` LWW tombstone map; client shadow `syncState:v1` + paint source `homeRead:v1` in localStorage | homepage JS ↔ feedback-sink Worker (passkey session) |
| Institutions ledger | `sources/institutions.yml` | `meta.synced_editions` + `aliases:` + per-institution `{class, status, streams, first_seen, last_cited, citations, lifecycle}` | writer bylines → Step C `affiliations` → `institutions.py sync` (Step C.25c); class + aliases hand-curated |
| Passkey auth | Cloudflare KV `cred:{id}` / `session:{token}` / `chal:{kind}:{c}` (not in repo) | credential pubkey+counter; 90d rolling sessions; single-use challenges TTL 300s | feedback-sink `/auth/*` (registration invite-gated by `INVITE_TOKEN` secret) |
| Spec suite | `tools/tests/` (stdlib unittest + fixtures) | 366 tests: store invariants, fold, registry, institutions, affiliations + prompt-mirror drift, lint, metrics (+ computed briefs dimensions), dedup convergence, reconcile, dual-write byte-identity goldens, fetch wrapper, computed footer, publish orchestrator, watch gate, linkcheck, plane (bake artifact roundtrip, cosine/groupbys, entities + blank-headline record path, thread enrichment) | dev/CI-less drift guard (`python3 -m unittest discover -s tools/tests`); worker smokes run separately (`node tools/feedback-sink/test/smoke.mjs` 46 checks, `node tools/embed-proxy/test/smoke.mjs` 23 checks) |
| Plane artifact | Cloudflare KV `plane:v1` on embed-proxy (not in repo; namespace `459b76a2…`) | magic `PLANEv1\0` + meta JSON (n, dim, ts, norms, compact stories incl. entities) + n×1024 float32 vectors (~7.4MB), baked from the ledger | `tools/plane/bake.py --push` (publish-tail `plane-push`, every edition) → embed-proxy `/plane/*` queries (dedup check thread-enrichment, Weekend cross-cutting grounding, ad-hoc); `tools/plane/query.py` = offline reference twin |

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
homepage card widget (_layouts/home.html; kill switch + URL via window.__FB in custom.html —
                      the per-brief-page widget was deleted 2026-07-18 with the brief pages)
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
               └─ Writers (News/AI-ML/Science/Weekend): read reader-profile.md +
                     source-weights.yml at compose time (favor/demote; never:/reduce:).
```

- **Worker:** `https://feedback-sink.khalic-lab.workers.dev` — `/submit` public (shape-capped,
  no bearer: a browser can't keep one), `/drain`+`/ack` bearer-gated (two-phase delete-on-ack so a
  missed bridge tick neither loses nor double-commits). Not on the env_018 allowlist — it's called
  by the *browser* and the *Mac bridge*, never the routine sandbox. Since 2026-07-10 also the
  account backend (`/auth/*` passkeys + `/readstate` sync — see the 2026-07-10 block in §1.1 and
  `tools/feedback-sink/README.md`); a signed-in browser's `/submit` carries the session bearer,
  so `reader` is server-pinned instead of self-declared.
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

### 5.1 Story item (the dedup unit) — `index/stories/{date}-{slug}.jsonl` (flat, dash-joined), one per line

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
  "topics": ["switzerland"],              // homepage beat(s), 1-2 from the controlled vocabulary;
                                          //   writer-supplied (newsroom-ethos rubric), [] if omitted.
                                          //   NOTE: no record carries these yet (added 2026-07-06;
                                          //   they flow in as routines fire) — the feed's join-rate
                                          //   line shows when they start landing
  "importance": 3,                        // homepage card size: 3=lead 2=standard 1=brief; null if
                                          //   the writer didn't score it (feed derives a fallback)
  "thread_id": "bilaterals-iii",          // assigned when matched to a prior story
  "first_seen_date": "2026-05-03",          // earliest member of the thread (first COVERAGE)
  "event_date": "2026-05-02",               // when the event HAPPENED (nullable; ISO 8601 reduced
                                            //   precision YYYY|YYYY-MM|YYYY-MM-DD). Distinct from
                                            //   `date` (compose) and `first_seen_date` (coverage).
  "embedding_model": "bge-m3",
  "emb": "<base64 float16 x1024>"           // packed via dedup.py encode_vec (~8x smaller than
                                            //   float text); decoded to an in-memory `embedding`
                                            //   list by load_recent_index(). The raw-float
                                            //   `embedding` column is the Phase-2 parquet shape.
}
```

**Homepage feed — `_data/homefeed.json`.** The front page (`_layouts/home.html`) is a per-STORY
masonry grid (topic filters, importance-sized cards, real og:images lazy-loaded via og-proxy with
text-only fallback, per-story thumbs posting `surface:"home"`), not the old edition list.
`tools/build_stories_feed.py` **parses the recent `_posts/*.md` briefs** for each story's real
prose (headline, body, and the writers' `Why it matters` paragraph — the dedup summary is a terse
embedding one-liner, deliberately not used for display), then overlays `topics`/`importance` **and
the writer-recorded `display_body`/`why` prose** from the matching `index/stories/*.jsonl` record —
**joined by canonical URL** (slugified headlines diverge between the post's bold lead and the
record's curated headline), slug-id as fallback; the build prints the join rate. Recorded prose
beats the markdown re-parse (the record is authored, the parse is recovered); as records accumulate
the parser becomes legacy fallback only. `tools/home_harness.py` renders the layout standalone for
headless-Chrome smoke tests (geometry self-check included) — no local Jekyll needed. Unmatched stories get derived tags (topic from section+keywords,
importance from brief position). Output is URL-deduped across streams, sorted newest+lead first,
and capped per-edition (each stream's latest edition keeps ≥6 stories, so weekly Science never
vanishes). Writers regenerate and commit it after `record` (DEDUP.md Step D; `_data/` is in their
publish `git add`, and their push-retry regenerates it on a rebase conflict — two editions firing
the same minute both rewrite this whole file).

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
   `www.letemps.ch`, plus `fetch-proxy.khalic-lab.workers.dev` (added 2026-06-18; since 2026-07-18
   `embed-proxy.…workers.dev` also serves the analytical plane as `/plane/*` — new capabilities
   mount on existing allowlisted hostnames because this list is exact-hostname and UI-managed). The chronic AI/ML
   403s were this list not covering lab/news hosts — now solved via the fetch-proxy (§1.4) rather than
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
- Migrating the legacy `briefs/` dir — resolved 2026-07-03: deleted (was dead weight; git history keeps it).
- Replacing ntfy / Gmail-draft delivery — unchanged by this design.
