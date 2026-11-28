#!/usr/bin/env python3
"""The routine schedule, parsed from the table in routines/MANIFEST.md.

That table is the repo's one copy of the live trigger crons (the triggers themselves are
reachable only through RemoteTrigger, from the main session). Everything that needs a
schedule reads it here: tools/health/freshness.py (overdue editions) and the docs-consistency
test, which holds ARCHITECTURE.md and diagrams/ to the same models and crons.

Crons are stored as `CRON_TZ=Europe/Zurich`, so every time here is Zurich wall-clock time.
Only the standard five-field syntax is supported: `*`, lists, ranges and `/step`.
"""
import datetime as dt
import os
import re

try:
    from zoneinfo import ZoneInfo
    ZURICH = ZoneInfo("Europe/Zurich")
except Exception:  # pragma: no cover -- every supported Python has zoneinfo + system tzdata
    ZURICH = None

# | News | `news.md` | `trig_…` | `0 12 * * *` (12:00 Zurich, …) | `claude-opus-5-5` | yes |
_ROW_RE = re.compile(
    r"^\|\s*(?P<name>[^|`]+?)\s*\|\s*`(?P<file>[a-z-]+)\.md`\s*\|\s*`(?P<trigger>trig_\w+)`\s*\|"
    r"\s*`(?P<cron>[^`]+)`[^|]*\|\s*`(?P<model>claude-[a-z0-9-]+)`[^|]*\|\s*(?P<shim>[^|]+?)\s*\|\s*$")

# prompt-file stem -> the slug its posts carry in `_posts/{date}-{slug}.md`; None = no posts.
_SLUG = {"weekly-evaluator": "evaluator", "watch": None}

_FIELDS = (("minute", 0, 59), ("hour", 0, 23), ("dom", 1, 31), ("month", 1, 12), ("dow", 0, 7))


def _expand(field, lo, hi):
    """One cron field -> the sorted set of values it allows. Raises ValueError on bad syntax."""
    out = set()
    for part in field.split(","):
        step = 1
        if "/" in part:
            part, s = part.split("/", 1)
            step = int(s)
            if step < 1:
                raise ValueError("cron step must be >= 1: %r" % field)
        if part == "*":
            a, b = lo, hi
        elif "-" in part:
            a, b = (int(x) for x in part.split("-", 1))
        else:
            a = b = int(part)
            if step != 1:  # `5/15` means 5,20,35,50
                b = hi
        if not (lo <= a <= b <= hi):
            raise ValueError("cron value out of range: %r" % field)
        out.update(range(a, b + 1, step))
    return out


def parse_cron(expr):
    """`27 2-22/4 * * *` -> {minute: {27}, hour: {2, 6, …}, dom, month, dow, restricted: …}.

    A leading `CRON_TZ=…` is dropped. dow 7 folds into 0 (Sunday). `restricted` records which
    of dom/dow were not `*`, for cron's OR rule when both are restricted."""
    parts = expr.split()
    if parts and parts[0].startswith("CRON_TZ="):
        parts = parts[1:]
    if len(parts) != 5:
        raise ValueError("expected five cron fields: %r" % expr)
    spec = {}
    for (name, lo, hi), field in zip(_FIELDS, parts):
        spec[name] = _expand(field, lo, hi)
    if 7 in spec["dow"]:
        spec["dow"] = (spec["dow"] - {7}) | {0}
    spec["restricted"] = {"dom": parts[2] != "*", "dow": parts[4] != "*"}
    return spec


def same_schedule(a, b):
    """True when two cron expressions fire at exactly the same times."""
    pa, pb = parse_cron(a), parse_cron(b)
    return all(pa[k] == pb[k] for k in ("minute", "hour", "dom", "month", "dow"))


def load(root):
    """MANIFEST table rows -> [{name, file, slug, trigger_id, cron, model, shim}] in table order.

    `slug` is None for a routine that writes no post (Watch). Raises ValueError when the table
    has no rows, so a reformatted MANIFEST fails loudly instead of reading as "no schedule"."""
    path = os.path.join(root, "routines", "MANIFEST.md")
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = _ROW_RE.match(line.rstrip("\n"))
            if not m:
                continue
            stem = m.group("file")
            parse_cron(m.group("cron"))  # validate now, not at first use
            rows.append({
                "name": m.group("name"),
                "file": stem + ".md",
                "slug": _SLUG.get(stem, stem),
                "trigger_id": m.group("trigger"),
                "cron": m.group("cron"),
                "model": m.group("model"),
                "shim": m.group("shim").split()[0].lower(),
            })
    if not rows:
        raise ValueError("no routine rows found in %s" % path)
    return rows


def _matches_day(spec, day):
    dow = (day.weekday() + 1) % 7  # Python Monday=0 -> cron Sunday=0
    dom_ok = day.day in spec["dom"]
    dow_ok = dow in spec["dow"]
    if spec["restricted"]["dom"] and spec["restricted"]["dow"]:
        return day.month in spec["month"] and (dom_ok or dow_ok)
    return day.month in spec["month"] and dom_ok and dow_ok


def fires_between(cron, start, end, tz=None):
    """Every fire time t with start < t <= end, as aware datetimes in `tz` (default Zurich),
    oldest first. `start` / `end` are aware datetimes."""
    tz = tz or ZURICH
    spec = parse_cron(cron)
    out = []
    day = start.astimezone(tz).date()
    last = end.astimezone(tz).date()
    while day <= last:
        if _matches_day(spec, day):
            for h in sorted(spec["hour"]):
                for mi in sorted(spec["minute"]):
                    t = dt.datetime(day.year, day.month, day.day, h, mi, tzinfo=tz)
                    if start < t <= end:
                        out.append(t)
        day += dt.timedelta(days=1)
    return out
