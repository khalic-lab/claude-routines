#!/usr/bin/env python3
"""Logging fetch wrapper -- the deterministic curl -> fetch-proxy fallback chain.

Replaces the prompt-prose fetch mechanics ("try curl first, fall back to the proxy,
mark the method in the footer") with one command, and logs every attempt so the
Coverage footer's fetch telemetry can be COMPUTED (tools/footer.py) instead of
self-reported by the model.

Chain: direct `curl -fsSL` first (the egress path that works from the routine
sandbox -- WebFetch and python urllib do not share it, so this MUST shell out to
curl), then the fetch-proxy Worker with the bearer from $FETCH_PROXY_TOKEN.
`--proxy` skips the direct attempt for hosts known to 403 the sandbox IP.
No token in the environment -> the proxy step is skipped silently (the Evaluator
holds no bearer by design).

Every ATTEMPT appends one JSON line to $FETCH_LOG (default /tmp/fetch.log):
  {"ts": "...Z", "url": ..., "method": "curl"|"proxy", "status": 200|403|"ERR:6", "ok": bool}

Body goes to stdout on success; exit is 0 on success, 22 on failure (mirroring
`curl -f`, so `fetch.py URL || fallback-to-snippet` keeps its semantics).

Usage: fetch.py <url> [--proxy] [--max-time N] [--log PATH]
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlparse

PROXY_URL = "https://fetch-proxy.khalic-lab.workers.dev/"
DEFAULT_LOG = os.environ.get("FETCH_LOG", "/tmp/fetch.log")


def _log(path, url, method, status, ok):
    line = json.dumps({
        "ts": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "url": url, "method": method, "status": status, "ok": ok,
    })
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass  # a broken log must never break the fetch


def _curl(argv, out_path, max_time):
    """Run curl writing the body to out_path, HTTP code on stdout.
    Returns (ok, status) where status is an int HTTP code or "ERR:<curl exit>"."""
    # -g (--globoff): without it curl expands [..] and {..} in the URL locally and exits 3
    # before any request -- the arXiv submittedDate:[A TO B] range query failed that way.
    cmd = ["curl", "-gsSL", "--max-time", str(max_time),
           "-o", out_path, "-w", "%{http_code}"] + argv
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except OSError as exc:
        return False, "ERR:%s" % exc
    code_text = (proc.stdout or "").strip()
    try:
        status = int(code_text)
    except ValueError:
        status = 0
    if proc.returncode != 0 and status == 0:
        return False, "ERR:%d" % proc.returncode
    return (proc.returncode == 0 and 200 <= status < 300), status


# Hosts whose API terms ask for spacing between calls (arXiv: one request every 3 s). The
# writers' sweep of 5 RSS categories + the Atom API in one burst drew 26 HTTP 429s and 7 502s
# from export.arxiv.org over 2026-10-01..11-27 (fetch-log footers).
PACED_HOSTS = {"export.arxiv.org": 4}
# A host that has answered 429 this many times since its last success in THIS run, the latest
# under RATE_LIMIT_HOLD_S ago, is rate-limiting us: further calls fail at once, logged as
# SKIP:429, instead of repeating the storm (api.openalex.org: 12-18 consecutive 429s per Science
# run, 0 successes, 2026-10/11). The hold lapses, so a host can recover inside a run; paced hosts
# are exempt -- arXiv 429s come from bursts, and pacing is their remedy (10-02 AI/ML: 19 x 429
# beside 15 successes).
RATE_LIMIT_TRIP = 3
RATE_LIMIT_HOLD_S = 600


def _host(url):
    netloc = urlparse(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


def _host_history(log_path, host):
    """This run's logged attempts for `host`, oldest first (the log is per-sandbox)."""
    out = []
    try:
        with open(log_path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if isinstance(rec, dict) and _host(rec.get("url") or "") == host:
                    out.append(rec)
    except OSError:
        pass
    return out


def _ts(rec):
    try:
        return dt.datetime.strptime(rec["ts"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except (KeyError, TypeError, ValueError):
        return None


def _rate_limited(history, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    n, latest = 0, None
    for rec in reversed(history):
        if rec.get("ok"):
            break
        if rec.get("status") == 429:
            n += 1
            latest = latest or _ts(rec)
    return (n >= RATE_LIMIT_TRIP and latest is not None
            and (now - latest).total_seconds() < RATE_LIMIT_HOLD_S)


def _pace(history, gap):
    last = _ts(history[-1]) if history else None
    if last is None:
        return
    wait = gap - (dt.datetime.now(dt.timezone.utc) - last).total_seconds()
    if wait > 0:
        time.sleep(wait)


def fetch(url, proxy_first=False, max_time=25, log_path=DEFAULT_LOG):
    """Returns (ok, body_path). Caller reads/streams body_path on ok."""
    token = os.environ.get("FETCH_PROXY_TOKEN", "")
    fd, body_path = tempfile.mkstemp(prefix="fetch-", suffix=".body")
    os.close(fd)

    host = _host(url)
    history = _host_history(log_path, host)
    if host not in PACED_HOSTS and _rate_limited(history):
        _log(log_path, url, "skip", "SKIP:429", False)
        return False, body_path
    if host in PACED_HOSTS:
        _pace(history, PACED_HOSTS[host])

    if not proxy_first:
        ok, status = _curl([url], body_path, max_time)
        _log(log_path, url, "curl", status, ok)
        if ok:
            return True, body_path

    if token:
        ok, status = _curl(
            ["-G", PROXY_URL, "--data-urlencode", "url=%s" % url,
             "-H", "Authorization: Bearer %s" % token],
            body_path, max_time)
        _log(log_path, url, "proxy", status, ok)
        if ok:
            return True, body_path
    elif proxy_first:
        # --proxy with no bearer: nothing was attempted at all; try direct after all
        # rather than failing silently (better one honest attempt than none).
        ok, status = _curl([url], body_path, max_time)
        _log(log_path, url, "curl", status, ok)
        if ok:
            return True, body_path

    return False, body_path


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("url")
    p.add_argument("--proxy", action="store_true",
                   help="skip the direct attempt (host known to 403 the sandbox)")
    p.add_argument("--max-time", type=int, default=25)
    p.add_argument("--log", default=DEFAULT_LOG)
    args = p.parse_args(argv)

    ok, body_path = fetch(args.url, proxy_first=args.proxy,
                          max_time=args.max_time, log_path=args.log)
    try:
        if ok:
            with open(body_path, "rb") as fh:
                sys.stdout.buffer.write(fh.read())
            return 0
        print("fetch.py: FAILED %s (see %s)" % (args.url, args.log), file=sys.stderr)
        return 22
    finally:
        try:
            os.unlink(body_path)
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main())
