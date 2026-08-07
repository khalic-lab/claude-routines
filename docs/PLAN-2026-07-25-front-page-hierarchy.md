# PLAN v2 — front page: the ranked list is the model

**Date:** 2026-07-25 · **Status:** PARTLY SHIPPED — **Stages 1–5 shipped 2026-07-26**; **Stages 6–9
OPEN** (masonry deletion → CSS-grid ruled layout, thumb-zone controls + tier index as real text, the
wide projection, imagery) · **Supersedes:** PLAN v1 (same path, 2026-07-25) and
`docs/SPIKE-2026-07-25-front-page-redesign.md` §5 + A.8.

**Updated 2026-08-07.** Stage 5 shipped as a straight flip, not behind `--policy`: the shipped form
is `apply_cap`'s per-edition drop order with each stream's newest edition floored at
`MIN_LATEST_EDITION` (`build_stories_feed.py`), which is Amendment A.1's base of the pyramid. Nothing
in Stages 6–9 is built — `home_harness.py` still renders and asserts a masonry board. Stage 6 is the
gate (7 and 8 depend on it, 9 on 8) and it cannot start on this plan alone: **§4 D-II is unanswered**
— "does the front page show ~12 modules with the rest behind beat filters and scroll, or all 80 in
descending prominence? Stage 6 needs the answer; Stages 1–5 do not." Awaiting that decision.
Invariants **I2** (a correct ranked list with no JavaScript) and **I3** (tier reaches assistive tech
as real text) are still owed, by Stages 6 and 7 respectively.

v1 was a plan to refine a masonry packer. That was wrong. This is a plan to **delete** it, because
the page's hierarchy already exists in two places the current code throws away: the ranked order of
`feed.stories`, and a curated short headline sitting unused in `index/stories/*.jsonl`.

**Verification marks.** ⊕ = I measured or read it this session. ◇ = measured by an agent with
method and numbers stated. ○ = reasoned from mechanism, not measured.

---

## §0 What changed from v1, and why

Four inputs, in order of how much they moved the plan:

1. **The mock.** Its legibility comes from **six-to-twelve-word uppercase headlines**, a rigid
   modular band grid with shared baselines, a nameplate rail, and a tier index as real text. v1
   never looked at it — every claim v1 verified was a geometry number.
2. **Mobile-first (Rafael).** Flatten information hierarchy and you get a **list**. Rank = position.
   Size, span and bands are wide-viewport *projections* of list position, not mechanisms. A phone has
   one thumb, so controls belong at the bottom. v1's central device — a splash spanning every
   column — is a **no-op at `cols=1`**, which is where the page is actually read.
3. **An external review (GPT Sol).** Independently reached "retire masonry for CSS Grid", and
   corrected two v1 errors: the dominant story is the mock's **upper-right module, not full width**
   (v1's full-width splash was an invention), and page placement should be a **deterministic
   manifest computed in Python**, not rank inferred in JS from `data-imp` + card height.
4. **Three measurement agents**, which found the two highest-leverage changes on the page — both of
   which are a handful of lines, and neither of which was in v1 or in Sol's proposal.

v1's core diagnosis survives intact: the cap deletes the base of the pyramid (Amendment A.1). What
does not survive is v1's conclusion that theme comes last. **Grid, type, imagery and hierarchy are
one system** — the mock cannot be reached by fixing distribution and placement alone.

---

## §1 The model

```
SOURCE OF TRUTH          ranked list:  feed.stories sorted (date, importance) desc
                                       ↓
BASE LAYER (all widths)  one column, DOM order = reading order.  No JS.
                                       ↓
PROJECTIONS (by width)   ≥700px: 2-column bands · ≥1024: 3-column · ≥1280: rail + 12-col sheet
```

**The base layer already exists and the JS destroys it.** ⊕

```css
.folio-grid:not(.on) .fcard{ max-width:44em; margin:0 auto 20px; }   /* :362 — the list */
```
```js
grid.classList.add('on');   /* :615 — "switch from block-flow fallback to JS placement" */
```

DOM order is Liquid emission order, which is `stories.sort(key=(date, importance), reverse=True)` at
`build_stories_feed.py:632`. So the correct ranked list is the *fallback*, and `.on` repacks it by
height. ⊕ There is **no `.sort()` anywhere in the client script** ◇ — the packer doesn't reorder
deliberately, it reorders as a side effect of greedy shortest-column placement plus a notch-backfill
and steal pass.

This reframes Amendment A.6 ("position must encode rank"). That is not a constraint to add to the
packer — it is a property the base layer **has** and the packer **removes**.

### What this deletes

`_layouts/home.html:637-771` — passes 1–4, the notch machinery, tallest-fit backfill, the adjacent-pair
chooser, the bottom-steal and shift-steal fallbacks. With it goes every bug class v1 spent most of
its verification budget on, including two I reproduced myself:

- the brief row skin costing `maxGap` **200 → 300** at 1440px (⊕ reproduced, paired runs) — caused
  entirely by short cards flipping the pair chooser's notch penalty at `:683`;
- `maxGap=244` at 1024px already violating the harness's own documented `< 200` invariant ⊕.

Both are arguments *for* deletion. v1 treated them as constraints to satisfy.

---

## §2 The atom is the gate — and it is three lines

**The short headlines already exist in the repo, unused.** ⊕ measured myself:

| | parsed lead (shipping) | record headline (unused) |
|---|---|---|
| median chars | 114 | **75** |
| max chars | 311 | **137** |
| median words | 19 | **12** |
| repeated verbatim as the body's opening | **27 / 78** | **0** |
| join rate against the feed | — | **78 / 80** |

The three cards above the fold become `Andy Burnham becomes UK prime minister` (38ch),
`Europe wildfires force 200,000 from homes across France, Spain and Italy`,
`Poland's opposition PiS splits as Kaczynski moves against Morawiecki`.

**Why it duplicates.** Not a prompt defect and not a parser defect — **mixed provenance in the
overlay.** ⊕ `build_stories_feed.py:549` takes the *recorded* `display_body`, `:557` takes the
*parsed* bold lead as `headline`, and `display_body` **opens with that same lead** by spec. And
`load_index_meta` (`:365-367`) never loads `headline` at all ⊕. The function's own docstring already
names the cause and is the reason URL is the join key: ⊕

> *"the post's bold lead and the record's `headline` are written independently by the routine, so
> slugified-headline ids only agree ~28% of the time"* — `build_stories_feed.py:350-354`

**Identity safety:** `hid` is computed at `:539` from the *parsed* headline, before `:557`, so story
ids — and therefore read state — stay byte-stable. ◇ Leave that as-is.

No backfill is needed. The next ordinary writer run regenerates the feed and all 80 cards get
curated headlines.

**The prompt half is still needed**, but it is forward-looking, not blocking: only **6 / 78** record
headlines land in the mock's 3–8 word range ⊕. `tools/dedup/DEDUP.md:17` is the active cause — it
tells the writer the record headline *is* the bold lead. That plus a `headline` bullet in
`routines/_shared/newsroom-ethos.md:15-18` (which enumerates the recorded fields and omits `headline`
entirely) reaches all five writers in one edit. Assembled files — run `routines/assemble.py` and its
`check` guard.

---

## §3 Stages, ordered by leverage

| # | Stage | Files | Est. | Depends on |
|---|---|---|---|---|
| **1** | **The atom, build half.** Carry `headline` in `load_index_meta`; prefer record over parsed lead at `:549`/`:557`; update `ARCHITECTURE.md:825-829`. | `build_stories_feed.py`, `ARCHITECTURE.md` | 1h | — |
| **2** | **Editorial demotion + reorder.** §3.1. | `home.html` | 2–3h | — (parallel with 1) |
| **3** | **The atom, prompt half.** `DEDUP.md` Step A + Step C, `newsroom-ethos.md`, then `assemble.py`. | `tools/dedup/DEDUP.md`, `routines/_shared/`, `routines/*.md` | 1h | — (parallel) |
| **4** | **Verification: published DOM as fixture.** §8. Retires the hand-written Liquid mirror without a Ruby toolchain and without a Liquid interpreter. | `home_harness.py` | 3h | — (parallel) |
| **5** | **Preserve the base of the pyramid** — weighted recency cap behind `--policy`, then flip; pin `--policy` at both `publish.py` call sites; fix `test_feed_sid.py`. | `build_stories_feed.py`, `test_feed_cap.py`, `test_feed_sid.py`, `publish.py`, `_data/homefeed.json` | 4h | 4 |
| **6** | **Delete masonry; the list becomes the primary layer.** CSS Grid, zero-gap modules with shared hairline borders, content-driven row heights, DOM order = rank. One column at `<700px` with no JS required. | `home.html` | 8–12h | 1, 2, 4 |
| **7** | **Controls to the thumb zone.** Bottom bar on mobile, rail on desktop; tier index as **real text** in the same furniture. | `home.html` | 4h | 6 |
| **8** | **The wide projection — the mock.** Rail + 12-column sheet, upper-right dominant module, band alignment, type scale, hairline rule system, red accent, self-hosted condensed woff2. | `home.html`, `head/custom.html`, `assets/fonts/` | 10–14h | 6, 7 |
| **9** | **Imagery + marks.** Grayscale/high-contrast source images in designated feature slots; deterministic SVG diagrams for threads. **Scope with care** — §7. | `home.html`, new generator | ? | 8 |

Stages 1–4 are genuinely parallel (four different files, no shared region). **Stages 1 + 2 together
are the whole visible win before any structural work**, and they total ~4h.

### §3.1 Stage 2 — the two changes that buy the most, measured

**Editorial-first is a template accident, not a ranking decision.** ⊕ `{% for e in feed.editorials %}`
at `:55` emits before `{% for s in feed.stories %}` at `:77`. The two arrays are built independently
(`:632` vs `:644`) and never compared. At `cols=1`, DOM order **is** reading order.

Measured consequences, at three widths: ◇

| width | editorial share of board | first real news story |
|---|---|---|
| 390 (`cols=1`) | 100% (366/366) — span2 is a no-op | y ≈ **4355px, ~5.2 phone screens down** |
| 1024 (`cols=2`) | **100%** (1000/1000) — zero news visible anywhere | y = 1679px |
| 1440 (`cols=3`) | 66% (817/1236) | y = 1974px |

The 1024 band is the **worst case and v1 never measured it**.

Three edits, none touching `edread`, `.fcard__fb` or the rank chip:

1. **Strip `lead` from `.fcard--ed`** (`:56`). v1 claimed editorials carry `.lead` "purely for the
   span=2 side effect" — **that is false** ◇. `:399` sets only `font-style`, so `:421`'s
   `clamp(1.5rem,2.6vw,2.05rem)` — the largest headline treatment in the system — lands on the
   editorial's generic section title. Two independent dominance effects, not one.
2. **Split the Liquid emission** — `{% for s in feed.stories limit: N %}` → editorial loop →
   `{% for s in feed.stories offset: N %}`. **Do not merge editorials into `feed.stories`** ◇:
   `apply_cap` runs at `:633` *before* `load_editorials` at `:644`, so merge-then-cap silently evicts
   real stories; merge-after changes what `feed.count` and the "All N" chip mean; and the schemas
   differ (`headline/summary/why/url` vs `title/paras/kicker`).
3. **Fold the editorial body.** The existing mechanism does **not** apply: `:448` hides
   `.fcard__sum`/`.fcard__why` and never mentions `.fcard__edp` ◇. Needs `:448` extended, a
   `.fcard__more` button emitted for editorial cards (today gated to `s.importance == 1` at `:85`),
   and a decision on peek-one-paragraph vs hide-all. Recommend peeking one. The auto-fold JS at
   `:865-868` then picks it up unchanged. There is **no full page to link to** — `_config.yml`
   defaults every post to `published: false` and only evaluator posts opt in ◇ — so fold-in-place is
   the only option, not a preference.

---

## §4 Decisions needed

**D-I · Roamed topic prefs — unchanged from v1, still open.** ⊕ `worker.js:583-585` **rejects** with
400 above 50 topics rather than clamping, and `home.html:965` branches only on 401. The obvious
one-line concat therefore kills topic *and* read-state roaming permanently and silently at key 51;
it also stops "back to All" propagating, reversing documented replace semantics at `:923-925`. And
`worker.js:612` re-serialises only `{topics, rs, ts}`, so a separate `held` field cannot roam — the
ambiguity is structural. **Recommend: held keys win, capped client-side at 50, non-2xx surfaced.**
The cap and surfacing are needed under every option and land in Stage 4.

**D-II · How many stories does the front page show?** The mock shows ~8 prominent modules. The page
shows 80 ⊕ (live: 24 leads / 52 features / 4 briefs). This is a bigger lever than the cap ratio, and
it is an editorial call: does the front page show ~12 modules with the rest behind beat filters and
scroll, or all 80 in descending prominence? Stage 6 needs the answer; Stages 1–5 do not.

**D-III · The presentation manifest.** Sol's proposal, and better than v1's JS-derived rank because
it is unit-testable rather than only observable through headless Chrome. Emit from
`build_stories_feed.py`: `{"front_page": {"primary": …, "features": […], "briefs": […], "editorial": …}}`,
selected deterministically (freshness, importance, stream priority, original order) with a diversity
guard against adjacent same-topic modules.

Two things to settle before adopting it. **(a)** ⊕ `tools/tests/test_feed_sid.py:121-134` rejects any
new top-level feed key except `sid`; that test must be amended, deliberately. **(b) Static
assignment collides with client-side filtering** — if slots are baked to story ids, filtering by beat
empties named slots. So the manifest can only be the *unfiltered default composition*, with filtered
states falling back to ranked bands. Name that, or the slot machinery will be written twice.

---

## §5 Invariants

| | |
|---|---|
| **I1** | DOM order == rank, at every width. Nothing may reorder for layout convenience. This is what deleting the packer buys; a future "optimization" that repacks by height is a regression, not a tuning. |
| **I2** | The page must be a correct ranked list with **no JavaScript**. Today it already is (`:362`); Stage 6 must keep it so. |
| **I3** | **Tier reaches assistive tech as real text.** ⊕ Today it reaches it nowhere: `.fcard__rank` is an empty `<span>` (`:60`/`:82`), the words are CSS `::after` (`:388-394`), and `.ff-legend` (`:45`) is `aria-hidden="true"` **and** `display:none` below 720px. Since post pages were unpublished, the feed is the only reading surface. Stage 7 owns this. |
| **I4** | **Editorials are never splash/primary candidates.** ◇ True today for a stronger reason than v1's C3 assumed: `load_editorials` never assigns `fresh` at all (only `load_recent` does, `:635`), so editorials are on a separate code path. Assert it; do not inherit it by accident. |
| **I5** | No literal expected counts in any test. Derive from `_data/homefeed.json` and inject. Every asserted cardinality across nine specs was a day-stale literal, and they disagreed (24/52/4 reproducible and live, 23/53/4 committed, 14/64/4 asserted). |
| **I6** | Story ids stay byte-stable, or read state breaks. `hid` from the parsed lead at `:539` ◇ — do not "clean this up". |
| **I7** | Never a resident server. Per repo identity; the manifest is a build artifact, the plane stays serverless. |

---

## §6 Instrument facts

| Fact | Consequence |
|---|---|
| ⊕ Headless Chrome clamps `--window-size` width to a **500px floor**; `--hide-scrollbars` and `--force-device-scale-factor` don't lift it. | Every "390px check" ever run was at 500px. **Fix: render inside an `<iframe>` of the exact width** in a larger window — media queries fire against the iframe viewport. ◇ Verified by injected `innerWidth` reading exactly 390. |
| ◇ `cols` flips 1→2 at viewport **≥700px**, not ~676 — `W = grid.clientWidth` is viewport minus a 24px board inset. | Mobile band is `<700px`. Test 390, 640, 690, 700, 1024, 1440. |
| ⊕ Headless subtracts a phantom 15px classic scrollbar; production macOS uses overlay scrollbars (`bodyScrollW` 1425 vs `innerW` 1440). | `--hide-scrollbars` on every invocation; restores 1425→1440. |
| ◇ Colour scheme: only `--blink-settings=preferredColorScheme=1` (light) / `=0` (dark) work in Chrome 150; `=2`/`"dark"`/`"light"` crash the renderer or are ignored. | Both schemes, every capture. Theme only recolours, never relayouts ◇. |
| ⊕ Test baseline: **455 tests, 1 known failure** (`test_reconcile_lint…test_real_cuba_story_is_resolved_by_merge_not_flagged`). | A second failure blocks the commit. |
| ⊕ Every viewport-height-dependent rule is structurally untestable today — all documented harness invocations use window heights 2800–9000. | Any `vh` rule needs a real 390×844 / 640×844 capture plus a landscape case. |

---

## §7 Cut, and why

**The Liquid-subset interpreter (v1 Stage 1, ~350 lines).** Sol is right to reject it. But its
alternative — build real Jekyll locally — is not free either: ⊕ `jekyll` is **absent**, system Ruby
is **2.6.10**, Bundler 1.17.2, there is no `Gemfile.lock`, and `remote_theme:
mmistakes/minimal-mistakes@4.26.2` needs network at build time. That is an rbenv + Ruby 3 project.
**Use the published DOM instead** (§8) — it is the real Jekyll output and it is one `curl` away.

**Stage 9 of the spike, as specified.** ⊕ It depends on `--rw`, `--rw-heavy`, `--pad` and `--red`,
none of which exist anywhere in the repo, and its filler completeness assertion passes *because* of
its worst bug (a `> 0.5` gap test paints paper over every horizontal rule — the design thesis). The
*goals* are not deferrable and live in Stage 8; that document was.

**The type-scale guards.** ◇ `getComputedStyle().fontFamily` returns the specified list, never the
resolved face, and `document.fonts.check()` returns true for a nonexistent family — both proposed
detectors are tautologies. The condensed stack resolves on macOS Chrome only via a PostScript name,
and the resolved face vs Arial Narrow differ by a **full line** on the median lead headline. So the
self-hosted woff2 is a Stage 8 **prerequisite**, not polish.

**`--band0-policy` and `ABS_STREAM_FLOOR`.** ◇ The first ships a flag no measurement pass has
exercised at production scale; the second is defined, documented as "no live stream may be capped to
zero", and referenced nowhere.

**Deterministic SVG marks are scoped, not cut.** The mock wants per-thread abstract diagrams, a
tactical play diagram, and two maps. That is a content-generation project with no pipeline, not a CSS
decision. Stage 9 is a placeholder until it has a design of its own.

---

## §8 Verification: the published page is the fixture

⊕ `https://khalic-lab.github.io/claude-routines/` returns 344KB with all 82 cards and the correct
`data-imp` distribution. It **is** the real Jekyll output, theme included.

So: **scrape the published card DOM as the harness fixture and inject local CSS/JS over it.** Markup
becomes production-true by construction, the hand-written mirror dies, and no Ruby is involved. That
also retires the v1 defect where the harness's editorial mirror was 52px short and printed the wrong
tooltip field ◇.

The cost, stated plainly: you cannot preview unpushed *markup* changes. That matters only when
changing markup, and fidelity is then provable against the next deploy. (Incidentally the fetch
settled a discrepancy: the live page is **24/52/4**, matching a fresh rebuild, not the committed
23/53/4 ⊕.)

**Per-stage protocol.** Capture at 390 / 640 / 700 / 1024 / 1440, both schemes, with
`--hide-scrollbars` and the iframe technique below 700. Assert structure (order == rank, no overlap,
zone boundaries, real-text tier). Then **look at the images** — for a claim about whether a page
reads as a hierarchy there is no number, and not looking is what produced v1.

---

## §9 Residual exposure

- **Sub-700px behaviour has barely been measured**, and it is the primary surface. The iframe
  technique closes the instrument gap; the coverage gap is still open.
- **The manifest/filter interaction** (§4 D-III) is unresolved by design, not by omission.
- **`routines/weekly-evaluator.md:69`** tells the Sunday Evaluator to flag "an edition with no 3 /
  several 3s" as the writer's error ⊕. Under a weighted cap old editions read ~50% leads, so the
  Evaluator may manufacture findings against writers every Sunday. ○ One measurement pass before
  Stage 5's flip.
- **`ARCHITECTURE.md:821-822`** describes the front page as "a per-STORY masonry grid
  (importance-sized cards…)" ⊕ — false after Stage 6, and this file is the repo's declared single
  source of truth.

---

## §10 The composition reconciliation — why the masonry band became conditional

**Date:** 2026-07-25 · **Status:** RESOLVED · Supersedes the task-#3 directive's item 2.

The owner ruled that text is never cropped. That killed the per-tier line-clamps (`c9f0ec1`) and
handed the front page back its full-length modules, which re-opened the question the clamps had
closed: what absorbs the height variance. A three-agent prior-art fan-out was run to answer it. Its
output is internally contradictory, and the contradiction is the whole finding.

**The css-masonry agent** recommends a hybrid band system — static grid for the top band, and a tail
band using the grid row-span technique (`grid-auto-rows` at a fine unit, per-item spans measured by
JS via `ResizeObserver`). It is right that this is the only mechanism satisfying all four hard
constraints *at once, today*: no truncation, DOM order == rank, JS-off renders full content, and all
three engines. Native CSS masonry (`display: grid-lanes`, Grid L3) ships stably only in Safari 26;
Chrome 140 has a flagged alternate syntax under rework and Firefox an outdated 2020 implementation,
so it is a progressive enhancement behind `@supports`, never a foundation.

**The news-design agent, studying five live fronts, concluded the opposite:**

> "None of the mainstream fronts studied use algorithmic masonry … for their primary news package.
> Height variation comes from a small, fixed enum of card formats … so heights vary in discrete
> steps, not continuously. True justified/masonry packing … shows up on these sites only in
> secondary contexts: photo galleries … not the main story hierarchy."

> "…implement as a small enumerated set of card-format components … i.e. stepped/quantized masonry,
> not an auto-packing algorithm."

Its first recommendation is a written length budget enforced **at authoring time, never at render** —
the Guardian's per-front `trailText` field.

**The resolution.** Both agents are right about different worlds. The row-span band is correct *if*
continuous full-text height variance is a fixed constraint. It is not: the owner approved the `deck`
field the same day — a writer-authored front-page standfirst with a per-tier character budget — which
attacks that variance at its source and makes module heights quantized by tier, exactly the shape the
news-design agent found on every real front. Building an observer against a height distribution we
know is about to shift is the one thing "measurement wins" argues against.

Three further considerations pointed the same way. This repo has killed JS layout twice
(`9344d2d`, `297ee9c`), and the row-span technique reintroduces its class — JS measuring rendered
height and writing layout — with four known failure modes (first-paint measurement race, sub-pixel
drift, a no-JS state needing its own guard, and re-measure on font load). The mock is a quantized
broadsheet, not a Pinterest wall. And the void it would fix is currently **median 189px / max 1,978px
at 1440** and shrinking editorially.

A concrete collision confirmed the sequencing. `grid-auto-rows` at a fine unit applies to the whole
grid, including the explicitly placed dominant at `grid-area: 1 / 1 / 2 / 13` — under an 8px unit the
splash renders **8px tall**. Masonry-ing the tail therefore forces the top band's row placement to
become JS-dependent too, contradicting the directive's own item 1 ("TOP BAND — UNCHANGED … no JS,
exact DOM==rank"). Solvable with a separate grid container for the tail, but that is an architectural
choice, not an implementation detail.

**What ships instead, in order:** the deck render (folded card = headline + deck + why, `More`
expands the body; deck-absent renders exactly as today, indefinitely, because the feed stays mixed
for weeks); then a quantized tail using stepped CSS allocations with no observer; then the rail
chrome and nameplate.

**The masonry band is conditional, not cancelled.** Once the feed is majority-deck, re-measure the
void distribution; build the row-span band exactly as amended **iff** median slack at 1440 still
exceeds 150px. The amended no-JS requirement stands as its spec — the fine row unit is applied only
by the span-computing JS via a class it sets, never as the stylesheet default, so an unspanned card
can never clip or overlap. **The tail band gets its OWN grid container** — decided now rather than
re-litigated then, because a fine `grid-auto-rows` unit applies to every item in its grid, so sharing
one container would make the dominant's height JS-dependent and break item 1. A separate container
keeps the top band statically placed and no-JS-exact. So does the tail-band drift bound: *no tail module may render visually
above any module ranked more than one column ahead of it*, counted at every width and both themes.

**I1 is unchanged and non-negotiable throughout.** The deleted packer's sin was deriving *position*
from packing state, so height fed back into order. Row-span derives only *extent*; auto-placement
still takes position from DOM order. That distinction is what would make the conditional build safe —
it is not a licence to revisit shortest-column packing, which the research rejects outright as
unbounded and content-dependent.
