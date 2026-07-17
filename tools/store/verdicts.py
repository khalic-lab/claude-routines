#!/usr/bin/env python3
"""Persist a writer run's dedup verdicts -- the desk-stats raw material.

`dedup.py check` writes its per-candidate verdicts to /tmp/verdicts.json and the run
throws them away: the very numbers the homepage stats panel wants ("N candidates
checked, X dropped as repeats") die with the sandbox. This tool snapshots them into
`index/verdicts/{date}-{slug}.json`, joining each verdict back to its candidate (for
the url the check output omits). Step E's `git add index/` already stages the file --
no extra writer wiring beyond the one DEDUP.md Step A line that invokes this.

Non-fatal contract like every dedup step: the caller wraps it in `|| echo ...`; a
malformed input exits non-zero and costs the run nothing but the snapshot.
Idempotent: re-running for the same edition overwrites with the same content.

Usage:
  python3 tools/store/verdicts.py --candidates /tmp/cand.json --verdicts /tmp/verdicts.json \
      --date 2026-07-12 --slug news [--root .]
"""
import argparse
import json
import os
import re
import sys

SLUGS = ("news", "ai-ml", "science", "weekend", "sports")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _load(path, list_key):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict) and list_key in data:
        return data, data[list_key]
    if isinstance(data, list):
        return {}, data
    raise ValueError("%s: expected a list or an object with %r" % (path, list_key))


def snapshot(candidates_path, verdicts_path, date, slug, root="."):
    """Build the snapshot dict (pure -- no I/O beyond reading the two inputs)."""
    _, cands = _load(candidates_path, "candidates")
    meta, results = _load(verdicts_path, "results")

    by_id = {c["id"]: c for c in cands if isinstance(c, dict) and "id" in c}
    joined = []
    for pos, r in enumerate(results):
        cand = by_id.get(r.get("id"))
        if cand is None and len(results) == len(cands):
            cand = cands[pos]  # cmd_check emits results in candidate order
        cand = cand or {}
        row = {
            "headline": r.get("headline") or cand.get("headline", ""),
            "verdict": r.get("verdict"),
        }
        if row["verdict"] not in ("NEW", "ONGOING", "REPEAT"):
            raise ValueError("result %d: bad verdict %r" % (pos, row["verdict"]))
        if cand.get("url"):
            row["url"] = cand["url"]
        if r.get("score") is not None:
            row["score"] = r["score"]
        if r.get("match_reason"):
            row["match_reason"] = r["match_reason"]
        m = r.get("matched") or {}
        if m.get("id"):
            row["matched_id"] = m["id"]
        if m.get("date"):
            row["matched_date"] = m["date"]
        if m.get("headline"):
            row["matched_headline"] = m["headline"]
        joined.append(row)

    return {
        "date": date,
        "slug": slug,
        "window_days": meta.get("window_days"),
        "checked": len(joined),
        "results": joined,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--verdicts", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--root", default=".")
    args = ap.parse_args(argv)

    if not DATE_RE.match(args.date):
        print("verdicts: bad --date %r (want YYYY-MM-DD)" % args.date, file=sys.stderr)
        return 2
    if args.slug not in SLUGS:
        print("verdicts: bad --slug %r (want one of %s)" % (args.slug, "/".join(SLUGS)), file=sys.stderr)
        return 2
    try:
        snap = snapshot(args.candidates, args.verdicts, args.date, args.slug, args.root)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as e:
        print("verdicts: %s" % e, file=sys.stderr)
        return 2

    out_dir = os.path.join(args.root, "index", "verdicts")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "%s-%s.json" % (args.date, args.slug))
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(snap, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    tally = {v: 0 for v in ("NEW", "ONGOING", "REPEAT")}
    for r in snap["results"]:
        tally[r["verdict"]] += 1
    print("verdicts snapshot: %s (%d checked: %d new, %d ongoing, %d repeat)"
          % (os.path.relpath(out_path, args.root), snap["checked"],
             tally["NEW"], tally["ONGOING"], tally["REPEAT"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
