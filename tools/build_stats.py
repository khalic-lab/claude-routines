#!/usr/bin/env python3
"""Aggregate desk stats -> _data/stats.json (the homepage "in numbers" panel).

Reads only what the pipeline already commits -- no network, non-fatal by convention:
  - index/ledger/*.jsonl        publish/seen events (all-time story + edition counts,
                                 per-stream split, distinct source domains, tag counts)
  - _posts/*.md Coverage footers (window only: word-count + research-tool-call lines)
  - sources/registry.yml         credibility-lifecycle status counts
  - index/verdicts/*.json        dedup verdict snapshots (tools/store/verdicts.py;
                                 exist only from 2026-07-12 onward -- the panel's
                                 "tracking since" honesty label comes from the earliest
                                 file, and every derived number degrades to null/0
                                 when the directory is empty)

"Dropped" is computed, not trusted: a REPEAT verdict is dropped by definition
(DEDUP.md Step B: always drop); an ONGOING verdict counts as dropped only when its
url does NOT appear in that edition's index/stories/{date}-{slug}.jsonl (the writer
may legitimately keep an ONGOING with a new development). ONGOING verdicts whose
edition index file is already pruned (>40 days) are counted `ongoing_unjoinable`,
never guessed. Time saved = drops x 2 min -- an estimate, labeled as such in the UI.

Invoked automatically at the end of tools/build_stories_feed.py (which every writer
already runs unconditionally), so it needs no routine-prompt wiring of its own.

Usage: python3 tools/build_stats.py [--root .] [--window 30] [--as-of YYYY-MM-DD]
"""
import argparse
import datetime as dt
import glob
import importlib.util
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLUGS = ("news", "ai-ml", "science", "weekend", "sports")
TRACKED_TAGS = ("single-source", "disputed", "preprint", "vendor PR", "official PR", "rumour", "unconfirmed")
MINUTES_PER_DROP = 2  # reading-time estimate; the UI labels it "~"

_store_spec = importlib.util.spec_from_file_location(
    "_store", os.path.join(os.path.dirname(os.path.abspath(__file__)), "store", "store.py"))
_store = importlib.util.module_from_spec(_store_spec)
_store_spec.loader.exec_module(_store)
norm_url = _store.norm_url

WORDS_RE = re.compile(r"^- Word count:\s*~?([\d,]+)", re.M)
CALLS_RE = re.compile(r"tool calls[^:]*:\s*(\d+)")
STATUS_RE = re.compile(r"^ {2}status:\s*(\S+)", re.M)


def _edition_slug(edition):
    return edition[11:] if len(edition) > 11 else edition


def _edition_date(edition):
    return edition[:10]


def load_ledger(root):
    """(publishes, stories): distinct publish (id, edition) pairs + id -> seen-story map."""
    stories, publishes = {}, set()
    for path in sorted(glob.glob(os.path.join(root, "index", "ledger", "*.jsonl"))):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except ValueError:
                    continue  # union-merged ledger: not every line is ours
                if ev.get("ev") == "seen" and isinstance(ev.get("story"), dict):
                    sid = ev["story"].get("id")
                    if sid and sid not in stories:
                        stories[sid] = ev["story"]
                elif ev.get("ev") == "publish" and ev.get("id") and ev.get("edition"):
                    if _edition_slug(ev["edition"]) in SLUGS:
                        publishes.add((ev["id"], ev["edition"]))
    return publishes, stories


def footer_stats(root, since):
    words, calls = [], []
    for path in glob.glob(os.path.join(root, "_posts", "*.md")):
        name = os.path.basename(path)
        date, slug = name[:10], name[11:-3]
        if slug not in SLUGS or date < since:
            continue
        try:
            text = open(path, encoding="utf-8").read()
        except OSError:
            continue
        m = WORDS_RE.search(text)
        if m:
            words.append(int(m.group(1).replace(",", "")))
            c = CALLS_RE.search(text[m.start():m.start() + 200])
            if c:
                calls.append(int(c.group(1)))
    return words, calls


def registry_counts(root):
    path = os.path.join(root, "sources", "registry.yml")
    if not os.path.exists(path):
        return {}
    counts = {}
    for status in STATUS_RE.findall(open(path, encoding="utf-8").read()):
        counts[status] = counts.get(status, 0) + 1
    return counts


def dedup_stats(root):
    out = {"since": None, "editions": 0, "checked": 0, "repeats_dropped": 0,
           "ongoing_dropped": 0, "ongoing_unjoinable": 0, "est_minutes_saved": 0}
    for path in sorted(glob.glob(os.path.join(root, "index", "verdicts", "*.json"))):
        try:
            snap = json.load(open(path, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        date, slug = snap.get("date"), snap.get("slug")
        if not date or slug not in SLUGS:
            continue
        out["editions"] += 1
        out["since"] = min(out["since"] or date, date)
        out["checked"] += snap.get("checked", 0)

        idx = os.path.join(root, "index", "stories", "%s-%s.jsonl" % (date, slug))
        published = None  # None = edition index pruned; ONGOING is then unjoinable
        if os.path.exists(idx):
            published = set()
            with open(idx, encoding="utf-8") as fh:
                for line in fh:
                    try:
                        u = norm_url(json.loads(line).get("url"))
                    except ValueError:
                        continue
                    if u:
                        published.add(u)
        for r in snap.get("results", []):
            if r.get("verdict") == "REPEAT":
                out["repeats_dropped"] += 1
            elif r.get("verdict") == "ONGOING":
                if published is None:
                    out["ongoing_unjoinable"] += 1
                elif norm_url(r.get("url")) not in published:
                    out["ongoing_dropped"] += 1
    out["est_minutes_saved"] = (out["repeats_dropped"] + out["ongoing_dropped"]) * MINUTES_PER_DROP
    return out


def build(root, window, as_of):
    publishes, stories = load_ledger(root)
    since = (dt.date.fromisoformat(as_of) - dt.timedelta(days=window)).isoformat()

    editions = {e for _, e in publishes}
    by_stream, domains, tags = {}, set(), {t: 0 for t in TRACKED_TAGS}
    for sid in {i for i, _ in publishes}:
        s = stories.get(sid, {})
        d = s.get("source_domain") or (norm_url(s.get("url")) or "").split("/")[0]
        if d:
            domains.add(d)
        for t in TRACKED_TAGS:
            if t in (s.get("tags") or []):
                tags[t] += 1
    for _, e in publishes:
        by_stream[_edition_slug(e)] = by_stream.get(_edition_slug(e), 0) + 1

    win_pub = {(i, e) for i, e in publishes if _edition_date(e) >= since}
    words, calls = footer_stats(root, since)

    return {
        "generated": as_of,
        "all_time": {
            "since": min((_edition_date(e) for e in editions), default=None),
            "stories": len(publishes),
            "editions": len(editions),
            "by_stream": dict(sorted(by_stream.items())),
            "distinct_domains": len(domains),
            "tags": {k: v for k, v in tags.items() if v},
        },
        "window": {
            "days": window,
            "stories": len(win_pub),
            "editions": len({e for _, e in win_pub}),
            "avg_words": round(sum(words) / len(words)) if words else None,
            "avg_tool_calls": round(sum(calls) / len(calls)) if calls else None,
        },
        "sources": registry_counts(root),
        "dedup": dedup_stats(root),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--window", type=int, default=30)
    ap.add_argument("--as-of", default=None, help="YYYY-MM-DD; defaults to today")
    ap.add_argument("--out", default=None, help="defaults to <root>/_data/stats.json")
    args = ap.parse_args(argv)
    as_of = args.as_of or dt.date.today().isoformat()

    stats = build(args.root, args.window, as_of)
    out = args.out or os.path.join(args.root, "_data", "stats.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(stats, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    d = stats["dedup"]
    print("wrote %s: %d stories / %d editions all-time, dedup tracking %s (%d checked, %d dropped)"
          % (os.path.relpath(out, args.root), stats["all_time"]["stories"],
             stats["all_time"]["editions"], d["since"] or "not started",
             d["checked"], d["repeats_dropped"] + d["ongoing_dropped"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
