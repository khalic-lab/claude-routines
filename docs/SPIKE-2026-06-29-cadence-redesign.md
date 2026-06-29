# SPIKE — Briefing cadence + topic-lineup redesign (2026-06-29)

> Proposal. Evidence-grounded (Evaluator reviews, reader-feedback corpus, archive analyses, SPIKEs,
> current prompts, post-corpus metrics) and adversarially verified. **Not yet implemented; no live
> RemoteTrigger edits made.** §8 decisions RESOLVED by the user 2026-06-29 and folded into §2/§3:
> News = daily every-day evening; AI/ML = Tue+Fri midday; Science = Wed; Weekend = in-depth weekly
> revisit, security dropped pipeline-wide.

## 1. What the evidence says

- **Thinning the cadence is well-supported, but "empty" is the wrong word — the real defect is
  *repetition*, not blank sections.** The corpus scan found **zero filler phrases across all 23 posts**
  (06-17→06-24); blank desks were honestly skipped, not padded. The actual rot is cross-day recurrence.
  **The load-bearing number is ai-ml's 53% repeat rate** — that is the live stream actually being cut to
  2×/week. (A corpus-wide **37% repeat over 156 items**, with markets at **84%**, also exists
  [AUDIT-2026-05-31] but **predates the 2026-06-18 markets removal**, so the aggregate inflates the case;
  cite the ai-ml 53% figure, not the markets-inclusive number.) The fix is *fewer, less frequent editions*
  + omit-empty, not a hunt for null text.
- **AI/ML is the clearest cut-to-2×/week candidate.** Lowest-value daily: **975 words on 06-20 (2 bullets),
  1557 avg — thinnest stream** [corpus]; **68% industry-news / vendor-PR, ~5 of 40 items research-result**
  [AUDIT]; Evaluator repeatedly flags "genuinely quiet day," **all 9 T3 blogspam citations belong to this
  stream**, and it's the only stream emitting no "Feeds hit" line [evaluator 2026-06-14]. **Zero reader
  interactions** in the feedback window — nobody misses it daily.
- **Dropping *security* is defensible only on a precise read — and it partly contradicts the instinct.**
  cyber-papers is the **single most-liked stream (+12, 0 downvotes)** with the strongest praise [feedback].
  BUT upvotes concentrate on the **arXiv papers** ("crazy how many papers have direct impact," six papers
  tapped 06-19), not the CVE/CISA security-ops content — which has **no positive signal**. Since the papers
  migrate into AI/ML, the *valued* content survives; only the unscored security-ops half is deleted.
  **Stated honestly: the data does not independently justify killing the papers, and does not defend the
  security desk either way — it's simply unscored.**
- **More local CH is directionally supported (small n).** The two Swiss-local stories (Bern CHF 200M,
  Swiss AI ecosystem) were **both upvoted, none downvoted** [feedback].
- **Affiliations have no direct demand signal — say so — but rest on a real adjacent signal.** No
  reason-text mentions affiliations. Justification is the **one downvote**: Rafael rejected a *Nature blog*
  cited in place of the actual study — "read the actual study… steer away from sensationalism." A
  credibility-lifecycle / primary-source complaint; surfacing author institution is part of that posture.
  Mechanically **near-zero infra**: `api.semanticscholar.org` is allowlisted and returns
  `authors.affiliations` [PRIOR-ART-2026-05-31 §A5].
- **Moving Overview to evening has no evidence for or against** — clean user preference. The lone downvote
  *was* a morning-overview item, but about sourcing, not timing.
- **Weekend should draw from the week's best, not be date-gated.** Explicit request: "accept the 'best of
  the best' for this week… not only stuff from that day" [feedback 2026-06-20]. AUDIT found Weekend's
  **65% repeat rate is structural**; only fresh value is the long-form papers.
- **arXiv emptiness was a feed-routing failure, not a content shortage.** Old cyber "second batch" was empty
  4/5 days because arXiv listing pages 403'd with no fallback, while Weekend pulled 9 papers from the same
  window [evaluator 2026-05-03/05-24]. Whatever absorbs the papers must inherit the **curl-first arXiv Atom
  + HF + Semantic Scholar fallback chain**.
- **Cron must never let the Evaluator race the writers** [evaluator Open-Q-2], and **date discipline matters
  most for the daily News edition** (SVP-vote re-derivation bug — event_date not carried forward)
  [REVIEW-2026-06-08 §2.5].

## 2. New lineup & schedule

CEST = UTC+2 (summer). UTC = CEST − 2.

| Edition | Topic | Cadence (CEST) | UTC cron | Model | Trigger |
|---|---|---|---|---|---|
| **News** | Local CH + world (evening) | Daily (every day) 19:00 | `0 17 * * *` | opus-4-8 | **Retarget Morning Overview** `trig_012KfuF2Fc8KxNRS9KT1iuYb` |
| **AI/ML** | AI/ML news + migrated ML arXiv papers | Tue & Fri **12:00 (midday)** | `0 10 * * 2,5` | opus-4-8 | **Keep AI/ML** `trig_01QVL6eSmHTUrmnSLHrpNN9Q` |
| **Science** | Non-AI science (Nature/Quanta/non-CS arXiv) | Wed 17:00 | `0 15 * * 3` | opus-4-8 | **Retarget Cyber+Papers** `trig_01YLiCr5YJ2XNh2QyPbkyzQP` |
| **Weekend** | Long read (week's best) | Sat 09:30 | `30 7 * * 6` | opus-4-8 | **Keep Weekend** `trig_01XKzge4DxP6wTjLwtkoYeqj` (unchanged) |
| Evaluator | QA backstop | Sun 11:30 | `30 9 * * 0` | opus-4-8 | Keep `trig_01F5npsKTQTLKekAZ5BczKtG` (cron unchanged; **prompt edited**) |
| Watch | Topic poll | every 4h | `0 */4 * * *` | haiku-4-5 | Keep `trig_01FgrFMfsreu597nKUXEEQMt` (no change) |

**Collision check (UTC weekly grid — Watch INCLUDED: it fires 00/04/08/12/16/20 daily).** No two routines
share a fire time. Fire times in UTC: AI/ML 10:00 (Tue/Fri), Science 15:00 (Wed), News 17:00 (daily),
Weekend 07:30 (Sat), Evaluator 09:30 (Sun). Nearest-Watch gaps: AI/ML 10:00 is 2h from Watch-08/12;
Science 15:00 is 1h from Watch-16; News 17:00 is 1h from Watch-16/20; Weekend 07:30 is 30m from Watch-08;
Evaluator 09:30 is 1.5h from Watch-08. Same-day writer pairs never overlap (Tue: AI/ML 10:00 + News 17:00;
Wed: Science 15:00 + News 17:00; Fri: AI/ML 10:00 + News 17:00; Sat: Weekend 07:30 + News 17:00; Sun:
Evaluator 09:30 + News 17:00, Evaluator runs 7.5h *before* News and reads through Saturday — no race).
Cron arithmetic (UTC = CEST−2): 12:00−2=10:00; 17:00−2=15:00; 19:00−2=17:00; 09:30−2=07:30; 11:30−2=09:30.
Weekday codes: Tue=2, Wed=3, Fri=5, Sat=6, Sun=0. (Watch is haiku, writes only `last_fired` to
`watches.yml` — touches no post/index — so a collision was low-impact, but eliminated anyway.)

**Cadence justification.** AI/ML Tue+Fri midday: Tuesday clears the Mon–Tue arXiv backlog (arXiv silent on
weekends — the Sunday-1-item problem); Friday closes the week before the Saturday Weekend recap. Midday
(per user) makes these current-awareness editions rather than late-evening reads. Science Wed: Nature's main
weekly issue lands mid-week. News daily-evening (every day, incl. weekends) reuses the vacated evening slot.
Weekend is the **in-depth revisit of the week's most important** (per user), not a same-day brief.

## 3. Migration map per routine

### Morning Overview → **News** (retarget; reuse `trig_012KfuF2Fc8KxNRS9KT1iuYb`)
- **Cron:** `30 4 * * *` → `0 17 * * *`.
- **Content gutted & replaced.** Old `🔬 Science` + `📄 ML first arXiv batch` are *removed*. New body =
  **local CH + world news**, recipe lifted from old Cyber+Papers' `🇨🇭 Switzerland & Vaud` and
  `🌍 World politics & geopolitics` (admin.ch/parlament.ch/vd.ch, SRF-DE + Le Temps-FR RSS with ≥1 DE/FR
  citation; reuters/apnews/AFP, Al Jazeera, BBC/FT, ≥3 countries).
- **Where the old content goes:** `🔬 Science` → seeds the new **Science** edition. `📄 ML first arXiv
  batch` → folds into **AI/ML**.
- **Email digest — resolved explicitly.** Morning Overview today has its own weekday morning-email step
  (§4 of `morning-overview.md`); Cyber+Papers separately composed the consolidated evening email. Under the
  new cadence the streams no longer co-fire daily, so a 17:00 News email cannot consolidate same-day
  AI/ML/Science. **Decision: the News email carries News-only content** (local CH + world); the cross-stream
  daily consolidation is **dropped**. When renaming, **DELETE the morning-overview email block** — or two
  email steps ship. (A cross-stream digest, if ever wanted, can only reference the *previous* day's
  AI/ML/Science; out of scope for v1 — see §8.7.)
- **session_context:** keep model `opus-4-8`, full `allowed_tools`, `sources` verbatim; change only cron +
  the email-scope edit.
- **Output slug:** `overview` → `news`.
- **File edits:** rewrite `routines/src/morning-overview.md` → rename `routines/src/news.md`; keep all five
  `<!-- include: _shared/*.md -->` placeholders; **strip the morning-email block**. Carry forward the
  dated-weekday table + event_date discipline.

### AI/ML → **2×/week + absorbs all ML arXiv papers** (keep `trig_01QVL6eSmHTUrmnSLHrpNN9Q`)
- **Cron:** `30 19 * * *` → **`0 10 * * 2,5`** (Tue & Fri **12:00 CEST / 10:00 UTC** — "midday" per user;
  current-awareness editions, the in-depth weekly revisit lives in Weekend).
- **New papers section** (`## 📄 ML/AI research`) consolidating **both** old arXiv batches into one. Per
  user: "the arxiv stuff IS ML/AI."
  - **Sourcing migrated in:** arXiv RSS (cs.LG, cs.AI, cs.CL, cs.CV, stat.ML) **via curl Atom API first**,
    then the proven fallback chain (HF `paper_search` snippet → Semantic Scholar → site:arxiv.org search).
    Apply Patch-1/2 (2026-06-14): emit "Feeds hit (reachability + method)" footer; enforce the T3 deny-list
    (aiweekly.co, aitoolsrecap.com, codersera.com, techtimes.com, …).
  - **Paper format with affiliations** (§4).
  - **arXiv-ID exact dedup now intra-edition** (one batch) — simpler than the old cross-edition gate.
- **Two fires/week → multi-day window:** set coverage to "since last AI/ML fire," not "since 06:30 today."
- **File edits:** `routines/src/ai-ml.md` (papers section + window + affiliations); regen.

### Cyber+Papers → **DROPPED, then retargeted to Science** (reuse `trig_01YLiCr5YJ2XNh2QyPbkyzQP`)
- **Cyber/security DELETED entirely.** `🛡️ Cybersecurity` (NVD/CISA/CVE/APT) removed, no destination.
  NVD/CISA/KEV feed-routing patches die with it.
- **News content extracted first:** `🇨🇭 Switzerland & Vaud` + `🌍 World politics` → **News**.
- **ML papers extracted:** `📄 ML research — second arXiv batch` → **AI/ML**.
- **Freed trigger repurposed** (no delete API; retarget):
  - **Cron:** `0 17 * * *` → `0 15 * * 3` (Wed 17:00 CEST).
  - **New body = Science edition** (NEW, non-AI): Nature primary (`s41586-…`, dig through `d41586-…`
    journalism to the paper), science.org, bioRxiv/medRxiv JSON, Quanta, Semantic Scholar across fields, and
    **non-CS arXiv** (physics, math, q-bio, astro-ph, cond-mat, quant-ph, chem, climate, neuro). Seed = old
    Overview `🔬 Science` + Weekend's `🔭 Fundamental science` / `🧬 Biology`. **NOT seeded from cyber
    papers** (those were CS/ML → AI/ML).
  - Apply Patch-4 (2026-06-14): Nature item with no fetchable abstract → locate arXiv cross-list preprint,
    summarise with `[preprint]`, not a title-only stub.
  - **Output slug:** `cyber-papers` → `science`.
  - **File edits:** new `routines/src/science.md` (delete `cyber-papers.md`); keep five shared includes;
    **add** the affiliations param (§4).
- **Net statement:** nothing scientific is lost. ML/CS preprints → AI/ML (with affiliations). Broad non-AI
  science → Science. Only deletion is the unscored security-ops desk.

### Weekend → **keep; now the in-depth weekly revisit + only long-read** (no trigger/cron change)
- **Content change (per user — "keep long read on weekend with in depth; revisiting most important of the
  week is here"):** the Weekend brief is explicitly the **in-depth revisit of the week's most important
  stories**, not a same-day brief. Add: "Select and go deep on the strongest items across the past 7 days
  regardless of which day they broke — including stories already surfaced briefly in News/AI/ML/Science this
  week (this is the place to revisit them in depth, not to avoid them). Dedup only against prior *Weekend*
  editions, not against the week's daily briefs." (Note: this deliberately relaxes the cross-stream dedup
  for Weekend — daily editions flag a story; Weekend is where it gets the long treatment.)
- **Drop** the `🛡️ Cybersecurity research of the week` section — **CONFIRMED (user): security dropped
  pipeline-wide, including Weekend.**
- Add affiliations (§4 — **ADD** the param, currently absent).
- **File edits:** `routines/src/weekend.md`; regen.

### Evaluator → **keep cron; teach it the new lineup** (edit directly, not assembled)
- Edit `routines/weekly-evaluator.md`: slug set `{overview, ai-ml, cyber-papers, weekend}` →
  **`{news, ai-ml, science, weekend}`**. Drop all cyber/markets references. Update expected-cadence model
  (News daily; AI/ML Tue+Fri; Science Wed; Weekend Sat) so it doesn't flag 2×/week AI/ML as "missing days."

### Watch → keep as-is (haiku, every 4h); see §8.6.

**Shared-partial regen:** all four writer src files keep the include placeholders; after editing, run
`python3 routines/assemble.py` then `python3 routines/assemble.py check` (must exit 0) before any mirror.

## 4. Affiliations mechanism

**Goal:** every scientific item names where the authors are. Near-zero new infra.

- **Critical: the S2 URL is NOT uniform across the four srcs — "edit" vs "add" differ.** Verified: only
  `ai-ml.md` and `morning-overview.md` carry the S2 URL with `fields=title,abstract,year,authors`.
  **`weekend.md` (line ~67) and the Science seed in `cyber-papers.md` reference S2 as
  `…/paper/search?query=…` with NO `fields=` param at all** — and S2's default response without `fields=`
  returns only paperId+title (no authors, no abstract). So Weekend's existing author/affiliation capability
  is **already non-functional**, and a blanket "change `fields=` everywhere" instruction would be a **no-op**
  for Weekend/Science.
  - **EDIT** (param present): `ai-ml.md`, `morning-overview.md` → `fields=title,abstract,year,authors,authors.affiliations`.
  - **ADD** (param absent): `weekend.md` and new `science.md` → append the full
    `&fields=title,abstract,year,authors,authors.affiliations` to the S2 URL.
- **Secondary — arXiv Atom API.** Parse `<author><arxiv:affiliation>` when populated (inconsistent → fallback).
- **Tertiary — HF `paper_search`.** Returns author/institution, but the HF MCP tools are **not in any
  routine's `allowed_tools`**. **Recommend: S2 primary + arXiv fallback, skip the HF allowlist change** to
  keep migration minimal.
- **Which editions:** **AI/ML**, **Science**, **Weekend** (paper sections). News does not need it.
- **Prompt instruction to add** (papers sections of those three srcs):
  > For every paper, after the author list, surface the lead authors' institutional affiliations from the
  > Semantic Scholar `authors.affiliations` field (fall back to arXiv `<arxiv:affiliation>`). If no
  > affiliation is retrievable, write `(affiliation not listed)` — never fabricate.
- **Output format** (extends Weekend's `Authors et al.` line):
  ```
  **[arXiv:2606.XXXXX](URL)** · J. Doe, A. Smith et al. (MIT; Google DeepMind) · `[preprint]`
  ```
  Nature/journal items in Science: `Authors: … (ETH Zürich; CERN)`.
- **Verification step (REQUIRED before mirror):** `grep -nE 'semanticscholar\.org' routines/src/*.md` —
  every match in ai-ml/science/weekend must show `authors.affiliations`; news may drop S2 entirely.
- **Credibility tie-in (optional):** the same S2 call exposes "Highly Influential Citations"; not v1.

## 5. Kill the empty/artificial shape

The corpus shows the problem is **repetition + equal-weight aggregator-feel**, not literal blanks.

**CORE — ship now (directly motivated by "many are empty, artificial"):**
- **Omit-don't-null / drop fixed grids.** Remove the rigid "Required section headers (exactly)" lists from
  each src; a section appears only if it has ≥1 genuinely-new item. *Solves:* AI/ML's chronically-empty
  `🍎 Apple Silicon` and the cyber arXiv "skipped" stubs. Headers become *available*, not *mandatory*. This
  is the lever the user's wording directly demands; deliver it with the lineup change. Inline per-src or a
  small shared partial — either; do **not** gate the lineup migration on building shared infra.

**OPTIONAL FOLLOW-ON — a separate optimization track, NOT part of the cadence/lineup redesign asked for now.
Do not block the lineup change on any of it:**
- **Instrumentation:** each writer appends word-count + tool-call count to its Coverage footer; Evaluator
  reports per-stream mean + trend.
- **Honest-short on quiet days (Lever 1):** if <N=2 genuinely-new stories, emit a 3–5 bullet brief.
- **Length caps (Lever 2):** News/AI/ML/Science target 1500–2500 words; Weekend stays 4000–8000.
- **Comprehensive-with-dive-fallback:** lead with one take, 1–3 stories at unequal weight.
- If pursued, sequence one lever per week, reading the Evaluator between changes; instrumentation first so
  caps are measurable. **Explicitly deferred and decoupled from the v1 redesign.**

**Also include in v1 (cheap, directly tied to the one downvote):** add to `_shared/newsroom-ethos.md`
(already carries "go to the primary source") an explicit line — *"Cite the study/filing/advisory, not a blog
write-up of it; never upgrade mixed/early evidence to a firm finding."* Hits all writers, one edit.

## 6. Dedup / threading implications

- **Slug list is HARD-CODED in code, not a config file.** Authoritative tuple at
  **`tools/dedup/dedup.py:93`**: `KNOWN_SLUGS = ("overview","ai-ml","cyber-papers","weekend","evaluator")`.
  Edit to **`("news","ai-ml","science","weekend","evaluator")`**, *then* update `DEDUP.md` prose. **Run
  `python3 tools/dedup/dedup.py selftest` after.** (Editing only `DEDUP.md` would miss the code.)
- **`index/stories/` slug churn:** retire `overview.jsonl` and `cyber-papers.jsonl` (stop writing; leave as
  history). Add `news.jsonl`, `science.jsonl`. `ai-ml.jsonl`, `weekend.jsonl` continue.
- **arXiv-ID exact dedup simplifies.** Old cross-edition gate (Cyber-second vs Overview-first) disappears —
  both batches now in AI/ML (intra-edition). Remaining cross-edition overlap: AI/ML (CS/ML) vs Science
  (non-CS) — different categories, near-zero collision. **Weekend dedup is deliberately relaxed** (per the
  §3 Weekend change): it dedups only against **prior Weekend editions**, NOT against the week's daily briefs
  — Weekend is where a week's important story gets the in-depth treatment even if a daily edition already
  flagged it. Keep the deterministic same-URL / same-arXiv-ID hard-REPEAT rule *within* the Weekend slug's
  own history. (Implementation: `dedup.py` already loads the recent index cross-slug by default — the
  Weekend prompt must instruct "ignore non-weekend matches when deciding to include," or the `check` call
  for Weekend must be scoped to the `weekend` slug. Flag for the implementer: this is a behavior nuance, not
  just a prompt line — confirm how `load_recent_index` is filtered for the Weekend run.)
- **Dated-outcome hard gate — keep, but only for News.** News is the only edition with elections / Swiss
  votes / scheduled events (SVP-vote re-derivation bug) [REVIEW-2026-06-08 §2.5]. Carry forward `event_date`
  propagation, `[ongoing since]` thread-genesis binding, dated-weekday table. **Do not** build threading for
  AI/ML/Science papers — arXiv-ID exact dedup covers them.
- **Embeddings index volume drops** (3 daily streams → 1 daily + 2 weekly + 1 weekly) — fewer compose-time
  embed-proxy writes; no code change.

## 7. Migration order & verification

Repo-only edits and `assemble.py check` **must pass before any live mirror**. RemoteTrigger is
**main-session-only** — all GET→edit→update→re-GET steps run in the main session.

**Commit gate (every step):** stage edits, but **commit only on explicit go-ahead** — repo convention is
commit/push only when asked. When approved, commit with `-c commit.gpgsign=false` and **no Claude signature**.

0. **PRECONDITION — RESOLVED 2026-06-29: pipeline is LIVE.** The apparent "silence since 06-24" was a local
   sandbox artifact (stale clone + no github egress from the dev environment), NOT an outage. `RemoteTrigger
   list` confirms every enabled trigger fired within the last day: Morning Overview 06-29 04:32, Cyber+Papers
   06-28 17:02 (next 06-29 17:01), AI/ML 06-28 19:33, Weekend 06-27, Evaluator 06-28, Watch 06-29 08:06;
   Markets disabled. All live crons match the documented schedule. Caveat: `last_fired_at` proves the cron
   *fired*, not that each run pushed a brief — confirm origin/main has commits past 06-24 from a
   network-capable checkout before/after mirroring. Migration de-risked: triggers are known-live.
1. **(Optional follow-on only) Instrumentation** — skip for the v1 lineup change.
2. **Author shared edits:** add the primary-source/anti-sensationalism line to `_shared/newsroom-ethos.md`;
   apply the omit-empty rule; make the affiliations `fields=` change/addition per §4.
3. **Edit src files:** rename `morning-overview.md`→`news.md` (news body, strip morning-email block);
   `ai-ml.md` (papers section + multi-day window); new `science.md` (delete `cyber-papers.md`); `weekend.md`
   (week's-best + affiliations + drop cyber section).
4. **`python3 routines/assemble.py` then `assemble.py check`** — must exit 0. Update `routines/MANIFEST.md`.
5. **Update dedup + Evaluator:** edit `tools/dedup/dedup.py:93` KNOWN_SLUGS, then `DEDUP.md`, then
   `dedup.py selftest`; edit `routines/weekly-evaluator.md` slug set + cadence model.
6. **Live mirror, one trigger at a time, lowest-blast-radius first** — for each: `RemoteTrigger get <id>` →
   copy full `session_context` + `environment_id` + content → string-insert the new prompt against a unique
   anchor (don't hand-escape ~10 KB) → send `{"job_config":{"ccr":{environment_id, events, session_context}}}`
   with the **complete** `session_context` and new cron → **re-GET and byte-diff** stored vs intended; retry
   on mismatch. Re-substitute the redacted `${FETCH_PROXY_TOKEN}`. Order:
   1. **Science** (`trig_01YLiCr5YJ2XNh2QyPbkyzQP`): new prompt + cron `0 15 * * 3` + slug `science`.
   2. **AI/ML** (`trig_01QVL6eSmHTUrmnSLHrpNN9Q`): new prompt + cron `30 19 * * 2,5`.
   3. **News** (`trig_012KfuF2Fc8KxNRS9KT1iuYb`): new prompt + cron `0 17 * * *` + slug `news` + News-only email.
   4. **Weekend** (`trig_01XKzge4DxP6wTjLwtkoYeqj`): prompt only (cron unchanged).
   5. **Evaluator** (`trig_01F5npsKTQTLKekAZ5BczKtG`): prompt only (slug list).
7. **Confirm cadence fires.** Re-GET proves *stored*, not *executed* — shows only at next fire (why step 0
   matters). Verify after first real fires: Science → next Wed `_posts/{date}-science.md`; AI/ML → next
   Tue/Fri only; News → daily evening `_posts/{date}-news.md` + News-only email; confirm **no new
   `*-overview.md` or `*-cyber-papers.md`**.

## 8. Decisions — RESOLVED (user, 2026-06-29)

1. **News cadence — RESOLVED: every day.** Daily evening 19:00 CEST, `0 17 * * *` (incl. weekends).
2. **AI/ML days — RESOLVED: Tue & Fri, midday.** `0 10 * * 2,5` (12:00 CEST). User: "Tue/fri midday, keep
   long read on weekend with in depth. Revisiting most important of the week is here" → AI/ML are midday
   current-awareness editions; the in-depth weekly revisit lives in Weekend (see §3 Weekend).
3. **Science day — RESOLVED: Wednesday.** `0 15 * * 3` (17:00 CEST).
4. **Weekend security — RESOLVED: drop it too.** Security removed pipeline-wide, including Weekend's
   `🛡️ Cybersecurity research of the week`.
5. **Per-story feedback widget — keep** (default; not contested). Only closed feedback loop; produced the
   credibility signal behind affiliations.
6. **Watch frequency — keep 4h** (default; not contested). `0 */4 * * *`; fires 16:00 UTC Wed, which is why
   Science sits at 15:00 not 16:00.
7. **Cross-stream digest — deferred (v2).** The old daily consolidated email is dropped because streams no
   longer co-fire; a digest could only reference the *previous* day's editions.
