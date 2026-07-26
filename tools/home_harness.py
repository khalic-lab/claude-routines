#!/usr/bin/env python3
"""Render the homepage masonry as a standalone HTML harness — the smoke test for
_layouts/home.html's inline CSS/JS (which Jekyll-only rendering makes otherwise untestable
without a local Ruby toolchain).

It substitutes the Liquid card loop with Python over the real _data/homefeed.json and embeds
the layout's <style>/<script> blocks verbatim plus the Folio tokens from head/custom.html's
palette, so the masonry algorithm, filters, image swap and thumbs run exactly as deployed.

Usage:
    python3 tools/home_harness.py [--out /tmp/home-harness.html]
    # then, no local Jekyll needed:
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new \
        --hide-scrollbars --screenshot=/tmp/home.png --window-size=1440,2800 \
        --virtual-time-budget=8000 "file:///tmp/home-harness.html"

    # or let it drive Chrome and JUDGE the result — this is the oracle, not a report:
    python3 tools/home_harness.py --check --widths 1440,1280,1024,800,390
    #   ...which ALSO drives, once, at the widest width asked for: '#bsread' (the boot-seeded read
    #   lead), '#synced' (the roam path, SYNCED_CHECKS) and the six-cell scroll-container census at a
    #   860px viewport. Those three were the oracle's blind spots and they are no longer optional.
    python3 tools/home_harness.py --check --hash '#synced'      # ONE mode at every width — debugging
    python3 tools/home_harness.py --check --hash '#bootempty'   # boot-into-empty; EMPTY rows only

`--check` PARSES EVERY PROBE MARKER AND EXITS NON-ZERO ON ANY FAILED ASSERTION (2026-07-26,
external-review R17). Until then every check here appended diagnostic text and nothing on earth
compared it: in `#synced` the EMPTY probe printed `vis=1 hidden=1` — contradicting its own
zero-card invariant — and the harness still exited 0. The assertion table is `CHECKS` below, one row
per claim with prose for what it means; a marker that never appears is itself a failure, because a
probe that did not run cannot have passed. Markers are read off the probe ELEMENTS, never off the
page text: the dumped DOM contains the probes' own source, so a bare search for `GEOM …` matches the
code that EMITS the marker and reads its variable NAMES as values.

`--hide-scrollbars` IS PART OF THE INVOCATION, not a screenshot nicety, and this line omitted it
until 2026-07-25 — so the documented command produced numbers no report ever quoted. Headless
Chrome lays out a 15px classic scrollbar on this 19,000px page and takes it out of the board:
board=1381 without the flag, 1396 with, and every width-dependent number downstream (gridH,
slackMed, ragMax, driftMax, even `inversions`) moves with it. Quote numbers from a run with it.

DRIVING IT: RESIZEOBSERVER NEVER FIRES HERE. Under `--headless=new --virtual-time-budget` Chrome
150 delivers no resize observations at all — not even the initial one every observer gets on
`observe()`. Verified 2026-07-25 on a five-line control page (a div, an observer, a width change):
`initial=0 afterResize=0`, with and without `--run-all-compositor-stages-before-draw`;
`--headless=old` delivered the initial callback on one run and nothing on the next. So the layout's
debounced re-pack-on-resize CANNOT be exercised from this harness, and a run that narrows the page
and finds stale spans is measuring the instrument, not the engine. To test a width change, drive a
pass through a path that does run — a fold click re-spans synchronously — and compare.

DRIVING IT: A TRANSITIONED PROPERTY CANNOT BE READ AFTER A SYNTHETIC CLICK. Under
`--virtual-time-budget` the timer clock races ahead but the ANIMATION clock does not, so a CSS
transition never advances past its first frame. Read `getComputedStyle` after `el.click()` and you
get the PRE-click value however long you wait — while untransitioned properties in the very same
rule already show the new state, which reads exactly like a broken selector. `.ff-chip` transitions
border-color/background/color, and this cost a round of chasing a rail-selection "bug" that was not
there on 2026-07-25. Inject `transition:none !important` for any such assertion, or assert on a
property that is not transitioned.

The harness appends a geometry self-check 4s after load: a `#geomcheck` div (grep the --dump-dom
output for 'GEOM') carrying structure, the absolute-width sanity floor, and the void metrics.
Read them in this order:
  upInv      MUST be 0 — no module renders above one ranked ahead of it. Under row-span packing
             this is a structural guarantee (sparse auto-placement advances a monotone cursor),
             so a non-zero value means something reordered.
  inversions the OLD banded-grid order metric, kept for the banded modes. It groups row-mates by
             a 4px top tolerance, which packing deliberately breaks, so it reads non-zero under
             `packed=1` BY CONSTRUCTION. Diagnose with upInv, not with this.
  slack*     inside-panel void: last painted content element to the pinned `.fcard__line`, in px.
             Median/p90/max over every visible module. The 9px panel flex gap is its floor.
  holes/rag  unfilled paper INSIDE a column track, and the ragged foot under the container's
             single straight border-block-end.
  packed/spanned/rowUnit  runtime proof the span engine ran: `spanned` counts modules carrying an
             inline `grid-row`, which nothing but a measurement pass writes.
A `#foldcheck` div follows at 4.2s ('FOLD'): expands a mid-page module, asserts the zero-drift
scroll compensation still holds around the FULL re-span (`drift` ~ 0), re-reads the void metrics
while expanded (the worst hole case — a span-8 module needs 8 contiguous tracks), then collapses
and asserts the module is restored byte-for-byte in height.

It also stubs window.fetch (no real network) and appends a `#synccheck` div at 4.5s
exercising the passkey read-state sync engine (grep for 'SYNC'):
  plain URL     -> signed-out run: rsCalls must be 0 (no sync traffic without a session).
  URL + #synced -> seeded session + stubbed GET /readstate: expects gets=1 painted=1
                   unpainted=1 shadow=1 (remote read paints; newer remote tombstone
                   unmarks a locally-read card; both land in the syncState:v1 shadow).
Both modes also expect edread=1 (editorial cards are read-markable since 2026-07-18: the ✓
toggles is-read and writes/clears an ed-<stream>-<date> key in homeRead:v1); -1 means no
editorial card was in the feed window, which is only OK if homefeed.json truly has none.

Last comes `#emptycheck` at 4.8s ('EMPTY'), which drives the board to ZERO visible modules the way
a reader does — every card's ✓, then the Unread button — and asserts the empty state is actually
on screen and sane. It exists because the failure it covers was invisible to every metric here:
the message was wired correctly and rendered 1,651px down the page, below the rail, while the
board the reader was looking at held nothing at all. So `topDelta` (message top minus SHEET top)
is the number that matters, not merely `hidden=0`:
  vis=0 hidden=0   the filter really emptied the board and the message really shows
  topDelta<=2      it opens the sheet rather than trailing a rail-height void
  h>0 inGrid=1     it has a line box of its own, inside the grid's own rect
  packedEmpty=0    the 4px row unit came off, so the line is not squeezed into one track
  restored=1 rePacked=1 reSpanned=N  clearing the filter brings the packed board back — the
                   boot-into-empty path must not leave the pack engine disarmed. AT >=700px ONLY:
                   below that the grid is one column, where `packRowSpans` unpacks by design (a
                   row holds one module, so it is already tight), and `rePacked=0 reSpanned=0` is
                   the correct reading — measured 390/800/1024 on 2026-07-25.
Two extra URL modes:
  #empty      stop at the empty state instead of restoring — this is the screenshot mode.
  #bootempty  seed the read map + a roamed Unread filter BEFORE the layout script runs, so the
              page boots straight into the empty board. That is the owner's actual scenario and
              the only path where the pack engine's FIRST pass sees zero modules; `rePacked=1`
              there is what proves clearing the filter still packs. In this mode every card starts
              read, so the earlier probes read as expected noise (GEOM cards=0, FOLD-SKIP,
              SYNC edread=0) — read only the EMPTY line from a #bootempty run, which is exactly
              what `--check --hash '#bootempty'` scores.

Added 2026-07-26 for the ordering/seen/expansion rework:
  #daycheck  ('DAY', 4.1s)     `data-daybreak` must be on exactly the first card of each date
             block. Expected count is derived from the DOM's own printed `.fcard__date` values,
             never from the attribute under test — a probe that reads its own answer is not a
             probe. Reports DAY-SKIP in a filtered view, where daybreak is a property of the
             BOARD and not of the view.
  #filtercheck ('FILTER', 4.35s) order and holes with a beat filter on — `.is-filtered` drops the
             composed band to uniform cells and re-places what survives, a placement problem the
             resting state never exercises. Restores the board and its prefs key.
  #readcheck ('READ', 5.6s)    the read spine, as a state machine: per-tier collapse ratio
             (`spineOk`, scoped to imp3/imp2 — a folded brief already hides body AND why, so its
             spine is nearly its folded height and a blanket ratio would go red on correct code),
             read-then-More re-opening in place (`reopen`, which pins the load-bearing
             `:not(.is-open)` guards), the AI disclosure in all four editorial states (`edOk`,
             folded/open/read/read+open), and the ALL-READ board — a geometry state this harness
             had never seen — for order, holes and `gridDrop`. Restores everything, storage too.
  #shotcheck ('SHOT', 5.9s)    screenshot modes for the states the probes deliberately restore:
             `#open`, `#read`, `#allread`. Each abandons the page mid-state and therefore clears
             its own storage first.
`__hmVoid()` now also reports `upInv`/`maxUp`, so EVERY state that reads it reports order —
resting, open, filtered and all-read — where that invariant used to be checked only at rest.

THE STATE MATRIX (`--matrix`, 2026-07-26) is the other driver: read state x filter x width x
expansion, ONE Chrome run per cell, one `MX` line per cell, non-zero exit on any violated assertion.

    python3 tools/home_harness.py --matrix                       # 52 cells, numbers only
    python3 tools/home_harness.py --matrix --shots /tmp/home-shots/matrix \\
        --sheet /tmp/home-shots/matrix/contact-sheet.html --log /tmp/mx.log
    python3 tools/home_harness.py --matrix --cells '^1440-R1' --scheme light

It writes its OWN artifact (`/tmp/home-matrix.html`) carrying MATRIX_PRE + MATRIX_CHECK and none of
the nine probes above, because those all measure the full board and restore it — they cannot coexist
with a cell that must still be filtered, still be read and still be open when it is measured. A cell
is addressed by hash: `#mx:R1,F3,E1` (`,keep` abandons the state for the screenshot). See MATRIX_PRE
for the axes and MX_CHECKS for the assertion table. Three things it knows that the driver above
does not:

  THE 500px FLOOR IS REAL, and every "390" number this harness ever printed was taken at 500 —
  `--window-size=390,2800` reports `innerW=500`, and `/tmp/home-shots/390-resting.png` is 500px wide.
  Below the floor the matrix renders the artifact in an `<iframe>` of the exact width inside a 500px
  window and copies the probe marker out of the frame, which needs `--allow-file-access-from-files`.
  `frameW` is asserted against the requested width, so a silent fallback to 500 fails the cell.

  THE COLOUR SCHEME IS PINNED (`--scheme`, default dark) rather than inherited from the host's
  appearance — see MX_SCHEMES for why that is not optional.

  THE READ STATE IS REACHED TWO WAYS, and they differ: `R1` seeds `homeRead:v1` before the layout
  script runs (a returning reader), `R1c` clicks the ✓ now. `foldForRead` runs only from `setRead`,
  so only the clicked path normalizes fold state — which is what `seamN` measures.
"""
import argparse
import glob
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

THEME_URL = "https://khalic-lab.github.io/claude-routines/assets/css/main.css"
THEME_CACHE = "/tmp/mm-main.css"


def _theme_css(refresh=False):
    """The COMPILED theme CSS, or "" if it cannot be fetched.

    `remote_theme: mmistakes/minimal-mistakes@4.26.2` means the skin we are layering over exists
    nowhere in this repo — it is built by GitHub Pages. So every geometry number this harness has
    ever produced was measured WITHOUT it, and the theme has bled through this restyle in LAYOUT
    before, not only in colour. The concrete one: minimal-mistakes' reset sets
    `html{box-sizing:border-box}` + `*{box-sizing:inherit}`, so in production `.fcard__in` is
    border-box and in a theme-blind harness it is content-box — a per-card difference on the one
    measurement that matters.

    Inlined BEFORE the local tokens so our rules still win the cascade, which is the deployed
    order (custom.html loads last in <head>). Cached, because a page render should not depend on
    the network; `--refresh-theme` re-pulls. Degrades to "" with a loud warning rather than
    failing, so the harness still works offline — but a run that prints that warning is measuring
    the wrong page and its numbers should not be quoted.
    """
    import urllib.request
    if refresh or not os.path.exists(THEME_CACHE):
        try:
            req = urllib.request.Request(THEME_URL, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=25) as r:
                data = r.read().decode("utf-8", "replace")
            with open(THEME_CACHE, "w") as fh:
                fh.write(data)
        except Exception as exc:                       # offline, DNS, 4xx/5xx
            if not os.path.exists(THEME_CACHE):
                print("home_harness: WARNING could not fetch the theme CSS (%s) — rendering "
                      "THEME-BLIND; box-sizing and skin geometry will differ from production" % exc)
                return ""
    with open(THEME_CACHE) as fh:
        return "<style>%s</style>" % fh.read()


def _css_sanity(label, css):
    """Reject CSS a browser would SILENTLY discard. Guards our own blocks, not the theme's.

    A stray `*/` — the residue of editing inside a long comment block, which is most of the
    commentary in home.html — is not an error any browser reports. The text before it becomes a
    bad selector and the parser then swallows the NEXT declaration block whole: one rule deleted,
    no warning, nothing in the console. On 2026-07-25 it deleted `.tier-key`'s fixed 9px box while
    every glyph still painted (they come from `::before`, a different rule), so the page looked
    right and only a computed-style probe caught the 2px of label rag it caused. That is the same
    green-while-broken shape as the 327px shrink-wrap, and it is cheap to make impossible.
    Brace imbalance is the identical failure with a wider blast radius, so it is checked here too.
    """
    body = re.sub(r"</?style>", "", css)
    stripped = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
    for token, why in (("*/", "the browser turns the text before it into a bad selector and "
                              "DISCARDS the next rule silently"),
                       ("/*", "an unterminated comment eats every rule after it")):
        if token in stripped:
            i = stripped.index(token)
            raise SystemExit("home_harness: stray `%s` in %s CSS — %s.\nNear: %r"
                             % (token, label, why, stripped[max(0, i - 110):i + 2]))
    if stripped.count("{") != stripped.count("}"):
        raise SystemExit("home_harness: unbalanced braces in %s CSS (%d '{' vs %d '}') — a rule is "
                         "being swallowed" % (label, stripped.count("{"), stripped.count("}")))


def _extract_tokens():
    """Embed EVERY <style> block from _includes/head/custom.html verbatim.

    This used to regex out just the `:root{...}` palette. Selecting one block has two silent
    failure modes, both plausible: a SECOND :root block added later (a type scale, say) is
    dropped while the guard still passes on the first, and a `:root` inside an earlier @media
    gets extracted INSTEAD of the real palette. In both cases the harness renders a page
    production does not have and reports success. The deeper flaw was that the guard checked the
    extracted TEXT, never that the tokens actually APPLY — the original garbage-selector bug
    would have passed it too, had the garbage contained the token names.

    Embedding everything cannot drop a token, needs no guard, and picks up the .propose__* /
    .fb-btn rules the harness was missing anyway. It is the same `re.findall` over <style> that
    main() already uses for _layouts/home.html — one mechanism instead of two.
    """
    src = os.path.join(ROOT, "_includes", "head", "custom.html")
    with open(src) as fh:
        blocks = re.findall(r"<style>.*?</style>", fh.read(), re.S)
    if not blocks:
        raise SystemExit("home_harness: no <style> block in %s" % src)

    # @font-face src is Liquid — `url('{{ "/assets/fonts/x.woff2" | relative_url }}')` — because
    # this is a project Pages site under `baseurl: /claude-routines` and a root-absolute url()
    # 404s there. Jekyll expands it; verbatim extraction does not, so the literal braces survive,
    # the woff2 never loads, and the harness silently paints the metric-matched FALLBACK instead.
    # That is not a cosmetic difference: Anton's cap height is 0.859em against Arial Narrow's
    # 0.716em, so every leading and wrap judgement taken off such a screenshot is ~20% wrong in
    # exactly the dimension this redesign is tuning.
    blocks = [re.sub(r"""\{\{\s*["'](/assets/fonts/[^"']+)["']\s*\|\s*relative_url\s*\}\}""",
                     lambda m: "file://" + ROOT + m.group(1), b) for b in blocks]

    # Generalised guard. The rail extractor has had one of these since it shipped, but it only
    # covered the rail — which is precisely why the font bug above could sit in the stylesheet
    # looking fine. ANY unexpanded Liquid in embedded CSS is a wrong render, so fail loudly rather
    # than let the next one be found by eye three reports later.
    leftover = re.findall(r"\{\{.*?\}\}|\{%.*?%\}", "".join(blocks), re.S)
    if leftover:
        raise SystemExit("home_harness: unexpanded Liquid in custom.html's CSS: %r — the harness "
                         "renders it literally, so add a substitution above" % leftover[:4])
    _css_sanity("custom.html", "".join(blocks))
    return "".join(blocks) + """<style>
body{ background:var(--paper); color:var(--ink); font-family:var(--serif); margin:0; }
/* Production's wrapper chain, measured off the live DOM at a 1440 viewport:
   .folio-board 1396 < .archive 1396 < #main 1440 (padding-inline 22px, max-width 1680)
   < .initial-content 1440 < body.layout--home 1440.
   So #main's box is what decides the board width, and these two values reproduce it exactly
   (board 1396, grid 1110 at 1440 — identical to live). The old 1236/12px understated the sheet by
   ~100px, which is enough to change how many text columns fit and how many lines a headline
   wraps to; every wide-width number taken before this was measuring a narrower page than
   readers see. */
/* `#main.wrap` — the wrapper carries production's ID as well as the harness class, and that is
   load-bearing rather than decorative. The layout styles the front page's outer box through
   `.layout--home #main` (max-width, and since 2026-07-25 the top padding that produced the dead
   band Rafael reported); with only a `.wrap` class here, none of those rules matched and the
   harness could not see the page's top geometry at all — it measured a box production does not
   have. The fourth blindness of this kind, after the image slot, the tier legend and the header.
   Specificity is deliberate: `#main.wrap` is (1,1,0), so it beats BOTH the theme's `#main`
   padding-inline and nothing else, while `.layout--home #main` — also (1,1,0) but declared later,
   since home.html's <style> is emitted after these tokens — still wins for the properties the
   layout actually sets. So the inline padding stays the harness's measured 22px and the vertical
   padding comes from the layout under test, which is exactly the split we want. */
#main.wrap{ max-width:1680px; margin:0 auto; padding:0 22px; }
/* `.harness-doc` is deliberately UNSTYLED — it models `.initial-content` and its whole job is to
   be a flex item with non-auto cross margins. See the note where it is emitted in main(). */
</style>"""


TOKENS = _extract_tokens()

SVG = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28'
       'a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>')

# THE IMAGE SLOT WAS INVISIBLE TO THIS HARNESS, AND THAT IS HOW THE REGRESSION SHIPPED APPROVED.
# og:images arrive at runtime from og-proxy, `window.fetch` is stubbed here, and nothing else ever
# put an `.fimg` in the DOM — so every geometry number this harness has produced was measured on a
# page with no pictures on it, while production put a 521px photo above the fold. A card that WOULD
# carry an image now renders this placeholder at the real slot, so heights, module order and the
# first screen are measured with the images in place.
#
# DELIBERATELY SATURATED. A grey placeholder under `filter:grayscale(1)` is indistinguishable from
# a grey placeholder with the filter missing; magenta and cyan stripes render as grey ONLY if the
# filter is actually applied, so the screenshot proves the rule rather than merely not
# contradicting it. The diagonals also make `object-fit:cover`'s crop visible.
IMG_PH = ("data:image/svg+xml;utf8,"
          "<svg xmlns='http://www.w3.org/2000/svg' width='320' height='200'>"
          "<rect width='320' height='200' fill='%23d81b8c'/>"
          "<path d='M-40 200L200 -40M40 280L280 40M120 360L360 120M-120 120L120 -120'"
          " stroke='%2300b3c8' stroke-width='34'/></svg>")


def _wants_image(s):
    """Mirrors swapImage() in the layout: lead/feature with a URL, arXiv excluded.

    Kept as one function so the placeholder cannot appear where production would show nothing
    (a harness that invents images is as wrong as one that omits them).
    """
    if not s.get("url") or s.get("importance", 0) <= 1:
        return False
    host = ""
    m = re.match(r"^[a-z]+://([^/]+)", str(s["url"]), re.I)
    if m:
        host = m.group(1).split("@")[-1].split(":")[0].lower()
    return not re.search(r"(^|\.)arxiv\.org$", host)

# THE VOID METRICS, defined ONCE and called from two states (all-folded, and with a module
# expanded). Sideways expansion is the worst hole case on the page — a `.is-open` module needs 8
# contiguous free tracks of twelve, and sparse placement scans DOWN for them rather than back — so
# measuring only the resting state would miss it. One function, two call sites, no second copy of
# the arithmetic to drift.
VOID_METRICS = """<script>
/* THE BOOT-OPEN SET, CAPTURED ONCE, BEFORE ANY PROBE TOUCHES THE PAGE. This block parses straight
   after the layout's own IIFE, so the fold defaults have already run: whatever has a More button and
   no `is-folded` right now is a card that BOOTED open (today's leads).
   It has to be captured, because reading such a card now normalizes it to folded and un-reading
   deliberately does NOT restore that (see foldForRead in the layout). Every probe that mass-marks
   the board therefore has to put boot-open back, or the probes that run after it measure a page the
   reader never had — and the seam probe below could not see the state it exists to test. */
window.__hmBootOpen = [].slice.call(document.querySelectorAll('.fcard')).filter(function(c){
  return c.querySelector('.fcard__more') && !c.classList.contains('is-folded');
});
window.__hmRestoreBootOpen = function(){
  var n = 0;
  window.__hmBootOpen.forEach(function(c){
    if (!c.classList.contains('is-folded')) return;
    c.classList.remove('is-folded'); c.classList.remove('is-open');
    var b = c.querySelector('.fcard__more');
    if (b){ b.setAttribute('aria-expanded','true');
      var l = b.querySelector('span'); if (l) l.textContent = 'Less'; }
    n++;
  });
  /* AND THEN RE-PACK, THROUGH A REAL PATH. Writing classes changes a card's CONTENT height, but
     under `.packed` its RENDERED height is the row span the last measurement pass wrote — so
     without this the restore reads back at the spine's height and every probe after it measures a
     grid whose extents no longer match its contents. A fold toggle calls packRowSpans()
     synchronously; open-then-close is the pass, and FOLD_CHECK already asserts that round trip
     restores the card byte-for-byte in height. No test hook is added to the layout for this. */
  if (n){
    var sy = scrollY;                 // the fold toggle below pays back a scroll delta for ITS card
    var other = null, all = document.querySelectorAll('.fcard.is-folded');
    for (var i = 0; i < all.length; i++){
      if (window.__hmBootOpen.indexOf(all[i]) < 0 && all[i].querySelector('.fcard__more')){
        other = all[i]; break;
      }
    }
    if (other){ var mb = other.querySelector('.fcard__more'); mb.click(); mb.click(); }
    scrollTo(0, sy);
  }
  return n;
};
window.__hmVoid = function(){
  var grid=document.getElementById('folioGrid');
  var cards=[].slice.call(grid.querySelectorAll('.fcard')).filter(function(c){return c.style.display!=='none';});
  var R=cards.map(function(c){return c.getBoundingClientRect();});
  // INSIDE-PANEL SLACK — the void this whole exercise is about. `.fcard__line` is pinned to the
  // panel foot by `margin-top:auto`, so every pixel a module is taller than its content opens
  // between the last visible content element and that footer. Hidden elements (a folded
  // `.fcard__sum`) have a zero rect, so walk back to the last one that actually paints.
  // The floor is not 0 but the panel's own 9px flex gap, which is design, not void.
  var slack=[],per=new Array(cards.length),panelGap=0;
  cards.forEach(function(c,i){
    var ln=c.querySelector('.fcard__line');if(!ln)return;
    if(!panelGap)panelGap=parseFloat(getComputedStyle(c.querySelector('.fcard__in')).rowGap)||0;
    var pv=ln.previousElementSibling;
    while(pv&&pv.getBoundingClientRect().height===0)pv=pv.previousElementSibling;
    if(pv){var s=ln.getBoundingClientRect().top-pv.getBoundingClientRect().bottom;slack.push(s);per[i]=s;}
  });
  slack.sort(function(a,b){return a-b;});
  function pct(p){return slack.length?Math.round(slack[Math.min(slack.length-1,Math.floor(p*(slack.length-1)))]):-1;}
  // HOLES AND RAG. Walk each column TRACK (not each card) so a spanning module counts in every
  // track it covers: an interior hole is unfilled paper between two cards in one track — the
  // thing sparse placement can leave when the next module is too tall for the gap and the cursor
  // has already moved past it (`dense` would backfill it and reorder, which is banned). `rag` is
  // the different artifact at the foot: the container paints one straight border-block-end at the
  // tallest column, so shorter columns end above it.
  var gs=getComputedStyle(grid),gb=grid.getBoundingClientRect();
  var tracks=gs.gridTemplateColumns.split(' ').map(parseFloat).filter(function(v){return !isNaN(v);});
  var colGap=parseFloat(gs.columnGap)||0,cx=gb.left+(parseFloat(gs.borderLeftWidth)||0)+(parseFloat(gs.paddingLeft)||0);
  var centers=[];tracks.forEach(function(w){centers.push(cx+w/2);cx+=w+colGap;});
  // CUMULATIVE DRIFT, the failure mode a per-module bound cannot see. Each module is rounded UP to
  // a whole number of row units, so every one of them sits a sub-unit fraction lower than its
  // content needs, and down a 28-module column those fractions add. `driftMax` is the worst
  // column's total — the number that says whether the rounding stays a rounding or becomes a void
  // again. The panel's own flex gap is subtracted, since that is design and not residue.
  var holes=0,holePx=0,ragMax=0,driftMax=0,gTop=gb.top,gBot=gb.bottom;
  centers.forEach(function(x){
    var col=[],drift=0;
    R.forEach(function(b,i){if(b.left<=x&&b.right>=x){col.push([b.top,b.bottom]);
      if(per[i]!==undefined)drift+=Math.max(0,per[i]-panelGap);}});
    col.sort(function(a,b){return a[0]-b[0];});
    var y=gTop;
    col.forEach(function(iv){if(iv[0]-y>2){holes++;holePx+=Math.round(iv[0]-y);}if(iv[1]>y)y=iv[1];});
    var rag=Math.round(gBot-y);if(rag>ragMax)ragMax=rag;
    if(drift>driftMax)driftMax=Math.round(drift);
  });
  // NEVER-CROP SAFETY NET. A span short by a rounding pixel must overflow, never clip: assert
  // `overflow:visible` survives on both boxes, and report the largest measured overflow of a
  // panel's last child past its module's own bottom edge.
  var ovOk=1,maxOver=0;
  cards.forEach(function(c,i){
    var inn=c.querySelector('.fcard__in');if(!inn)return;
    if(getComputedStyle(c).overflow!=='visible'||getComputedStyle(inn).overflow!=='visible')ovOk=0;
    var last=inn.lastElementChild;if(!last)return;
    var o=last.getBoundingClientRect().bottom-R[i].bottom;if(o>maxOver)maxOver=o;
  });
  // THE ORDER INVARIANT TRAVELS WITH THE VOID METRICS (2026-07-26), so every state that reads
  // these — resting, open, filtered, all-read — reports it. It used to live only in GEOM_CHECK,
  // i.e. only in the resting state, while the states most likely to break it were exactly the
  // ones a read spine and an expanded module create. Absolute tops: a card may never be placed
  // at a row ABOVE one earlier in DOM order.
  var A=cards.map(function(c){return Math.round(c.getBoundingClientRect().top+scrollY);});
  var upInv=0,maxUp=0;
  for(var q=1;q<A.length;q++){var dd=A[q-1]-A[q];if(dd>1)upInv++;if(dd>maxUp)maxUp=dd;}
  // PROOF OF EXECUTION, produced at RUNTIME rather than by grepping the artifact for a name:
  // `spanned` can only be non-zero if the engine measured and wrote, and `rowUnit` can only be
  // fine if the class it is gated behind was set by that same pass.
  return 'upInv='+upInv+' maxUp='+maxUp
    +' packed='+(grid.classList.contains('packed')?1:0)
    +' spanned='+cards.filter(function(c){return !!c.style.gridRow;}).length
    +' rowUnit='+gs.gridAutoRows
    +' gridH='+Math.round(gb.height)
    +' slackMed='+pct(0.5)+' slackP90='+pct(0.9)
    +' slackMax='+(slack.length?Math.round(slack[slack.length-1]):-1)+' slackN='+slack.length
    +' holes='+holes+' holePx='+holePx+' ragMax='+ragMax+' driftMax='+driftMax
    +' ovOk='+ovOk+' maxOver='+Math.round(maxOver);
};
</script>"""

# FOLD + ZERO-DRIFT. The More/Less control changes a module's column span AND its content height,
# so under row-span packing it must re-span the whole grid — and the existing scroll compensation
# has to pay back the delta measured around that FULL pass, not around the class toggle alone.
# `drift` is what the reader feels: the clicked module's viewport-relative top must not move.
# Also re-reads the void metrics WHILE EXPANDED (see VOID_METRICS' note) and then restores both
# the fold state and the scroll position, so the screenshot and the sync probe see a clean page.
FOLD_CHECK = """<script>
setTimeout(function(){
  var grid=document.getElementById('folioGrid');
  var vis=[].slice.call(grid.querySelectorAll('.fcard')).filter(function(c){return c.style.display!=='none';});
  var target=null;
  for(var i=8;i<vis.length;i++){ if(vis[i].querySelector('.fcard__more')){ target=vis[i]; break; } }
  var out='FOLD-SKIP no foldable module past rank 8';
  function hlSize(c){ var h=c.querySelector('.fcard__hl');
    return h?getComputedStyle(h).fontSize:'-'; }
  if(target){
    var mb=target.querySelector('.fcard__more');
    var t0=target.getBoundingClientRect().top,h0=Math.round(target.getBoundingClientRect().height);
    var w0=Math.round(target.getBoundingClientRect().width);
    var hlSizeBefore=hlSize(target);
    var s0=scrollY;
    mb.click();
    var t1=target.getBoundingClientRect().top,h1=Math.round(target.getBoundingClientRect().height);
    var w1=Math.round(target.getBoundingClientRect().width);
    var opened=(target.classList.contains('is-open')&&!target.classList.contains('is-folded'))?1:0;
    var openVoid=window.__hmVoid();
    // TYPE SCALE IS INVARIANT UNDER More (2026-07-26), and this is the assertion that keeps it.
    // Sideways expansion doubled the module's inline size, and `.fcard__hl` is sized in `cqi`, so
    // opening a lead resized its headline from ~38px to the 60px clamp ceiling — a fold control
    // restating rank. Height-only expansion cannot do that, and `hlSame` proves it rather than
    // asserting it in prose. `font-size` is not a transitioned property here, so it is safe to
    // read straight after a synthetic click (see this module's docstring on transitions).
    // BOTH NUMBERS ARE REPORTED, not just the boolean, and `openWSame` sits beside them: a `cqi`
    // font-size can only move if the container did, so the two together say WHY. Verified by
    // re-adding the deleted `.is-open{ grid-column:span 8 }` rule in a throwaway working tree
    // (2026-07-26, one variable, same feed, same target card): `openW 405 -> 810`,
    // `hl 37.976px -> 60px`, i.e. straight to the lead clamp's ceiling. With the rule gone:
    // `405 -> 405`, `37.976px -> 37.976px`. The first target must NOT be an editorial for this to
    // mean anything — `.fcard--ed .fcard__hl` is a fixed 1.15rem, so it reads identical either way;
    // FOLD_CHECK picks the first foldable module past rank 8, which under the board is a story.
    var hl0=hlSizeBefore, hl1=hlSize(target);
    mb.click();
    var t2=target.getBoundingClientRect().top,h2=Math.round(target.getBoundingClientRect().height);
    var back=(target.classList.contains('is-folded')&&!target.classList.contains('is-open')
              &&h2===h0&&mb.getAttribute('aria-expanded')==='false')?1:0;
    out='FOLD opened='+opened+' collapsed='+back+' drift='+Math.round(t1-t0)
      +' backDrift='+Math.round(t2-t0)+' grew='+(h1-h0)+' openW='+w1
      +' openWSame='+(w1===w0?1:0)
      +' hl='+hl0+'/'+hl1+' hlSame='+(hl0===hl1?1:0)
      +' [open: '+openVoid+']';
    scrollTo(0,s0);
  }
  var d=document.createElement('div');d.id='foldcheck';d.textContent=out;document.body.appendChild(d);
},4200);
</script>"""

# DAYBREAK IS HONEST, or it is a decoration that lies about which day you are reading. The claim is
# that exactly the FIRST card of each date block carries `data-daybreak` and prints its day — so the
# expected count is derived from the DOM's own printed dates (`.fcard__date`, which every card
# including the editorials has), never from the same attribute the probe is checking. A tautological
# probe is how this repo shipped three green-while-broken pages.
DAY_CHECK = """<script>
setTimeout(function(){
  var grid=document.getElementById('folioGrid');
  var cards=[].slice.call(grid.querySelectorAll('.fcard'));
  // DAYBREAK IS A BOARD FACT, NOT A VIEW FACT, so this can only be asserted unfiltered. `daybreak`
  // is set server-side on the first card of each date block of the WHOLE board; hide some of those
  // cards behind a beat or read filter and the first VISIBLE card of a block need not carry it.
  // That is accepted design, not a defect — but a probe that scored it as one reported dbOk=0 in
  // `#synced` (one card hidden by a roamed Unread filter) and in `#bootempty` (all of them),
  // which is a probe printing its own proof of a failure that is not there.
  if(grid.classList.contains('is-filtered')){
    var s=document.createElement('div');s.id='daycheck';
    s.textContent='DAY-SKIP filtered state — daybreak is a property of the board, not of the view';
    document.body.appendChild(s);return;
  }
  var prev=null,expected=0,marked=0,printed=0,mismatch=0;
  cards.forEach(function(c){
    var dEl=c.querySelector('.fcard__date'),d=dEl?dEl.textContent.trim():'';
    var isFirst=(d!==prev);prev=d;
    if(isFirst)expected++;
    var flagged=c.hasAttribute('data-daybreak');
    if(flagged)marked++;
    if(flagged!==isFirst)mismatch++;
    var day=c.querySelector('.fcard__day');
    if(day&&day.getBoundingClientRect().height>0)printed++;
  });
  var d=document.createElement('div');d.id='daycheck';
  d.textContent='DAY expected='+expected+' marked='+marked+' printed='+printed
    +' mismatch='+mismatch+' dbOk='+((expected===marked&&marked===printed&&!mismatch)?1:0);
  document.body.appendChild(d);
},4100);
</script>"""


# THE READ / BOOT-OPEN SEAM. Runs at 4.65s — after SYNC, BEFORE the probes that mass-mark the board —
# because it is the only probe that needs a card still in its BOOT-open state, and reading such a card
# normalizes it to folded for good (foldForRead; un-reading deliberately does not undo that).
# The seam it pins: a boot-open card is open by the ABSENCE of `is-folded`, so before the fix, marking
# it read left the body hidden by the spine rule while its own button still read "Less" with
# aria-expanded="true" — and re-opening took TWO clicks, the first one against an already-hidden body.
# So: one state transition, the control agreeing with what the card looks like, and ONE click to open.
LEADREAD_CHECK = """<script>
setTimeout(function(){
  var grid=document.getElementById('folioGrid');
  var boot=(window.__hmBootOpen||[]).filter(function(c){
    return c.style.display!=='none' && !c.classList.contains('is-folded')
      && !c.classList.contains('is-open') && c.querySelector('.fcard__sum'); });
  var out='LEADREAD-SKIP no boot-open card with a body';
  if(boot.length){
    var c=boot[0], mb=c.querySelector('.fcard__more'), sum=c.querySelector('.fcard__sum');
    var rb=c.querySelector('.fcard__read'), sy0=scrollY;
    var h0=Math.round(c.getBoundingClientRect().height);
    var bodyBefore=Math.round(sum.getBoundingClientRect().height);
    rb.click();                                  // mark read
    var v1=window.__hmVoid();
    var lbl=mb.querySelector('span').textContent.trim();
    var aria=mb.getAttribute('aria-expanded');
    var spined=(sum.getBoundingClientRect().height===0)?1:0;
    var folded=(c.classList.contains('is-folded')&&!c.classList.contains('is-open'))?1:0;
    var h1=Math.round(c.getBoundingClientRect().height);
    mb.click();                                  // ONE click must open it again
    var oneClick=(sum.getBoundingClientRect().height>0)?1:0;
    var v2=window.__hmVoid();
    var upA=(v1.match(/upInv=(\\d+)/)||[0,'?'])[1], upB=(v2.match(/upInv=(\\d+)/)||[0,'?'])[1];
    mb.click(); rb.click();                      // fold it back, then un-read
    var restored=(window.__hmRestoreBootOpen()>=0
      && !c.classList.contains('is-read')
      && !c.classList.contains('is-folded')
      && mb.querySelector('span').textContent.trim()==='Less'
      && Math.round(c.getBoundingClientRect().height)===h0)?1:0;
    scrollTo(0,sy0);
    try{ ['homeRead:v1','syncState:v1'].forEach(function(k){ localStorage.removeItem(k); }); }catch(e){}
    out='LEADREAD boot='+boot.length+' imp='+c.dataset.imp+' age='+c.dataset.age
      +' bodyBefore='+bodyBefore+' spined='+spined+' folded='+folded
      +' label='+lbl+' aria='+aria+' oneClick='+oneClick
      +' h='+h0+'/'+h1+' upInvRead='+upA+' upInvOpen='+upB+' restored='+restored;
  }
  var d=document.createElement('div');d.id='leadreadcheck';d.textContent=out;
  document.body.appendChild(d);
},4650);
</script>"""


# THE READ SPINE — the one probe for the 2026-07-26 seen rework, and it is a state machine rather
# than four probes fighting over the same page. In order:
#   1. per-card, mark a lead and a feature read and measure the collapse (spine <= 0.70x folded,
#      IMAGE SLOT EXCLUDED on both sides). The photo survives the read spine by owner ruling
#      (2026-07-26 evening — an all-read board had gone imageless), and its clamp() height is
#      identical folded and read, so subtracting it isolates the prose collapse.
#      0.70 IS RE-DERIVED, NOT THE OLD 0.55 LOOSENED CASUALLY: the old bound was measured with
#      the image in the DENOMINATOR only (the spine hid it), so the slot flattered every image
#      card's ratio. Clean prose collapse measures 0.52 at 1024/1440 and 0.63 at 700 — at narrow
#      containers the brief and feature headline scales converge under the cqi clamp floor, so
#      the collapse there is mostly the why/body and the fixed chrome is a larger fraction. A
#      spine that failed to collapse reads >=0.9, so 0.70 still separates the two states at
#      every packed width without going red on correct code.
#      SCOPED TO imp3/imp2 ON PURPOSE: a brief already hides its body AND its why when folded
#      (`.fcard[data-imp="1"].is-folded`), and an editorial already hides its paragraphs, so for
#      those tiers the spine IS very nearly the folded card and a blanket ratio would go red on a
#      correct implementation.
#   2. read -> More re-opens it in place: `.fcard__sum` gets a rect back. This pins the
#      `:not(.is-open)` guards, which are load-bearing — drop one and More on a read card does
#      nothing at all, silently.
#   3. the disclosure in ALL FOUR editorial states (folded, open, read, read+open). It is
#      transparency, not content, so it may never hide.
#   4. the whole board read: a geometry state this harness has never seen. Order and holes must
#      hold, and the page must actually get shorter (gridDrop).
# It restores everything it touched, including localStorage, because `file://` shares one origin
# across every artifact ever opened from it — 82 read entries left behind here would boot the next
# run of ANY harness into a half-read board.
READ_CHECK = """<script>
setTimeout(function(){
  var grid=document.getElementById('folioGrid');
  if(location.hash==='#empty'||location.hash==='#bootempty'){
    var s=document.createElement('div');s.id='readcheck';
    s.textContent='READ-SKIP empty-state mode';document.body.appendChild(s);return;
  }
  var cards=[].slice.call(grid.querySelectorAll('.fcard'));
  function h(c){ return c.getBoundingClientRect().height; }
  function tick(c){ var b=c.querySelector('.fcard__read'); if(b)b.click(); }
  /* EVERY TICK PAYS BACK A SCROLL DELTA (setRead runs inside anchored(), because a spine is ~1/3 the
     height of the card it replaces). ~180 of them accumulate, so this probe has to restore the
     scroll position the way FOLD_CHECK always has — otherwise the next probe, and the screenshot,
     open on a page scrolled somewhere arbitrary. */
  var scroll0=scrollY;
  var gridH0=Math.round(grid.getBoundingClientRect().height);

  // 1 + 2 — per-tier collapse, then re-open in place
  var worst=0,measured=0,reopen=-1;
  function imgH(c){ var im=c.querySelector('.fimg'); return im?im.getBoundingClientRect().height:0; }
  var probe=cards.filter(function(c){
    return !c.classList.contains('fcard--ed')
      && (c.dataset.imp==='3'||c.dataset.imp==='2')
      // NOT ONE THAT IS ALREADY READ. The ✓ is a toggle, so in any mode that boots with read state
      // (`#bsread` seeds the lead) ticking such a card UN-reads it and the ratio measures the card
      // growing back — a probe reporting spineOk=0 for the spine working. Same class of instrument
      // bug the EMPTY probe had before R17.
      && !c.classList.contains('is-read')
      && c.classList.contains('is-folded') && c.querySelector('.fcard__sum');
  }).slice(0,6);
  probe.forEach(function(c){
    // THE IMAGE SLOT IS SUBTRACTED FROM BOTH SIDES: the photo survives the spine (owner ruling,
    // 2026-07-26 evening) at an identical clamp() height, so the ratio below is the collapse of
    // everything else — the geometry the 0.55 bound has always been about. Measured before AND
    // after, not assumed equal: if the spine ever hid the image again, iH1 would go to 0 and the
    // ratio would harden rather than flatter (and imgKept below goes red anyway).
    var iH0=imgH(c),before=h(c);
    tick(c);
    var iH1=imgH(c),denom=before-iH0;
    var ratio=denom>0?(h(c)-iH1)/denom:9;
    if(ratio>worst)worst=ratio;
    measured++;
  });
  if(probe.length){
    var c0=probe[0],mb=c0.querySelector('.fcard__more');
    mb.click();                                  // read + More: the spine must open again
    var sum=c0.querySelector('.fcard__sum');
    reopen=(sum&&sum.getBoundingClientRect().height>0)?1:0;
    mb.click();
  }
  probe.forEach(tick);                           // un-read them again

  // 3 — the AI disclosure, four states
  var edOk=-1,edStates='';
  var ed=grid.querySelector('.fcard--ed');
  if(ed){
    var disc=ed.querySelector('.fcard__eddisc'),edMore=ed.querySelector('.fcard__more');
    function vis(){ return disc.getBoundingClientRect().height>0?1:0; }
    var st=[];
    st.push(vis());                              // folded (boot state)
    edMore.click(); st.push(vis());               // open
    edMore.click();                               // back to folded
    tick(ed); st.push(vis());                     // read
    edMore.click(); st.push(vis());               // read + open
    edMore.click(); tick(ed);                     // restore
    edStates=st.join('');
    edOk=(st.join('')==='1111')?1:0;
  }

  // 4 — the whole board read
  cards.forEach(function(c){ if(!c.classList.contains('is-read'))tick(c); });
  var allVoid=window.__hmVoid();
  var gridH1=Math.round(grid.getBoundingClientRect().height);
  // EVERY PICTURE SURVIVES AN ALL-READ BOARD — the pin for the owner ruling above, measured on
  // all ~76 image cards rather than the 6-card ratio sample so it cannot be vacuous. Filter-hidden
  // cards are excluded (#synced runs this probe under a roamed Unread filter, where one card's
  // display:none zeroes every rect it contains).
  var imgTot=0,imgVis=0;
  cards.forEach(function(c){
    if(c.style.display==='none')return;
    var im=c.querySelector('.fimg'); if(!im)return;
    imgTot++; if(im.getBoundingClientRect().height>0)imgVis++;
  });
  var imgKept=(imgTot>0&&imgVis===imgTot)?1:0;
  cards.forEach(function(c){ if(c.classList.contains('is-read'))tick(c); });
  window.__hmRestoreBootOpen();          // reading normalized them to folded; un-reading does not undo it
  var gridH2=Math.round(grid.getBoundingClientRect().height);
  try{ ['homeRead:v1','syncState:v1'].forEach(function(k){ localStorage.removeItem(k); }); }catch(e){}

  scrollTo(0,scroll0);
  var drop=gridH0>0?Math.round(100*(gridH0-gridH1)/gridH0):-1;
  var d=document.createElement('div');d.id='readcheck';
  d.textContent='READ measured='+measured+' worstRatio='+(Math.round(worst*100)/100)
    +' spineOk='+((measured>0&&worst<=0.70)?1:0)
    +' imgTot='+imgTot+' imgKept='+imgKept
    +' reopen='+reopen+' edStates='+(edStates||'-')+' edOk='+edOk
    +' gridH0='+gridH0+' allReadH='+gridH1+' gridDrop='+drop
    +' restored='+((Math.abs(gridH2-gridH0)<=8)?1:0)
    +' stillRead='+cards.filter(function(c){return c.classList.contains('is-read');}).length
    +' [allread: '+allVoid+']';
  document.body.appendChild(d);
},5600);
</script>"""


# THE FILTERED STATE, which `upInv` never saw: `.is-filtered` drops the composed band to uniform
# span-4 cells and re-places whatever survives, so it is a different placement problem from the
# resting board. Picks the first real beat chip, reads the metrics, and puts the board back.
FILTER_CHECK = """<script>
setTimeout(function(){
  var chip=document.querySelector('.folio-filters .ff-chip:not(.ff-all)');
  var out='FILTER-SKIP no beat chip';
  if(chip){
    chip.click();
    var grid=document.getElementById('folioGrid');
    out='FILTER beat='+(chip.dataset.topic||'?')
      +' filtered='+(grid.classList.contains('is-filtered')?1:0)
      +' vis='+[].slice.call(grid.querySelectorAll('.fcard')).filter(function(c){
          return c.style.display!=='none';}).length
      +' ['+window.__hmVoid()+']';
    document.querySelector('.folio-filters .ff-all').click();
    try{ localStorage.removeItem('topicPrefs:v1'); }catch(e){}
  }
  var d=document.createElement('div');d.id='filtercheck';d.textContent=out;
  document.body.appendChild(d);
},4350);
</script>"""


# SCREENSHOT MODES for the states the probes deliberately restore. Every other probe here puts the
# page back — which is correct, because they all measure the full board — so without these there is
# no way to PHOTOGRAPH an opened module, a page of spines, or an all-read board, and those are
# exactly the states this rework changes. Runs last (5900ms), after READ_CHECK has restored and
# cleared, so it composes with nothing. Like `#empty` it abandons the page mid-state and therefore
# clears its own storage first: `file://` shares one origin across every artifact ever opened from
# it, so read entries left behind here would boot the NEXT run of any harness half-read.
SHOT_CHECK = """<script>
setTimeout(function(){
  var h=location.hash;
  if(h!=='#open'&&h!=='#read'&&h!=='#allread')return;
  var grid=document.getElementById('folioGrid');
  var cards=[].slice.call(grid.querySelectorAll('.fcard'));
  function tick(c){ var b=c.querySelector('.fcard__read'); if(b)b.click(); }
  var what='';
  if(h==='#open'){
    for(var i=8;i<cards.length;i++){
      var mb=cards[i].querySelector('.fcard__more');
      if(mb){ mb.click(); what='opened card '+i; break; }
    }
  } else {
    var n=(h==='#allread')?cards.length:10;
    for(var j=0;j<n&&j<cards.length;j++) tick(cards[j]);
    what='read '+Math.min(n,cards.length);
  }
  try{ ['homeRead:v1','syncState:v1','topicPrefs:v1'].forEach(function(k){
    localStorage.removeItem(k); }); }catch(e){}
  /* THE SCREENSHOT OPENS AT THE TOP OF THE PAGE, always. Marking read runs through anchored(), which
     pays back a scroll delta per card, so a mode that ticks ten of them ends up looking at wherever
     the last compensation left it — a 1440-read10 shot came back with 790px of blank paper above the
     board. What this mode photographs is the resting first screen in a given state, so it says so. */
  scrollTo(0,0);
  var d=document.createElement('div');d.id='shotcheck';
  d.textContent='SHOT mode='+h.slice(1)+' '+what;document.body.appendChild(d);
},5900);
</script>"""


# ---------------------------------------------------------------------------------------------
# THE STATE MATRIX (2026-07-26). One cell = one page load = one measured state, addressed by a URL
# hash: `#mx:R1,F3,E1`. It is a SEPARATE artifact from the check driver's, not a tenth probe on the
# same page, because every probe above measures the FULL board and puts it back — nine of them
# fighting over one page cannot hold a seeded read map and a filter still on at measurement time.
#
# The axes, and how each is reached:
#   R  read state   SEEDED into homeRead:v1 before the layout script runs (`R1`/`R2`/`R2s`), which
#                   is how a returning reader arrives, or CLICKED at probe time (`R1c` — the same
#                   state reached by ticking ✓ now). The suffix exists because the two used to
#                   DIVERGE: `foldForRead` ran from setRead and never from paintRead, so a
#                   click-marked card was normalized to `is-folded`/More while a boot-seeded one kept
#                   whatever fold default it booted with — the seam, and what these cells found. Since
#                   2026-07-26 both go through `paintReadState` and the two paths agree; the A/B stays,
#                   because "they agree" is exactly the claim that has to keep being measured.
#   F  filter       CLICKED, not seeded — apply() + schedulePack is the path a reader takes, and
#                   clicking gives the round-trip for free in EVERY filtered cell (measure at rest,
#                   filter, measure, unfilter, compare) instead of in one designated cell. Boot-time
#                   filter seeding is already covered by `#bootempty` in the check driver.
#                   The chip clicked is the one VISIBLE at that width (>=1280 hides the bar's chips
#                   and the rail carries them), and `chipVis` reports it rather than falling back
#                   silently — a width where no chip is reachable must not pass by accident.
#   E  expansion    CLICKED More, at probe time.
# F5 IS NOT A PURE BEAT FILTER, and this is a finding rather than a shortcut: every chip on this
# feed has a non-zero count (the smallest, `tech`, has 2), so "a beat with zero results" is
# unreachable by beat alone. F5 is realized as the narrowest reachable zero-result beat view —
# `tech` + Read with nothing read — which is also the only way to reach the empty message's
# beat-clause composition.
MATRIX_PRE = """<script>
(function(){
  var h = location.hash || '';
  if (h.indexOf('#mx:') !== 0){ window.__mx = null; return; }
  var C = { R:'R0', F:'F0', E:'E0', keep:false, bootlead:false, bslead:false, roam:false,
            struct:false, click:false, raw:h.slice(4) };
  C.raw.split(',').forEach(function(t){
    t = t.trim(); if (!t) return;
    if (t === 'keep'){ C.keep = true; return; }
    if (t === 'bootlead'){ C.bootlead = true; return; }
    if (t === 'bslead'){ C.bslead = true; return; }
    if (t === 'roam'){ C.roam = true; return; }
    if (t === 'struct'){ C.struct = true; return; }
    if (t.charAt(0) === 'R'){
      if (t.charAt(t.length - 1) === 'c'){ C.click = true; C.R = t.slice(0, -1); } else C.R = t;
      return;
    }
    if (t.charAt(0) === 'F'){ C.F = t; return; }
    if (t.charAt(0) === 'E'){ C.E = t; return; }
  });
  window.__mx = C;
  /* SEEDED READ STATE, written before the layout script reads localStorage — the same key and the
     same shape production writes (`homeRead:v1`, sid -> ms timestamp). PRE_SYNC has just cleared
     it, so the seed is the whole state and the run is deterministic. */
  if (!C.click && C.R !== 'R0'){
    try {
      var map = {}, T = Date.now(), n = 0;
      Array.prototype.forEach.call(document.querySelectorAll('.fcard'), function(c){
        var ed = c.className.indexOf('fcard--ed') >= 0;
        if (C.R === 'R2s' && ed) return;              // all STORIES read, editorials untouched
        var fb = c.querySelector('.fcard__fb');
        var sid = c.getAttribute('data-story') || (fb && fb.getAttribute('data-story'));
        if (!sid) return;
        if (C.R === 'R1'){ if (ed || n >= 10) return; n++; }   // the first ten STORY cards
        map[sid] = T;
      });
      localStorage.setItem('homeRead:v1', JSON.stringify(map));
    } catch(e){}
  }
  /* THE ONE CARD THAT BOOTS OPEN, SEEDED READ — a returning reader who ticked today's lead earlier,
     or whose read state roamed in from another device. It is a DIFFERENT path from ticking it now:
     the boot fold-default loop keys on `data-age="0" data-imp="3"` alone and never consults the read
     map, and `paintRead` (which is what boot runs) does not call `foldForRead` (which is what the
     click path runs). Seeded here, i.e. before the layout script reads localStorage, because that
     ordering is the whole point of the cell. */
  if (window.__mx && window.__mx.bslead){
    try {
      var lead = document.querySelector('.fcard[data-age="0"][data-imp="3"]');
      var lb = lead && lead.querySelector('.fcard__fb');
      var lsid = lead && (lead.getAttribute('data-story') || (lb && lb.getAttribute('data-story')));
      if (lsid){ var m2 = {}; m2[lsid] = Date.now();
        localStorage.setItem('homeRead:v1', JSON.stringify(m2)); }
    } catch(e){}
  }
  /* THE THIRD PATH TO A READ CARD: a ROAM landing after boot. Nothing is seeded read here — only a
     SESSION is, which is enough, because the layout's boot then calls pullRemote() -> the /readstate
     stub PRE_SYNC already installed -> mergeRemote(), whose paint is `cards.forEach(paintRead)` with
     no `foldForRead` either. The stub marks the FIRST card's story id read, and the first card of
     this board is the boot-open lead, so this reproduces the seam without touching homeRead:v1 at
     all. It exists so the roam path is MEASURED rather than inferred from a shared call site. */
  if (window.__mx && window.__mx.roam){
    try {
      localStorage.setItem('syncSession:v1',
        JSON.stringify({ token: new Array(65).join('a'), reader: 'rafael' }));
    } catch(e){}
  }
})();
</script>"""


# THE MATRIX PROBE. Emits ONE `MX` line per cell, and exactly one `__hmVoid()` reading — the FINAL
# state's, since the driver's kv parse keeps the last occurrence of a repeated key and the cell's
# claim is about the state it ends in. Everything measured before that point carries its own prefix.
MATRIX_CHECK = """<script>
setTimeout(function(){
  var C = window.__mx;
  if (!C) return;
  var grid = document.getElementById('folioGrid'), empty = document.getElementById('folioEmpty');
  var filters = document.getElementById('folioFilters');
  var cards = [].slice.call(grid.querySelectorAll('.fcard'));
  var K = {}, notes = [];
  function put(k, v){ K[k] = v; }
  function shown(c){ return c.style.display !== 'none'; }
  function visible(){ return cards.filter(shown); }
  function isEd(c){ return c.classList.contains('fcard--ed'); }
  function tick(c){ var b = c.querySelector('.fcard__read'); if (b) b.click(); return !!b; }
  function more(c){ var b = c.querySelector('.fcard__more'); if (b) b.click(); return !!b; }
  function bodyH(c){ var s = c.querySelector('.fcard__sum'); return s ? Math.round(s.getBoundingClientRect().height) : -1; }
  function hlSize(c){ var e = c.querySelector('.fcard__hl'); return e ? getComputedStyle(e).fontSize : '-'; }
  function gh(){ return Math.round(grid.getBoundingClientRect().height); }
  function r1h(){ return cards.length ? Math.round(cards[0].getBoundingClientRect().height) : -1; }
  function banded(){ return grid.classList.contains('is-filtered') ? 0 : 1; }
  function spannedN(){ return cards.filter(function(c){ return !!c.style.gridRow; }).length; }
  /* THE CHIP THE READER CAN ACTUALLY CLICK AT THIS WIDTH. Both chip sets share `data-topic` and
     the layout's one `active` Set, but only one set is on screen at a given width, and clicking a
     `display:none` control would test a path no reader has. */
  function chipFor(topic){
    var all = [].slice.call(document.querySelectorAll('.folio-filters .ff-chip, .rail-beats .ff-chip'))
      .filter(function(c){ return (c.dataset.topic || '') === topic; });
    var vis = all.filter(function(c){ return c.offsetParent !== null; });
    return { el: vis[0] || all[0] || null, n: all.length, nVis: vis.length };
  }
  function rbtn(rs){ return filters.querySelector('.ff-rbtn[data-rs="' + rs + '"]'); }

  var BEAT = { F3:'geopolitics', F4:'geopolitics', F5:'tech' }[C.F] || '';
  var RS   = { F1:'unread', F2:'read', F4:'unread', F5:'read' }[C.F] || '';

  /* `data-age` IS CLAMPED AT 3 AND CANNOT ORDER DATES — measured 2026-07-26, and it cost this probe
     a false failure before it was found. The feed's `age_days` is the clamped expression the type
     scale and the read spine speak (importance minus age minus read), so on a 15-day board eleven
     different dates all carry `data-age="3"`. Any probe that treats it as a date proxy silently
     loses resolution past three days: `ageMono` is kept because non-decreasing ages IS a true and
     useful claim, but "dates descend down the page" is read off the PRINTED LABEL instead.
     `Jul 26` has no year, so it is ordered as a within-year ordinal with one wrap allowed — over a
     14-day window at most one Dec->Jan boundary can appear, and that is the only legal ascent. */
  var MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  function dnum(lbl){
    var p = (lbl || '').trim().split(/\\s+/);
    var m = MON.indexOf(p[0]), d = parseInt(p[1], 10);
    return (m < 0 || isNaN(d)) ? -1 : m * 100 + d;
  }
  function measure(pfx){
    var V = visible();
    put(pfx + 'vis', V.length);
    put(pfx + 'visStory', V.filter(function(c){ return !isEd(c); }).length);
    put(pfx + 'visEd', V.filter(isEd).length);
    put(pfx + 'H', gh());
    var ages = V.map(function(c){ return parseInt(c.dataset.age, 10); });
    var mono = 1;
    for (var i = 1; i < ages.length; i++) if (ages[i] < ages[i-1]) mono = 0;
    put(pfx + 'ageMono', mono);
    // daybreak, among the cards that are VISIBLE: each must still print its day, and their dates
    // must strictly descend (ages strictly increase). Daybreak is a BOARD property, so which cards
    // carry it in a filtered view is not asserted here — only that the ones on screen are honest.
    var db = V.filter(function(c){ return c.hasAttribute('data-daybreak'); });
    var printed = 0, desc = 1, wraps = 0, last = -1;
    db.forEach(function(c){
      var d = c.querySelector('.fcard__day');
      if (d && d.getBoundingClientRect().height > 0) printed++;
      var dl = c.querySelector('.fcard__date');
      var n = dnum(dl ? dl.textContent : '');
      if (n < 0) desc = 0;
      else if (last >= 0){
        if (n > last){ wraps++; if (wraps > 1 || !(last < 200 && n > 1100)) desc = 0; }
        else if (n === last) desc = 0;      // two daybreaks may never print the same date
      }
      last = n;
    });
    put(pfx + 'dbVis', db.length); put(pfx + 'dbPrinted', printed); put(pfx + 'dbDesc', desc);
    /* DATE BLOCKING, the other half of "descending down the page": a date value may occupy exactly
       ONE contiguous run in DOM order. A JS reorder that interleaved two days would keep every
       daybreak card honest about its own date and still read as noise, and this is the metric that
       would see it. Counted over the VISIBLE cards, so it holds in filtered views too. */
    var runs = 0, uniq = {}, prevD = null;
    V.forEach(function(c){
      var dl = c.querySelector('.fcard__date');
      var t = dl ? dl.textContent.trim() : '';
      if (t !== prevD){ runs++; prevD = t; }
      uniq[t] = 1;
    });
    put(pfx + 'dateRuns', runs); put(pfx + 'dateUniq', Object.keys(uniq).length);
    put(pfx + 'dateBlocked', runs === Object.keys(uniq).length ? 1 : 0);
    // the unread tally against what is on screen. Editorials are excluded BY DESIGN (the tally
    // counts the same population as "All N", which is stories-only) — so this compares like with
    // like, and the added cell below is where that design decision gets pinned as a number.
    var uctEl = filters.querySelector('.ff-uct');
    var uct = uctEl ? parseInt(uctEl.textContent || '-1', 10) : -1;
    var unreadVis = V.filter(function(c){ return !isEd(c) && !c.classList.contains('is-read'); }).length;
    var unreadAll = cards.filter(function(c){ return !isEd(c) && !c.classList.contains('is-read'); }).length;
    put(pfx + 'uct', uct); put(pfx + 'unreadVis', unreadVis); put(pfx + 'unreadAll', unreadAll);
    /* TWO READINGS OF THE SAME NUMBER, and they only agree in an unfiltered view. `readCounts()`
       sweeps every card regardless of `display`, so the tally is the BOARD's unread story count —
       self-consistent with the "All 80" beside it, and deliberately so. The spec's phrasing ("the
       counter equals the visible unread story cards") is the same claim only while nothing is
       filtered, so both are emitted and the judge scores the second one only where it means
       something. Silently asserting one of them would have manufactured a failure per filtered
       cell, or hidden a real one. */
    put(pfx + 'uctOk', uct === unreadAll ? 1 : 0);
    put(pfx + 'uctVisOk', uct === unreadVis ? 1 : 0);
    // THE DISCLOSURE, on every editorial card on screen, in whatever state this cell is in.
    var eds = V.filter(isEd), dmin = -1;
    eds.forEach(function(c){
      var d = c.querySelector('.fcard__eddisc');
      var hh = d ? Math.round(d.getBoundingClientRect().height) : 0;
      if (dmin < 0 || hh < dmin) dmin = hh;
    });
    put(pfx + 'edN', eds.length); put(pfx + 'edDiscMin', dmin);
    put(pfx + 'edDiscOk', eds.length === 0 ? 1 : (dmin > 0 ? 1 : 0));
    // the empty state, and the completeness of its sentence (this page forbids crops and ellipses)
    var er = empty.getBoundingClientRect(), gr = grid.getBoundingClientRect();
    var txt = (empty.textContent || '').trim();
    put(pfx + 'emptyHidden', empty.hidden ? 1 : 0);
    put(pfx + 'emptyH', Math.round(er.height));
    put(pfx + 'emptyTop', Math.round(er.top - gr.top));
    put(pfx + 'emptyDot', (txt.length > 12 && txt.charAt(txt.length - 1) === '.') ? 1 : 0);
    put(pfx + 'emptyOk', V.length === 0
      ? ((!empty.hidden && er.height > 0 && Math.abs(er.top - gr.top) <= 2
          && txt.length > 12 && txt.charAt(txt.length - 1) === '.') ? 1 : 0)
      : (empty.hidden ? 1 : 0));
    // read/fold census
    var rd = cards.filter(function(c){ return c.classList.contains('is-read'); });
    put(pfx + 'readN', rd.length);
    put(pfx + 'openN', cards.filter(function(c){ return c.classList.contains('is-open'); }).length);
    put(pfx + 'foldedN', cards.filter(function(c){ return c.classList.contains('is-folded'); }).length);
    /* THE SPINE, ASSERTED PER CARD RATHER THAN AS A PAGE HEIGHT. The spec expected an R1 board (ten
       of 82 read) to lose >=25% of its height, and at a packed width it arithmetically cannot: the
       grid's height is its TALLEST COLUMN, so ten cards spread over three tracks take about a third
       of their own height off each one — measured 18405 -> 16853, i.e. 8%, while the lead itself
       collapsed 912 -> 228 (75%). The page really did spine; the page HEIGHT is simply the wrong
       instrument for it below an all-read board. So: every read story card that is not explicitly
       open must have a zero-height body, and the height drop is reported for the record.
       Editorial cards are excluded because they have no `.fcard__sum` at all (their body is
       `.fcard__edp`), which reads as -1 rather than 0 and would fail a naive count. */
    var spineWant = rd.filter(function(c){
      return !isEd(c) && c.querySelector('.fcard__sum') && !c.classList.contains('is-open'); });
    put(pfx + 'spineWant', spineWant.length);
    put(pfx + 'spineN', spineWant.filter(function(c){ return bodyH(c) === 0; }).length);
    put(pfx + 'spineOk', spineWant.filter(function(c){ return bodyH(c) === 0; }).length
      === spineWant.length ? 1 : 0);
    /* THE READ / BOOT-OPEN SEAM, COUNTED — the invariant commit 3cc4b4d established, as a number
       that every cell reports. A card that is read, has a More control, and carries neither
       `is-folded` nor `is-open` has its body hidden by the spine rule while its own button still
       says "Less" with aria-expanded="true": it looks collapsed and claims to be expanded, and it
       takes TWO clicks to open (the first only adds `is-folded`). `foldForRead` closes that on the
       CLICK path. This counts it wherever it occurs, on any path. */
    var seam = cards.filter(function(c){
      return c.classList.contains('is-read') && c.querySelector('.fcard__more')
        && !c.classList.contains('is-folded') && !c.classList.contains('is-open'); });
    put(pfx + 'seamN', seam.length);
    if (seam.length){
      var sb = seam[0].querySelector('.fcard__more');
      put(pfx + 'seamLbl', sb.querySelector('span').textContent.trim());
      put(pfx + 'seamAria', sb.getAttribute('aria-expanded'));
      put(pfx + 'seamBody', bodyH(seam[0]));
    }
    put(pfx + 'r1H', r1h()); put(pfx + 'band', banded()); put(pfx + 'spanned', spannedN());
  }

  /* ============ THE SCROLL / STRUCTURE CENSUS (owner report 2026-07-26: "there's a double scroll
     issue right at the top, maybe a rest of the header area"). It runs INSTEAD of the state machine
     below and needs a REALISTIC VIEWPORT HEIGHT — every other cell here uses an 1800-5200px window
     because it photographs a whole page, and at that height nothing on this page can overflow
     vertically at all: the rail's `max-height:calc(100vh - 71px)` is 2529px in a 2600px window, so
     the very container under suspicion is not a scroll container in any other cell. Struct cells run
     at 860px (see _mx_cells), which is why this had to be its own kind of cell rather than one more
     field on an existing one.
     WHAT IT CAN AND CANNOT DO: it measures geometry and computed style. It does NOT dispatch wheel
     events, because a synthesised WheelEvent is untrusted and Chrome does not scroll for it — a
     probe that dispatched one and reported "the page did not move" would be reporting the
     instrument. Scroll capture and chaining are read off the two facts that fully determine them:
     whether the element under the pointer is a scroll container with room to move on that axis, and
     whether `overscroll-behavior` lets it hand the rest to the page. ============ */
  if (C.struct){
    var cont = [], notes2 = [];
    function selOf(el){
      if (el === document.documentElement) return 'html';
      if (el === document.body) return 'body';
      var s = el.tagName.toLowerCase();
      if (el.id) s += '#' + el.id;
      var cl = (el.getAttribute('class') || '').trim().split(/\\s+/).filter(Boolean).slice(0, 3);
      if (cl.length) s += '.' + cl.join('.');
      return s;
    }
    function scrollable(el){
      var cs = getComputedStyle(el);
      var dW = el.scrollWidth - el.clientWidth, dH = el.scrollHeight - el.clientHeight;
      var ox = cs.overflowX, oy = cs.overflowY;
      var out = [];
      if ((ox === 'auto' || ox === 'scroll') && dW > 2) out.push(['x', dW]);
      if ((oy === 'auto' || oy === 'scroll') && dH > 2) out.push(['y', dH]);
      if (!out.length) return null;
      var r = el.getBoundingClientRect();
      return out.map(function(a){
        return { sel: selOf(el), axis: a[0], delta: a[1], ox: ox, oy: oy,
          ob: cs.overscrollBehaviorX + '/' + cs.overscrollBehaviorY,
          pos: cs.position, top: cs.top, mh: cs.maxHeight,
          rect: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]
            .join(',') };
      });
    }
    var els = [document.documentElement, document.body];
    [].push.apply(els, [].slice.call(document.querySelectorAll('body *')));
    els.forEach(function(el){
      var s = scrollable(el);
      if (s) [].push.apply(cont, s);
    });
    /* THE html-vs-body DOUBLE SCROLLBAR, which is a different failure from a nested container: it is
       both of them being independently scrollable, so the viewport shows two vertical bars and a
       wheel hits whichever one the pointer is over. minimal-mistakes sets `body{display:flex}` here,
       so this is worth asserting rather than assuming. */
    var de = document.documentElement, bd = document.body;
    var deD = de.scrollHeight - de.clientHeight, bdD = bd.scrollHeight - bd.clientHeight;
    var deOv = getComputedStyle(de).overflowY, bdOv = getComputedStyle(bd).overflowY;
    var deScrolls = deD > 2 && deOv !== 'hidden';
    var bdScrolls = bdD > 2 && (bdOv === 'auto' || bdOv === 'scroll');
    var K2 = {};
    function put2(k, v){ K2[k] = v; }
    put2('w', innerWidth); put2('h', innerHeight);
    put2('docDelta', deD); put2('bodyDelta', bdD);
    put2('docOv', deOv); put2('bodyOv', bdOv);
    put2('doubleScroll', (deScrolls && bdScrolls) ? 1 : 0);
    put2('nCont', cont.length);
    // the two suspects, always reported by name whether or not they made the census
    var fil = document.getElementById('folioFilters');
    if (fil){
      var fcs = getComputedStyle(fil), fr = fil.getBoundingClientRect();
      put2('filOx', fcs.overflowX); put2('filOy', fcs.overflowY);
      put2('filPos', fcs.position); put2('filTop', fcs.top); put2('filBottom', fcs.bottom);
      put2('filDx', fil.scrollWidth - fil.clientWidth);
      put2('filDy', fil.scrollHeight - fil.clientHeight);
      put2('filRect', [Math.round(fr.left), Math.round(fr.top), Math.round(fr.width),
                       Math.round(fr.height)].join(','));
    }
    var rail = document.querySelector('.folio-rail');
    if (rail){
      var rcs = getComputedStyle(rail), rr = rail.getBoundingClientRect();
      put2('railOy', rcs.overflowY); put2('railOb', rcs.overscrollBehaviorY);
      put2('railPos', rcs.position); put2('railTop', rcs.top); put2('railMaxH', rcs.maxHeight);
      put2('railDy', rail.scrollHeight - rail.clientHeight);
      put2('railClientH', rail.clientHeight); put2('railScrollH', rail.scrollHeight);
      /* WHETHER THE REFERENCE PROSE IS FOLDED, which is the state every rail number here is about.
         `railScrollH` only means "the collapsed furniture" while this is 0; with the index open the
         rail is SUPPOSED to be taller than its scrollport (the reader asked for it), so the ceiling
         assertion in _mx_struct_judge is gated on this rather than applied blind. */
      var rdet = rail.querySelector('.rail-d');
      put2('railDetailsOpen', rdet ? (rdet.open ? 1 : 0) : -1);
      /* WHERE THE TWO ACTIONS END, in the rail's own content coordinates — the acceptance criterion of
         the 2026-07-26 reorder ruling, measured rather than eyeballed. Something is always below this
         rail's fold at a laptop height; the ruling is about WHAT. Two standalone links below a fold
         are undiscoverable, a beat list cut mid-tail advertises itself, so the actions go first and
         these numbers are what says they made it. Offsets, not rects, because the rail may already be
         scrolled: rect-top delta plus scrollTop is the content-box position either way. */
      function railBottom(sel){
        var e = rail.querySelector(sel);
        if (!e) return -1;
        return Math.round(e.getBoundingClientRect().bottom - rr.top + rail.scrollTop);
      }
      var hiwB = railBottom('.hiw-open--rail'), revB = railBottom('.rail-review');
      var beatsB = railBottom('.rail-beats');
      put2('railHiwBottom', hiwB); put2('railReviewBottom', revB);
      put2('railBeatsBottom', beatsB);
      put2('railActionsIn',
        (hiwB > 0 && revB > 0 && hiwB <= rail.clientHeight && revB <= rail.clientHeight) ? 1 : 0);
      put2('railRect', [Math.round(rr.left), Math.round(rr.top), Math.round(rr.width),
                        Math.round(rr.height)].join(','));
      /* CAN IT CHAIN? A wheel over a container that still has room scrolls the container. When it
         runs out, `overscroll-behavior: contain` refuses to hand the remainder to the page. Both
         together are the symptom, so both are reported as one derived flag. */
      put2('railTraps', (rail.scrollHeight - rail.clientHeight > 2
        && rcs.overscrollBehaviorY === 'contain') ? 1 : 0);
      /* IS THE TRAP TOP-SPECIFIC, OR PERMANENT? The owner reports it "right at the top", and the
         answer changes what a fix would even be: a bug that only bites at scrollY=0 is a different
         thing from a standing property of the left column that you happen to meet on arrival.
         `max-height` is viewport-relative and the rail's content is fixed, so the prediction is that
         the delta does not move -- measured rather than assumed, at the top and 4000px down, and the
         scroll position is put back (this file's own rule: a probe may not leak scrollY). */
      var sy0 = scrollY, dy0 = rail.scrollHeight - rail.clientHeight;
      scrollTo(0, 4000);
      var dy1 = rail.scrollHeight - rail.clientHeight;
      put2('railDyScrolled', dy1);
      var rr2 = rail.getBoundingClientRect();
      put2('railRectScrolled', [Math.round(rr2.left), Math.round(rr2.top), Math.round(rr2.width),
                                Math.round(rr2.height)].join(','));
      /* THE CLAIM STATED AS THE COMPARISON IT IS: the hidden delta at the top equals the hidden delta
         4000px down. It used to be computed against a pinned 2010px content height, which was the
         PRE-FIX rail — after the index folded (968px) that constant reported a constant trap as
         non-constant, i.e. an instrument measuring its own stale number. */
      put2('railTrapConstant', dy1 === dy0 ? 1 : 0);
      scrollTo(0, sy0);
    } else put2('railPresent', 0);
    /* ---- STRUCTURE ABOVE THE BOARD. What this artifact can see is what `_layouts/home.html`
       owns: the h1, the tagline, the How-this-works trigger and the two chip sets. `.masthead`,
       `.greedy-nav#site-nav` and `nav.skip-links` come from the minimal-mistakes DEFAULT LAYOUT,
       not from home.html, so they are NOT in this artifact and their absence here is not evidence
       of anything — they are reported as `notInHarness` and have to be checked on the built page. */
    ['masthead', 'greedy-nav', 'skip-links'].forEach(function(c){
      put2('has_' + c.replace('-', '_'), document.querySelector('.' + c) ? 1 : 0);
    });
    function visOf(sel){
      var el = document.querySelector(sel);
      if (!el) return 'absent';
      var cs = getComputedStyle(el), r = el.getBoundingClientRect();
      if (cs.display === 'none') return 'none';
      if (cs.visibility === 'hidden') return 'hidden';
      if (Math.round(r.width) <= 1 && Math.round(r.height) <= 1) return 'sronly';
      return Math.round(r.width) + 'x' + Math.round(r.height);
    }
    put2('h1', visOf('h1.page__title')); put2('tagline', visOf('.home-tagline'));
    put2('hiw', visOf('#hiwOpen'));
    /* THE MODAL'S OWN SCROLLPORT is legitimate — `.hiw` is `overflow-y:auto` and its body is long —
       but only while it is open, so the whitelist entry is gated on this flag rather than standing
       open at all times. No census cell opens it yet (matrix report §9 item 3), so the entry is
       documented-and-inert rather than verified; the flag is what a cell that opens it would need. */
    var hiwM = document.getElementById('hiwModal');
    put2('hiwModalOpen', hiwM && hiwM.classList.contains('on') ? 1 : 0);
    // exactly ONE chip set on screen, and the hidden one contributing no scroll width
    function chipStats(sel){
      var els2 = [].slice.call(document.querySelectorAll(sel));
      var shown = els2.filter(function(e){ return e.offsetParent !== null; });
      var w = 0;
      shown.forEach(function(e){ w += e.getBoundingClientRect().width; });
      return els2.length + '/' + shown.length + '/' + Math.round(w);
    }
    put2('barChips', chipStats('.folio-filters .ff-chip'));
    put2('railChips', chipStats('.rail-beats .ff-chip'));
    var barShown = document.querySelectorAll('.folio-filters .ff-chip')[1];
    var railShown = document.querySelectorAll('.rail-beats .ff-chip')[1];
    put2('barChipsVis', barShown && barShown.offsetParent !== null ? 1 : 0);
    put2('railChipsVis', railShown && railShown.offsetParent !== null ? 1 : 0);
    var d2 = document.createElement('div'); d2.id = 'mxstruct';
    d2.setAttribute('style', 'display:none');
    var parts2 = ['MXS'];
    Object.keys(K2).forEach(function(k){ parts2.push(k + '=' + K2[k]); });
    cont.forEach(function(c2){
      parts2.push('|C sel=' + c2.sel + ' axis=' + c2.axis + ' delta=' + c2.delta
        + ' ov=' + c2.ox + '/' + c2.oy + ' ob=' + c2.ob + ' pos=' + c2.pos
        + ' top=' + c2.top + ' maxH=' + c2.mh + ' rect=' + c2.rect);
    });
    d2.textContent = parts2.join(' ');
    document.body.appendChild(d2);
    try { ['homeRead:v1','syncState:v1','topicPrefs:v1','syncSession:v1'].forEach(function(k){
      localStorage.removeItem(k); }); } catch(e){}
    return;
  }

  var steps = [];
  var rest = {};          // the resting state's numbers, kept for the round-trip comparison

  // --- 0. the resting state for this R, at this width
  steps.push(function(){
    measure('r0');
    rest = { vis: K.r0vis, H: K.r0H, r1H: K.r0r1H, band: K.r0band, spanned: K.r0spanned };
    put('bootOpen', (window.__hmBootOpen || []).length);
  });

  // --- 1. R by CLICK, when the cell asks for the clicked path rather than the seeded one
  if (C.click && C.R !== 'R0'){
    steps.push(function(){
      var n = 0;
      cards.forEach(function(c){
        if (C.R === 'R2s' && isEd(c)) return;
        if (C.R === 'R1'){ if (isEd(c) || n >= 10) return; n++; }
        if (!c.classList.contains('is-read')) tick(c);
      });
      scrollTo(0, 0);            // every tick pays back a scroll delta through anchored()
      notes.push('clicked-read');
    });
  }

  // --- 2. the added cell: reading the BOOT-OPEN lead, which is open by the ABSENCE of is-folded
  if (C.bootlead){
    steps.push(function(){
      var boot = (window.__hmBootOpen || []).filter(function(c){
        return shown(c) && !c.classList.contains('is-folded') && !c.classList.contains('is-open')
          && c.querySelector('.fcard__sum'); });
      put('blN', boot.length);
      if (!boot.length){ notes.push('bootlead-SKIP'); return; }
      var c = boot[0], mb = c.querySelector('.fcard__more');
      var sy = scrollY, h0 = Math.round(c.getBoundingClientRect().height);
      put('blBody0', bodyH(c));
      tick(c);
      put('blSpined', bodyH(c) === 0 ? 1 : 0);
      put('blFolded', (c.classList.contains('is-folded') && !c.classList.contains('is-open')) ? 1 : 0);
      put('blLabel', mb.querySelector('span').textContent.trim());
      put('blAria', mb.getAttribute('aria-expanded'));
      more(c);
      put('blOneClick', bodyH(c) > 0 ? 1 : 0);
      put('blH', h0 + '/' + Math.round(c.getBoundingClientRect().height));
      if (!C.keep){ more(c); tick(c); window.__hmRestoreBootOpen(); }
      scrollTo(0, sy);
    });
  }

  /* --- 2b. THE SAME SEAM, REACHED BY BOOTING INSTEAD OF CLICKING, and counted in clicks. `seamN`
       above says the state exists; this says what it costs the reader: how many presses of More it
       takes to get the body back. One is correct. Two is the pre-3cc4b4d behaviour. */
  if (C.bslead || C.roam){
    steps.push(function(){
      var lead = grid.querySelector('.fcard[data-age="0"][data-imp="3"]');
      if (!lead){ notes.push('bslead-SKIP no age0/imp3 card'); return; }
      if (C.roam){
        /* proof the roam is what marked it, not a seeded map: the read map was empty at boot and
           the only writer since was mergeRemote. Also proves the stub actually landed. */
        var rs = (window.__fetchLog || []).filter(function(l){ return l.indexOf('/readstate') >= 0; });
        put('roamGets', rs.length);
        put('roamPainted', lead.classList.contains('is-read') ? 1 : 0);
      }
      var mb = lead.querySelector('.fcard__more');
      put('bsRead', lead.classList.contains('is-read') ? 1 : 0);
      put('bsFolded', lead.classList.contains('is-folded') ? 1 : 0);
      put('bsOpen', lead.classList.contains('is-open') ? 1 : 0);
      put('bsLabel', mb ? mb.querySelector('span').textContent.trim() : '-');
      put('bsAria', mb ? mb.getAttribute('aria-expanded') : '-');
      put('bsBody', bodyH(lead));
      /* THE CLICK COST IS ONLY MEASURABLE ON A VISIBLE CARD, and on the roam path it is not one: the
         stubbed GET /prefs also roams `rs:'unread'`, so the lead this cell just painted read is
         filtered off the board (`vis` 81, its rect 0). Counting clicks against a `display:none` card
         measured "the card is hidden", not "the control lies" — it read 4 (the cap) with the body
         never returning, which would have overstated a real finding. The seam STATE above is what
         this cell proves on the roam path; the cost is quoted from the boot path. */
      if (lead.style.display === 'none' || !lead.getBoundingClientRect().height){
        put('bsHidden', 1);
        notes.push('click-cost-not-measurable: lead filtered off the board');
      } else {
        put('bsHidden', 0);
        var clicks = 0;
        while (mb && bodyH(lead) === 0 && clicks < 4){ mb.click(); clicks++; }
        put('bsClicksToOpen', clicks);
        put('bsBodyAfter', bodyH(lead));
      }
      scrollTo(0, 0);
    });
  }

  // --- 3. F, by clicking what is on screen
  if (BEAT){
    steps.push(function(){
      var f = chipFor(BEAT);
      put('chipN', f.n); put('chipVis', f.nVis); put('beat', BEAT);
      if (f.el) f.el.click(); else notes.push('no-chip');
    });
  }
  if (RS){
    steps.push(function(){
      var b = rbtn(RS);
      put('rsVis', b && b.offsetParent !== null ? 1 : 0); put('rs', RS);
      if (b) b.click(); else notes.push('no-rbtn');
    });
  }

  // --- 4. E, by clicking More. The target is picked the way FOLD_CHECK picks it: the first
  //     foldable module past rank 8, i.e. a mid-page card rather than the composed top band.
  var eTargets = [];
  function pickFoldable(n, wantRead){
    var V = visible(), out = [];
    for (var i = 8; i < V.length && out.length < n; i++){
      var c = V[i];
      if (!c.querySelector('.fcard__more') || !c.querySelector('.fcard__sum')) continue;
      if (isEd(c)) continue;
      if (wantRead === true && !c.classList.contains('is-read')) continue;
      out.push(c);
    }
    return out;
  }
  if (C.E === 'E1' || C.E === 'E2'){
    steps.push(function(){
      var n = C.E === 'E2' ? 2 : 1;
      eTargets = pickFoldable(n);
      put('eN', eTargets.length);
      if (!eTargets.length){ notes.push('E-SKIP no foldable module past rank 8'); return; }
      put('hl0', hlSize(eTargets[0]));
      var body0 = eTargets.map(bodyH).join('/');
      var t0 = eTargets[0].getBoundingClientRect().top;
      var w0 = Math.round(eTargets[0].getBoundingClientRect().width);
      eTargets.forEach(more);
      put('hl1', hlSize(eTargets[0]));
      put('hlSame', hlSize(eTargets[0]) === K.hl0 ? 1 : 0);
      put('openW', Math.round(eTargets[0].getBoundingClientRect().width));
      put('openWSame', Math.round(eTargets[0].getBoundingClientRect().width) === w0 ? 1 : 0);
      put('drift', Math.round(eTargets[0].getBoundingClientRect().top - t0));
      put('eBody', body0 + '>' + eTargets.map(bodyH).join('/'));
      put('eOpened', eTargets.filter(function(c){
        return c.classList.contains('is-open') && !c.classList.contains('is-folded'); }).length);
    });
  }
  if (C.E === 'E3'){
    /* More ON A READ SPINE — the `.is-open`-beats-`.is-read` cascade. The target is read first if
       this cell's R has not already read it, because the state under test is "read, then opened",
       not "read". */
    steps.push(function(){
      var t = pickFoldable(1, true), hlU = '';
      if (!t.length){
        t = pickFoldable(1);
        /* THE UNREAD RANK SCALE, CAPTURED BEFORE THE TICK — the reference `e3HlRestored` needs, and
           the only moment it exists. `hlSame` used to be asserted here and that was pinning the E4
           bug as an invariant: reading demotes a headline to `--hl-brief` (the spine) and More is
           supposed to LIFT that demotion, so a run where the size does not move through More is a run
           where `:not(.is-open)` is missing. Measured at 1280 with the guard in place:
           21.0394 -> 32.9617px, i.e. straight back to the card's own feature scale. */
        if (t.length){ hlU = hlSize(t[0]); tick(t[0]); notes.push('E3-marked'); }
      }
      eTargets = t;
      put('eN', t.length);
      if (!t.length){ notes.push('E-SKIP no foldable module past rank 8'); return; }
      var c = t[0];
      put('e3Spine', bodyH(c));
      put('hl0', hlSize(c));
      var w0 = Math.round(c.getBoundingClientRect().width);
      more(c);
      put('e3Body', bodyH(c));
      put('e3Reopen', bodyH(c) > 0 ? 1 : 0);
      put('hl1', hlSize(c));
      // the width half of the More invariant still holds here, and it is the half `hlSame` was really
      // about: a `cqi` font-size can only move if the container did.
      put('openWSame', Math.round(c.getBoundingClientRect().width) === w0 ? 1 : 0);
      if (hlU){
        put('e3HlUnread', hlU);
        put('e3HlDemoted', K.hl0 !== hlU ? 1 : 0);
        put('e3HlRestored', hlSize(c) === hlU ? 1 : 0);
      }
      put('e3Open', c.classList.contains('is-open') ? 1 : 0);
      put('e3Read', c.classList.contains('is-read') ? 1 : 0);
      put('eOpened', 1);
    });
  }
  if (C.E === 'E4'){
    /* OPEN A MODULE, THEN MARK IT READ. `.is-open` is deliberately untouched by foldForRead — a
       card the reader explicitly opened stays open when they tick it — so this cell pins the
       documented behaviour as numbers rather than as a comment. */
    steps.push(function(){
      var t = pickFoldable(1);
      eTargets = t;
      put('eN', t.length);
      if (!t.length){ notes.push('E-SKIP no foldable module past rank 8'); return; }
      var c = t[0], mb = c.querySelector('.fcard__more');
      put('hl0', hlSize(c));
      more(c);
      /* `hlSame` IS THE More INVARIANT AND ONLY THAT, so it is read around the More click alone.
         `e4HlSame` is the second, separate claim: reading an OPEN card must not move its headline
         either. It used to, and this cell is what found it — the five `display:none` read rules
         carry `:not(.is-open)` and the font-size rule did not, so ticking an open lead gave back a
         brief-sized headline over a full body (37.976px -> 24.24px at 1440). The guard landed in the
         layout on 2026-07-26; both sizes are still reported (`hl0`, `e4HlRead`) so the number says
         which way it broke rather than only that it did. */
      put('hl1', hlSize(c));
      put('hlSame', hlSize(c) === K.hl0 ? 1 : 0);
      put('e4BodyOpen', bodyH(c));
      tick(c);
      put('e4BodyRead', bodyH(c));
      put('e4StaysOpen', bodyH(c) > 0 ? 1 : 0);
      put('e4Label', mb.querySelector('span').textContent.trim());
      put('e4Aria', mb.getAttribute('aria-expanded'));
      put('e4Read', c.classList.contains('is-read') ? 1 : 0);
      put('e4HlRead', hlSize(c));
      put('e4HlSame', hlSize(c) === K.hl0 ? 1 : 0);
      put('eOpened', 1);
      scrollTo(0, 0);
    });
  }

  // --- 5. THE CELL'S OWN STATE. One void reading, and it is this one: the driver's kv parse keeps
  //     the LAST occurrence of a repeated key, so a second `upInv=` from any other state would
  //     silently become the number the assertion table scores.
  var voidStr = '';
  steps.push(function(){
    measure('');
    voidStr = window.__hmVoid();
  });

  // --- 6. THE ROUND TRIP, in every cell that changed anything — unfilter, un-open, un-read, and
  //     compare against the resting numbers this same page load started from. `keep` is the
  //     screenshot path and deliberately abandons the state instead.
  /* `bslead` HAS NO ROUND TRIP, and that is a property of the state rather than a gap in the probe.
     It was true of the BUG — the boot state was read + un-folded + un-opened, and since the More
     handler can only toggle `is-folded`, a card once clicked could reach "folded/More" or
     "open/Less" but never the boot combination again. It stays true of the FIX for a different
     reason: the cell's own click opens the card, and closing it would restore the boot state only
     if un-reading restored the boot-open fold, which it deliberately does not (see `foldForRead`).
     Either way, asserting a restore here would report a phantom failure. */
  if (!C.keep && !C.bslead){
    steps.push(function(){
      if (BEAT){ var f = chipFor(''); if (f.el) f.el.click(); }        // the All chip
      if (RS){ var b = rbtn(''); if (b) b.click(); }
      eTargets.forEach(function(c){ if (c.classList.contains('is-open')) more(c); });
      if (C.E === 'E3' || C.E === 'E4'){
        eTargets.forEach(function(c){ if (c.classList.contains('is-read')) tick(c); });
      }
      if (C.click) cards.forEach(function(c){ if (c.classList.contains('is-read')) tick(c); });
      window.__hmRestoreBootOpen();
      scrollTo(0, 0);
    });
    steps.push(function(){
      put('rtVis', visible().length); put('rtH', gh()); put('rtR1H', r1h());
      put('rtBand', banded()); put('rtSpanned', spannedN());
      /* THE RESTORE IS AN ASSERTION, not cleanup: spans, counts and the composition band all have
         to come back. `rtH` is compared with a small tolerance because a re-pack rounds each
         module up to a whole 4px row unit and a seeded read map is not undone here (an R1 cell
         restores to ITS resting height, which is what `r0H` recorded). */
      put('rtOk', (visible().length === rest.vis && Math.abs(gh() - rest.H) <= 8
        && banded() === rest.band && spannedN() === rest.spanned
        && Math.abs(r1h() - rest.r1H) <= 4) ? 1 : 0);
    });
  }

  // --- 7. emit, and CLEAN. `file://` shares one origin across every artifact ever opened from it,
  //     so a cell that walked away leaving 82 read entries would boot the next one half-read.
  steps.push(function(){
    /* THE SCREENSHOT IS ALWAYS TAKEN FROM THE TOP OF THE DOCUMENT, and scrolling to frame a
       mid-page module is not an option here — it produces a WRONG PICTURE, not a different one.
       Tried and reverted 2026-07-26: scrolling to the opened module before the capture returned a
       1440x2600 PNG with ~1500px of empty paper and the whole page, nameplate and control bar
       included, displaced to the bottom. Headless `--screenshot` re-lays-out at the window size and
       does not honour the scroll offset the way a viewport capture would. The E modules sit past
       rank 8, so the driver photographs them with a TALLER WINDOW instead (see _mx_shot) and
       `eTop` says where in the document to look. */
    if (C.keep) scrollTo(0, 0);
    if (eTargets.length){
      put('eTop', Math.round(eTargets[0].getBoundingClientRect().top + scrollY));
    }
    try { ['homeRead:v1','syncState:v1','topicPrefs:v1','syncSession:v1'].forEach(function(k){
      localStorage.removeItem(k); }); } catch(e){}
    var order = ['cell','innerW','bootOpen','vis','visStory','visEd','r0vis','r0H',
      'ageMono','dbVis','dbPrinted','dbDesc','uct','unreadVis','unreadAll',
      'edN','edDiscMin','edDiscOk','emptyHidden','emptyH','emptyTop','emptyDot','emptyOk',
      'readN','spinedN','openN','foldedN','r1H','band','spanned','H',
      'beat','chipN','chipVis','rs','rsVis','eN','eOpened','hl0','hl1','hlSame','openW','openWSame',
      'drift','eBody','e3Spine','e3Body','e3Reopen','e3Open','e3Read',
      'e4BodyOpen','e4BodyRead','e4StaysOpen','e4Label','e4Aria','e4Read',
      'blN','blBody0','blSpined','blFolded','blLabel','blAria','blOneClick','blH',
      'roamGets','roamPainted',
      'bsRead','bsFolded','bsOpen','bsLabel','bsAria','bsBody','bsHidden','bsClicksToOpen',
      'bsBodyAfter',
      'rtVis','rtH','rtR1H','rtBand','rtSpanned','rtOk','shotScroll'];
    var parts = ['MX'];
    order.forEach(function(k){ if (K[k] !== undefined) parts.push(k + '=' + K[k]); });
    Object.keys(K).forEach(function(k){
      if (order.indexOf(k) < 0) parts.push(k + '=' + K[k]); });
    if (notes.length) parts.push('notes=' + notes.join('|'));
    /* THE VOID GOES LAST AND BRACKETED, the way FOLD_CHECK's does: the driver's kv regex skips the
       `[` and reads `upInv`, `holes`, `ovOk` and the rest as top-level keys, which is exactly how
       the assertion table wants to name them. */
    if (voidStr) parts.push('[' + voidStr + ']');
    var d = document.createElement('div'); d.id = 'mxcheck'; d.textContent = parts.join(' ');
    d.setAttribute('style', 'display:none');
    document.body.appendChild(d);
  });

  put('cell', C.raw); put('innerW', innerWidth);
  var i = 0;
  (function run(){
    if (i >= steps.length) return;
    steps[i++]();
    setTimeout(run, 320);     // apply()'s re-pack is coalesced through a timeout
  })();
}, 4000);
</script>"""


GEOM_CHECK = """<script>
setTimeout(function(){
  // The board is CSS Grid now, so the old metrics are gone with the engine they diagnosed:
  // `overlaps` and `maxGap` measured a hand-rolled packing that no longer exists (grid rows
  // cannot overlap and leave no vertical voids). What CAN still regress is the property the
  // packer used to violate: DOM order == reading order == rank. So assert that instead.
  var grid=document.getElementById('folioGrid');
  var cards=[].slice.call(grid.querySelectorAll('.fcard')).filter(function(c){return c.style.display!=='none';});
  var r=cards.map(function(c){var b=c.getBoundingClientRect();return{t:Math.round(b.top+scrollY),l:Math.round(b.left),h:Math.round(b.height)};});
  // Reading order for a row-major grid: sort by (row, column) and check it matches DOM order.
  // Rows are grouped by top within a tolerance, since cards in a row share a baseline.
  // KEPT, BUT IT IS NO LONGER THE INVARIANT — see `upInv` below. This metric assumes a BANDED
  // grid where row-mates share a top within 4px; under row-span packing (2026-07-25) tops are
  // staggered by design, so two neighbours 4px apart in different columns sort by `left` and
  // register as an inversion the reader can never see. A non-zero value here is the MODEL being
  // wrong, not the layout. It stays because it still diagnoses the banded modes (no-JS, filtered,
  // <700px) exactly as before, and deleting a metric to make a number green is how this repo
  // shipped three green-while-broken pages.
  var order=r.map(function(x,i){return{i:i,t:x.t,l:x.l};})
             .sort(function(a,b){return (Math.abs(a.t-b.t)>4?a.t-b.t:a.l-b.l);});
  var inversions=0;for(var k=0;k<order.length;k++) if(order[k].i!==k) inversions++;
  var xs=[];r.forEach(function(x){if(xs.indexOf(x.l)<0)xs.push(x.l);});
  var rows={};r.forEach(function(x){var key=Math.round(x.t/4);rows[key]=1;});
  // THE ORDER INVARIANT UNDER PACKING, and it is a structural guarantee rather than a tuning:
  // sparse auto-placement advances a monotone cursor, so a card can never be placed at a row
  // ABOVE a card earlier in DOM order. `upInv` counts violations (must be 0) and `maxUp` reports
  // the largest upward drift in px, which is the §10 one-column drift bound measured directly.
  var upInv=0,maxUp=0;
  for(var i=1;i<r.length;i++){var d=r[i-1].t-r[i].t;if(d>1)upInv++;if(d>maxUp)maxUp=d;}
  var v=window.__hmVoid();
  // ABSOLUTE WIDTH SANITY — the invariant the whole set was missing (directive, 2026-07-25).
  // On 2026-07-25 the page rendered in a 327px column at a 1440 viewport and EVERY metric here
  // passed: inversions 0, rank2 >= tail, cols 3, scrollW == innerW. All of them are ratios or
  // orderings, and a uniformly shrink-wrapped page satisfies every ratio perfectly. That was the
  // third green-while-broken incident in this repo. So assert the one thing none of them cover:
  // the board must actually be about as wide as the viewport allows. The theme's own chain caps
  // at max-width 1680 with a 22px inset each side; 0.9x of that minus a tolerance is far below any
  // legitimate layout and far above any collapse (the real one measured 283 against a 1236 floor).
  var boardEl=document.querySelector('.folio-board');
  var boardW=boardEl?Math.round(boardEl.getBoundingClientRect().width):-1;
  var expectW=Math.min(innerWidth,1680);
  var floorW=Math.round(0.9*expectW-60);
  var widthSane=boardW>=floorW;
  var d=document.createElement('div');d.id='geomcheck';
  d.textContent=(widthSane?'GEOM':'GEOM-FAIL')
    +' widthSane='+(widthSane?1:0)+' board='+boardW+' floor='+floorW
    +' inversions='+inversions+' upInv='+upInv+' maxUp='+maxUp
    +' cards='+cards.length+' cols='+xs.length
    +' rows='+Object.keys(rows).length+' '+v
    +' bodyScrollW='+document.body.scrollWidth+' innerW='+innerWidth;
  document.body.appendChild(d);
  if(!widthSane){
    // loud in the SCREENSHOT too: the collapse was invisible to every number, so the failure has
    // to be visible to the other instrument as well.
    var w=document.createElement('div');
    w.setAttribute('style','position:fixed;inset:0 0 auto 0;z-index:9999;background:#c8102e;'
      +'color:#fff;font:700 15px/1.5 system-ui,sans-serif;padding:9px 14px');
    w.textContent='HARNESS FAIL — board '+boardW+'px at a '+innerWidth+'px viewport (floor '
      +floorW+'px): the page has shrink-wrapped.';
    document.body.appendChild(w);
  }
},4000);
</script>"""


# The control bar's tier legend, which this harness did NOT emit until 2026-07-25 — so the swatches
# production shows between 721 and 1279px were never once on screen here, and a change to them could
# not be reviewed. It shares `data-imp` + `.tier-key` with the modules and the rail index, which is
# the property worth being able to see: all three must render the same glyph.
LEGEND_UI = """<span class="ff-legend" aria-hidden="true">
    <span class="ff-li" data-imp="3"><i class="tier-key"></i>Lead</span>
    <span class="ff-li" data-imp="2"><i class="tier-key"></i>Feature</span>
    <span class="ff-li" data-imp="1"><i class="tier-key"></i>Brief</span>
  </span>"""

SYNC_UI = """<span class="ff-sync" id="ffSync" hidden>
    <button class="ff-sbtn" type="button" aria-expanded="false" aria-controls="ffSyncPanel">Sync</button>
    <div class="ff-spanel" id="ffSyncPanel" hidden>
      <div class="ffs-out">
        <button class="ffs-btn ffs-signin" type="button">Sign in with passkey</button>
        <button class="ffs-lnk ffs-setup-t" type="button" aria-expanded="false">First time? Set up</button>
        <div class="ffs-setup" hidden>
          <input class="ffs-invite" type="password" placeholder="invite code" aria-label="Invite code" autocomplete="off">
          <button class="ffs-btn ffs-create" type="button">Create passkey</button>
        </div>
      </div>
      <div class="ffs-in" hidden>
        <span class="ffs-who"></span>
        <button class="ffs-btn ffs-signout" type="button">Sign out</button>
      </div>
      <p class="ffs-status" aria-live="polite"></p>
    </div>
  </span>"""

# Runs AFTER the cards are in the DOM but BEFORE the layout script: resets localStorage for a
# deterministic run, stubs fetch (readstate canned, everything else 404), and — on #synced —
# seeds a fake session plus a locally-read second card the remote tombstone must unmark.
PRE_SYNC = """<script>
(function(){
  var SYNCED = location.hash === '#synced';
  try { ['homeRead:v1','syncState:v1','syncSession:v1','topicPrefs:v1'].forEach(function(k){ localStorage.removeItem(k); }); } catch(e){}
  var fbs = document.querySelectorAll('.fcard__fb');
  /* sidA IS THE BOOT-OPEN LEAD, DELIBERATELY, not merely the first card. It is the id the stubbed
     GET /readstate marks read, so it decides which card the ROAM path lands on — and the one card a
     roam can get wrong is exactly this one: today's lead boots OPEN by the absence of `is-folded`
     (see the layout's fold defaults), so a mark that paints it read without folding it leaves the
     seam. It happens to be the first card on today's feed; pinning it by selector means a feed whose
     first card is a brief cannot silently retire the roam assertions in SYNC_CHECK. */
  var leadEl = document.querySelector('.fcard[data-age="0"][data-imp="3"] .fcard__fb');
  var sidA = (leadEl && leadEl.dataset.story) || (fbs[0] && fbs[0].dataset.story), sidB = null;
  for (var i = 0; i < fbs.length; i++){
    if (fbs[i].dataset.story && fbs[i].dataset.story !== sidA){ sidB = fbs[i].dataset.story; break; }
  }
  window.__syncSids = [sidA, sidB];
  window.__fetchLog = [];
  window.fetch = function(url, opts){
    var method = ((opts && opts.method) || 'GET').toUpperCase();
    window.__fetchLog.push(method + ' ' + String(url));
    if (String(url).indexOf('/readstate') >= 0){
      if (method === 'GET'){
        var T = Date.now(), state = {};
        if (sidA) state[sidA] = { ts: T - 5000, v: 1 };
        if (sidB) state[sidB] = { ts: T - 1000, v: 0 };
        return Promise.resolve(new Response(JSON.stringify({ reader:'rafael', state: state }), { status: 200 }));
      }
      return Promise.resolve(new Response(JSON.stringify({ ok: true }), { status: 200 }));
    }
    if (String(url).indexOf('/prefs') >= 0){
      if (method === 'GET'){
        // remote prefs carry a roamed read-filter (rs:'unread') with a ts newer than the
        // cleared local shadow -> the merge must flip the segmented toggle to Unread.
        return Promise.resolve(new Response(JSON.stringify(
          { reader:'rafael', prefs: { topics: [], rs: 'unread', ts: Date.now() - 500 } }), { status: 200 }));
      }
      return Promise.resolve(new Response(JSON.stringify({ ok: true, applied: true }), { status: 200 }));
    }
    return Promise.resolve(new Response('', { status: 404 }));
  };
  if (SYNCED){
    try {
      localStorage.setItem('syncSession:v1', JSON.stringify({ token: new Array(65).join('a'), reader: 'rafael' }));
      var seed = {}; seed[sidB] = Date.now() - 100000;   // read locally, OLDER than the remote tombstone
      localStorage.setItem('homeRead:v1', JSON.stringify(seed));
    } catch(e){}
  }
  /* BOOT WITH TODAY'S LEAD ALREADY READ (#bsread) — the second of the three paths into read, and the
     one no click-driven probe can reach. A returning reader who ticked the lead yesterday, or whose
     mark roamed in and persisted, loads the page with it in the read map; the boot pass paints it,
     and until 2026-07-26 painting did not fold (see `paintReadState` in the layout). Seeded HERE
     because "before the layout script reads localStorage" is the whole content of the cell — nothing
     driven after boot can put a card back into that state, since the More handler can only toggle
     `is-folded`. The state matrix proved the bug on this path (`bsClicksToOpen=2`); this is the same
     cell in the STANDING oracle, so it cannot quietly reopen. */
  if (location.hash === '#bsread'){
    try {
      var one = {};
      if (sidA) one[sidA] = Date.now();
      localStorage.setItem('homeRead:v1', JSON.stringify(one));
    } catch(e){}
  }
  // BOOT INTO AN EMPTY BOARD (#bootempty) — the owner's 2026-07-25 report exactly: a roamed
  // Unread filter plus every story already read, so the page's FIRST pack pass ever run sees zero
  // visible modules. It is a distinct path from filtering into empty at runtime, because the pack
  // engine is not armed yet at that point, and it is the one the `packOn` line in packRowSpans'
  // empty branch exists for. Seeded here rather than driven later precisely because it has to be
  // true BEFORE the layout script reads localStorage.
  if (location.hash === '#bootempty'){
    try {
      var all = {}, T = Date.now();
      Array.prototype.forEach.call(document.querySelectorAll('.fcard'), function(c){
        var b = c.querySelector('.fcard__fb');
        var sid = c.dataset.story || (b && b.dataset.story);
        if (sid) all[sid] = T;
      });
      localStorage.setItem('homeRead:v1', JSON.stringify(all));
      localStorage.setItem('topicPrefs:v1', JSON.stringify({ topics: [], rs: 'unread', ts: T }));
    } catch(e){}
  }
})();
</script>"""

# THE BOOT-SEEDED READ LEAD (`--hash '#bsread'`), promoted out of the state matrix into the standing
# oracle (matrix report §9 item 2). READ_CHECK and LEADREAD_CHECK both reach read state by CLICKING
# `.fcard__read`, which is the one path that was already correct — so 25 matrix cells could fail on
# the boot and roam paths while this driver stayed green at every width. That is exactly the shape of
# regression that must not be invisible twice.
# Runs at 4.4s: after FOLD (4.2s, which opens and restores a card past rank 8) and before anything
# that mass-marks the board (LEADREAD 4.65s, EMPTY 4.8s, READ 5.6s), so the state it reads is still
# the one the page BOOTED into. It clears the seed after measuring, because `file://` shares one
# origin across every artifact ever opened from it.
BSREAD_CHECK = """<script>
setTimeout(function(){
  if (location.hash !== '#bsread'){
    var s=document.createElement('div');s.id='bsreadcheck';
    s.textContent='BSREAD-SKIP not the boot-seeded-read mode';document.body.appendChild(s);return;
  }
  var lead=document.querySelector('.fcard[data-age="0"][data-imp="3"]');
  var out='BSREAD-SKIP no age0/imp3 lead on this feed';
  if(lead){
    var mb=lead.querySelector('.fcard__more'),sum=lead.querySelector('.fcard__sum');
    var sy0=scrollY;
    var read=lead.classList.contains('is-read')?1:0;
    var fold0=lead.classList.contains('is-folded'),open0=lead.classList.contains('is-open');
    var folded=(fold0&&!open0)?1:0;
    // THE SEAM, READ OFF THE BOOT STATE AND NOT OFF THE POST-CLICK ONE. Computed after the click loop
    // below it could never be 1 — the More handler always leaves `is-folded` or `is-open` set — so the
    // row would have been an assertion that cannot fail. Caught by running this probe against the
    // pre-fix layout, where it printed seam=0 beside four genuine failures.
    var seam=(read&&!fold0&&!open0)?1:0;
    var lbl=mb?mb.querySelector('span').textContent.trim():'-';
    var aria=mb?mb.getAttribute('aria-expanded'):'-';
    var body0=sum?Math.round(sum.getBoundingClientRect().height):-1;
    // THE COST IN CLICKS, which is what the reader actually feels. One is correct; two is the
    // pre-fix behaviour, where the first press only added `is-folded` against an already-hidden body.
    var clicks=0;
    while(mb&&sum&&sum.getBoundingClientRect().height===0&&clicks<4){ mb.click(); clicks++; }
    var v1=window.__hmVoid();
    var upA=(v1.match(/upInv=(\\d+)/)||[0,'?'])[1];
    out='BSREAD read='+read+' folded='+folded+' label='+lbl+' aria='+aria
      +' body0='+body0+' clicksToOpen='+clicks
      +' bodyAfter='+(sum?Math.round(sum.getBoundingClientRect().height):-1)
      +' seam='+seam+' upInv='+upA;
    scrollTo(0,sy0);
    try{ ['homeRead:v1','syncState:v1'].forEach(function(k){ localStorage.removeItem(k); }); }catch(e){}
  }
  var d=document.createElement('div');d.id='bsreadcheck';d.textContent=out;
  document.body.appendChild(d);
},4400);
</script>"""


SYNC_CHECK = """<script>
setTimeout(function(){
  var log = window.__fetchLog || [];
  var rs = log.filter(function(l){ return l.indexOf('/readstate') >= 0; });
  var gets = rs.filter(function(l){ return l.indexOf('GET ') === 0; }).length;
  var prefsCalls = log.filter(function(l){ return l.indexOf('/prefs') >= 0; }).length;
  // roamed read-filter (2026-07-18): the stubbed GET /prefs carries rs:'unread'; signed-in the
  // segmented toggle must land on Unread, signed-out it must stay on All (no prefs traffic).
  var rbOn = document.querySelector('.ff-rbtn[aria-pressed="true"]');
  var prefsRs = location.hash === '#synced'
    ? ((rbOn && rbOn.dataset.rs === 'unread') ? 1 : 0)
    : ((rbOn && rbOn.dataset.rs === '') ? 1 : 0);
  var sids = window.__syncSids || [];
  var painted = -1, unpainted = -1, shadow = -1;
  function cardOf(sid){ var fb = document.querySelector('.fcard__fb[data-story="' + sid + '"]'); return fb && fb.closest('.fcard'); }
  if (location.hash === '#synced' && sids[0] && sids[1]){
    painted = cardOf(sids[0]).classList.contains('is-read') ? 1 : 0;
    unpainted = cardOf(sids[1]).classList.contains('is-read') ? 0 : 1;
    var st = {}; try { st = JSON.parse(localStorage.getItem('syncState:v1') || '{}'); } catch(e){}
    shadow = (st[sids[0]] && st[sids[0]].v === 1 && st[sids[1]] && st[sids[1]].v === 0) ? 1 : 0;
  }
  /* THE ROAM PATH INTO THE READ/FOLD SEAM — the third way a card becomes read, and the one this
     driver could not see (matrix report §9 item 2). `sidA` is pinned to the boot-open lead in
     PRE_SYNC, so the stubbed GET /readstate marks THAT card read and mergeRemote paints it: before
     2026-07-26 it painted without folding, leaving the lead read + un-folded with its control still
     saying "Less". State only, deliberately: the same stubbed roam also carries `rs:'unread'`, so the
     card it just marked read is filtered off the board and a click count here would be measuring
     `display:none` rather than the control (the matrix cell read 4 — the cap — for that reason). The
     click cost is asserted on the boot path, in `#bsread`.
     `roamLeadRead` IS THE PREMISE, asserted like any other row: if the roam ever stops landing on
     the lead, this must fail loudly rather than pass three vacuous assertions. */
  var roamLeadRead = -1, roamFolded = -1, roamLabel = '-', roamAria = '-', roamSeam = -1;
  var leadCard = document.querySelector('.fcard[data-age="0"][data-imp="3"]');
  if (location.hash === '#synced' && leadCard){
    var lmb = leadCard.querySelector('.fcard__more');
    var lFold = leadCard.classList.contains('is-folded');
    var lOpen = leadCard.classList.contains('is-open');
    roamLeadRead = leadCard.classList.contains('is-read') ? 1 : 0;
    roamFolded = (lFold && !lOpen) ? 1 : 0;
    roamLabel = lmb ? lmb.querySelector('span').textContent.trim() : '-';
    roamAria = lmb ? lmb.getAttribute('aria-expanded') : '-';
    roamSeam = (roamLeadRead && !lFold && !lOpen) ? 1 : 0;
  }
  // editorial read state (2026-07-18): clicking the ✓ on an ed- card must toggle is-read and
  // land the ed-<stream>-<date> id in homeRead:v1; a second click must fully undo both.
  var edread = -1;
  var edCard = document.querySelector('.fcard--ed[data-story]');
  var edBtn = edCard && edCard.querySelector('.fcard__read');
  if (edCard && edBtn){
    var edSid = edCard.dataset.story;
    edBtn.click();
    var m1 = {}; try { m1 = JSON.parse(localStorage.getItem('homeRead:v1') || '{}'); } catch(e){}
    var on = edCard.classList.contains('is-read') && !!m1[edSid] && edSid.indexOf('ed-') === 0;
    edBtn.click();
    var m2 = {}; try { m2 = JSON.parse(localStorage.getItem('homeRead:v1') || '{}'); } catch(e){}
    var off = !edCard.classList.contains('is-read') && !m2[edSid];
    edread = (on && off) ? 1 : 0;
  }
  var aff = document.getElementById('ffSync');
  var d = document.createElement('div'); d.id = 'synccheck';
  d.textContent = 'SYNC mode=' + (location.hash === '#synced' ? 'in' : 'out') + ' rsCalls=' + rs.length +
    ' gets=' + gets + ' affordance=' + (aff && !aff.hidden ? 1 : 0) +
    ' painted=' + painted + ' unpainted=' + unpainted + ' shadow=' + shadow +
    ' prefsCalls=' + prefsCalls + ' prefsRs=' + prefsRs + ' edread=' + edread +
    ' roamLeadRead=' + roamLeadRead + ' roamFolded=' + roamFolded +
    ' roamLabel=' + roamLabel + ' roamAria=' + roamAria + ' roamSeam=' + roamSeam;
  document.body.appendChild(d);
}, 4500);
</script>"""


# THE EMPTY BOARD — DRIVEN THE WAY A READER REACHES IT, not by poking `hidden` directly. Marking
# every module read through its own ✓ and then pressing Unread is the exact sequence behind the
# 2026-07-25 owner report, and it is the only sequence that exercises setRead -> apply() ->
# schedulePack together. A probe that set `empty.hidden = false` itself would have passed on the
# broken page: the flag was already correct there, and the message was still off screen.
#
# RUNS LAST (4.8s) AND PUTS THE PAGE BACK. Every other probe here measures the full board, so this
# one must not leave 82 modules marked read behind it — the restore is also the assertion for the
# boot-into-empty path, where an early `return` in the pack engine used to leave `packOn` false and
# swallow every later filter change.
EMPTY_CHECK = """<script>
setTimeout(function(){
  var grid=document.getElementById('folioGrid'), empty=document.getElementById('folioEmpty');
  var board=document.querySelector('.folio-board');
  var cards=[].slice.call(grid.querySelectorAll('.fcard'));
  var keep=location.hash==='#empty';        // stop at the empty state, for the screenshot
  var boot=location.hash==='#bootempty';    // already empty at load — see PRE_SYNC
  function emit(t){ var d=document.createElement('div'); d.id='emptycheck'; d.textContent=t;
    document.body.appendChild(d); }
  var noSid=0;
  cards.forEach(function(c){
    var fb=c.querySelector('.fcard__fb');
    if(!(c.dataset.story||(fb&&fb.dataset.story)))noSid++;
    if(boot)return;                          // the seeded read map already did this
    // ONLY WHAT IS NOT ALREADY READ — the ✓ is a TOGGLE, and this loop used to assume every card
    // boots unread. In `#synced` a roamed remote mark lands one card read before this runs, so the
    // click UN-read it: the probe then reported `vis=1 hidden=1` with a zero-rect message, which is
    // the self-contradiction the external review caught (R17) and read as a broken empty state
    // rather than as a broken probe.
    if(c.classList.contains('is-read'))return;
    var b=c.querySelector('.fcard__read'); if(b)b.click();
  });
  if(!boot)document.querySelector('.ff-rbtn[data-rs="unread"]').click();
  setTimeout(function(){                     // apply()'s re-pack is coalesced through a timeout
    var vis=cards.filter(function(c){return c.style.display!=='none';}).length;
    var er=empty.getBoundingClientRect(),gr=grid.getBoundingClientRect(),br=board.getBoundingClientRect();
    var cs=getComputedStyle(empty);
    var out='EMPTY vis='+vis+' noSid='+noSid+' hidden='+(empty.hidden?1:0)
      +' text="'+empty.textContent+'"'
      +' h='+Math.round(er.height)+' w='+Math.round(er.width)
      +' absTop='+Math.round(er.top+scrollY)
      +' topDelta='+Math.round(er.top-gr.top)+' leftDelta='+Math.round(er.left-gr.left)
      +' sheetTop='+Math.round(gr.top-br.top)
      +' inGrid='+((empty.parentElement===grid&&er.top>=gr.top-1&&er.bottom<=gr.bottom+1)?1:0)
      +' display='+cs.display+' align='+cs.alignSelf
      +' packedEmpty='+(grid.classList.contains('packed')?1:0)
      +' rowUnit='+getComputedStyle(grid).gridAutoRows
      +' rs='+((document.querySelector('.ff-rbtn[aria-pressed="true"]')||{dataset:{}}).dataset.rs||'all');
    /* THE SCREENSHOT MODE ABANDONS THE PAGE MID-STATE, so it clears what it wrote to storage
       before it does. `file://` shares ONE origin across every artifact ever opened from it, so 82
       read entries left behind here would boot the next run — any run, this harness or another
       agent's — into a half-read board. PRE_SYNC's reset happens to cover it today; that is a side
       effect of a different probe, not a guarantee this one may lean on. */
    if(keep){
      try{ ['homeRead:v1','topicPrefs:v1'].forEach(function(k){ localStorage.removeItem(k); }); }catch(e){}
      emit(out+' restored=- rePacked=- reSpanned=-'); return;
    }
    /* CLEARING THE FILTER IS THE OTHER HALF OF THE TEST, not just cleanup. The pack engine has to
       be armed on the way out of an empty board — under `#bootempty` the empty pass IS the first
       pass — so a board that comes back UNPACKED here is the regression, and every other probe on
       this page would still be green while it happened. */
    document.querySelector('.ff-rbtn[data-rs=""]').click();      // back to All ...
    if(!boot)cards.forEach(function(c){ if(c.classList.contains('is-read')){
      var b=c.querySelector('.fcard__read'); if(b)b.click(); } });   // ... and unread again
    /* `#bootempty` clears the map it was SEEDED with (PRE_SYNC wrote all 82 entries before the
       layout script ran, so there is nothing for this probe to un-click). Leaning on PRE_SYNC's
       own reset to cover it is a side effect of a different probe, which is exactly what the note
       above refuses to rely on. */
    if(boot){ try{ ['homeRead:v1','topicPrefs:v1','syncState:v1'].forEach(function(k){
      localStorage.removeItem(k); }); }catch(e){} }
    window.__hmRestoreBootOpen();   // the mass-mark above normalized every boot-open card to folded
    setTimeout(function(){
      var back=cards.filter(function(c){return c.style.display!=='none';}).length;
      var spanned=cards.filter(function(c){return !!c.style.gridRow;}).length;
      emit(out+' restored='+((back===cards.length&&empty.hidden)?1:0)
        +' rePacked='+(grid.classList.contains('packed')?1:0)+' reSpanned='+spanned
        +' stillRead='+cards.filter(function(c){return c.classList.contains('is-read');}).length);
    },250);
  },300);
},4800);
</script>"""


def card(s):
    e = lambda x: html.escape(str(x or ""))
    lead = " lead" if s["is_lead"] else ""
    og = ' data-ogurl="%s"' % e(s["url"]) if s.get("url") and s["importance"] > 1 else ""
    hl = ('<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>' % (e(s["url"]), e(s["headline"]))
          if s.get("url") else e(s["headline"]))
    # mirrors the layout's `{% unless hl_last == '?' ... %}` — a headline ending in ? or ! must not
    # render "?." once .fcard__hl--dot::after adds the terminal period.
    _hl = (s["headline"] or "").strip()
    if _hl[-1:] in ('"', "'", "\u201d", "\u2019"):     # a headline may close on a quote
        _hl = _hl[:-1]
    dot = "" if _hl[-1:] in ("?", "!", ".") else " fcard__hl--dot"
    # mirrors the layout: since the 2026-07-25 fold ruling every tier hides its body when folded,
    # so More is emitted wherever there IS a body. Still "only where it reveals something" — the
    # old deck-or-brief condition existed only because a deckless lead used to stay open.
    more = ('<button class="fcard__more" type="button" aria-expanded="true">'
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>'
            '<span>More</span></button>'
            if s["summary"] else "")
    deck = '<p class="fcard__deck">%s</p>' % e(s["deck"]) if s.get("deck") else ""
    # placed exactly where swapImage() places it: after the deck when there is one, else after the
    # headline — never above the headline, which is the whole point of the 2026-07-25 fix.
    img = ('<img class="fimg" src="%s" alt="" loading="eager" referrerpolicy="no-referrer">' % IMG_PH
           if _wants_image(s) else "")
    summ = '<p class="fcard__sum">%s</p>' % e(s["summary"]) if s["summary"] else ""
    why = ('<p class="fcard__why"><span class="fcard__why-lbl">Why it matters</span>%s</p>' % e(s["why"])
           if s.get("why") else "")
    fresh = '<span class="fcard__fresh">Just in</span>' if s.get("fresh") and s["importance"] > 1 else ""
    readbtn = ('<button class="fcard__read" type="button" aria-pressed="false" aria-label="Mark as read"'
               ' title="mark as read"><svg viewBox="0 0 24 24" aria-hidden="true">'
               '<path d="M20 6L9 17l-5-5"/></svg></button>')
    # institution-first source label (mirrors the Liquid in _layouts/home.html)
    src = ('<span class="fcard__aff">%s</span> · %s' % (e(s["affiliation_label"]), e(s["source_domain"]))
           if s.get("affiliation_label") else e(s["source_domain"]))
    # board fields (2026-07-26): `data-age` drives the age demotion and the fold default,
    # `data-daybreak` + the printed day mark each date block's first card.
    day = '<span class="fcard__day">%s</span>' % e(s.get("day_label")) if s.get("daybreak") else ""
    return """<article class="fcard imp%(imp)s%(lead)s" data-topics="%(topics)s" data-imp="%(imp)s" data-age="%(age)s"%(db)s%(dk)s%(og)s>
<div class="fcard__in" style="--tc:%(color)s">
<div class="fcard__top">%(day)s<span class="fcard__beat" title="%(stream)s · %(dlabel)s"><span class="ff-dot"></span>%(tlabel)s</span><span class="fcard__rank" data-imp="%(imp)s"><i class="tier-key" aria-hidden="true"></i>%(rank)s</span></div>
<h2 class="fcard__hl%(dot)s">%(hl)s</h2>
%(deck)s%(img)s%(summ)s%(why)s%(more)s
<div class="fcard__line"><span class="fcard__src">%(src)s</span>%(fresh)s<span class="fcard__date">%(dlabel)s</span>%(readbtn)s</div>
<div class="fcard__fb" data-story="%(id)s" data-brief="%(date)s-%(stream)s">
<button class="ffb-t" type="button" data-v="1" aria-label="Useful">%(svg)s</button>
<button class="ffb-t ffb-down" type="button" data-v="-1" aria-label="Not useful">%(svg)s</button>
<span class="ffb-note" aria-live="polite"></span></div>
</div></article>""" % {
        "imp": s["importance"], "rank": {3:"Lead",2:"Feature"}.get(s["importance"],"Brief"),
        "lead": lead, "topics": e(" ".join(s["topics"])), "og": og,
        "color": s["topic_color"], "tlabel": e(s["topic_label"]), "hl": hl, "summ": summ, "why": why,
        "src": src, "fresh": fresh, "dlabel": e(s["date_label"]),
        "id": e(s.get("sid") or s["id"]), "date": e(s["date"]), "stream": e(s["stream"]), "svg": SVG,
        "readbtn": readbtn, "more": more, "dot": dot, "deck": deck, "img": img,
        "dk": ' data-deck=""' if s.get("deck") else "",
        "age": s.get("age_days", 0), "db": ' data-daybreak=""' if s.get("daybreak") else "",
        "day": day,
    }


def _require_board(feed):
    """The page renders `feed.board` — ONE ranked sequence over stories and editorials — so this
    harness must render the same sequence or every screenshot certifies an order the site does not
    have.

    What was here: `_extract_ed_after()`, which read `{% assign ed_after = 3 %}` out of the layout
    so the harness spliced the editorials at production's index. That assign is gone with the
    splice (2026-07-26); the board replaced it. Extraction was the right instinct then and the
    right instinct now — the difference is that the order is data rather than a constant, so the
    harness reads the data instead of scraping a number out of a template.
    """
    board = feed.get("board")
    if not board:
        raise SystemExit("home_harness: _data/homefeed.json has no `board` — regenerate it with "
                         "tools/build_stories_feed.py; the layout renders feed.board")
    for i, it in enumerate(board):
        if it.get("kind") not in ("story", "editorial"):
            raise SystemExit("home_harness: board[%d] has kind=%r — the layout branches on "
                             "'editorial' vs everything else" % (i, it.get("kind")))
    return board


def _extract_rail(feed):
    """The >=1280px rail, READ out of the layout rather than mirrored here.

    Without it this harness reserved the rail's grid track and rendered NOTHING in it — roughly
    390px of blank left margin at 1440 — and that fake defect cost a revert and a re-land on
    2026-07-25 before a live-DOM probe showed production's rail present, 286x567, with content.
    A harness that omits markup the layout emits does not merely fail to test it; it invents
    defects. Extracted, so it cannot drift.

    The Liquid in the block is substituted from the same feed the cards come from. Any OTHER tag
    appearing in there is a hard error: silently shipping `{{ ... }}` into the page would render as
    literal braces and quietly change wrap widths.
    """
    src = os.path.join(ROOT, "_layouts", "home.html")
    with open(src) as fh:
        m = re.search(r'<aside class="folio-rail">.*?</aside>', fh.read(), re.S)
    if not m:
        raise SystemExit("home_harness: no <aside class=\"folio-rail\"> in %s — if the rail was "
                         "renamed or removed, update this extractor deliberately" % src)
    rail = m.group(0)
    # Jekyll drops {%- comment -%} blocks; leaving them in would trip the leftover-Liquid guard
    # below on the rail's own design notes.
    rail = re.sub(r"\{%-?\s*comment\s*-?%\}.*?\{%-?\s*endcomment\s*-?%\}", "", rail, flags=re.S)
    first = (feed.get("stories") or [{}])[0]
    rail = re.sub(r"\{\{\s*feed\.stories\.first\.date_label\s*\}\}",
                  html.escape(str(first.get("date_label") or "")), rail)

    # The rail's beat chips are a `{% for t in feed.topics %}` loop. WITHOUT expanding it the guard
    # below fires — loudly, which is correct — but the tempting "fix" of dropping the loop instead
    # would render a rail holding only the All chip, i.e. a harness that certifies a selector the
    # page does not have. Expanded from the same `feed["topics"]` the bar's chips come from, so the
    # two renderings of the one control cannot disagree here for a reason production would not have.
    def _topics(m):
        out = []
        for t in feed.get("topics") or []:
            body = m.group(1)
            for k in ("key", "color", "label", "count"):
                body = re.sub(r"\{\{\s*t\.%s\s*\}\}" % k, html.escape(str(t.get(k, ""))), body)
            out.append(body)
        return "".join(out)
    rail = re.sub(r"\{%-?\s*for\s+t\s+in\s+feed\.topics\s*-?%\}(.*?)\{%-?\s*endfor\s*-?%\}",
                  _topics, rail, flags=re.S)
    rail = re.sub(r"\{\{\s*feed\.count\s*\}\}", str(feed.get("count") or 0), rail)

    # THE SUNDAY REVIEW LINK. Resolved from `_posts/*-evaluator.md` — the same files
    # `site.categories.evaluator` resolves from, since evaluator posts are the only ones that opt
    # back into rendering — rather than dropped, which would photograph a rail the page does not
    # have. The permalink shape is `_config.yml`'s `/:year/:month/:day/:title/`.
    evs = sorted(glob.glob(os.path.join(ROOT, "_posts", "*-evaluator.md")))
    if evs:
        d = os.path.basename(evs[-1])[:10]
        y, mo, dy = d.split("-")
        rail = re.sub(r"\{%-?\s*if\s+review\s*-?%\}(.*?)\{%-?\s*endif\s*-?%\}",
                      lambda m: m.group(1), rail, flags=re.S)
        rail = re.sub(r"\{\{\s*review\.url\s*\|\s*relative_url\s*\}\}",
                      "/%s/%s/%s/evaluator/" % (y, mo, dy), rail)
        rail = re.sub(r"""\{\{\s*review\.date\s*\|\s*date:\s*["'][^"']*["']\s*\}\}""",
                      "%d %s" % (int(dy), _MONTHS[int(mo) - 1]), rail)
    else:
        rail = re.sub(r"\{%-?\s*if\s+review\s*-?%\}.*?\{%-?\s*endif\s*-?%\}", "", rail, flags=re.S)
    rail = re.sub(r"\{%-?\s*assign\s+review\s*=[^%]*-?%\}", "", rail)

    leftover = re.findall(r"\{\{.*?\}\}|\{%.*?%\}", rail, re.S)
    if leftover:
        raise SystemExit("home_harness: un-substituted Liquid in the rail markup: %r — add a "
                         "substitution for it rather than rendering literal braces" % leftover)
    return rail


def _extract_block(start_re, label, allow_liquid=False):
    """Pull a static markup block out of the layout verbatim, like `_extract_rail` does.

    Added 2026-07-25 for the page header and the How-this-works modal. Neither was ever in this
    harness, so the nameplate/header composition and the modal's open path could not be reviewed
    here at all — the same blindness that let the image slot and the tier legend go unseen. Both
    blocks are pure static markup, so verbatim extraction is exact; any Liquid appearing in them
    later is a hard error rather than a silent literal.
    """
    src = os.path.join(ROOT, "_layouts", "home.html")
    with open(src) as fh:
        body = fh.read()
    m = re.search(start_re, body, re.S)
    if not m:
        raise SystemExit("home_harness: could not find the %s block in %s — if it was renamed, "
                         "update this extractor deliberately" % (label, src))
    block = m.group(0)
    block = re.sub(r"\{%-?\s*comment\s*-?%\}.*?\{%-?\s*endcomment\s*-?%\}", "", block, flags=re.S)
    # `| relative_url` on repo assets — same substitution the @font-face src needs, and for the
    # same reason: this is a project Pages site under a baseurl, so Jekyll expands these and
    # verbatim extraction does not. The modal's diagrams are the case in point; without this the
    # harness would paint broken images and the guard below (correctly) refuses to let that pass.
    block = re.sub(r"""\{\{\s*["'](/[^"']+)["']\s*\|\s*relative_url\s*\}\}""",
                   lambda m: "file://" + ROOT + m.group(1), block)
    # `allow_liquid` is for a block the CALLER substitutes (the editorial card, whose fields come
    # from the feed the same way _extract_rail's do). It still has to answer for every tag: the
    # caller runs the identical guard after substituting.
    leftover = re.findall(r"\{\{.*?\}\}|\{%.*?%\}", block, re.S)
    if leftover and not allow_liquid:
        raise SystemExit("home_harness: un-substituted Liquid in the %s block: %r"
                         % (label, leftover[:3]))
    return block


def _hiw_stub():
    """A CONTRACT stub for the How-this-works modal — deliberately not the real markup.

    The real modal cannot be extracted: its proof section is a `{% if site.data.stats %}` block
    with real Liquid logic, and expanding that here would mean reimplementing Liquid against
    _data/stats — the mirror-that-drifts this harness keeps deleting. Its CONTENTS are also not
    what any of this exercises. What is under test is the open path: two `.hiw-open` buttons in
    different places, one binding, one modal.

    So the stub carries only the contract the script depends on, and the contract is CHECKED
    against the layout rather than assumed — if the real modal ever stops being `#hiwModal` with a
    `[data-hiw-close]` inside it, this fails loudly instead of testing a fiction.
    """
    src = os.path.join(ROOT, "_layouts", "home.html")
    with open(src) as fh:
        body = fh.read()
    for needle, what in (('id="hiwModal"', "the modal id"),
                         ("data-hiw-close", "a close control")):
        if needle not in body:
            raise SystemExit("home_harness: %s is gone from %s — the modal stub below encodes it, "
                             "so update both deliberately" % (what, src))
    return ('<div class="hiw" id="hiwModal" aria-hidden="true">'
            '<div class="hiw__box" role="dialog" aria-modal="true" aria-label="How this works">'
            '<button type="button" class="hiw__x" data-hiw-close aria-label="Close">&times;</button>'
            '<p>Harness stub — the real modal body is Liquid over site.data.stats.</p>'
            '</div></div>')


_ED_TEMPLATE = None


def _ed_template():
    """The editorial card's REAL markup, extracted from the layout once (review R17).

    The hand-mirrored copy this replaces had already drifted: it emitted no `.fcard__fb` strip at
    all, so the editorial card's two vote buttons and its note span — production markup since the
    editorials shipped — were never on screen here, never measured, and never in a screenshot.
    That is the same blindness as the image slot, the tier legend and the page header, and this
    repo's standing answer to it is extraction rather than a "keep in step" comment.
    """
    global _ED_TEMPLATE
    if _ED_TEMPLATE is None:
        _ED_TEMPLATE = _extract_block(
            r'<article class="fcard fcard--ed".*?</article>', "editorial card",
            allow_liquid=True)
    return _ED_TEMPLATE


def ed_card(e):
    """The extracted editorial template with this item's fields substituted in.

    Liquid handled here, and NOTHING else — any other tag is a hard error below, because rendering
    `{{ ... }}` literally would change wrap widths and photograph as content.
    """
    esc = lambda x: html.escape(str(x or ""))
    block = _ed_template()

    # {% if it.daybreak %}…{% endif %} / {% if it.title != blank %}…{% endif %}
    def _cond(m):
        return m.group(2) if _truthy(e, m.group(1)) else ""
    block = re.sub(r"\{%-?\s*if\s+it\.(\w+)(?:\s*!=\s*blank)?\s*-?%\}(.*?)\{%-?\s*endif\s*-?%\}",
                   _cond, block, flags=re.S)
    # {% for p in it.paras %}<p …>{{ p }}</p>{% endfor %}  — paras are pre-sanitized html
    block = re.sub(
        r"\{%-?\s*for\s+p\s+in\s+it\.paras\s*-?%\}(.*?)\{%-?\s*endfor\s*-?%\}",
        lambda m: "".join(re.sub(r"\{\{\s*p\s*\}\}", p, m.group(1)) for p in e.get("paras") or []),
        block, flags=re.S)
    block = re.sub(r"\{\{\s*it\.(\w+)\s*\}\}", lambda m: esc(e.get(m.group(1))), block)

    leftover = re.findall(r"\{\{.*?\}\}|\{%.*?%\}", block, re.S)
    if leftover:
        raise SystemExit("home_harness: un-substituted Liquid in the editorial card: %r — add a "
                         "substitution rather than rendering literal braces" % leftover[:3])
    return block


def _truthy(item, field):
    v = item.get(field)
    return bool(v) and v != ""


MARKERS = ("GEOM", "DAY", "FILTER", "FOLD", "LEADREAD", "BSREAD", "READ", "SYNC", "EMPTY")

CHROME = os.environ.get("CHROME_BIN",
                        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

# THE ASSERTION TABLE — this is what turns the probes above from a REPORT into an ORACLE (review
# R17). Until now every check appended diagnostic text and nothing on earth parsed it: the `#synced`
# EMPTY probe printed `vis=1 hidden=1`, contradicting its own zero-card invariant, and the harness
# still exited 0. A number nobody compares is a number nobody reads.
# Each entry is (marker, key, predicate, prose). `min_width` gates the rows that are only true where
# the board has more than one column — below 700px `packRowSpans` unpacks BY DESIGN, so demanding a
# packed board there would be asserting the opposite of the code's intent.
CHECKS = [
    ("GEOM", "widthSane", lambda v: v == "1", "the board has not shrink-wrapped"),
    ("GEOM", "upInv", lambda v: v == "0", "no card is placed above one ranked ahead of it"),
    ("GEOM", "maxUp", lambda v: v == "0", "...and not by a single pixel"),
    ("GEOM", "ovOk", lambda v: v == "1", "overflow stays visible — a short span may never clip"),
    ("GEOM", "cards", lambda v: int(v) > 0, "the board rendered cards at all"),
    ("DAY", "dbOk", lambda v: v == "1", "exactly the first card of each date block prints its day"),
    ("FILTER", "upInv", lambda v: v == "0", "order holds in the filtered state"),
    ("FILTER", "holes", lambda v: v == "0", "no interior hole in the filtered state"),
    ("FOLD", "opened", lambda v: v == "1", "More opens the module"),
    ("FOLD", "collapsed", lambda v: v == "1", "Less restores it byte-for-byte in height"),
    ("FOLD", "drift", lambda v: abs(int(v)) <= 1, "the clicked module does not move under the cursor"),
    ("FOLD", "openWSame", lambda v: v == "1", "expansion is height-only — the module never widens"),
    ("FOLD", "hlSame", lambda v: v == "1", "type scale is invariant under More"),
    ("FOLD", "holes", lambda v: v == "0", "the open state leaves no interior hole"),
    ("FOLD", "holePx", lambda v: v == "0", "...and no interior void px"),
    ("FOLD", "upInv", lambda v: v == "0", "order holds with a module open"),
    ("LEADREAD", "spined", lambda v: v == "1", "reading a boot-open card collapses it to its spine"),
    ("LEADREAD", "folded", lambda v: v == "1", "...and normalizes it to is-folded, without is-open"),
    ("LEADREAD", "label", lambda v: v == "More", "its control agrees with what the card now looks like"),
    ("LEADREAD", "aria", lambda v: v == "false", "...and so does aria-expanded"),
    ("LEADREAD", "oneClick", lambda v: v == "1", "ONE click re-opens it (it used to take two)"),
    ("LEADREAD", "upInvRead", lambda v: v == "0", "order holds through the read transition"),
    ("LEADREAD", "upInvOpen", lambda v: v == "0", "order holds through the re-open"),
    ("LEADREAD", "restored", lambda v: v == "1", "the probe put the boot-open card back"),
    ("READ", "spineOk", lambda v: v == "1",
     "a read lead/feature collapses to <=0.70x its folded height (image slot excluded)"),
    ("READ", "imgKept", lambda v: v == "1", "every image card on an all-read board keeps its photo"),
    ("READ", "reopen", lambda v: v == "1", "More re-opens a READ card in place (:not(.is-open) guards)"),
    ("READ", "edOk", lambda v: v == "1", "the AI disclosure is visible folded, open, read and read+open"),
    ("READ", "gridDrop", lambda v: int(v) >= 25, "an all-read board is at least 25% shorter"),
    ("READ", "upInv", lambda v: v == "0", "order holds with every card read"),
    ("READ", "holes", lambda v: v == "0", "no interior hole with every card read"),
    ("READ", "restored", lambda v: v == "1", "un-reading restores the board's height"),
    ("READ", "stillRead", lambda v: v == "0", "the probe cleaned up after itself"),
    ("EMPTY", "vis", lambda v: v == "0", "the filter really emptied the board"),
    ("EMPTY", "hidden", lambda v: v == "0", "and the empty message really shows"),
    ("EMPTY", "topDelta", lambda v: abs(int(v)) <= 2, "it opens the sheet, not a rail-height void"),
    ("EMPTY", "packedEmpty", lambda v: v == "0", "the 4px row unit came off for the empty state"),
    ("EMPTY", "restored", lambda v: v == "1", "clearing the filter brings the board back"),
    ("EMPTY", "rePacked", lambda v: v == "1", "...packed, i.e. the pack engine stayed armed", 700),
    ("SYNC", "edread", lambda v: v == "1", "an editorial card's read toggle round-trips"),
]

# Signed-in only (`--hash '#synced'`). Read state now changes GEOMETRY, so a roam landing after boot
# is the highest-risk path in this rework — it repaints spines, some above the viewport, and it is
# the reason mergeRemote() got the anchor bracket. Every row in CHECKS above holds in this mode too
# (DAY correctly reports DAY-SKIP, since the roamed Unread filter makes it a filtered view).
SYNCED_CHECKS = [
    ("SYNC", "gets", lambda v: v == "1", "the signed-in boot pulls /readstate exactly once"),
    ("SYNC", "painted", lambda v: v == "1", "a remote mark paints the card read"),
    ("SYNC", "unpainted", lambda v: v == "1", "a newer remote tombstone un-marks a locally-read card"),
    ("SYNC", "shadow", lambda v: v == "1", "both land in the syncState:v1 shadow"),
    ("SYNC", "prefsRs", lambda v: v == "1", "a roamed read-filter lands on the segmented toggle"),
    # THE ROAM PATH'S FOLD NORMALIZATION (2026-07-26). The premise first, then the three facts that
    # were wrong before `mergeRemote` called `paintReadState`: 24 matrix cells failed on `seamN` and
    # this driver could not see any of them, because every read state it reached, it reached by click.
    ("SYNC", "roamLeadRead", lambda v: v == "1",
     "PREMISE: the stubbed roam really marks the boot-open lead read"),
    ("SYNC", "roamFolded", lambda v: v == "1",
     "...and a roamed mark folds the card it lands on, exactly as a click does"),
    ("SYNC", "roamLabel", lambda v: v == "More", "...with its control agreeing"),
    ("SYNC", "roamAria", lambda v: v == "false", "...and so does aria-expanded"),
    ("SYNC", "roamSeam", lambda v: v == "0",
     "...so no roamed card is left read, un-folded and claiming 'Less'"),
]

# Boot-seeded-read only (`--hash '#bsread'`), and the ONLY rows scored in that mode — the seeded lead
# makes the whole board a different state from the one every other probe on the page asserts about
# (READ would tick an already-read card, LEADREAD's boot-open set is one card smaller), exactly as
# `#bootempty` scores only EMPTY. The mode is driven by --check itself; see main().
BSREAD_CHECKS = [
    ("BSREAD", "read", lambda v: v == "1", "PREMISE: the seed really booted the lead read"),
    ("BSREAD", "folded", lambda v: v == "1",
     "a lead that was ALREADY read at boot is folded, without is-open"),
    ("BSREAD", "label", lambda v: v == "More", "...with its control agreeing"),
    ("BSREAD", "aria", lambda v: v == "false", "...and so does aria-expanded"),
    ("BSREAD", "body0", lambda v: v == "0", "...over a body the read spine is hiding"),
    ("BSREAD", "clicksToOpen", lambda v: v == "1", "ONE click re-opens it (it used to take two)"),
    ("BSREAD", "seam", lambda v: v == "0", "...i.e. the boot path leaves no un-folded read card"),
    ("BSREAD", "upInv", lambda v: v == "0", "order holds through the re-open"),
]


def _run_check(artifact, width, height=2800, budget=9000, hash=""):
    """Render the artifact in headless Chrome, parse every probe marker, apply CHECKS.

    Returns (failures, lines). A marker that never appears is itself a failure: a probe that did
    not run cannot have passed, and a silently missing probe is exactly how a green harness
    certified a broken page three times in this repo's history.
    """
    import subprocess
    cmd = [CHROME, "--headless=new", "--hide-scrollbars", "--disable-gpu", "--no-sandbox",
           "--virtual-time-budget=%d" % budget, "--window-size=%d,%d" % (width, height),
           "--dump-dom", "file://" + artifact + hash]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=300).stdout
    # PARSED OFF THE PROBE ELEMENTS, never off the page text. The dumped DOM contains the probes'
    # own SOURCE — they are inline <script> bodies — so a bare search for `GEOM …` matches the code
    # that emits the marker and reads its variable NAMES as values. Every probe appends
    # `<div id="…check">`, so that is the only thing this looks at.
    marks = {}
    for div_id, mk in (("geomcheck", "GEOM"), ("daycheck", "DAY"), ("filtercheck", "FILTER"),
                       ("foldcheck", "FOLD"), ("leadreadcheck", "LEADREAD"),
                       ("bsreadcheck", "BSREAD"),
                       ("readcheck", "READ"), ("synccheck", "SYNC"), ("emptycheck", "EMPTY")):
        m = re.search(r'<div id="%s"[^>]*>(.*?)</div>' % div_id, out, re.S)
        if not m:
            continue
        text = re.sub(r"\s+", " ", m.group(1)).strip()
        name = text.split(" ", 1)[0]
        kv = dict(re.findall(r"(\w+)=([^\s\]]+)", text))
        marks[mk] = (name, kv, text)
    lines, failures = [], []
    for mk in MARKERS:
        if mk in marks:
            lines.append("  %s" % marks[mk][2])
        else:
            lines.append("  %s  <MARKER MISSING>" % mk)
    if hash == "#bootempty":
        # The ONLY mode where the pack engine's first pass ever sees zero modules, and the only
        # thing it can prove: clearing the filter re-arms the packer. Every other row here is
        # expected noise there (GEOM cards=0, FOLD-SKIP, SYNC edread=0 — every card boots read), so
        # scoring them would be scoring the mode's own premise as a failure.
        rows = [r for r in CHECKS if r[0] == "EMPTY"]
    elif hash == "#bsread":
        # ONLY the boot-seeded rows, for the reason `#bootempty` scores only EMPTY: the mode's premise
        # is a board one card of which is read before any probe runs, which is not the board the other
        # eight probes assert about. Their lines are still printed, so the state is visible.
        rows = BSREAD_CHECKS
    else:
        rows = CHECKS + (SYNCED_CHECKS if hash == "#synced" else [])
    for row in rows:
        mk, key, pred, why = row[0], row[1], row[2], row[3]
        if len(row) > 4 and width < row[4]:
            continue
        if mk not in marks:
            failures.append("%s.%s: probe never emitted — %s" % (mk, key, why))
            continue
        name, kv, _ = marks[mk]
        if name.endswith("-SKIP"):
            continue
        if key not in kv:
            failures.append("%s.%s: key absent from the marker — %s" % (mk, key, why))
            continue
        try:
            ok = pred(kv[key])
        except (ValueError, TypeError):
            ok = False
        if not ok:
            failures.append("%s.%s=%s — expected: %s" % (mk, key, kv[key], why))
    return failures, lines


# =============================================================================================
# THE STATE MATRIX DRIVER — one Chrome run per cell, one row per cell, a real exit status.
# =============================================================================================

# HEADLESS CHROME CLAMPS `--window-size` WIDTH TO 500px, and nothing lifts it: not
# `--hide-scrollbars`, not `--force-device-scale-factor`. Measured 2026-07-26 on this artifact —
# `--window-size=390,2800` reports `innerW=500`, so EVERY "390px" number this harness has ever
# printed (and `/tmp/home-shots/390-resting.png`, which is 500px wide) was taken at 500. Below the
# floor the artifact is rendered inside an `<iframe>` of the exact width in a 500px window: media
# queries fire against the iframe's viewport, and the parent copies the probe's marker out of the
# frame so `--dump-dom` can see it. That copy needs `--allow-file-access-from-files` (two `file://`
# documents are opaque origins to each other without it), and the flag is therefore passed on EVERY
# matrix run, not only the narrow ones, so all widths are measured under one flag set.
MX_FLOOR = 500

MX_FRAME = """<!doctype html><meta charset="utf-8"><title>mx frame %(w)d</title>
<style>html,body{margin:0;padding:0;background:#fff}iframe{border:0;display:block}</style>
<body>
<iframe id="f" src="%(src)s" style="width:%(w)dpx;height:%(h)dpx"></iframe>
<script>
var tries = 0;
(function poll(){
  tries++;
  var done = 0;
  try {
    var d = document.getElementById('f').contentDocument;
    var m = d && (d.getElementById('mxcheck') || d.getElementById('mxstruct'));
    if (m){
      var o = document.createElement('div'); o.id = m.id;
      o.setAttribute('style','display:none');
      o.textContent = m.textContent + ' frameW=' + d.defaultView.innerWidth;
      document.body.appendChild(o); done = 1;
    }
  } catch(e){
    var er = document.createElement('div'); er.id = 'mxcheck';
    er.textContent = 'MX FRAME-ERROR ' + e.name; document.body.appendChild(er); done = 1;
  }
  if (!done && tries < 60) setTimeout(poll, 250);
})();
</script>
"""


def _mx_url(artifact, cell_hash, width, height, tmpdir="/tmp"):
    """The URL to drive for a cell, and the real viewport width it will report.

    At or above the 500px floor that is the artifact itself. Below it, a wrapper page holding an
    iframe of the exact width — see MX_FLOOR.
    """
    if width >= MX_FLOOR:
        return "file://" + artifact + cell_hash, width
    path = os.path.join(tmpdir, "mx-frame-%d.html" % width)
    with open(path, "w") as fh:
        fh.write(MX_FRAME % {"src": "file://" + artifact + cell_hash, "w": width, "h": height})
    return "file://" + path, MX_FLOOR


# THE COLOUR SCHEME IS PINNED, BECAUSE HEADLESS CHROME INHERITS THE HOST'S APPEARANCE. Caught
# 2026-07-26 in the middle of this pass: fifteen shots came out on dark paper and the four re-taken
# twenty minutes later came out on light, from the same artifact and the same flags — the Mac's
# appearance had changed under the run (`defaults read -g AppleInterfaceStyle`), and
# `prefers-color-scheme` follows it. A screenshot set whose theme depends on the wall clock is not a
# baseline. `--blink-settings=preferredColorScheme=0` is dark and `=1` is light (verified by reading
# `matchMedia('(prefers-color-scheme: dark)').matches` back out of the page under each; `=2` yields
# NEITHER media query matching, and `--force-dark-mode` also works but is the auto-darkening feature
# rather than the media query, so it is not what this uses).
# Geometry is theme-independent — 1440 E1 measured gridH=18709 under both, 390 E1 41606 under both —
# so this pins the pictures, not the numbers. The numbers were never at risk; the review of them was.
MX_SCHEMES = {"dark": "0", "light": "1"}


def _mx_chrome(url, window_w, height, budget=16000, shot=None, scheme="dark"):
    import subprocess
    cmd = [CHROME, "--headless=new", "--hide-scrollbars", "--disable-gpu", "--no-sandbox",
           "--allow-file-access-from-files",
           "--blink-settings=preferredColorScheme=%s" % MX_SCHEMES[scheme],
           "--virtual-time-budget=%d" % budget, "--window-size=%d,%d" % (window_w, height)]
    cmd.append("--screenshot=" + shot if shot else "--dump-dom")
    cmd.append(url)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=300).stdout


# THE MATRIX ASSERTION TABLE. Rows marked `all` hold in EVERY cell — they are the invariants the
# spec asks for by name (order, holes, never-crop, the disclosure, the tally, the empty state, the
# type scale under More, honest daybreaks). Rows keyed to a cell flag apply only where that state
# exists. `min_width` gates the rows that are only true where the board has more than one column.
MX_CHECKS = [
    ("upInv", lambda v, c: v == "0", "DOM order == visual order: nothing is placed above its rank"),
    # `maxUp` is asserted at ZERO, not at a tolerance, because that is what it measures: read,
    # filtered, open and 390px states were all probed for it first (2026-07-26) and every one of
    # them read 0, so a tolerance here would only hide a real upward drift.
    ("maxUp", lambda v, c: v == "0", "...and not by a single pixel"),
    ("holes", lambda v, c: v == "0", "no unfilled paper inside a column track"),
    ("holePx", lambda v, c: v == "0", "...and no interior void px"),
    ("ovOk", lambda v, c: v == "1", "overflow stays visible — a short span may never clip"),
    ("edDiscOk", lambda v, c: v == "1", "the AI disclosure paints on every editorial card on screen"),
    ("uctOk", lambda v, c: v == "1", "the unread tally equals the board's unread stories"),
    ("uctVisOk", lambda v, c: v == "1" or c.get("band") != "1",
     "...and in an UNFILTERED view that is also what is on screen"),
    ("emptyOk", lambda v, c: v == "1", "the empty state shows iff the board is empty, with a whole sentence"),
    ("ageMono", lambda v, c: v == "1", "no card carries a smaller data-age than one above it"),
    ("dbDesc", lambda v, c: v == "1", "the daybreaks on screen are in strictly descending date order"),
    ("dateBlocked", lambda v, c: v == "1", "each date holds one contiguous run — no interleaving"),
    ("dbPrinted", lambda v, c: v == c.get("_dbVis"), "every daybreak card on screen prints its day"),
    ("rtOk", lambda v, c: v == "1", "the round trip restores spans, counts and the composition band"),
    ("hlSame", lambda v, c: v == "1", "type scale is invariant under More"),
    ("openWSame", lambda v, c: v == "1", "expansion is height-only — the module never widens"),
    ("drift", lambda v, c: abs(int(v)) <= 1, "the opened module does not move under the cursor"),
    ("eOpened", lambda v, c: int(v) >= 1, "More actually opened the module"),
    ("e3Reopen", lambda v, c: v == "1", "More re-opens a READ spine in place (.is-open beats .is-read)"),
    # THE READ DEMOTION IS A PAIR, and both halves are asserted because either one alone passes on a
    # broken page: demoted when read and folded, restored to the card's OWN rank scale when opened.
    # Before the `:not(.is-open)` guard the second was false and `hlSame` recorded that as invariance.
    ("e3HlDemoted", lambda v, c: v == "1", "reading a card demotes its headline to brief scale"),
    ("e3HlRestored", lambda v, c: v == "1",
     "...and More lifts the demotion exactly, back to the scale the card had unread"),
    ("e4StaysOpen", lambda v, c: v == "1", "a module the reader opened stays open when it is ticked read"),
    ("e4Label", lambda v, c: v == "Less", "...and its control still says so"),
    ("e4HlSame", lambda v, c: v == "1",
     "...and its headline keeps its RANK scale — reading an open card may not demote its type"),
    ("blSpined", lambda v, c: v == "1", "reading the boot-open lead collapses it to its spine"),
    ("blFolded", lambda v, c: v == "1", "...in ONE state transition, to is-folded without is-open"),
    ("blLabel", lambda v, c: v == "More", "...with its control agreeing"),
    ("blOneClick", lambda v, c: v == "1", "...and ONE click re-opens it"),
    ("spineOk", lambda v, c: v == "1", "every read story card that is not open shows a zero-height body"),
    ("seamN", lambda v, c: v == "0",
     "no read card is left un-folded and un-opened (body hidden, control still claiming 'Less')"),
    ("bsClicksToOpen", lambda v, c: v == "1", "ONE click opens a boot-seeded-read lead"),
    ("bsLabel", lambda v, c: v == "More", "...and its control says More before that click"),
    ("bsAria", lambda v, c: v == "false", "...and so does aria-expanded"),
]


# THE RAIL'S COLLAPSED HEIGHT, PINNED — the number that lets the census bite (2026-07-26). Measured
# with the index disclosure closed: scrollHeight 969px at 1440/1512 and 950px at 1300, composed of
# nameplate 247 + edition 38 + How-this-works 52 + review 100 + beats 462 + summary 64 + padding 24
# (that is the post-reorder order; the sum moved 968 -> 969 because the collapse above the button is
# its own 1.5em rather than the edition line's 1.4em).
# Two rules key on it, and the pinning is what makes the first one non-vacuous: "the rail may scroll
# only where the viewport is genuinely shorter than its collapsed furniture" is a tautology if the
# collapsed height is read off the same element (a censused container is overflowing BY DEFINITION),
# so the height has to come from outside the measurement.
# A CEILING, NOT THE MEASUREMENT: ~30px of headroom for the theme's root-size ladder and no more, so
# re-inflating the rail — prose added back outside the <details>, another block of furniture — fails
# the census wherever it is censused instead of quietly restoring the trap.
MX_RAIL_COLLAPSED_MAX = 1000

# THE SCROLL-CONTAINER WHITELIST, which is the whole of structure-cleanliness as an assertion: a
# page with ONE scroller plus the deliberate ones is clean, and anything else is a finding by
# definition rather than by taste. Each entry is (selector-substring, axis, min_width, max_width,
# condition-on-the-cell's-numbers-or-None, prose). A censused container matching none of these fails
# its cell.
#   - the rail is a scroll container only as a SAFETY VALVE, and only at >=1280 where it exists: its
#     `max-height`/`overflow-y` were introduced because a sticky box taller than the viewport pins at
#     the top with everything past the fold unreachable. Since the index folded (2026-07-26) it is no
#     longer the page's front door, so the entry is conditional — see MX_RAIL_COLLAPSED_MAX, and the
#     two direct rail assertions in _mx_struct_judge, which are what actually guard the fix.
#   - `.folio-filters` is a scroll container ONLY below 700px, where it is the fixed BOTTOM bar and
#     its `overflow-x:auto` lets a long chip row be swiped. The director's brief expected it below
#     1280; the CSS gives it `overflow:visible` from 700px up (line 533), so the whitelist follows
#     the CSS and the discrepancy is reported rather than encoded.
#   - the How-this-works modal scrolls its own body, but only while it is OPEN.
#   - `html` is the page scroller. It is expected and it is the ONLY unconditional vertical one.
MX_SCROLL_WHITELIST = [
    ("html", "y", 0, 99999, None, "the page itself scrolls — this is the one that should"),
    # MATCHED ON THE CLASS, NOT THE TAG: the rail is an `<aside>` and the first version of this
    # whitelist said `div.folio-rail`, so the one container that is here BY DESIGN was reported as
    # the finding at all three wide widths. A whitelist that misses its own entry manufactures
    # exactly the failure it exists to suppress.
    (".folio-rail", "y", 1280, 99999,
     lambda kv: int(kv.get("h") or 0) - 71 < MX_RAIL_COLLAPSED_MAX,
     "the rail's safety-valve scrollport — allowed ONLY where the viewport cannot hold its "
     "collapsed furniture (max-height is calc(100vh - 71px))"),
    (".folio-filters", "x", 0, 699, None,
     "the fixed bottom bar's swipeable chip row (<700px by design)"),
    ("hiwModal", "y", 0, 99999, lambda kv: kv.get("hiwModalOpen") == "1",
     "the How-this-works modal scrolls its own body while it is open"),
]


def _mx_struct_judge(cell, kv, conts):
    """Score a struct cell: the whitelist, the double-scrollbar check, and the visibility bands."""
    fails, w = [], cell["w"]
    for c in conts:
        ok = False
        for sel, axis, lo, hi, cond, _why in MX_SCROLL_WHITELIST:
            if sel in c["sel"] and c["axis"] == axis and lo <= w <= hi and (cond is None or cond(kv)):
                ok = True
                break
        if not ok:
            fails.append("unexpected %s scroller %s delta=%s ov=%s ob=%s pos=%s rect=%s"
                         % (c["axis"], c["sel"], c["delta"], c.get("ov"), c.get("ob"),
                            c.get("pos"), c.get("rect")))
    # THE RAIL, ASSERTED DIRECTLY AND NOT ONLY THROUGH THE WHITELIST (2026-07-26). The whitelist can
    # only ever say "this container is allowed here"; these two say what the fix actually was, and
    # each catches a regression the other misses.
    if w >= 1280 and "railOy" in kv:
        # 1. IT MAY NOT TRAP. `overscroll-behavior:contain` is what turned 1221px of clipped rail into
        #    the owner's "double scroll right at the top": the wheel ran the rail out and then refused
        #    to hand the remainder to the page. Height-independent, so asserted unconditionally.
        if kv.get("railOb") == "contain":
            fails.append("railOb=contain — the rail refuses to chain its overscroll to the page, "
                         "which is the trap the reader meets on arrival (delta=%s)"
                         % kv.get("railDy"))
        # 2. ITS COLLAPSED FURNITURE MAY NOT GROW. Exempt only where the disclosure is explicitly
        #    OPEN — then the rail is supposed to exceed its scrollport, because the reader asked it
        #    to. Gated on `!= "1"` rather than `== "0"` on purpose: the probe reports -1 when there is
        #    no `.rail-d` at all, and deleting the disclosure is exactly the regression that must not
        #    also delete the assertion (verified against the pre-fix layout, which reads -1/2010).
        if kv.get("railDetailsOpen") != "1" and int(kv.get("railScrollH") or 0) > MX_RAIL_COLLAPSED_MAX:
            fails.append("railScrollH=%s > %d with the index disclosure CLOSED — the rail's own "
                         "furniture has re-inflated past what folding the prose bought "
                         "(clientH=%s, hidden=%s)"
                         % (kv.get("railScrollH"), MX_RAIL_COLLAPSED_MAX,
                            kv.get("railClientH"), kv.get("railDy")))
        # 3. THE TWO ACTIONS STAY INSIDE THE SCROLLPORT — the acceptance criterion of the reorder
        #    ruling, and the one rule here that scores ORDER rather than size. Something is always
        #    below this rail's fold at a laptop height; what may be below it is the beat list's tail
        #    (count-sorted, so the least-used chips, and a cut list advertises that it continues),
        #    never the only path to the review and the explainer. Fails if the actions drift back below
        #    the beats, and equally if new furniture above them pushes them out.
        if kv.get("railActionsIn") is None:
            # A PROBE THAT DID NOT RUN CANNOT HAVE PASSED — this file's own doctrine, and the reason
            # the absence is a failure rather than a skip: `.get()` returning None would otherwise
            # quietly retire the acceptance criterion the moment a selector is renamed.
            fails.append("railActionsIn absent from the census marker — the rail-order acceptance "
                         "criterion did not run (renamed selector? probe edited?)")
        elif kv["railActionsIn"] != "1":
            fails.append("railActionsIn=0 — an action is below the rail's fold at a %spx viewport: "
                         "How-this-works ends at %s, the review link at %s, scrollport is %s "
                         "(beats end at %s). The actions come FIRST; only the beat tail may be cut."
                         % (kv.get("h"), kv.get("railHiwBottom"), kv.get("railReviewBottom"),
                            kv.get("railClientH"), kv.get("railBeatsBottom")))
    if kv.get("doubleScroll") != "0":
        fails.append("doubleScroll=%s — html and body are BOTH scrollable (two vertical bars): "
                     "docDelta=%s bodyDelta=%s docOv=%s bodyOv=%s"
                     % (kv.get("doubleScroll"), kv.get("docDelta"), kv.get("bodyDelta"),
                        kv.get("docOv"), kv.get("bodyOv")))
    # exactly ONE beat-chip set on screen per width — the duplicated set must not be visible twice
    bar, rail = kv.get("barChipsVis"), kv.get("railChipsVis")
    if bar is not None and rail is not None:
        if bar == rail:
            fails.append("barChipsVis=%s railChipsVis=%s — exactly one beat-chip set may be "
                         "visible at a given width (bar=%s rail=%s)"
                         % (bar, rail, kv.get("barChips"), kv.get("railChips")))
        want_rail = "1" if w >= 1280 else "0"
        if rail != want_rail:
            fails.append("railChipsVis=%s at %dpx — the rail carries the chips from 1280 up"
                         % (rail, w))
    # the documented visibility bands for the page header
    if w >= 1280:
        for k in ("h1", "tagline", "hiw"):
            if kv.get(k) not in ("none", "sronly", "hidden"):
                fails.append("%s=%s at %dpx — from 1280 up the rail carries the nameplate, so this "
                             "should be hidden or screen-reader-only" % (k, kv.get(k), w))
    else:
        for k in ("h1", "tagline", "hiw"):
            v = kv.get(k)
            if v in ("absent", "none"):
                fails.append("%s=%s at %dpx — below 1280 this is the page's only masthead"
                             % (k, v, w))
    return fails


def _mx_cells():
    """Every cell this pass runs, in the order it runs them.

    Coverage is the spec's, not the full ~500-cell product: (W x R) at rest, (F x R) at 1440,
    E1-E4 at the three packed widths, the empty state at both ends of the width range, and the two
    cells the implementer's report added.
    """
    W_ALL = [1440, 1280, 1024, 800, 700, 390]
    cells = []

    def add(w, tokens, shot=False, expect=None, note="", mindrop=None, h=None, idsfx="",
            shoth=None):
        # `idsfx` exists so the SAME tokens can be run at two window heights as two distinct cells
        # (the census at a laptop height and at the owner's), since the id is otherwise derived from
        # width + tokens alone. `shoth` is the window height for the SCREENSHOT only — see the note on
        # the owner-height cell below for why the two heights differ.
        cid = "%d-%s%s" % (w, tokens.replace(",", "-"), idsfx)
        cells.append({"id": cid, "w": w, "tokens": tokens, "shot": shot,
                      "expect": expect or {}, "note": note, "mindrop": mindrop, "h": h,
                      "shoth": shoth})

    # 0. THE SCROLL / STRUCTURE CENSUS, first and at a REALISTIC VIEWPORT HEIGHT. 860px is a laptop
    #    window; at the 1800-5200px heights the rest of this matrix uses, `max-height:calc(100vh-71px)`
    #    makes the rail taller than its own content and the container under suspicion cannot overflow
    #    at all. 1512 and 1300 are here because they are the widths either side of the rail's 1280
    #    breakpoint that the owner actually uses.
    # +87 BECAUSE THE WINDOW IS NOT THE VIEWPORT: `--window-size=W,860` yields innerHeight 773 in
    # headless-new, measured constant across all six widths. The brief asked for a ~860px viewport,
    # so the window asks for 947 and the probe reports the innerHeight it actually got.
    for w in (1512, 1440, 1300, 1024, 800, 390):
        add(w, "R0,F0,E0,struct", h=947, shot=(w == 1440),
            note="scroll-container census + structure cleanliness at a 860px viewport")
    # 0b. THE OWNER'S OWN WINDOW HEIGHT, as its own cell (2026-07-26 reorder ruling). The built page
    #     measured an 804px viewport on his machine, which is 56px shorter than the laptop height above
    #     — enough to change WHICH rail furniture is below the fold, i.e. exactly what the ruling is
    #     about. So the acceptance criterion is scored at his height and not only near it.
    #     +87 AGAIN for the measurement (`--window-size=W,891` yields innerHeight 804 under
    #     --dump-dom), but the SHOT is taken at 804: `--screenshot` does NOT lose those 87px, so a
    #     picture framed at 891 would show a ~820px scrollport and photograph a rail state the owner
    #     never sees. Two heights, one for the numbers and one for the artifact, both 804 in effect.
    add(1440, "R0,F0,E0,struct", h=891, shoth=804, shot=True, idsfx="-owner804",
        note="the same census at the owner's measured 804px viewport — the reorder's acceptance cell")

    # 1. every (W x R) resting — the width axis crossed with the read axis. The all-read board is
    #    the only read state whose HEIGHT drop is a meaningful assertion (see `spineOk`), and only
    #    where the board is packed: below 700px it is one column and every card is its own row.
    for w in W_ALL:
        for r in ("R0", "R1", "R2"):
            add(w, "%s,F0,E0" % r,
                shot=(w, r) in {(1440, "R0"), (1440, "R1"), (1440, "R2"), (1024, "R1"),
                                (800, "R1"), (700, "R0"), (390, "R0"), (390, "R1")},
                mindrop=25 if (r == "R2" and w >= 700) else None)
    # 2. every (F x R) at 1440
    for r in ("R0", "R1", "R2"):
        for f in ("F1", "F2", "F3", "F4", "F5"):
            add(1440, "%s,%s,E0" % (r, f),
                shot=(r, f) in {("R1", "F1"), ("R0", "F3"), ("R1", "F2"), ("R0", "F5")})
    # 3. E1-E4 at the packed widths
    for w in (1440, 1280, 1024):
        for e in ("E1", "E2", "E3", "E4"):
            add(w, "R0,F0,%s" % e,
                shot=(w, e) in {(1440, "E1"), (1440, "E2"), (1024, "E1")})
    # 4. the empty state at both ends of the width range, and expansion on the phone — where the
    #    board is one unpacked column, so More is a pure height change with no packer involved
    add(390, "R0,F5,E0", shot=True)
    add(390, "R0,F0,E1", shot=True)
    # 5. the round trips, stated as their own cells rather than implied: every F cell round-trips
    #    its filter already, so what is left is read-then-unread — which is what `R1c` measures,
    #    since a clicked read state is un-clicked in the restore step.
    add(1440, "R1c,F0,E0", note="read-then-unread round trip; also the boot-seeded vs clicked A/B")
    add(1440, "R2c,F0,E0", note="all-read by click rather than by seed")
    # 6. THE ADDED CELLS (implementer report 2026-07-26)
    add(1440, "R2s,F1,E0", shot=True,
        expect={"uct": "0", "vis": "2", "visEd": "2", "visStory": "0", "emptyHidden": "1"},
        note="all 80 stories read, both editorials unread, Unread filter — the owner's "
             "reported-bug surface, pinned as exact numbers")
    add(1440, "R0,F0,E0,bootlead", note="the read / boot-open lead seam, reached by CLICKING")
    add(1440, "R0,F0,E0,bslead", shot=True,
        note="the same seam reached by BOOTING with the lead already read — the path foldForRead "
             "does not run on")
    add(1440, "R0,F0,E0,roam",
        expect={"roamGets": "1", "roamPainted": "1"},
        note="and the same seam reached by a ROAM landing after boot (mergeRemote -> paintRead), "
             "with nothing seeded read locally. The two expectations are the cell's PREMISE — that "
             "the roam really landed and really painted the lead — so a stub that silently stopped "
             "working could not read as a pass")
    return cells


def _mx_row(text):
    """Parse an MX marker into a dict, the way _run_check parses the others."""
    kv = dict(re.findall(r"(\w+)=([^\s\]]+)", text))
    kv["_dbVis"] = kv.get("dbVis", "0")
    return kv


def _mx_judge(cell, kv):
    """Score one cell. Returns a list of failure strings — empty means the cell passed."""
    fails = []
    for key, pred, why in MX_CHECKS:
        if key not in kv:
            continue          # the state this row describes does not exist in this cell
        try:
            ok = pred(kv[key], kv)
        except (ValueError, TypeError):
            ok = False
        if not ok:
            fails.append("%s=%s — expected: %s" % (key, kv[key], why))
    for key, want in cell["expect"].items():
        got = kv.get(key)
        if got != want:
            fails.append("%s=%s — this cell pins it at %s" % (key, got, want))
    return fails


def _mx_run(artifact, cells, shots_dir=None, log=None, budget=16000, scheme="dark"):
    """Drive every cell, print a row each, and return (rows, failures).

    Progress is appended to `log` the instant each cell finishes — a ~50-cell run is ten minutes
    long and a batch that reports only at the end is a batch nobody can watch.
    """
    rows, failed = [], []
    base = {}          # width -> the R0 resting grid height, for the read-state height drops
    for n, cell in enumerate(cells, 1):
        h = "#mx:" + cell["tokens"]
        height = cell.get("h") or (2600 if cell["w"] >= MX_FLOOR else 1800)
        url, win = _mx_url(artifact, h, cell["w"], height)
        out = _mx_chrome(url, win, height, budget=budget, scheme=scheme)
        if "struct" in cell["tokens"]:
            rows.append(_mx_struct_row(cell, out, n, len(cells), log))
            if rows[-1]["fails"]:
                failed.append(cell["id"])
            if shots_dir and cell["shot"]:
                # A STRUCT CELL IS THE ONLY SHOT TAKEN AT A REAL WINDOW HEIGHT, and that is the point
                # of photographing it: every other shot here is 2600-6200px tall, so the rail's
                # `max-height:calc(100vh - 71px)` is larger than the rail's own content and no
                # screenshot in this set has ever shown the rail clipped at its scrollport.
                png = _mx_shot(artifact, cell, shots_dir, budget, scheme=scheme)
                rows[-1]["png"] = png
                print("        shot %s" % png, flush=True)
                if log:
                    with open(log, "a") as fh:
                        fh.write("        shot %s\n" % png)
            continue
        m = re.search(r'<div id="mxcheck"[^>]*>(.*?)</div>', out, re.S)
        if not m:
            kv, text = {}, "<MARKER MISSING>"
            fails = ["the probe never emitted — a cell that did not run cannot have passed"]
        else:
            text = re.sub(r"\s+", " ", m.group(1)).strip()
            kv = _mx_row(text)
            fails = _mx_judge(cell, kv)
            if cell["w"] < MX_FLOOR and kv.get("frameW") != str(cell["w"]):
                fails.append("frameW=%s — the iframe did not render at %d px"
                             % (kv.get("frameW"), cell["w"]))
        # THE HEIGHT DROP IS A CROSS-CELL FACT, so the driver owns it: a cell seeded read at boot
        # reports its OWN resting height in `r0H` and cannot know the unread board's. The R0 cell
        # for each width runs first (see _mx_cells) and its height is the baseline.
        drop = None
        if cell["tokens"].startswith("R0,F0,E0") and "H" in kv:
            base[cell["w"]] = int(kv["H"])
        if cell["w"] in base and "H" in kv and base[cell["w"]]:
            drop = round(100.0 * (base[cell["w"]] - int(kv["H"])) / base[cell["w"]])
            kv["dropPct"] = str(drop)
        if cell.get("mindrop") is not None:
            if drop is None:
                fails.append("dropPct: no R0 baseline at %dpx to compare against" % cell["w"])
            elif drop < cell["mindrop"]:
                fails.append("dropPct=%d — expected: an all-read board is at least %d%% shorter"
                             % (drop, cell["mindrop"]))
        rows.append({"cell": cell, "kv": kv, "text": text, "fails": fails})
        if fails:
            failed.append(cell["id"])
        line = "%3d/%d %-26s %s  %s" % (n, len(cells), cell["id"],
                                        "FAIL" if fails else "ok  ", text)
        print(line, flush=True)
        for f in fails:
            print("        FAIL %s" % f, flush=True)
        if log:
            with open(log, "a") as fh:
                fh.write(line + "\n")
                for f in fails:
                    fh.write("        FAIL %s\n" % f)
        if shots_dir and cell["shot"]:
            png = _mx_shot(artifact, cell, shots_dir, budget, scheme=scheme)
            rows[-1]["png"] = png
            print("        shot %s" % png, flush=True)
            if log:
                with open(log, "a") as fh:
                    fh.write("        shot %s\n" % png)
    return rows, failed


def _mx_shot(artifact, cell, shots_dir, budget=16000, scheme="dark"):
    """One curated screenshot, in the `keep` variant of the cell — which abandons the state instead
    of restoring it, because a restored state photographs as the resting page.

    Below the 500px floor the shot comes out of the iframe wrapper and is 500px wide with the page
    on the left, so it is CROPPED to the real width rather than reported as if it were 390.
    """
    import subprocess
    os.makedirs(shots_dir, exist_ok=True)
    png = os.path.join(shots_dir, cell["id"] + ".png")
    # `shoth` overrides the window height for the picture. It exists because `--screenshot` and
    # `--dump-dom` do not agree about the viewport at the same `--window-size` (the +87 note above), so
    # a cell whose numbers must land at a given viewport asks for a different window than its shot.
    height = cell.get("shoth") or cell.get("h") or (2600 if cell["w"] >= MX_FLOOR else 1800)
    # AN EXPANSION CELL NEEDS A TALLER WINDOW, not a scroll: its module is the first foldable one
    # past rank 8, which at 1440 begins around y=2000 and grows ~900px when it opens, so a 2600px
    # frame photographs the resting top of the page and misses the very thing the cell exists to
    # show. Scrolling instead was tried and produced a displaced, mostly-empty PNG (see the probe).
    # Measured `eTop` (the probe reports it): 2057 at 1440, 2137 at 1280, 2278 at 1024 — and 4090 at
    # 390, where one unpacked column puts rank 8 twice as far down the page.
    if re.search(r"E[1-4]", cell["tokens"]):
        height = 5200 if cell["w"] >= MX_FLOOR else 6200
    url, win = _mx_url(artifact, "#mx:" + cell["tokens"] + ",keep", cell["w"], height)
    _mx_chrome(url, win, height, budget=budget, shot=png, scheme=scheme)
    if cell["w"] < MX_FLOOR and os.path.exists(png):
        # CROPPED FROM THE TOP-LEFT, EXPLICITLY. `sips -c H W` crops from the CENTRE, so the first
        # version of this took the middle 390px of the 500px frame and produced four phone shots
        # missing 55px off each side — the rail's edge gone on the left, white paper on the right,
        # and the headline clipped mid-word. It looked like a layout defect in the contact sheet and
        # was the instrument. `magick -crop WxH+0+0` says where it cuts; `sips --cropOffset 0 0` is
        # the fallback for a machine without ImageMagick.
        box = "%dx%d+0+0" % (cell["w"], height)
        if subprocess.run(["magick", png, "-crop", box, "+repage", png],
                          capture_output=True, text=True).returncode != 0:
            subprocess.run(["sips", "--cropOffset", "0", "0",
                            "-c", str(height), str(cell["w"]), png],
                           capture_output=True, text=True)
    return png


def _mx_struct_row(cell, out, n, total, log=None):
    """Parse and score one scroll/structure census cell, and print it as its own block.

    The census is a LIST, not a set of scalars, so it does not fit the one-line `MX` shape the other
    cells share — each censused container prints on its own line under the cell, which is also how a
    reader wants to read it.
    """
    m = re.search(r'<div id="mxstruct"[^>]*>(.*?)</div>', out, re.S)
    if not m:
        row = {"cell": cell, "kv": {}, "text": "<MXS MARKER MISSING>", "conts": [],
               "fails": ["the census never emitted — a probe that did not run cannot have passed"]}
    else:
        text = re.sub(r"\s+", " ", m.group(1)).strip()
        head, _, tail = text.partition(" |C ")
        kv = dict(re.findall(r"(\w+)=(\S+)", head))
        conts = []
        for chunk in ((" |C " + tail) if tail else "").split(" |C ")[1:]:
            c = dict(re.findall(r"(\w+)=(\S+)", chunk))
            c.setdefault("sel", "?")
            conts.append(c)
        row = {"cell": cell, "kv": kv, "text": text, "conts": conts,
               "fails": _mx_struct_judge(cell, kv, conts)}
    lines = ["%3d/%d %-26s %s  SCROLL/STRUCT %dx%s" % (
        n, total, cell["id"], "FAIL" if row["fails"] else "ok  ", cell["w"],
        row["kv"].get("h", "?"))]
    k = row["kv"]
    lines.append("        doc: docDelta=%s bodyDelta=%s docOv=%s bodyOv=%s doubleScroll=%s nCont=%s"
                 % (k.get("docDelta"), k.get("bodyDelta"), k.get("docOv"), k.get("bodyOv"),
                    k.get("doubleScroll"), k.get("nCont")))
    lines.append("        filters: ov=%s/%s pos=%s top=%s bottom=%s dx=%s dy=%s rect=%s"
                 % (k.get("filOx"), k.get("filOy"), k.get("filPos"), k.get("filTop"),
                    k.get("filBottom"), k.get("filDx"), k.get("filDy"), k.get("filRect")))
    lines.append("        rail: %s"
                 % ("ABSENT" if k.get("railPresent") == "0" else
                    "ov=%s ob=%s pos=%s top=%s maxH=%s client=%s scroll=%s dy=%s traps=%s "
                    "rect=%s | scrolled-4000px: dy=%s rect=%s"
                    % (k.get("railOy"), k.get("railOb"), k.get("railPos"), k.get("railTop"),
                       k.get("railMaxH"), k.get("railClientH"), k.get("railScrollH"),
                       k.get("railDy"), k.get("railTraps"), k.get("railRect"),
                       k.get("railDyScrolled"), k.get("railRectScrolled"))))
    # THE REORDER'S ACCEPTANCE NUMBERS, PRINTED. The judge scores `railActionsIn`, and a scored number
    # nobody can read in the log is how a reviewer ends up taking "ok" on trust.
    if k.get("railActionsIn") is not None:
        lines.append("        rail order: HIW ends %s, review ends %s, beats end %s, scrollport %s "
                     "-> actions inside: %s (details open=%s)"
                     % (k.get("railHiwBottom"), k.get("railReviewBottom"),
                        k.get("railBeatsBottom"), k.get("railClientH"), k.get("railActionsIn"),
                        k.get("railDetailsOpen")))
    lines.append("        header: h1=%s tagline=%s hiw=%s | chips bar=%s(vis %s) rail=%s(vis %s)"
                 % (k.get("h1"), k.get("tagline"), k.get("hiw"), k.get("barChips"),
                    k.get("barChipsVis"), k.get("railChips"), k.get("railChipsVis")))
    lines.append("        theme chrome in this artifact: masthead=%s greedy-nav=%s skip-links=%s "
                 "(all from the minimal-mistakes DEFAULT layout, not home.html -> absence here is "
                 "expected, verify on the built page)"
                 % (k.get("has_masthead"), k.get("has_greedy_nav"), k.get("has_skip_links")))
    for c in row["conts"]:
        lines.append("        [C] %s axis=%s delta=%s ov=%s ob=%s pos=%s top=%s maxH=%s rect=%s"
                     % (c.get("sel"), c.get("axis"), c.get("delta"), c.get("ov"), c.get("ob"),
                        c.get("pos"), c.get("top"), c.get("maxH"), c.get("rect")))
    for f in row["fails"]:
        lines.append("        FAIL %s" % f)
    for ln in lines:
        print(ln, flush=True)
    if log:
        with open(log, "a") as fh:
            fh.write("\n".join(lines) + "\n")
    return row


def _mx_rows_from_log(log):
    """Reconstruct a run's rows from its progress log, so the contact sheet can be rebuilt without
    re-driving Chrome 70-odd times.

    The log already holds everything the sheet needs — cell id, verdict, the full MX line, each
    failure and each shot path — and a re-render that changes only how the PNGs are cut has no
    business re-measuring the page. Written after a centre-crop bug meant four phone tiles had to be
    re-cut: the alternative was a third full 14-minute run to redraw one HTML file.
    """
    rows, cur = [], None
    for ln in open(log):
        m = re.match(r"\s*\d+/\d+ (\S+)\s+(ok|FAIL)\s+(MX .*)", ln)
        if m:
            cur = {"cell": {"id": m.group(1), "expect": {}, "note": ""},
                   "kv": _mx_row(m.group(3).strip()), "text": m.group(3).strip(), "fails": []}
            rows.append(cur)
            continue
        # A SCROLL/STRUCT CELL PRINTS AS A BLOCK, not as one `MX` line, so it needs its own header
        # pattern here — without it the census cells were silently dropped from the contact sheet
        # while the sheet still reported a cell count, which is the quiet kind of wrong.
        m = re.match(r"\s*\d+/\d+ (\S+)\s+(ok|FAIL)\s+(SCROLL/STRUCT .*)", ln)
        if m:
            cur = {"cell": {"id": m.group(1), "expect": {}, "note": ""},
                   "kv": {"struct": "1"}, "text": m.group(3).strip(), "fails": []}
            rows.append(cur)
            continue
        if cur is None:
            continue
        m = re.match(r"\s+(?:doc|rail): (.*)", ln)
        if m and cur["kv"].get("struct"):
            cur["kv"].update(dict(re.findall(r"(\w+)=(\S+)", m.group(1))))
            continue
        m = re.match(r"\s+FAIL (.*)", ln)
        if m:
            cur["fails"].append(m.group(1).strip())
            continue
        m = re.match(r"\s+shot (\S+)", ln)
        if m:
            cur["png"] = m.group(1)
    return rows


def _mx_sheet(rows, path, shots_dir):
    """The contact sheet: one page, every shot embedded as a thumbnail, each captioned with its
    cell id, verdict and the numbers that matter. Full-size PNGs sit beside it on disk.
    """
    import base64
    import subprocess
    tiles = []
    for r in rows:
        png = r.get("png")
        if not png or not os.path.exists(png):
            continue
        thumb = png.replace(".png", "-thumb.png")
        subprocess.run(["sips", "-Z", "560", png, "--out", thumb], capture_output=True, text=True)
        src = thumb if os.path.exists(thumb) else png
        with open(src, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()
        kv = r["kv"]
        keys = [k for k in ("vis", "visStory", "visEd", "uct", "readN", "openN",
                            "H", "upInv", "holes", "gridH", "emptyHidden",
                            "nCont", "doubleScroll", "dy", "traps", "eTop")
                if k in kv]
        nums = " ".join("%s=%s" % (k, kv[k]) for k in keys)
        tiles.append(
            '<figure class="%s"><a href="%s"><img src="data:image/png;base64,%s" alt="%s"></a>'
            '<figcaption><b>%s</b> <span class="v">%s</span><br><code>%s</code>%s</figcaption>'
            '</figure>' % ("bad" if r["fails"] else "good", "file://" + os.path.abspath(png), b64,
                           html.escape(r["cell"]["id"]), html.escape(r["cell"]["id"]),
                           "FAILED" if r["fails"] else "pass", html.escape(nums),
                           "".join("<br><em>%s</em>" % html.escape(f) for f in r["fails"])))
    doc = """<!doctype html><meta charset="utf-8"><title>front page — state matrix contact sheet</title>
<style>
 body{margin:0;padding:26px;background:#f6f5f2;color:#141414;
      font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
 h1{font-size:20px;margin:0 0 4px} p.sub{margin:0 0 22px;color:#555;max-width:64em}
 .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px}
 figure{margin:0;background:#fff;border:1px solid #ddd;padding:8px}
 figure.bad{border-color:#c8102e;box-shadow:0 0 0 2px rgba(200,16,46,.18)}
 img{width:100%%;height:auto;display:block;border:1px solid #eee}
 figcaption{font-size:12px;line-height:1.45;margin-top:7px;word-break:break-word}
 code{font-size:11px;color:#444} .v{color:#137a3a;font-weight:600}
 figure.bad .v{color:#c8102e} em{color:#c8102e;font-style:normal;font-size:11px}
 @media (prefers-color-scheme:dark){
   body{background:#151515;color:#eee} figure{background:#1e1e1e;border-color:#333}
   p.sub{color:#aaa} code{color:#bbb} img{border-color:#2a2a2a}}
</style>
<h1>Front page — state matrix (%d shots)</h1>
<p class="sub">Read state &times; filter &times; width &times; expansion, from
<code>tools/home_harness.py --matrix</code>. Every shot is the cell's own state, abandoned rather
than restored. Click a tile for the full-size PNG (in <code>%s</code>). Cells outlined in red
failed an assertion; the failure is printed under the caption.</p>
<div class="grid">%s</div>
""" % (len(tiles), html.escape(shots_dir), "\n".join(tiles))
    with open(path, "w") as fh:
        fh.write(doc)
    return path


def _build_page(feed, matrix=False, refresh_theme=False):
    """The artifact, built from the LAYOUT ITSELF — styles, scripts and markup extracted, never
    mirrored. `matrix` swaps the nine-probe bundle for the single state-matrix probe (see
    MATRIX_CHECK's note on why they cannot share a page).

    Lifted out of main() on 2026-07-26 so ONE run can build both artifacts: `--check` now also
    drives the scroll-container census, which lives on the matrix page because that is where the
    census probe is (matrix report §9 item 1). Two builds of the same source, not two sources.
    """
    src = open(os.path.join(ROOT, "_layouts", "home.html")).read()
    styles = "\n".join(re.findall(r"<style>.*?</style>", src, re.S))
    _css_sanity("_layouts/home.html", styles)
    # ALL script blocks, in document order — re.search took only the FIRST block, which
    # since 2026-07-11 was the modal script, so the 600+-line folio engine went untested.
    script = "\n".join(re.findall(r"<script>.*?</script>", src, re.S))

    chips = "".join(
        '<button class="ff-chip" type="button" data-topic="%s" aria-pressed="false" style="--tc:%s">'
        '<span class="ff-dot"></span>%s <span class="ff-ct">%d</span></button>'
        % (t["key"], t["color"], t["label"], t["count"]) for t in feed["topics"])

    # THE `.harness-doc` WRAPPER IS NOT DECORATION — WITHOUT IT THIS HARNESS INVENTS A COLLAPSE.
    # minimal-mistakes sets `body{display:flex; flex-direction:column}`, so every child of <body>
    # is a flex item and the cross axis is HORIZONTAL. `.wrap` carries `margin:0 auto`, i.e. two
    # auto cross-axis margins, and per Flexbox 9.4 an item with an auto cross margin is NOT
    # stretched — its width becomes fit-content instead of the container's 1440.
    # That was survivable only by accident: fit-content is min(max-content, available), and the
    # bar's ~13 wrapping chips gave `.folio-filters` a max-content of a full single line, which
    # held `.wrap` open at the viewport width. The moment the >=1280 rule hides those chips, the
    # widest remaining max-content is the board's — and `container-type:inline-size` on `.fcard`
    # (contain:inline-size) zeroes each module's intrinsic contribution, so the 12-track sheet
    # collapses to ~103px. Measured, chips hidden and no other change: wrap 1440 -> 327,
    # board 1396 -> 283, grid 1216 -> 103. Every geometry invariant still PASSED through it
    # (inversions 0, rank2 >= tail, scrollW == innerW) — only the widths and the screenshot showed
    # it, which is how it cost a revert on 2026-07-25 before the cause was known.
    # Production never had this: `.initial-content` is the flex item there and the theme gives it
    # `flex:1 0 auto` with NO auto cross margins, so it stretches to a definite width and `#main`
    # (max-width + margin:auto) does ordinary block layout inside it. An unstyled block here
    # reproduces exactly that chain, so `.wrap` is sized by a definite parent rather than by its
    # own contents. `width:100%` on `.wrap` fixes the symptom identically and says nothing about
    # why, so it is not what ships.
    # The page header and the modal, extracted rather than mirrored. `<body class="layout--home">`
    # is REQUIRED, not cosmetic: every header rule is scoped `.layout--home .page__title` /
    # `.layout--home .home-tagline`, so without the class the harness would render the header and
    # silently fail to apply the very rules under review. `<h1 class="page__title">` stands in for
    # the archive layout's own — it is the element those rules target and the page's only h1.
    header = ('<h1 class="page__title">News</h1>'
              + _extract_block(r'<p class="home-tagline">.*?</button>', "page header"))
    modal = _hiw_stub()
    # The propose disclosure, extracted like the header — it was the last piece of the front page
    # this harness did not render, so the page foot could not be reviewed here at all. It is
    # spliced INSIDE `#main` rather than after it, and that is the same trap the `.harness-doc`
    # note above describes: `.propose` carries `margin:2.6em auto 2.4em`, i.e. two auto cross-axis
    # margins, so as a direct child of the flex `<body>` it would size to fit-content and photograph
    # narrow — with no metric complaining, because nothing measures it.
    propose = _extract_block(r'<section class="propose">.*?</section>', "propose disclosure")
    # The empty state, EXTRACTED — the mirrored copy that used to live in the template below had
    # already drifted (it carried neither `role="status"` nor `aria-live`), and the div's POSITION
    # is now the thing under test: it is the grid's last child, so the message opens the sheet
    # instead of landing in the board grid's second row under a rail-height void. Spliced inside
    # `#folioGrid` for that reason; putting it back outside would silently reproduce the bug this
    # harness now measures.
    empty_state = _extract_block(r'<div class="folio-empty".*?</div>', "empty state")

    page = """<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>home harness</title>%s%s
<body class="layout--home">
<div class="harness-doc"><div class="wrap" id="main">%s
<div class="folio-filters" id="folioFilters"><span class="ff-lbl">Beat</span>
<button class="ff-chip ff-all" type="button" data-topic="" aria-pressed="true">All <span class="ff-ct">%d</span></button>
%s<span class="ff-read" role="group" aria-label="Read state"><button class="ff-rbtn" type="button" data-rs="" aria-pressed="true">All</button><button class="ff-rbtn" type="button" data-rs="unread" aria-pressed="false">Unread <span class="ff-ct ff-uct"></span></button><button class="ff-rbtn" type="button" data-rs="read" aria-pressed="false">Read</button></span>%s%s</div>
<div class="folio-board">
<span class="ff-crop tl"></span><span class="ff-crop tr"></span><span class="ff-crop bl"></span><span class="ff-crop br"></span>
%s<div class="folio-grid" id="folioGrid">%s%s</div>
</div>%s</div></div>
%s
%s%s%s%s""" % (_theme_css(refresh_theme) + TOKENS, styles, header, feed["count"], chips,
               SYNC_UI, LEGEND_UI,
               _extract_rail(feed),
               # ONE LOOP OVER feed.board, branching on `kind` — exactly what the layout does.
               "".join(ed_card(it) if it["kind"] == "editorial" else card(it)
                       for it in _require_board(feed)),
               empty_state,
               propose,
               modal, PRE_SYNC + (MATRIX_PRE if matrix else ""), script, VOID_METRICS,
               # THE MATRIX PAGE CARRIES ONE PROBE, and that is the point: the nine probes below
               # each measure the FULL board and restore it, so they cannot coexist with a cell that
               # has to still be filtered, still be read and still be open at measurement time.
               MATRIX_CHECK if matrix else
               (GEOM_CHECK + DAY_CHECK + FILTER_CHECK + FOLD_CHECK + BSREAD_CHECK + SYNC_CHECK
                + LEADREAD_CHECK + EMPTY_CHECK + READ_CHECK + SHOT_CHECK))
    return page


def _assert_reworked(page):
    """PROVE THE ARTIFACT EMBEDS THE REWORKED CODE BEFORE TRUSTING A SINGLE NUMBER OFF IT.

    Three green-while-broken pages in this repo's history all came from an instrument that did not
    contain the code under test (see `verify the test tool first`). `data-daybreak` and `foldForRead`
    exist only in the 2026-07-26 rework; `paintReadState` and `rail-d` only in the fix to it, so a
    harness driven against an older layout cannot report on either one.
    """
    for token, what in (("data-daybreak", "the daybreak attribute"),
                        ("paintReadState", "the one read painter all three paths call"),
                        ("rail-d", "the rail's index disclosure"),
                        ("foldForRead", "the read/boot-open normalization"),
                        ("packRowSpans", "the row-span pack engine"),
                        ("fcard__eddisc", "the AI disclosure")):
        if token not in page:
            raise SystemExit("home_harness: the artifact does not contain %r (%s) — "
                             "the harness is not testing the reworked page" % (token, what))


def _run_census(feed, out_path):
    """The scroll-container census, scored inside the STANDING oracle (matrix report §9 item 1).

    Structure cleanliness used to be scored only under `--matrix`, which is how a 1221px scroll trap
    occupying the left 180px of the first screen lived behind a green `--check` at six widths: the
    census needs a REALISTIC WINDOW HEIGHT (947, i.e. a 860px viewport) and every `--check` render is
    2800px tall, where `max-height:calc(100vh - 71px)` exceeds the rail's own content and the suspect
    container is not a scroll container at all.

    It reuses the matrix census cells verbatim rather than re-keying them to `--widths`: 1512 and 1300
    bracket the rail's 1280 breakpoint and are the widths the owner actually uses, which is the point
    of those two cells. No screenshots here — that is the matrix run's job.
    """
    page = _build_page(feed, matrix=True)
    _assert_reworked(page)
    with open(out_path, "w") as fh:
        fh.write(page)
    cells = [c for c in _mx_cells() if "struct" in c["tokens"]]
    print("census: %d cell(s) at a 860px viewport (%s)" % (len(cells), out_path), flush=True)
    rows, failed = _mx_run(os.path.abspath(out_path), [dict(c, shot=False) for c in cells])
    return sum(len(r["fails"]) for r in rows), failed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/home-harness.html")
    ap.add_argument("--refresh-theme", action="store_true",
                    help="re-pull the compiled minimal-mistakes CSS into %s" % THEME_CACHE)
    ap.add_argument("--check", action="store_true",
                    help="render in headless Chrome, parse every probe marker, and exit non-zero "
                         "on any failed assertion (see CHECKS)")
    ap.add_argument("--widths", default="1440",
                    help="--check only: comma-separated viewport widths")
    ap.add_argument("--hash", default="",
                    help="--check only: drive ONLY this hash mode, at every width ('#synced', "
                         "'#bsread', '#bootempty'). Omit it and the sweep drives the base mode at "
                         "every width plus #bsread, #synced and the scroll census once each")
    ap.add_argument("--matrix", action="store_true",
                    help="drive the state matrix: read state x filter x width x expansion, one "
                         "Chrome run per cell, exits non-zero on any violated assertion")
    ap.add_argument("--cells", default="",
                    help="--matrix only: run only the cells whose id matches this regex")
    ap.add_argument("--shots", default="",
                    help="--matrix only: write the curated screenshots to this directory")
    ap.add_argument("--sheet", default="",
                    help="--matrix only: write the one-page contact sheet here (implies --shots)")
    ap.add_argument("--log", default="",
                    help="--matrix only: append per-cell progress here as each cell finishes")
    ap.add_argument("--sheet-from", default="",
                    help="--matrix only: rebuild --sheet from a previous run's --log instead of "
                         "re-driving Chrome (see _mx_rows_from_log)")
    ap.add_argument("--scheme", default="dark", choices=sorted(MX_SCHEMES),
                    help="--matrix only: pin prefers-color-scheme rather than inheriting the "
                         "host's appearance (see MX_SCHEMES)")
    args = ap.parse_args()
    if args.matrix and args.out == "/tmp/home-harness.html":
        # A SEPARATE ARTIFACT, so a matrix run never clobbers the file another agent is driving —
        # and because the matrix page carries a different probe bundle entirely.
        args.out = "/tmp/home-matrix.html"

    feed = json.load(open(os.path.join(ROOT, "_data", "homefeed.json")))
    page = _build_page(feed, matrix=args.matrix,
                       refresh_theme=args.refresh_theme)

    with open(args.out, "w") as fh:
        fh.write(page)
    print("wrote %s (%d bytes, %d stories)" % (args.out, len(page), feed["count"]))

    if args.matrix:
        _assert_reworked(page)
        if args.sheet_from:
            if not args.sheet:
                raise SystemExit("home_harness --matrix --sheet-from: needs --sheet too")
            rows = _mx_rows_from_log(args.sheet_from)
            shots = args.shots or os.path.dirname(args.sheet)
            print("sheet %s (rebuilt from %s, %d cell(s), %d shot(s))"
                  % (_mx_sheet(rows, args.sheet, shots), args.sheet_from, len(rows),
                     sum(1 for r in rows if r.get("png"))))
            return
        cells = _mx_cells()
        if args.cells:
            rx = re.compile(args.cells)
            cells = [c for c in cells if rx.search(c["id"])]
        shots = args.shots or (os.path.dirname(args.sheet) if args.sheet else "")
        if args.log:
            open(args.log, "w").close()
        print("matrix: %d cell(s)%s" % (len(cells), (", shots -> " + shots) if shots else ""),
              flush=True)
        rows, failed = _mx_run(os.path.abspath(args.out), cells, shots_dir=shots or None,
                               log=args.log or None, scheme=args.scheme)
        if args.sheet:
            print("sheet %s" % _mx_sheet(rows, args.sheet, shots), flush=True)
        print("\nmatrix: %d/%d cells passed" % (len(rows) - len(failed), len(rows)))
        if failed:
            print("FAILED cells: %s" % ", ".join(failed))
            raise SystemExit("home_harness --matrix: %d cell(s) failed" % len(failed))
        return

    if not args.check:
        return
    bad = 0
    widths = [int(x) for x in args.widths.split(",") if x.strip()]

    def drive(w, hash):
        failures, lines = _run_check(os.path.abspath(args.out), w, hash=hash)
        print("--- %dpx%s" % (w, (" " + hash) if hash else ""))
        for ln in lines:
            print(ln)
        for f in failures:
            print("  FAIL %s" % f)
        print("  %s at %dpx%s (%d assertion(s) failed)"
              % ("PASS" if not failures else "FAIL", w,
                 (" " + hash) if hash else "", len(failures)))
        return len(failures)

    for w in widths:
        bad += drive(w, args.hash)
    # THE DEFAULT SWEEP DRIVES THE SEAM MODES AND THE CENSUS TOO (2026-07-26), because a mode nobody
    # remembers to pass is a mode nobody runs. Both were the SAME blind spot: 25 of 53 matrix cells
    # failed on the read/fold seam while this oracle was green at six widths, since every read state it
    # reaches, it reaches by CLICKING — and the rail's scroll trap was invisible here for want of a
    # realistic window height. `#bsread` is the boot-seeded read lead; `#synced` carries the roam
    # assertions (see SYNCED_CHECKS). Once each, at the widest width asked for: both are width-
    # independent class/label facts, and paying six Chrome runs for them would buy nothing.
    # An explicit `--hash` still drives exactly that mode and nothing else — it is the debugging path.
    if not args.hash:
        for mode in ("#bsread", "#synced"):
            bad += drive(max(widths), mode)
        cbad, cfailed = _run_census(feed, os.path.join(os.path.dirname(os.path.abspath(args.out)),
                                                       "home-census.html"))
        print("  %s census (%d assertion(s) failed%s)"
              % ("PASS" if not cbad else "FAIL", cbad,
                 (", cells: " + ", ".join(cfailed)) if cfailed else ""))
        bad += cbad
    if bad:
        raise SystemExit("home_harness: %d assertion(s) failed" % bad)


if __name__ == "__main__":
    main()
