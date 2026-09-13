#!/usr/bin/env python3
"""Render /admin/ as a standalone HTML file — the smoke surface for _layouts/admin.html's inline
CSS/JS, which Jekyll-only rendering makes otherwise untestable without a local Ruby toolchain.

It composes admin.html's content into _layouts/admin.html, substitutes the one theme include
(`head/custom.html`) with that file's Folio palette <style> blocks (fonts rewritten to file:// so
they actually load, exactly as tools/home_harness.py does), strips all remaining Liquid, then
injects a small bootstrap that:
  * seeds the passkey session (syncSession:v1) so the page renders SIGNED IN — unless --signed-out,
  * stubs window.fetch for /admin/* and /auth/* off the inlined fixture snapshot (no network), and
  * keeps window.__fetchLog so a reviewer can confirm the signed-out page makes zero requests.

The architect drives Chrome and the iPhone simulator against the output; this only renders. No JS is
executed here — see tools/tests/test_admin_harness.py for the static + `node --check` verification.

Usage:
    python3 tools/admin/harness.py --out /tmp/admin-harness.html
    python3 tools/admin/harness.py --out /tmp/admin-signedout.html --signed-out
    python3 tools/admin/harness.py --out /tmp/x.html --fixture tools/tests/fixtures/admin-snapshot.json
"""
import argparse
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_FIXTURE = os.path.join("tools", "tests", "fixtures", "admin-snapshot.json")

# window.__FB in head/custom.html is a <script>, not a <style>, so the style-only embed below does
# not carry it. Define it here so base() resolves the Worker origin just as it does in production;
# the fetch stub matches on pathname, so the host is cosmetic.
FB_URL = "https://feedback-sink.khalic-lab.workers.dev"


def _tokens():
    """Every <style> block from _includes/head/custom.html, fonts rewritten to file:// URLs.

    Mirrors tools/home_harness.py._extract_tokens: embedding the whole blocks (not a regex-picked
    :root) cannot silently drop a token, and it carries the button/field chrome too. Any Liquid left
    after the font substitution is a wrong render, so fail loudly.
    """
    src = os.path.join(ROOT, "_includes", "head", "custom.html")
    with open(src) as fh:
        blocks = re.findall(r"<style>.*?</style>", fh.read(), re.S)
    if not blocks:
        raise SystemExit("admin harness: no <style> block in %s" % src)
    blocks = [re.sub(r"""\{\{\s*["'](/assets/fonts/[^"']+)["']\s*\|\s*relative_url\s*\}\}""",
                     lambda m: "file://" + ROOT + m.group(1), b) for b in blocks]
    joined = "".join(blocks)
    leftover = re.findall(r"\{\{.*?\}\}|\{%.*?%\}", joined, re.S)
    if leftover:
        raise SystemExit("admin harness: unexpanded Liquid in custom.html CSS: %r" % leftover[:4])
    fb = '<script>window.__FB = { enabled: true, url: "%s" };</script>' % FB_URL
    return joined + fb


def _page_content():
    """admin.html with its Jekyll front matter stripped — the {{ content }} body."""
    src = os.path.join(ROOT, "admin.html")
    with open(src) as fh:
        text = fh.read()
    # strip a leading `---\n ... \n---\n` front-matter block
    text = re.sub(r"\A---\r?\n.*?\r?\n---\r?\n", "", text, count=1, flags=re.S)
    return text


def _bootstrap(fixture, signed_out):
    """Synchronous <script> that installs the fetch stub + (optional) seeded session BEFORE the
    page's own DOMContentLoaded handler runs. The fixture snapshot is inlined verbatim, so the
    output file literally contains the sample domains even though the visible render happens in the
    browser off the stubbed fetch."""
    snap = json.dumps(fixture)
    # A small live queue for GET /admin/actions (the snapshot carries only actions_recent). Kept
    # here rather than in the fixture so the committed snapshot stays a faithful §2.4 shape.
    queue = json.dumps({"count": 2, "actions": [
        {"key": "adm:1757745600:q1", "id": "q1", "ts": "2026-09-13T12:38:20Z", "reader": "rafael",
         "type": "retire", "domain": "aiweekly.co", "note": "still low-signal on re-review"},
        {"key": "adm:1757745720:q2", "id": "q2", "ts": "2026-09-13T12:39:05Z", "reader": "rafael",
         "type": "add", "domain": "lesswrong.com", "tier": "T2", "reach": "direct",
         "status": "probation", "streams": ["ai-ml", "weekend"]},
    ]})
    seed = "" if signed_out else (
        "try { localStorage.setItem('syncSession:v1', JSON.stringify("
        "{ token: new Array(65).join('a'), reader: 'rafael', at: Date.now() })); } catch (e) {}\n"
    )
    return (
        "<script>\n"
        "// ---- admin harness bootstrap (test scaffolding, not shipped) ----\n"
        + seed +
        "window.__ADMIN_SNAPSHOT = " + snap + ";\n"
        "window.__ADMIN_QUEUE = " + queue + ";\n"
        "window.__fetchLog = [];\n"
        "function __resp(status, obj){ return Promise.resolve({ ok: status >= 200 && status < 300,"
        " status: status, json: function(){ return Promise.resolve(obj); } }); }\n"
        "window.fetch = function(url, opts){\n"
        "  var u = String(url); window.__fetchLog.push(((opts && opts.method) || 'GET') + ' ' + u);\n"
        "  if (/\\/admin\\/snapshot/.test(u)) return __resp(200, window.__ADMIN_SNAPSHOT);\n"
        "  if (/\\/admin\\/actions/.test(u)){\n"
        "    if (opts && opts.method === 'POST') return __resp(200, { ok: true, id: 'stub', action: JSON.parse(opts.body || '{}') });\n"
        "    return __resp(200, window.__ADMIN_QUEUE);\n"
        "  }\n"
        "  if (/\\/auth\\//.test(u)) return __resp(200, { ok: false });\n"
        "  return __resp(404, { error: 'stub: unrouted ' + u });\n"
        "};\n"
        "</script>\n"
    )


def render(fixture_path, signed_out):
    with open(os.path.join(ROOT, "_layouts", "admin.html")) as fh:
        layout = fh.read()
    with open(fixture_path) as fh:
        fixture = json.load(fh)

    # the one theme include -> embedded palette tokens + window.__FB
    layout = re.sub(r"\{%-?\s*include\s+head/custom\.html\s*-?%\}", lambda m: _tokens(), layout)
    # {{ content }} -> admin.html body
    layout = layout.replace("{{ content }}", _page_content())
    # bootstrap goes right after <body> so it runs before the page script at </body>
    layout = layout.replace("<body>", "<body>\n" + _bootstrap(fixture, signed_out), 1)

    leftover = re.findall(r"\{\{.*?\}\}|\{%.*?%\}", layout, re.S)
    if leftover:
        raise SystemExit("admin harness: unexpanded Liquid left in output: %r" % leftover[:4])
    return layout


def main():
    ap = argparse.ArgumentParser(description="Render /admin/ as a standalone HTML harness.")
    ap.add_argument("--out", default="/tmp/admin-harness.html")
    ap.add_argument("--fixture", default=DEFAULT_FIXTURE)
    ap.add_argument("--signed-out", action="store_true",
                    help="render the signed-out gate (no session seeded, no requests made)")
    args = ap.parse_args()

    fixture_path = args.fixture if os.path.isabs(args.fixture) else os.path.join(ROOT, args.fixture)
    html = render(fixture_path, args.signed_out)
    with open(args.out, "w") as fh:
        fh.write(html)
    print("admin harness: wrote %s (%d bytes, %s)"
          % (args.out, len(html), "signed-out" if args.signed_out else "signed-in"))


if __name__ == "__main__":
    main()
