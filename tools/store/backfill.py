#!/usr/bin/env python3
"""Backfill the legacy per-day index (index/stories/{date}-{slug}.jsonl) into the
story ledger as ev:"seen" events (SPIKE-2026-07-07 §5 Step 1).

Mapping per record: id = story_id(url), or sha1("legacy:"+legacy_id) for urlless
records; legacy_ids = [record id]; editions/origin from the filename;
first_seen/updated = the file's date at midnight UTC; status = settled; every
other record field is carried verbatim. Idempotent: a legacy id already carried
by any seen event in the ledger is skipped.

Usage: python3 tools/store/backfill.py [--root R]
"""
import argparse
import glob
import hashlib
import importlib.util
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("_store_for_backfill",
                                               os.path.join(_HERE, "store.py"))
store = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(store)

_FNAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)\.jsonl$")


def legacy_fallback_id(legacy_id):
    """Stable id for records with no URL to canonicalize."""
    return "st-" + hashlib.sha1(("legacy:" + legacy_id).encode("utf-8")).hexdigest()[:12]


def _backfilled_legacy_ids(root):
    done = set()
    ledger = os.path.join(root, "index", "ledger")
    if not os.path.isdir(ledger):
        return done
    for name in sorted(os.listdir(ledger)):
        if not name.endswith(".jsonl"):
            continue
        with open(os.path.join(ledger, name), encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except ValueError:
                    continue
                if ev.get("ev") == "seen":
                    for lid in (ev.get("story") or {}).get("legacy_ids") or []:
                        done.add(lid)
    return done


def backfill(root):
    done = _backfilled_legacy_ids(root)
    added = skipped = 0
    for path in sorted(glob.glob(os.path.join(root, "index", "stories", "*.jsonl"))):
        m = _FNAME_RE.match(os.path.basename(path))
        if not m:
            continue
        date, slug = m.groups()
        ts = date + "T00:00:00Z"
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                lid = record.get("id")
                if not lid or lid in done:
                    skipped += 1
                    continue
                url = record.get("url")
                story = dict(record)  # carried fields survive verbatim
                story["id"] = store.story_id(url) if url else legacy_fallback_id(lid)
                story["status"] = "settled"
                story["first_seen"] = ts
                story["updated"] = ts
                story["legacy_ids"] = [lid]
                story["editions"] = ["%s-%s" % (date, slug)]
                story["origin"] = "writer:" + slug
                story["streams"] = [record.get("stream") or slug]
                store.append_event({"ev": "seen", "ts": ts, "actor": "backfill",
                                    "story": story}, root=root)
                done.add(lid)
                added += 1
    print("backfilled %d records (%d already present)" % (added, skipped))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="backfill.py", description=__doc__.splitlines()[0])
    p.add_argument("--root", default=store.REPO_ROOT)
    args = p.parse_args(argv)
    return backfill(args.root)


if __name__ == "__main__":
    sys.exit(main())
