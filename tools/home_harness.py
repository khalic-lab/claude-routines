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
    python3 tools/home_harness.py --check --hash '#synced'      # the signed-in roam path
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


# THE READ SPINE — the one probe for the 2026-07-26 seen rework, and it is a state machine rather
# than four probes fighting over the same page. In order:
#   1. per-card, mark a lead and a feature read and measure the collapse (spine <= 0.55x folded).
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
  var gridH0=Math.round(grid.getBoundingClientRect().height);

  // 1 + 2 — per-tier collapse, then re-open in place
  var worst=0,measured=0,reopen=-1;
  var probe=cards.filter(function(c){
    return !c.classList.contains('fcard--ed')
      && (c.dataset.imp==='3'||c.dataset.imp==='2')
      && c.classList.contains('is-folded') && c.querySelector('.fcard__sum');
  }).slice(0,6);
  probe.forEach(function(c){
    var before=h(c);
    tick(c);
    var ratio=before>0?h(c)/before:9;
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
  cards.forEach(function(c){ if(c.classList.contains('is-read'))tick(c); });
  var gridH2=Math.round(grid.getBoundingClientRect().height);
  try{ ['homeRead:v1','syncState:v1'].forEach(function(k){ localStorage.removeItem(k); }); }catch(e){}

  var drop=gridH0>0?Math.round(100*(gridH0-gridH1)/gridH0):-1;
  var d=document.createElement('div');d.id='readcheck';
  d.textContent='READ measured='+measured+' worstRatio='+(Math.round(worst*100)/100)
    +' spineOk='+((measured>0&&worst<=0.55)?1:0)
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
  var d=document.createElement('div');d.id='shotcheck';
  d.textContent='SHOT mode='+h.slice(1)+' '+what;document.body.appendChild(d);
},5900);
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
  var sidA = fbs[0] && fbs[0].dataset.story, sidB = null;
  for (var i = 1; i < fbs.length; i++){
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
    ' prefsCalls=' + prefsCalls + ' prefsRs=' + prefsRs + ' edread=' + edread;
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
    ("READ", "spineOk", lambda v: v == "1", "a read lead/feature collapses to <=0.55x its folded height"),
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
                       ("foldcheck", "FOLD"), ("readcheck", "READ"), ("synccheck", "SYNC"),
                       ("emptycheck", "EMPTY")):
        m = re.search(r'<div id="%s"[^>]*>(.*?)</div>' % div_id, out, re.S)
        if not m:
            continue
        text = re.sub(r"\s+", " ", m.group(1)).strip()
        name = text.split(" ", 1)[0]
        kv = dict(re.findall(r"(\w+)=([^\s\]]+)", text))
        marks[mk] = (name, kv, text)
    lines, failures = [], []
    for mk in ("GEOM", "DAY", "FILTER", "FOLD", "READ", "SYNC", "EMPTY"):
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
                    help="--check only: a URL hash mode to drive (e.g. '#synced', '#bootempty')")
    args = ap.parse_args()

    feed = json.load(open(os.path.join(ROOT, "_data", "homefeed.json")))
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
%s%s%s%s""" % (_theme_css(args.refresh_theme) + TOKENS, styles, header, feed["count"], chips,
               SYNC_UI, LEGEND_UI,
               _extract_rail(feed),
               # ONE LOOP OVER feed.board, branching on `kind` — exactly what the layout does.
               "".join(ed_card(it) if it["kind"] == "editorial" else card(it)
                       for it in _require_board(feed)),
               empty_state,
               propose,
               modal, PRE_SYNC, script, VOID_METRICS,
               GEOM_CHECK + DAY_CHECK + FILTER_CHECK + FOLD_CHECK + SYNC_CHECK + EMPTY_CHECK
               + READ_CHECK + SHOT_CHECK)

    with open(args.out, "w") as fh:
        fh.write(page)
    print("wrote %s (%d bytes, %d stories)" % (args.out, len(page), feed["count"]))
    if not args.check:
        return
    bad = 0
    for w in [int(x) for x in args.widths.split(",") if x.strip()]:
        failures, lines = _run_check(os.path.abspath(args.out), w, hash=args.hash)
        print("--- %dpx%s" % (w, (" " + args.hash) if args.hash else ""))
        for ln in lines:
            print(ln)
        for f in failures:
            print("  FAIL %s" % f)
        print("  %s at %dpx%s (%d assertion(s) failed)"
              % ("PASS" if not failures else "FAIL", w,
                 (" " + args.hash) if args.hash else "", len(failures)))
        bad += len(failures)
    if bad:
        raise SystemExit("home_harness: %d assertion(s) failed" % bad)


if __name__ == "__main__":
    main()
