#!/usr/bin/env python3
"""Fold the append-only usage ledger into a single summary the admin page reads.

Reads every index/usage/*.jsonl, keeps ONE record per session_id -- a run may be recorded
twice (a publish-time record and a Stop-hook record for the same session), so the most
complete stage wins: session-end > stop > publish, ties broken by the later recorded_at.
The kept runs are then rolled up by routine, by day, into rolling 7/30-day windows, and a
newest-first `recent` list.

`cache_write` throughout is 5m + 1h writes summed; `cost_usd_list` is list-price dollars
(tools/usage/pricing.py). Pass `as_of` (a date) explicitly to keep the windows deterministic;
it defaults to today only for interactive use.
"""
import argparse
import datetime as dt
import glob
import json
import os


_STAGE_RANK = {"session-end": 3, "stop": 2, "publish": 1}


def _iter_records(root):
    for path in sorted(glob.glob(os.path.join(root, "index", "usage", "*.jsonl"))):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


def _more_complete(a, b):
    """Return whichever of two records for the same session should be kept."""
    ra = _STAGE_RANK.get(a.get("stage"), 0)
    rb = _STAGE_RANK.get(b.get("stage"), 0)
    if ra != rb:
        return a if ra > rb else b
    return a if (a.get("recorded_at") or "") >= (b.get("recorded_at") or "") else b


def _tokens(record):
    t = record.get("totals") or {}
    return {
        "input": t.get("input", 0) or 0,
        "cache_write": (t.get("cache_write_5m", 0) or 0) + (t.get("cache_write_1h", 0) or 0),
        "cache_read": t.get("cache_read", 0) or 0,
        "output": t.get("output", 0) or 0,
    }


def _add_tokens(acc, tok):
    for k in ("input", "cache_write", "cache_read", "output"):
        acc[k] = acc.get(k, 0) + tok[k]


def _zero_tokens():
    return {"input": 0, "cache_write": 0, "cache_read": 0, "output": 0}


def _total_tokens(tok):
    return tok["input"] + tok["cache_write"] + tok["cache_read"] + tok["output"]


def _cost(record):
    return (record.get("cost_usd_list") or {}).get("total", 0.0) or 0.0


def _day(record):
    return (record.get("started") or "")[:10] or None


def _as_of_date(as_of):
    if as_of is None:
        return dt.date.today()
    if isinstance(as_of, dt.date):
        return as_of
    return dt.date.fromisoformat(str(as_of)[:10])


def fold(root, as_of=None):
    """Fold the ledger under `root` into the summary dict (schema in §1.6 of the plan)."""
    as_of_date = _as_of_date(as_of)

    kept = {}
    records = 0
    for rec in _iter_records(root):
        records += 1
        sid = rec.get("session_id")
        if sid is None:
            # keep an id-less record under a unique key so it still counts as a run
            sid = "_anon_%d" % records
        prev = kept.get(sid)
        kept[sid] = rec if prev is None else _more_complete(prev, rec)

    runs = list(kept.values())
    runs.sort(key=lambda r: (r.get("started") or "", r.get("recorded_at") or ""))

    by_routine = {}
    by_day = {}
    windows = {"7d": {"runs": 0, "tokens": _zero_tokens(), "cost_usd_list": 0.0},
               "30d": {"runs": 0, "tokens": _zero_tokens(), "cost_usd_list": 0.0}}
    since = None

    for rec in runs:
        routine = rec.get("routine") or "unknown"
        tok = _tokens(rec)
        cost = _cost(rec)
        day = _day(rec)
        if day and (since is None or day < since):
            since = day

        slot = by_routine.get(routine)
        if slot is None:
            slot = {"runs": 0, "tokens": _zero_tokens(), "cost_usd_list": 0.0,
                    "_duration_s": 0, "_messages": 0}
            by_routine[routine] = slot
        slot["runs"] += 1
        _add_tokens(slot["tokens"], tok)
        slot["cost_usd_list"] += cost
        slot["_duration_s"] += rec.get("duration_s") or 0
        slot["_messages"] += rec.get("messages") or 0

        if day:
            d = by_day.get(day)
            if d is None:
                d = {"date": day, "runs": 0, "tokens": _zero_tokens(), "cost_usd_list": 0.0}
                by_day[day] = d
            d["runs"] += 1
            _add_tokens(d["tokens"], tok)
            d["cost_usd_list"] += cost

            try:
                age = (as_of_date - dt.date.fromisoformat(day)).days
            except ValueError:
                age = None
            if age is not None and 0 <= age < 7:
                windows["7d"]["runs"] += 1
                _add_tokens(windows["7d"]["tokens"], tok)
                windows["7d"]["cost_usd_list"] += cost
            if age is not None and 0 <= age < 30:
                windows["30d"]["runs"] += 1
                _add_tokens(windows["30d"]["tokens"], tok)
                windows["30d"]["cost_usd_list"] += cost

    # finalise per-routine averages
    for slot in by_routine.values():
        n = slot["runs"] or 1
        total_tok = _total_tokens(slot["tokens"])
        slot["avg"] = {
            "tokens_per_run": round(total_tok / n),
            "cost_per_run": round(slot["cost_usd_list"] / n, 6),
            "duration_s": round(slot.pop("_duration_s") / n),
            "messages": round(slot.pop("_messages") / n),
        }
        slot["cost_usd_list"] = round(slot["cost_usd_list"], 6)

    for w in windows.values():
        w["cost_usd_list"] = round(w["cost_usd_list"], 6)

    recent = []
    for rec in reversed(runs):  # newest first
        recent.append({
            "session_id": rec.get("session_id"),
            "stage": rec.get("stage"),
            "routine": rec.get("routine"),
            "edition": rec.get("edition"),
            "started": rec.get("started"),
            "duration_s": rec.get("duration_s"),
            "messages": rec.get("messages"),
            "models": sorted((rec.get("models") or {}).keys()),
            "tokens": _tokens(rec),
            "cost_usd_list": round(_cost(rec), 6),
        })
        if len(recent) >= 100:
            break

    by_day_list = [by_day[k] for k in sorted(by_day)]
    for d in by_day_list:
        d["cost_usd_list"] = round(d["cost_usd_list"], 6)

    return {
        "generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "records": records,
        "runs": len(runs),
        "since": since,
        "by_routine": by_routine,
        "by_day": by_day_list,
        "windows": windows,
        "recent": recent,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--root", default=".")
    p.add_argument("--as-of", default=None, help="window anchor date YYYY-MM-DD (default: today)")
    p.add_argument("--json", action="store_true", help="print the fold as JSON")
    p.add_argument("--out", default=None, help="write the fold JSON to this path")
    args = p.parse_args(argv)
    result = fold(args.root, as_of=args.as_of)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print("wrote %s (%d runs)" % (args.out, result["runs"]))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
