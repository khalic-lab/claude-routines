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

## What I simplified, and why

1. **Housekeeping** (`741e9d14`, corrected in round 2): the README lists the `sports` slug and
   `REVIEW.md` is excluded from the Pages build like the other root docs. The same commit also
   removed `CLAUDE.md`, `HANDOFF.md`, `bridge.sh` and `briefs` from the excludes and the README
   pointers to `CLAUDE.md`, on the mistaken reading that those files were gone from the repo.
   They were only absent from this worktree; the excludes are deliberate guards and `CLAUDE.md`
   is a private file that must never publish. All of that is restored.
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
   the record-join key). The meta line printed every domain, alternates as links; round 2 moved
   the list into the story's fold and the meta line names the primary alone again (see below).
2. **Discuss** (`e95a6e49`). Every story's footer carries a plain link to
   `https://claude.ai/new?q=…` prefilled with the headline, deck, prose (cut at 500 characters),
   the desk's "why it matters", the desk and day, and every source URL, ending with a request to
   separate what the sources establish from what is open. No script, no Worker, no change to any
   routine. Round 2 rebuilt it: the prompt is built at load from the page, editorials and whole
   day editions get one too, and a click reads the story (see below).
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

**Merge note.** `main` rewrites `_data/homefeed.json` on every publish, so merging this branch
will conflict on that file. It is derived: take `main`'s copy, run `python3 tools/build_stories_feed.py`
on the merged tree, commit the result. (`publish.py` says the same about its own rebase retry.)

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

Not run in round 1, and why (both ran in round 2, see below):

- The Docker Pages build (`tools/verify/build.sh`): the OrbStack daemon was not running in the
  round-1 session. The Playwright suite needs that build.
- The claude.ai prefill itself: no browser from the sandbox. The link follows the documented
  `claude.ai/new?q=` scheme, and the prompt is encoded with `%20` for spaces so it decodes the
  same under a form-style and a plain URI decoder; a human click is the remaining check.

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
8. **Small follow-ups to the new features**: ~~mark a story read when Discuss is clicked; per-desk
   feeds~~ (both done in round 2); and since the writers already tag `[single-source]`, the
   prompts could ask leads to carry a second source now that the page shows them.

---

# Round 2 — the frontend rebuild (2026-10-22, same day)

The owner's reply to round 1 was "i was hoping for a frontend rebuild". Round 2 first undoes the
`CLAUDE.md` mistake, then rebuilds the page around multi-source stories, Discuss and the story
feed, and runs the real Pages build and the browser suite as the deliverable. Everything is on
`review/cold-fable-2026-10-22`; nothing was pushed, deployed, or touched outside this worktree.

## Commits (signed)

| Commit | What |
|---|---|
| `bacfdd32` | Restore the `CLAUDE.md` pointers and the publish guards (`_config.yml` excludes, `REQUIRED_EXCLUDES`, both READMEs, two findings deleted from this file) |
| `31efc382` | `build.sh` copies only files present in the checkout (two tracked files are absent from this worktree on purpose; the Pages build died on them) |
| `0d96d4b5` | Builder: the desk's credibility flags and the source count on board stories |
| `358c20d1` | Suite: the reason-box step undoes itself before the All layout check (the 20 baseline failures) |
| `10aca334` | Page: every outlet in the fold, the flags, Discuss on stories, editorials and days; the suite's new gates and the stronger void measure |
| `22afcc78` | Feeds: one include renders `stories.xml` and a feed per desk, with the flags; the suite's feeds runner |
| the REVIEW.md commit | this section |

## What the rebuild is

**Builder** (`tools/build_stories_feed.py`). A story's credibility is now data, not prose: a
fixed vocabulary `FLAGS` (`single-source`, `disputed`, `unconfirmed`, `rumour`, `preprint`,
`vendor-pr`, `official-pr`, `ongoing`), read from the record's `tags` and the writers' inline
`[preprint]`-style markers, tolerant of brackets, backticks, case and "ongoing since …". Board
stories carry `flags` (only when non-empty) and `n_sources`; `feed.stories` keeps its pinned shape
(`flags` is popped like `event_date`). Today: 45 of the 80 board stories are flagged (preprint 17,
ongoing 13, vendor PR 8, single source 6, official PR 6, disputed 1); 35 cite more than one outlet.
`_data/homefeed.json` is rebuilt in the branch and differs from the committed one only in those
two keys; `stats.json` is unchanged. Tests: `test_feed_flags.py` (vocabulary, tag parsing, the
board carrying them); the golden feed re-captured.

**Page.** Before → after, file by file:

| Before | After |
|---|---|
| `home/meta.html`: beat, primary, then every alternate domain as a link (round 1) | beat and the primary alone; the list moved into the fold |
| — | `home/signals.html`: the flags and "3 sources" in the header line of a folded item |
| — | `home/sources.html`: every outlet with its label and domain, each a new-tab link, closing the fold |
| `home/actions.html`: Discuss (stories only, full prompt in the href), More, ✓, votes | Discuss first for a story or an editorial (`data-discuss`), a short no-script prompt in the href; then the same controls |
| `home/front-card.html`, `home/row.html` | wire signals and sources; a story with sources always has a fold |
| `home/editorial.html` | passes itself to Discuss |
| `_layouts/home.html` | masthead "Story feed · RSS"; the key note names flags, counts and Discuss; every day header has a links line with "Discuss this edition" (the prompt lists the day's headlines) before the desk's-view jumps |
| `head.html` | a `<link rel="alternate">` per feed |
| `home/hiw.html` | "Reading this page" explains flags, counts, Discuss and names the feeds |
| `stories.xml` (the whole feed inline) | `_includes/storyfeed.xml` rendered by `stories.xml` and by `feeds/<desk>.xml` for each of the five desks; items carry the flags |
| `assets/css/components.css` | `.flag`, `.srcn`, `.srcs*`, `.discuss`; the meta-line alternates' rules gone |
| — | `assets/js/discuss.js` (5.6 KB): builds every Discuss prompt once at load from the page's own text, and again when the refill adopts a reserve copy |
| `assets/js/main.js`, `assets/js/board.js` | init + adopt hook; a Discuss click reads the item like a headline click |

**Not rebuilt, on purpose:** the read-state and refill engine (`board.js`, `refill.js`,
`store.js`, `sync.js`, `fold.js`, `og.js`, `fresh.js`, `votes.js`, `dialog.js`, `propose.js`,
`prefs.js`, `probe.js`) and the layout, base, state and utilities sheets. They implement the
owner rulings of 2026-09-25 (All's front composed at load, a tick only dims, focus survives a
recompose, the sync roam rules) that the suite pins with about 35 line-level faults. Rewriting
them would have meant rewriting the proof as well, for no reader-facing gain the brief asked
for. The brief left the depth to me; I went deep where the ask was and left the engine alone.

## Decisions, with the reasoning

1. **Where the Discuss prompt lives.** Measured on the baseline build: 96 template-written
   `claude.ai/new?q=` hrefs were 139 KB of a 600 KB homepage, and every story that also sits in
   a reserve `<template>` carried its prompt twice. Three options: keep them (simple, works
   without script, but the page carries a second copy of its own prose, growing with every
   source and flag); build on click (small, but a middle-click, "copy link", a keyboard activation
   and the suite would each see a different href, and the link would do nothing without script);
   build once at load from the text already on the page (chosen). The template still writes a
   short no-script prompt (headline and primary source; an editorial's title; a day's headlines),
   so the link always works; `discuss.js` rebuilds it from the headline, deck, body (cut at 600
   characters), why (300), flags, every source with its label, desk and day, with the same opening
   request as round 1. Result: 115 links in 28 KB; the homepage is 537 KB with the 96 source
   lists and 59 flags added. The href is built once, not per event, so every way of following
   it sees the same URL, and the suite can read it.
2. **Discuss on editorials and days.** An editorial is discussed as what it is: the prompt says an
   AI wrote it as a desk's view, not reporting, and asks which of its claims would need a source.
   A day's prompt lists every story with its primary source and flags, biggest first. Round 1's
   reason for leaving editorials out ("nothing to check them against") was the wrong frame: the
   point is to argue with the opinion, and the sources are one click away in the same prompt.
3. **A Discuss click reads the story**, like opening its article (round 1's "next" item 8): one
   selector in the two click handlers. It dims, never re-filters.
4. **Flags are a fixed vocabulary in the builder**, never free text from a writer: the page shows
   only labels the vocabulary knows, in its order, and the suite checks them against the board.
   They are outlined like the event label, in ink (never red: the page's red is the lead's).
5. **Feeds.** One include, since five near-identical files would drift. Per-desk feeds because a
   reader who wants the Science desk should not subscribe to the sports results. The items carry
   the flags so a reader sees "Preprint" in their feed reader too.
6. **Spaces as `%20`** in every href (round 1's late fix, now a fault in the suite).

## Reader-facing behaviour dropped or changed

- The meta line no longer lists alternate outlets (round 1, `e95a6e49`); the fold lists every
  outlet instead, and the header line says how many. The folded index line keeps the shape the
  2026-09-24 plan asked for (R2).
- Without script, the Discuss prompt is shorter than round 1's (headline and primary source, not
  the whole story). With script it is longer than round 1's (flags, labels, the day).
- Nothing from before round 1 was dropped. Added: the day header's links line now always shows
  (it carries the day's Discuss link, whether or not the day has an editorial).

## Verification

**Baseline first** (HEAD `bacfdd32` plus the `build.sh` fix, before any page change), so that
round 2's own effect is separable: the Docker Pages build (`ghcr.io/actions/jekyll-build-pages
v1.0.13`) exit 0, 0 Liquid warnings, 28 pages; the suite **3621 passed / 20 failed / 0 skipped**,
fault self-test **72/73**. The 20 failures were all `refillAll` (front-read) at every width and
engine, "84–86 of 88 moved": the suite's own step (c) had opened a reason box and a vote note in
a card and left them; on today's data that card is one of All's load-time cards, so everything
below it "moved". The page never moved anything. Fixed in the suite (`358c20d1`); the assertion
itself is unchanged. The MISSED fault was `gap`: its void measure read the article's child blocks,
and since the photo-beside grid (2026-09-25) a stretched grid row lets a block cover the slack,
so a 30%-wide open card measured as void-free. Fixed by measuring the content's own line boxes
(`10aca334`); the same fault now reads 233 px → 4184 px.

**Final** (this tree):

- `tools/verify/build.sh`: exit 0, 0 Liquid warnings, 0 Gemfile warnings, 28 HTML pages, plus
  `stories.xml` and `feeds/*.xml`.
- `tools/verify/suite.mjs` (every state, Chromium at 8 widths and WebKit as iPhone 15 and at
  1024, light and dark, no-JS, contract, two tabs, pages, feeds, the fault self-test and the
  screenshots): **ALL 3743 passed / 0 failed / 0 skipped**, fault self-test **85/85 caught**
  (baseline default@1440 clean), exit 0. The 85 include the 81 the suite had after the page
  commit plus the four feed faults; the 73rd of the baseline (`gap`) is among them.
- `python3 -m unittest discover -s tools/tests`: 820 tests, OK (1 skipped).
- `python3 routines/assemble.py check`: OK, exit 0.
- `python3 tools/check_publish.py`: PUBLISH-SAFE after every commit.
- Worker contract: the `contract` state passes (same storage shapes, same request bodies, no
  field added); no Worker was touched or called.

**Every assertion changed or added**, what it checked before and what it checks now:

| Assertion (state) | Checked before | Checks now | Why |
|---|---|---|---|
| refillAll (front-read) | Before: compared every item's document rectangle at load with its rectangle after the Unread sequence and back under All, but step (c) (refillFocusTyping) had opened a reason box and a "sign in to vote" note in card FOCUS_L and left them; on today's data FOCUS_L is one of All's load-time cards, so the open box made 84–86 of 88 items "move" and the assertion failed at every width and engine (baseline run). | Now: the same comparison, after step (c) retracts its vote (which hides the box) and clears the note, so the layout difference is the recompose's alone. The assertion itself is unchanged and as strict. | A test's own side effect was being measured; the page never moved anything. |
| gap, gapDesk, gapLead (expanded) | Before: a front cell's void was the largest gap between the rectangles of its article's child blocks (and the cell's bottom), plus any partial flex line. Since the photo-beside grid (2026-09-25) an open card's `article` is a grid whose stretched rows let a child block (`.fc__text`) cover the slack, so a 30%-wide open rest card measured as void-free: the suite's own `gap` fault was MISSED on the baseline run ("folded max 220px, after one expand 22px"). | Now: the void is measured between the content's own boxes (each text node's line boxes via Range.getClientRects, each img/svg; `.vh` text excluded), same cells, same partial-line rule, same tolerance (open ≤ folded + 50px). On the real page the numbers move by the padding only (1440px: folded 217→233, open 22→30; 1024px: 226→237; 768px: 276→287) and all three keep passing at every width and engine; the gap fault now reads 233px → 4184px (1440) and is CAUGHT. | The measure was blind to the defect it exists to catch. Strengthened, not loosened. |
| fullRow (expanded) | Before: no fault keyed to it. | Now: a fault `.js .fcards--rest > .fc.is-open{flex-basis:30%!important}` is keyed to fullRow as well as gap (an open card 399 of 1198px). The assertion itself is unchanged. | The same break must fail both gates that guard it. |
| sources (default) NEW | — | On every copy of a story (card, row, reserve template): `.src__dom` == board `source_domain`; the `.srcs a` hrefs and labels == board `sources` in order (each target=_blank rel=noopener); `.srcn` reads "N sources" iff N > 1; the list is hidden on a folded row/card and shown inside the item's box once opened (one row and one front card are opened and closed again). Faults: `.srcs{display:none}` (hidden when opened) and an init script removing one `<li>` (order/completeness). | Multi-source stories are the first-class behaviour the brief asks for. |
| flags (default) NEW | — | On every copy of a story the `.flag` texts == the board's `flags[].label` in order; on a shown item each flag is visible inside it. Passes with zero flags only when the board has none (and then no flag may show). Fault: an init script inserting a bogus `<span class="flag">Disputed</span>` into the first row's meta line. | The credibility flags are reader-facing claims about sourcing; they must be the builder's, never invented or dropped by the template. |
| discuss (default) NEW | — | Exactly one `a.discuss` per live story copy, per editorial and per day; href origin `https://claude.ai`, path `/new`, has `q`, contains no raw `+`, target=_blank rel=noopener. A story's decoded prompt contains the headline, every source label and url, every flag label, the desk label, the first 40 chars of the summary and its day (card label or day heading); an editorial's: its title, desk and the first 40 chars of its first paragraph; a day's: its heading and every story's headline and primary url. Faults: discuss.js without its "Sources:" lines; discuss.js writing `+` for spaces. | The prompt is built at load from page text (the 140 KB of template-written hrefs are gone), so the suite must prove the rebuilt prompt is complete and the encoding survives either decoder. |
| discussRead (default) NEW | — | A click on a day row's Discuss link (navigation cancelled by a one-shot capture listener) marks the row read, stores it in `homeRead:v1` and drops the Unread count by one; its ✓ un-reads it, removes it from storage and restores the count. Fault: board.js's click handler reading `.hl a` only. | Opening a conversation about a story is reading it, like opening its article; the suite pins that the two paths behave the same. |
| refillDiscuss (front-read) NEW | — | After the Unread refill, every promoted copy (reserve card adopted from its `<template>`, and the promoted Desk's view) has a Discuss prompt containing the headline, every source url and the desk label (the template fallback has no desk, so this proves discuss.js ran on the adopted copy). SKIP only with no promoted copy. Fault: main.js adopt hook without `prepare(el)`. | Reserve copies are rendered inert in templates; the href must be built when they enter the document. |
| no-js | Before: hidden-text check over `.fold, .why, .sum, .ed__body, .ed__disc, .hl, .ptag`; no Discuss check. | Now: also `.srcs, .flag, .srcn` must show without script; every `a.discuss` in `.page` is visible, its href is `https://claude.ai/new?q=` with no raw `+`, and its decoded prompt contains the story's headline and primary url (an editorial's title; every headline of the day). Part of the single no-js pass/fail line. | Discuss, the list and the flags are plain HTML by design; the no-script run proves it. |
| feeds NEW (own runner, chromium 1024 + WebKit iPhone 15) | — (round 1's stories.xml was checked only by the Liquid harness and a static unit test) | `stories.xml` and `feeds/<desk>.xml` for every desk in `routines/src` (the suite's CAP keys): fetched from the served site, parsed with DOMParser as application/xml (any parse error fails), first bytes the XML declaration, atom self link = the production URL of that file, lastBuildDate parseable; the items' guids == the board's story sids in board order (a desk feed: that desk's stories); each item's title == headline, link == primary url, pubDate parseable, desk label among its categories, description starting with the summary, carrying "Why it matters" + the why, every source as `<a href="url">label</a>`, every flag label (and no "Flagged by the desk" on an unflagged story); the homepage head carries a `<link rel=alternate type=application/rss+xml>` per feed and the masthead a visible link to stories.xml. Faults (served rewritten through route()): stories.xml without its last item; the biggest desk's feed with its first two items swapped; stories.xml with one source anchor removed; the homepage without its stories.xml alternate link. | The feeds are reader-facing output that only the Pages build produces; they were untested in a browser. |

Not run, and why: the claude.ai prefill itself (no browser leaves the machine; the suite proves
every href decodes to the intended prompt under either decoder); a real Pages deploy (out of
scope). The screenshots are in the session scratchpad.

**Merge note**, again: `main` rewrites `_data/homefeed.json` on every publish, so the merge will
conflict on it. Take `main`'s copy and run `python3 tools/build_stories_feed.py` on the merged
tree; the builder in this branch adds `flags` and `n_sources` to the board.

## What I would do next (round 2)

1. Let the writers' prompts ask for a second source when a lead would otherwise be
   `single-source`, now that the page shows the flag and the count.
2. The "Reading this page" text and the key note say the same things twice; one of them could go.
3. The remaining round-1 items (retire `feed.stories`, the legacy index, the token) stand.

# Round 3 — the full frontend rebuild (2026-10-25)

Round 2 kept the design and the engine. This round rewrites the homepage's layout, includes, CSS
and JavaScript from scratch against the behaviour contract (C1–C16 in the round-3 brief), rewrites
the Playwright suite alongside, and moves the admin, prompts, 404 and evaluator pages onto the new
design system. This section opens with the design note (written before any page code) and closes
with the record of what was built, verified and measured.

**Signing.** `gpg-unlock --status` reported the personal key uncached at the start; `gpg-unlock`
failed because the 1Password CLI is signed out (`op whoami`: "account is not signed in";
`~/.gnupg/gpg-agent.conf` does allow presets, so the agent is not the blocker). Per the brief,
every intended commit is appended to `/tmp/argon-ux/shots-r3/pending-commits.md` with its paths
and a `git write-tree` SHA of the worktree at that point, and the status is re-checked before each
commit point. **Docker.** The OrbStack daemon socket was absent when the first build was
attempted; a poller waits for it (the brief: poll, never skip).

## Design note

### 1. Findings taken and rejected

Every critical and major finding of the UX evaluation (`/tmp/argon-ux/review.md`), with its
disposition. "Fixed" means built in this round; "proposal" means written up for the owner under
§6 and the current behaviour kept; "rejected" gives the reason.

| # | Finding (severity) | Disposition |
|---|---|---|
| F1 | Lead boots open; one story fills the first screen; right 40% of the card empty (critical) | **Fixed.** Nothing boots open. The builder no longer emits `boot_open` (R33 was AG/Open); the folded lead follows R2: kicker, headline, image slot, "Why it matters", footer line with More. At 1440 the first screen shows the lead, the Desk's view and the three feature cards. |
| F2 | Headline click should expand in place and collapsing should mark read; outlet link only on source chips (critical) | **Proposal** (§6.1). The read contract (headline click or ✓ reads; More never reads; voting never reads, R26) is the owner's since July. Built instead, inside the contract: More is a labelled 44 px control on phones, not a 9 px chevron; the headline link keeps its "(opens in a new tab)" text and the source domain beside it says where it goes. |
| F3 | Metadata soup: up to seven tokens above a headline, the date three times (critical) | **Fixed.** One kicker per item (tier glyph + word, desk, "Just in" in red per R36), the date only where it is new information (masthead, day heading, an older card's own day), epistemic flags as the only outlined chips, the event date and source count as plain muted text, a 12 px floor on every label. |
| F4 | Beat counts jump to the union under a held beat (critical) | **By design** (C12, PLAN decision 4); the counts are honest under multi-select. **Fixed the unsignalled part**: pressed chips carry a check mark and the group is labelled "Beats · pick any". **Proposal** for single-select (§6.3). |
| F5 | Phone: two-row 88 px bottom bar clips controls; targets under 44 px (critical) | **Fixed.** One 52 px bar (+ `env(safe-area-inset-bottom)`, R16) at the bottom (R13): read state, Beats, Days, Sync; beats and the day jump open bottom sheets (`<dialog>`, top layer, so the bar clips nothing). Every control on phones is at least 44 px tall. |
| F6 | Open day row strands controls in the left column over a void; a folded row without a why leaves the right 58% blank (major) | **Fixed.** From 1024 px a folded row with no why spans both tracks; an open row keeps its headline on the left and runs body, why and then the controls down the right track, so Less, ✓ and the votes sit where the eye finishes. No CSS multi-column anywhere (decision 3 reopened, §3). |
| F7 | "↑ On the front" pointer rows take a quarter of a phone screen (major) | **Fixed** by reopening PLAN decision 1 (§3): no pointer rows. The day header counts what is on the front and links to it ("4 on the front ↑"); C9 holds (every story once, the day says what it lent). |
| F8 | Refilled front: a Wednesday lead under a "Thu 22 Oct" heading (major) | **Fixed as presentation.** The front heading carries no date; the subtitle says "from Wed 21 Oct" and an older card prints its own day in its kicker. The pick is C10 and unchanged. |
| F9 | Rail: rotated nameplate wastes 250 px, beats clipped at 900 px, controls split between corners (major) | **Fixed.** Horizontal wordmark; the rail (≥1280 px) holds every control in R19's order: nameplate, edition, read state, Sync, beats, then How this works, the weekly review, RSS, and the closed key. No top bar at that width, so nothing is split and nothing dead sits above the sheet (R20). Fits 804 px. |
| F10 | Front card voids: open card text at 30 em, equal-height stretch holes, Desk's view stretched to the lead (major) | **Fixed.** Cards are start-aligned (no stretch, no boxed void); the Desk's view is a ruled column, not a filled panel; an open card with a photo sets the photo beside the text and the text at the measure. R7 keeps the folded editorial at title + disclosure + More. |
| F11 | Root 16/18/20/22 px: 9.6 px labels on phones, 23 px body at 1440 (major) | **Fixed** by reopening PLAN decision 11 (§3): the root stays 16 px; body 17–18 px; labels never under 12 px. |
| F12 | Admin: `[hidden]` broken, no way back, `window.prompt`/`confirm` (major) | **Fixed.** `[hidden]{display:none}` in the layout's one `<style>`; "Front page" link in the header; retire/restore use an inline confirmation row; one sign-in control when signed out. |
| F13 | Evaluator page: two near-identical H1s (major) | **Fixed.** When a post body opens with its own `<h1>`, the layout prints the kicker and date only and styles the body's heading as the title: one h1. |
| F14 | No-JS: every text expands, no day navigation (major) | **Partly fixed, rest a proposal.** The day jump is plain links and renders without script; the pointer rows are gone. Folding without script collides with PLAN decision 9; `<details>` is proposed in §6.2 and not shipped. |
| F15 | `columns: 2` in open rows and editorials (minor) | **Fixed** (see F6, decision 3). |
| F16 | How-this-works diagram cut in half (minor) | **Rejected as stated** (the brief verified the whole desktop diagram shows at 1440). **Built anyway**: the "Reading this page" prose comes before the diagram, so the explanation is what opens first on every width. |
| F17 | Active rail beat only a 2 px bar; read headlines reuse the metadata colour (minor) | **Fixed.** A pressed rail beat gets a fill as well as the bar and a check mark; reading dims by opacity (R3's own wording) with contrast kept at or above 4.5:1, so read text is never the kicker colour. |
| F18 | Synthetic terminal period on headlines; "Deep read" vs "Weekend"; 404 without a link to the latest review (minor) | **Fixed.** `hl_dot` leaves the builder and the page; /prompts/ says Weekend; the 404 links the latest review. |
| F19 | Discuss is the loudest control on every folded row (round-2 placement) | **Fixed.** Discuss moves into the fold, after the sources, as a quiet text link (C16 href contract kept; the day's Discuss stays in the day header, quiet). |
| F20 | Touch targets below 44 px (accessibility) | **Fixed** on phones (every control ≥ 44 px); 36 px from 700 px. |
| F21 | Bar first in DOM but last on screen on phones (accessibility) | **Kept, by the brief's own allowance** (C3: the bar's placement is the one allow-listed `order` exception). The bar is last in tab order among the chrome and the skip link goes straight to the stories. |
| F22 | Focus when the refill moves nodes (accessibility) | **Already a contract** (C14) and re-implemented: lists are reconciled, never rebuilt; the suite's focus gates stay. |

### 2. Rulings that constrain the choices

Owner rulings (OA/OQ) implemented as written: R1 (never crop: no clamp, no ellipsis, whole-element
folds only), R2 (folded card = headline + [deck] + image + why + More, why visible), R3 (reading
dims by opacity, never hides, moves or folds), R4 (no glyph on the editorial), R5 (the disclosure
never hides or dims), R6 (editorial chip outlined; tier words plain small caps), R7 (folded
editorial = title + disclosure + More), R8 (editorial title is the builder's lede), R9 (image: a
capped monochrome slot after the headline, never above; none on briefs, papers or editorials),
R10 (tier from one module: glyph + word), R11 (Swiss broadsheet: Anton, rules, red pair kept), R12
(hierarchy over theme), R13 (mobile first; controls at the bottom on phones), R14 (no new
attention surface; nothing added that asks for more reading), R15 (expansion sideways, never giant
lines: an open row's body runs in the track beside its headline from 1024 px, at a 36 em measure),
R16 (`viewport-fit=cover` + `env(safe-area-inset-bottom)`), R18 (the rail never traps the wheel:
no `overscroll-behavior: contain`; the key sits behind a closed `<details>`), R19 (rail order, every
control above the fold at 804 px), R20 (no dead band: no sticky bar above the sheet at rail widths),
R21 (an empty board says so on its first line), R22 (metric-matched fallback, no transition on the
swap), R23 (self-hosted Anton only), R24 (affiliation institution-first, the `affiliation_label`
slot kept), R25 (sync opt-in, zero traffic signed out), R26 (feedback per article; voting never
reads), R27 (no server), R36 (red only on the source domain, "Just in" and the lead glyph), R37
(held beat keys survive).

AG/Open rows changed, with the reason: R31 (rail 180 px) → 232 px, to hold the read-state list and
the beat names with counts at 12 px; R32 (full-width dominant) → the lead keeps rank 1 but shares
the top band with the Desk's view, folded; R33 (today's leads boot open) → nothing boots open
(F1); R34 (age demotes a type step) → not carried: the day editions already encode age by
position, and a second size axis fought the tier axis; R35 (1.10 Anton line height) kept, the cqi
sizes replaced by a viewport-fluid scale; R38 (stories are h2) → PLAN decision 10 wins (h2 per
front/day, h3 per story), as round 1 already had it. R17 (simulator) is not covered by this round,
as in round 2.

### 3. Reopened decisions

Each may be reverted at merge by the owner; the revert path is given.

**Decision 1 — the "↑ On the front" pointer form.** Finding: F7 (major): on a phone the pointer
stubs under the newest day take about a quarter of the screen, say nothing a reader can act on,
and the refill turns live rows into stubs. Built instead: no pointer rows. A story lifted to the
front has no row in its day; the day header reads "9 stories · 4 on the front ↑", the count a link
to the front section; the count follows the composition (All's load-time front, Unread's live
pick), so the day still says what it lent (C9). A builder-front story that All leaves off gets its
real row back from a `<template data-front-row>` kept at its rank position, and a reserve story the
refill promotes has its live row hidden. Revert: render a `<li class="ptr">` beside each
`data-front-row` template in `_layouts/home.html`, show it when the story is on the front
(`front.js` `place()`), and restore `.ptr` styles.

**Decision 3 — "two columns where they fit" for open rows.** Finding: F6/F15 (major, minor): CSS
multi-column inside an accordion makes the reader scroll down one column and back up the next,
and the controls strand over a void. Built instead: an open row from 1024 px runs its body, why
and controls down the right-hand track beside the headline (R15's sideways expansion), at a
36 em measure (62–72 characters a line at 17–18 px); below 1024 px one column at the measure.
Revert: `columns: 2 17em` on `.row__body` in `components.css` and drop the right-track foot.

**Decision 11 — root steps 16/18/20/22 px.** Finding: F11 (major): 9.6 px labels on a 16 px
phone root and 23 px body copy at a 22 px desktop root. Built instead: the root is 16 px at every
width; prose 17 px (1.0625rem) below 1024 px and 18 px above; labels 12 px (0.75rem); headlines on
a viewport-fluid clamp. Revert: restore the four `html { font-size }` steps in `base.css` and
re-tune the clamps.

### 4. The new design

**Type scale (root 16 px).** Display: Anton, line-height 1.10 (R35), uppercase. Nameplate 44 px
(phone) / 56 px (rail). Day heading `clamp(26px, 2.4vw, 36px)`. Lead headline `clamp(30px, 2.6vw +
14px, 52px)`; feature `clamp(22px, 1vw + 14px, 30px)`; row headlines by tier 26/22/19 px at ≥1024
(24/20/18 below). Prose: system serif, 17 px (18 px from 1024), line-height 1.5; the why 16 px;
row body 16 px. Labels: system sans, 12 px, weight 600, uppercase, letter-spacing .08em; the only
small-caps idiom. Controls: 13 px sans. Measure: 36 em on prose blocks (card text box 32 em).

**Layout by width.**
- < 700 px (phones): single column; compact masthead (wordmark, edition date, count line, three
  text links, closed key); front = lead card, Desk's view, feature cards stacked; days = ruled rows
  (glyph | headline, kicker, why; a foot with More ✓ votes at 44 px); bottom bar 52 px + safe area
  with [All / Unread / Read] [Beats n] [Days] [Sync]; Beats and Days open bottom sheets.
- 700–1023 px: masthead on one line (wordmark left, edition centre, links right); a top sticky bar
  with the read-state segment, the beat strip (scrolling, no mask over a focused chip) and Sync;
  front: lead | Desk's view side by side from a 860 px container, features 3-up from 720 px; rows
  one column.
- 1024–1279 px: as above; rows two tracks (headline+kicker 5fr | why 7fr; a row without a why
  spans; an open row runs body → why → controls down the right track).
- ≥ 1280 px: a 232 px sticky rail (`max-block-size: 100dvh`, `overflow-y: auto`, no overscroll
  containment) with nameplate, edition, read state (a list), Sync, beats (a list with counts),
  the links and the key; no top bar; the column keeps the notice and the sheet; the page caps at
  1600 px.

**Density.** The front is an index (R2): a folded lead is about 420 px tall at 1440 (image
200 px), a folded feature about 240 px; a folded row is two to three lines (headline, kicker,
why). Nothing opens on boot. At 1440 × 900 the first screen holds the lead, the Desk's view and
three features; on an iPhone 15 the first screen holds the masthead, the lead's headline, image
and why.

**How state reads.** Read: the item's text drops to .68 opacity (contrast stays ≥ 4.5:1 on both
papers), the ✓ turns accent and pressed; nothing moves, folds or resizes (R3); the disclosure
keeps full opacity (R5). Open: the fold shows, More reads "Less" with `aria-expanded`. Filter: a
pressed chip inverts and carries a ✓; the segment inverts the active state; the first line of the
sheet states an empty result (R21). Front composition: the front subtitle recounts ("The 3 unread
stories that matter most right now · from Wed 21 Oct"); an older card prints its day in its
kicker; the day header's "n on the front" follows. Promotion: a promoted card starts folded.

**Phone layout.** Bar at the bottom in the thumb zone (R13), `position: sticky` with
`padding-block-end: env(safe-area-inset-bottom)` (R16), 44 px controls; the beat sheet and the
day sheet are `<dialog>`s anchored to the bottom edge (top layer; the page behind is inert; Esc
and a tap on the scrim close); `scroll-padding-block-end` keeps focused controls above the bar.
Without script the bar does not render (C5); the day links in the masthead key do.

**DOM contract** (what the engine, the suite, the static tests and the screenshot script read).
Zones: `data-zone` = masthead, bar, notice, main, empty, front, front-head, front-lead, desk,
front-rest, day, day-head, rows, card, row, editorial, footer. Items: `[data-story]` on `li.fc`
(front card, id `c-<sid>`), `li.row` (id `r-<sid>`), `article.ed` (id `<sid>`; the Desk's view
copy of a reserve editorial `desk-<sid>`; the builder desk editorial's own day article
`day-<sid>`); every item carries `data-edition`, `data-topics`; cards and rows carry `data-imp`.
Templates: `template[data-reserve-card]`, `template[data-reserve-desk]` at the end of the front;
`template[data-front-row]` at a builder-front story's rank in its day; `template[data-front-ed]`
after the day's rows for the builder desk editorial. Day: `section.day#d-<date>[data-date]` with
`.day__h`, `.day__n[data-total]`, `a.day__front[href="#front"]`, `.day__cov .ptag[data-stream]`,
`.day__links a.discuss[data-discuss=day]`, `ol.rows`. Front: `section.front#front[data-reserve]
[data-desk-reserve]`, `.front__n[data-date]`, `ol.fcards--top`, `aside.desk`, `ol.fcards--rest`.
Controls: `.seg button[data-rs]` and `.chip[data-topic]` (rendered in the bar/sheet and the rail,
one painter), `.readbtn`, `.vote[data-v]`, `.more[aria-controls]`, `a.discuss[data-discuss]`,
`.syncbtn[data-dialog=sync]`, `[data-dialog=hiw|beats|days]`, `#empty`, `.notice[data-src]`,
`#announce`. Text: `.hl` (h3), `.deck`, `.sum`, `.why` (`.why__l`), `.photo[data-og]`, `.kick`
(the kicker) with `.tier[data-imp] .tg--lead|feature|brief`, `.fday`, `.fresh`, `.evt`, `.flag`,
`.srcn`, `.src__dom`, `.srcs .srcs__list`, `.ed__kick`, `.ed__hl`, `.ed__disc`, `.ed__body`,
`.edchip`. States: `.is-folded`, `.is-open`, `.is-read`, `[hidden]`, `.needs-js`, `html.js`.

### 5. How C1–C16 are implemented

- **C1** Builder decides: the page prints `feed.board`, `days`, `front`, `beats`, `edition_label`,
  `count_line`. Two builder changes this round, both presentation decisions that belonged to it:
  `boot_open` and `hl_dot` leave `build_views()`; `tools/tests/test_feed_views.py` pins their
  absence; `_data/homefeed.json` is regenerated and the golden re-captured.
- **C2** `_layouts/home.html` prints the front (lead, up to three, Desk's view), then one
  `section.day` per `feed.days` entry with its heading, period tags per desk, rows biggest first
  (board order), the editorial last.
- **C3** DOM order = visual order = board order: flex/grid in normal flow, no `order` on content;
  `order` only on `.bar`, `.notice`, `main`, `.foot` (test_frontend_static's ORDER_ALLOWED,
  unchanged); no `grid-auto-flow: dense`; no layout script.
- **C4** No `line-clamp`, no `text-overflow`, no `overflow: hidden` on text; folds hide whole
  elements under `html.js` only.
- **C5** Every control that needs script is `.needs-js` (hidden unless `html.js`, which the
  head's gate adds only when the entry module runs and `main.js` confirms with `__siteReady`);
  the fold CSS is under `.js`.
- **C6** `paint()` toggles `.is-read` and the ✓ only; under All `apply()` recomposes from the
  load-time snapshot, so a tick moves nothing.
- **C7** `front.js`: `snapshot()` at load takes the unread pick (first four unread reserve
  entries on no beats, lead slot to the first importance-3) padded to four with read reserve
  entries after the unread ones; with nothing unread the builder's front; the Desk's view the
  first unread editorial of `desk_reserve` or the builder's. `compose('all')` always places that
  snapshot; `compose('unread')` the live pick; `compose('read')` the builder's.
- **C8** `board.js`: an interaction gate armed after load (pointerdown, keydown, focusin, wheel,
  touchstart anywhere; a scroll of the reader's own detected by the top item moving with the
  page; `#fragment` at load counts); the first `roam` re-takes the snapshot only while untouched,
  anchoring on the first on-screen item the recompose keeps; every later roam only repaints.
- **C9** No pointer rows: a promoted reserve story's live row is hidden; a builder-front story off
  All's front is its `data-front-row` template, inserted at rank; the Desk's view editorial's day
  copy likewise; the day header's "n on the front" is recounted after every compose.
- **C10** `pick(beats)`: the reserve in order, unread and on the beats, four, lead slot to the
  first `data-imp="3"`; `deskPick`; Read puts the builder's front back.
- **C11** `read.js`: an editorial is read when stored in `homeRead:v1`, else unread when in
  `homeUnread:v1`, else read when every story of its `data-edition` is read; un-ticking a
  rule-read editorial stores it in `homeUnread:v1`.
- **C12** `counts()`: a chip's count is the number of items that would show with that chip
  pressed under the current read state; a segment's count under the current beats; editorials
  carry `data-topics` from the builder's union.
- **C13** `fresh.js`: `pageshow` with `persisted`, or visible after ≥ 10 min hidden (counting from
  load for a background tab), fetches `edition.json` (no-store) and shows the in-flow notice with
  a Reload button; never reloads itself.
- **C14** `front.js` reconciles lists in place (remove what leaves, insert what arrives around
  what stays; a list already right is untouched); `apply()` restores focus and the caret when a
  move dropped them.
- **C15** `state.js` keeps the keys and shapes byte for byte (`homeRead:v1`, `syncState:v1`,
  `topicPrefs:v1`, `syncSession:v1`, `homeUnread:v1`; sessionStorage `homeOg:v2:<url>`; `siteKey`
  dropped on load; `ed-` ids pruned from `syncState:v1`); `session.js`, `prefs.js`, `votes.js`,
  `propose.js` send the same routes, headers and bodies field for field; the suite's `contract`
  state replays the old capture.
- **C16** `actions.html` writes the short no-script prompt into every Discuss href
  (`https://claude.ai/new?q=`, `url_encode` then `+` → `%20`); `discuss.js` rebuilds every href
  once at load and on adoption from the page's own text; the day prompt walks the day's story ids
  (`data-sids` on the section) so a story on the front is still in its day's conversation.
  `stories.xml` and `feeds/<desk>.xml` keep their include.

### 6. Proposals for the owner (not shipped)

1. **Headline click expands; collapsing marks read; outlet links only on the source chips** (F2).
   Meets no ruling and rewrites the July read contract (headline click or ✓ reads; More never
   reads, R26 keeps voting out of it). The evaluator's argument is sound for a reader who wants
   the on-site summary; the counter-argument is R14: the page is an index to the sources, and a
   headline that goes to the source keeps it one. Decision needed before anyone ships it.
2. **`<details>` folds so text stays folded without script** (F14). Collides with PLAN decision
   9 (without script every text shows). The gain is a shorter no-script page; the cost is a
   no-script reader who cannot find text that is there. The day jump now works without script,
   which covers the navigation half of the finding.
3. **Single-select beats** (F4). C12's honest counts are correct under multi-select and now
   signalled; single-select would make every count the beat's own and remove the "union" surprise,
   at the cost of the held-key semantics (R37) and the prefs shape's `topics` array (which would
   still carry one key). Owner's call.
4. **R15's mechanism** (F6). This round reads "taking up spaces adjacent" as the row's right-hand
   track; if the owner meant a multi-column flow, decision 3's columns can return in that track.

### 7. Build order

1. This note, committed (or pended) first.
2. Builder: drop `boot_open` and `hl_dot`; tests; regenerate `_data/homefeed.json`; re-capture the
   golden. `python3 -m unittest discover -s tools/tests` green.
3. Tokens, CSS (reset, base, layout, components, prose, utilities, state), layouts and includes;
   `test_frontend_static.py`, `test_feed_sources.py` (template wiring), `test_liquid_balance.py`
   rewritten to the new markup where they pinned the old.
4. JavaScript (`main`, `state`, `session`, `prefs`, `read`, `board`, `front`, `anchor`, `fold`,
   `discuss`, `votes`, `og`, `fresh`, `dialogs`, `propose`, `probe`).
5. The suite: server/stubs/mutation plumbing and the derived oracle first, then default-state
   geometry, then engine states as the engine lands, then no-JS, contract, two-tab, pages, feeds,
   faults; `SYNTH=1` run.
6. Secondary pages (admin, single, prompts, 404) and their fixes.
7. `tools/verify/build.sh`, the suite, unit tests, `assemble.py check`, `check_publish.py`;
   screenshots into `/tmp/argon-ux/shots-r3/` with `INDEX.md`; weights; this section completed.
