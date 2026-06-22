# Prior-Art Survey — Temporal Grounding & Date Handling in LLM News/RAG Pipelines

Compiled 2026-06-08. Covers ground **not already in** the two prior docs (AUDIT-2026-05-31 and
PRIOR-ART-2026-05-31-credibility-and-editor). Four areas surveyed: (1) anchoring LLMs to
"now", (2) event-time vs publish-time vs ingestion-time in news IR, (3) temporal reasoning
failure modes and mitigations, (4) production AI-news systems. Closes with concrete
recommendations for this pipeline.

---

## 1. How LLM systems anchor "now"

### 1a. Universal standard: explicit date injection

LLMs have no internal clock. Without an explicit date in context, a model reasons from
training-time patterns — a form of temporal hallucination that is silent and hard to detect.
The universal mitigation is to inject the current date (or "as-of" date) into the system
prompt on every call. This is now so standard it is reflected in vendor-published production
system prompts.

**Anthropic's own published system prompt** (the verbatim system prompt released for each
Claude model at [`platform.claude.com/docs/en/release-notes/system-prompts`](https://platform.claude.com/docs/en/release-notes/system-prompts))
uses a template variable:

```
"It answers the way a highly informed individual in Jan 2026 would if talking to someone
from {{currentDateTime}}"
```

The `{{currentDateTime}}` placeholder is substituted at runtime before the prompt reaches
the model. Claude Opus 4.8, Claude Opus 4.7, and Claude Sonnet 4.6 all use this exact
pattern. The variable resolves to a date-time string; the model then has an explicit "you
are speaking to someone who lives on this date" anchor.

**OpenAI's community guidance** confirms the same pattern. Their developer forum and cookbook
examples use the system-prompt field to pass `datetime.now().isoformat()` on each API call.
The canonical code pattern (from a Jan 2026 production guide by Damian Galarza,
[`damiangalarza.com/posts/2026-01-07-llm-date-time-context-production/`](https://www.damiangalarza.com/posts/2026-01-07-llm-date-time-context-production/)):

```ruby
def build_user_prompt(users)
  <<~PROMPT
    Today's date is: #{Date.today.iso8601}
    User timezone is: America/New_York
    Request timestamp is: #{Time.now.iso8601}
    [instructions]
  PROMPT
end
```

**Format guidance**: ISO 8601 (`YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ`) is the prescribed
format. This is also the format the pipeline already uses in its `_posts/` slugs and dedup
index (`YYYY-MM-DD`), so no format conversion is needed.

### 1b. Per-call vs one-time injection

A nuance raised in a dev.to piece ([Why Your Agent Doesn't Know What Time It Is](https://dev.to/terrapin88/why-your-agent-doesnt-know-what-time-it-is-15j4)): a
single-session system prompt injection sets the date once; if the session or conversation
is long-lived across days, the date goes stale. The recommended mitigation for long-running
agents is to refresh temporal context on each turn. For a compose-time routine that runs
once per invocation and exits, this is a non-issue — a single injection at session start is
sufficient.

### 1c. Tool-based date retrieval

The alternative to prompt injection is giving the agent a callable `get_current_date()`
tool. Reviews of this pattern (e.g.,
[Riccardo Tartaglia's Medium guide](https://medium.com/@riccardo.tartaglia/teaching-your-llm-to-tell-time-a-practical-guide-to-llm-tool-integration-a52436f68a58))
position it as complementary to, not a replacement for, prompt injection:

| Approach | Advantage | Disadvantage |
|---|---|---|
| System prompt injection | Zero overhead; no tool calls | Stale if session is long-lived |
| Tool-based retrieval | Always fresh; agent can self-query | Adds latency; requires tool definition |

For the `claude-routines` pipeline, the right scope for a date helper tool is **date
arithmetic** — computing deltas ("how many days ago was this?"), window comparisons ("is
this story within the 30-day dedup horizon?"), ISO 8601 parsing of relative expressions.
The papers below show that is precisely where LLMs fail independently of knowing today's
date (see §3).

---

## 2. Event-time vs publish-time vs ingestion-time

Three distinct dates attach to any news story, and conflating them causes both retrieval
errors and writer confusions.

### 2a. The canonical three-date model

| Date type | Definition | Source / Standard |
|---|---|---|
| **event_date** | When the real-world event occurred | GDELT `SQLDATE`; TimeML `TIMEX3 DATE`; OpenAI knowledge-graph cookbook `valid_at` |
| **publish_date** | When the source article was published / broadcast | schema.org `datePublished`; Perplexity API `search_after_date_filter` |
| **ingestion_date** (compose_date) | When the pipeline processed and indexed the story | GDELT `DATEADDED`; temporal-RAG `created_at`; this pipeline's `date` field in the JSONL |

**GDELT's codebook** (v2.0, [`data.gdeltproject.org`](http://data.gdeltproject.org/documentation/GDELT-Event_Codebook-V2.0.pdf))
makes the event vs ingestion distinction explicit:

> "SQLDATE: The date the event took place in YYYYMMDD format."
> "DATEADDED: Date event was added to the main GDELT database in YYYYMMDDHHMMSS format."
> "Because news coverage published today could add events from the distant past, the
> DATEADDED field will carry today's date while SQLDATE contains the date the event
> actually took place."

GDELT is the largest public event/news temporal dataset; their naming is the de-facto
standard for this distinction.

### 2b. TimeML / TIMEX3 — formal annotation standard for news NLP

TimeML ([ISO 24617-1](https://en.wikipedia.org/wiki/TimeML)) is the ISO-standard markup
language for temporal expressions in news text, originally developed for AQUAINT QA systems.
It annotates four element types: `EVENT`, `TIMEX3` (times/dates/durations/sets), `SIGNAL`,
and `LINK`. `TIMEX3` encodes the *expressed* date in the text — for instance, "last
Tuesday" normalized to `2026-06-02` via `value="2026-06-02"`. The `type` attribute
distinguishes `DATE`, `TIME`, `DURATION`, and `SET` (recurring).

The **TimeBank corpus** (the reference gold standard, ~65K tokens of English newswire) was
built on this scheme. While TimeML is designed for annotation/tagging rather than direct
pipeline metadata, its core insight is directly applicable: news text contains at least
two distinct date references — the *publication* date of the article and the *event* date
of what it describes — and conflating them corrupts temporal queries.

### 2c. schema.org and the four-date vocabulary

For structured metadata on the open web, [schema.org](https://schema.org) defines these
properties for `NewsArticle` and `Event`:

- **`datePublished`** — "The date of first publication or broadcast"
- **`dateModified`** — "The date on which the work was most recently modified"
- **`startDate`** / **`endDate`** — The event's temporal bounds (on `Event` type)

Google Search's structured data documentation ([developers.google.com](https://developers.google.com/search/docs/appearance/structured-data/article))
requires `datePublished` and `dateModified` for NewsArticle. The Google Knowledge Graph,
however, has been retreating from event entities — in June 2025 the KG's "event" category
dropped 76.91%, with the average event entity lifespan falling from 839 days pre-COVID to
124 days post-2020 ([Search Engine Land](https://searchengineland.com/google-great-clarity-cleanup-knowledge-graph-ai-future-460836)).

### 2d. Temporal RAG metadata schemas in production

Research on production temporal RAG systems (from the Towards Data Science post
[RAG Is Blind to Time — I Built a Temporal Layer to Fix It in Production](https://towardsdatascience.com/rag-is-blind-to-time-i-built-a-temporal-layer-to-fix-it-in-production/),
corroborated by the `temporal-rag` GitHub library [`github.com/Emmimal/temporal-rag`](https://github.com/Emmimal/temporal-rag))
converges on a minimal recommended schema per indexed document:

| Field | Type | Purpose |
|---|---|---|
| `created_at` | timestamp | Ingestion / compose time (= GDELT `DATEADDED`) |
| `t_published` | timestamp (optional) | Source publication date (= schema.org `datePublished`) |
| `valid_from` | timestamp | When the content became / became true |
| `valid_until` | timestamp | Expiry / deprecation date |
| `kind` | enum | `STATIC` / `VERSIONED` / `EVENT` — distinguishes timeless content from time-bounded events |
| `version` | int | Revision counter for superseded documents |

The **OpenAI knowledge-graph cookbook** ([developers.openai.com](https://developers.openai.com/cookbook/examples/partners/temporal_agents_with_knowledge_graphs/temporal_agents))
uses `valid_at` / `invalid_at` per individual fact-triplet, plus an `invalidated_by` link
to the successor entry. The practical advice in that cookbook: *"Use the reference or
publication date as the current time when determining the `valid_at` and `invalid_at`
dates"* — i.e., anchor temporal extraction to the article's own `datePublished`, not the
query time.

**Important scoping note**: most of the temporal-RAG machinery (reranking, decay scoring,
validity multipliers, the `final_score = α·sim + (1-α)·f_time` formula) is designed for
*query-time retrieval* — re-ranking a vector-store search on each user request. The
`claude-routines` pipeline is a **compose-time writer**: it fires, researches, writes one
brief, and exits. The valuable transfer from temporal RAG is the **schema** (track the
three dates per story) and the **document kind** classification (`EVENT` vs `VERSIONED` vs
`STATIC`), not the reranking stack.

---

## 3. Temporal reasoning failure modes in LLMs

### 3a. Four distinct failure modes

Research from 2024–2026 identifies four failure modes that are relevant to a news pipeline:

**1. Knowledge cutoff hallucination** — The model confidently answers questions about
post-cutoff events from training priors. Standard mitigation: inject current date + use RAG
for post-cutoff facts. (Universal consensus; Anthropic, OpenAI, and every framework
addresses this.)

**2. Temporal blindness in multi-turn agents** — From *"Your LLM Agents are Temporally Blind"*
([arXiv:2510.23853](https://arxiv.org/abs/2510.23853), dataset: TicToc, 76 scenarios):

> "Agents skip necessary tool calls because they fail to recognise when information has
> become outdated due to elapsed time."

No model exceeded 65% normalized alignment with human temporal perception even when given
timestamp information. Simple prompting was insufficient; the authors recommend
post-training alignment for agents that must make fresh-vs-stale judgments. For a
compose-time routine (no multi-turn session), this failure mode is less acute — but it
explains why writer routines sometimes re-cover old stories if they lack explicit date
context about the coverage window.

**3. Date tokenization fragmentation** — From *Date Fragments: A Hidden Bottleneck of
Tokenization for Temporal Reasoning* ([arXiv:2505.16088](https://arxiv.org/abs/2505.16088),
EMNLP 2025):

> "Modern BPE tokenizers frequently split calendar dates into meaningless fragments (e.g.,
> '20250312' → '202', '503', '12'), causing up to 10-point accuracy drops on uncommon
> dates."

Fragmentation is worst for historical (pre-2000) and futuristic (post-2025) dates — i.e.,
the exact range a news-research routine might encounter when dating events. The mitigation
is to always express dates as separated `YYYY-MM-DD` (hyphen-delimited), which tokenizes
cleanly into recognizable year/month/day segments, rather than as unseparated numeric
strings. ISO 8601 with hyphens (not `20250312`) is the robust format. A companion paper
([arXiv:2603.19017](https://arxiv.org/abs/2603.19017)) confirms that in high-resource
language settings the bottleneck is representational, but in lower-resource settings
(non-Gregorian calendars, minority languages) fragmentation dominates.

**4. Recency bias in retrieval/reranking** — From *Do Large Language Models Favor Recent
Content?* ([arXiv:2509.11353](https://arxiv.org/abs/2509.11353)):

> "Fresh passages are consistently promoted, shifting ranking positions by up to 95 ranks
> in listwise experiments. The mean publication year of top-10 results shifts forward by up
> to 4.78 years when artificial dates are added."

All seven tested models (GPT-3.5-turbo through Qwen-2.5) showed this bias. This is a
*retrieval* failure mode. For a compose-time pipeline that uses the dedup index as a
similarity-threshold gate (not a reranked retrieval), the implication is: if the writer
uses LLM-based reranking anywhere (e.g., deciding which of several wire sources to cite),
the recency bias will favor the most-recently-dated article even if it is thinner. Awareness
is the primary mitigation; explicit scoring against content quality separate from date is
the structural one.

### 3b. Known effective mitigations

| Technique | Evidence | Applicability |
|---|---|---|
| Explicit current-date block in system prompt | Universal production standard (Anthropic, OpenAI) | HIGH — trivial to add |
| ISO 8601 hyphen-separated date format | arXiv:2505.16088 (EMNLP 2025) | HIGH — format discipline |
| Metadata `event_date` separate from `publish_date` | GDELT, TimeML, temporal-RAG schemata | HIGH — schema change |
| Date arithmetic via deterministic tool (not LLM) | arXiv:2510.23853; practitioner consensus | MEDIUM — scoped to delta calculations |
| Explicit timeline / "as-of" framing in output | Temporal knowledge graph cookbooks (OpenAI) | HIGH — output discipline |
| Recency prior for freshness filtering | arXiv:2509.19376 (achieves 1.0 accuracy on freshness tasks) | LOW-MEDIUM — compose-time, not query-time |

---

## 4. Production AI-news handling of dating and recency

### Bloomberg Terminal AI Summary

Bloomberg's AI Summary for Terminal users is explicitly described as a **timestamped
point-in-time snapshot** ([Bloomberg press release](https://www.bloomberg.com/company/press/investors-harness-bloombergs-expanded-ai-tools-to-discover-and-summarize-news/)):

> "A concise yet comprehensive timestamped summary of relevant recent news and thematic
> developments about a company, distilling large volumes of financial news from verified
> sources into high-value summaries grouped by financial analysis topics."

Users are instructed to "note the timestamp" when using the summary. The temporal anchor
is the timestamp of the summary *generation*, not the constituent articles. Bloomberg also
notably sponsored the `Temporal` JavaScript proposal ([Bloomberg JS Blog](https://bloomberg.github.io/js-blog/post/temporal/))
— their engineering investment in correct date/time handling reflects operational priority.
Technical details of their LLM pipeline are not public.

### Perplexity API — published temporal filtering

Perplexity's API ([docs.perplexity.ai/docs/search/filters/date-time-filters](https://docs.perplexity.ai/docs/search/filters/date-time-filters))
exposes six date/time parameters distinguishing the three date types:

| Parameter | Filters on |
|---|---|
| `search_after_date_filter` | Original publication date |
| `search_before_date_filter` | Original publication date |
| `last_updated_after_filter` | Last modification date |
| `last_updated_before_filter` | Last modification date |
| `search_recency_filter` | Relative (`hour`/`day`/`week`/`month`/`year`) |

This is the most detailed public API design for the publish-time vs modified-time
distinction in a production AI-news system. Results display both `date` (publication) and
`last_updated` fields. The publish-vs-modified distinction maps directly to schema.org's
`datePublished` vs `dateModified`.

### Reuters News Tracer

Reuters' News Tracer (2018–present) scans 700M+ tweets daily and performs credibility
assessment on breaking-news clusters. Temporal handling is implicit: the system alerts
journalists to potential news breaks in near-real-time, with reports of an 8–60 minute
head start over manual monitoring. Technical date handling details are not public, but the
architectural implication is that the detection timestamp (ingestion time) and the claimed
event time are treated as separate signals for credibility — a recent tweet claiming an
"old" event is scored differently than a cluster of tweets converging on a fresh event.

### GDELT — open public event database

GDELT (Global Database of Events, Language and Tone) is the most transparently documented
public news-event temporal system. Its clear codification of `SQLDATE` (event time) vs
`DATEADDED` (ingestion time) — with a specific note that post-April-2013 records are stored
by *detection date* rather than *event date* — is the clearest published example of the
event/ingestion split and the hazards of conflating them.

---

## Applicability to this pipeline

### What "compose-time" changes vs "query-time"

The pipeline runs as a compose-time writer: a routine fires, researches from web sources,
writes a brief, records to the JSONL index, and exits. It does **not** run query-time
retrieval over the JSONL. The only place query-time logic applies is Step A of DEDUP.md,
where the embedding check is a similarity threshold against the rolling index — and that
check already uses `--since 30` (a hard date window), which is the temporal RAG "recency
prior" applied correctly and deterministically.

### Existing schema for context

Current JSONL schema per story (from `index/stories/YYYY-MM-DD-SLUG.jsonl`):

```json
{
  "id": "2026-05-02-ai-ml-...",
  "date": "2026-05-02",          ← compose/ingestion date
  "stream": "ai-ml",
  "headline": "...",
  "summary": "...",
  "url": "...",
  "source_domain": "...",
  "tier": null,
  "tags": [],
  "thread_id": "...",
  "first_seen_date": "2026-05-02",
  "embedding_model": "bge-m3"
}
```

`date` = compose date (when the brief was written). `first_seen_date` = earliest date the
story-thread appeared in the index. Neither is the *event date* — the date the described
event actually occurred. `url` is present but is the primary-source URL, not structured
event metadata.

---

## Recommendations

Three changes, in priority order.

### (a) Inject an explicit as-of date block — HIGH priority, minimal effort

Every routine's system prompt / session context should open with an explicit current-date
block in ISO 8601 format:

```
Today's date: {YYYY-MM-DD} (Europe/Zurich, UTC+2)
Coverage window: stories from the past 7 days (since {YYYY-MM-DD}).
```

**Rationale**: This is the universal standard (Anthropic's own production system prompt
uses `{{currentDateTime}}`; OpenAI cookbooks codify it). It prevents the model from guessing
the date from training priors, anchors relative expressions like "yesterday" and "last
week", and removes the ambiguity in `[ongoing since YYYY-MM-DD]` tags — the model needs
to know today's date to correctly compute the staleness gap. The routine already passes
`{YYYY-MM-DD}` as the compose date in DEDUP.md; using the same value as the as-of anchor
is consistent.

Always use hyphen-separated ISO 8601 (`2026-06-08`, not `20260608`). The arXiv:2505.16088
finding shows tokenization fragmentation drops accuracy up to 10 points for unseparated
numeric date strings.

### (b) Add `event_date` to the story schema — HIGH priority, moderate effort

Add an optional `event_date` field (ISO 8601 `YYYY-MM-DD`) to the JSONL schema:

```json
{
  "date": "2026-06-08",           ← compose date (unchanged)
  "first_seen_date": "2026-06-01", ← first coverage date (unchanged)
  "event_date": "2026-05-29",     ← NEW: when the described event occurred
  ...
}
```

**Rationale and mapping**:

- **event_date** = GDELT `SQLDATE` = TimeML TIMEX3 event anchor = schema.org `Event.startDate`
- **date** (existing) = GDELT `DATEADDED` = ingestion/compose date
- **first_seen_date** (existing) ≈ publish date of the *first* source to cover it

The `event_date` is specifically needed for: (1) stories where the event predates the
source article by days (e.g., an arXiv paper posted May 29 about a result completed in
March — the brief runs June 1, `date`=June 1, `first_seen_date`=June 1, `event_date`=May 29);
(2) the `[ongoing since YYYY-MM-DD]` ONGOING tagging — the date in that tag should be
the event's first occurrence date, not the first *coverage* date; (3) avoiding the
"two-week-old story framed as breaking" failure mode.

**The repeat problem is already fixed** (AUDIT established this). `event_date` is not a
new repeat fix — it augments the existing dedup machinery by letting the writer accurately
frame a story's age ("this event occurred on X; we first covered it on Y; today is Z")
rather than conflating those three.

Population strategy: writers set `event_date` when they can determine it from the source
(arXiv submission date, CVE publication date, announcement date). It is nullable — existing
records remain valid without it; the field defaults to null and the dedup/record tooling
continues to work unchanged.

### (c) Add a deterministic date-arithmetic helper — MEDIUM priority, scoped

A small deterministic tool (callable by the writer routine) that handles:

- `days_since(date_str)` → int (how many days ago was this event?)
- `within_window(date_str, days=7)` → bool (is this story within the coverage window?)
- `parse_relative(expression, anchor_date)` → ISO 8601 (resolves "last Tuesday" → "2026-06-03")

**Rationale**: This is not "give the model a way to get today's date" — (a) already covers
that. This is scoped to *date arithmetic*, which is a known LLM failure mode independent
of knowing today's date. arXiv:2510.23853 (TicToc) shows LLMs fail at judging whether
information is fresh even when given timestamps; arXiv:2505.16088 shows fragmented date
tokens produce reasoning errors on arithmetic. A deterministic helper side-steps both
failures: the model decides *when* to call it (what dates to compare), but the computation
is exact.

Practically: `days_since(event_date)` tells the writer routine "this event happened 10 days
ago" deterministically, removing any LLM date-arithmetic inference from the temporal framing
in the brief.

---

## Top patterns by applicability

1. **(Universal standard) Explicit as-of date in system prompt** — ISO 8601, `{{currentDateTime}}`
   pattern from Anthropic's own published prompts. Already-present in the pipeline's date
   convention; requires wiring into the session_context as a literal line.

2. **(GDELT/TimeML/schema.org) Three-date model** — `event_date` / `publish_date` /
   `ingestion_date` as distinct schema fields. The existing JSONL captures ingestion only;
   adding `event_date` closes the gap.

3. **(Temporal-RAG, scoped) Document kind classification** — `EVENT` (time-bounded,
   expires), `VERSIONED` (superseded by newer), `STATIC` (timeless). The existing `tier`
   field in the JSONL is currently null; it is already the right slot for this kind of
   classification, possibly doubling as document kind rather than adding a new field.

4. **(Production: Perplexity API) Publish vs modified date exposure** — public evidence
   that publish-time and last-modified-time are distinct query parameters in a production
   AI-news system, validating the three-date model as operationally real, not theoretical.

5. **(arXiv:2505.16088) Hyphen-separated ISO 8601 for all date tokens** — simple format
   discipline that provably reduces tokenization fragmentation. No schema change; purely
   a prompt/output convention.

---

## Still open

- Whether `event_date` should be extracted by the writer LLM (cheap, occasionally wrong) or
  derived deterministically from metadata (exact for arXiv/CVE/official filings, unavailable
  for wire stories). The deterministic path covers the pipeline's strongest content categories
  (arXiv IDs, CVE NVD dates); a best-effort LLM extraction covers the rest with nullable fallback.
- Whether the existing `tier` field (currently null in all indexed stories) should be repurposed
  as the document kind (`EVENT`/`VERSIONED`/`STATIC`) rather than as the T1/T2/T3 source-tier
  originally envisioned. Two semantically distinct uses fighting for one field.
- The query-time dedup check (`dedup.py check --since 30`) already implements the most important
  temporal boundary: a hard 30-day window. Whether that window should adapt per document kind
  (shorter for `EVENT`, longer for `STATIC`) is an open design question not addressed by the
  literature surveyed here.

---

## Sources

- Anthropic published system prompts: [platform.claude.ai/docs/en/release-notes/system-prompts](https://platform.claude.com/docs/en/release-notes/system-prompts)
- Damian Galarza — LLM Date/Time Context in Production (Jan 2026): [damiangalarza.com](https://www.damiangalarza.com/posts/2026-01-07-llm-date-time-context-production/)
- Dev.to — Why Your Agent Doesn't Know What Time It Is: [dev.to/terrapin88](https://dev.to/terrapin88/why-your-agent-doesnt-know-what-time-it-is-15j4)
- Riccardo Tartaglia — Teaching Your LLM to Tell Time: [medium.com/@riccardo.tartaglia](https://medium.com/@riccardo.tartaglia/teaching-your-llm-to-tell-time-a-practical-guide-to-llm-tool-integration-a52436f68a58)
- GDELT Event Codebook V2.0 (2015): [data.gdeltproject.org](http://data.gdeltproject.org/documentation/GDELT-Event_Codebook-V2.0.pdf)
- TimeML Wikipedia: [en.wikipedia.org/wiki/TimeML](https://en.wikipedia.org/wiki/TimeML)
- schema.org datePublished: [schema.org/datePublished](https://schema.org/datePublished)
- schema.org dateModified: [schema.org/dateModified](https://schema.org/dateModified)
- Google structured data / NewsArticle: [developers.google.com](https://developers.google.com/search/docs/appearance/structured-data/article)
- RAG Is Blind to Time (Towards Data Science): [towardsdatascience.com](https://towardsdatascience.com/rag-is-blind-to-time-i-built-a-temporal-layer-to-fix-it-in-production/)
- temporal-rag library (GitHub): [github.com/Emmimal/temporal-rag](https://github.com/Emmimal/temporal-rag)
- ScrapingAnt — Temporal Vector Stores: [scrapingant.com](https://scrapingant.com/blog/temporal-vector-stores-indexing-scraped-data-by-time-and)
- OpenAI knowledge-graph temporal agents cookbook: [developers.openai.com](https://developers.openai.com/cookbook/examples/partners/temporal_agents_with_knowledge_graphs/temporal_agents)
- Tomoro.ai — Temporal Agents, Why Your Knowledge Needs a Timeline: [tomoro.ai](https://tomoro.ai/insights/temporal-agents-why-your-knowledge-needs-a-timeline)
- arXiv:2510.23853 — Your LLM Agents are Temporally Blind: [arxiv.org/abs/2510.23853](https://arxiv.org/abs/2510.23853)
- arXiv:2505.16088 — Date Fragments, Hidden Bottleneck of Tokenization (EMNLP 2025): [arxiv.org/abs/2505.16088](https://arxiv.org/abs/2505.16088)
- arXiv:2603.19017 — Tokenisation or Representation for Temporal Reasoning: [arxiv.org/abs/2603.19017](https://arxiv.org/abs/2603.19017)
- arXiv:2509.11353 — Recency Bias in LLM-Based Reranking: [arxiv.org/abs/2509.11353](https://arxiv.org/abs/2509.11353)
- arXiv:2509.19376 — Solving Freshness in RAG with a Recency Prior: [arxiv.org/abs/2509.19376](https://arxiv.org/abs/2509.19376)
- arXiv:2510.13590 — RAG Meets Temporal Graphs (TG-RAG): [arxiv.org/abs/2510.13590](https://arxiv.org/abs/2510.13590)
- arXiv:2507.13396 — DyG-RAG, Dynamic Event-Centric Reasoning: [arxiv.org/abs/2507.13396](https://arxiv.org/abs/2507.13396)
- Bloomberg AI Summary press release: [bloomberg.com](https://www.bloomberg.com/company/press/investors-harness-bloombergs-expanded-ai-tools-to-discover-and-summarize-news/)
- Bloomberg Temporal JS blog: [bloomberg.github.io/js-blog/post/temporal](https://bloomberg.github.io/js-blog/post/temporal/)
- Perplexity date/time filters API docs: [docs.perplexity.ai](https://docs.perplexity.ai/docs/search/filters/date-time-filters)
- Nieman Lab — three newsrooms on AI summaries (2025): [niemanlab.org](https://www.niemanlab.org/2025/06/lets-get-to-the-point-three-newsrooms-on-generating-ai-summaries-for-news/)
- Search Engine Land — Google KG Clarity Cleanup (2025): [searchengineland.com](https://searchengineland.com/google-great-clarity-cleanup-knowledge-graph-ai-future-460836)
