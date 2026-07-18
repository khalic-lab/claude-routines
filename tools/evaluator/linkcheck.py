#!/usr/bin/env python3
"""Link-health sampler for the Weekly Evaluator (dimension C, mechanical half).

Collects every http(s) link from the window's writer briefs, draws a
DETERMINISTIC sample (seeded by the window end date -- same week, same sample,
so a re-run mid-review checks the same links), and with --check resolves each
via `curl -sIL` (the sandbox egress path that works; no bearer needed).

The evaluator's remaining judgment work on this dimension is the claim
spot-check: of the resolved sample, read ~8 and verify the cited claim is
actually in the source. That cannot be scripted; this tool does the rest.

Usage: linkcheck.py [--root .] [--week YYYY-MM-DD] [--sample 20] [--check]
"""
import argparse
import datetime as dt
import glob
import os
import random
import re
import subprocess
import sys

_POST_NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z0-9-]+)\.md$")
_LINK_RE = re.compile(r"\]\((https?://[^)\s]+)")
_SLUGS = ("news", "ai-ml", "science", "weekend", "sports")
_WINDOW_DAYS = 7


def collect_links(root, start, end):
    seen, links = set(), []
    for path in sorted(glob.glob(os.path.join(root, "_posts", "*.md"))):
        m = _POST_NAME_RE.match(os.path.basename(path))
        if not m or m.group(2) not in _SLUGS or not (start <= m.group(1) <= end):
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            continue
        body = text.split("\n## Coverage footer")[0]
        for url in _LINK_RE.findall(body):
            if url not in seen:
                seen.add(url)
                links.append((os.path.basename(path), url))
    return links


def resolve(url, max_time=15):
    try:
        proc = subprocess.run(
            ["curl", "-sIL", "--max-time", str(max_time), "-o", os.devnull,
             "-w", "%{http_code}", url],
            capture_output=True, text=True)
    except OSError as exc:
        return "ERR:%s" % exc
    code = (proc.stdout or "").strip()
    if proc.returncode != 0 and code in ("", "000"):
        return "ERR:%d" % proc.returncode
    return code


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--root", default=".")
    p.add_argument("--week", default=None, help="window END date; default today")
    p.add_argument("--sample", type=int, default=20)
    p.add_argument("--check", action="store_true", help="resolve each sampled link via curl -sIL")
    args = p.parse_args(argv)

    end = args.week or dt.date.today().isoformat()
    start = (dt.date.fromisoformat(end) - dt.timedelta(days=_WINDOW_DAYS - 1)).isoformat()
    links = collect_links(args.root, start, end)
    if not links:
        print("linkcheck: no links found in window [%s, %s]." % (start, end))
        return 0

    rng = random.Random(end)  # deterministic per window
    sample = rng.sample(links, min(args.sample, len(links)))

    ok = 0
    for post, url in sample:
        if args.check:
            status = resolve(url)
            passed = status.isdigit() and 200 <= int(status) < 400
            ok += passed
            print("%s  %s  (%s)" % (status.rjust(7), url, post), flush=True)
        else:
            print("%s  (%s)" % (url, post))
    if args.check:
        print("linkcheck: %d/%d resolve (2xx/3xx) — window [%s, %s], %d links total."
              % (ok, len(sample), start, end, len(links)))
    else:
        print("linkcheck: sampled %d of %d links — window [%s, %s] (run with --check to resolve)."
              % (len(sample), len(links), start, end))
    return 0


if __name__ == "__main__":
    sys.exit(main())
