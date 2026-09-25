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
- Runs these states: default, expanded, unread-edition, beat, multi-beat, empty, stale and
  stale-bg (a tab opened in the background), plus no-JS, contract parity, two tabs and the
  reading pages.
- Covers Chromium at 360, 390, 700, 768, 1024, 1280, 1440 and 1600, and WebKit as iPhone 15 and at
  1024, all in light and dark.

**Every expectation is derived in the suite from the data**, so the suite stays valid on any day's
feed, not only the one it was written against:

- periods come from the `_posts/` filenames and the "Coverage window" line in `routines/src/*.md`
- the front selection, day slices and targets come from `_data/homefeed.json`'s board

**Assertions:**

- no horizontal scroll
- no sibling zones overlap, with sticky chrome measured at its flow position
- every item stays inside its day section
- DOM order equals visual order, and equals board order
- the period tags are correct
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
`ONLY=default,contract`, `FAULTS=0` or `SHOTS=0`.

**Not covered here:** Safari's floating tab bar and real passkeys. Headless WebKit has no browser
chrome, so those need the iPhone simulator (`?probe=1` prints the viewport numbers on the page)
and a real phone on the production origin.
