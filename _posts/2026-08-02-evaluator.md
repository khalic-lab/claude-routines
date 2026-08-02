---
layout: single
title: "Weekly Pipeline Review — 2026-08-02"
date: 2026-08-02T11:46:22+02:00
categories: [evaluator]
published: true
---

# Weekly Brief Pipeline Review — 2026-08-02

_Coverage: briefs from 2026-07-27 to 2026-08-02._
_Files read: 6 news, 2 AI/ML (expect ~2), 1 science (expect ~1), 1 sports (expect ~1), 1 weekend, prior review found (2026-07-26, 7 days old)._

The pipeline is healthy and productive: 11 of 11 expected (slug, date) pairs landed, every brief carries a Discovery footer, reconcile is clean (0 flagged / 24 editions), the feedback fold is caught up (0 unconsumed), and continuity is intact. The editorial quality is high — this week's Weekend cross-threads and Science muon/Fields synthesis are among the strongest the pipeline has produced, and a reader said so. The problems this week are almost entirely **instrumentation**, not content: two evaluator self-metrics keep crying wolf for a third straight week, and a stale `git push failed` footer is now printing on 8 of 11 briefs despite every one of them reaching origin. Discovery concentration in **Science** (top-5 share 1.00) is the one genuine content deficit, and it is a dormant-source-activation problem, not a missing-source one.

## Health summary

| Metric | Value | Target | Status |
|---|---|---|---|
| Unique domains 30d (worst stream: science / sports) | 7 | ≥30 | 🔴 |
| New domains this window (`[new source]` tags, portfolio) | ~10 | ≥2–3/wk | 🟢 |
| Top-5 outlet share (worst stream: science) | 1.00 | ≤0.50 | 🔴 |
| Waiver rate (worst stream: sports) | 1.00 | ≤50% | 🔴 |
| Discovery footer present (every brief) | 11/11 | 100% | 🟢 |
| T1 citation % (portfolio) | ~40% | ≥40% | 🟡 |
| T3 leakage count | 0 | 0 | 🟢 |
| Non-English citation % (portfolio) | ~19% | ≥10% | 🟢 |
| Link sample pass rate | 3/20 | ≥90% | ⚪ unmeasurable |
| Fabrication count | 0 | 0 | 🟢 |
| Single-source rate (portfolio) | ~7% | <20% | 🟢 |
| Empty section instances | 3 (all false positives) | <5 | 🟢 |
| Repeat rate (worst stream: news) | 0.26 | judge | 🟢 (legit ongoing) |
| Direct-fetch ratio (portfolio) | ~0.98 | ≥0.35 | 🟢 |
| Feeds with >50% fail rate | ~4 content-relevant | 0 | 🟡 |
| Citations on `reach: blocked` domains without `[via snippet]` | 0 | 0 | 🟢 |
| Unconsumed feedback backlog | 0 | 0 | 🟢 |
| Vendor-PR-lead share (AI/ML, §M) | ~25% | ≤40% | 🟢 |
| Aggregator-shape failures (§M, of 5) | 0–1 | 0–1 | 🟢 |
| Personalization misses (§M, of 5) | 0 | 0–1 | 🟢 |
| Affiliation "not listed" rate (§N, papers) | ~20% | <~20% | 🟡 |
| Weekend ML share (§H) | 0.58 | 0.35–0.65 | 🟢 |

## A–N: Detailed findings

### A. Source diversity & discovery
Portfolio unique-domain sum is 92 (30d). The two worst streams by concentration are **Science** (unique 7, top-5 share **1.00**, waiver **0.75**, new_domains 4) and **Sports** (unique 7, top-5 share 0.78, waiver **1.00**, new_domains 7). News (unique 33) and Weekend (24) are healthy on breadth. The key judgment: Science's concentration is **not a missing-source problem** — the registry already carries cern.ch, eso.org, esa.int, mpg.de, elifesciences.org, journals.plos.org, pnas.org, aasnova.org, simonsfoundation.org and quantamagazine.org with science affinity. The 07-29 Science brief *did* reach two of them well (Simons Foundation and AAS Nova, both `[new source]`), but the paper coverage still concentrated on nature.com + arXiv + Quanta, and the writer waived further discovery. This is a **dormant-registered-source activation** deficit, not a coverage gap (see Patch 1). Sports' 1.00 waiver is a reachability wall — its official primaries (sfl.ch, atptour.com, wtatennis.com, formula1.com, letour.fr) were all JS-shells or unreachable in the sandbox; last week's scout candidates for exactly this (esv.ch, olympics.com, uci.ch, rts.ch) remain mostly unpromoted (see Prior proposals).

Tier distribution: portfolio T1 ≈ 46/115 ≈ **40%** (at target). This is carried entirely by arXiv (T1) in AI/ML and Weekend. **News runs T1 = 0 across all six editions** — but that is a tiering artifact, not a quality failure: news's primaries (SRF, Le Temps, Al Jazeera, DW) are classed T2, and there is no T1 wire in the news source set. New domains this window (via `[new source]` tags): ~10 distinct (news 6, ai-ml 2, science 2) — well above the ≥2–3/wk target. T3 leakage: 0.

Linguistic diversity is a genuine strength: News cited FR (Le Temps), DE (SRF), and ES (El País, El Mundo) heavily; portfolio non-English ≈ 19%, comfortably above the 10% floor and a direct product of the Swiss/European sourcing charter.

### B. Aggregator leakage
`health.json → briefs.aggregator_leakage`: **empty**. No citations of HN, Reddit, X, Mastodon, Bluesky, etc. 🟢

### C. Link health — UNMEASURABLE this run
`linkcheck.py --check` resolved **3/20** (15%), almost entirely `ERR:56` (curl CONNECT failures) plus one 403 (anthropic.com). This is the evaluator sandbox's egress wall, not broken links: the bearer-less evaluator cannot reach arxiv.org/abs, dw.com, elpais.com, the-decoder.com, theguardian.com by direct curl, while the same URLs were fetched cleanly by the **writers** (whose footers show ok_curl/ok_proxy on all of them). The three that *did* resolve (srf.ch, letemps.ch, quantamagazine.org) are the direct-reachable ones. **I therefore report dimension C as unmeasurable and flag the egress limitation, not a content regression.** The judgment half was salvaged via WebFetch (agent proxy): I verified the **muon g-2 reversal** claim (Science 07-29) against Quanta — accurate, "the BMW group's lattice calculation, Fermilab's muons were wobbling exactly as they should" — and the Quanta feature itself. Other spot-check targets (BBC, Simons Foundation, ARC Prize, physicsworld) 403'd from the sandbox. **Fabrications detected: 0** among reachable claims.

### D. Section vitality
`empty_sections`: Science 1 ("🧠 Why it matters"), Weekend 2 ("🧠 Cross-cutting threads", "🍎 Apple Silicon / local inference ecosystem"). **All three are false positives** — I read each and they contain substantial prose (the Weekend cross-threads is four dense synthesis paragraphs; Apple Silicon is two paragraphs on llama.cpp/MLX; Science "Why it matters" is a prose synthesis bullet). The parser counts `st-` story anchors and marks anchor-free analytical sections "empty." This is the **carried-over rm-4 defect**, now firing on 3 sections across 2 streams (up from 2 last week). Genuine empty sections this week: **0**.

### E. Coverage gap recurrence
Reading the Gaps footers: the recurring cluster is **JS-shell / empty-feed primaries** — Comparis (news housing), vd.ch and admin.ch cantonal feeds (news), the SNB press page (news), and the sports official sites (sfl.ch, atptour, formula1, letour.fr). This has recurred ≥3 weeks and is structural: these publishers serve results/tables via client-side JS the sandbox can't render. The mitigation is registry reach flips (proxy) + the sports candidate promotions, both already in the proposal pipeline.

### F. Triangulation
`single_source_rate`: ai-ml 0.154, news 0.051, science 0.25, sports 0.0, weekend 0.024. Portfolio ≈ 7%, well under 20%. Science's 0.25 nominally exceeds the 25% single-stream bar, but it is 1 of 4 citations (the Paxlovid long-COVID figure honestly tagged `[single-source]` because the Lancet primary wasn't reachable) — a small-sample artifact, not a triangulation failure. 🟢

### G. Tag discipline
Counts (health.json): ai-ml — preprint 20, vendor PR 3, disputed 1, new source 2; news — new source 6, disputed 1, via snippet 1; weekend — preprint 19, vendor PR 4; sports — via snippet 2; science — new source 2. Spot-checks: `[preprint]` correctly on every arXiv item sampled; `[vendor PR]` correctly on MAI-Cyber, Gemini Robotics 2, OpenAI price cut, and the Weekend model drops; `[disputed]` used well on the ARC-AGI-3 7.8%-vs-38.3% harness dispute (07-31 ai-ml) and the Japan quake 6.8-vs-7.1 magnitude (07-30 news). `[new source]` — I checked the two freshest candidates I could reason about (foreignpolicy.com, fcc.gov): both genuine primaries, no junk anchors. `[via snippet]` rates are near-zero and *dropping* (portfolio 2 total) — the curl-first chain is working; no stream shows rising via-snippet. 🟢

### H. Topic balance (Weekend)
`weekend_balance`: 22 ML / 16 science, ml_share **0.579** — inside the [0.35, 0.65] band. 🟢

### I. Repetition & identity integrity
`reconcile.py`: **0 flagged, 0 resolved-by-merge, 24 editions** — no id fork. News repeat_rate 0.26 (10 repeats) is the highest, but every repeat is legitimate `[ongoing since]` tracking with a **new dated fact**: the Japan/Kumamoto quake (07-28 "50 injured" → 07-29 "13 dead" → 07-30 "~30 dead"), the daily US–Iran strike exchanges, and the Ceuta crossing (07-31 → 08-01, rising toll). None are re-summaries. Weekend's 0.14 is the "Week in headlines" digest deliberately re-anchoring the week's news events with event-dates — by design. 🟢

### J. Cross-week trend
Vs the 2026-07-26 review: source concentration is roughly flat (Science still top-5 share ~1.0, Sports still waiver ~1.0 — both are the same reachability/dormancy issues); via-snippet rate continues to fall (curl-first chain holding); direct-fetch ratio remains excellent (~0.98). The **new** regression this week is the stale `git push failed` footer spreading to 8/11 briefs (see K/pipeline defect below) — last week it was noted on fewer, and one edition (07-31 news) even got a follow-up commit to strip it.

### K. Feed reachability & direct-fetch
Per-stream direct-fetch ratios are all at or near ceiling: news 0.97, ai-ml 1.00, science 1.00, sports 0.75, weekend 1.00 — every stream far above its range. The curl-first wrapper is doing its job (export.arxiv.org, srf.ch, letemps.ch, aljazeera.com, quantamagazine.org all serving via **curl**; arxiv.org, nature.com, the-decoder.com, huggingface.co carried by **proxy**). Feeds failing >50% of attempts number ~15 in raw count, but most are **non-content endpoints or JS shells** (api.github.com rate-limited, comparis.ch/admin.ch/vd.ch JS-or-empty, uber.com/eng.uber.com 404). The **content-relevant** >50% failures are four: **swissinfo.ch** (4 fail / 0 ok — cited last week via proxy; reach flip pending), **elpais.com** (7 fail direct / 0 ok — but feeds.elpais.com works via proxy), **france24.com** (13 fail / 1 ok proxy), and **sfl.ch** (sports league, empty body). No citation appeared on a `reach: blocked` domain without `[via snippet]`; the two via-snippet uses (El País on 07-27, atptour/wtatennis on sports) are correct.

### L. Output volume
`words_mean` vs prev week: news 1,176 (↑ from 1,022, +15%), ai-ml 2,867 (↓ from 3,572), science 1,111 (↓ from 1,277), sports 1,348 (↑ from 1,293, +4%), weekend 7,077 (↑ from 6,320, +12%). No stream breached the +25% WoW cap. News's +15% tracks a genuinely heavier news week (two wars, Ceuta, Japan quake, Gaza framework) with matching story counts, not padding. Weekend's +12% at 7,077 words is the one to watch — it is long *and* the only stream with meaningful repeat_rate besides news — but it is within cap and the length buys real synthesis this week. No output-cap lever needed yet.

### M. Editorial shape
- **Vendor-PR-lead share (AI/ML): ~25%** (≈3 of ~12 news items lead with vendor framing: MAI-Cyber, Gemini Robotics 2, OpenAI price cut) — under the 40% flag, and each is explicitly `[vendor PR]`-tagged with skeptical framing ("every number here is Microsoft's own on a benchmark it selected"). 🟢
- **Aggregator-shape (of 5 leads): 0–1 failures.** News leads pair a primary (SRF/Al Jazeera/Le Temps) with added CH/geopolitical judgment; AI/ML leads pair arXiv primaries with independent analysis. The nearest miss is a couple of AI/ML industry items resting on The Decoder (secondary), but they add the "national-security framing vs commercial pressure" read the source lacks. 🟢
- **Personalization (of 5): 0 misses.** CH/builder framing is present where available and not forced where absent — Swiss firefighters in France, OFDF restructuring, UBS/SNB, connected-car espionage, cross-border housing, Beznau reactor shutdown, the Swiss tariff thread. 🟢

### N. Affiliation element (papers)
- **Coverage: ~20% "(affiliation not listed)"** (≈10 of ~50 paper bylines) — right at the flag line. The unlisted ones cluster on the **freshest** papers (submitted 2026-07-30, covered 07-31), whose arXiv HTML author blocks hadn't rendered — an honest no-fabrication fallback the footers document explicitly, not a skipped Step-C field. 🟡, explained.
- **Halo audit: no prestige bias detected.** This week's independent-researcher / unlisted-affiliation papers were featured **on merit, prominently** — the Mirzaei "self-refine doesn't beat repeated sampling at equal cost" negative result *led* the 07-31 arXiv section, and the L. Dong emergence-as-joint-alignment and B.H. Yoon capacity-lower-bound papers got full treatment. Big-lab papers were not systematically scored higher. 🟢

### Continuity / self-delivery guard
Previous evaluator: `_posts/2026-07-26-evaluator.md`, **7 days old** — healthy, no staleness flag. **`continuity.off_main` reported 14 `commits_not_on_main`, but this is the known rm-3 false positive, NOT a real diversion.** I verified: HEAD == origin/main == `28fd077`; the sandbox is in detached HEAD after `git pull --ff-only`, and the local `main` ref is stale at `77c025c`, so `git log --not main` reports every pulled commit as "off main." Every listed commit is a normal News/AI-ML/Weekend/drain publish provably present on origin/main, and `remote_branches` is empty — no `claude/*` stranding, no `outcomes` diversion. **Not a pipeline defect this week.** (Correctly distinguishing this from the real stranding class is exactly what rm-3's fix would make automatic.)

## Prior proposals status

From `proposals/reader-model-2026-07-26.json` and `registry-2026-07-26.yml`:

- **rm-1** (reader-profile.md "unreliable narrator" line) — **applied & verified.** The dated line is present in `reader-profile.md` (line 50), auto-applied by the evaluator as stamped.
- **rm-2** (ai-ml/weekend: attach canonical primary URL even when JS-rendered) — **pending, not stamped** (`applied: false`). The *behavior* appears present in practice this week (07-31 ai-ml attaches Anthropic + FCC + MCP-blog primaries alongside secondaries), but the prompt patch itself is unverified and human-gated. Carried.
- **rm-3** (metrics.py `build_off_main`: compare against origin/main) — **NOT applied, 3rd consecutive week.** `build_off_main` still runs `git log --not main`. This run reproduced the exact false positive it predicts (14 phantom off-main commits). Re-proposed below.
- **rm-4** (metrics.py section-vitality: detect emptiness by body text, not `st-` anchors) — **NOT applied, 3rd consecutive week.** Fired on 3 prose sections this week (up from 2). Re-proposed below.
- **registry-2026-07-26.yml** (`applied: false`) — reach flips **science.org / swissinfo.ch / cell.com / journals.aps.org** (direct→proxy) **not landed** (registry still shows `reach: direct` on all four). Candidate promotions: **olympics.com landed** (now `status: probation, reach: proxy`) but is unstamped; **esv.ch, uci.ch still `candidate`**; the proposed sports **rts.ch** promotion did not land (the registry's rts.ch is a separate news-stream entry). Carried below.

## Source scout (Sunday duty)

**Stream picked: Science** (lowest new_domains = 4; top-5 share = 1.00; waiver = 0.75). **Fetches used: 6** (all WebFetch; well under the 20 budget) — but evaluator egress 403'd every scout/spot-check target except Quanta, so direct vetting was not possible. Per protocol, genuinely-primary candidates are appended with `reach: proxy-needed` for the bearer-holding writers to vet at first citation.

Appended to `sources/candidates.jsonl` (3, all science physics-primaries the registry lacks, matching this week's physics-heavy science content):
- **physicsworld.com** — IOP Publishing / Institute of Physics news & features.
- **symmetrymagazine.org** — Fermilab/SLAC joint particle-physics magazine.
- **cerncourier.com** — CERN Courier, HEP primary-adjacent (complements registered cern.ch).

**Re-probe of stale reach entries: skipped** — the evaluator sandbox blocked every direct curl/WebFetch this run (403/ERR:56), so no probe would produce valid reach evidence. The reach-flip evidence continues to come from the writers' own footers (swissinfo.ch, science.org, elpais.com all confirmed reachable-via-proxy in-window), which is what the carried registry proposal rests on.

**Scout's real finding:** Science's deficit is dormancy, not absence. Adding candidates helps at the margin, but the higher-leverage fix is Patch 1 (activate the already-registered dormant science sources before waiving discovery).

## Patch proposals (for human review)

### Patch 1 — Science: reach the dormant registry before waiving discovery
**Target prompt:** Science (`routines/src/science.md`)
**Section affected:** Discovery / sourcing block
**Issue:** Science top-5 outlet share is 1.00 and waiver rate 0.75, yet the registry already carries ~10 science-affinity primaries (cern.ch, eso.org, elifesciences.org, journals.plos.org, pnas.org, mpg.de …) that go dormant. The writer waives discovery rather than reaching them.
**Proposed change:**
> **Before:**
> ```
> End with exactly one Discovery footer line: `- Discovery: met (…)` or
> `- Discovery: waived — <concrete reason>`.
> ```
>
> **After:**
> ```
> Before waiving discovery, the preflight plan lists registered science domains with
> last_cited=None (dormant). Attempt at least two of them this edition; only waive if
> they are unreachable or carry nothing on-topic, and name which you tried in the waiver
> reason. End with exactly one Discovery footer line: `- Discovery: met (…)` or
> `- Discovery: waived — <concrete reason, incl. which dormant domains were tried>`.
> ```
**Why this helps:** Converts an over-concentrated stream's honest waivers into active use of breadth the registry already paid for, lowering top-5 share without inventing sources.
**Risk:** Could nudge the writer to force a weak dormant-source citation to satisfy the instruction — the "only waive if nothing on-topic" clause and the newsroom quality bar should hold that off, but watch the next Science edition's citation quality.

### Patch 2 — publish.py: stop printing a `git push failed` footer that the push contradicts
**Target:** `tools/publish.py` (mechanical tier — **not a prompt patch**)
**Section affected:** push-verification / footer emission
**Issue:** 8 of 11 briefs this week (07-27 sports, 07-28 ai-ml, 07-29 news+science, 07-30 news, 07-31 ai-ml, 08-01 news+weekend) carry `- git push failed: this edition has NOT reached origin -- retry git push origin main` — yet **all 8 are provably on origin/main** (HEAD == origin/main). The push succeeds (on retry or via the bridge's later drain-reconcile) but the failure line is already baked into the committed body. 07-31 news even needed a follow-up commit to strip it.
**Proposed change:**
> **Before:**
> ```
> # after push attempt: if the initial push returns non-zero, append the failure footer.
> ```
>
> **After:**
> ```
> # after the push+retry sequence completes, re-verify with `git rev-parse origin/main`
> vs HEAD (fetch first). Only append the failure footer if HEAD is genuinely absent
> from origin after all retries. Never write the footer on a push that later succeeds.
> ```
**Why this helps:** Removes a false, reader-visible-in-data self-report that is now on the majority of briefs and pollutes the footer telemetry the evaluator itself reads.
**Risk:** If the re-verify races the remote, a genuinely-failed push could go unflagged — mitigate with a fetch immediately before the rev-parse check.

### Patch 3 — metrics.py: fix the off-main false positive (rm-3, 3rd week)
**Target:** `tools/evaluator/metrics.py` → `build_off_main`
**Issue:** Compares against the local `main` ref, which goes stale in the detached-HEAD sandbox after `git pull --ff-only`, so every pulled commit is reported off-main. Fired again this run (14 phantom commits).
**Proposed change:**
> **Before:**
> ```
> commits = _git_lines(root, ["log", "--all", "--oneline",
>                             "--since=%s" % window_start, "--not", "main"])
> ```
>
> **After:**
> ```
> commits = _git_lines(root, ["log", "--all", "--oneline",
>                             "--since=%s" % window_start, "--not", "origin/main"])
> ```
**Why this helps:** origin/main is the published line the guard actually cares about; the local ref is an artifact of how the routine checks out.
**Risk:** Requires a fresh `git fetch` before metrics run so origin/main is current — the fire-start already pulls, so this holds.

### Patch 4 — metrics.py: section-vitality by body text, not anchors (rm-4, 3rd week)
**Target:** `tools/evaluator/metrics.py` → `_sections` / empty-section detection
**Issue:** Emptiness is inferred from absence of `st-` anchors, so anchor-free analytical/prose sections ("🧠 Cross-cutting threads", "🍎 Apple Silicon", Science "🧠 Why it matters") are false-flagged. 3 false positives this week.
**Proposed change:**
> **Before:**
> ```
> for name, items in _sections(body):
>     s["sections"] += 1
>     if items == 0:
>         s["empty_sections"].append({"post": post_name, "section": name})
> ```
>
> **After:**
> ```
> for name, items, text_len in _sections(body):   # text_len = non-whitespace body chars
>     s["sections"] += 1
>     if items == 0 and text_len < 200:            # empty only if no anchors AND little prose
>         s["empty_sections"].append({"post": post_name, "section": name})
> ```
**Why this helps:** Stops penalising the synthesis sections that are the point of the Weekend/Science briefs; keeps catching genuinely blank sections.
**Risk:** A 200-char threshold could miss a one-line stub section — tune the constant against a couple of known-empty examples.

_(Prioritised by severity: Patch 1 is the one genuine content deficit (dim A); Patch 2 is the spreading pipeline defect; Patches 3–4 are the 3-week-carried instrumentation bugs that keep generating false flags. The pending registry reach flips and sports candidate promotions are carried in the machine-readable file rather than re-argued here.)_

## Reader-feedback → profile proposals

Window feedback (health.json + ledger `ev:"feedback"`): ai-ml +7, news +6 / −2 / 2 retractions, science +2, weekend +3; unconsumed_total 0 (fold caught up). Only **two** votes carried written reasons:
- **news 2026-07-29 (👎):** _"You didn't talk about the Trojan horse of sanctions they're putting inside the bill"_ — on the Russia-sanctions-bill item (st-5fc30718cad9), plus one bare 👎 on the same edition.
- **science 2026-07-29 (👍):** _"Damn fine cross thread"_ — praise for the Science cross-thread synthesis.

**No new auto-applied learned-preference line this week.** Both reasoned votes are **single signals on single stories**, below the ≥2-distinct-stories noise threshold (the bare 👎 on the same news edition is one story double-tapped, which counts as one signal). The sanctions 👎 is on-theme with the already-applied 2026-07-19 / 2026-07-26 "unreliable narrator / supply the omitted legal-factual substance" preference — it is that preference recurring on legislative content, not a new axis, so the standing line already covers it. **If a "read the substance inside the bill, not the headline vote" signal recurs on a second distinct story next week, it warrants sharpening the 07-26 line toward legislative-content specifically** — but a single tap is noise, so nothing is applied or proposed here. The Science 👍 is logged as positive reinforcement for the cross-thread format; single, so no profile edit.

## Cross-week trend

Concentration (Science top-5 ~1.0, Sports waiver ~1.0) is flat vs 2026-07-26 — same reachability/dormancy roots, same pending fixes. Via-snippet continues to fall; direct-fetch stays ~0.98. The one moving-the-wrong-way metric is the stale `git push failed` footer, now on 8/11 briefs (Patch 2). Instrumentation debt (rm-3, rm-4) is unchanged for a 3rd week and is the single most repeatable source of false flags in these reviews.

## Open questions for human review

1. **Three-week instrumentation debt.** rm-3 (off-main) and rm-4 (section-vitality) have now generated false flags for three consecutive reviews. They are ~2-line fixes (Patches 3–4). Is there a blocker to applying them, or should the evaluator stop reporting these two computed sub-dimensions until they're fixed?
2. **The `git push failed` footer (Patch 2)** is the highest-frequency defect this week and self-inflicted by the publish path. Worth prioritising over the content patches.
3. **Sports reachability** remains structurally blocked (all official primaries JS-walled). Last week's scout candidates (esv.ch, olympics.com, uci.ch, rts.ch) are the intended fix but mostly unpromoted — olympics.com landed, the rest are still `candidate`. Promote them so the writer can start citing official sports primaries via proxy?
4. No reader brief-proposals (`proposals/*.jsonl`) directory exists yet — nothing to surface.
- git push failed: this edition has NOT reached origin -- retry `git push origin main` before the session ends.
