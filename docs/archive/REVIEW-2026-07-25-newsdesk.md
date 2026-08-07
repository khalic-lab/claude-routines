# Fresh-Eyes Newsdesk Review - 2026-07-25

**Verdict:** Not release-ready. The redesign has strong editorial intent, but the current system
cannot yet prove that an edition reached `main`, that every selected story reached the reader, or
that synced reader state survives production storage semantics. Those are newsroom fundamentals,
not polish.

**Scope:** Final state at `ae324a66a302271c47e6b6c6f4e2202982cd9738`, reviewed against the
start-of-day base `c647dda11e1339f60af3f35333d6f201e769a6d5`. The range contains 63 changed
files, 8,056 insertions, 2,087 deletions, and a clean worktree before this document was added.
Committed routine and bridge artifacts were reviewed where they expose the real behavior of the
changed paths. No implementation file was changed as part of this review.

**Severity summary:** 1 blocker, 9 high, 11 medium, 5 low. An item marked *inherited* predates
today's first commit but is included because today's work expanded its blast radius or relied on it
as a supposedly safe foundation.

## Release Blocker

### R1 - Detached routine runs can report success without publishing their commit

**Scope:** Inherited, expanded today to the evaluator path.

`commit_and_push()` commits the checked-out `HEAD`, then runs `git push origin main`, which pushes
the local `main` ref rather than the newly created detached commit
(`tools/publish.py:255-297`, especially `:283` and `:296`). The routine environment is known to run
detached with a stale local `main`; the prior evaluator records that exact state in
`_posts/2026-07-19-evaluator.md:148-154`. A detached-HEAD reproduction committed a new edition,
returned `ok`, and left the bare origin on its previous commit. The documented manual fallback
repeats the same command at `tools/dedup/DEDUP.md:190-194`.

**Impact:** A routine can print `DONE`, disappear with its sandbox, and never publish the brief,
feed, notification, feedback-derived profile update, or evaluator review. This is silent edition
loss.

**Correction direction:** Push the commit being published (`HEAD:main`), make every retry step
fatal when it fails, and verify that `origin/main` resolves to the committed SHA before printing
`DONE`.

## High Severity

### R2 - The publisher's success contract is false on several other failure paths

`git add` is run without checking its result (`tools/publish.py:261-274`), and
`staged_changes()` treats every non-zero `git diff --cached --quiet` result as "changes", including
an actual Git error (`:245-252`). With `.git/index.lock` present, a reproduction logged
`git-add: FAIL`, performed a no-op push, and returned `DONE` while the edition stayed uncommitted.

The same permissive policy applies to the reader-facing build: `record`, anchoring, footer,
source lint, the hard date lint, feed generation, and source health all have ignored return values
at `tools/publish.py:358-397`. The date linter explicitly exits non-zero for a wrong weekday
(`tools/dedup/dedup.py:1219-1240`), yet publication continues. Omitting `--notify-body` merely skips
the notification at `tools/publish.py:399-406`. Because ordinary post pages are unpublished
(`_config.yml:21-38`), a failed feed build means the edition has no reading surface.

**Impact:** "DONE" does not mean staged, valid, visible, or notified.

**Correction direction:** Define a strict fatality matrix. Staging, record integrity, hard date
lint, homepage feed generation, required notification creation, commit, and push must gate success.
Keep genuinely analytical extras such as plane refresh best-effort.

### R3 - Homepage metadata leaks across editions that reuse a source URL

`load_index_meta()` stores one record per normalized URL across the whole window
(`tools/build_stories_feed.py:349-374`). Filesystem glob order silently decides which record wins,
and every parsed edition then reads that global winner at `:541`. The emitted card can retain an
anchor SID and URL from one edition while taking headline, body, topics, and importance from another
(`:562-577`). Reversing index-file iteration changes the winner.

The corruption is visible now. `_data/homefeed.json:101-121` labels the card as the 25 July Weekend
edition but uses the 20 July News headline, long body, and importance 3. The exact Weekend record is
short and importance 2 (`index/stories/2026-07-25-weekend.jsonl:3`), while the leaked record is
`index/stories/2026-07-20-news.jsonl:2`. A second live card at
`_data/homefeed.json:759-779` is a 24 July News card carrying the 25 July Weekend Iran framing and
importance.

**Impact:** The front page can lie about what a desk filed, promote an old treatment as today's
lead, and attach feedback to an SID whose displayed editorial treatment came from another edition.

**Correction direction:** Join metadata by exact edition identity, such as
`(date, stream, normalized_url)` with SID as the stronger key, and emit the URL from that matched
record. Add a test where the same URL deliberately has different copy and importance in two editions.

### R4 - Four valid Weekend stories are missing from the only reading surface

The parser recognizes only `###` stories or bullets whose lead starts with bold text
(`tools/build_stories_feed.py:109-114,201-271`). The Weekend format explicitly permits ordinary
`- ...` bullets (`routines/src/weekend.md:162-179`). Consequently the current edition parses 40
stories while its index contains 44. The dropped prose is at
`_posts/2026-07-25-weekend.md:24-25,28,140`; matching records include
`index/stories/2026-07-25-weekend.jsonl:1-2,5` and the llama.cpp record later in that file. Two of
the missing stories are importance 2.

**Impact:** Selected and recorded reporting disappears from the homepage, and the retired post page
cannot rescue it.

**Correction direction:** Make the format contract and parser agree, then fail current-edition feed
generation when kept records cannot be mapped to cards. A count-only check is insufficient; compare
SIDs or normalized URLs.

### R5 - The new standfirst/deck feature is dead end to end

The shared newsroom contract requires a writer-authored `deck` for lead and feature cards
(`routines/_shared/newsroom-ethos.md:15-20`). The record constructor does not copy it
(`tools/dedup/dedup.py:1094-1118`), although the feed loader and renderer expect it
(`tools/build_stories_feed.py:365-368,562-589`; `_layouts/home.html:173-181`). No current index
record or homefeed story contains a `deck`. `tools/tests/test_deck.py` injects decks directly into
an index fixture, bypassing the producer that drops them.

**Impact:** The central front-page hierarchy feature shipped with zero live instances. Cards fall
back to the long body the feature was designed to replace.

**Correction direction:** Persist non-empty decks during `record`, preserve them on same-edition
convergence, and add one real `final.json -> record -> homefeed` integration test.

### R6 - WebAuthn challenge consumption is not single-use in Workers KV

`consumeChallenge()` performs a non-atomic KV `get` followed by `delete`
(`tools/feedback-sink/src/worker.js:206-212`). Registration and login rely on that as the replay
barrier (`:353-375`, `:407-452`), while credential counter read/update is another non-atomic pair.
Workers KV is eventually consistent and has no transaction spanning those operations. A concurrent
replay reproduction let two requests observe and consume the same challenge.

**Impact:** The account backend advertises WebAuthn replay protection that its storage primitive
cannot enforce. Newly issued challenges and credentials can also be rejected transiently from stale
reads.

**Correction direction:** Put challenge consumption and credential-counter verification/update in a
strongly consistent per-reader Durable Object transaction.

### R7 - Roaming state and daily session renewal are not safe under production KV semantics

`/readstate` and `/prefs` both read a shared KV blob, mutate it, and overwrite it
(`tools/feedback-sink/src/worker.js:494-535,598-619`). Concurrent devices can lose disjoint read
marks or let an older preferences timestamp overwrite a newer one. Adversarial concurrent checks
reproduced both outcomes. The 52-check smoke uses a sequential in-memory `Map`, so it cannot model
this race.

Daily rolling adds another race. `rollSession()` rewrites the same key (`:181-189`), while the
homepage starts `/readstate` and `/prefs` pulls together (`_layouts/home.html:2025-2030,2133-2134`).
Cloudflare KV's write-rate limit can reject one renewal. `/submit` and `/propose` persist their
record before rolling (`tools/feedback-sink/src/worker.js:256-258,289-291`), so a renewal failure
can return an error after a successful write; a user retry then duplicates it.

**Impact:** Roaming can silently lose or roll back state, and successful votes/proposals can look
failed and be duplicated.

**Correction direction:** Serialize per-reader mutations in a Durable Object or store append-only
per-mutation keys and fold them. Make renewal coalesced and non-fatal to a completed request. Give
writes client idempotency keys.

### R8 - The mobile Sync panel is clipped and effectively unusable

The mobile rule tries to open the panel upward at `_layouts/home.html:476-483`, but the later base
rule restores `top` and `right` at `:529-531`. Its parent is a horizontally scrolling, clipping
container (`:469-473`). At a real 390 x 844 viewport, opening Sync produced a panel at approximately
`top=844`, `right=440`, with only 26 px visible and no usable sign-in, setup, or sign-out control.

**Impact:** The passkeys-only policy makes mobile write access depend on a panel mobile users cannot
operate.

**Correction direction:** Apply the mobile inset override after the base declaration, reset every
inset property, and render the popup outside the clipping scroller or position it against the
viewport.

### R9 - Dynamic content can overlap the next grid row

The row-span pass fixes each card's extent at `_layouts/home.html:1446-1492`. Showing or hiding a
vote-reason field at `:1833-1872` changes card height without scheduling another pass. On the first
card, opening the reason field grew content past its assigned row by 26.1 px and overlaid the next
row. The initial font wait has a related one-shot race: after the 2.5-second timeout wins,
`document.fonts.ready` is prevented from correcting the spans (`:1515-1527`). Delaying Anton four
seconds left two cards overflowing by 19 px.

**Impact:** The newspaper layout can place controls or prose on top of another story under normal
interaction or a slow font load.

**Correction direction:** Repack after every reason show/hide/send/retract, preserving the clicked
card's visual anchor. Treat the timeout pack as provisional and always run one final pass when fonts
actually settle.

### R10 - A committed "low-value" bearer can overwrite the analytical corpus

The embedding token is committed as a default and described as gating only AI spend
(`tools/dedup/dedup.py:77-81`). The Worker uses the same bearer for every route
(`tools/embed-proxy/src/worker.js:15-18,63-71`), including `/plane/ingest`, which replaces
`plane:v1` (`:177-190`). The private repository and Jekyll exclusions reduce public exposure, but
the secret is in Git history and available to every repo reader and routine context.

**Impact:** Anyone holding what the code calls a low-value embedding token can replace the corpus
used for thread, entity, search, and continuity grounding.

**Correction direction:** Rotate the token, inject it at runtime, and use a separate privileged
credential for ingest. Document the real blast radius.

## Medium Severity

### R11 - Editorial read state is local-only despite the roaming claim

Editorial cards deliberately use `ed-<stream>-<date>` IDs (`_layouts/home.html:213-227,1530-1533`),
and the client puts them into the sync shadow. `/readstate` accepts only `st-...`
(`tools/feedback-sink/src/worker.js:70,509-518`). A direct request returned
`200 {changed:0, skipped:1}` for a valid editorial mark.

The same endpoint caps only one incoming body, not the merged stored value
(`:475-535`). Three valid 800-entry batches produced 2,400 stored entries and roughly 108 KB despite
the documented 2,000/64 KB limits. GET does not age records out, and the state key has no TTL.

**Impact:** Editorial read status never roams, and reading-history storage can exceed its stated
privacy and resource bounds.

**Correction direction:** Validate both strict `st-` and `ed-` forms, enforce limits after merge,
prune before every response, and test real editorial tombstones.

### R12 - The vote and sync UI claims success state before the server does

The active thumb changes before `/submit` returns (`_layouts/home.html:1855-1872`) and is not rolled
back on 400, 401, 500, or network failure. Rapid switch/retract operations run concurrently, so
server processing order can differ from final visible state. `flushPush()` clears its pending flag
before the request and restores it only on a rejected promise (`:1914-1925`); HTTP failures are
dropped. The one-minute 401 grace simply ignores the response (`:1970-1973`) and does not retry the
initial pulls or failed vote. "Sign out" removes only local storage (`:2120-2123`); there is no
server logout route.

**Impact:** The UI can show a vote or "Synced" state that was never persisted, and a copied bearer
remains valid for up to 90 rolling days after sign-out.

**Correction direction:** Serialize mutations per card, acknowledge or roll back UI state from the
response, retry idempotent reads with bounded backoff, retain pending state for all non-2xx results,
and revoke sessions server-side.

### R13 - The trust boundary is every project on the GitHub Pages origin

The RP ID and accepted origin are the account-wide `https://khalic-lab.github.io`
(`tools/feedback-sink/src/worker.js:51-57`). The 90-day bearer lives in origin-wide localStorage
(`_layouts/home.html:1884-1890`). Any sibling Pages project on that host shares the storage and
satisfies both CORS and WebAuthn origin checks.

**Impact:** A compromised or experimental sibling project can read the session and act as the
reader.

**Correction direction:** Give the newsdesk a dedicated origin/RP ID. Prefer a Secure, HttpOnly,
SameSite session cookie issued on that origin over a long-lived JavaScript-readable bearer.

### R14 - Future-date recovery creates two identities for one edition

When `--date` is ahead of the clock, front matter is clamped to now
(`tools/publish.py:162-180`), while filename, index path, title, default notification title, and
commit message continue to use the requested date (`:340-353,399-409`). A reproduction produced a
tomorrow-named post and index with today's front-matter date and evaluator URL. An unterminated
front-matter block only warns and continues (`:142-147`).

**Impact:** Storage, page URL, notification, and edition analytics can disagree about what day was
published.

**Correction direction:** Reject invalid/future edition dates instead of partially rewriting one
field, and stop on malformed front matter.

### R15 - A partial same-edition retry can erase its index

`cmd_record()` reads the old edition for identity convergence, then unconditionally replaces the
file with only the new payload (`tools/dedup/dedup.py:1020-1028,1124`). The writer truncates directly
rather than using an atomic temporary file. Re-recording a two-story edition with an empty payload
produced a successful zero-record index while old ledger publish events remained.

**Impact:** A retry after partial model output can destroy the active dedup/feed snapshot and leave
the ledger and edition index contradictory.

**Correction direction:** Write atomically and require explicit destructive replacement or a
post/index parity check before reducing an existing edition.

### R16 - The AI/ML prompt contradicts the new headline contract

The shared contract says the card headline is a separate 3-8 word artifact, not the brief's bold
lead (`routines/_shared/newsroom-ethos.md:15-17`). The AI/ML stream later says the bold paper
headline is also the dedup headline (`routines/src/ai-ml.md:81-84`; assembled copy at
`routines/ai-ml.md:223-226`).

**Impact:** AI/ML can reintroduce exactly the long, repeated front-page headlines today's change
was meant to eliminate.

**Correction direction:** Remove the stream-specific override and require a separate Step-C card
headline.

### R17 - The browser harness is a reporter, not a test oracle

The injected checks append diagnostic text but no command parses it or exits non-zero
(`tools/home_harness.py:381-443,540-654,955-957`). In `#synced` mode, the EMPTY probe emitted
`vis=1 hidden=1 packedEmpty=1`, contradicting its own zero-card invariant, while the harness still
exited successfully. Its editorial fixture omits production voting controls
(`tools/home_harness.py:841-863` versus `_layouts/home.html:227-231`), and its image path does not
exercise production's late insertion.

The wider suite is already red: 468 of 469 tests pass. The failing real-repo test hard-codes
"today is 2026-07-10" while using a rolling 14-day default
(`tools/tests/test_reconcile_lint.py:41-44,556-570`). The plan records one known failure as an
accepted baseline (`docs/PLAN-2026-07-25-front-page-hierarchy.md:220-227`).

**Impact:** New failures can hide behind a permanently red baseline, and visual checks can print
their own proof of failure while CI remains green.

**Correction direction:** Add a check driver that parses every marker and exits non-zero, make
state probes idempotent, use production DOM or exact extracted fixtures, and restore a zero-failure
unit-test baseline with clock-independent fixtures.

### R18 - Progressive enhancement and mobile accessibility regressed

With JavaScript disabled, all story prose is visible as intended, but the static markup still
exposes inert More, read, and vote controls (`_layouts/home.html:193-204,222-231`); folding and
handlers are added only at `:1623-1630`. A 390 px no-JS check exposed 82 dead More buttons, 82 dead
read buttons, and 164 dead vote buttons.

On mobile, CSS visually moves Read and Sync ahead of topics while DOM/tab order remains topics first
(`_layouts/home.html:22-50,476-480`). Measured target heights ranged from 11 to 23 px for several
controls. The fixed bar overlaps footer links because only `#main` receives bottom padding
(`:482-483`). Read styling also dims prose to about 3.68:1 in the light palette and omits the new
deck (`:1213-1216`).

**Impact:** Keyboard and no-JS users traverse misleading controls; touch targets are too small; the
footer is obscured; read text can miss AA contrast.

**Correction direction:** Reveal JS-only controls only after handlers install, align DOM and visual
order, provide approximately 44 px hit areas, reserve footer safe-area space, and use explicit
AA-safe read colors including deck text.

### R19 - Operational documentation contradicts the live system

The architecture still calls `/submit` public and the feedback loop strictly human-gated
(`ARCHITECTURE.md:630-659`), while `/submit` is session-only and the evaluator may auto-append
writer-read preferences (`routines/weekly-evaluator.md:252-254`). It also omits Sports from the
writer list at `ARCHITECTURE.md:649-650`. `diagrams/04-bridge-delivery-and-feedback.md:19-20`
correctly shows session auth, then `:34-37` calls the same endpoint public. The whole transformation
pipeline in `diagrams/05-frontend-rendering.md:1-65` describes retired post-page code. The current
home layout contains a "NOT YET APPLIED" comment for an editorial reorder that is already implemented
(`_layouts/home.html:132-150,207-235`). Both front-page design documents still say `PROPOSED` after
the implementation shipped (`docs/PLAN-2026-07-25-front-page-hierarchy.md:1-4`).

The local Worker sample still configures removed `WIDGET_KEY` and omits required `INVITE_TOKEN`
(`tools/feedback-sink/.dev.vars.example:1-10`). The README omits the `rs` preferences field and
points redeployers to a nonexistent `FEEDBACK_URL` constant
(`tools/feedback-sink/README.md:54-66,120-122`). Gmail MCP remains attached to triggers and the
How-it-works SVGs still show Gmail despite digest removal (`ARCHITECTURE.md:100-115`).

**Impact:** The designated source of truth cannot safely guide an incident, redeploy, or future
change.

**Correction direction:** Reconcile live architecture once, archive obsolete diagrams, mark shipped
plans accordingly, update deploy samples/contracts, regenerate the public diagrams, and remove
retired trigger connectors/secrets after verification.

### R20 - Feedback ingestion accepts records that cannot be safely attributed

`/submit` permits an omitted `story_id` (`tools/feedback-sink/src/worker.js:242-255`), but homepage
records have no URL fallback and `fold.py` must leave such a record unresolved
(`tools/feedback/fold.py:73-90`). The production verification example itself omits the ID
(`tools/feedback-sink/README.md:132-136`). Conversely, fold accepts any `st-` or `ed-` prefix as
resolved without checking shape, existence, or whether an editorial stream/date matches its brief
(`tools/feedback/fold.py:79-81,145-167`).

The trust model is also documented incorrectly: `feedback/FEEDBACK.md:46-58` and
`tools/feedback-sink/README.md:25-27` say no tap can auto-mutate writer-read files, but the evaluator
has a bounded auto-apply grant for reasoned/repeated feedback
(`routines/weekly-evaluator.md:252-254`).

**Impact:** The API can return success for permanently unresolved feedback, arbitrary IDs can become
orphan ledger events, and operators may underestimate prompt-injection risk in reason text.

**Correction direction:** Require `story_id` for card feedback, verify `st-` against materialized
state, validate `ed-` strictly against the brief, and document or remove the auto-apply trust path.

### R21 - Public auth routes allow cheap write amplification

`/auth/login-options` writes a KV challenge for every unauthenticated request
(`tools/feedback-sink/src/worker.js:396-404`). CORS only controls browser access to the response; it
does not reject a foreign-origin request (`:83-99`). Auth JSON routes also parse unbounded request
bodies before validation (`:332-339,407-420`).

**Impact:** A foreign page or scripted client can consume challenge-write quota, raise cost, impede
login, or force oversized JSON parsing.

**Correction direction:** Reject unexpected `Origin` server-side, add edge rate limits, and cap all
JSON bodies before parsing.

## Low Severity

### R22 - The Weekend tariff recap bypasses an available primary source

`_posts/2026-07-25-weekend.md:25` cites only Swissinfo for the US tariff, despite the direct USTR
action already being available and cited in `_posts/2026-07-24-news.md:14`. This conflicts with the
primary-source rule in `routines/_shared/newsroom-ethos.md:9-11`.

**Correction direction:** Cite the USTR action for the legal facts and keep Swissinfo only for Swiss
reaction or context.

### R23 - The Weekend neutrino item overstates both the particle and the paper

`_posts/2026-07-25-weekend.md:88-91` calls ultra-high-energy neutrinos "the most energetic particles
known"; cosmic rays reach higher energies. It then says no arrangement of ordinary astrophysical
sources can reconcile the data, while the cited paper evaluates specific diffuse and rare-transient
hypotheses rather than every possible ordinary source arrangement.

**Correction direction:** Use "among the highest-energy neutrino candidates" and limit the negative
conclusion to the source classes the paper actually tested.

### R24 - Institution aliases split provenance history

`sources/institutions.yml:1327-1369` records `LBNL` separately from Lawrence Berkeley National
Laboratory, and `:1486-1557` separates `MPE Garching` from Max Planck Institute for Extraterrestrial
Physics. Citations and classifications are therefore split, leaving abbreviated forms `unknown`.

**Correction direction:** Add aliases to the canonical records and run the existing prompt-sync and
assembly checks.

### R25 - Browser fallbacks and image privacy attributes are incomplete

All palette values exist only inside `light-dark()` with no legacy fallback
(`_includes/head/custom.html:59-96`), so older supported browsers can invalidate the consuming color
declarations. Image `loading` and `referrerPolicy` are assigned in `onload`, after `src` starts the
request (`_layouts/home.html:2149-2174`).

**Correction direction:** Provide baseline values outside an `@supports` override, and set image
attributes before assigning `src`.

### R26 - The added font license makes `git diff --check` fail

All 93 lines in `assets/fonts/OFL.txt` use CRLF that Git reports as trailing whitespace.

**Correction direction:** Normalize the license file to LF without changing its text.

## What Held Up

- Generated writer prompts are byte-consistent with their sources: `python3 routines/assemble.py check` passes all five writers.
- The source-registry expansion was evidence-rich and schema-valid; no unsupported reach/freshness claim was confirmed in this review.
- Deleting the three 14 June rolling index files did not lose their durable records; all 20 remain in the append-only ledger.
- The feedback sink correctly rejects unauthenticated `/submit` and `/propose`, pins `reader` from the session, and enforces the documented vote/reason/topic shapes.
- Feedback folding keeps append-before-consume crash safety and `fb_id` idempotency; its 20-test suite passes.
- Resting homepage rank order stayed monotonic at 390, 500, 800, 1024, and 1440 px, with no horizontal overflow or resting card overlap.
- Fold expansion/collapse preserved the clicked card's position, beat filtering preserved rank, signed-out mode sent no sync traffic, and the live Pages build for current HEAD succeeded.
- Both Anton files are valid WOFF2 files and the OFL license is present.

## Verification Record

| Check | Result |
|---|---|
| Full Python suite, `python3 -m unittest discover -s tools/tests` | 469 run; 468 passed; 1 wall-clock-dependent failure |
| Prompt assembly, `python3 routines/assemble.py check` | 5/5 generated prompts match |
| Feedback Worker smoke | 52/52 passed; mock does not model KV consistency, TTL, or write-rate limits |
| Embed/plane Worker smoke | 23/23 passed |
| Feedback fold suite | 20/20 passed |
| Scoped publish/feed/deck tests | 107 passed across the independent pipeline pass |
| Clean-clone data regeneration | Homefeed, stats, and source health regenerated byte-identically |
| Browser checks | Multiple desktop/mobile widths plus delayed-font, reason-box, no-JS, filter, fold, and sync-state probes |
| `git diff --check c647dda1 HEAD` | Failed only on 93 CRLF lines in `assets/fonts/OFL.txt` |
| Worktree before review document | Clean and aligned with `origin/main` |

## Remediation Order

1. Fix R1 and R2. Do not trust another routine fire until origin-SHA verification and fatal staging/reader-surface gates exist.
2. Fix R3-R5 and regenerate the feed. The current reader surface is incomplete and editorially cross-contaminated.
3. Fix R6-R7 before describing sync or WebAuthn challenges as strongly reliable. KV is the wrong mutation primitive for the stated contracts.
4. Fix R8-R9 so the passkeys-only path and vote reasons work on the primary mobile surface without overlap.
5. Rotate and split the credential in R10.
6. Restore trustworthy verification with R17, then clear the remaining medium findings by reader impact.
7. Correct the live neutrino and tariff copy when editorial amendments are next allowed; do not let a code-only remediation leave known factual/sourcing defects published.

## Residual Gaps

- No real passkey ceremony or authenticated production write was performed; the review stayed read-only.
- Safari and Firefox were not executed. Browser-compatibility findings are source-supported, not cross-browser reproductions.
- No local Jekyll build was available. The live GitHub Pages build and generated harness were used instead.
- Remote trigger configuration was not fetched, so Gmail MCP and retired-secret cleanup rely on the repository's own current architecture statement.
- The factual spot-check was targeted, not a complete source-by-source verification of all 51 stories published today.
- The bridge's local-only implementation was not comprehensively re-audited; only its committed artifacts and contracts touched by today's changes were reviewed.
