# JS audit — preservation contract for the frontend rewrite (key: js)

Scope: every `<script>` in `_layouts/home.html` (H) — 541-585 (modal), 1791-2685 (main IIFE), 2686-2726 (propose), 2733-2764 (probe) — and `_includes/head/custom.html` (C) — 1-6, 7-24, 41-47, 275-290. Cross-checked against `tools/feedback-sink/src/worker.js` (W), `tools/og-proxy/src/worker.js` (O), `_layouts/admin.html` (A), `tools/build_stories_feed.py` (B), `_data/homefeed.json`.
Line refs are `file:line`. Nothing in the repo was modified. (`tools/home_harness.py` was invoked once with `--out` in the scratchpad; it printed its disabled message and exited. `find tools -name '*.pyc' -mmin -180` shows only `tools/usage/__pycache__/pricing.cpython-314.pyc` (14:11), which comes from the owner's concurrent pricing.py work; the harness does not import it. This audit made no repo write.)

---

## 0. Headline facts

- **JS never reorders or date-gates cards.** DOM order is `feed.board` (H:277-278), built server-side (B:1025-1085). JS only toggles `style.display`, classes and attributes, and inserts `.fimg` and `.ffb-rzn` nodes. So the "editorials show up days late" bug is not in JS. JS touches editorials in only two ways. (a) Any active beat hides every editorial: `data-topics=""` (H:280) never matches (H:2038-2041), and a roamed `topicPrefs:v1` carries that hidden state across devices. (b) Editorials always boot folded: they carry `data-imp="2"` (H:280), and the fold rule opens only `age 0 && imp 3` (H:2092).
- **The whole harness is dead.** `tools/home_harness.py` exits with "disabled 2026-09-13 … Verify against a real DOM instead: Playwright WebKit for layout, the ?probe=1 readout on the iOS simulator". So the `#synced/#bsread/#bootempty/#open/#read/#allread/#empty` hash modes exist only in that harness (home_harness.py:634,770-782,1674,1729,1742,1895-1896). **The page has no hash modes.** Its one live URL mode is `?probe=1` (H:2737).
- **Origin pinning.** The Worker answers CORS only for `https://khalic-lab.github.io` on /auth/*, /submit, /propose, /readstate and /prefs (W:62,118-133). WebAuthn pins rpID `khalic-lab.github.io` and origin (W:60-62,423,487). **A local or preview build of the rewrite cannot sign in, vote, propose or sync.** End-to-end verification only works on the deployed origin, or by stubbing `fetch` the way the old harness PRE_SYNC did (home_harness.py:1672-1712).

---

## 1. Storage keys (byte-compatible — do not rename, reshape or reuse)

| Key | Store | Value shape | Written by | Read by | Migration / guards |
|---|---|---|---|---|---|
| `homeRead:v1` | localStorage | `{ "<sid>": <ms epoch number>, … }` (presence = read) | `saveRead` H:1976, from `setRead` H:2025-2026, `prune` H:1977-1981, `mergeRemote` H:2420-2423 | boot H:1974; `isRead` H:1986 | Corrupt or non-object value resets to `{}` (H:1975). **45-day prune** at boot (H:1977-1981). |
| `syncState:v1` | localStorage | `{ "<sid>": {ts:<ms>, v:0\|1}, … }` (v:0 = tombstone) | `saveSync` H:2372, from `noteLocalRead` H:2380-2383 (**written even while signed out**), `pruneSync` H:2373-2377, `mergeRemote` H:2412,2419,2423 | boot H:2370; POSTed whole by `flushPush` H:2400 | Corrupt guard H:2371. 45-day prune H:2373-2377. **Migration:** `mergeRemote` seeds shadows `{ts:readMap[k], v:1}` for pre-sync `homeRead` entries (H:2411-2412). |
| `topicPrefs:v1` | localStorage | `{topics:[string…], rs:""\|"unread"\|"read", ts:<ms>}` | `saveTopicPrefs` H:2198, from `recordPrefsChange` H:2246-2247 and `mergeRemoteTopics` H:2253-2254 | boot H:2195-2196 | **Migration:** `validRs` coerces a missing or invalid `rs` (pre-2026-07-18 values) to `""` (H:2192,2196). Non-number `ts` becomes 0. Must keep `topics` keys that have no chip today ("held", H:2204-2208). |
| `syncSession:v1` | localStorage | `{token:<64 hex>, reader:<string>, at:<ms>}` | `adoptSession` H:2511; removed by `dropSession` H:2449 | `session()` H:2363-2368 (requires token **and** reader); propose `session()` H:2698-2702 (token only) | **Shared with the admin page:** A:151-161,189 copies the shape and validator. The old harness seeded it without `at` (home_harness.py:1716), and `sessionDied` tolerates that (H:2456). |
| `homeOg:v2:<article url>` | **sessionStorage** | image URL string, or `""` = known no-image | H:2667 | H:2661 | Version bump v1 to v2 at c8608ca/b14bad9. Per tab, so losing it costs only refetches. |

**Retired names. Never reuse them with a new shape:** `siteKey` (localStorage, which held the shared write secret; removed 71d4c56 from C, and may still sit in readers' browsers, so the rewrite may `removeItem('siteKey')` as cleanup), `homeOg:v1:` (sessionStorage), `autoPreview:v2:` (removed e7c8745). `window.__siteKey` API gone (71d4c56).

**Globals (cross-script contract):**
- `window.__FB = {enabled, url}` is defined in C:46. It is read by H:2272 (`fbConf`, with a hard-coded fallback), H:2694 (propose), and **A:152** (the admin page includes C *only* for tokens, the font and `__FB`, A:9-11). C is also included by `layout: single` pages (prompts, evaluator). **Any change to C affects three page types.**
- `window.__syncNudge = nudgeSignIn` is defined H:2615 (only when WebAuthn exists) and borrowed by propose H:2706.

---

## 2. Read-state identity (byte-stable or every reader's history resets)

- **Story card:** `sid = .fcard__fb[data-story]`, whose Liquid value is `{{ s.sid | default: s.id }}` (H:367). `sid` comes from B:979: `s.anchor_sid or _safe_story_id(url)`, format `st-[0-9a-f]{12}`. The fallback `id` is the slug `hid` (for example `2026-09-24-news-estonia-latvia-…`). B:964-965 says hid "must stay byte-stable". Today all 80 stories have an `st-` sid and none are duplicates.
- **Editorial card:** `sid = li.fcard[data-story]` = `ed-{{ it.stream }}-{{ it.date }}` (H:280). The same value is repeated on `.fcard__fb` (H:300). `it.date` is the editorial's brief date (`YYYY-MM-DD`). A new edition from the same desk gets a new id, so it comes back unread (H:1965-1966).
- **Resolver:** `sidOf(card)` = `card.dataset.story || card.querySelector('.fcard__fb').dataset.story || ''` (H:1982-1985). **Coupling hazard: for stories, read identity lives on the *feedback box*.** If the rewrite drops `.fcard__fb`, renders it conditionally, or leaves it out when `__FB.enabled=false`, every story's read state is lost with it. The contract should put the id on the card itself, for example `li[data-story]` for every card, and keep the value `sid | default: id` byte-for-byte.
- **Twins:** the same sid may appear on more than one card. `setRead` repaints all of them (H:2028-2030).
- **Feedback identity** (separate from read, but uses the same sid): `data-brief="{{date}}-{{stream}}"` (H:300,367) goes to the `/submit` body as `brief`, and `data-story` goes as `story_id`.

---

## 3. Network contract

Base: `fbConf().url` = `window.__FB.url` = `https://feedback-sink.khalic-lab.workers.dev` (C:46, H:2272,2362). Auth = `Authorization: Bearer <syncSession.token>` (the Worker requires `^Bearer\s+([0-9a-f]{64})$`, W:201).

| Call | Where | Method | Body / query | Response used | Worker validation |
|---|---|---|---|---|---|
| `/submit` | `postFb` H:2279-2286 | POST, JSON, Bearer | `{brief, vote: 1\|-1\|0, reason:trimmed, story_id: data-story\|null, surface:'home'}` | `r.ok`, 401 → `sessionDied` | W:269-310. `brief` non-empty; vote ∈ {1,-1,0}; reason ≤2000 chars; `story_id` must match `^(st-[0-9a-f]{12}\|ed-[a-z0-9-]{1,40}-\d{4}-\d{2}-\d{2})$` (W:79) or the call returns **400**. `reader` comes from the session. |
| `/propose` | H:2715-2723 | POST, JSON, Bearer | `{topic:trimmed, detail:trimmed, surface:'web'}` | ok, 401 | W:312-343. topic ≤300 (the input also has maxlength=300, H:410); detail ≤2000. |
| `/readstate` GET | `pullRemote` H:2437 | GET, Bearer | — | `j.state` `{sid:{ts,v}}` | W:507-521 |
| `/readstate` POST | `flushPush` H:2397-2402 | POST, `keepalive:true`, JSON, Bearer | `{state: syncMap}` (the **whole** shadow, not a delta) | only 401 checked | W:523-587. Body ≤65536 B → 413; ≤2000 entries; **each key must match `^st-[0-9a-f]{12}$` (W:77) or it is silently skipped**; ts ≤ now+1d; v ∈ {0,1}. LWW, tie keeps the server's value. Server ages out entries after 90 days. |
| `/prefs` GET | `pullTopics` H:2261 | GET, Bearer | — | `j.prefs` `{topics, rs, ts}` | W:599-616 |
| `/prefs` POST | `flushTopics` H:2225-2234 | POST, `keepalive:true`, JSON, Bearer | **exactly `{topics, rs, ts}`** (H:2228) | 401 → sessionDied; any other non-2xx → keeps pending + `saySync('beat sync failed (N)')` | W:618-671. **Re-serialises only `{topics, rs, ts}`** (W:663). topics must be an array of ≤50 (**400 above**, no clamp, hence TOPIC_CAP H:2236,2245), each matching `^[a-z0-9][a-z0-9-]{0,39}$`, deduped. `rs` outside {"", unread, read} is coerced to "". A ts that is not a positive number or is more than 1 day ahead is replaced by `now`. Whole-object LWW: stored only if `ts > stored.ts`. **Any new pref field needs worker.js + smoke + `wrangler deploy` (user-run)**, per the memory note. |
| `/auth/login-options` | `doLogin` H:2518 | POST `{}`, no auth | — | `challenge`, `allowCredentials` (b64u, decoded) | W:447-456 (discoverable, UV required) |
| `/auth/login` | H:2537 | POST `{response:{id, rawId, type, clientExtensionResults, response:{clientDataJSON, authenticatorData, signature, userHandle?}}}` | — | `{ok, session, reader}` → `adoptSession` | W:458-505; 403 → "passkey not recognized" |
| `/auth/register-options` | `doRegister` H:2546 | POST `{invite}` | — | `challenge`, `user.id`, `excludeCredentials` decoded | W:383-402; 403 bad invite |
| `/auth/register` | H:2565 | POST `{invite, response:{id, rawId, type, clientExtensionResults, response:{clientDataJSON, attestationObject, transports?}}}` | — | `{ok, session, reader}` | W:404-445 |
| og-proxy | `swapImage` H:2624,2664 | GET `https://og-proxy.khalic-lab.workers.dev/?url=<encodeURIComponent(url)>`, no auth | — | `j.image` (null → "") | O:1-4. CORS `*`, 200 with `image:null` on failure, edge-cached 30 days. |

- `authFetch` (H:2500-2508) sends no auth header and wraps the result as `{ok,status,j}`, tolerating a non-JSON body.
- Base64url helpers `b64uToBuf`/`bufToB64u` (H:2488-2499) are copied verbatim in A. **No `sendBeacon` anywhere**: it cannot carry Authorization (H:2392).
- Signed out means **zero** sync requests: `pullRemote`, `pullTopics`, `schedulePush` and `pushTopics` all bail on `!session()` (H:2386,2214,2436,2260). The admin page also depends on this (A:147-148).

---

## 4. Feature list, with DOM hooks

### 4.1 "How this works" modal (H:541-585)
- Hooks: `.hiw-open` (every instance: header H:111 + rail H:161), `#hiwModal` (H:435), `[data-hiw-close]` (H:437,538), class `on` on the modal (CSS H:1696 `.hiw.on{display:flex}`), `aria-hidden` on the modal, `aria-expanded` on the button that was pressed, `html.hiw-lock` (CSS H:1692 `overflow:hidden`).
- Behaviour: opening focuses the first close button (`x`) and resets `modal.scrollTop` to 0. Clicking the backdrop (`e.target === modal`) closes it. Esc closes. Tab and Shift-Tab trap focus within the modal. Focus returns to `lastFocus` on close.
- The IIFE bails only if there is no `.hiw-open`. The header button is emitted even when the feed is empty, so the modal works without a feed.
- It is not a `<dialog>`. A rewrite could use `<dialog>.showModal()` and drop the trap, but it must keep the two-trigger model (one control, two placements).

### 4.2 Beat filter (H:2034-2042, 2149-2172)
- Hooks: `CHIP_SEL = '.folio-filters .ff-chip, .rail-beats .ff-chip'` (H:2157), plus `data-topic` (`""` = All) and `aria-pressed`. There is **one `active` Set and one painter `sync()`** for both renderings; the ruling at H:178-185 and H:2149-2156 is "the same control rendered twice, never two selectors".
- Multi-select, OR semantics: a card matches if any key in `card.dataset.topics` (space-separated, H:309) is active. All clears the Set **and `held`** (H:2168).
- Every click runs `sync(); apply(); recordPrefsChange()`.

### 4.3 Read filter All / Unread / Read (H:2069-2076, 2199-2203)
- Hooks: `#folioFilters .ff-rbtn[data-rs=""|"unread"|"read"]` + `aria-pressed`. **The bar only; the rail has no copy.** Each click calls `apply()` and `recordPrefsChange()`.

### 4.4 `apply()` (H:2043-2068)
- Hides cards with **inline `style.display='none'`**. `packRowSpans` (H:1841) and `topCard` (H:1958) read that exact property.
- Toggles `.folio-grid.is-filtered` whenever any beat or read filter is active. CSS (H:945-976, 1228) uses it to turn off the `nth-child(1..3)` composed top band.
- Empty state: `#folioEmpty` (`li.folio-empty`, role=status, aria-live, H:388) gets its text and `hidden`. The copy is a ruling ("most specific true sentence, always terminated, never an ellipsis"):
  - unread: `All caught up — every story on this beat|in this edition is read.`
  - read: `Nothing marked read[ on this beat] yet.`
  - default: `No stories on this beat right now.` (also the static markup text)
  - Ruling (H:376-387): **the empty state is the last child of the grid.**

### 4.5 Counters
- The `.ff-ct` in chips is **static Liquid** (`feed.count`, `t.count`, H:58,60,193,195). JS never updates chip counts.
- `.ff-uct` (Unread N) is JS-owned (`readCounts` H:1998-2009). It is found through `filters.querySelector` (bar only) and **excludes `.fcard--ed`**, so that Unread can never exceed "All N" (ruling 2026-07-26, H:1999-2002).

### 4.6 Read marking (H:1964-2032, 2124-2148)
- The explicit ✓ `.fcard__read` toggles read. It sets `aria-pressed`, and its `title` alternates between "mark as read" and "mark as unread". The label stays constant: `aria-label="Mark as read"`, with the rationale at H:1992.
- Implicit read: a `click` on `.fcard__hl a`, plus an `auxclick` with button 1 (middle click). An implicit read only **sets** read, never toggles, and **never re-applies the filter** (dims, never hides from under the cursor).
- ✓ under an active read filter calls `apply()` right away. If the card vanished, focus moves to the pressed `.ff-rbtn` (H:2129-2134).
- Visual: `.fcard.is-read` means **opacity only** (CSS H:1569-1574). **RULING, dims-never-hides (H:1575-1589, H:2010-2018): reading must never change geometry or fold state.** It must never hide text, and no `foldForRead` may come back. All three read paths (click, boot paint H:2104, roam `mergeRemote`) call only `paintRead`.
- Voting does **not** mark read (ruling 2026-07-25, H:1967-1969).
- Sign-out clears only `syncSession:v1`. Local read state stays (H:2606).

### 4.7 Fold / More (H:2077-2122)
- Hooks: `.fcard__more` (with a `<span>` label More/Less and `aria-expanded`). Classes: `.is-folded`, and `.is-open` for reader-opened cards (**no CSS consumer**, kept on purpose as a record of reader intent, H:2084-2088,2113-2116). Also reads `data-age`, `data-imp`.
- Boot default: `data-age==="0" && data-imp==="3"` means open (label becomes "Less", no `.is-open`). Every other card that has a More button boots folded. The fold is JS-applied, so **no-JS shows full text** (ruling: the fold is presentation, never a crop, H:2077-2079; the never-crop ruling is also cited at H:1874).
- The fold is ephemeral: no persistence. Expanding does not count as a read.
- CSS consumers: H:1501, 1518, 1523-1524, 1559.
- Side note: with no JS, the More button still renders and does nothing (CSS H:1495 has no `.on` gate). Editorial More is always emitted (H:295).

### 4.8 Thumbs + reason (H:2268-2350)
- Hooks: `.fcard__fb[data-story][data-brief]`, `.ffb-t[data-v="1"|"-1"]`, `.ffb-t.on` (CSS H:1614), `.ffb-note` (aria-live), and the lazily built `.ffb-rzn` (an input with maxlength 500 plus a "send" button; CSS H:1616).
- Clicking the active thumb again retracts it: it posts vote 0 and the note says "withdrawn ✓".
- One reason box per card, shared by both thumbs. The polarity is read live when "send" is pressed (H:2288-2311), and the input is cleared on a polarity switch. The placeholder and aria-label switch between up and down wording.
- A down-vote focuses the input; an up-vote does not.
- Vote state is **not persisted**: after a reload no thumb shows `.on`.
- A signed-out tap shows 'sign in to vote' and calls `nudgeSignIn` (see bug B1).
- Kill switch: `!__FB.enabled` adds `.folio-grid.fb-off` (H:2317; CSS H:2728 hides `.fcard__fb`) and `postFb` no-ops.

### 4.9 Sync / passkey (H:2352-2618)
- Hooks: `#ffSync` (hidden in markup, and un-hidden **only when `window.PublicKeyCredential` exists**, H:2572-2573), `.ff-sbtn` (text becomes `Synced · <reader>`; `aria-expanded`), `.ff-spanel` (`hidden`), `.ffs-out`/`.ffs-in` (`hidden`), `.ffs-signin`, `.ffs-setup-t` (`aria-expanded`), `.ffs-setup`, `.ffs-invite` (Enter clicks create), `.ffs-create`, `.ffs-signout`, `.ffs-who`, `.ffs-status` (aria-live). `#ffSync.is-in` is styled at CSS H:761.
- Panel: Esc (a document-level listener) closes it and returns focus to the button. A click outside `#ffSync` closes it.
- Pulls run at boot (H:2617-2618) and after sign-in (`adoptSession`).
- Read state: pushes are debounced 30 s (H:2389). **Prefs:** pushes are debounced 1.5 s (H:2217). Both are flushed on `visibilitychange→hidden` and on `pagehide` (H:2404-2407).
- 401 handling: `sessionDied` has a **60 s KV-lag grace** after `at` (H:2454-2458). Otherwise it drops the session and nudges.
- Merges: readstate is LWW **per sid**, with ties keeping local (H:2414-2422). Prefs are LWW over the **whole object**; `remote.ts <= local.ts` keeps local (H:2252). After `pullTopics` it always calls `pushTopics()` (H:2263).

### 4.10 Prefs "held" keys (H:2181-2188, 2204-2211, 2237-2249)
- Roamed topic keys that have no chip today are preserved in `held` and written back. The All chip clears them.
- The client caps the list at 50 (TOPIC_CAP).
- This is a correctness ruling. A rewrite that serialises only the visible chips re-introduces the "beat silently dropped" bug.

### 4.11 Propose form (H:2686-2725; markup H:406-415; CSS C:307-350)
- Hooks (the comment at H:403-404 says **do not rename**): `.propose__form`, `[name=topic]`, `[name=detail]`, `.propose__msg`, `.fb-btn`.
- It is a standalone IIFE so it works even when the feed is empty.
- Disclosure: a native `<details class="propose__d">` needs no JS (ruling 2026-07-25).
- Signed out: shows 'sign in to propose — Sync, top right' and calls `__syncNudge`. **That copy assumes the Sync button sits top-right**, but below 700px the bar is at the bottom (H:52-55). Update the copy if the bar moves.

### 4.12 og:image swap (H:2620-2676)
- Hooks: `li.fcard[data-ogurl]`, emitted only when `s.url and s.importance > 1` (H:309). `data-og-done` is the re-entry guard.
- arXiv hosts are skipped (logo-only og:image).
- An IntersectionObserver with rootMargin `600px 0px` unobserves each card after first sight. Without IntersectionObserver there are no images.
- The image is inserted `afterend` of `.fcard__deck`, or of `.fcard__hl` when there is no deck (**ruling: never above the headline**, H:2638-2643).
- Class `fimg`, `alt=""`. Afterwards it calls `schedulePack(60)`.
- CSS H:1378-1382 (a clamp height, and grayscale in dark mode); read cards dim `.fimg` to .5 (H:1574).

### 4.13 Skip link
- `.ff-skip` goes to `#folioGrid`. The grid has `tabindex="-1"` so it can take focus (H:49, 253). No JS.

### 4.14 `?probe=1` readout (H:2733-2764)
- A fixed overlay prints innerHeight, visualViewport, lvh/svh/dvh, the bar's top/bottom/gap measured from `.folio-filters`, scrollY and docH. It repaints on scroll, resize and visualViewport resize.
- It is the **sanctioned on-device verification path** (per the harness-disabled message), so keep it or an equivalent, and re-point it at the new bar's selector.
- Trigger quirk: it uses `location.search.indexOf('probe') > -1`, so any query containing "probe" (for example `?utm=probe`) turns it on.

### 4.15 Keyboard handling (complete list)
- Modal: Esc closes; Tab/Shift-Tab trap (H:575-583).
- Sync panel: Esc (document-level, H:2608-2610).
- Invite input: Enter creates (H:2601-2603).
- Reason input: Enter sends (H:2313).
- Everything else is native buttons, links and `<details>`.
- **There are no keyboard shortcuts** (no j/k and no hotkeys).

### 4.16 custom.html scripts (shared by home, admin and single pages)
- C:1-6: dedups a title of the form "X - X" (theme `seo.html`). Needed wherever the theme head is used; admin has its own `<title>` and is unaffected.
- C:13-23: the `.page__content` stub. It exists **only** because home loads the theme's `main.min.js` through `{% include scripts.html %}` (H:2730-2732,2765), which throws without that element. If the rewrite drops `scripts.html` from home, the stub becomes dead there (single pages have a real `.page__content`; admin loads no theme JS). `_config.yml` has **no `analytics` key** (grep is empty), so dropping `scripts.html` from home loses no tracking. The theme's `scripts.html` also emits `site.footer_scripts`, `after_footer_scripts`, search and comments providers, but `_config.yml` sets none of them (grep finds only `comments: false` under post defaults, _config.yml:29). On home the include therefore delivers only `main.min.js`, whose greedy-nav code is unused because no masthead is emitted.
- C:275-290: strips emoji from `.page__content h2,h3`. On home it matches only the empty stub, a no-op. It is live for evaluator and prompts pages, so keep it in the shared include or move it to `single`.
- C:41-47: `window.__FB` (§1).

---

## 5. Layout-engine JS — DELETABLE if placement and extent become pure CSS

Deletable as a unit (H:1801-1924 + calls):
- `ROW_UNIT`, `packOn/packW/packT/roT/packRo`, `trackCount`, `unpack`, `packRowSpans`, `schedulePack`, `watchPack` (the ResizeObserver on the grid, width-only guard), `bootPack` (a race between `document.fonts.ready` and a 2500 ms provisional pass), and the `bootPack()` call at H:2683.
- The inline `style.gridRow = 'auto / span N'` writes, and the `.packed`/`.packing` classes (CSS H:918-919).
- The `schedulePack(0)` call in `apply()` (H:2055) and `schedulePack(60)` in the og `place()` (H:2656).
- `grid.classList.add('on')` (H:1795): **no CSS consumer exists** (CSS H:1237,1243 say it is a "JS is live" marker; grep finds no `.folio-grid.on` rule). Delete it, or give it a real purpose.
- `.is-filtered` (H:2050) is only needed if the rewrite keeps an `nth-child` composed top band. It is a class toggle, not a measurement.

Entangled features (keep the behaviour, drop the pack):
- **`anchored(el, fn)`** (H:1941-1949) is scroll-position preservation around height-changing mutations. It calls `packRowSpans()` unconditionally. Its callers are the More/Less toggle (H:2111), the vote click (H:2329), reason send (H:2306) and `mergeRemote` (H:2429). Under pure CSS it reduces to "measure the top, mutate, `scrollBy` the delta". Keep it: browser scroll anchoring does not hold the clicked element steady (H:1931-1932). **`topCard()`** (H:1950-1962) exists for the no-click roam case. It reads the bar's bottom at ≥700px, because the bar is sticky at the top there, and it depends on the inline `display:none` convention.
- Filtering, og insert and the reason box only called the packer to fix row spans. With CSS-derived heights those calls go away.
- Stale-comment warning: CSS H:1238-1244 ("No layout JS remains") and H:2049 ("the ONLY layout thing any JS still does") contradict the live packer. Don't trust either as a spec.

---

## 6. Bugs, races, fragility

- **B1 — CONFIRMED: the signed-out vote nudge closes itself.** `postFb` → `nudgeSignIn` → `openPanel(true)` runs inside the grid's click listener (H:2277,2459-2463). The same click then bubbles to the document-level close-on-outside-click listener (H:2611-2613). The target is not inside `#ffSync`, so the listener runs `openPanel(false)` and `saySync('')`, and the panel never shows. Reproduced with the same listener topology in headless Chrome: `scratchpad/understand/order.html` → `panelHidden=true`. Propose is **not** affected: the submit handler runs after click propagation ends. Fix it in the rewrite with `stopPropagation`, a check against the nudge origin, or by deferring the open.
- **B2 — editorial read state never roams.** `ed-<stream>-<date>` ids enter `syncMap` (H:2381), but W:77 `SID_RE=/^st-[0-9a-f]{12}$/` skips them on POST (W:561-570). They are then re-sent on every push. Read state for the same editorial differs per device.
- **B3 — the `sid | default: id` fallback is half-supported.** A story whose sid is null gets the slug `id`, which is neither a valid `/readstate` key (it is skipped) nor a valid `/submit` `story_id` (W:79 → **400**, shown as "failed (400)"). Latent: 0/80 today.
- **B4 — propose 401 leaves a dead session.** H:2720 calls only `askSignIn`. It does not drop `syncSession:v1`, so the nudged panel still shows the signed-in state ("Synced · rafael", Sign out). Propose's `session()` (H:2701) also skips the `reader` check that main uses (H:2366), so the two scripts can disagree about whether the reader is signed in.
- **B5 — the kill switch misses propose.** C:43-45 says `__FB.enabled` governs the propose form, but H:2694 reads only `.url`.
- **B6 — og image attributes are set too late.** `referrerPolicy='no-referrer'` and `loading='lazy'` are set inside `onload` (H:2637), after `img.src = src` (H:2658) has already sent the request. The request carries the default referrer: no Referrer-Policy header or meta exists in `_includes`/`_layouts`, so the browser default `strict-origin-when-cross-origin` sends the site origin, not the page URL. Hotlink-protected hosts may refuse, and `lazy` does nothing. Set both before `src`.
- **B7 — `/readstate` POST ignores non-401 failures.** 413 (>65536 B) and 400 (>2000 entries) are dropped silently (H:2401), unlike `/prefs` (H:2233). Sending the whole map is also near keepalive's 64 KB body limit. Low risk now: 45-day prune, about 40 B per entry.
- **R1 — `anchored` can pack before fonts load.** Calling `anchored` from `mergeRemote` runs `packRowSpans()` even before `bootPack` (H:1944). A fast `/readstate` reply therefore packs against fallback-font metrics and arms `packOn` early. `fonts.ready` corrects it later. This goes away with pure CSS.
- **R2 — a roamed filter change is not scroll-anchored.** `mergeRemoteTopics` (H:2250-2257) calls `apply()` without `anchored`, while the analogous `mergeRemote` is anchored. A roamed filter change arriving after the reader has scrolled can jump the page.
- **B8 — an untouched default can overwrite a real selection.** `pullTopics` always calls `pushTopics()` after a GET (H:2263), even while local `topicPrefs.ts === 0`, and the Worker coerces ts 0 to `now` (W:638). Scenario: device A has never touched a chip and loads signed in with no server prefs, so the server stores `{topics:[],rs:'',ts:now}`. Device B made a selection earlier while signed out (its ts is older than that `now`). When B signs in, its pull sees the remote as newer and replaces B's selection with A's empty default. This breaks "a later sign-in pushes it up" (H:2179-2180). Client-only fix: never push while `ts === 0`. Side effect today: every signed-in load POSTs `/prefs`.
- **R4 — Escape does two things.** The modal's Escape handler (H:576) and the sync panel's document handler (H:2608) both run when both are open.
- **F1 — the whole main IIFE depends on `#folioGrid`.** The id is also the skip-link target (H:49,253). With no grid, sync and the `__syncNudge` wiring never run. That is why propose is its own IIFE.
- **F2 — script order relies on hoisting.** `held`, `recordPrefsChange`, `session` and `noteLocalRead` are used before their `var` or declaration lines (for example H:2168 before H:2204). This works only because the code runs in one IIFE with function hoisting. Keep a single module, or order the code explicitly.
- **F3 — thin no-JS behaviour.** Without JS the More buttons render and do nothing, `#ffSync` stays hidden (fine), and the chips and read toggles render and do nothing.

---

## 7. Constants (preserve the semantics)

| Constant | Value | Ref |
|---|---|---|
| Local read/sync prune | 45 days | H:1978, 2374 |
| Server readstate age-out | 90 days | W:75 |
| Server session TTL / roll | 90 d idle / daily | W:67-72 |
| KV-lag 401 grace | 60 s from `at` | H:2456 |
| Readstate push debounce | 30 000 ms | H:2389 |
| Prefs push debounce | 1 500 ms | H:2217 |
| TOPIC_CAP (client) / PREFS_MAX_TOPICS (Worker) | 50 | H:2236 / W:80 |
| Font-wait provisional pack | 2 500 ms | H:1921 (deletable) |
| ResizeObserver repack delay | 120 ms | H:1897 (deletable) |
| og insert repack delay | 60 ms | H:2656 (deletable) |
| og IntersectionObserver rootMargin | `600px 0px` | H:2674 |
| Reason max / Worker reason max | 500 input / 2000 | H:2298 / W:52 |
| Propose topic max | 300 | H:410 / W:53 |
| Bar-at-top breakpoint used by `topCard` | `(min-width:700px)` | H:1956 |
