#!/usr/bin/env python3
"""Evaluator metrics computer (SPIKE-2026-07-07-continuous-news.md §3.5,
dimensions A/C/G/I/K/L): reads the story ledger + feedback/_posts/_data trees
and writes/prints `_data/health.json`. Schema is fixed by
tools/tests/test_metrics.py -- see that file's module docstring for the exact
shape; this module implements it, it does not re-derive it.

Stdlib only. Never aborts on missing/partial input (SPIKE §4 failure-
semantics: a tool crash degrades, it never blocks the brief) -- absent
ledger/feedback/_posts/_data trees just yield empty/zero/fallback values.

CLI: metrics.py [--root PATH] [--week YYYY-MM-DD]
  --week is the window's END date (inclusive); the window is the 7 calendar
  days [end-6, end]. Defaults to today (UTC-naive local date) if omitted.
"""
import argparse
import datetime as dt
import glob
import json
import os
import re
import sys

_EDITION_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)$")
_EVALUATOR_POST_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-evaluator\.md$")
_LOOKBACK_DAYS = 14
_WINDOW_DAYS = 7


def _parse_edition(edition):
    """"YYYY-MM-DD-slug" -> (date_str, stream); (None, None) if malformed."""
    m = _EDITION_RE.match(edition or "")
    return (m.group(1), m.group(2)) if m else (None, None)


def _date_of(ts):
    """ISO8601 ts ("...Z" or naive) -> its "YYYY-MM-DD" date prefix."""
    return (ts or "")[:10]


def _parse_dt(ts):
    """ISO8601 UTC ts -> naive datetime for arithmetic (drops the offset;
    the ledger only ever uses "Z"-suffixed UTC timestamps). None on an
    empty/garbage ts -- a malformed ledger line must degrade (treated as
    non-repeat/unusable for the lookback), never crash the whole run."""
    try:
        return dt.datetime.strptime((ts or "")[:19], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return None


def compute_week(week_arg):
    end = dt.datetime.strptime(week_arg, "%Y-%m-%d").date()
    start = end - dt.timedelta(days=_WINDOW_DAYS - 1)
    return start.isoformat(), end.isoformat()


def _iter_ledger_events(root):
    """Every parseable JSON line under index/ledger/*.jsonl, file order then
    line order (deterministic); unparseable lines are skipped (store.py does
    the same -- a tool crash must degrade, not abort)."""
    ledger = os.path.join(root, "index", "ledger")
    if not os.path.isdir(ledger):
        return
    for name in sorted(os.listdir(ledger)):
        if not name.endswith(".jsonl"):
            continue
        try:
            fh = open(os.path.join(ledger, name), encoding="utf-8")
        except OSError:
            continue
        with fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except ValueError:
                    continue


def build_thread_map(events):
    """id -> thread_id, from every `seen` event's story payload across the
    WHOLE ledger (not window-restricted -- a genesis `seen` can predate the
    --week window by any amount and must still be reachable for the repeat
    proxy's lookback). Falls back to self if a `seen` never set one."""
    thread = {}
    for ev in events:
        if ev.get("ev") != "seen":
            continue
        story = ev.get("story") or {}
        sid = story.get("id")
        if not sid:
            continue
        thread.setdefault(sid, story.get("thread_id") or sid)
    return thread


def _thread_of(thread_map, sid):
    return thread_map.get(sid, sid)


def dedup_publishes(events):
    """All ledger `publish` events, deduped by (ev, id, edition) -- ts is NOT
    part of the key, so a retried append with a new ts folds to one
    occurrence. The occurrence's canonical ts is the EARLIEST of the group
    (the retry is the same real event, not a later one). Returns a list of
    {id, edition, ts, stream}."""
    groups = {}
    for ev in events:
        if ev.get("ev") != "publish":
            continue
        sid, edition = ev.get("id"), ev.get("edition")
        if not sid or not edition:
            continue
        ts = ev.get("ts") or ""
        key = (sid, edition)
        prev = groups.get(key)
        if prev is None or ts < prev["ts"]:
            groups[key] = {"id": sid, "edition": edition, "ts": ts}
    out = []
    for (sid, edition), g in groups.items():
        _, stream = _parse_edition(edition)
        out.append({"id": sid, "edition": edition, "ts": g["ts"], "stream": stream})
    return out


def compute_repeat_flags(occurrences, thread_map):
    """occurrence (id, edition) -> bool, per the contract's 14-day id/
    thread_id lookback proxy: true iff some OTHER occurrence sharing the same
    thread (same id trivially shares a thread; a different id sharing
    thread_id also counts, per contract "id OR thread_id") has an earlier ts
    within the preceding 14 days. Computed over ALL occurrences regardless of
    --week window -- the earlier occurrence may lie outside it."""
    by_thread = {}
    for occ in occurrences:
        by_thread.setdefault(_thread_of(thread_map, occ["id"]), []).append(occ)
    flags = {}
    for occs in by_thread.values():
        ordered = sorted(occs, key=lambda o: o["ts"])
        for i, occ in enumerate(ordered):
            cur = _parse_dt(occ["ts"])
            repeat = False
            if cur is not None:
                for prior in ordered[:i]:
                    prior_dt = _parse_dt(prior["ts"])
                    if prior_dt is not None and cur - prior_dt <= dt.timedelta(days=_LOOKBACK_DAYS):
                        repeat = True
                        break
            flags[(occ["id"], occ["edition"])] = repeat
    return flags


def build_streams(occurrences, window_start, window_end, thread_map):
    """Per-stream editions/citations/anchors/repeats/by_edition, restricted to
    occurrences whose ts falls in [window_start, window_end] (inclusive date
    strings -- ISO format sorts lexically). Sparse: streams with zero
    in-window occurrences are absent."""
    flags = compute_repeat_flags(occurrences, thread_map)
    acc = {}
    for occ in occurrences:
        if not (window_start <= _date_of(occ["ts"]) <= window_end):
            continue
        stream = occ["stream"]
        if not stream:
            continue
        s = acc.setdefault(stream, {"citations": 0, "anchors": set(), "repeats": 0, "by_edition": {}})
        s["citations"] += 1
        s["anchors"].add(occ["id"])
        if flags.get((occ["id"], occ["edition"])):
            s["repeats"] += 1
        be = s["by_edition"].setdefault(occ["edition"], {"citations": 0, "anchors": set()})
        be["citations"] += 1
        be["anchors"].add(occ["id"])

    streams = {}
    for stream, s in acc.items():
        by_edition = {ed: {"citations": v["citations"], "anchors": len(v["anchors"])}
                      for ed, v in s["by_edition"].items()}
        citations = s["citations"]
        streams[stream] = {
            "editions": sorted(by_edition.keys()),
            "citations": citations,
            "anchors": len(s["anchors"]),
            "repeats": s["repeats"],
            "repeat_rate": (s["repeats"] / citations) if citations else 0.0,
            "by_edition": by_edition,
        }
    return streams


def build_feedback(events, root, window_start, window_end):
    """unconsumed_total (unfiltered, from feedback/*.jsonl), notify_count and
    by_stream (both windowed, from ledger events)."""
    by_stream = {}
    notify_count = 0
    for ev in events:
        ts_date = _date_of(ev.get("ts"))
        in_window = window_start <= ts_date <= window_end
        if ev.get("ev") == "notify" and in_window:
            notify_count += 1
        elif ev.get("ev") == "feedback" and in_window:
            _, stream = _parse_edition(ev.get("brief"))
            if not stream:
                continue
            tally = by_stream.setdefault(stream, {"up": 0, "down": 0, "retractions": 0})
            vote = ev.get("vote")
            if vote == 1:
                tally["up"] += 1
            elif vote == -1:
                tally["down"] += 1
            elif vote == 0:
                tally["retractions"] += 1

    unconsumed_total = 0
    for path in sorted(glob.glob(os.path.join(root, "feedback", "*.jsonl"))):
        try:
            fh = open(path, encoding="utf-8")
        except OSError:
            continue
        with fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if not rec.get("consumed", False):
                    unconsumed_total += 1

    return {"unconsumed_total": unconsumed_total, "notify_count": notify_count, "by_stream": by_stream}


def build_sources(root):
    """Verbatim passthrough of _data/source-health.json; a fixed fallback
    marker if absent/unreadable -- never crashes (SPIKE §4)."""
    path = os.path.join(root, "_data", "source-health.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"available": False, "reason": "source-health.json not found"}


def build_continuity(root, week_end):
    """Most recent `_posts/*-evaluator.md` dated strictly before week.end
    (POSIX-relative path), deliberately "most recent prior post" rather than
    an exact 7-day-ago lookup (SPIKE §2: 2 of 9 continuity failures traced to
    that brittle heuristic)."""
    best = None
    for path in glob.glob(os.path.join(root, "_posts", "*-evaluator.md")):
        m = _EVALUATOR_POST_RE.match(os.path.basename(path))
        if not m or m.group(1) >= week_end:
            continue
        if best is None or m.group(1) > best[0]:
            best = (m.group(1), os.path.basename(path))
    if best is None:
        return {"previous_evaluator_found": False, "previous_evaluator_path": None}
    return {"previous_evaluator_found": True, "previous_evaluator_path": "_posts/" + best[1]}


def compute_health(root, week_arg):
    window_start, window_end = compute_week(week_arg)
    events = list(_iter_ledger_events(root))
    thread_map = build_thread_map(events)
    occurrences = dedup_publishes(events)
    return {
        "week": {"start": window_start, "end": window_end},
        "streams": build_streams(occurrences, window_start, window_end, thread_map),
        "feedback": build_feedback(events, root, window_start, window_end),
        "sources": build_sources(root),
        "continuity": build_continuity(root, window_end),
    }


def main(argv=None):
    p = argparse.ArgumentParser(prog="metrics.py", description=__doc__.splitlines()[0])
    p.add_argument("--root", default=os.getcwd())
    p.add_argument("--week", default=None, help="window end date, YYYY-MM-DD (default: today)")
    args = p.parse_args(argv)

    week_arg = args.week or dt.date.today().isoformat()
    health = compute_health(args.root, week_arg)

    out_dir = os.path.join(args.root, "_data")
    os.makedirs(out_dir, exist_ok=True)
    text = json.dumps(health, indent=2, sort_keys=True, ensure_ascii=False)
    with open(os.path.join(out_dir, "health.json"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
