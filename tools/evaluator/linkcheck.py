#!/usr/bin/env python3
"""Link-health sampler for the Weekly Evaluator (dimension C, mechanical half).

Collects every http(s) link from the window's writer briefs, draws a
DETERMINISTIC sample (seeded by the window end date -- same week, same sample,
so a re-run mid-review checks the same links), and with --check resolves each
via `curl -sIL` (the sandbox egress path that works; no bearer needed).

The Weekend's "Week in headlines" recap links are ALWAYS listed (and checked),
on top of the random sample and excluded from its pool: that recap is where the
pipeline's only measured link fabrications came from (2026-07-12 review: two
reconstructed Al Jazeera slugs, both 404), so a sample that can miss it cannot
tell whether the fetched-URL-only rule is holding. Their pass rate prints on its
own line.

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
import tempfile

_POST_NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z0-9-]+)\.md$")
_LINK_RE = re.compile(r"\]\((https?://[^)\s]+)")
_SLUGS = ("news", "ai-ml", "science", "weekend", "sports")
_WINDOW_DAYS = 7
_RECAP_HEADING = "Week in headlines"
PROXY_URL = "https://fetch-proxy.khalic-lab.workers.dev/"
# Direct answers worth a second path: egress refusals are ERR:*, these are anti-bot / HEAD-refused.
_RETRY_VIA_PROXY = ("403", "405", "429", "451")


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


def collect_recap_links(root, start, end):
    """(post, url) for every link in the window's Weekend "Week in headlines" section(s)."""
    links, seen = [], set()
    for path in sorted(glob.glob(os.path.join(root, "_posts", "*-weekend.md"))):
        m = _POST_NAME_RE.match(os.path.basename(path))
        if not m or not (start <= m.group(1) <= end):
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            continue
        in_recap = False
        for line in text.split("\n## Coverage footer")[0].splitlines():
            if line.startswith("## "):
                in_recap = _RECAP_HEADING in line
                continue
            if in_recap:
                for url in _LINK_RE.findall(line):
                    if url not in seen:
                        seen.add(url)
                        links.append((os.path.basename(path), url))
    return links


def _code(status):
    """The HTTP digits of a status string; a proxied result carries a trailing 'p'."""
    return status[:-1] if status.endswith("p") else status


def _passed(status):
    code = _code(status)
    return code.isdigit() and 200 <= int(code) < 400


def classify(status):
    """pass | broken (404/410: the page is gone -- the fabrication signal) | blocked (any other
    HTTP answer: the host refused us, the page may exist) | unreachable (ERR:* / PROXY:*: no
    HTTP answer from the target at all, so nothing is known about the page)."""
    code = _code(status)
    if code.isdigit():
        n = int(code)
        if 200 <= n < 400:
            return "pass"
        return "broken" if n in (404, 410) else "blocked"
    return "unreachable"


def _curl_code(args, max_time, header_file=None):
    cmd = ["curl", "-gsL", "--max-time", str(max_time), "-o", os.devnull, "-w", "%{http_code}"]
    if header_file:
        cmd += ["-D", header_file]
    try:
        proc = subprocess.run(cmd + args, capture_output=True, text=True)
    except OSError as exc:
        return "ERR:%s" % exc
    code = (proc.stdout or "").strip()
    if proc.returncode != 0 and code in ("", "000"):
        return "ERR:%d" % proc.returncode
    return code


def _via_proxy(url, token, max_time):
    """GET through the fetch-proxy Worker (GET-only). The Worker mirrors the upstream status and
    stamps X-Proxy-Upstream-Status; an answer WITHOUT that header is the Worker's own (401 bad
    bearer, 400/403 refused target, 502 upstream unreachable) and says nothing about the page,
    so it comes back as PROXY:<code>, never as a page status."""
    fd, hdr = tempfile.mkstemp(prefix="linkcheck-", suffix=".hdr")
    os.close(fd)
    try:
        code = _curl_code(["-G", PROXY_URL, "--data-urlencode", "url=%s" % url,
                           "-H", "Authorization: Bearer %s" % token], max_time, hdr)
        with open(hdr, encoding="latin-1") as fh:
            mirrored = any(l.lower().startswith("x-proxy-upstream-status:") for l in fh)
    except OSError:
        mirrored = False
    finally:
        try:
            os.unlink(hdr)
        except OSError:
            pass
    if code.startswith("ERR:") or not mirrored:
        return "PROXY:%s" % code
    return code + "p"


def resolve(url, max_time=15):
    """Direct HEAD first. On an egress refusal (ERR:*) or an anti-bot answer, one GET through
    the fetch proxy when $FETCH_PROXY_TOKEN holds a real bearer (an unsubstituted
    `${FETCH_PROXY_TOKEN}` placeholder counts as none). Proxied statuses end in 'p'."""
    status = _curl_code(["-I", url], max_time)
    if _passed(status):
        return status
    if status in ("404", "405", "410"):
        # some servers answer HEAD with 404/405 yet serve the page to a GET; a "broken" verdict
        # is a fabrication candidate, so confirm it with the GET the writer's fetch made
        status = _curl_code([url], max_time)
        if _passed(status) or status in ("404", "410"):
            return status
    token = os.environ.get("FETCH_PROXY_TOKEN", "")
    if not token or token.startswith("${"):
        return status
    if status.startswith("ERR:") or status in _RETRY_VIA_PROXY:
        return _via_proxy(url, token, max_time + 10)
    return status


def _tally_line(statuses):
    c = {"pass": 0, "broken": 0, "blocked": 0, "unreachable": 0}
    for s in statuses:
        c[classify(s)] += 1
    measurable = c["pass"] + c["broken"] + c["blocked"]
    return ("; broken (404/410) %d, blocked %d, unreachable %d; measurable %d/%d"
            % (c["broken"], c["blocked"], c["unreachable"], c["pass"], measurable))


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
    recap = collect_recap_links(args.root, start, end)
    recap_urls = {u for _, u in recap}
    pool = [l for l in links if l[1] not in recap_urls]

    recap_ok, recap_st = 0, []
    for post, url in recap:
        if args.check:
            status = resolve(url)
            recap_ok += _passed(status)
            recap_st.append(status)
            print("%s  %s  (%s) [recap]" % (status.rjust(7), url, post), flush=True)
        else:
            print("%s  (%s) [recap]" % (url, post))
    if recap:
        if args.check:
            print("linkcheck: recap %d/%d resolve (2xx/3xx) — Weekend \"%s\", always checked%s."
                  % (recap_ok, len(recap), _RECAP_HEADING, _tally_line(recap_st)))
        else:
            print("linkcheck: %d Weekend recap link(s) always included, outside the sample."
                  % len(recap))

    rng = random.Random(end)  # deterministic per window
    sample = rng.sample(pool, min(args.sample, len(pool)))

    ok, sample_st = 0, []
    for post, url in sample:
        if args.check:
            status = resolve(url)
            ok += _passed(status)
            sample_st.append(status)
            print("%s  %s  (%s)" % (status.rjust(7), url, post), flush=True)
        else:
            print("%s  (%s)" % (url, post))
    if args.check:
        print("linkcheck: %d/%d resolve (2xx/3xx) — window [%s, %s], %d links total%s."
              % (ok, len(sample), start, end, len(links), _tally_line(sample_st)))
        down = sorted({s for s in recap_st + sample_st if s.startswith("PROXY:")})
        if down:
            print("linkcheck: proxy unavailable (%s) -- proxied links count as unreachable."
                  % ", ".join(down))
    else:
        print("linkcheck: sampled %d of %d links — window [%s, %s] (run with --check to resolve)."
              % (len(sample), len(links), start, end))
    return 0


if __name__ == "__main__":
    sys.exit(main())
