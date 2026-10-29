# SPIKE — Cloudflare Web Search API as a logged, scriptable search

> Status: **proposed 2026-10-05, parked for later.** Nothing built. Start at §5 step 1 (the
> freshness probe): its result decides how much of the rest is worth doing.

## 1. What Cloudflare shipped

[Web Search API](https://developers.cloudflare.com/changelog/post/2026-10-02-introducing-web-search-api/)
(beta, 2026-10-02), routed through AI Gateway. One call fronts three providers:

| Provider | List price | Pitch | Zero data retention |
|---|---|---|---|
| Ceramic (default) | $0.25 / 1k | low latency, low cost; descriptions up to 8,000 chars | yes |
| Exa | $7.00 / 1k | query-relevant excerpts for model context | no |
| Linkup | $5.00 / 1k | quick cited results from trusted sources | yes |

- **Worker binding:** `env.AI.websearch({ gatewayId, query, provider, limit })`, needing only
  `[ai] binding = "AI"` in `wrangler.toml`.
- **REST:** `POST https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/websearch/`, with a
  token holding Workers AI Read + AI Gateway Read.
- **Request:** `query` (1–1024 chars, required), gateway id (required), `provider`, `limit` (1–10,
  default 10), and an optional `byokAlias`.
- **Response:**
  `{ items: [{ url, title, description }], metadata: { query, requestId, latencyMs } }`.
- **Missing:** the docs list no date field and no recency, domain or country filter.
- **Billing:** from AI Gateway credits at the provider's list price, or bring your own provider
  key. There is no free tier.

Docs: [overview](https://developers.cloudflare.com/web-search/) ·
[providers](https://developers.cloudflare.com/web-search/providers/) ·
[how to use](https://developers.cloudflare.com/web-search/how-to-use/).

## 2. How the routines search today

The routines barely search, because they read feeds first. The writers use the built-in WebSearch
tool as a discovery aid and as the `[via snippet]` fallback when `tools/fetch.py` fails even
through the proxy. Watch's whole probe is one WebSearch call per due watch.

The numbers below come from `index/usage/*.jsonl`, `stop` records only (the `publish` record
duplicates the same session), from the start of usage recording to 2026-10-05:

| Routine | Runs | WebSearch calls | Per run |
|---|---|---|---|
| News | 21 | 36 | 1.7 |
| Sports | 3 | 8 | 2.7 |
| AI/ML | 6 | 1 | 0.2 |
| Science, Weekend, Evaluator | 9 | 0 | 0 |
| Watch | 131 | 11 | 0.1 (most fires stop at the cooldown gate) |

**This is not a cost play.** At these volumes even Exa comes to cents a month.

## 3. What it would add

1. **More text when a page is blocked.** When `fetch.py` exits non-zero, today's fallback is a
   short search snippet. A Ceramic description can carry up to 8,000 characters of the page. The
   citation still gets `[via snippet]`: a search description is not a fetch, and the honesty rule
   does not change.
2. **Searches become countable.** The built-in WebSearch leaves no trace in `/tmp/fetch.log`, so
   the footer and the evaluator cannot count searches or check what a `[via snippet]` citation
   rested on. A wrapper that logs every search fixes that.
3. **Plain Python can search.** Code such as `tools/watch/`, `tools/sources/health.py` or the
   evaluator could search without the model's built-in tool, for example to run the Watch probe
   in code and leave the model only the `match_when` judgment.
4. **Primary-source discovery.** Exa is built for this. It serves the pipeline's main editorial
   goal and the per-stream discovery quota.

## 4. Risks and open questions

- **Freshness (the deciding question).** With no date field and no recency filter, it is unknown
  whether Ceramic or Exa surface last-24h news as well as the built-in WebSearch. The docs cannot
  answer this; only the probe can.
- **No domain filter.** `site:` is not a documented parameter. Test whether `site:` inside the
  query string works, since the AI/ML arXiv fallback depends on it.
- **Beta.** The response shape may change. Pin it in the smoke test so a change fails loudly.
- **Exa keeps queries** (no zero data retention). The queries are about public news, so this is
  probably acceptable, but note it if Exa becomes the default.
- **Gateway setup.** The binding requires a gateway id. Do not assume `default` exists: check the
  account.

## 5. Plan

1. **Freshness probe (no code in the repo).** Pick about five queries:
   - two News headlines from the last 48h;
   - one Sports result;
   - one `watches.yml` query;
   - one primary-document lookup by bill, case or docket number.

   Run each through Ceramic and Exa, either via REST from a local shell or via a throwaway Worker.
   Run the same queries through WebSearch in a session. For each provider, record the top-5 URLs,
   how many are from the last 48h, and how many are primary sources.

   Decision:
   - **If it is as fresh as WebSearch:** make it the default search, and keep WebSearch as the
     fallback.
   - **If it is weaker:** use it only for the blocked-page fallback (§3.1) and for discovery
     (§3.4, Exa), and keep WebSearch for news recency.
2. **Worker route.** Add `POST /search` (`{ query, provider?, limit? }`) to **embed-proxy**:
   - The sandbox can already reach it; its egress allowlist lists exact hostnames, so a new
     capability goes on an allowlisted Worker, not a new host.
   - It already has the `[ai]` binding.
   - Its bearer already gates spend.
   - Pin the response contract in `test/smoke.mjs`, and follow the existing live-path deploy
     protocol: smoke first, then deploy, then check the live route.
3. **`tools/search.py`.** Model it on `fetch.py`:
   - It appends one JSON line per search to the fetch log, with `method: "search"`.
   - `tools/footer.py` builds "Feeds hit" by host and method, so search entries must be skipped
     there or reported on their own line. Otherwise they appear as fake feed hosts and skew the
     direct-vs-snippet split.
   - Check `tools/sources/lint.py` the same way.
   - Add tests, then run `python3 -m unittest discover -s tools/tests`.
4. **Prompts, last.**
   - **Writers:** change a `routines/_shared/` partial (most likely
     `feed-first-source-order.md`), run `python3 routines/assemble.py`, and commit. No
     RemoteTrigger is needed.
   - **Watch:** its full prompt is still stored in the trigger, so changing its probe needs a
     RemoteTrigger update. Alternatively, put Watch on a bootstrap shim first, as part of this
     work, so later changes are repo-only. The auto-mode classifier will want the change restated
     by Rafael in his own words.

## 6. Steps only Rafael can do

- Confirm which AI Gateway id exists on the account, or create one.
- Load AI Gateway credits, or set up a bring-your-own provider key (`byokAlias`).
- Run `wrangler deploy` for embed-proxy. The route must be live **before** any prompt that calls it
  reaches `main`, because the bridge publishes `main` within 10 minutes.
