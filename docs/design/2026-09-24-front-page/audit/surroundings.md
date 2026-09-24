# Surroundings audit: what the frontend rewrite touches outside `_layouts/home.html`

Repo is `/Users/rflnogueira/code/claude-routines` at `2160514`, audited read-only.
Live evidence was fetched 2026-09-24 and saved next to this file as `live_*.html`:

- `live_.html` is `/`.
- `live_prompts_.html`
- `live_2026_09_20_evaluator_.html`
- `live_admin_.html`
- `live_feed_xml.html`
- `live_sitemap_xml.html`
- `live_robots_txt.html`
- `live_404_html.html`

GitHub facts come from `gh api repos/khalic-lab/claude-routines/pages[/builds]`.

---

## 1. Other pages, and what renders each one

### Site-wide config (`_config.yml`)

- **Theme.** `remote_theme: mmistakes/minimal-mistakes@4.26.2` (:6), skin `default` (:7).
- **Permalink.** `/:year/:month/:day/:title/` (:9).
- **Plugins.** feed, sitemap, paginate and include-cache (:12-16). `paginate: 20` (:18).
- **Post defaults** (:21-38):
  - `layout: single`
  - `published: false` for ALL posts (a 2026-07-18 ruling). Brief pages are retired, and the `_posts/*.md` files must stay because they feed homefeed, stats and the evaluator.
- **Archives.** `category_archive` / `tag_archive` are declared with `type: liquid` (:40-45), but no archive pages exist in the repo (there is no `_pages/`).
- **Excludes** (:47-73). Note `index/stories` rather than bare `index`; bare `index` prefix-matches `index.md` and kills the homepage (:60).

### `/` (`index.md` → `_layouts/home.html`)

- `index.md:1-4` contains only front matter (`layout: home`, `title: "News"`). The layout supplies the whole document.
- `home.html` has no `layout:` front matter (:1-2), so it owns `<html>` (:28-41).
- It still calls four theme includes by name:
  - `copyright.html` (:29)
  - `head.html` (:32), followed by our `head/custom.html` (:33)
  - `footer.html` (:430), inside our own `<footer id="footer" class="page__footer">` (:429)
  - `scripts.html` (:2765)
- **Theme items it does NOT call:** masthead, skip-links, sidebar, breadcrumbs. The rationale is in the comment block at :4-26.
- **Viewport.** A second viewport meta with `viewport-fit=cover` (:39) overrides the theme's. It is required for `env(safe-area-inset-bottom)` (comment :34-38).
- **Live `<head>` of `/`** (`live_.html`):
  - canonical and og:* from the theme's SEO include
  - `feed.xml` alternate link
  - `assets/css/main.css`
  - **Font Awesome from `cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@latest`**, loaded twice (a preload link and a stylesheet link)
  - `assets/js/main.min.js`
  - This contradicts `head/custom.html:54-57`, which claims "no third-party request and no extra CSP surface".
  - The only FA consumer on `/` is the RSS icon in the theme's `footer.html` (`<i class="fas fa-fw fa-rss-square">`, live_.html footer).
- **Footer.** The theme's `footer.html` emits a "Feed" link to `/claude-routines/feed.xml` and "© 2026 News. Powered by Jekyll & Minimal Mistakes." (live_.html). Comment :425-427 says it is "still the theme's to change".
- **Data consumed:**
  - `site.data.homefeed` (:42)
  - `site.data.stats` (:467), from `tools/build_stats.py:2,204`
  - `site.categories.evaluator | first` (:173), which drives the rail's "Weekly pipeline review · <date>" link (:175)
- **Asset links in the page:**
  - `/prompts/` link (:537)
  - `assets/diagrams/how-it-works-{wide,mobile}-{light,dark}.svg` (:443-446). Their Mermaid source is `diagrams/06-public-how-it-works-mobile.mmd`; the `diagrams/` directory is excluded from the build (`_config.yml:70`).

### `/admin/` (`admin.html` → `_layouts/admin.html`, theme-free)

- **`admin.html`:**
  - Front matter at :1-6: `layout: admin`, `permalink: /admin/`, `sitemap: false`.
  - A section skeleton with six ids in a fixed order (:12-…).
  - The comment at :7-9 says every dynamic value is filled by the script after passkey sign-in.
- **`_layouts/admin.html`:**
  - Its own doctype and head (:1-8), with `robots noindex` (:6) and `viewport-fit=cover` (:5).
  - `{% include head/custom.html %}` is its ONLY theme-adjacent include (:9-11).
  - One `<style>` and one `<script>`; both are pinned by a test (see §3).
  - No `main.css` and no `main.min.js`. The live `live_admin_.html` has 5 inline `<script>` tags and no `<link>` stylesheet other than the font preload.
- **Routes it calls** (all under `window.__FB.url`, from `_layouts/admin.html:152`):
  - `/auth/login-options` and `/auth/login` (:193, :212)
  - `/admin/snapshot` (:312)
  - `/admin/actions` (:313, :331, :475, :529)
- **Session.** It copies home's passkey session shape `syncSession:v1` (:151, :157, :189).

### `/prompts/` (`prompts.html`, `layout: single`, theme)

- Front matter at :1-5, `permalink: /prompts/`.
- It pulls in `routines/{news,ai-ml,science,weekend,sports,weekly-evaluator}.md` via `include_relative` (:10-15), even though `routines` is in `exclude` (`_config.yml:69`). It works: live `/prompts/` is 313 KB.
- **Constraint:** `include_relative` resolves against the page's own directory, so `prompts.html` must stay at the repo root. Moving it into `_pages/` breaks the paths.
- Its own `<style>` (:42-96) is `.page__content`-prefixed to beat theme and custom.html specificity (comment :56-58). It depends on the theme's `.highlighter-rouge` / rouge markup (:83-93). It hard-codes a dark code slab and explicitly warns against using `color-scheme: dark` (:75-83).
- **Also affected by the head include:** the emoji-strip script runs on every `.page__content` h2/h3 (`_includes/head/custom.html:276-289`). That rewrites the text of the prompt headings on /prompts/, although the page's intro promises "the real wording" (`home.html:537`, `prompts.html:6-8`).

### Evaluator reviews (`_posts/*-evaluator.md` → theme `single`)

- 20 posts, all carrying `published: true`. `ls _posts | grep -c evaluator` gives 20, and `grep -rn "published: true" _posts | wc -l` also gives 20.
- Example front matter: `_posts/2026-09-20-evaluator.md:1-7`, with `layout: single`, `categories: [evaluator]` and `published: true`.
- **Live chrome** (`live_2026_09_20_evaluator_.html`):
  - `<body class="layout--single">`
  - theme masthead containing `.site-title` "News" and an empty greedy-nav
  - `page__meta` showing read_time
  - `page__taxonomy` linking to `/claude-routines/categories/#evaluator`, which is a **dead link** because `/categories/` returns 404
  - prev/next `nav.pagination`
  - `main.css`, Font Awesome from jsdelivr, and `main.min.js`
- **Styled by** `_includes/head/custom.html:98-205`:
  - `.page__content`, `.page__title`, `.page__meta`
  - h2 kicker styling
  - tables re-skinned for dark mode (:176-185)
  - `.page__title a` forced to `--ink !important` (:155-157)
- **The URL is pinned by:**
  - the notification click URL, `tools/publish.py:222-224` (`SITE/<y>/<m>/<d>/evaluator/`)
  - the evaluator prompt, `routines/weekly-evaluator.md:298`
  - the rail link (`home.html:173-176`)
  - the sitemap
- **`layout: single` is pinned by** `publish.py` `ensure_front_matter` (:185-189 writes `layout: single`) and by `tools/tests/test_publish.py:148` (`assertIn("layout: single", fm)`), plus :49, :205, :218 and :233.

### Feed, sitemap, paginate, archives, robots, 404

- **`/feed.xml`** (jekyll-feed): 200 with 10 `<entry>` items, all evaluator reviews because the other posts are unpublished. It is linked from the theme head and the theme footer.
- **`/sitemap.xml`** (jekyll-sitemap): 22 URLs, i.e. 20 evaluator reviews, `/` and `/prompts/`. `/admin/` is excluded via `sitemap: false`.
- **`/robots.txt`** is jekyll-sitemap's (`Sitemap: …/sitemap.xml`).
- **jekyll-paginate:** no evidence of use. `home.html` has no `paginator` reference, and `/page2/` returns 404. (Pagination only works on `index.html`, and the homepage is `index.md`.)
- **`/categories/` and `/tags/`:** both 404. The archive config is dead, and the evaluator taxonomy link points into it.
- **No custom 404.** `/404.html` serves GitHub's generic "Page not found · GitHub Pages".

### What `_includes/head/custom.html` does on EVERY page

It is included by home (:33), admin (:9-11), and by the theme's `default.html`, which serves prompts and the evaluator.

| Lines | Code | Runs on | Needed by |
|---|---|---|---|
| 1-6 | Title dedup script ("News - News" → "News") | all | only `/`, where the title equals the site title |
| 13-23 | `.page__content` stub appended to `<body>`; works around `main.min.js` assuming the element exists | all; it appends a hidden div to admin and home | pages loading `main.min.js` (home, prompts, evaluator), not admin |
| 26-40, 207-216 | `.fb-btn` / focus / placeholder CSS | all | home propose form only (`home.html:395-415`) |
| 41-47 | `window.__FB = {enabled, url: feedback-sink}` | all | home (`home.html:2272,2694`), admin (`_layouts/admin.html:152`) |
| 58-217 | Palette tokens (`light-dark()`, :69-96), body, and theme-bleed overrides (`#main`, `.masthead`, `.greedy-nav`, `.page__content*`, tables, `.page__footer`, `.archive__*`) | all | tokens: every page. `.page__*`/`.masthead`/`.archive__*`: theme pages only |
| 111-126 | Kill the theme's `transition:all .2s` on b, i, p, span, h1, h2… ("theme motion bleed") | all | only exists to fight `main.css` |
| 228-273 | Anton `@font-face` ×2 (with `relative_url`, :224-226 says it is load-bearing) + metric-matched `Anton Fallback` (size-adjust 86%, a tuned ruling at :263-272) + preload | all | every page (`--display`) |
| 275-290 | Emoji strip on `.page__content` h2/h3 | all | evaluator; misfires on /prompts/ |
| 292-305 | `.layout--home .page__title`, `.home-tagline` | all | home only |
| 307-350 | `.propose*` form styling | all | home only |

This is the memory note "retiring pages retargets shared-head code" in practice. Home-only CSS/JS sits in a shared head, and theme-only CSS is shipped to the theme-free admin page.

---

## 2. Theme dependency (minimal-mistakes 4.26.2 via remote_theme)

### What the site actually uses from the theme

- **Layouts:**
  - `single` (→ `default`): prompts and the 20 evaluator posts.
  - Theme `home`/`archive` are unused. `home.html` shadows the theme's `home` and stopped using `archive` on 2026-09-12 (`home.html:4-9`).
- **Includes, called by name from home:** `copyright.html`, `head.html` (including SEO/og, canonical, the feed link, `main.css` and Font Awesome), `footer.html`, `scripts.html` (`main.min.js`).
- **Includes, via `default`/`single`:** additionally masthead, skip-links, page__meta/read_time, page__taxonomy, post_pagination, and `head/custom.html`, which is the theme's own hook.
- **Sass → `assets/css/main.css`:** consumed by home, prompts and evaluator. Home fights it in many places:
  - root font-size ladder, 16→18→20→22px (`home.html:1006`, :1385, :1887)
  - `body{min-height:100vh}` (:603, :619)
  - `#main{max-width:1280px; margin-inline:auto}` (:641-646, :1662)
  - `animation:intro` on `#main`/footer (:624-626)
  - `:visited` link colour (:1198)
  - bare `figure` as a flex row (:1713)
  - transform rules (:1078)
  - `transition:all` (custom.html:111-126)
- **JS bundle `main.min.js`:** used for nothing on home (comment `home.html:2730-2732`). The `no-js`→`js` class swap in the theme's `scripts.html`/head (live_.html: `document.documentElement.className.replace(/\bno-js\b/g,'')+' js '`) is emitted, and `home.html:30` sets `class="no-js"`.
- **`jekyll-include-cache`** is present only because the theme uses `include_cached`.
- **Search** is not enabled (no `search:` key in `_config.yml`).
- **Gemfile** lists the `minimal-mistakes-jekyll` gem (Gemfile:4), but `_config.yml` uses `remote_theme`, and `jekyll-remote-theme` is not in `plugins:`. GitHub Pages adds it implicitly, so a plain local `bundle exec jekyll build` with this Gemfile would not pick up the theme.

### What dropping the theme would take

1. **Own base layout.** Two options:
   - a `_layouts/default.html`
   - (b) keep `home.html` self-owned. In that case replace the four theme includes (`copyright`, `head`, `footer`, `scripts`) with our own. Any `{% include X %}` naming a missing file is a hard build error.
2. **Own `_layouts/single.html`.** The name `single` must stay, or `publish.py` and `test_publish.py` must change (§1). It would serve the evaluator posts and prompts, and needs to carry title, date, content and prev/next if the owner wants them.
3. **SEO/og, canonical and the feed `<link>`.** Either hand-write them or add `jekyll-seo-tag`, which is on the Pages plugin allowlist. jekyll-feed's `{% feed_meta %}` tag supplies the feed link.
4. **Delete the theme-bleed CSS.** All the fights listed above go (custom.html :100-205, :111-126, :293-305, and the home comments). So does the `.page__content` stub, and the title-dedup script if our `<title>` is authored correctly.
5. **Font Awesome goes.** The only consumer is the footer RSS icon, which could become inline SVG or text.
6. **Remove `jekyll-include-cache` and `jekyll-paginate`**, plus the dead `category_archive`/`tag_archive` config. Also fix or drop the evaluator taxonomy link.
7. **prompts.html** would need its own prose/code styles and would lose the rouge-theme reliance (:83-93). `markdownify` + kramdown/rouge are Jekyll core, so they still work.

### Risks

- **GitHub Pages legacy build** (`gh api …/pages` → `build_type: "legacy"`, source `main` `/`):
  - allowlisted plugins only, no custom plugins, no `.github/workflows` present
  - remote_theme is fetched from GitHub at build time
  - Pages builds ONLY `main`, so there is no preview for a branch or worktree
- **No local Jekyll:** `jekyll` is not found, and system Ruby is 2.6.10 (`ruby -v`). Docker is installed (`/usr/local/bin/docker`) but the daemon is down, so a `github-pages` container build would need the owner to start Docker.
- **Consequence:** unless Docker is started, the first full render of any template change is the production Pages build. A Liquid error poisons that SHA (pages-deploy-wedge; `test_liquid_balance.py:4-14`).
- **Origin lock limits any preview:** `RP_ID = "khalic-lab.github.io"`, `SITE_ORIGIN = "https://khalic-lab.github.io"` (`tools/feedback-sink/src/worker.js:60-62`). Session routes echo CORS only for that exact origin (:112-132). On localhost or any other host, passkey sign-in, sync, votes, prefs and propose all fail. og-proxy is `*` (`tools/og-proxy/src/worker.js:16`), so thumbnails still work anywhere.

---

## 3. Tests and tools that pin the frontend

The suite command is `python3 -m unittest discover -s tools/tests` (CLAUDE.md). I did not run it.

### `tools/tests/test_liquid_balance.py`

- **What it does:** a tag-balance check over `_layouts/**`, `_includes/**` and `_pages/**` (html/md), plus root `index.html`/`index.md` (:39-54). It checks `comment`/`raw` inertness (:57-92) and guards that `_layouts/home.html` is covered (:107-110).
- **Gap:** root `admin.html` and `prompts.html` are NOT scanned (:50-53 lists only index.*).
- **For the rewrite:** it survives as-is if templates stay in `_layouts`/`_includes`. `test_home_layout_is_covered` hard-codes `_layouts/home.html` (:110); keep that filename or update it. It is not a Liquid parser (:16-18).

### `tools/tests/test_admin_harness.py` + `tools/admin/harness.py`

- **How it runs:** the harness is run via subprocess (:44-47). It composes `admin.html` into `_layouts/admin.html`, then **regex-replaces `{% include head/custom.html %}`** (`harness.py` ~:116, pattern `\{%-?\s*include\s+head/custom\.html\s*-?%\}`) with **only the `<style>` blocks** of `_includes/head/custom.html`, with font `url()`s rewritten to file:// (`harness.py:36-52`).
- **It aborts** if any other Liquid remains in those styles (`harness.py:50-52`).
- **Assertions:**
  - no Liquid in the output (:81-85)
  - no external `src`/`href`/`url()` except `/assets/fonts/` (:88-97)
  - `viewport-fit=cover`, `noindex`, `charset` (:100-107)
  - **banned tokens across the WHOLE output, including custom.html's CSS:** `position:fixed`, `position:sticky`, `100vh`, `100dvh`, `overflow-y:` (:110-114)
  - `overflow-x:auto` in the layout (:116-118)
  - **exactly one `<style>` and one `<script>` in `_layouts/admin.html`** (:121-124)
  - six section ids in order in `admin.html` (:126-130)
  - self-contained auth functions `session`, `doLogin`, `b64uToBuf`, `bufToB64u`, and no external script (:132-137)
  - session-shape strings shared with home (:139-144)
  - `node --check` on every script (:217-224)
- **Consequences for a rewrite of the shared head:**
  - Moving the palette out of `<style>` blocks (e.g. into an external CSS file) blinds the harness: it embeds nothing and the page renders untokened. Add Liquid other than the font form and it aborts.
  - Putting sticky/fixed/100vh/overflow-y rules into the shared head (for example home's sticky bar) fails `test_no_fixed_or_full_viewport`.
  - Renaming the include path breaks the regex.

### Builder-shape tests (Python over `tools/build_stories_feed.py`)

- **`test_feed_sid.py:121-135`:** golden `tools/tests/fixtures/dualwrite/golden-feed.json` pins `generated`, `count`, `topics` and **every `feed.stories[]` field and value**; only `sid` may be added. Golden story keys: date, date_label, fresh, headline, id, importance, is_lead, permalink, source_domain, stream, stream_label, summary, topic_color, topic_label, topic_primary, topics, url, why.
  - **Rule:** new render fields belong on `board`, which is a view the golden does not pin; see the comment at `build_stories_feed.py:1051-1055`. Otherwise regenerate the golden via `capture_golden_feed()` (:99-107).
  - `permalink` is still emitted (`build_stories_feed.py:986`) but no Liquid reads it (the grep of `home.html` finds no `permalink`). It is dead but pinned.
- **`test_editorials.py`:**
  - `BuildBoardTest` (:227-301) pins: an editorial closes its own date block (:241-249); `ED_MIN_BOARD_INDEX` keeps editorials out of the first 3 slots (:251-260); editorial-only boards are left alone (:262-265); stable in-tier order (:267-271); `age_days` clamped to `AGE_MAX` (:273-277); daybreak once per contiguous date run (:279-287); the 2026-07-26 regression (:289-301).
  - Editorial lifetime tests (:161-214): `ED_MAX_AGE_DAYS` must be less than the 7-day cadence (:179-208), which is the regression guard for the owner's "the editorials keep reappearing" report of 2026-09-12. There is also the live-edition gate (:210-214).
  - Extractor tests (:25-123) cover title/paras parsing.
- **`test_feed_age.py`:** unit tests for `drop_aged_out` (:44-107). Live-artifact tests over the committed `_data/homefeed.json` `board` (:109-163): no stale story, no editorial older than `ED_MAX_AGE_DAYS`, and every editorial edition still has a story. It reads `kind` and `board`.
- **`test_deck.py`** (:74, :106-136): `deck` is emitted only when non-empty; key absence is the contract.
- **`test_feed_join.py`, `test_prose_derivation.py`, `test_url_identity.py`:** these pin story content and the join, not markup. They are unaffected by a pure frontend rewrite.
- `test_metrics.py`, `test_store.py` and `test_sources_preflight.py` matched only on words like "includes"; they have no frontend pins.

### `tools/home_harness.py`: DISABLED 2026-09-13

- It raises `SystemExit` unconditionally (:3083-3087): "Verify against a real DOM instead: Playwright WebKit for layout, the ?probe=1 readout on the iOS simulator". The rationale is at :3075-3081 and in commit `f778038`.
- **What replaced it:**
  - `?probe=1`, the on-device readout (`home.html:2733-2764`), which paints inner/visual/lvh/svh/dvh and the bar rect.
  - The runbook in `docs/archive/REVIEW-2026-09-13-front-page-ios.md:78-80`: simctl at `/Applications/Xcode.app/Contents/Developer/usr/bin/simctl`, `python3 -m http.server` + `<base href>`, and Playwright WebKit for layout only (blind to browser chrome).
- **The planned replacement `tools/verify/shell.mjs` (REVIEW :71) was never added;** `tools/verify` does not exist. The review also forbids borrowing Playwright from `/usr/local/src/spcs/hk-sofa-front/node_modules` (REVIEW :49). A personal cache at `~/Library/Caches/ms-playwright` (webkit-2287, webkit-2359) exists, but there is no personal Playwright package in this repo.
- Stale docs still point at the harness:
  - `_includes/head/custom.html:67-68` ("The harness EXTRACTS this block by regex")
  - `test_liquid_balance.py:5`
  - `build_stories_feed.py:1053`, :1092
  - `ARCHITECTURE.md:1035`

---

## 4. Builder-side layout workarounds (`tools/build_stories_feed.py`)

| Item | Where | Exists because of | If the layout changes | Pinned by |
|---|---|---|---|---|
| `ED_MIN_BOARD_INDEX = 3` + the push-down loop | :1013, :1044-1049, :1070-1081 | The composed top band places children 1-3 by `nth-child` (`home.html:945-973`). A `.fcard--ed` in slot 1 spans `grid-area:1/1/2/13` (failure of 2026-07-25). Also noted in the comment at `home.html:384`. | Deletable once no layout position is keyed on `nth-child`. The docstring calls it "a dead branch on any normal day" (:1047-1049). | `test_editorials.py:251-260` |
| `AGE_MAX = 3` / `age_days` clamp | :1014-1023, :1084-1089 | `home.html` keys the type scale on the literal `[data-age="3"]`, at **:1443-1444**. The builder comment cites a stale :1431-1432. | Keep it as a bucket, or emit a real duration as a SECOND field; the ruling at :1015-1023 says "do not widen this one". Staleness is handled upstream by `STORY_MAX_AGE_DAYS`. | `test_editorials.py:273-277`, :301 |
| `day_label` | :1090-1094 | The daybreak card prints the weekday and date; it is formatted in Python so the page and the (now disabled) harness share one string. | Could become Liquid `date` or stay; the harness reason is gone. | Nothing asserts the format. |
| `daybreak` | :1095-1100 | Marks contiguous date-run starts so a column-packed board can print the date typographically (`home.html:280,283,309,318,312-317`). | Still needed for any per-day heading. With real `<section>` day groups it could be derived in Liquid (`it.date != prev`) or kept. | `test_editorials.py:279-287` |
| Editorial rank 0 (below briefs) | :1066-1068, docstring :1030-1041 | The owner ruling (2026-07-26): one ranking, and an editorial closes its own edition's date block. | **A ruling, not a layout mechanic. Keep.** | `test_editorials.py:241-249`, :289-301 |
| `deck` / `affiliations` / `affiliation_label` emitted only when non-empty | :988-1002 | Liquid treats `""` as truthy, so key absence is the render gate (`home.html:309,344,362`). | Harmless; keep the absent-key contract. | `test_deck.py:112-134` |
| `is_lead`, `fresh`, `date_label` | :985, :1269, :982 | `.lead` class (`home.html:309`), "Just in" (:363), rail edition line (`feed.stories.first.date_label`, :150) | `is_lead` duplicates `importance == 3`. It is deletable only via the golden. | golden (`test_feed_sid.py`) |
| `feed.stories`, `feed.editorials`, `feed.count` next to `board` | :1281-1282 | `count` is used by the "All" chip (`home.html:192`); `stories.size` gates the page (:49,:51,:120). `editorials` is emitted but only `board` is iterated. | Keep `count`/`topics`. The `board` fallback `feed.board | default: feed.stories` (:277) is a pre-board relic. | golden, `test_feed_age` |
| `permalink` | :986 | Brief pages (retired 2026-07-18) | Dead in the template | golden |

### Editorial timeliness (the owner's "appear days after" complaint): builder and deploy facts only

- I traced the editorial board indices through 35 `homefeed.json` commits since 2026-09-05 (`git show <c>:_data/homefeed.json`).
- **Each editorial enters `board` in the same commit as its edition**, for example:
  - weekend/09-19 @10 in `8bbbb8a`
  - sports/09-21 @5 in `6fa0175`
  - science/09-23 @13 in `eed8848`
- It then sinks as newer dates stack above it, and leaves after `ED_MAX_AGE_DAYS=5` days. For example, weekend/09-19 is at @52 on 09-24.
- **The live `/` DOM order matches the board:** `.fcard--ed` sit at li indices 12, 36 and 52 (`live_.html`), the same as commit `3ecf3f1`.
- **So there is no lag in the builder or the deploy.** What the reader perceives comes from the render side:
  - the board is column-packed (`home.html:312-317`, :594)
  - the editorial is placed at the END of its date block
  - it persists for 5 days
- The home.html auditors own the visual-placement question.

---

## 5. Publish and deploy path

### Regeneration

- **Writers:** `tools/publish.py` runs `feed` → `tools/build_stories_feed.py` (:464) after record, anchor, footer and lints. It is followed by `source-health` and `plane-push` (:465-468). The stats rebuild is part of the same chain (docstring :7).
- **Push conflict handling:** on a push conflict it pulls with rebase, **regenerates the feed** (:360-370, "Concurrent editions both rewrite `_data/homefeed.json`"), amends and retries.
- **Evaluator:** skips preprocessing (:426-427) and writes the front matter with `layout: single` and `published: true` (:185-189).
- **Notifications:** click through to `/` for writers and to `/<y>/<m>/<d>/evaluator/` for the review (:219-224).
- **Implication:** `_data/homefeed.json` changes only when a writer publishes. A layout-only commit re-renders the existing JSON.

### GitHub Pages

- The build is legacy Jekyll from `main` `/` (`gh api …/pages`), with `remote_theme` fetched at build time.
- **15 of the last 100 builds errored,** with `"Page build failed."` and `duration: 0`. Each errored SHA was an edition commit, and the next commit, about 30 s later, built fine. Examples:
  - `3ecf3f1` at 10:21:11Z errored; `81ce426` at 10:21:39Z built.
  - The same pattern holds for `eed8848`, `cf931ca`, `b41c37c` and `1838b10`.
- Whether these are cancellations or supersessions is not observed.
- The bridge self-heal covers a real errored build (an empty commit) and a stale SHA (`POST /pages/builds`); see `/usr/local/src/news-brief-ntfy-bridge/bridge.sh:59-165`.

### Local bridge (why the rewrite must happen in a worktree on a non-main branch)

- It runs from cron every 10 minutes, 07-22h: `*/10 7-22 * * * …/bridge.sh` (`crontab -l`).
- It does `cd "$REPO"` (the main checkout, :54).
- If the tree is dirty, it **auto-stashes with `--include-untracked`** (:195-203), runs `git pull --rebase origin main` (:208), and restores the stash. On a conflict it **resets `--hard` and parks the work in the stash** (:178-190).
- It `git add`s `feedback/ proposals/ index/ledger/ sources/ index/admin/ index/usage/` (bridge :288-293), commits unsigned as "Bridge", and **pushes any local commits ahead of origin on `main`** (bridge :305-315).
- **Consequence:** any commit on local `main` goes live within 10 minutes.
- **Safe:** worktree commits on another branch are not pushed.
- **Unsafe:** merging the rewrite into local `main` publishes it.
- The main checkout currently has the owner's uncommitted `tools/usage/pricing.py`. Current worktrees: only `/Users/rflnogueira/code/claude-routines [main]` (`git worktree list`).

### Worker routes the pages call

| Worker | Host | Route | Caller |
|---|---|---|---|
| feedback-sink | `feedback-sink.khalic-lab.workers.dev` (`custom.html:46`) | `POST /submit` | `home.html:2279`; body `{brief, vote, reason, story_id, surface:'home'}` (:2281-2282) |
| | | `POST /propose` | `home.html:2715` |
| | | `GET/POST /prefs` | `home.html:2225`, :2261; body `{topics, rs, ts}` (:2228) |
| | | `GET/POST /readstate` | `home.html:2397`, :2437; body `{state: syncMap}` |
| | | `/auth/login-options`, `/auth/login`, `/auth/register-options`, `/auth/register` | `home.html:2518-2565`, admin :193, :212 |
| | | `GET /admin/snapshot`, `POST /admin/actions` | admin :312-313, :331, :475, :529 |
| og-proxy | `og-proxy.khalic-lab.workers.dev/?url=` | `GET` | `home.html:2624`, :2664; CORS `*` |
| embed-proxy | n/a | `/plane/*` | **Not called by any page.** It is fed by `publish.py` plane-push (:468). |

- **Router:** `tools/feedback-sink/src/worker.js:871-935`.
- **No Worker change is needed** if the rewrite keeps these request shapes, the site origin, and these reader-state identifiers:
  - `localStorage`: `homeRead:v1` (`home.html:1972`), `topicPrefs:v1` (:2189), `syncSession:v1`, `syncState:v1` (:2361)
  - `sessionStorage`: `homeOg:v2:` (:2625)
  - card ids: `data-story` = `sid | default: id` (:367) and `ed-<stream>-<date>` (:280, :300); `data-brief` = `<date>-<stream>`
  - these ids are resolved by `tools/feedback/fold.py:79-90` and keyed in roamed read-state
- **A Worker change would require a user-run `wrangler deploy`,** and the auto-mode classifier denies agents running it (memory "bridge owns this checkout"). Triggers:
  - new `/prefs` fields: the Worker re-serializes only known fields (memory "feedback-sink prefs roaming")
  - a new route
  - a new origin or preview host (`worker.js:60-62`)
- **Sequencing rule:** deploy the Worker routes BEFORE merging pages that call them.
- **Stale docs:** `tools/feedback-sink/README.md:167` and `tools/og-proxy/README.md:3,53` still say the widgets and og loader live in `_includes/head/custom.html`. They moved to `home.html`.
