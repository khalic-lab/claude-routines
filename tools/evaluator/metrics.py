#!/usr/bin/env python3
"""Evaluator metrics computer (SPIKE-2026-07-07-continuous-news.md §3.5):
reads the story ledger + feedback/_posts/_data trees and writes/prints
`_data/health.json`. Since 2026-07-18 it also computes the brief-text
dimensions the evaluator used to hand-count (B aggregator leakage, D section
vitality, F single-source rate, G tag counts, H weekend paper balance, K
footer fetch ratios + feeds, L word-count means) under the top-level "briefs"
key, plus the off-main self-delivery guard under continuity.off_main. Since
2026-10-01 also briefs.reach_drift: registry `reach: direct` domains the
writers' fetch log reached only through the proxy. Schema
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
# A `## ` section counts as empty only if it carries no items AND less than this
# many non-whitespace body chars (rm-4, 2026-07-19/26/08-02): anchor-free
# synthesis prose ("Cross-cutting threads", "Why it matters") is not emptiness.
# Tuned against the real false positives: the thinnest anchor-free prose section
# in July/August is science 2026-07-29 "Why it matters" at 362 chars (next 469,
# weekend threads run 2.4k-5.3k), so 200 clears every one with ~1.8x margin and
# still flags a one-line stub (~20-30 chars).
_MIN_SECTION_CHARS = 200

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
_TIERS_RE = re.compile(r"^- Sources used: T1 = (\d+), T2 = (\d+), untiered = (\d+)", re.M)
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
            repeat = False   # False, or the earlier occurrence's stream ("?" when unknown)
            if cur is not None:
                for prior in ordered[:i]:
                    prior_dt = _parse_dt(prior["ts"])
                    if prior_dt is not None and cur - prior_dt <= dt.timedelta(days=_LOOKBACK_DAYS):
                        repeat = prior.get("stream") or "?"
                        if repeat == occ.get("stream"):
                            break   # a same-stream prior is the finding; stop looking
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
        s = acc.setdefault(stream, {"citations": 0, "anchors": set(), "repeats": 0,
                                    "repeats_same_stream": 0, "by_edition": {}})
        s["citations"] += 1
        s["anchors"].add(occ["id"])
        prior = flags.get((occ["id"], occ["edition"]))
        if prior:
            s["repeats"] += 1
            if prior == stream:
                s["repeats_same_stream"] += 1
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
            # split of `repeats`: an earlier telling in THIS stream (a re-run) vs in another
            # stream (for the Weekend, a revisit of a daily -- allowed within its budget)
            "repeats_same_stream": s["repeats_same_stream"],
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


_FEEDBACK_CARRY_DAYS = 120


def _feedback_dispositions(root):
    """{fb_id: disposition} from every proposals/reader-model-*.json `dispositions` list
    (file = date order, later files win)."""
    out = {}
    for path in sorted(glob.glob(os.path.join(root, "proposals", "reader-model-*.json"))):
        try:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError):
            continue
        rows = doc.get("dispositions") if isinstance(doc, dict) else None
        for row in rows or []:
            if isinstance(row, dict) and row.get("fb_id"):
                out[row["fb_id"]] = str(row.get("disposition") or "").lower()
    return out


def build_reasoned(events, root, window_start, window_end):
    """Every reasoned ev:"feedback" event the review still owes a disposition, oldest first:
    dated within _FEEDBACK_CARRY_DAYS of window_end (not after it) and not dispositioned
    `applied`/`rejected` in a reader-model file. Keyed on fb_id, not the window: a vote cast on
    a Sunday AFTER that review ran sat in no 7-day window (20 votes, 4 reasoned, 07-19..10-18),
    and a deferred signal must stay visible so a second one on the same theme or source can
    combine with it. carried = dated before window_start."""
    disp = _feedback_dispositions(root)
    floor = (dt.date.fromisoformat(window_end)
             - dt.timedelta(days=_FEEDBACK_CARRY_DAYS)).isoformat()
    latest = {}
    for ev in events:
        if ev.get("ev") != "feedback" or not ev.get("fb_id"):
            continue
        latest[ev["fb_id"]] = ev  # a re-folded event (same fb_id) keeps its newest form
    out = []
    for ev in latest.values():
        if not str(ev.get("reason") or "").strip():
            continue
        day = _date_of(ev.get("ts"))
        if not day or day < floor or day > window_end:
            continue
        prior = disp.get(ev.get("fb_id"))
        if prior in ("applied", "rejected"):
            continue
        out.append({"fb_id": ev.get("fb_id"), "ts": ev.get("ts"), "story_id": ev.get("id"),
                    "brief": ev.get("brief"), "vote": ev.get("vote"),
                    "reason": ev.get("reason"), "carried": day < window_start,
                    "prior": prior})
    out.sort(key=lambda r: r["ts"] or "")
    return out


def refresh_source_health(root):
    """Run sources/health.py so `_data/source-health.json` is this run's, not last week's.

    It used to be a second command in the evaluator's prompt, with a stated ordering rule
    ("health.py must run before metrics.py") -- an invariant a script can just hold. Failure
    is non-fatal: build_sources already degrades to the not-found marker, and a stale-but-
    present file still beats aborting the review."""
    tool = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sources", "health.py")
    try:
        proc = subprocess.run([sys.executable, os.path.normpath(tool), "--root", root],
                              cwd=root, capture_output=True, text=True)
    except OSError as exc:
        print("source-health refresh failed (%s) -- folding what is on disk" % exc,
              file=sys.stderr)
        return False
    if proc.returncode != 0:
        print("source-health refresh exited %d -- folding what is on disk\n%s"
              % (proc.returncode, (proc.stderr or "").strip()), file=sys.stderr)
        return False
    return True


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
    """[(name, item_count, text_len)] per `## ` section (citation bullets +
    heading-register items; text_len = non-whitespace chars of everything
    between the heading and the next `## `, excluding the heading itself).
    Sections run to the next `## ` only -- post bodies carry no `# ` (the
    title lives in front matter), so that is the same-or-higher-level
    boundary in practice."""
    sections = []
    after_h3 = False   # a `### ` entry's own `**[cite](url)**` line is part of that entry
    for line in body.split("\n"):
        m = _SECTION_RE.match(line)
        if m:
            sections.append([m.group(1).strip(), 0, 0])
            after_h3 = False
        elif sections:
            if line.startswith("### "):
                sections[-1][1] += 1
                after_h3 = True
            elif _HEADING_CITE_RE.match(line) and after_h3:
                after_h3 = False
            elif _BULLET_RE.match(line) or _HEADING_CITE_RE.match(line):
                sections[-1][1] += 1
                after_h3 = False
            elif line.strip():
                after_h3 = False
            sections[-1][2] += len("".join(line.split()))
    return [(name, count, text_len) for name, count, text_len in sections]


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


_SID_RE = re.compile(r'(?:\{#|<a id=")(st-[0-9a-f]{12})')
_RECAP_UNFETCHED_RE = re.compile(r"Recap links not fetched this run: (\d+)")


def _story_blocks(body):
    """sid -> (section, text) for every `### ... {#st-...}` entry and `- <a id="st-...">` bullet."""
    out, section, cur, buf = {}, None, None, []
    for line in body.split("\n"):
        m = _SECTION_RE.match(line)
        if m:
            if cur:
                out[cur] = (section, "\n".join(buf))
            section, cur, buf = m.group(1).strip(), None, []
            continue
        sm = _SID_RE.search(line)
        if sm and (line.startswith("### ") or line.startswith("- ")):
            if cur:
                out[cur] = (section, "\n".join(buf))
            cur, buf = sm.group(1), [line]
        elif cur:
            buf.append(line)
    if cur:
        out[cur] = (section, "\n".join(buf))
    return out


def _shingles(text, n=5):
    w = re.findall(r"[a-z0-9']+", text.lower())
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def build_weekend_revisits(posts):
    """Per Weekend section: `entries`, `revisits` (entries whose story id a News / AI/ML /
    Science post of the same span already ran) and `containment_mean` -- the share of a
    revisit's 5-word sequences that appear verbatim in the daily's text (0..1). A reworded
    re-summary scores high; an entry written from the source scores low."""
    daily = {}
    for _, slug, text in posts:
        if slug in ("news", "ai-ml", "science"):
            for sid, (_, block) in _story_blocks(_split_footer(text)[0]).items():
                daily[sid] = block
    out = {}
    for date, slug, text in posts:
        if slug != "weekend":
            continue
        for sid, (section, block) in _story_blocks(_split_footer(text)[0]).items():
            s = out.setdefault(section or "?", {"entries": 0, "revisits": 0, "_c": []})
            s["entries"] += 1
            if sid in daily:
                s["revisits"] += 1
                sh = _shingles(block)
                s["_c"].append(len(sh & _shingles(daily[sid])) / max(1, len(sh)))
    for s in out.values():
        c = s.pop("_c")
        s["containment_mean"] = round(sum(c) / len(c), 2) if c else None
    return out


def build_feeds_walled(feeds):
    """Feeds the curl -> proxy chain cannot reach: failures beyond one rescued curl miss per
    proxy success outnumber all successes. The raw >50%-fail ratio is not a finding, because
    every proxy-only host fails curl once per success (29-47 feeds tripped it each week)."""
    out = []
    for label, c in feeds.items():
        ok = c.get("ok_curl", 0) + c.get("ok_proxy", 0) + c.get("ok_webfetch", 0) + c.get("ok_mcp", 0)
        fail = c.get("fail", 0)
        if fail - c.get("ok_proxy", 0) > ok:
            out.append({"feed": label, "ok": ok, "fail": fail})
    out.sort(key=lambda r: (-r["fail"], r["feed"]))
    return out


_LINT_ITEM_CAP = 80


def _lint_post(acc, reg, post_name, slug, date, text):
    """Replay tools/sources/lint.py's checks over one window post, in process and read-only
    (novelty is judged as of the post's own date). The publish-time lint never fails a publish,
    so its violations -- a false `met` discovery claim, an outlet-cap breach -- went unseen."""
    if reg is None:
        return
    try:
        lint = _load_lint()
        violations = lint.compute_violations(text, lint.extract_citations(text), reg, slug, date)
    except Exception:  # noqa: BLE001 -- a lint replay must never break the health build
        return
    for category, message in violations:
        acc["by_category"][category] = acc["by_category"].get(category, 0) + 1
        per = acc["by_stream"].setdefault(slug, {})
        per[category] = per.get(category, 0) + 1
        if len(acc["items"]) < _LINT_ITEM_CAP:
            acc["items"].append({"post": post_name, "category": category, "message": message})


_LINT_MOD = []


def _load_lint():
    if not _LINT_MOD:
        import importlib.util
        sources = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "..", "sources"))
        if sources not in sys.path:
            sys.path.insert(0, sources)  # lint.py does a plain `import registry`
        tool = os.path.join(sources, "lint.py")
        spec = importlib.util.spec_from_file_location("_lint_m", tool)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _LINT_MOD.append(mod)
    return _LINT_MOD[0]


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
    reg_for_lint = _load_registry(root)
    lint_acc = {"by_category": {}, "by_stream": {}, "items": []}
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
            "_words": [], "_calls": [], "_tiers": [0, 0, 0]})
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

        for name, items, text_len in _sections(body):
            s["sections"] += 1
            if items == 0 and text_len < _MIN_SECTION_CHARS:
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
        tm = _TIERS_RE.search(footer)
        if tm:
            for k in range(3):
                s["_tiers"][k] += int(tm.group(k + 1))
        _lint_post(lint_acc, reg_for_lint, post_name, slug, date, text)
        _parse_feeds(footer, feeds)
        rm = _RECAP_UNFETCHED_RE.search(footer)
        if rm:
            s["recap_unfetched"] = s.get("recap_unfetched", 0) + int(rm.group(1))

    for slug, s in by_stream.items():
        fetches = s["direct_fetches"] + s["via_snippet"]
        s["direct_fetch_ratio"] = round(s["direct_fetches"] / fetches, 3) if fetches else None
        s["single_source_rate"] = (round(s["single_source"] / s["citations"], 3)
                                   if s["citations"] else 0.0)
        s["tags"] = {t: n for t, n in s["tags"].items() if n}
        s["words_mean"] = _mean(s.pop("_words"))
        s["calls_mean"] = _mean(s.pop("_calls"))
        s["words_mean_prev_week"] = _mean(prev_words.get(slug, []))
        t1, t2, untiered = s.pop("_tiers")
        s["tiers"] = {"T1": t1, "T2": t2, "untiered": untiered}
        s["t1_share"] = round(t1 / (t1 + t2 + untiered), 3) if (t1 + t2 + untiered) else None

    if weekend_seen and (weekend_ml + weekend_sci):
        balance = {"ml_items": weekend_ml, "science_items": weekend_sci,
                   "ml_share": round(weekend_ml / (weekend_ml + weekend_sci), 3)}
    else:
        balance = {"available": False}

    # A Saturday Weekend's siblings run Sunday..Friday, so reach one day before the window.
    span_start = (dt.date.fromisoformat(window_start) - dt.timedelta(days=1)).isoformat()
    tiers = [sum(v["tiers"][k] for v in by_stream.values()) for k in ("T1", "T2", "untiered")]
    return {"aggregator_leakage": leakage, "by_stream": by_stream,
            "t1_share": round(tiers[0] / sum(tiers), 3) if sum(tiers) else None,
            "feeds": feeds, "feeds_walled": build_feeds_walled(feeds),
            "lint": lint_acc, "weekend_balance": balance,
            "weekend_revisits": build_weekend_revisits(_window_posts(root, span_start, window_end))}


# A `reach: direct` registry domain is drifting when the window's writer fetch log never reached
# it over plain curl yet the proxy carried at least this many successes. At least one logged
# failure is also required: `fetch.py --proxy` skips curl entirely, so 0 curl successes with 0
# failures means curl was never tried, not that it failed.
_REACH_DRIFT_MIN_PROXY = 3


def _load_registry(root):
    """sources/registry.yml through registry.py's own loader (the file is a YAML subset PyYAML
    does not fully accept). None when absent or unreadable -- never raises."""
    import importlib.util
    tool = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sources", "registry.py")
    try:
        spec = importlib.util.spec_from_file_location("_registry_m", os.path.normpath(tool))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with open(mod.registry_path(root), encoding="utf-8") as f:
            reg = mod.yaml_load(f.read())
    except (OSError, ValueError, ImportError, AttributeError, SyntaxError):
        return None
    return reg if isinstance(reg, dict) else None


def window_feeds(root, window_start, window_end):
    """The writers' per-host fetch counts ("Feeds hit" footer lines) over [start, end], in the
    shape build_reach_drift takes. registry.py sync reads it for the bounded auto reach flip."""
    feeds = {}
    for _date, _slug, text in _window_posts(root, window_start, window_end):
        _parse_feeds(_split_footer(text)[1], feeds)
    return feeds


def build_reach_drift(root, feeds):
    """Registry `reach:` drift from the writers' own fetch telemetry (K). Each feed label is a
    host; it maps to the longest registry key equal to it or a parent domain of it (rss.dw.com
    -> dw.com). An entry recorded `reach: direct` whose mapped hosts show 0 curl successes and
    >= _REACH_DRIFT_MIN_PROXY proxy successes and at least one failure this window is listed as
    a direct -> proxy flip. Malformed (non-mapping) registry entries are skipped, never raised on.
    Writer telemetry, not an evaluator probe: the evaluator's egress cannot reach most of these
    hosts, which is why `reach:` drifted unmaintained until 2026-10-01."""
    reg = _load_registry(root)
    if reg is None:
        return {"available": False}
    by_domain = {}
    for label, counts in feeds.items():
        host = label.lower()
        host = host[4:] if host.startswith("www.") else host
        keys = [k for k in reg if host == k or host.endswith("." + k)]
        if not keys:
            continue
        domain = max(keys, key=len)
        acc = by_domain.setdefault(domain, {"ok_curl": 0, "ok_proxy": 0, "fail": 0, "hosts": []})
        for field in ("ok_curl", "ok_proxy", "fail"):
            acc[field] += counts.get(field, 0)
        acc["hosts"].append(label)
    drift = []
    for domain, acc in by_domain.items():
        entry = reg.get(domain)
        if not isinstance(entry, dict):
            continue
        if (entry.get("reach") == "direct" and acc["ok_curl"] == 0 and acc["fail"] > 0
                and acc["ok_proxy"] >= _REACH_DRIFT_MIN_PROXY):
            drift.append(dict(domain=domain, recorded="direct", observed="proxy",
                              hosts=sorted(acc["hosts"]), ok_curl=0,
                              ok_proxy=acc["ok_proxy"], fail=acc["fail"]))
    drift.sort(key=lambda d: (-d["ok_proxy"], d["domain"]))
    return {"available": True, "min_proxy": _REACH_DRIFT_MIN_PROXY, "flips": drift}


def _git_lines(root, argv):
    proc = subprocess.run(["git"] + argv, cwd=root, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip())
    return [l for l in (proc.stdout or "").splitlines() if l.strip()]


def build_off_main(root, window_start):
    """Self-delivery guard, computed: remote branches besides origin/main + recent
    commits not reachable from origin/main (the `outcomes`-stranding class). Only
    runs when root itself is a git repo -- fixture trees degrade to available:false.

    The comparison is against `origin/main`, NOT the local `main` ref (rm-3,
    2026-07-19/26/08-02): the routine runs detached after `git pull --ff-only`,
    which leaves local `main` stale and made every pulled commit look off-main
    (~14-20 phantoms a week). No fetch here -- the fire-start already pulled, so
    the local `origin/main` ref is current; if it cannot be resolved this
    degrades to available:false rather than falling back to the stale ref.

    Shallow clones (2026-09-20/27 reviews): the sandbox pulls into a depth-limited
    clone, so the new origin/main history stops at a fresh shallow boundary and
    git cannot connect it to the pre-pull tip -- the pull prints "(forced update)"
    and the stale local `main` plus its ancestors read as off-main although they
    are on main. Ancestry is unknowable below the boundary, so in a shallow repo
    a commit dated at or before origin/main's oldest visible commit is not
    judged: it is counted in `shallow_skipped`, never listed. The skip applies
    only to commits reachable from local refs/HEAD; anything on a remote branch
    (the `outcomes` claude/* stranding class) is always listed, and a commit made
    after the pull is newer than the boundary, so both stay caught."""
    if not os.path.isdir(os.path.join(root, ".git")):
        return {"available": False}
    try:
        branches = [b.strip() for b in _git_lines(root, ["branch", "-r", "--format=%(refname:short)"])
                    if b.strip() not in ("", "origin", "origin/main") and "HEAD" not in b]
        shallow = _git_lines(root, ["rev-parse", "--is-shallow-repository"]) == ["true"]
        since = "--since=%s" % window_start
        rows = _git_lines(root, ["log", "--all", "--format=%ct %H %h %s", since, "--not", "origin/main"])
        boundary, on_remote = None, set()
        if shallow and rows:
            boundary = min(int(t) for t in _git_lines(root, ["log", "--format=%ct", "origin/main"]))
            on_remote = set(_git_lines(root, ["log", "--remotes", "--format=%H", since,
                                              "--not", "origin/main"]))
        commits, skipped = [], 0
        for row in rows:
            ts, sha, line = row.split(" ", 2)
            if boundary is not None and int(ts) <= boundary and sha not in on_remote:
                skipped += 1
            else:
                commits.append(line)
        return {"available": True, "remote_branches": branches,
                "commits_not_on_main": commits[:20],
                "shallow": shallow, "shallow_skipped": skipped}
    except (OSError, RuntimeError, ValueError):
        return {"available": False}


def build_lost_editions(root, window_start, window_end):
    """Editions a writer session measured but `_posts/` does not hold (2026-10-06 News: a
    10-minute run with a stage:"publish" usage record and no post; the 10-11 review called it a
    skipped fire because nothing else could see it). The usage ledger is written by the Stop
    hook even when the edition commit never reaches origin, so `edition` on any usage record
    in the window with no matching post is a lost edition, whatever lost it."""
    lost = {}
    for path in sorted(glob.glob(os.path.join(root, "index", "usage", "*.jsonl"))):
        try:
            fh = open(path, encoding="utf-8")
        except OSError:
            continue
        with fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                edition = rec.get("edition") if isinstance(rec, dict) else None
                if not edition or not _EDITION_RE.match(edition):
                    continue
                if not (window_start <= edition[:10] <= window_end):
                    continue
                if os.path.exists(os.path.join(root, "_posts", edition + ".md")):
                    continue
                row = lost.setdefault(edition, {"edition": edition,
                                                "session_id": rec.get("session_id"),
                                                "started": rec.get("started"), "stages": []})
                if rec.get("stage") not in row["stages"]:
                    row["stages"].append(rec.get("stage"))
    return [lost[k] for k in sorted(lost)]


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
    continuity["lost_editions"] = build_lost_editions(root, window_start, window_end)
    briefs = build_briefs(root, window_start, window_end)
    briefs["reach_drift"] = build_reach_drift(root, briefs["feeds"])
    return {
        "week": {"start": window_start, "end": window_end},
        "streams": build_streams(occurrences, window_start, window_end, thread_map),
        "feedback": dict(build_feedback(events, root, window_start, window_end),
                         reasoned=build_reasoned(events, root, window_start, window_end)),
        "sources": build_sources(root),
        "continuity": continuity,
        "briefs": briefs,
    }


def main(argv=None):
    p = argparse.ArgumentParser(prog="metrics.py", description=__doc__.splitlines()[0])
    p.add_argument("--root", default=os.getcwd())
    p.add_argument("--week", default=None, help="window end date, YYYY-MM-DD (default: today)")
    p.add_argument("--no-refresh-sources", dest="refresh_sources", action="store_false",
                   help="skip the source-health refresh and fold whatever is on disk")
    args = p.parse_args(argv)

    if args.refresh_sources:
        refresh_source_health(args.root)
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
