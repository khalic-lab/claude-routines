---
layout: single
title: "Weekly Pipeline Review — 2026-11-01"
date: 2026-11-01T11:46:22+01:00
categories: [evaluator]
published: true
---

# Weekly Brief Pipeline Review — 2026-11-01

_Coverage: briefs from 2026-10-26 to 2026-11-01._
_Files read: 6 news, 2 AI/ML (expect ~2), 1 science (expect ~1), 1 sports (expect ~1), 1 weekend, prior review found (2026-10-25, 7 days old)._

The writing had another good week. All six expected News editions ran; Sunday's has not fired yet, which is normal. All 11 editions carry a Discovery footer. Aggregator leakage, T3 leakage, empty sections, identity-reconcile flags and off-main commits are all zero. All 8 claim spot-checks matched their sources. The best editorial moment of the week was how the 10-27 AI/ML and 10-31 Weekend handled OpenAI's claimed proofs (ETH, Kakeya, a QFT existence proof). Both put "claims" in the headline, tagged the item `[vendor PR]` `[disputed]`, named the reviewers along with the reviewers' own line that taking part "is not an endorsement", and explained what a Lean formalisation does and does not settle.

What needs attention is again mostly outside the writing:

1. **The reading surface regressed: 6 lede-fallback WARNs, 5 of them new.** Four are News stories on 10-29 and 10-30, and the cause is a builder defect, not a writer slip. When "Why it matters:" sits on a continuation line *after* the citation run, `_split_inline_why` runs its meta test on the unsplit paragraph. The citations are then no longer trailing, so the middot-chained links read as a byline and the body is dropped (§D). The fifth is the same parenthesised-byline shape as last week's open WARN, with an organisation instead of authors.
2. **The reach-flip backlog is now in its fifth week.** There are 23 computed flips, 18 of them carried from unstamped files. arxiv.org, lemonde.fr, rfi.fr and huggingface.co have been in **all five** files from 10-04 to 11-01. The last stamped registry file is still 2026-09-27.
3. **The registry-sync defect is unfixed and still manufactures drift.** Four of the five new flips (insee.fr, ukrinform.net, agmai.org, rik.parlament.gov.rs) are writer `[new source]` domains registered this week as `reach: direct`. Last week's six scout candidates also landed as `reach: direct`, despite `proxy-needed` (e.g. ox.ac.uk).
4. **Sports is now the worst stream: 4 unique domains in 30 days, with 3 of them saturated.** Its bench already holds about 25 untried candidates, so this is a reach and usage problem, not a shortage of candidates.
5. **openai.com is now effectively dead from the sandbox** (18 fail / 2 ok, all via proxy). Two OpenAI safety posts were *dropped* on 10-30 rather than run on the RSS summary with `[via snippet]`. The computed drift rule cannot catch this, so I've proposed a judgment flip to `blocked`.

There was no reader feedback this week, and no prompt patches are proposed.

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains 30d (worst stream vs its tier) | **sports 4**, science 7 (news 58, weekend 42, ai-ml 33) | ≥30 news/ai-ml · ≥10 weekly | 🔴 |
| New domains this window (portfolio) | 16 `[new source]` tags; every stream at or above its monthly tier (sports exactly 3/3, science 5/3) | ≥2–3/wk (≥10/mo) | 🟢 |
| Top-5 outlet share (worst of news/ai-ml) | news 0.653 (ai-ml 0.548) | ≤0.50 (→0.35); weekly report-only | 🔴 |
| Waiver rate (worst stream) | weekend 0.60 (science 0.50, sports 0.50) | ≤50% | 🟡 |
| Discovery footer present (every brief) | 11/11 | 100% | 🟢 |
| T1 citation %                   | 35.2% (75/213; 7 unregistered) | ≥40% | 🟡 |
| T3 leakage count                | 0 | 0 | 🟢 |
| Non-English citation % (portfolio) | ~35% (heuristic: SRF, RTS, Le Temps, RFI, Le Monde, El País, ANSA, INSEE, admin.ch/fr …) | ≥10% | 🟢 |
| Link sample pass rate           | 3/20; recap 1/6. **Unmeasurable**: every failure is egress ERR:56, with no 404s | ≥90% | ⚪ |
| Fabrication count               | 0 | 0 | 🟢 |
| Single-source rate (portfolio)  | 11.6% (18/155); news 23.2% | <20% (<25%/stream) | 🟢 |
| Empty section instances         | 0 | <5 | 🟢 |
| Reading-surface flags (§D, surface.py) | **6** (6 WARN; 0 parity, 0 overdue) — builder shapes | 0 | 🔴 |
| Repeat rate (worst stream)      | weekend 0.47 (by construction); news 0.014; rest 0.0 | judge | 🟢 |
| Direct-fetch ratio (portfolio)  | 1.0 on every stream (0 via-snippet in the computed footers) | ≥0.35 | 🟢 |
| Feeds with >50% fail rate       | 47 by the raw ratio. Those with no or little net success: openai.com 18/2, science.org 8/1, sec.gov 4/0, tse.jus.br 4/0, ukmto.org 4/0, plus a 1–3/0 tail | 0 | 🟡 |
| Citations on `reach: blocked` domains w/o `[via snippet]` | 0 | 0 | 🟢 |
| Unconsumed feedback backlog     | 0 | 0 | 🟢 |
| Vendor-PR-lead share (AI/ML, §M) | 8/11 non-paper items vendor-sourced, all tagged; vendor framing as the lead in 2/11 (~18%) | ≤40% | 🟢 |
| Aggregator-shape failures (§M, of 5) | 0 | 0–1 | 🟢 |
| Personalization misses (§M, of 5) | 0 | 0–1 | 🟢 |
| Affiliation coverage (§N) | ~6 of ~40 unique papers "not listed" (~15%) | <20% | 🟢 |
| Halo audit (§N) | no prestige skew | — | 🟢 |

## A–N: Detailed findings

### A. Source diversity & discovery
From `source-health.json` (30-day windows):

- **news**: 58 unique domains (52 last week), 46 new, waiver rate 0.207 (0.276), nothing saturated. Top-5 share is 0.653, the fifth straight small improvement (0.695 → 0.691 → 0.685 → 0.662 → 0.653). Four of six editions met discovery, and the tags are first-party primaries: rik.parlament.gov.rs (Serbia's electoral commission), ubs.com (the Q3 results release), insee.fr (GDP and inflation flashes), press.un.org (the MINURSO vote record) and pm.gc.ca (the EU–Canada summit release). The two waivers (10-27 and 10-29) are honest and specific. Each names three primaries tried and the failure mode (bechirot.gov.il empty, unfccc.int blocked, ukmto.org/adif.es/press.un.org unreachable). press.un.org failed on 10-29 and succeeded on 10-31, so the rotation is persistent, not lucky. At this pace the 0.50 bar is still months away, because only SRF, Al Jazeera and Le Temps curl.
- **ai-ml**: 33 unique (34), 27 new, waiver 0.222, top-5 0.548 (0.547), flat. 10-27 met discovery with agmai.org and kimi.ai (Moonshot's own blog), both genuine first-party sources. The 10-30 waiver is honest: mlcommons.org was the edition's institutional first citation but is already registered, and openai.com was unreachable.
- **science**: 7 unique (4), 5 new, top-5 1.00, nature.com saturated, waiver 0.50. **This is the first real improvement in seven reviews.** The 10-28 edition anchored two institutional newsrooms as `[new source]`, uni-wuerzburg.de and news.northwestern.edu. That is the paper-plus-institutional-release pairing last week's Open question 4 suggested counting, and the writer is producing it anyway. Science still sits below the ≥10 tier bar.
- **sports**: **4 unique (6 last week, 9 the week before)**, 3 new, top-5 1.00, **three saturated domains** (autosport.com, bbc.co.uk, srf.ch). It is now the worst stream. Eight stories rest on SRF, BBC, Autosport and swissindoorsbasel.ch (the edition's one new source, which is legitimate). The Gaps line repeats the four-week story: sfl.ch, uefa.com and premierleague.com are "unreachable or JS-only". **The preflight bench is not the constraint.** `preflight.py --slug sports` lists about 25 `candidates_to_try` (iihf.com, swiss-ski.ch, swissolympic.ch, swisstennis.ch, rsi.ch, lequipe.fr, kicker.de, tourdesuisse.ch, and more), and most have `last_cited: None`. The writer is not working through them, or they fail. Its footer shows autosport.com at 5/5 and bbc.co.uk at 12/8 (fail/ok), so even the incumbents need the proxy on every retry. Note also that **bbc.co.uk is still unregistered** (3 body citations this week, 3 last week), yet it is counted as saturated.
- **weekend**: 42 unique (38), 34 new, waiver 0.60 (flat for the third week). The waiver is honest: agmai.org was anchored, uni-wuerzburg.de appeared only as a second source, and noemamag.com and republik.ch (feed failed) did not produce the second anchor.

**Tier distribution:** of 213 body citations, 75 are T1 (**35.2%**, down from 41.9%), 131 T2 and 7 unregistered (bbc.co.uk ×3, uni-wuerzburg.de ×2, news.northwestern.edu, swissindoorsbasel.ch). There is **no T3**. The drop is compositional. The Weekend's 16 arXiv/Verge-anchored ML items and News' heavier DW/RFI/Le Monde wire use (T2) outweighed fewer admin.ch/Nature anchors. It is not a policy slip. 🟡

**Linguistic/geographic:** about 35% non-English by a host/path heuristic (SRF, RTS, Le Temps, RFI, Le Monde, El País, ANSA, INSEE, La Moncloa, Ukrinform, Swiss federal pages in French). News covered about 15 countries alongside Switzerland.

### B. Aggregator leakage
`briefs.aggregator_leakage` is **empty**. 🟢 The 10-27 AI/ML cites simonwillison.net once, as the second source for an Artificial Analysis score. That blog is a registered T2 outlet, not an aggregator.

### C. Link health: unmeasurable (egress wall), no fabrication found
`linkcheck: 3/20 resolve (2xx/3xx) — window [2026-10-26, 2026-11-01], 191 links total.`
`linkcheck: recap 1/6 resolve (2xx/3xx) — Weekend "Week in headlines", always checked.`

All 17 sample failures and all 5 recap failures are **ERR:56**: the egress proxy refused the CONNECT to DW, RFI, Le Monde, arXiv, Nature, the Guardian, El País, admin.ch, BBC, Ukrinform, RTÉ and SNB. **There are zero 404s and zero fabrication candidates.** Every recap URL sits on a host that writer telemetry shows working through the proxy, and the one recap host reachable from here (ecb.europa.eu) resolved 200. This is the seventh straight week the dimension is unmeasurable. (A second run for a recount drew one 429 from SRF, which is rate limiting caused by my re-fetching, not a defect.)

**Claim spot-checks (8, on reachable hosts): 8 consistent.**
- Swiss parts in Russian weapons (10-30 news, SRF): eleven Swiss firms, the Geran-4 and "Filin", Vlasiuk's criticism, the SECO position that most parts are not made in Switzerland, and the u-blox/STMicro statements all match. The `[single-source]` tag is correct (SRF's own investigation). ✔
- Migros merger (10-26 news, SRF + RTS): the 1940s Duttweiler structure, the six regional councils, SonntagsZeitung's ~3,000 jobs, no layoffs until mid-2028, and Irminger/Diethelm stepping down all match SRF. The two-thirds-per-region rule and the 2.3 million members are not in SRF and RTS was unreachable, so those two are **unverified, not contradicted**. ✔ (partial)
- UBS Q3 (10-28 news, UBS + SRF): the $5.1B asset-management outflow and the 97,593 / 99,085 headcount match SRF. The other figures come from UBS's own release (`[official PR]`), which was unreachable from here. ✔
- Saudi intercepts and the Tehran talks (10-27 news, Al Jazeera): three ballistic missiles and four drones, al-Maliki, the Eastern Province, no casualties, and Munir/Kalin all match. ✔
- Lagarde stepping down (10-30 news, ECB): 7 February 2027, Costa informed, the Article 283 TFEU procedure. Matches. ✔
- Pretraining-poison backdoor (10-31 weekend, arXiv API): Qwen3 at 0.6B/1.7B/4B, 0.1% poison, ~92% ASR at 4B, positive at 0.0005%, code public. Matches. ✔
- RSI Arena (10-27 ai-ml / 10-31 weekend, arXiv API): ten agents, and eight of ten improved from Stage 1 to Stage 2. The abstract says "style-adjusted relative rating" and the brief says "preference rating", a slight simplification but not wrong. Modest benchmark gains with no clear link to preference matches. ✔
- Basel 0–0 GC (10-26 sports, SRF Sport): three prior defeats, the injury to the GC goalkeeper and Hammel coming on, Lugano winning at Thun, Sion beating Lausanne. Matches. ✔

### D. Section vitality + reading surface
There are **no empty sections** in any stream. Omissions are disclosed in Gaps (the Weekend's 🍎 Apple Silicon: "no MLX release this week"). That is honest omit-don't-fill.

`surface: 6 flag(s) -- 0 parity miss(es), 6 lede-fallback WARN(s), 0 overdue desk(s)`
- `FLAG WARN _posts/2026-10-29-news.md story st-3b1c1bdf8ebb` (Spain crash toll)
- `FLAG WARN _posts/2026-10-30-news.md story st-fb7d688d5a1f` (Israel final count)
- `FLAG WARN _posts/2026-10-30-news.md story st-9fa21cc3d182` (INSEE Q3)
- `FLAG WARN _posts/2026-10-30-news.md story st-7a4b732422f6` (Oleshky mission)
- `FLAG WARN _posts/2026-10-31-weekend.md story st-c71b778862b5` (Nemotron 3.5)
- `FLAG WARN _posts/2026-10-24-weekend.md story st-5745ce974a94` (carried, last week's Open question 3; unfixed)

**The four News WARNs are one builder defect, and I traced it.** The 10-29 and 10-30 News editions write each story as a bold lead line that ends on its citation run, then `  Why it matters: …` on an indented continuation line (5 and 7 instances). The other four editions put "Why it matters:" inline *before* the citations. The continuation-line form is legal: `routines/src/news.md:46` literally asks for "a 'Why it matters:' line". `parse_post` joins the continuation into one paragraph, so the citation run now sits *mid-paragraph*. `_split_inline_why` (build_stories_feed.py:346) then calls `_is_meta_para(p)` **before** splitting. `strip_trailing_citations` finds no trailing run to peel, because the why text follows it. The leftover ` · [DW, 30 Oct 2026](…)` reads as a byline, the paragraph is classed as meta, it is never split, and `_pick_body` returns "". The ECB story in the same edition has the same shape and survives, because its tail happens not to trip `_is_meta`. The defect is order-dependent, not shape-proof. Fix: in `_split_inline_why`, try the `_INLINE_WHY_RE` split first and run the meta test on the *head* only. Add golden cases for st-fb7d688d5a1f and st-9fa21cc3d182. Card impact: the writer's `display_body` payload carries the authored prose, so the documented fallback still shows the paragraph, and there is no confirmed loss to readers. Some editions now trip it four times, though.

**The Nemotron WARN is last week's shape, generalised.** The bullet ends `([arXiv:2610.38095](u) · NVIDIA · \`[preprint]\` \`[vendor PR]\`)`. Once the tags are stripped, ` · NVIDIA ·  )` is a parenthesised trailing run with an *organisation* byline inside. Like the 10-24 author byline, `strip_trailing_citations` does not peel it. The writer's format is legal. One fix covers both: balance parentheses when peeling the trailing run.

Newest editions keep every story: sports 8/8, science 16/16, ai-ml 15/15, news 11/11, weekend 34/34.

### E. Coverage gap recurrence
Recurring gaps (≥3 occurrences = structural):
1. **Official government, electoral and court primaries that refuse the fetch** (6 of 6 News editions). bechirot.gov.il failed three editions running (the last time behind a bot challenge), along with about a dozen others: tse.jus.br, results.cik.bg, unfccc.int, ohchr.org, adif.es, ukmto.org, OFAC, parlament.ch, dsca.mil, trybunal.gov.pl and more. Each time the writer says so and falls back to wire-grade secondaries. This is structural egress and no source addition fixes it.
2. **openai.com article pages fail through every path** (10-27 ai-ml, 10-30 ai-ml, 10-31 weekend; 18 fail / 2 ok). It is now in four of the last six AI-desk editions. On 10-30 the writer **dropped** OpenAI's "How we detect frontier model misalignment" and Model Spec posts rather than running them on the RSS summary. That is a coverage loss on the reader's core beat (AI safety), and the prompt already allows the `[via snippet]` fallback (`routines/src/ai-ml.md:34`). Registry proposal below.
3. **Science/APS journal pages** (science.org 8/1, journals.aps.org, physics.aps.org) in science 10-28 and weekend 10-31, the third week. Crossref metadata and the institutional releases stand in, which is a sound workaround.
4. **Official sports pages are JavaScript shells or unreachable** (sfl.ch, uefa.com, premierleague.com) for a fifth week (§A).

### F. Triangulation rate
Single-source rates: news **0.232** (16/69, up from 0.148), ai-ml 0.036, science 0.062, sports 0.0, weekend 0.0. The portfolio rate is 11.6%. 🟢 News is under its 25% stream bar but rising. Each `[single-source]` item I read says why: the SRF investigation into Swiss parts is SRF's own story, and the Dnipro strike rests on a developing Kyiv Independent report, as stated in Gaps. This tracks the official-primary wall in §E: when the government page refuses, the second source often refuses too. Watching, not flagging.

### G. Tag discipline
These counts come from health.json. ai-ml: 17 `[preprint]`, 7 `[vendor PR]`, 2 `[new source]`, 1 `[disputed]`, 1 `[via snippet]`. News: 22 `[official PR]`, 16 `[single-source]`, 8 `[new source]`. Weekend: 10 `[preprint]`, 3 `[vendor PR]`, 3 `[new source]`, 2 `[official PR]`, 1 `[disputed]`.
- `[preprint]`: all 5 sampled arXiv items carry it (the seed-jailbreak, shutdown, BF16 RL, CoT-reliance and backdoor papers). ✔
- `[vendor PR]`: Kimi K3.1 Pro, Gemini 4 Carbon, Mistral Large 4, the Cohere/Qwen story and Nemotron 3.5 are all tagged. ✔ The Anthropic analyst study (10-30) and the Anthropic S-1 item: the study is first-party research and is attributed in the headline ("Anthropic study finds"). The S-1 is a regulatory filing confirmed through EDGAR full-text search, so it is correctly *not* tagged vendor PR.
- `[disputed]`: the OpenAI ETH/Kakeya item. The claims are unverified, the reviewers explicitly decline to endorse, and AGMAI has objected publicly. Textbook use. ✔
- `[official PR]`: News uses it 22 times, up from 1. Usage is correct (ECB, INSEE, UBS, La Moncloa releases). The jump comes from more first-party anchoring this week, which is the discovery push working. One format wobble: on 10-28 UBS the tag sits *before* the first link (`[official PR] [UBS, …](…)`), elsewhere after it, and bare-bracket rather than backticked on 10-30 INSEE. This is harmless to the parser here but inconsistent.
- `[new source]`: spot-checked two. **insee.fr** is France's national statistics office, cited for its own GDP flash. **agmai.org** is an IAS-hosted advisory group's statement, the primary for its own objection. Both are genuine, not junk anchors. ✔ `sources/candidates.jsonl` was empty at fire time because the sync folds it.
- `[via snippet]`: 1 tag (ai-ml) in the text, 0 in the computed footers. Flat-low.

### H. Topic balance (weekend)
There are 16 ML papers and 16 science papers, so `ml_share` is **0.50**, on target for a fifth straight week. 🟢 One editorial caveat: the 🔭 lead item (OpenAI's ETH/Kakeya claims) is a vendor announcement anchored on The Verge, not a paper. It counts as one science item. That is defensible given the stakes, but it is not research the reader can read.

### I. Repetition detection
Repeat rates are 0.0 on ai-ml, science and sports, and 0.014 on news (1/69). Weekend is **0.47** (16/34, down from 0.588), by construction: the deep read carries the week's papers forward with their story ids. A spot-check of the RSI Arena and Masked Erosion papers shows the Weekend re-framing rather than copying. Cross-cutting thread 2 ties them to the RLVR theorem and Anthropic's analyst study as one "optimising what the gate sees" pattern, which is the deep-read mandate working. Israel's election appears in four News editions (10-27 vote, 10-28 no majority, 10-30 final count, weekend recap), and each carries a new dated fact under `[ongoing since 2026-10-27]`. ✔
`reconcile: 0 flagged, 0 resolved-by-merge, 24 editions checked`. 🟢

### J. Cross-week trend
See the section below.

### K. Feed reachability and direct-fetch rate
Direct-fetch ratios are 1.0 on every stream, with 0 via-snippet in the computed footers. 🟢 (The ratio treats proxy fetches as direct, which is correct, so it no longer separates curl from proxy. The per-feed table does.)

**Feeds failing >50%.** The raw ratio counts the curl-first miss before every proxy success, so 47 feeds trip it. The ones with **no or little net success** are the real list:
- `openai.com` 18/2 (§E). Worse than last week's 11/2.
- `science.org` 8/1, `journals.aps.org` 1/0, `physics.aps.org` 1/0: the journal wall (§E 3).
- `sec.gov` 4/0 (efts.sec.gov full-text search 0/1 worked, a smart workaround), `tse.jus.br` 4/0, `ukmto.org` 4/0, `api.openalex.org` 3/0 (still called; rm-1 pending), `dsca.mil` 3/0.
- No net success, low volume: about 25 hosts at 1–3/0. They are mostly government and court sites (§E 1), plus three Migros hosts (all 2/0) and the Swiss and US lab newsrooms (EPFL, PSI, CERN, LBL).
- Working through the proxy, despite the high raw ratios: lemonde.fr 21/18, rfi.fr 23/19, dw.com 13/19, bbc.co.uk 12/8, doi.org 14/10, ansa.it 6/6, admin.ch 1/23.

**Method comparison:** curl carries Al Jazeera (12), export.arxiv.org (33), ecb.europa.eu (4) and the SRF/Le Temps feeds. Everything else is proxy. arXiv RSS returned **empty channels for all five categories again on 10-30** (also on 10-20). That makes it two of the last four AI/ML editions, and the writer fell back to the Atom API correctly both times. One more recurrence would justify listing the Atom API first in the preflight plan.

**Reach drift (computed):** there are **23 flips**, all copied into `proposals/registry-2026-11-01.yml`. **18 are CARRIED** from unstamped files. arxiv.org (abstract host; export.arxiv.org stays direct), rfi.fr, lemonde.fr and huggingface.co are in **all five** files from 10-04 to 11-01. The five new flips are mlcommons.org, ukrinform.net, agmai.org, insee.fr and rik.parlament.gov.rs. Every entry has ≥3 proxy successes, 0 curl successes and non-transient failures, so there are no judgment overrides. **One judgment addition:** openai.com `direct → blocked`. It is not a computed flip because 2 proxy successes is below `min_proxy`, but two weeks of 0 curl and ≥85% overall failure justify it. With `reach: blocked`, the writers would cite the RSS summary with `[via snippet]` instead of retrying a dead page and then dropping the story. The reverse case (curl now succeeding on a `proxy` domain) does not occur.

**Domains that shouldn't be cited:** there are 0 citations of `reach: blocked`/`blocked-paywall` domains without `[via snippet]`. `never:` is empty, and no `reduce:` domain appears this week. The WSJ report mentioned in the 10-29 Gaps was left out rather than cited, which is correct. 🟢

### L. Output volume
- **news**: 1917 words vs 1626 (+18%), with citations rising from 61 to 69 (+13%). That is below the 25% flag line and roughly tracks content, with the growth mostly in longer leads (Spain crash, Israel). No flag, but it is the one stream trending up.
- **science**: 3248 vs 3028 (+7%), with stories from 14 to 16. calls_mean is 75, down from 177. The dead-host retries that drove it last week (APS, Duke, UCSC, OpenAlex) have mostly stopped. 🟢
- **sports**: 1333 vs 1258 (+6%), stories from 7 to 8. **ai-ml**: 2662 vs 3010 (−12%). **weekend**: 6564 vs 7701 (−15%), calls 117 (127).
No stream is both long and repetitive.

### M. Editorial shape
- **Vendor-PR-lead share (AI/ML):** 8 of 11 non-paper items are vendor-sourced (OpenAI ×3, Cohere, Kimi, Gemini 4 Carbon, Anthropic study, Mistral). The independent items are the S-1 via EDGAR, MLCommons Candela and the DOJ/Hugging Face report. Every vendor item is tagged and attributed. **Vendor framing as the lead happens in 2 of 11 (~18%).** "Kimi K3.1 Pro scores near the frontier" and "Gemini 4 Carbon tops cyber benchmarks" put the vendor's own benchmark claim in the headline, though both bodies attribute it ("Moonshot's own Terminal-Bench figure", "Google says it is first") and add Artificial Analysis or Ars Technica as a check. Green, improved from amber. One observation to watch rather than flag: **two of the week's three AI importance-3 slots went to unverified vendor announcements** (Gemini 4 Carbon on 10-30, and OpenAI's claimed proofs in the Weekend). The ETH claim's stakes justify the lead, and the skepticism is on the page. If vendor launches keep taking the AI lead slot, that is the vendor-PR-lead failure showing up through `importance` instead of headlines.
- **Aggregator shape (5 leads: news 10-26, 10-29 and 10-30; ai-ml 10-30; sports 10-26):** 0 failures. Lula and Vučić (10-26) are anchored on the electoral commissions where reachable (rik.parlament.gov.rs) and wire reports where not, with the gap named. The Spain crash timeline rests on El País's reconstruction of the minister's briefing and audio it obtained, plus La Moncloa. The Switzerland–China FTA uses the Federal Council communiqué. Gemini 4 Carbon is first-party plus Ars. Sports anchors on SRF Sport. Each adds framing the source does not contain (the Swiss-market angle, the pre-election context in Spain, "you can't use it").
- **Personalization (5 stories):** 0 misses. Migros names the Vaud head-office exposure. Lagarde's exit is tied to the franc and SNB policy. INSEE frames France as a main trading partner. Swiss parts in Russian weapons names u-blox (Thalwil) and STMicro (Plan-les-Ouates). The 80 km/h motorway contingency (10-28) is pure CH. Israel and Western Sahara correctly carry no forced Swiss angle.

### N. Affiliation element
- **Coverage:** about 6 of 40 unique papers read "(affiliation not listed)", around 15%. 🟢 The 10-27 AI/ML is the outlier at 5 of 7. Its Gaps line explains why: arXiv HTML returned 404 for three papers, and RSI Arena's HTML lists no affiliations. That is disclosed, not skipped. Science 10-28 is 0 of 16. Byline-to-record checks: E. Xin "(Independent Researcher)" → `["Independent Researcher"]` ✔. **Last week's Zanolini defect did not recur.** Meta's looping paper → `["Meta AI", "MIT"]` ✔, and Cohere's speculative-decoding paper → `["Cohere"]` ✔.
- **Halo audit:** the not-listed and independent papers scored 2, 2, 2, 1 and 1, and the independent CoT-reliance paper scored 2. Meta AI/MIT, Cohere, CMU/A*STAR and UIUC/Argonne papers scored 1. There is no prestige gradient. 🟢

## Prior proposals status
- `proposals/registry-2026-10-04.yml`, `-10-11.yml`, `-10-18.yml` and `-10-25.yml`: **pending, not applied** (all unstamped). arxiv.org, lemonde.fr, rfi.fr and huggingface.co are still `reach: direct` in `sources/registry.yml`. The last stamped registry file is `registry-2026-09-27.yml`.
- `proposals/reader-model-2026-10-18.json` rm-1 (drop the OpenAlex lookup from `routines/_shared/affiliations.md`): **pending, not applied**. The OpenAlex bullet is still at lines 16–17, and the writers still call it (3/0 this week). Not re-proposed.
- `proposals/reader-model-2026-10-25.json`: no proposals, so there is nothing to verify.
- Last week's six scout candidates (ox.ac.uk, helmholtz.de, ucl.ac.uk, imperial.ac.uk, nih.gov, pasteur.fr) reached the registry as `status: candidate` **with `reach: direct`** (`proxy-needed` was dropped) and `last_cited: 2026-10-25` (the scout date; none was cited). This confirms the sync defect (Open question 2).
- `sources/registry.yml` line 1017 still breaks strict YAML (`yaml.scanner.ScannerError: mapping values are not allowed here, line 1017, column 19`), for the fourth week.

## Source scout (Sunday duty)
- **Stream picked: sports.** Its new-domain ratio is the lowest (3/3 = 1.0× target), against science 5/3 = 1.67×, ai-ml 27/10 = 2.7×, news 4.6× and weekend 11.3×. It is also the worst stream on unique domains (4).
- **Candidates:** 8 sports primaries not in the registry were probed: nationalleague.ch (Swiss ice hockey's top league), bscyb.ch and fcb.ch (club newsrooms), spenglercup.ch (the Davos tournament), bundesliga.com, laliga.com, skysports.com and velonews.com. **All 8 returned `000`/ERR:56**, the egress wall and not a verdict on the sites. Six league, club and event primaries were appended to `sources/candidates.jsonl` with `reach: proxy-needed`: nationalleague.ch, bscyb.ch, fcb.ch, spenglercup.ch, bundesliga.com and laliga.com. Sky Sports and VeloNews are outlets and were held back. **Candid assessment:** sports already has about 25 untried candidates in preflight, so six more will not move the metric by themselves. The binding constraint is that the writer reaches for SRF/BBC/Autosport and does not try the bench. A sports-specific quota tweak may be warranted if next week is flat (Open question 4).
- **Re-probes** of the next 5 stalest `reach:` entries (bootstrap-only, 2026-07-07, continuing alphabetically after last week's block): businesswire.com, cbsnews.com, ccianet.org, cloud.google.com and cnbc.com. **cloud.google.com returned 200 by direct curl, which confirms `reach: direct`.** The other four returned ERR:56 from this egress, which is inconclusive, and none is in writer telemetry this week. No flips were recorded.
- **Fetches used: 13 of 20** (8 candidates + 5 re-probes). The 8 claim-check fetches in §C (plus two keyword re-reads of the same pages) are counted separately.

## Patch proposals (for human review)

**No new prompt patches this week.** The issues found sit in four places, and a prompt patch fixes none of them:
- **The builder:** the `_split_inline_why` ordering, and the parenthesised trailing run (Open question 3).
- **The registry apply step:** 23 flips plus the openai.com judgment flip.
- **Tooling:** the sync reach default, and the YAML colon.
- **Egress:** the government, journal and OpenAI walls.

The one tempting prompt patch is to tell the News writer to put "Why it matters" inline. I rejected it: `routines/src/news.md:46` asks for a "line", the continuation form is legal markdown, and changing the writer to suit a parser bug is the wrong direction. The openai.com drop on 10-30 contradicts an instruction that already exists (`routines/src/ai-ml.md:34`, fall back to snippets with `[via snippet]`). The registry flip makes that path explicit without new prompt text. rm-1 (OpenAlex) is still pending and is not re-proposed.

## Reader-feedback → profile proposals
**No reader feedback this week.** There are zero `ev:"feedback"` events with `ts` in 2026-10-26..11-01. `health.json` agrees: `feedback.by_stream` is empty and `unconsumed_total` is 0. Nothing is deferred, nothing is auto-applied to `reader-profile.md`, and there is no source-weights proposal. Reader brief-proposals: no `proposals/*.jsonl` reader records exist, so there is nothing to surface.

## Machine-readable proposals
- `proposals/registry-2026-11-01.yml`: 23 reach flips (18 CARRIED), 1 judgment flip (openai.com → blocked) and 6 scout candidate adds, all `applied: false`.
- `proposals/reader-model-2026-11-01.json`: no new proposals. The `note` records the zero-feedback window and that rm-1 (10-18) is still pending.

## Cross-week trend
| Metric | 10-04 | 10-11 | 10-18 | 10-25 | 11-01 |
|---|---|---|---|---|---|
| news top-5 share | 0.695 | 0.691 | 0.685 | 0.662 | **0.653** ↓ (better) |
| ai-ml top-5 share | 0.544 | 0.618 | 0.571 | 0.547 | 0.548 → |
| news unique 30d | — | — | 47 | 52 | **58** ↑ |
| ai-ml unique 30d | — | 29 | 31 | 34 | 33 → |
| science unique 30d | 5 | 4 | 4 | 4 | **7** ↑ |
| sports unique 30d | — | — | 9 | 6 | **4** ↓ (worst) |
| weekend waiver rate | 1.00 | 0.80 | 0.60 | 0.60 | 0.60 → |
| T1 citation % | — | 33% | 39% | 42% | **35%** ↓ |
| aggregator citations | 0 | 0 | 0 | 0 | 0 |
| T3 leakage | 0 | 0 | 0 | 0 | 0 |
| empty sections | 0 | 0 | 0 | 0 | 0 |
| surface WARNs | — | — | 1 | 1 | **6** ↑ |
| via-snippet (portfolio) | 0 | 1 | 0 | 2 | 1 |
| reach-drift flips | 13 | 24 | 29 | 21 | 23 (18 carried) |
| link sample | 5/20 unmeas. | 6/20 unmeas. | 4/20 unmeas. | 5/20 unmeas. | 3/20 unmeas. |
| openai.com fail/ok | — | — | — | 11/2 | **18/2** |

Editorial quality is steady-good, and the claim checks were clean for the first time in three weeks. News diversity keeps improving, and science finally moved. Four lines are getting worse: sports diversity (third week down), the reading surface (a builder defect, not a writer one), T1 share (compositional), and the registry backlog (fifth week unapplied).

## Open questions for human review
1. **Apply the reach flips, or grant the evaluator a bounded auto-apply for computed `briefs.reach_drift` flips.** Five registry files are now pending (10-04 to 11-01), and four domains are in every one of them. The flips are deterministic writer telemetry. This is the fourth week the question has been asked. Without either step, the drift section is a list that grows by about five domains a week.
2. **Registry sync drops the candidate's reach (unfixed, confirmed again).** `tools/sources/registry.py:455` writes `"reach": "direct"` for every new candidate (and `:406` does the same on the other path). It also writes `"last_cited": rec.get("first_seen")` even for scout entries that were never cited. Evidence this week: all six 10-25 scout candidates landed `direct`, and four of the five new drift flips are this week's writer-tagged domains first reached through the proxy. Proposed fix: map the record's `reach` when present (`proxy-needed` → `proxy`), and set `last_cited` only when `via != "scout"`. Run `python3 -m unittest discover -s tools/tests` after the change.
3. **Builder: two parser shapes, now 6 WARNs.** (a) `_split_inline_why` (build_stories_feed.py:346) meta-tests the whole paragraph before splitting. When "Why it matters:" follows the citation run on a continuation line (News 10-29/10-30), the citations are mid-paragraph and read as a byline. Split first, then meta-test the head. Golden cases: st-fb7d688d5a1f, st-9fa21cc3d182. (b) `strip_trailing_citations` does not peel a parenthesised trailing run with a nested byline: `([arXiv:…](u) · Authors (affiliation not listed))` on 10-24, and `([arXiv:…](u) · NVIDIA · tags)` on 10-31. Balance parentheses when peeling. Golden cases: st-5745ce974a94, st-c71b778862b5. Verify with `tools/verify/build.sh` and `suite.mjs` before it reaches main.
4. **Sports diversity: decide the lever.** Sports went 9 → 6 → 4 unique domains in 30 days, with SRF, BBC and Autosport all saturated, while preflight shows about 25 untried candidates. The options: (a) arm the report-only per-outlet cap for sports, so a third SRF/BBC story forces a bench try; (b) raise the sports discovery quota from ≥1 to ≥2; or (c) accept that weekly sports with official sites behind JavaScript will sit around 5. I lean to (a), because it uses machinery that already exists. If you pick (b), I'll draft the patch against `routines/src/sports.md` next week.
5. **openai.com → `blocked` (judgment flip in this week's registry file).** If you'd rather keep it `direct`/`proxy`, consider a one-line clarification in the AI/ML stream body that a first-party post reachable only by RSS summary should run `[via snippet]` with a secondary, not be dropped. The 10-30 drop of OpenAI's misalignment-detection post is exactly the reader's beat.
6. **bbc.co.uk is unregistered** but is the sports stream's second-most-cited host and is counted as saturated. Registering it (`class: outlet`, `tier: T2`, `reach: proxy`, given 0 curl / 8 proxy this week) would make its cap and tier accounting honest.
7. **Test suite in this sandbox:** 820 tests, the same 3 failures (ledger and fold permission tests that cannot fail when running as root) and 2 skipped. This is an environment artefact, unchanged. `assemble.py check` is OK on all five generated prompts.
8. **`sources/registry.yml` line 1017** still has the unquoted colon (`note: sports: https://…`), which breaks strict YAML parsers. Quoting it is a one-character fix, raised for the fourth week.
