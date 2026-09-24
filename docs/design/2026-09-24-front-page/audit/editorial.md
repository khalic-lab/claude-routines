# editorial — why do the AI editorials "appear days after they were published"?

Scope: read-only audit. Repo files cited `file:line`; live site measured 2026-09-24 (~12:00Z, deploy of 3ecf3f18 + drain commits). All raw evidence sits beside this file:
`ed_history.tsv`, `ed_history_july.tsv` (editorial set per homefeed revision), `actions_runs.tsv` (600 Pages runs, 07-09 to 09-24), `deploy_lag.tsv`, `deploy_lag_all.tsv`, `stale_votes.tsv`, `measure_ed.out`, `unread_sim.out`, plus screenshots `ed-*.png` and `unread-*.png`. The scripts are `measure_ed.mjs` and `unread_sim.mjs`.

## 0. Verified premises (a)-(c)

- **(a) TRUE for every editorial that exists.** Every editorial that reached `_data/homefeed.json` did so in its own post's commit (all of 07-18 to 09-23 in `ed_history.tsv` and `ed_history_july.tsv`). Example: Science 09-23 is present in eed8848a at board index 13. At the first build of its day, an editorial sits at board index 4-15.
- Three Science editions never produced one: 07-22, 08-05 and 08-12. None of those posts has a "Why it matters" section; their `## ` headings are only the three beat sections plus the Coverage footer (`_posts/2026-08-05-science.md:12,29,41,55`; `_posts/2026-08-12-science.md:12,24,36,55`; `_posts/2026-07-22-science.md:19,52,83,114`).
- This is writer variance, not a parse failure and not lateness. After 08-05 the feed kept serving science 07-29 (afef4c18), because `by_stream` keeps the newest edition that HAS a section.
- **(b) TRUE, and it extends back to 07-09.** Of 141 homefeed commits since 07-09, exactly one reached a successful Pages deploy more than 30 min after commit (`deploy_lag_all.tsv`). That one is **Science 2026-08-26 (51c65565): 18.9 h**. Its own run was `cancelled` and stayed pending until 08-29. The drain commit's run 6b7144fc was a `startup_failure`. The page first deployed at 08-27 10:15Z, with the next News commit b8871853. The ntfy notification for that edition was drained at 15:30Z the same day (6b7144f), so the reader was pinged about 19 h before the site had the edition. Every other editorial deployed within 0.7-2.5 min (`deploy_lag.tsv`).
- **(c) TRUE.** The sort key is `(date, 0 if editorial else importance, -position)` descending (`tools/build_stories_feed.py:1066-1068`), so each editorial closes its own date block. The live DOM has 83 `li.fcard`, which matches board length 83, with 0 kind mismatches (`measure_ed.out`).
- **No runtime data fetch.** The board is baked at Jekyll build time (`_layouts/home.html:42` `site.data.homefeed`). There is no service worker anywhere (grep of `_layouts`, `_includes`, `assets`, `*.html`). The live response carries `cache-control: max-age=600` (checked with curl -I), so CDN and HTTP caching can delay a new edition by at most about 10 min.
- **Expiry cannot delay an editorial, only drop it.** `load_editorials` gates are `ED_MAX_AGE_DAYS=5` (`build_stories_feed.py:795`, `:854`) and `live_editions` (`:856`). Both only remove an editorial. MIN_LATEST_EDITION (`:1161`) keeps the commented-on edition on the board. By design each weekly editorial is live for 6 builds-days (D..D+5), which the history confirms: weekend 09-12 left on 09-18, sports 09-14 left on 09-20, science 09-16 left on 09-22 (`ed_history.tsv`).
## 1. Ranked causes (the ranking changed after the check on the 07-25 owner report; see the "Counter-evidence" paragraph under Unread)

Final order:
1. Desktop masonry misfiling, §"#2" below. It is always on at ≥700 px, and it was measured.
2. Stale resumed tab, §"#3". It was proven once, and it is the only cause that gives multi-day lateness.
3. Unread resurfacing, §"#1". The mechanism was measured, but the owner's 07-25 behaviour cuts against its precondition.
4. Beat filter hides editorials, §"#5".
5. Deploy wedge, §"#4". One 19 h case.

The section numbers below are kept as first written. Read them in the order above.

### #1 (DEMOTED to rank 3): the Unread filter re-surfaces every UNTICKED editorial, next to today's stories, for up to 5 days
Mechanism, all cited:
- An editorial's read id is `ed-<stream>-<date>` (`home.html:280`, `:1983`). The only implicit read path is "opening the headline marks read" (`home.html:1967`), and editorials have no headline link: the `<h2>` is plain text (`:292`). So an editorial is read only when the reader ticks ✓ on it explicitly.
- `matches()` hides a read card under Unread (`home.html:2036`) and shows every unticked editorial.
- `readCounts()` excludes editorials from the "Unread N" chip (`home.html:1999-2006`), so the chip does not tell the reader that editorials are in the set.
- `.is-filtered` drops the composed band and day structure (`home.html:976`, `:2050`), so the filtered view is the unread cards in board order.

Measured on the LIVE site (`unread_sim.out`, screenshots `unread-c1440-cut2026-09-24.png`, `unread-iphone-cut2026-09-24.png`). Setup: all stories dated before 09-24 marked read, editorials not ticked, Unread selected, the state a daily reader is in on 09-24.
- At 1440 the first screen shows 4 cards: the one 09-24 News story at (top 77, left 202), **Science 09-23 editorial** beside it (top 77, left 607), **Sports 09-21 editorial** (top 77, left 1012), and **Weekend 09-19 editorial** (top 297). Those editorials are 1, 3 and 5 days old, sitting in the first row next to today's only story. The chip reads "Unread 1" while 4 cards show.
- On iPhone (393 wide) the same 4 cards are stacked at 175, 368, 630 and 916 px, so all of them are on the first screen.
- With stories read through 09-22 instead, the editorials still close the unread list at 2129/2337/2477 (1440), behind 12 unread stories.

So a reader on Unread who does not tick editorials sees each one at the top of the page every day for 5 days after its edition, beside that day's news. That is literally "appearing days after they were published".
- **Evidence the owner reads on Unread:** owner report "signed in, Unread selected, every story read" (`home.html:377`), and the roamed "Unread with everything read" boot case (`home.html:1848`). Prefs roam across devices (`home.html:2174-2192`).
- **Counter-evidence (this is why it was demoted).** That same report (commit dc974e8, 2026-07-25 22:41) describes an EMPTY board under Unread.
  - At dc974e8^ the editorial cards were `<article class="fcard fcard--ed" data-story="ed-…">` inside the filtered set (`git show dc974e8^:_layouts/home.html`: lines 213 and 1379 `grid.querySelectorAll('.fcard')`, and line 1532-1533 `matches()` with `isRead`).
  - The feed at the time carried weekend 07-25 and sports 07-20 editorials (891b7990, `ed_history_july.tsv`).
  - A board that was empty therefore means the owner HAD ticked both live editorials. The commit's harness reproduces the report as "every card's ✓, then the Unread button" (dc974e8 diff of `tools/home_harness.py`).
  - So the owner does tick editorials, at least sometimes, and #1 holds only if that habit is inconsistent.
- The mechanism itself is real and measured, and it is a bug regardless of the habit: "Unread 1" beside 4 visible cards.
- **UNVERIFIED:** whether the owner ticks editorials consistently. The Worker holds read-state, and I did not access it. The 07-25 evidence above says he did on that day.
- This is also a plausible real content of the earlier "they keep reappearing" report (`build_stories_feed.py:797-805`). The 7→5 day fix shortened the resurfacing window but did not remove it.

Fix:
- **Layout/JS side (primary).** Give editorials a read rule. An editorial counts as read when the reader ticks it, OR when every story of its own `(date, stream)` edition is read. The last condition is the one the reader already meets, and an editorial is commentary on that edition.
- Alternative: under Unread, show an editorial only while its edition still has an unread story.
- Either way, make the chip honest. Count unread editorials separately ("Unread 1 + 3 editorials") or not show them.
- The card needs `data-date`/`data-stream` attributes for the edition join. Today the li carries neither (`home.html:280`, `:309`).
- Data side (optional): emit `edition` = `"<date>-<stream>"` on board items so the page does not reparse ids.

### #2: Desktop masonry files each editorial beside the NEXT (older) day's first cards
- **Mechanism:** a 3-column (≥1024) or 12-track/span-4 (≥1280) grid (`home.html:878-879`, `:971-976`), with 4 px row spans written by JS (`:1821`, `:1873-1876`) and sparse DOM-order auto-placement (`:885-895`).
- A daybreak is only a small label inside the first card of a date (`home.html:283`, `:318`, `:1291`), not a row boundary. Columns therefore interleave days, and the last card of a block (always the editorial, per build_board) lands level with the next date's first cards.
- Measured on LIVE (`measure_ed.out`, `ed-c1440-weekend-2026-09-19.png`):

| width | editorial (y range) | next-older daybreak top | Δ top | share of the editorial's height beside older-day cards |
|---|---|---|---|---|
| 1440 | Science 09-23 1925-2273 | 09-22 @2161 | -236 | ~32% |
| 1440 | Sports 09-21 6349-6729 | 09-20 @6449 | -100 | ~74% |
| 1440 | Weekend 09-19 8945-9261 | Fri 18 @8957 | **-12** | **~96%** |
| 1024 | Science 2166-2514 | 09-22 @2354 | -188 | ~46% |
| 1024 | Sports 6550-6926 | 09-20 @6646 | -96 | ~74% |
| 1024 | Weekend 9122-9458 | 09-18 @9210 | -88 | ~74% |
| iPhone | all three sit directly above the next daybreak (Δ = -own height) | | | 0% (single column) |

- In the screenshot, "WEEKEND · CROSS-CUTTING THREADS · SEP 19" sits in the right column level with the "FRI 18 SEP" daybreak card. Its row-mates are Sep 18 stories ("Iran strikes tanker", "OpenAI to test ads in ChatGPT", "Diffusion LMs…"). On desktop the editorial reads as filed in an older day's block.
- This is misplacement, not lateness, but a reader scanning rows can read it either way. Mobile is correct.

Fix (redesign, layout side): make each date a structural zone, e.g. `<section aria-labelledby>` per date with its own grid, or a full-width daybreak row (`grid-column:1/-1`). No card of day D can then share a row with day D-1. That is the "content zones that cannot overlap" requirement. The editorial should close its own zone, for example as a full-width strip at the end of the zone. The board data already supports this: `daybreak` is computed on contiguous runs (`build_stories_feed.py:1093-1100`).

### #3: Stale document, where a tab is resumed without reload (evidence: 1 hit)
- **Hard evidence:** at 2026-08-15T19:37:59Z the owner up-voted `ed-weekend-2026-07-25` (`feedback/2026-08.jsonl`, surface "home", reader "rafael", `ts` is server-stamped at `tools/feedback-sink/src/worker.js:299/334`).
- That editorial left the live board at a704b505 (2026-08-01T07:56Z), and every Pages deploy after that succeeded (`deploy_lag.tsv`).
- Authenticated calls are origin-locked to `https://khalic-lab.github.io` (`worker.js:62`, `:130`), and only `home.html` posts `surface:'home'`.
- Conclusion: the owner was reading a homepage document at least 14.5 days old.
- Rate: 1 of 197 home votes landed on an item no longer on the board (`stale_votes.tsv`). The mechanism is real but rare in the vote record. The vote record only catches it when a stale card is voted.
- **Page gap:** no freshness check on resume. The only lifecycle hooks flush sync state (`home.html:2404-2407`). There is no `pageshow`/`persisted` or visible-again handler, and no build stamp to compare.
- iOS Safari tab/page-cache restores and "open ntfy link → existing tab" do not refetch. Notifications click through to the bare homepage (`pending-notifications/*.json` `"click": "https://khalic-lab.github.io/claude-routines/"`). A reader in that state first sees an edition's editorial whenever the tab finally reloads, which can be days later.
- Fix (JS, zero infra): bake a build stamp, either `feed.generated` plus a commit or time value in a `<meta>`. On `pageshow` with `e.persisted`, and on `visibilitychange`→visible after more than 10 min, fetch the page or a tiny stamp file with `cache:'no-store'`. If it is newer, show a "New edition — reload" bar, and never auto-reload under the reader.

### #4: Pages deploy wedge, one ~19 h case (08-26 Science)
- See §0(b). This is not "days", and it has not recurred in 141 commits.
- Fix (ops, not frontend): the bridge's wedge self-heal should also trigger when a post commit's run is `cancelled`/`startup_failure` and no success follows within about 15 min. Today the site waited for the next day's News commit.

### #5 (visibility, not timing): any beat chip hides every editorial
- Editorial `li` has `data-topics=""` (`home.html:280`). `matches()` returns false for it whenever `active.size>0` (`home.html:2038-2041`), and the beat selection roams across devices (`home.html:2174-2192`).
- A reader on a beat never sees an editorial until they return to All, at which point up to 5 days of them "appear".
- Fix: either give editorials their edition's topics (the union of the edition's story topics), or always show an editorial whose edition has a visible card.

### Ruled out
- Build-time absence on the edition's day: premise (a) holds.
- Expiry/`live_editions`/MIN_LATEST_EDITION: these only drop an editorial, never delay one (§0).
- CDN/HTTP caching: 600 s max-age.
- Service worker: none exists.
- Client re-sort or re-date: no JS touches order. Only `display` and `.is-filtered` change (`home.html:2042-2048`), and `order`/`dense` are banned (`:895`, `:1473`).
- "Just in" only applies to stories (`home.html:363`).
- Date semantics: the kicker and date line print the edition date (`build_stories_feed.py:876-881`, `home.html:284`, `:297`). The Weekend date is the Saturday it was filed. The prose is a retrospective on the week ("The week's real AI frontier…", `_posts/2026-09-19-weekend.md:22`), which is content, not a date bug. Science is filed at about 15:20Z on Wednesday, so a morning reader first meets it on Thursday: a 1-day effect at most.

## 2. Folded / titleless rendering (redesign constraint)
- Weekend 09-19 has `title:''`. Its lede "1. The week's real AI frontier was trust…" exceeds `ED_TITLE_CAP=90` (`build_stories_feed.py:756`, `:759-791`; source `_posts/2026-09-19-weekend.md:22`).
- Folded, the card shows only the kicker, "AI editorial", the disclosure, More and the date. The prose is hidden (`home.html:1559`) and there is no `<h2>` (`:292`).
- It is visible (316 px at 1440, 265 px on iPhone), but it has no content. That makes it easy to skip on its day and easy to notice only later.
- The feed has shipped 7 titleless editorials since 07-29: science 07-29, 09-16; weekend 08-01, 08-29, 09-05, 09-12, 09-19 (`ed_history*.tsv`).
- The never-crop ruling forbids truncating the lede (`build_stories_feed.py:771-777`).
- Redesign fix: show the first sentence of para 1 folded, or show the whole lede as a standfirst, which is a fold rather than a crop.
- Data-side alternative: ask the Weekend writer for a ≤90-char bold lede.

## 3. Single most likely explanation: the evidence is NOT conclusive
**Best single candidate: the desktop masonry misfiling (#2).**
- It is the only mechanism active on every desktop page view today, with no precondition, and it was measured on the live site. At 1440 the Weekend 09-19 editorial's top is 12 px above the "Fri 18 Sep" daybreak card, and ~96% of its height sits beside 09-18 cards. Sports and Science each sit beside the next-older day's lead cards.
- Each editorial therefore reads as belonging to a different day from its edition.
- It is a one-date-block displacement, not literal multi-day lateness.

**If the owner means literal lateness (seeing an editorial for the first time days after its edition), the candidates are:**
- the stale resumed tab (#3). It is the only mechanism with proven multi-day magnitude (≥14.5 days on 08-15) but a low observed rate (1 of 197 votes);
- Unread resurfacing of unticked editorials (#1). The mechanism is measured, but the owner is shown ticking editorials on 07-25;
- a beat chip hiding editorials until the reader returns to All (#5).

The one deploy lag (08-26, 19 h) cannot explain a recurring report.

**Fixes worth shipping regardless of which cause is his:**
- per-date structural zones (fixes #2);
- an edition-based read rule for editorials and an honest Unread count (fixes #1);
- a resume-freshness check (fixes #3);
- editorials inheriting their edition's topics (fixes #5).

## 4. One clarifying question for the owner
"When you saw an editorial days late, were you on the Unread tab, and had you already seen it on its own day, or was that the first time it showed up for you?"
- Seen before, on Unread → cause #1.
- First time → #3 or #4.
- On All, looking out of place among other days → #2.
