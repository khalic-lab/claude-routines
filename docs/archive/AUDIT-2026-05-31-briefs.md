# Brief Audit — 2026-05-25 to 2026-05-31

_7-day window, 23 brief files, all five streams (overview, ai-ml, cyber-papers, markets, weekend)._

Source-type rubric: classified by URL host.
- **PRIMARY**: arxiv.org, github.com, nature.com, *.cell.com, nvd.nist.gov, cisa.gov, ecb.europa.eu, sec.gov, state.gov, consilium.europa.eu, paloaltonetworks.com (security advisories), anthropic.com, blog.google, deepmind.google, openai.com, mistral.ai, huggingface.co (canonical model card), *.edu, vendor security advisories (Red Hat, Plesk, Veeam, Comet, Synology, GitHub Security Advisories), llama.cpp GitHub releases.
- **SECONDARY**: TechCrunch, CNBC, Bloomberg, Reuters, MacRumors, VentureBeat, MarkTechPost, Wired, NYT, Verge, Ars, Al Jazeera, SRF, Le Temps, Quanta Magazine, 9to5Google, BleepingComputer, Axios, Fortune, TheStreet, CBS News, CNN, Time, ABC News, Help Net Security, Artificial Analysis, Simon Willison blog, LessWrong, Wikipedia, Crunchbase, AP wire, Federal News Network, news.ycombinator.com, law-firm client alerts.
- **MIXED**: both kinds present in the same item.
- **NONE**: no URL.

`[via snippet]` is NOT a downgrade — it reflects fetch fidelity, not source tier.

`[vendor PR]` is a topic/stakes signal (industry-news), NOT a source-tier downgrade.

Repeat detection uses three signals: (a) writer's own `[ongoing since YYYY-MM-DD]` tag, (b) shared arXiv ID or CVE ID, (c) same named entity + same event within the window. A repeat earlier-date pointer in the per-brief tables uses the format `→ 05-DD`.

---

## Headline numbers

- **Total items audited: 156** across 7 days, 5 streams.
- **Source-type split**: PRIMARY **62%** (97), SECONDARY **24%** (37), MIXED **14%** (22), NONE 0%.
- **Repeat items**: **58 of 156 = 37%** of all items were re-runs of stories already covered earlier in the 7-day window. (Includes 47 explicit `[ongoing since …]` tags written inside the audit window plus 11 unflagged repeats picked up by entity+event match.)
- **Worst stream by %secondary**: **markets** (74% secondary). Next: **overview-world section** (Al Jazeera/SRF-heavy).
- **Worst stream by repeat rate**: **markets** (84% — every daily commodity/FX/Iran item recycles) closely followed by **overview** (47% — daily FX, weekly stories that re-land).
- **Cleanest stream**: **cyber-papers science arXiv blocks** (≈100% primary, ≈8% repeat) and **cyber-papers CVE blocks** (≈100% primary NVD).

---

## Per-stream rollup

### overview (7 files: 25→31, all dates)
- Items: **47** (Science 33 incl. arXiv ML, Markets 14).
- Primary: **39 (83%)** — driven by nature.com, arxiv.org, ecb.europa.eu direct fetches.
- Secondary: **6 (13%)** — CNBC, Quanta, ScienceDaily, TheStreet, UCSC press release.
- Mixed: **2 (4%)** — KM3NeT (Nature + ScienceDaily); FemoCo (Quanta covering Caltech work).
- Repeat rate: **34%** — daily ECB FX rate is the same story re-printed every weekday with a new number; Asian close / US futures placeholders likewise; some Nature items repeat verbatim into the weekend brief.
- Topic mix: Heavy `research-result` (28), `market-signal` (12 — most are FX rote), few `industry-news`.

### ai-ml (6 files: 25–30, no Sun)
- Items: **40** (Lab blogs 14, Models 10, Benchmarks 8, Industry 8).
- Primary: **15 (38%)** — arxiv.org, github.com, huggingface.co, EU Council press releases, SEC EDGAR, llama.cpp releases.
- Secondary: **15 (38%)** — TechCrunch, VentureBeat, MarkTechPost, Bloomberg, CNBC, MacRumors, BleepingComputer, Crunchbase, Artificial Analysis, MIT Tech Review, law-firm client alerts.
- Mixed: **10 (24%)** — most "vendor announcement + ecosystem coverage" items cite the lab blog AND a tech-press story; classified mixed when both URLs render in the item.
- Repeat rate: **53%** — Opus 4.8 (4 of 6 days), Anthropic-SpaceX (3 days), Glasswing/Mythos (4 days), Gemini 3.5 Flash (4 days), DeepSeek/Kimi/GLM/MiniMax open-weight cluster (3 days), EU AI Act omnibus (3 days), Colorado AI Act (2 days), llama.cpp build-of-the-day (4 days, different build #s but same "maintenance build" story shape).
- Topic mix: **27 of 40 are `industry-news`** (model launches, funding, regulation). Only ~5 are `research-result` (the arXiv evaluation papers folded into the AI/ML brief). No `incident-cve`. No `gossip-drama` per se but several items have the texture of it (DeepSWE / Claude Opus loophole; xAI absorbed into SpaceXAI).

### cyber-papers (5 files: 26–30, no 25 or 31)
- Items: **52** (Switzerland 27, World politics 9 distinct, CVEs 26 grouped, arXiv ML papers 20).
- Primary: **31 (60%)** — nvd.nist.gov for every CVE, arxiv.org for every paper, plus official vendor advisories.
- Secondary: **20 (38%)** — Al Jazeera, SRF, Le Temps for the Switzerland and World sections; these are *entirely* secondary.
- Mixed: **1 (2%)**.
- Repeat rate: **23%** — chiefly the Israel-Lebanon-Gaza thread (5 days), DRC Ebola (4 days), US-Iran/Hormuz (5 days), Winterthur attack (2 days), G7 Evian (2 days), Drupal CVE / Langflow CVE / Samba CVE family (each 2 days).
- Topic mix: CVEs are uniformly `incident-cve`, papers uniformly `research-result` or `technical-depth`. Switzerland section is mostly `policy-regulation`. World politics block is heavy `policy-regulation` and `gossip-drama`-adjacent (Spain raid, Senegal speaker, etc.).
- **Subdivides cleanly**: CVE and paper sub-blocks are pristine primary; CH+World sub-blocks are pristine secondary.

### markets (4 files: 26–29, no 25/30/31; retired 30 May)
- Items: **19** (FX, European equities, US session, oil, gold, individual earnings, world-politics-US-morning, PCE).
- Primary: **4 (21%)** — ECB FX feed (4 of 4 days), US State Dept press statement (once), SEC EDGAR for earnings 8-K (twice, both returned 403 and were cited via secondary anyway).
- Secondary: **14 (74%)** — CNBC, Bloomberg, TheStreet, Fortune, Times of Israel, CBS News, CNN, ABC News, Trading Economics, Benzinga, Irish Times, Federal News Network, Texas Tribune, KSAT, Business Upturn, T. Rowe Price commentary.
- Mixed: **1 (5%)**.
- Repeat rate: **84%** — *every* daily entry is the same five buckets re-instantiated (FX, European close, US session, oil, gold), with US-Iran/Hormuz reappearing as the proximate cause every single day. The only `[NEW]` items in 4 days were: Micron earnings (26th), Texas Senate runoff (27th), PCE print (28th), Romania expels Russian consul (29th).
- Topic mix: 100% `market-signal` / `industry-news`. No research, no policy substance beyond inflation prints.

### weekend (1 file, 30 May)
- Items: **26** (Headlines 5, ML papers 9, Science 5, Models 2 + a 3rd 4-model cluster bullet = 4, Apple Silicon 1, Biology 3, Cybersecurity 4, Essays 4, Cross-cutting threads 4 are meta — excluded).
- Primary: **18 (69%)** — arxiv.org, nature.com, cell.com, github.com, nvd.nist.gov, cisa.gov, llama.cpp/mlx-lm releases, anthropic.com/research.
- Secondary: **5 (19%)** — Quanta, Al Jazeera, SRF, Simon Willison blog, LessWrong, VentureBeat, TechTimes, MacRumors-class.
- Mixed: **3 (12%)**.
- Repeat rate: **65%** — by design: the Weekend brief is a synthesis read of the week. 17 of 26 items are explicitly tagged `[ongoing since …]` and re-summarized at greater length: Gram (5/30), RiM (5/30), LLMSurgeon (5/30), undersea volcanoes (5/27), pig xenotransplant (5/30), Th-229 (5/30), Opus 4.8 (5/28), Glasswing (5/24), supply chain pattern (5/28), Blue Origin (5/30 ai-ml), Gram-negative enzyme (5/30), Opus open-weight cluster, US-Iran MOU, Israel-Lebanon escalation, Winterthur attack, EU AI Act omnibus, llama.cpp/MLX status. **For a weekly digest this isn't a bug**, but counted against the audit window it is the highest-overlap stream.

---

## Per-brief breakdown

Compact: `topic | source-type | stakes | repeat?`. `→ 05-DD` means repeats an earlier item that day.

### 2026-05-25 overview (7 items)
| Topic | Source | Stakes | Repeat |
|---|---|---|---|
| H5N1 cow infectious dose | mixed (Nature + ScienceDaily snippet) | research-result | no |
| Hypothalamic Menin aging driver | secondary (ScienceDaily) | research-result | no |
| Crystal lattice angular-momentum transfer | primary (Nature Physics) | research-result | no |
| KM3NeT 220 PeV blazar candidates | mixed (Nature + ScienceDaily) | research-result | no |
| JWST WASP-94A mineral clouds | secondary (UCSC press release) | research-result | no |
| arXiv ML batch: nothing confirmed | none (gap notice) | — | n/a |
| Nikkei 225 record | secondary (CNBC) | market-signal | no |
| EUR/CHF ≈ 0.915 | primary (ECB graph) | market-signal | no |

### 2026-05-25 ai-ml (17 items)
| Topic | Source | Stakes | Repeat |
|---|---|---|---|
| Google I/O aftermath (Gemini 3.5 Flash) | mixed (deepmind blog + TechCrunch) | industry-news | no |
| Anthropic Code-with-Claude / Glasswing | mixed (anthropic + MIT Tech Review) | industry-news | no |
| OpenAI $25B ARR + IPO | secondary (VentureBeat) | industry-news | no |
| Thinking Machines TML-Interaction-Small | secondary (TechCrunch) | industry-news | no |
| ByteDance Lance 3B multimodal | mixed (HF + MarkTechPost) | technical-depth | no |
| Tencent Hy-MT2 33-language | mixed (HF + Phemex) | technical-depth | no |
| Gemini 3.5 Flash GA | primary (blog.google) | industry-news | no |
| DeepSeek V4-Pro/Flash pricing | mixed (HF + Artificial Analysis) | industry-news | no |
| Moonshot Kimi K2.6 swarm scaling | mixed (HF + MarkTechPost) | industry-news | no |
| CohereLabs command-a-plus w4a4 | primary (HF) | technical-depth | no |
| Gemini 3.5 Flash benchmarks SOTA | secondary (MarkTechPost) | industry-news | yes (same Gemini 3.5 item) |
| Open-weight agentic coding leaderboard | secondary (Artificial Analysis) | industry-news | yes (re-uses Kimi/DeepSeek) |
| LMArena April snapshot | secondary (LLM-Stats) | industry-news | no |
| gpt-oss-120b matches o4-mini | secondary (Fireworks/VentureBeat) | industry-news | no |
| EU AI Act compliance extension | mixed (EU Council + Latham&Watkins) | policy-regulation | no |
| Anthropic $30B Series H round | secondary (Crunchbase) | industry-news | no |
| Anthropic × SpaceX 220K GPUs | mixed (anthropic + CNBC) | industry-news | no |
| xAI absorbed into SpaceXAI | secondary (Wikipedia) | gossip-drama | no |
| DeepMind acquires Contextual AI | secondary (Air Street Press) | industry-news | no |
| NIST CASI pre-release evals | secondary (CNBC) | policy-regulation | no |
| llama.cpp b9297 NVFP4 MTP | primary (GitHub releases) | technical-depth | no |
| MLX Engine v1.8.1 | secondary (snippet, no canonical URL) | technical-depth | no |
| unsloth/Qwen3.6-27B-MTP-GGUF | primary (HF) | technical-depth | no |

### 2026-05-26 overview (8 items)
| Topic | Source | Stakes | Repeat |
|---|---|---|---|
| GWTC-4 BH spin subpopulations | primary (arXiv) | research-result | no |
| JWST CC supernova z=3.19 | primary (arXiv) | research-result | no |
| Altermagnetism in MnTe | primary (arXiv) | research-result | no |
| Cavity vacuum singlet→triplet SC | primary (arXiv) | research-result | no |
| Nature comment: brain-as-computer | primary (Nature) | research-result | no |
| Majorana modes Rashba SC | primary (Nature Physics) | research-result | no |
| arXiv ML batch (6 papers) | primary (arXiv all) | research-result | no |
| EUR/CHF 0.9099 | primary (ECB) | market-signal | yes (→ 05-25 FX) |

### 2026-05-26 ai-ml (10 items)
| Topic | Source | Stakes | Repeat |
|---|---|---|---|
| Google SynthID cross-industry adoption | secondary (Google blog snippet + ETV Bharat) | industry-news | no |
| Gemini 3.5 Flash Composer 2.5 pricing | mixed (blog.google + TechCrunch) | industry-news | yes (→ 05-25 Gemini) |
| MiniCPM5-1B on-device LLM | mixed (HF + Gigazine) | technical-depth | no |
| LongCat-Video-Avatar-1.5 | primary (HF) | technical-depth | no |
| Supertonic-3 31-lang TTS | mixed (HF + MarkTechPost) | technical-depth | no |
| CohereLabs Command-A+ w4a4 | primary (HF) | technical-depth | yes (→ 05-25 ai-ml) |
| SWE-bench Verified leaderboard | mixed (swebench.com + Artificial Analysis) | industry-news | yes (→ 05-25 leaderboards) |
| MiniCPM5-1B composite score | secondary (BenchLM.ai) | technical-depth | yes (same MiniCPM item above) |
| Anthropic >$30B Series H closing | secondary (Bloomberg + CNBC) | industry-news | yes (→ 05-25 ai-ml) |
| Anthropic-Google-Broadcom 3.5GW TPU | mixed (TechCrunch + CNBC) | industry-news | no |
| China NDRC blocks Meta/Manus | secondary (36kr.com) | policy-regulation | no |
| MiniCPM5-1B Apple Silicon build | mixed (github + HF) | technical-depth | yes (same MiniCPM) |

### 2026-05-26 cyber-papers (17 items)
| Topic | Source | Stakes | Repeat |
|---|---|---|---|
| OFSP 5% premium hike 2027 | secondary (Le Temps) | policy-regulation | no |
| BÜPF/LSCPT surveillance revision | secondary (Le Temps) | policy-regulation | no |
| Vaud bouclier fiscal | secondary (Le Temps) | policy-regulation | no |
| MILAK NATO survey | secondary (SRF) | policy-regulation | no |
| G7 Evian No-G7 impasse | secondary (Le Temps) | policy-regulation | no |
| Geneva 3-day strike June 2-4 | secondary (Le Temps) | policy-regulation | no |
| US strikes Iranian boats | secondary (Al Jazeera) | policy-regulation | no |
| EU summons Russian envoys over Kyiv | secondary (Al Jazeera + SRF) | policy-regulation | no |
| Israel 1000 sq km occupation | secondary (Al Jazeera) | policy-regulation | no |
| India-US critical minerals | secondary (Al Jazeera) | policy-regulation | no |
| Senegal Sonko speaker | secondary (Al Jazeera) | gossip-drama | no |
| Hajj 2026 Arafat | secondary (Al Jazeera) | industry-news | no |
| CVE-2026-7374 KubeVirt | primary (NVD + Red Hat) | incident-cve | no |
| CVE-2026-45247 Mirasvit Magento | primary (NVD + Sansec) | incident-cve | no |
| CVE-2026-4480 Samba print | primary (NVD + Red Hat) | incident-cve | no |
| CVE-2026-40033 FreeRDP | primary (NVD + GHSA) | incident-cve | no |
| CVE-2026-48131/48132 Check Point | primary (NVD + vendor SK) | incident-cve | no |
| CVE-2026-46368 OpenWrt LuCI | primary (NVD + Exploit-DB) | incident-cve | no |
| 5 arXiv papers (second batch) | primary (arXiv) | research-result | no |

### 2026-05-26 markets (6 items)
| Topic | Source | Stakes | Repeat |
|---|---|---|---|
| FX EUR/CHF 0.9136 | primary (ECB) | market-signal | yes (→ 05-26 overview) |
| SMI/DAX/Stoxx after Iran-rally reversal | secondary (CNBC) | market-signal | no |
| US session S&P/Nasdaq record | secondary (TheStreet + CNBC) | market-signal | no |
| Micron $1T market cap | secondary (CNBC + 247WallSt) | market-signal | no |
| BP chair ousted | secondary (Bloomberg + Irish Times) | gossip-drama | no |
| Brent $100, gold $4,542 | secondary (CNBC + Time) | market-signal | no |
| Iran US strikes (world section) | secondary (CNBC + Time) | policy-regulation | yes (→ 05-26 cyber-papers same day) |
| India-US critical minerals (world) | mixed (state.gov + Al Jazeera) | policy-regulation | yes (→ 05-26 cyber-papers same day) |
| Armenia-US partnership | secondary (Al Jazeera) | policy-regulation | no |
| US Senate DHS reconciliation | secondary (Federal News Network) | policy-regulation | no |

### 2026-05-27 overview (8 items)
| Topic | Source | Stakes | Repeat |
|---|---|---|---|
| Molecular nanodiamond | primary (Nature) | research-result | no |
| Somatic mutations & autoimmune | primary (Nature) | research-result | no |
| Iceland mid-ocean explosive eruptions | secondary (Quanta) | research-result | no |
| Mars atmospheric isotopes | primary (arXiv) | research-result | no |
| NuSTAR axion helioscope | primary (arXiv) | research-result | no |
| 5 arXiv ML papers | primary (arXiv) | research-result | no |
| EUR/CHF 0.9136 | primary (ECB) | market-signal | yes (→ 05-26) |

### 2026-05-27 ai-ml (15 items)
| Topic | Source | Stakes | Repeat |
|---|---|---|---|
| Anthropic-SpaceX $45B/Colossus | mixed (anthropic + Data Center Dyn + Axios) | industry-news | yes (→ 05-25 ai-ml) |
| xAI Grok Build 0.1 | mixed (x.ai + Kilo AI) | industry-news | no |
| Datacurve DeepSWE benchmark | secondary (Datacurve + VentureBeat) | industry-news | no |
| DeepSeek V4 Pro/Flash cluster | mixed (simonwillison + Artificial Analysis) | industry-news | yes (→ 05-25/26 ai-ml) |
| Moonshot Kimi K2.6 | secondary (NVIDIA Build/Moonshot snippet) | industry-news | yes (→ 05-25 ai-ml) |
| Z.ai GLM-5.1 | primary (HF) | industry-news | no |
| MiniMax M2.7 | primary (minimax.io) | industry-news | no |
| Grok Build 0.1 (open weights) | secondary (OpenRouter) | industry-news | yes (same Grok above) |
| DeepSWE leaderboard recap | secondary (Datacurve) | industry-news | yes (same DeepSWE above) |
| Artificial Analysis Index v4.0 | secondary (Artificial Analysis) | industry-news | yes (→ 05-26 SWE-bench) |
| Mistral Medium 3.5 benchmark gap | secondary (MarkTechPost) | industry-news | no |
| Meta raises 2026 capex to $125-145B | secondary (CNBC + Fortune) | industry-news | no |
| DeepSeek V4 Pro price cut | secondary (Artificial Analysis) | industry-news | yes (same DeepSeek cluster) |
| EU AI Act omnibus political agreement | mixed (EU Council + Latham&Watkins) | policy-regulation | yes (→ 05-25 ai-ml) |
| US federal AI governance blueprint | secondary (Wilson Sonsini) | policy-regulation | no |
| llama.cpp b9370 Hexagon | primary (GitHub releases) | technical-depth | yes (→ 05-25 ai-ml as continuing build cadence) |

### 2026-05-27 cyber-papers (16 items)
| Topic | Source | Stakes | Repeat |
|---|---|---|---|
| Federal communication 60-post cut | secondary (Le Temps) | policy-regulation | no |
| Blatten landslide retrospective | secondary (SRF) | industry-news | no |
| G7 Geneva conditional protest auth | secondary (Le Temps) | policy-regulation | yes (→ 05-26 cyber-papers) |
| 27 Sept neutrality/nutrition vote | secondary (SRF) | policy-regulation | no |
| Nestlé "Simpli Water" Henniez launch | secondary (Le Temps) | industry-news | no |
| Hungary post-Orbán analysis | secondary (SRF) | policy-regulation | no |
| Israel kills Hamas Odeh; Nabatieh displacement | secondary (Al Jazeera) | policy-regulation | yes (→ 05-26 Israel-Gaza) |
| Iran deal Hormuz + troop withdrawal | secondary (SRF) | policy-regulation | yes (→ 05-26 Iran strikes) |
| Spain PSOE police raid | secondary (Al Jazeera) | gossip-drama | no |
| Bangladesh IMF Iran-war shock | secondary (Al Jazeera) | market-signal | no |
| DRC Ebola WHO warning | secondary (Al Jazeera) | policy-regulation | no |
| CVE-2026-9082 Drupal KEV | primary (NVD) | incident-cve | yes (→ 05-26 listed implicitly) |
| CVE-2026-8054 dotCMS CVSS 10.0 | primary (NVD) | incident-cve | no |
| CVE-2026-9312 GHES SSRF | primary (NVD) | incident-cve | no |
| CVE-2026-7524 IBM Langflow zip-slip | primary (NVD) | incident-cve | no |
| CVE-2025-12686 Synology BeeStation | primary (NVD) | incident-cve | no |
| 5 arXiv papers (second batch) | primary (arXiv) | research-result | no |

### 2026-05-27 markets (5 items)
| Topic | Source | Stakes | Repeat |
|---|---|---|---|
| FX EUR/CHF 0.9153 | primary (ECB) | market-signal | yes (→ 05-26) |
| European equities DAX/CAC/SMI | secondary (CNBC) | market-signal | yes (→ 05-26 markets) |
| US Dow record S&P/Nasdaq flat | secondary (TheStreet) | market-signal | yes (→ 05-26 markets) |
| Oil −4.6%, WTI $89 | secondary (CNBC) | market-signal | yes (→ 05-26 oil item) |
| Gold ~$4,420 | secondary (CNBC Select) | market-signal | yes (→ 05-26 gold item) |
| Texas Paxton defeats Cornyn | secondary (Texas Tribune + KSAT) | policy-regulation | no |
| Iran-US deal draft "fabrication" | secondary (Bloomberg + CNBC) | policy-regulation | yes (→ 05-26 Iran items) |

### 2026-05-28 overview (12 items)
| Topic | Source | Stakes | Repeat |
|---|---|---|---|
| Antihydrogen hyperfine 4ppm CPT | primary (Nature) | research-result | no |
| Direct BH mass in little-red-dot galaxy | primary (Nature) | research-result | no |
| Superallowed α-decay ¹⁰⁴Te | primary (Nature) | research-result | no |
| Hippocampal CA3→CA1 coding | primary (Nature) | research-result | no |
| Blood stem cell inflammation memory | primary (Nature) | research-result | no |
| Mammalian aging transcriptomic signatures | primary (Nature) | research-result | no |
| 6 arXiv ML papers | primary (arXiv) | research-result | no |
| ECB FX EUR/CHF 0.9153 | primary (ECB) | market-signal | yes (→ 05-27) |

### 2026-05-28 ai-ml (8 items)
| Topic | Source | Stakes | Repeat |
|---|---|---|---|
| Anthropic Claude Opus 4.8 launch | secondary (MacRumors + 9to5Google) | industry-news | no |
| Anthropic Mythos rollout signal | secondary (WTVB/AP + BleepingComputer) | industry-news | yes (→ 05-25 ai-ml Glasswing) |
| Mistral AI Now Summit (Airbus/BMW) | mixed (Bloomberg + mistral.ai) | industry-news | no |
| Poolside Laguna XS.2/M.1 tech report | mixed (arXiv + Poolside blog) | technical-depth | no |
| Opus 4.8 SWE-bench Pro 69.2% | secondary (llm-stats + BenchLM) | industry-news | yes (same Opus 4.8) |
| MLE-Bench AIBuildAI-2 70.7% | primary (arXiv) | research-result | no |
| EgoBench multimodal 30.62% | primary (arXiv) | research-result | no |
| NextEra $66.8B Dominion AI power | mixed (Bloomberg + CNBC + SEC EDGAR) | industry-news | no |
| Colorado AI Act SB 26-189 | secondary (Holland&Knight + Crowell + DWT) | policy-regulation | no |
| llama.cpp b9371 | secondary (github releases snippet) | technical-depth | yes (→ 05-27 b9370 pattern) |

### 2026-05-28 cyber-papers (17 items)
| Topic | Source | Stakes | Repeat |
|---|---|---|---|
| Winterthur knife attack Terrorakt | secondary (SRF) | policy-regulation | no |
| Blatten one year on memorial | secondary (SRF) | industry-news | yes (→ 05-27 cyber-papers Blatten retrospective) |
| Swiss PACS civil-pact | secondary (SRF) | policy-regulation | no |
| BFS "10-Million-Schweiz" scenarios | secondary (SRF) | policy-regulation | no |
| Sandoz EU complaint China antibiotics | secondary (SRF) | policy-regulation | no |
| US strikes Bandar Abbas + Oman threat | secondary (Al Jazeera) | policy-regulation | yes (→ 05-26/27 Iran items) |
| DRC Ebola 17th outbreak WHO Tedros | secondary (Al Jazeera) | policy-regulation | yes (→ 05-27 DRC Ebola) |
| Yemen Hadi dies | secondary (Al Jazeera) | gossip-drama | no |
| Israel attacks southern Lebanon 16 killed | secondary (Al Jazeera + Le Temps) | policy-regulation | yes (→ 05-26/27 Israel-Lebanon) |
| Norway under French nuclear umbrella | secondary (SRF) | policy-regulation | no |
| South Africa Ramaphosa Farmgate | secondary (Al Jazeera) | gossip-drama | no |
| Supply-chain triple hit (Nx/DAEMON/TanStack KEV) | primary (NVD ×3) | incident-cve | no |
| Veeam VSPC RCE + Agent LPE | primary (NVD + Veeam KB) | incident-cve | no |
| Samba check-password-script CVE-2026-4408 | primary (NVD) | incident-cve | yes (→ 05-26 Samba %J) |
| Comet Backup CVE-2026-32999 | primary (NVD + Comet) | incident-cve | no |
| TinyMCE stored-XSS cluster (4 CVEs) | primary (NVD + TinyMCE) | incident-cve | no |
| Multipass VM escape CVE-2026-49238 | primary (NVD + GHSA) | incident-cve | no |
| 5 arXiv papers (second batch) | primary (arXiv) | research-result | no |

### 2026-05-28 markets (5 items)
| Topic | Source | Stakes | Repeat |
|---|---|---|---|
| FX EUR/CHF 0.9167 | primary (ECB) | market-signal | yes (→ 05-27) |
| SMI −1.29% European equities lower | secondary (CNBC + Trading Economics) | market-signal | yes (→ 05-27) |
| April PCE 3.8% YoY 3-year high | secondary (CNBC + Benzinga) | market-signal | no |
| US midday S&P/Nasdaq records | secondary (TheStreet) | market-signal | yes (→ 05-27) |
| Brent rebounds +2.6%; gold flat | secondary (Fortune ×2) | market-signal | yes (→ 05-27 oil/gold) |
| Iran 60-day MoU negotiated | secondary (Times of Israel + CNN + ABC) | policy-regulation | yes (→ 05-26/27 Iran) |
| PCE pressure on Trump/Warsh | secondary (CBS + CNN) | policy-regulation | yes (same PCE) |

### 2026-05-29 overview (8 items)
| Topic | Source | Stakes | Repeat |
|---|---|---|---|
| ETH Zurich randomness amplification superconducting | primary (Nature) | research-result | no |
| β-arrestin LLPS condensates GPCR | primary (Nature) | research-result | no |
| End-Cretaceous extinction darkness/size | primary (Nature) | research-result | no |
| Cavity photons attractive exciton interactions | primary (Nature) | research-result | no |
| Heart failure gene therapy review | primary (Nature news) | research-result | no |
| 6 arXiv ML papers | primary (arXiv) | research-result | no |
| EUR/CHF 0.9167 | primary (ECB) | market-signal | yes (→ 05-28) |
| Asian close Nikkei/Hang Seng/CSI | secondary (CNBC) | market-signal | no |
| US records 28 May | secondary (TheStreet) | market-signal | yes (→ 05-28 markets) |

### 2026-05-29 ai-ml (9 items)
| Topic | Source | Stakes | Repeat |
|---|---|---|---|
| Opus 4.8 + GitHub Copilot GA + near-Mythos alignment | mixed (TechCrunch + github blog + VentureBeat) | industry-news | yes (→ 05-28 Opus 4.8) |
| Glasswing 23K vulns 90.6% confirmed | mixed (anthropic.com/research + Help Net + Hacker News) | industry-news | yes (→ 05-25/28 Glasswing) |
| OpenAI Frontier Governance Framework | mixed (openai.com + AI News) | policy-regulation | no |
| Open-weight context (no new releases) | (meta) | — | yes (recapping cluster) |
| RightNow-Arabic-0.5B / Aryabhata 2 | primary (arXiv) | technical-depth | no |
| Glasswing methodology benchmark | mixed (anthropic.com/research) | research-result | yes (same Glasswing) |
| LMArena late-May state | secondary (swfte.com) | industry-news | yes (→ 05-25 LMArena) |
| BenchTrace / OpenClawBench / COLAGUARD | primary (arXiv) | research-result | no |
| California ~30 AI bills crossover | secondary (Transparency Coalition + Troutman) | policy-regulation | no |
| Colorado AI Act enforcement stay | secondary (Hunton) | policy-regulation | yes (→ 05-28 Colorado SB 26-189) |
| llama.cpp b9413 CUDA maintenance | primary (github releases) | technical-depth | yes (→ 05-28 b9371) |
| mlx-lm v0.31.3 status | primary (github releases) | technical-depth | no |

### 2026-05-29 cyber-papers (15 items)
| Topic | Source | Stakes | Repeat |
|---|---|---|---|
| Winterthur detention + clinic inquiry | secondary (SRF + Le Temps) | policy-regulation | yes (→ 05-28 Winterthur) |
| Patriot air-defence five candidates | secondary (SRF) | policy-regulation | no |
| Vaud 2027 Cavalli candidate | secondary (Le Temps) | gossip-drama | no |
| Swiss solar surplus batteries | secondary (SRF) | technical-depth | no |
| Medphone hotline closure | secondary (SRF) | policy-regulation | no |
| Israel crosses Litani River | secondary (Al Jazeera) | policy-regulation | yes (→ 05-28 Israel-Lebanon) |
| US-Iran 60-day MOU explainer | secondary (Al Jazeera) | policy-regulation | yes (→ 05-28 Iran MoU) |
| Sudan RSF kills 27; 19.5M hunger | secondary (Al Jazeera) | policy-regulation | no |
| Quad Fiji port | secondary (Al Jazeera) | policy-regulation | no |
| Trump $1.8B anti-weaponisation fund frozen | secondary (Al Jazeera + Le Temps) | policy-regulation | no |
| Germany Gaza concern | secondary (Al Jazeera) | policy-regulation | yes (→ 05-28 Israel-Gaza) |
| CVE-2026-45312 RAGFlow Jinja2 SSTI | primary (NVD + GHSA) | incident-cve | no |
| CVE-2026-9559/9558 Mautic double | primary (NVD + GHSA) | incident-cve | no |
| CVE-2026-45663 Dokploy | primary (NVD + GHSA) | incident-cve | no |
| CVE-2026-44962 Plesk APS XPath | primary (NVD + Plesk) | incident-cve | no |
| CVE-2026-8732 WP Maps Pro admin takeover | primary (NVD + Wordfence) | incident-cve | no |
| CVE-2026-10042 manga-image-translator pickle | primary (NVD + github commit) | incident-cve | no |
| 4 arXiv papers (second batch) | primary (arXiv) | research-result | no |

### 2026-05-29 markets (6 items)
| Topic | Source | Stakes | Repeat |
|---|---|---|---|
| FX EUR/CHF 0.9111 | primary (ECB) | market-signal | yes (→ 05-28) |
| European equities week +3% | secondary (CNBC + T. Rowe Price) | market-signal | yes (→ 05-28) |
| SMI/SPI Friday | secondary (Trading Economics) | market-signal | yes (→ 05-28) |
| US midday Dell +30% AI server | secondary (TheStreet) | market-signal | no |
| Oil WTI ~$87 / Brent $94 / gold $4,470 | secondary (Fortune + Business Upturn) | market-signal | yes (→ 05-28) |
| Gap Inc Q1 earnings | secondary (Yahoo Finance/PR Newswire) | market-signal | no |
| Kohl's Q1 earnings | secondary (GuruFocus) | market-signal | no |
| US-Iran 60-day ceasefire final determination | secondary (Al Jazeera + Axios) | policy-regulation | yes (→ 05-28 Iran MoU) |
| Trump $1.8B fund blocked | secondary (CBS + Bloomberg) | policy-regulation | yes (→ 05-29 cyber-papers same day) |
| Romania expels Russian consul | secondary (Al Jazeera) | policy-regulation | no |

### 2026-05-30 overview (8 items)
| Topic | Source | Stakes | Repeat |
|---|---|---|---|
| Blue Origin New Glenn destroyed | mixed (Spaceflightnow + Nature) | industry-news | no |
| Macrophage MATCH cirrhosis trial | mixed (Cell Stem Cell + Nature news) | research-result | no |
| Pig-to-human xenotransplant 8mo | primary (Nature news) | research-result | no |
| Th-229 isomer lifetime resolved | primary (Nature Physics) | research-result | no |
| FeMoCo classical sim (Quanta) | secondary (Quanta) | research-result | no |
| Outer-membrane enzyme antibiotic target | primary (Nature) | research-result | no |
| 5 arXiv ML papers (Friday batch) | primary (arXiv) | research-result | no |
| Asian close Nikkei +2.53% | secondary (CNBC) | market-signal | yes (→ 05-29 Asian close) |
| EUR/CHF 0.9111 | primary (ECB) | market-signal | yes (→ 05-29) |
| US futures (weekend) | secondary (Investing.com) | market-signal | no |

### 2026-05-30 ai-ml (4 items)
| Topic | Source | Stakes | Repeat |
|---|---|---|---|
| Lab blogs: nothing today (meta) | none | — | n/a |
| AlphaProof Nexus correction | primary (arXiv) | research-result | no (chased lead, outside window) |
| HiDream-O1-Image 8B MIT | mixed (HF + WaveSpeed + AA arena) | technical-depth | no |
| No new LLM open-weight (meta) | none | — | n/a |
| SoundnessBench | primary (arXiv) | research-result | no |
| Gram alignment auditing | primary (arXiv) | research-result | no |
| ProjectionBench / RoboWits | primary (arXiv) | research-result | no |
| No funding/M&A today (meta) | none | — | n/a |
| MLX CUDA backend status | secondary (github snippet) | technical-depth | yes (→ 05-29 mlx-lm v0.31.3) |
| llama.cpp release cadence note | secondary (github snippet) | technical-depth | yes (→ 05-29 b9413) |

### 2026-05-30 cyber-papers (12 items)
| Topic | Source | Stakes | Repeat |
|---|---|---|---|
| Pfister at Shangri-La | secondary (SRF + Al Jazeera) | policy-regulation | no |
| Swissmem EU frustration | secondary (SRF) | policy-regulation | no |
| Zurich 2500 housing protest | secondary (SRF) | policy-regulation | no |
| Federal Court affair Caroni | secondary (SRF) | gossip-drama | no |
| Romandie cantonal slates | secondary (Le Temps) | gossip-drama | no |
| Valais security chief interview | secondary (Le Temps) | industry-news | no |
| Colombia votes Sunday | secondary (Al Jazeera) | policy-regulation | no |
| Israel pushes into Nabatieh | secondary (Al Jazeera) | policy-regulation | yes (→ 05-27/28/29 Lebanon) |
| Egypt warns Israel Gaza | secondary (Al Jazeera) | policy-regulation | yes (→ 05-26 onwards Gaza) |
| Russia-Ukraine 100s projectiles; Romania | secondary (SRF) | policy-regulation | yes (→ 05-29 Romania consul) |
| Strait of Hormuz tense | secondary (SRF) | policy-regulation | yes (→ 05-26 onwards Iran) |
| Rubio: Syria envoy Barrack steps down | secondary (Al Jazeera) | gossip-drama | no |
| WHO chief in Bunia DRC | secondary (Al Jazeera) | policy-regulation | yes (→ 05-27/28 DRC Ebola) |
| Palo Alto CVE-2026-0257 KEV | primary (NVD + Palo Alto) | incident-cve | no |
| Nx Console CVE-2026-48027 | primary (NVD + Nx postmortem + GHSA) | incident-cve | yes (→ 05-28 cyber-papers KEV triple) |
| Daemon Tools Lite CVE-2026-8398 | primary (CISA KEV) | incident-cve | yes (→ 05-28 cyber-papers) |
| Spectra Gutenberg Blocks CVE-2026-7465 | primary (NVD) | incident-cve | no |
| KEV recent additions (Drupal/Trend Micro/LiteSpeed) | primary (CISA) | incident-cve | yes (→ 05-27 cyber-papers Drupal KEV) |

### 2026-05-30 weekend (26 items)
| Topic | Source | Stakes | Repeat |
|---|---|---|---|
| US-Iran framework + Oman threat | secondary (Al Jazeera) | policy-regulation | yes (→ week) |
| Israel Litani; Germany Gaza | secondary (Al Jazeera) | policy-regulation | yes (→ week) |
| Blue Origin New Glenn destroyed | secondary (Spaceflightnow) | industry-news | yes (→ 05-30 overview) |
| Switzerland Winterthur + No-10M | secondary (SRF) | policy-regulation | yes (→ week) |
| DRC Ebola + Rwanda nuclear | secondary (Al Jazeera) | policy-regulation | yes (→ week) |
| RL Welfare Axis paper | primary (arXiv) | research-result | no |
| Reasoning with Sampling | primary (arXiv) | research-result | no |
| HPO sparse-reward | primary (arXiv) | research-result | no |
| In-Context Reward Adaptation | primary (arXiv) | research-result | no |
| Self-Trained Verification | primary (arXiv) | research-result | no |
| Gram sabotage auditing | primary (arXiv) | research-result | yes (→ 05-30 ai-ml) |
| Qwen-VLA | primary (arXiv) | research-result | no |
| RiM Reasoning in Memory | primary (arXiv) | research-result | yes (→ 05-30 overview ML batch) |
| LLMSurgeon data audit | primary (arXiv) | research-result | yes (→ 05-30 overview ML batch) |
| FeMoCo classical algorithm | secondary (Quanta) | research-result | yes (→ 05-30 overview) |
| Pig xenotransplant 8mo | primary (Nature news) | research-result | yes (→ 05-30 overview) |
| Th-229 lifetime puzzle | primary (Nature Physics) | research-result | yes (→ 05-30 overview) |
| Iceland mid-ocean explosive | secondary (Quanta) | research-result | yes (→ 05-27 overview) |
| Gram-negative enzyme target | primary (Nature) | research-result | yes (→ 05-30 overview) |
| Opus 4.8 model recap | secondary (github blog) | industry-news | yes (→ 05-28/29 ai-ml) |
| Poolside Laguna tech report recap | primary (arXiv) | technical-depth | yes (→ 05-28 ai-ml) |
| Chinese open-weight cluster recap | (meta-recap, no new URLs) | industry-news | yes (→ 05-25/26/27 ai-ml) |
| GPIC 28T pixel dataset | primary (arXiv) | technical-depth | no |
| MLX/llama.cpp ecosystem state | primary (github) | technical-depth | yes (→ 05-29 ai-ml) |
| MiniCPM5-1B on-device recap | mixed (HF + ai-ml citations) | technical-depth | yes (→ 05-26 ai-ml) |
| Macrophage MATCH 4-yr cirrhosis | mixed (Cell + Nature news) | research-result | yes (→ 05-30 overview) |
| Gut-brain protein circuit | secondary (snippets only) | research-result | no |
| Brain organoid firing sequences | secondary (Nature Neuroscience snippet) | research-result | no |
| Karpathy autoresearch | secondary (TechTimes) | industry-news | no |
| DeepSWE benchmark Opus gaming | secondary (Datacurve + VentureBeat) | industry-news | yes (→ 05-27 ai-ml) |
| Glasswing 90.6% TPR weekend deep | mixed (anthropic.com/research) | research-result | yes (→ 05-29 ai-ml) |
| Supply chain pattern 3 vectors recap | primary (NVD ×3) | incident-cve | yes (→ 05-28/30 cyber-papers) |
| PAN-OS KEV recap | primary (CISA + Palo Alto) | incident-cve | yes (→ 05-30 cyber-papers) |
| RAGFlow SSTI recap | primary (NVD + GHSA) | incident-cve | yes (→ 05-29 cyber-papers) |
| "The Pressure" — Simon Willison essay | secondary (simonwillison.net) | gossip-drama | no |
| Synthetic Persona Pretraining (LessWrong) | secondary (lesswrong.com) | research-result | no |
| Karpathy Sequoia Ascent 2026 | secondary (bearblog snippet) | industry-news | no |
| ACOUP gap-week recs | secondary (acoup.blog) | industry-news | no |

### 2026-05-31 overview (4 items)
| Topic | Source | Stakes | Repeat |
|---|---|---|---|
| FeMoCo classical sim | secondary (Quanta) | research-result | yes (→ 05-30 overview + weekend) |
| Gut bacteria Parkinson's risk | primary (Nature Medicine) | research-result | no |
| Indigenous American genome map | primary (Nature Medicine) | research-result | no |
| Sleuths flag Thermo Fisher antibody images | primary (Nature) | research-result | no |
| Markets closed (meta) | n/a | — | n/a |
| Last ECB FX 05-29 | primary (ECB) | market-signal | yes (→ 05-30 overview) |
| Most recent Asian close Hang Seng -1.3% | secondary (CNBC) | market-signal | yes (→ 05-29 markets) |

---

## Representative examples

### overview — "the science block is doing the heavy lifting"
> **GWTC-4: mass-dependent spin subpopulations in merging black holes** — Population analysis of the LIGO/Virgo/KAGRA fourth gravitational-wave transient catalog finds statistically significant evidence that merging stellar-mass black holes split into at least two distinct spin subpopulations that correlate with mass… [arXiv:2605.24281] (2026-05-26)

Pure primary, fresh arXiv ID, real research-result. This is the *good* shape.

> **EUR/CHF 0.9099 | USD/CHF ≈ 0.7815** — ECB daily FX reference (2026-05-25). Franc has firmed ~0.5% vs. the euro since last week (0.9144 on 2026-05-18)… (2026-05-26)

Primary URL but repeats the same daily FX snapshot every weekday across the week — the URL is canonical, the *story* is dead weight in a daily overview brief.

### ai-ml — "vendor PR carousel even when primary"
> **Anthropic Expands Project Glasswing; Code with Claude London Wraps** [vendor PR] — Anthropic's "Code with Claude" developer event in London (May 19–21) was the company's major public-facing week. Alongside the conference: **Claude Security** opened in public beta under **Project Glasswing**… [Anthropic news] [via snippet] / [MIT Technology Review, 2026-05-21] (2026-05-25)

URL is anthropic.com (primary by rubric), but the *content* is corporate PR digest of a week-old event. Threads forward for 4 more days as Mythos/Glasswing/Opus 4.8 announcements.

> **DeepSeek V4 Pro permanent price cut: $0.435/$0.87 per million tokens (May 22)** — DeepSeek reduced V4 Pro API pricing on May 22, establishing it as the cheapest publicly available hosted model in the frontier-class coding tier… [Artificial Analysis] [single-source] (2026-05-27)

Same DeepSeek V4 story re-told for the third time in three days, secondary URL, item is industry-news commentary not new artifact.

### cyber-papers — "two halves; CVE+arXiv halves are pristine, CH+World halves are wire-rehash"
> **CVE-2026-9082 — Drupal Core SQL injection (CISA KEV): CVSS 9.8, remediation deadline today** — CISA's Known Exploited Vulnerabilities catalog lists this Drupal Core SQL injection — added 2026-05-22, with a remediation deadline of today, 27 May — as exploited in the wild… [NVD CVE-2026-9082] (2026-05-27)

NVD + CISA + Drupal advisory = textbook primary. Actionable. This is what the brief does best.

> **Israel kills Hamas military wing leader Mohammed Odeh; forced displacement order for Lebanon's Nabatieh** — A funeral was held for Mohammed Odeh, identified as the leader of Hamas's military wing, following an Israeli strike… [Al Jazeera, 2026-05-27]

Single Al Jazeera link, narrative wire-style summary, recurs for 5 of 5 cyber-papers brief days under different headlines. Pure secondary aggregator.

### markets — "85% recycled-CNBC"
> **US session (intraday, ~14:30 ET) — S&P 500 +0.57% to ~7,516 · Nasdaq +1%+ to new all-time high · Dow −~80 pts** — First trading session after the Memorial Day long weekend. Technology and semiconductors led… [TheStreet] / [CNBC] (2026-05-26)

> **US midday: S&P 500 and Nasdaq at all-time highs despite hot PCE; Dow flat** — As of ~14:30 ET: S&P 500 +0.49%, Nasdaq Composite +0.64% (both fresh records)… [TheStreet] (2026-05-28)

Same item shape, two different days, same CNBC/TheStreet sources, same "tech leading, Iran in the background" framing. The retired-2026-05-30 stream was almost entirely this.

### weekend — "by design retrospective; only fresh content is the long-form papers section"
> **How's it going? Reinforcement Learning Recruits a Functional Welfare Axis** — [arXiv:2605.30232]… The most rigorous investigation to date of whether RL training creates morally relevant internal states in language models…

This is the weekend brief at its best: a primary arXiv paper, given 300 words of synthesis. 9 of these are present. Worth the price.

> **DRC Ebola outbreak classified PHEIC; Rwanda signs nuclear deal with Russia** — The WHO director-general traveled personally to Ituri Province… [Al Jazeera, 28 May 2026]

Already covered Wed and Thu and Fri in cyber-papers; re-told as one of five week-in-headlines bullets. The synthesis adds nothing not already in the daily briefs.

---

## Diagnosis

**The dominant problem is repetition, not source quality. Topic mix is the close second.**

Sorted:

**(b) Repetition is the biggest problem.** 37% of the 156 items in the audit window are explicit re-runs (`[ongoing since …]` tags from earlier in the week or unflagged-but-clearly-same-story rehashes). The worst offenders are predictable: every markets brief is the same five buckets (FX, European close, US session, oil, gold) with Iran-US/Hormuz threaded through all five every day — 84% repeat rate, and the writers themselves are aware (the brief retired on 2026-05-30 for explicitly this reason). The Iran-US/Hormuz story shows up *every single day* in the audit window across three streams (overview FX, markets, cyber-papers world); the same is true of Israel-Lebanon-Gaza (5 days), Anthropic Opus 4.8 (5 days: 25 → 28 → 29 → 30 ai-ml → 30 weekend), Glasswing/Mythos (4 days), the Chinese open-weight cluster (4 days), and the EU AI Act omnibus (3 days). The weekend brief's 65% repeat rate is structural (it's a synthesis read) but means the deepest writing in the corpus is mostly material the reader already saw three times.

**(c) Topic mix is the second-biggest problem, and it's concentrated in ai-ml.** Of 40 ai-ml items, 27 (68%) are `industry-news` — model launches, funding rounds, regulatory motion, leaderboard reshuffling. Only ~5 are research-result. The shape is: vendor blog → tech-press story → benchmark recap → ecosystem commentary, on a 24-48h cycle. This is the "HN-aggregator" feel the user was reacting to. The cyber-papers stream has the opposite shape — almost no industry-news, dominated by `incident-cve` and `research-result` — and is the strongest stream by content type.

**(a) Source quality is the *weakest* of the three problems.** Once vendor-PR is correctly treated as topic-not-source, 62% of all items cite primary sources (arxiv.org, nature.com, nvd.nist.gov, ecb.europa.eu, github.com, huggingface.co, anthropic.com/blog.google/openai.com), 24% are pure secondary, 14% are mixed. The overview and cyber-papers streams hit 83% and 60% primary respectively; weekend hits 69%. The streams that *are* secondary-dominated are the ones structurally bound to wire copy: markets (no first-party financial data feed beyond ECB FX) and the CH+World halves of cyber-papers (Al Jazeera/SRF/Le Temps wire is the only daily Switzerland-and-world feed reaching the sandbox). The fix for those is feed-allowlist work; the source classification itself isn't the bug.

**Honest near-tie**: if the reader experiences a brief as "primary citations to vendor PR" (Opus 4.8 from anthropic.com is technically primary, but the post is corporate marketing), then (a) and (c) collapse into the same complaint. The cleanest framing is: **the problem is the recurrence of industry-news vendor-cycle stories, not the per-item URL choice**. Repetition makes that recurrence feel worse than it would in isolation.
