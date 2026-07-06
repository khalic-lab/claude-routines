#!/usr/bin/env python3
"""Build the homepage story feed (_data/homefeed.json) from the published briefs.

The Folio homepage renders individual STORIES as a masonry grid with topic filters and
importance-sized cards. It shows the writers' actual explanatory prose — so this reads the
`_posts/*.md` briefs (where the insightful multi-sentence body lives), NOT the dedup index
(whose `summary` is a terse one-liner built for embedding). It flattens the four live streams'
recent stories into `_data/homefeed.json` that the `home` layout iterates at build time.

Per-story `topics` + `importance` come from the dedup index record when the writer supplied them
(joined by story id); otherwise they're derived — topic from the brief's section heading (falling
back to keywords), importance from position within the brief. Pure stdlib, no network.

Run after `dedup.py record` (DEDUP.md Step D) and commit the result with the brief.
Usage: python3 tools/build_stories_feed.py [--days 14] [--max 80] [--out _data/homefeed.json]
"""
import argparse
import datetime as _dt
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(ROOT, "_posts")
INDEX_DIR = os.path.join(ROOT, "index", "stories")
DEFAULT_OUT = os.path.join(ROOT, "_data", "homefeed.json")
_FILE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})-([a-z0-9-]+)\.md$")
_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

STREAM_LABEL = {"news": "News", "ai-ml": "AI/ML", "science": "Science", "weekend": "Weekend"}
CURRENT_STREAMS = {"news", "ai-ml", "science", "weekend"}

# controlled topic vocabulary (mirrors routines/_shared/story-tagging in newsroom-ethos). key ->
# (label, dot color). Colors are per-beat MARKERS only, never the page accent.
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
_KEYWORD_RULES = [
    ("switzerland", ["swiss", "switzerland", "bern", " vaud", "geneva", "zurich", "ticino", "canton", "srf"]),
    ("security",    ["drone", "cyber", "espionage", "hack", "breach", "spyware"]),
    ("ai-ml",       ["arxiv", " llm", "transformer", "gpt", "deepseek", "neural", "rlhf", "fine-tun"]),
    ("geopolitics", ["nato", "china", "russia", "ukraine", "iran", "israel", "gaza", "missile",
                     "summit", "war", "kyiv", "treaty", "settlement"]),
    ("politics",    ["election", "trump", "president", "parliament", "impeachment", "senate", "midterm"]),
    ("economy",     ["job", "inflation", "market", "credit", "tax", "trade", "payroll", "fund", "bn "]),
    ("health",      ["vaccine", "hiv", "antibody", "cancer", "clinical", "disease", "outbreak", "primate"]),
    ("science",     ["physics", "quantum", "graphene", "black hole", "genome", "telescope", "matroid"]),
]
_HEALTH_KW = ["vaccine", "hiv", "antibody", "cancer", "clinical", "disease", "primate", "immune", "bnab"]

_BULLET_RE = re.compile(r"^-\s+\*\*(.+?)\*\*\.?\s*(.*)$")
_H2_RE = re.compile(r"^##\s+(.*)$")
_H3_RE = re.compile(r"^###\s+(.*)$")
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
    return _trim(text)


def _trim(text, limit=600):
    """Cap runaway bodies at a sentence boundary so a card stays substantial but not a wall."""
    if len(text) <= limit:
        return text
    cut = text[:limit]
    end = max(cut.rfind(". "), cut.rfind(".” "), cut.rfind('." '), cut.rfind("? "), cut.rfind("! "))
    if end > 250:
        return cut[:end + 1]
    sp = cut.rfind(" ")
    return (cut[:sp] if sp > 250 else cut).rstrip(" ,;—-") + "…"


def _is_meta(p):
    """A citation / author / date byline, not story prose."""
    p = p.strip()
    if not p:
        return True
    if re.match(r"^\*{0,2}\[", p):                      # leading link: **[Nature](…) or [arXiv…]
        return True
    if re.match(r"^[—–]\s*\**\[", p):        # em-dash INTO a citation: "— [arXiv…] · authors" (not "— prose")
        return True
    if " · " in p:                                      # middot-separated byline / citation line
        low = p.lower()
        if re.search(r"arxiv|preprint|published|submitted|reported|affiliation|et al|university|institute", low):
            return True
        if p.count(" · ") >= 2:                         # author · source · date
            return True
        if re.search(r"·\s*\d{4}(?:-\d{2}-\d{2})?\s*$", p):                     # trailing date
            return True
        if re.search(r"\b[a-z0-9-]+\.(?:com|net|org|blog|io|ai|dev|ch|co)\b", low):  # bare source domain
            return True
    return False


def _pick_body(paras):
    for p in paras:
        if _is_meta(p):
            continue
        c = clean_body(p)
        if len(c) >= 40:
            return c
    for p in paras:                                     # relax the length floor
        c = clean_body(p)
        if c:
            return c
    return ""


def parse_post(md):
    """Return [{section, headline, body, url, raw}] for every story bullet or ### paper heading."""
    lines = md.splitlines()
    out, section, in_footer, i, n = [], "", False, 0, len(lines)

    def emit(headline, paras):
        raw = " ".join(paras)
        urls = _URL_RE.findall(raw)
        out.append({"section": section, "headline": _strip_md(headline),
                    "body": _pick_body(paras), "url": urls[0] if urls else None, "raw": raw})

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
                if nx.lstrip().startswith("- **"):
                    break
                if nx.strip():
                    paras.append(nx.strip())
                j += 1
            emit(h3.group(1).strip(), paras)
            i = j
            continue
        m = _BULLET_RE.match(line)
        if m:                                           # bullet-style story (news / ai-ml / weekend headlines)
            paras, j = [m.group(2).strip()], i + 1
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
            emit(m.group(1).strip(), paras)
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


def fnv1a(s):
    h = 2166136261
    for ch in s:
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return h


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


def load_index_meta(window_dates):
    """id -> {topics, importance} from the dedup index, for authoritative overlay."""
    meta = {}
    for path in glob.glob(os.path.join(INDEX_DIR, "*.jsonl")):
        base = os.path.basename(path)
        if not any(base.startswith(d) for d in window_dates):
            continue
        with open(path) as fh:
            for ln in fh:
                if not ln.strip():
                    continue
                r = json.loads(ln)
                if r.get("id"):
                    meta[r["id"]] = {"topics": r.get("topics"), "importance": r.get("importance")}
    return meta


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
    idx_meta = load_index_meta({d for d, _, _ in window})

    stories = []
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
            hid = "%s-%s-%s" % (date, stream, slugify(s["headline"]))
            im = idx_meta.get(hid, {})
            topics = topic_for(s, stream, im.get("topics"))
            imp = importance_for(pos, lead_pos, singles[pos], im.get("importance"))
            primary = topics[0]
            label, color = TOPICS.get(primary, (primary.title(), "#6b6f76"))
            y, mo, dy = date.split("-")
            stories.append({
                "id": hid, "headline": s["headline"], "summary": s["body"],
                "url": s["url"], "source_domain": source_domain(s["url"]),
                "date": date, "date_label": date_label(date),
                "stream": stream, "stream_label": STREAM_LABEL.get(stream, stream.title()),
                "topics": topics, "topic_primary": primary, "topic_label": label, "topic_color": color,
                "importance": imp, "is_lead": imp == 3, "has_plate": imp >= 2,
                "permalink": "/%s/%s/%s/%s/" % (y, mo, dy, stream),
                "seed": fnv1a(s["headline"]),
            })
    return stories, max_date


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--max", type=int, default=80, dest="cap", help="cap the front page (0 = no cap)")
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()

    stories, max_date = load_recent(args.days)
    stories.sort(key=lambda s: (s["date"], s["importance"]), reverse=True)   # newest + lead first
    if args.cap and len(stories) > args.cap:
        stories = stories[:args.cap]
    for s in stories:
        s["fresh"] = s["date"] == max_date

    counts = {}
    for s in stories:
        for t in s["topics"]:
            counts[t] = counts.get(t, 0) + 1
    topics = [{"key": k, "label": TOPICS[k][0], "color": TOPICS[k][1], "count": counts[k]}
              for k in sorted(counts, key=lambda k: (-counts[k], k)) if k in TOPICS]

    feed = {"generated": max_date, "count": len(stories), "topics": topics, "stories": stories}
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(feed, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    by = {i: sum(1 for s in stories if s["importance"] == i) for i in (3, 2, 1)}
    print("wrote %d stories (%d beats) -> %s  [lead=%d standard=%d brief=%d, through %s]"
          % (len(stories), len(topics), os.path.relpath(args.out, ROOT), by[3], by[2], by[1], max_date))


if __name__ == "__main__":
    main()
