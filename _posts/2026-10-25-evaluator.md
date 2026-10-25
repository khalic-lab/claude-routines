---
layout: single
title: "Weekly Pipeline Review — 2026-10-25"
date: 2026-10-25T10:46:59+01:00
categories: [evaluator]
published: true
---

# Weekly Brief Pipeline Review — 2026-10-25

_Coverage: briefs from 2026-10-19 to 2026-10-25._
_Files read: 6 news, 2 AI/ML (expect ~2), 1 science (expect ~1), 1 sports (expect ~1), 1 weekend, prior review found (2026-10-18, 7 days old)._

The briefs had another clean week. All six expected News editions ran; Sunday's has not fired yet, which is normal. Every edition has a Discovery footer and exactly one importance-3 story. Aggregator leakage, T3 leakage, empty sections and identity-reconcile flags are all zero. **T1 citations reached 42%, the first green reading on that line.** Seven of the eight claim spot-checks matched their sources. The eighth was a small sports error: Taverne is fourth-tier, not "third-tier". The best editorial moment of the week: the 10-24 News follow-up on Hebron corrected its own death toll in the open ("a higher toll than first reported").

What needs attention is again outside the writing:

1. **The reach-flip backlog has gone unapplied for four weeks.** The computed drift list has 21 domains this week. 15 of them are already in the unstamped 10-04, 10-11 or 10-18 files. arxiv.org, lemonde.fr, rfi.fr and huggingface.co are now in **all four**. The last stamped registry file is 2026-09-27.
2. **A registry-sync defect manufactures part of that drift.** `tools/sources/registry.py sync` hard-codes `reach: direct` for every new candidate. It drops the scout's `"reach": "proxy-needed"`, and it also covers writer-tagged domains the writer could only reach through the proxy. Four of this week's six new flips (gfsbern.ch, svp.ch, merck.com, unep.org) are domains first registered this month. Open question 2.
3. **A new reading-surface WARN** on the 10-24 Weekend, traced to a parser shape the builder misses (§D). It is a builder defect, not a writer slip.
4. **Science (4 domains) and Sports (6) are below the ≥10 weekly-tier bar.** Science's shortfall is still the metric-versus-policy mismatch raised last week, which is unanswered. Sports' shortfall is new and real: three domains are saturated.

There is one reasoned reader vote this week. It is deferred because it sits below the two-distinct-stories bar. Nothing is auto-applied.

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains 30d (worst stream vs its tier) | science 4, sports 6 (news 52, weekend 38, ai-ml 34) | ≥30 news/ai-ml · ≥10 weekly | 🔴 |
| New domains this window (portfolio) | 14 `[new source]` tags this week; science 2/3 per 30d, every other stream at or above its tier | ≥2–3/wk (≥10/mo) | 🟡 |
| Top-5 outlet share (worst of news/ai-ml) | news 0.662 (ai-ml 0.547) | ≤0.50 (→0.35); weekly report-only | 🔴 |
| Waiver rate (worst stream) | science 0.75 (weekend 0.60, sports 0.50) | ≤50% | 🔴 |
| Discovery footer present (every brief) | 11/11 | 100% | 🟢 |
| T1 citation %                   | 41.9% (88/210; 5 unregistered) | ≥40% | 🟢 |
| T3 leakage count                | 0 | 0 | 🟢 |
| Non-English citation % (portfolio) | ~27% (56/210) | ≥10% | 🟢 |
| Link sample pass rate           | 5/20; recap 3/9. **Unmeasurable**: every failure is egress ERR:56, with no 404s | ≥90% | ⚪ |
| Fabrication count               | 0 | 0 | 🟢 |
| Single-source rate (portfolio)  | 9.2% (14/153) | <20% | 🟢 |
| Empty section instances         | 0 | <5 | 🟢 |
| Reading-surface flags (§D, surface.py) | 1 (new WARN, 10-24 weekend; builder shape) | 0 | 🟡 |
| Repeat rate (worst stream)      | weekend 0.588 (by construction); all others 0.0 | judge | 🟢 |
| Direct-fetch ratio (portfolio)  | ≥0.97 on every stream (2 via-snippet) | ≥0.35 | 🟢 |
| Feeds with >50% fail rate       | 29 by the raw ratio. Those with no net success: openai.com 11/2, physics.aps.org 6/0, actu.epfl.ch 4/0, corporate.dukehealth.org 4/0, plus a 2–3/0 tail | 0 | 🟡 |
| Citations on `reach: blocked` domains w/o `[via snippet]` | 0 | 0 | 🟢 |
| Unconsumed feedback backlog     | 0 | 0 | 🟢 |
| Vendor-PR-lead share (AI/ML, §M) | 14/19 non-paper items vendor-sourced, all tagged; vendor framing as the lead ~1/19 | ≤40% | 🟡 |
| Aggregator-shape failures (§M, of 5) | 0 | 0–1 | 🟢 |
| Personalization misses (§M, of 5) | 0 | 0–1 | 🟢 |
| Affiliation coverage (§N) | ~5 of ~40 unique papers "not listed" (~12%) | <20% | 🟢 |
| Halo audit (§N) | no prestige skew (independent Zanolini paper at importance 2) | — | 🟢 |

## A–N: Detailed findings

### A. Source diversity & discovery
From `source-health.json` (30-day windows):

- **news**: 52 unique domains (47 last week), 41 new, waiver rate 0.276 (0.414 last week), nothing saturated. Top-5 share is 0.662, the first real move in four weeks (0.695 → 0.691 → 0.685 → 0.662). All six editions met discovery, and every tag is a first-party primary: stats.gov.cn (NBS Q3 release), elections.ab.ca (Elections Alberta turnout), unep.org (the Emissions Gap Report), eida.ethz.ch (the Swiss Seismological Service's event catalogue), gfsbern.ch (the SRG poll's own institute) and svp.ch (the party's own candidate list). The rotation is working. It is still above the 0.50 bar because only SRF, Al Jazeera and Le Temps curl reliably.
- **ai-ml**: 34 unique (31), 30 new, waiver 0.111, top-5 0.547 (0.571). It is improving for a second week. Both editions met discovery. itm.nrw hosts the Landgericht Aachen order PDF, which is the court document itself, so the citation is primary even though the host is a university institute. thephp.foundation and wiz.io are first-party security primaries. claude.com is Anthropic's product blog.
- **science**: 4 unique, 2 new, top-5 1.00, waiver 0.75. **Worst stream for the sixth consecutive review.** The 10-21 waiver is honest and specific: ligo.org was anchored, and corporate.dukehealth.org and news.ucsc.edu were probed and found unreachable. Editorially the edition cites Google Quantum AI, COHERENT, ETH, AWI, Northwestern, LVK, TESS/UCLA/CfA, INAF and more. It still scores 4 because each paper is anchored on its journal host. Last week's Open question 2 (count institutions, not publisher hosts) has no answer, so the line stays red whatever the writer does. None of the seven candidates scouted last week (unibas.ch, cam.ac.uk, caltech.edu and others) was cited. That is expected: the science writer anchors on the paper by policy. More scouting will not move this metric.
- **sports**: **6 unique (9 last week)**, 4 new, top-5 0.958, and **three saturated domains** (autosport.com, bbc.co.uk, srf.ch). bbc.co.uk was saturated for a third week last week and now has company. The edition met discovery with haasf1team.com, the team's own driver announcement and a legitimate primary. Diversity is sliding, though: seven stories rest on four hosts. The Gaps line explains why. The official league sites (SFL, Premier League, F1) are JavaScript shells, the same renderer limit as the past three weeks. The structural fix is a non-JavaScript primary per desk, such as the SFL's press releases or the FIS/IIHF results PDFs. This is the obvious target for next week's scout if science's metric question is settled.
- **weekend**: 38 unique, 30 new, waiver 0.60 (flat). The waiver is honest: merck.com was anchored as the INTerpath-001 sponsor, and noemamag.com and hai.stanford.edu were probed, reachable but with nothing strong enough to cite.

**Tier distribution:** of 210 body citations, 88 are T1 (**41.9%**, up from 39% and 33%), 117 T2 and 5 unregistered (bbc.co.uk ×2, elections.ab.ca, ligo.org, wiz.io; the tagged ones are awaiting registry sync). There is **no T3**. 🟢

**Linguistic/geographic:** about 27% non-English (SRF, Le Temps, RFI, Le Monde, ANSA, El País, GFS Bern, SVP, vd.ch and others). News covered France, Canada, Russia/Ukraine, Saudi Arabia/Yemen, Israel/West Bank, Sudan/South Sudan, Tibet, Kenya, Romania, Serbia, North Korea/China and Australia alongside Switzerland.

### B. Aggregator leakage
`briefs.aggregator_leakage` is **empty**. 🟢

### C. Link health: unmeasurable (egress wall), no fabrication found
`linkcheck: 5/20 resolve (2xx/3xx) — window [2026-10-19, 2026-10-25], 183 links total.`
`linkcheck: recap 3/9 resolve (2xx/3xx) — Weekend "Week in headlines", always checked.`

All 15 sample failures and all 6 recap failures are **ERR:56**: the egress proxy rejected the CONNECT to DW, RFI, Le Monde, arXiv, TechCrunch, the Guardian, UN News, USGS, svp.ch, gfsbern.ch, unep.org, kyivindependent.com and the-decoder.com. **There are zero 404s and zero fabrication candidates.** The recap URLs all sit on hosts the writers' own telemetry shows working through the proxy. This is the sixth straight week the dimension is unmeasurable. Only allowlisted hosts resolve: SRF, Al Jazeera and Le Temps.

**Claim spot-checks (8, on reachable hosts): 7 consistent, 1 minor error:**
- Taiz displacement (10-22 news, Al Jazeera): "nearly 260,000", OHCHR's 251 casualties (57 killed, 194 injured), and the spokesperson's 835 operations and 285 Houthi fighters all match. The brief correctly flags the government figures as unverifiable. ✔
- IRGC Hormuz mine claims (10-21 news, Le Temps/AFP): Sepah News, the "illegal" route and "two million barrels" with radar off all match. The brief correctly says there was no independent confirmation. ✔
- Swiss Ebola case (10-23 news, SRF): Abuja, the private clinic, probable infection in Uganda about two weeks earlier, no travel to DR Congo, the husband isolating without symptoms, and the other 25 staff well all match. ✔
- SRG poll (10-23 news, SRF/GFS Bern): 14,874 respondents, ±2.8, and the AHV age split (18–39: 56/35 against; over-65s 55% for) all match. ✔
- West Bank closure (10-23 news, Al Jazeera): Netanyahu's order, the "major attack" quote and the 20-minute gunfight match. The brief's "prepare for a full closure" paraphrases the DW wording ("full lockdown" on Al Jazeera). The soldier toll on the live page now reads "two of whom later died", against the brief's "two critically". The page was updated after publication, and **the 10-24 edition corrected it explicitly.** ✔ (The Al Jazeera URL slug still reads "israel-arrests-36-palestinians…" because the page was repurposed. Not a writer error.)
- Anthropic workforce study (10-20 ai-ml): junior technical hires 27% → 9%, juniors' share 21% → 14%, agent hours outnumbering staff six to one, and 17 interviews all match. ✔
- Claude Duet (10-23 ai-ml, claude.com): built on Opus 5.5, waitlist for US Pro and Max subscribers. Matches. ✔
- YB's Conte (10-19 sports, SRF Sport): the 5-0 Cup win at Taverne, the cruciate-ligament tear and the 839 days match. **✘ minor:** the brief calls Taverne "third-tier". SRF says *1. Liga*, which is Switzerland's **fourth** tier (Super League, Challenge League, Promotion League, 1. Liga). The headline's "839 days of injury" is also slightly loose: SRF counts 839 days since his transfer, and the injury came soon after. This is a factual slip, not a fabrication. One instance does not justify a patch.

### D. Section vitality + reading surface
There are no empty sections in any stream. The 10-23 AI/ML edition omitted its Benchmarks and Apple Silicon sections, and its Gaps line says so ("no standalone new substance this window"). That is honest omit-don't-fill. Sports omitted tennis, skiing and hockey for the same reason; the alpine World Cup opener in Sölden falls after the 10-19 edition.

`surface: 1 flag(s) -- 0 parity miss(es), 1 lede-fallback WARN(s), 0 overdue desk(s)`
- `FLAG WARN _posts/2026-10-24-weekend.md story st-5745ce974a94: no body parsed, card shows its lede` (the Apple Silicon inference paper). **This is a builder defect, and I traced the shape.** The bullet ends with the paper citation in parentheses, *containing* the byline and its own parenthesised sentinel: `([arXiv:2610.31479](…) · K. Yemets, … et al. (affiliation not listed))`. `strip_trailing_citations` does not remove that trailing run because the parentheses nest. The leftover ` · <authors>` makes `_is_meta_para` classify the whole prose paragraph as a byline, so `_pick_body` returns "". The writer's format is legal: the AI/ML dailies use the same byline, just outside parentheses. The ledger's `display_body` is intact, so the card still shows the authored prose through the documented fallback, and no reader-visible loss is confirmed. Open question 3 has the proposed fix.
- Last week's stale WARN on `2026-10-03-weekend.md` has aged out of the surface window.
- Newest editions keep every story: sports 7/7, science 14/14, ai-ml 20/20, news 9/9, weekend 34/34.

### E. Coverage gap recurrence
Recurring gaps (≥3 occurrences = structural):
1. **Official government and court primaries that refuse the fetch** (6 of 6 News editions): elysee.fr, bvger.ch (10-21), bger.ch's anonymised database (10-22), nmag.gov (10-22), whitehouse.gov (10-24), presidency.ro (10-24) and president.gov.ua (10-19). Each time the writer says so and falls back to wire-grade secondaries. This is structural egress and no source addition fixes it. consilium.europa.eu, last week's top gap, did not recur.
2. **openai.com article pages 403 even through the proxy** (10-23 ai-ml: 11 fail / 2 ok). Two OpenAI items rest on feed summaries plus Ars/TechCrunch. This is back after a week's lull and is now three of the last five AI/ML editions. The `[via snippet]` tag on the Google Cloud item is correct use.
3. **APS journal pages** (physics.aps.org 6/0, journals.aps.org 2/0) in science 10-21 and weekend 10-24. The RSS feed and the arXiv version stand in. This is new to the recurring list.
4. **Official sports pages are JavaScript shells** (SFL, Premier League, Formula1.com), for a fourth week (§A).

### F. Triangulation rate
Single-source rates: news 0.148 (9/61), ai-ml 0.108, science 0.0, sports **0.0** (0.40 last week), weekend 0.029. The portfolio rate is 9.2%. 🟢 Each news `[single-source]` item I checked carries the tag and says in the body why only one source was available.

### G. Tag discipline
These counts come from health.json. ai-ml: 19 `[preprint]`, 15 `[vendor PR]`, 4 `[new source]`, 1 `[disputed]`, 1 `[via snippet]`. News: 6 `[new source]`, 3 `[disputed]`, 1 `[official PR]`. Weekend: 16 `[preprint]`, 6 `[vendor PR]`.
- `[preprint]`: all 5 sampled arXiv items (10-20: the scheming, RL-4%-tokens and jailbreak-judge papers; 10-23: the sabotage and KLS papers) carry it. ✔
- `[vendor PR]`: Beam, DeepSeek V4.1-Flash, Flint, MiniMax M3.1 and Claude Duet are all tagged. ✔ The Merck/Moderna melanoma release in the Weekend carries `[vendor PR]` alongside `[new source]`, which is correct: the sponsor's release is the primary until the NEJM paper appears.
- `[disputed]`: the 10-24 Oleshky start date (27 vs 29 October, with all three sources named) is a textbook use. ✔
- `[new source]`: spot-checked two. **itm.nrw** hosts the Aachen court order PDF. The host is a university institute, but the document is the court's own order, so it is a genuine primary rather than a junk anchor. **haasf1team.com** is the team's own driver announcement, also genuine. ✔ `sources/candidates.jsonl` was empty at fire time because the sync folds it, so the tagged domains are already `status: candidate` in the registry.
- `[via snippet]`: 1 ai-ml and 1 news use. That is flat-low and healthy.

### H. Topic balance (weekend)
There are 16 ML papers and 16 science papers, so `ml_share` is **0.50**, on target for a fourth straight week. 🟢

### I. Repetition detection
Repeat rates are 0.0 on news, ai-ml, science and sports. Weekend is **0.588** (20/34), by construction: the deep read carries the week's papers forward with their story ids. A spot-check of the scheming paper (weekend importance 2, ai-ml 10-20 importance 3) and the KLS item shows the Weekend re-fetching and re-framing rather than copying. KLS gained the "two new arXiv digestions" context and an explicit note that peer review is pending. This is the deep-read mandate working. The rate is up from 0.389 because the Weekend leaned more on this week's dailies than on fresh finds. I'm watching it rather than flagging it.

News Ukraine coverage: the 10-21 Witkoff/Putin/Hubbard lead and the 10-24 Oleshky truce are distinct dated facts, and `[ongoing since]` is used where applicable.
`reconcile: 0 flagged, 0 resolved-by-merge, 24 editions checked`. 🟢

### J. Cross-week trend
See the section below.

### K. Feed reachability and direct-fetch rate
Direct-fetch ratios: news 0.984, ai-ml 0.973, science 1.0, sports 1.0, weekend 1.0. Via-snippet is 2 portfolio-wide. 🟢

**Feeds failing >50%.** The raw ratio counts the curl-first miss before every proxy success, so 29 feeds trip it. The feeds with **no or little net success** are the real list:
- `openai.com`: 11 fail / 2 proxy ok, a 403 through the proxy itself (§E).
- `physics.aps.org` 6/0, `journals.aps.org` 2/0: APS is walled from both paths.
- `api.openalex.org`: **3/0, down from 26/0.** The science writer is calling it less, apparently by its own judgment ("OpenAlex was rate-limited"), but the instruction is still in the prompt (rm-1, pending).
- No net success, low volume: actu.epfl.ch 4/0, corporate.dukehealth.org 4/0, api.github.com 2/0, bvger.ch, cases.stretto.com, doi.org, journals.aps.org, lindt-spruengli.com, news.ucsc.edu, newscenter.lbl.gov, nmag.gov, nmdoj.gov, ornl.gov, presidency.ro, president.gov.ua, psi.ch and whitehouse.gov (2/0 each). EPFL and PSI are back in the tail: this is the same Swiss-institution wall that pins science's domain count.
- Working through the proxy, despite the high raw ratios: api.crossref.org 30/28, dw.com 14/26, admin.ch 6/13, ansa.it 8/8.

**Method comparison:** curl still carries only Al Jazeera (25), SRF, Le Temps, export.arxiv.org, nature.com, claude.com (3) and a few others. Everything else is proxy. The 10-20 AI/ML Gaps line reports arXiv RSS returning **empty channels for all five categories**, with the writer falling back to the Atom API. That was a one-morning upstream quirk handled correctly. If it recurs, the preflight plan should list the Atom API first.

**Reach drift (computed):** there are **21 flips**, all copied into `proposals/registry-2026-10-25.yml`. **15 are CARRIED** from unstamped files. arxiv.org (abstract/HTML host; export.arxiv.org stays direct), lemonde.fr, rfi.fr and huggingface.co are in **all four** files from 10-04 to 10-25. The six new flips are phys.org, gfsbern.ch, svp.ch, balkaninsight.com, merck.com and unep.org (phys.org is the only one that is not a recent candidate). No judgment overrides: every entry has ≥3 proxy successes, 0 curl successes and non-transient failures. The reverse case (curl now succeeding on a `proxy` domain) does not occur.

**Domains that shouldn't be cited:** there are 0 citations of `reach: blocked`/`blocked-paywall` domains without `[via snippet]`. Bloomberg (the Nscale–Anthropic talks) was *dropped* rather than cited, which is correct. `never:` is empty, and no `reduce:` domain (france24.com, siliconangle.com) appears this week. 🟢

### L. Output volume
- **sports**: 1258 words vs 810 (+55%), with stories going from 5 to 7 (+40%). Words per story rose about 11%. A quiet week last week explains the base, so no flag.
- **weekend**: 7701 vs 7306 (+5%), with stories from 36 to 34. No flag, but words per story are creeping up and calls_mean is 127.
- **science**: 3028 vs 2993 (+1%), with stories from 12 to 14. calls_mean is **177**, the highest per story of any stream (12.6 calls/story against news 6.0, ai-ml 4.6 and weekend 3.7). The dead-host retries above (APS, Duke, UCSC, EPFL, PSI, OpenAlex) account for part of it.
- **news**: 1592 vs 1594 (flat). **ai-ml**: 3010 vs 2806 (+7%), with stories from 32 to 37.

### M. Editorial shape
- **Vendor-PR-lead share (AI/ML):** 14 of 19 non-paper items are vendor-sourced. That is up from 10/16, and the Lab-blogs and New-models sections are vendor-sourced by definition. Every item is tagged and attributed, and the "Why it matters" lines do the skeptical work: "a self-study by a firm that sells the agents, with no independent check" (Anthropic hiring), "The claims are Anthropic's own and have not yet been independently replicated" (Theorem), and "Skip the 'superintelligence' framing" (Microsoft diagnostics). Vendor framing as the *lead* happens in about 1 of 19. The KLS headline ("Microsoft researcher… announces a proof") states the claim flatly, though the body attributes the independent-verification claim to Microsoft and notes that peer review is pending. The independent items are strong: the Aachen court order, the PHP Foundation emergency release and the DeepSeek-funding press account, each labelled as what it is. Amber, unchanged. The framing discipline holds.
- **Aggregator shape (5 leads: news 10-19, 10-22 and 10-24; ai-ml 10-23; sports 10-19):** 0 failures. Nuñez is anchored on the Élysée statement via AFP/Reuters, with the ministry's revised arrest and injury counts set against Sunday's figures. Dammam is anchored on the civil-aviation authority and the State Department on record. Oleshky has the ombudsman, the General Staff and the White House, with their three start dates reconciled to Swiss time. PHP Foundation is first-party. Sports anchors on SRF Sport. Each lead adds framing the source does not contain.
- **Personalization (5 stories):** 0 misses. The Ebola case carries the Swiss embassy angle and why it matters. The SRG poll covers the VAT/AHV consequence and the age split. The PostFinance ruling (10-21) explains what it means for customers. The Apple Silicon paper ends "benchmark on your own machine before adopting a trick", a builder angle where one plausibly exists. The Dammam lead correctly carries no forced CH angle.

### N. Affiliation element
- **Coverage:** about 5 of 40 unique papers read "(affiliation not listed)": KronLSTM (the HTML numbers affiliations without naming them), arXiv 2610.31624 (power-seeking), the Apple Silicon paper (HTML failed) and the weekend's two carried items. That is about 12%, and every case is disclosed in Gaps. 🟢 Byline-to-record checks: Columbia (Yan & Hewitt) → `["Columbia University"]` ✔, Scale AI (sabotage) → `["Scale AI"]` ✔, **Zanolini "(Independent researcher)" → `affiliations: None`** ✘. The byline names the affiliation but the 10-23 Step C record omitted it. Qin "(Independent researcher)" is the same. This is minor, but it is the "byline never reached the record" pattern. The Weekend's KLS record correctly has `["Independent researcher", "Microsoft Research"]`, so the AI/ML writer is treating "Independent researcher" as no affiliation. That matters for the halo audit, which depends on it.
- **Halo audit:** the independent Zanolini paper got importance 2, above four lab-affiliated papers at 1 (Sogang/Samsung, HKUST/Huawei, UW/Anthropic, and Qin's own). The unaffiliated power-seeking paper was 2 in AI/ML. The Weekend's 1s and 2s split without any visible prestige gradient: IBM Research got 1. There is no skew. 🟢

## Prior proposals status
- `proposals/registry-2026-10-04.yml`, `-10-11.yml`, `-10-18.yml`: **pending, not applied** (all unstamped). arxiv.org, lemonde.fr, rfi.fr and huggingface.co are still `reach: direct` in `sources/registry.yml`. The last stamped registry file is `registry-2026-09-27.yml`.
- `proposals/reader-model-2026-10-18.json` rm-1 (drop the OpenAlex lookup from `routines/_shared/affiliations.md`): **pending, not applied**. The OpenAlex bullet is still at lines 16–17 of the partial, and `assemble.py check` passes, so the generated prompts match the unchanged source. The writer's own call volume fell (26 → 3), which suggests it already treats the instruction as optional. Applying rm-1 would make that explicit. I'm not re-proposing it as new.
- Last week's 7 scout candidates reached the registry as `status: candidate` but with `reach: direct` and `last_cited: 2026-10-18` (the scout date, though none was cited). See Open question 2.
- `sources/registry.yml` changed only through writer-side candidate and `last_cited` bookkeeping. It is still not strict YAML: line 1017 has an unquoted colon in a letemps.ch `note:` (`note: sports: https://…`). This was raised in the last two reviews.

## Source scout (Sunday duty)
- **Stream picked: science.** Its new-domain ratio is the lowest (2/3 = 0.67× target), against sports 4/3, weekend 30/3, ai-ml 30/10 and news 41/10. Sports (1.33×) is the runner-up and the better use of scouting next week (§A).
- **Candidates:** 10 research newsrooms not in the registry were probed: ox.ac.uk, helmholtz.de, ucl.ac.uk, imperial.ac.uk, kit.edu, tum.de, news.ku.dk, nih.gov, pasteur.fr and wmo.int. **All 10 returned `000`/ERR:56**, the egress wall and not a verdict on the sites. Six genuine institutional primaries were appended to `sources/candidates.jsonl` with `reach: proxy-needed`: ox.ac.uk, helmholtz.de, ucl.ac.uk, imperial.ac.uk, nih.gov and pasteur.fr. kit.edu, tum.de, ku.dk and wmo.int were held back to keep the bench focused. Because of the sync defect, these six will land as `reach: direct` unless Open question 2 is fixed first.
- **Re-probes** of the next 5 stalest `reach:` entries (bootstrap-only, 2026-07-07; the a–b block was done in prior weeks): blog.google, blog.newlimit.com, blogs.microsoft.com, bloomberg.com and businesstoday.in. All returned ERR:56 from this egress, which is inconclusive. Writer telemetry shows blog.google (2 proxy ok / 2 fail) and blogs.microsoft.com (1/1) working only through the proxy. Both are below the `min_proxy` 3 threshold, so they are not flipped.
- **Fetches used: 15 of 20** (10 candidates + 5 re-probes). The 8 claim-check fetches in §C are counted separately.

## Patch proposals (for human review)

**No new prompt patches this week.** The one open prompt issue is rm-1 (OpenAlex), which is pending and not re-proposed. Every other finding belongs to the registry apply step (21 flips), to tooling (the sync reach default, the builder parser shape, the YAML colon), or to egress (government, APS and OpenAI walls). Or it is a single-instance slip: the Taverne tier, and the Zanolini record field. A prompt patch would not fix any of them, and the sourcing charter is being followed.

## Reader-feedback → profile proposals
There were 4 ledger feedback events in the window (selected by event `ts`), matching health.json (ai-ml down 2, news up 2).

**Reasoned events (complete list, each with a disposition):**
- st-e0cc4bc86ef7 (ai-ml 10-20, "Reflection's Beam weights are now out under Apache 2.0"): 👎, *"some info about Beam would have been useful"*. **Deferred.** This is the only reasoned signal and it is on one story. It is below the 2-distinct-stories bar. The reader also tapped 👎 bare on the same story 11 seconds earlier, which counts as the same signal. The point is fair: the item is an `[ongoing since 2026-10-05]` follow-up that gives specs but not what Beam is for or how it compares. If a second follow-up item draws the same complaint, the proposal is a line under Learned preferences: *"`[ongoing since]` follow-ups restate in one sentence what the thing is and why it mattered the first time."*

**Bare events:** 👍 st-17f3db820237 (news 10-20, "Bern tenders the Swiss Government Cloud") and 👍 st-15a3f2e3eb53 (news 10-22, "Bern rejects urgent-credit clawback bill"). These are two distinct stories on one theme, Swiss federal governance and finance. That clears the bar on count, but there is no reason text, and it reinforces what `reader-profile.md` already makes central (Switzerland first). **Not proposed**, because the line would add nothing a writer does not already do. If the theme keeps drawing 👍, a reinforcement line could name *federal fiscal and IT procurement* specifically.

Nothing is auto-applied to `reader-profile.md`, and there is no source-weights proposal. Reader brief-proposals: no `proposals/*.jsonl` reader records exist, so there is nothing to surface.

## Machine-readable proposals
- `proposals/registry-2026-10-25.yml`: 21 reach flips (15 CARRIED) and 6 scout candidate adds, all `applied: false`.
- `proposals/reader-model-2026-10-25.json`: no new proposals. The `note` records the feedback dispositions and that rm-1 (10-18) is still pending.

## Cross-week trend
| Metric | 10-04 | 10-11 | 10-18 | 10-25 |
|---|---|---|---|---|
| news top-5 share | 0.695 | 0.691 | 0.685 | **0.662** ↓ (better) |
| ai-ml top-5 share | 0.544 | 0.618 | 0.571 | 0.547 ↓ (better) |
| ai-ml unique 30d | — | 29 | 31 | 34 ✔ |
| news unique 30d | — | — | 47 | 52 |
| science unique 30d | 5 | 4 | 4 | 4 (flat, worst) |
| sports unique 30d | — | — | 9 | **6** ↓ |
| weekend waiver rate | 1.00 | 0.80 | 0.60 | 0.60 |
| T1 citation % | — | 33% | 39% | **42%** ✔ |
| aggregator citations | 0 | 0 | 0 | 0 |
| T3 leakage | 0 | 0 | 0 | 0 |
| empty sections | 0 | 0 | 0 | 0 |
| via-snippet (portfolio) | 0 | 1 | 0 | 2 |
| reach-drift flips | 13 | 24 | 29 | 21 (15 carried) |
| link sample | 5/20 unmeas. | 6/20 unmeas. | 4/20 unmeas. | 5/20 unmeas. |
| openalex fail/ok | dead | 23/0 | 26/0 | 3/0 |

Editorial quality is steady-good. News and AI/ML diversity are improving week over week, and T1 has crossed its target. Three lines are getting worse: sports diversity (new), the unapplied registry backlog (fourth week), and science's metric (sixth week, waiting on a definitional decision).

## Open questions for human review
1. **Apply the reach flips, or grant the evaluator a bounded auto-apply for them.** Four registry files are pending (10-04 to 10-25), and four domains are in all of them. The flips are deterministic writer telemetry. The same kind of bounded grant as for learned-preference lines would close a loop that has been open for a month. This is the third week the question has been asked.
2. **Registry sync drops the candidate's reach.** `tools/sources/registry.py` (the `sync` fold, about line 455) writes `"reach": "direct"` for every new candidate, and `"last_cited": rec.get("first_seen")` even for scout entries that were never cited. Proposed fix: map the record's `reach` when present (`proxy-needed` → `proxy`), and set `last_cited` only when `via != "scout"`. Writer-tagged candidates first reached through the proxy (svp.ch, gfsbern.ch, merck.com, unep.org this week) would also stop showing up as drift a week later. This touches a spec-suite-covered module, so run `python3 -m unittest discover -s tools/tests` after the change.
3. **Builder parser shape (the §D WARN).** `strip_trailing_citations` does not peel a trailing citation run that is itself parenthesised and contains a nested parenthesis: `([arXiv:…](u) · Authors (affiliation not listed))`. The leftover ` · byline` then makes `_is_meta_para` treat the whole paragraph as meta. The fix is either to balance parentheses when stripping the trailing run, or to have `_is_meta_para` look only at the last ` · `-delimited segment. Add a golden case for `2026-10-24-weekend.md` st-5745ce974a94.
4. **Science's diversity metric** (repeated from 10-18 Q2, unanswered). Count `sources/institutions.yml` entries, or the paper-plus-institutional-release pair, rather than anchor hosts? Until this is decided, science stays red and the Sunday scout keeps picking it, while its candidates are never cited by design. Suggestion: pick sports next week either way.
5. **Sports factual slip:** "third-tier Taverne" should be fourth-tier (1. Liga). It is one instance and I'm not patching it. If Swiss league-tier labels go wrong again, a one-line tier map (Super League / Challenge League / Promotion League / 1. Liga) in the sports stream body would remove the guesswork.
6. **Test suite in this sandbox:** 792 tests, the same 3 failures (ledger and fold permission tests that cannot fail when running as root). This is an environment artefact, unchanged. `assemble.py check` is OK on all five generated prompts.
7. **`sources/registry.yml` line 1017** has an unquoted colon (`note: sports: https://www.letemps.ch/sport.rss …`) that breaks strict YAML parsers (PyYAML fails). The repo's own loader tolerates it. Quoting it is a one-character fix, raised for the third week.
