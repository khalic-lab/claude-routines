"""Spec tests for tools/feeds.py (writer-side feed listing and article text).

Contract: `titles` lists RSS 2.0 / Atom / RDF / JSON Feed items newest first, drops items
older than the window, KEEPS undated items, strips tracking parameters, and reports an
unreadable file instead of failing; `text` returns <article> > <main> > <body> text without
chrome, keeps an article's own <header> headline, falls back to whole-page text when the
cleaned region is short, and marks a cut.
"""
import contextlib
import io
import os
import sys
import tempfile
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, TOOLS)
import feeds  # noqa: E402

RSS = """<?xml version="1.0"?><rss version="2.0"><channel><title>T</title>
<item><title>Fresh story</title><link>https://ex.org/a?utm_source=rss&amp;id=7#top</link>
  <pubDate>Fri, 27 Nov 2026 10:00:00 +0000</pubDate></item>
<item><title>Old story</title><link>https://ex.org/b</link>
  <pubDate>Mon, 23 Nov 2026 10:00:00 +0000</pubDate></item>
<item><title>No date</title><link>https://ex.org/c?traffic_source=rss</link></item>
</channel></rss>"""
ATOM = """<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>Atom one</title><link rel="replies" href="https://ex.org/x/comments"/>
  <link rel="alternate" href="https://ex.org/x"/><updated>2026-11-27T08:30:00Z</updated></entry>
</feed>"""
JSONFEED = '{"version": "https://jsonfeed.org/version/1.1", "items": [' \
           '{"title": "J", "url": "https://ex.org/j", "date_published": "2026-11-27T09:00:00+01:00"}]}'

ARTICLE = """<html><body>
<div class="site-menu"><a>Wirtschaft</a> Untermenü einblenden <a>Sport</a></div>
<nav>Home | World | Sport</nav>
<article><header><h1>EU summit ends early</h1></header>
<p>Leaders broke off the budget summit a day early. """ + "More detail follows here. " * 30 + """</p>
<aside class="related">Related: other stories</aside>
<div class="share-bar">Share on X</div>
<p>They meet again on 17 December.</p></article>
<footer>Impressum</footer><script>var x = 1;</script></body></html>"""


def _run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = feeds.main(argv)
    return rc, out.getvalue()


class TitlesTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def _f(self, name, body):
        p = os.path.join(self.d, name)
        with open(p, "w") as fh:
            fh.write(body)
        return p

    def test_window_keeps_undated_and_strips_tracking(self):
        p = self._f("srf.xml", RSS)
        rc, out = _run(["titles", "--since", "2026-11-26T00:00:00Z", p])
        self.assertEqual(rc, 0)
        lines = out.splitlines()
        self.assertEqual(lines[0], "== srf: 2/3 in window")
        self.assertIn("2026-11-27 10:00 | Fresh story | https://ex.org/a?id=7", lines)
        self.assertIn("undated | No date | https://ex.org/c", lines)
        self.assertNotIn("Old story", out)

    def test_atom_alternate_link_and_json_feed(self):
        rc, out = _run(["titles", self._f("a.xml", ATOM), self._f("j.json", JSONFEED)])
        self.assertIn("2026-11-27 08:30 | Atom one | https://ex.org/x", out)
        self.assertIn("2026-11-27 08:00 | J | https://ex.org/j", out)  # +01:00 shown in UTC

    def test_max_caps_newest_first(self):
        rc, out = _run(["titles", "--max", "1", self._f("srf.xml", RSS)])
        lines = out.splitlines()
        self.assertEqual(lines[0], "== srf: 3/3 in window, showing 1")
        self.assertTrue(lines[1].startswith("undated |"))  # undated sorts as now: newest

    def test_unreadable_file_is_reported_not_raised(self):
        rc, out = _run(["titles", self._f("bad.xml", "<html><p>not a feed"),
                        os.path.join(self.d, "missing.xml")])
        self.assertEqual(rc, 0)
        self.assertEqual(out.count("unreadable"), 2)


class TextTest(unittest.TestCase):
    def test_article_without_chrome_keeps_headline(self):
        t = feeds.extract_text(ARTICLE)
        self.assertTrue(t.startswith("EU summit ends early"))
        self.assertIn("They meet again on 17 December.", t)
        for chrome in ("Untermenü", "Home | World", "Related:", "Share on X", "Impressum", "var x"):
            self.assertNotIn(chrome, t)

    def test_short_region_falls_back_to_page_text(self):
        page = "<html><body><article><p>Teaser.</p></article><div>" + "Body text. " * 60 + "</div></body></html>"
        t = feeds.extract_text(page)
        self.assertIn("Body text.", t)  # body region wins over a 7-character article
        tiny = "<html><body><p>Only a line.</p></body></html>"
        self.assertEqual(feeds.extract_text(tiny), "Only a line.")

    def test_cut_marker(self):
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as fh:
            fh.write(ARTICLE)
        try:
            rc, out = _run(["text", "--max", "100", fh.name])
        finally:
            os.unlink(fh.name)
        self.assertRegex(out.strip().splitlines()[-1], r"^\[\.\.\. cut at 100 of \d+ characters\]$")


if __name__ == "__main__":
    unittest.main()
