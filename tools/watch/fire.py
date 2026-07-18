#!/usr/bin/env python3
"""Watch fire bookkeeping -- everything after the model's match judgment.

`match` writes the ntfy notification stub (real JSON encoding, computed UTC
timestamp) and updates that watch's `last_fired` in watches.yml with a targeted
line substitution -- comments, ordering, and every other field are preserved
byte-for-byte (the model no longer hand-edits YAML). `push` stages + commits +
pushes any pending watch changes, deriving the commit message from the new stub
filenames, with the retry-once rule; it is a silent no-op when nothing changed.

Usage:
  fire.py match --id <watch-id> --url <click-url> --body <one-liner> [--root .] [--today YYYY-MM-DD]
  fire.py push [--root .] [--dry-run]
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import due as _due  # noqa: E402  (parse_watches, zurich_today)

STUB_RE = re.compile(r"-watch-(.+)\.json$")


def _git(argv):
    return ["git", "-c", "user.email=routine@khalic-lab", "-c", "user.name=Watch Routine",
            "-c", "commit.gpgsign=false"] + argv


def update_last_fired(text, watch_id, today):
    """Within the `- id: <watch_id>` block only, rewrite the last_fired line.
    Returns the new text, or None when the id (or its last_fired line) is absent."""
    lines = text.split("\n")
    start = None
    for i, line in enumerate(lines):
        m = _due.ENTRY_RE.match(line)
        if m and _due._unquote(m.group(1)) == watch_id:
            start = i
            break
    if start is None:
        return None
    for j in range(start + 1, len(lines)):
        if _due.ENTRY_RE.match(lines[j]):
            break
        m = re.match(r"^(\s+last_fired:\s*).*$", lines[j])
        if m:
            lines[j] = '%s"%s"' % (m.group(1), today)
            return "\n".join(lines)
    return None


def cmd_match(args):
    root = os.path.abspath(args.root)
    path = os.path.join(root, "watches.yml")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if not any(w.get("id") == args.id for w in _due.parse_watches(text)):
        print("fire.py: unknown watch id %r -- nothing written." % args.id, file=sys.stderr)
        return 1

    today = args.today or _due.zurich_today().isoformat()
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stub_path = os.path.join(root, "pending-notifications", "%s-watch-%s.json" % (ts, args.id))
    os.makedirs(os.path.dirname(stub_path), exist_ok=True)
    with open(stub_path, "w", encoding="utf-8") as fh:
        json.dump({"title": "Watch fired -- %s" % args.id, "click": args.url,
                   "body": args.body, "tags": "eyes"}, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    new_text = update_last_fired(text, args.id, today)
    if new_text is None:
        print("fire.py: no last_fired line for %r -- stub written, watches.yml untouched." % args.id,
              file=sys.stderr)
    elif new_text != text:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new_text)
    print("fire.py: %s fired -- stub %s, last_fired -> %s"
          % (args.id, os.path.relpath(stub_path, root), today))
    return 0


def cmd_push(args):
    root = os.path.abspath(args.root)
    # -uall: an untracked pending-notifications/ must list its individual stub
    # files (the commit message is derived from their names), not just the dir.
    proc = subprocess.run(["git", "status", "--porcelain", "-uall", "--", "watches.yml",
                           "pending-notifications"], cwd=root, capture_output=True, text=True)
    changed = [l for l in (proc.stdout or "").splitlines() if l.strip()]
    if not changed:
        print("fire.py: nothing to push.")
        return 0
    ids = sorted({m.group(1) for l in changed for m in [STUB_RE.search(l)] if m})
    message = "Watch fired: %s" % ", ".join(ids) if ids else "Watch bookkeeping"
    if args.dry_run:
        print("fire.py: DRY-RUN would commit %r (%d change(s))" % (message, len(changed)))
        return 0
    subprocess.run(_git(["add", "watches.yml", "pending-notifications/"]), cwd=root)
    subprocess.run(_git(["commit", "-m", message]), cwd=root)
    if subprocess.run(_git(["push", "origin", "main"]), cwd=root).returncode == 0:
        print("fire.py: pushed -- %s" % message)
        return 0
    subprocess.run(_git(["pull", "--rebase", "origin", "main"]), cwd=root)
    if subprocess.run(_git(["push", "origin", "main"]), cwd=root).returncode == 0:
        print("fire.py: pushed on retry -- %s" % message)
        return 0
    print("fire.py: push failed after retry -- next cron run picks up the unpushed stub.",
          file=sys.stderr)
    return 0  # per the watch contract: do NOT retry further, never crash the run


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("match")
    m.add_argument("--id", required=True)
    m.add_argument("--url", required=True)
    m.add_argument("--body", required=True)
    m.add_argument("--root", default=".")
    m.add_argument("--today", default=None)
    m.set_defaults(fn=cmd_match)
    q = sub.add_parser("push")
    q.add_argument("--root", default=".")
    q.add_argument("--dry-run", action="store_true")
    q.set_defaults(fn=cmd_push)
    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
