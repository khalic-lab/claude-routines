---
layout: single
title: "Weekly Pipeline Review — 2026-10-11"
date: 2026-10-11T11:50:40+02:00
categories: [evaluator]
published: true
---

# Weekly Brief Pipeline Review — 2026-10-11

_Coverage: briefs from 2026-10-05 to 2026-10-11._
_Files read: 5 news, 2 AI/ML (expect ~2), 1 science (expect ~1), 1 sports (expect ~1), 1 weekend, prior review found (2026-10-04, 7 days old)._

The pipeline is healthy on the dimensions that measure the briefs themselves. Every edition carries a Discovery footer, aggregator leakage is zero, identity reconciliation is clean, all eight claim spot-checks matched their sources, and no section went empty. Tagging is disciplined too: exactly one importance-3 story per edition.

Three things need attention:

1. **News skipped one day.** No edition ran on Tuesday 6 October. The 10-07 writer said so in its own Gaps line ("No edition ran on 6 October"). It is a one-off skipped fire, not a history rewrite: the ledger has no trace of it either.
2. **Reach drift is piling up.** Last week's 13 reach flips are still unstamped. This week's computed drift list has grown to **24 domains**, and 6 of those are carry-overs.
3. **Science is still the worst stream.** It has 4 unique domains in 30 days against a target of 10. The cause is structural, and the scout added five institutional newsrooms to the bench.

There is one reasoned vote from a reader, on the AI/ML "Super Intelligence Force" item. It is below the threshold for a proposal, but it points to a real framing slip, covered under Reader feedback below.

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains 30d (worst stream vs its tier) | science 4 (ai-ml 29) | ≥30 news/ai-ml · ≥10 weekly | 🔴 |
| New domains this window (portfolio) | 18 `[new source]` tags this week; 30d new ≥ tier on every stream | ≥2–3/wk (≥10/mo) | 🟢 |
| Top-5 outlet share (worst of news/ai-ml) | news 0.691 (ai-ml 0.618) | ≤0.50 (→0.35); weekly report-only | 🔴 |
| Waiver rate (worst stream) | weekend 0.80 (science 0.75) | ≤50% | 🔴 |
| Discovery footer present (every brief) | 10/10 | 100% | 🟢 |
| T1 citation %                   | 33% (57/175; 7 unregistered) | ≥40% | 🟡 |
| T3 leakage count                | 0 | 0 | 🟢 |
| Non-English citation % (portfolio) | ~27% (47/175) | ≥10% | 🟢 |
| Link sample pass rate           | 6/20; recap 2/8 — **unmeasurable** (egress wall, all failures ERR:56) | ≥90% | ⚪ |
| Fabrication count               | 0 | 0 | 🟢 |
| Single-source rate (portfolio)  | 10.2% (13/128) | <20% | 🟢 |
| Empty section instances         | 0 | <5 | 🟢 |
| Reading-surface flags (§D, surface.py) | 2 (1 SHORT, 1 stale WARN) | 0 | 🟡 |
| Repeat rate (worst stream)      | weekend 0.625 (by construction) | judge | 🟡 |
| Direct-fetch ratio (portfolio)  | ~0.99 (1 via-snippet in 128) | ≥0.35 | 🟢 |
| Feeds with >50% fail rate       | 5 high-volume (openalex, openai.com, api.github, tse.jus.br, imf.org) + low tail | 0 | 🟡 |
| Citations on `reach: blocked` domains w/o `[via snippet]` | 0 | 0 | 🟢 |
| Unconsumed feedback backlog     | 0 | 0 | 🟢 |
| Vendor-PR-lead share (AI/ML, §M) | 8/17 non-paper items vendor-sourced, all tagged and attributed; vendor framing as lead ~1/17 | ≤40% | 🟡 |
| Aggregator-shape failures (§M, of 5) | 0 | 0–1 | 🟢 |
| Personalization misses (§M, of 5) | 0 | 0–1 | 🟢 |
| Affiliation coverage (§N) | 2 of ~27 unique papers "not listed" (~7%) | <20% | 🟢 |
| Halo audit (§N) | no systematic bias; watch | — | 🟢 |

## A–N: Detailed findings

### A. Source diversity & discovery
From `source-health.json` (30-day windows):

- **news**: 45 unique domains, 35 new, top-5 share 0.691, waiver rate 0.483, nothing saturated. Breadth is excellent, and seven `[new source]` tags this week were all genuine first-party primaries: lamoncloa.gob.es, publica.ch, bwl.admin.ch, icc-cpi.int, ofac.treasury.gov, english.president.gov.tw and kuvendikosoves.org (pursued). **Top-5 share has not moved** (0.695 last week, 0.691 now). The outlet-rotation patch applied on 2026-09-25 has now had two full weeks and has not shifted concentration. The concentration is a reachability artefact: SRF (40 curl successes), Al Jazeera (20), Le Temps (13) and DW are the only outlets that curl reliably, so they carry the lead slots. I am not proposing another prompt patch here. A rotation instruction cannot beat the egress wall. Applying the pending reach flips (§K), so writers stop wasting a curl attempt on Le Monde, RFI and the Guardian, is the cheaper lever.
- **ai-ml**: 29 unique, 25 new, **top-5 0.618, worse than last week's 0.544**, waiver rate 0.222. Still one domain short of 30. The jump comes from TechCrunch (14 proxy hits) and Anthropic (three lab-blog items in 10-09) carrying a heavy news week. With only two editions in the window this is one week's noise, so I'm watching it, not patching.
- **science**: 4 unique, 3 new, top-5 1.00, waiver rate 0.75. This is the worst stream again; unique domains fell from 5 to 4. The 10-07 brief was a Nobel week and met discovery honestly through nobelprize.org and news.wisc.edu. The 30-day window, though, is three ordinary editions built on nature.com, arxiv.org and a handful of institutional hosts. The science writer's own probes (actu.epfl.ch, psi.ch, ptb.de, pubs.aip.org) failed even via proxy (§K). The cause is structural, not the prompt.
- **sports**: 12 unique, 8 new, top-5 0.696 (report-only), waiver rate 0.25, bbc.co.uk saturated for a second week. Its discovery waiver (uefa.com and fia.com returned JavaScript shells) is honest and recurring; see §E.
- **weekend**: 27 unique, 22 new, waiver rate 0.80. The waiver rate is inflated by older editions. This week's edition met discovery with three genuine institutional primaries: tuwien.at, icecube.wisc.edu and warwick.ac.uk.

**Tier distribution:** of 175 body citations, 57 are T1 (33%), 111 T2 and 7 unregistered. Most of the unregistered ones are this week's new institutional primaries. Amber, as last week: most T2 citations are first-party outlets on reachable feeds. **No T3 citations appeared.**

**Linguistic/geographic:** about 27% of citations are non-English (SRF, Le Temps, Le Monde, RFI, El País, ANSA, La Moncloa, vd.ch, admin.ch, publica.ch). News covered Brazil, Bosnia, Kosovo, Spain, Mali, Ethiopia, Taiwan, Panama, Ukraine and the Gulf alongside Switzerland.

### B. Aggregator leakage
`briefs.aggregator_leakage` is **empty**. 🟢

### C. Link health: unmeasurable (egress wall), no fabrication found
`linkcheck: 6/20 resolve (2xx/3xx) — window [2026-10-05, 2026-10-11], 153 links total.`
`linkcheck: recap 2/8 resolve (2xx/3xx) — Weekend "Week in headlines", always checked.`

Every failure is **ERR:56**: this sandbox's egress proxy rejected the CONNECT. No failure was an HTTP 404. The six that resolved are exactly the allowlisted direct hosts: Le Temps, Al Jazeera, SRF and anthropic.com. So no recap 404s means no fabrication candidates. I am reporting the dimension as **unmeasurable**, for the fourth straight week.

**Claim spot-checks (8, all on reachable hosts), 8/8 consistent:**
- Anthropic usage-policy item (10-09 ai-ml): the policy does take effect on 12 November, and the "sustained and needless abusive or cruel behavior" clause is quoted verbatim. ✔
- Eduardo Bolsonaro arrest warrant (10-09 news, Al Jazeera): matches. ✔
- Esther Friedli declining to run (10-10 news, SRF): Toggenburg 24 is the venue, "dreieinhalb Jahre" matches the brief's "three and a half years", and SRF confirmed. ✔
- SVP will present "at least two" candidates (10-10 news, SRF Samstagsrundschau): Aeschi is quoted, matches. ✔
- Edmond de Rothschild trial in Marseille (10-10 news, Le Temps): matches. One small wording mismatch: the brief says "organised money laundering", which follows Le Temps' URL slug ("en bande organisée"), while the article body says "blanchiment aggravé". The mismatch is in the source itself, so this is not a defect. ✔
- CERN collider initiative in Geneva (10-07 news, Le Temps): matches. ✔
- Brazil first round (weekend recap, Al Jazeera): the source gives about 47% vs 44.9%; the weekend writes "about 47% to 45%". News 10-05 gave 47.06/45.12 via RFI, from a different counting stage, and the writer flagged that in Gaps. ✔
- Ethiopian troops entering Mekelle on Saturday (weekend recap, Le Temps): matches. ✔

### D. Section vitality + reading surface
There are no empty sections in any stream.

`surface: 2 flag(s) -- 0 parity miss(es), 1 lede-fallback WARN(s), 0 overdue desk(s)`
- `FLAG SHORT 2026-10-07-science: newest edition shows 5 card(s) of 8 stories (floor 6)`. The edition has 8 stories and 8 kept records, but only 5 reach the feed. Science is the newest science edition, so the floor applies. This looks like the builder's per-desk cap trimming a Nobel-heavy edition, where three Nobel stories also run as weekend cards. The cause is likely the cross-desk dedup in `build_stories_feed.py`, not the writer. **Builder question for Rafael** (Open questions).
- `FLAG WARN _posts/2026-10-03-weekend.md story st-5b5761c99f32: no body parsed`. This is the same WARN as last week, on a now-older edition, so it is stale and not new.
- The weekend has 33 stories and 32 kept records, with no parity flag. The difference is one recap item that shares a story id with its news-edition original, which is legal.

### E. Coverage gap recurrence
Recurring gaps (≥3 occurrences, structural):
1. **openai.com primaries unreachable** (10-06 ai-ml, 10-09 ai-ml, 10-10 weekend): eu-text-provenance, the GPT-6 rollout, the maths release and the influence-operations report. The 8 October report was dropped entirely for lack of a readable primary. openai.com had 14 failures and 3 proxy successes this week. This is the biggest primary-source hole in AI/ML.
2. **US government primaries** (whitehouse.gov in 10-06 ai-ml, state.gov in 10-10 news, plus the WHO feed in 10-07 news): failed even via proxy. Stories fell back to DW and press accounts.
3. **Official sports and electoral result pages are JavaScript shells** (uefa.com, sfl.ch and fia.com in 10-05 sports; tse.jus.br and izbori.ba in 10-05 news; parlament.ch last week). This is a renderer limit, not a reach problem, and no source addition fixes it.

### F. Triangulation rate
Single-source rates: news 0.188 (9/48), ai-ml 0.086, science 0.125, sports 0.0, weekend 0.0. The portfolio rate is 10.2%. 🟢 News sits near its 25% ceiling but is honest: every `[single-source]` tag is paired with a Gaps line naming the missing primary.

### G. Tag discipline
These counts come from health.json. ai-ml has 19 `[preprint]` and 8 `[vendor PR]`, weekend has 10 `[preprint]` and 4 `[vendor PR]`, and there are 3 `[disputed]` in total.
- `[preprint]`: all arXiv abstracts in 10-06 and 10-09 are tagged. The 10-09 count is 9 tags against 10 arXiv links, because one arXiv link is a citation inside another item, not its own paper. ✔
- `[vendor PR]`: all six first-party lab items I sampled are tagged (Haiku 5.5, the usage policy, Cyber Mission, Mistral Large 4, EmbeddingGemma 2, Aleph Alpha Kolibri). ✔
- `[disputed]`: the OpenAI fired-researchers item (10-09) is a textbook correct use, with both sides presented as interested parties.
- `[new source]` is junk-anchor safe. Spot-checks: icc-cpi.int (the court's own statement) and publica.ch (the pension fund at the centre of the leak story) are both genuine primaries. `sources/candidates.jsonl` held no entries before today's scout additions; tagged domains are going straight into the registry as candidates (pubs.acs.org and pubs.rsc.org now appear there dated 2026-10-04).
- `[via snippet]`: 1 use all week (the FT revenue item, paywalled), down from near zero. Flat-low is the healthy state.

### H. Topic balance (weekend)
There are 14 ML papers and 14 science papers, so `ml_share` is **0.50**, right on target. 🟢

### I. Repetition detection
Repeat rates are 0.0 on every daily or weekly writer. Weekend is **0.625** (20 of 32 stories), which is by construction: the deep read re-runs the week's Nobels, white dwarf and arXiv papers with the same story ids. That is legitimate for a weekly synthesis as long as the re-runs add depth. A spot-check of the Physics Nobel item (st-b93690c1e96a, weekend) against science's st-0f117c5a2e24 shows the weekend version is a distinct record written up at deep-read length, so it is not a re-summary defect. However, the Chemistry Nobel, Medicine Nobel and white-dwarf items reuse the science stream's story id verbatim (st-81867e437b1d, st-ec394220b5de, st-eb23978bb234). That is fine for identity, and likely explains §D's science SHORT flag.
`reconcile: 0 flagged, 0 resolved-by-merge, 23 editions checked`. 🟢

### J. Cross-week trend
See the section below.

### K. Feed reachability and direct-fetch rate
The direct-fetch ratio is ~1.0 on every stream (computed footers), and via-snippet is 1 portfolio-wide. 🟢

**Feeds failing >50% with little or no success** (net failures, not counting the curl-then-proxy pattern):
- `api.openalex.org`: 23 failures, 0 successes. **Third straight week dead** from both curl and proxy. The science writer keeps spending calls on it. Proposal: mark `reach: blocked` or drop it from the science fetch list (Open questions; this is a registry field, so Rafael decides).
- `openai.com`: 14 failures, 3 proxy successes. See §E. This hurts editorially more than any other feed.
- `api.github.com`: 13 failures, 3 proxy successes, likely rate-limited unauthenticated calls.
- `tse.jus.br`: 5/0. `imf.org`: 5 failures, 1 success. Low tail at 2/0: actu.epfl.ch, news.sbb.ch, psi.ch, ptb.de, pubs.aip.org, state.gov, whitehouse.gov, timesofisrael.com, uefa.com.
- nature.com shows 31 failures against 4 curl and 29 proxy successes, which is the curl-first pattern. It works through the proxy.

**Method comparison:** curl carries only SRF (40), Al Jazeera (20), export.arxiv.org (18), Le Temps (13), Quanta (12) and anthropic.com (5). Everything else lives on the proxy.

**Reach drift (computed):** there are **24 flips** this window, all copied into `proposals/registry-2026-10-11.yml`. Six are carried over from the still-pending 2026-10-04 file: arxiv.org (abstract host only; export.arxiv.org stays direct), lemonde.fr, rfi.fr, theguardian.com, huggingface.co and simonwillison.net. The 18 new ones include techcrunch.com (0 curl / 14 proxy), nobelprize.org (11), vd.ch (9), kyivindependent.com (8), autosport.com (7), elpais.com (6) and terrytao.wordpress.com (6). Each flip saves a doomed curl attempt per fetch.

**Domains that shouldn't be cited:** no citations of `reach: blocked`/`blocked-paywall` domains without `[via snippet]`. The FT citation is correctly marked `[via snippet]`. No `never:` domains appeared. 🟢

### L. Output volume
- **weekend**: 6248 words vs 3631 last week (+72%), but stories went from 19 to 33 (+74%). Words per story is flat, so this is not a flag. It is still the largest brief by far.
- **news**: 1611 words vs 1154 (+40%), with average stories per edition rising from ~7 to ~9.6 (+37%). Proportional; no flag.
- **science**: 2131 words vs 1109 (+92%), with stories going from 5 to 8 (+60%). Words per story rose about 25%, a borderline flag. The cause is a Nobel week with three prize explainers. It is a one-week event, so I am watching it, not patching.
- **ai-ml**: 3009 vs 2932 (+3%). **sports**: 1146 vs 1386 (−17%).

### M. Editorial shape
- **Vendor-PR-lead share (AI/ML):** 8 of 17 non-paper items are vendor-sourced. Every one is tagged `[vendor PR]`, attributes claims ("on Anthropic's own table", "Mistral claims"), and most add a skeptical note ("the weights are not out yet", "if the weights ship as promised"). Each brief opens with arXiv research, not a vendor item. 10-09 does run three consecutive Anthropic items at the top of the Lab-blogs section, which reads as a cluster. I'm calling this amber, not red: the framing is disciplined; only the count is high in a release-heavy week.
- **Aggregator shape (5 leads: news 10-07, 10-08, 10-09 and 10-10, plus the sports lead):** 0 failures. Each lead cites a primary or wire-grade source: the Kyiv Independent with Air Force figures, the Nobel Committee press release, OFAC listings plus the ICC statement, and SRF. Each adds a "Why it matters" the source doesn't state.
- **Personalization (5 stories):** 0 misses. Swiss items carry a concrete CH angle: VAT points and AHV cost, Vaud's unemployment-counting caveat, Publica data fields including AHV numbers. The Pillay and Brazil leads rightly carry no forced CH angle. EmbeddingGemma 2 has a correct builder angle (local semantic search on Apple Silicon).

### N. Affiliation element
- **Coverage:** 2 of about 27 unique papers read "(affiliation not listed)": arXiv 2610.11064 and 2610.11291, both in the 10-09 ai-ml brief and repeated in the weekend. That is about 7%. 🟢 Byline-to-record check: 10-06 2610.04083 (Anthropic, Constellation) ✔, 10-09 2610.12445 (FAR.AI) ✔, and 10-09 2610.10422, whose byline reads "A. Nautiyal (Independent Researcher)" while the index record has `affiliations: null`. That is a small Step C omission: "Independent Researcher" should be recorded.
- **Halo audit:** the three unaffiliated or independent papers are all importance 1. Lab-affiliated papers in the same edition are split: FAR.AI and Stuttgart at 2, while MATS/Google DeepMind, Imperial and Duke are at 1. Six of nine 10-09 papers are at 1. There is no systematic prestige skew, but all three no-affiliation papers sitting at the floor is worth watching for one more week.

## Prior proposals status
- `proposals/registry-2026-10-04.yml`: **pending, not applied** (unstamped). All 13 reach flips are still `reach: direct` in `sources/registry.yml`; 6 recurred in this week's drift list. The scout adds pubs.acs.org and pubs.rsc.org are present in the registry as `status: candidate` (dated 2026-10-04), but the file is not stamped. They got there through the candidate path, not Rafael's apply step.
- `proposals/reader-model-2026-10-04.json`: had no proposals. Nothing to verify.
- The 2026-09-27 items were verified as landed last week, and nothing has regressed.

## Source scout (Sunday duty)
- **Stream picked: science.** Its new-domain ratio is the lowest at 3/3 = 1.0×, against sports 8/3, weekend 22/3, ai-ml 25/10 and news 35/10. It also has the worst unique count (4 vs ≥10).
- **Candidates:** five institutional research newsrooms that the science registry affinity lacks. All returned `000 / connect_rejected` from this egress, which is the policy wall, not a verdict on the sites. All five were appended to `sources/candidates.jsonl` with `reach: proxy-needed`:
  - embl.org: EMBL news feed.
  - news.uzh.ch: University of Zurich. A Swiss-university gap; ETH, EPFL, UNIGE and UNIBE are already present.
  - ista.ac.at: ISTA.
  - weizmann.ac.il: Weizmann Institute.
  - riken.jp: RIKEN research news.
- **Re-probes** of the 5 stalest `reach:` entries (bootstrap-only lifecycle):
  - aljazeera.com: 200 ✔ (direct confirmed).
  - acoup.blog, alignment.openai.com, amnesty.org, appleinsider.com: connect_rejected by the egress policy. Inconclusive, so no flips proposed.
- **Fetches used: 10 of 20.** The 8 claim checks in §C are counted separately. The caveat is the same as every science scout: the binding constraint is reachability, not candidate supply.

## Patch proposals (for human review)
**No prompt patches this week.** The A–N findings are either structural, owned by the registry (reach flips, openalex), or one-week events (the ai-ml top-5 spike, the science Nobel-week length). The one editorial slip (below) has a single reader signal, under the bar. Re-patching News rotation would be the third attempt at a problem that reachability causes. Applying the reach flips comes first.

## Reader-feedback → profile proposals
There were 12 ledger feedback events in the window: health.json counts news up 2 with 1 retraction, and ai-ml up 4, down 2, with 3 retractions. Every reasoned event, with its disposition:

- **ai-ml 2026-10-06, st-d00c2ce656e2, "Trump creates a 'Super Intelligence Force' with a 120-day mandate", 👎, "Don’t you dare call it Super Intelligence..,"**. **Deferred**: one story, below the 2-distinct-stories bar. A bare 👎 on the same story a few seconds earlier is the same signal. Editorial note: the reader has a point. The cited source's own headline is "Trump launches Super Intelligence Force that has nothing to do with actual superintelligence". The brief kept the brand, put it in quotes, and dropped the source's key framing. There is no "Why it matters" and no line saying what the unit actually is. This is the same family as the 2026-09-27 Die Linke contested-label rule (reader-profile.md), applied to official branding instead of party labels. If a second story draws the same complaint, the proposal writes itself as an extension of that line: "official names that make a claim (e.g. 'Super Intelligence Force') get a one-clause reality check from the source."

All other events are bare taps or up/retract toggles, which are noise by the filter. Nothing clears the bar, so **no auto-applied learned-preference line** and no source-weights proposal.

## Machine-readable proposals
- `proposals/registry-2026-10-11.yml`: 24 reach flips (6 marked CARRIED from the pending 2026-10-04 file) and 5 scout candidate adds, all `applied: false`.
- `proposals/reader-model-2026-10-11.json`: empty `proposals`, with the feedback disposition recorded in `note`.

## Cross-week trend
| Metric | 09-27 | 10-04 | 10-11 |
|---|---|---|---|
| news top-5 share | — | 0.695 | 0.691 (flat) |
| ai-ml top-5 share | — | 0.544 | 0.618 ↑ (worse) |
| science unique 30d | — | 5 | 4 ↓ |
| weekend waiver rate | — | 1.00 | 0.80 ↓ (better) |
| aggregator citations | 0 | 0 | 0 |
| T3 leakage | 0 | 0 | 0 |
| empty sections | — | 0 | 0 |
| via-snippet (portfolio) | ~0 | 0 | 1 |
| reach-drift flips | 2 | 13 | 24 ↑ |
| link sample | unmeasurable | 5/20 unmeasurable | 6/20 unmeasurable |

Quality on the briefs themselves (sourcing discipline, tags, triangulation, fabrication) is holding flat at good. The deteriorating line is **registry bookkeeping**: reach drift nearly doubles each week while proposals sit unapplied.

## Open questions for human review
1. **Apply the reach flips.** Two weeks of unapplied flips (13, then 24 including 6 carry-overs). One apply pass on `proposals/registry-2026-10-04.yml` and `-10-11.yml` clears it. Should reach drift be auto-applied, like learned-preference lines? It is computed writer telemetry, not judgment.
2. **api.openalex.org** has been dead for three weeks (23/0 this week). Set `reach: blocked` or remove it from the science plan?
3. **`sources/registry.yml` is not strict YAML.** Line 1017 (`note: sports: https://www.letemps.ch/sport.rss …`, on letemps.ch) has an unquoted colon, so PyYAML `safe_load` fails ("mapping values are not allowed here"). The repo's own parser and the test suite tolerate it, so nothing in the publish path breaks, but any standard-YAML consumer will crash. Quoting that note fixes it.
4. **Science SHORT flag (surface.py)**: is the builder trimming the 10-07 science edition to 5 cards because three of its story ids also appear in the weekend? If so, the floor check and the cross-desk dedup disagree; one of them needs a rule.
5. **News skipped 6 October.** Was this a one-off scheduler or quota event? The writer noticed and reached back for Swiss releases, so no coverage was lost. A second skip would point to a trigger problem.
6. **Test suite in the routine sandbox**: 3 failures (`test_dualwrite` unwritable-ledger test, two `test_fold` crash-safety tests). They come from the sandbox running as root: permission-denied induced failures don't happen. This is an environment artefact, not a code regression, but worth knowing if anyone runs the suite here.
7. **Reader brief-proposals**: no `proposals/*.jsonl` reader records exist, so there is nothing to surface.
