# 05 · Frontend rendering pipeline — `_includes/head/custom.html`

All custom CSS + JS is layered over the minimal-mistakes "default" skin and loads last in the
document head. On `DOMContentLoaded` a sequence of passes transforms the kramdown-rendered brief
into the editorial layout, then enriches it with link previews, feedback widgets and the unlock
modal. The editorial CSS targets only `.story` — the class the normaliser tags — so the
Coverage-footer / "Gaps:" list stays plain prose.

```mermaid
flowchart TD
  subgraph headblk["custom.html — parsed in document head"]
    H["Shared helpers (global)<br/>findCoverageFooter(content) · afterFooter(footer, el)"]
    stub["Stub: ensure .page__content exists<br/>(guards theme main.min.js)"]
  end

  DCL(["DOMContentLoaded"]) --> tag

  subgraph tag["1 · Story normaliser (tags .story)"]
    direction TB
    t1["for each .page__content &gt; ul &gt; li before the Coverage footer"]
    t1 --> t2{"lead element?"}
    t2 -->|"tight: leading &lt;strong&gt;"| t3["wrap inline run in p.story-body<br/>+ add class .story"]
    t2 -->|"loose: &lt;p&gt;&lt;strong&gt;…"| t4["add class .story"]
    t2 -->|"text lead (e.g. Gaps:)"| t5["leave untagged → plain prose"]
  end

  tag --> prev
  subgraph prev["2 · Link preview (IntersectionObserver, rootMargin 300px)"]
    direction TB
    p1{"external link kind"}
    p1 -->|"arxiv.org"| p2["render a.auto-preview.pdf chip → /pdf/ID.pdf"]
    p1 -->|"other host"| p3["unfurl via og-proxy worker"]
    p3 -->|"og:image"| p4["a.auto-preview-wrap &gt; img.auto-preview (figure)"]
    p3 -->|"no image"| p5["favicon → img.auto-preview.fav"]
    p6["sessionStorage cache key: autoPreview:v2:"]
  end

  tag --> fb
  subgraph fb["3 · Feedback widgets"]
    direction TB
    f1["per-story .fb-inline 👍 / 👎 + reason (story_id set)"]
    f2["bottom .fb-box overall (story_id = null)"]
    f1 --> f3
    f2 --> f3
    f3["post() → feedback-sink /submit<br/>X-Widget-Key = __siteKey.get() (localStorage)"]
    f3 -->|"no key / HTTP 403"| f4[".site-unlock modal — prompt for shared key"]
  end

  tag --> emo["4 · Strip leading section emoji on h2/h3"]
  home(["home page only"]) --> prop[".propose__form → feedback-sink /propose"]

  CSS["Editorial CSS — variable-driven (:root + dark @media)<br/>.story headlines (Fraunces) · arXiv shape-A/B rules<br/>.auto-preview figures · feedback widgets"]
  tag -.->|"styling targets .story"| CSS
```

Notes:
- Per-story `story_id` is `{date}-{slug}-{slugify(bold lead)}`, mirroring `dedup.py slugify()` so
  the Evaluator can join feedback back to stories by re-slugifying the same bold leads.
- The story id slug prefix comes from `window.__BRIEF` (injected by Jekyll on post pages only).
- Both the normaliser and the feedback pass stop at the Coverage footer via the shared
  `findCoverageFooter()` / `afterFooter()` helpers.

**Grounded in:** `_includes/head/custom.html` (every class/function named here is literal), the
arXiv markup shapes in `_posts/*.md`, `tools/og-proxy/` + `tools/feedback-sink/`, and
`_layouts/home.html` (`.home-hero`, `.home-tagline`, `.entries-list`, `.propose__form`).
