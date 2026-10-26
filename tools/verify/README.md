# tools/verify: build and check the site locally

GitHub Pages builds only `main`. These two scripts let you see a change before it gets there:
a faithful local Pages build, and a Playwright suite run against that build.

```sh
cd tools/verify && npm install                    # once; pins playwright 1.63.0 (public npm, see .npmrc)
LOG=/tmp/fp-build.log ./build.sh /tmp/fp-build    # Docker: GitHub's own jekyll-build-pages image
node suite.mjs /tmp/fp-build/src/_site > /tmp/fp-suite.log 2>&1   # ~40 min with the self-test; one line per case
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
- Stubs both Workers with `route()`, and aborts and logs any other host. No test browser ever
  reaches a live Worker.
- Runs these states: default, expanded, unread-edition, front-read (the builder's front read,
  then Unread), all-read (the whole reserve read), all-partial (the reserve read but its last two
  entries), all-sync (signed in, with the Worker's read set held until the page asks: nine
  scenarios, a fresh page each), beat, multi-beat, empty, stale and stale-bg (a tab opened in the
  background), plus no-JS, contract parity, two tabs, the reading pages and the story feeds.
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

**Assertions** (the round-3 page; REVIEW.md's rule-to-test map says which owner ruling or
contract clause each one serves):

- no horizontal scroll; no sibling zones overlap, with sticky chrome measured at its flow
  position; every item stays inside its day section; DOM order equals visual order, and equals
  board order over cards, rows and the templates that stand in for a story that is elsewhere
- the period tags are correct; a "Happened" label shows on a card, row or reserve template exactly
  when the story's event date is day-precise and before its period start, and it stays inside
- nothing boots open; every card and row has the folded anatomy (kicker, headline, why visible,
  More in the foot; the fold holds body, every outlet and Discuss); the tier glyph and word come
  from one module; every label is at least 12px on a 16px root; every tappable thing is at least
  44px tall on phones and 32px from 700px, the ✓ and the votes square; red only on the source
  domain, "Just in" and the lead glyph; no clamp, ellipsis or hidden overflow on text; one kicker
  per item; the Desk's view prints its edition's day
- the chrome by width: on phones a bottom bar (read state, Beats, Days, Sync) under 64px tall
  that respects `env(safe-area-inset-bottom)`, with Beats and Days opening bottom sheets that
  close on Esc, on a day link and on Done; from 700px a top bar with the beat strip and the day
  jump in the masthead; from 1280px a 232px sticky rail in the owner's order and no bar at all;
  the key is a closed `<details>`; "How this works" opens from `#hiw` with the prose before the
  diagram
- the measure of opened rows and cards is 50–80 characters per line; from 1024px an open row runs
  its body beside its headline and the why and controls down the same track, narrower under it;
  an open card at 760px or more sets its photo under the headline and the text beside, narrower
  one column; the og slots really fill and collapse, the image request carries `no-referrer`, and
  a photo never sits above a headline. A front whose stories are all arXiv/doi links has no image
  slot, so for these checks the suite serves the day's homepage with slots injected where the
  template puts them (always ≥ 2, one on the first openable card of the rest band)
- a fold opens below the head the reader read, and the head stays still; Less with the head
  scrolled past brings the head back under the chrome; opening the Desk's view, the lead or a
  rest card never leaves a void (measured between the content's own line boxes, inside every grid
  track as well as every card) and never resizes a headline; every More tells the truth
- under Unread the front refills: the first four unread reserve entries in order, lead slot to the
  first importance-3 one, the next unread editorial as the Desk's view; a promoted story's day row
  hides and its day header counts it ("n on the front", a link to the front); a tick, a beat and
  another tab's write recompose it; with the whole reserve read the front hides and no day lends
  anything; back under All the builder's front returns dimmed and nothing on the page has moved
- the focus survives a recompose: an un-tick that changes nothing, a tick around a card that
  stays, another tab's write while the reader types in a reason box (the caret kept), an apply
  under All, and a card moved to the lead slot. A card that stays is never taken out of the
  document (a mutation observer watches)
- a promoted editorial's day link reaches its day's edition, and with only the Desk's view on the
  front the story-count line is hidden
- All's front (owner decision 2026-09-25) is the Unread pick from the read set the page opened
  with; a tick under All only dims (nothing moves); Read is the builder's front; Unread→All shows
  the load-time front; with everything read All is the builder's front, dimmed; every story and
  editorial shows exactly once, a builder-front story off the front as its real row at its rank,
  and day headers count the front as composed; a partly-read All (the all-partial state) is
  filled to four with read stories in reserve order after the unread ones, dimmed, the lead
  unread, and a first roam retakes it by the same rule
- signed in: with no input since load the first roamed read set retakes All's front once, and a
  second roam moves nothing. Any interaction first means that roam only dims, with the focus
  kept: a click in the row of the story the roam would promote, focus in a builder-front story's
  restored row while the roam un-reads it, focus in the front, a scroll by script alone, and a
  #fragment load. A scroll the page makes itself (a fold closed by script that brings its head
  back) is not interaction: the roam still retakes. A reload that puts the promoted row on top is
  the browser's scroll: the roam retakes All and what was below that row stays within 2px
- honest counts: each chip shows what pressing it shows, on every copy of the chip (rail, bar,
  sheet); a pressed chip carries a check mark; the editorial read rule and its un-tick override
- in-page links have visible targets; focus rings are whole, including under the phone bar; every
  visible masthead, bar and rail control is reached by Tab
- read text contrast is ≥ 4.5:1, and the AI disclosure is never dimmed
- the "New edition" bar appears on resume, including for a tab opened in the background, and
  never for an unchanged edition; two open tabs keep each other's read marks
- multi-source stories: on every copy of a story the kicker names the primary outlet; the fold
  lists every outlet with its label in the builder's order, each opening in a new tab; the kicker
  reads "N sources" exactly when N > 1; the desk's flags ("Preprint", "Single source", ...) are
  the builder's labels in its order on every copy, in the kicker
- Discuss: one plain link per story, editorial and day to `https://claude.ai/new?q=`, inside the
  fold after the sources (the day's in its header), its prompt built at load from the page;
  spaces travel as `%20`, never `+`; a Discuss click reads the story as opening its article does,
  and its ✓ un-reads it; a reserve copy promoted under Unread carries the full prompt too
- without script: every text shows, no fold, no script-only control, the day links and the
  builder's front once, every Discuss href the template's short prompt
- the story feeds: `stories.xml` and `feeds/<desk>.xml` are well-formed RSS advertised by a
  `<link rel="alternate">` each and linked from the page; the items are the board's stories in
  order with headline, primary link, store-id guid, date, desk category, prose, why, flags and
  every outlet
- every reading page (each review, /prompts/ fully open, the 404, /admin/) fits the width at 360px,
  1440px and on an iPhone, has exactly one h1, wraps a 116-character token in every heading, never
  lets a title overlap the kicker or date line, and reaches no other host; /admin/ signed out shows one sign-in control, no Sign out and a way back
  to the front page; /prompts/ names the Weekend desk; the 404 links the latest review
- zero requests to hosts other than the two Workers; zero Worker requests while signed out

**Contract parity** replays `fixtures/old-contract.json`, which `capture_old_contract.mjs` recorded
against the old page:

- an old snapshot (legacy shapes: no `rs`, no `at`, `ed-` ids in `syncState`) paints the same
  cards as read
- the same interactions write the same storage shapes and send the same Worker bodies, minus the
  `ed-` ids that the Worker never accepted

**Fault injection:** the suite ends with a self-test that breaks the CSS (a rule injected, or
one sheet served with a rule rewritten), the markup, a request, storage, or one line of a JS
module (served mutated through `route()`: the editorial rule's `every` turned into `some`,
discuss.js without its source lines, board.js hearing touches only inside the front, anchor.js
not counting the page's own scrolls, fold.js anchoring on the button, front.js keeping a promoted
story's row, a feed served with an item dropped, two swapped or a source link removed) on purpose.
Each break must fail its own assertion; a SKIP there is counted apart and never as caught.
`FAULT=key,key` runs a few of them alone.

Screenshots go to `$SHOTS` (default `/tmp/fp-shots`). Narrow a run with `WIDTHS=390,1440`,
`ONLY=default,contract` (`ONLY=none` runs the self-test alone), `FAULTS=0` or `SHOTS=0`;
`VERBOSE=1` prints every assertion's detail.

**Not covered here:** Safari's floating tab bar and real passkeys. Headless WebKit has no browser
chrome, so those need the iPhone simulator (`?probe=1` prints the viewport numbers on the page)
and a real phone on the production origin.
