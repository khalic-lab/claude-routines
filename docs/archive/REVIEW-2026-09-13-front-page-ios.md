# REVIEW 2026-09-13 — Front page on iOS: audit verdict, designs, plan

> Point-in-time record of the 2026-09-13 audit (five read agents, adversarial verification, three designs, one judge). What shipped the same day: `11a5b36` (min-block-size hotfix), `f778038` (harness disarmed, ?probe=1 readout), `f9cff27` (unwind to a scrolling document, sticky bar) and the follow-up that replaced the invented `100dvh - 100svh` padding with the documented `viewport-fit=cover` + `env(safe-area-inset-bottom)` handling. Measured on an iPhone 17 / iOS 26 simulator: toolbar showing — innerHeight 714, 100vh/lvh 754, dvh/svh 714, safe-area-inset-bottom 0 with and without viewport-fit=cover; toolbar minimised after a swipe — innerHeight 754, dvh 754, svh 714, inset still 0, the pill overlays the bottom 40pt.

# Front page on iOS — audit verdict and plan (2026-09-13)

## What the phone actually shows

The main session's simulator run (iPhone 17, iOS 26.5, 402×874, screenshots in the session scratchpad) settles the two questions the auditors argued about:

- `probe-auto-1.png` (a synthetic page, `viewport-fit=auto`): at first paint `innerHeight 714`, `100lvh 754`, `100dvh = 100svh 714`, `env(safe-area-inset-bottom) 0px`; a plain `position:sticky; bottom:0` bar sits at 670..714, fully above Safari's capsule. **Safari 26 insets the layout viewport for its own chrome; the capsule is not an overlay.** The 40px lvh−dvh delta is exactly the band our bar was laid out in.
- `probe-cover-1.png` (`viewport-fit=cover`): every number identical, inset still 0. `cover` buys nothing for this bug.
- `probe-auto-2.png` (scrolled): `innerHeight 754`, capsule minimised, sticky bar at 710..754. A scrolling document gets the 40pt back.
- `ios-03-scrolled.png`: scrolling the live page's inner scroller never minimises the capsule.
- `ios-05-minblock.png` / `ios-06-minblock-tap.png`: the live page with one added declaration, `min-block-size:100dvh` on `body.layout--home`, shows every chip clear and Unread tappable.

So the blocker is S1 exactly as the audit stated, and one line fixes it.

## Findings, with status

| id | finding | status |
|---|---|---|
| S1 ios-shell | theme `body{min-height:100vh}` (live main.css) survives `_layouts/home.html:620-621`; body is 100lvh, the bottom track is laid out at 714..754 under the capsule, unreachable under `overflow:hidden` | **confirmed blocker; cause and fix proven on the simulator** |
| S3 ios-shell | document never scrolls (`:621`, `:622`) → capsule pinned expanded, no pull-to-refresh, no rubber band | confirmed (`ios-03`); permanent 40pt tax on a reading surface — major, not the blocker |
| S3 js | nothing persists `#shellView.scrollTop`; reload or cold open lands at story 1 (`pagehide` at `:2394` saves nothing) | confirmed, major |
| S4 ios-shell | Sync panel: phone override `:685` loses to base rule `:752`; bar clips both axes via `overflow-x:auto` at `:676` | confirmed, major, **pre-existing since July** — sign-in unreachable on phones |
| S1 js | og-image observer `:2659-2662` with `.shell__view` clipper `:622`: 600px prefetch band is 0 | confirmed, minor (image inserts land at the fold) |
| S2 js | theme SmoothScroll (`{% include scripts.html %}` `:2720`) intercepts `.ff-skip` `:42`; dead under Reduce Motion | confirmed, minor, keyboard/VoiceOver only |
| S5 js | `env(safe-area-inset-bottom)` at `:675` is 0; `viewport-fit=cover` proposed | half right: the inset is 0 (probe); `cover` changes nothing (probe-cover); the "capsule pinned expanded is the cause" half is wrong |
| unverified S6–S10 | `topCard()` measures the viewport not the scrollport `:1940-1948`; `anchored()` runs an inert pack at phone width `:1929-1939`; `.hiw-lock` `:1680` redundant; modal `4vh` `:1682`; rail `calc(100dvh - 85px)` `:1045` inside a shorter scrollport | all real, all minor; most dissolve once the document scrolls |

## The three designs

| criterion (weight) | A repair | B unwind | C rewrite |
|---|---|---|---|
| fixes iOS blocker (×3) | 9 — one line, proven | 9 — sticky on a scrolling document, proven by the probe | 7 — same mechanism, 23h+ away |
| kills the bug class (×2) | 7 — still a computed height; adds `calc(100dvh - var(--kbd))` | 9 — sticky is placed against the scrollport, footer in flow | 9 |
| preserves contract (×3) | 9 | 9 (S4 open until its Stage 4) | 4 — rail and top band dropped, masonry reorders |
| code health after (×2) | 4 — five compensations added | 6 — break-even, no new JS | 9 |
| effort / risk (×1) | 8 | 8 | 3 |
| verifiable here (×2) | 7 | 7 | 7 |
| **total / 130** | **98** | **106** | **86** |

Errors found in the designs (full list in `design_errors`):

- **A** over-hedges: its "min-block-size may still leave chips under the capsule" and the whole Stage 7 premise are refuted by `probe-auto-1` and `ios-05/06`. Its `--kbd` keyboard measurement (`innerHeight − vv.height − vv.offsetTop`) reads ~0 on iOS because Safari reveals a field by offsetting the visual viewport, and it puts a computed number back into `block-size`. Its scroll restore runs at `fonts.ready` or 2.5s, so a reload shows story 1 then jumps.
- **B** blames `overscroll-behavior-block:contain` for the lost pull-to-refresh (that declaration is inert; `body{overflow:hidden}` is the cause). Its runbook's "simctl not found" is the CommandLineTools `xcode-select` path, not agent sandboxing.
- **C** `display:grid-lanes` places items in the lane "closest to the start" (WebKit 26.4 notes) — placement by height, the mechanism the 2026-07-25 ruling at `home.html:829-850` banned. It drops the ≥1280 rail (`home.html:129-238`) and the composed top band (`:1005-1060`) while claiming to re-implement "dual chip sync (bar + rail)". Its ≥700 popover dropdown is positioned in the top layer against the viewport, not `.sync`. Its Stage 0 asks Playwright WebKit to reproduce a defect it cannot see (no chrome, lvh == dvh). Its `viewport-fit=cover` acceptance readout ("34px, if 0 it did not take") contradicts `probe-cover-1`.
- **All three** run Playwright from `/usr/local/src/spcs/hk-sofa-front/node_modules`, a work tree this personal repo must not depend on; A and B write `xcrun simctl`, which fails on this Mac (`xcode-select -p` → CommandLineTools; simctl is at `/Applications/Xcode.app/Contents/Developer/usr/bin/simctl`).

## Is a rewrite warranted?

No, and not now. The blocker is one inherited declaration and one line closes it today. The remaining iOS costs — chrome never minimises, no pull-to-refresh, no scroll restoration, dead prefetch band, dead skip link — come from the non-scrolling shell, and B removes that mechanism in ~65 lines without touching any JavaScript. C's end state is the right destination for code health, but its board and rail decisions break the contract and its estimate would be spent re-deriving behaviour that already works. Do C's health items in stages on top of B.

## Recommendation

1. Today: A's one line (`min-block-size:100dvh` at `home.html:620`).
2. Then B's Stage 0 (harness guard becomes an unconditional raise; `?probe=1` readout) and Stage 1 (unwind).
3. Then S4: A's `position:fixed` bottom-sheet sync panel, both faults at once.
4. Then the oracle: a URL-driven Playwright-WebKit script plus a simulator runbook; delete `home_harness.py`.
5. Then C's health items, one commit each, screenshot-paired — one `session()`, dead `custom.html` rules, prose diet, CSS/JS extracted to files. No grid-lanes, no rail deletion.

## Plan

| # | step | acceptance | h |
|---|---|---|---|
| 1 | `home.html:620` add `min-block-size:100dvh`; commit, push | simulator first paint: chips and All/Unread/Read above the capsule, Unread toggles on tap (pair with `ios-02-clean.png`); desktop `body.height === innerHeight`, screenshot unchanged | 0.5 |
| 2 | `tools/home_harness.py:3123-3128` → unconditional raise; `?probe=1` script before `home.html:2720` | harness exits non-zero whatever the shell says; probe prints inner/visual/lvh/svh/dvh/bar.bottom on the simulator | 1 |
| 3 | B Stage 1: delete `.shell__view` (`:97`, `:428`) and the grid shell (`:595-633`); body flex column + `min-block-size:100dvh` + `animation:none` on `#main`/`.page__footer` + `#main::after{display:none}`; bar `order:1; position:sticky; inset-block-end:0; z-index:20` below 700, `inset-block-start:0` at ≥700; `scroll-padding`; drop `:633`; `4vh→4dvh` (`:1682`); rail `top:55px; calc(100dvh - 71px)` (`:1044-1045`); fix comment `:1935-1937`; `topCard` from the bar's bottom | simulator: bar.bottom == innerHeight at first paint, chips clear; after a swipe capsule minimised and bar tracks; `#footer` jump shows bar under the footer. Playwright at 402×874/390×844/800×900/1400×900: document scrolls, bar never below the fold at 0–100%, footer never covered, every card reachable, chips hit-testable, IO band reports a card 300px below the fold, reload restores scrollY, modal keeps scrollY, no horizontal overflow, ≥700 bar top-stuck; zero console errors | 3 |
| 4 | S4: delete `:685`; after `:752` add the ≤699 `position:fixed; inset:auto 0 0 0` sheet + `.ffs-close` (markup `:62`, listener beside `:2575`) | 402 wide: Sync → panel fully inside the viewport, sign-in tappable, Close/Escape/outside dismiss; 1024/1400: `position === 'absolute'`, dropdown as today | 2 |
| 5 | `tools/verify/shell.mjs` + README (Xcode simctl path, http.server + `<base href>`, before/after rule); Playwright from a personal install; delete `home_harness.py` | script fails on the ff48375 page, passes on step 3's; runs green in under two minutes | 3 |
| 6 | Health, one commit each: one `session()` (`:2685` reuses `:2350`), one Worker URL (`:2681`); drop `scripts.html` (`:2720`); delete dead theme rules `custom.html:103,124,194-198` + false comment `:299-304`; merge split selectors and the orphan `<style>` (`:2714-2716`); nameplate cascade (`custom.html:294` vs `home.html:777`); prose diet; extract to `assets/css/home.css` and `assets/js/home.js` | after each: suite green; three-width screenshots pixel-identical except the named change; a token-without-reader session is signed out everywhere | 8 |

Phone usable after step 1 (0.5h); structural fix after step 3 (4.5h cumulative); 17.5h total.

## Verification protocol

**Simulator — real Mobile Safari, proves chrome clearance.** `SIMCTL=/Applications/Xcode.app/Contents/Developer/usr/bin/simctl`. Serve the candidate page locally the way the main session did (`python3 -m http.server`, `<base href="https://khalic-lab.github.io/claude-routines/">` so assets resolve) or hit the live URL; `$SIMCTL openurl booted "<url>?probe=1"`; `$SIMCTL io booted screenshot`. Read off the image: bar.bottom == innerHeight; every chip above the capsule; after one manual swipe the capsule minimises and bar.bottom == the new innerHeight; the `#footer` jump shows the bar in flow beneath the footer. Both colour schemes. Every "fixed" claim is a pair of screenshots taken the same way, before and after.

**Playwright WebKit — proves layout, blind to chrome.** No browser chrome, so lvh == dvh and every `env()` is 0; it cannot see the capsule and must not be cited as if it could. It proves the page's own contract (the assertion list in step 3), and the script must fail on yesterday's page before it is trusted on today's.

**Desktop Chrome** (the headless-chrome skill) for the 1400×900 before/after screenshots in step 6.

**Rule kept from the history:** an oracle built after the fix is built to agree with it. Step 2's probe ships before step 3's change, and step 5's script is checked against the broken page first.

---

# Appendix — Design B (unwind), as implemented

# Approach B — UNWIND: give the document its scroll back

**Target:** `_layouts/home.html` (+ one line in `tools/home_harness.py`).
**Status:** design only. Nothing in the repo was modified to write this.
**Date:** 2026-09-13. Written against `main` @ `46b883a`, page shell as of `3a4c2c6`.

---

## 1. Approach in one paragraph

Keep everything `ff48375` got right — the page owns its own `<html>`/`<head>`/`<body>`, the theme's
`head.html` / `footer.html` / `scripts.html` are called by name, and the footer lives inside the
page's own column where a bar can actually see it — and throw away the one thing that made the bar
unreachable: the viewport-sized, clipped body. `<body>` goes back to normal flow as a **flex column**
(which is what the theme already declares, so we stop fighting it and start stating it), the
`.shell__view` scrollport `<div>` is deleted, and the document scrolls again. The bar stays the first
child in the DOM — focus order is unchanged — and below 700px becomes visually last via flex `order`,
held at the bottom edge by `position: sticky; inset-block-end: 0`. **That is the whole mechanism, and
it needs no number:** a sticky box is positioned against the *scrollport*, which the browser defines
as the area the reader can actually see, so it cannot be laid out below the fold no matter what
`lvh`/`dvh`/Safari's chrome are doing. Its natural flow position is the end of the document, so when
the reader reaches the footer the bar comes to rest in flow above it — the exact bug `2192b44` was
written to fix, solved structurally instead of by a reservation. **The trade, stated up front:** under
today's grid shell nothing is ever underneath the bar; under sticky, the bar overlays roughly 44px of
whatever card sits at the viewport bottom for the whole scroll. Nothing becomes unreachable (one flick
moves it), but it is a persistent overlay, and it is why `scroll-padding-block-end` is part of the fix
rather than a nicety. At ≥700px nothing about the reader's experience changes: the bar is still the
top bar, still sticky, and the rail gets its real viewport back.

---

## 2. Exact changes

### Files

| File | Action | Why |
|---|---|---|
| `tools/home_harness.py` | **edit, 1 line + docstring** | **Stage 0, ships first.** Unwinding the grid *disarms* the current guard. See §2.0. |
| `_layouts/home.html` | edit | The shell, the bar, the rail, the modal lock, three comment blocks, one probe script. |
| `_includes/head/custom.html` | **untouched** | Shared with `prompts.html` and the evaluator posts. Nothing here needs it. |
| `_includes/head.html` | **create — optional Stage 5 only** | The only way to change the viewport meta. Gated on device evidence; see §3 and §8. |
| `tools/home_harness.py` | **delete — Stage 6** | Replaced, not repaired. See §4 and §7. |

No new dependencies. No Node in the publish path. Jekyll on Pages, unchanged.

---

### 2.0 Stage 0 — re-arm the oracle *before* touching the page

`tools/home_harness.py:3123` is:

```python
shell = "body.layout--home{ display:grid" in styles
if shell and '<div class="harness-doc">' in own:
    raise SystemExit(...)
```

That is a string match against `_layouts/home.html:620`. The moment Stage 1 writes
`body.layout--home{ display:flex`, `shell` goes `False`, the guard silently stands down, and a
3397-line harness that has not modelled production for a week starts printing geometry again. Under
approach B its numbers would look *more* plausible than today's, because the page really is in
document flow again — and they would still be wrong in two ways I confirmed by reading the template
at `tools/home_harness.py:3204`:

- `.folio-filters` is emitted **inside** `.wrap#main` inside `.harness-doc`. A `position:sticky` bar
  there resolves against the wrong containing block and would report clearances that do not exist.
- `grep footer tools/home_harness.py` finds the word twice, both in prose. **The harness has never
  rendered a footer.** The precise bug `2192b44` fixed — bar covering the last 40px of the footer —
  is not expressible in this instrument at all.

This is the failure the repo has already paid for three times (`65b0259`, `8a8ba9d`, and `dd24901`'s
own docstring). So the guard becomes unconditional, in its own commit, changing no rendering:

```python
def _assert_shell_modelled(styles):
    """Refuse to render: this harness has not modelled production since 2026-09-12.

    The guard used to latch on `body.layout--home{ display:grid`. That literal was the bug:
    the 2026-09-13 unwind (approach B) returns <body> to `display:flex`, which would have
    cleared the latch and resumed rendering off `.harness-doc > .wrap#main` — a shape
    production has not emitted since ff48375, with `.folio-filters` nested inside `#main`
    (so a sticky bar sticks to the wrong box) and NO FOOTER AT ALL (so bar-over-footer, the
    one defect this page has actually shipped, cannot be measured here).
    The replacement drives the real DOM. Delete this module with it.
    """
    raise SystemExit(
        "home_harness: disabled 2026-09-13. It re-assembles a page instead of loading one, "
        "and the shape it assembles is two rewrites out of date. Verify against a real DOM: "
        "Playwright WebKit for layout, the ?probe=1 readout on an iOS simulator for chrome "
        "clearance. See the shell-unwind design doc in docs/, sections 4 and 7.")
```

Also in Stage 0, the on-device readout — the only channel that gets numbers out of Mobile Safari
without attaching Web Inspector. Appended to `_layouts/home.html` just before
`{% include scripts.html %}` (currently `:2720`). Inert without the query string; ~25 lines:

```html
<script>
/* ON-DEVICE READOUT (?probe=1). Real Mobile Safari will not hand a terminal its numbers, and
   headless Chrome/WebKit have no browser chrome to measure against, so the page prints its own
   measurements into a fixed layer and the SCREENSHOT is the measurement. Inert otherwise. */
if (location.search.indexOf('probe') > -1) (function(){
  var p = document.createElement('div');
  p.style.cssText = 'position:fixed;inset-block-start:0;inset-inline:0;z-index:99999;'
    + 'font:11px/1.35 ui-monospace,monospace;background:#000;color:#0f0;padding:4px 6px;white-space:pre';
  function unit(u){
    var d = document.createElement('div');
    d.style.cssText = 'position:absolute;top:0;left:0;width:1px;height:100' + u + ';visibility:hidden';
    document.body.appendChild(d);
    var h = d.getBoundingClientRect().height; d.parentNode.removeChild(d); return Math.round(h);
  }
  function paint(){
    var bar = document.querySelector('.folio-filters');
    var r = bar ? bar.getBoundingClientRect() : { bottom:-1, height:-1 };
    var vv = window.visualViewport || { height:-1 };
    p.textContent = [
      'inner ' + window.innerHeight + '   visual ' + Math.round(vv.height),
      'lvh ' + unit('lvh') + '  svh ' + unit('svh') + '  dvh ' + unit('dvh'),
      'bar.bottom ' + Math.round(r.bottom) + '  bar.h ' + Math.round(r.height)
        + '  padB ' + (bar ? getComputedStyle(bar).paddingBottom : '-'),
      'GAP inner-bar.bottom ' + Math.round(window.innerHeight - r.bottom),
      'scrollY ' + Math.round(window.scrollY) + '  docH ' + document.documentElement.scrollHeight
    ].join('\n');
  }
  document.body.appendChild(p); paint();
  addEventListener('scroll', paint, { passive:true });
  addEventListener('resize', paint);
  if (window.visualViewport) visualViewport.addEventListener('resize', paint);
})();
</script>
```

`GAP inner-bar.bottom` is the number the whole question turns on. See §7.

---

### 2.1 The shell — replaces `_layouts/home.html:595-633`

Delete the 25-line "TWO TRACKS THAT CANNOT OVERLAP" comment (`:595-619`), the body grid rule
(`:620-621`), `.shell__view` (`:622-623`), `.folio-filters{grid-row:2}` (`:624`), the ≥700px track
swap (`:625-630`), and `.hiw-lock .shell__view` (`:631-633`). In their place:

```css
  /* ===== THE PAGE SHELL: THE DOCUMENT SCROLLS, THE BAR RIDES IT (2026-09-13) =====
     <body> is a flex column in ordinary flow. No viewport unit sizes it, nothing is clipped, and
     the only scrollport on this page is the one the browser owns.
     WHY THIS REPLACED A TWO-TRACK GRID (2026-09-12 -> 2026-09-13): a grid track is placed at a
     COMPUTED height, and on iOS that height was wrong. minimal-mistakes declares, unconditionally,
     `body{ display:flex; min-height:100vh; flex-direction:column }`. The grid rule overrode
     `display` and never mentioned `min-height`, so body's used height was max(100vh, 100dvh) =
     100LVH — the LARGE viewport — while the reader could only see 100dvh. The bar was therefore
     laid out in the band Safari's toolbar occupies, and `overflow:hidden` meant that band could
     not be scrolled to. Correct on every desktop; unusable on a phone.
     A STICKY BOX IS NOT PLACED AT A HEIGHT, it is placed against the SCROLLPORT, which the engine
     defines as the area the reader can actually see. There is no viewport unit in the bar's
     position and nothing for a chrome-height mismatch to get wrong. Its flow position is the end
     of the document, so at the foot of the page it comes to rest above the footer: the footer can
     never be covered, and no box carries a number on behalf of another.
     THE COST, stated rather than discovered later: mid-scroll the bar OVERLAYS the card at the
     bottom edge, which a track never did. Nothing becomes unreachable — one flick moves it — but
     `background` and `z-index` below are load-bearing now, not decoration, and
     `scroll-padding-block-end` exists because a focused field could otherwise land under it. */
  body.layout--home{
    /* the theme already says display/flex-direction; restated so a theme bump cannot move it */
    display:flex; flex-direction:column; margin:0;
    /* BEATS THE THEME'S `body{min-height:100vh}`. min-height and min-block-size are one logical
       property group (css-logical-1), so this is a real cascade contest and (0,1,1) wins it over
       (0,0,1) regardless of source order. dvh, not svh or vh: this bound only BINDS when the
       board is short (a filtered-empty sheet), and a short page has nothing to reflow when the
       browser chrome moves — so dvh costs nothing here and removes both the phantom scroll `vh`
       would add and the strip of bare paper `svh` would leave under the bar. */
    min-block-size:100dvh;
    /* the theme fades #main in at 150ms and the footer at 450ms (`animation:intro .3s both`).
       Neutralised once, here, for the same reason the motion bleed is killed in head/custom.html. */
  }
  #main.shell__main, .page__footer{ animation:none; }
  /* the theme's clearfix ::after is a stray (harmless) flex item at the end of #main's column */
  #main.shell__main::after{ display:none; }

  /* THE BAR IS FIRST IN THE DOM AND LAST IN THE FLOW, and that split is deliberate. DOM order is
     focus order and is unchanged from every version of this page: at >=700px, where the bar is
     the top bar, a keyboard reader meets the controls where the eye does. Below 700 the eye wants
     them under the thumb, so `order` moves the BOX and leaves the DOM alone — the same divergence
     the fixed bar always had, and `.ff-skip` is still the compensation for it. */
  .folio-filters{ order:1; position:sticky; inset-block-end:0; z-index:20; }

  /* A SCROLL HINT, NOT A RESERVATION, and the difference is the whole argument of this rewrite.
     Too large only means a focused field lands a little higher than it had to; too small only
     means the reader scrolls once. Being wrong is visible and costs nothing, where a wrong
     `padding-bottom` hid 40px of footer for months. In rem on purpose: the bar's chips are sized
     in rem, so this tracks the thing it clears across the theme's 16->22px root ladder.
     IT COVERS THE DOCUMENT ONLY. `scroll-padding` is a property of a scroll CONTAINER and is not
     inherited by one, so `.folio-rail` (its own scrollport at >=1280) is unaffected and does not
     need it — nothing focusable lands at its bottom edge.
     THE >=700 VALUE IS KNOWINGLY SHORT between 700 and 767px, where the root is still 16px and
     thirteen chips wrap to roughly three rows. Being short by one chip row costs one extra
     scroll, which is exactly the failure mode a hint is chosen for over a reservation. */
  html{ scroll-padding-block-end:4.5rem; }

  @media (min-width:700px){
    /* the bar changes EDGE, not nature — one object, read first where the screen is wide */
    .folio-filters{ order:0; inset-block-end:auto; inset-block-start:0; }
    html{ scroll-padding-block-end:0; scroll-padding-block-start:6rem; }
  }
```

`.shell__view`'s two remaining jobs move to boxes that already exist:

- `display:flex; flex-direction:column` → now on `<body>` (the theme's own declaration, restated).
- `overflow-y:auto` → the viewport's again. `overscroll-behavior-block:contain` is deleted with it;
  it was the thing suppressing iOS pull-to-refresh.

The column rules at `:640-652` (`.shell__head, #main.shell__main{ inline-size:min(1680px,100%);
max-inline-size:none; margin-inline:auto; padding-inline:1em }`, `#main.shell__main{ display:flex;
flex-direction:column; flex:1 0 auto }`, `.folio-board{ flex:1 0 auto }`) are **unchanged and still
correct** — `#main` is now a flex item of `<body>` instead of of `.shell__view`, which is the same
relationship the comment already argues for.

---

### 2.2 The markup — two lines

```diff
@@ _layouts/home.html:88-97
-{%- comment -%}
-  THE SCROLLPORT, and the one element here that is not a landmark. ...
-{%- endcomment -%}
-<div class="shell__view" id="shellView">
+{%- comment -%}
+  No scrollport element: the document is the scrollport again (2026-09-13). `.shell__head`,
+  `#main` and the page foot are direct children of <body>, which is the flex column. The
+  `#shellView` id is gone with it; `anchored()` already falls back to `window`.
+{%- endcomment -%}
@@ _layouts/home.html:425-428
   <footer id="footer" class="page__footer">
     {% include footer.html %}
   </footer>
-</div>
```

Everything else in the body — `.ff-skip` (`position:fixed`, so not a flex item), the `.hiw` modal
(`position:fixed`), the `.page__content` stub `head/custom.html` injects (`display:none`) — stays
out of the flex flow and needs no change. **The stub must keep `display:none`**; it is appended to
`<body>` after the bar and would otherwise become a trailing flex item.

---

### 2.3 The modal lock — revert to the document

```diff
-  /* the modal locks the scrollport rather than the document, which has no scroll to take away. */
-  .hiw-lock .shell__view{ overflow:hidden; }
```

`_layouts/home.html:1680` already carries `.hiw-lock{ overflow:hidden; }` on `<html>`, dead since
`ff48375` and live again the moment the document scrolls. The modal script at `:539-581` is unchanged
— it already adds the class to `documentElement`. While here, `:1682`:

```diff
-  .hiw{ position:fixed; inset:0; ... padding:4vh 16px; ... }
+  .hiw{ position:fixed; inset:0; ... padding:4dvh 16px; ... }
```

`4vh` is 4% of the LARGE viewport, which is the same unit mistake the shell rewrite existed to fix.

---

### 2.4 The rail (≥1280px) — `_layouts/home.html:1044-1045`

```diff
     .folio-rail{ display:block; grid-column:1; align-self:start;
-      position:sticky; top:8px; max-block-size:calc(100dvh - 85px); overflow-y:auto;
+      position:sticky; top:55px; max-block-size:calc(100dvh - 71px); overflow-y:auto;
       scrollbar-width:thin;
       padding:0 20px 24px 0; border-inline-end:1px solid var(--rule); }
```

This is a **restoration of a measured, shipped configuration**, not a new guess: `2192b44^:865-866`
had `top:55px; max-height:calc(100vh - 71px)` against the same sticky top bar (47px + 8px of air;
71 = 55 + 16 of bottom gap), with `vh` swapped for `dvh`.

Note what the unwind *fixes* here for free: the current `100dvh` bound is measured against the
viewport while the rail lives inside a scrollport that is `100dvh` **minus the bar** — the bound
could exceed its own container (unverified finding S10). With the document as the scrollport again,
`100dvh` means what it says. What comes back is one desktop clearance offset, and the existing
comment at `:1028-1030` already names the change that deletes it (rail as a body grid column at
≥1280). That is still the next piece, not this one.

---

### 2.5 The viewport meta — **not changed**, and that is a decision

The live meta comes from the theme: `<meta name="viewport" content="width=device-width,
initial-scale=1.0">`, no `viewport-fit=cover`. Both refuters of S5 and the independent S7 note agree
on the consequence: without `cover`, iOS insets the layout viewport to the safe area automatically
and **every `env(safe-area-inset-*)` resolves to `0px`**, so `.folio-filters`'s
`padding: 8px 12px max(8px, env(safe-area-inset-bottom))` (`:675`) has always computed a flat 8px.

Adding `cover` is a *net risk*, not a fix, for three reasons:

1. It **un-insets** the page — the layout viewport extends under the home indicator — so you then
   owe `env(safe-area-inset-bottom)` back just to return to where you already are. Zero net gain in
   bar position; the only visible change is the bar's paper bleeding into the indicator band.
2. The number it hands you describes the **home indicator (~21–34pt)**, not Safari's toolbar or the
   iOS 26 capsule. Apple Developer Forums 716552 documents the inset reporting `0px` when the
   toolbar is hidden. It is not the quantity anyone needs here.
3. It is the one change that cannot be made from this file. The page owns `<body>` but calls
   `{% include head.html %}` (`:31`), so the meta requires a local `_includes/head.html` shadowing
   the theme's — a ~30-line fork, pinned to 4.26.2, affecting `prompts.html` and every evaluator
   post as well. `_includes/` currently holds one file (`head/custom.html`); this would be the
   first fork.

So: keep the meta, keep `max(8px, env(...))` exactly as written (it is inert, it costs nothing, and
it becomes correct automatically if `cover` is ever added), and hold the fork as Stage 5, gated on
the device check in §7 actually showing that `cover` would buy something. Open question #2.

---

### 2.6 What the theme's compiled CSS still imposes, and how it is neutralised

Extracted from the live `assets/css/main.css` (66,715 bytes, byte-identical to `/tmp/mm-main.css`),
every rule that lands on `html` / `body` / `#main` / `.page__footer`:

| Theme rule | Effect under approach B | Neutralised by |
|---|---|---|
| `body{display:flex;min-height:100vh;flex-direction:column}` | `display`/`flex-direction` are **what we want** — B stops fighting them. `min-height:100vh` would make body 100lvh. | `body.layout--home{display:flex;flex-direction:column;min-block-size:100dvh}` — same logical property group, (0,1,1) beats (0,0,1). **This is the S1 leak, closed by declaration.** |
| `body{margin:0;padding:0;color;font-family;line-height:1.5}` | benign; colour/family already re-set | `custom.html:98-99`; `margin:0` restated in the shell rule |
| `body.overflow--hidden{overflow:hidden}` | never applied — this page sets no such class | nothing needed |
| `html{box-sizing:border-box;background-color:#fff;font-size:16px}` + `18/20/22px` at 48/64/80em | the root ladder is relied on by the type scale | `custom.html:98` re-paints the background |
| `html{position:relative;min-height:100%}` | benign | — |
| `#main{clear:both;margin-inline:auto;padding-inline:1em;max-width:100%}` + `@80em{max-width:1280px}` | would clamp the 1680px column | `#main.shell__main{inline-size:min(1680px,100%);max-inline-size:none}` (`:641-643`) |
| `#main{animation:intro .3s both;animation-delay:.15s}` | the board is `opacity:0` for 150ms on every load | **new:** `#main.shell__main{animation:none}` |
| `#main::after{clear:both;content:"";display:table}` | a stray zero-height flex item at the end of `#main`'s column — nothing floats under a flex column, so it is harmless either way | **new (clarity, not a fix):** `#main.shell__main::after{display:none}` |
| `.page__footer{float:left;width:100%}` | **inert, because the footer is a flex item** — floats do not apply. Worth knowing: it would bite the moment `<body>` became a plain block. | body stays a flex column |
| `.page__footer{margin-top:3em;color:#646769;background-color:#f2f3f3}` | the 3em is wanted air; the greys are not | `custom.html:202-205` |
| `.page__footer{animation:intro .3s both;animation-delay:.45s}` | the footer is `opacity:0` for 450ms | **new:** `.page__footer{animation:none}` |
| `.page__footer footer{margin-inline:auto;margin-top:2em;padding:0 1em 2em}` + `@80em{max-width:1280px}` | the theme's own `footer.html` box inside ours — fine | — |
| `.initial-content,.search-content{flex:1 0 auto}` | never emitted here | — |
| `@media print{...}` | untouched by any of this | — |

Three new declarations total, all in the shell block, all one-time.

---

### 2.7 JavaScript — zero required changes in Stage 1

| Site | Today | Under B |
|---|---|---|
| `anchored()` `:1938` | `(document.getElementById('shellView') \|\| window).scrollBy(...)` | `#shellView` is gone → **falls back to `window`, which is correct again.** Only the comment at `:1935-1937` needs rewriting. |
| `IntersectionObserver` `:2659-2662` | implicit root; `.shell__view` was an intermediate clipper that collapsed `rootMargin:"600px 0px"` to zero | **no clipper left** → the 600px prefetch band works as originally written. No code change. |
| `.hiw-lock` `:554/:561` | class on `<html>`; `:633` locked the scrollport | `:1680` locks the document again. No code change. |
| `modal.scrollTop = 0` `:550` | modal's own scroll | unchanged |
| `bootPack` / `packRowSpans` `:1789-1913` | measures `grid.clientWidth`, never the viewport | unchanged |

One optional one-liner, worth taking in Stage 2 (unverified finding S6):

```diff
   function topCard(){
+    /* against the SCROLLPORT's usable top, not the viewport's: at >=700px the sticky bar covers
+       the first ~47px, and a card with rect.bottom in 0..47 is "intersecting" but invisible. */
+    var bar = document.querySelector('.folio-filters');
+    var top = (bar && innerWidth >= 700) ? bar.getBoundingClientRect().bottom : 0;
     for (var i = 0; i < cards.length; i++){
       if (cards[i].style.display === 'none') continue;
-      if (cards[i].getBoundingClientRect().bottom > 0) return cards[i];
+      if (cards[i].getBoundingClientRect().bottom > top) return cards[i];
     }
```

---

## 3. Verified findings — fixed, and not fixed

### Fixed by the unwind

| id | Title (short) | How B fixes it |
|---|---|---|
| **S1** `ios-shell` — blocker | theme's `body{min-height:100vh}` makes body 100lvh; bar laid out under the toolbar | Two independent kills. (a) `min-block-size:100dvh` on `body.layout--home` wins the cascade contest the grid rule never entered. (b) More importantly, **the bar is no longer placed at a computed height at all** — sticky resolves against the scrollport. The mechanism is deleted, not retuned. Also removes the iOS 15.0–15.3 path one refuter flagged, where `block-size:100dvh` is dropped entirely as an invalid declaration. |
| **S3** `ios-shell` — major/minor | document can never scroll → toolbar never collapses; pull-to-refresh, rubber band, tap-status-bar gone | `overflow:hidden` and `block-size` are gone from `<body>`; `overscroll-behavior-block:contain` is deleted with `.shell__view`. The document scrolls, so Safari's chrome minimises on scroll-down again and all three native gestures return. Note the compounding effect: even in the pessimistic reading of iOS 26 (§7), a chrome that minimises on scroll means the bar is crowded only at first paint, where today it can never clear. |
| **S3** `js` — major/minor | nothing persists `#shellView.scrollTop`; reload opens at story 1 of 80 | Browsers restore **document** scroll natively. No sessionStorage, no `pagehide` handler, no restore-after-`bootPack()` ordering problem. The whole finding dissolves rather than being coded around. |
| **S1** `js` — major/minor | `rootMargin:"600px 0px"` dead against the nested scroller | `.shell__view` was the only intermediate clipper between `li.fcard` and the viewport (confirmed by both refuters). Deleting it restores the band with **zero JS change**. |
| **S2** `js` — major/minor | theme's SmoothScroll intercepts the skip link and drives `window.scrollTo` on an unscrollable document | `window.scrollTo` moves the document again, so both branches work — the animated one and the `prefers-reduced-motion` short-circuit that is currently a total no-op. Dropping `{% include scripts.html %}` would also fix it and is still the better long-term move (`:2717-2719`), but B does not depend on it. |
| **S10** (unverified) | rail's `100dvh` bound measured against a scrollport that is smaller than `100dvh` | The rail's scrollport is the viewport again, so `100dvh` means what it says. §2.4. |
| **S8** (unverified) | `.hiw-lock{overflow:hidden}` at `:1680` is dead code | Live again; `:633` deleted. |
| **S9** (unverified) | modal locks a mid-scrolled nested container instead of the document | Reverts to the pre-shell document lock, which shipped for months without complaint. `4vh → 4dvh` in the same pass. |

### Partly fixed / re-scoped

| id | Status |
|---|---|
| **S5** `js` — contested | Split it, as the two verdicts imply. The **agreed** half — `env(safe-area-inset-bottom)` is `0` on this page and always has been — is **not fixed** by B, because B does not change the viewport meta. It stops being load-bearing, though: nothing in the new shell asks that expression for anything. The **contested** half — "the capsule is pinned expanded and that is the cause" — becomes **moot either way**: the document scrolls, so the chrome minimises if it is going to, and the bar's position does not depend on the chrome's height regardless. Say plainly: `viewport-fit=cover` does **not** fix the reported bug. |
| **S6** (unverified) | `topCard()` off by the sticky bar at ≥700px — still true under B (same sticky bar, same 47px). One-line fix offered in §2.7. |

### Not fixed — and one of them is the highest-value follow-up

| id | Why not, and what it needs |
|---|---|
| **S4** — major, **the sign-in path** | Two independent faults in the Sync popover, neither touched by B: (a) a **cascade inversion** — the phone override at `:685` sits *before* the base rule at `:752` at equal specificity, so `top` and `right` are restored and the box solves to zero content height; (b) the bar is a **scroll container in both axes** (`overflow-x:auto` at `:676` forces `overflow-y` to `auto`), which clips the panel. **Do not half-fix this.** One refuter established that repairing (a) alone makes it *worse*: the panel then overflows toward the block-**start** edge, which is genuinely unreachable in any browser, where today it at least overflows into the scrollable direction. It is a paired fix — move the override after `:752` with all four insets reset, **and** take the panel out of the bar's clip (the `popover` attribute, Safari 17+, escapes every ancestor overflow clip on its own; CSS anchor positioning in Safari 26 is a placement convenience, not a requirement). Stage 4. |
| **S7** (unverified) | `anchored()` calls `packRowSpans()` unconditionally, so every More/Less tap runs an ~83-element style sweep that is inert at phone width. Pure cost, pre-existing, orthogonal. |
| **S8** (unverified) | No `touch-action` anywhere; the bar is a two-axis scroll container at the bottom edge that swallows vertical drags. Under B a vertical drag on the bar will now **chain to the document** (there is a scrollable ancestor again), so the swallowing half improves for free — but the gesture-strip overlap is unaddressed and unquantified. |
| **S9** (unverified) | `.hiw` modal's bottom band under the browser chrome — `4vh → 4dvh` (§2.3) is the cheap part; it is `position:fixed`, so it resolves against the layout viewport and its close button stays reachable. Not a blocker either way. |
| **S7** (unverified, env) | `env(safe-area-inset-bottom)` = 0. See S5 above and §2.5. Deliberately unchanged. |

---

## 4. What this deletes, and what it must re-implement

### Deletes

| What | Where | Lines |
|---|---|---|
| "TWO TRACKS THAT CANNOT OVERLAP" comment | `:595-619` | 25 |
| body grid rule, `.shell__view`, `grid-row` assignments, ≥700px track swap | `:620-630` | 11 |
| `.hiw-lock .shell__view` + its comment | `:631-633` | 3 |
| `.shell__view` element + its 10-line comment | `:88-97`, `:428` | 11 |
| Retired-band history block (already describes a design deleted twice over) | `:686-700` | 15 |
| **`tools/home_harness.py`** — Stage 6, replaced not repaired | whole file | **3397** |
| **Total, excluding the harness** | | **~65** |

Added back: ~40 lines of shell (of which ~22 are the comment explaining why sticky, kept because
this is the third design of this bar and the reasoning is what stops a fourth), the ~25-line probe,
and 3 theme-neutralising declarations. **Net on `_layouts/home.html`: roughly break-even.**

That is honest and it is the point — B is not a simplification exercise, it is a change of mechanism.
The ~1450 lines of prose/duplication the code-health pass identified are a separate, orthogonal
cleanup; folding them into this change would make the diff unreviewable and would put the shell fix
behind an argument about comment density.

### Must be re-implemented — no product behaviour, and none of the JS

This is the strongest property of approach B and worth stating plainly: **it removes code and
re-implements none.** `packRowSpans`, `anchored`, read/unread, filters, fold defaults, dual-chip
sync, prefs roaming, votes, passkey sync, the WebAuthn ceremony, og-image unfurl and the modal focus
trap are all untouched. The two JS sites that knew about the scrollport (`anchored`'s
`|| window` fallback, the IntersectionObserver's implicit root) were written to survive exactly this
unwind, and they do.

### Must be replaced — the test oracle, and only the test oracle

`tools/home_harness.py`. Its original sin is not the stale shell — it is that it **re-assembles a
page from extracted fragments** instead of loading the one Jekyll builds, so it can be
simultaneously green and testing a document nobody has. The replacement (§7) is a ~200-line
Playwright-WebKit script that navigates to a URL and asserts against the real DOM. It will not
reproduce all 40-odd CHECK/MX rows on day one; it should reproduce the ones that would have caught
this class of bug, and the rest can migrate as they earn it.

---

## 5. Effort by stage — each independently shippable to `main`

| Stage | Scope | Hours | Ships alone? |
|---|---|---:|---|
| **0** | Harness guard → unconditional `raise`; `?probe=1` readout added to `home.html`. Changes no rendering. | **1** | Yes — and **must** precede Stage 1. |
| **1** | The unwind: shell block rewritten, `.shell__view` deleted, three comment blocks rewritten, theme-neutralising declarations, `scroll-padding`. Local `jekyll serve` + Playwright WebKit pass. | **2–3** | Yes. This is the fix. |
| **2** | Rail offsets restored, modal lock reverted (`:633` out, `4vh→4dvh`), `topCard()` bar-aware, comment at `:1935-1937` corrected. | **1** | Yes. Desktop/polish; no phone dependency. |
| **3** | Verification: `tools/verify/shell.mjs` (Playwright WebKit, ~200 lines) + the simulator run in §7, results recorded. | **3** | Yes (adds a file, changes no page). |
| **4** | **S4 sync-panel pair fix** — cascade inversion + take the panel out of the bar's clip via `popover`. | **2** | Yes. Highest-value follow-up. |
| **5** | *Optional, gated:* `viewport-fit=cover` via a local `_includes/head.html` fork, only if §7 shows it buys something. | **1.5** | Yes, and trivially revertible (delete the file). |
| **6** | Delete `home_harness.py`; port the CHECK rows worth keeping into `tools/verify/`. | **6–8** | Yes. Do not let it block 1–4. |

**Critical path to a working phone: Stages 0 + 1 = 3–4 hours.**

---

## 6. Risk and rollback

**R1 — the unwind disarms the oracle. Highest-probability failure and it is procedural, not
technical.** Changing `display:grid` to `display:flex` clears
`tools/home_harness.py`'s string latch, and a harness that has not modelled production since
`ff48375` starts printing plausible-looking wrong numbers off a template with no footer in it.
*Mitigation:* Stage 0 ships first, alone, and makes the guard unconditional. **If Stage 0 is skipped,
do not ship Stage 1.**

**R2 — iOS 26's floating capsule still overlaps the bar.** The two S1 refuters split on whether
Safari 26 insets the layout viewport for its floating bar (`obscuredContentInsets`) or merely
overlays it. Under the pessimistic reading, `sticky; bottom:0` lands *behind* the capsule and the
chips are still crowded at first paint. *Mitigation, two fallbacks, both cheap:*
- **(a)** a cosmetic `padding-block-end` on `.folio-filters` below 700px. It is a number, but it
  fails soft — too large wastes a few px, too small shows up immediately in a screenshot — and it
  never hides content, because the bar's *box* is still correctly placed.
- **(b)** the `position:fixed` variant. **This is the real rollback target, and it has device
  history:** `2192b44` was `position:fixed; inset-block-end:0` with a reservation, measured and
  shipped, and the owner did not report it covered. Its sin was that the reservation lived on
  `#main` and could not reach a footer emitted outside it — **under approach B the footer is a direct
  child of `<body>`, so the reservation reaches.** Switching (a)→(b) is two declarations.
  One inference to be explicit about: what was empirically acceptable on device was **fixed**, not
  **sticky**. Both resolve against the layout viewport's bottom edge at rest, which is why sticky
  should behave identically — but that is an inference, and §7 is what confirms it.

**R3 — mid-scroll overlay.** By design (§1). The bar covers ~44px of the card at the viewport
bottom throughout the scroll. Mitigated by the fact that nothing is ever unreachable, and by
`scroll-padding-block-end` for focus-driven scrolls. If it reads badly on device, the escape hatch
is a scroll-direction auto-hide — ~15 lines of JS, and a deliberate later decision, not part of this.

**R4 — sticky jank on iOS momentum scroll.** WebKit has composited sticky asynchronously for many
years; low risk. Visible immediately in the simulator screenshots if it happens.

**R5 — `.hiw-lock{overflow:hidden}` on `<html>` losing scroll position.** The classic body-scroll-lock
family of bug. This is pre-`ff48375` behaviour with no recorded complaint, and it is directly
testable in Playwright (`scrollY` before open == `scrollY` after close). Covered in §7.

**R6 — a future theme bump.** `min-block-size:100dvh` on `body.layout--home` is the only thing
standing between the page and minimal-mistakes' `min-height:100vh`. Under B a regression there is
*benign* (a slightly over-tall body on a scrolling document), where under the grid shell it was the
blocker. That asymmetry is itself an argument for B.

**Rollback.** Every stage is one commit touching one file; `git revert <sha>` restores the previous
state exactly. Stage 1 reverts to today's shipped (broken-on-phone) page, which is why the ordering
matters: land Stage 1 when there is time to watch it, not on a Friday. The *preferred* rollback is
not "back to the grid" but forward to R2(b) — `position:fixed` on the same body, which is the
configuration with the best device record of the three.

---

## 7. Verification, runnable from this Mac, no device

Two tiers. They prove different things and conflating them is the mistake this repo has made three
times (`65b0259`, `8a8ba9d`, and yesterday's three commits: *"verified in headless Chrome"* against a
browser shape the readers do not have).

