# SPIKE — Front page restyle: Swiss brutalist newspaper

**Date:** 2026-07-25 · **Status:** PROPOSED · **Ask (Rafael):** a mock of the homepage as a
strict black-on-white International-Typographic-Style front page — full-bleed ruled grid, huge
rotated `NEWS` nameplate rail, condensed uppercase headlines, red used only as tier markers /
active underline / source links — with the verdict *"make it look like this"*.

The mandate is settled. This spike decides **how**, in shippable stages, without breaking a
single behaviour the front page already carries (filters, read state, passkey sync, voting,
editorials, propose, the how-this-works modal, both colour schemes).

The headline finding: **the mock is closer to the existing code than it looks.** The mock's
LEAD / FEATURE / BRIEF squares *are* `feed.stories[].importance` 3/2/1 — already rendered as
`.fcard__rank` and `.ff-legend`. The mock's numbered THREADS band *is* `feed.editorials`. The
mock's section index *is* `feed.topics` with its counts. Nothing in the mock needs data we do
not already build. What it needs is a different **drawing model** for the same board.

---

## 0. GATE (not a stage): make the harness trustworthy first

`tools/home_harness.py` is the only way to see this page without a Ruby toolchain, and it has
two defects that would rubber-stamp every screenshot in this project:

1. **`TOKENS` is a hand-copied duplicate** of `head/custom.html`'s `:root` block (harness lines
   40–52). A token swap that lands in `custom.html` and not in the harness renders the *old*
   palette while reporting success. Fix: extract the two `:root` blocks (light + the
   `prefers-color-scheme` override) out of `custom.html` by regex at harness build time. ~15
   lines. Non-negotiable — Stage 1 *is* a token swap.
2. **The theme's compiled `main.css` is absent.** `remote_theme: mmistakes/minimal-mistakes@4.26.2`
   means there is no local copy, so the harness never sees the skin we are fighting. Concretely
   for this redesign: minimal-mistakes' reset sets `html{box-sizing:border-box}` +
   `*{box-sizing:inherit}` — **in production `.fcard__in` is border-box, in the harness it is
   content-box**. Stage 2 adds a 2px border to every card whose width the engine assigns in px.
   The harness would therefore disagree with production by exactly 4px per column, in either
   direction, on the one measurement that matters. Fix: `--with-theme` mode that fetches
   `https://khalic-lab.github.io/claude-routines/assets/css/main.css` once into
   `/tmp/mm-main.css` (cached; `--refresh-theme` to re-pull) and inlines it *before* the tokens.

Cost: ~1h. Everything downstream depends on it. (Prior art: the harness silently tested only
the first `<script>` block for a week — 2026-07-18.)

---

## 1. Design language: token mapping

### 1.1 The mechanic — do NOT redefine `--accent`

`--accent` is load-bearing in ~24 rules and it plays two roles: *brand ink* (active chip fill,
why-it-matters rule, focus rings, sync-button hover, `.ffb-t.on`, hiw diagram keys) and
*emphasis*. Making it red floods the page with red and forces a 24-rule audit.

**Set `--accent: var(--ink)`** — every existing chrome rule turns black with zero edits — and
add a **new `--red`** applied in exactly the six places the mock uses red:

| Red is allowed | Rule |
|---|---|
| tier squares (LEAD/FEATURE/BRIEF) | `.fcard__rank[data-imp="3"]` fill, `[2]`/`[1]` border; rail index squares |
| active nav / filter underline | `.ff-chip[aria-pressed=true]` → `border-bottom:var(--rw) solid var(--red)` |
| source domain link | `.fcard__src` |
| `Just in` | `.fcard__fresh` |
| band numerals | `.fcard--ed::before` counter |
| (that is the whole list) | |

Measured: `#d81e05` on `#fff` = **5.11:1** (AA at any size). `#ff5c4d` on `#000` = **6.89:1**.
`#e3120b` (the FT red) is 4.82:1 — passes, but 5.11 buys margin against the 14px source line.

### 1.2 Values

| Token | Now (Folio) | New (Broadsheet) | Note |
|---|---|---|---|
| `--paper` | `#eceae4` / `#14151a` | `#ffffff` / `#000000` | pure both ways |
| `--panel` `--card` `--field` | 3 bone tints | `#ffffff` / `#000000` | **no grey washes** — all surfaces collapse to paper; the grid rules carry the structure the tints used to |
| `--ink` | `#23252b` / `#e7e5dd` | `#000000` / `#ffffff` | 21:1 |
| `--muted` `--muted-ui` | 4 greys | `#000000` / `#ffffff` | hierarchy moves to **scale + tracking**, the Swiss method. Escape hatch if the tiny uppercase labels overpower: `#333` (12.63:1). Existing read-dim `opacity:.58` computes to `#6b6b6b` = 5.33:1 light / `#949494` = 6.92:1 dark — both still AA, so the read-state mechanic survives untouched |
| `--rule` | `rgba(...,.62)` | `#000000` / `#ffffff` | colour only; **weight** is new tokens below |
| `--hair` | `rgba(...,.14)` | `#000000` / `#ffffff` | same colour, 1px width — internal card separators stay hairlines, exactly as the mock shows |
| `--frame` | `rgba(...,.46)` | `#000000` / `#ffffff` | |
| `--accent` | `#2b3f6b` / `#8fa9df` | `var(--ink)` | see §1.1 |
| **`--red`** *(new)* | — | `#d81e05` / `#ff5c4d` | |
| **`--rw`** *(new)* | — | `2px` | structural rules: grid gutters, card frames |
| **`--rw-heavy`** *(new)* | — | `3px` | board frame, band separators, nameplate rail edge |
| `--serif` `--display` | ui-serif stacks | grotesque stacks below | the serif voice goes entirely |
| `--sans` | Helvetica Neue… | unchanged | it was already right |

**Retire:** `--accent-chip`, `--accent-chip-hover` (unused since the brief pages went), and the
per-beat `topic_color` / `.ff-dot` colour coding — red-only forbids eleven hues. The dot becomes
a 6px **square**, ink, red when its beat is active. `topic_color` stays in the feed (harmless,
one consumer removed, no pipeline change). Beat identity is carried by the kicker text, which
every card already prints.

### 1.3 Type: one grotesque, and the condensed problem

Body / labels / kickers — system stack, zero requests, unchanged in spirit:

```css
--sans: 'Helvetica Neue', Helvetica, 'Segoe UI', Arial, system-ui, sans-serif;
--serif: var(--sans);   /* keep the token; every serif rule silently becomes grotesque */
```

Aliasing `--serif` to the sans stack is the cheapest honest way to convert ~30 body rules
(`.fcard__sum`, `.fcard__why`, `.fcard__edp`, `.hiw-*`, `.propose__*`) in one line. Delete the
alias later if a rule wants a genuinely different face; it will not.

**Headlines are the hard part.** The mock's identity is extreme weight *and* condensation. There
is no condensed grotesque installed everywhere: `Helvetica Neue Condensed Bold/Black` is Apple
only; `Arial Narrow` is Windows/Office; `Liberation Sans Narrow` is Linux; Android has neither
reliably. `font-stretch:condensed` is a no-op on static system faces.

**Recommendation, in two moves:**

*Stage 1 ships system-only* — the honest fallback, no request, ~85% of the effect:

```css
--display: 'Helvetica Neue Condensed Black','Helvetica Neue Condensed Bold',
           'HelveticaNeue-CondensedBlack','Arial Narrow',
           'Liberation Sans Narrow','Helvetica Neue',Helvetica,Arial,sans-serif;
```
plus `font-weight:900; letter-spacing:-.02em` (leads `-.035em`), `line-height:.94`,
`text-transform:uppercase`. Never `scaleX()` on headlines — it distorts stems and reads cheap.
`scaleX(.92)` is allowed on the **rotated nameplate only** (one decorative word).

*Stage 5 self-hosts one face* — and I recommend doing it. The site's rule is **zero external
requests**, not zero fonts: a `woff2` under `/assets/fonts/` is same-origin, adds no CSP
surface, no third party, no infra. Subset to **uppercase + digits + `.,:;—–'"()%$&/` only**
(every headline and label in this design is uppercase; body stays system Helvetica) → **8–15 KB,
one file**, OFL/Apache licence (Archivo Narrow / Barlow Condensed / Oswald at 700–800).
`font-display:swap`, system stack retained as the tail of the same `--display` declaration, so a
blocked or missing font degrades to Helvetica Black rather than a fallback flash of nothing.

The usual objection — "FOUT reflows the masonry" — **is already dead in this codebase**:
`home.html` line 1313 does `document.fonts.ready.then(reflow)`. The hook exists precisely for
this.

---

## 2. Layout: the ruled grid

### 2.1 The rules must be the gutters, not the borders

Drawing borders on the current masonry and setting `GAP:0` does **not** work: adjacent cards
double their borders (4px where two meet, 2px at an edge), and because columns end at different
heights the vertical rules stop at different `y` — the "full-bleed grid" reads as broken
scaffolding. Repacking is also off the table: the file already documents why CSS grid
`dense` + row-spans cannot pack around 2-column leads (300px+ voids).

**Keep the engine. Change what paints.**

1. `.folio-grid.on { background: var(--ink) }` — the ink goes on the **grid**, not the board.
   `.folio-board` keeps only `border: var(--rw-heavy) solid var(--ink); padding: 0`. Putting ink
   on the board would wreck the no-JS path: `.folio-grid:not(.on) .fcard{max-width:44em; margin:0
   auto}` over a `max-width:none` ink board is a 44em white column floating in a several-hundred-px
   black field. On the grid, the ink appears exactly when absolute placement does.
2. `.fcard__in { background: var(--paper); border: 0 }`
3. `GAP: 20 → 2` (= `--rw`)

The gutter now *is* the rule: every place two cards abut, exactly 2px of ink shows through —
one rule, never doubled, automatically correct at every junction, and automatically inverted in
dark mode (white rules on black) because it is token-driven. This is a three-value diff.

4. **Fillers — the part that makes or breaks it, and the thing that also draws the column rules.**
   With an ink grid, *every* void is a black wedge. There are three: interior notches
   (`notches[].room` residue), the **ragged column bottoms** (`grid.style.height = max(col) - GAP`,
   so every column shorter than the tallest ends in a black block), and the old board padding
   (`22px 0 10px` — zeroed in 1). Fix all three in one ~10-line pass after pass 4: for each
   residual notch and for each column `c` with `col[c] < maxH`, emit an absolutely-positioned
   `.ffill` paper block.

   **Emit fillers at exactly `colW` wide, pitch-aligned to `c*(colW+GAP)`** — the same geometry
   the engine already uses for cards. Then a filler never crosses a gutter, the 2px ink gutters on
   either side of it stay exposed, and **the column rules are continuous by construction**. No
   `repeating-linear-gradient`, no `--colw`/`--cols` writes from `layout()`: a background gradient
   on the grid would be occluded by the very fillers meant to sit in front of it, so collapsing
   both mechanisms into one is not just cheaper, it is the only version that works.

   The largest bottom filler carries the **colophon** (`News Feed` + edition line) — a print
   device, not a patch. Result: a closed frame, which is what the mock's full-width footer rule
   requires.

   Consequence: packing quality now *shows*. Tighten the harness invariant from `maxGap < 200`
   to `maxGap < 60` **on non-filled columns**, and assert `bodyScrollW == innerW` (the border-box
   check from §0).

6. **Kill the hover lift.** `transform:translateY(-2px)` + `box-shadow` are the exact anti-idiom
   here, and with 2px gutters the lift visibly tears the rules. Replace with `box-shadow: inset 0
   0 0 var(--rw) var(--ink)` on hover, or simply let the red source link be the affordance. Keep
   `.fcard__in:hover .fcard__fb{opacity:1}` and the `@media (hover:none){opacity:.82}` fallback —
   that is the voting affordance, not decoration. Also drop the per-card
   `transition:transform .28s` on reflow: mid-flight geometry in a ruled grid looks broken.
   Replace with a 120ms opacity dip on the board. (Bonus: the GEOM check reads target transforms
   precisely because of that animation; removing it makes the harness measurement exact.)

### 2.2 Nameplate rail + section index

**The shell goes on `.archive`, not `#main`.** `home.html` is `layout: archive`, and the theme's
`archive.html` renders `<div id="main"><!-- sidebar -->…<div class="archive"><h1
class="page__title">…</h1>{{ content }}</div></div>`. `#main`'s children are the sidebar include
and `.archive` — the rail would be a child of `.archive`. Making `#main` the grid host therefore
pins the *entire board* into a 180px column. Correct form (the existing `width:100%; padding:0`
reset on that selector stays):

```css
.layout--home .archive{ display:grid; grid-template-columns:clamp(150px,12vw,200px) 1fr; }
.layout--home .archive > .np-rail{ grid-column:1; grid-row:1 / -1; }
.layout--home .archive > *:not(.np-rail){ grid-column:2; }   /* tagline, filters, board, propose */
```

Second-order: the theme emits `<h1 class="page__title">News</h1>` inside `.archive` (today styled
centred at 2.7em by `custom.html`). It would become a stray grid item **and** it duplicates the
rail nameplate. Decision: `.layout--home .page__title{display:none}`; the rail plate is new markup.
The hiw modal is `position:fixed`, so it generates no grid item.

Rail contents, top to bottom: rotated `NEWS` (`writing-mode:vertical-rl; rotate(180deg)`,
`clamp(3.4rem, 8vw, 7rem)`, weight 900, `line-height:.82`) → **section index** → `News Feed`
colophon. Sticky needs **`align-self:start`** on the rail or it stretches and never sticks;
`max-height:100vh; display:flex; flex-direction:column; min-height:0` so the nameplate absorbs
the slack. Right edge `border-right: var(--rw-heavy) solid var(--ink)`.

**The section index is the beat filter** — one filtering surface, not two. It renders
`feed.topics` (label + total) and, per beat, the three tier squares with **live** LEAD / FEATURE
/ BRIEF counts.

- Counts are computed **in JS from the DOM**, not added to `build_stories_feed.py`. The
  discriminating reason: a build-time `tiers` field is wrong the instant you click *Unread* or
  deselect a beat. The filter code already iterates every card with `data-imp` + `data-topics`;
  this is a ~12-line `recount()` called from `apply()`, exactly like the existing `.ff-uct`
  unread counter. Zero pipeline change.
- Squares are `aria-hidden`; the count is real text (WCAG 1.4.1 — colour must not be the only
  carrier). Count 0 → hollow square (border only).
- `.ff-legend` in the filter bar becomes redundant and is retired: its LEAD/FEATURE/BRIEF
  vocabulary has moved into the rail, which is what the mock shows.

**The trap that would ship silently broken:** the engine resolves chips as
`filters.querySelectorAll('.ff-chip')` where `filters = getElementById('folioFilters')`, in
**four** places (`sync()`, the click binder, `chipKeys` seeding, and `seedActiveFromPrefs`'s
paint path). Chips rendered inside the rail are outside `#folioFilters`, so `active` never
populates and **`topicPrefs:v1` quietly stops roaming across devices — with no error**. The fix
is one line plus four swaps:

```js
var chipRoot = document.getElementById('folioBeats') || filters;
```

`.ff-rbtn` (read toggle), `.ff-uct`, `.ff-sync` and the focus-recovery path stay bound to
`filters` — they remain in the sticky bar.

**Responsive:** ≤900px the shell collapses to one column, the rail becomes a horizontal band
(`writing-mode:horizontal-tb`, index as an `overflow-x:auto` row). **Same element, no duplicated
markup** — so `chipRoot` stays valid and prefs keep roaming on mobile.

### 2.3 Top band, threads band, footer bar

**Top band:** the real tagline, `THE DAY'S STORIES, SIZED BY HOW MUCH THEY MATTER.` set in
`--display` at `clamp(1.5rem, 4.4vw, 3.4rem)`, uppercase, `line-height:.95`, `text-wrap:balance`,
`border-bottom:var(--rw-heavy)`. The `.folio-filters` bar (read toggle, Sync, How this works)
becomes the small nav row beneath it and **keeps `position:sticky; top:0`**.

**CROSS-CUTTING THREADS band:** `feed.editorials` (2 in the current window) restyled — but they
**must stay inside `#folioGrid`**. `cards = grid.querySelectorAll('.fcard')` drives read state,
`readCounts()`, `paintRead()` and `apply()`, and the harness asserts `edread=1`. Lifting them
into a standalone `<section>` breaks all of that invisibly. Instead **generalize the engine's
`span` from `2` to `n`**: `.fcard--ed` becomes a full-width row (width math already reads
`colW*span + GAP*(span-1)`; placement for `span===n` is `y = max(col)`, then all columns level).
The notch bookkeeping needs the same generalization — one notch per column with
`room = maxTop - col[i]` instead of the current single-column pair case (~6 lines), which also
lets the eager tallest-fit backfill fill *under* the band. Consecutive full-width rows read as
one band because the rules are continuous. Prose sets in `columns: 22em` so a 4-column-wide row
does not produce a 1200px measure. Numbering via CSS counter on `.fcard--ed::before` (red);
abstract geometric mark from a 6-item inline `data:image/svg+xml` set picked by
`:nth-of-type` — abstract marks only, ~150 bytes each. Per-editorial `ed-<stream>-<date>` read
keys are untouched.

**Footer bar:** `border-top:var(--rw-heavy)`, `News Feed` left, timestamp right.
**Correction the mock needs:** `feed.generated` is a **date** (`"2026-07-24"` — it is
`max_date`), not a wall clock; it cannot produce `03:39 AM CEST`. Do not add a field: `_config.yml`
already sets `timezone: Europe/Zurich`, so `{{ site.time | date: "%H:%M %Z" }}` renders
`03:39 CEST` honestly — Pages rebuilds on every publish push, so build time *is* publish time.
Render both, labelled: `EDITION 24 JUL 2026 · BUILT 03:39 CEST`. Zero pipeline change.

---

## 3. Images: halftone without a request

Today: `.fimg` is a bare `<img>` inserted by `swapImage()` with `filter:saturate(.9)` and a
hairline border, `aspect-ratio:16/10` (`21/9` on leads), og:image via og-proxy, lead+feature
only (77 of 80 current stories qualify), arXiv skipped.

**Treatment (Stage 4):**

```css
.fimg { filter: grayscale(1) contrast(1.42) brightness(1.04); }
@media (prefers-color-scheme: dark) { .fimg { filter: grayscale(1) contrast(1.34) brightness(.86); } }
```

Photos stay **positive** in dark mode — inverting a photograph is wrong; the white frame carries
the mode. On top, a `.fimg-wrap::after` dot screen: a 3px-pitch `repeating-radial-gradient`
at `mix-blend-mode:multiply`, `opacity:.35`. Two required guards: **`isolation:isolate` on the
wrapper** (otherwise `multiply` blends against the ink *board* and muddies the frames), and
`.fcard.is-read .fimg-wrap{opacity:.5}` must follow the existing `.is-read .fimg` rule.

The wrapper is a **JS change**: `place()` currently does
`top.insertAdjacentElement('afterend', img)` on a bare `img.fimg` — it must build
`<span class="fimg-wrap"><img class="fimg"></span>` instead. ~4 lines, same reflow call.

**Full bleed, hard frame:** the image escapes the card padding
(`margin-inline: calc(-1 * var(--pad))`, `width: calc(100% + 2*var(--pad))`) and is separated
from the text by `border-block: var(--rw) solid var(--ink)` — so the photo's frame is the same
rule as the grid's. That is the mock's look.

**Rejected:** an SVG `feComponentTransfer` posterize (true threshold duotone). It works inline
with no request, but `filter:url(#id)` drops GPU compositing in some engines and there are up to
77 filtered images on this page. Revisit only with a measured profile.

**Cards without images:** the mock fills them with engraved line-art diagrams (tactics boards,
world maps, watch drawings). **We will not generate those** — inventing illustrative imagery for
a sourced news story is fabrication, and it is against the pipeline's editorial direction. The
substitute is typographic, which is also the more Swiss answer: the kicker rule plus an oversized
condensed headline *is* the graphic. One cheap print device for a text-only lead: a drop cap on
the first summary paragraph (`::first-letter`, `float:left`, `font-size:3.4em`,
`line-height:.82`) — free, no asset, unmistakably front-page.

---

## 4. What must survive, functionally untouched

| Feature | Verdict | The specific risk |
|---|---|---|
| topic chips (multi-select) | survives, **moves** to the rail | `chipRoot` — §2.2. Silent failure mode: prefs stop roaming |
| read filter All/Unread/Read + `.ff-uct` | survives in the bar | keep bound to `#folioFilters` |
| `topicPrefs:v1` roaming (`/prefs`) | survives | same as chips; verify with a signed-in click, then restore All/All (test clicks push as the user's roamed prefs) |
| `homeRead:v1` + `syncState:v1` + passkey sync | survives, restyle only | `.ff-spanel` loses its `box-shadow` → needs `border:var(--rw) solid var(--ink)` to stay legible over the ruled board |
| thumbs + reasoned downvote | survives | `.ffb-t` / `.ffb-rzn` border-radius → 0; keep the hover-reveal opacity rules |
| editorial cards | survives **inside the grid** as the THREADS band | §2.3 — `edread=1` |
| brief-tier fold (`.fcard__more`) | survives | reflow already called |
| propose form | survives | restyle as a ruled cell; radius 0; `--field` is now white → border must carry the input |
| how-this-works modal | survives | `.hiw__box` frame `var(--rw-heavy)`; **theme styles bare `<figure>` as a flex row** — the existing `display:block` reset must stay. The 4 mermaid SVGs still carry the indigo palette; repalette in Stage 5 from `diagrams/06-public-how-it-works-{light,dark}.{json,css}` (`lineColor`, `primaryColor`, … → `#000`/`#fff`/`#d81e05`) and re-render. Acceptable interim: they are inside a modal |
| accessibility | improves | text contrast becomes 21:1. **Focus rings:** `--accent` → ink means a black outline on black rules — use `outline:var(--rw) solid var(--ink); outline-offset:2px; box-shadow:0 0 0 4px var(--paper)` (double ring, visible against rule and paper alike). Keep `.fcard__rank::after{content:"Lead"}` — the red square must never be the only carrier |
| reduced motion | improves | dropping the hover lift and the card transform transition removes two motion sources; keep the existing `prefers-reduced-motion` blocks |
| implicit read-on-open | survives — **only if the source line stays a `<span>`** | the mock renders the source domain as the card's bottom link. It is a `<span>` today; the headline is the card's only anchor. **Decision: keep it a label**, red but *not* underlined (red alone would already promise a link — underlining would compound the false affordance). If we later make it an `<a>`, the implicit-read handler matches `e.target.closest('.fcard__hl a')` in **both** the `click` and `auxclick` listeners; a second anchor needs that selector widened or opening a story from the source line silently stops marking it read |
| no-JS / pre-JS | survives | ink is on `.folio-grid.on`, so the fallback stays white (§2.1 item 1); cards there need an explicit `border:var(--rw) solid var(--ink)`, since without absolute placement there are no gutters to show ink through |
| dark mode | **pure inversion** | white rules on black, photos positive, `--red:#ff5c4d` (6.89:1). Decided: no grey "dark theme" — a B/W design inverts, that is the whole point. Every rule above is token-driven, so inversion is free |

---

## 5. Staged plan

Each stage is independently shippable and independently revertible.

| Stage | Content | Effort | Ships as |
|---|---|---|---|
| **0** | Harness gate: tokens extracted from `custom.html`; `--with-theme` main.css inline | 1h | trustworthy screenshots |
| **1** | **Token swap + hard-edge pass** — values in `:root` + dark block, `--accent:var(--ink)`, new `--red`/`--rw`, `--serif`→sans alias, `--display` system condensed stack, **plus `border-radius:0` and shadow removal on our prefixed classes** (`.fcard__in:hover`, `.ff-spanel`, `.site-unlock__box`, `.hiw__box`, `.fb-btn`, `.ffs-invite`, `.ffb-rzn input`, `.propose__*`) | 2–3h | "the black-and-white edition". No structural change, ~80% of the visual shock, safe to revert alone. The radius/shadow pass is value-level and zero structural risk, but omitting it ships rounded, shadowed modals into a design whose brief says *no rounded corners, no shadows* — Stage 1 would look accidental instead of deliberate |
| **2** | Structural rules — `GAP→2`, board=ink, column-rule gradient, `.ffill` fillers, heavy frames, hover-lift removal, full-width `span=n` for editorials | 3–4h | the ruled grid |
| **3** | Nameplate rail, top band, section index with live tier counts, `chipRoot` fix, footer bar | 3–4h | the front page |
| **4** | Image treatment — grayscale/contrast chain, dot screen, `.fimg-wrap` in `swapImage`, full bleed | 2h | halftone photography |
| **5** | Polish — self-hosted condensed woff2, THREADS marks + numerals, drop caps, hiw diagram repalette, propose/modal detail | 3–5h | finished |

≈ two focused days. **Per-stage verification** (same protocol each time): harness at 1440 / 1024
/ 390 → `GEOM overlaps=0`, `maxGap<60`, `bodyScrollW==innerW`; `SYNC` signed-out `rsCalls=0` and
`#synced` `gets=1 painted=1 unpainted=1 shadow=1`; `edread=1`; screenshots in **both** schemes;
a keyboard focus walk (chips → read toggle → sync panel → card ✓ → thumbs → reason → propose →
modal trap); contrast probe on `--red` and on `.is-read` dimmed text.

### Risks

1. **Theme bleed-through** — the recurring trap, and this restyle is its worst case because it
   changes *geometry* as well as colour. Named suspects: **the grid host is `.archive`, not
   `#main`** (§2.2 — getting this wrong pins the whole board into the 180px rail column), the
   theme's `.page__title` becoming a stray grid item, `.archive`'s reserved right-sidebar padding
   (already zeroed — must stay zeroed once it is the grid shell), `#main{max-width:1680px}` →
   `none` for full bleed, skin colours on `h1/h3/h4` and `:visited`, `.page__title a` needing
   `!important`, the light-palette table skin, bare `figure` as a flex row, and skin
   `border-radius` on buttons/inputs (re-assert `border-radius:0` on **our** classes only — do
   not blanket-reset the theme). Mitigation: Stage 0 is what makes these visible at all.
2. **Silent prefs breakage** via `chipRoot` (§2.2) — the only failure here that produces no
   visible symptom. Explicit acceptance test: click a beat, reload, chip still active.
3. **Border-box divergence** harness↔production (§0.2).
4. **Black voids** if `.ffill` is skipped or mis-measured — the design fails loudly rather than
   subtly, which is the good kind of risk.
5. **Condensed fallback flatness** on Windows/Android before Stage 5. Accept for two days, or
   pull Stage 5's font forward if the maintainer judges Stage 1 too soft.
6. **Losing eleven beat colours** costs peripheral scanability. Mitigated by the kicker text on
   every card plus the rail index; reversible by allowing one non-red hue if it reads worse.
7. **Dot-screen blend** muddying frames without `isolation:isolate` (§3).

**Rollback:** the entire redesign lives in two files — `_layouts/home.html` and
`_includes/head/custom.html` (plus `tools/home_harness.py`). No data, no schema, no Worker, no
routine prompt, no trigger. `git revert` of a stage's commit is a complete undo; `_data/homefeed.json`
is untouched by every stage.

---

## 6. Code sketch (ready to try)

### 6.1 The token block

```css
:root{
  /* surfaces — strict, no tints */
  --paper:#fff; --panel:#fff; --card:#fff; --field:#fff;
  --ink:#000; --muted:#000; --muted-ui:#000;
  /* rules: one colour, three weights */
  --rule:#000; --hair:#000; --frame:#000;
  --rw:2px; --rw-heavy:3px; --rw-hair:1px;
  /* accent mechanic: chrome is ink, red is reserved (see SPIKE §1.1) */
  --accent:var(--ink);
  --red:#d81e05;                       /* 5.11:1 on white */
  /* type: one grotesque family */
  --sans:'Helvetica Neue',Helvetica,'Segoe UI',Arial,system-ui,sans-serif;
  --serif:var(--sans);                 /* alias — converts every body rule in one line */
  --display:'Broadsheet Cond','Helvetica Neue Condensed Black','Helvetica Neue Condensed Bold',
            'HelveticaNeue-CondensedBlack','Arial Narrow','Liberation Sans Narrow',
            'Helvetica Neue',Helvetica,Arial,sans-serif;   /* 'Broadsheet Cond' = Stage 5 self-hosted subset */
  --pad:14px;
}
@media (prefers-color-scheme:dark){
  :root{
    --paper:#000; --panel:#000; --card:#000; --field:#000;
    --ink:#fff; --muted:#fff; --muted-ui:#fff;
    --rule:#fff; --hair:#fff; --frame:#fff;
    --red:#ff5c4d;                     /* 6.89:1 on black */
  }
}
```

### 6.2 The gutter *is* the rule

```css
/* The ink plane paints the rules; cards and fillers paint over it. GAP in the JS engine = 2.
   Ink lives on .folio-grid.on — NOT on .folio-board — so the no-JS block-flow fallback
   stays white (see §2.1 item 1). */
.folio-board{ position:relative; padding:0; border:var(--rw-heavy) solid var(--ink); }
.folio-grid.on{ background:var(--ink); }

/* Paper blocks closing interior notches and ragged column feet, emitted by layout() at
   exactly colW wide and pitch-aligned to c*(colW+GAP): a filler never crosses a gutter, so
   the 2px ink rules on either side stay exposed and the column rules are continuous by
   construction. No background gradient — a filler would occlude it. */
.ffill{ position:absolute; background:var(--paper); }
.ffill--colophon{ display:flex; flex-direction:column; justify-content:flex-end;
  padding:var(--pad); font-family:var(--sans); font-size:.6rem; font-weight:700;
  text-transform:uppercase; letter-spacing:.14em; }
```

### 6.3 A card

```css
.fcard__in{
  background:var(--paper); border:0; border-radius:0;
  padding:var(--pad) var(--pad) calc(var(--pad) - 2px);
  display:flex; flex-direction:column; gap:8px;
  transition:none;                                   /* no lift: it tears the rules */
}
.fcard__in:hover{ box-shadow:inset 0 0 0 var(--rw) var(--ink); }
.fcard.lead .fcard__in{ padding:calc(var(--pad) + 6px); }

.fcard__top{                                          /* kicker row: SPORTS ———— Jul 20 */
  display:flex; align-items:baseline; gap:.7em;
  padding-bottom:6px; border-bottom:var(--rw-hair) solid var(--hair);
  font-family:var(--sans); font-size:.6rem; font-weight:700;
  text-transform:uppercase; letter-spacing:.14em;
}
.fcard__hl{
  font-family:var(--display); font-weight:900; text-transform:uppercase;
  line-height:.94; letter-spacing:-.02em; text-wrap:balance;
  font-size:1.18rem; margin:0; color:var(--ink);
}
.fcard.imp2 .fcard__hl{ font-size:1.6rem; }
.fcard.lead .fcard__hl{ font-size:clamp(2rem,3.4vw,3.1rem); letter-spacing:-.035em; }
.fcard__hl a{ color:inherit; text-decoration:none; }

/* labelled blocks — "Synthesis:" / "Why it matters:" (ink rule, NOT red) */
.fcard__why{ border-left:var(--rw) solid var(--ink); padding-left:10px; }
.fcard__why-lbl{ display:block; font-family:var(--sans); font-weight:800; font-size:.56rem;
  text-transform:uppercase; letter-spacing:.13em; color:var(--ink); }

/* the six red things. .fcard__src stays a <span> and is deliberately NOT underlined —
   red already reads as a link; underlining it would promise a target that isn't there. */
.fcard__src{ color:var(--red); text-transform:lowercase; text-decoration:none; }
.fcard__fresh{ color:var(--red); }
.fcard__rank[data-imp="3"]{ background:var(--red); color:var(--paper); border:0; }
.fcard__rank[data-imp="2"]{ color:var(--ink); border:var(--rw-hair) solid var(--red); }
.fcard__rank[data-imp="1"]{ color:var(--ink); border:var(--rw-hair) solid var(--hair); }
```

### 6.4 Nameplate rail + halftone frame

```css
/* shell on .archive (the theme wraps {{ content }} in it) — NOT on #main; see §2.2 */
.layout--home #main{ max-width:none; padding:0; }
.layout--home .page__title{ display:none; }            /* duplicates the rail nameplate */
.layout--home .archive{ width:100%; padding:0; margin:0; float:none;
  display:grid; grid-template-columns:clamp(150px,12vw,200px) 1fr; }
.layout--home .archive > .np-rail{ grid-column:1; grid-row:1 / -1; }
.layout--home .archive > *:not(.np-rail){ grid-column:2; min-width:0; }
.np-rail{
  align-self:start;                  /* without this the rail stretches and never sticks */
  position:sticky; top:0; max-height:100vh; min-height:0;
  display:flex; flex-direction:column; gap:18px;
  padding:10px 10px 14px; border-right:var(--rw-heavy) solid var(--ink);
}
.np-rail__plate{
  flex:1 1 auto; min-height:0; overflow:hidden;
  writing-mode:vertical-rl; transform:rotate(180deg) scaleX(.92); transform-origin:center;
  font-family:var(--display); font-weight:900; font-size:clamp(3.4rem,8vw,7rem);
  line-height:.82; letter-spacing:-.04em; text-transform:uppercase;
}
.np-tier{ width:8px; height:8px; background:var(--red); }        /* count 0 -> hollow */
.np-tier[data-n="0"]{ background:transparent; box-shadow:inset 0 0 0 1px var(--red); }
@media (max-width:900px){
  .layout--home .archive{ grid-template-columns:1fr; }
  .layout--home .archive > *{ grid-column:1; }
  .np-rail{ position:static; flex-direction:row; align-items:center; overflow-x:auto;
    border-right:0; border-bottom:var(--rw-heavy) solid var(--ink); }
  .np-rail__plate{ writing-mode:horizontal-tb; transform:none; font-size:2.4rem; flex:0 0 auto; }
}

.fimg-wrap{ position:relative; isolation:isolate;   /* keeps multiply off the ink board */
  display:block; margin-inline:calc(-1 * var(--pad)); width:calc(100% + 2 * var(--pad));
  border-block:var(--rw) solid var(--ink); }
.fimg-wrap::after{ content:""; position:absolute; inset:0; pointer-events:none;
  mix-blend-mode:multiply; opacity:.35;
  background-image:repeating-radial-gradient(circle at 0 0, #000 0 .6px, transparent .6px 3px);
  background-size:3px 3px; }
.fimg{ display:block; width:100%; border:0;
  filter:grayscale(1) contrast(1.42) brightness(1.04); }
@media (prefers-color-scheme:dark){ .fimg{ filter:grayscale(1) contrast(1.34) brightness(.86); } }
.fcard.is-read .fimg-wrap{ opacity:.5; }
```

---

## 7. Open questions (for Rafael)

1. **Self-hosted display face** — do it in Stage 5 as recommended (one ~12KB same-origin woff2,
   uppercase subset), or stay system-only forever and accept a flatter headline voice off Apple?
2. **Beat colour** — retiring the eleven `topic_color` dots is what red-only demands, but it costs
   peripheral scanning. Accept, or keep *one* non-red hue for the active beat?
3. **`--muted` at pure `#000`** (Swiss: hierarchy from scale + tracking) or the `#333` escape hatch
   if the dense uppercase label rows read as noise?
4. **Editorials at the top** of the board (where the code puts them today) or as a band lower
   down, nearer the mock's composition — the latter needs a placement hint in the engine, not just
   CSS.
5. **Stage 1 alone** as a first ship (black-and-white edition, no structural change) — worth a
   day of living with before Stage 2 lands the rules?
