---
layout: single
title: "Weekly Pipeline Review — 2026-11-15"
date: 2026-11-15T11:47:47+01:00
categories: [evaluator]
published: true
---

# Weekly Brief Pipeline Review — 2026-11-15

_Coverage: briefs from 2026-11-09 to 2026-11-15._
_Files read: 6 news, 2 AI/ML (expect ~2), 1 science (expect ~1), 1 sports (expect ~1), 1 weekend (2026-11-14), prior review found (2026-11-08, 7 days old)._

All eleven expected editions ran. Sunday's News has not fired yet, which is normal. Every edition carries a Discovery footer: 8 met, 3 waived. Aggregator leakage, T3 leakage, identity-reconcile flags, off-main commits and the feedback backlog are all zero. All 8 claim spot-checks matched their sources. Every edition has exactly one importance-3 story. **AI/ML top-5 outlet share fell to 0.439, the first time any multi-edition stream has been under the 0.50 bar.** News improved for the seventh straight week, to 0.608.

Four items need attention:

1. **News single-sourcing rose to 28.3% (17/60), over the 25% per-stream bar.** The cause is a prompt line. The shared partial says "cite no outlet domain more than twice in one edition", and the writers apply it to every link, including corroborating second links. On 11-12 the Kohat attack was dropped because "Al Jazeera had reached the per-edition outlet cap". On 11-10 an SRF item was cut "to keep SRF to two citations". Only SRF, Al Jazeera and Le Temps reach by curl, so the cap removes the cheapest corroboration. The publish lint already counts only a story's first link. Patch 1 makes the prompt match it.
2. **Sports thinned out.** It had 5 items, 839 words (−31%) and **T1 = 0 of 5 citations**. The discovery waiver reads "official sites on the fetch list were not fetched". That is a non-attempt, not a reason, and the fetch log confirms that no league or federation host was tried. Sports is the worst stream for diversity for the third week: 4 unique domains in 30 days, srf.ch at 48% and bbc.co.uk at 30% of citations. Patch 2 addresses the waiver. Last week's hockey patch is still **pending, not applied**.
3. **The registry backlog is in its seventh week.** There are 19 computed reach flips, 16 of them carried from unstamped files. arxiv.org, lemonde.fr, rfi.fr and huggingface.co are in **all seven** files from 10-04 to 11-15. The registry-sync default is unchanged: all 10 of this week's newly registered `[new source]` domains landed as `reach: direct`, although every one was reached through the proxy.
4. **The OpenAlex lookup now costs real calls.** api.openalex.org went **42 fail / 0 ok** (18 HTTP 429 in Science alone). The 10-18 proposal to drop it is still pending, and this is the first week it has cost anything.

## Health summary

| Metric                          | Value | Target | Status |
|---------------------------------|-------|--------|--------|
| Unique domains 30d (worst stream vs its tier, source-health) | **sports 4**, science 5 (news 63, weekend 46, ai-ml 34) | ≥30 news/ai-ml · ≥10 weekly | 🔴 |
| New domains this window (portfolio, source-health) | 17 `[new source]` tags. 30-day: news 46, weekend 31, ai-ml 25, science 3/3, **sports 1/3** | ≥2–3/wk (≥10/mo) | 🟡 |
| Top-5 outlet share (worst of news/ai-ml, source-health) | news **0.608** (ai-ml **0.439** ✔) | ≤0.50 (→0.35); weekly report-only | 🔴 |
| Waiver rate (worst stream, source-health) | science 0.50, sports 0.50 (weekend 0.40, ai-ml 0.11, news 0.10) | ≤50% | 🟢 |
| Discovery footer present (every brief) | 11/11 (8 met, 3 waived) | 100% | 🟢 |
| T1 citation %                   | 63.9% of story anchors (92/144, writer-recorded tiers) | ≥40% | 🟢 |
| T3 leakage count                | 0 | 0 | 🟢 |
| Non-English citation % (portfolio) | ~29% (56/190 body links, host/path heuristic) | ≥10% | 🟢 |
| Link sample pass rate           | 4/20; recap 4/8. **Unmeasurable**: every failure is egress ERR:56, with no 404s | ≥90% | ⚪ |
| Fabrication count               | 0 | 0 | 🟢 |
| Single-source rate (portfolio)  | 18.1% (26/144). **news 28.3%**, science 36.4% (papers, see §F) | <20% (<25%/stream) | 🟡 |
| Empty section instances         | 1 (sports "🧠 Why it matters", a one-bullet section; see §D) | <5 | 🟢 |
| Reading-surface flags (§D, surface.py) | 2: 1 SHORT (11-13 ai-ml, 5 cards against a floor of 6), 1 WARN carried from 10-31; 0 parity, 0 overdue | 0 | 🟡 |
| Repeat rate (worst stream, health.json) | weekend 0.59 (22/37, up from 0.31); all others 0.0 | judge | 🟡 |
| Direct-fetch ratio (portfolio)  | 0.99 (143/144); sports 0.80 | ≥0.35 | 🟢 |
| Feeds with >50% fail rate       | 29 by the raw ratio. With no success at all: api.openalex.org 42/0, bbc.co.uk 8/0, doi.org 8/0, president.gov.ua 7/0, plus a 1–3/0 tail. Mostly failing: science.org 19/2, rfi.fr 20/13 | 0 | 🟡 |
| Citations on `reach: blocked` domains without [via snippet] | 0 (the registry has no `blocked` entries) | 0 | 🟢 |
| Unconsumed feedback backlog (health.json) | 0 | 0 | 🟢 |
| Vendor-PR-lead share (AI/ML, §M) | 7/14 non-paper items lead with the vendor's own post. 4/14 (29%) have no independent source at all, all in 11-13 | ≤40% | 🟡 |
| Aggregator-shape failures (§M, of 5) | 0 | 0–1 | 🟢 |
| Personalization misses (§M, of 5) | 0 | 0–1 | 🟢 |
| Affiliation coverage (§N) | 2 of ~40 paper bylines "not listed" (~5%) | <20% | 🟢 |
| Halo audit (§N) | no prestige skew | — | 🟢 |

## A–N: Detailed findings

### A. Source diversity & discovery
From `source-health.json` (30-day windows):

- **news**: 63 unique domains (65), 46 new, waiver rate 0.10, nothing saturated. Top-5 share is **0.608**, down from 0.643, the seventh straight improvement and the largest weekly drop yet. Five of six editions met discovery with first-party primaries: unia.ch (the union's own Just Eat release), astra.admin.ch (the roads office's condition page), news.met.police.uk and ccpi.org, irish-presidency.consilium.europa.eu, and iletisim.gov.tr (Türkiye's communications directorate, the defence-pact document list). Radio Tamazuj was also tagged on 11-14. It is a regional outlet, honestly not claimed for discovery. The 11-12 waiver is concrete: the Kremlin feed had no readout yet and the Indonesian presidency feed came back empty. This is the pattern working.
- **ai-ml**: 34 unique (31), 25 new, waiver 0.11, top-5 **0.439** (0.517). **This is the first stream to clear the 0.50 "now" bar.** Both editions met discovery: nousresearch.com (11-10) and pm.gov.au (11-13, Australia's frontier-AI announcement). renaissancecapital.com is tagged too. It is an IPO-data firm, not a primary for Anthropic's terms, and is not claimed for discovery (see §G).
- **science**: 5 unique (5), 3 new, top-5 1.00, nature.com saturated, waiver 0.50. 11-11 was **waived honestly**: biham.unibe.ch was anchored against a quota of two, and unibe.ch, insel.ch, psi.ch, Carnegie, AWI and MPIA were probed and named. The cap on this stream is reachability, not effort. science.org and nejm.org both fail through the proxy, so journal coverage falls back on Crossref abstracts and HCPLive. No patch.
- **sports**: **4 unique (4), 1 new, top-5 1.00, srf.ch and bbc.co.uk saturated** (autosport.com dropped off the saturated list). It is the worst stream for the third week. The 11-09 waiver says the official sites "were not fetched", and the fetch log agrees: the only hosts tried were srf.ch, bbc.co.uk/feeds.bbci.co.uk, autosport.com, kicker and wikipedia, and 31 research calls were logged. The 11-02 edition probed five primaries before waiving. This one tried none. Patch 2.
- **weekend**: 46 unique (46), 31 new, waiver 0.40. It met discovery with psi.inc (the lab's own research page for the Aaronson–Ambainis proof) and mathhelm.org. Dormant probes are named: noemamag.com was reached, republik.ch was not.

**Tier distribution:** from writer-recorded anchor tiers in `index/stories/` (the same method as last week), 92 of 144 anchors are T1 (**63.9%**, 62.9% last week) and 52 are T2, with **no T3**. 🟢

**Linguistic/geographic:** about 29% of body links are non-English (SRF, Le Temps, Le Monde, RFI, El País, ANSA, tagesschau, admin.ch/fr, vd.ch, kicker). Countries covered alongside Switzerland include the US, Ukraine/Russia, Iran/Israel, Qatar/Türkiye, Hungary, South Sudan, Indonesia, Pakistan, Algeria/France, Spain, Australia and China.

### B. Aggregator leakage
`briefs.aggregator_leakage` is **empty**. 🟢

### C. Link health: unmeasurable (egress wall), no fabrication found
`linkcheck: 4/20 resolve (2xx/3xx) — window [2026-11-09, 2026-11-15], 163 links total.`
`linkcheck: recap 4/8 resolve (2xx/3xx) — Weekend "Week in headlines", always checked.`

All 16 sample failures and all 4 recap failures are **ERR:56**: the egress proxy refused the CONNECT to admin.ch, arXiv, unibe.ch, psi.inc, hcplive, tagesschau, deepmind.google, doi.org, nature.com, euronews, rfi.fr and nvidianews. **There are zero HTTP 404s and zero fabrication candidates.** Every failing recap host shows proxy successes in the writers' own logs that week (admin.ch 23 ok, rfi.fr 13 ok, nvidianews 6 ok, euronews 2 ok). Every host reachable from here (SRF, Al Jazeera, Le Temps) resolved 200. This is the ninth straight week the dimension is unmeasurable.

**Claim spot-checks (8, on reachable hosts): 8 consistent.**
- Trump–Xi–Putin meeting (11-14 news, Le Temps): Le Temps's headline says "le 21 novembre", but its body says "jeudi prochain", which from Friday 13 November is the 19th. The brief chose the 19th, flagged the conflict in its Gaps line and cross-checked a second report. ✔ That is how a source conflict should be handled.
- Qatar–Türkiye pact (11-14 news, Al Jazeera): common position against external armed attack, Supreme Strategic Committee in Istanbul, "deter rather than offensive". All match. ✔
- South Sudan election (11-14 news, Al Jazeera): 11 February poll, registration 14–28 November, campaign 27 December – 9 February. All match. ✔
- US soldier arrest (11-11 news, SRF): 41-year-old, National Security Act, Russia link, Patel's "utmost concern", Army CI command quote. All match. ✔
- Eternit/Schmidheiny (11-11 news, SRF): the Cassation quashed the 9½-year sentence for 91 deaths, 1976–1986 tenure. Matches. ✔
- Thun 3–3 Basel (11-09 sports, SRF): Celar after 40 s, Otele 2–0 in the 12th minute, Omlin's dribble, Rüegg own goal in the 78th, Basel "unter dem Strich" one place ahead of Thun, Lugano 0–5, Servette–FCZ goalless. All match. ✔
- Alcaraz Paris (11-09 sports, SRF): 7–6(5), 7–5 over Shelton, 7 of 9 Masters titles, Canada and Shanghai missing, US Open revenge. All match. ✔
- Swiss hockey in Helsinki (11-09 sports, SRF): 1–3, 2–4, 2–4, 0 points, 5–11, no win since 6–0 over Norway on 30 May, Cadieux's young squad. All match. ✔

### D. Section vitality + reading surface
`empty_sections` has **one entry**: `2026-11-09-sports.md` "🧠 Why it matters". The section holds one synthesis bullet with no citation, so this is the counter's shape rule (no cited item) rather than an empty desk. It is not a finding. No desk was empty three times. 🟢

**Reading surface:** `surface: 2 flag(s) -- 0 parity miss(es), 1 lede-fallback WARN(s), 0 overdue desk(s)`
- `FLAG SHORT 2026-11-13-ai-ml: newest edition shows 5 card(s) of 15 stories (floor 6)`. The feed was regenerated on 11-14 by the News and Weekend runs, and both 11-14 editions took 9 cards each. The 11-13 AI/ML edition, still the newest AI/ML edition, was cut to 5, under its own floor. This is a builder allocation outcome, not a writer error: the post has 15 parseable stories and 0 unmapped. The builder should not let a newer desk push another desk's newest edition under its floor. Open question 3.
- `FLAG WARN _posts/2026-10-31-weekend.md st-c71b778862b5`: carried. **The other five carried WARNs have aged off**, and no edition in this window trips one.

### E. Coverage gap recurrence
Gaps clusters this week (≥3 = structural):
- **Kremlin / Ukrainian presidency primaries not fetched (4 editions: 11-09, 11-12, 11-13, 11-14).** president.gov.ua went 7 fail / 0 ok, including through the proxy. en.kremlin.ru worked once via the proxy (11-12) but had no readout. Peace-talk items rested on Le Monde, DW and Al Jazeera. 🔴 This is structural, and it is the same fetch-Worker egress wall as last week's election sites (Open question 4).
- **Journal full text unreachable (science 11-11, weekend 11-14): science.org 19/2, nejm.org 2/0.** The Weekend **cut** three Science papers that the 11-11 edition had covered "rather than cited unread". That is the right call, and it also explains why the Weekend's fundamental-science picks came entirely from arXiv, Nature and AAS.
- **arXiv RSS empty or truncated (both AI/ML editions plus weekend).** On 11-10, cs.LG, cs.AI, cs.CV and stat.ML returned empty item lists. On 11-13 all five did. The writers fell back to the Atom API, which on 11-13 swept only three categories and only partly covered 10 November. That is a real coverage hole. It is also why the Weekend took 6 of its 8 ML papers from the AI/ML editions (§I).
- **openai.com article pages (2nd consecutive cluster):** 4 fail / 2 ok. The 11-10 Control Room and wet-lab-evaluation posts went uncovered. The 11-13 edition anchored on alignment.openai.com, which works.
- **Official sports sites not fetched (sports, 6th consecutive week):** this week they were not even tried (Patch 2).

### F. Triangulation rate
Portfolio: 26 `[single-source]` of 144 citations (**18.1%**). By stream: **news 0.283 (17/60)**, science 0.364 (4/11), ai-ml 0.097, weekend 0.054, sports 0.0.
- **News** is over the 25% bar for the first time since the tiered targets started. Of the 17, about five are honest Swiss scoops or institutional items (the SRF Olympics-bid guarantee, the Rohner fine order that "is not public", the AFBS survey). Another five are blocked primaries (France's summons of Iran's ambassador, the House roll call, the Massie articles). The rest are widely reported stories carried by one outlet, such as Trump's "positive momentum" on Iran and the Mississippi Senate call, where a second link was cheap. Two Gaps lines show the outlet cap suppressing corroboration directly (11-10, 11-12). Patch 1. 🟡
- **Science**'s 4 are Science-journal papers whose abstracts came via Crossref because science.org was unreachable, and which had no independent coverage. For a paper, the paper is the primary, so this is a reachability symptom, not a sourcing defect.

### G. Tag discipline
Counts from `health.json`: ai-ml preprint 17, vendor PR 7, new source 3, single-source 3. News official PR 16, new source 8, single-source 17, disputed 1. Science new source 2, preprint 1, single-source 4. Weekend preprint 17, vendor PR 6, new source 4, official PR 1, disputed 1. Sports via snippet 1.
- `[preprint]`: all 17 AI/ML arXiv items carry it. I sampled 5 Weekend arXiv entries (2611.16510, 2611.17300, 2611.13560 and two RL papers) and all are tagged. ✔
- `[vendor PR]`: Fable/Mythos 5.2, Muse Ember, Arete-27B, OpenAI CoT monitorability, AlphaProof Code, Gemini 4 Hydrogen and Inkling 2 are all tagged, consistently across AI/ML and Weekend this week (last week's Astra mismatch did not recur). ✔ The Nvidia "Message to Our Company" and CEO-transition releases are untagged, which is right: they are corporate acts, not product claims.
- `[disputed]`: two uses (news, weekend). The weekend use is on the Domingos "quantum supremacy is dead" claim that Aaronson rebuts, which is appropriate.
- `[new source]` spot-checks (2): **iletisim.gov.tr** is a genuine primary (the Turkish presidency's communications directorate listing the signed documents). ✔ **renaissancecapital.com** is a data firm's write-up of an S-1/A. It is a secondary, not a primary for the IPO terms, and the Gaps line admits that EDGAR was not fetched. It was not claimed for discovery, but this is the second week of a non-primary carrying the tag on an AI/ML money story (adweek.com last week). Watch.
- **Subdomain novelty (new observation):** astra.admin.ch (news 11-10), biham.unibe.ch (science 11-11) and irish-presidency.consilium.europa.eu (news 11-13) were claimed as `[new source]` discoveries. Each is a subdomain of a registered domain (admin.ch, unibe.ch, consilium.europa.eu). The lint scores novelty by full host, so they pass, but the registry sync folds them into the parent, so **none was registered** (none is in `sources/registry.yml`). Each is a genuine primary, so the editorial outcome is fine. The bookkeeping, though, lets the same host be claimed as new again next time. Open question 5.
- `[via snippet]`: **1** (sports, Forest–City, BBC article 403). Last week there were 0. It is flat-low. 🟢

### H. Topic balance (weekend)
`ml_items 16 / science_items 16`, `ml_share` **0.50**, inside [0.35, 0.65]. 🟢

### I. Repetition detection
Repeat rates are 0.0 for news, ai-ml, science and sports. The weekend rate is **0.595 (22/37)**, up from 0.314. By section, the shared ids are: headlines 5/6, ML papers 6/8, models 4/4, data science 2/2, biology 2/3, essays 1/4, Apple 1/2, fundamental-science papers **0/8**. The Weekend's own dedup is scoped to prior Weekends by design (`--only-slug weekend`), so re-running the week's items is the brief's job. The rise has two causes. One is the arXiv feed failure: the Weekend says it took 7–9 November ML papers "from the AI/ML sibling briefs plus a re-fetch of their abstracts". The other is the "Models & datasets" desk, whose four items are near-restatements of the AI/ML items with no new dated fact. The cross-cutting thread ("RL teaches whatever the reward actually pays for", across seven papers) is genuine added synthesis. Verdict: by construction, not a defect, but see §L.

**Identity integrity:** `reconcile: 0 flagged, 0 resolved-by-merge, 24 editions checked`. 🟢

### J. Cross-week trend
See the trend table below.

### K. Feed reachability and direct-fetch rate
**Per-stream:** `direct_fetch_ratio` is 1.0 for news (60/60), ai-ml (31/31), science (11/11) and weekend (37/37), and **0.80 for sports (4/5)**, the one BBC snippet. All streams are above their ranges. 🟢

**Per-feed (method comparison):** curl carries only srf.ch, aljazeera.com (30 ok / 5 fail), letemps.ch and export.arxiv.org. **Everything else rides the proxy**, which is the steady state. The feeds with no or almost no success:
- **api.openalex.org 42/0** (18 of them HTTP 429): pure waste. See Prior proposals.
- **bbc.co.uk 8/0**: 4 ERR:56 plus 4 HTTP 403 *through the proxy*, so the proxy does not reach BBC article pages either. feeds.bbci.co.uk RSS works via the proxy.
- **doi.org 8/0**: the publisher behind the redirect is what fails (mostly science.org).
- **president.gov.ua 7/0**, plus ebrd.com, diplomatie.gouv.fr, elections.org.za, wto.org, tccb.gov.tr, nejm.org, psi.ch, mpia.de, gea.mpg.de and newscenter.lbl.gov at 2/0. These are government and institutional hosts where both curl and the proxy fail: **the fetch Worker's egress is the wall.**
- **science.org 19/2, rfi.fr 20/13 (4 HTTP 404 on 11-13), api.crossref.org 19/17**. Crossref is the 1-curl-fail-then-proxy-ok pattern, so the chain is working.

**Reach drift (computed):** there are **19 flips**, all copied into `proposals/registry-2026-11-15.yml`. **16 are CARRIED**, and arxiv.org, huggingface.co, lemonde.fr and rfi.fr have been in every file since 10-04. The **3 new** flips are unibe.ch (8 proxy ok, including biham.unibe.ch), nvidianews.nvidia.com (6) and tagesschau.de (6). There are no judgment overrides. The carried `openai.com → blocked` flip stays in the file. The carried bbc.co.uk registration is **revised to `reach: blocked`**, because this week's 403s came through the proxy. doi.org gets a watch note, not a flip. The reverse case (curl now succeeding on a `proxy` domain) does not occur.

**Domains that shouldn't be cited:** 0. The registry holds no `reach: blocked` entries and `source-weights.yml` has `never: []`. No retired or demoted domain appears as an anchor. 🟢

### L. Output volume
Mean words (this week vs last): news 1500 vs 1629 (−8%), ai-ml 3019 vs 2794 (+8%), science 2852 vs 2985 (−4%), **sports 839 vs 1218 (−31%)**, **weekend 7778 vs 6423 (+21%)**. No stream grew more than 25%. 🟢 The Weekend is the one to watch. It grew 21% on 37 stories against 35, it is the most repetitive stream (§I), and it logged 160 calls. Per the token-levers SPIKE, it is the prime candidate if spend needs trimming. The cheapest lever is a one-line pointer to the AI/ML edition for "Models & datasets" items with no new fact. It is not proposed this week because the growth is under the threshold. The sports drop is a quality signal, not a saving (§A).

### M. Editorial shape
- **Vendor-PR-lead share (AI/ML):** there were 14 non-paper items (6 on 11-10, 8 on 11-13), and 7 lead with the vendor's own post. Three of those add an independent check: Fable/Mythos (TechCrunch's system-card quote), Muse Ember (Simon Willison's hands-on) and Arete (Hugging Face artefacts). **Four have no independent source at all, and all four are in 11-13**: OpenAI's CoT-monitorability post, AlphaProof Code, Gemini 4 Hydrogen and Inkling 2. That puts vendor-only leads at **4/14 (29%) for the week**, but 4/8 in the 11-13 edition, against ~17% last week. Each has a candid "the data are the vendor's own" line, which is the minimum. It is not patched yet (one edition), but it gets a patch if 11-17 and 11-20 repeat it. 🟡 The best items were independent: Ars Technica's Claude Code secret-leak story (with concrete remediation), Australia's frontier-AI announcement anchored on pm.gov.au, and the Fireworks/Notion breach.
- **Aggregator-shape check (5 leads):** I sampled the Qatar–Türkiye pact (iletisim.gov.tr + AJ), the Vaud strike legality (vd.ch with a "government's reading, not a court's" frame), the IEA surplus with the UN seafarers figure (iea.org + UN), the Met Police arrest (met.police.uk) and the STREAM statin trial (Insel/NEJM via HCPLive + Crossref). All five anchor a primary and add framing the source lacks. **0 failures.** 🟢
- **Personalization (5 stories):** I sampled the Qatar emir's Bern visit (energy and good-offices angle, tied to the pact), the STREAM trial (Bern-led, Swiss sites), the Claude Code leak (a concrete `.gitignore` action for builders), Inkling 2 ("too large for a Mac", a local-inference angle) and the Hungarian cash find (no CH angle forced, correctly). **0 misses.** 🟢
- **Follow-up on last week's Open question 1 (chain-of-thought framing):** without any profile change, both AI/ML editions and the Weekend now describe CoT as "the model's written reasoning" or "reasoning text a model writes". The 11-13 lead is OpenAI's own finding that CoT is becoming *less* reliable to monitor. The framing the reader objected to did not recur. The open question can stay open, but the urgency has dropped.

### N. Affiliation element
- **Coverage:** 2 of about 40 paper bylines read "not listed" (~5%): the Euclid collaboration DR1 overview (a collaboration paper, explained in Gaps) and one Weekend entry. AI/ML 0/17, Science 0/12. I spot-checked three bylines against `index/stories/`: MATS/Google DeepMind (reward-hacking evasion), Stevens/UMass Boston (Arena drift) and Carnegie Science (iron melting) all reached `affiliations`. 🟢
- **Halo audit:** small or independent labs sit at importance 2 (Incubilate/UMass, PayPal, CUHK, Prefrontal at 1). A MATS/Anthropic paper was demoted from 2 to 1 in the Weekend, as was the UK AISI one. The two no-affiliation items sit at 1 and 2. **No prestige skew.** 🟢

## Prior proposals status
- `proposals/registry-2026-10-04.yml` through `-11-08.yml` (6 files): **pending, not applied**. All are unstamped. The carried domains are still `reach: direct` in `sources/registry.yml`, openai.com is still `established`/`direct`, and bbc.co.uk is still unregistered. The last stamped registry file is still `registry-2026-09-27.yml`.
- `proposals/reader-model-2026-11-08.json` rm-1 (Sports: check the Swiss hockey round every in-season edition): **pending, not applied**. `routines/src/sports.md:78` is unchanged. This week's edition did carry a hockey item (the national team at the Euro Hockey Tour). The National League was on its international break, so this week neither supports nor weakens the patch.
- `proposals/reader-model-2026-10-18.json` rm-1 (drop the OpenAlex lookup from `routines/_shared/affiliations.md`): **pending, not applied**. The bullet is still at lines 16–17. **It now costs calls:** 42 fail / 0 ok this week, mostly HTTP 429 in the 11-11 Science run (218 calls logged, the highest of any edition). Not re-proposed as new, but escalated (Open question 1).
- Last week's Open questions: the registry-sync reach default is unchanged (`tools/sources/registry.py:406` and `:455` still write `"reach": "direct"`), and all 10 of this week's new candidates are `direct`. `sources/registry.yml` line 1017 still breaks strict YAML (`ScannerError … line 1017, column 19`, sixth week). The builder WARN shapes produced no new instances.

## Source scout (Sunday duty)
- **Stream picked: sports.** Its new-domain ratio is the lowest (1/3 = 0.33× target), against science 3/3 = 1.0×, ai-ml 2.5×, news 4.6× and weekend 10×.
- **Candidates:** last week established that the bench (about 45 fetch-list domains, about 35 `candidates_to_try`) is not the constraint. So this week I looked only for genuine primaries that are absent from the registry and match named desks or Swiss interest. I probed 9 directly; all returned ERR:56 from this egress, which is inconclusive and not a site verdict. **6 were appended to `sources/candidates.jsonl` with `"reach": "proxy-needed"`**: swissunihockey.ch (the Swiss floorball federation), championshockeyleague.com (Swiss NL clubs compete), nhl.com (the named NHL desk), uci.org, biathlonworld.com (IBU, whose World Cup opens late November) and swiss-athletics.ch. swissvolley.ch, swiss-cycling.ch and handball.ch were probed but not appended, because they fit the desks less well.
- **Re-probes** of the next 5 stalest `reach:` entries (bootstrap-only, 2026-07-07, alphabetically after last week's block): deploymentsafety.openai.com, devops.com, digital-strategy.ec.europa.eu, dnhkng.github.io and doi.org. All five returned ERR:56 from here, which is inconclusive. Writer telemetry adds context. deploymentsafety.openai.com worked via the proxy last week. doi.org went 8 fail / 0 ok in writer logs, but the failure is the publisher behind it, so it gets a watch note, not a flip.
- **Fetches used: 14 of 20** (9 candidate probes + 5 re-probes). The 8 claim-check fetches in §C are counted separately.

## Patch proposals (for human review)

### Patch 1 — The outlet cap counts anchors, not corroborating links
**Target prompt:** all writers, via the shared partial (`routines/_shared/feed-first-source-order.md`, then `python3 routines/assemble.py`)
**Section affected:** "Pressure" bullet
**Issue:** The writers read "cite no outlet domain more than twice" as a per-link limit. They drop stories (Kohat, 11-12) and cut items (Bund drone duty, 11-10) or leave them single-sourced rather than add a third SRF or Al Jazeera link. News single-sourcing rose to 28.3%. The lint already counts only a line's first link.
**Proposed change:**

> **Before:**
> ```
> but when two sources carry the same story, prefer the unsaturated one, and cite no outlet domain more than twice in one edition (hubs exempt).
> ```
>
> **After:**
> ```
> but when two sources carry the same story, prefer the unsaturated one, and anchor no more than two stories in one edition on the same outlet domain (hubs exempt). The cap counts ANCHORS (a story's first link) only: a second, corroborating link to a capped outlet is always allowed, and is never a reason to drop a story or leave it [single-source].
> ```

**Why this helps:** It restores cheap corroboration from the three curl-reachable outlets without loosening the anchor diversity the top-5 share measures. It also brings the prompt in line with `tools/sources/lint.py`.
**Risk:** SRF's and Al Jazeera's link share may rise slightly in body text. That does not move `top5_share`, which is anchor-based. A writer might also read it as permission to pile on links. The "corroborating" wording limits it to second sources.

### Patch 2 — A sports discovery waiver must name what was tried
**Target prompt:** Sports (`routines/src/sports.md`, then `python3 routines/assemble.py`)
**Section affected:** `## Coverage footer` (the Discovery line template)
**Issue:** On 11-09 the waiver read "official sites on the fetch list were not fetched". The edition tried no league or federation page, cited T1 = 0 of 5, and the stream has been the worst for diversity for three weeks.
**Proposed change:**

> **Before:**
> ```
> - Discovery: {met (<new domain(s) anchored>) | waived — <concrete reason>}
> ```
>
> **After:**
> ```
> - Discovery: {met (<new domain(s) anchored>) | waived — <concrete reason>}
>   (A waiver must name at least two official league/federation pages from the fetch list that you actually tried this run, via the proxy, and what each returned; "not fetched" is not a reason.)
> ```

**Why this helps:** It turns the waiver back into evidence of an attempt, and it makes the writer touch T1 primaries (sfl.ch, sihf.ch, fis-ski.com and others), which is what moves both T1 share and unique domains.
**Risk:** It adds about two proxy fetches per edition. If the template line is machine-parsed, the parenthetical must stay on its own line so the footer lint still sees exactly one `- Discovery:` line.

No other prompt patches. The rest sits in the registry apply step, registry-sync tooling, the feed builder and the fetch Worker's egress, and a prompt patch fixes none of them.

## Reader-feedback → profile proposals
**Reasoned events in window (by event `ts`, 2026-11-09..11-15): 0.** One bare 👍 (reason `""`) was cast at 2026-11-09T12:53Z on st-1be4fb668f8e (news 11-09, Trump's CBS interview on deportation policy), so there is nothing to dispose of. `health.json`: `feedback.by_stream` = news up 1, down 0, retractions 0; `unconsumed_total` 0.

No reader feedback with a reason this week. Nothing was auto-applied to `reader-profile.md`, and there is no source-weights proposal. **Reader brief-proposals:** there are no `proposals/*.jsonl` reader records, so there is nothing to surface.

## Machine-readable proposals
- `proposals/registry-2026-11-15.yml`: 19 computed reach flips (16 CARRIED, 3 new), the carried `openai.com → blocked` judgment flip, the carried bbc.co.uk registration (revised to `reach: blocked`), and a doi.org watch note. All are `applied: false`.
- `proposals/reader-model-2026-11-15.json`: rm-1 = Patch 1 (`routines/_shared/feed-first-source-order.md`) and rm-2 = Patch 2 (`routines/src/sports.md`), both `applied: false`. Its `note` records the bare-vote feedback and the two pending prior proposals.

## Cross-week trend
| Metric | 10-18 | 10-25 | 11-01 | 11-08 | 11-15 |
|---|---|---|---|---|---|
| news top-5 share | 0.685 | 0.662 | 0.653 | 0.643 | **0.608** ↓ (better) |
| ai-ml top-5 share | 0.571 | 0.547 | 0.548 | 0.517 | **0.439** ↓ (under the bar) |
| news unique 30d | 47 | 52 | 58 | 65 | 63 → |
| ai-ml unique 30d | 31 | 34 | 33 | 31 | 34 ↑ |
| science unique 30d | 4 | 4 | 7 | 5 | 5 → |
| sports unique 30d | 9 | 6 | 4 | 4 | **4** → (worst) |
| weekend waiver rate | 0.60 | 0.60 | 0.60 | 0.40 | 0.40 → |
| news discovery met | — | — | 4/6 | 6/6 | 5/6 |
| T1 citation % (anchors) | — | — | — | 62.9% | 63.9% |
| news single-source | — | — | — | 21.8% | **28.3%** ↑ (worse) |
| aggregator citations | 0 | 0 | 0 | 0 | 0 |
| T3 leakage | 0 | 0 | 0 | 0 | 0 |
| empty sections | 0 | 0 | 0 | 0 | 1 (shape artefact) |
| surface flags | 1 | 1 | 6 | 6 | 2 (1 SHORT new, 1 WARN carried) |
| via-snippet (portfolio) | 0 | 2 | 1 | 0 | 1 |
| weekend repeat rate | — | — | — | 0.31 | **0.59** |
| reach-drift flips | 29 | 21 | 23 | 19 | 19 (16 carried) |
| link sample | 4/20 unmeas. | 5/20 unmeas. | 3/20 unmeas. | 5/20 unmeas. | 4/20 unmeas. |
| claim checks consistent | — | — | 8/8 | 8/8 | 8/8 |
| api.openalex.org fail/ok | — | — | — | 0/0 | **42/0** |

The writing on the operator's primary lens keeps improving: AI/ML has cleared its "now" diversity bar and News is closing on it. The two regressions this week both come from prompt wording, and both are cheap to fix: the outlet cap suppressing corroboration (Patch 1), and the sports waiver that permits not trying (Patch 2). The non-writing backlog is unchanged for its seventh week: unstamped registry files, the sync reach default, the YAML colon, and now the live OpenAlex waste.

## Open questions for human review
1. **Apply the 10-18 OpenAlex removal.** It is one bullet in `routines/_shared/affiliations.md` (lines 16–17). This week it cost 42 failed calls and pushed Science to 218 logged calls, the highest of any edition. Affiliations came out fine without it (0/12 "not listed" in Science), so the lookup adds cost and no value.
2. **Apply the reach flips, or grant the evaluator a bounded auto-apply for computed `briefs.reach_drift` flips.** This is the sixth time I have asked. Four domains have been in all seven files since 10-04. Pair it with the sync fix that keeps producing new ones: `tools/sources/registry.py:406/:455` should map `proxy-needed` → `proxy`, set `proxy` for writer `[new source]` domains first reached through the proxy, and set `last_cited` only when `via != "scout"`. Then run `python3 -m unittest discover -s tools/tests`.
3. **Builder: per-desk floor for the newest edition.** On 11-14, two same-day editions took 9 cards each and pushed the newest AI/ML edition (11-13) to 5 cards, under its floor of 6. The fix belongs in `tools/build_stories_feed.py`'s allocation: reserve each desk's newest-edition floor before distributing the rest. It is a decision for the builder, not the Liquid.
4. **Government primaries behind the fetch Worker's egress wall.** This week it was president.gov.ua (7/0), en.kremlin.ru (intermittent), diplomatie.gouv.fr, ebrd.com, wto.org and tccb.gov.tr. Last week it was the election commissions. Together with bbc.co.uk returning 403 through the proxy, this is now a stable class. Is a second egress path worth having (a different Worker region, or a search-API cached copy recorded as `[via snippet]`)? Or is outlet-sourcing for this class accepted? The writers disclose it honestly every time.
5. **Subdomain novelty.** astra.admin.ch, biham.unibe.ch and irish-presidency.consilium.europa.eu counted as `[new source]` discoveries (lint scores by full host), but the sync folds them into their registered parents and none was registered. Decide one rule. Either a new subdomain of a registered institution counts as discovery and gets its own registry entry, or it is "dormant/registered" and must not carry the tag. Right now both tools are self-consistent, but they disagree with each other.
6. **Test suite in this sandbox:** 820 tests, the same 3 failures (the ledger and fold permission tests cannot fail when running as root) and 2 skipped. This is an environment artefact, unchanged. `assemble.py check` is OK on all generated prompts.
7. **`sources/registry.yml` line 1017**: the unquoted `note: sports: https://…` still breaks strict YAML. Sixth week.
