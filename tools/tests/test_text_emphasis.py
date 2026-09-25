#!/usr/bin/env python3
"""Spec tests for markdown emphasis in the story fields the homepage prints (review F6, 2026-09-25).

A story's deck, summary and why are printed as ESCAPED TEXT, so "_Released 22 September 2026._"
showed its underscores on the card. `plain_emphasis` drops the markers and keeps the words; it
must never touch an underscore that is part of a word, a URL or a code span. Editorials are
emitted as html and render the same emphasis as <em>. Headlines lose their markers too (owner OK,
2026-09-25), but no id is derived from the printed headline: urls, sids and ids stay byte-identical.
"""
import contextlib
import importlib.util
import io
import json
import os
import shutil
import tempfile
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("_bsf_emphasis", os.path.join(TOOLS, "build_stories_feed.py"))
bsf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bsf)


class PlainEmphasisTest(unittest.TestCase):
    def test_markers_go_and_words_stay(self):
        for src, want in (
            ("care about most. _Released 22 September 2026._", "care about most. Released 22 September 2026."),
            ("a Togo-flagged tanker, the _Trend_, for", "a Togo-flagged tanker, the Trend, for"),
            ("draft length _k_, acceptance", "draft length k, acceptance"),
            ("releases _(direct fetch)_", "releases (direct fetch)"),
            ("*it* and **bold** and **_both_**", "it and bold and both"),
            ("conflates _internal computation_ with _external_ ones", "conflates internal computation with external ones"),
        ):
            self.assertEqual(bsf.plain_emphasis(src), want, src)

    def test_words_urls_and_code_keep_their_underscores(self):
        for src in ("foo_bar_baz", "__init__ runs", "file_name.py", "_x_y_", "a_b_ c",
                    "see https://example.org/_a_/b", "`_k_` in code", "a * b * c", "2*3*4",
                    "_ spaced _", "no markers at all", "", None):
            self.assertEqual(bsf.plain_emphasis(src), src, src)

    def test_editorials_render_it_as_em(self):
        self.assertIn("<em>Trend</em>", bsf._ed_inline_html("the _Trend_, for"))


class StoryFieldsTest(unittest.TestCase):
    """Through load_recent: the recorded deck/body/why and the headline lose their markers, the
    parsed why too, and the url and ids come out exactly as before."""

    def _load(self, root):
        saved = (bsf.ROOT, bsf.POSTS_DIR, bsf.INDEX_DIR)
        bsf.ROOT, bsf.POSTS_DIR, bsf.INDEX_DIR = root, os.path.join(root, "_posts"), os.path.join(root, "index", "stories")
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                return bsf.load_recent(14)[0]
        finally:
            bsf.ROOT, bsf.POSTS_DIR, bsf.INDEX_DIR = saved

    def _tree(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root)
        os.makedirs(os.path.join(root, "_posts"))
        os.makedirs(os.path.join(root, "index", "stories"))
        with open(os.path.join(root, "_posts", "2026-09-25-news.md"), "w") as fh:
            fh.write("---\ntitle: x\n---\n\n## World\n\n"
                     "- **Five employees formally charged (_prévenus_) after the collapse.** A body long enough "
                     "to be the prose of the story, and then some more. [SRF, 25 Sep 2026](https://srf.ch/a_b)\n"
                     "  **Why it matters:** the _first_ charges in the case.\n"
                     "- **A tanker is seized.** Another body that is certainly long enough to be kept as prose. "
                     "[DW, 25 Sep 2026](https://dw.com/tanker)\n")
        rec = {"id": "2026-09-25-news-a-tanker-is-seized", "url": "https://dw.com/tanker", "topics": ["world"],
               "importance": 2, "headline": "A tanker is seized", "deck": "*Seized* at sea",
               "display_body": "Forces seized the _Trend_, a tanker.", "why": "It matters. _Released 22 September 2026._"}
        with open(os.path.join(root, "index", "stories", "2026-09-25-news.jsonl"), "w") as fh:
            fh.write(json.dumps(rec) + "\n")
        return root

    def test_printed_fields(self):
        first, tanker = self._load(self._tree())
        self.assertEqual(first["why"], "the first charges in the case.")
        self.assertEqual(first["headline"], "Five employees formally charged (prévenus) after the collapse")
        self.assertEqual(first["url"], "https://srf.ch/a_b")
        self.assertTrue(first["id"].startswith("2026-09-25-news-five-employees"))
        self.assertEqual(tanker["deck"], "Seized at sea")
        self.assertEqual(tanker["summary"], "Forces seized the Trend, a tanker.")
        self.assertEqual(tanker["why"], "It matters. Released 22 September 2026.")

    def test_ids_do_not_see_the_printed_headline(self):
        """The 2026-07-31 "(_prévenus_)" shape: with the markers kept (plain_emphasis off) and
        stripped, every id, sid and url is byte-identical; only the printed text differs."""
        root = self._tree()
        real = bsf.plain_emphasis
        bsf.plain_emphasis = lambda t: t
        try:
            kept = self._load(root)
        finally:
            bsf.plain_emphasis = real
        clean = self._load(root)
        for k in ("id", "sid", "url", "date", "stream", "permalink"):
            self.assertEqual([s[k] for s in kept], [s[k] for s in clean], k)
        self.assertIn("(_prévenus_)", kept[0]["headline"])
        self.assertNotIn("_", clean[0]["headline"])


if __name__ == "__main__":
    unittest.main()
