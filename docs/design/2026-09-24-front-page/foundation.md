# Foundation: the shared base every layout option is built on

Repo: `/Users/rflnogueira/code/claude-routines`. The audit reports are in `scratchpad/understand/*.md`, and R-numbers refer to history.md.

## 1. Theme: drop minimal-mistakes

Evidence:
- 15 theme-fight rule groups plus 9 unfought bleeds (css.md §3).
- Font Awesome `@latest` loaded twice from jsdelivr for one RSS icon (breaks R23).
- `main.min.js` loaded for nothing (forces the `.page__content` stub and title dedup).
- The root font ladder drives every rem; `/categories/` is a dead link.

The layout name `single` must survive, because it is pinned by `tools/publish.py:182` and `tools/tests/test_publish.py:148`.

Final tree:
```
_layouts/folio.html      shell: doctype, <html lang=en>, head include, <body class="{{page.body_class}}">, content
_layouts/home.html       layout: folio (keeps its filename: test_liquid_balance.py:110)
_layouts/single.html     layout: folio; <article class="prose"><h1>, <time>, content, page.previous/next
_layouts/admin.html      unchanged self-owned doc; include path changes to folio/tokens.html (stage 4)
_includes/folio/head.html    charset, viewport-fit=cover, {% seo %}, {% feed_meta %}, noindex flag, tokens, CSS links
_includes/folio/tokens.html  @layer order statement + tokens + @font-face + window.__FB (the only shared include)
_includes/folio/footer.html  feed link (text or inline SVG, no FA) + copyright
```

After the change:
- **prompts.html** keeps `layout: single`; its `.page__content` prefix becomes `.prose` (dark code slab and kramdown/rouge unchanged).
- **Evaluator posts**: h1, `<time>`, content, prev/next; masthead, read_time and taxonomy link go. The emoji strip moves into single.html behind `{% if page.categories contains 'evaluator' %}`, so /prompts/ headings stop being rewritten.
- **_config.yml**:
  - Delete `remote_theme`, `minimal_mistakes_skin`, `paginate*`, `category_archive`, `tag_archive`, and the post defaults `author_profile/read_time/share/related`.
  - Plugins become `jekyll-feed`, `jekyll-sitemap` and `jekyll-seo-tag`, all Pages-allowlisted.
  - `Gemfile`: drop `minimal-mistakes-jekyll`, `jekyll-paginate` and `jekyll-include-cache`. Add `github-pages` for the Docker build.

Timing: a local `single.html`/`default.html` would hijack themed pages at once, so the shell is named `folio` and `single.html` lands only in stage 4.

## 2. CSS architecture

**Location.** Static files under `assets/folio/css/`, with no front matter and no Liquid.
- The directory avoids the theme's `assets/css/main.css` / `assets/js/main.min.js`.
- Font URLs are relative (`../fonts/…`), so baseurl needs no Liquid.
- Linked with `?v={{ site.time | date: '%s' }}` so CSS never goes stale against new HTML (`max-age=600`).

**Files and layers.** The order is declared once, as the first rule in `folio/tokens.html`:
`@layer reset, tokens, base, layout, components, utilities, state;`

| file | layer | holds |
|---|---|---|
| `folio/tokens.html` (inline `<style>`) | tokens | css.md §1.1 palette verbatim (`light-dark()`), font stacks, Anton `@font-face` ×2 (`400 900`) + `Anton Fallback` metrics verbatim; new `--shadow-pop`, `--scrim`; drop `--accent-chip*` |
| `reset.css` | reset | box-sizing, zero margins, `list-style:none` on `ol[role=list]`, `overflow-wrap:anywhere` on prose |
| `base.css` | base | root size, body `line-height:1.5` (the theme supplied it before), headings, links (no `:visited` recolour), `:focus-visible` = `2px solid var(--accent)` on EVERY control, `::selection` from tokens |
| `layout.css` | layout | shell, bar, rail, day zones, sheets. The only file layout options differ in |
| `components.css` | components | card, chips, tier glyphs (css.md §1.6), image slot (§1.7), sync panel, dialog, propose, footer |
| `utilities.css` | utilities | `.vh` (visually hidden) |
| `state.css` | state | `.is-read` dim (css.md §1.8: opacity only), `[data-js]` gates, `.fb-off` |
| `prose.css` | components | single pages only |

Rules:
- Zero `!important`; layers replace the specificity fights.
- The two `prefers-color-scheme` colour rules become `light-dark()`; the image filter becomes `--img-filter`, set in one dark media block (filters cannot use `light-dark()`).
- `container-type:inline-size` only on definite-width boxes: `main`, each day sheet, cards at ≥700 (the <700 1px collapse, css.md §1.4). Headline `cqi` clamps verbatim.

**Root size.** Replace the theme ladder with `html{font-size:clamp(1rem, .75rem + .78125vw, 1.375rem)}`.
It hits 16/18/20/22px exactly at ≤512/768/1024/≥1280 and respects the user's text size. Fallback for zero drift in 512–768: the stepped ladder verbatim.

**Harness.**
- `tools/admin/harness.py` (`_tokens()` + include regex) repoints from `head/custom.html` to `folio/tokens.html` in stage 4; the tokens file holds no sticky/fixed/100vh/overflow-y, so the banned-token test passes.
- New `tools/tests/test_frontend_static.py` checks:
  - no `!important`, `grid-auto-flow:dense`, `order:` or `position:absolute` in `layout.css`
  - no `https?://` in `assets/folio/**` other than the two Worker hosts
  - `node --check` on each JS module, copied to `.mjs`
  - the token blocks of `head/custom.html` and `folio/tokens.html` are identical until stage 4 deletes custom.html (a drift guard)
- `test_liquid_balance.py` gains `next/*.html` and `edition.json`.

## 3. JS architecture

**Modules.** Plain ES modules in `assets/folio/js/`, loaded by one `<script type="module">`.
- An inline `<script type="importmap">` maps `folio/*` to the `?v=`-stamped URLs, so submodules are cache-busted too.
- No third-party requests.
- A 1-line inline head script sets `document.documentElement.dataset.js = ""` before first paint.

| module | job |
|---|---|
| `store.js` | try/catch localStorage; `homeRead:v1`, `syncState:v1`, 45-day prune; `removeItem('siteKey')` |
| `cards.js` | index by `data-story`, `data-edition`; `paintRead` (dims only, R3); derived editorial read (§4a) |
| `filters.js` | one `active` Set + `held`, read-filter `rs`; `apply()` via `hidden` attribute; counts; empty line (R21) |
| `prefs.js` | `topicPrefs:v1`, `/prefs`; TOPIC_CAP 50; fix B8 (never push while `ts===0`) |
| `sync.js` | `syncSession:v1`, passkeys, `/readstate` (`st-` only, B2), 60 s grace, flush on hidden/pagehide; panel = `popover` (unclips css.md §2.7F); B1 fixed |
| `votes.js` | `/submit`, one reason box, `aria-pressed` on thumbs, one shared live region |
| `fold.js` | `<details>` toggle + `anchored()` scroll hold |
| `og.js` | IntersectionObserver `600px 0px`; set `referrerPolicy`/`loading` BEFORE `src` (B6); fills a pre-rendered `hidden` slot |
| `fresh.js` | §4c |
| `dialog.js` | How-this-works as `<dialog>.showModal()`, every `.hiw-open` opener |
| `propose.js` | own entry, no-feed safe; B4, B5 fixed |
| `probe.js` | dynamic import only when `URLSearchParams.has('probe')` |

**Byte-compatible contract** (js.md §1–3):
- Storage keys and shapes stay exactly: `homeRead:v1` `{sid:ms}`; `syncState:v1` `{sid:{ts,v}}`; `topicPrefs:v1` `{topics,rs,ts}` (coerce `rs`, keep held keys); `syncSession:v1` `{token,reader,at}` (tolerate a missing `at`); `homeOg:v2:<url>` in sessionStorage.
- Never reuse `siteKey`, `homeOg:v1:` or `autoPreview:v2:`.
- Ids on the card itself: `li[data-story]` = `{{ s.sid | default: s.id }}` or `ed-<stream>-<date>`; `data-edition` = `<date>-<stream>` (= `/submit` `brief`).
- Request bodies stay exactly: `/prefs` `{topics,rs,ts}`, `/readstate` `{state}`, `/submit` `{brief,vote,reason,story_id,surface:'home'}`, `/propose` `{topic,detail,surface:'web'}`.
- `window.__FB = {enabled,url}` stays in tokens.html for admin. `__syncNudge` is dropped, since propose imports sync.

**No JS.** A correct ranked, dated list; the fold is native `<details>` (boot-open leads baked as `open`). Chips, ✓, votes and sync are `.needs-js`, hidden by `:root:not([data-js])`, so nothing inert renders (NDR R18).

## 4. Editorial fixes (independent of layout)

- **a. Edition read rule** (page only; Playwright). An editorial is read when ticked OR every card sharing its `data-edition` is read; derived at paint time, never stored. "Unread N" = exactly the cards Unread shows; "All N" = board size.
- **b. Beat filters** (builder). Editorial board item `topics` = sorted union of its edition's story topics. Test: `test_editorials.py::test_editorial_inherits_edition_topics`.
- **c. Freshness** (builder + page). Builder emits `feed.edition_key` = `generated` + sha1[:10] of board ids (changes only on a writer publish, not bridge drains). `edition.json` (`layout: null`, `sitemap: false`) prints it; the page bakes `<meta name="folio-edition">`. `fresh.js`, on `pageshow.persisted` or visible after ≥10 min hidden, fetches `edition.json?t=<now>` `no-store`; on mismatch it un-hides a "New edition · Reload" button inside the bar (own space, no shift). Never auto-reloads.
- **d. Titleless** (builder; extractor tests). When `title` is empty, emit `standfirst` = the whole bold lede (leading "1. " stripped) or, with none, para 1's first whole sentence; rendered as the editorial `h3` in the serif italic face. Folded = kicker, title/standfirst, disclosure, More; nothing cropped (R1, R8 intent).
- **e. Sync.** Keep editorial read state local: rule (a) roams it through the stories' `st-` ids. `sync.js` stops queuing `ed-` ids (B2). No worker.js change, no wrangler.

## 5. Builder and data

In `tools/build_stories_feed.py`, keep `board` as the canonical ranking and add a VIEW, `feed.days`:
```
[{date, datetime, day_label, age_step, streams:[{key,label}],
  items:[board stories of that date, board order],
  editorials:[board editorials of that date]}]
```
- Board-only fields: `edition`, `hl_dot` (the terminal-period logic moves out of Liquid), `tier_label`, `show_fresh`, `unfurl`, `standfirst`, and `age_step` (1 when `age_days == AGE_MAX`).
- CSS keys `[data-step="1"]`, ending the `[data-age="3"]` literal coupling.
- `feed.stories` untouched, so **golden-feed.json does not change**.

Deleted after the swap:
- `ED_MIN_BOARD_INDEX` and the push-down loop. No `nth-child` placement survives, and editorials leave the card stream.
- `test_no_editorial_in_the_composed_top_band`.
- The Liquid `board | default: stories` fallback.
- `daybreak` becomes redundant. Keep it until the old page is gone.

The editorial rank-0 sort stays. It is a ruling, and `days` inherits it.

New `DaysViewTest` (dates strictly descending and unique; items + editorials concatenated == board order; each editorial in its own date's day); `test_feed_age` repeats them on the live artifact.

## 6. Verification

- **i. `tools/verify/`.** `package.json` pins `@playwright/test`. `node_modules` is gitignored. It uses public npm, never the spcs node_modules.
  - Input: `_site` from a Docker `github-pages` build, served by `python3 -m http.server`; Workers stubbed with `page.route` (origin lock).
  - WebKit + Chromium at 360/390/430/700/768/1024/1280/1440/1600, light and dark:
    - `zones.spec`: bar, header, rail, day sections, cards, footer rects pairwise disjoint, at boot, all More open, og loaded, each filter.
    - `overflow.spec`: `scrollWidth <= innerWidth`.
    - `order.spec`: DOM `data-story` order == `days` flattening; no card starts above its predecessor; day D+1 below day D.
    - `contract.spec`: legacy shapes seeded (no `rs`, no `at`) restore; written shapes and POST bodies byte-exact; signed out = zero Worker requests.
    - `thirdparty.spec`: only the site and the two Worker hosts.
- **ii. Same-origin preview.** `next/index.html` (`layout: home-next`, `noindex: true`, `sitemap: false`) ships on main beside the old page, so the owner tests passkey, sync, votes and prefs on the real origin.
  - /next/ shares localStorage with /: first load copies the three state keys to new `folioBackup:v1:<key>`. Votes there are real.
- **iii. iPhone simulator** (R17, session Bash only): simctl openurl `…/next/?probe=1`; bottom bar vs Safari's floating bar, chip taps, popover, dialog, scroll restore. Passkeys on the real phone.

Owner: start Docker Desktop, allow `npm i` in `tools/verify`, approve each push, run/allow the simulator pass. No wrangler.

## 7. Rollout

One agent, one worktree, branch `folio`; the main checkout is never touched (bridge pushes local `main` in ≤10 min and auto-stashes). Each stage lands via `git push origin HEAD:main` after suite + Playwright pass and owner approval.

1. Builder views and tests. The old page ignores the new keys. The next News edition fills the data.
2. `/next/` preview: folio shell, `assets/folio/*`, `edition.json`, `tools/verify`.
3. Swap. `home.html` becomes the new page, `/next/` redirects to `/`, and the old CSS/JS and builder workarounds are deleted.
4. Drop the theme (§1). Admin and the harness are repointed, and custom.html is deleted.

Rollback: `git revert <stage sha>` + push. Never force-push. A wedged Pages SHA takes a new commit.

## 8. Risks and owner decisions

1. Drop the theme: evaluator and prompts pages lose the masthead, read_time and pagination chrome.
2. Per-day zones supersede the "masonry-tight" packing (H:881). Confirm.
3. `<details>` fold puts "Why it matters" before the body when expanded. The alternative is a JS button with a no-JS full view.
4. Edition-derived editorial read state, and All/Unread counting editorials.
5. A standfirst heading for titleless editorials (touches R7/R8).
6. D-II is still open: keep all ~80 stories?
7. Fluid root vs the verbatim stepped ladder.
8. Rail copy still says Read "collapses", which contradicts R3. It gets rewritten.
9. Risks: Docker off means production is the first render; import maps/popover need Safari 16.4/17+; /next/ shares localStorage (backup covers it).
