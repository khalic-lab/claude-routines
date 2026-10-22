# Cold review — 2026-10-22

Branch `review/cold-fable-2026-10-22`, worked in a separate worktree, nothing pushed. Commits are
GPG-signed (signing inside the sandbox fails because gpg cannot reach its agent socket, so each
commit ran with the sandbox off; signing itself was never disabled). Baseline before any change:
`python3 -m unittest discover -s tools/tests` → 792 tests OK. After: 807 OK (15 new).

## What the project is

An automated news desk with no server of its own. Remote claude.ai routines (bootstrap shims that
`git pull` and read `routines/<slug>.md`) research and write briefs into `_posts/`; `tools/publish.py`
records the stories (embeddings, ledger, anchors), rebuilds `_data/homefeed.json`, and commits and
pushes to `main`; GitHub Pages renders the front page from that JSON with Liquid alone, and a few
small ES modules add read-state, votes and the Unread refill on top. A Mac-side bridge (outside the
repo) drains notifications and reader feedback; two Cloudflare Workers hold feedback and embeddings.
The individual brief pages are unpublished; the homepage board is the only reading surface, plus
the Sunday evaluator reviews.

The character worth protecting: the template decides nothing, the builder emits data, tests pin
the shapes, and every surface works without script.

## What I found

### Dead or stale

- **`README.md` linked `CLAUDE.md`**, deleted months ago. `_config.yml` and
  `tools/check_publish.py` still excluded `CLAUDE.md`, `HANDOFF.md`, `bridge.sh` and `briefs/`,
  none of which exist. `routines/README.md` pointed at `../CLAUDE.md` too. *Fixed.*
- **`permalink` on every feed story** pointed at `/YYYY/MM/DD/<stream>/`, pages retired on
  2026-07-18. Nothing read it except one test. *Removed.*
- **The colophon's "RSS feed" was `/feed.xml`**, which jekyll-feed builds from published posts.
  Every brief is `published: false`, so the feed only ever listed the evaluator reviews. *Replaced
  by a story feed, see below.*
- **`homefeed.json` carries four lists the page never reads**: `stories`, `editorials`, `topics`,
  `count`. `board` is a superset copy of `stories`, so roughly 40% of the 350 KB file is duplicate.
  Still read by `tools/evaluator/surface.py` (card counts per edition) and by the builder's own
  tests, so I left it; retiring it is the first item under "next".
- **`index/stories/*.jsonl`, the legacy per-edition index, is still live** beside the ledger
  (`index/ledger/`). The 2026-07-07 migration said "retire at end of migration"; it never was.
  `dedup.py`, the feed builder's join, `store/anchor.py`, `sources/registry.py` and
  `sources/institutions.py` all still read it.
- **One-shot migrations ship as first-class commands**: `tools/store/backfill.py` (last touched
  2026-07-07) and `dedup.py backfill` / `affil-backfill` (2026-07-10). They are idempotent and
  tested, so they are recovery tools rather than dead code, but they sit in the same `--help` as
  the daily `check`/`record`/`lint`.
- **`.gitattributes` names `sources/last-cited.jsonl`**, which does not exist;
  `sources/candidates.jsonl` is empty.
- **The public "How this works" wide diagram still shows a "GMAIL DRAFT" delivery node**
  (`assets/diagrams/how-it-works-wide-*.svg`, source `diagrams/06-public-how-it-works-wide.mmd`).
  There is no Gmail anywhere in `routines/` or `tools/`. The mobile SVGs are already clean. It
  needs a mermaid re-render, which I could not do offline.
- **`ARCHITECTURE.md` is 1,316 lines / 116 KB**: §1 "Current state" is a reverse-chronological
  changelog of quoted dated blocks, and §3–§8 are superseded design history (pgvector, S3),
  marked as such inline. It is honest but it is not an architecture document any more.
- `diagrams/01–05` were last verified 2026-07-03; `docs/SPIKE-writer-token-levers.md` still
  lists open levers; `test_liquid_balance.test_accepts_the_real_shapes_home_uses` exercises
  `feed.stories`/`feed.editorials` loops the page no longer has (harmless).
- **`_layouts/admin.html` duplicates the passkey login** from `assets/js/sync.js` ("copied, not
  imported", by its own comment).

### Fragile

- **The embed-proxy bearer token is committed** as a default in `tools/dedup/dedup.py` (line 98)
  and once in `tools/plane/query.py`. The repo calls it low-value, but it gates Workers AI spend.
  Removing the literal would break the live routines until their `session_context` carries
  `EMBED_TOKEN`, which cannot be done from this checkout, so it stays, as a finding.
- **`publish.py` ignores the feed builder's exit code** (`_, feed_out = run_step_out("feed", …)`
  near line 591), as the builder's own comment notes. Today the builder only exits non-zero under
  `--strict-parity`, so nothing is lost yet, but the first fatal condition anyone adds there will
  be silently swallowed. Patch:

  ```python
  ok, feed_out = run_step_out("feed", [py, "tools/build_stories_feed.py"], root, args.dry_run)
  alert_missing_stories(root, args.slug, args.date, feed_out, args.dry_run)
  if not ok:
      write_alert(root, "feed-build-failed", args.slug, args.date, feed_out)   # same stub path
  ```

  and decide in the fatality matrix whether a failed feed build should still push.
- **`tools/build_stories_feed.py` is 1,800 lines** doing parsing, the record join, ageing, the
  quota, ranking, the page views, edition parity, the masthead copy and a piggybacked stats
  build (imported by path from `main()` so no prompt needed wiring). Every piece is well
  commented; the file is still the one place a newcomer cannot hold in their head.
- **The golden feed test pinned the story shape by special-casing `sid`**: any additive field
  either had to be popped after the board was built (`event_date` is) or needed test surgery.
  Now it compares whole stories and a new field means a deliberate re-capture.
- `.claude/settings.json` is tracked but marked skip-worktree, so it is absent in a fresh
  worktree while `git status` reads clean. Surprising, not wrong.

## What I simplified, and why

1. **Stale names** (`741e9d14`): README, `routines/README.md`, `_config.yml` excludes and
   `check_publish.REQUIRED_EXCLUDES` now name only files that exist; the README's agent entry
   points at `routines/README.md`, `routines/MANIFEST.md` and `tools/admin/BRIDGE.md`; the
   `sports` slug is listed. `REVIEW.md` is excluded from the Pages build like the other root docs.
2. **`permalink` dropped** (`68534b0d`): a dead field on every story and every board item.
3. **Golden test compares whole stories** (`68534b0d`): `test_feed_sid` no longer hard-codes
   which keys may appear; the golden fixture was re-captured and now pins the full current output,
   including `board`, so an accidental change anywhere in the story shape fails one clear test.

I did **not** retire `feed.stories` and friends, the legacy index, the backfill commands or the
token default: each has a live reader or needs a remote change first. They are listed under
"next" with the concrete step.

## What I added

1. **Multi-source stories** (`68534b0d`, `e95a6e49`). A story often cites two or three outlets
   (124 of the 511 stories filed in October; 35 of the 80 on today's board) but the feed kept only
   the first URL. `parse_post` now emits `sources`: one entry per distinct domain, prose order,
   primary first, `{url, domain, label}` with the label being the citation text minus its date
   ("DW, 1 Oct 2026" → "DW"). `url` / `source_domain` are unchanged (still the headline link and
   the record-join key). The meta line prints every domain, alternates as links; an old-shape feed
   still prints the primary alone.
2. **Discuss** (`e95a6e49`). Every story's footer carries a plain link to
   `https://claude.ai/new?q=…` prefilled with the headline, deck, prose (cut at 500 characters),
   the desk's "why it matters", the desk and day, and every source URL, ending with a request to
   separate what the sources establish from what is open. No script, no Worker, no change to any
   routine; editorials do not get it (nothing to check them against). The "How this works" text
   mentions it in one sentence.
3. **Story RSS** (`e95a6e49`). `stories.xml` is an RSS 2.0 feed over the board: one item per
   story, source as the link, store id as the guid (a running story re-told under the same source
   updates rather than duplicates), the sources listed in the description, desk and beat as
   categories. Linked from the colophon and a `<link rel="alternate">` in the head; `/feed.xml`
   stays for the reviews. Covered by the Liquid balance check.
4. **Tests**: `tools/tests/test_feed_sources.py` (15 tests: the extractor, the feed shape, the
   template wiring, the feed page).

Nothing added needs infrastructure: the next push to `main` publishes `stories.xml` and the
Discuss links as part of the normal Pages build. `_data/homefeed.json` is rebuilt in the branch
so the page has the data on day one; the next routine publish regenerates it identically plus the
new edition.

## Verification

Ran here:

- `python3 -m unittest discover -s tools/tests`: 807 tests, OK (1 skipped), 56 s.
- `python3 tools/check_publish.py`: PUBLISH-SAFE after every change.
- `tools/build_stories_feed.py` against the real posts: the rebuilt `homefeed.json` differs from
  HEAD only in `sources` and `permalink` (checked field by field by script); `stats.json` is
  byte-identical.
- The templates were rendered with the real Liquid 4.0.4 gem (installed into the session
  scratchpad, with small stubs for Jekyll's `include` tag and its `relative_url` / `absolute_url` /
  `xml_escape` / `date_to_rfc822` filters) against today's `homefeed.json`: `stories.xml` is
  well-formed XML with 80 items; the row, card, meta and editorial partials and the whole
  `_layouts/home.html` render without a Liquid error; every Discuss prompt decodes to the intended
  text with all source URLs; an old-shape story prints its primary domain only.

Not run, and why:

- The Docker Pages build (`tools/verify/build.sh`): the OrbStack daemon is not running in this
  session. The Playwright suite needs that build.
- The claude.ai prefill itself: no browser from the sandbox. The link follows the documented
  `claude.ai/new?q=` scheme; a human click is the remaining check.

## What I would do next

1. **Retire `feed.stories` / `editorials` / `topics` / `count`.** Switch `tools/evaluator/surface.py`
   to count `board` items with `kind == "story"`, drop the four keys and the `event_date` pop in
   `main()`, re-capture the golden. Saves ~40% of the JSON and removes the last "pinned shape" caveat.
2. **Retire `index/stories/`.** Make the feed join and `anchor.py` read the ledger's materialised
   view; keep the per-edition files only as the `record` step's output if dedup still wants them.
3. **Split `build_stories_feed.py`** into parse / join / rank / views modules with `main()` as
   orchestration; 807 tests make this a mechanical refactor.
4. **Gate the publish on the feed build** with the patch above, then make parity fatal.
5. **Rotate the embed token**: set `EMBED_TOKEN` in the six triggers' `session_context`, confirm a
   run, delete the two literals.
6. **Turn `ARCHITECTURE.md` into a 200-line current-state document** and move the dated blocks to
   `docs/CHANGELOG.md`; re-render `diagrams/06` without the Gmail node and re-verify 01–05.
7. **`admin.html` should import the passkey module** from `sync.js` instead of carrying a copy.
8. **Small follow-ups to the new features**: mark a story read when Discuss is clicked (one
   selector in `board.js`'s headline-click handler); per-desk feeds (`stories-news.xml`, …) if
   anyone asks; and since the writers already tag `[single-source]`, the prompts could ask leads
   to carry a second source now that the page shows them.
