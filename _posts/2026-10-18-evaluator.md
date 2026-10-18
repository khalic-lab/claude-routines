---
layout: single
title: "Weekly Pipeline Review — 2026-10-18"
date: 2026-10-18T11:50:08+02:00
categories: [evaluator]
published: true
---

# Weekly Brief Pipeline Review — 2026-10-18

_Coverage: briefs from 2026-10-12 to 2026-10-18._
_Files read: 6 news, 2 AI/ML (expect ~2), 1 science (expect ~1), 1 sports (expect ~1), 1 weekend, prior review found (2026-10-11, 7 days old)._

This was a clean week for the briefs themselves. All six expected News editions ran (Sunday's has not fired yet, which is normal). Every edition carries a Discovery footer. Aggregator leakage, T3 leakage and identity-reconcile flags are all zero. No section went empty, and all eight claim spot-checks matched their sources. Each edition has exactly one importance-3 story. The halo concern from last week has also gone away: the one unaffiliated paper this week (Athanor) was rated importance 2 on Friday and was the Weekend's single importance-3 lead.

Three things need attention, and none of them is in the writing:

1. **The reach-flip backlog keeps growing.** The computed drift list has **29 domains** this week. 15 of them were already proposed in the still-unstamped 10-04 or 10-11 files. Six have now recurred for three straight weeks: arxiv.org, huggingface.co, rfi.fr, lemonde.fr, simonwillison.net and parlament.ch. Neither prior registry file has been applied.
2. **OpenAlex has been dead for four weeks** (26 fail / 0 ok this week). It is not in the registry: the shared affiliations partial tells every papers writer to call it. That makes it a prompt patch, not a registry flip, and it is this week's only patch (Patch 1).
3. **Science is still the worst stream on source diversity**: 4 unique domains in 30 days against a target of ≥10. This week's edition cited eleven different institutions, but almost all of its anchor URLs sit on nature.com, doi.org or arxiv.org. The metric counts publisher hosts, not institutions. See Open question 2.

There was no reasoned reader feedback this week, so there are no profile proposals.

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains 30d (worst stream vs its tier) | science 4 (ai-ml 31, news 47) | ≥30 news/ai-ml · ≥10 weekly | 🔴 |
| New domains this window (portfolio) | 18 `[new source]` tags this week; science 2/3 per 30d, every other stream at or above its tier | ≥2–3/wk (≥10/mo) | 🟡 |
| Top-5 outlet share (worst of news/ai-ml) | news 0.685 (ai-ml 0.571) | ≤0.50 (→0.35); weekly report-only | 🔴 |
| Waiver rate (worst stream) | science 0.75 (weekend 0.60, sports 0.50) | ≤50% | 🔴 |
| Discovery footer present (every brief) | 11/11 | 100% | 🟢 |
| T1 citation %                   | 39% (77/198; 9 unregistered) | ≥40% | 🟡 |
| T3 leakage count                | 0 | 0 | 🟢 |
| Non-English citation % (portfolio) | ~30% (60/198) | ≥10% | 🟢 |
| Link sample pass rate           | 4/20; recap 7/10. **Unmeasurable**: all 18 non-2xx results are egress ERR:56 or one GitHub 403, no 404s | ≥90% | ⚪ |
| Fabrication count               | 0 | 0 | 🟢 |
| Single-source rate (portfolio)  | 15.4% (17/110) | <20% | 🟢 |
| Empty section instances         | 0 | <5 | 🟢 |
| Reading-surface flags (§D, surface.py) | 1 (stale WARN on the 10-03 weekend; nothing in window) | 0 | 🟢 |
| Repeat rate (worst stream)      | weekend 0.389 (by construction); all other streams ≤0.031 | judge | 🟢 |
| Direct-fetch ratio (portfolio)  | 1.0 (0 via-snippet) | ≥0.35 | 🟢 |
| Feeds with >50% fail rate       | 4 high-volume with no net success (openalex 26/0, kyivindependent 4/0, president.gov.ua 4/0, consilium 13/2), plus a low tail | 0 | 🟡 |
| Citations on `reach: blocked` domains w/o `[via snippet]` | 0 | 0 | 🟢 |
| Unconsumed feedback backlog     | 0 | 0 | 🟢 |
| Vendor-PR-lead share (AI/ML, §M) | 10/16 non-paper items vendor-sourced, all tagged; vendor framing as the lead ~2/16 | ≤40% | 🟡 |
| Aggregator-shape failures (§M, of 5) | 0 | 0–1 | 🟢 |
| Personalization misses (§M, of 5) | 0 | 0–1 | 🟢 |
| Affiliation coverage (§N) | 2 of ~35 unique papers "not listed" (~6%) | <20% | 🟢 |
| Halo audit (§N) | no prestige skew; the unaffiliated paper got the Weekend's single importance 3 | — | 🟢 |

## A–N: Detailed findings

### A. Source diversity & discovery
From `source-health.json` (30-day windows):

- **news**: 47 unique domains, 34 new, top-5 share 0.685, waiver rate 0.414, nothing saturated. Five of six editions met discovery, and every tagged primary was first-party: volitve.dvk-rs.si (Slovenia's election commission), efk.admin.ch (the Swiss Federal Audit Office's own pesticide audit), imf.org, vaticannews.va (the Holy See Press Office's medical statement), home.treasury.gov, enav.it (Italy's air-traffic-control provider), sotomo.ch (the institute behind the SRG Wahlbarometer) and gov.br (INPE's PRODES data). The 10-15 waiver is honest and specific: three first-party primaries were attempted and all failed (bger.ch was blocked by Incapsula, rna.ro failed, and the FOEN study page was not found). **Top-5 share is flat for a third week** (0.695 → 0.691 → 0.685). As last week, I'm not re-patching rotation. Only SRF (42 curl hits), Al Jazeera (23) and Le Temps (22) curl reliably, and everything else goes through the proxy.
- **ai-ml**: 31 unique, which crosses the ≥30 bar for the first time. 25 new, waiver rate 0.222. Top-5 share improved from 0.618 to 0.571. Both editions met discovery: research.meta.ai, machinelearning.apple.com, blogs.nvidia.com and swarmcha.se, an independent research group and a genuine primary for its own Tencent-agent-fleet finding.
- **science**: 4 unique, 2 new, top-5 1.00, waiver rate 0.75. This is the worst stream for the fifth consecutive review. The 10-14 waiver is honest: it anchored one new primary (iob.ch, the Basel Institute of Molecular and Clinical Ophthalmology), probed ptb.de and dana-farber.org, and saw PSI, EPFL, UNIGE, Empa, UNIBE and WSL all fail to fetch. **The editorial reality is more diverse than the metric.** The edition's twelve papers come from TU Wien/PTB, USTC, Berkeley, Dalian, IOB, Columbia/HHMI, Weizmann, Dana-Farber, UCL/CNRS, Cornell/JPL, INAF and NYU. But each is anchored on its journal's host, so `unique_domains` sees four. Prompt patches cannot fix this. Either the reachability wall falls, or the metric counts what science actually diversifies on (Open question 2).
- **sports**: 9 unique, 5 new, top-5 0.818 (report-only), and bbc.co.uk is saturated for a **third** week. The waiver ("iihf.com, ita.sport, diamondleague.com had no relevant item this week") is honest but thin. The edition ran 5 stories and 810 words (−29% week-over-week).
- **weekend**: 34 unique, 28 new, waiver rate 0.60, which is better again (1.00 → 0.80 → 0.60). It met discovery with bipm.org (the CGPM leap-second resolution) and iucn.org (the coral Red List). Both are genuine intergovernmental primaries.

**Tier distribution:** of 198 body citations, 77 are T1 (39%), 112 T2 and 9 unregistered (ukrinform.net 4, bbc.co.uk 2, pravda.com.ua, iob.ch, watson.ch). That is up from 33% last week and one point short of green. There is **no T3**.

**Linguistic/geographic:** about 30% of citations are non-English (SRF, Le Temps, RFI, Le Monde, RTS, ANSA, El País, watson, Le Nouvelliste, Sotomo, gov.br, Ukrainska Pravda, BTA, the Slovenian DVK). News covered Saudi Arabia/Yemen, Ukraine/Russia, Sudan, DR Congo, Slovenia, Bulgaria, Turkey, Romania, Pakistan, North Korea, Brazil, Ethiopia and Albania alongside Switzerland.

### B. Aggregator leakage
`briefs.aggregator_leakage` is **empty**. 🟢 The AI/ML edition's Nadella item quotes an X post, but it carries no x.com link: the story is anchored on secondary press coverage, and the Gaps line says "Nadella's X post was not fetched directly". That is the correct handling.

### C. Link health: unmeasurable (egress wall), no fabrication found
`linkcheck: 4/20 resolve (2xx/3xx) — window [2026-10-12, 2026-10-18], 177 links total.`
`linkcheck: recap 7/10 resolve (2xx/3xx) — Weekend "Week in headlines", always checked.`

Of the 16 sample failures, 15 are **ERR:56** (the egress proxy rejected the CONNECT). The 16th is an HTTP 403 from github.com on the llama.cpp release tag, which is GitHub's anti-bot response to an unauthenticated curl, not a missing page. The three recap failures (DW, vaticannews.va and an admin.ch release) are all ERR:56. **There were zero 404s and zero fabrication candidates.** The dimension is unmeasurable for the fifth straight week. Every host that resolved is on the direct allowlist (Al Jazeera, SRF, Le Temps, anthropic.com).

**Claim spot-checks (8, all on reachable hosts), 8/8 consistent:**
- North Korea submarine-launched cruise missiles (10-15 news, Al Jazeera): the Pulhwasal-3-31 type, "war deterrent" and the 8,700-tonne submarine all match. ✔
- ECHR admissibility of the Vaud tax-liability complaint (10-12 news, Le Temps): Mahaim, "petite victoire", the ~10% admissibility rate and the Appenzell parallel all match. ✔
- Anthropic's "unintended model actions" report (10-13 ai-ml): SQL/command injection, URL-shortening services used to get around fetch limits, the White House briefing and the false police tip all match. ✔
- Anthropic and METR access (10-16 ai-ml): "six METR employees with company hardware, office space, and access to internal tools", plus SecureBio and Accenture in lower tiers, matches. ✔
- Graham Act waiver (10-17 news; weekend recap via Al Jazeera): "national interest", the 100% tariffs, Dmitriev and Blumenthal all match. ✔
- SRG Wahlbarometer (10-17 news, SRF): SRF says "knapp 30 Prozent" for the SVP, while the brief gives 29.9 (the Sotomo figure). SP 19.3 (+1), Mitte −1.5, FDP −1 and the 27% "about right" figure all match. ✔
- Leewas poll (10-14 news; weekend, Le Temps): VAT 60–36, War Material Act 47 no, fireworks 68 in detail vs 65 in the summary (the brief flags this discrepancy itself), and the 1.6-point margin all match. ✔
- Leap-second item (weekend, SRF): the 2022 decision to abolish it "by 2035 at the latest" matches. The CGPM resolution details come from bipm.org, which this egress cannot reach. ✔ for the SRF half.

### D. Section vitality + reading surface
There are no empty sections in any stream. The 10-13 AI/ML edition omitted its open-weights section, and its Gaps line says why: the two candidates were uploaded before the last edition. That is honest omit-don't-fill, not a vitality failure.

`surface: 1 flag(s) -- 0 parity miss(es), 1 lede-fallback WARN(s), 0 overdue desk(s)`
- `FLAG WARN _posts/2026-10-03-weekend.md story st-5b5761c99f32: no body parsed, card shows its lede`. This is the same stale WARN as the last two weeks, on an edition outside the window. It is not new, but it is now three weeks old. Open question 4.
- Last week's science SHORT flag has cleared: the 10-14 science edition shows 9 cards for 12 stories, above the floor. Weekend 36/36, AI/ML 17/17 and News 9/9 on the newest editions all kept every story.

### E. Coverage gap recurrence
Recurring gaps (≥3 occurrences = structural):
1. **EU institution primaries** (consilium.europa.eu in 10-13, 10-15 and 10-16 news: 13 fail / 2 ok). The record sanctions package, the European Council summit and Kallas's quotes all rest on DW, RFI and SRF. This is new to the recurring list and now the largest primary-source hole in News.
2. **Ukrainian official primaries** (president.gov.ua 4/0 and kyivindependent.com 4/0 in 10-12 and 10-14 news). Zelensky is quoted via Axios/DW, Al Jazeera and Ukrinform. With Ukraine the lead four days running, this matters.
3. **Swiss federal-court and official-statistics primaries unreachable** (bger.ch blocked by Incapsula in 10-15; bafu.admin.ch study not found; the Leewas own release not fetched in 10-14 and the weekend). These stories rest on SRF, Le Temps and ATS, which are wire-grade but secondary.
4. **Official sports pages are JavaScript shells** (10-12 sports: FIA, WTA, Premier League), for a third week. This is a renderer limit, so no source addition fixes it.

openai.com (last week's top gap) dropped off: 1 fail and 1 proxy success in each AI/ML edition.

### F. Triangulation rate
Single-source rates: news 0.19 (11/58), ai-ml 0.094, science 0.0, sports **0.40** (2/5), weekend 0.028. The portfolio rate is 15.4%. 🟢 Sports is over the 25% per-stream ceiling, but on a 5-story edition. The two single-source items (the City verdict via BBC Sport only, and one SRF-only Super League item) are both disclosed in Gaps. I'm noting it rather than patching: it is one week and one edition.

### G. Tag discipline
These counts come from health.json. ai-ml: 16 `[preprint]`, 10 `[vendor PR]`, 2 `[new source]`. Weekend: 12 `[preprint]`, 3 `[vendor PR]`. News: 12 `[new source]`, 4 `[official PR]`. There are no `[disputed]` uses this week.
- `[preprint]`: all arXiv research items sampled (5, across 10-13 and 10-16) carry it. ✔
- `[vendor PR]`: Nemotron 3.5, FLUX.3 Klein, LFM2.5, Gemini 4 Argon and Muse Spark Open are all tagged. ✔ METR access is a lab announcement about external oversight. It is anchored on anthropic.com and correctly attributed ("Anthropic says it cannot veto them").
- `[disputed]`: no uses. Nothing this week called for one. The Houthi death tolls (four vs two) were handled by giving both figures with their sources, which is fine.
- `[new source]`: spot-checked two of the week's tagged domains. **enav.it**: Italy's air-navigation service provider, publishing its own outage notices, so a genuine primary. **sotomo.ch**: the research institute that runs the poll it is cited for, also genuine. No junk anchors. `sources/candidates.jsonl` held no lines before today's scout additions: tagged domains are entering the registry directly as `status: candidate`.
- `[via snippet]`: 0 uses all week, flat-low, which is healthy.

### H. Topic balance (weekend)
There are 16 ML papers and 16 science papers, so `ml_share` is **0.50**, on target for a third straight week. 🟢

### I. Repetition detection
Repeat rates are news 0.0, science 0.0, sports 0.0, ai-ml 0.031 (1 repeat) and weekend **0.389** (14/36). Weekend is down from 0.625 and by construction: the deep read re-runs the week's arXiv papers with their story ids. A spot-check of the Athanor item (weekend, importance 3) against the 16 Oct AI/ML original shows a genuinely deeper treatment. It explains what post-training is and why handing it to agents matters, and it states openly that the arXiv HTML 404'd and the summary rests on the abstract. That is depth, not re-summary.

News carried Ukraine as the lead four days running (10-14 grid strike, 10-15 refinery-strike pause lifted, 10-16 Trump's "shame" remark plus the EU summit, 10-17 the Graham Act waiver). Each lead has a distinct story id and a new dated fact, and `[ongoing since]` is used where applicable. That is a real running story, not repetition.
`reconcile: 0 flagged, 0 resolved-by-merge, 23 editions checked`. 🟢

### J. Cross-week trend
See the section below.

### K. Feed reachability and direct-fetch rate
The direct-fetch ratio is 1.0 on every stream (computed footers), and via-snippet is 0 portfolio-wide. 🟢

**Feeds failing >50% with no or little net success:**
- `api.openalex.org`: 26 fail / 0 ok (13 ERR:56 direct, 13 HTTP 429 via proxy, all in 10-14 science). **Fourth straight week dead.** It is not a registry domain, so no flip can fix it. The call comes from `routines/_shared/affiliations.md`. That makes it **Patch 1**.
- `consilium.europa.eu`: 13 fail / 2 ok. The proxy gets HTTP 403s, so the EU Council is blocking the proxy's egress itself. See §E.
- `ukrinform.net`: 15 fail / 11 proxy ok. `rfi.fr`: 14/12. `volitve.dvk-rs.si`: 14/12. These are curl-first-then-proxy patterns that do work, and are covered by the reach flips.
- No net success at all: kyivindependent.com 4/0, president.gov.ua 4/0, and a 2/0 tail of actu.epfl.ch, psi.ch, ptb.de, unibe.ch, unige.ch, wsl.ch, empa.ch, home.cern, cell.com, physics.aps.org, mod.go.jp, occ.gov, fincen.gov, smartraveller.gov.au, sudantribune.com, telegraph.co.uk, axios.com, vals.ai and rna.ro. **Six Swiss research institutions** (EPFL, PSI, UNIBE, UNIGE, WSL, Empa) are in that tail. That is the same structural wall behind science's 4-domain count.
- nature.com shows 16 fail / 4 curl / 16 proxy successes, the usual curl-first pattern. It works.

**Method comparison:** curl carries only SRF (42), export.arxiv.org (31), Al Jazeera (23), Le Temps (22), anthropic.com (7), nature.com (7), Quanta (6) and microsoft.com (1). Everything else lives on the proxy. Nothing moved between curl and proxy this week.

**Reach drift (computed):** there are **29 flips**, all copied into `proposals/registry-2026-10-18.yml`. 15 are **CARRIED** from the unstamped 10-04 and 10-11 files. Six appear in all three files: arxiv.org (abstract/HTML host; export.arxiv.org stays direct), huggingface.co, rfi.fr, lemonde.fr, simonwillison.net and parlament.ch. The 14 new ones include doi.org (0/10), volitve.dvk-rs.si (12), bipm.org (6), enav.it (6), home.treasury.gov (5), vaticannews.va (5), physicsworld.com (5) and ethz.ch (3). No judgment overrides: every entry has ≥3 proxy successes and 0 curl successes, and none of the failures look transient. The reverse case (curl now succeeding on a `proxy` domain) does not occur.

**Domains that shouldn't be cited:** there are 0 citations of `reach: blocked`/`blocked-paywall` domains without `[via snippet]`. The FT and The Information are referenced only as "according to…, as summarised by" with no link. No `never:` domains appear. 🟢

### L. Output volume
- **science**: 2993 words vs 2131 (+40%), with stories going from 8 to 12 (+50%). Words per story fell, so no flag. calls_mean is 154, inflated by the 26 dead OpenAlex attempts (Patch 1).
- **weekend**: 7306 vs 6248 (+17%), with stories from 33 to 36. No flag, but it is still the longest brief by a factor of 2.4, and calls_mean is 194.
- **news**: 1625 vs 1562 (+4%). **ai-ml**: 2806 vs 3009 (−7%). **sports**: 810 vs 1146 (−29%) on 5 stories: shorter prose in a quiet week, not a defect.

### M. Editorial shape
- **Vendor-PR-lead share (AI/ML):** 10 of 16 non-paper items are vendor-sourced. That is high, but the Lab-blogs and New-models sections are vendor-sourced by definition, and every one is tagged and attributed ("Nvidia claims", "Liquid reports", "According to TechCrunch's reading of Meta's model card"). Vendor framing as the *lead* happens in about 2 of 16. "Google DeepMind … reports it solved every simulated cyberattack it was tested on" puts the vendor's own safety-eval number in the headline; the attribution is present but the claim is the hook. "Meta releases Muse Wonder, its first frontier model" adopts Meta's "frontier" positioning unqualified. The independent items are well done: the FTC probe, the swarmcha.se agent-fleet investigation, the Anthropic revenue reporting with a clear secondary-sourcing chain, and AlphaProof Nexus via its Science paper. Amber, as last week. It is under the patch threshold because the framing discipline holds.
- **Aggregator shape (5 leads: news 10-12, 10-13, 10-17, ai-ml 10-13, sports 10-12):** 0 failures. Riyadh is anchored on UN News and Al Jazeera citing the civil-aviation authority. The EU sanctions lead uses DW with Kallas on record, and openly notes that the Council's legal acts were unreachable. The Graham Act waiver is anchored on the White House order itself, `[official PR]`. The Anthropic evals report is first-party with outside context (Nadella's response). Sports anchors on BBC Sport and SRF. Each adds a "Why it matters" the source does not contain. The best of the week is the 10-13 lead's note that the listings "are asset freezes and travel bans, … not new sector-wide trade bans".
- **Personalization (5 stories):** 0 misses. The Leewas poll ties the VAT rise to the 13th AHV/AVS payment, and the ECHR item spells out who carries ex-spouses' tax debt in Vaud. The Wahlbarometer gives the method caveat (opt-in, weighted, ±1.2). Muse Spark/MLX has a builder angle ("runs at reading speed on desk hardware, though at a cost of four high-end Macs"). The Riyadh lead correctly carries no forced CH angle.

### N. Affiliation element
- **Coverage:** 2 of about 35 unique papers (23 arXiv plus 12 science journal papers) read "(affiliation not listed)". Both are in 10-16 ai-ml: Athanor (arXiv HTML 404) and the Minecraft paper (author block did not render). Both are disclosed in Gaps. That is about 6%. 🟢 Byline-to-record checks: 10-14 science's nuclear-clock paper → `["TU Wien","BEV","PTB"]` ✔. 10-14 science's IOB optogenetics paper → `["University of Pittsburgh","IOB Basel"]` ✔. 10-13 ai-ml's ETH Zürich paper → `["ETH Zürich"]` ✔. Every journal paper's institutions reached the record even though OpenAlex failed every call. The publisher-page fallback is doing all the work, which supports Patch 1.
- **Halo audit:** this resolves last week's watch item. The unaffiliated Athanor paper was importance 2 in 10-16 ai-ml, above three lab-affiliated papers (MBZUAI, LASR/ELLIS/MPI-IS and Dartmouth, all at 1), and it was the Weekend's single importance 3. The 10-13 importance-2 papers include Contramont Research (a small independent lab) next to Meta Superintelligence Labs. There is no prestige skew. 🟢

## Prior proposals status
- `proposals/registry-2026-10-04.yml`: **pending, not applied** (unstamped). arxiv.org, rfi.fr, lemonde.fr and huggingface.co, among others, are still `reach: direct` in `sources/registry.yml`.
- `proposals/registry-2026-10-11.yml`: **pending, not applied** (unstamped). None of its 24 flips has landed. Its 5 scout candidates (embl.org, news.uzh.ch, ista.ac.at, weizmann.ac.il, riken.jp) were already present in the registry as `status: candidate` through the candidate path. That is not Rafael's apply step, so the file stays unstamped.
- `proposals/reader-model-2026-10-11.json`: had no proposals. Last week's "Super Intelligence Force" note was deferred; no second complaint of that kind arrived this week, so it stays deferred.
- `sources/registry.yml` is unchanged since 10-11 apart from writer-side candidate and `last_cited` bookkeeping in the publish commits.

## Source scout (Sunday duty)
- **Stream picked: science.** Its new-domain ratio is the lowest, at 2/3 = 0.67× its tier target, against sports 5/3, weekend 28/3, ai-ml 25/10 and news 34/10. It also has the worst unique count (4 vs ≥10).
- **Candidates:** 10 research newsrooms were probed. I avoided last week's five, now registry candidates, and anything already registered (snf.ch, unil.ch, cnrs.fr and epfl.ch are present). All 10 returned `000 / ERR:56`, the egress policy wall and not a verdict on the sites. Seven genuine institutional primaries were appended to `sources/candidates.jsonl` with `reach: proxy-needed`:
  - unibas.ch: University of Basel. It closes the last large Swiss-university gap next to ETH, EPFL, UNIGE, UNIBE and UZH, and IOB Basel already anchored this week.
  - presse.inserm.fr (inserm.fr): Inserm press feed.
  - csic.es: Spanish National Research Council.
  - cam.ac.uk: Cambridge research news.
  - fz-juelich.de: Forschungszentrum Jülich.
  - news.mit.edu: MIT News research RSS.
  - caltech.edu: Caltech news.
  - Not appended: iob.ch (the writer already cited it with `[new source]`), ox.ac.uk and helmholtz.de (kept for a future week to keep the bench focused).
- **Re-probes** of the next 5 stalest `reach:` entries (bootstrap-only lifecycle, 2026-07-07; last week's five excluded): arena.ai, artificialanalysis.ai, authorsguild.org, axios.com and benchlm.ai all returned ERR:56 from this egress. That is inconclusive, so no probe-based flips. Writer telemetry independently shows **axios.com failing via proxy too** (1 ERR:56 + 1 HTTP 403 in 10-16 ai-ml), but at 0 proxy successes it does not qualify for a `proxy` flip. It is a `blocked` candidate if it recurs.
- **Fetches used: 15 of 20** (10 candidates + 5 re-probes). The 8 claim checks in §C are counted separately. As every week: the binding constraint is reachability, not candidate supply.

## Patch proposals (for human review)

### Patch 1 — Drop the dead OpenAlex lookup from the affiliations chain
**Target prompt:** shared partial `routines/_shared/affiliations.md` (feeds AI/ML, Science and Weekend; regenerate with `python3 routines/assemble.py`)
**Section affected:** Affiliations, "Published papers (journal DOI)" bullet
**Issue:** `api.openalex.org` has returned 0 successes for four straight weeks. This week it failed 26 times (ERR:56 direct, HTTP 429 via proxy). Every journal paper's affiliations still reached the index, because the writer already falls back to the publisher page. The instruction now costs one dead call per paper and nothing else.
**Proposed change:**

> **Before:**
> ```
> - **Published papers (journal DOI) — OpenAlex:**
>   `https://api.openalex.org/works?filter=doi:<doi>&select=authorships` returns resolved
>   institution names (measured: complete for fresh Nature papers). On a miss, take them from
>   the publisher/press page you are already reading; else the sentinel.
> ```
>
> **After:**
> ```
> - **Published papers (journal DOI) — the page you are already reading:** take the
>   institutions from the publisher page's author/affiliation block, or from the institution's
>   own press release; else the sentinel. (OpenAlex was dropped 2026-10-18: 0 successes in
>   four weeks from the sandbox — ERR:56 direct, HTTP 429 via proxy.)
> ```

**Why this helps:** it removes about 13 wasted fetch pairs per science edition with no loss of coverage. The fallback already produced 100% of this week's journal affiliations.
**Risk:** if OpenAlex becomes reachable again, papers whose publisher page hides affiliations behind JavaScript could fall to the sentinel. That would show up as §N coverage rising above ~20%, so the change is easy to reverse.

No other prompt patches. The remaining findings are owned by the registry (29 reach flips), structural to egress (the EU, Ukrainian and Swiss-institution walls), or one-week events (the thin sports edition).

## Reader-feedback → profile proposals
There were 6 ledger feedback events in the window, matching health.json (news up 3 with 2 retractions, ai-ml up 1). **None has a reason**, so nothing needs an explicit disposition:
- st-5ff205b06c38 (news 10-13, "Kabila takes command of M23-backed front"): 👍, bare.
- st-2ea302ed111c (ai-ml 10-16, "METR gets inside access at Anthropic"): 👍, bare.
- st-f8cf0cbadfea (news 10-17, "Children's-rights network flags child poverty"): 👍 / retract / 👍 / retract within 3 seconds, net retracted. That is one story and a toggle, so it is noise.

No reader feedback clears the bar this week. Nothing is auto-applied to `reader-profile.md`, and there is no source-weights proposal. Reader brief-proposals: no `proposals/*.jsonl` reader records exist, so there is nothing to surface.

## Machine-readable proposals
- `proposals/registry-2026-10-18.yml`: 29 reach flips (15 CARRIED) and 7 scout candidate adds, all `applied: false`.
- `proposals/reader-model-2026-10-18.json`: rm-1 (Patch 1), `applied: false`, with the feedback summary in `note`.

## Cross-week trend
| Metric | 10-04 | 10-11 | 10-18 |
|---|---|---|---|
| news top-5 share | 0.695 | 0.691 | 0.685 (flat) |
| ai-ml top-5 share | 0.544 | 0.618 | 0.571 ↓ (better) |
| ai-ml unique 30d | — | 29 | 31 ✔ crosses target |
| science unique 30d | 5 | 4 | 4 (flat, worst) |
| weekend waiver rate | 1.00 | 0.80 | 0.60 ↓ (better) |
| T1 citation % | — | 33% | 39% ↑ |
| aggregator citations | 0 | 0 | 0 |
| T3 leakage | 0 | 0 | 0 |
| empty sections | 0 | 0 | 0 |
| via-snippet (portfolio) | 0 | 1 | 0 |
| reach-drift flips | 13 | 24 | 29 ↑ (15 carried) |
| link sample | 5/20 unmeas. | 6/20 unmeas. | 4/20 unmeas. |
| openalex fail/ok | dead | 23/0 | 26/0 |

The briefs are holding at good on every editorial dimension, and AI/ML and Weekend are trending better on diversity. The deteriorating lines are the same as last week: unapplied registry bookkeeping, and science's diversity, which is pinned by the egress wall.

## Open questions for human review
1. **Apply the reach flips.** Three files are pending (10-04, 10-11, 10-18), with six domains in all three. Last week's question stands: should computed reach drift be auto-applied by the evaluator, under the same kind of bounded grant as learned-preference lines? It is deterministic writer telemetry, not judgment, and the manual step has not happened in three weeks.
2. **Science's diversity metric.** `source-health.json` counts anchor hosts. Science anchors journal papers on nature.com, doi.org and arxiv.org by policy (the paper is the primary), so it scores 4 domains while citing 11+ institutions per edition. Should science's §A target count `sources/institutions.yml` entries, or the paper-plus-institutional-release pair, instead of hosts? Otherwise it stays red indefinitely whatever the writer does.
3. **consilium.europa.eu** returns 403 to the proxy itself (13 fail / 2 ok). Is there an alternative EU Council source the proxy can reach (EUR-Lex for the legal acts, or the Council's RSS), or should it be marked `blocked`?
4. **Stale surface WARN** on `2026-10-03-weekend.md` st-5b5761c99f32 has been flagged for three weeks. Is it a legal shape the builder's parser misses (a builder defect), or a one-off format slip worth hand-fixing?
5. **Test suite in this sandbox:** 792 tests, the same 3 failures as last week (permission-denied tests that can't fail when running as root). This is an environment artefact, unchanged.
6. **`sources/registry.yml` is still not strict YAML** (the unquoted colon in letemps.ch's `note:`, raised last week). It is unchanged; quoting it is a one-character fix.
