# B-prime: front page and day editions

B plus A's day editions and C's grafts; every edition says which span each desk's reporting covers.

## Merged from

- **B (base):** front, index rows, tokens, ladder, type, rail, `<dialog>`, `.js` gate.
- **A:** each date is a `<section>` with a full-width `h2 <time>` header, plus the edition read rule with its explicit tick/un-tick override.
- **C:** `<search aria-label="Filter the stories">` with Sync outside the chip strip; two-way links ("→ Science desk's view", "← Wed 23 Sep edition"); `overflow-wrap:anywhere`; the whole-lede serif-italic heading for titleless editorials, with "1. " stripped.

## Period rule

For each (date, stream) edition, **start** = the previous `_posts/…-<stream>.md` + 1 day (a first-ever edition starts at the cap, else on the day itself), then **capped** to the window its `routines/src/<stream>.md` states: news "last ~24 hours" = 1 day; science, weekend, sports "past 7 days" = 7 inclusive days; ai-ml "since the last AI/ML edition" = uncapped.

Result: NEWS · 24 SEP, SCIENCE · 17–23 SEP, AI/ML · 19–22 SEP, SPORTS · 15–21 SEP, WEEKEND · 13–19 SEP. Day headers, front cards and editorial kickers carry the tag. "How to read this page" (now at every width) and How this works explain the tags.

**Discrepancy:** post footers print date−7..date, which overlaps the previous edition by a day. The tags use the non-overlapping rule.

## Front selection

Walk the newest dates until they hold four leads or features. The lead slot takes the first lead; the other three take leads and features in board order, and briefs fill in only when there are too few. The Desk's view is the newest editorial.

First-round rulings still hold: R7 (editorials boot folded), R2 (briefs fold "why"), R15 (an opened front card takes its band's width; headlines never grow), and every lifted item keeps an "↑ On the front" pointer.

## Review fixes (second round)

- **Row measure:** an opened index row sets its body in two columns where they fit (`columns:2 17em`, as opened front cards do), and why/summary carry a 36em cap. The longest line of the opened Yemen row is now 50–80 characters at every width (it was 117–153).
- **Dead links:** `apply()` hides any in-page link whose target is hidden.
- **Focus:** `.seg` loses `overflow:hidden`, and its end buttons are rounded instead. The chip strip gets 4px room and a focusin scroll-into-view, and drops its fade while a chip has `:focus-visible`. On phones the bar is two rows, [read state · Sync] over a full-width strip (at 360 the old strip, 81px, was narrower than one chip). DOM order is seg, Sync, strip, so visual order equals focus order.
- **Disclosure** never dims (4.70:1).
- **Read dim** is by colour toward `--muted`, not opacity. The lowest read text is 4.70:1 (it was 3.68).
- **Counts:** one rule for every chip: its number is what shows with it pressed (a beat chip counts active ∪ itself, so a held chip shows the current total).
- **Day header under a filter:** "5 of 9 stories shown", and desks with nothing shown drop their tag.
- **No-JS:** How this works is `<a href="#hiw">`, which JS upgrades to `showModal()`. Without JS it falls back to `dialog:target`, and the inert Close is hidden.

## Checks (`check.mjs` → `check.out`)

8 Chromium widths (360–1600) plus WebKit iPhone 15, 5 states: **516/516 pass** (default 111, expanded 108, unread-science 117, beat-sports 99, empty 81). No-JS 2/2: nothing hidden, no inert control, #hiw reachable, key visible.

New assertions:

- `measure`: 45–90 characters per line.
- `focus`: Tab through the masthead and bar; every ring is nonzero, unclipped and unmasked. `focusMain`: on phones, a control tabbed to from under the bar lands above it.
- `links`, `dayMeta`, `disc`, `readContrast` (≥4.5:1), `multiBeat` (Sports held).

**Fault injection: 22/22 caught**, each flipping its own assertion.

## Trade-offs

1. The phone bar is two rows (~86px plus the safe area).
2. At ≥1024 the folded Desk's view leaves a 79–97px void beside the lead; R7 forbids filling it.
3. "Neighbours flow below" is exact only when the first story opens.
4. iOS Safari (R17) is still unverified.
5. Builder fields: `period`, `front`, `edition`, editorial `sid` and topic union, `build_at`.
