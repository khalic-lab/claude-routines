# 01 · System overview — components & data flow

End-to-end: cloud routines research and write briefs into the git repo; GitHub Pages publishes
them; a local Mac bridge fans notifications out to the phone; Cloudflare Workers serve the
client-side enrichments and the feedback sink. `main` is the single source of truth.

```mermaid
flowchart TB
  subgraph cloud["Anthropic Cloud · routines · env_018zypSdRSdGdrZ8J5usqCWA"]
    direction TB
    W["Writers — claude-opus-4-8<br/>News · AI/ML · Science · Weekend<br/>Write _posts/{date}-{slug}.md"]
    WA["Watch — claude-haiku-4-5<br/>reads watches.yml every 4h<br/>writes pending-notifications/*.json"]
    EV["Weekly Evaluator — claude-opus-4-8<br/>reads 7d of _posts + feedback/*.jsonl<br/>writes _posts/{date}-evaluator.md"]
    step["per run: clone → git pull → curl/WebFetch + MCP → Write → commit → push main"]
  end

  subgraph cf["Cloudflare Workers · *.khalic-lab.workers.dev"]
    FP["fetch-proxy<br/>edge fetch, browser UA, bearer-gated"]
    EP["embed-proxy<br/>Workers-AI @cf/baai/bge-m3 · 1024-dim · [ai] binding"]
    OG["og-proxy<br/>article HTML → og:image · 30d edge cache"]
    FS["feedback-sink<br/>KV FEEDBACK_KV<br/>/submit /drain /ack /propose"]
  end

  GH["GitHub · khalic-lab/claude-routines (private)<br/>main = source of truth<br/>_posts/ · pending-notifications/ · index/stories/<br/>feedback/ · watches.yml · reader-profile"]

  subgraph pages["GitHub Pages · Jekyll minimal-mistakes@4.26.2"]
    SITE["khalic-lab.github.io/claude-routines"]
    JS["browser: _includes/head/custom.html JS"]
  end

  subgraph mac["Local Mac"]
    BR["bridge.sh — cron */10 7-22<br/>pull · drain notifs → ntfy · drain feedback · commit · push · Pages self-heal"]
  end

  NTFY["ntfy.sh · topic khalic"]
  PHONE["phone (ntfy app)"]
  GM["Gmail DRAFTS (sent manually)"]

  W -->|"fetch non-allowlisted hosts"| FP
  W -->|"embed candidates (dedup)"| EP
  W -->|"git push main"| GH
  WA -->|"push stubs"| GH
  EV -->|"push review + create_draft"| GH
  EV --> GM
  W --> GM

  GH -->|"Pages build"| SITE
  SITE --> JS
  JS -->|"unfurl link"| OG
  JS -->|"POST /submit feedback"| FS

  GH -->|"git pull --rebase"| BR
  BR -->|"git push (Drained N)"| GH
  BR -->|"POST body"| NTFY
  NTFY -->|"push"| PHONE
  BR -->|"GET /drain · POST /ack"| FS
```

**Grounded in:** `ARCHITECTURE.md` §1.1, `_config.yml` (remote_theme, baseurl), `CLAUDE.md`
(env + trigger IDs), `tools/{og-proxy,embed-proxy,fetch-proxy,feedback-sink}/wrangler.toml`,
`_includes/head/custom.html`. The Mac bridge `bridge.sh` + `.env`
(`/usr/local/src/news-brief-ntfy-bridge/`) are excluded from the repo by `_config.yml`.
