#!/usr/bin/env python3
"""Source health metrics -- SPIKE-2026-07-07-continuous-news.md §3.4 ("Measurement:
tools/sources/health.py -> _data/source-health.json").

Deterministic, no network: computes per-live-stream concentration/saturation/waiver numbers
from the index + recent briefs + the open-candidates buffer, and writes
_data/source-health.json (regenerated at every writer Step D, added to the rebase-retry
regenerate list -- review C2 fix). Never trusts a model's self-report -- same
recompute-don't-trust posture as lint.py, whose discovery_footer() this reuses for
waiver_rate.

Per stream: stories/unique_domains (rolling 30d window), new_domains (domain's first-ever
citation in that stream falls inside the window), top5_share (outlet-class ONLY -- hubs and
institutional excluded from both the ranking and its denominator), saturated (outlet >20% /
institutional >30% of the ALL-class rolling-30d total; hubs always exempt), waiver_rate
(share of in-window editions whose Discovery footer says "waived"), candidates_open (open
sources/candidates.jsonl lines for that stream). Plus an "overall" block.

Usage: health.py [--root PATH]
"""
import argparse
import datetime
import json
import os
import re
import sys

import registry
import lint

LIVE_STREAMS = ("news", "ai-ml", "science", "weekend")
WINDOW_DAYS = 30
OUTLET_BAR = 0.20
INSTITUTIONAL_BAR = 0.30
TOP_N = 5

POST_FILENAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-([a-z0-9-]+)\.md$")
CATEGORIES_RE = re.compile(r"^categories:\s*\[([a-z0-9-]+)\]", re.M)
DATE_RE = re.compile(r"^date:\s*(\d{4}-\d{2}-\d{2})", re.M)


def _in_window(date_str, today):
    try:
        return registry.days_since(date_str, today) <= WINDOW_DAYS
    except (ValueError, TypeError):
        return False


def _post_slug_and_date(path, text):
    m = CATEGORIES_RE.search(text)
    slug = m.group(1) if m else None
    if not slug:
        fm = POST_FILENAME_RE.match(os.path.basename(path))
        slug = fm.group(1) if fm else None
    dm = DATE_RE.search(text)
    date = dm.group(1) if dm else None
    if not date:
        fm = re.match(r"^(\d{4}-\d{2}-\d{2})-", os.path.basename(path))
        date = fm.group(1) if fm else None
    return slug, date


def _waiver_counts(root, slug, today):
    posts_dir = os.path.join(root, "_posts")
    if not os.path.isdir(posts_dir):
        return 0, 0
    waived = editions = 0
    for fname in sorted(os.listdir(posts_dir)):
        if not fname.endswith(".md"):
            continue
        with open(os.path.join(posts_dir, fname)) as f:
            text = f.read()
        post_slug, date = _post_slug_and_date(fname, text)
        if post_slug != slug or not date or not _in_window(date, today):
            continue
        editions += 1
        claim, _ = lint.discovery_footer(text)
        if claim == "waived":
            waived += 1
    return waived, editions


def _candidates_open(root, slug):
    path = os.path.join(root, "sources", "candidates.jsonl")
    return sum(1 for r in registry.read_jsonl(path) if r.get("stream") == slug)


def compute_stream_metrics(root, slug, all_records, today):
    in_window = [r for r in all_records if r.get("stream") == slug and r.get("date")
                 and _in_window(r["date"], today)]
    counts = {}
    for r in in_window:
        d = r.get("source_domain")
        if d:
            counts[d] = counts.get(d, 0) + 1

    # new_domains: domain's earliest-ever citation IN THIS STREAM falls inside the window --
    # a domain active in-window but with older history elsewhere is NOT "new".
    earliest = {}
    for r in all_records:
        if r.get("stream") != slug:
            continue
        d, date = r.get("source_domain"), r.get("date")
        if not d or not date:
            continue
        if d not in earliest or date < earliest[d]:
            earliest[d] = date
    new_domains = sum(1 for d in counts if d in earliest and _in_window(earliest[d], today))

    all_total = sum(counts.values())
    outlet_counts = {d: c for d, c in counts.items() if registry.classify_domain(d) == "outlet"}
    outlet_total = sum(outlet_counts.values())
    top5 = sorted(outlet_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:TOP_N]
    top5_share = (sum(c for _, c in top5) / outlet_total) if outlet_total else 0.0

    saturated = []
    for d, c in counts.items():
        cls = registry.classify_domain(d)
        if cls == "hub":
            continue
        bar = INSTITUTIONAL_BAR if cls == "institutional" else OUTLET_BAR
        if all_total and (c / all_total) > bar:
            saturated.append(d)
    saturated.sort()

    waived, editions = _waiver_counts(root, slug, today)

    return {
        "stories": len(in_window),
        "unique_domains": len(counts),
        "new_domains": new_domains,
        "top5_share": round(top5_share, 4),
        "saturated": saturated,
        "waiver_rate": round(waived / editions, 4) if editions else 0.0,
        "candidates_open": _candidates_open(root, slug),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default=".")
    args = p.parse_args()

    today = datetime.datetime.now(datetime.timezone.utc).date()
    all_records = list(registry.load_story_records(args.root))

    streams = {slug: compute_stream_metrics(args.root, slug, all_records, today) for slug in LIVE_STREAMS}
    overall = {
        "stories": sum(s["stories"] for s in streams.values()),
        "unique_domains_sum": sum(s["unique_domains"] for s in streams.values()),
        "candidates_open": sum(s["candidates_open"] for s in streams.values()),
    }
    data = {"streams": streams, "overall": overall}

    out_dir = os.path.join(args.root, "_data")
    os.makedirs(out_dir, exist_ok=True)
    text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    with open(os.path.join(out_dir, "source-health.json"), "w") as f:
        f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
