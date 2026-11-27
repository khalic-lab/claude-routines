#!/usr/bin/env python3
"""arXiv papers submitted inside a date window, per category, as one line per paper.

    python3 tools/arxiv_window.py --cat cs.LG --cat cs.AI --from 20261121 --to 20261127
        [--max 120] [--grep 'reinforcement|RL\\b'] [--page-size 500] [--max-pages 6]

Why (2026-11-22 review): arXiv RSS carries only the latest daily announcement, and the Atom
query the prompts used ("the 100 newest, filter client-side") covers about one day of cs.LG,
so a multi-day window silently lost most of its papers. This pages the API's SERVER-SIDE
`submittedDate:[FROM TO]` range instead. Every call goes through tools/fetch.py (logged, so the
footer's Feeds hit counts it; export.arxiv.org is paced there), one retry after 10 s on failure.

Output, per category: a `# arXiv <cat> <from>..<to>: total N ...` header, then
`<id>\t<YYYY-MM-DD>\t<primary category>\t<title>` lines. A paper already printed under an
earlier --cat is not repeated. Without --grep the --max lines are spread evenly over the
window's days (newest first inside a day), so a week is never just its last day; with --grep
(case-insensitive, over title + abstract) the matches are listed newest first up to --max.
Shortlist from the titles, then fetch abstracts only for the shortlist.
"""
import argparse
import datetime as dt
import importlib.util
import os
import re
import sys
import time
import xml.etree.ElementTree as ET

API = "http://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom",
      "os": "http://a9.com/-/spec/opensearch/1.1/"}
RETRY_WAIT_S = 10


def _fetch_mod():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fetch.py")
    spec = importlib.util.spec_from_file_location("_fetch_for_arxiv", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def query_url(cat, start_day, end_day, start, size):
    # brackets percent-encoded: no curl globbing, no proxy re-encoding surprises
    q = "cat:%s+AND+submittedDate:%%5B%s0000+TO+%s2359%%5D" % (cat, start_day, end_day)
    return ("%s?search_query=%s&sortBy=submittedDate&sortOrder=descending&start=%d&max_results=%d"
            % (API, q, start, size))


def parse_feed(xml_text):
    """(total, [entry]) where entry = {id, date, primary, title, summary}."""
    root = ET.fromstring(xml_text)
    total_el = root.find("os:totalResults", NS)
    total = int(total_el.text) if total_el is not None and (total_el.text or "").strip() else 0
    out = []
    for e in root.findall("a:entry", NS):
        raw_id = (e.findtext("a:id", "", NS) or "").strip()
        m = re.search(r"abs/([^v\s]+)(?:v\d+)?$", raw_id)
        if not m:
            continue
        prim = e.find("arxiv:primary_category", NS)
        out.append({
            "id": m.group(1),
            "date": (e.findtext("a:published", "", NS) or "")[:10],
            "primary": prim.get("term") if prim is not None else "",
            "title": " ".join((e.findtext("a:title", "", NS) or "").split()),
            "summary": " ".join((e.findtext("a:summary", "", NS) or "").split()),
        })
    return total, out


def collect(cat, start_day, end_day, fetch_text, page_size=500, max_pages=6):
    """All entries of one category's window, newest first, paging until exhausted or capped.
    Returns (total, entries, pages, complete)."""
    entries, total, pages = [], 0, 0
    while pages < max_pages:
        text = fetch_text(query_url(cat, start_day, end_day, pages * page_size, page_size))
        if text is None:
            break
        pages += 1
        total, batch = parse_feed(text)
        entries.extend(batch)
        if not batch or len(entries) >= total:
            break
    return total, entries, pages, pages > 0 and len(entries) >= total


def spread(entries, n):
    """Up to n entries spread round-robin over their days, newest day first."""
    by_day = {}
    for e in entries:
        by_day.setdefault(e["date"], []).append(e)
    days = sorted(by_day, reverse=True)
    picked, k = [], 0
    while len(picked) < n and any(k < len(by_day[d]) for d in days):
        for d in days:
            if k < len(by_day[d]) and len(picked) < n:
                picked.append(by_day[d][k])
        k += 1
    return sorted(picked, key=lambda e: e["date"], reverse=True)


def run(cats, start_day, end_day, fetch_text, max_lines=120, grep=None, page_size=500,
        max_pages=6, out=sys.stdout):
    seen = set()
    rx = re.compile(grep, re.I) if grep else None
    span = "%s-%s-%s..%s-%s-%s" % (start_day[:4], start_day[4:6], start_day[6:],
                                   end_day[:4], end_day[4:6], end_day[6:])
    for cat in cats:
        total, entries, pages, complete = collect(cat, start_day, end_day, fetch_text,
                                                  page_size, max_pages)
        fresh = [e for e in entries if e["id"] not in seen]
        if rx:
            fresh = [e for e in fresh if rx.search(e["title"] + " " + e["summary"])]
            shown = fresh[:max_lines]
            how = "%d matching /%s/" % (len(fresh), grep)
        else:
            shown = spread(fresh, max_lines)
            how = "showing %d spread over %d day(s)" % (
                len(shown), len({e["date"] for e in shown}))
        print("# arXiv %s %s: total %d, fetched %d in %d page(s)%s; %d already listed above; %s"
              % (cat, span, total, len(entries), pages, "" if complete else " (INCOMPLETE)",
                 len(entries) - len([e for e in entries if e["id"] not in seen]), how),
              file=out, flush=True)
        for e in shown:
            print("%s\t%s\t%s\t%s" % (e["id"], e["date"], e["primary"], e["title"]), file=out)
        seen.update(e["id"] for e in entries)


def _live_fetch_text():
    fetch = _fetch_mod()

    def get(url):
        for attempt in (0, 1):
            ok, body_path = fetch.fetch(url, max_time=60)
            try:
                if ok:
                    with open(body_path, encoding="utf-8", errors="replace") as fh:
                        return fh.read()
            finally:
                try:
                    os.unlink(body_path)
                except OSError:
                    pass
            if attempt == 0:
                time.sleep(RETRY_WAIT_S)
        return None
    return get


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--cat", action="append", required=True, help="repeatable, e.g. cs.LG")
    p.add_argument("--from", dest="start", required=True, help="YYYYMMDD (inclusive)")
    p.add_argument("--to", dest="end", required=True, help="YYYYMMDD (inclusive)")
    p.add_argument("--max", type=int, default=120, help="lines per category")
    p.add_argument("--grep", default=None)
    p.add_argument("--page-size", type=int, default=500)
    p.add_argument("--max-pages", type=int, default=6)
    a = p.parse_args(argv)
    for d in (a.start, a.end):
        dt.datetime.strptime(d, "%Y%m%d")  # fail loudly on a malformed date
    run(a.cat, a.start, a.end, _live_fetch_text(), a.max, a.grep, a.page_size, a.max_pages)
    return 0


if __name__ == "__main__":
    sys.exit(main())
