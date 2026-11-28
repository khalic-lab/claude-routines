#!/usr/bin/env python3
"""Compact readers for what tools/fetch.py saves: feed item lists and article text.

Writers used to write a throwaway parser every run (a titles.py and a txt.py in the session
scratchpad, re-invented each time) and read their output whole: every feed item whatever its
date, and article text with the site's menus still in it. In the News run of 2026-11-27 that
was about 60K characters of feed listing and 80K of article text, all of it written to the
cache and re-read on every later turn. These two commands do the same job deterministically:

  feeds.py titles [--hours H | --since ISO] [--max N] FILE...
      One line per feed item: `YYYY-MM-DD HH:MM | title | url`, newest first, items older
      than the window dropped. An item with no parsable date is KEPT and shown as `undated`
      (a feed without dates must not vanish). Known tracking parameters (utm_*, fbclid, ...)
      are dropped from URLs; everything else, fragment included, is kept as written. Reads
      RSS 2.0, Atom, RSS 1.0/RDF (HTML entities such as &nbsp; tolerated), JSON Feed and a
      bare JSON array of posts (WordPress REST). A header line per file gives
      `== NAME: kept/total in window`.

  feeds.py text [--max CHARS] FILE
      The article's readable text: <article>, else <main>, else <body>, without script,
      style, nav, footer, aside, form and menu chrome. An <article> or <main> is read even
      inside a wrapper whose class looks like chrome. When that comes back shorter
      than 400 characters (an unusual layout), it falls back to the whole page's text, so a
      page is never silently emptied. Output is capped at --max (default 6000) with a
      `[... cut at N of M characters]` marker.

Stdlib only; exit 0 even on an unreadable file (it prints why), so a sweep keeps going.
"""
import argparse
import datetime as dt
import email.utils
import html
import html.entities
import html.parser
import json
import os
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET

# Only names that are tracking everywhere. `ref`, `src`, `feed` or `rss` can select the page
# itself (?feed=rss2, ?src=...), so they stay.
_TRACKING = re.compile(r"^(utm_[a-z]+|traffic_source|at_[a-z_]+|cmpid|ns_[a-z]+|ito|xtor|"
                       r"fbclid|gclid|mc_[a-z]+|ocid)$", re.I)


def clean_url(url):
    """Drop known tracking query parameters. Every other byte stays as written: the other
    parameters (even `?12345` with no `=`), their encoding and order, and the fragment (a
    `#/article/99` route is the page)."""
    url = (url or "").strip()
    try:
        parts = urllib.parse.urlsplit(url)
    except ValueError:
        return url
    if not parts.query:
        return url
    segs = parts.query.split("&")
    kept = [seg for seg in segs
            if seg and not _TRACKING.match(urllib.parse.unquote_plus(seg.split("=", 1)[0]))]
    if kept == segs:
        return url
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, "&".join(kept),
                                    parts.fragment))


def parse_date(s):
    """RFC 822 (RSS), ISO 8601 (Atom, JSON Feed, dc:date) -> aware UTC datetime, or None."""
    if not s:
        return None
    s = s.strip()
    try:
        d = email.utils.parsedate_to_datetime(s)
        if d is not None:
            return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
    except (TypeError, ValueError, IndexError):
        pass
    try:
        d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def _local(tag):
    return tag.rsplit("}", 1)[-1].lower() if isinstance(tag, str) else ""


def _text(el):
    return re.sub(r"\s+", " ", html.unescape("".join(el.itertext()))).strip() if el is not None else ""


_XML_ENTITIES = {b"amp", b"lt", b"gt", b"quot", b"apos"}


def _html_entities_to_xml(raw):
    """&nbsp; &eacute; ... are HTML, not XML; many feeds use them anyway. Turn each into a
    numeric reference (an unknown name into literal text) so the feed parses."""
    def repl(m):
        name = m.group(1)
        if name in _XML_ENTITIES:
            return m.group(0)
        cp = html.entities.name2codepoint.get(name.decode("ascii"))
        return b"&#%d;" % cp if cp else b"&amp;" + name + b";"
    return re.sub(rb"&([A-Za-z][A-Za-z0-9]*);", repl, raw)


def _items_xml(raw):
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        root = ET.fromstring(_html_entities_to_xml(raw))
    out = []
    for el in root.iter():
        if _local(el.tag) not in ("item", "entry"):
            continue
        title = link = date = ""
        for ch in el:
            name = _local(ch.tag)
            if name == "title":
                title = _text(ch)
            elif name == "link":
                href = ch.get("href")
                rel = ch.get("rel", "alternate")
                if href and rel == "alternate" and not link:
                    link = href
                elif not href and not link:
                    link = _text(ch)
            elif name in ("pubdate", "published", "updated", "date", "issued") and not date:
                date = _text(ch)
            elif name == "guid" and not link and ch.get("isPermaLink", "true") != "false":
                link = _text(ch)
        if title or link:
            out.append((title, link, date))
    return out


def _str(v):
    """A JSON field as text: WordPress REST nests it ({"rendered": "..."}) and may put HTML in it."""
    if isinstance(v, dict):
        v = v.get("rendered") or v.get("text") or ""
    if v is None or isinstance(v, (list, dict, bool)):
        return ""
    return html.unescape(re.sub(r"<[^>]+>", "", str(v)))


def _items_json(raw):
    """JSON Feed ({"items": [...]}) or a bare array of posts (WordPress /wp-json/wp/v2/posts)."""
    data = json.loads(raw)
    items = data if isinstance(data, list) else (data.get("items") if isinstance(data, dict) else None)
    if not isinstance(items, list):
        raise ValueError("no item list")
    out = []
    for it in items:
        if isinstance(it, dict):
            out.append((_str(it.get("title")),
                        _str(it.get("url") or it.get("external_url") or it.get("link")),
                        _str(it.get("date_published") or it.get("date_modified")
                             or it.get("date_gmt") or it.get("date"))))
    return out


def read_items(path):
    """[(title, url, aware datetime | None)] from one saved feed file. Raises ValueError."""
    with open(path, "rb") as fh:
        raw = fh.read()
    head = raw.lstrip()[:1]
    try:
        rows = _items_json(raw) if head in (b"{", b"[") else _items_xml(raw)
    except (ET.ParseError, ValueError) as exc:
        raise ValueError("not a feed (%s)" % str(exc).split("\n")[0][:80])
    return [(re.sub(r"\s+", " ", t).strip(), clean_url(u), parse_date(d)) for t, u, d in rows]


def cmd_titles(a):
    now = dt.datetime.now(dt.timezone.utc)
    since = parse_date(a.since) if a.since else (now - dt.timedelta(hours=a.hours) if a.hours else None)
    for path in a.files:
        name = os.path.splitext(os.path.basename(path))[0]
        try:
            items = read_items(path)
        except Exception as exc:  # one odd file must not end the sweep over the rest
            print("== %s: unreadable -- %s" % (name, str(exc).split("\n")[0][:120]))
            continue
        kept = [i for i in items if i[2] is None or since is None or i[2] >= since]
        kept.sort(key=lambda i: i[2] or now, reverse=True)
        shown = kept[: a.max] if a.max else kept
        extra = "" if len(shown) == len(kept) else ", showing %d" % len(shown)
        print("== %s: %d/%d in window%s" % (name, len(kept), len(items), extra))
        for title, url, d in shown:
            when = d.astimezone(dt.timezone.utc).strftime("%Y-%m-%d %H:%M") if d else "undated"
            print("%s | %s | %s" % (when, title or "(no title)", url))
    return 0


_SKIP = {"script", "style", "noscript", "nav", "footer", "aside", "form", "svg",
         "button", "select", "template", "iframe", "figure"}
_BLOCK = {"p", "div", "section", "article", "main", "li", "h1", "h2", "h3", "h4", "h5", "h6",
          "blockquote", "tr", "br", "dd", "dt", "pre", "figcaption", "td"}
# A <header> is kept: inside an article it holds the headline. Site chrome is caught by its
# class / id / ARIA role instead (role=navigation, banner, contentinfo, complementary).
_CHROME = re.compile(r"(^|[\s_-])(menu|nav|navigation|cookie|consent|banner|share|social|related|"
                     r"newsletter|subscribe|breadcrumb|footer|sidebar|promo|advert|paywall|"
                     r"contentinfo|complementary)([\s_-]|$)", re.I)
# Class tokens that describe the CONTENT or the layout, not a chrome block: WordPress puts
# tag-<slug> / category-<slug> on the article and body (tag-social-media), themes put
# no-sidebar / has-sidebar on the page wrapper.
_NOT_CHROME = re.compile(r"^(tag|category|no|not|without|has|is|with)[-_]", re.I)
# Never skipped for a class or id: they ARE the regions (the article's own classes are
# taxonomy), and an <article> or <main> inside a chrome-looking wrapper is still read.
_STRUCTURAL = {"html", "body", "main", "article"}
_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source",
         "track", "wbr"}


def _looks_like_chrome(attrs):
    tokens = [t for key in ("class", "id") for t in (attrs.get(key) or "").split()
              if not _NOT_CHROME.match(t)]
    if attrs.get("role"):
        tokens.append(attrs["role"])
    return any(_CHROME.search(t) for t in tokens)


class _Extract(html.parser.HTMLParser):
    """Collects text per region (article / main / body), skipping chrome subtrees.

    Each open element carries a skip state: None (read), "tag" (script, nav, aside, hidden...:
    skipped with everything inside), or "class" (a chrome-looking class or id: skipped, except
    that an <article> or <main> inside it is read)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []     # (tag, skip state, region it opened or None)
        self.regions = {"article": [], "main": [], "body": []}
        self.open = {"article": 0, "main": 0, "body": 0}

    def _skip(self):
        return self.stack[-1][1] if self.stack else None

    def handle_starttag(self, tag, attrs):
        if tag in _VOID:
            if tag == "br" and self._skip() is None:
                self._emit("\n")
            return
        attrs = dict(attrs)
        parent = self._skip()
        if parent == "tag" or tag in _SKIP or attrs.get("aria-hidden") == "true" or "hidden" in attrs:
            state = "tag"
        elif tag in _STRUCTURAL:
            state = None
        elif parent == "class" or _looks_like_chrome(attrs):
            state = "class"
        else:
            state = None
        region = tag if state is None and tag in self.open else None
        self.stack.append((tag, state, region))
        if region:
            self.open[region] += 1
        if state is None and tag in _BLOCK:
            self._emit("\n")

    def handle_endtag(self, tag):
        if tag in _VOID or all(t != tag for t, _, _ in self.stack):
            return
        while self.stack:  # close up to the matching tag (tolerates unclosed children)
            t, state, region = self.stack.pop()
            if state is None and t in _BLOCK:
                self._emit("\n")
            if region:
                self.open[region] -= 1
            if t == tag:
                break

    def handle_data(self, data):
        if self._skip() is None:
            self._emit(data)

    def _emit(self, s):
        for region in ("article", "main", "body"):
            if self.open[region]:
                self.regions[region].append(s)


def _tidy(parts):
    text = "".join(parts)
    lines = [re.sub(r"[ \t\r\f\v]+", " ", l).strip() for l in text.split("\n")]
    return "\n".join(l for l in lines if l)


def extract_text(raw_html):
    """Readable text of a page: article > main > body, chrome removed; falls back to the whole
    body text (chrome included) when the cleaned region is under 400 characters."""
    p = _Extract()
    try:
        p.feed(raw_html)
        p.close()
    except Exception:  # html.parser is lenient; anything it still rejects falls through
        pass
    for region in ("article", "main", "body"):
        t = _tidy(p.regions[region])
        if len(t) >= 400:
            return t
    plain = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", raw_html)
    plain = html.unescape(re.sub(r"(?s)<[^>]+>", "\n", plain))
    return _tidy([plain])


def cmd_text(a):
    try:
        with open(a.file, encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
    except OSError as exc:
        print("unreadable: %s" % exc)
        return 0
    t = extract_text(raw)
    if a.max and len(t) > a.max:
        t = t[: a.max].rstrip() + "\n[... cut at %d of %d characters]" % (a.max, len(t))
    print(t)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("titles", help="feed items in the window, newest first")
    t.add_argument("--hours", type=float, help="keep items from the last H hours")
    t.add_argument("--since", help="keep items at or after this ISO time")
    t.add_argument("--max", type=int, default=0, help="at most N items per feed (0 = all)")
    t.add_argument("files", nargs="+")
    x = sub.add_parser("text", help="an article's readable text")
    x.add_argument("--max", type=int, default=6000)
    x.add_argument("file")
    a = ap.parse_args(argv)
    return cmd_titles(a) if a.cmd == "titles" else cmd_text(a)


if __name__ == "__main__":
    sys.exit(main())
