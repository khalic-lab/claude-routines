# Prior-Art Survey — Source Credibility & Editor-Writer Patterns

Compiled 2026-05-31 to ground a redesign of `claude-routines`. Two clusters surveyed: **(A)**
source credibility / lifecycle frameworks, **(B)** editor+writer agent patterns and
personal-newsletter products. Personal-scale framing throughout — enterprise/newsroom
machinery stripped out.

---

## A. Source credibility & lifecycle frameworks

### A1. NewsGuard

NewsGuard rates news/info websites on **nine pass-fail criteria** producing a 0–100 score
([rating process](https://www.newsguardtech.com/ratings/rating-process-criteria/)). Weights:
*does not publish false content* 22, *gathers/presents responsibly* 18, *corrects errors* 12.5,
*news vs opinion* 12.5, *avoids deceptive headlines* 10, *discloses ownership/financing* 7.5,
*labels advertising* 7.5, *reveals who's in charge* 5, *names content creators* 5. Tiers:
≥75 "Generally Credible", 60–74 "with Exceptions", 40–59 "Caution", <40 "Maximum Caution",
plus satire/platform special labels.

Lifecycle: ratings are updated "periodically" when practices change; analysts contact site
proprietors for comment before publishing a rating. No published refresh cadence.

Access: personal browser-extension subscription is **$4.95/month**
([FAQ](https://www.newsguardtech.com/newsguard-faq/)). Any non-personal use — research,
content moderation, programmatic ingestion — requires a paid commercial license; pricing not
public ([Terms of Service](https://www.newsguardtech.com/terms-of-service/)). For a private
CI-style pipeline that wants a machine-readable feed, **NewsGuard is effectively closed**.

**Applicability:** the nine-criterion rubric is reusable as a private prompt-checklist for
classifying sources you find; the *scores themselves* are unlicensable for our context.
Reuse the rubric; skip the data feed.

### A2. Media Bias/Fact Check (MBFC)

Two-axis: **Bias** (Economic 35% + Social 35% + Straight News 15% + Editorial 15% → −10…+10
scale) and **Factual Reporting** (Failed Fact Checks 40% + Sourcing 25% + Transparency 25% +
Omission 10%; "Very Low"…"Very High"), updated under a Jan-2025 methodology revision
([methodology](https://mediabiasfactcheck.com/methodology/)). Minimum review threshold: 10
headlines + 5 full stories per source; only failed fact-checks within the last 5 years count.
~9,000 sources total.

Access via RapidAPI and a "Business API"
([MBFC's Data API](https://mediabiasfactcheck.com/mbfcs-data-api/),
[RapidAPI listing](https://rapidapi.com/mbfcnews/api/media-bias-fact-check-ratings-api2)). A
community scraper exists ([drmikecrowe/mbfcext](https://github.com/drmikecrowe/mbfcext)) but
ToS-questionable.

No explicit lifecycle/deprecation taxonomy — re-reviews happen but cadence isn't published.

**Applicability:** the two-axis split (bias × factuality) and the explicit fact-check
5-year rolling window are both reusable mental models. The Sourcing/Transparency/Omission
sub-weights are a *cheap rubric to apply with an LLM judge*. Don't depend on the API.

### A3. Ad Fontes — Media Bias Chart

Two-axis chart (Bias × Reliability), 4,500+ sources, flagship chart twice yearly (Jan/Aug),
monthly partial charts in between
([Jan-2026 flagship](https://adfontesmedia.com/flagship-media-bias-chart-jan2026/),
[Data Platform](https://adfontesmedia.com/)). Free static PDF for personal/educational use;
underlying data + API are paid add-ons to the Data Platform.

**Applicability:** Similar to MBFC — the *visual axis idea* (every source has both a bias
coordinate and a reliability coordinate) is reusable cheaply. Static download is fine for a
one-time seed list; ignore the API.

### A4. NATO Admiralty Code / OSINT grading

Two independent dimensions
([SANS overview](https://www.sans.org/blog/enhance-your-cyber-threat-intelligence-with-the-admiralty-system/),
[ResearchGate AJP-2.1 table](https://www.researchgate.net/figure/NATO-AJP-21-Source-Reliability-and-Information-Credibility-Scales_tbl1_328858953)):

- **Source reliability** A–F: A=completely reliable, B=usually, C=fairly, D=not usually,
  E=unreliable, F=cannot be judged.
- **Information credibility** 1–6: 1=confirmed by other sources, 2=probably true,
  3=possibly true, 4=doubtful, 5=improbable, 6=cannot be judged.

Combined as `B3`, etc. Crucially, **the source's reliability and the specific claim's
credibility are scored independently** — a usually-reliable outlet can still publish a
weak claim, and a weak outlet can break a true story.

Real implementations exist: **MISP taxonomy `admiralty-scale`**
([MISP/misp-taxonomies](https://github.com/MISP/misp-taxonomies/blob/main/admiralty-scale/README.md))
provides machine-readable tags like `admiralty-scale:source-reliability="b"` for cyber-threat
intelligence platforms. So this isn't just doctrine — it's wired into real tagging systems.

**Applicability:** *Strongest finding in cluster A.* The decoupling of "source trust" from
"this-particular-claim confidence" is exactly what a brief-writer with editorial integrity
needs. Reusable as a tagging schema for stories the routine ingests: each story carries both
an inherited source grade and a per-story credibility judgment. Cheap to apply with an LLM.

### A5. Academic credibility — Retraction Watch, Semantic Scholar, OpenAlex

- **Retraction Watch**: acquired by Crossref Sept 2023, retractions now in the **Crossref
  REST API**, updated daily
  ([Crossref blog](https://www.crossref.org/blog/retraction-watch-retractions-now-in-the-crossref-api/),
  [Retraction Watch DB user guide](https://retractionwatch.com/retraction-watch-database-user-guide/)).
  Free API call: `https://api.crossref.org/v1/works?filter=update-type:retraction`. **This is
  the cluster-A finding with the best free programmatic access.** Lifecycle is concretely
  modeled — a retraction `update-to` link points from the new record to the retracted one.
- **Semantic Scholar Graph API**: free
  ([API page](https://www.semanticscholar.org/product/api)). Distinguishes "Highly Influential
  Citations" via a trained classifier
  ([explainer](https://www.semanticscholar.org/faq/influential-citations)).
- **OpenAlex**: free, large entity graph
  ([sources filtering](https://docs.openalex.org/api-entities/sources/filter-sources)). Use to
  look up a venue's `host_organization`/`works_count`/`is_in_doaj` etc. for cheap venue triage.
- **CORE rankings** (CS conferences): A*/A/B/C tiers; methodology mixes citations, acceptance
  rate, PC profile
  ([guide](https://www.iconf.com/news/1076)). **CORE journal rankings were discontinued in
  2022** — conferences only.
- **SJR vs JCR**: SJR is **free**, Scopus-based, 3-year window, PageRank-style weighting; JCR
  is **paywalled**, WoS, 2-year, equal weights
  ([SCImago Wikipedia](https://en.wikipedia.org/wiki/SCImago_Journal_Rank)). For a personal
  pipeline, SJR + OpenAlex is the only sensible combo.

**Applicability:** For a "is this paper worth flagging" filter: cheap mechanical signals
that compose well are **(a) Retraction Watch check via Crossref**, **(b) Semantic Scholar
influential-citation count**, **(c) venue tier from CORE (CS) or SJR (journals)**, in that
priority order. All free. Skip JCR, skip Clarivate.

### A6. Wikipedia Perennial Sources (WP:RSP)

Five-tier classification
([WP:RSP](https://en.wikipedia.org/wiki/Wikipedia:Reliable_sources/Perennial_sources)):

1. **Generally Reliable** — consensus reliable in areas of expertise.
2. **No Consensus** — case-by-case.
3. **Generally Unreliable** — poor fact-checking / no editorial oversight / SPS / UGC.
4. **Deprecated** — RfC consensus to prohibit; technical warning when added.
5. **Blacklisted** — on the spam blacklist; technically blocked.

Process: addition needs *"an uninterrupted RfC or two or more significant noticeboard
discussions"*. Re-classification is via fresh RfC presenting new evidence. Discussions go
"stale" after 4 calendar years — a soft expiry that triggers re-review. No fixed update
cadence.

**Applicability:** Critical insight is the **two-stage promotion gate** (sources don't get
into the list on a whim; they need substantial discussion) and the **stale-after-N-years**
rule. The classification *labels* (generally reliable / no consensus / unreliable /
deprecated / blacklisted) are a clean five-level vocabulary that maps directly to routine
behavior: ingest / ingest-and-flag / ignore-by-default / never-ingest / hard-block.

### A7. Open-source credibility tooling

- **OpenSources** ([repo](https://github.com/OpenSourcesGroup/opensources)) — once-canonical
  curated list of credible/non-credible sites. **Effectively abandoned**: last release April
  2017. Dataset still has reuse value as historical seed, but it's frozen.
- **TrustNews** ([repo](https://github.com/kburk1997/TrustNews)) — crowdsourced ratings of
  60+ outlets, Chrome extension scope. Small, demo-grade.
- **Credibility** ([martin226/credibility](https://github.com/martin226/credibility)) — LLM
  + heuristic per-URL credibility scorer, 0–100. Personal-scale, modern.
- **MBFC ext** ([drmikecrowe/mbfcext](https://github.com/drmikecrowe/mbfcext)) — scrapes MBFC.

No widely-used library maintains a **rolling, programmatic** credibility score for sources
that I could find. The closest is Crossref+Retraction-Watch for academic content, and
Pocket's "algotorial" approach for popular content, neither of which is a drop-in lib.

**Applicability:** there's no library to reuse. There's also no real precedent for what we
want (per-user rolling credibility ledger). We'd be building it.

### Applicability to claude-routines — Cluster A summary

**Reuse**:
- A tagging schema combining (i) NATO admiralty's decoupled source-vs-claim grading and
  (ii) WP:RSP's five-tier vocabulary, applied by the LLM at ingestion time.
- NewsGuard's nine-criterion checklist as a rubric the LLM uses to grade *newly-discovered*
  sources, even though we can't license the scores.
- Free academic signals: Retraction Watch via Crossref, Semantic Scholar influential
  citations, OpenAlex/SJR/CORE for venue tier. All free, all programmatic.

**Skip**:
- Any paid feed (NewsGuard data, MBFC business API, Ad Fontes Data Platform, JCR).
- OpenSources (abandoned). Don't seed off frozen data.

**Still open**:
- The lifecycle/decay mechanism — none of the surveyed systems publish a clean "if a source
  scores X for N weeks, demote / retire" rule. WP:RSP's stale-after-4-years is the only
  precedent and is too coarse. We have to design this.

---

## B. Editor+writer agent patterns & personal-newsletter products

### B1. AI curation/newsletter products

- **Artifact** (Jan 2023 – Jan 2024): Instagram cofounders Systrom + Krieger. Personalized
  ML recommendations on topics/sources/authors, AI-rewriting of clickbait headlines that
  users flagged, AI-narrated audio (celebrity voices), social/comments layer
  ([Wikipedia](https://en.wikipedia.org/wiki/Artifact_(app))). Shutdown reason per Krieger:
  "the market opportunity isn't big enough" — they had pre-defined experiment thresholds, the
  experiments moved the numbers but not enough
  ([TechStartups summary](https://techstartups.com/2024/04/03/yahoo-acquires-ai-news-app-artifact-from-instagram-co-founders-a-year-after-shutdown/)).
  Acquired by Yahoo March 2024; personalization tech folded into Yahoo News
  ([Yahoo announcement](https://www.yahooinc.com/press/yahoo-announces-the-acquisition-of-artifact-the-news-discovery-platform-created-by-instagram-cofounders-kevin-systrom-and-mike-krieger)).
  Wikipedia entry does **not** record which features users specifically loved vs ignored —
  no public post-mortem dissects feature traction.
- **Particle** (founded 2023, ex-Twitter team Beykpour + Molina; $4.4M seed, $10.9M Series A):
  AI-generated multi-source story rebuilds; podcast-clip extraction tied to news topics; web
  client launched May 2025
  ([TechCrunch web launch](https://techcrunch.com/2025/05/06/particle-brings-its-ai-powered-news-reader-to-the-web/),
  [Particle+ tier](https://www.aibase.com/news/www.aibase.com/news/25598)). Distinguishing
  pitch: summaries that *rebuild* a story from many sources rather than excerpt one.
  Subscription $2.99/mo.
- **Flipboard / SmartNews**: Flipboard explicitly markets a *human + AI* curation model and
  rolled out tooling to push curated AI Flipboard "Magazines" to Bluesky in 2025
  ([Flipboard+Bluesky](https://about.flipboard.com/fediverse/flipboard-brings-human-ai-curation-bluesky/)).
  SmartNews spun off "NewsArc" in Aug 2025 as a long-form-leaning AI app
  ([Readless comparison](https://www.readless.app/blog/flipboard-alternatives-2026)).
- **Curio / Bulletin**: no substantive 2025–2026 coverage found in this search; no claim
  made about their state.

**Pattern across products that survived**: pure AI summarization is table stakes; the
*differentiator* is either (a) a structural innovation in how the story is presented
(Particle's multi-source rebuild) or (b) a human-editorial layer on top of algorithmic
discovery (Flipboard, Pocket). Pure-AI aggregation without one of those didn't sustain.

**Applicability:** the "rebuild a story from multiple sources rather than excerpt the loudest
one" idea (Particle) is a structural reuse target — it forces source diversity and
naturally produces an editorially-distinct output. The "AI rewrites clickbait headlines"
idea (Artifact) is cheap and useful as an inline cleanup step.

### B2. Personal-voice human newsletters — what makes them feel non-aggregated

The shared editorial pattern across Stratechery / The Diff / Money Stuff / Platformer is
**thesis-tied selection plus 1-to-few-story focus, not breadth**.

- **Ben Thompson / Stratechery**: explicit thesis vehicle ("Aggregation Theory") — every
  daily Update is read as inference about strategy under that thesis
  ([about](https://stratechery.com/about/),
  [Wikipedia](https://en.wikipedia.org/wiki/Ben_Thompson_(analyst))). Subscription model
  removes the click-chasing incentive.
- **Byrne Hobart / The Diff**: editorial rule = "stuff still worth reading in 5 years",
  prefers non-mean-reverting topics, iterative pattern→case-study→pattern process
  ([Nathan Barry interview](https://nathanbarry.com/021-byrne-hobart-build-recurring-revenue-newsletter/),
  [about page](https://www.thediff.co/archive/about-best-of-faq-25df97a74467/)). The
  newsletter feels personal because the *taste-filter* is consistent, not the topic.
- **Matt Levine / Money Stuff**: daily, ~1,500–3,000 words, picks ~5 stories and runs each
  through hypothetical/Socratic decomposition with running neologisms and footnote tangents
  ([Harvard Magazine profile](https://www.harvardmagazine.com/2025/07/harvard-bloomberg-column-matt-levine),
  [policy punchline interview](https://www.policypunchline.com/episodes/2021/6/28/matt-levine-king-of-the-financial-newsletter)).
  The voice signature is the structural device — neologism + hypothetical conversation —
  more than the story selection.
- **Casey Newton / Platformer** (most relevant primary source): in April 2026 Platformer
  announced an explicit pivot
  ([Platformer schedule changes](https://www.platformer.news/platformer-schedule-changes-ai-automation/),
  [Nieman Lab coverage](https://www.niemanlab.org/2026/04/more-scoops-less-aggregation-and-analysis-how-casey-newton-is-revamping-his-newsletter-to-compete-with-ai/)) — dropping the *Side Quests* link
  roundup ("Techmeme does this better than we can, 24/7") and de-emphasizing news analysis
  because "chatbots are getting sharper at responding to questions about the implications
  of this or that news story". New rule: "instead of promising to show up on a set schedule,
  we're promising to show up when we find out something interesting." His bet: "the value
  in tech journalism is moving away from aggregation and predictability and toward original
  reporting and surprise." Announcement was Platformer's largest paid-sub day that year.

**The shared structural pattern**:

1. **Lead with a take, not a list.** None of these write "Top 10 stories of the day".
2. **Pick few stories.** Money Stuff at ~5 is the high end; Stratechery / The Diff often pick
   one. Aggregator-feel comes from giving every story equal weight.
3. **Tie everything back to a thesis or framework.** The reader is buying *consistency of
   judgment*, not coverage.
4. **Permanence preference.** Hobart's "still relevant in 5 years" filter is the explicit
   version; Thompson and Levine apply it implicitly.

**Applicability:** *Strongest finding in cluster B for our case.* The fastest way to stop
sounding like an aggregator is to **stop choosing 10 stories and start choosing 1–3**, and
make every story earn its place against a writer-persona thesis. The Newton/Platformer
2026 piece is essentially a primary source telling us that link roundups and routine
analysis are dead-end work in the LLM era — which is exactly what `claude-routines` is
producing right now.

### B3. Multi-agent editor+writer in LLM research

- **STORM (Stanford)**
  ([repo](https://github.com/stanford-oval/storm),
  [project page](https://storm-project.stanford.edu/research/storm/),
  [DigitalOcean walkthrough](https://blog.paperspace.com/stanford-oval-storm-wikipedia-writer-llm/)):
  not an editor-writer split — it's a **perspective-guided question-asker + writer** split.
  Modules: Knowledge Curation → Outline Generation → Article Generation → Polishing.
  *Co-STORM* extends this with Expert agents + a Moderator that injects "thought-provoking
  questions". Reported wins are vs single-agent baselines: +25% structure rating, +10%
  coverage in expert evaluation. **No explicit editor agent**; the discipline comes from the
  outline step.
- **CrewAI editor/writer cookbook patterns**
  ([CrewAI newsletter agent guide](https://araptus.com/blog/how-to-build-ai-newsletter-agent),
  [Multi-agent blog publisher](https://dev.to/aileenvl/building-a-multi-agent-blog-publishing-system-with-crewai-efn)):
  standard recipe is Researcher → Writer → Editor (sometimes + Editor-in-Chief that does
  prioritization and headline rewriting). These are *blueprints*, not benchmarks — they
  show the *shape* works for content production but no rigorous head-to-head vs a
  single-agent baseline is in the cookbook material.
- **Multi-agent ablations**
  ([Specialists or Generalists? essay grading](https://arxiv.org/pdf/2601.22386) —
  multi-agent better at weak essays, single-agent better mid-range;
  [Rethinking the Bounds of LLM Reasoning](https://arxiv.org/pdf/2402.18272) — finds that
  a single agent with good demonstrations matches the discussion frameworks;
  [Multi-Turn Multi-Agent Orchestration vs Single LLMs](https://arxiv.org/pdf/2509.23537) —
  orchestration matches strongest single model on GPQA/IFEval/MuSR but ablation flags
  herding/premature-consensus risks when agents see ongoing votes).

**Honest read of the literature**: there is **no clean published verdict** that an editor+
writer split beats a single agent with a good prompt and a good profile, for content-
generation tasks at our scale. STORM shows multi-stage *pipelining* (curate → outline →
write → polish) helps; that's not the same as a separate editor "agent". The CrewAI material
is enthusiastic but not benchmarked.

**Applicability:** prefer a **pipelined single agent** (or several call-stages with
distinct prompts) over true multi-agent. The mechanism that demonstrably helps in STORM is
**outline-before-write with explicit perspective enumeration**, not the agent persona split.
For us: one writer call, but force it to (1) enumerate angles, (2) write an outline,
(3) draft, (4) self-review against an editor rubric — same model, four steps. That gives us
STORM's benefit without the orchestration overhead of CrewAI-style multi-agent.

### B4. Reader-profile / personalization patterns

- **Profile-in-prompt** (lightweight retrieval-augmentation of past behavior into the prompt
  context) is the dominant pattern in recent personalized-LLM research
  ([Guided Profile Generation, arXiv 2409.13093](https://arxiv.org/pdf/2409.13093),
  [GRAVITY profile-grounded synthetic preferences, arXiv 2510.11952](https://arxiv.org/pdf/2510.11952),
  [Optimizing User Profiles via Contextual Bandits, arXiv 2601.12078](https://arxiv.org/pdf/2601.12078)).
  The "profile" is a natural-language summary of what the user cares about; it goes in the
  system prompt and steers selection + voice.
- **Pocket** ([Mozilla algotorial overview](https://blog.mozilla.org/en/internet-culture/deep-dives/break-free-from-the-doomscroll-with-pocket/),
  [Year-in-review](https://blog.mozilla.org/en/mozilla/year-in-review-how-were-curating-the-web-with-you-and-our-top-pocket-features/))
  uses "algotorial" — algorithm flags candidates from save/read signals, human editors pick
  the final set. Personalization runs locally on-device for privacy; the editorial layer is
  central, not optional.
- **Artifact's user-modeling** wasn't publicly documented in detail; the implementation
  reportedly ran on topics + sources + authors as the personalization vector
  ([Wikipedia](https://en.wikipedia.org/wiki/Artifact_(app))). The post-shutdown comment was
  *not* "personalization didn't work"; it was "the market isn't big enough" — suggesting the
  personalization itself was fine but the *product wrapper* didn't differentiate.

**Applicability:** for a single-user system, the right "profile" is a **hand-curated
natural-language description of Rafael's interests, decision context, and weight function**,
fed in the system prompt. That's literally the cheapest, most-evidenced personalization
approach in the literature, and it makes the editor-vs-writer-split question mostly moot —
the profile *is* the editor's standing brief.

### Applicability to claude-routines — Cluster B summary

**Reuse**:
- The Platformer 2026 pivot rationale, applied to us: drop equal-weight aggregation; the
  routine produces 1–3 stories that earn a take, not 10 that get summarized.
- STORM's pipeline pattern: outline → perspectives → draft → polish, all within a single
  agent (no orchestration framework).
- Profile-in-prompt personalization: a hand-written "what Rafael cares about, and how he
  weights impact" doc injected as the system prompt's editorial brief.
- Particle-style "rebuild from multiple sources" for any story that does survive selection —
  forces source diversity in the output.

**Skip**:
- True multi-agent editor+writer frameworks (CrewAI/AutoGen). No published benchmark
  proves they beat a single agent + good prompt for content tasks at our scale, and the
  orchestration overhead is real.
- Imitating product features from Artifact (celebrity AI audio, social comments) — we
  have one reader.

**Still open**:
- How to *operationalize* "impact on Rafael" — none of the surveyed work gives a recipe for
  encoding personal editorial weight beyond "describe it in the system prompt". Whether
  that's enough is empirical.
- Whether the "1–3 stories" cut should happen during ingestion (cheap, cuts work early) or
  during writing (richer judgment, more tokens). The literature doesn't decide this.

---

## Top 3 reusable patterns per cluster

**Cluster A (credibility)**
1. **Decouple source-trust from per-claim credibility (NATO Admiralty + MISP tagging).** Each
   story carries an inherited source grade *and* an independent claim-confidence grade.
2. **WP:RSP-style five-tier vocabulary** (generally-reliable / no-consensus /
   generally-unreliable / deprecated / blacklisted) maps directly onto routine behavior
   (ingest / ingest-and-flag / ignore / never-ingest / hard-block).
3. **Free academic signals stack** for any paper: Retraction Watch via Crossref (free,
   daily-updated) → Semantic Scholar Highly Influential Citations → CORE/SJR venue tier.
   All programmatic; replaces any need for NewsGuard-style paid academic licensing.

**Cluster B (editor + personalization)**
1. **Casey Newton's 2026 cut**: drop link aggregation, drop predictable analysis, lead with
   what's *interesting* — 1–3 stories not 10, take-first not list-first. This is the lever
   that makes the brief feel personal vs. aggregator.
2. **STORM's pipelined writing (within one agent)**: outline → enumerate perspectives →
   draft → polish, in sequence. Avoids multi-agent overhead; matches the only published
   wins on coverage + structure.
3. **Profile-in-prompt personalization**: hand-written editorial brief encoding what the
   reader cares about and how they weight impact, injected as the writer's standing
   context. Cheapest, best-evidenced personalization approach in the recent LLM literature.
