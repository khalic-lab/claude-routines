#!/usr/bin/env python3
"""Watch cooldown gate -- the deterministic first step of the Watch routine.

Parses watches.yml and prints, as JSON, the watches whose cooldown has lapsed
(`last_fired` null, or today - last_fired >= cooldown_days) -- or exactly
`NONE DUE` when none has, so the routine can stop after a single Bash call
instead of parsing YAML and reasoning about dates itself. The model's only
remaining job is the probe: WebSearch(query) + judging `match_when` against
snippets, then tools/watch/fire.py for the bookkeeping.

Read-only; never edits watches.yml. Malformed file -> prints NONE DUE (the
routine's contract on a malformed registry is: exit silently, commit nothing).

Usage: due.py [--root .] [--today YYYY-MM-DD]
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

ENTRY_RE = re.compile(r"^\s*-\s+id:\s*(.+?)\s*$")
FIELD_RE = re.compile(r"^\s+([A-Za-z_]+):\s*(.*?)\s*$")
DEFAULT_COOLDOWN = 14


def _unquote(v):
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def parse_watches(text):
    watches, cur = [], None
    for line in text.split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = ENTRY_RE.match(line)
        if m:
            cur = {"id": _unquote(m.group(1))}
            watches.append(cur)
            continue
        if cur is not None and not line.lstrip().startswith("- "):
            m = FIELD_RE.match(line)
            if m:
                cur[m.group(1)] = _unquote(m.group(2))
    return watches


def zurich_today():
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo("Europe/Zurich")).date()
    except Exception:
        return dt.date.today()


def due_watches(watches, today):
    due = []
    for w in watches:
        if not w.get("id") or not w.get("query"):
            continue
        try:
            cooldown = int(w.get("cooldown_days") or DEFAULT_COOLDOWN)
        except ValueError:
            cooldown = DEFAULT_COOLDOWN
        last = (w.get("last_fired") or "").strip()
        if last.lower() in ("", "null", "~", "none"):
            last = None
        if last:
            try:
                if (today - dt.date.fromisoformat(last)).days < cooldown:
                    continue
            except ValueError:
                pass  # unparseable last_fired -> treat as due (fail open, probe it)
        due.append({"id": w["id"], "query": w.get("query", ""),
                    "match_when": w.get("match_when", ""),
                    "cooldown_days": cooldown,
                    "last_fired": last})
    return due


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--root", default=".")
    p.add_argument("--today", default=None, help="YYYY-MM-DD; defaults to Europe/Zurich today")
    args = p.parse_args(argv)

    today = dt.date.fromisoformat(args.today) if args.today else zurich_today()
    path = os.path.join(args.root, "watches.yml")
    try:
        with open(path, encoding="utf-8") as fh:
            watches = parse_watches(fh.read())
    except OSError:
        print("NONE DUE")
        return 0

    due = due_watches(watches, today)
    if not due:
        print("NONE DUE")
    else:
        print(json.dumps({"today": today.isoformat(), "due": due},
                         ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
