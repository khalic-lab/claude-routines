# CSS audit — front page (key: css)

Scope: `_layouts/home.html` `<style>` 587–1789 and 2727–2729, all `<style>` in `_includes/head/custom.html`, and the minimal-mistakes 4.26.2 compiled CSS that bleeds in.
Abbreviations: **H** = `_layouts/home.html`, **C** = `_includes/head/custom.html`, **MM** = the deployed theme CSS `https://khalic-lab.github.io/claude-routines/assets/css/main.css`, fetched to `scratchpad/understand/mm.css` and pretty-printed one rule per line as `scratchpad/understand/mm.pretty.css`. MM:n is a line in the pretty file.
Size: H's style block is 1,201 lines, but only **426 of them are code** (294 rule blocks, ~26 KB). The other ~66 KB is comments. C carries 139 code lines. The admin console `_layouts/admin.html:11,18` also includes C and consumes its tokens, so the token block is shared. Do not fork it per page.

---------------------------------------------------------------------------------------------------
## 1. Design tokens to preserve (exact values)

### 1.1 Palette. `light-dark(light, dark)`, one `:root`, C:69–96. `color-scheme: light dark` at C:70 is what arms it.
| token | light | dark | uses (H+C / admin) | role |
|---|---|---|---|---|
| --paper | #eceae4 | #14151a | 12/1 | page, bar, modal box, chip-on-ink text |
| --panel | #e2e1d9 | #1d1e25 | 6/1 | editorial module fill, image placeholder, table th |
| --card | #f3f2ec | #1a1b21 | 1 live (`.ff-spanel` H:763) / 2 | sync panel only. Removed from modules (H:1255–1258: 1.07:1, did nothing) |
| --ink | #23252b | #e7e5dd | 52/7 | text, selected chip fill, feature glyph |
| --muted | #5f616a | #9a9ca6 | 29/17 | labels, beat kicker, meta |
| --muted-ui | #565863 | #b0b2bb | 21/3 | control text; ≥3:1 control borders (C:208) |
| --rule | rgb(35 37 43/.62) | rgb(231 229 221/.5) | 26/3 | module rule system, 4.12:1 / 4.44:1 (H:868–872) |
| --hair | rgb(35 37 43/.14) | rgb(231 229 221/.13) | 30/8 | decoration only, 1.31 / 1.38:1 |
| --field | #f6f5f0 | rgb(255 255 255/.05) | 3/2 | inputs |
| --frame | rgb(35 37 43/.46) | rgb(231 229 221/.3) | 1/1 | input border, ≥3:1 (C:332–334) |
| --accent | #2b3f6b | #8fa9df | 44/8 | ink-indigo structure: lead edge, focus, "Why" rule, read ✓, All chip. 8.62:1 |
| --red | #c8102e | #ff5a5f | 4/8 | 4.89:1 / 5.97:1. Lead glyph, source domain, "Just in", selected rail beat. Must stay a PAIR (C:82–86) |
| --accent-chip, --accent-chip-hover | #3a3d47/#4a4d57, #2b2e36/#565a65 | | **0/0** | dead tokens (C:88–89) |

- **Topic colours** are data, not CSS: `tools/build_stories_feed.py:77–87`, reaching the page as `style="--tc:…"` (H:60,195,310). Values: switzerland #c2454a, geopolitics #c0563b, politics #9a6a34, economy #9a7b2e, ai-ml #2f7d8c, science #4c6b3c, health #a44a72, security #6a4b8a, tech #3b6ea5, sports #c26b2e, world #6b6f76 (also the fallback, :950). They are **single hexes with no dark pair**, and the only consumer is the 7px `.ff-dot` (H:738) and the 6px card dot (H:1285). "Topic-coloured beats" means dots only. Editorial dots have no --tc and fall back to --muted (H:738).
- **Non-token colours:** the sync panel shadow `0 8px 26px rgba(0,0,0,.14)`, and `.55` in dark via a separate `@media (prefers-color-scheme:dark)` (H:763,765). The modal scrim is `rgba(0,0,0,.45)` and its shadow `0 8px 44px rgba(0,0,0,.32)` (H:1695,1699). Hover tint `color-mix(in srgb,var(--ink) 4%,transparent)`, with a `var(--panel)` base on editorials (H:1270–1271). Feature edge `color-mix(… var(--accent) 45%, transparent)` (H:1267). Two rules still use a `prefers-color-scheme` media query instead of light-dark(): H:765 and H:1382.

### 1.2 Fonts
- `--serif: ui-serif,'New York','Iowan Old Style',Charter,Georgia,'Times New Roman',serif` (C:90). Used for body, summaries and editorial heads.
- `--display: 'Anton','Anton Fallback','Arial Narrow','Helvetica Neue Condensed',sans-serif-condensed,sans-serif` (C:94). 'Anton Fallback' must stay ahead of the system condensed faces (C:91–93).
- `--sans: 'Helvetica Neue',Helvetica,Arial,-apple-system,BlinkMacSystemFont,sans-serif` (C:95). Used for labels and UI.
- **Anton** is self-hosted in two unicode-range subsets, `assets/fonts/anton-latin.woff2` (12 KB) and `anton-latin-ext.woff2` (C:236–250). `font-display:swap`. `font-weight:400 900` is a deliberate over-claim that suppresses faux-bold. **Ruling: do not "fix" it to 400** (C:231–235). The URL goes through `relative_url` because the baseurl is `/claude-routines` (C:224–226). The latin subset is preloaded (C:228–229).
- **Fallback metrics** (C:258–273): `local('Arial Narrow'),local('ArialNarrow'),local('Helvetica Neue Condensed Bold'),local('Roboto Condensed')` with `size-adjust:86%; ascent-override:140%; descent-override:39.1%; line-gap-override:0%`. These were fitted to the live corpus of 82 headlines. Values above 88% make it worse (C:263–271).
- No Google Fonts, no third-party font request (C:54–57, ruling).
- `text-rendering:optimizeLegibility; -webkit-font-smoothing:antialiased` on body (C:99). `strong` is weight 600 (C:127).
- **Body line-height 1.5 is inherited from the theme** (MM:111). Nothing on our side sets it globally.

### 1.3 The root font-size ladder (the largest implicit token)
The theme sets `html{font-size:16px}`, 18px at ≥48em (768), 20px at ≥64em (1024) and 22px at ≥80em (1280) (MM:82–88). The page's own breakpoints are 700, 1024 and 1280, so **700–767 is two columns at a 16px root**. Every rem value rides this ladder. Resolved px per band <768 / 768–1023 / 1024–1279 / ≥1280:
- `.6rem` labels (beat, day, rank, line, more, rail edition, sync, propose summary): **9.6 / 10.8 / 12 / 13.2**
- `.72rem` chips (`.ff-chip` H:731, rail beats H:1210, invite H:778): 11.5 / 13 / 14.4 / 15.8
- `.56rem` "Why it matters" label and vote note (H:1479,1615): 9 / 10.1 / 11.2 / 12.3
- `.fcard__sum 1rem` (H:1462): 16 / 18 / 20 / 22. `.fcard.lead .fcard__sum 1.05rem` (H:1463): 16.8 / 18.9 / 21 / 23.1
- `.fcard__deck` 1.05rem, and 1.15rem on a lead (H:1519–1521). `.fcard__why` and `.fcard__edp` .95rem (H:1477,1343): 15.2 / 17.1 / 19 / 20.9
- Editorial headline `1.15rem` serif (H:1452–1453): 18.4 / 20.7 / 23 / 25.3
- `scroll-padding-block-start:6rem` (H:637).

Anything in px or cqi is immune to the ladder on purpose: the display type (H:1384–1388), the rail at 180px (H:1005–1017) and the nameplate (H:1079–1081). **If the theme is dropped, a theme-free rewrite must reproduce this ladder (or convert to px/clamp), or the whole page shrinks up to 27% at ≥1280.**

### 1.4 Type scale
- **Headlines** `.fcard__hl` (H:1423–1427): --display, weight 600, **line-height 1.10**, uppercase, `text-wrap:balance`, --ink, margin 0. Ruling: 1.10 not 0.95 or 1.06, because Anton's Ä/Ü marks reach 1.053em and Å's ring 1.229em (H:1389–1399).
  - Custom props on `.fcard` (H:1422, 1428–1432):
    - below 700: `--hl-brief:1.15rem`, `--hl-feat:24px`, `--hl-lead:30px`
    - ≥700: `container-type:inline-size`, with `--hl-brief:clamp(15px,6cqi,26px)`, `--hl-feat:clamp(20px,8.4cqi,36px)` and `--hl-lead:clamp(28px,9.4cqi,60px)`
  - Tracking: brief .02em, feature and lead .005em.
  - Container queries must stay off below 700. `container-type` there collapsed every module to 1px (H:1408–1413).
- **Age step** (H:1443–1444): `data-age="3"` drops a lead to --hl-feat and a feature to --hl-brief. **Ruling: size only, never opacity or colour for age** (H:1438–1440).
- **Editorial headline**: --serif, italic, no transform, 1.15rem/1.25 (H:1339,1452–1453). **Ruling: never Anton italic**, which would be synthetic oblique (H:1449–1451).
- **Terminal period**: `.fcard__hl--dot::after{content:"."}` (H:1457). The class is computed in Liquid, H:328–336.
- **Headline link**: `color:inherit; text-decoration:none`, and on hover --accent with a 1px underline at 2px offset (H:1458–1459).
- **Nameplate** `.page__title` on home: `clamp(40px,5vw,76px)/.85`, letter-spacing 0, uppercase (H:787–788). The base comes from C:294–295 (display 700, centred, -.015em, margin .3em 0 .12em). C's `font-size:2.7em` is dead on home, because H overrides it.
- **Rail nameplate** (≥1280): `writing-mode:vertical-rl; rotate:180deg`, `clamp(54px,7.4vw,104px)/.85`, -.01em, margin `0 0 .34em -.06em` (H:1084–1087).
- **Tagline**: --sans .8em, .03em tracking, --muted, max 34em, line-height 1.5 (C:296–297).
- **Label voice** (the page's one small-caps idiom): --sans, .6rem, weight 700, uppercase, letter-spacing .1–.16em, --muted or --muted-ui. See `.ff-lbl` H:730, `.fcard__beat` H:1279, `.fcard__day` (--ink, tabular) H:1291, `.fcard__rank` H:1301, `.rail-title` H:1091, `.propose__s` C:318–320.
- **Body copy**:
  - summary: --serif 1rem/1.5 at `opacity:.9` (H:1462)
  - deck: 1.05rem/1.45, lead 1.15/1.4 (H:1519–1521)
  - why: .95rem/1.5 at opacity .88, with a `2px solid --accent` left rule and 10px padding (H:1477–1478)
  - editorial paragraph: .95rem/1.55 (H:1343)
  - rail note and index: .75–.78rem/1.45 (H:1121,1182)
- **Footer line**: --sans .6rem .04em --muted, with a --hair top rule and 9px padding-top (H:1589–1590). The source is lowercase in --red (H:1594). The date is tabular and pushed right (H:1598). "Just in" is --red 700 uppercase .08em (H:1602).

### 1.5 Spacing and rules
- Column: `inline-size:min(1680px,100%)`, `padding-inline:1em` (H:649–650).
- **Zero-gap rule system** (H:858, 863–874, 1247–1248). Each module paints only its `border-block-start` and `border-inline-start` (1px --rule), and the grid closes the end edges. **Ruling: --rule, not --hair, for module edges.** Hover is a tint, never a transform lift (H:1268–1269).
- Module padding `17px 18px 16px`, lead `22px 22px 20px`. Inner flex column, gap 9px (H:1253–1259).
- Board padding `22px 0 10px`, and `14px` top at ≥1280 (H:827,820).
- Radius is **2px everywhere** (H:742, 758, C:332–336). The only exception is `.fb-btn`'s base 6px (C:31), which the propose form overrides to 2px (C:347).

### 1.6 Tier visual language (one vocabulary, three render sites, H:1123–1181)
- **Glyph box**: 9×9px `.tier-key` with the shape drawn by `::before`. Keyed on `[data-imp]` across `.fcard__rank`, `.rail-index dt` and `.ff-li` (H:1142–1146).
  - **Lead** (3): 8px **red disc** (H:1149–1150)
  - **Feature** (2): 7px **ink square** (H:1152–1153)
  - **Brief** (1): 9×2px **--rule dash** (H:1157–1158). Ruling: not a hollow square.
  - Ruling: shape carries the tier and colour is a second channel (H:1133–1135).
- **Tier word is real text** in `.fcard__rank`, never `::after` (H:1295–1300). It is plain muted small-caps, with no box on tiers (H:1313–1316).
- **Module edges**: lead `box-shadow:inset 0 3px 0 var(--accent)`, feature `inset 0 2px 0` at 45% accent, brief nothing. The edge is an inset shadow so the shared 1px rule stays uniform (H:1260–1267). Note that `.lead` comes from `s.is_lead` and the glyph from `data-imp` (H:309,323). Two keys drive one tier.
- **AI editorial**:
  - outlined chip, `border:1px solid --ink`, --ink text, 2px radius (H:1321)
  - `--panel` fill and `inset 0 2px 0 var(--ink)` edge (H:1338)
  - **no glyph on the card** (ruling, H:1159–1163); the rail index draws a 9×6 outlined box (H:1171–1172)
  - the disclosure `.fcard__eddisc` has a --hair under-rule. **Ruling: the disclosure never hides, in any fold or read state** (H:1554–1558, 1586–1588).
- **Read ✓ legend**: an 8×4 rotated L in --accent (H:1179–1181).

### 1.7 Image treatment (`.fimg`, H:1378–1382; JS inserts it at H:2637–2646)
- Slot rule: `height:clamp(120px,22cqi,260px); width:100%; object-fit:cover; object-position:50% 18%`, `1px --hair` border, --panel background.
- Filter: `grayscale(1) contrast(1.08)` in light and `grayscale(1) contrast(1.06) brightness(.9)` in dark.
- **Ruling: slot, not aspect ratio. Type leads, and the image goes AFTER the deck or headline** (H:1349–1366, JS H:2640–2645). **The 18% crop bias was chosen against live faces.** A bad crop is fixed by moving the bias, never by a taller slot (H:1367–1377).
- Only lead and feature cards get images (`data-ogurl` when importance>1, H:309). arXiv cards are skipped.

### 1.8 Read state, focus, motion
- **Read**: headline, summary, why, editorial paragraphs and disclosure at `opacity:.58`, image at `.5` (H:1571–1574). The toggle turns --accent (H:1569–1570). **Ruling: reading dims and NEVER hides or resizes** (07-26 night, H:1575–1588). **Conflict:** the rail copy still says Read "Collapses to its headline" (H:229) and "a story you've read … shrinks" (H:238). That contradicts the later ruling. Flag it to the owner or fix the copy.
- **Focus**: `2px solid var(--accent)`, with offset -2px (in-bar buttons), 1px (fields, read toggle) or 2px (everything else) (H:1621–1628, C:36–39). **`.ff-chip` has NO focus-visible rule.** Its only ring is the theme's `button:focus{outline:5px auto #6f777d; outline-offset:-2px}` (MM:80), which also fires on mouse click in Chrome. Nor does `.fcard__hl a`, `.ff-skip` (it has a visible state only) or `.rail-review` (colour only, H:1197).
- **Motion**: `.fcard__in` background .18s, chips .15s, `.fcard__fb` opacity .15s (H:733,1254,1605). Reduced motion kills two of them (H:1666). Theme transitions are neutralised in C:123–126 (see §3).
- **Feedback row**: `opacity:.42`, 1 on card hover or focus-within, .82 on `(hover:none)` (H:1604–1607).

---------------------------------------------------------------------------------------------------
## 2. Layout mechanism today

### 2.1 Shell (H:615–658)
- `body.layout--home` is a flex column. `min-block-size:100dvh` beats the theme's `body{min-height:100vh}` (MM:647) at (0,1,1). `padding-inline:env(safe-area-inset-left/right)`.
- Children in DOM order: `a.ff-skip` (fixed), `nav.folio-filters`, `header.shell__head`, `main#main.shell__main`, `footer#footer.page__footer`, the `.hiw` modal and scripts (H:49–432).
- `#main.shell__main` is `display:flex; column; flex:1 0 auto` with a definite `inline-size:min(1680px,100%)`. The definite size is needed because the theme's `#main{margin-inline:auto}` would shrink a flex item to fit-content, which measured 305px in a 500px viewport (H:640–650). `max-inline-size:none` beats the theme's `#main{max-width:1280px}` (MM:645).
- `.folio-board{flex:1 0 auto}` lets an empty board fill the screen (H:658, 1653–1665).
- Viewport meta `width=device-width, initial-scale=1, viewport-fit=cover` is emitted at H:39, after the theme's `head.html`, so it replaces the theme's.

### 2.2 Control bar `nav.folio-filters`
- **<700**: `order:1` (last in the flex column), `position:sticky; inset-block-end:0; z-index:20` (H:630). It is one nowrap row with `overflow-x:auto`, scrollbar hidden (H:679–689). Padding is `8px 12px max(8px, env(safe-area-inset-bottom))` (H:685). Also:
  - `.ff-lbl` is hidden
  - `.ff-read` and `.ff-sync` are reordered to the front with `order:-2/-1` (H:690–693)
  - `html{scroll-padding-block-end:4.5rem}` (H:633)
  - the full-bleed bar has a `--rule` top border
- **≥700**: `order:0`, sticky `inset-block-start:0`, `inline-size:min(1680px,100%)`, wrapping, `overflow:visible`, padding `12px 1em 8px`, --hair bottom border (H:634–638, 712–719). `scroll-padding-block-start:6rem`.
- **≥1280**: the bar hides its chips, `.ff-lbl` and `.ff-legend`, because the rail carries them (H:1070). `.ff-legend` is also hidden below 720 (H:751).
- The beat chips are **rendered twice**, once in the bar (H:58–61) and once in the rail (H:193–196). There is one JS state for both, and exactly one set is visible (ruling, H:177–185).

### 2.3 Masthead
`header.shell__head` holds the h1, the tagline and a How-this-works button, and it scrolls away. At ≥1280 the h1 is visually hidden with the clip pattern and the others are `display:none` (H:801–821). **Ruling: exactly one h1.** The rail nameplate is an aria-hidden span (H:134–141, 793–797).

### 2.4 Board and rail
- `.folio-board` is a flex column below 1280 (H:827). At ≥1280 it becomes `grid-template-columns:180px minmax(0,1fr)` (H:1019). **Ruling: the rail is 180 fixed px, not rem** (H:1005–1017).
- `.folio-rail` is `display:none` below 1280 (H:969). At ≥1280 it is `position:sticky; top:55px; max-block-size:calc(100dvh - 71px); overflow-y:auto; align-self:start`, padding `0 20px 24px 0`, with a --rule end border (H:1054–1059).
- **Ruling: `overscroll-behavior` must NOT be `contain`.** That was the double-scroll bug, and the harness asserts it (H:1041–1047).
- Rail order (ruling, H:143–157): nameplate, then edition, then How-this-works, then review link, then the beat list, then a `<details>` index with the rule note.

### 2.5 Story sheet `ol.folio-grid` (a CSS grid plus a JS row-span "masonry")
- Base (H:857–879): `display:grid; gap:0`. One column below 700, `repeat(2,1fr)` at ≥700, `repeat(3,1fr)` at ≥1024, and `repeat(12,minmax(0,1fr))` at ≥1280 with every `.fcard{grid-column:span 4}` (H:971–972).
- `list-style:none; margin:0; padding:0`, plus `li{margin-bottom:0}` to beat the theme's `ul li,ol li{margin-bottom:.5em}` (MM:135).
- **Composed top band** (explicit `grid-area` on `:nth-child`, all scoped to `:not(.is-filtered)`, H:941–977):
  - 700–1023: rank 1 at `1/1/2/3` (full width), rank 2 at `2/1/3/2`, rank 3 at `2/2/3/3`
  - 1024–1279: rank 1 at `1/1/2/4` (full width)
  - ≥1280: rank 1 at `1/1/2/13` (full width)
  - Filtered: `grid-area:auto; grid-column:span 4` (H:976)
  - The dominant's summary is set in 2 columns at ≥700 (H:1227–1229)
  - **Rulings: `grid-auto-flow:dense` and `order:` are BANNED on the grid, and DOM order equals rank** (H:894–895, 1473–1474)
- **Row-span packing** (H:881–919, JS H:1800–1925):
  - JS measures each visible module with `.packing{align-self:start}`, adds `.packed{grid-auto-rows:4px}`, and writes inline `grid-row: auto / span ceil((h+gap)/(4+gap))`
  - It is inert below 2 tracks (H:1836–1840)
  - Runs: a provisional pass at 2.5s, a corrective pass on `document.fonts.ready` (H:1904–1924), a width-only ResizeObserver (H:1885–1901), `schedulePack(0)` on filter (H:2055), `schedulePack(60)` after each og-image insert (H:2656), and inside `anchored()` (H:1941–1944) for fold, vote-reason and roam changes
  - I verified in a synthetic headless repro (12 tracks, span-4, 4px rows, 80 random heights; `scratchpad/understand/lanes2.html`) that sparse auto-placement then behaves as **exact greedy first-free-lane masonry in DOM order**: lanes aligned at 0/400/800, 0 voids, 0 cards starting above an earlier-ranked card, row-major order equal to rank
- **Fold** (`.is-folded`, H:1518–1524, 1559): whole-element `display:none` of the summary. Briefs also hide `.fcard__why`, and editorials hide `.fcard__edp`. **Ruling: never crop, no line-clamp or ellipsis anywhere; element-level disclosure only** (H:1532–1542). **Ruling: expansion is height-only, never wider** (H:978–1004).
- **Empty state**: `li.folio-empty` must be the last grid child, `grid-column:1/-1; align-self:start`, and may set no `display` (H:1630–1652, 376–388).
- **Crop marks** `.ff-crop.tl/.tr/.bl/.br`: 14px L-shapes at ±6px outside the board, hidden ≤640 (H:829–834, markup H:122). This is decoration, part of the journal look.

### 2.6 Breakpoints in use
Page: 640, 680 (C:187), 699/700, 720, 900, 1023/1024, 1279/1280.
Theme root ladder: 768, 1024, 1280.
That makes 10 distinct thresholds. 700–767 is a hybrid band (§1.3).

### 2.7 Why zones overlap or look disordered
A. **Days interleave with no boundary. This comes from an OWNER RULING, so it is a conflict to hand to the owner, not a bug to delete.** H:881 labels the row-span band "owner ruling, 2026-07-25; PLAN v2 section 10". It asks for masonry-tight packing, with slack bounded by the unit instead of the 923px maximum that band stretch left (H:884–889, 907–912). Today's request for "clear content zones that can't overlap" conflicts with it: tight single-grid packing is exactly what makes day blocks interpenetrate. The owner must choose between them, for example tight packing inside a per-day zone.
- Which lane a card lands in is decided by its height, via the first free lane. The next day's first card can therefore sit beside, or start above the bottom of, the previous day's last cards in other lanes.
- The day marker is only a label inside the card's meta row (`.fcard__day`, H:1286–1292). Liquid H:312–317 concedes there is "no shared row line".
- An editorial "closes its day" in rank (H:255–258) but can visually sit beside the next day's stories.
- A left-to-right sweep does not follow rank. Rank 6 in lane 1 can sit 4px below rank 5 in lane 3.
- This is the structural reason "content zones" overlap. It is inherent in single-grid masonry, not a bug in the code.

B. **Painted overlap from stale spans.** A span is a snapshot, and when content grows past its span it overflows into the next module's rows (overflow is visible and nothing clips). Windows:
- (i) before `fonts.ready` resolves, spans are measured against fallback metrics (2.5s provisional pass, H:1904–1923)
- (ii) the 60ms between an og-image insert (H:2646) and the repack (H:2656); each insert adds 129–269px (H:2647–2655)
- (iii) the frame between `apply()` toggling `.is-filtered` and `schedulePack(0)`. The dominant drops from 12 to 4 tracks but keeps its old span (H:2045–2055)
- (iv) any height change that does not change grid width. A user text-size or zoom change that keeps the width is ignored by the width-only observer (H:1894–1896)
- (v) no ResizeObserver: no repack on resize at all (H:1891)
- (vi) any future height-changing interaction that forgets `anchored()`. The vote-reason field already did this once (H:1937–1938).

C. **Intended overlays**:
- the sticky bar covers the bottom card mid-scroll below 700, by design (H:612–614)
- the sync dropdown is absolute, z 30 (H:762)
- the modal is fixed, z 9999 (H:1693)
- the skip link is fixed, z 40 (H:725)
- the crop marks are absolute at -6px

D. **Magic numbers coupling two zones.** The rail's `top:55px` and `calc(100dvh - 71px)` assume a 47px bar (H:1054–1057), and the comment at H:1037–1040 names this as the last viewport number. If the bar grows, the bar (z 20) covers the rail's top.

E. **Absolute track numbers in `:nth-child` placement leak across breakpoints.** They already did once: rank 3 was clipped to one track of 12 (H:934–940). This is why each band is range-bounded.

F. **Sync panel clipped below 700 (bug).** `overflow-x:auto` (H:686) computes `overflow-y:auto`, so the absolutely-positioned panel is clipped. The panel opens upward (`bottom:calc(100% + 9px)`, H:695) from `.ff-sync` inside the scroller. I confirmed this in a minimal headless repro (`scratchpad/understand/clip.html`: `elementFromPoint` inside the panel returns HTML and overflowY is `auto`), but not on the deployed page. The JS does not reparent it (H:2482–2487).

G. **Dead `.on` marker.** `.folio-grid.on` is added by JS (H:1795) but no CSS consumes it. The comments claiming it "gates interactive skins" (H:1235–1237, 1243–1244) are false.

---------------------------------------------------------------------------------------------------
## 3. Theme-fight inventory

**Rules that exist only to beat or neutralise MM:**
1. `body.layout--home{display:flex;margin:0;min-block-size:100dvh}` beats `body{display:flex;min-height:100vh}` (H:615–623 vs MM:647)
2. `#main.shell__main, .page__footer{animation:none}` and `#main.shell__main::after{display:none}` beat the intro animation and clearfix (H:626–627 vs MM:643–644, 429)
3. `max-inline-size:none`, the definite `inline-size` and padding on `#main` (H:649–650 vs MM:643,645)
4. `.folio-grid{list-style:none;margin:0;padding:0}` and `.folio-grid > li{margin-bottom:0}` (H:862,875 vs MM:135)
5. `.ff-spanel[hidden] …{display:none}` re-asserted (H:768). This is a self-inflicted UA fight, not the theme.
6. `.rail-review:visited` (H:1198) and `.hiw-read a:visited` (H:1765) beat `a:visited{#4e91a5}` (MM:130)
7. `.hiw-architecture{display:block}` and `img{margin:0;border-radius:0}` beat the flex-row `figure` (H:1712–1718 vs MM:137–139)
8. C:98–103 re-paint `html,body,#main,.initial-content,.page,.archive,.masthead,.greedy-nav…,.sidebar,.toc__menu,.notice*` with tokens
9. C:123–126 kill the `transition:all .2s` on `b,i,strong,em,blockquote,p,q,span,figure,img,h1,h2,header,tr,td,.highlight,.archive__item-teaser` and re-declare `a`'s transitions (vs MM:156)
10. C:146–157: heading re-ink, plus `.page__title a, .page__title a:visited{color:var(--ink) !important}`. This is the **only !important** in either file (C:157), and it serves evaluator and prompts pages, not home.
11. C:167–170 `.page__content code.highlighter-rouge{background:transparent}`
12. C:176–185 re-skin the theme tables
13. C:202–205 re-skin the footer (MM:429–438)
14. C:321–324 and H:1098–1112: the details-marker kill. This one is UA, not theme.
15. Font-family on every button and input. MM:164 forces the theme's sans on `input,button,select,textarea`, so every control re-declares `font-family:var(--sans)`.

**Bleed that is NOT fought today** (live defects the rewrite fixes by dropping MM):
- `form{padding:1em;margin:0 0 5px;background-color:#f2f3f3}` (MM:157). `.propose__form` overrides the padding (C:331) but **not the background**, so a light-grey slab shows behind the open form in dark mode. I read this from the CSS and did not render it.
- `input,textarea{margin-bottom:.5em; box-shadow:0 1px 1px rgba(0,0,0,.125)}` (MM:168) and `input:focus{box-shadow:… 0 0 5px …; outline:0}` (MM:187) reach `.propose__topic`, `.propose__detail`, `.ffs-invite` and `.ffb-rzn input`.
- `a:focus,button:focus{outline:5px auto #6f777d; outline-offset:-2px}` (MM:80) is the **only** focus ring for `.ff-chip` and the headline links, and it also shows on click.
- `::selection{color:#fff;background:#000}` (MM:91) is black-on-dark-paper in dark mode.
- `figure img{transition:all .2s}` at (0,0,2) beats C's `img{transition:none}` at (0,0,1) on the modal diagram (MM:139). `input` and `form button` keep `transition:all` (MM:156), which C:123 does not list.
- `ul li{margin-bottom:.5em}` applies to `.hiw-stats li` and `.hiw-principles li` (H:1743,1754 vs MM:135).
- `h1..h6{margin:2em 0 .5em;line-height:1.2;font-weight:bold;font-family:theme sans}` (MM:113–119). `.fcard__hl` and `.hiw__*` override it, but any new heading inherits it.
- `p{margin-bottom:1.3em}` (MM:121). Every `p` in H re-sets its margin. The fallback `<p style=…>` at H:392 does not.
- `.page__footer{float:left;width:100%;margin-top:3em;background:#f2f3f3}` (MM:429). The float is ignored as a flex item, but the 3em top margin is live.
- `html{position:relative;min-height:100%}` (MM:110).
- The root ladder, 16→22px (MM:82–88). It is load-bearing (see §1.3), not just bleed.
- JS: C:13–23 stubs `.page__content` because the theme's `main.min.js` throws without it. H:2730–2732 notes that `scripts.html` still loads main.min.js "for nothing".

**If the theme is dropped** from home (H already owns `<html>` and `<body>` and only calls `head.html`, `footer.html` and `scripts.html` by name, H:3–27):
- In H: about 25 code lines go, plus **~3–4 KB of justification comments** (the shell and figure rationales).
- In C: about 90 of 139 code lines go. That is everything `.page__*`, `.archive__*`, `.greedy-nav`, `.masthead`, `.sidebar`, `.notice`, tables, footer and transitions.
- **But C:98–205 also serves `prompts.html` and the evaluator posts** (`layout: single`, still themed) and admin. It can only be deleted if those pages are rewritten too, or if it is split into a themed-pages sheet.
- Net for home: roughly 15–20% of the combined CSS code, plus the root-ladder decision.

---------------------------------------------------------------------------------------------------
## 4. Dead or mechanics-only CSS vs. design decisions

**Delete in a rewrite (mechanics, dead or stale):**
- MECHANISM ONLY: `.folio-grid.packed`, `.packing` and the row-span JS (H:918–919, 1800–1925), plus `anchored()`'s repack coupling. **The OUTCOME is an owner ruling (H:881) and stays a requirement:** neighbours stack independently, and a panel carries only unit-sized slack, never band-stretch voids. A replacement must still meet that, and it must be reconciled with per-day zones (see §2.7A).
- Composed-band `:nth-child` grid-area rules and `.is-filtered` fallbacks (H:941–977), if the new structure composes the top band explicitly (a separate lead zone).
- `.ff-spanel` media flip (H:695) and the upward-open hack. Redesign it, since it is also buggy (§2.7F).
- The ≥1280 masthead-hiding block and its spacing zeroing (H:801–821), which exists only because the header and the rail duplicate each other.
- The rail's magic sticky numbers (H:1054–1057).
- The `.hiw-open--rail` source-order fix (H:1678–1690), which exists because the same control is rendered twice.
- Dead tokens `--accent-chip`, `--accent-chip-hover` (C:88–89). `--card` is kept only for the sync panel.
- `.folio-grid.on` marker (H:1795): no consumer.
- `.layout--home .page__title{font-size:2.7em}` in C:294 is overridden at H:787.
- Stale comments that **contradict code**. Designers should treat the code as truth:
  - H:836–837 and JS H:1795 ("switches to absolute placement"): there has been no absolute placement since 07-25
  - H:1238–1244 ("No layout JS remains"): false, the packer is at H:1800–1925
  - H:950–953 ("dominant upper-RIGHT, two bands tall, 5.1× area"): the rule at H:953 is full width `1/1/2/4`
  - H:921–930 ("rank1 at (400,0)") describes the same retired geometry
  - H:959–968 ("8 + 4 split lands rank 2 at tail width"): the rule at H:973 is full width `1/1/2/13`. H:1525–1531 also discusses the 8+4 split
  - H:1464–1474 ("Every card occupies exactly one grid column FOR NOW"): stale
  - H:1445–1448 ("Two lead sizes"): no rule backs it, the cqi clamp replaced it
  - H:665–678 and H:720–724 describe the bar as `position:fixed` or "a grid track" in a "two-track model": it has been sticky in flow since 09-13 (H:598–614)
  - H:1027–1036 ("bar is a track above the scrollport now"): superseded, and the 55/71 numbers were reinstated
  - H:1482–1494 ("clamped last and least"): contradicts never-crop
  - Rail copy H:229 and H:238 contradicts the dims-never-hides ruling (§1.8)

**Owner rulings to carry forward as requirements:**
- masonry-tight packing: no band-stretch voids, slack no bigger than the unit (H:881–912). This conflicts with non-overlapping day zones, so the owner decides (§2.7A)
- D-II: keep all ~80 stories, compose only the top band, **no story cap** (H:921–925)
- the feedback kill switch `.folio-grid.fb-off .fcard__fb{display:none}` (H:2727–2729), driven by `window.__FB.enabled` (C:46). This is behaviour to keep
- never crop, never clamp mid-text; element-level fold only (H:1532–1542)
- reading dims and never hides or resizes (H:1575–1588)
- expansion is height-only (H:978–1004)
- DOM order equals rank; no `dense` and no `order:` on stories (H:894–895, 1473–1474); `order` is fine on the control bar (H:665–667)
- the AI disclosure never hides (H:1554–1558)
- AI editorial gets no card glyph; outlined chip only (H:1159–1163, 1317–1321)
- tier chips demoted to plain small-caps (H:1307–1316)
- every tier folds its body; "Why it matters" stays visible on leads and features (H:1505–1517)
- no editorial peek paragraph (H:1547–1553)
- images are a monochrome capped slot after the headline or deck (H:1349–1377)
- age is shown by size, never by fading (H:1433–1442)
- rail actions go before beats; the index sits in a closed `<details>`; the rail is not overscroll-contained (H:143–157, 198–213, 1041–1053)
- one h1; the rail labels are `<p>` or `<summary>`, never headings, because story headlines are the h2 level (H:187–191, 209–213)
- one beat control state, with only one set visible
- the empty state is a quiet flush-left serif line in the sheet (H:1630–1649)
- the propose form sits behind a native `<details>` in the page foot; its class names are bound by JS (H:403–404)
- tap targets: the read toggle's hit area grows via `::before inset:-6px` (H:1565); `.fb-btn` is at least 44px at ≤680 (C:190)
- the mobile controls sit in the thumb zone at the bottom, with `.ff-skip` as the focus-order compensation (H:660–678, 44–48)
- Safari is handled the documented way: `viewport-fit=cover` plus `env(safe-area-inset-*)` (H:680–685, 34–39). Memory note: never an invented dvh/svh padding
- no third-party fonts; Anton is self-hosted with a tuned fallback
- contrast discipline: 3:1 for rules and controls, 4.5:1 for text (H:868–872, C:82–86, 208)

---------------------------------------------------------------------------------------------------
## 5. Horizontal overflow risks at 390px

- **The bar is `flex-wrap:nowrap`, with `.folio-filters > *{flex:0 0 auto}`** (H:686,689). It is contained by its own `overflow-x:auto`, so it cannot push the page. The side effect is the sync-panel clipping (§2.7F).
- **`.ff-spanel{width:248px}`** (H:762): it fits at 390, but it is positioned `left:0` from a chip that may be scrolled inside the bar.
- **`white-space:nowrap`**:
  - `.fcard__beat` (H:1280), `.fcard__rank` (H:1302), `.fcard__day` (H:1292) are safe, because the parent `.fcard__top` is `flex-wrap:wrap` (H:1278). The editorial kicker is released to `normal` (H:1284).
  - `.hiw-legend > span` (H:1723): short labels inside a wrapping flex.
- **`.fcard__line` is `display:flex` with no wrap** (H:1589). Source, "Just in", date and the ✓ share one row. `.fcard__src{min-width:0}` lets it shrink and wrap internally (H:1594–1597). The date has no `min-width:0` and no nowrap. That is low risk.
- **No `overflow-wrap` or `hyphens` anywhere.** Measured on the current `_data/homefeed.json`: the longest whitespace-free tokens are 35 characters (`reinforcement-learning-on-reasoning`, in a summary) and 29 (`sliding-window/full-attention`). Both contain break opportunities at the hyphen and slash. The longest headline word is `Qwen-Image-2.1` (14 characters). A raw URL or a long unhyphenated token in a summary, editorial or source label would overflow the card (the grid item has `min-width:0`, H:1247) without making the page scroll, because `#main` has padding. That is a latent risk. Add `overflow-wrap:anywhere` on prose.
- **Negative offsets**:
  - `.ff-crop` at ±6px (H:832–833), hidden ≤640
  - `.rail-nameplate` `margin-left:-.06em`, ≥1280 only
  - `.hiw-open{margin:-1.15em auto 2em}` (H:1671), vertical only
  - `.fcard__eddisc{margin:-.1em 0 .9em}` (H:1342), vertical
  - `.fcard__read::before{inset:-6px}` (H:1565), inside an 18px pad
  - None of these reach the viewport edge at 390.
- **No `100vw` anywhere.** The full-bleed bar gets its width from flex stretch, and `body` padding carries the safe-area insets.
- **Fixed widths**: `.hiw__close-end{min-width:88px}`, `.hiw__x` 44px (H:1700–1704). `.hiw-stats` is 3 columns at 390 with 7px padding, `minmax(0,1fr)` (H:1741, 1782). Tight but safe. `.hiw-principles` collapses to 1fr at ≤700 (H:1785).
- **Headline sizes below 700** are fixed (30/24/18.4px), not clamped to width. A 14-character Anton word at 30px is about 190px, so it fits.
- **The theme's `table{display:block;overflow-x:auto}`** (MM:206) is harmless here; there are no tables on home.
- **Measurement caveat** (H:660–661): headless Chrome clamps `--window-size` to a 500px floor. The owner's harness uses an iframe to get a real 390px, and simulator checks are session-Bash only (memory: iphone-simulator-verification).

---------------------------------------------------------------------------------------------------
## 6. Coupling a rewrite must update
- `tools/home_harness.py` (3,354 lines) extracts C's `:root` token blocks by regex (C:67–68, harness :243–250). It embeds the live theme CSS from `THEME_URL` (harness :176–177) and targets about 30 selectors (`.fcard__more` ×20, `.fcard` ×20, `.fcard__sum` ×12, `.folio-filters` ×9, …). It asserts `railTraps`, `railActionsIn` and headline-size invariance under More (H:996–997, 156, 1047).
- `tools/tests/test_liquid_balance.py:12–14,110` reads `home.html` and `folio-grid`.
- JS binds by class: `.propose__form/__topic/__detail/__msg/.fb-btn` (H:403–404), `.fcard`, `.ff-chip` (`allChips()`), `.ff-spanel`, `.fcard__fb` and `.hiw-open`.
- `_layouts/admin.html` consumes C's tokens.
- Editorial lateness: the CSS has no date logic. Ordering comes from `feed.board` (`build_stories_feed.py::build_board`, H:255–258), which is outside this key's scope.
