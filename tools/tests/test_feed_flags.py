#!/usr/bin/env python3
"""Credibility flags and source counts on the board (2026-10-22).

The writers mark doubt inline (`[preprint]`, `[single-source]`, `[disputed]`, `[ongoing since …]`)
and the dedup record keeps the same marks in `tags`; `clean_body` strips them from the prose and
nothing on the page showed them, although "How this works" promises they are labelled. The
builder now merges the record's tags with the tags in the prose, normalises them, keeps only the
fixed FLAGS vocabulary in its fixed order and emits `flags: [{key, label}]` on BOARD stories
(absent when empty), plus `n_sources`, the count of distinct outlets a story cites.
`feed.stories` is untouched: its keys are pinned by the golden.

Run: python3 -m unittest tools.tests.test_feed_flags
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
    spec = importlib.util.spec_from_file_location("_bsf_flags_%d" % id(root), BUILD_FEED_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if root:
        mod.ROOT = root
        mod.POSTS_DIR = os.path.join(root, "_posts")
        mod.INDEX_DIR = os.path.join(root, "index", "stories")
        mod.DEFAULT_OUT = os.path.join(root, "_data", "homefeed.json")
    return mod


class NormFlagTests(unittest.TestCase):
    def setUp(self):
        self.b = _mod()

    def test_record_and_prose_spellings_map_to_one_key(self):
        n = self.b.norm_flag
        for raw in ("preprint", "[preprint]", "`[preprint]`", "Preprint", "  PREPRINT "):
            self.assertEqual(n(raw), "preprint", raw)
        self.assertEqual(n("single-source"), "single-source")
        self.assertEqual(n("single source"), "single-source")
        self.assertEqual(n("vendor PR"), "vendor-pr")
        self.assertEqual(n("official pr"), "official-pr")
        self.assertEqual(n("rumor"), "rumour")

    def test_ongoing_since_a_date_is_ongoing(self):
        self.assertEqual(self.b.norm_flag("ongoing since 2026-10-03"), "ongoing")
        self.assertEqual(self.b.norm_flag("[ongoing since 3 Oct]"), "ongoing")

    def test_anything_outside_the_vocabulary_is_dropped(self):
        for raw in ("new source", "via snippet", "football", "f1", "", None, 42, ["preprint"]):
            self.assertIsNone(self.b.norm_flag(raw), repr(raw))


class StoryFlagsTests(unittest.TestCase):
    def setUp(self):
        self.b = _mod()

    def test_union_of_record_and_prose_in_fixed_order_without_repeats(self):
        got = self.b.story_flags("A claim. [single-source] More `[preprint]` text.",
                                 ["ongoing since 2026-10-01", "disputed", "new source", "preprint"])
        self.assertEqual([f["key"] for f in got], ["single-source", "disputed", "preprint", "ongoing"])
        self.assertEqual([f["label"] for f in got], ["Single source", "Disputed", "Preprint", "Ongoing"])

    def test_the_order_is_the_vocabulary_not_the_input(self):
        keys = [k for k, _ in self.b.FLAGS]
        got = self.b.story_flags("", list(reversed(keys)))
        self.assertEqual([f["key"] for f in got], keys)

    def test_junk_records_never_raise(self):
        self.assertEqual(self.b.story_flags("", None), [])
        self.assertEqual(self.b.story_flags(None, 42), [])
        self.assertEqual(self.b.story_flags("", {"preprint": 1}), [])
        self.assertEqual([f["key"] for f in self.b.story_flags("", "preprint")], ["preprint"],
                         "a bare string is one tag")
        self.assertEqual([f["key"] for f in self.b.story_flags("", [None, 3, "disputed"])], ["disputed"])

    def test_the_prose_tags_clean_body_strips_are_the_ones_counted(self):
        raw = "Fact. [unconfirmed] [rumour] Why it matters: x. [DW, 1 Oct 2026](https://www.dw.com/a)"
        self.assertEqual([f["key"] for f in self.b.story_flags(raw, None)], ["unconfirmed", "rumour"])
        self.assertNotIn("[unconfirmed]", self.b.clean_body(raw))
        self.assertNotIn("[rumour]", self.b.clean_body(raw))


FLAGGED = (
    "- **A tanker hit a mine south of Hormuz, the Guards said.** No independent confirmation. "
    "[single-source] [Le Temps (AFP), 21 Oct 2026](https://www.letemps.ch/a) "
    "[DW, 21 Oct 2026](https://www.dw.com/b)"
)
PLAIN = "- **A second story with two sources.** Body. [A, 1 Oct 2026](https://a.example/1) [B, 1 Oct 2026](https://b.example/2)"
LINKLESS = "- **Local weather turns warm.** A ridge over the Alps persists through the week."
POST = "---\ntitle: \"News — 2026-10-21\"\n---\n\n## World\n\n%s\n\n%s\n\n%s\n" % (FLAGGED, PLAIN, LINKLESS)


class BoardCarriesFlagsTests(unittest.TestCase):
    """Through main(): flags and n_sources on the board, not on feed.stories; a record's tags
    join the prose's; an unflagged story has no `flags` key at all (Liquid gates on the key)."""

    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp(prefix="feedflags-")
        for d in ("_posts", os.path.join("index", "stories"), "_data"):
            os.makedirs(os.path.join(cls.root, d))
        with open(os.path.join(cls.root, "_posts", "2026-10-21-news.md"), "w") as fh:
            fh.write(POST)
        # the record for the second story carries tags the prose does not, one of them junk
        rec = {"id": "x", "date": "2026-10-21", "stream": "news", "url": "https://a.example/1",
               "headline": "A second story with two sources", "tags": ["vendor PR", "new source", "[preprint]"]}
        with open(os.path.join(cls.root, "index", "stories", "2026-10-21-news.jsonl"), "w") as fh:
            fh.write(json.dumps(rec) + "\n")
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

    def _board(self):
        return {b.get("url"): b for b in self.feed["board"] if b["kind"] == "story"}

    def test_board_stories_carry_flags_and_counts(self):
        by = self._board()
        self.assertEqual([f["key"] for f in by["https://www.letemps.ch/a"]["flags"]], ["single-source"])
        self.assertEqual(by["https://www.letemps.ch/a"]["n_sources"], 2)
        self.assertEqual([f["key"] for f in by["https://a.example/1"]["flags"]], ["preprint", "vendor-pr"],
                         "the record's tags count, normalised, junk dropped")
        self.assertNotIn("flags", by[None], "an unflagged story omits the key")
        self.assertEqual(by[None]["n_sources"], 0)

    def test_feed_stories_keep_their_pinned_keys(self):
        for s in self.feed["stories"]:
            self.assertNotIn("flags", s)
            self.assertNotIn("n_sources", s)


if __name__ == "__main__":
    unittest.main()
