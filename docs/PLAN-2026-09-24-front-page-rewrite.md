# PLAN 2026-09-24 — front page rewrite (Option B′) and theme drop

Status: APPROVED by the owner on 2026-09-24. This is the execution spec. Supporting material lives in
`docs/design/2026-09-24-front-page/`:
- `mock.html` + `build_mock.py` + `proposal.md` — **the visual and behavioural spec (B′)**. It renders from the real
  `_data/homefeed.json`. `check.mjs` is its Playwright oracle (516/516 green, 22/22 injected faults caught).
- `foundation.md` — the shared architecture (theme, CSS, JS, builder, verification). Where this PLAN differs, this PLAN wins.
- `audit/*.md` — read-only audit of the old page: owner rulings R1–R38 and failed approaches (`history.md`), exact
  tokens (`css.md`), card anatomy (`markup.md`), the behaviour contract (`js.md`), the other pages/tests/deploy
  (`surroundings.md`), and the late-editorial diagnosis (`editorial.md`).

## Owner asks (verbatim, 2026-09-24)
"redesign and rewrite the frontend … keeps the overall look and feel but with a better HTML/CSS work, cleaner
structures, semantic tags where it makes sense, clear content zones that can't overlap … there is an issue with the
editorials appearing days after they were published." Then: "B is the clear winner, take the best from C and A too,
but the idea of day editions is great, might be good to explicitely say which period it covers for that tag."
Then: Docker is available (OrbStack); **ship straight to live once done — no /next/ preview**; **drop the theme right
away**.

## Decisions (final — do not reopen)
1. Layout = B′ as mocked: composed FRONT (lead + up to 3 stories + newest editorial as "Desk's view"), then every
   date as a DAY EDITION `<section>` with A's header and per-desk **period tags** ("SCIENCE · 17–23 SEP"), compact
   index rows, a one-line "↑ On the front" pointer for lifted stories, the day's editorial closing its section.
2. One section per day; no height packing; **no layout JS**; DOM order == visual order; no `grid-auto-flow:dense`,
   no `order:`.
3. Expanding: a front card opens to the full front row, headlines never resize; index rows open inline with a
   readable measure (two columns where they fit, 50–80 chars/line).
4. Editorial read rule: read when ticked, OR when every story of its `(date, stream)` edition is read; an explicit
   tick/un-tick overrides. Chip counts are honest (each chip shows what pressing it would show, multi-beat included,
   editorials included). Editorial ticks stay LOCAL (the Worker drops non-`st-` ids) — prune `ed-` keys from
   `syncState:v1` on load.
5. Titleless editorial → its whole bold lede becomes the heading (leading "1. " stripped), serif italic, never cropped.
6. Keep every story on the board (~80).
7. **Drop minimal-mistakes now.** Own `default`, `home`, `single` (name pinned by `tools/publish.py` +
   `tools/tests/test_publish.py`), `admin` layouts; `jekyll-seo-tag` + `{% feed_meta %}`; a plain 404 page.
8. No preview route: verify locally (Docker Jekyll + Playwright), then ship to `main`.
9. Fold = JS button; without JS every text shows and no JS-only control renders.
10. Headings: one h1 (site), h2 per day edition / front, h3 per story/editorial.
11. Root font steps stay EXACTLY 16/18/20/22px at 0/768/1024/1280 (they were the theme's; now ours).
12. Late-editorial fixes all ship: day zones (misfiling), edition read rule + honest counts (Unread resurfacing),
    editorials inherit the union of their edition's story topics (beat filters), freshness check on resume
    (`pageshow` persisted / visible after >10 min → fetch a no-store build stamp → in-flow "New edition · Reload"
    bar, never auto-reload).

## Period rule (the owner's addition)
For each `(date, stream)` edition: start = the day after the same stream's previous `_posts/<date>-<stream>.md`,
end = the edition date, then capped at the lookback the routine prompt states (news 1 day; science, weekend, sports
7 days; ai-ml uncapped). Single day → "NEWS · 24 SEP"; range → "SCIENCE · 17–23 SEP". Computed in the BUILDER and
emitted as data (never in Liquid, never parsed from the post footer — the footers overlap by a day).

## Contract that must stay byte-compatible (see audit/js.md)
- Storage: `homeRead:v1` `{sid: ms}`, `syncState:v1` `{sid:{ts,v}}`, `topicPrefs:v1` `{topics, rs, ts}` (held beats
  survive), `syncSession:v1` `{token, reader, at}` (shared with admin.html), sessionStorage `homeOg:v2:<url>`.
  Retired names never reused: `siteKey`, `homeOg:v1:`, `autoPreview:v2:`.
- Read ids: stories `{{ s.sid | default: s.id }}`, editorials `ed-<stream>-<date>`. Moved onto the row/card element,
  values unchanged.
- `/prefs` body `{topics, rs, ts}`, ≤50 topics. Votes, sync, propose, og-proxy endpoints and payloads unchanged
  (read `tools/feedback-sink/src/worker.js`, `tools/og-proxy/src/worker.js`). **No Worker change, no wrangler.**
- `window.__FB` (read by admin.html and single pages) keeps its shape.
- The golden `tools/tests/fixtures/dualwrite/golden-feed.json` (`feed.stories` shape) does NOT change — new fields go
  on `feed.board` items (or a new view key) only.

## Builder (`tools/build_stories_feed.py`) — additive, writer-sandbox safe
The writer routines run this file from the pulled repo at every fire, so it must stay CLI-compatible and must not
raise on odd data. New board-view fields: `edition` (`<date>-<stream>`), per-edition `period` {start, end, label},
editorial `topics` (union of its edition's story topics) + `sid`, promoted-lede heading for titleless editorials,
front selection (a deterministic rule, documented), `build_stamp` (ISO time). Delete `ED_MIN_BOARD_INDEX` and the
literal `data-age="3"` coupling (emit what CSS needs). Regenerate `_data/homefeed.json` in the same commit.

## Verification (all must be green before shipping)
- `python3 -m unittest discover -s tools/tests` — green (baseline 545 OK, 1 skip), with updated/added tests for every
  builder change (period derivation incl. caps and gaps, topics union, lede stripping, front selection, board
  fields) and `test_admin_harness` adapted to the new tokens include.
- Local faithful Pages build via Docker (`ghcr.io/actions/jekyll-build-pages:v1.0.13`, the image GitHub's own Pages
  action uses; see `tools/verify/build.sh`) exits 0 with no Liquid warnings.
- `tools/verify/` Playwright suite against the served `_site` (baseurl `/claude-routines`), Chromium at
  360/390/700/768/1024/1280/1440/1600 + WebKit iPhone 15 and 1024, light and dark, states default / expanded /
  unread-with-an-edition-read / beat / multi-beat / empty / stale / no-JS, Workers stubbed via route():
  no horizontal scroll; no sibling zone overlap (sticky chrome measured in flow); every row inside its day section;
  DOM order == visual order; honest chip counts; editorial read rule; visible in-page links resolve to visible
  targets; focus rings unclipped; readable measure on opened rows; no request to any host but the two Workers
  (none to jsdelivr/Font Awesome); contract parity (an old-page `homeRead:v1` snapshot marks the same cards read;
  written shapes identical). A fault-injection self-test proves the suite fails when the CSS is broken.
- `/prompts/`, one evaluator post, `/admin/`, `/404.html` render correctly (screenshots) with the new layouts.

## Rollout
One agent, one worktree (`front-page-rewrite`), signed commits, no push. The session owner reviews, rebases onto
`origin/main` (resolving `_data/homefeed.json` by re-running the builder, never a text merge), pushes to `main`,
watches the Pages build, and checks the live page. Rollback = `git revert`.
