#!/usr/bin/env python3
"""Spec tests for the homefeed editorial extractor (build_stories_feed.py, 2026-07-18).

Contract: section-level synthesis prose ("Cross-cutting threads" / "Why it matters")
becomes feed["editorials"] cards. Regression anchors from the 2026-07-18 external audit:
  - Markdown rules (---/***/___) are separators, NEVER emitted as prose paragraphs
    (both live cards shipped a literal '---' paragraph).
  - Fenced code blocks are skipped, not flattened into prose.
  - '&' inside a linked URL is escaped exactly once (&amp;, never &amp;amp;).
"""
import importlib.util
import os
import shutil
import tempfile
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location(
    "_bsf", os.path.join(TOOLS, "build_stories_feed.py"))
bsf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bsf)


class HeadingTest(unittest.TestCase):
    def test_known_headings_normalize_through_emoji_and_hyphens(self):
        self.assertEqual(bsf._editorial_heading("## Cross-cutting threads"),
                         "Cross-cutting threads")
        self.assertEqual(bsf._editorial_heading("## 🧠 Cross-cutting threads"),
                         "Cross-cutting threads")
        self.assertEqual(bsf._editorial_heading("## Why it matters"), "Why it matters")

    def test_other_headings_and_non_headings_are_ignored(self):
        self.assertIsNone(bsf._editorial_heading("## Stories"))
        self.assertIsNone(bsf._editorial_heading("Cross-cutting threads"))


class ParagraphsTest(unittest.TestCase):
    def test_markdown_rules_are_separators_not_prose(self):
        paras = bsf._ed_paragraphs(["First point.", "", "---", "", "Second point.",
                                    "***", "___", "----"])
        self.assertEqual(paras, ["First point.", "Second point."])

    def test_trailing_rule_never_becomes_last_paragraph(self):
        # the exact live-bug shape: section body ends "prose, blank, ---"
        paras = bsf._ed_paragraphs(["Only point.", "", "---"])
        self.assertEqual(paras, ["Only point."])

    def test_fenced_code_is_skipped(self):
        paras = bsf._ed_paragraphs(["Before.", "", "```python",
                                    "# not a heading", "x = 1", "```", "After."])
        self.assertEqual(paras, ["Before.", "After."])

    def test_unmatched_fence_does_not_swallow_trailing_prose(self):
        """Adversarial-review catch: a stray ``` mid-prose must not silently drop every
        paragraph after it -- unclosed 'fence' content is prose, not code."""
        paras = bsf._ed_paragraphs(["Point one.", "", "```", "", "Point two."])
        self.assertEqual(paras, ["Point one.", "Point two."])

    def test_bullets_split_and_wrapped_lines_join(self):
        paras = bsf._ed_paragraphs(["- first bullet", "- second bullet",
                                    "", "wrapped", "line"])
        self.assertEqual(paras, ["first bullet", "second bullet", "wrapped line"])

    def test_cap(self):
        lines = []
        for i in range(9):
            lines += ["para %d" % i, ""]
        self.assertEqual(len(bsf._ed_paragraphs(lines)), 6)


class InlineHtmlTest(unittest.TestCase):
    def test_amp_in_linked_url_is_escaped_exactly_once(self):
        html = bsf._ed_inline_html("See [the paper](https://x.test/a?b=1&c=2).")
        self.assertIn('href="https://x.test/a?b=1&amp;c=2"', html)
        self.assertNotIn("&amp;amp;", html)

    def test_source_html_is_stripped_and_text_escaped(self):
        html = bsf._ed_inline_html('<a id="x"></a>Tools & **agents** win')
        self.assertNotIn("<a id", html)
        self.assertIn("Tools &amp; <strong>agents</strong> win", html)


class LoadEditorialsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ed-test-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self._orig = bsf.POSTS_DIR
        bsf.POSTS_DIR = self.tmp
        self.addCleanup(setattr, bsf, "POSTS_DIR", self._orig)

    def _post(self, name, body):
        with open(os.path.join(self.tmp, name), "w") as fh:
            fh.write("---\ntitle: x\n---\n" + body)

    def test_latest_edition_per_stream_wins_and_rules_are_dropped(self):
        self._post("2026-07-11-weekend.md",
                   "## 🧠 Cross-cutting threads\n\nOld take.\n\n---\n")
        self._post("2026-07-18-weekend.md",
                   "## 🧠 Cross-cutting threads\n\nNew take.\n\n---\n\n## Stories\n\nx\n")
        eds = bsf.load_editorials(days=14)
        self.assertEqual(len(eds), 1)
        self.assertEqual(eds[0]["date"], "2026-07-18")
        self.assertEqual(eds[0]["title"], "Cross-cutting threads")
        self.assertEqual(eds[0]["paras"], ["New take."])
        self.assertEqual(eds[0]["kicker"], "Weekend · Jul 18")

    def test_rule_only_section_yields_no_card(self):
        self._post("2026-07-18-science.md", "## Why it matters\n\n---\n")
        self.assertEqual(bsf.load_editorials(days=14), [])


if __name__ == "__main__":
    unittest.main()
