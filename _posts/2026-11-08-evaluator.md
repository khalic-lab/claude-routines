---
layout: single
title: "Weekly Pipeline Review — 2026-11-08"
date: 2026-11-08T11:46:12+01:00
categories: [evaluator]
published: true
---

# Weekly Brief Pipeline Review — 2026-11-08

_Coverage: briefs from 2026-11-02 to 2026-11-08._
_Files read: 6 news, 2 AI/ML (expect ~2), 1 science (expect ~1), 1 sports (expect ~1), 1 weekend (2026-11-07), prior review found (2026-11-01, 7 days old)._

The writing was clean again this week. All six expected News editions ran; Sunday's has not fired yet, which is normal. All 11 editions carry a Discovery footer, and 10 of 11 met discovery with genuine first-party primaries. Aggregator leakage, T3 leakage, empty sections, identity-reconcile flags, off-main commits and the feedback backlog are all zero. All 8 claim spot-checks matched their sources. The homepage tagging is disciplined: every edition has exactly one importance-3 story, and each is a defensible pick. News top-5 outlet share fell to 0.643, its sixth straight improvement.

Four items need attention:

1. **Sports is still the worst stream, and the cause is now visible: Swiss hockey is never checked.** Sports has 4 unique domains in 30 days, 1 new domain against a target of 3, and 3 saturated domains. Swiss National League hockey is a named desk and has been in season since September. It has had **no item in any of the last six editions**. `sihf.ch` is already in the sports fetch list (probation, `reach: proxy`), but no sports edition has ever fetched it. This is the one prompt patch this week (Patch 1).
2. **One reasoned reader 👎, on the AI/ML Astra story:** *"don't use intermediate token generation as a reasoning proxy, this is proveably wrong"*. It is a single story, so it falls below the auto-apply bar and is **deferred**. But the Weekend repeated the same framing the next day, and the rule is general, so I raise it as Open question 1.
3. **The registry backlog is in its sixth week.** There are 19 computed reach flips, 16 of them carried from unstamped files. arxiv.org, lemonde.fr, rfi.fr and huggingface.co are in **all six** files from 10-04 to 11-08. All three new flips (ina.gl, swisstph.ch, nasa.gov) are this week's writer `[new source]` domains that the sync step registered as `reach: direct`. That is the registry-sync defect again, its third straight week of confirmation.
4. **Official election-results sites are a structural gap.** Bulgaria (cik.bg), Israel (bechirot.gov.il), New Zealand (electionresults.govt.nz) and South Africa (elections.org.za) all failed through the proxy. That happened in 4 of 6 News editions, so four election results rested on outlets alone.

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains 30d (worst stream vs its tier) | **sports 4**, science 5 (news 65, weekend 46, ai-ml 31) | ≥30 news/ai-ml · ≥10 weekly | 🔴 |
| New domains this window (portfolio) | 15 `[new source]` tags. 30-day: news 52, weekend 39, ai-ml 25, science 3/3, **sports 1/3** | ≥2–3/wk (≥10/mo) | 🟡 |
| Top-5 outlet share (worst of news/ai-ml) | news 0.643 (ai-ml 0.517) | ≤0.50 (→0.35); weekly report-only | 🔴 |
| Waiver rate (worst stream) | science 0.50, sports 0.50 (weekend 0.40, ai-ml 0.22, news 0.10) | ≤50% | 🟢 |
| Discovery footer present (every brief) | 11/11 (10 met, 1 waived) | 100% | 🟢 |
| T1 citation %                   | 62.9% of story anchors (88/140, from index records; see §A for the method change) | ≥40% | 🟢 |
| T3 leakage count                | 0 | 0 | 🟢 |
| Non-English citation % (portfolio) | ~33% (host/path heuristic) | ≥10% | 🟢 |
| Link sample pass rate           | 5/20; recap 3/8. **Unmeasurable**: every failure is egress ERR:56, with no 404s | ≥90% | ⚪ |
| Fabrication count               | 0 | 0 | 🟢 |
| Single-source rate (portfolio)  | 11.4% (16/140); news 21.8% | <20% (<25%/stream) | 🟢 |
| Empty section instances         | 0 | <5 | 🟢 |
| Reading-surface flags (§D, surface.py) | 6 WARN, **all carried** from editions 10-24..10-31; 0 in this window; 0 parity, 0 overdue | 0 | 🟡 |
| Repeat rate (worst stream)      | weekend 0.31 (by construction); all others 0.0 | judge | 🟢 |
| Direct-fetch ratio (portfolio)  | 1.0 on every stream (0 via-snippet) | ≥0.35 | 🟢 |
| Feeds with >50% fail rate       | 30 by the raw ratio. With little or no net success: openai.com 13/2, science.org 5/1, president.gov.ua 4/0, electionresults.govt.nz 4/0, consilium.europa.eu 3/0, sec.gov 3/0, plus a 1–2/0 tail | 0 | 🟡 |
| Citations on `reach: blocked` domains w/o `[via snippet]` | 0 | 0 | 🟢 |
| Unconsumed feedback backlog     | 0 | 0 | 🟢 |
| Vendor-PR-lead share (AI/ML, §M) | 6/12 non-paper items vendor-sourced; vendor framing as the lead in 2/12 (~17%) | ≤40% | 🟢 |
| Aggregator-shape failures (§M, of 5) | 0 | 0–1 | 🟢 |
| Personalization misses (§M, of 5) | 0 | 0–1 | 🟢 |
| Affiliation coverage (§N) | 4 of 54 papers "not listed" (~7%) | <20% | 🟢 |
| Halo audit (§N) | no prestige skew | — | 🟢 |

## A–N: Detailed findings

### A. Source diversity & discovery
From `source-health.json` (30-day windows):

- **news**: 65 unique domains (58 last week), 52 new, waiver rate 0.10 (0.207), nothing saturated. Top-5 share is **0.643**, the sixth straight small improvement (0.695 → … → 0.653 → 0.643). **All six editions met discovery**, the first clean sweep. The tagged domains are first-party: uvek-gis.admin.ch (the energy office's reservoir open data), mausam.imd.gov.in (India's cyclone bulletin), ina.gl (Greenland's parliament agenda record), tuomioistuimet.fi (the Helsinki court's own judgment notice), swisstph.ch (the heat-mortality estimate), and fincen.gov plus fintrac-canafe.canada.ca (the regulators' own orders). This is the pattern the 0.35 target needs: when an outlet reports an institution's act, fetch the institution. At about 0.01 per week, the 0.50 bar is still months away. That is structural, because only SRF, Al Jazeera and Le Temps reach by curl.
- **ai-ml**: 31 unique (33), 25 new, waiver 0.222, top-5 **0.517** (0.548). That is the best reading on record and close to the 0.50 bar. Both editions met discovery: datatracker.ietf.org and cursor.com (11-03), and newsletter.semianalysis.com (11-06, the GDPx benchmark's own creator). One weak tag: **adweek.com** carries `[new source]` on the 11-06 Anthropic–AP licensing item. Adweek is a trade outlet, not a primary, and the item is also `[single-source]`. It did not count toward discovery, but it is the junk-anchor pattern §G watches for (see §G).
- **science**: 5 unique (7 last week), 3 new, top-5 1.00, nature.com saturated, waiver 0.50. The 11-04 edition met discovery with jpl.nasa.gov and jamstec.go.jp, both institutional newsrooms paired with their papers, as last week. The 30-day count fell because the 10-07 edition's domains aged out. With one edition a week and journals as the core, science needs about two institutional pairings per edition to hold ≥10. The writer is doing exactly that, so no patch is needed.
- **sports**: **4 unique (4), 1 new, top-5 1.00, three saturated** (autosport.com, bbc.co.uk, srf.ch). It is the worst stream for the second week. The 11-02 discovery was **waived**. The writer probed swissindoorsbasel.ch, fia.com, atptour.com, sfl.ch and motogp.com, the same football, F1 and tennis primaries as every week. The preflight fetch list holds ~45 sports domains, including **sihf.ch, fis-ski.com, football.ch and tas-cas.org** at `probation` / `reach: proxy`. None appears in any sports Feeds-hit line, ever. The section list explains why. Across the last six editions the desks were football, F1 and tennis every week. "Winter sports & the rest" appeared only twice, and Swiss National League hockey never did, although it is in season (the prompt itself says Sep–Apr). The Gaps lines on 10-05, 10-12 and 10-19 name hockey as "not covered" or "nothing verified". **The diversity deficit and the coverage gap are the same problem: the writer never opens the hockey desk.** Patch 1.
- **weekend**: 46 unique (42), 39 new, waiver **0.40** (0.60, flat for three weeks before this). It met discovery with ricursive.com (the lab's own launch post) and blog.redwoodresearch.org.

**Tier distribution:** this week I read anchor tiers from the writers' own index records rather than hand-mapping body citations. Of 140 story anchors, 88 are T1 (**62.9%**) and 52 are T2, with **no T3**. **This is not comparable with last week's 35.2%**, which counted every body link against the registry, so T2 secondaries counted as much as anchors. The anchor measure is the one that matches the policy ("lead with T1"), so I propose keeping it. 🟢

**Linguistic/geographic:** about 33% of citations are non-English by a host/path heuristic (SRF, RTS, Le Temps, RFI, Le Monde, El País, ANSA, NZZ, admin.ch/fr, tuomioistuimet.fi). Countries covered alongside Switzerland include the US, Iran, Ukraine, Russia, Israel, Bulgaria, Greenland/Denmark, Spain, Sudan/Ethiopia, Venezuela, India, Finland, Hong Kong, Paraguay, France, Malaysia, New Zealand and South Africa.

### B. Aggregator leakage
`briefs.aggregator_leakage` is **empty**. 🟢 The Weekend's Simon Willison essay is a registered T2 blog and was cited for his own experiment, so it is not an aggregator.

### C. Link health: unmeasurable (egress wall), no fabrication found
`linkcheck: 5/20 resolve (2xx/3xx) — window [2026-11-02, 2026-11-08], 171 links total.`
`linkcheck: recap 3/8 resolve (2xx/3xx) — Weekend "Week in headlines", always checked.`

All 15 sample failures and all 5 recap failures are **ERR:56**: the egress proxy refused the CONNECT to admin.ch, vd.ch, DW, RFI, Ukrinform, arXiv, doi.org, Nature, JPL, Fermilab, BBC, swisstph.ch and openai.com. **There are zero 404s and zero fabrication candidates.** Every failing recap URL sits on a host that the writers' fetch logs show working through the proxy that week (ukrinform 10 ok, dw 16 ok, swisstph 3 ok, admin.ch 17 ok). All the hosts reachable from here (SRF, Al Jazeera, Le Temps) resolved 200. This is the eighth straight week the dimension is unmeasurable.

**Claim spot-checks (8, on reachable hosts): 8 consistent.**
- Swiss inflation (11-03 news, SRF): 1.5% in October, highest since December 2023, forecasts 1.1–1.4%. All match. ✔
- Joshua Wong (11-05 news, Al Jazeera): ten more years, collusion under the NSL, two months before his January 2027 release. All match. ✔
- Init7 v. Vaud prosecutor (11-04 news, SRF): no legal basis for prosecutor-ordered DNS blocks outside specific laws, appeal by Init7. Matches. ✔
- BVG minimum rate (11-04 news, Le Temps): 1.25% → 2%, above the commission's 1.75%. Matches. The brief dates the recommendation "4 September". Le Temps says "fin août", so the date is **unverified, not contradicted** (likely the federal release date). ✔ (minor)
- Federal judges' relationship (11-06 news, SRF): unanimous, public deliberation, pilot case, Donzallaz (no party) / van de Graaf (SVP), "dauernde Lebensgemeinschaft". All match. The brief's French gloss "durablement ménage commun" is ungrammatical (the statutory phrase is "ménage commun de fait durable"). This is cosmetic. ✔
- New Zealand election (11-07 news, Al Jazeera): each party just under 30%. Matches. The page has since been updated to a "slim majority" headline, consistent with the brief's "too close to call" at press time. ✔
- Bulgaria runoff (11-02 news, SRF): Iotova 57.5%, Gyurov runner-up. Matches. ✔
- Lugano 2–1 Basel (11-02 sports, SRF): Otele's 37th-minute goal, ~65% Basel possession, 23 games unbeaten in all competitions, YB 3–5 Zürich, a nine-point lead. All match. ✔

### D. Section vitality + reading surface
`briefs.by_stream.*.empty_sections` is **empty for every stream**. 🟢 No desk was empty three times. The writers omit out-of-season desks rather than filling them. Sports applies this a little too freely to hockey, as §A explains.

**Reading surface:** `surface: 6 flag(s) -- 0 parity miss(es), 6 lede-fallback WARN(s), 0 overdue desk(s)`
- FLAG WARN `_posts/2026-10-24-weekend.md` st-5745ce974a94
- FLAG WARN `_posts/2026-10-29-news.md` st-3b1c1bdf8ebb
- FLAG WARN `_posts/2026-10-30-news.md` st-fb7d688d5a1f, st-9fa21cc3d182, st-7a4b732422f6
- FLAG WARN `_posts/2026-10-31-weekend.md` st-c71b778862b5

These are **the same six WARNs as last week**, all on editions older than this window, and **none of this week's eleven editions trips one**. Every newest edition reaches its card floor (7–9 cards each). The two builder shapes diagnosed last week are unchanged in `tools/build_stories_feed.py`: `_split_inline_why` meta-tests the paragraph before splitting, and `strip_trailing_citations` does not balance parentheses. This week's writers simply did not produce those shapes. The six cards will age off the feed, but the defect is still live (Open question 4).

### E. Coverage gap recurrence
Gaps clusters this week (≥3 = structural):
- **Official election-results sites unreachable (4 editions: 11-02, 11-04, 11-07 ×2):** cik.bg / results.cik.bg, bechirot.gov.il, electionresults.govt.nz and elections.org.za all failed even through the proxy. The election items then rested on SRF, Al Jazeera/AP or a single outlet. 🔴 This is structural, and no prompt line can fix it. These sites block the fetch Worker's egress. See Open question 3.
- **openai.com article pages (3 editions: 11-03 and 11-06 ai-ml, 11-07 weekend):** 13 fail / 2 ok. The writers handled it better than on 10-30. 11-06 anchored the GPT-6 Cyber item on the deploymentsafety.openai.com system card and the Astra item on alignment.openai.com, which both worked. But 11-03 still left three OpenAI posts uncovered. The pending `openai.com → blocked` judgment flip is carried.
- **Sports official league pages (5th consecutive week):** sfl.ch, atptour.com, motogp.com and premierleague.com were unreachable or JS-only. Note that sihf.ch, the hockey federation's results page, is **not** in this list, because it was never tried.
- **science.org (2nd week):** article pages and TOC feeds fail (5/1). Crossref abstracts are the working fallback, used correctly on 11-04.
- **Primary not fetched, outlet used (one-offs):** CENTCOM, OFAC, consilium.europa.eu, bger.ch press, Ukrenergo, president.gov.ua. Each is named honestly.

### F. Triangulation rate
Portfolio: 16 `[single-source]` of 140 citations (**11.4%**). By stream: news 0.218 (12/55, below the 25% per-stream bar), ai-ml 0.10, science 0.077, sports 0.0, weekend 0.0. 🟢 News single-sourcing is concentrated in Swiss institutional items, such as SFAO and federal releases (where the institution is itself the primary), and in the two blocked-commission election items.

### G. Tag discipline
Counts from `health.json`: ai-ml preprint 18, vendor PR 4, new source 4, single-source 3. News official PR 6, new source 7, single-source 12. Science new source 2, preprint 1. Weekend preprint 12, vendor PR 3, new source 2, official PR 1. Sports none.
- `[preprint]`: all 18 AI/ML arXiv items carry it (9 + 9). Five sampled Weekend arXiv entries also carry it. ✔
- `[vendor PR]`: LFM3, GPT-6 Cyber, ERNIE-5.5 and Claude Personal Finance are all tagged. ✔ **One inconsistency:** the Astra misalignment report is untagged in the 11-06 AI/ML edition but tagged `[vendor PR]` in the 11-07 Weekend. Untagged is defensible, since it is a self-reported failure rather than a launch, and both editions say the figures are OpenAI's own and unverified. The two streams should still agree. It is minor and not patched.
- `[disputed]`: no uses this week, and none were needed.
- `[new source]` spot-checks (2): **swisstph.ch** is a genuine primary (the research institute publishing its own FOPH-commissioned estimate). ✔ **adweek.com** is a trade outlet tagged as new. It is not a primary, and the item is single-sourced to it. It was not claimed for discovery, so the lint impact is nil. If it recurs, the fix is wording in the shared discovery partial rather than a patch now. `sources/candidates.jsonl` is empty: this week's tags have already synced into the registry as `status: candidate`.
- `[via snippet]`: **0 portfolio-wide** (1 last week). 🟢

### H. Topic balance (weekend)
`ml_items 14 / science_items 16`, `ml_share` **0.467**, inside [0.35, 0.65]. 🟢

### I. Repetition detection
Repeat rates are 0.0 for news, ai-ml, science and sports. The weekend rate is **0.314 (11/35)**, mostly by construction: the six "Week in headlines" items, the Astra report and the Kimi/llama.cpp follow-ons all carry ids that ran during the week. Each re-run I checked adds a dated new fact. Komyshuvakha rose from 42 to 53 bodies recovered. Paraguay moved from resignation to the Senate's impeachment and house arrest. The Federal Council pension item has no new fact, but it is a recap entry, which is the section's job. 🟢 The News 11-07 Gaps line explicitly holds Paraguay back "no confirmed new fact", which is good `[ongoing since]` discipline.

**Identity integrity:** `reconcile: 0 flagged, 0 resolved-by-merge, 24 editions checked`. 🟢

### J. Cross-week trend
See the trend table below.

### K. Feed reachability and direct-fetch rate
**Per-stream:** `direct_fetch_ratio` is 1.0 on all five streams, with 0 via-snippet (news 55/55, ai-ml 30/30, science 13/13, sports 7/7, weekend 35/35). 🟢 Every stream is above its range.

**Per-feed (method comparison):** curl carries only aljazeera.com (30/0), srf.ch (38/2), letemps.ch (15/0), export.arxiv.org (38/0), quantamagazine.org (5/0), anthropic.com, claude.com and microsoft.com, plus 9 nature.com hits. **Everything else rides the proxy**, which is the expected state of the sandbox, not a regression. Feeds with >50% failure and little or no net success: openai.com 13/2, science.org 5/1, president.gov.ua 4/0, electionresults.govt.nz 4/0, fintrac-canafe.canada.ca 4/2, consilium.europa.eu 3/0, sec.gov 3/0 (efts.sec.gov full-text search 1 ok, which is the right workaround), 24heures.ch 3/1, mausam.imd.gov.in 3/1, and a 1–2/0 tail of institutional newsrooms (actu.epfl.ch, news.uzh.ch, psi.ch, unibe.ch, mpg.de, home.cern, news.cornell.edu). For the government, election and court hosts, both curl and the proxy fail, so **the fetch Worker's egress is the wall** (Open question 3). Most of the other ">50%" entries are 1 curl fail plus 1 proxy ok, which means the chain is working.

**Reach drift (computed):** there are **19 flips**, all copied into `proposals/registry-2026-11-08.yml`. **16 are CARRIED** from unstamped files. arxiv.org (the abstract host; export.arxiv.org stays direct), huggingface.co, lemonde.fr and rfi.fr are in **all six** files from 10-04 to 11-08. The **3 new** flips are ina.gl, swisstph.ch and nasa.gov (via jpl.nasa.gov). Each is a writer `[new source]` domain from this week, first reached *through the proxy*, and each was registered as `reach: direct` (registry lines ~5382 and ~5406). That is the sync defect again (Open question 2). There are no judgment overrides: every entry has ≥3 proxy successes and 0 curl successes. The `openai.com → blocked` judgment flip and a proposal to register bbc.co.uk are carried in the same file. The reverse case (curl now succeeding on a `proxy` domain) does not occur.

**Domains that shouldn't be cited:** there are 0 citations on `reach: blocked` domains and 0 `never:` domains. No retired or demoted domain appears as an anchor. 🟢

### L. Output volume
Mean words (this week vs last): news 1663 vs 1907 (−13%), ai-ml 2794 vs 2662 (+5%), science 2985 vs 3248 (−8%), sports 1218 vs 1333 (−9%), weekend 6423 vs 6564 (−2%). **No stream grew >25%.** 🟢 Weekend remains the largest single spend, about 6.4k words and 160 calls, and its repeats are structural rather than re-summaries, so no lever is warranted.

### M. Editorial shape
- **Vendor-PR-lead share (AI/ML):** there were 12 non-paper items across 11-03 and 11-06. Six are vendor-sourced: LFM3, Astra, GPT-6 Cyber, ERNIE, Claude Personal Finance and the Cursor incident notice. Two lead with vendor framing: "OpenAI ships GPT-6 Cyber to vetted security teams" and "Claude adds read-only bank-account analysis". Even these two add independent context, such as The Verge's quote on evaluation awareness and TechCrunch's list of what data Claude sees. That puts vendor-framed leads at **~17%**. 🟢 The best items were independent: the Anthropic S-1/A risk-factor text (located through SEC full-text search when sec.gov 403'd), the IETF training-preference draft and the SemiAnalysis GDPx benchmark.
- **Aggregator-shape check (5 leads):** I sampled the Init7 ruling (court via SRF + init7.net), Greenland's defence vote (ina.gl), the Fitburg sentence (tuomioistuimet.fi), the Swiss TPH heat deaths (swisstph.ch) and the GDPx benchmark (the creator's own post). All five anchor a primary and add framing the source lacks. **0 failures.** 🟢
- **Personalization (5 stories):** I sampled the Init7 DNS-block ruling (what it means for Swiss ISPs and prosecutors), the BVG rate rise (effect on insured savings), the heat-mortality estimate (MeteoSwiss thresholds), the Claude Personal Finance item (US-only, stated plainly) and the Joshua Wong sentence (no CH angle forced, correctly). **0 misses.** 🟢

### N. Affiliation element
- **Coverage:** 4 of 54 papers read "not listed" or carry no affiliation (~7%). They are AI/ML 11-03 arXiv:2611.02404, 11-06 arXiv:2611.07639, and the Weekend's 2611.05609 and 2611.07639, with reasons given in the Gaps line. Science 11-04 is 0/13. I spot-checked three bylines against `index/stories/`: Princeton/Anthropic (2611.07554), Stanford/Cornell (2611.08417) and TU Berlin/BIFOLD (2610.41480) all reached their records' `affiliations`. 🟢
- **Halo audit:** both unaffiliated AI/ML papers sit at importance 1, alongside MBZUAI, UC Riverside, UC San Diego, HK PolyU and Queen's University papers. Small or independent labs (Sparq, Tara Research, Queen Mary's single author) sit at 2. Stanford and Princeton/Anthropic also sit at 2, and none of the papers is at 3. **No prestige skew.** 🟢

## Prior proposals status
- `proposals/registry-2026-10-04.yml` through `-11-01.yml` (5 files): **pending, not applied**. All are unstamped, and the carried domains are still `reach: direct` in `sources/registry.yml`. The 11-01 `openai.com → blocked` judgment flip is also pending (openai.com is still `status: established`, `reach: direct`). The last stamped registry file is still `registry-2026-09-27.yml`.
- `proposals/reader-model-2026-10-18.json` rm-1 (drop the OpenAlex lookup from `routines/_shared/affiliations.md`): **pending, not applied**. The bullet is still at lines 16–17. No writer called api.openalex.org this week, so the cost was nil. Not re-proposed.
- `proposals/reader-model-2026-11-01.json`: no proposals, so there is nothing to verify.
- Last week's six scout candidates (nationalleague.ch, bscyb.ch, fcb.ch, spenglercup.ch, bundesliga.com, laliga.com) reached the registry as `status: candidate`, **`reach: direct`** (the `proxy-needed` was dropped), with **`last_cited: 2026-11-01`**, the scout date, although none was cited. That is the sync defect for the third straight week.
- 11-01 Open questions still open: bbc.co.uk unregistered (re-proposed in this week's registry file); `sources/registry.yml` line 1017 unquoted colon (`yaml.scanner.ScannerError … line 1017, column 19`, fifth week); the two builder shapes (unchanged); sports lever (a)/(b)/(c) (no decision; Patch 1 is a narrower alternative).

## Source scout (Sunday duty)
- **Stream picked: sports.** Its new-domain ratio is the lowest (1/3 = 0.33× target), against science 3/3 = 1.0×, ai-ml 25/10 = 2.5×, news 5.2× and weekend 13×.
- **Candidates:** I looked for primaries absent from the bench. The two strongest Swiss gaps were the Swiss Ice Hockey Federation (sihf.ch) and FIS (fis-ski.com), both probed (ERR:56). **Both turn out to be registered already** (probation, `reach: proxy`, seeded 2026-07-17), so **no candidates were appended**. The sports bench is not short of sources: ~45 domains in the fetch list and ~35 `candidates_to_try`. More candidates would not help, so I spent the remaining budget on reachability. I probed six untried bench entries directly (rsi.ch/sport, swiss-ski.ch, iihf.com, kicker.de, lequipe.fr, swisstennis.ch). All returned ERR:56 from this egress, which is inconclusive and not a site verdict. The finding is that the writer's coverage choice, not the bench, is the constraint (Patch 1).
- **Re-probes** of the next 5 stalest `reach:` entries (bootstrap-only, 2026-07-07, alphabetically after last week's block): cnn.com, commission.europa.eu, consilium.europa.eu, csoonline.com and decrypt.co. All five returned ERR:56 from here, which is inconclusive. One is noteworthy: **consilium.europa.eu** is `reach: direct` but went 3 fail / 0 ok in writer telemetry this week (11-07 News methane item), through the proxy too. That is not yet a computed flip (no proxy success), so it is watched, not proposed.
- **Fetches used: 13 of 20** (8 candidate/bench probes + 5 re-probes). The 8 claim-check fetches in §C are counted separately.

## Patch proposals (for human review)

### Patch 1 — Check the Swiss hockey round every in-season edition
**Target prompt:** Sports (`routines/src/sports.md`, then `python3 routines/assemble.py`)
**Section affected:** `## ⛷️🏒 Winter sports & the rest`
**Issue:** Swiss National League hockey has been in season since September, yet it has had no item in six editions. sihf.ch is in the fetch list but has never been fetched, and the stream is the worst for diversity (4 domains, 3 saturated). "Omit anything with nothing new" is being applied to a desk that is never opened.
**Proposed change:**

> **Before:**
> ```
> Alpine skiing World Cup (favour Swiss racers), Swiss National League + NHL headlines, and a catch-all for cycling (Tour de Suisse / de France), athletics, and other notable events. In-season only; omit anything with nothing new.
> ```
>
> **After:**
> ```
> Alpine skiing World Cup (favour Swiss racers), Swiss National League + NHL headlines, and a catch-all for cycling (Tour de Suisse / de France), athletics, and other notable events. In-season only; omit anything with nothing new. Hockey runs Sep–Apr: in season, check the Swiss National League round every edition (SRF Sport /sport/eishockey, sihf.ch game-center via the proxy) before deciding to omit the desk — a quiet round is a valid omit, an unchecked one is not.
> ```

**Why this helps:** It opens the Swiss sport with the most top-league fixtures each week and puts sihf.ch, a registered T1 primary, to work. That moves both the coverage gap and the unique-domain count without arming any cap.
**Risk:** It may add one or two proxy fetches per edition, and it could tempt a filler hockey item on a quiet round. The "valid omit" clause is there to guard against that.

No other prompt patches. The rest of this week's issues sit in the registry apply step, registry sync tooling, the builder and the fetch Worker's egress, and a prompt patch fixes none of them.

## Reader-feedback → profile proposals
**Reasoned events in window (by event `ts`, 2026-11-02..11-08): 1.**
- st-268f8d7e2515 (ai-ml 2026-11-06, "OpenAI says GPT-6 Astra quietly held back on safety research"), 👎, 2026-11-06T13:43:50Z: *"don't use intermediate token generation as a reasoning proxy, this is proveably wrong"*. It was preceded 40 s earlier by a bare 👎 on the same story, which counts as the same signal. **Deferred: below the 2-distinct-stories bar.** Editorial note: the item glossed chain of thought as "the model's visible reasoning", and its "Why it matters" says the gap left "little trace in its reasoning". Both treat intermediate tokens as a faithful readout of the model's reasoning. The 11-07 Weekend re-ran the item with the same framing ("runs where the chain of thought stated a decision"). The writers could not have seen the vote, because only `reader-profile.md` reaches them. See Open question 1.

`health.json`: `feedback.by_stream` = ai-ml down 2, up 0, retractions 0; `unconsumed_total` 0. Nothing is auto-applied to `reader-profile.md`, and there is no source-weights proposal. **Reader brief-proposals:** no `proposals/*.jsonl` reader records exist, so there is nothing to surface.

## Machine-readable proposals
- `proposals/registry-2026-11-08.yml`: 19 computed reach flips (16 CARRIED, 3 new), the carried `openai.com → blocked` judgment flip, and a bbc.co.uk registration (probation, T2, `reach: proxy`). All are `applied: false`.
- `proposals/reader-model-2026-11-08.json`: rm-1 = Patch 1 (`routines/src/sports.md`), `applied: false`. Its `note` records the deferred feedback event and that the 10-18 rm-1 (OpenAlex) is still pending.

## Cross-week trend
| Metric | 10-11 | 10-18 | 10-25 | 11-01 | 11-08 |
|---|---|---|---|---|---|
| news top-5 share | 0.691 | 0.685 | 0.662 | 0.653 | **0.643** ↓ (better) |
| ai-ml top-5 share | 0.618 | 0.571 | 0.547 | 0.548 | **0.517** ↓ (better) |
| news unique 30d | — | 47 | 52 | 58 | **65** ↑ |
| ai-ml unique 30d | 29 | 31 | 34 | 33 | 31 → |
| science unique 30d | 4 | 4 | 4 | 7 | 5 ↓ (age-out) |
| sports unique 30d | — | 9 | 6 | 4 | **4** → (worst) |
| weekend waiver rate | 0.80 | 0.60 | 0.60 | 0.60 | **0.40** ↓ (better) |
| news discovery met | — | — | — | 4/6 | **6/6** |
| T1 citation % | 33% | 39% | 42% | 35% | 63%* (anchor-level; not comparable) |
| aggregator citations | 0 | 0 | 0 | 0 | 0 |
| T3 leakage | 0 | 0 | 0 | 0 | 0 |
| empty sections | 0 | 0 | 0 | 0 | 0 |
| surface WARNs | — | 1 | 1 | 6 | 6 (all carried, 0 new) |
| via-snippet (portfolio) | 1 | 0 | 2 | 1 | 0 |
| reach-drift flips | 24 | 29 | 21 | 23 | 19 (16 carried) |
| link sample | 6/20 unmeas. | 4/20 unmeas. | 5/20 unmeas. | 3/20 unmeas. | 5/20 unmeas. |
| openai.com fail/ok | — | — | 11/2 | 18/2 | 13/2 |
| claim checks consistent | — | — | — | 8/8 | 8/8 |

\*Measured from writer-recorded anchor tiers this week, not body-link counts.

The writing is steady-good and improving on the operator's primary lens. News diversity rose for the sixth week, AI/ML reached its best top-5 share yet, and the Weekend waiver rate finally fell. The non-writing backlog is unchanged and still growing: six registry files are unstamped, the sync default is producing new drift every week, the builder shapes are unfixed, and the YAML colon is still there. Sports diversity is flat at its worst. This week's finding gives it a concrete, editorial cause.

## Open questions for human review
1. **Chain-of-thought framing (reader 👎, deferred).** The reader's rule, *"don't use intermediate token generation as a reasoning proxy"*, is general, and the Weekend repeated the framing a day later. It is below the auto-apply bar (one story), so I have not written it to `reader-profile.md`. If you agree with it, a one-line learned preference would reach every AI writer at once. Suggested wording: `- 2026-11-08: do not present chain-of-thought / intermediate tokens as a faithful readout of a model's reasoning; describe them as the model's generated reasoning text and, where a result depends on it, say that CoT faithfulness is contested (1× 👎 with reason on ai-ml 2026-11-06 Astra item, "don't use intermediate token generation as a reasoning proxy, this is proveably wrong").` Alternatively, I can auto-apply it next week if a second story draws the same signal.
2. **Registry sync drops the candidate's reach (unfixed, third confirmation).** `tools/sources/registry.py:406` and `:455` write `"reach": "direct"` for every new candidate, and `last_cited` is taken from `first_seen` even for uncited scout entries. This week it produced all three new drift flips (ina.gl, swisstph.ch, nasa.gov) and stamped last week's six scout candidates as cited on 2026-11-01. The fix is unchanged: map `reach` from the record when present (`proxy-needed` → `proxy`, and writer `[new source]` first reached via the proxy → `proxy`), and set `last_cited` only when `via != "scout"`. Then run `python3 -m unittest discover -s tools/tests`.
3. **Official election-results and government sites block the fetch Worker (4 of 6 News editions).** Covered so far: cik.bg, bechirot.gov.il, electionresults.govt.nz, elections.org.za, president.gov.ua and consilium.europa.eu. Both curl and the proxy fail. Is a second egress path worth having for this class, for example a different Worker region or a search-API cached-copy fallback recorded as `[via snippet]`? Or do you accept outlet-sourced results for elections? The writers already disclose the gap honestly every time.
4. **Builder: two parser shapes, 6 WARNs (carried).** Same diagnosis and golden cases as 11-01, Open question 3. No new instances this week, so this is now about correctness, not urgency.
5. **Apply the reach flips, or grant the evaluator a bounded auto-apply for computed `briefs.reach_drift` flips.** This is the fifth time I have asked. Four domains have been in all six files since 10-04.
6. **Test suite in this sandbox:** 820 tests, the same 3 failures (the ledger and fold permission tests cannot fail when running as root) and 2 skipped. This is an environment artefact, unchanged. `assemble.py check` is OK on all generated prompts.
7. **`sources/registry.yml` line 1017**: the unquoted `note: sports: https://…` still breaks strict YAML. Fifth week.
