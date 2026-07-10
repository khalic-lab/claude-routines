#!/usr/bin/env python3
"""Report-only reconciliation lint (SPIKE-2026-07-07 follow-up): catches exactly the
2026-07-07 Cuba defect class -- a story id present in a `publish` ledger event for an
edition but ABSENT from that edition's current index/stories/{edition}.jsonl.

Scans index/ledger/*.jsonl for ev=="publish" events whose edition falls within the last
--days days (default 14, root default '.'). For each in-window publish event, resolves
index/stories/{edition}.jsonl:
  - file missing entirely -> one "edition file missing" finding for that edition, no
    matter how many publish events reference it.
  - file present -> the publish sid "matches" iff ANY record in the file has
    story_id(norm_url(record["url"])) == that sid (imported from tools/store/store.py,
    never reimplemented). Matching is scoped to that edition file only -- a sid correctly
    reconciled under a DIFFERENT edition does not excuse its absence here.
  - a non-matching sid is FLAGGED -- unless a LATER ledger event (ts strictly after the
    publish event's ts) of kind "status" for the same sid has a status value starting
    with "merged-into:", in which case it is reported as 'resolved-by-merge'
    informationally and is not counted as flagged.

Output: one greppable line per finding, prefixed "RECONCILE:", plus a final summary line
"reconcile: X flagged, Y resolved-by-merge, Z editions checked". Report-only: always
exits 0 (mirrors tools/sources/lint.py without --arm). Corrupt/blank ledger lines and
url-less story records are skipped silently -- a broken line never costs an edition.
No network, stdlib only. Missing index/ dirs entirely -> exit 0, "nothing to check".

Usage: python3 tools/store/reconcile.py [--root PATH] [--days N]
"""
import argparse
import datetime as dt
import importlib.util
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("_store_for_reconcile",
                                               os.path.join(_HERE, "store.py"))
_store = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_store)
story_id = _store.story_id
norm_url = _store.norm_url


def _load_all_ledger_events(ledger_dir):
    """Every parseable event in every *.jsonl under ledger_dir, corrupt/blank lines
    skipped silently. Unlike store.py's _load_events, this is NOT windowed by file name --
    a resolving 'merged-into:' status can legitimately land in an older or newer day's
    file than the publish event it resolves, so every file must be considered."""
    events = []
    try:
        names = sorted(os.listdir(ledger_dir))
    except OSError:
        return events
    for name in names:
        if not name.endswith(".jsonl"):
            continue
        path = os.path.join(ledger_dir, name)
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ev = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(ev, dict):
                        events.append(ev)
        except OSError:
            continue
    return events


def _load_edition_sids(root, edition):
    """set of story ids present in index/stories/{edition}.jsonl, or None if the file
    doesn't exist. Corrupt lines and records lacking a usable url are skipped silently --
    they simply can't vouch for a sid, but never crash matching for the rest of the file."""
    path = os.path.join(root, "index", "stories", edition + ".jsonl")
    if not os.path.exists(path):
        return None
    sids = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if not isinstance(rec, dict):
                continue
            url = rec.get("url")
            if not url:
                continue
            try:
                sids.add(story_id(url))
            except ValueError:
                continue
    return sids


def reconcile(root, days):
    """Returns (finding_lines, flagged, resolved, editions_checked)."""
    ledger_dir = os.path.join(root, "index", "ledger")
    if not os.path.isdir(ledger_dir):
        return None, 0, 0, 0

    events = _load_all_ledger_events(ledger_dir)
    cutoff_date = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).strftime("%Y-%m-%d")

    # in-window publish events, deduped by (sid, edition) -> latest ts seen for that pair
    publish_by_key = {}
    editions_seen = set()
    for ev in events:
        if ev.get("ev") != "publish":
            continue
        sid, edition, ts = ev.get("id"), ev.get("edition"), ev.get("ts")
        if not sid or not edition or not ts:
            continue
        edition_date = edition[:10]
        if edition_date < cutoff_date:
            continue
        editions_seen.add(edition)
        key = (sid, edition)
        if key not in publish_by_key or ts > publish_by_key[key]:
            publish_by_key[key] = ts

    # every status event, keyed by sid -- unrestricted by window (a resolving event may be
    # dated well after the publish event's own edition/window)
    status_by_sid = {}
    for ev in events:
        if ev.get("ev") != "status":
            continue
        sid, status, ts = ev.get("id"), ev.get("status"), ev.get("ts")
        if not sid or not status or not ts:
            continue
        status_by_sid.setdefault(sid, []).append((ts, status))

    findings = []
    flagged = resolved = 0
    stories_cache = {}
    reported_missing_editions = set()

    for (sid, edition), pub_ts in sorted(publish_by_key.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        if edition not in stories_cache:
            stories_cache[edition] = _load_edition_sids(root, edition)
        sids_in_file = stories_cache[edition]

        if sids_in_file is None:
            if edition not in reported_missing_editions:
                reported_missing_editions.add(edition)
                findings.append(
                    "RECONCILE: edition file missing -- edition=%s (index/stories/%s.jsonl "
                    "not found) sid=%s" % (edition, edition, sid))
            continue

        if sid in sids_in_file:
            continue  # matched -- no finding

        merged_resolution = None
        for st_ts, status in sorted(status_by_sid.get(sid, [])):
            if st_ts > pub_ts and status.startswith("merged-into:"):
                merged_resolution = status
                break

        if merged_resolution:
            resolved += 1
            findings.append(
                "RECONCILE: resolved-by-merge sid=%s edition=%s -- publish present but story "
                "absent from edition file; later status %r stands it down" %
                (sid, edition, merged_resolution))
        else:
            flagged += 1
            findings.append(
                "RECONCILE: flagged sid=%s edition=%s -- publish present but story absent "
                "from edition file, no resolving merged-into status found" % (sid, edition))

    return findings, flagged, resolved, len(editions_seen)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default=".")
    p.add_argument("--days", type=int, default=14)
    args = p.parse_args(argv)

    findings, flagged, resolved, editions_checked = reconcile(args.root, args.days)

    if findings is None:
        print("reconcile: nothing to check (no index/ledger directory under %r)" % args.root)
        return 0

    for line in findings:
        print(line)
    print("reconcile: %d flagged, %d resolved-by-merge, %d editions checked" %
          (flagged, resolved, editions_checked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
