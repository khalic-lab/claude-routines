#!/usr/bin/env python3
"""Evaluator metrics computer (SPIKE-2026-07-07-continuous-news.md §3.5):
reads the story ledger + feedback/_posts/_data trees and writes/prints
`_data/health.json`. Since 2026-07-18 it also computes the brief-text
dimensions the evaluator used to hand-count (B aggregator leakage, D section
vitality, F single-source rate, G tag counts, H weekend paper balance, K
footer fetch ratios + feeds, L word-count means) under the top-level "briefs"
key, plus the off-main self-delivery guard under continuity.off_main. Schema
is fixed by tools/tests/test_metrics.py -- see that file's module docstring
for the exact shape; this module implements it, it does not re-derive it.

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
import subprocess
import sys

_EDITION_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)$")
_EVALUATOR_POST_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-evaluator\.md$")
_LOOKBACK_DAYS = 14
_WINDOW_DAYS = 7

# --- brief-text dimensions (B/D/F/G/H/K/L), computed so the evaluator reads
# --- instead of recounting (same principle as A/I since 2026-07-07) ----------
_WRITER_SLUGS = ("news", "ai-ml", "science", "weekend", "sports")
_AGGREGATORS = ("news.ycombinator.com", "lobste.rs", "reddit.com", "twitter.com",
                "x.com", "mastodon.social", "threads.net", "bsky.app")
_TRACKED_TAGS = ("single-source", "preprint", "vendor PR", "official PR",
                 "disputed", "rumour", "unconfirmed", "new source", "via snippet")
_POST_NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z0-9-]+)\.md$")
_BULLET_RE = re.compile(r"^-\s+(?:<a\b[^>]*></a>\s*)?\*\*")
_HEADING_CITE_RE = re.compile(r"^\*\*\[")
_LINK_RE = re.compile(r"\]\((https?://[^)\s]+)")
_SECTION_RE = re.compile(r"^##\s+(.*)$")
_FOOTER_HEADING = "## Coverage footer"
_WORDS_RE = re.compile(r"^- Word count:\s*~?([\d,]+)", re.M)
_CALLS_RE = re.compile(r"tool calls[^:]*:\s*~?(\d+)")
_DIRECT_RE = re.compile(r"Direct fetches:\s*~?(\d+)\s*\|\s*via-snippet citations:\s*~?(\d+)")
_FEEDS_LINE_RE = re.compile(r"^- Feeds hit[^:]*:\s*(.*)$", re.M)
_FEED_OK_RE = re.compile(r"(?:(\d+)\s+)?ok via (curl|proxy|WebFetch|MCP)", re.I)
_FEED_FAIL_RE = re.compile(r"(?:(\d+)\s+)?fail", re.I)


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


def _split_footer(text):
    i = text.find("\n" + _FOOTER_HEADING)
    if i < 0:
        return text, ""
    return text[:i], text[i + 1:]


def _window_posts(root, start, end):
    """[(date, slug, text)] for writer posts whose filename date is in [start, end]."""
    out = []
    for path in sorted(glob.glob(os.path.join(root, "_posts", "*.md"))):
        m = _POST_NAME_RE.match(os.path.basename(path))
        if not m or m.group(2) not in _WRITER_SLUGS:
            continue
        date, slug = m.group(1), m.group(2)
        if not (start <= date <= end):
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                out.append((date, slug, fh.read()))
        except OSError:
            continue
    return out


def _sections(body):
    """[(name, item_count)] per `## ` section (citation bullets + heading-register items)."""
    sections = []
    for line in body.split("\n"):
        m = _SECTION_RE.match(line)
        if m:
            sections.append([m.group(1).strip(), 0])
        elif sections and (_BULLET_RE.match(line) or _HEADING_CITE_RE.match(line)
                           or line.startswith("### ")):
            sections[-1][1] += 1
    return [(name, count) for name, count in sections]


def _parse_feeds(footer, feeds_acc):
    """Aggregate `Feeds hit` segments into feeds_acc[label] += ok/fail counts.
    Handles both the legacy hand-written `{ok via curl}` markers and footer.py's
    computed `{2 ok via curl, 1 fail HTTP 403}` form with the same regexes."""
    for m in _FEEDS_LINE_RE.finditer(footer):
        for segment in m.group(1).split(";"):
            segment = segment.strip()
            if not segment:
                continue
            label = segment.split("{")[0].strip(" -—:") or "unlabelled"
            acc = feeds_acc.setdefault(label, {"ok_curl": 0, "ok_proxy": 0,
                                               "ok_webfetch": 0, "ok_mcp": 0, "fail": 0})
            for ok in _FEED_OK_RE.finditer(segment):
                n = int(ok.group(1) or 1)
                acc["ok_%s" % ok.group(2).lower()] += n
            for fail in _FEED_FAIL_RE.finditer(segment):
                acc["fail"] += int(fail.group(1) or 1)


def _mean(values):
    return round(sum(values) / len(values)) if values else None


def build_briefs(root, window_start, window_end):
    """Dimensions the evaluator used to hand-count from the week's briefs:
    aggregator leakage (B), section vitality (D), single-source rate (F), tag
    counts (G), weekend paper balance (H), footer fetch ratios + feeds (K),
    word-count means incl. previous week (L). Pure parsing -- the evaluator's
    job on these numbers is judgment, not arithmetic."""
    posts = _window_posts(root, window_start, window_end)
    prev_start = (dt.date.fromisoformat(window_start) - dt.timedelta(days=_WINDOW_DAYS)).isoformat()
    prev_end = (dt.date.fromisoformat(window_start) - dt.timedelta(days=1)).isoformat()
    prev_words = {}
    for _, slug, text in _window_posts(root, prev_start, prev_end):
        wm = _WORDS_RE.search(text)
        if wm:
            prev_words.setdefault(slug, []).append(int(wm.group(1).replace(",", "")))

    leakage, feeds = [], {}
    by_stream = {}
    weekend_ml, weekend_sci = 0, 0
    weekend_seen = False

    for date, slug, text in posts:
        body, footer = _split_footer(text)
        post_name = "%s-%s.md" % (date, slug)
        s = by_stream.setdefault(slug, {
            "posts": 0, "citations": 0, "single_source": 0,
            "tags": {t: 0 for t in _TRACKED_TAGS},
            "sections": 0, "empty_sections": [],
            "direct_fetches": 0, "via_snippet": 0,
            "_words": [], "_calls": []})
        s["posts"] += 1

        for url in _LINK_RE.findall(body):
            host = url.split("/")[2].lower() if url.count("/") >= 2 else ""
            host = host[4:] if host.startswith("www.") else host
            if any(host == a or host.endswith("." + a) for a in _AGGREGATORS):
                leakage.append({"post": post_name, "url": url})

        citations = sum(1 for line in body.split("\n")
                        if (_BULLET_RE.match(line) or _HEADING_CITE_RE.match(line))
                        and _LINK_RE.search(line))
        s["citations"] += citations
        for tag in _TRACKED_TAGS:
            s["tags"][tag] += body.count("[%s]" % tag)
        s["single_source"] += body.count("[single-source]")

        for name, items in _sections(body):
            s["sections"] += 1
            if items == 0:
                s["empty_sections"].append({"post": post_name, "section": name})
            if slug == "weekend" and re.search(r"papers?", name, re.I):
                weekend_seen = True
                if re.search(r"\b(ML|AI)\b", name):
                    weekend_ml += items
                else:
                    weekend_sci += items

        dm = _DIRECT_RE.search(footer)
        if dm:
            s["direct_fetches"] += int(dm.group(1))
            s["via_snippet"] += int(dm.group(2))
        wm = _WORDS_RE.search(text)
        if wm:
            s["_words"].append(int(wm.group(1).replace(",", "")))
            cm = _CALLS_RE.search(text[wm.start():wm.start() + 200])
            if cm:
                s["_calls"].append(int(cm.group(1)))
        _parse_feeds(footer, feeds)

    for slug, s in by_stream.items():
        fetches = s["direct_fetches"] + s["via_snippet"]
        s["direct_fetch_ratio"] = round(s["direct_fetches"] / fetches, 3) if fetches else None
        s["single_source_rate"] = (round(s["single_source"] / s["citations"], 3)
                                   if s["citations"] else 0.0)
        s["tags"] = {t: n for t, n in s["tags"].items() if n}
        s["words_mean"] = _mean(s.pop("_words"))
        s["calls_mean"] = _mean(s.pop("_calls"))
        s["words_mean_prev_week"] = _mean(prev_words.get(slug, []))

    if weekend_seen and (weekend_ml + weekend_sci):
        balance = {"ml_items": weekend_ml, "science_items": weekend_sci,
                   "ml_share": round(weekend_ml / (weekend_ml + weekend_sci), 3)}
    else:
        balance = {"available": False}

    return {"aggregator_leakage": leakage, "by_stream": by_stream,
            "feeds": feeds, "weekend_balance": balance}


def _git_lines(root, argv):
    proc = subprocess.run(["git"] + argv, cwd=root, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip())
    return [l for l in (proc.stdout or "").splitlines() if l.strip()]


def build_off_main(root, window_start):
    """Self-delivery guard, computed: remote branches besides origin/main + recent
    commits not reachable from main (the `outcomes`-stranding class). Only runs
    when root itself is a git repo -- fixture trees degrade to available:false."""
    if not os.path.isdir(os.path.join(root, ".git")):
        return {"available": False}
    try:
        branches = [b.strip() for b in _git_lines(root, ["branch", "-r", "--format=%(refname:short)"])
                    if b.strip() not in ("", "origin", "origin/main") and "HEAD" not in b]
        commits = _git_lines(root, ["log", "--all", "--oneline",
                                    "--since=%s" % window_start, "--not", "main"])
        return {"available": True, "remote_branches": branches,
                "commits_not_on_main": commits[:20]}
    except (OSError, RuntimeError):
        return {"available": False}


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
    continuity = build_continuity(root, window_end)
    continuity["off_main"] = build_off_main(root, window_start)
    return {
        "week": {"start": window_start, "end": window_end},
        "streams": build_streams(occurrences, window_start, window_end, thread_map),
        "feedback": build_feedback(events, root, window_start, window_end),
        "sources": build_sources(root),
        "continuity": continuity,
        "briefs": build_briefs(root, window_start, window_end),
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
