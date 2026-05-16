# News Brief Pipeline — Handoff

> Generated 2026-05-14 from session `9dc2cb5e-c5f4-41ff-a991-a206ddd0199d` and plan `~/.claude/plans/prancy-finding-lerdorf.md`. Verify trigger IDs and feed status against current state before acting.

## Goal

Daily/weekly curated news briefs (AI/ML, markets, cyber, general) delivered via push (ntfy) and stored in this repo. Six remote Claude Code routines run on Anthropic's platform; briefs land here under `briefs/{stream}/{YYYY-MM-DD}.md`; a coverage ledger in MEMORY.md eliminates duplicate stories and tracks source health.

## Architecture

- **Routines:** 6 remote agents (claude.ai/code/routines), one trigger ID each. Schedules in UTC.
- **Storage:** this repo (`github.com/khalic-lab/claude-routines`, private). Briefs at `briefs/{stream}/{YYYY-MM-DD}.md` for streams: `morning`, `markets`, `ai-ml`, `cyber-papers`, `weekend`, `reviews`.
- **Delivery:** ntfy.sh topic `khalic-news-96034763387a`. Click-through currently points at Drive `webViewLink`; flips to GitHub blob URL when Phase 2 ships.
- **Sources:** feed-first (RSS/JSON APIs), snippet fallback. Direct HTML fetch from the routine sandbox is unreliable (403s).

## Current State (as of 2026-05-06)

- **Phase 1** (feed-first prompts): SHIPPED to all 6 routines.
- **Phase 1.5** (curl-first instruction + per-feed `Feeds hit` line in Coverage footer): SHIPPED to 4 routines (Morning, Cyber+Papers, Weekend, Evaluator). **Markets and AI/ML still need this patch.**
- **Phase 2** (briefs commit/push to GitHub): GATED on Phase 1 validation. 15 historical briefs (May 2-4) staged uncommitted in this repo.
- **Phase 3** (MEMORY.md coverage ledger + source-health log): GATED on Phase 2.
- **Phase 4 partial** (ntfy push): SHIPPED to same 4 routines as Phase 1.5.

## Open Work (Next Actions)

1. **Verify Phase 1.5 worked** — check today's briefs in Drive (`News Briefs/Overview/` etc.) for `Direct fetches: N | via-snippet citations: M` and `Feeds hit: …` lines. Pass criterion: N ≥ 5 (Overview) / N ≥ 3 (Cyber+Papers), most feeds `ok via curl`.
2. **Fan curl-first to Markets and AI/ML** — they fire daily and would benefit equally; only got skipped because the May 6 sweep bundled the 4 ntfy-notifying routines.
3. **Ship Phase 2** — commit the 15 staged briefs, update prompts to `git commit && git push` instead of (or alongside) Drive write, swap ntfy click-through to GitHub blob URL.
4. **Ship Phase 3** — initialize MEMORY.md coverage ledger + source-health sections; add read step to writer prompts (skip duplicate stories, skip blocked sources); Evaluator updates weekly.
5. **Decide on email** — Phase 4 originally planned Resend email alongside ntfy. Currently only ntfy is wired. Decide whether to add email back or stay push-only.

## Decisions Worth Remembering

### Feed-first, not HTML-first

Original design fetched article HTML directly. Audit 2026-05-03 found 0/18 direct fetches in Morning Overview. Pivoted to feed endpoints (arXiv RSS, NVD JSON, CISA KEV, Quanta, Nature, etc.). 2026-05-04 Cyber+Papers run still showed feeds 403'ing via WebFetch — confirmed sandbox-level WebFetch issue, not feed availability (feeds verified live from a planning session that day). Phase 1.5 added curl-first because `Bash{curl}` egresses through a different path than WebFetch and tends to succeed where WebFetch fails.

### Coverage footer is the production health metric

The system has no other way to know if it's succeeding. The `Direct fetches: N | via-snippet: M` line plus the per-feed `Feeds hit: {ok via curl|ok via WebFetch|fail — HTTP NNN}` line is what triggers escalation if curl ALSO starts failing (= egress proxy is the wall).

### Sunday Markets skip

Cron changed from `30 18 * * *` to `30 18 * * 1-5`. Markets close Friday; Sunday briefs were stale recycles.

### Evaluator is the only writer to MEMORY.md

Phase 3 design: writers READ MEMORY.md to skip duplicates and blocked sources; only Evaluator (Sunday) WRITES. Conflict-free, no need for locking.

### Sibling brief lookup → MEMORY.md grep

Weekend brief originally consulted ~28 prior briefs via `gh api .../contents/...` (one call per file). Phase 3's coverage ledger collapses this to one `grep $story_hash` over the last 7 days — O(1) instead of O(28).

### Evaluator runs Opus, others run Sonnet

Evaluator (`trig_01F5npsKTQTLKekAZ5BczKtG`) is on `opus-4-7`. Others on `sonnet-4-6`. Preserve when updating triggers — `RemoteTrigger update` overwrites `session_context.model` if you include it.

## Gotchas

1. **`RemoteTrigger update` payload requires full `session_context`.** Body MUST include `environment_id` (`env_011CUNry3hmavNvADoLNP9D4`) AND `session_context` (model, sources, allowed_tools). Partial body returns HTTP 400: `translate job_config v1→v2: job_config missing ccr.environment_id`.
2. **WebFetch ≠ Bash{curl} from inside routines.** WebFetch 403s on public feeds the sandbox should reach. Curl tends to work. Always try `Bash{curl -fsSL <feed>}` BEFORE WebFetch.
3. **ntfy topic is unguessable but not authenticated.** Anyone with `khalic-news-96034763387a` can publish or subscribe. Don't share casually.
4. **Anthropic git proxy is set up** (`/web-setup` already run), so Phase 2's `git push` from inside routines works without further auth.
5. **Cron is UTC.** Convert from Europe/Zurich (UTC+2 summer / UTC+1 winter). 7am CEST = `0 5 * * 1-5`.

## Key Paths / IDs

### Trigger IDs
- Morning Overview: `trig_012KfuF2Fc8KxNRS9KT1iuYb` (sonnet-4-6)
- Markets: `trig_01GBugAS5qw88yQK3tv8kKWx` (sonnet-4-6) — **needs curl-first patch**
- AI/ML: `trig_01QVL6eSmHTUrmnSLHrpNN9Q` (sonnet-4-6) — **needs curl-first patch**
- Cyber+Papers: `trig_01YLiCr5YJ2XNh2QyPbkyzQP` (sonnet-4-6)
- Weekend: `trig_01XKzge4DxP6wTjLwtkoYeqj` (sonnet-4-6)
- Evaluator: `trig_01F5npsKTQTLKekAZ5BczKtG` (**opus-4-7** — preserve when updating)

### Environment
- `environment_id`: `env_011CUNry3hmavNvADoLNP9D4`

### ntfy
- Topic: `khalic-news-96034763387a`
- Subscribe: ntfy iOS app or `https://ntfy.sh/khalic-news-96034763387a`

### Repo
- This repo: `github.com/khalic-lab/claude-routines` (private)
- Brief layout: `briefs/{morning,markets,ai-ml,cyber-papers,weekend,reviews}/{YYYY-MM-DD}.md`

### Resources
- Plan doc: `~/.claude/plans/prancy-finding-lerdorf.md`
- Origin session: `~/.claude/projects/-Users-rflnogueira--config/9dc2cb5e-c5f4-41ff-a991-a206ddd0199d.jsonl` (7.6 MB)
- Memory note: `~/.claude/projects/-Users-rflnogueira--config/memory/news-brief-pipeline.md`
- Routines dashboard: `https://claude.ai/code/routines`
- Drive output: `News Briefs/{Overview,Markets,AI-ML,Cyber-Papers,Weekend,Reviews}/`

### Verified Feed Endpoints (confirmed live 2026-05-04)
- arXiv RSS: `https://export.arxiv.org/rss/{cs.LG,cs.AI,cs.CL,cs.CV,stat.ML}`
- arXiv API: `https://export.arxiv.org/api/query?search_query=cat:cs.LG&...`
- NVD JSON 2.0: `https://services.nvd.nist.gov/rest/json/cves/2.0?pubStartDate=...&pubEndDate=...`
- CISA KEV: `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json`
- Quanta: `https://www.quantamagazine.org/feed/`
- Nature: `https://www.nature.com/nature.rss` (also nphys, natastron, nm)
- Al Jazeera: `https://www.aljazeera.com/xml/rss/all.xml`
- ECB FX: `https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml`
- Semantic Scholar: `https://api.semanticscholar.org/graph/v1/paper/search`
- SRF: `https://www.srf.ch/news/bnf/rss/1646`
- Le Temps: `https://www.letemps.ch/articles.rss`

### Confirmed Blocked / Unavailable
bioRxiv, medRxiv, Science.org, Reuters, Yahoo Finance, Spiegel, paywalled news.
