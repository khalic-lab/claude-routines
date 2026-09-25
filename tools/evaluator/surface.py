#!/usr/bin/env python3
"""Reading-surface check for the Weekly Evaluator (dimension D, second half).

The homepage feed is the only place a reader sees a story, so "the brief published" and "the
reader could read it" are separate facts. This reports the gap between them, READ-ONLY and with
no network: it imports tools/build_stories_feed.py for its parser and parity check (never runs
its main(), which writes _data/homefeed.json and _data/stats.json) and reads the committed
_data/homefeed.json as the surface the reader actually got.

Per edition in the window: stories the post holds, records the index kept, cards on the
committed feed, and the builder's identity parity (kept records that reached no card). Then the
builder's lede-fallback WARNs (a story whose prose the parser could not find), desks whose newest
edition is overdue for its cadence, and a feed older than the newest post.

Only three things are FLAGS; the rest is context. Older editions legitimately show fewer cards
than stories (the builder's age-out and per-edition cap drain them), so a low count is flagged
only on a desk's NEWEST edition, below min(stories, the builder's MIN_LATEST_EDITION floor).

Usage: surface.py [--root .] [--today YYYY-MM-DD] [--days 14]
"""
import argparse
import contextlib
import datetime as dt
import glob
import importlib.util
import io
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_BUILDER = os.path.normpath(os.path.join(_HERE, "..", "build_stories_feed.py"))

# Days a desk may go without a new edition before it is overdue, from its cron cadence
# (ARCHITECTURE.md §1.1): News daily; AI/ML Tue+Fri, so Fri->Tue is the long gap; the rest weekly.
CADENCE_DAYS = {"news": 1, "ai-ml": 4, "science": 7, "weekend": 7, "sports": 7}
WARN_RE = re.compile(r"^WARN no body parsed: (\S+) story (\S+)")


def load_builder(root):
    """The feed builder as a module, re-pointed at `root`. Import only: its main() writes."""
    spec = importlib.util.spec_from_file_location("_surface_builder", _BUILDER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.ROOT = root
    mod.POSTS_DIR = os.path.join(root, "_posts")
    mod.INDEX_DIR = os.path.join(root, "index", "stories")
    return mod


def _count_lines(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return sum(1 for ln in fh if ln.strip())


def survey(root, today, days):
    """Everything the report prints, as data (the tests read this, not the text)."""
    b = load_builder(root)
    start = (dt.date.fromisoformat(today) - dt.timedelta(days=days)).isoformat()

    editions = []                                   # (date, stream, path), oldest first
    latest = {}
    for path in sorted(glob.glob(os.path.join(root, "_posts", "*.md"))):
        m = b._FILE_RE.search(os.path.basename(path))
        if not m or m.group(2) not in b.CURRENT_STREAMS or m.group(1) > today:
            continue
        latest[m.group(2)] = max(latest.get(m.group(2), ""), m.group(1))
        if m.group(1) >= start:
            editions.append((m.group(1), m.group(2), path))

    feed_path = os.path.join(root, "_data", "homefeed.json")
    feed = {}
    if os.path.exists(feed_path):
        with open(feed_path, encoding="utf-8") as fh:
            feed = json.load(fh)
    cards = {}
    for s in feed.get("stories") or []:
        key = (s.get("date"), s.get("stream"))
        cards[key] = cards.get(key, 0) + 1

    # The builder prints its lede-fallback WARNs while parsing; capture, never echo raw.
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        b.load_recent(days)
    warns = [m.groups() for m in map(WARN_RE.match, buf.getvalue().splitlines()) if m]

    misses = {}
    for date in sorted({d for d, _, _ in editions}):
        for ed, recs in b.edition_parity(date):
            misses[ed] = recs

    floor = getattr(b, "MIN_LATEST_EDITION", 6)
    rows, flags = [], []
    for date, stream, path in editions:
        with open(path, encoding="utf-8") as fh:
            n_post = len(b.parse_post(fh.read()) or [])
        ed = "%s-%s" % (date, stream)
        row = {"edition": ed, "post": n_post,
               "kept": _count_lines(os.path.join(root, "index", "stories", ed + ".jsonl")),
               "cards": cards.get((date, stream), 0),
               "unmapped": len(misses.get(ed, [])),
               "warns": sum(1 for p, _ in warns if os.path.basename(p) == ed + ".md"),
               "newest": date == latest.get(stream)}
        rows.append(row)
        if row["unmapped"]:
            flags.append("PARITY %s: %d kept record(s) reached no card" % (ed, row["unmapped"]))
        if row["newest"] and row["cards"] < min(n_post, floor):
            flags.append("SHORT %s: newest edition shows %d card(s) of %d stories (floor %d)"
                         % (ed, row["cards"], n_post, floor))
    for post, sid in warns:
        flags.append("WARN %s story %s: no body parsed, card shows its lede" % (post, sid))

    overdue = []
    for stream in sorted(CADENCE_DAYS):
        last = latest.get(stream)
        age = (dt.date.fromisoformat(today) - dt.date.fromisoformat(last)).days if last else None
        if age is None or age > CADENCE_DAYS[stream]:
            overdue.append({"stream": stream, "latest": last, "age": age,
                            "cadence": CADENCE_DAYS[stream]})
            flags.append("OVERDUE %s: newest edition %s (%s days; cadence %d)"
                         % (stream, last or "none", "?" if age is None else age,
                            CADENCE_DAYS[stream]))

    newest_post = max(latest.values()) if latest else None
    feed_gen = feed.get("generated")
    if newest_post and feed_gen != newest_post:
        flags.append("STALE-FEED: homefeed.json generated %s, newest post %s"
                     % (feed_gen or "missing", newest_post))
    return {"window": [start, today], "rows": rows, "warns": warns, "overdue": overdue,
            "feed_generated": feed_gen, "flags": flags}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--root", default=".")
    p.add_argument("--today", default=None, help="window END date; default today")
    p.add_argument("--days", type=int, default=14, help="window length (the builder's scan)")
    args = p.parse_args(argv)
    root = os.path.abspath(args.root)
    today = args.today or dt.date.today().isoformat()
    try:
        r = survey(root, today, args.days)
    except Exception as exc:   # the builder is edited by other tracks; degrade, never crash
        print("surface: unavailable (%s: %s) -- read _data/homefeed.json by hand"
              % (type(exc).__name__, exc))
        return 0
    print("surface: window [%s, %s], feed generated %s"
          % (r["window"][0], r["window"][1], r["feed_generated"] or "missing"))
    print("%-24s %5s %5s %6s %9s %6s" % ("edition", "post", "kept", "cards", "unmapped", "warns"))
    for row in r["rows"]:
        print("%-24s %5d %5s %6d %9d %6d%s"
              % (row["edition"], row["post"], "-" if row["kept"] is None else row["kept"],
                 row["cards"], row["unmapped"], row["warns"], "  (newest)" if row["newest"] else ""))
    for f in r["flags"]:
        print("FLAG " + f)
    print("surface: %d flag(s) -- %d parity miss(es), %d lede-fallback WARN(s), %d overdue desk(s)"
          % (len(r["flags"]), sum(x["unmapped"] for x in r["rows"]), len(r["warns"]),
             len(r["overdue"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
