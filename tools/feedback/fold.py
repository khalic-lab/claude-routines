#!/usr/bin/env python3
"""Bridge-side feedback fold (SPIKE-2026-07-07-continuous-news.md §3.5 / §4): resolves each
feedback record's carried story_id to a real ledger story id and appends one ev:"feedback"
event per resolved record, closing the window-arithmetic orphaning class the old
Evaluator-driven consumption had (27% of all reader feedback lost, per the dossier).

Resolution order (first match wins; CONTRACT):
  1. story_id already "st-..." -> direct, no ledger lookup needed
  2. story_id found in materialize()'s by_legacy (pre-anchor slug ids)
  3. record's own "url" field found in materialize()'s by_url (covers alt_urls too)
  4. unresolvable -> left consumed:false, counted + printed with a reason

Resolved records: consumed flipped true, source_domain backfilled (derived from the resolved
story's own url) only if not already set, and one ev:"feedback" ledger event appended — ts is
the record's OWN ts (the reader's vote time), never fold wall-clock, so last-write-wins has a
deterministic winner. Appending is skipped if that fb_id is already in the ledger (crash-
recovery safe: a run that appended but died before rewriting feedback/*.jsonl won't double-
append on retry). Per feedback file, ledger events are appended BEFORE that file is rewritten —
never the reverse — so a crash/error mid-append leaves the feedback file byte-untouched (no
consumed:true with no matching ledger event) and a retry folds it cleanly. Untouched records'
raw JSON lines survive rewrite byte-identical; a file with nothing to fold is never opened for
writing. A line that fails to parse as JSON is skipped with a printed warning and preserved
byte-identical in any rewrite — one corrupt/truncated line never aborts the whole fold.

Usage: python3 tools/feedback/fold.py [--root R] [--dry-run]
"""
import argparse
import glob
import importlib.util
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "_store_for_fold", os.path.join(_HERE, "..", "store", "store.py"))
store = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(store)

# fold must resolve against the FULL ledger history, not materialize()'s 60-day default window
_ALL_TIME_DAYS = 36500


def _domain(url):
    nu = store.norm_url(url)
    return nu.split("/", 1)[0] if nu else None


def _existing_fb_ids(root):
    """fb_id set already folded into the ledger (any file, any age) — dedupe key for idempotent
    re-runs and crash recovery."""
    ids = set()
    ledger = os.path.join(root, "index", "ledger")
    if not os.path.isdir(ledger):
        return ids
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
                if ev.get("ev") == "feedback" and ev.get("fb_id"):
                    ids.add(ev["fb_id"])
    return ids


def _resolve(rec, snap):
    """CONTRACT resolution order. Returns (sid, reason) — reason is set only when sid is None."""
    raw = rec.get("story_id")
    if raw and raw.startswith("st-"):
        return raw, None
    if raw and raw in snap["by_legacy"]:
        return snap["by_legacy"][raw], None
    url = rec.get("url")
    if url:
        nu = store.norm_url(url)
        sid = snap["by_url"].get(nu) if nu else None
        if sid:
            return sid, None
    return None, "no story_id/legacy/url match"


def fold(root, dry_run=False):
    snap = store.materialize(days=_ALL_TIME_DAYS, root=root)
    stories = snap["stories"]
    already = _existing_fb_ids(root)

    table = []       # (fb_id, status, detail) — printed as the disposition table
    folded = reconciled = unresolved = 0

    for path in sorted(glob.glob(os.path.join(root, "feedback", "*.jsonl"))):
        raw_lines, recs = [], []
        with open(path, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                line = line.rstrip("\n")
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except ValueError as e:
                    print("fold: %s:%d: skipping corrupt line (%s)" % (path, lineno, e))
                    raw_lines.append(line)
                    recs.append(None)  # preserved byte-identical below, never touched
                    continue
                raw_lines.append(line)
                recs.append(rec)

        dirty = False
        to_append = []   # ev:"feedback" events for THIS file — appended before its rewrite
        for i, rec in enumerate(recs):
            if rec is None:
                continue  # corrupt line — left untouched, preserved verbatim on rewrite
            fb_id = rec.get("id")
            if not fb_id:
                continue  # malformed record — not fold.py's job to repair
            if rec.get("consumed"):
                continue  # already folded (or handled by the pre-ledger Evaluator flow)

            sid, reason = _resolve(rec, snap)
            if sid is None:
                unresolved += 1
                table.append((fb_id, "UNRESOLVED", reason))
                continue

            rec["consumed"] = True
            story = stories.get(sid)
            domain = _domain(story.get("url")) if story else None
            if domain and not rec.get("source_domain"):
                rec["source_domain"] = domain
            raw_lines[i] = json.dumps(rec, ensure_ascii=False)
            dirty = True

            if fb_id in already:
                reconciled += 1  # ledger already has this vote; just fixing up the record
                table.append((fb_id, "reconciled", sid))
                continue
            already.add(fb_id)
            folded += 1
            table.append((fb_id, "resolved", sid))
            to_append.append({
                "ev": "feedback", "ts": rec.get("ts"), "actor": "bridge", "id": sid,
                "fb_id": fb_id, "vote": rec.get("vote"), "reason": rec.get("reason") or "",
                "reader": rec.get("reader"), "surface": rec.get("surface"),
                "brief": rec.get("brief"), "raw_story_id": rec.get("story_id"),
            })

        if dirty and not dry_run:
            # Append FIRST, rewrite SECOND — never the reverse. The ledger event is the
            # durable fact; a crash/error here leaves this file's raw_lines (with consumed
            # still false) unwritten. A retry re-resolves the same records: any event that DID
            # land is caught by the fb_id dedupe (the "reconciled" path fixes up the record with
            # no duplicate append); any that didn't land is retried for real. This is what makes
            # append-then-crash safe to just re-run — rewrite-then-crash is not.
            for ev in to_append:
                store.append_event(ev, root=root)
            with open(path, "w", encoding="utf-8") as f:
                for ln in raw_lines:
                    f.write(ln + "\n")

    for fb_id, status, detail in table:
        if status == "UNRESOLVED":
            print("fold: %-38s UNRESOLVED  (%s)" % (fb_id, detail))
        else:
            print("fold: %-38s %-10s -> %s" % (fb_id, status, detail))
    print("fold: %d folded, %d reconciled, %d unresolved (of %d)%s"
          % (folded, reconciled, unresolved, len(table),
             "  [DRY RUN — nothing written]" if dry_run else ""))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="fold.py", description=__doc__.splitlines()[0])
    p.add_argument("--root", default=store.REPO_ROOT)
    p.add_argument("--dry-run", action="store_true", help="print the disposition table, write nothing")
    args = p.parse_args(argv)
    return fold(args.root, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
