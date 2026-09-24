# history — front-page design history and owner rulings

Scope: `_layouts/home.html` (HL), `_includes/head/custom.html` (CH), `tools/build_stories_feed.py` (BSF),
docs/SPIKE-2026-07-25-front-page-redesign.md (SPIKE), docs/PLAN-2026-07-25-front-page-hierarchy.md (PLAN),
docs/archive/REVIEW-2026-09-13-front-page-ios.md (IOS), docs/archive/REVIEW-2026-07-25-newsdesk.md (NDR),
git log bodies of those 3 files (dumped to `understand/history-gitlog.txt`), auto-memory files under
`~/.claude/projects/-Users-rflnogueira-code-claude-routines/memory/` (MEM:<file>).

**Source tiers.** Each item carries one:
- **OQ**: owner, verbatim quote.
- **OA**: owner-approved or owner-reported, with no verbatim quote.
- **AG**: agent-decided. Designers may revisit.
- **EXT**: external review (NDR, IOS, "GPT Sol").
- **?**: the direction's author is ambiguous.

**Kind.** DESIGN = keep through a rewrite. MECH = tied to the old layout's mechanics and may lapse.

---

## 1. OWNER RULINGS / STANDING DECISIONS

### 1a. Content and hierarchy

| # | Ruling | Date | Source | Tier | Kind |
|---|---|---|---|---|---|
| R1 | **Never crop text.** No line-clamp, no ellipsis, no severed sentence. Whole-element folds behind "More" are allowed, and mid-paragraph truncation is not. | 07-25 | c9f0ec1; HL:1532-1542; PLAN:313; ARCH:1027 | OA ("Owner ruling") | DESIGN |
| R2 | **The front page is an index.** Every lead and feature folds its body. Folded card = headline + [deck] + image + why + More. "Why it matters" stays visible. | 07-25 | fa089d7 §3; HL:1505-1518 | OA ("Rafael has read that live and wants the mock's density") | DESIGN. Keeping "why" visible is AG (fa089d7) |
| R3 | **Reading dims and never hides.** A read card keeps every element at its size, changes only opacity, and never changes fold state. "Do not re-add compaction … without a new explicit ruling." | 07-26 night | 19280f4 (no body); HL:1575-1588, HL:2010-2018 | OQ: "hiding the text for read articles was a bad choice." (quoted HL:1580-1581). Earlier the same day the photo was kept, dimmed (97c5814) | DESIGN |
| R4 | **AI editorial gets NO glyph on the card.** "It is not a tier, it is a disclosure." | 07-25 | 92105c8; HL:1159-1170 | OA ("THE RULING") | DESIGN |
| R5 | **The AI disclosure line never hides**, whether folded, expanded or read. `.fcard__eddisc` appears in no fold rule and no read rule. | 07-25 | 3bc7cd7; HL:1554-1558, HL:1587-1588 | OA ("Ruling granted on a flag I raised twice") | DESIGN |
| R6 | **The AI editorial keeps its boxed chip as an outline, not a fill.** The tier chips are plain small-caps. | 07-25 | 0ba0909 (outline, measured loudest badge); cd2a007 ("approved mock-grammar items"); HL:1307-1321 | OA | DESIGN |
| R7 | **Editorial peek paragraph removed.** Folded editorial = title + disclosure + More. | 07-25 | 3bc7cd7; HL:1547-1553 | OA ("ruling … closing a flag") | DESIGN |
| R8 | **Editorial title = its own opening bold lede, never the scraped section heading.** When there is no lede, or the lede is over 90 characters, emit no `<h2>` (a capped lede would be a crop). The heading moves to the kicker. | 07-26 | a0a5e29; HL:287-292; BSF:755-790 (ED_TITLE_CAP 90) | OA (owner report: a card headlined "Why it matters", HL:262) | DESIGN |
| R9 | **Image discipline: type leads and the photo is a capped monochrome slot.** Slot, not aspect ratio: `height:clamp(120px,22cqi,260px)`, `object-fit:cover`, `object-position:50% 18%`, `grayscale(1)`. Inserted after the headline/deck, never above the headline. No images on briefs, arXiv cards or editorials. "The lever for a bad crop is this, never a taller slot." | 07-25 | 35aeca8 ("Owner rejection of the live page"), 01da4b5; HL:1349-1382 | OA | DESIGN. The numbers are AG |
| R10 | **Tier must read from ONE module on its own.** "just the top border is too subtle". This produced the shape glyphs: lead = red disc, feature = ink square, brief = bare rule. One vocabulary, defined once on `data-imp`, rendered in three places. Colour is only a second channel. | 07-25 | 61330ee; HL:1123-1158 | OQ | DESIGN. The glyph shapes are AG |
| R11 | **Match the mock** ("make it look like this"), a Swiss broadsheet. What actually shipped from it is in §6. | 07-25 | SPIKE:3-6 | OQ | DESIGN (spirit) |
| R12 | **Hierarchy over theme:** "it's not just a matter of theme, the information hierarchy on the page needs to be more prominent." | 07-25 | SPIKE:558-559 | OQ | DESIGN |
| R13 | **Mobile first.** A flattened hierarchy is a list and rank = position. Size, span and bands are wide-viewport projections of that list. One thumb, so controls sit at the bottom on phones. | 07-25 | PLAN:34-37; HL:660-678 | OA ("Mobile-first (Rafael)") | DESIGN |
| R14 | **The goal is to make the owner watch less news, not to add another avenue.** Every surface-adding feature needs an attention justification. | 07-07 | MEM:project-editorial-direction.md:378-384 | OQ | DESIGN (product) |
| R15 | **Expansion must not create "giant lines".** OQ: "the more/less views should expand by taking up spaces adjacent to them instead of making giant lines." Sideways expansion shipped (9fdae92). An AGENT then reversed it to height-only, arguing that "giant lines" was a width problem (f561ecc; HL:978-1004). | 07-25 → 07-26 | 9fdae92, f561ecc | OQ (complaint); AG (reversal) | The complaint is DESIGN. The mechanism is open |

### 1b. Chrome and platform

| # | Ruling | Date | Source | Tier | Kind |
|---|---|---|---|---|---|
| R16 | **Safari's floating tab bar is handled the documented way:** `viewport-fit=cover` + `env(safe-area-inset-bottom)`, accepting that the pill overlays the bar when minimised. Search vendor docs before inventing a mechanism. OQ: "This is a stupid fix, you should have made a simple web search about how to manage the variable island in safari ios, not imagine something new." | 09-13 | b50f26d; HL:34-39, HL:680-685; MEM:platform-mechanism-before-invention.md:101-115 | OQ | DESIGN (process + mechanism) |
| R17 | **Verify phones on the iPhone simulator (real Mobile Safari).** Headless Chrome and the harness cannot see the iOS chrome. | 09-13 | MEM:iphone-simulator-verification.md:127-133; IOS:76-84 | OQ ("good idea to use the iphone simulator") | DESIGN (process) |
| R18 | **The rail must not trap the wheel ("double scroll issue right at the top").** No `overscroll-behavior:contain`. Reference prose sits behind a closed native `<details>`. | 07-26 | b8cf781; HL:198-213, HL:1041-1053 | OQ | Complaint DESIGN; mechanism MECH |
| R19 | **Rail order: nameplate, edition, How this works, weekly-review link, beats, closed reference details.** Controls come before a list that is cut at its tail, measured at the owner's 804px-tall viewport. | 07-26 | 5ae322c ("Director's ruling"); HL:143-156 | ? ("Director" not identified; 3cc4b4d says "Both directed") | DESIGN intent (controls reachable above the fold); order MECH |
| R20 | **No dead band above the sheet.** Spacing must exist FOR something. | 07-25 | fa089d7 §1 ("owner triad … reported together"); HL:805-820 | OA | DESIGN |
| R21 | **An empty or filtered-out board says so on its first line, where the first module would be.** Never a void with no acknowledgement. | 07-25 | dc974e8; HL:376-388 (owner report: signed in, Unread, all read → "full-height black void"), HL:1630-1652 | OA | DESIGN |
| R22 | **The webfont swap must not animate** ("Why does the text animate to a smaller font on load?"). The theme's `transition:all` is killed and the fallback is metric-matched. `font-display:optional` was left pending a ruling. | 07-25 | 2e373e1; CH:111-122 | OQ | DESIGN |
| R23 | **No third-party font requests.** Old Google Fonts "are not coming back". Anton is self-hosted. | 07-06 / 07-25 | 27319f8; 461371c; CH:55-57 | AG, consistent with owner zero-infra | DESIGN |
| R24 | **Affiliation on paper cards is institution-first** (`ETH Zürich · arxiv.org`), names only, no class marker. | 07-10 | SPIKE-2026-07-10-affiliation-element.md:3-5, §6; HL:362 | OA ("§6 decided") | DESIGN |
| R25 | **Read-state sync is opt-in with passkeys.** Signed out means zero sync traffic. Covers read state + votes. | 07-10 | SPIKE-2026-07-07-read-state-sync.md:3-13 | OA ("Rafael … chose passkey") | DESIGN (functional) |
| R26 | **Feedback is per article** ("I MEANT PER ARTICLE OF COURSE"). Reasoned votes are the highest-value signal, including on briefs and editorials. Voting is NOT an implicit read (a reported bug). | 06-19; 07-25 | MEM:project-editorial-direction.md:347; 71d4c56; SPIKE:671-672 | OQ / OA | DESIGN (functional) |
| R27 | **Never a resident server.** Serverless / git / Workers only. | 07-18 | PLAN:226 (I7); MEM:zero-infra-preference.md | OA | DESIGN |

### 1c. Ranking, layout and agent-set parameters

| # | Ruling | Date | Source | Tier | Kind |
|---|---|---|---|---|---|
| R28 | **Position is the ranking and nothing the reader does moves it.** DOM order == rank at every width. `grid-auto-flow:dense` and `order:` are banned on content. No height-driven repacking, including `display:grid-lanes`. | 07-25 | PLAN:220 (I1), PLAN:375-379; HL:238 (rail copy), HL:895, HL:1473-1474; IOS:48 | AG (PLAN), reiterated in owner-facing copy | DESIGN |
| R29 | **PLAN invariants I2–I6.** I2: a correct ranked list with no JS. I3: tier is real text for assistive tech (3281fb9). I4: editorials are never splash candidates. I5: no literal counts in tests. **I6: the story id `hid` is computed from the PARSED lead and must stay byte-stable, or read state breaks** (c169782). | 07-25 | PLAN:218-226 | AG | DESIGN (I6 is a hard data contract) |
| R30 | **Keep all 80 stories and compose only the top ("D-II decided").** CONTRADICTED: the PLAN header updated 08-07 says D-II is still unanswered (PLAN:11-14). See §7. | 07-25 | f81d468; HL:921-924 | ? | Open |
| R31 | **Rail 180 fixed px.** Rem inflation and the 1280 floor arithmetic. | 07-25 | bb6e63c; HL:1005-1017 | AG | MECH |
| R32 | **Full-width dominant (rank 1 spans every track ≥700).** Re-measured after never-crop. The code is full width at HL:945, 953, 973, but comments still describe "upper-right". | 07-25 | 7d710b4, c9f0ec1 | AG | MECH |
| R33 | **Today's leads boot open** (`data-age=0` + `data-imp=3`). Everything else boots folded. | 07-26 | f561ecc; HL:2066-2089 | AG | Open |
| R34 | **Age demotes one type step at `data-age="3"`**, with no opacity or colour ageing (contrast discipline). AGE_MAX stays 3 because CSS keys the literal. | 07-26 / 09-12 | f561ecc; 20e6986; HL:1433-1444 | AG | MECH |
| R35 | **Line-height 1.10 on Anton** for ÄÜÅ diacritic clearance (ZÜRICH headlines). px, not rem. `cqi` module-width sizing. | 07-25 | 8a3f423, cd2a007, 6059e0c ("Approved architecture"); HL:1384-1432 | AG; cqi OA | DESIGN (1.10 floor); sizes MECH |
| R36 | **Red is a light-dark pair (#c8102e / #ff5a5f)**, spent on the source domain, "Just in" and the lead glyph. `--accent` indigo carries structure. | 07-25 | b5dcc8d, cd2a007; CH:82-87; HL:1591-1602 | OA (source red = "approved mock-grammar") | DESIGN |
| R37 | **Beat prefs: held keys survive**, All = replace, client cap 50, non-2xx surfaced. | 07-25 | 54411e3 ("as agreed"); PLAN:189-195 | OA? | DESIGN (functional) |
| R38 | **Semantics:** `<nav>` filters, `<header>` masthead, `<main>` sheet, `<footer>`. The sheet is an `<ol role="list">` of `<li class="fcard">` containing an `<article>`. One `<h1>`. Stories are `<h2>`. No heading in the rail. | 09-12, 07-25 | ff48375, 3a4c2c6, 4c1b799, 751eaff; HL:52-56, HL:187-191, HL:241-253 | AG | DESIGN (matches the owner's "semantic tags" ask) |

---

## 2. FAILED APPROACHES (tried → reverted or abandoned, and why)

1. **CSS-grid row-span masonry v1** (3973b2e, 07-06) left 300px+ voids around 2-column leads. Replaced by a JS packer (c8608ca).
2. **JS absolute-placement masonry packer** (c8608ca, 97cbc8c: notch backfill, tallest-fit, bottom-steal, shift-steal) was DELETED in 9344d2d.
   - It reordered stories by HEIGHT, so position encoded packing rather than rank.
   - Shortening headlines worsened maxGap 186→435.
   - The harness tested none of it for a week (MEM:verify-the-test-tool-first.md:409-415).
3. **Generated halftone "noise plates"** as image stand-ins (27319f8) were dropped for text-only cards (c8608ca).
4. **Natural-aspect og:images** (16:10, and 21:9 on leads; c8608ca) put a 521px full-colour photo with Guardian branding above the headline. The owner rejected it (35aeca8).
5. **Per-tier line-clamps**, the "module diet" (f953e13), were killed by never-crop (c9f0ec1).
6. **Upper-right 8+4 dominant** (f81d468, b8a2448) flip-flopped with a full-width band (7d710b4, c9f0ec1). Full width won because a full-text module in one track is about 1500px tall and pinched rank 2 to a seven-line headline.
7. **Rail `minmax(10rem,13rem)`** inflated with the root font ladder, so the rail ate the sheet. It became 180px (bb6e63c). The first rail commit was reverted and reapplied (b5dcc8d → 862dc90 → b74d064); the collapse was the harness, not the change (be8f9e8).
8. **Grid `align-items:start`** left ragged panels and 480px holes. Switched to stretch (2f7afe3).
9. **`align-self:start` opt-outs for editorials and folded briefs** (e27ebd1, 16ca166) tore the zero-gap rule lines and were reverted (b71be66).
10. **Hover lift `translateY(-2px)`** tore the shared rules. It is now a tint (b71be66; HL:1268-1270).
11. **Sideways expansion on More** (`span 8` + multicol, 9fdae92) manufactured voids and resized headlines through `cqi`. Reverted to height-only (f561ecc).
12. **Read "spine" compaction** (f561ecc → 3cc4b4d → e97b302 → 97c5814) was rejected outright by the owner the same day (19280f4). It also spawned the `foldForRead` seam, which failed 25 of 53 state cells (e97b302).
13. **Editorial placement:**
    - Editorials were rendered FIRST (63683b1). At 390px they stacked to 4104px, and the first news story sat 5.2 screens down.
    - They were then spliced at index 3 (db400ff), which put a six-day-old Sports editorial at position 4.
    - Now they are ranked below briefs in one board (a0a5e29).
    - A 14-day window with a `[:3]` cap was replaced by invariants.
14. **Editorial peek paragraph** removed (3bc7cd7). The **AI-editorial ring glyph** (61330ee) was removed a few minutes later (92105c8).
15. **Tier encoding by top-edge weight** (02a95a4 plus the inset shadow, b71be66) was "too subtle" and became glyphs (61330ee). The filled LEAD/FEATURE chips were demoted to small-caps (cd2a007).
16. **Rail `overscroll-behavior:contain`** (fa089d7) caused the "double scroll". Removed (b8cf781).
17. **"Rail actions above reference prose"** (3cc4b4d) was superseded the same day because the actions were still below the fold at the owner's height (5ae322c).
18. **Bottom bar chain on phones, 07-25 → 09-13:**
    - `position:fixed` + `#main{padding-bottom:58px}`. The reservation could not reach the footer and covered 40px of it.
    - Reservation moved to `<body>` (2192b44).
    - **Two-track body grid + `.shell__view` scrollport** (ff48375, "tracks cannot overlap"). On iOS the body was 100lvh, so the bar sat under Safari's toolbar and the document could not scroll: no collapse, no pull-to-refresh, no scroll restore.
    - Hotfix `min-block-size:100dvh` (11a5b36).
    - Unwound to a scrolling document with a sticky bar (f9cff27).
    - The invented `calc(100dvh - 100svh)` padding was rejected by the owner and replaced with the documented env() handling (b50f26d).
19. **Flex page shell under the theme's `archive` layout** collapsed to about 305px (Flexbox 9.4, auto cross margins; 2192b44, HL:640-648). Resolved by owning the document (ff48375, HL:3-27).
20. Other dropped mechanisms:
    - `min-block-size:40dvh` on an emptied board.
    - A ResizeObserver publishing the bar's height.
    - The `--ff-bar` token.

    All were dropped (HL:696-710, HL:1653-1666).
21. **`tools/home_harness.py`** (a page re-assembled from regex-extracted fragments) was blind many times:
    - it saw only the first `<script>`
    - it rendered no theme CSS
    - it rendered no images
    - it rendered no header or modal
    - it rendered the wrong font face
    - it never rendered a footer

    It was disarmed for good on 09-13 (f778038; home_harness.py:3085). The replacement (Playwright plus the simulator, IOS:61-74) is NOT built: `tools/verify/` does not exist. Rule: "an oracle built after the fix is built to agree with it" (IOS:84).
22. **Design C "rewrite"** (09-13) was rejected (IOS:34-53).
    - `display:grid-lanes` places items by height.
    - It dropped the rail and the composed top band.
    - Its popover and viewport-fit claims were wrong.
23. **Swiss B/W spike §1–§6** was superseded by Amendment A and PLAN v2 (SPIKE:547-550, SPIKE:825-839). Its Stage 9 spec was cut: undefined tokens, and a filler bug that painted over the rules (PLAN:251-254).
24. **Liquid-subset interpreter harness** was cut (PLAN:245-249).
25. **Presentation manifest (D-III)** was never built. Baked slots collide with filtering, so the composition is scoped to `:not(.is-filtered)` (f81d468; HL:1230-1234).
26. **Deck field** (80f2aa3, d7c80c0) shipped but is dead end to end: the record constructor drops it (NDR:100-110). Current feed: 0 of 80 stories have a deck.
27. **Row-span "masonry-tight" band** (17d90d9) is still live: JS measures heights and writes spans, gated by `.packed`. PLAN §10 wanted it conditional (build it only if median slack at 1440 > 150px; 9fdae92 measured 47px, "answered NO"), and 17d90d9 built it anyway. HL:881 labels it an "owner ruling". Status: ? It reintroduces JS-measured layout, the class of which the repo "killed twice" (PLAN:346-350).
28. **Older restyles** (06-19: ae2535a, 1ba5e74, a7e93ed, 82a7fe3) went through Playfair/Spectral, then Fraunces/Source Serif/Inter, then a 58/30 flex split (a7e93ed: "layout disaster … cramped text … postage-stamp image"). All were superseded.

---

## 3. OWNER COMPLAINTS OVER TIME

| Date | Complaint | Source |
|---|---|---|
| 05-31 | "surfacing stuff that i could get from a news aggregator … not very different from just reading hackernews" (editorial, not layout) | MEM:project-editorial-direction.md:219-222 |
| 06-18 | "you forgot to hook up the whole feedback system to the frontend." | MEM:project-editorial-direction.md:326 |
| 06-19 | "I MEANT PER ARTICLE OF COURSE" (per-story feedback) | MEM:…:347 |
| 06-19 | Layout "disaster": cramped column, void, postage-stamp image (commit wording; the source is a design critique) | a7e93ed, 1ba5e74 |
| 06-30 | Dark-mode title invisible (theme link colour bleed) | 4317ee1; MEM:theme-link-color-bleed.md |
| 07-07 | "the goal is to make me watch less news, not another avenue." | MEM:…:378-379 |
| 07-18 | Brief-page widgets misfiring on the evaluator post; editorial sections lost after pages retired | f2b52b7, 63683b1; MEM:retiring-pages-… |
| 07-20 | Modal diagram collapsed (theme `figure` flex bleed) | a3e197b |
| 07-25 | Mock: "make it look like this" | SPIKE:3-6 |
| 07-25 | "doesn't go far enough … information hierarchy … more prominent" | SPIKE:558-559 |
| 07-25 | Rejected the live page: full-colour branded photo above the headline | 35aeca8 |
| 07-25 | "just the top border is too subtle" | 61330ee |
| 07-25 | Never crop text | c9f0ec1 |
| 07-25 | Triad: dead band above the sheet, unreachable rail bottom, wall of text (wants index density) | fa089d7 |
| 07-25 | "the more/less views should expand … instead of making giant lines" | 9fdae92 |
| 07-25 | "Why does the text animate to a smaller font on load?" | 2e373e1 |
| 07-25 | Empty board: black void with no acknowledgement (signed in, Unread, all read) | dc974e8; HL:376-382 |
| 07-26 | Six-day-old Sports editorial at board position 4, headlined "Why it matters" | a0a5e29; HL:259-263; ARCH:979-983 |
| 07-26 | "a double scroll issue right at the top" (rail) | b8cf781 |
| 07-26 | "hiding the text for read articles was a bad choice." | HL:1580-1581 |
| 07-28 | A "Why it matters" opened mid-quotation and looked cropped | ARCH:113-116 |
| 09-12 | "EDITORIALS keep reappearing"; "SPORTS weird stuff" (08-31 results beside 09-11 news) | 20e6986 |
| 09-12/13 | Phone: bottom bar under Safari's toolbar, chips untappable; bar covering the footer | 11a5b36, 2192b44; IOS:21-30 |
| 09-13 | "This is a stupid fix, you should have made a simple web search … not imagine something new." | MEM:platform-mechanism-before-invention.md:101-104 |
| 09-24 | "this sucks"; overlapping zones; "editorials appearing days after they were published" | current request |

External review findings that are still open (EXT, not owner complaints):
- NDR R18 (NDR:306-322):
  - no-JS renders inert More, read and vote buttons, which are still emitted statically at HL:295-304 and HL:360-370
  - targets of 11–23px
  - the mobile visual order ≠ DOM order
  - read dim of 3.68:1, which contradicts the "AA-safe" claim at HL:1572
- IOS S4: the Sync panel is unreachable on phones. The cascade inversion is still present (the phone rule at HL:695 precedes the base rule at HL:762, and `overflow-x:auto` is at HL:686). The fix was planned at IOS:70 and no `popover` is present.
- NDR R5: deck is dead.

---

## 4. LAYOUT EVOLUTION

- **≤06-19:** theme-default edition list. Journal restyles (Playfair → Fraunces → a single column). An extra-wide hero for the latest edition plus a dated list (82a7fe3).
- **07-06 "Folio":** per-story masonry from `homefeed.json`. Importance-sized cards, topic chips, halftone plates, then og:images through og-proxy. The first attempt used CSS row-spans, which were replaced the same day by a JS absolute packer (27319f8, 3973b2e, b14bad9, c8608ca).
- **07-07 to 07-18:** tier chips and edges, local read state, brief fold, passkey sync, prefs roaming. Brief pages retired (07-18), so the feed became the ONLY reading surface. Editorial cards were added (07-18). The packer was hardened with notch/steal passes (97cbc8c).
- **07-25 morning:** editorial demotion. The packer was DELETED and replaced by CSS Grid in DOM order (9344d2d). Zero-gap 1px rule system (b71be66). A composed top band placed by `nth-child` (f81d468). Rail + 12-track sheet at ≥1280 (b5dcc8d …).
- **07-25 afternoon:**
  - self-hosted Anton
  - `cqi` type
  - glyphs
  - the rail becomes the masthead (rotated nameplate) and the beat selector
  - the image slot
  - never-crop
  - folding everything
  - sideways expansion
  - the row-span packer (17d90d9)
- **07-26:** one ranked `feed.board` loop (editorials close their date block), daybreak labels, age demotion, today's leads boot open. The read spine arrived and was reversed. Rail details and ordering.
- **08-07 to 09-11:** no layout change. Prose derivation.
- **09-12:**
  - the page owns its document (no `layout: archive`)
  - landmarks
  - a two-track body-grid shell with a `.shell__view` scrollport
  - the `<ol>` sheet
  - editorials and stories expire by cadence
- **09-13:** iOS failure → min-block hotfix. Unwound to a scrolling document with a sticky bar (bottom edge <700px, top edge ≥700). viewport-fit=cover + env(). Harness disarmed. `?probe=1` readout.

---

## 5. EDITORIALS: placement and timing (pattern, not diagnosis)

The owner has complained about editorials from both directions, and each fix was a constant or an ordering tweak:

1. **07-18:** rendered first and 2-col, excluded from read state, hidden under beat filters (63683b1). Labelled "AI editorial" with a standing disclosure (d4cb38d).
2. **07-25:** "taking the whole front page". This was found by measurement agents (PLAN:152-162), not reported by the owner. Moved to after rank 3; body folded (db400ff).
3. **07-26, owner report:** a six-day-old Sports editorial at position 4, headlined "Why it matters". The fix was:
   - `feed.board` with editorials ranked BELOW briefs, so each closes its own date block
   - `ED_MIN_BOARD_INDEX=3`
   - `ED_MAX_AGE_DAYS=7`
   - an "edition must still have a story on the board" invariant

   (a0a5e29; BSF:1013-1080; HL:254-276)
4. **09-12, owner:** "EDITORIALS keep reappearing". There were exactly 3 editorials on every build for 24 days. Fixed with `ED_MAX_AGE_DAYS` 7→5, which must stay below the weekly cadence (20e6986; BSF:795-806). **ARCHITECTURE.md:983 still says 7, which is stale.**
5. **09-24, owner:** "appearing days after they were published". Not diagnosed here.

Relevant facts:
- Only weekly desks (science, sports, weekend) produce editorials (BSF:803-805).
- One editorial per stream: the latest edition's (BSF:808-).
- Its rank key puts it after every story of its own date (BSF:1034-1036), so today's editorial lands below all of today's stories.
- Current board (`_data/homefeed.json`, generated 09-24): science 09-23 at index 12; sports 09-21 at index 36 (age 3); weekend 09-19 at index 52 (age 3, **empty title**).
- The owner's standing rulings on editorials: no glyph (R4), disclosure never hides (R5), outline chip (R6), no peek (R7), bold-lede title (R8), never in the top band (PLAN I4), read-markable with `ed-<stream>-<date>` ids (715c583) and votable (71d4c56), and excluded from the Unread count (HL:1998-2002).

---

## 6. WHAT SHIPPED FROM THE SWISS SPIKE (so no one assumes the page is black and white)

**Kept:**
- Anton condensed display (self-hosted woff2)
- a red accent as a pair #c8102e/#ff5a5f (not the spike's #d81e05/#ff5c4d)
- the ≥1280 rail with a rotated nameplate and a beat index
- grayscale, capped, cover-cropped images
- a zero-gap ruled grid at **1px `--rule`** (not 2px ink gutters)
- tier index as real text
- source domain in red

**Never adopted:**
- pure B/W tokens. The palette is still bone paper #eceae4 / dark #14151a with an ink-indigo accent #2b3f6b / #8fa9df (CH:70-81).
- retiring beat colours. Topic dots `--tc` remain (HL:60, HL:738).
- the `--muted` = black flattening
- the halftone dot screen and full-bleed image frames
- drop caps
- the numbered THREADS band and SVG marks
- 3px heavy frames and colophon fillers
- the `--rw` tokens

The "dark/paper journal look" the owner wants kept = CH:70-90 + Anton + topic dots + the red pair.

---

## 7. CONTRADICTIONS AND STALE COMMENTS THAT READ LIKE RULINGS (do NOT treat these as requirements)

- **D-II (show all 80 vs about 12 modules).** f81d468 and HL:921-924 say "decided: keep all 80". The PLAN header dated 08-07 (PLAN:11-14) says it is unanswered and awaiting a decision. **Open.**
- **Upper-right dominant.**
  - HL:950-952 ("dominant upper-RIGHT, two bands tall") and HL:959-968 ("the mock's upper-right dominant, now that it fits … 8+4") are stale.
  - The code is full-width at HL:945, HL:953 (`1/1/2/4` of 3 columns) and HL:973 (`1/1/2/13`).
  - HL:1525-1531 says "revisit the 8+4 split" with no current basis.
- **HL:588-596:** the file header still describes "Folio masonry … JS-placed (absolute cards)". HL:836-837 is a stale "absolute placement" note.
- **HL:1461:** "full summary on every card … no truncation". Contradicted by the fold rules at HL:1518 and HL:1523.
- **HL:1493-1494:** "why … is clamped last and least". There are no clamps (R1).
- **HL:124-126 and HL:134-135:** "one h1 supplied by the archive layout". The page no longer uses `archive` (HL:3-27).
- **HL:668-678 and HL:713-715, HL:720-724:** describe the bar as a "grid track". It is sticky since f9cff27.
- **HL:1027-1040:** "offsets measured against the scrollport now (2026-09-12)". Superseded by HL:1054-1057.
- **HL:881:** calls the row-span band an "owner ruling". The commit and PLAN §10 frame it as conditional agent work (§2 item 27).
- **HL:1572:** "keeps AA contrast". NDR:314-315 measured 3.68:1.
- **ARCHITECTURE.md:955:** "per-STORY masonry grid". **ARCHITECTURE.md:983:** `ED_MAX_AGE_DAYS = 7` (code: 5).
- **SPIKE and PLAN status headers:** the SPIKE says "PROPOSED" and PLAN Stages 6–9 are "OPEN" (NDR:334-336). Most of Stages 6–8 did ship on 07-25/26; the header was never updated.

---

## 8. CURRENT-STATE DATA POINTS (data only, not analysed)

- `_data/homefeed.json` (generated 09-24): 80 stories. Tiers are 17 lead, 59 feature, 4 brief.
- 0 stories have a `deck`.
- 83 board items. age_days 0/1/2/3 = 1/12/14/56.
- Date 2026-09-24 has 1 item on the board.
- Editorials sit at board indices 12, 36 and 52.
