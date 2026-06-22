# 03 · Compose-time dedup — `tools/dedup/dedup.py`

Dedup runs **inside the ephemeral cloud sandbox at compose time** — the only moment a writer can
decide "skip / thread / keep". The sandbox has HTTPS-allowlist egress only, so the index lives in
the git repo (`index/stories/*.jsonl`) and embeddings come from the allowlisted `embed-proxy`
Worker. Verdict precedence and thresholds are from `decide_verdict()`.

```mermaid
flowchart TD
  cand["Writer compose (cloud sandbox)<br/>after feed sweep → candidate stories<br/>{headline, summary, url, date}"]
  cand -->|"dedup.py check --candidates --since 30"| embed
  embed["embed_text(headline, summary)<br/>POST embed-proxy → @cf/baai/bge-m3 (EMBED_DIM=1024)<br/>cache: /tmp/dedup-embcache.json"]
  embed --> load
  load["load recent index slice<br/>index/stories/*.jsonl · SINCE=30d · KEEP_DAYS=40"]
  load --> dv

  subgraph dv["decide_verdict() — precedence order"]
    direction TB
    s1{"exact-source match?<br/>same canonical URL or arXiv id<br/>as a recent story"}
    s1 -->|"yes"| rep["REPEAT (cosine-independent)"]
    s1 -->|"no"| dp{"_distinct_paper guard:<br/>arXiv id mismatch on the match?"}
    dp -->|"yes"| strip["strip continuation<br/>match_reason: distinct-paper<br/>first_seen_date: null"]
    dp -->|"no"| cos{"max cosine vs recent vectors"}
    cos -->|"sim ≥ 0.945 (T_HIGH)"| rep
    cos -->|"0.72 ≤ sim &lt; 0.945"| ong["ONGOING<br/>thread to first_seen<br/>frame as [ongoing since …]"]
    cos -->|"sim &lt; 0.72 (T_LOW)"| new["NEW — fresh thread_id"]
  end

  rep --> compose
  strip --> compose
  ong --> compose
  new --> compose
  compose["compose _posts/{d}-{slug}.md honouring verdicts<br/>drop REPEAT · thread ONGOING · NEW as normal"]
  compose -->|"after Write"| record
  record["dedup.py record --stories --date --slug<br/>→ index/stories/{d}-{slug}.jsonl<br/>validates writer thread_id · autolink ≥ 0.93 (AUTOLINK_MIN)<br/>carries event_date forward along a thread"]
  record -->|"git add index/ → commit → push"| done["main"]
```

**Calibration caveat (from `docs/archive/DEDUP-DIAGNOSIS-2026-05-31.md`):** cosine alone does *not* separate
"same story restated" from "same story with a real update" (they overlap ~0.6–0.95), so the
similarity threshold catches almost no reruns. Repeat-suppression rests on the **deterministic
exact-source layer** plus the `DEDUP.md` Step-B "ONGOING-defaults-to-drop" writer policy.
Auto-threading in `record` is gated separately at `AUTOLINK_MIN=0.93`, above the observed 0.914
DISTINCT ceiling, to avoid false merges.

**Subcommands** (`dedup.py`, stdlib-only so it runs without pip in the sandbox):
`check` · `record` · `backfill` (seed from `_posts/*.md`) · `lint` (post-compose date checks) ·
`selftest` (offline logic checks).

**Grounded in:** `tools/dedup/dedup.py` (`decide_verdict`, `cmd_check/record/backfill/lint`,
`embed_text`, `_distinct_paper`, `T_HIGH_DEFAULT=0.945`, `T_LOW_DEFAULT=0.72`,
`AUTOLINK_MIN_DEFAULT=0.93`, `EMBED_MODEL=bge-m3`, `EMBED_DIM=1024`), `tools/dedup/DEDUP.md`,
`tools/embed-proxy/wrangler.toml`, `ARCHITECTURE.md` §6, `index/stories/`.
