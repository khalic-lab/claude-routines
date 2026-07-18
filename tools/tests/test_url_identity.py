#!/usr/bin/env python3
"""Spec tests for the two URL-identity fixes from the 2026-07-18 external audit follow-up.

1. dedup.canon_url keeps DISCRIMINATING query params: an exact-key hit marks a repeat
   unconditionally (no cosine backstop), so a query-blind key falsely collides stories a
   query-keyed CMS distinguishes only by query (watch?v=, article.php?id=) and silently
   drops genuinely new coverage. Tracking params still normalize away.

2. build_stories_feed homepage URL dedup keeps the NEWEST telling: the window iterates
   oldest->newest and used to keep the first (oldest) card for a re-cited primary URL, so
   an ONGOING update's fresher prose never reached the page.
"""
import importlib.util
import os
import shutil
import tempfile
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(TOOLS, rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


dedup = _load("_dedup_urlid", "dedup/dedup.py")
bsf = _load("_bsf_urlid", "build_stories_feed.py")


class CanonUrlTest(unittest.TestCase):
    def test_query_distinguished_stories_get_distinct_keys(self):
        a = dedup.canon_url("https://site.example/article.php?id=1")
        b = dedup.canon_url("https://site.example/article.php?id=2")
        self.assertNotEqual(a, b, "query-keyed CMS stories must not collide")
        self.assertEqual(a, "site.example/article.php?id=1")

    def test_tracking_params_still_normalize_away(self):
        bare = dedup.canon_url("https://www.site.example/story/")
        tracked = dedup.canon_url(
            "http://site.example/story?utm_source=x&ref=rss&fbclid=abc#frag")
        self.assertEqual(bare, tracked)
        self.assertEqual(bare, "site.example/story")

    def test_param_order_is_identity_insensitive(self):
        self.assertEqual(dedup.canon_url("https://x.example/w?a=1&b=2"),
                         dedup.canon_url("https://x.example/w?b=2&a=1"))

    def test_mixed_tracking_and_real_params(self):
        self.assertEqual(dedup.canon_url("https://y.example/v?utm_medium=m&v=abc123"),
                         "y.example/v?v=abc123")

    def test_exact_keys_still_require_a_path(self):
        # bare host (+ query) is not a story identity -- unchanged contract
        self.assertEqual(
            [k for k in dedup.exact_keys("H", "S", "https://site.example") if k.startswith("url:")],
            [])


def _post(headline, url):
    return ("---\ntitle: x\n---\n\n## World\n\n- **%s** A neutral summary sentence "
            "about the story. ([Source](%s))\n" % (headline, url))


class FeedNewestWinsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="feed-dedup-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.posts = os.path.join(self.tmp, "posts")
        self.index = os.path.join(self.tmp, "index")
        os.makedirs(self.posts)
        os.makedirs(self.index)
        for attr, val in (("POSTS_DIR", self.posts), ("INDEX_DIR", self.index)):
            self.addCleanup(setattr, bsf, attr, getattr(bsf, attr))
            setattr(bsf, attr, val)

    def _write(self, name, text):
        with open(os.path.join(self.posts, name), "w") as fh:
            fh.write(text)

    def test_newer_edition_supersedes_older_card_for_same_url(self):
        url = "https://example.com/ongoing-story"
        self._write("2026-07-10-news.md", _post("Old telling.", url))
        self._write("2026-07-12-news.md", _post("New telling.", url))
        stories, _, _ = bsf.load_recent(days=14)
        hits = [s for s in stories if s["url"] == url]
        self.assertEqual(len(hits), 1, "one card per primary URL")
        self.assertEqual(hits[0]["date"], "2026-07-12")
        self.assertEqual(hits[0]["headline"], "New telling")  # parser strips the period

    def test_same_date_cross_stream_repeat_keeps_first(self):
        url = "https://example.com/shared-story"
        self._write("2026-07-12-news.md", _post("News telling.", url))
        self._write("2026-07-12-science.md", _post("Science telling.", url))
        stories, _, _ = bsf.load_recent(days=14)
        hits = [s for s in stories if s["url"] == url]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["stream"], "news")

    def test_distinct_urls_are_untouched(self):
        self._write("2026-07-10-news.md", _post("One.", "https://a.example/1"))
        self._write("2026-07-12-news.md", _post("Two.", "https://b.example/2"))
        stories, _, _ = bsf.load_recent(days=14)
        self.assertEqual(len(stories), 2)


if __name__ == "__main__":
    unittest.main()
