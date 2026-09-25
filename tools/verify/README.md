# tools/verify: build and check the site locally

GitHub Pages builds only `main`. These two scripts let you see a change before it gets there:
a faithful local Pages build, and a Playwright suite run against that build.

```sh
cd tools/verify && npm install                    # once; pins playwright 1.63.0 (public npm, see .npmrc)
LOG=/tmp/fp-build.log ./build.sh /tmp/fp-build    # Docker: GitHub's own jekyll-build-pages image
node suite.mjs /tmp/fp-build/src/_site > /tmp/fp-suite.log 2>&1   # ~10 min; one line per case
```

## build.sh

- Runs `ghcr.io/actions/jekyll-build-pages:v1.0.13`, the container GitHub's Pages action uses.
  That means the github-pages gem, safe mode and the plugin allowlist.
- Needs Docker (OrbStack is fine) and `gh auth token`, because jekyll-github-metadata calls the API.
  The token only ever travels in the environment, and the log is scrubbed of token-shaped strings.
- Builds a copy of the tree (tracked files plus untracked files that are not ignored) in `OUT/src`, so
  `_site` and `.jekyll-cache` never land in the repo.
- Exits non-zero on a build error, on any Liquid warning, or on the Pages "can't satisfy your
  Gemfile" warning.

## suite.mjs

- Serves the built `_site` under `/claude-routines/`.
- Stubs both Workers with `route()`, and aborts and logs any other host.
- Runs these states: default, expanded, unread-edition, front-read (the default front read, then
  Unread), all-read (the whole reserve read), all-partial (the reserve read but its last two
  entries), all-sync (signed in, with the Worker's read set held until the page asks: eight
  scenarios, a fresh page each), beat, multi-beat, empty, stale and
  stale-bg (a tab opened in the background), plus no-JS, contract parity, two tabs and the reading
  pages.
- Covers Chromium at 360, 390, 700, 768, 1024, 1280, 1440 and 1600, and WebKit as iPhone 15 and at
  1024, all in light and dark.

**Every expectation is derived in the suite from the data**, so the suite stays valid on any day's
feed, not only the one it was written against:

- periods come from the `_posts/` filenames and the "Coverage window" line in `routines/src/*.md`
- the front selection, day slices and targets come from `_data/homefeed.json`'s board
- the Unread refill order is the same selection re-run in rounds over the board, and the
  "Happened" labels come from each story's `event_date` against its derived period
- when the day's data has no scenario for a refill gate (no beat that changes the refill, no
  non-lead entry before a lead), the suite makes one, as it injects image slots: a beat no reserve
  story carries, or a card's `data-imp` set before the refill first runs. `SYNTH=1` forces the
  made-up scenarios on any data. What cannot be made is reported as SKIP, counted apart from
  passes and failures, never as a pass

**Assertions:**

- no horizontal scroll
- no sibling zones overlap, with sticky chrome measured at its flow position
- every item stays inside its day section
- DOM order equals visual order, and equals board order
- the period tags are correct
- a "Happened" label shows on a card, row or reserve template exactly when the story's event date
  is day-precise and before its period start, and it stays inside its card
- under Unread the front refills: the first four unread reserve entries in order, lead slot to the
  first importance-3 one, the next unread editorial as the Desk's view; a promoted story's day row
  becomes its pointer; a tick, a beat and another tab's write recompose it; with the whole reserve
  read the front hides; back under All the builder's front returns dimmed and nothing on the page
  has moved
- the focus survives a recompose: an un-tick that changes nothing, a tick around a card that
  stays, another tab's write while the reader types in a reason box (the caret kept), an apply
  under All, and a card moved to the lead slot. A card that stays is never taken out of the
  document (a mutation observer watches), since the board's focus rescue would hide that
- a promoted editorial's day link reaches its front copy, and with only the Desk's view on the
  front the story-count line is hidden
- All's front (owner decision 2026-09-25) is the Unread pick from the read set the page opened
  with; a tick under All only dims (nothing moves); Read is the builder's front; Unread→All shows
  the load-time front; with everything read All is the builder's front, dimmed; every story and
  editorial shows exactly once, a builder-front story off the front as its real row after its
  pointer, and day headers count the front as composed; the Desk's view prints its edition's day; a
  partly-read All (the all-partial state) is filled to four with read stories in reserve order
  after the unread ones, dimmed, the lead unread, and a first roam retakes it by the same rule
- signed in: with no input since load the first roamed read set retakes All's front once, and a
  second roam moves nothing. Any interaction first means that roam only dims, with the focus
  kept: a click in the row of the story the roam would promote, focus in a builder-front story's
  restored row while the roam un-reads it, focus in the front, a scroll by script alone, and a
  #fragment load. A reload that puts the promoted row on top is the browser's scroll: the roam
  retakes All and what was below that row stays within 2px
- honest counts: each chip shows what pressing it shows
- the editorial read rule and its un-tick override
- in-page links have visible targets
- focus rings are whole, including under the phone bar
- the measure of opened rows is 50–80 characters per line (the ceiling only below 700px)
- read text contrast is ≥ 4.5:1, and the AI disclosure is never dimmed
- the "New edition" bar appears on resume, including for a tab opened in the background, and
  never for an unchanged edition
- two open tabs keep each other's read marks (a `storage` listener reloads the maps)
- the og slots really fill and collapse, and the image request carries `no-referrer`. A front whose
  stories are all arXiv/doi links has no image slot, so for these checks the suite serves the day's
  homepage with slots injected where the template puts them (always ≥ 2, one on the first openable
  card of the rest band): no gate passes, or says n/a, for lack of data
- an open front card with a photo sets it beside the headline
- every visible masthead and bar control is reached by Tab
- every reading page (each review, /prompts/ fully open, the 404, /admin/) fits the width at 360px, 1440px and on an iPhone
- zero requests to hosts other than the two Workers
- zero Worker requests while signed out

**Contract parity** replays `fixtures/old-contract.json`, which `capture_old_contract.mjs` recorded
against the old page:

- an old snapshot (legacy shapes: no `rs`, no `at`, `ed-` ids in `syncState`) paints the same
  cards as read
- the same interactions write the same storage shapes and send the same Worker bodies, minus the
  `ed-` ids that the Worker never accepted

**Fault injection:** the suite ends with a self-test that breaks the CSS, the markup, a request,
storage, or one line of a JS module (served mutated through `route()`, e.g. the editorial rule's
`every` turned into `some`) on purpose. Each break must fail its own assertion.

Screenshots go to `$SHOTS` (default `/tmp/fp-shots`). Narrow a run with `WIDTHS=390,1440`,
`ONLY=default,contract`, `FAULTS=0` or `SHOTS=0`; `VERBOSE=1` prints every assertion's detail.

**Not covered here:** Safari's floating tab bar and real passkeys. Headless WebKit has no browser
chrome, so those need the iPhone simulator (`?probe=1` prints the viewport numbers on the page)
and a real phone on the production origin.
