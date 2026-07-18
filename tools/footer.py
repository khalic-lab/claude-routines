#!/usr/bin/env python3
"""Computed Coverage-footer telemetry -- fills the hidden operational-telemetry
comment under `## Coverage footer` with numbers a script can prove, replacing the
model's self-reported approximations ("~5,300 words", "~130 tool calls").

Computed lines (owned by this tool -- rewritten in place, idempotent):
  - Sources used:      registry tier (T1/T2) of each citation's FIRST link + untiered count
  - Direct fetches:    total citations minus [via snippet]-tagged ones
  - Word count:        exact body word count | research tool calls (logged) from the fetch log
  - Token estimate:    words / 0.75, exactly -- with the not-billed-cost caveat
  - Feeds hit:         per-host ok/fail/method aggregation of tools/fetch.py's log

Anything else inside the comment (e.g. a writer-authored `- Languages:` line) is
preserved verbatim. The visible judgment lines (Gaps, Discovery, Sibling
consultation) are never touched -- they stay the model's job.

Line shapes are kept compatible with tools/build_stats.py's WORDS_RE/CALLS_RE and
the Evaluator's footer parsers. Report-only, never aborts the brief: any crash
prints a warning and exits 0.

Usage: footer.py <post.md> [--root .] [--fetch-log /tmp/fetch.log] [--dry-run]
"""
import argparse
import datetime as dt
import importlib.util
import json
import os
import re
import sys
from urllib.parse import urlparse

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TOOLS, "sources"))
_lint_spec = importlib.util.spec_from_file_location("_lint", os.path.join(TOOLS, "sources", "lint.py"))
_lint = importlib.util.module_from_spec(_lint_spec)
_lint_spec.loader.exec_module(_lint)

FOOTER_HEADING_RE = re.compile(r"^## Coverage footer\s*$")
FRONT_MATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.S)
VIA_SNIPPET = "[via snippet]"

COMMENT_HEADER = ("<!-- operational telemetry — machine/evaluator-read; computed by "
                  "tools/footer.py at publish time; hidden from the rendered page")
COMPUTED_PREFIXES = ("- Sources used:", "- Direct fetches:", "- Word count:",
                     "- Token estimate", "- Feeds hit")

_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_HTML_RE = re.compile(r"<[^>]+>")
_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


def clean_words(text):
    text = _COMMENT_RE.sub(" ", text)
    text = _MD_LINK_RE.sub(r"\1", text)
    text = _HTML_RE.sub(" ", text)
    text = re.sub(r"[*_`#>|]+", " ", text)
    text = re.sub(r"^-{3,}\s*$", " ", text, flags=re.M)
    return len(text.split())


def split_post(text):
    """(front_matter, body, footer) -- body ends just before the trailing `---`
    separator (if any) above `## Coverage footer`; footer starts at the heading."""
    fm = FRONT_MATTER_RE.match(text)
    fm_text = fm.group(0) if fm else ""
    rest = text[len(fm_text):]
    lines = rest.split("\n")
    for i, line in enumerate(lines):
        if FOOTER_HEADING_RE.match(line):
            body_lines = lines[:i]
            while body_lines and body_lines[-1].strip() in ("", "---"):
                body_lines.pop()
            return fm_text, "\n".join(body_lines), "\n".join(lines[i:])
    return fm_text, rest, ""


def citation_lines(text):
    """Citation lines per the lint's own registers (bullet / heading-cite,
    anchor-tolerant, first-link attribution)."""
    out = []
    for line in text.split("\n"):
        if not (_lint.BULLET_RE.match(line) or _lint.HEADING_CITE_RE.match(line)):
            continue
        urls = _lint.LINK_RE.findall(line)
        if urls:
            out.append({"line": line, "domain": _lint.domain_of(urls[0])})
    return out


def tier_split(citations, reg):
    tiers = {"T1": 0, "T2": 0, "untiered": 0}
    for c in citations:
        tier = (reg.get(c["domain"]) or {}).get("tier")
        tiers[tier if tier in ("T1", "T2") else "untiered"] += 1
    return tiers


def read_fetch_log(path):
    attempts = []
    if not path or not os.path.exists(path):
        return attempts
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if isinstance(rec, dict) and rec.get("url"):
                    attempts.append(rec)
    except OSError:
        pass
    return attempts


def feeds_hit_line(attempts):
    """Per-host aggregation: `host {2 ok via curl, 1 fail HTTP 403}; ...` --
    the `N ok via <method>` / `N fail` markers parse with the same regex the
    Evaluator metrics use for the legacy hand-written format."""
    hosts = {}
    for a in attempts:
        netloc = urlparse(a["url"]).netloc.lower()
        host = netloc[4:] if netloc.startswith("www.") else netloc
        h = hosts.setdefault(host, {})
        if a.get("ok"):
            key = "ok via %s" % a.get("method", "curl")
        else:
            status = a.get("status")
            key = "fail HTTP %s" % status if isinstance(status, int) and status else "fail %s" % status
        h[key] = h.get(key, 0) + 1
    segments = []
    for host in sorted(hosts):
        parts = ["%d %s" % (n, key) for key, n in sorted(hosts[host].items())]
        segments.append("%s {%s}" % (host, ", ".join(parts)))
    return "; ".join(segments)


def build_comment(post_path, root, fetch_log, text):
    _, body, footer = split_post(text)
    reg = _lint.load_registry(root)
    citations = citation_lines(body)
    via = sum(1 for c in citations if VIA_SNIPPET in c["line"])
    direct = len(citations) - via
    tiers = tier_split(citations, reg)
    body_words = clean_words(body)
    total_words = body_words + clean_words(footer)
    attempts = read_fetch_log(fetch_log)

    lines = [
        "- Sources used: T1 = %d, T2 = %d, untiered = %d (registry tier of each citation's first link)"
        % (tiers["T1"], tiers["T2"], tiers["untiered"]),
        "- Direct fetches: %d | via-snippet citations: %d" % (direct, via),
    ]
    words_line = "- Word count: %s (body, excl. footer)" % format(body_words, ",d")
    if attempts:
        words_line += " | research tool calls (logged): %d" % len(attempts)
    lines.append(words_line)
    lines.append(
        "- Token estimate (computed): output ≈ %s tokens (post words ÷ 0.75); NOT billed session "
        "cost — per-turn context re-billing and prompt caching are excluded; true spend lives in "
        "the claude.ai run history." % format(round(total_words / 0.75), ",d"))
    if attempts:
        lines.append("- Feeds hit (from fetch log): %s" % feeds_hit_line(attempts))
    return lines


def rewrite(text, computed_lines):
    """Insert-or-replace the telemetry comment right under `## Coverage footer`,
    preserving writer-authored lines the computed set doesn't own."""
    lines = text.split("\n")
    heading_i = None
    for i, line in enumerate(lines):
        if FOOTER_HEADING_RE.match(line):
            heading_i = i
            break
    if heading_i is None:
        return None  # no footer heading -- nothing to do

    # Locate an existing comment directly after the heading (blank lines allowed).
    start = heading_i + 1
    while start < len(lines) and not lines[start].strip():
        start += 1
    preserved, end = [], start
    if start < len(lines) and lines[start].lstrip().startswith("<!--"):
        end = start
        while end < len(lines) and "-->" not in lines[end]:
            end += 1
        end = min(end + 1, len(lines))
        for raw in lines[start:end]:
            stripped = raw.strip()
            if stripped.startswith("<!--") or stripped.startswith("-->") or stripped == "":
                continue
            if stripped.endswith("-->"):
                stripped = stripped[:-3].rstrip()
                if not stripped:
                    continue
            if not stripped.startswith(COMPUTED_PREFIXES):
                preserved.append(stripped)
    else:
        end = start = heading_i + 1

    comment = [COMMENT_HEADER] + computed_lines + preserved + ["-->"]
    return "\n".join(lines[:heading_i + 1] + comment + lines[end:])


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("post")
    p.add_argument("--root", default=".")
    p.add_argument("--fetch-log", default=os.environ.get("FETCH_LOG", "/tmp/fetch.log"))
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    try:
        with open(args.post, encoding="utf-8") as fh:
            text = fh.read()
        computed = build_comment(args.post, args.root, args.fetch_log, text)
        new_text = rewrite(text, computed)
        if new_text is None:
            print("footer.py: no '## Coverage footer' heading in %s -- skipped." % args.post)
            return 0
        if args.dry_run:
            print("\n".join(computed))
            return 0
        if new_text != text:
            with open(args.post, "w", encoding="utf-8") as fh:
                fh.write(new_text)
        print("footer.py: telemetry computed for %s (%d citation(s))."
              % (os.path.basename(args.post), len(citation_lines(split_post(text)[1]))))
        return 0
    except Exception as exc:  # report-only: never block the brief
        print("footer.py: crashed (%s) -- telemetry left as written." % exc, file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
