# Markup audit — _layouts/home.html (1-586, 2686-2767), index.md, _includes/head/custom.html, _config.yml

H = `_layouts/home.html`, C = `_includes/head/custom.html`, B = `tools/build_stories_feed.py`, F = `_data/homefeed.json` (generated 2026-09-24: 80 stories, 83 board items, 3 editorials).

## 0. Document shell (owner rulings to keep)
- The layout owns the whole document (front matter empty, H:1-2). This is a ruling: under the theme's layouts the fixed bar could not see `#footer` and covered its last 40px (H:3-27). Keep it; do not go back to `layout: archive`.
- Theme includes it still calls by name: `copyright.html` (H:29, emitted BEFORE `<html>`), `head.html` (H:32), `footer.html` (H:430), `scripts.html` (H:2765). It deliberately does NOT call `masthead.html` / `skip-links.html` (H:17-23).
- `scripts.html` loads the theme's main.min.js, "which this page uses for nothing"; the only reason C:13-23 stubs `.page__content` is to stop main.min.js throwing (H:2730-2732, C:13-23). Dropping scripts.html is flagged in the code as "the next decoupling step" (H:2731).
- `<html lang>` comes from `site.locale`, which `_config.yml` does not set → always the `en` default (H:30; _config.yml:1-73 has no `locale`). `class="no-js"` (H:30) is removed by the theme's head.html script (theme-side, not in repo).
- `<body class="layout--home">` (H:41). About 20 CSS rules in C and H key on `.layout--home` (e.g. C:294, H:787, H:802).
- index.md is 4 lines: `layout: home`, `title: "News"`, no body (index.md:1-4). So `{{ content }}` (H:119) is always empty.
- The document scrolls; there is no scrollport element (H:96-100, 2026-09-13). The bar is `position:sticky`, not fixed (H:11-12, H:52-55). A two-track grid shell was tried and sized to the wrong viewport on iOS (H:11-12).

## 1. Zone map (DOM order)

| # | Zone | Element / classes (file:line) | Content | Landmark today | Should be |
|---|---|---|---|---|---|
| 1 | Skip link | `a.ff-skip[href=#folioGrid]` H:49, only when stories exist | "Skip to the stories" | — | keep; must stay first focusable (H:43-48) |
| 2 | Control bar | `nav.folio-filters#folioFilters[aria-label="Filter the stories"]` H:56-93 | label `span.ff-lbl` "Beat" H:57; "All N" chip + one chip per `feed.topics` H:58-61; read-state group `span.ff-read[role=group]` H:62-66; sync widget `span.ff-sync#ffSync[hidden]` H:67-84 (button + panel: passkey sign-in, invite setup with password input, signed-in "who"/sign out, live status `p.ffs-status`); tier legend `span.ff-legend[aria-hidden]` H:88-92 | `navigation` | Filters are buttons that filter in place, not links, so this is not navigation. Better: `<search>` or `form`/`section` with an accessible name for the filters, and the sync/account controls in their own group. The legend is decoration. Sticky: bottom edge below 700px, top edge at 700px and wider (H:52-55). |
| 3 | Masthead | `header.shell__head` H:108-116 | `h1#page-title.page__title` = `page.title` ("News") H:109; `p.home-tagline` H:110; `button.hiw-open#hiwOpen` "How this works" + 3-dot SVG H:111-115 | `banner` (header is a body child) | keep `<header>`. Ruling: the masthead scrolls away and is not a track (H:101-107). At 1280px and wider the h1 is visually hidden, not removed (C/H:801-803), and the rail repeats the nameplate. |
| 4 | Main | `main#main.shell__main` H:118-416 | everything below | `main` | keep |
| 5 | Board wrapper | `div.folio-board` H:121-390 | 4 corner crop marks `span.ff-crop.{tl,tr,bl,br}` H:122 (empty decorative spans), the rail and the grid | none | a layout div is fine; the crop marks should be pseudo-elements or CSS |
| 6 | Rail (1280px and wider only, `display:none` below: H:969, H:1054) | `aside.folio-rail` H:132-240 | nameplate `span.rail-nameplate[aria-hidden]` "News" (hardcoded, not `page.title`) H:141; `p.rail-edition` = `feed.stories.first.date_label` H:142; second `button.hiw-open.hiw-open--rail` H:161-165 (no id); `a.rail-review` to the newest evaluator post, "Weekly pipeline review · D Mon" H:173-176; beat group `div.rail-beats[role=group][aria-label="Filter by beat"]` with `p.rail-title` "Beat" and a SECOND full chip set H:186-197; `details.rail-d > summary.rail-title.rail-s#railIndexTitle` "How to read this page" H:214-215, holding `dl.rail-index[aria-labelledby]` (5 entries: Lead / Feature / Brief / Read / AI editorial, each `dt[data-imp]` with `i.tier-key`) H:216-232 and `p.rail-note` (the two-sentence rule) H:238 | `complementary`, nested inside `main`, with no name | `<aside aria-label>`; it could sit outside `<main>` as a sibling column. Order ruling: actions (How this works, review link) come BEFORE the beat list, and the harness asserts the offsets (`railActionsIn`, H:143-157). The index stays behind a native `<details>` (ruling 2026-07-26, H:198-213). |
| 7 | Board | `ol.folio-grid#folioGrid[tabindex=-1][role=list]` H:253-389 | one `li.fcard` per `feed.board` item (H:277-375), then the empty state | none (list) | keep `<ol>` (ruling 2026-09-12: DOM order IS the ranking, H:241-252). Keep `role=list`, because WebKit drops list semantics on grid/flex (H:246-247). Candidate: one `<section aria-labelledby>` per day, with a real day heading (see §4). |
| 8 | Day breaks | `span.fcard__day` INSIDE the first card of each date block H:283 / H:318, driven by `data-daybreak` | `day_label` e.g. "Thu 24 Sep" | none; a plain span in the card's top row | Ruling: the day break is typographic and is not a new grid child, because `nth-child(1..3)` composition and the `.folio-empty` last-child invariant count children (H:312-317). A redesign that adds day `<section>`/`<h2>` elements must drop the nth-child band and the last-child rule. |
| 9 | Empty state | `li.folio-empty#folioEmpty[role=status][aria-live=polite][hidden]` H:388 | "No stories on this beat right now." | status | Ruling: it must be inside the board so it opens the empty sheet, not 1.5 screens down under the rail (H:376-387). It must be LAST because of the nth-child band. |
| 10 | No-feed fallback | `p[style=…]` H:392 | "No stories yet — check back after the next brief." | — | inline style should become a class |
| 11 | Propose | `section.propose > details.propose__d > summary.propose__s > span` "Propose a brief" + `form.propose__form[action="#"]` holding `input.propose__topic[name=topic][required][maxlength=300]`, `textarea.propose__detail[name=detail]`, `button.fb-btn[type=submit]`, `span.propose__msg` H:406-415 | page-foot furniture. Ruling: collapsed behind a native details and works without JS (H:395-405). DO NOT RENAME `.propose__form/__topic/__detail/__msg/.fb-btn`, because the handler binds by class (H:403-404, H:2692-2697). Its styles live in C:307-350 | `section` without a name = generic | `<section aria-label>` or `<aside>`; labelled fields |
| 12 | Footer | `footer#footer.page__footer` wrapping the theme's `footer.html` H:429-431 | theme feed link + copyright | `contentinfo` | keep. Ruling: the footer is content in the flow; the sticky bar comes to rest above it (H:418-428) |
| 13 | How-this-works modal | `div.hiw#hiwModal[aria-hidden]` > `div.hiw__box[role=dialog][aria-modal][aria-labelledby=hiwTitle][aria-describedby=hiwIntro]` H:435-540 | close ×, `h2#hiwTitle`, `p#hiwIntro`; `figure.hiw-architecture` with `<picture>` of 4 SVGs + figcaption legend + "Reading the map" H:441-456; `div.hiw-a11y` (visually hidden, H:1731) with `h3` + `ol` of 3 steps H:458-465; `section.hiw-proof` (stats, only if `site.data.stats`) H:467-485; two `section.hiw-contract` with `ul.hiw-principles` (4 items each, SVG icon + strong + small) H:487-536; link to `/prompts/` H:537; `button.hiw__close-end` H:538 | dialog (hand-rolled) | native `<dialog>` + `showModal()`: it gives focus trap, Esc, `inert` background and top layer for free, replacing H:541-585 |
| 14 | Probe overlay | JS-created fixed `div`, only with `?probe` in the URL H:2733-2764 | viewport measurements | — | dev tool; keep or move to a separate file. Note: the query test matches any `probe` substring (H:2737) |

## 2. Card anatomy

### 2a. Story card (`it.kind != 'editorial'`, H:308-373)
```
li.fcard.imp{1|2|3}[.lead]            H:309
  data-topics   = s.topics | join ' '          → beat filter matches(): H:2039
  data-imp      = s.importance                 → CSS type scale, fold boot rule (H:2092), legend swatch keying
  data-age      = s.age_days (clamped 0..3, B:1087) → CSS [data-age="3"] (H:1443-1444), fold boot (age 0 + imp 3 = open)
  data-daybreak = "" if s.daybreak             → CSS day-break styling
  data-deck     = "" if s.deck                 → CSS fold variants
  data-ogurl    = s.url, only if url and importance > 1 → og-proxy image swap (H:2629, H:2675)
  (JS adds: .is-folded, .is-open, .is-read, data-og-done, style.display)
  article.fcard__in[style="--tc:{s.topic_color}"]   H:310
    div.fcard__top                                    H:311
      span.fcard__day  {day_label}  (daybreak only)   H:318
      span.fcard__beat[title="{stream_label} · {date_label}"] > span.ff-dot + {topic_label}  H:319
      span.fcard__rank[data-imp] > i.tier-key[aria-hidden] + Lead|Feature|Brief (Liquid case)  H:323
    h2.fcard__hl[.fcard__hl--dot] > a[href=url][target=_blank][rel=noopener noreferrer] {headline}   H:336
                                     (plain text if no url)
    p.fcard__deck {deck}  (if deck)                   H:344
    [img.fimg is inserted by JS after .fcard__deck, or after .fcard__hl when there is no deck: H:2641-2643]
    p.fcard__sum {summary}  (if summary != "")        H:345
    p.fcard__why > span.fcard__why-lbl "Why it matters" + {why}   (if why)   H:346
    button.fcard__more[aria-expanded=true] > svg + span "More"  (if summary != "")   H:360
    div.fcard__line                                   H:361
      span.fcard__src > [span.fcard__aff {affiliation_label} " · "] {source_domain}   H:362
      span.fcard__fresh "Just in"  (fresh and importance > 1)   H:363
      span.fcard__date {date_label}                   H:364
      button.fcard__read[aria-pressed][aria-label="Mark as read"][title]  ✓ svg   H:365
    div.fcard__fb[data-story={sid|default:id}][data-brief={date}-{stream}]   H:367
      button.ffb-t[data-v=1][aria-label=Useful]       H:368
      button.ffb-t.ffb-down[data-v=-1][aria-label="Not useful"]   H:369
      span.ffb-note[aria-live=polite]                 H:370
      [JS lazily adds span.ffb-rzn > input[aria-label] + button "send", H:2296-2299]
```
Tiers differ only in classes and data values (`imp1/2/3`, `lead`, `data-imp`). The markup is the same for every tier. Lead, feature and brief differences are all CSS plus the JS fold. Brief (imp 1) also hides `.fcard__why` when folded (H:1523-1524). `lead` duplicates `data-imp="3"`, because the builder sets `is_lead = importance == 3` (B:985).

### 2b. Editorial card (`it.kind == 'editorial'`, H:279-306)
```
li.fcard.fcard--ed
  data-topics=""        (EMPTY: any active beat filter hides every editorial, H:2037-2040)
  data-imp="2"          (HARDCODED: never boot-open, see §3)
  data-age={age_days} [data-daybreak]
  data-story="ed-{stream}-{date}"   (read-state key, sidOf() H:1983)
  article.fcard__in     (NO --tc custom property, so .ff-dot takes the fallback colour)
    div.fcard__top > [span.fcard__day] + span.fcard__beat > span.ff-dot + {kicker} + span.fcard__rank[data-imp=ed] "AI editorial" (no tier-key glyph)
    h2.fcard__hl {title}  only if title != blank   H:292 (no h2 at all otherwise; ruling H:287-291)
    p.fcard__eddisc  static AI-opinion disclosure   H:293
    p.fcard__edp {p}  for each paras (raw HTML from B::_ed_inline_html)   H:294
    button.fcard__more   (ALWAYS emitted, even for 1 paragraph)   H:295
    div.fcard__line > span.fcard__date + button.fcard__read  (no source, no fresh)   H:296-299
    div.fcard__fb[data-story=ed-…][data-brief=…]  votes, same as a story   H:300-304
```
`data-story` appears twice (on the li and on `.fcard__fb`). Editorials are left out of the Unread count (H:1998-2006).

### 2c. homefeed.json fields: read vs not read
Top level (F): `generated` NOT read · `count` read (All N, H:58, H:193) · `topics[]` read (`key`, `label`, `color`, `count`, H:59-61, H:194-196) · `editorials` NOT read (the board supersedes it; it is kept for the builder and tests, B:1043-1057) · `stories` read only as a guard (H:49, 51, 120), for `stories.first.date_label` (H:142) and as the `board` fallback (H:277) · `board` read (H:277).

Story item fields (board copy):

| field | read? | where |
|---|---|---|
| kind | yes | H:279 |
| importance | yes | H:309 (class, data-imp, ogurl gate), H:323, H:363 |
| is_lead | yes | H:309 |
| topics | yes | H:309 |
| age_days | yes | H:309 |
| daybreak | yes | H:309, H:318 |
| day_label | yes | H:318 |
| deck | yes | H:309, H:344. **Currently absent from all 80 stories** (it comes from the index overlay, B:971-993) |
| url | yes | H:309, H:336 |
| topic_color | yes | H:310 |
| stream_label | yes (title attribute only) | H:319 |
| date_label | yes | H:319, H:364 |
| topic_label | yes | H:319 |
| headline | yes | H:328, H:336 |
| summary | yes | H:345, H:360 |
| why | yes | H:346 |
| affiliation_label | yes | H:362 (23/80 have it) |
| source_domain | yes | H:362 |
| fresh | yes | H:363 |
| sid | yes | H:367 |
| id | fallback only | H:367 |
| date, stream | yes | H:367 (data-brief) |
| topic_primary | **no** | — |
| permalink | **no** (post pages are unpublished) | — |
| affiliations | **no** (only the joined label) | — |

Editorial item fields: `kind` yes, `age_days` yes, `daybreak` / `day_label` yes, `stream` / `date` yes (ids), `kicker` yes, `title` yes, `paras` yes, `date_label` yes, **`heading` not read** (it is already folded into `kicker`, B:880).

## 3. Liquid logic
- `assign feed = site.data.homefeed` H:42. The guard `feed and feed.stories and feed.stories.size > 0` is repeated 3 times (H:49, 51, 120). Hoist it into one assign.
- Chip loop over `feed.topics`, rendered twice with identical markup (H:58-61, H:193-196). This is a ruling: "the same control rendered twice, never two selectors", and exactly one set is visible (H:177-185). Both sets have the same classes and no ids, so there is no id collision.
- `site.categories.evaluator | first` for the rail review link, `date: "%-d %b"` H:173-176. This relies on `_config.yml` `published:false` plus evaluator posts opting in (_config.yml:33-38).
- `assign board = feed.board | default: feed.stories` H:277. Ruling: this is a failure mode, not a shim (H:274-275).
- `for it in board` + `if it.kind == 'editorial'` branch H:278-375.
- **Headline terminal-period logic in Liquid** H:328-336: strip, `slice: -1`, a check for a closing quote, then `slice: -2, 1`, then the `fcard__hl--dot` class when the headline does not end in ?, ! or `.`. The comment gives the reason: the data stays period-free by spec (H:325-332). **MOVE TO BUILDER**: emit a boolean `hl_dot` (or `hl_end_punct`). Two implementations will drift, and the harness already re-renders strings (B:1090-1093 moved `day_label` to the builder for exactly this reason).
- Tier word `case importance` 3/2/else H:323. Could be a builder field (`tier_label`), but it is trivial.
- `s.sid | default: s.id` H:367. The builder always emits `sid` (80/80), so the default is dead.
- Editorial id `ed-{{stream}}-{{date}}` is composed twice (H:280, H:300). Candidate builder field `sid`.
- `data-brief="{{date}}-{{stream}}"` is composed in Liquid twice (H:300, H:367).
- `ogurl` gate `s.url and s.importance > 1` H:309 and `fresh and importance > 1` H:363 are policy in the template. They belong in the builder (e.g. `show_fresh`, `unfurl`).
- `rail-edition` uses `feed.stories.first.date_label` H:142. This is the newest story's short date, and it duplicates `generated`. Should come from a builder field `edition_label`.
- Modal stats: `site.data.stats` reads `all_time.{stories,since,distinct_domains,editions,tags[...]}` and `dedup.{since,checked,repeats_dropped,ongoing_dropped}` with `date` and `plus` filters (H:467-485). Arithmetic (`plus`) in the template.
- `relative_url` on the 4 SVG diagram URLs (H:443-446) and `/prompts/` (H:537). Story `url`s are absolute and external. No output escaping anywhere: `headline`, `summary`, `why`, `deck`, `title`, `kicker` are printed raw (Jekyll does not autoescape). `paras` are intentionally HTML (B:697). The headline goes into an `href` and the `title` attribute unescaped. Add `| escape` for text fields, or have the builder guarantee escaping.
- Summaries carry inline credibility tags as literal text, e.g. `[single-source].` inside `summary` (F board[0]). The template has no markup hook for these tags.
- **Editorial "late" facts (relevant to the owner's complaint), from markup and data only:**
  - Editorial data lands in homefeed.json in the SAME commit as its post (git log -S: eed8848, 6fa0175, 8bbbb8a), so the builder is not late.
  - The builder's sort key ranks editorials BELOW every brief of their date (B:1025-1062). On its own day an editorial is therefore the last item of its block: board index 12 of 83 for science 09-23, 36 for sports 09-21, 52 for weekend 09-19. Its `date` is the post date, so the next day's daily News edition then sorts above it.
  - The markup hardcodes `data-imp="2"` (H:280). The JS boot-opens only `age 0 && imp 3` (H:2092), so every editorial boots folded: `.fcard--ed.is-folded .fcard__edp{display:none}` (H:1559) shows only kicker, title and disclosure. With an empty title (weekend 09-19, `title: ""`) the folded card has no headline at all.
  - `data-topics=""` (H:280) means any active beat or a roamed prefs filter (`pullTopics` / `seedActiveFromPrefs`, H:2258-2266) hides ALL editorials (H:2037-2040).
  - The editorial article has no `--tc` (H:281 vs H:310).
  - `ED_MAX_AGE_DAYS = 5` (B:795) expires them.
  - Conclusion from these facts: the redesign should give editorials a deliberate slot and visibility, not "last in the date block, folded, filter-invisible". Placement is a builder decision (`build_board`); visibility is a markup and JS decision.

## 4. Accessibility and semantics defects
1. The bar is a `<nav>` holding filter buttons, a sign-in widget with a password field, and a legend (H:56-93). It is not navigation. The bar's chip set has no group or label association: the `span.ff-lbl` "Beat" is not linked (H:57), while the rail copy does use `role=group` + `aria-label` (H:186).
2. Day blocks have no headings or grouping: the date is a `span` inside card 1 (H:283, H:318), so screen reader heading navigation cannot jump by day. 83 flat `h2`s sit under one `h1`.
3. An editorial without a title has no heading (H:292), so it is absent from heading navigation. Neither `article` has an accessible name (no `aria-labelledby` to its h2).
4. `li.folio-empty[role=status]` inside `ol[role=list]` (H:388): a list may contain only listitems, so the role override breaks list semantics. It is also counted as an item when shown.
5. The modal is a hand-rolled dialog: `aria-hidden` toggling on the wrapper, a manual focus trap and no `inert` on the page (H:435-436, H:541-585). A native `<dialog>` removes all of this. The openers use `aria-expanded` together with `aria-haspopup=dialog` (H:111-112, H:161-162), which is redundant for a modal. Only the first opener has an id.
6. Vote buttons keep their state as the class `.on` only, with no `aria-pressed` (H:301-302, H:368-369, JS H:2330, CSS H:1614). The ✓ read button does have `aria-pressed` (H:1993).
7. Every card has its own `aria-live` region (`span.ffb-note`, H:303, H:370): about 83 live regions. One shared status region would be better.
8. Propose form: the fields have placeholders only, no `<label>` (H:410-411). `propose__msg` is NOT a live region (H:412), so "sending… / proposed ✓ / sign in" is never announced. `action="#"` (H:409). `section.propose` has no name (H:406).
9. Sync invite input: `type=password` with a placeholder and `aria-label` only (H:74). `ffs-lnk` "First time? Set up" is a button styled as a link (H:72); acceptable. The `ffs-in`/`ffs-out` divs are unlabelled (H:70, H:78).
10. `button.fcard__more` has `aria-expanded` but no `aria-controls` (H:295, H:360). The body it controls is not a wrapped region: `.fcard__sum`/`.fcard__why`/`.fcard__edp` are siblings, so there is nothing to point at. Proposal: wrap the foldable body in one element, e.g. `div.fcard__body` with an id, or use `<details>`.
11. Headline links open `target=_blank` with no textual or visual indication (H:336).
12. The `title` tooltip is the only carrier of stream + date on `.fcard__beat` (H:319). The ✓ button has both `aria-label` and a `title` in a different case (H:298, H:365).
13. Rail `aside` is nested in `main` with no label (H:132). The nameplate is hardcoded "News" and not `page.title` (H:141). The h1 is visually hidden at 1280px and wider (H:801-803) while a decorative duplicate shows. This is a ruling (one accessible title, H:133-140); keep the principle.
14. Div soup: `div.fcard__top`, `div.fcard__line` and `div.fcard__fb` could be `header`/`footer` of the article (the top row is kicker metadata; the line is byline/date/actions). The date is a `span`, not a `<time datetime>` (H:297, H:364; `day_label` also H:283, H:318). The source is plain text with no link (H:362).
15. Decorative empty spans: `ff-crop` ×4 (H:122), `ff-dot` (H:60, 195, 284, 319), and `i.tier-key` used as a presentational box (`<i>` misuse; H:89-91, 217-230, 323).
16. The `hiw-a11y` transcript is visually hidden (H:458, H:1731). Sighted keyboard users get only the SVG image with alt text. That is acceptable, but the `h3` there is the first h3 in the dialog, before the visible ones.
17. Inline `style` on the fallback `p` (H:392) and inline `style="--tc:…"` custom properties (H:60, 195, 310). The latter are acceptable as data.
18. `<style>`/`<script>` blocks sit in `<body>` (H:541-585, H:587-1789, H:1791-2685, H:2686-2729, H:2733-2764). The kill-switch style block is 2 lines (H:2727-2729).
19. `copyright.html` is emitted between the doctype and `<html>` (H:28-30). It is a comment and harmless.
20. `lang` is always `en` (no `site.locale`), but some story content is non-English sources' titles. Minor.

## 5. Assets and head
- Theme `head.html` (remote, minimal-mistakes 4.26.2; not in repo, so this is unverified locally): SEO/OG tags from `seo.html` (title "{page} - {site}", deduped by JS in C:1-6), feed link, the compiled `main.css`, and the viewport `width=device-width, initial-scale=1.0`. Theme head.html in 4.2x also pulls Font Awesome from a CDN; the page does not use FA. Verify before dropping.
- Viewport override `width=device-width, initial-scale=1, viewport-fit=cover` H:39. Ruling: `env(safe-area-inset-*)` needs `viewport-fit=cover` for Safari's floating tab bar (H:34-38; memory "platform mechanism before invention"). It is a duplicate meta that relies on "later wins". Emit one meta if the page stops using the theme head.
- NOT present anywhere in the repo's layouts, includes or config: `<meta name="theme-color">`, favicon or apple-touch-icon, web manifest, `og:image` / `site.og_image` (grep over _layouts, _includes, _config.yml: no matches). `description` comes from `_config.yml:2`.
- Fonts: Anton, self-hosted, OFL (`assets/fonts/anton-latin.woff2` 12 KB, `anton-latin-ext.woff2` 21 KB, `OFL.txt`). The latin subset is preloaded (C:228-229). Two `@font-face` rules with unicode-range (C:236-250). Owner rulings: `font-weight:400 900` is a deliberate over-claim to stop faux-bold (C:231-235); the metric-matched `'Anton Fallback'` has `size-adjust:86%` tuned on the real corpus (C:251-273); `relative_url` inside `url()` is load-bearing because of the project baseurl (C:224-226). There are no third-party font requests; that is a ruling (C:54-57).
- Font stacks: `--serif` is ui-serif/New York (C:90), `--sans` is Helvetica Neue (C:95), `--display` is Anton (C:94).
- Palette: a single `:root` using `light-dark()` + `color-scheme: light dark` (C:59-96). `tools/home_harness.py` extracts this `:root{…}` block by regex, so do not reformat its delimiters without updating the harness (C:67-68). There is no manual theme toggle. The red is a deliberate light/dark pair for contrast (C:82-87).
- SVG diagrams: `assets/diagrams/how-it-works-{wide,mobile}-{light,dark}.svg` (35-47 KB each), chosen by `<picture>` media queries on `max-width:900px` and `prefers-color-scheme:dark` (H:442-447). The img has alt text and `decoding=async`, but no width/height attributes, which is a CLS risk.
- Inline SVG icons: 3-dot "how" glyph (H:113, 163), chevron (H:295, 360), check (H:298, 365, 528), thumb ×2 per card, rotated for down (H:301-302, 368-369), and 8 modal icons (H:494-532). The thumb path is duplicated 4× in the template and 166× in the rendered page. Candidate: a `<symbol>` sprite with `<use>`.
- og-proxy image swap (JS, H:2620-2676): the markup contract is `data-ogurl` on `li.fcard` (H:309), set only for importance > 1 with a url. arXiv hosts are skipped. It inserts `img.fimg[alt=""][loading=lazy][referrerpolicy=no-referrer]` after `.fcard__deck` or `.fcard__hl` and repacks. Endpoint: `https://og-proxy.khalic-lab.workers.dev/?url=`; sessionStorage key `homeOg:v2:`. The redesign needs a reserved media slot, so the insert does not change geometry after layout (H:2644-2653 documents a 269px / 129px jump).
- External endpoints referenced from the markup scripts: `feedback-sink.khalic-lab.workers.dev` (C:46, H:2694). `window.__FB` is the kill switch (C:42-46). The `fb-off` class hides `.fcard__fb` (H:2728).
- C is SHARED: `prompts.html` and evaluator posts (`layout: single`) and `_layouts/admin.html:11` all include `head/custom.html`. Anything moved out of C must keep those pages styled. C also carries rules for theme pages (`.page__content`, tables, `.archive__*`, masthead; C:98-216) and an emoji-stripping script for `.page__content` h2/h3 (C:275-290) that never runs on the homepage.
- _config.yml: `remote_theme` pinned to 4.26.2 (:6); skin "default" (:7); `timezone: Europe/Zurich` (:10); plugins feed/sitemap/paginate/include-cache (:12-16). `paginate: 20` is unused by the home layout (:18-19). `published:false` for all posts by default (:33-38). `exclude` (:47-73) notes "not bare `index`" (:60), because that would kill index.md.
