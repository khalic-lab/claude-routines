#!/usr/bin/env python3
"""Overdue editions: a scheduled writer fire whose post has not reached `_posts/` in time.

Run by the local bridge every tick, after a successful pull (tools/bridge/bridge.sh). For
each routine in routines/MANIFEST.md that writes posts, every fire time in the lookback
window that is at least `--grace-min` old must have its `_posts/{date}-{slug}.md`, where
`date` is the fire's Zurich date. No writer skips an edition on purpose (no prompt has a
publish-nothing path), so a missing post is always a fault. Why it is missing is read from
the usage ledger:

  * lost    -- the run was measured with this edition but its post is not on main: the
               evaluator's own `continuity.lost_editions` rule (metrics.build_lost_editions)
  * no-post -- a run of this routine was recorded near the slot but named no edition
  * no-run  -- nothing was recorded: the trigger did not fire, or the run died before its
               Stop hook

Output: one line per overdue edition NOT already in the state file, `<title>\t<body>`,
for the bridge to send as one ntfy push each; then the state file is updated so each
edition alerts once. Exit 0 always unless the arguments are wrong -- the bridge treats any
failure as a log line, never as a reason to stop draining notifications.

usage: freshness.py [--root DIR] [--state PATH] [--now ISO] [--grace-min 120]
                    [--lookback-h 48] [--dry-run]
"""
import argparse
import datetime as dt
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "evaluator"))
import schedule  # noqa: E402
import metrics  # noqa: E402  (build_lost_editions: the evaluator's lost-edition rule)

STATE_KEEP_DAYS = 14
NEAR_SLOT = dt.timedelta(hours=4)  # a run "belongs" to a slot when it starts within this


def _parse_ts(s):
    if not isinstance(s, str) or not s:
        return None
    try:
        t = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def _usage_runs(root, slug):
    """Start times of every usage record of routine `slug` (any stage)."""
    out = []
    for path in glob.glob(os.path.join(root, "index", "usage", "*-%s.jsonl" % slug)):
        try:
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    try:
                        rec = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(rec, dict) and rec.get("routine") == slug:
                        t = _parse_ts(rec.get("started"))
                        if t:
                            out.append(t)
        except OSError:
            continue
    return out


def overdue(root, now, grace_min=120, lookback_h=48):
    """[{key, slug, name, date, slot, reason}] for every fire in (now - lookback, now - grace]
    whose post is missing, oldest first."""
    end = now - dt.timedelta(minutes=grace_min)
    start = now - dt.timedelta(hours=lookback_h)
    found = []
    for row in schedule.load(root):
        slug = row["slug"]
        if not slug:
            continue
        for slot in schedule.fires_between(row["cron"], start, end):
            date = slot.date().isoformat()
            if os.path.exists(os.path.join(root, "_posts", "%s-%s.md" % (date, slug))):
                continue
            edition = "%s-%s" % (date, slug)
            if any(r["edition"] == edition for r in metrics.build_lost_editions(root, date, date)):
                reason = "lost"
            elif any(slot - dt.timedelta(minutes=10) <= t <= slot + NEAR_SLOT
                     for t in _usage_runs(root, slug)):
                reason = "no-post"
            else:
                reason = "no-run"
            found.append({"key": "%s|%s" % (slug, date), "slug": slug, "name": row["name"],
                          "date": date, "slot": slot.isoformat(), "reason": reason})
    found.sort(key=lambda r: r["slot"])
    return found


_WHY = {
    "lost": "The run was measured but its post never reached main (a lost edition).",
    "no-post": "A run was recorded near the slot but published no edition.",
    "no-run": "No run was recorded: the trigger did not fire, or the run died before its Stop hook.",
}


def message(item):
    slot = item["slot"][11:16]
    title = "Missing edition: %s %s" % (item["name"], item["date"])
    body = "%s was due at %s Zurich and _posts/%s-%s.md is not on main. %s" % (
        item["name"], slot, item["date"], item["slug"], _WHY[item["reason"]])
    return title, body


def load_state(path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_state(path, state, now):
    cutoff = (now - dt.timedelta(days=STATE_KEEP_DAYS)).date().isoformat()
    kept = {k: v for k, v in state.items() if k.split("|", 1)[-1] >= cutoff}
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(kept, fh, indent=1, sort_keys=True)
    os.replace(tmp, path)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(HERE)))
    ap.add_argument("--state", help="JSON file of already-alerted editions (kept by the bridge)")
    ap.add_argument("--now", help="ISO timestamp to evaluate at (default: now)")
    ap.add_argument("--grace-min", type=int, default=120)
    ap.add_argument("--lookback-h", type=int, default=48)
    ap.add_argument("--dry-run", action="store_true", help="print every overdue edition; no state")
    a = ap.parse_args(argv)
    now = _parse_ts(a.now) if a.now else dt.datetime.now(dt.timezone.utc)
    if now is None:
        ap.error("--now must be an ISO timestamp")
    now = now.astimezone(schedule.ZURICH)
    items = overdue(a.root, now, a.grace_min, a.lookback_h)
    state = {} if (a.dry_run or not a.state) else load_state(a.state)
    for item in items:
        if item["key"] in state:
            continue
        title, body = message(item)
        print("%s\t%s" % (title, body))
        state[item["key"]] = now.isoformat(timespec="seconds")
    if a.state and not a.dry_run:
        save_state(a.state, state, now)
    return 0


if __name__ == "__main__":
    sys.exit(main())
