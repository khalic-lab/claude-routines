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
