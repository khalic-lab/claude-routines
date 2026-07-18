#!/usr/bin/env python3
"""Build the homepage story feed (_data/homefeed.json) from the published briefs.

The Folio homepage renders individual STORIES as a masonry grid with topic filters and
importance-sized cards. It shows the writers' actual explanatory prose — so this reads the
`_posts/*.md` briefs (where the insightful multi-sentence body lives), NOT the dedup index
(whose `summary` is a terse one-liner built for embedding). It flattens the four live streams'
recent stories into `_data/homefeed.json` that the `home` layout iterates at build time.

Per-story `topics` + `importance` come from the dedup index record when the writer supplied them
— joined by canonical URL first (stable across both sides), story-id slug second (the post's bold
lead and the record's `headline` are worded independently, so the slug join alone missed ~72% of
stories). The join rate is printed on every run so a silent regression is visible. When no record
matches, they're derived: topic from the brief's section heading (falling back to keywords),
importance from position within the brief. Pure stdlib, no network.

The `--max` cap is per-edition-quota'd: over the cap, the largest editions lose their
least-important tail stories first, and no edition drops below MIN_PER_EDITION — so a dense
Weekend brief can't evict the weekly Science edition from the page.

Run after `dedup.py record` (DEDUP.md Step D) and commit the result with the brief.
Usage: python3 tools/build_stories_feed.py [--days 14] [--max 80] [--out _data/homefeed.json]
"""
import argparse
import datetime as _dt
import glob
import importlib.util
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(ROOT, "_posts")
INDEX_DIR = os.path.join(ROOT, "index", "stories")
DEFAULT_OUT = os.path.join(ROOT, "_data", "homefeed.json")

# story_id: st-{sha1(norm_url)[:12]} (SPIKE-2026-07-07 §3.6, store.py::story_id). Loaded by
# path, not package-imported: tools/ has no __init__.py and this script also runs standalone
# (python3 tools/build_stories_feed.py) with no package context to import a sibling from.
_store_spec = importlib.util.spec_from_file_location(
    "_story_store", os.path.join(os.path.dirname(os.path.abspath(__file__)), "store", "store.py"))
_store = importlib.util.module_from_spec(_store_spec)
_store_spec.loader.exec_module(_store)
story_id = _store.story_id


def _safe_story_id(url):
    """story_id(url), or None for a falsy or degenerate-but-truthy url (e.g. a bare
    'https://' scheme with no host, which norm_url reduces to an empty string) -- story_id
    raises ValueError on that, and one malformed link must never crash the whole feed build."""
    if not url:
        return None
    try:
        return story_id(url)
    except ValueError:
        return None


_FILE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})-([a-z0-9-]+)\.md$")
_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

STREAM_LABEL = {"news": "News", "ai-ml": "AI/ML", "science": "Science", "weekend": "Weekend", "sports": "Sports"}
CURRENT_STREAMS = {"news", "ai-ml", "science", "weekend", "sports"}

# controlled topic vocabulary — MUST mirror the tagging rubric in
# routines/_shared/newsroom-ethos.md and DEDUP.md Step C (an out-of-vocab writer tag is dropped
# by topic_for's validity filter and falls back to keywords). key -> (label, dot color).
# Colors are per-beat MARKERS only, never the page accent.
TOPICS = {
    "switzerland": ("Switzerland", "#c2454a"),
    "geopolitics": ("Geopolitics", "#c0563b"),
    "politics":    ("Politics",    "#9a6a34"),
    "economy":     ("Economy",     "#9a7b2e"),
    "ai-ml":       ("AI / ML",     "#2f7d8c"),
    "science":     ("Science",     "#4c6b3c"),
    "health":      ("Health",      "#a44a72"),
    "security":    ("Security",    "#6a4b8a"),
    "tech":        ("Tech",        "#3b6ea5"),
    "sports":      ("Sports",      "#c26b2e"),
    "world":       ("World",       "#6b6f76"),
}

# section-heading -> topic (checked first; the brief's own section is the best signal we have).
_SECTION_RULES = [
    ("switzerland", ["switzerland", "vaud"]),
    ("geopolitics", ["world polit", "geopolit", "international", "nahost", "middle east"]),
    ("economy",     ["market", "econom", "finance"]),
    ("ai-ml",       ["ml/ai", "ai research", "ml / ai", "ai papers", "models &", "benchmark",
                     "data science", "apple silicon", "lab blog", "release"]),
    ("science",     ["physic", "chemistr", "math", "quantum", "astronom", "cosmolog", "biolog",
                     "medicine", "neuroscience", "biotech", "fundamental science"]),
]
# per-story keyword fallback for mixed sections (Week in headlines, Cross-cutting threads, ...).
# geopolitics is checked BEFORE security: war coverage mentions drones/strikes constantly, and the
# bare 'drone' keyword was misfiling Russia-Ukraine stories under Security.
_KEYWORD_RULES = [
    ("switzerland", ["swiss", "switzerland", "bern", " vaud", "geneva", "zurich", "ticino", "canton", "srf"]),
    ("geopolitics", ["nato", "china", "russia", "ukraine", "iran", "israel", "gaza", "missile",
                     "summit", "war", "kyiv", "treaty", "settlement"]),
    ("security",    ["drone", "cyber", "espionage", "hack", "breach", "spyware"]),
    ("ai-ml",       ["arxiv", " llm", "transformer", "gpt", "deepseek", "neural", "rlhf", "fine-tun"]),
    ("politics",    ["election", "trump", "president", "parliament", "impeachment", "senate", "midterm"]),
    ("economy",     ["job", "inflation", "market", "credit", "tax", "trade", "payroll", "fund", "bn "]),
    ("health",      ["vaccine", "hiv", "antibody", "cancer", "clinical", "disease", "outbreak", "primate"]),
    ("science",     ["physics", "quantum", "graphene", "black hole", "genome", "telescope", "matroid"]),
]
_HEALTH_KW = ["vaccine", "hiv", "antibody", "cancer", "clinical", "disease", "primate", "immune", "bnab"]

# Step C.25 (tools/store/anchor.py) rewrites bullets to '- <a id="st-…" class="st-a"></a>**…'
# and appends '{#st-…}' kramdown IALs to ### headings BEFORE Step D parses the post — every
# matcher here must read both the anchored and the bare form (2026-07-07 regression: both
# editions published anchored and the feed harvested zero stories from them).
_BULLET_RE = re.compile(r'^-\s+(?:<a id="(st-[0-9a-f]{12})" class="st-a"></a>\s*)?\*\*(.+?)\*\*\.?\s*(.*)$')
_BULLET_START_RE = re.compile(r'^-\s+(?:<a id="st-[0-9a-f]{12}" class="st-a"></a>\s*)?\*\*')
_H2_RE = re.compile(r"^##\s+(.*)$")
_H3_RE = re.compile(r"^###\s+(.*)$")
_H3_IAL_RE = re.compile(r"\s*\{#([^}]+)\}\s*$")
_URL_RE = re.compile(r"https?://[^\s)\]]+")
_TAG_RE = re.compile(r"`?\[(single-source|via snippet|preprint|disputed|vendor pr|ongoing since[^\]]*)\]`?", re.I)
_META_ITALIC_RE = re.compile(r"\s*_[^_]*(?:announced|submitted|published|reported)[^_]*_\s*", re.I)


def _strip_md(text):
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)   # [text](url) -> text
    return text.replace("**", "").replace("*", "").replace("`", "").strip(" .")


_CITE_PAREN_RE = re.compile(
    r"\s*\([^()]*(?:\d{4}-\d{2}-\d{2}|\b\d{1,2}\s+[A-Z][a-z]{2,8}\s+\d{4}|\b[A-Z][a-z]{2,8}\s+\d{4})[^()]*\)")


def clean_body(text):
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)   # links -> text FIRST (delinks citations too)
    text = _TAG_RE.sub("", text)                          # [single-source] / [via snippet] / `[preprint]`
    text = _CITE_PAREN_RE.sub("", text)                   # (Source, 6 Jul 2026; Other, 2026-07-04) citations
    text = _META_ITALIC_RE.sub(" ", text)                 # _Announced …_ / _submitted …_
    text = text.replace("**", "").replace("*", "").replace("`", "")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^[\s—–-]+", "", text)               # drop a leading dash lead-in ("— the week's…")
    return text


def _is_meta(p):
    """A citation / author / date byline, not story prose."""
    p = p.strip()
    if not p:
        return True
    if re.match(r"^\*{0,2}\[", p):                      # leading link: **[Nature](…) or [arXiv…]
        return True
    if re.match(r"^[—–]\s*\**\[", p):        # em-dash INTO a citation: "— [arXiv…] · authors" (not "— prose")
        return True
    low = p.lower()
    # author-list shapes, with or without a middot delimiter (peer-reviewed papers' bylines have
    # no `· [preprint]` tag, so requiring the middot let 'A, B, C et al. (…)' pass as story prose)
    if re.search(r"\bet al\b|affiliations not listed|senior author", low):
        return True
    if " · " in p:                                      # middot-separated byline / citation line
        if re.search(r"arxiv|preprint|published|submitted|reported|affiliation|university|institute", low):
            return True
        if p.count(" · ") >= 2:                         # author · source · date
            return True
        if re.search(r"·\s*\d{4}(?:-\d{2}-\d{2})?\s*$", p):                     # trailing date
            return True
        if re.search(r"\b[a-z0-9-]+\.(?:com|net|org|blog|io|ai|dev|ch|co)\b", low):  # bare source domain
            return True
    return False


_WHY_RE = re.compile(r"^\*{1,2}\s*Why (?:it|this) matters:?\s*\*{0,2}\s*", re.I)
# A '## Why it matters' H2 ROUNDUP section (e.g. 2026-07-01-science.md's weekly takeaways)
# is prose commentary, not stories -- its bullets must not be harvested as pseudo-stories.
# Deliberately scoped to the bullet branch only (### paper headings never appear there).
_WHY_SECTION_RE = re.compile(r"why it matters", re.I)


def _pick_body(paras):
    for p in paras:
        if _is_meta(p) or _WHY_RE.match(p.strip()):     # the why-block is its own field, not the body
            continue
        c = clean_body(p)
        if len(c) >= 40:
            return c
    for p in paras:                                     # relax the length floor
        if _WHY_RE.match(p.strip()):
            continue
        c = clean_body(p)
        if c:
            return c
    return ""


def _pick_why(paras):
    """The writers' `**Why it matters:**` (ai-ml) / `*Why it matters:*` (science) paragraph."""
    for p in paras:
        m = _WHY_RE.match(p.strip())
        if m:
            return clean_body(p.strip()[m.end():])
    return ""


def parse_post(md):
    """Return [{section, headline, body, url, raw}] for every story bullet or ### paper heading."""
    lines = md.splitlines()
    out, section, in_footer, i, n = [], "", False, 0, len(lines)

    def emit(headline, paras, anchor_sid=None):
        if headline.replace("*", "").rstrip().endswith(":"):
            return                                      # '**Datasets:** …' roundup label, not a story
        raw = " ".join(paras)
        urls = _URL_RE.findall(raw)
        out.append({"section": section, "headline": _strip_md(headline),
                    "body": _pick_body(paras), "why": _pick_why(paras),
                    "url": urls[0] if urls else None, "raw": raw,
                    "anchor_sid": anchor_sid})

    while i < n:
        line = lines[i]
        h2 = _H2_RE.match(line)
        if h2:
            sec = h2.group(1).strip()
            in_footer = "coverage footer" in sec.lower()
            if not in_footer:
                section = sec
            i += 1
            continue
        if in_footer:
            i += 1
            continue
        h3 = _H3_RE.match(line)
        if h3:                                          # heading-style story (science/weekend papers)
            paras, j = [], i + 1
            while j < n:
                nx = lines[j]
                if _H2_RE.match(nx) or _H3_RE.match(nx) or nx.startswith("# "):
                    break
                if _BULLET_START_RE.match(nx.lstrip()):
                    break
                if nx.strip():
                    paras.append(nx.strip())
                j += 1
            head = h3.group(1).strip()
            ial = _H3_IAL_RE.search(head)
            h3_sid = ial.group(1) if ial and ial.group(1).startswith("st-") else None
            emit(_H3_IAL_RE.sub("", head).strip(), paras, anchor_sid=h3_sid)
            i = j
            continue
        m = _BULLET_RE.match(line)
        if m:                                           # bullet-style story (news / ai-ml / weekend headlines)
            paras, j = [m.group(3).strip()], i + 1
            while j < n:
                nxt = lines[j]
                if nxt.startswith("#"):
                    break
                if not nxt.strip():
                    k = j + 1
                    while k < n and not lines[k].strip():
                        k += 1
                    if (k < n and lines[k][:1] in (" ", "\t") and not lines[k].lstrip().startswith("- ")):
                        j += 1
                        continue
                    break
                if nxt.lstrip().startswith("- "):
                    break
                paras.append(nxt.strip())
                j += 1
            if not _WHY_SECTION_RE.search(section):     # skip a why-it-matters roundup's bullets
                emit(m.group(2).strip(), paras, anchor_sid=m.group(1))
            i = j
            continue
        i += 1
    return out


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:48].strip("-")
    return s or "story"


def _match(text, rules, default=None):
    low = text.lower()
    for topic, kws in rules:
        if any(k in low for k in kws):
            return topic
    return default


def topic_for(story, stream, index_topics):
    if index_topics:                                    # writer-supplied (authoritative)
        valid = [t for t in index_topics if t in TOPICS]
        if valid:
            return valid
    text = story["headline"] + " " + story["body"]
    healthy = any(k in text.lower() for k in _HEALTH_KW)
    if stream == "ai-ml":                               # single-topic stream: don't let a stray keyword win
        return ["ai-ml"]
    if stream == "sports":                              # single-topic stream: the stream IS the beat
        return ["sports"]
    if stream == "science":
        return ["health"] if healthy else ["science"]
    sec = _match(story["section"], _SECTION_RULES)      # news + weekend are mixed
    if stream == "weekend" and sec:                     # weekend sections are topical (ML papers / science / …)
        return ["health"] if (sec == "science" and healthy) else [sec]
    if sec == "switzerland":                            # a Swiss-desk story is Swiss regardless of subtopic
        return ["switzerland"]
    topic = _match(text, _KEYWORD_RULES) or sec or "world"   # else finer per-story keyword
    if topic == "science" and healthy:
        topic = "health"
    return [topic]


def importance_for(pos, lead_pos, single_source, index_importance):
    if isinstance(index_importance, int) and index_importance in (1, 2, 3):
        return index_importance
    if pos == lead_pos:
        return 3
    if single_source:
        return 1
    return 2 if pos <= 3 else 1


def date_label(d):
    y, m, day = d.split("-")
    return "%s %d" % (_MONTHS[int(m) - 1], int(day))


def source_domain(url):
    if not url:
        return ""
    m = re.match(r"https?://([^/]+)", url)
    if not m:
        return ""
    host = m.group(1).lower()
    return host[4:] if host.startswith("www.") else host


def norm_url(url):
    """Canonicalize for the feed↔index join: scheme/www/fragment/utm-insensitive."""
    if not url:
        return None
    u = url.strip().split("#", 1)[0]
    u = re.sub(r"^https?://(www\.)?", "", u, flags=re.I)
    if "?" in u:
        base, q = u.split("?", 1)
        keep = [p for p in q.split("&") if p and not p.lower().startswith(("utm_", "ref=", "fbclid"))]
        u = base + ("?" + "&".join(keep) if keep else "")
    return u.rstrip("/").lower()


def load_index_meta(window_dates):
    """(by_url, by_id) -> {topics, importance} from the dedup index, for authoritative overlay.

    URL is the primary join key: the post's bold lead and the record's `headline` are written
    independently by the routine, so slugified-headline ids only agree ~28% of the time. Both
    sides cite the same primary-source URL, which survives the round trip."""
    by_url, by_id = {}, {}
    for path in glob.glob(os.path.join(INDEX_DIR, "*.jsonl")):
        base = os.path.basename(path)
        if not any(base.startswith(d) for d in window_dates):
            continue
        with open(path) as fh:
            for ln in fh:
                if not ln.strip():
                    continue
                r = json.loads(ln)
                m = {"topics": r.get("topics"), "importance": r.get("importance"),
                     "display_body": r.get("display_body"), "why": r.get("why"),
                     "affiliations": r.get("affiliations")}
                if r.get("id"):
                    by_id[r["id"]] = m
                nu = norm_url(r.get("url"))
                if nu:
                    by_url[nu] = m
    return by_url, by_id


# --- editorials (2026-07-18) -----------------------------------------------------------------
# The briefs' SECTION-level synthesis prose (Weekend "Cross-cutting threads", Science/Sports
# "Why it matters") is not per-story, so it never became feed cards — and with the individual
# brief pages retired the same day, it had nowhere on the site at all. Extract those sections
# into feed["editorials"]; the homepage renders them as distinct 2-col editorial cards.
_EDITORIAL_HEADINGS = {
    "cross cutting threads": "Cross-cutting threads",
    "why it matters": "Why it matters",
}
_ED_HEAD_RE = re.compile(r"^##\s+(.*)$")
_ED_HR_RE = re.compile(r"^[-*_]{3,}$")   # markdown rule (---/***/___): separator, never prose
_ED_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
_ED_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_ED_EM_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
_ED_TAG_RE = re.compile(r"<[^>]+>")


def _editorial_heading(line):
    m = _ED_HEAD_RE.match(line)
    if not m:
        return None
    title = _strip_md(m.group(1)).strip()
    # collapse every non-letter run to one space so emoji AND hyphens normalize away
    # ("🧠 Cross-cutting threads" -> "cross cutting threads")
    key = re.sub(r"[^a-z]+", " ", title.lower()).strip()
    return _EDITORIAL_HEADINGS.get(key)


def _ed_inline_html(text):
    """Markdown -> SAFE html for one paragraph: everything escaped, then only links/bold/em
    rebuilt from the escaped text. Source HTML (e.g. anchor.py's <a id> stubs) is stripped."""
    import html as _h
    s = _ED_TAG_RE.sub("", text).replace("`", "")
    s = _h.escape(s, quote=False)
    # m.group(2) comes out of the ALREADY-escaped text (& is &amp;) -- escaping it
    # again would double-escape to &amp;amp;. Only quotes still need attribute-escaping.
    s = _ED_LINK_RE.sub(
        lambda m: '<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>'
        % (m.group(2).replace('"', "&quot;"), m.group(1)), s)
    s = _ED_BOLD_RE.sub(r"<strong>\1</strong>", s)
    s = _ED_EM_RE.sub(r"<em>\1</em>", s)
    return s.strip()


def _ed_paragraphs(lines, cap=6):
    """Section lines -> [html paragraph]: blank-line-delimited chunks, '- ' bullets split out,
    wrapped lines joined. Markdown rules (---) and fenced code blocks are structure, not prose --
    both live cards shipped a literal '---' paragraph before this filter existed."""
    paras, chunk = [], []
    fenced, fence_buf = False, []

    def flush():
        if chunk:
            paras.append(_ed_inline_html(" ".join(chunk)))
            del chunk[:]

    def consume(stripped):
        if not stripped or _ED_HR_RE.match(stripped):
            flush()
        elif stripped.startswith("- "):
            flush()
            chunk.append(stripped[2:])
            flush()
        else:
            chunk.append(stripped)

    for ln in lines:
        stripped = ln.strip()
        if stripped.startswith("```"):
            flush()
            if fenced:
                del fence_buf[:]        # closed: a genuine code block, dropped whole
            fenced = not fenced
        elif fenced:
            fence_buf.append(stripped)  # held, not dropped -- the fence may never close
        else:
            consume(stripped)
    if fenced:
        # Unmatched fence (a stray ``` mid-prose): the held lines are prose, not code --
        # silently swallowing the rest of the section was an adversarial-review catch.
        for stripped in fence_buf:
            consume(stripped)
    flush()
    return [p for p in paras if p][:cap]


def load_editorials(days):
    """Latest edition's editorial section per stream, newest first, max 3 cards."""
    posts = []
    for path in glob.glob(os.path.join(POSTS_DIR, "*.md")):
        m = _FILE_RE.search(os.path.basename(path))
        if m and m.group(2) in CURRENT_STREAMS:
            posts.append((m.group(1), m.group(2), path))
    if not posts:
        return []
    cutoff = (_dt.date.fromisoformat(max(p[0] for p in posts)) - _dt.timedelta(days=days)).isoformat()

    by_stream = {}
    for date, stream, path in sorted(posts):
        if date < cutoff:
            continue
        with open(path) as fh:
            lines = fh.read().splitlines()
        i = 0
        while i < len(lines):
            title = _editorial_heading(lines[i])
            if title is None:
                i += 1
                continue
            j = i + 1
            body = []
            while j < len(lines) and not lines[j].startswith("## "):
                body.append(lines[j])
                j += 1
            paras = _ed_paragraphs(body)
            if paras:
                d = _dt.date.fromisoformat(date)
                label = "%s %d" % (_MONTHS[d.month - 1], d.day)
                by_stream[stream] = {         # later (newer) editions overwrite: latest wins
                    "stream": stream, "date": date,
                    "date_label": label,
                    "kicker": "%s · %s" % (STREAM_LABEL.get(stream, stream), label),
                    "title": title, "paras": paras,
                }
            i = j
    return sorted(by_stream.values(), key=lambda e: e["date"], reverse=True)[:3]


def load_recent(days):
    posts = []
    for path in glob.glob(os.path.join(POSTS_DIR, "*.md")):
        m = _FILE_RE.search(os.path.basename(path))
        if m and m.group(2) in CURRENT_STREAMS:
            posts.append((m.group(1), m.group(2), path))
    if not posts:
        return [], None
    max_date = max(p[0] for p in posts)
    cutoff = (_dt.date.fromisoformat(max_date) - _dt.timedelta(days=days)).isoformat()
    window = sorted(p for p in posts if p[0] >= cutoff)
    idx_by_url, idx_by_id = load_index_meta({d for d, _, _ in window})

    stories, url_pos, ov_flags = [], {}, []
    for date, stream, path in window:
        with open(path) as fh:
            parsed = parse_post(fh.read())
        if not parsed:
            continue
        singles = ["single-source" in s["raw"].lower() for s in parsed]
        lead_pos = next((i for i, sgl in enumerate(singles) if not sgl), 0)
        for pos, s in enumerate(parsed):
            if not s["body"]:
                continue
            nu = norm_url(s["url"])
            replace_at = None
            if nu and nu in url_pos:
                # Same primary source already on the page. The window iterates oldest->
                # newest, so this occurrence is the NEWER telling (an ONGOING update
                # re-citing its primary): it supersedes the older card in place. Same-date
                # cross-stream repeats keep the first telling (no basis to prefer either).
                prev = stories[url_pos[nu]]
                if prev["date"] == date:
                    continue
                replace_at = url_pos[nu]
            hid = "%s-%s-%s" % (date, stream, slugify(s["headline"]))
            im = (nu and idx_by_url.get(nu)) or idx_by_id.get(hid) or {}
            overlaid = bool(im.get("topics") or im.get("importance"))
            topics = topic_for(s, stream, im.get("topics"))
            imp = importance_for(pos, lead_pos, singles[pos], im.get("importance"))
            primary = topics[0]
            label, color = TOPICS.get(primary, (primary.title(), "#6b6f76"))
            y, mo, dy = date.split("-")
            # the writer's recorded prose (display_body/why, DEDUP Step C) beats the markdown
            # re-parse — the record is authored, the parse is recovered.
            body = (im.get("display_body") or "").strip() or s["body"]
            why = (im.get("why") or "").strip() or s["why"]
            affs = im.get("affiliations") or []
            story = {
                # the post's embedded anchor id is authoritative (anchor.py keyed it on the
                # RECORDED story url via --index); recompute from the first link only for
                # pre-anchor posts
                "id": hid, "sid": s.get("anchor_sid") or _safe_story_id(s["url"]),
                "headline": s["headline"], "summary": body, "why": why,
                "url": s["url"], "source_domain": source_domain(s["url"]),
                "date": date, "date_label": date_label(date),
                "stream": stream, "stream_label": STREAM_LABEL.get(stream, stream.title()),
                "topics": topics, "topic_primary": primary, "topic_label": label, "topic_color": color,
                "importance": imp, "is_lead": imp == 3,
                "permalink": "/%s/%s/%s/%s/" % (y, mo, dy, stream),
            }
            if affs:
                # institution-first source label (SPIKE-2026-07-10): the affiliation is the
                # editorial source of a paper; the domain is just the platform. Keys are
                # emitted only when present so Liquid's `{% if %}` (empty string is truthy)
                # can gate on them directly.
                story["affiliations"] = affs
                story["affiliation_label"] = ", ".join(affs[:2]) + (
                    " +%d" % (len(affs) - 2) if len(affs) > 2 else "")
            if replace_at is not None:
                stories[replace_at] = story
                ov_flags[replace_at] = overlaid
            else:
                if nu:
                    url_pos[nu] = len(stories)
                stories.append(story)
                ov_flags.append(overlaid)
    return stories, max_date, sum(ov_flags)


MIN_LATEST_EDITION = 6   # each stream's NEWEST edition keeps at least this many stories


def apply_cap(stories, cap):
    """Global newest-first truncation let one dense Weekend brief erase whole streams from the
    window (Science was entirely absent). Instead: repeatedly drop the least-important tail
    story from the edition with the most droppable stories (oldest first on ties). Each stream's
    latest edition is floored at MIN_LATEST_EDITION so every live stream stays on the page;
    older editions can drain fully — their briefs remain in the archive."""
    if not cap or len(stories) <= cap:
        return stories
    pos = {id(s): i for i, s in enumerate(stories)}
    editions = {}
    for s in stories:
        editions.setdefault((s["date"], s["stream"]), []).append(s)
    latest = {}
    for date, stream in editions:
        latest[stream] = max(latest.get(stream, ""), date)

    def floor(key):
        date, stream = key
        return MIN_LATEST_EDITION if date == latest[stream] else 0

    # drop order within an edition: lowest importance first, later position first
    for ed in editions.values():
        ed.sort(key=lambda s: (s["importance"], -pos[id(s)]))
    dropped = set()
    total = len(stories)
    while total > cap:
        key = max((k for k, ed in editions.items() if len(ed) > floor(k)),
                  key=lambda k: (len(editions[k]) - floor(k), [-ord(c) for c in k[0]]),
                  default=None)
        if key is None:
            break                                        # everything at its floor; accept > cap
        dropped.add(id(editions[key].pop(0)))
        total -= 1
    return [s for s in stories if id(s) not in dropped]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--max", type=int, default=80, dest="cap", help="cap the front page (0 = no cap)")
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()

    stories, max_date, joined = load_recent(args.days)
    n_parsed = len(stories)
    stories.sort(key=lambda s: (s["date"], s["importance"]), reverse=True)   # newest + lead first
    stories = apply_cap(stories, args.cap)
    for s in stories:
        s["fresh"] = s["date"] == max_date

    counts = {}
    for s in stories:
        for t in s["topics"]:
            counts[t] = counts.get(t, 0) + 1
    topics = [{"key": k, "label": TOPICS[k][0], "color": TOPICS[k][1], "count": counts[k]}
              for k in sorted(counts, key=lambda k: (-counts[k], k)) if k in TOPICS]

    editorials = load_editorials(args.days)
    feed = {"generated": max_date, "count": len(stories), "topics": topics,
            "editorials": editorials, "stories": stories}
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(feed, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    by = {i: sum(1 for s in stories if s["importance"] == i) for i in (3, 2, 1)}
    streams = sorted({s["stream"] for s in stories})
    print("wrote %d/%d stories (%d beats, streams: %s) -> %s  [lead=%d standard=%d brief=%d, through %s]"
          % (len(stories), n_parsed, len(topics), ",".join(streams),
             os.path.relpath(args.out, ROOT), by[3], by[2], by[1], max_date))
    print("editorials: %d (%s)" % (len(editorials),
          ", ".join("%s %s" % (e["stream"], e["date"]) for e in editorials) or "none in window"))
    print("index overlay: %d/%d stories carry writer-supplied topics/importance"
          % (joined, n_parsed))                      # 0 is EXPECTED until routines start tagging

    # Desk-stats piggyback (2026-07-11): every writer already runs this script
    # unconditionally, so regenerating _data/stats.json here needs zero prompt wiring.
    try:
        import importlib.util as _ilu
        _sp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_stats.py")
        _spec = _ilu.spec_from_file_location("build_stats", _sp)
        _bs = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_bs)
        _bs.main(["--root", ROOT])  # module global, so a test-patched ROOT is honored
    except Exception as e:  # stats are decorative; the feed must never fail on them
        print("stats build skipped (non-fatal): %s" % e)


if __name__ == "__main__":
    main()
