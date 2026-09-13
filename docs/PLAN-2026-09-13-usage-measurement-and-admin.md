# PLAN — Measured token usage per routine run, and an admin page for sources

**Date:** 2026-09-13 · **Status:** APPROVED FOR BUILD · **Owner's ask (Rafael):** "For the token
usage, I want measuring, not estimation, starting next deploy. I want a dedicated admin page where I
can also delete or include sources."

Architectural decisions below are settled. Implementers build to the contracts in §1–§3 and do not
relitigate them; where a contract is silent, pick the simplest stdlib answer and say so in the commit
message. Anything that changes a contract goes back to the architect, not into the code.

---

## 0. Decisions

1. **Measurement source = the run's own Claude Code transcript.** Every assistant message in
   `<transcript>.jsonl` carries `message.usage` with `input_tokens`, `cache_creation_input_tokens`
   (and a `cache_creation` object splitting `ephemeral_5m_input_tokens` / `ephemeral_1h_input_tokens`),
   `cache_read_input_tokens`, `output_tokens`, `server_tool_use` and `message.model`. Summing those is
   a measurement, not an estimate. Nothing else in the sandbox measures anything (no API key, no
   admin API, no OTel collector — and adding a collector would be a new host, which the environment
   allowlist forbids).
2. **Two entry points, same parser, append-only records.** (a) A **`Stop` hook** (and `SessionEnd`
   as its backup) in the repo's `.claude/settings.json` receives `transcript_path` on stdin, parses,
   appends a record, commits and pushes it. This measures every run, including runs that publish
   nothing (Watch idle ticks, skip-on-empty writers). (b) **`publish.py` gains a `usage` step** that
   finds the live transcript by glob and appends a `stage: "publish"` record into the edition commit.
   That is the guarantee for "starting next deploy": if the hook does not fire in the sandbox, the
   publish-time record still lands. Fold takes the most complete record per `session_id`.
3. **One JSONL file per routine per month** — `index/usage/<YYYY-MM>-<routine>.jsonl`. News and
   AI/ML both fire at 10:00 UTC on Tuesdays and Fridays; two hooks appending to one file would conflict
   on rebase. Per-routine files cannot.
4. **Cost is reported at list price**, labelled as such, from a hand-maintained table with a
   `pricing_as_of` date. The subscription pays the real bill; list price is the comparable number.
5. **Admin page at `/admin/`, theme-free, phone-first, document scroll.** Its own `<html>`, own
   viewport meta with `viewport-fit=cover`, no minimal-mistakes includes except `head/custom.html`
   (tokens, fonts, `window.__FB`). Nothing private is embedded in the public HTML: all data comes from
   the Worker after passkey sign-in.
6. **Reads and writes go through the existing feedback-sink Worker** (already the account backend;
   the browser and the Mac bridge reach it; the sandbox never needs to). New routes under `/admin/*`.
   The registry snapshot the page reads is pushed to KV by the bridge; admin actions queue in KV and
   the bridge drains, applies, commits, pushes, then acks — the two-phase pattern the feedback path
   already uses. No new host, no new secret, no resident server.
7. **"Delete" = retire, never a physical delete.** `sources/registry.yml` is an audit trail; a retired
   entry is excluded from preflight fetch lists and discovery candidates (`tools/sources/preflight.py`
   already skips `retired`/`demoted`). "Include" = add a new entry (default `status: probation`) or
   restore a retired one. Every action appends a lifecycle event. Registry edits go through
   `tools/sources/registry.py`'s own `yaml_load`/`yaml_dump` — never PyYAML (absent in the sandbox).
8. **Effect timing is honest on the page:** an action is applied at the next bridge tick
   (`*/10 7-22 * * *` Europe/Zurich), and writers honour the registry at their next fire.

---

## 1. Measurement contract

### 1.1 Parsing a transcript (`tools/usage/transcript.py`)

- Input: a path to `<session>.jsonl`. If a sibling directory `<session-id>/subagents/` exists, also
  parse every `agent-*.jsonl` in it (sub-agent tokens are real spend; routines have no Agent tool
  today, so this is normally empty).
- Consider only lines with `"type": "assistant"` whose `message.model` is a string not equal to
  `"<synthetic>"`. Skip lines whose `isApiErrorMessage` is true.
- **Dedupe by `message.id`.** Claude Code writes one line per content block of a streamed message,
  all with the same `message.id` (measured locally: up to 15 lines per id). For each id take, per usage
  field, the **max** across its lines (usage only grows while a message streams). Count the id once as
  a message.
- Per message collect: `model`, `input_tokens`, `cache_creation.ephemeral_5m_input_tokens`,
  `cache_creation.ephemeral_1h_input_tokens` (fall back to `cache_creation_input_tokens` as 5m when
  the object is absent), `cache_read_input_tokens`, `output_tokens`,
  `server_tool_use.web_search_requests`, `server_tool_use.web_fetch_requests`, and the names of
  `tool_use` content blocks.
- Session metadata from any line: `sessionId`, `cwd`, `version`, `gitBranch`; `started` = timestamp of
  the first `user` line, `ended` = timestamp of the last `assistant` line.
- Routine detection, in order: first user message text matches
  `routines/(news|ai-ml|science|weekend|sports)\.md` → that slug; matches
  `routines/weekly-evaluator\.md` → `evaluator`; contains `tools/watch/due.py` or `Watch routine` →
  `watch`; else the first Bash `tool_use` input containing `tools/publish.py --slug <s>` → `<s>`; else
  `unknown`.
- Edition detection: first Bash `tool_use` input containing `tools/publish.py … --slug S … --date D`
  → `D-S`; else null.

### 1.2 Record schema v1 (`tools/usage/record.py` emits; one JSON object per line)

```json
{
  "v": 1,
  "session_id": "…",
  "stage": "publish" | "stop" | "session-end",
  "routine": "news" | "ai-ml" | "science" | "weekend" | "sports" | "evaluator" | "watch" | "unknown",
  "edition": "2026-09-14-news" | null,
  "started": "2026-09-14T10:00:12Z", "ended": "2026-09-14T10:41:03Z", "duration_s": 2451,
  "messages": 87,
  "models": {
    "claude-opus-4-8": { "input": 0, "cache_write_5m": 0, "cache_write_1h": 0, "cache_read": 0, "output": 0, "messages": 87 }
  },
  "totals": { "input": 0, "cache_write_5m": 0, "cache_write_1h": 0, "cache_read": 0, "output": 0 },
  "server_tools": { "web_search_requests": 0, "web_fetch_requests": 0 },
  "tool_calls": { "Bash": 0, "WebFetch": 0, "WebSearch": 0, "Read": 0, "Write": 0, "Edit": 0, "Glob": 0, "Grep": 0 },
  "cost_usd_list": { "total": 0.0, "by_model": { "claude-opus-4-8": 0.0 }, "pricing_as_of": "2026-09-13", "missing_models": [] },
  "claude_version": "2.1.141", "cwd": "/…", "transcript": "/…/<session>.jsonl", "transcript_lines": 1234,
  "hook_event": "Stop" | "SessionEnd" | null,
  "recorded_at": "2026-09-14T10:41:05Z"
}
```

### 1.3 Files, commits, gate

- Path: `index/usage/<YYYY-MM>-<routine>.jsonl`, month from `started`. Append-only. Never rewrite.
- **Gate:** `record.py` records only when `platform.system() != "Darwin"` or `USAGE_RECORD_LOCAL=1`.
  On the Mac it exits 0 silently in well under a second (local sessions load the same project
  settings and must not pollute the ledger).
- **Idempotency:** before appending, scan the target file for a line with the same `session_id` and
  `stage`; if present, exit 0 without writing or committing.
- **`--hook` mode** (stdin JSON from Claude Code: `session_id`, `transcript_path`, `cwd`,
  `hook_event_name`): parse → append → commit → push. Git protocol, mirroring `tools/publish.py`'s
  wrapper: `git -c user.email=routine@khalic-lab -c user.name="Usage Hook" -c commit.gpgsign=false`.
  Steps: `add index/usage/` → `commit -m "Usage — <routine> <started date> (<stage>)" -- index/usage/`
  (path-scoped, so anything the routine left staged is not swept in) → `push origin HEAD:refs/heads/main`;
  on push failure: `stash --include-untracked` if dirty (never popped — the session is over),
  `pull --rebase origin main`, push again; three attempts. **Always exit 0**, print one summary line
  to stderr. Never write JSON to stdout (a Stop hook's stdout is parsed for decisions).
- **`--find` mode** (publish time, inside the running session, no commit): locate the live transcript
  as the newest `*.jsonl` under `$CLAUDE_CONFIG_DIR/projects/*/` or `~/.claude/projects/*/` whose
  `cwd` equals the repo root and whose last line is younger than 30 minutes; append a
  `stage: "publish"` record; `publish.py`'s existing `git add index/` picks it up. If no transcript is
  found, print `usage: transcript not found (<n> candidates)` and return 0 — the step is non-fatal
  like every other analytics step in `publish.py`.
- `--transcript <path> [--dry-run] [--routine X]` mode for tests and for measuring any transcript
  locally (prints the record as JSON; with `USAGE_RECORD_LOCAL=1` it also appends).

### 1.4 Hook configuration (`.claude/settings.json`, new file, checked in)

```json
{
  "hooks": {
    "Stop":       [{ "hooks": [{ "type": "command", "command": "python3 \"${CLAUDE_PROJECT_DIR:-.}/tools/usage/record.py\" --hook", "timeout": 120 }] }],
    "SessionEnd": [{ "hooks": [{ "type": "command", "command": "python3 \"${CLAUDE_PROJECT_DIR:-.}/tools/usage/record.py\" --hook", "timeout": 120 }] }]
  }
}
```

Both events call the same script; idempotency makes the second a no-op when the first succeeded.
`.claude/settings.local.json` (permissions) is untouched.

### 1.5 Pricing (`tools/usage/pricing.py`)

A dict keyed by exact model id → USD per million tokens for `input`, `output`, `cache_write_5m`,
`cache_write_1h`, `cache_read`, plus `PRICING_AS_OF`. **Fetch the numbers from the official pricing
page at build time (load the `claude-api` skill; never from memory)** and cite the URL in a comment.
Cover at least: `claude-opus-4-8`, `claude-haiku-4-5-20251001` (the two models routines run on —
`routines/MANIFEST.md`), plus `claude-opus-4-7`, `claude-sonnet-4-6`, `claude-opus-5`,
`claude-sonnet-5`, `claude-fable-5-1` for local transcripts. Unknown model → its cost is null and the
id lands in `missing_models`; totals still sum the known ones. `cost(record_models) -> dict`.

### 1.6 Fold (`tools/usage/fold.py`)

`fold(root, as_of=None) -> dict` reads every `index/usage/*.jsonl`, keeps one record per `session_id`
(preference: `session-end` > `stop` > `publish`; ties → latest `recorded_at`), and returns:

```json
{
  "generated": "…", "records": 0, "runs": 0, "since": "2026-09-14",
  "by_routine": { "news": { "runs": 0, "tokens": {"input":0,"cache_write":0,"cache_read":0,"output":0}, "cost_usd_list": 0.0, "avg": {"tokens_per_run": 0, "cost_per_run": 0.0, "duration_s": 0, "messages": 0} } },
  "by_day": [ { "date": "2026-09-14", "runs": 0, "tokens": {…}, "cost_usd_list": 0.0 } ],
  "windows": { "7d": { "runs": 0, "tokens": {…}, "cost_usd_list": 0.0 }, "30d": { … } },
  "recent": [ { "session_id": "…", "stage": "…", "routine": "…", "edition": "…", "started": "…", "duration_s": 0, "messages": 0, "models": ["claude-opus-4-8"], "tokens": {…}, "cost_usd_list": 0.0 } ]
}
```

`recent` = the last 100 runs, newest first. `cache_write` = 5m + 1h. CLI: `python3 tools/usage/fold.py
[--root .] [--json]` prints the fold; with `--out PATH` writes it.

### 1.7 `publish.py` change (one step)

After the `footer` step, for every slug including `evaluator`:
`run_step("usage", [py, "tools/usage/record.py", "--find", "--stage", "publish", "--slug", args.slug, "--date", args.date], root, args.dry_run)`.
Non-fatal. If `tools/tests/test_publish.py` pins the step list, update the pin.

### 1.8 Jekyll

`_config.yml` `exclude:` gains `index/usage` and `index/admin` (same bare-`index` caveat as the
existing lines: never exclude `index` itself). `.claude/` is a dotdir and already ignored by Jekyll.

---

## 2. Admin contract

### 2.1 Worker routes (`tools/feedback-sink/src/worker.js`)

KV prefixes: `adm:` (queued actions; key `adm:<ts>:<id>`), `admin:` (`admin:snapshot`,
`admin:snapshot_meta`). Both are disjoint from `fb:`, `cred:`, `session:`, `chal:`, `readstate:`,
`prefs:`, so the existing `/drain` never sees them.

| Route | Auth | CORS | Body / result |
|---|---|---|---|
| `POST /admin/actions` | passkey session | site origin only | body = action (§2.2) → `{ok, id, action}`; 400 on shape error, 401 without session, 413 over 8 KB |
| `GET /admin/actions` | session | site origin | `{count, actions:[{key, …action}]}` — the queue, i.e. not yet applied |
| `GET /admin/snapshot` | session | site origin | the stored snapshot JSON, `Cache-Control: no-store`; 404 `{error:"no snapshot yet"}` |
| `PUT /admin/snapshot` | `FEEDBACK_TOKEN` bearer | `*` | body = JSON ≤ 4 MB → stores `admin:snapshot` and `admin:snapshot_meta` `{ts, bytes}` → `{ok, bytes}` |
| `GET /admin/drain` | bearer | `*` | like `/drain` over `adm:` (limit 200) |
| `POST /admin/ack` | bearer | `*` | like `/ack`, deletes only `adm:` keys |

Session routes roll the session (`rollSession`) like `/prefs`. `reader` is pinned from the session;
any `reader` in the body is ignored. `corsFor` treats `/admin/actions` and `/admin/snapshot` as
site-origin routes; `/admin/drain` and `/admin/ack` keep `*`.

### 2.2 Action schema (validated by the Worker, re-validated by `apply.py`)

```json
{ "id": "<uuid, Worker-assigned>", "ts": "<ISO, Worker-assigned>", "reader": "rafael",
  "type": "retire" | "restore" | "add" | "set",
  "domain": "example.org",
  "note": "≤ 500 chars, optional",
  "tier": "T1" | "T2",                       // add
  "streams": ["news", "ai-ml"],              // add: non-empty subset of news, ai-ml, science, weekend, sports
  "reach": "direct" | "proxy" | "search-only" | "blocked" | "blocked-paywall",   // add, default direct
  "status": "candidate" | "probation" | "established",                          // add, default probation
  "class": "outlet" | "hub" | "institutional",                                  // add, optional (else classify_domain)
  "probe": { "url": "https://…", "method": "curl" | "proxy" },                   // add, optional
  "field": "tier" | "reach" | "streams" | "status" | "class", "value": "…"      // set
}
```

`domain`: lowercase, `^(?=.{4,253}$)[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$`.
Unknown keys are dropped. `set` with `field: "status"` accepts only `candidate|probation|established|demoted`
(retire goes through `retire`).

### 2.3 Apply semantics (`tools/admin/apply.py`, run by the bridge on the Mac)

`apply_actions(root, actions, today=None) -> list[result]`, actions in key order. Load the registry
once with `registry.yaml_load`; write once with `registry.yaml_dump` (atomic replace) only if
something changed. Per action:

- `retire`: entry must exist and not already be `retired` → `status: retired`, lifecycle append
  `{date, event: retired, status: retired, note: "admin: <note>"}`.
- `restore`: entry exists with status `retired` or `demoted` → `status: probation`, lifecycle
  `{event: restored, status: probation}`.
- `add`: domain must not exist (else rejected with `"exists; use restore or set"`) → new entry
  `{class, tier, status, reach, streams, probe?, lifecycle: [{date, event: added, status, note}]}`;
  `reach: proxy` implies `probe.method: proxy` when a probe is given (the schema test pins
  `REACH_METHOD`).
- `set`: entry exists; field allowed; value validated; lifecycle `{event: "set <field>", note:
  "<from> -> <to> (admin: <note>)"}`.
- After all actions: `registry.validate(reg)` (new function, §3 S3) must return no violations; if it
  does, discard the in-memory registry, mark every action of this batch `rejected` with the violation
  text. Never leave a registry the schema test would fail.
- Every action, applied or rejected, is appended to `index/admin/actions.jsonl` as
  `{…action, "result": "applied"|"rejected", "error": null|"…", "applied_at": ISO}` and its key is
  returned for ack. A bad action is acked too — it must never loop.

### 2.4 Snapshot (`tools/admin/snapshot.py`, built by the bridge, pushed every tick)

```json
{ "generated": "…", "head": "<git sha>",
  "sources": [ { "domain": "…", "class": "…", "tier": "…", "status": "…", "reach": "…", "streams": [], "last_cited": "…"|null, "last_event": {"date":"…","event":"…","note":"…"}|null } ],
  "usage": <fold output from tools/usage/fold.py, or null if the module is missing>,
  "actions_recent": [ last 50 lines of index/admin/actions.jsonl, newest first ],
  "proposals_pending": [ { "file": "proposals/registry-2026-09-13.yml", "date": "2026-09-13" } ] }
```

`sources` sorted by domain. Proposals are listed only (the human gate stays manual for now).

### 2.5 Bridge-side client (`tools/admin/admin.py`, stdlib, mirrors `tools/feedback/feedback.py`)

Subcommands: `drain-apply` (GET `/admin/drain` → `apply_actions` → stash keys in
`$TMPDIR/admin-ack.json`), `ack` (POST `/admin/ack` with the stashed keys, then delete the stash),
`snapshot-push` (build → PUT `/admin/snapshot`). Env `FEEDBACK_WORKER_URL`, `FEEDBACK_TOKEN`, `REPO`;
identifiable `User-Agent`; every failure prints `WARN` and exits 1 (the bridge treats it as
non-fatal). The bridge script itself lives outside the repo
(`/usr/local/src/news-brief-ntfy-bridge/bridge.sh`); S3 writes the exact insertion as
`tools/admin/BRIDGE.md` and the architect applies it:

1. after the feedback drain (step 4): `python3 "$REPO/tools/admin/admin.py" drain-apply || echo "WARN: admin drain/apply failed (non-fatal)" >&2`
2. staging: `git add sources/ index/admin/ index/usage/` alongside the existing `feedback/ proposals/ index/ledger/`, and the `fb_staged` diff check covers them; commit message gains ` + admin actions` when `index/admin/` is staged
3. after a successful push (step 7): `python3 "$REPO/tools/admin/admin.py" ack`
4. last, every tick: `python3 "$REPO/tools/admin/admin.py" snapshot-push || echo "WARN: admin snapshot push failed (non-fatal)" >&2`

### 2.6 The page (`admin.html` + `_layouts/admin.html`)

- `admin.html`: front matter `layout: admin`, `permalink: /admin/`, `title: Admin`, `sitemap: false`.
  Layout emits `<meta name="robots" content="noindex,nofollow">`.
- Own document: `<!doctype html>`, `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">`,
  `{% include head/custom.html %}` (tokens, Anton, `window.__FB`), then one inline `<style>` and one
  inline `<script>`. No other theme include. No `position: fixed`, no `100vh`, no inner scroll
  container: the document scrolls. Bottom padding uses `env(safe-area-inset-bottom)`.
- Auth: reuse `syncSession:v1` in localStorage (`{token, reader, at}` — same origin as the homepage,
  so a signed-in reader is signed in here). Sign-in button runs the passkey login the homepage runs
  (`POST /auth/login-options` → `navigator.credentials.get` → `POST /auth/login`; copy the payload
  serialisation from `_layouts/home.html` around lines 2500–2530). Sign-out clears the key. No
  registration here.
- Sections, in this order, each a plain `<section>` with an `<h2>`:
  1. **Status line**: signed-in reader, snapshot age ("data as of 12:40, next bridge tick ≤ 10 min,
     07–22"), Worker reachability.
  2. **Usage**: four tiles (7-day tokens, 7-day cost at list, 30-day tokens, 30-day cost), a
     by-routine table (runs, tokens in/cache-write/cache-read/out, cost, avg per run, avg duration),
     a recent-runs table (started, routine, edition, models, tokens, cost, duration, stage). Numbers
     `tabular-nums`, thousands separators, cost to cents. State plainly when `usage` is null or empty
     ("no measured runs yet — first record lands at the next routine fire").
  3. **Sources**: a text filter, selects for status / stream / tier, a live count; a table with
     domain, tier, status, streams, last cited, last event; per row **Retire** (asks for an optional
     note, confirms) or **Restore**. Retired rows are dimmed but present. Sorting by domain; the
     filter is client-side over the snapshot.
  4. **Add a source**: form — domain, tier (T2 default), streams (checkboxes), reach, status
     (probation default), probe URL + method (optional), note. Validates client-side with the same
     rules as §2.2, posts, shows the result.
  5. **Pending actions**: from `GET /admin/actions`, refreshed every 60 s while the page is open, with
     a "queued, applies at the next bridge tick" label; **Recent actions** from
     `snapshot.actions_recent` with applied/rejected and the error text.
  6. **Evaluator proposals pending**: count and file names, read-only, with the sentence that they
     are applied by hand for now.
- Phone width first (390 px): tables become stacked rows below 700 px, or scroll inside their own
  `overflow-x: auto` wrapper; nothing else scrolls sideways. Buttons ≥ 44 px tall. Both colour schemes
  through the Folio tokens in `head/custom.html`.
- Harness: `tools/admin/harness.py --out /tmp/admin-harness.html [--fixture tools/tests/fixtures/admin-snapshot.json]`
  renders the layout with Liquid stripped, the fixture snapshot inlined, `window.fetch` stubbed for
  `/admin/*` and `/auth/*`, and a seeded session, so the page renders signed-in with sample data in a
  browser without Jekyll. The architect drives Chrome and the iPhone simulator against it; the harness
  only renders.

---

## 3. Slices (one agent each, own worktree, disjoint files)

Every slice: stdlib only (Python 3.9+), no PyYAML, no network in tests, tests under `tools/tests/`
named `test_<slice>_*.py`, `python3 -m unittest discover -s tools/tests` green before commit, commits
unsigned (`git -c commit.gpgsign=false`), **no Claude attribution or session trailer in any commit
message**, no pushes. Return: branch name, commit hashes, a paragraph of what was built, what was
verified and how, and anything left undone.

### S1 — usage measurement
Files: `tools/usage/__init__.py` (empty), `tools/usage/transcript.py`, `tools/usage/record.py`,
`tools/usage/pricing.py`, `tools/usage/fold.py`, `.claude/settings.json`, `_config.yml` (two exclude
lines), `tools/publish.py` (one `run_step`), `tools/tests/test_usage_transcript.py`,
`tools/tests/test_usage_record.py`, `tools/tests/test_usage_fold.py`, fixtures under
`tools/tests/fixtures/usage/` (a synthetic transcript with: repeated message ids, a `<synthetic>`
line, a subagent file, a shim first message, a publish.py Bash call, cache_creation both shapes).
Acceptance: dedupe by id proven by a test; routine/edition detection tests for all seven routines;
`--hook` with a fake git (a `PATH` shim that records argv) proves add/commit/push order, path-scoped
commit, the three-attempt push loop, exit 0 on every failure, and the Darwin gate; `--find` test with
a temp `CLAUDE_CONFIG_DIR`; pricing table with cited URL; fold preference order test;
`test_publish.py` still green.

### S2 — Worker admin routes
Files: `tools/feedback-sink/src/worker.js`, `tools/feedback-sink/test/smoke.mjs` (≥ 12 new checks:
each route's auth gate, CORS per origin, every validation branch of §2.2, drain/ack prefix isolation
from `fb:`, snapshot size cap, snapshot 404 before first push), `tools/feedback-sink/README.md` (API
section). Acceptance: `node test/smoke.mjs` exit 0; existing checks untouched; `wrangler deploy
--dry-run` (or `npx wrangler deploy --dry-run --outdir /tmp/ffs`) builds.

### S3 — apply, snapshot, bridge client
Files: `tools/admin/__init__.py`, `tools/admin/apply.py`, `tools/admin/snapshot.py`,
`tools/admin/admin.py`, `tools/admin/BRIDGE.md`, `tools/sources/registry.py` (add
`validate(reg) -> list[str]` mirroring `tools/tests/test_registry_schema.py`'s enumerations and the
`REACH_METHOD` probe rule, and `lifecycle_append(entry, date, event, status=None, note=None)`; CLI
unchanged), `tools/tests/test_admin_apply.py`, `tools/tests/test_admin_snapshot.py`,
`tools/tests/test_admin_client.py`, `tools/tests/fixtures/admin/`. Acceptance: every §2.3 branch
tested including the batch-rejection path; a round trip `yaml_load → apply(no-op) → yaml_dump` leaves
the real `sources/registry.yml` byte-identical; snapshot builds against the real repo (usage null when
`tools/usage/fold.py` is absent — S1 lands in parallel; import it by path with importlib and tolerate
absence); client drain/ack/snapshot-push tested with a fake `urlopen`; `test_registry_schema.py` and
`test_sources_*` still green.

### S4 — admin page
Files: `admin.html`, `_layouts/admin.html`, `tools/admin/harness.py`,
`tools/tests/fixtures/admin-snapshot.json` (a realistic snapshot: ~40 sources across statuses, a
usage fold with 12 runs over two routines, three recent actions incl. one rejected, one pending
proposal), `tools/tests/test_admin_harness.py` (the harness output contains the fixture's domains, no
`{{`/`{%` left, no external `src`/`href` except `fonts` from `assets/`, a `viewport-fit=cover` meta,
no `position:fixed`, no `100vh`/`100dvh`). Do not touch `_layouts/home.html` or
`_includes/head/custom.html`. Acceptance: harness renders; the page's JS has no dependency on the
homepage's script; all six sections present; form validation mirrors §2.2; a `--signed-out` harness
mode shows only the sign-in state.

### S5 — cold review (after S1–S4)
One reviewer per slice, reading the slice's diff against this plan: contract deviations, defects,
missing tests, anything that could break the live feedback path or a routine's publish. Findings only,
ranked, with file:line; no edits.

---

## 4. Integration (architect, main tree)

1. Rebase each slice branch onto `main` in order S1, S3, S2, S4; fast-forward merge; run the full
   suite after each.
2. `cd tools/feedback-sink && npm install && node test/smoke.mjs && npx wrangler deploy` (authed on
   this Mac). Post-deploy: `GET /admin/snapshot` with a live session must 404 with the JSON error;
   `/prefs` and `/readstate` unchanged (parity check with a live session token from the browser).
3. Apply `tools/admin/BRIDGE.md` to `bridge.sh`; run one tick by hand; confirm `PUT /admin/snapshot`
   returned `{ok}` and `GET /admin/snapshot` serves it.
4. Commit + push main. Watch fires every four hours on Haiku: the first `index/usage/<month>-watch.jsonl`
   record proves the hook path within four hours, before the next News run at 10:00 UTC proves the
   publish-time path. Both paths recorded = done; only publish recorded = hooks do not fire in the
   sandbox (see §5).
5. Open `/admin/` on the phone: sign in, retire a throwaway candidate, watch it move from pending to
   applied at the next tick, restore it.
6. ARCHITECTURE.md §1.1 entry + `routines/MANIFEST.md` note (hooks now ride the checkout).

Rollback: revert the main commits; `wrangler rollback` for the Worker; the bridge lines are guarded by
the same `FEEDBACK_WORKER_URL` check as feedback and are harmless without them.

## 5. Contingencies

- **Hooks do not fire in the sandbox** (no `stop` record after two Watch ticks): the publish-time
  record still measures every publishing run; Watch's idle ticks stay unmeasured. Next step would be a
  one-line `record.py --find --stage session-end` call at the end of every routine prompt
  (`routines/_shared/`), which is a prompt edit, not infrastructure.
- **No transcript exists in the sandbox** (both paths report not found): the sandbox does not persist
  `~/.claude/projects`. Then measurement needs the platform's own accounting, and the honest report is
  "not measurable from inside the run"; the architect escalates to the owner rather than reviving
  the estimate.
- **Worker deploy breaks a live route**: `wrangler rollback`, then fix under the smoke test.

## 6. Out of scope, noted

Applying evaluator proposals from the page (needs a block-scalar YAML reader the registry module does
not have); measuring local Mac sessions into the same ledger (the parser already handles them —
`USAGE_RECORD_LOCAL=1 record.py --transcript …`); a public "measured tokens" line in the
how-this-works modal; changing `reader-profile/source-weights.yml` from the page.
