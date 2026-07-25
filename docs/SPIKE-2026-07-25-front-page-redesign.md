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

> **Superseded by Amendment A below.** Questions 1–3 stand. Question 4 is answered there
> (editorials are a band, and the mechanism is a zone, not a placement hint). Question 5 is
> answered: no — Stage 1 alone now ships onto a board whose hierarchy is still flat, which is
> precisely the complaint Amendment A exists to answer.

---
---

# AMENDMENT A — Hierarchy first, theme second

**Date:** 2026-07-25 · **Status:** PROPOSED · **Reframes:** §1's premise and §5's stage order.
**Ask (Rafael):** *"The spike is interesting but doesn't go far enough, it's not just a matter of
theme, the information hierarchy on the page needs to be more prominent."*

He is right, and the reason is measurable rather than aesthetic. §1–§6 above are a **paint job on a
flat board**. They restyle a hierarchy that the pipeline has already flattened before a pixel is
drawn, and one that the *engine* actively scrambles. No token, rule weight or type scale fixes
either. This amendment finds both, fixes them where they happen, and re-orders the stages so the
visual work lands on a board that has something to express.

Every number below is reproduced from this repo on 2026-07-25 (`--days 14`), and every code claim
is quoted from the file it names.

---

## A.1 The first error: the cap deletes the base of the pyramid

| | imp 3 (LEAD) | imp 2 (FEATURE) | imp 1 (BRIEF) | total |
|---|---|---|---|---|
| **What the writers filed** (uncapped) | 24 — **8%** | 142 — 50% | 120 — **42%** | 286 |
| **What the page ships** (`--max 80`) | 24 — **30%** | 52 — 65% | 4 — **5%** | 80 |

*(The committed `_data/homefeed.json` — what is live this minute — reads 23/53/4: a routine built it
at a different moment in the day. The figures above are today's reproducible `--max 80` run, which is
what every other number in this amendment is measured against.)*

The writers are not the problem. `routines/_shared/newsroom-ethos.md:17` demands *"exactly one 3 per
edition unless the day genuinely has two majors; most stories are 1 or 2"* — and across the window's
**23 editions, 21 have exactly one lead**, one has three, one has none. 279 of 286 stories carry
writer-supplied `importance` from the dedup index, so `importance_for()`'s positional fallback
(`build_stories_feed.py:311`) barely fires. **Upstream judgment is already a clean 8/50/42 pyramid.**

`apply_cap()` (`build_stories_feed.py:587`) flattens it. It sorts each edition `(importance, -pos)`
and pops index 0 — **lowest importance first**:

```python
for ed in editions.values():
    ed.sort(key=lambda s: (s["importance"], -pos[id(s)]))
...
dropped.add(id(editions[key].pop(0)))          # <- lowest importance in the biggest edition
```

**The precise framing matters, because it kills the obvious fix.** The cap is not lead-hostile, it is
**brief-hostile**: `imp3` survives at exactly 24 at *every* cap from 80 to 240. It is the base that
gets deleted — 206 of 286 stories discarded, briefs first — leaving a page on which almost nothing
is ordinary. And **raising the cap measurably does not help**:

| `--max` | 80 | 120 | 160 | 200 | 240 |
|---|---|---|---|---|---|
| imp 3 / 2 / 1 | 24 / 52 / 4 | 24 / 90 / 6 | 24 / 111 / 25 | 24 / 131 / 45 | 24 / 142 / 74 |

The mix stays feature-dominated at every setting; the flat board just gets longer. **No cap can
produce a pyramid, because the source is 50% features.** The cap's job is only to stop deleting the
base and stop pinning a fortnight of stale features. The pyramid itself has to be *drawn* (§A.3–A.4).

## A.2 The second error: an edition's lead is not the page's lead

24 leads is **correct data** — 23 editions, one lead each, exactly as instructed. The rendering error
is treating *"this edition's lead"* as *"this page's lead"*. A newspaper has section leads too; only
one of them runs above the fold at 5rem.

So the page needs two distinct concepts where it currently has one:

- **tier** — editorial, writer-assigned, per edition (`importance`). Unchanged. Never overridden.
- **display rank** — page-level, derived, `(date, importance)` order. Exactly one card is the splash.

This is also why widening §6.3's type ratio backfires. 1.18 / 1.6 / `clamp(2rem,3.4vw,3.1rem)` is a
2.6× spread, up from today's 1.65× — but applied to 24 leads it does not produce a hierarchy, it
produces **a wall of 3.1rem headlines with 52 near-peers underneath**. The more emphatic the lead
treatment, the more absurd it looks repeated 24 times. **Scale is a consequence of A.1–A.4, not a
peer of them.**

## A.3 The fork: zones are DATA, never DOM

Three candidate architectures were stress-tested. Two are fatal, and the fatal mechanism is one line:

```css
.folio-grid.on .fcard{ position:absolute; top:0; left:0; margin:0; }   /* home.html:364 */
```

**It is a descendant selector**, and `.folio-grid` is the `position:relative` ancestor
(`home.html:361`). Therefore:

| Candidate | Verdict | The mechanism that kills it |
|---|---|---|
| **(a) keep the masonry, change only what paints** — the stance of §1–§6 | **insufficient** | `layout()` is one global shortest-column pass whose eager tallest-fit backfill (`:665-676`) pulls the *tallest* fitting card from the whole remaining queue, and whose pass-4 bottom-steal (`:719-771`) promotes cards from below into notches above. Position encodes packing convenience **by construction**. It can express A.1 and part of A.5 and cannot express a contiguous index, an edition fold, or one splash — i.e. it cannot answer the complaint. Worse, it is *self-defeating* the moment A.1 lands: ~90 cards ordered by height is a longer flat board |
| **zones as nested containers** (`<section class="zone-lead">` inside `#folioGrid`) | **fatal** | cards nested one level down still go absolute against `.folio-grid`; the wrapper collapses to 0 height and `grid.style.height = max(col) - GAP` (`:772`) accounts for nothing inside it. **All three zones stack at y≈0 and overlap** |
| **briefs in a flow index outside `#folioGrid`** | **fatal** | `cards = grid.querySelectorAll('.fcard')` is captured once (`:618`) and the fold (`:869`), read toggle (`:880`) and votes (`:1038`) are all delegated on `grid`; `readCounts()`, `paintRead()` and `apply()` iterate `cards`. Index rows would get no read dimming, no unread count, **no beat filtering** (they stay visible while the grid empties — the filter looks broken), no votes, no fold. **Six shipped features die silently** |
| **(c) full zones, retire the packer** | **fatal** | `home_harness.py:63` derives every rect by regexing `style.transform` for `translate(x,y)`. With no absolute placement the regex misses, every rect becomes `l=0,t=0`, and the overlap loop counts every pair. The only way to see this page without a Ruby toolchain **goes dark exactly when the riskiest change lands** — the third instance of that failure shape in this repo |

**Chosen: (b) zones + masonry band, where a zone is a data partition inside `layout()`.** Same
`#folioGrid`, same direct-child `.fcard` elements, same absolute placement, same `cards` array,
same delegated handlers. The existing body of `layout()` is extracted **unchanged** into
`packRange(items, cols, colW, x0, y0)` and called once per zone:

- **Zone A — the splash + today.** `data-fresh="1"` and `data-imp>=2`.
- **Zone B — the band.** Everything else with `data-imp>=2`, plus `.fcard--ed` (the THREADS band of
  §2.3 is a *zone*, which answers old open question 4 without a placement hint).
- **Zone C — the index.** `data-imp="1"`, placed by a second, **dumber** placer: ~15 lines,
  column-major, count-partitioned via `ceil(k/cols)`, no notches, no steal.

Zones are recomputed from `visible` on every layout, so a beat filter re-derives them; an empty zone
takes zero height and its divider goes `display:none`.

**The splash is slot-based, not tier-based:** its occupant is the first visible card in rank order
with `data-imp>=2`. **Never keyed on `.lead`** — editorial cards carry class `lead` with
`data-imp="2"` (`home.html:56`) purely for the `span=2` side effect, and would otherwise win the
splash. If nothing qualifies (filter to a briefs-only beat, or a no-lead fortnight) Zone A collapses
to zero height and the band becomes the top zone.

## A.4 Briefs stop being cards — the change that makes A.1 and A.5 affordable

A tier-1 brief becomes a **ruled one-line row** that is still a `.fcard`, still a direct child of
`#folioGrid`, still absolutely placed. Be honest about the numbers: the row is **~32px, not 24px**,
because `.fcard__read` (22×17 plus a −6px touch target) and the two `.ffb-t` thumbs stay per-story —
reasoned votes are this pipeline's highest-value signal and are not negotiable for a lower tier.

What it costs in the engine: nothing new. The fold is already there and already correct —
`.fcard[data-imp="1"] .fcard__more{display:inline-flex}` (`home.html:443`) plus `is-folded`
collapsing `.fcard__sum`/`.fcard__why`, with `reflow()` on expand; every imp1 has a summary
(`load_recent` skips bodyless stories), so every row gets its button. No image work: `data-ogurl`
and `.fcard__fresh` are both gated on `importance > 1` already. Retire the *"Brief"* rank chip on
rows (~40% of a 32px row's width) but keep the word in `.ff-legend`/the rail index as real text —
row shape must not become the only tier carrier (WCAG 1.4.1).

**This is the axis that unlocks the other two.** A brief at 32px instead of ~300px means the page can
afford ~20 of them, so A.5 has somewhere to put the base of the pyramid; and it is the real answer to
"scale ratio", because the contrast a reader actually perceives is **rendered area**, not type size —
a ~32px row against a multi-hundred-px splash, *without changing a single `font-size`*. **Unlike every
other figure in this amendment, that ratio is not yet measured**: it needs real card heights, which is
exactly what stage 1's harness makes obtainable. Treat it as directional until stage 3 prints it.

## A.5 The cap policy: weighted, recency-banded — verified by prototype

Weight by **rendered form**, not tier: `splash=6`, `feature card=3`, `index row=1`. Today's shipped
page is **235 weight**, so a budget of **B=240** is "no page-length regression" by construction
rather than by guess. Keep `apply_cap`'s edition/stream skeleton — it is the invariant that stops a
dense Weekend erasing Science — and **change only the comparator**:

1. **Age band** from `max_date`: `0` = today, `1` = ≤2d, `2` = ≤6d, `3` = older.
2. **Per-edition tier depth**, retaining earliest position first:
   band 0 `{3:∞, 2:8, 1:10}` · band 1 `{3:∞, 2:6, 1:4}` · band 2 `{3:∞, 2:3, 1:0}` ·
   band 3 `{3:∞, 2:1, 1:0}`. **Briefs are perishable — they expire at 2 days.** That single line is
   what keeps the index at ~20 rows instead of 120.
3. **Global weight backstop:** while `weight(keep) > B`, drop `max by (band, -importance, position)`
   — oldest band, lowest tier, latest position. **Never an imp3.** That is an *existing* structural
   property (measured: imp3 = 24 at every cap 80→240) — preserve it and **test** it.
4. **Floors:** `MIN_LATEST_EDITION` 6 → 3 (one lead + two features) on each stream's newest edition,
   plus an absolute per-stream floor of ≥1.

**Measured** (prototype run against the live uncapped window, reproduced independently):

```
KEPT n=91  3=24 2=48 1=19  (26%/53%/21%)  weight=238
today kept 28 of 47          (vs 16 today — today's coverage nearly doubles)
streams: news 42, weekend 23, ai-ml 17, science 5, sports 4
biggest edition kept: 21     beats: 11 of 11     leads dropped: 0
```

Note honestly that 26/53/21 is *not* the source 8/50/42 — it cannot be, per A.1. The pyramid is drawn
by one splash and 19 rows, not by the cap. What the cap delivers is a base that exists at all, a
fortnight of stale features thinned, and **31 → 19 of today's stories dropped**: since post pages
were unpublished on 2026-07-18 the feed is the only reading surface, so this strictly *improves*
reachability. Worth saying out loud when it ships.

**Degenerate cases, all measured or named:**

- **A 40-story edition.** Real, twice: `('2026-07-25','weekend')` = 40 (3/20/17) and
  `('2026-07-18','weekend')` = 40 (1/14/25). With no band-0 depth cap, Weekend takes ~54% of the
  page and Science falls to 4 — the front page becomes one desk's arXiv index. Hence a ceiling in
  band 0 too. Worth testing in the same stage: make the band-0 ceiling a per-edition *weight*
  ceiling rather than counts (so a 17-brief roundup is admitted generously as 17 weight of rows while
  its 20 features are rationed), binding only while the global budget is exceeded.
- **A stream silent for a week** (sports, science are weekly). The bands would reduce it to
  lead-only, so the per-stream floor is load-bearing. Floor 3 keeps science 5 / sports 4 above.
- **Never zero for a beat.** `feed.topics` is computed from the *capped* set
  (`build_stories_feed.py:637-642`), and a vanished chip corrupts reader prefs — see A.7.
- **Zero leads on the page** is impossible unless the writers emit no 3 for 14 days. If it happens,
  no card gets `span=2` and the splash falls back per A.3, handled in the zone code, not the cap.

**Do not fix this upstream.** `routines/weekly-evaluator.md:69` instructs the Sunday Evaluator to
spot-check `_data/homefeed.json` and treat *"an edition with no 3 / several 3s"* as **the writer's
error to flag**. Re-scoring importance in the writers to suit a rendering decision would manufacture
false findings against them every Sunday, and would turn a one-file page problem into
`newsroom-ethos.md` + four assembled prompts + the evaluator's ~8 enumerations.

## A.6 Ordering: position must encode rank

Rank already exists and is already correct — `build_stories_feed.py:632` sorts `(date, importance)`
descending and DOM order *is* rank order. Make it explicit as `data-rank` on the article so the
engine never re-derives it, and mirror it in `home_harness.py::card()`.

The engine change is three parts:

1. **Partition into zones first, pack per zone** (A.3). Packing keeps all its freedom *inside* a
   zone, where cards are peers and reordering costs nothing semantically.
2. **Promotion eligibility** — the actual fix for the eager backfill (`:665-676`) and the pass-4
   bottom-steal (`:719-771`). A candidate may fill a notch only if (i) it is in the **same zone** and
   (ii) its `data-date` equals the date of the card that owns the notch. Same-day is
   data-expressible, self-documenting, and directly encodes "position encodes recency-rank" —
   preferable to a tuned rank window nobody will ever retune. Whatever no longer qualifies leaves a
   hole, which becomes a pooled `.ffill` paper block at `colW` width, pitch-aligned to
   `c*(colW+GAP)`. §2.1 item 4 needs those fillers anyway: **a void stops being a bug and becomes a
   blank cell.**
3. **Kill the shift-steal fallback** (`:737-762`) outside Zone B. It moves every card at or below
   `leadTop` down by `delta` and rewrites `col`, `notches` and `placedRec`; inside a rank-ordered
   zone it would drag the whole page to close one hole.

**Pool dividers and fillers once at boot** and reposition them per layout. `reflow()` fires on up to
77 og-image loads, on resize, on `load`, on `document.fonts.ready` and on every fold/vote/reason
send — elements appended per call leak, and because `cards` was captured at `:618`, `apply()` would
never hide them. Never move a card between containers on reflow: moving a focused element blurs it
mid-vote-reason. Partition the index **by count**, not by height — a height-balanced partition
re-partitions when a `.fcard__more` expansion changes a row's height, so rows would jump columns
under the cursor.

## A.7 Two latent defects this work exposes — worth fixing regardless

**1. Roamed beat preferences are silently lossy.** `home.html:926` claims *"Chip keys absent from
this page are ignored, never lost."* They are lost. `seedActiveFromPrefs` (`:944`) admits a key only
`if (chipKeys[k])`, and `recordPrefsChange` (`:969`) then writes
`topicPrefs = { topics: Array.from(active), … }` with a fresh `ts` — so the next chip click
**overwrites the stored list with only the keys this build happened to render**, on every device.
Any cap policy that can take a beat to zero triggers it, but the bug is already live and independent
of this redesign. The obvious one line:

```js
topics: Array.from(active).concat(topicPrefs.topics.filter(function(k){ return !chipKeys[k]; }))
```

> **DO NOT SHIP THAT LINE AS WRITTEN** (verified 2026-07-25, see
> `docs/PLAN-2026-07-25-front-page-hierarchy.md` §1 D-I). Two reasons, both confirmed by reading the
> code. (a) `tools/feedback-sink/src/worker.js:583-585` **rejects** with HTTP 400 at
> `topics.length > 50` — it does not clamp — and `home.html:965` branches only on `401`, so an
> unbounded concat grows the list until topic *and read-state* roaming stops permanently and
> silently on every device. (b) It is not a pure bug fix: `active.clear()` (the All chip) then
> writes a non-empty `topics`, so **"back to All" stops propagating** — reversing the deliberate
> replace semantics documented at `:923-925`. And there is no escape hatch: `worker.js:612`
> re-serialises only `{topics, rs, ts}`, so a separate `held` field is dropped on the round trip.
> The All-vs-held choice is structural and needs Rafael's decision. The client-side cap and non-2xx
> surfacing are needed either way.

**2. The harness cannot see this class of change.** Three known blind spots, all confirmed:
`home_harness.py::card()` (`:209-225`) is a **hand-written mirror** of the Liquid, so a new
`data-fresh`/`data-rank`/`data-zone` attribute simply will not exist in the harness DOM; `GEOM`'s
`maxGap` groups rects by distinct left-x (`:68-69`), so zones with different column pitches report
inter-zone whitespace as a packing regression; and `apply_cap` has **zero test coverage** — `grep`
finds `apply_cap`/`MIN_LATEST_EDITION` nowhere under `tools/tests/`, and the golden byte-diff
(`test_feed_sid.py:87`) runs with `--max 0`, so the cap is excluded from the only regression net.

Consequence, and it is the whole reason Stage 1 is a gate: without an asserted **zone-cardinality**
line, a missing `data-fresh` attribute files every card into "earlier", the splash never renders, and
`GEOM` still prints `overlaps=0 maxGap=fine`. **Green on a broken page.** Add `zones=<a/b/c>` and
`fills=<n>` to the GEOM line with asserted values, report `maxGap` per `data-zone`, and dump
`(rank, zone, x, y)` per visible card to assert `y` is monotonically non-decreasing by rank within
each zone (modulo same-date reordering).

**One hard blocker to know about before A.5/A.6 add any feed field.**
`tools/tests/test_feed_sid.py:130` asserts `extra_keys == {"sid"} & extra_keys` — it whitelists
*exactly one* new key on a story dict and fails the instant a second appears. Adding e.g.
`display_rank` therefore also touches that whitelist and requires regenerating
`tools/tests/fixtures/dualwrite/golden-feed.json` via the `capture_golden_feed()` helper at
`test_feed_sid.py:99-108`. (Everything else tolerates extra keys: no consumer iterates `story.keys()`
or validates a closed schema.) **Cheapest path: derive rank and zone in JS from `data-imp` +
`data-date`, which the cards already carry, and add no feed field at all.**

## A.8 Revised staging

> **SUPERSEDED by `docs/PLAN-2026-07-25-front-page-hierarchy.md` (PLAN v2, 2026-07-25).** The table
> below is kept for the reasoning only. A.8 — and PLAN v1, which refined it — both assumed the
> masonry packer stays. **It does not.** v2 deletes `:637-771` outright: the ranked list is the model
> (`.folio-grid:not(.on)` at `:362` already IS it, and `.on` at `:615` repacks it by height), and the
> desktop composition is a CSS-Grid band projection of that list. Consequences: stages 2 and 5 of
> A.8 disappear rather than being resequenced; the full-width splash was an invention of the plan,
> not of the mock (the dominant module is upper-right); and **the theme is no longer last** — grid,
> type, imagery and hierarchy are one system. Stage 9's *spec* is still cut (four undefined custom
> properties) but its goals are load-bearing.
>
> Two changes worth more than everything in this table, neither of which was in A.8: the curated
> short headline already exists in `index/stories/*.jsonl` and the feed builder ignores it (median
> 114 → 75 chars, verbatim headline/body duplication 27 → 0, three lines); and the editorial loop at
> `:55` emits before the story loop at `:77`, putting ~4100px of AI opinion above the first news
> story on a phone.

The old §5 does not disappear — it becomes the **last** stage, applied to a page whose hierarchy is
structural. Effort figures are estimates; dependencies are not.

| Stage | Content | Files | Est. | Depends on |
|---|---|---|---|---|
| **1** | **Gate:** harness trust (`data-*` mirror, per-zone `maxGap`, asserted `zones=`/`fills=`, rank-monotonicity dump) + the one-line prefs fix (A.7) | `home_harness.py`, `home.html` | 2h | — |
| **2** | `packRange()` extraction — a provably behaviour-identical no-op refactor | `home.html` | 2h | 1 (needs a trustworthy geometry dump to diff against) |
| **3** | Brief **row skin** — CSS only; ships on the 4 imp1 cards already in the feed | `home.html` | 2h | 1 (screenshots); independent of 2 |
| **4** | `apply_cap` **spec test (RED)** — no behaviour change, closes a zero-coverage gap. Must assert: no imp3 ever dropped; every stream keeps ≥1; **at least one story with `date == max_date` survives** (`fresh` is stamped *after* the cap, so the top zone's existence depends on it) | `tools/tests/test_feed_cap.py` | 1h | — (parallel with 1–3) |
| **5** | **Zones:** `data-fresh`/`data-rank`, zone partition, splash slot, pooled dividers + `.ffill`, same-day promotion guard | `home.html`, `home_harness.py` | 5–6h | 1, 2, 3 |
| **6** | Weighted recency cap behind `--policy weighted`, old default unchanged | `build_stories_feed.py`, `test_feed_cap.py` | 2h | 4 |
| **7** | **Flip the cap default** (one line) + regenerate the feed | `build_stories_feed.py`, `_data/homefeed.json` | 0.5h | 5, 6 |
| **8** | Scale ratio to 4–6×: generalize `span` 2 → n, splash full-width, editorial band, mobile clamps | `home.html` | 3h | 5 |
| **9** | **The existing §5 in full** — tokens, ruled grid, rail, images, polish | `home.html`, `head/custom.html`, `home_harness.py` | 12–16h | 8 (its `GAP→2` / ink-grid work assumes the fillers and zone geometry from 5 and 8) |

**Correction to §5's rollback claim.** "The entire redesign lives in two files… `_data/homefeed.json`
is untouched by every stage" holds for stages 1–5, 8 and 9 — **not** for 6–7. `tools/publish.py:289`
and `:393` invoke `build_stories_feed.py` with **no arguments**, so the policy is a *default* and
reverting the commit does not regenerate the feed. That is exactly why the policy lands behind
`--policy weighted` in stage 6 and the default flips as a separate one-line commit in stage 7:
rollback of 7 is `git revert` **plus one** `python3 tools/build_stories_feed.py` run. Note also that
generalizing `span` 2 → n (stage 8) is the same engine change §2.3 already needs for the editorial
band — do it once, there.

Blast radius for the cap change, verified: `apply_cap` is its own sole implementation; **no test or
doc anywhere pins the 80-item total or the capped tier mix**; `build_stats.py` and all four live
Workers have zero references to `importance`/`is_lead`/`homefeed`; and the ledger-side `importance`
(`dedup.py`, `store/`, `plane/`, and every `tools/tests/test_{backfill,dualwrite,…}.py` fixture) is a
**separate store**, untouched by any stage here. Docs to update with stage 6: the module header at
`build_stories_feed.py:17`, `apply_cap`'s docstring (`:588-592`), and `ARCHITECTURE.md:834` only if
the floor mechanism itself changes (it does — 6 → 3).

## A.9 Revised open questions

Old questions 1–3 stand (self-hosted face; beat colour; `--muted` at pure black). 4 and 5 are
answered above. New:

1. **Budget `B=240`** is set to today's rendered weight so the page does not get longer. Is
   "no length regression" the right constraint, or should the front page get *shorter* and denser?
2. **Briefs expire at 2 days** (band-1 depth `1:4`, band-2 `1:0`). That is the single line governing
   index length. Right instinct, or should the index carry a full week of shorts?
3. **`MIN_LATEST_EDITION` 6 → 3** thins the weekly desks (science 5, sports 4 in the measured run).
   Acceptable, or floor the weekly streams higher than the daily ones?
4. **One splash, or one splash per band-0 stream?** A slot-based splash means a single story owns the
   top of the page. On a day when News and Science both lead strongly, is that right, or should
   Zone A hold up to two?
5. **Stage 3 alone** (brief rows, CSS only, 4 cards) is now the cheapest thing that shows Rafael
   whether the row form reads as an index at all — before stages 5–7 make 19 of them. Worth
   shipping first for a day?
