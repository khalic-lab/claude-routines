#!/usr/bin/env python3
"""Multi-source stories (2026-10-22): every story carries `sources`, one entry per distinct
domain it cites, primary first, and the page prints them all.

Before this the feed kept only the FIRST url of a story (`url` / `source_domain`), so a News
story sourced from DW, Le Monde and SRF read as sourced from DW alone -- 124 of the 511 stories
filed in October 2026 cited more than one outlet and the page named one. The builder now emits
`sources: [{url, domain, label}]`, the meta line prints every domain (alternates linked), the
Discuss link and the story RSS carry every URL. `url` and `source_domain` are unchanged: still
the first one, still the headline's link, still what the record join keys on.

Run: python3 -m unittest tools.tests.test_feed_sources
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(TESTS_DIR))
BUILD_FEED_PATH = os.path.join(REPO, "tools", "build_stories_feed.py")


def _mod(root=None):
    spec = importlib.util.spec_from_file_location("_bsf_sources_%d" % id(root), BUILD_FEED_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if root:
        mod.ROOT = root
        mod.POSTS_DIR = os.path.join(root, "_posts")
        mod.INDEX_DIR = os.path.join(root, "index", "stories")
        mod.DEFAULT_OUT = os.path.join(root, "_data", "homefeed.json")
    return mod


def _read(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as fh:
        return fh.read()


THREE_SOURCES = (
    "- **The UAE ordered a terrorism investigation into a Flydubai pilot.** The co-pilot tried "
    "to crash the jet, officials said. [DW, 1 Oct 2026](https://www.dw.com/en/uae-hijack/a-1) "
    "[DW, 1 Oct 2026](https://www.dw.com/en/flydubai-pilot/a-2) "
    "[Le Monde, 1 Oct 2026](https://www.lemonde.fr/international/article/2026/10/01/x.html) "
    "[SRF, 1 Oct 2026](https://www.srf.ch/news/international/vorfall?utm_source=t)"
)
PAPER_WITH_CODE = (
    "- **A retrieval paper cuts hallucination on multi-hop QA.** Code is released. "
    "([arXiv:2610.24872](https://arxiv.org/abs/2610.24872)) and https://github.com/lab/repo"
)
LINKLESS = "- **Local weather turns warm.** A ridge over the Alps persists through the week."

POST = "---\ntitle: \"News — 2026-10-01\"\n---\n\n## World\n\n%s\n\n%s\n\n%s\n\n## Coverage footer\n- footer [x](https://example.com/x)\n" % (
    THREE_SOURCES, PAPER_WITH_CODE, LINKLESS)


class StorySourcesTests(unittest.TestCase):
    def setUp(self):
        self.b = _mod()

    def test_one_entry_per_domain_in_prose_order_primary_first(self):
        s = self.b.parse_post(POST)[0]
        self.assertEqual([x["domain"] for x in s["sources"]], ["dw.com", "lemonde.fr", "srf.ch"])
        self.assertEqual(s["sources"][0]["url"], s["url"], "the primary is the first url, as before")
        self.assertEqual(s["sources"][0]["url"], "https://www.dw.com/en/uae-hijack/a-1",
                         "two DW pieces collapse to the first one")

    def test_label_is_the_citation_without_its_date(self):
        s = self.b.parse_post(POST)[0]
        self.assertEqual([x["label"] for x in s["sources"]], ["DW", "Le Monde", "SRF"])

    def test_bare_urls_count_and_a_label_falls_back_to_the_domain(self):
        s = self.b.parse_post(POST)[1]
        self.assertEqual([(x["domain"], x["label"]) for x in s["sources"]],
                         [("arxiv.org", "arXiv:2610.24872"), ("github.com", "github.com")])

    def test_a_linkless_story_has_an_empty_list(self):
        s = self.b.parse_post(POST)[2]
        self.assertEqual(s["sources"], [])
        self.assertIsNone(s["url"])

    def test_source_domain_matches_the_primary_entry(self):
        for s in self.b.parse_post(POST):
            if s["sources"]:
                self.assertEqual(self.b.source_domain(s["url"]), s["sources"][0]["domain"])

    def test_the_footer_is_never_a_source(self):
        for s in self.b.parse_post(POST):
            self.assertNotIn("example.com", [x["domain"] for x in s["sources"]])

    def test_story_sources_tolerates_empty_input(self):
        self.assertEqual(self.b.story_sources(""), [])
        self.assertEqual(self.b.story_sources(None), [])


class FeedCarriesSourcesTests(unittest.TestCase):
    """Through main(): the key is on feed.stories AND the board, absent (not []) when linkless,
    and `permalink` -- which pointed at pages retired on 2026-07-18 -- is gone."""

    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp(prefix="feedsrc-")
        for d in ("_posts", os.path.join("index", "stories"), "_data"):
            os.makedirs(os.path.join(cls.root, d))
        with open(os.path.join(cls.root, "_posts", "2026-10-01-news.md"), "w") as fh:
            fh.write(POST)
        mod = _mod(cls.root)
        old = sys.argv
        sys.argv = ["build_stories_feed.py", "--days", "3650", "--max", "0", "--out", mod.DEFAULT_OUT]
        try:
            mod.main()
        finally:
            sys.argv = old
        with open(mod.DEFAULT_OUT) as fh:
            cls.feed = json.load(fh)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def _by_url(self, items):
        return {s.get("url"): s for s in items}

    def test_stories_and_board_carry_the_same_sources(self):
        for items in (self.feed["stories"], [b for b in self.feed["board"] if b["kind"] == "story"]):
            by = self._by_url(items)
            self.assertEqual([x["domain"] for x in by["https://www.dw.com/en/uae-hijack/a-1"]["sources"]],
                             ["dw.com", "lemonde.fr", "srf.ch"])
            self.assertNotIn("sources", by[None], "a linkless story omits the key so Liquid can gate on it")

    def test_permalink_is_gone(self):
        for s in self.feed["stories"] + self.feed["board"]:
            self.assertNotIn("permalink", s)


class TemplateWiringTests(unittest.TestCase):
    """The page side, checked statically (tools/verify/suite.mjs renders; this does not)."""

    def test_meta_prints_every_domain_and_links_the_alternates(self):
        meta = _read("_includes/home/meta.html")
        self.assertIn("{% for src in s.sources %}", meta)
        self.assertIn('href="{{ src.url | escape }}"', meta)
        self.assertIn("{{ s.source_domain | escape }}", meta, "an old-shape feed still prints the primary")

    def test_discuss_is_a_plain_prefilled_link_on_stories_only(self):
        acts = _read("_includes/home/actions.html")
        self.assertIn('href="https://claude.ai/new?q={{ dq | url_encode | replace: "+", "%20" }}"', acts,
                      "spaces must travel as %20: a plus only decodes to a space under a form-style decoder")
        self.assertIn('rel="noopener noreferrer"', acts)
        self.assertNotIn('class="discuss needs-js"', acts, "Discuss must work without script")
        for inc in ("row.html", "front-card.html"):
            self.assertRegex(_read("_includes/home/" + inc), r"include home/actions\.html[^%]*\bs=s\b", inc)
        self.assertNotRegex(_read("_includes/home/editorial.html"), r"include home/actions\.html[^%]*\bs=",
                            "an AI editorial has no sources to discuss against")

    def test_the_prompt_carries_every_source_url(self):
        acts = _read("_includes/home/actions.html")
        i, j = acts.index("{%- capture dq -%}"), acts.index("{%- endcapture -%}")
        prompt = acts[i:j]
        self.assertIn("{% for src in st.sources %}", prompt)
        self.assertIn("{{ src.url }}", prompt)
        self.assertIn("{{ st.headline }}", prompt)

    def test_discuss_is_styled_inside_the_components_layer(self):
        css = _read("assets/css/components.css")
        self.assertIn(".discuss", css)
        self.assertIn("a.src__alt", css)


class StoryFeedTests(unittest.TestCase):
    """stories.xml: an RSS feed over the board, which /feed.xml never was (briefs are unpublished,
    so jekyll-feed only ever listed the Sunday reviews)."""

    def test_page_exists_with_null_layout_and_is_the_linked_feed(self):
        xml = _read("stories.xml")
        self.assertTrue(xml.startswith("---\nlayout: null\n"), "raw XML: no layout may wrap it")
        self.assertIn("sitemap: false", xml)
        self.assertIn('{%- if s.kind == "story" %}', xml)
        self.assertIn("{{ s.headline | xml_escape }}", xml)
        self.assertIn("{{ s.url | xml_escape }}", xml)
        self.assertIn("{{ desc | xml_escape }}", xml, "the HTML description is escaped once, as a whole")
        self.assertIn("<guid isPermaLink=\"false\">{{ s.sid | default: s.id | xml_escape }}</guid>", xml)
        self.assertIn("'/stories.xml' | relative_url", _read("_includes/colophon.html"))
        self.assertIn("'/stories.xml' | relative_url", _read("_includes/head.html"))

    def test_feed_is_excluded_from_nothing_but_the_sitemap(self):
        cfg = _read("_config.yml")
        self.assertNotRegex(cfg, r"(?m)^\s*-\s*stories\.xml")


if __name__ == "__main__":
    unittest.main()
