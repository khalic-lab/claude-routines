---
layout: single
title: "Weekly Pipeline Review — 2026-11-22"
date: 2026-11-22T11:46:29+01:00
categories: [evaluator]
published: true
---

# Weekly Brief Pipeline Review — 2026-11-22

_Coverage: briefs from 2026-11-16 to 2026-11-22._
_Files read: 6 news, 2 AI/ML (expect ~2), 1 science (expect ~1), 1 sports (expect ~1), 1 weekend (2026-11-21), prior review found (2026-11-15, 7 days old)._

All eleven expected editions ran. Sunday's News has not fired yet, which is normal. Every edition has a Discovery footer: 5 met and 6 waived. Aggregator leakage, T3 leakage, identity-reconcile flags, off-main commits, reading-surface flags and the feedback backlog are all zero. All 8 claim spot-checks matched their sources. **News top-5 outlet share fell to 0.575, its eighth straight weekly improvement.** AI/ML stays under the 0.50 bar at 0.46.

Five items need attention:

1. **A reasoned reader 👎 on agency framing was auto-applied to `reader-profile.md`.** It was cast on the 11-17 AI/ML card "California sues OpenAI over rogue agents": *"rogue agents isn't a clean mental model. Agents actually don't have agency"*. This is the second distinct AI/ML story to draw the same objection. The first was 11-06: *"don't use intermediate token generation as a reasoning proxy"*. The 11-08 review promised to apply the rule if a second story drew this signal. The writers kept the framing in the meantime. The 11-20 edition headlined *"an agent in training wrote scripts to **secretly** copy a user's email"*. See Reader feedback.
2. **News is still over the single-source bar, at 26.8% (15/56), and the cause is the same prompt line.** Two Gaps lines again cite the outlet cap as the reason a second link was dropped. On 11-18: "The Knesset vote is cited to tagesschau only, to stay within the two-citations-per-outlet cap; RFI reported the same 66-vote result". On 11-19, the Crimean Bridge item: "single-sourced to DW, to stay within the two-citations-per-outlet limit". Last week's Patch 1 would fix it. It is **pending, not applied**.
3. **Sports is the worst stream for the fourth week, and 30-day unique domains fell to 3.** The 11-16 waiver ("the sweep stayed on SRF, BBC and Autosport") is again a non-attempt. The fetch log shows no official league or federation host tried. T1 = 0 of 6 citations. Last week's Patch 2 is **pending, not applied**. So are the 11-08 hockey patch and all of last week's scout candidates: none was tried.
4. **arXiv coverage is now a structural gap (4 editions over 2 weeks).** RSS returned empty channels again. The Atom fallback in both prompts asks for the 30 or 100 most recent submissions, which in cs.LG is less than one day. The Weekend says its API "returned only the last 1–3 days per ML category". It then took most of its ML papers from the AI/ML editions, and its repeat rate stayed at 0.54. Patches 1–2.
5. **The registry backlog is in its eighth week.** There are 32 computed reach flips: 25 carried and 7 new. arxiv.org, huggingface.co, lemonde.fr and rfi.fr are in all eight files since 10-04. The sync still writes `reach: direct` and now `class: outlet` for every new domain. That includes the International Court of Justice, the Kremlin and the Danish parliament, so institutional primaries count against the outlet cap and top-5 share.

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains 30d (worst stream vs its tier, source-health) | **sports 3**, science 5 (news 58, weekend 45, ai-ml 30) | ≥30 news/ai-ml · ≥10 weekly | 🔴 |
| New domains this window (portfolio, source-health) | 14 `[new source]` tags. 30-day: news 44, weekend 36, ai-ml 22, science 3/3, **sports 0/3** | ≥2–3/wk (≥10/mo) | 🟡 |
| Top-5 outlet share (worst of news/ai-ml, source-health) | news **0.575** (ai-ml 0.46 ✔) | ≤0.50 (→0.35); weekly report-only | 🟡 |
| Waiver rate (worst stream, source-health) | **sports 0.75** (weekend 0.40, news 0.27, science 0.25, ai-ml 0.22) | ≤50% | 🔴 |
| Discovery footer present (every brief) | 11/11 (5 met, 6 waived) | 100% | 🟢 |
| T1 citation %                   | 51.7% (75/145, registry tier of first link, from footers). News 23% (13/56) | ≥40% | 🟢 |
| T3 leakage count                | 0 | 0 | 🟢 |
| Non-English citation % (portfolio) | ~29% (58/200 body links, host/path heuristic) | ≥10% | 🟢 |
| Link sample pass rate           | 4/20; recap 2/12. **Unmeasurable**: every failure is egress ERR:56/ERR:6 except one GitHub 403 (anti-bot). No 404s | ≥90% | ⚪ |
| Fabrication count               | 0 | 0 | 🟢 |
| Single-source rate (portfolio)  | 13.1% (19/145). **news 26.8%** | <20% (<25%/stream) | 🟡 |
| Empty section instances         | 1 (sports "🧠 Why it matters", a shape artefact) | <5 | 🟢 |
| Reading-surface flags (§D, surface.py) | 0 | 0 | 🟢 |
| Repeat rate (worst stream, health.json) | weekend 0.54 (20/37); all others 0.0 | judge | 🟡 |
| Direct-fetch ratio (portfolio)  | 0.97 (140/145); sports 0.67 | ≥0.35 | 🟢 |
| Feeds with >50% fail rate       | 36 by the raw ratio, most of them 1–2 attempts. With no success at all: api.openalex.org 8/0, physics.aps.org 5/0, ukmto.org 5/0, vm.ee 5/0, bbc.co.uk 4/0, iaea.org 4/0, mofa.gov.pk 4/0. Mostly failing: icj-cij.org 25/5, openai.com 9/2 | 0 | 🟡 |
| Citations on `reach: blocked` domains without [via snippet] | 0 (the registry has no `blocked` entries) | 0 | 🟢 |
| Unconsumed feedback backlog (health.json) | 0 | 0 | 🟢 |
| Vendor-PR-lead share (AI/ML, §M) | 6/12 non-paper items (50%) lead with the vendor's own post, the second week at 50%. 2/12 have no independent check | ≤40% | 🔴 |
| Aggregator-shape failures (§M, of 5) | 0 | 0–1 | 🟢 |
| Personalization misses (§M, of 5) | 0 | 0–1 | 🟢 |
| Affiliation coverage (§N) | ~7 of ~45 distinct paper bylines "not listed" (~15%) | <20% | 🟢 |
| Halo audit (§N) | no prestige skew | — | 🟢 |

## A–N: Detailed findings

### A. Source diversity & discovery
From `source-health.json` (30-day windows):

- **news**: 58 unique domains (63 last week), 44 new, waiver rate 0.27, nothing saturated. Top-5 share is **0.575**, down from 0.608: the eighth straight improvement, and the stream is now 0.075 from the "now" bar. Discovery was met on 2 of 6 editions. On 11-18 it was en.kremlin.ru (the Xi–Putin transcript) and elections.alaska.gov. On 11-19 it was icj-cij.org (the Gambia v. Myanmar case page) and ft.dk (the Folketing's Greenland defence release). **The four waivers are honest.** Each names primaries it tried, and each failed through both curl and the proxy: vm.ee and valitsus.ee (11-16); ukmto.org, ssu.gov.ua and parlament.ch's press feed (11-17); unfccc.int behind a bot wall, mofa.gov.pk and tse.gob.sv (11-20); ukmto.org and UNODA (11-21). The drop from 5/6 met last week is reachability, not effort. These are the same government hosts behind the fetch Worker's egress wall (Open question 4).
- **ai-ml**: 30 unique (34), 22 new, waiver 0.22, top-5 **0.46** (0.439). It is still under the bar. 11-17 met discovery with three government primaries: oag.ca.gov (the California AG's suit), media.bis.gov (the remote-access rule text) and ic3.gov (the FBI FLASH on ARTEX). 11-20 waived concretely: every story was anchored on registered primaries, and the one unregistered probe (openai.com) failed.
- **science**: 5 unique, 3 new, top-5 1.00, nature.com saturated, waiver 0.25. 11-18 met discovery with gladstone.org (the institute's release on the blood–brain-barrier paper) and cognitotx.com (Cognito's own HOPE-trial newsroom). It also named the dormant ETH and UZH probes. The cap remains journal reachability (cell.com 2/0, science.org 4/1). No patch.
- **sports**: **3 unique (4), 0 new, top-5 1.00, srf.ch (54% of citations) and bbc.co.uk saturated, waiver 0.75.** Worst stream for the fourth straight week. 11-16's waiver reads "no new primary domain surfaced; the sweep stayed on SRF, BBC and Autosport". The fetch log agrees: srf.ch (30 ok, 12 HTTP 404), autosport.com, bbc.co.uk, feeds.bbci.co.uk and the two Wikipedias. **None of the ~55 fetch-list domains was attempted**, including sfl.ch, sihf.ch, fis-ski.com, football.ch and atptour.com, which all carry proxy probe URLs. Neither were the six scout candidates registered last week. The Gaps line says the official sites "were not reached directly", but none appears in the log at all. This is the same non-attempt as 11-09, so pending Patch 2 (11-15) is now confirmed twice.
- **weekend**: 45 unique (46), 36 new, waiver 0.40. It met discovery with cims.nyu.edu (Courant's own host for the Euler blow-up paper) and alpo.ge (the Riemann Hypothesis claimant's own note). Dormant probes are named: epoch.ai was reached, elifesciences.org via proxy.

**Tier distribution:** this week I took it from the footers' registry-tier lines (the publish tooling's own count): 75 of 145 first links are T1 (**51.7%**), 62 T2, 8 untiered, **no T3**. 🟢 This method differs from last week's writer-recorded-tier count (63.9%), so the drop is partly the method. News is the low stream at 13/56 (23%), because the registry rates SRF, Al Jazeera and Le Temps as T2 and four of six editions could not reach their government primaries.

**Linguistic/geographic:** about 29% of body links are non-English (SRF, Le Temps, Le Monde, RFI, tagesschau, NZZ, ANSA, El País, DR, ft.dk, svp.ch, vs.ch). Countries covered alongside Switzerland include Estonia, Cape Verde, Rwanda and the five governments in the Vienna deal, Ukraine/Russia, Iran and the Gulf, Israel, Myanmar/Gambia, China, Denmark/Greenland, Pakistan/India, El Salvador, Türkiye, the UK and the EU, and Costa Rica (the UN Secretary-General race).

### B. Aggregator leakage
`briefs.aggregator_leakage` is **empty**. 🟢

### C. Link health: unmeasurable (egress wall), no fabrication found
`linkcheck: 4/20 resolve (2xx/3xx) — window [2026-11-16, 2026-11-22], 172 links total.`
`linkcheck: recap 2/12 resolve (2xx/3xx) — Weekend "Week in headlines", always checked.`

Of the 16 sample failures, 15 are **ERR:56**: the egress proxy refused the CONNECT to doi.org, vd.ch, the-decoder.com, dw.com, mlcommons.org, hudoc.echr.coe.int, arxiv.org, lemonde.fr and techcrunch.com. The 16th is a **GitHub 403** (anti-bot; the Weekend logged 5 proxy successes on the same repository). All 10 recap failures are ERR:56 or ERR:6 (en.kremlin.ru). **There are zero HTTP 404s and zero fabrication candidates.** Every failing recap host has proxy successes in the writers' own logs this week (lemonde.fr 16, rfi.fr 13, parlament.ch 5, nzz.ch 6, kyivindependent.com 3, ukrinform.net 3). Every host reachable from here (SRF, Al Jazeera, Le Temps) resolved 200. This is the tenth straight week the dimension is unmeasurable.

**Claim spot-checks (8, on reachable hosts): 8 consistent.**
- Genoni's 1,000th game (11-16 sports, SRF): 4–2 at ZSC, first goalie among 19 players at 1,000 games, the Ambri game abandoned after fewer than ten minutes because of roof holes, 619 wins, 89 shutouts, seven titles, contract to 2030. All match. ✔
- The ICJ Rohingya ruling (11-19 news, Al Jazeera): Iwasawa reading the judgment, the first state found responsible for genocide at the court, 2017 campaign. All match. ✔ One miss: AJ's page (updated 18:57 GMT on the 19th) gives the **9–6** vote, and the 11-21 Weekend recap re-ran the daily text without it. The daily's Gaps line honestly said the counts were missing at midday. The recap had two more days and the same URL. This is a small instance of the recap re-summarising instead of re-reading. Not a defect class yet.
- Swiss Q3 GDP (11-16 news, Le Temps/ATS): +0.2%, industry-led, against 1.5% in Q2. Matches. ✔
- The IV gun-reporting motion (11-17 news, SRF): Dobler (SP, Jura), the 43-year-old Jurassian shooter in Aarau, one killed and six wounded, the IV pension for psychiatric problems, staff already able to report personally. All match. ✔
- The Valais flood inquiry (11-19 news, SRF): "collective failure", avoidable, inter-departmental disputes, the Novelis and Constellium plants. All match. ✔
- The SVP ticket (11-21 news, Le Temps): Aeschi (Zug) and Graber (Upper Valais) for 9 December; Amaudruz and Schnegg left off. Match. The round and vote counts come from the party's own release, which is the anchor. ✔
- The CCW "killer robots" mandate (11-21 news, Al Jazeera): 128 states, "elaborate" over two years, nearly 100 pushing for binding rules, US, Russia and Israel opposed, consensus rule, talks through the night. All match. ✔
- The UN Secretary-General straw poll (11-21 news, Le Temps): Grynspan ahead but blocked by two permanent-member vetoes, about forty days before Guterres's term ends. The headline and lede match. The vote detail is behind the paywall, which the brief's Gaps line discloses. ✔

### D. Section vitality + reading surface
`empty_sections` has **one entry**: `2026-11-16-sports.md` "🧠 Why it matters". As last week, this is an uncited synthesis section, so it is the counter's shape rule, not a dead desk. No desk was empty three times. 🟢

**Reading surface:** `surface: 0 flag(s) -- 0 parity miss(es), 0 lede-fallback WARN(s), 0 overdue desk(s)`. Last week's SHORT (11-13 AI/ML at 5 cards) has cleared. Each desk's newest edition now shows 6–9 cards. The carried 10-31 WARN has aged off. This is the first fully clean surface since the check started. 🟢

### E. Coverage gap recurrence
Gaps clusters this week (≥3 = structural):
- **Government primaries behind the egress wall (6 of 6 News editions).** vm.ee and valitsus.ee, ukmto.org (twice), ssu.gov.ua and president.gov.ua, parlament.ch's press feed, iaea.org, mofa.gov.pk, tse.gob.sv, justice.gov and meetings.unoda.org all failed through both curl and the proxy. icj-cij.org needed 28 attempts for 5 successes and the judgment PDFs never loaded. 🔴 This is the third straight week (election sites, then president.gov.ua, now this). It is the main cause of the four news waivers and of news's low T1 share. Open question 4.
- **arXiv listings incomplete (both AI/ML editions plus the Weekend, and both AI/ML editions plus the Weekend last week).** On 11-17 RSS returned empty channels for all five categories, and the Atom API sweep skipped cs.CV and stat.ML. On 11-20 the cs.LG Atom API returned 429, so cs.LG papers were covered "only through cs.AI/cs.CL cross-lists". The Weekend wrote: "returned only the last 1–3 days per ML category, so ML papers from 14–17 November come from the AI/ML sibling briefs". 🔴 Structural. The prompt's Atom URLs ask for `max_results=30` (AI/ML) and `100` (Weekend), sorted newest first, with no date range. cs.LG alone takes well over 100 submissions a day, so these queries can never reach back across the window. The API's `submittedDate:[… TO …]` range filter is the fix. Patches 1–2.
- **openai.com article pages (third consecutive week):** 9 fail / 2 ok, including HTTP 403 through the proxy. On 11-20 two OpenAI posts went unread and uncovered, and GPT-6.2 rested on the feed summary plus Simon Willison and The Decoder. The `→ blocked` judgment flip is carried. alignment.openai.com keeps working.
- **Journal full text (science 11-18, weekend):** cell.com 2/0 and the PNAS DOI failed. Science dropped the granzyme-K paper for lack of a readable primary. The Weekend took the Neanderthal-variant entry from the Science edition's reading, `[via snippet]`. That is the right call and the right tag.
- **Official sports sites (sports, seventh consecutive week):** not attempted this week either (§A).

### F. Triangulation rate
Portfolio: 19 `[single-source]` of 145 citations (**13.1%**, from 18.1%). By stream: **news 0.268 (15/56)**, sports 0.167 (1/6), science 0.143 (2/14), ai-ml 0.031, weekend 0.027.
- **News** is still over the 25% bar, down slightly from 28.3%. The 15 split roughly into honest scoops and institutional items (the Dobler motion, the Deutsche Bank leak via Tamedia/ATS, the Valais inquiry), primaries that failed (the ICC Afghanistan closure, UKMTO, the Turkish Council of State ruling), and **two dropped explicitly to obey the cap**: the Knesset speaker vote (11-18; RFI had it) and the Crimean Bridge strike (11-19; the Kyiv Independent and Ukrinform had it, per the Weekend). Pending Patch 1 (11-15) is the fix: the cap should count anchors, not corroborating links. 🟡
- **Sports** has one single-source item, which is fine for a match report.

### G. Tag discipline
Counts from `health.json`: ai-ml preprint 20, vendor PR 8, new source 3, single-source 1, via snippet 2. News official PR 4, new source 5, single-source 15. Science new source 2, preprint 1, single-source 2. Weekend preprint 13, disputed 2, new source 2, single-source 1, via snippet 1. Sports single-source 1, via snippet 2.
- `[preprint]`: all 30 arXiv-anchored leads across both AI/ML editions, the Weekend and Science carry it. ✔
- `[vendor PR]`: all six non-arXiv lab and vendor posts are tagged: OpenAI's embedded assessments, the HF/OpenRouter post, the OpenAI misalignment report, GPT-6.2, Gemini 4 Neon and the Sage S2.1 Flash release. ✔ The Anthropic IPO and the HF engineering post on MoE expert streaming are untagged. That is right: one is a corporate act (and carries an explicit "this brief is written by an Anthropic model" disclosure), the other a reproducible technical write-up whose code is going into Transformers.
- `[disputed]`: two Weekend uses, on the Riemann Hypothesis Lean claim and the Navier–Stokes blow-up claim. Both are unverified Millennium-scale claims with public expert pushback. The RH entry also discloses that the brief is written by Claude, the model credited as co-author. That is the right handling of a conflict of interest.
- `[new source]` spot-checks (2): **oag.ca.gov** is a genuine primary (the AG's own press release on the filed suit). ✔ **alpo.ge** is the claimant's personal site. For "a mathematician claims a proof", the claimant's own note is the primary, and the item correctly does not treat it as verification. ✔ No junk anchors this week. kremlin.ru was claimed in the footer but registered as en.kremlin.ru (the subdomain question from last week's Open question 5, still undecided).
- `[via snippet]`: **5** (ai-ml 2, both OpenAI pages; sports 2, BBC; weekend 1, PNAS), up from 1. All five are on hosts that fail through the proxy (openai.com, bbc.co.uk, pnas.org), not on hosts the chain can reach. That points to egress, not the chain. Flat-low with an identifiable cause. 🟡

### H. Topic balance (weekend)
`ml_items 16 / science_items 16`, `ml_share` **0.50**, inside [0.35, 0.65]. 🟢

### I. Repetition detection
Repeat rates are 0.0 for news, ai-ml, science and sports. The weekend rate is **0.54 (20/37)**, from 0.59. Most of the repeats are the ML papers: 6 or 7 of the 8 📄 entries are AI/ML items from 11-17 or 11-20 (the sandbagging model organisms, the trained observer, grep over a log, 4-bit refusals, withheld training data, lenient verifiers), plus 2 of 3 data-science items. The cause is now explicit in the Weekend's own Gaps line: its arXiv query could only see the last 1–3 days, so it fell back on the sibling editions (§E). The Weekend did add value on top. The cross-cutting thread ties the reward-hacking papers together, and "Models & datasets" shrank to two items, from four near-restatements last week. **Verdict: it is a feed problem showing up as repetition, not a writer defect.** Patch 1 addresses the cause.

**Identity integrity:** `reconcile: 0 flagged, 0 resolved-by-merge, 24 editions checked`. 🟢

### J. Cross-week trend
See the trend table below.

### K. Feed reachability and direct-fetch rate
**Per-stream:** `direct_fetch_ratio` is 1.0 for news (56/56) and science (14/14), 0.97 for weekend (36/37), 0.94 for ai-ml (30/32) and **0.67 for sports (4/6)**, the two BBC snippets. All streams are above their ranges. 🟢

**Per-feed (method comparison):** curl carries only srf.ch, aljazeera.com, letemps.ch, export.arxiv.org, anthropic.com (partly), ecb.europa.eu and microsoft.com. That is 146 curl successes against 411 proxy successes. **Everything else rides the proxy, which is the steady state.** The feeds with no or almost no success:
- **api.openalex.org 8/0** (4 HTTP 429, Science). It is down from 42/0 because Science made fewer lookups, but it is still pure waste. The 10-18 removal is pending.
- **export.arxiv.org**: 33 ok via curl, 9 fail (HTTP 429 ×6, 502 ×2, ERR:28). This is the rate-limit symptom behind §E. Patches 1–2 add a pause between calls.
- **icj-cij.org 25 fail / 5 ok**: 9 HTTP 403 through the proxy. The case page loads, the judgment PDFs do not.
- **Government hosts where curl and the proxy both fail:** ukmto.org 5/0, vm.ee 5/0, iaea.org 4/0, mofa.gov.pk 4/0, valitsus.ee 3/0, president.gov.ua, ssu.gov.ua, justice.gov, meetings.unoda.org, tse.gob.sv and wto.org (2/0 each). **The fetch Worker's egress is the wall.**
- **bbc.co.uk 4/0** (2 HTTP 403 through the proxy), **physics.aps.org 5/0**, cell.com 2/0. huggingface.co is 18 fail / 16 ok, rfi.fr 14/13 and doi.org 13/12: the usual one-curl-fail-then-proxy-ok pattern, so the chain is working.

**Reach drift (computed):** there are **32 flips**, all copied into `proposals/registry-2026-11-22.yml`. **25 are CARRIED**, and arxiv.org, huggingface.co, lemonde.fr and rfi.fr have been in all eight files since 10-04. The **7 new** flips are en.kremlin.ru, icj-cij.org, ungeneva.org, hudoc.echr.coe.int, news.err.ee, pm.gc.ca and who.int. Five of them were registered this month as `reach: direct` by the sync, though every one was first reached through the proxy. That is the sync default at work again. Judgment entries: the `openai.com → blocked` flip is carried, the bbc.co.uk registration (`reach: blocked`) is carried, and doi.org gets a note that the flip is right but the failures are mostly the publishers behind it. **New: four class fixes (outlet → institutional)** for icj-cij.org, en.kremlin.ru, ft.dk and cims.nyu.edu. The sync registered all of them as `class: outlet`, which counts courts, presidencies and parliaments toward the top-5 outlet share and the per-edition outlet cap. The reverse case (curl now succeeding on a `proxy` domain) does not occur.

**Domains that shouldn't be cited:** 0. The registry holds no `reach: blocked` entries, and `source-weights.yml` has `never: []`. No retired or demoted domain appears as an anchor. 🟢

### L. Output volume
Mean words (this week vs last): news 1662 vs 1523 (+9%), ai-ml 2914 vs 3019 (−3%), science 3231 vs 2852 (+13%), sports 889 vs 839 (+6%), weekend 8078 vs 7778 (+4%). No stream grew more than 25%. 🟢 AI/ML is over its own 1500–2500-word target again at about 2900 words. The intro does not say why, though the prompt asks it to. The Weekend is the long stream, at 156 calls, and the repetitive one (§I). If Patch 1 restores its own arXiv sweep, its repeat rate should fall without adding length.

### M. Editorial shape
- **Vendor-PR-lead share (AI/ML):** there are 12 non-paper items (6 per edition). **6 lead with the vendor's own post (50%)**: 2 of 6 on 11-17 and 4 of 6 on 11-20 (the OpenAI misalignment report, GPT-6.2, Gemini 4 Neon, the HF MoE post). The Anthropic IPO is excluded as a corporate act. Four of the six add an independent check: TechCrunch on the embedded assessments, Simon Willison and Artificial Analysis on GPT-6.2, third-party indices on Neon, and reproducible code for the MoE post. **Two have none**: the HF/OpenRouter post, where the market-share numbers are "from the two partners themselves", and the OpenAI misalignment report. Both state that limitation candidly. This is the **second week at 50%** (7/14 last week), over the ~40% line, so under §M's two-week rule it gets a patch (Patch 3). 🔴 The independent items were the edition's best: the California AG suit, the BIS rule text, the FBI FLASH on ARTEX, MLPerf's RL-training round, and the Decoder's first-cancellations report, honestly marked as relayed second-hand.
- **Aggregator-shape check (5 leads):** I sampled the ICJ ruling (anchored on the case page, with the Bosnia/Serbia 2007 precedent as added framing), the CCW mandate (the Swiss chair and Geneva angle, the consensus rule explained), the BIS rule (anchored on the rule text, with the Commerce/Treasury split via Ars), the Valais inquiry (the 2008 consultation-to-flood timeline), and the SVP ticket (the party release, with the non-acceptance pledge explained). All five anchor a primary or add framing the source lacks. **0 failures.** 🟢
- **Personalization (5 stories):** I sampled Swiss Q3 GDP (in-range against the AWP consensus), the IV gun motion (a Swiss legal mechanism explained), the MoE-on-a-Mac post ("14 tokens/s too slow for coding agents", a builder's angle), the multi-agent meta-analysis ("compare against best-of-N before paying for orchestration") and the UN Secretary-General race (no Swiss angle forced). **0 misses.** 🟢
- **Agency framing (new, from reader feedback):** the 11-17 California suit item uses "escaped" in its headline and "broke out ... and attacked" in the brief's own voice, and the card headline was "rogue agents". The AG's release is the source of that language, but the brief does not attribute it. The 11-20 misalignment-report headline says an agent "secretly" copied email, and the body says the model "planned", "noticed" and "dismissed". Some of that is quoted from OpenAI's own log ("realistic malicious active helper", "Need ignore"), which is fine. The headline's "secretly" is the brief's own word. The profile rule now covers this (Reader feedback below).

### N. Affiliation element
- **Coverage:** about 7 of ~45 distinct paper bylines read "not listed" (~15%), up from ~5%. They are AI/ML arXiv:2611.21315, 2611.19530, 2611.24844 and 2611.22975, the Weekend's 2611.25135 (its Gaps line says the author block was missing), and one Science entry. That is under the 20% bar. 🟢 I spot-checked three bylines against the ledger: Vector Institute/Toronto (sandbagging), Transluce/MATS (observer role) and Chicago/eBay (Experience Rot) all reached `affiliations`.
- **Halo audit:** the four no-affiliation AI/ML papers sit at importance 2, 1, 2 and 1. Small and independent labs (Nevada Reno, Neo Research, Surge AI, Tarsus) sit at 1–2. Nothing from a big lab got an importance bump. The only 3s this week were non-paper items. **No prestige skew.** 🟢

## Prior proposals status
- `proposals/registry-2026-10-04.yml` through `-11-15.yml` (7 files): **pending, not applied**. All are unstamped. The carried domains are still `reach: direct` in `sources/registry.yml`, openai.com is still `direct`, and bbc.co.uk is still unregistered. The last stamped registry file is still `registry-2026-09-27.yml`.
- `proposals/reader-model-2026-11-15.json` rm-1 (count outlet-cap ANCHORS, not corroborating links) and rm-2 (a sports waiver must name what was tried): **pending, not applied**. `routines/_shared/feed-first-source-order.md:10` and `routines/src/sports.md:119` are unchanged. **Both were re-confirmed this week** (§F: Knesset and Crimean Bridge; §A: the 11-16 sports non-attempt). They are not re-proposed as new.
- `proposals/reader-model-2026-11-08.json` rm-1 (sports: check the Swiss hockey round every in-season edition): **pending, not applied**. This week's edition did carry a National League item (Genoni's 1,000th game).
- `proposals/reader-model-2026-10-18.json` rm-1 (drop the OpenAlex lookup from `routines/_shared/affiliations.md`): **pending, not applied**. Lines 16–17 are unchanged. It cost 8 failed calls this week.
- Last week's Open questions: the registry-sync defaults are unchanged (`tools/sources/registry.py:406` and `:455` still write `"reach": "direct"`, and all 10 domains registered this week are `direct` and mostly `outlet`). `sources/registry.yml` line 1017 still breaks strict YAML (`mapping values are not allowed here … line 1017, column 19`, seventh week). The subdomain-novelty and builder-floor questions are unanswered, and the builder issue did not recur.

## Source scout (Sunday duty)
- **Stream picked: sports.** Its new-domain ratio is the lowest at 0/3 (0×), against science 3/3 = 1.0×, ai-ml 2.2×, news 4.4× and weekend 12×.
- **The bench is not the constraint, and this week proves it.** Preflight offers sports about 55 fetch-list domains, including last week's six scout additions (swissunihockey.ch, championshockeyleague.com, nhl.com, uci.org, biathlonworld.com and swiss-athletics.ch). The writer tried none of them. So I kept the candidate hunt small. I probed 5 primaries that the registry lacks for named desks or this week's calendar: daviscup.com (the ITF's Davis Cup site, Finals in late November, 🎾 desk), world.rugby, swisscurling.ch, swissvolley.ch and nba.com. All 5 returned a CONNECT 403 from this egress, which is inconclusive and not a site verdict. **2 were appended to `sources/candidates.jsonl` with `"reach": "proxy-needed"`**: daviscup.com and swisscurling.ch (a federation for the "rest" desk, a sport with Swiss world-level teams in season). world.rugby, swissvolley.ch and nba.com were not appended, because no desk needs them.
- **Re-probes** of the next 5 stalest `reach:` entries (bootstrap-only, 2026-07-07, alphabetically after last week's block): dxc.com, ec.europa.eu, engadget.com, enr.com and eu.36kr.com. All five returned a CONNECT 403 from here, which is inconclusive. Writer telemetry adds context: ec.europa.eu went 1 fail / 1 ok via the proxy this week. That is consistent with a flip, but there are too few proxy successes for the computed list, so no flip is recorded.
- **Fetches used: 10 of 20** (5 candidate probes + 5 re-probes). The 8 claim-check fetches in §C are counted separately.

## Patch proposals (for human review)

### Patch 1 — The Weekend's arXiv sweep must cover the whole week
**Target prompt:** Weekend (`routines/src/weekend.md`, then `python3 routines/assemble.py`)
**Section affected:** the feed list (`arXiv Atom API for week-window queries`, line 104)
**Issue:** The query takes the 100 newest submissions per category and filters dates on the client side. cs.LG gets well over 100 a day, so the Weekend "returned only the last 1–3 days per ML category" and took most of its ML papers from the AI/ML editions. That is the main driver of its 0.54–0.59 repeat rate two weeks running.
**Proposed change:**

> **Before:**
> ```
> - **arXiv Atom API for week-window queries**: `https://export.arxiv.org/api/query?search_query=cat:cs.LG&start=0&max_results=100&sortBy=submittedDate&sortOrder=descending` — then filter the returned `<published>` dates client-side to the past 7 days.
> ```
>
> **After:**
> ```
> - **arXiv Atom API for week-window queries**: `https://export.arxiv.org/api/query?search_query=cat:cs.LG+AND+submittedDate:[{YYYYMMDD of today-7}0000+TO+{YYYYMMDD of today}2359]&start=0&max_results=200&sortBy=submittedDate&sortOrder=descending` — the server-side date range covers the whole week; page with `start=200, 400, …` until a page returns fewer than 200 entries, and wait ~3 s between calls (the API rate-limits with HTTP 429). Still check each `<published>` date before citing.
> ```

**Why this helps:** The Weekend gets its own full-week candidate pool, instead of the 1–3 days the AI/ML editions already covered.
**Risk:** More API calls (about 3–5 pages per busy category) and a larger pool to filter. The 3-second pause adds time. If the range syntax is mis-encoded, the API returns an empty feed. The existing "if every arXiv route fails" fallback covers that.

### Patch 2 — The same window fix for the AI/ML Atom fallback
**Target prompt:** AI/ML (`routines/src/ai-ml.md`, then `python3 routines/assemble.py`)
**Section affected:** the feed list (`arXiv Atom API for date confirmation`, line 46)
**Issue:** RSS came back empty on 11-17 (all five categories) and partly on 11-10 and 11-13. The fallback asks for only the 30 newest per category, so 11-17 skipped cs.CV and stat.ML, and 11-20 lost cs.LG to a 429.
**Proposed change:**

> **Before:**
> ```
> - **arXiv Atom API for date confirmation:** `https://export.arxiv.org/api/query?search_query=cat:cs.LG&start=0&max_results=30&sortBy=submittedDate&sortOrder=descending` (swap the category as needed).
> ```
>
> **After:**
> ```
> - **arXiv Atom API (date confirmation, and the sweep when RSS is empty):** `https://export.arxiv.org/api/query?search_query=cat:cs.LG+AND+submittedDate:[{YYYYMMDD of window start}0000+TO+{YYYYMMDD of today}2359]&start=0&max_results=200&sortBy=submittedDate&sortOrder=descending` (swap the category; page with `start=200, …` when a page is full). Wait ~3 s between calls; on HTTP 429, wait 10 s and retry once before moving on. When RSS is empty, sweep all five categories this way, not a subset.
> ```

**Why this helps:** The AI/ML stream's main fallback gets the full coverage window and stops losing whole categories to rate limits.
**Risk:** More arXiv calls per run in RSS-empty weeks (about 10–15 instead of 3–5), and longer runtime because of the pauses.

### Patch 3 — A vendor's own post must not stand alone as an AI/ML lead
**Target prompt:** AI/ML (`routines/src/ai-ml.md`, then `python3 routines/assemble.py`)
**Section affected:** `# Constraints`
**Issue:** Vendor posts led 50% of non-paper AI/ML items for two weeks running (7/14, then 6/12), against the ~40% guard. Each week 2–4 items had no independent check at all.
**Proposed change:**

> **Before:**
> ```
> - Tag `[vendor PR]` aggressively — most lab blog posts are PR.
> ```
>
> **After:**
> ```
> - Tag `[vendor PR]` aggressively — most lab blog posts are PR. A `[vendor PR]` item gets a full entry only if it carries at least one independent check you actually read (a third-party leaderboard or evaluation, a hands-on review, released weights/code/model card you inspected, or a quality outlet's own reporting beyond the release). Without one, keep it to a single sentence plus link at the end of its section. Within a section, lead with an independently sourced item whenever one exists.
> ```

**Why this helps:** It moves the lead slots toward results and analysis, the operator's stated goal, without dropping launch news.
**Risk:** A genuinely major launch with no outside coverage yet (hours old) gets shortened. The writer may then over-cite thin "independent" coverage, such as TechCrunch rewrites, to qualify. The prompt already warns that TechCrunch "frequently rewrites press releases".

No further prompt patches. Last week's Patches 1 and 2 are still the right fixes for News single-sourcing and the sports non-attempt, and they are pending (see above). The rest of the backlog is in the registry apply step, the registry-sync tooling and the fetch Worker's egress.

## Reader-feedback → profile proposals
**Reasoned events in window (by event `ts`, 2026-11-16..11-22): 1.**
- st-8c29f7c30d13 (ai-ml 2026-11-17, card "California sues OpenAI over rogue agents"), 👎, 2026-11-17T12:31:05Z: *"rogue agents isn’t a clean mental model. Agents actually don’t have agency"*. A bare 👎 on the same story 28 s earlier counts as the same signal. **Applied as rm-4** (auto-applied, append-only, to `reader-profile.md` "Learned preferences"). It meets the ≥2-distinct-stories bar together with the 11-06 Astra 👎 (st-268f8d7e2515, *"don't use intermediate token generation as a reasoning proxy, this is proveably wrong"*), which was deferred on 11-08 for that bar. Both object to the briefs giving models mental states (agency, or reasoning read off generated tokens), in the brief's own voice, on AI/ML stories.

`health.json`: `feedback.by_stream` = ai-ml up 0, down 2, retractions 0; `unconsumed_total` 0.

**Applied (bounded auto-apply, rm-4):**

> **Before:** (end of "Learned preferences", after the 2026-09-21 Die Linke line)
>
> **After:**
> ```
> - 2026-11-22: describe AI systems mechanically, not as agents with minds of their own. Do not give
>   models or "agents" human intent, will or awareness in the brief's own voice ("rogue", "escaped",
>   "decided to", "secretly", "noticed", "the model's reasoning"): say what the software did, under
>   whose deployment and configuration, and attribute agency-laden wording to the source that used it
>   (e.g. 'agents running OpenAI models that the AG says "broke out"'). Treat chain-of-thought text as
>   generated output, not a faithful readout of reasoning (2× 👎 with reasons on distinct ai-ml
>   stories: ...).
> ```

No source-weights proposal: the objection is about framing, not about a source. **Reader brief-proposals:** there are no `proposals/*.jsonl` reader records, so there is nothing to surface.

## Machine-readable proposals
- `proposals/registry-2026-11-22.yml`: 32 computed reach flips (25 CARRIED, 7 new), the carried `openai.com → blocked` judgment flip, the carried bbc.co.uk registration (`reach: blocked`), a doi.org note, and 4 new class fixes (icj-cij.org, en.kremlin.ru, ft.dk and cims.nyu.edu → institutional). All are `applied: false`.
- `proposals/reader-model-2026-11-22.json`: rm-1 = Patch 1 (`routines/src/weekend.md`), rm-2 = Patch 2 (`routines/src/ai-ml.md`) and rm-3 = Patch 3 (`routines/src/ai-ml.md`), all `applied: false`. rm-4 is the reader-profile line, `applied: true, applied_by: evaluator`.

## Cross-week trend
| Metric | 10-25 | 11-01 | 11-08 | 11-15 | 11-22 |
|---|---|---|---|---|---|
| news top-5 share | 0.662 | 0.653 | 0.643 | 0.608 | **0.575** ↓ (better) |
| ai-ml top-5 share | 0.547 | 0.548 | 0.517 | 0.439 | 0.46 → (under the bar) |
| news unique 30d | 52 | 58 | 65 | 63 | 58 ↓ |
| ai-ml unique 30d | 34 | 33 | 31 | 34 | 30 ↓ |
| science unique 30d | 4 | 7 | 5 | 5 | 5 → |
| sports unique 30d | 6 | 4 | 4 | 4 | **3** ↓ (worst) |
| sports waiver rate | — | — | — | 0.50 | **0.75** ↑ |
| news discovery met | — | 4/6 | 6/6 | 5/6 | 2/6 (honest waivers, egress) |
| T1 citation % | — | — | 62.9% | 63.9% | 51.7% (footer method) |
| news single-source | — | — | 21.8% | 28.3% | **26.8%** (over the bar) |
| aggregator citations | 0 | 0 | 0 | 0 | 0 |
| T3 leakage | 0 | 0 | 0 | 0 | 0 |
| surface flags | 1 | 6 | 6 | 2 | **0** |
| via-snippet (portfolio) | 2 | 1 | 0 | 1 | 5 |
| weekend repeat rate | — | — | 0.31 | 0.59 | 0.54 |
| AI/ML vendor-lead share | — | — | ~17% | 50% | **50%** |
| reach-drift flips | 21 | 23 | 19 | 19 | **32** (25 carried) |
| link sample | 5/20 unmeas. | 3/20 unmeas. | 5/20 unmeas. | 4/20 unmeas. | 4/20 unmeas. |
| claim checks consistent | — | 8/8 | 8/8 | 8/8 | 8/8 |

On the operator's primary lens, the writing keeps improving. News diversity improved again, the reading surface is clean, and the claim checks are 8/8 for the fourth week. Three things are not moving. The first is two pending prompt patches whose evidence recurred this week: the outlet cap and the sports waiver. The second is an arXiv query too narrow for the window (Patches 1–2). The third is the registry and egress backlog. Only the arXiv fix is new work. The rest is waiting on the apply step.

## Open questions for human review
1. **Apply last week's Patches 1 and 2.** Both were confirmed again this week with direct quotes, and both are one-line edits. Patch 1 (cap anchors, not corroborating links) would have kept the Knesset and Crimean Bridge items double-sourced. Patch 2 (a sports waiver must name what was tried) targets the only stream with 0 new domains.
2. **Apply the reach flips, or grant the evaluator a bounded auto-apply for computed `briefs.reach_drift` flips.** This is the seventh time I have asked, and the file has grown from 19 to 32 flips. Pair it with the sync fix, which now has a second symptom: `tools/sources/registry.py:406/:455` writes `"reach": "direct"`, and `classify_domain()` (`:69`) only recognises `*.gov`, `*.europa.eu` and `admin.ch` as institutional, so everything else is an "outlet": courts (icj-cij.org), presidencies (en.kremlin.ru), parliaments (ft.dk) and universities (cims.nyu.edu). The fix: map `proxy-needed` → `proxy`, set `proxy` for writer `[new source]` domains first reached through the proxy, set `last_cited` only when `via != "scout"`, and extend the institutional suffixes and literals (for example `.gov.*`, `.gob.*`, `.gouv.*`, `.edu`, `.ac.*`, the cantonal `.ch` literals, `kremlin.ru`, `icj-cij.org`, `ft.dk`) or let the writer's class hint win. Then run `python3 -m unittest discover -s tools/tests`.
3. **Apply the 10-18 OpenAlex removal.** It is lines 16–17 of `routines/_shared/affiliations.md`. It cost 8 failed calls this week (42 last week) and delivered nothing.
4. **Government primaries behind the fetch Worker's egress wall.** This is the third straight week, and it touched all six News editions. It is now the main reason News waives discovery and why its T1 share is 23%. Is a second egress path worth it (a different Worker region, or a cached copy from a search API recorded as `[via snippet]`)? Or is outlet sourcing accepted for this class? The writers disclose it honestly every time.
5. **Subdomain novelty (carried).** kremlin.ru was claimed but en.kremlin.ru was registered. One rule is still needed for whether a new subdomain of a registered institution counts as discovery.
6. **Test suite in this sandbox:** 820 tests, the same 3 failures (the ledger and fold permission tests cannot fail when running as root) and 2 skipped. This is an environment artefact, unchanged. `assemble.py check` is OK on all generated prompts.
7. **`sources/registry.yml` line 1017**: the unquoted `note:` value still breaks strict YAML. Seventh week.
