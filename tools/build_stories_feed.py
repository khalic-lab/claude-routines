#!/usr/bin/env python3
"""Build the homepage story feed (_data/homefeed.json) from the rolling dedup index.

The Folio homepage renders individual STORIES (not whole briefs) as a masonry grid with
topic filters and importance-driven card sizes. Jekyll can only read committed data, and
`index/stories/*.jsonl` is excluded from the published site, so this script flattens the
recent index into a single `_data/homefeed.json` that the `home` layout iterates at build
time. Run it after `dedup.py record` (see DEDUP.md Step D) and commit the result with the brief.

Per-story `topics` (list) and `importance` (1-3) are authoritative when the writer emits them
(they land in the index record). For older records that predate the fields, this script DERIVES
a sensible fallback — topic from stream + keywords, importance from position-in-brief — so the
grid looks right today. Pure stdlib, no network: it only reshapes files already on disk.

Usage:
  python3 tools/build_stories_feed.py [--days 21] [--out _data/homefeed.json]
"""
import argparse
import datetime as _dt
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_DIR = os.path.join(ROOT, "index", "stories")
DEFAULT_OUT = os.path.join(ROOT, "_data", "homefeed.json")
_FILE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})-([a-z0-9-]+)\.jsonl$")
_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# --- controlled topic vocabulary (mirrors routines/_shared/story-tagging.md) --------------------
# key -> (display label, small dot color). The color is a per-beat MARKER only, never the page
# accent. Keep this list in sync with the rubric so writer-supplied topics resolve to a chip.
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
STREAM_LABEL = {"news": "News", "ai-ml": "AI/ML", "science": "Science", "weekend": "Weekend"}
# only the four LIVE writer streams belong on the homepage. Retired slugs (overview, cyber-papers,
# markets) still have index files inside the 40-day window; excluding them here keeps the front page
# to current beats and stops their un-mappable stream from dumping everything into "world".
CURRENT_STREAMS = {"news", "ai-ml", "science", "weekend"}

# ordered (topic, keywords) — first hit wins. Only a FALLBACK for records without writer topics.
_NEWS_RULES = [
    ("switzerland", ["swiss", "switzerland", "bern", " vaud", "geneva", "zurich", "ticino",
                     "canton", "srf", "federal council", "lötschental", "blatten", "helvet"]),
    ("security",    ["drone", "cyber", "espionage", "hack", "breach", "surveillance", "spyware"]),
    ("geopolitics", ["nato", "china", "russia", "ukraine", "iran", "israel", "gaza", "missile",
                     "summit", "pact", "war", "military", "kyiv", "moscow", "beijing", "treaty"]),
    ("politics",    ["election", "trump", "president", "parliament", "impeachment", "vote",
                     "senate", "congress", "referendum", "coalition"]),
    ("economy",     ["job", "inflation", "market", "credit", "tax", "trade", "gdp", "payroll",
                     "rate", "tariff", "bond", "recession", "fund"]),
    ("health",      ["vaccine", "hospital", "disease", "outbreak", "clinical", "public health"]),
]
_WEEKEND_RULES = [
    ("ai-ml",   ["arxiv", "llm", "transformer", "model", " rl ", "neural", "attention",
                 "gpt", "deepseek", "fine-tun", "inference", "gradient", "benchmark"]),
    ("science", ["nature", "physics", "quantum", "black hole", "genome", "biology", "matroid",
                 "graphene", "gravitational", "telescope", "superconduct", "cosmolog"]),
    ("health",  ["vaccine", "antibody", "hiv", "cancer", "clinical", "neuro", "primate", "cell"]),
    ("economy", ["market", "credit", "private-credit", "fund", "redemption", "economy", "bn "]),
    ("geopolitics", ["nato", "war", "funeral", "china", "russia", "iran", "summit", "missile"]),
]


def _classify(text, rules, default):
    t = text.lower()
    for topic, kws in rules:
        if any(k in t for k in kws):
            return topic
    return default


def derive_topics(rec):
    """Fallback topic list for a record the writer didn't tag."""
    stream = rec.get("stream", "")
    text = (rec.get("headline", "") + " " + rec.get("summary", ""))
    if stream == "ai-ml":
        return ["ai-ml"]
    if stream == "science":
        return [_classify(text, [("health", _WEEKEND_RULES[2][1])], "science")]
    if stream == "weekend":
        return [_classify(text, _WEEKEND_RULES, "world")]
    if stream == "news":
        return [_classify(text, _NEWS_RULES, "world")]
    return ["world"]


def derive_importance(pos, tags, lead_pos):
    """Fallback importance for a record the writer didn't score. `lead_pos` is the chosen lead
    index within the brief (the first well-sourced story — see lead_index). The lead is 3, the
    next few are 2, the tail is 1, and a single-source non-lead never rises above a brief."""
    if pos == lead_pos:
        return 3
    base = 2 if pos <= 3 else 1
    if "single-source" in (tags or []):
        base = 1
    return base


def lead_index(recs):
    """Pick a brief's lead: the first story that is NOT single-source (news puts a parochial CH
    item first, so 'first bullet' alone is a poor lead signal), else fall back to the first."""
    for i, r in enumerate(recs):
        if "single-source" not in (r.get("tags") or []):
            return i
    return 0


def fnv1a(s):
    h = 2166136261
    for ch in s:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def date_label(d):
    y, m, day = d.split("-")
    return "%s %d" % (_MONTHS[int(m) - 1], int(day))


def load_recent(days):
    files = []
    for path in glob.glob(os.path.join(INDEX_DIR, "*.jsonl")):
        m = _FILE_RE.search(os.path.basename(path))
        if m and m.group(2) in CURRENT_STREAMS:
            files.append((m.group(1), m.group(2), path))
    if not files:
        return [], None
    max_date = max(f[0] for f in files)
    cutoff = (_dt.date.fromisoformat(max_date) - _dt.timedelta(days=days)).isoformat()
    stories = []
    for date, stream, path in sorted(files):
        if date < cutoff:
            continue
        with open(path) as fh:
            recs = [json.loads(ln) for ln in fh if ln.strip()]
        lead_pos = lead_index(recs)
        for pos, rec in enumerate(recs):
            topics = [t for t in (rec.get("topics") or []) if t in TOPICS] or derive_topics(rec)
            imp = rec.get("importance")
            if not isinstance(imp, int) or imp not in (1, 2, 3):
                imp = derive_importance(pos, rec.get("tags"), lead_pos)
            primary = topics[0]
            label, color = TOPICS.get(primary, (primary.title(), "#6b6f76"))
            y, mo, dy = date.split("-")
            stories.append({
                "id": rec.get("id"),
                "headline": rec.get("headline", ""),
                "summary": rec.get("summary", ""),
                "url": rec.get("url"),
                "source_domain": rec.get("source_domain") or "",
                "date": date,
                "date_label": date_label(date),
                "stream": stream,
                "stream_label": STREAM_LABEL.get(stream, stream.title()),
                "topics": topics,
                "topic_primary": primary,
                "topic_label": label,
                "topic_color": color,
                "importance": imp,
                "is_lead": imp == 3,
                "has_plate": imp >= 2,
                "permalink": "/%s/%s/%s/%s/" % (y, mo, dy, stream),
                "seed": fnv1a(rec.get("headline", "")),
            })
    return stories, max_date


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14, help="how many days back to include")
    ap.add_argument("--max", type=int, default=80, dest="cap",
                    help="cap the number of cards on the front page (0 = no cap)")
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()

    stories, max_date = load_recent(args.days)
    # newest first; within a day, leads first — this is the "fill from the top" order.
    stories.sort(key=lambda s: (s["date"], s["importance"]), reverse=True)
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
    by_imp = {i: sum(1 for s in stories if s["importance"] == i) for i in (3, 2, 1)}
    print("wrote %d stories (%d beats) -> %s  [lead=%d standard=%d brief=%d, through %s]"
          % (len(stories), len(topics), os.path.relpath(args.out, ROOT),
             by_imp[3], by_imp[2], by_imp[1], max_date))


if __name__ == "__main__":
    main()
