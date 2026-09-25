#!/usr/bin/env python3
"""Spec tests for the story parser's citation handling (build_stories_feed.parse_post), 2026-09-25.

THE BUG. A news story closing on two sources joined by a middot ("[Euronews, 25.09.2026](u) · [SRF,
25.09.2026](u)") came back with an empty body: "25.09.2026" was not a date to the trailing-citation
walk, so the tail stayed in the paragraph, its middot and bare domains read as a byline, and
load_recent dropped the story without a word. 12 of 18 news stories on 23-25 Sep never reached the
page (24 Sep printed "1 STORY"). The same walk missed tails the ai-ml and weekend desks write
(undated links chained by middots, a trailing "([arXiv…](u) · `[preprint]`)"), and two byline
placements hid a paper story's prose. And a story whose prose the parser still cannot find now
keeps its card with the lede as body and a WARN line, instead of vanishing.

Fixtures are the real 2026-09-25 News lines 14 (two sources) and 18 (one source).
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
FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "citations")
spec = importlib.util.spec_from_file_location("_bsf_cites", os.path.join(TOOLS, "build_stories_feed.py"))
bsf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bsf)


def one(md_line, section="World"):
    stories = bsf.parse_post("## %s\n\n%s\n" % (section, md_line))
    assert len(stories) == 1, stories
    return stories[0]


def fixture(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as fh:
        return fh.read().rstrip("\n")


class NewsTwoSourceTailTest(unittest.TestCase):
    """_posts/2026-09-25-news.md:14, the reported line."""

    @classmethod
    def setUpClass(cls):
        cls.line = fixture("2026-09-25-news-line14.md")
        lede_end = cls.line.index("**", cls.line.index("**") + 2)
        cls.lede = cls.line[cls.line.index("**") + 2:lede_end]
        cls.prose = cls.line[lede_end + 2:cls.line.index(" Why it matters:")].strip()
        cls.why = cls.line[cls.line.index("Why it matters:") + len("Why it matters: "):cls.line.index(" [Euronews")]

    def test_the_full_headline_and_the_full_body_come_back(self):
        s = one(self.line)
        self.assertEqual(s["headline"], self.lede.rstrip("."))
        self.assertTrue(s["headline"].endswith("ballistic missiles at the kingdom"))
        self.assertEqual(s["body"], self.prose)
        self.assertTrue(s["body"].startswith("President Emmanuel Macron told French television"))
        self.assertEqual(s["why"], self.why)
        self.assertEqual(s["display_body"], "%s %s" % (self.lede, self.prose))
        self.assertEqual(s["url"], "https://www.euronews.com/2026/09/25/saudi-arabia-reports-fresh-houthi-attacks"
                                   "-as-france-offers-military-support-to-protect-yan")
        for field in ("body", "why", "display_body"):
            self.assertNotIn("25.09.2026", s[field], field)

    def test_three_sources_are_one_tail_too(self):
        three = self.line + " · [DW, 25.09.2026](https://www.dw.com/en/yanbu/a-1)"
        s = one(three)
        self.assertEqual((s["body"], s["why"]), (self.prose, self.why))

    def test_the_date_forms_a_citation_may_carry(self):
        for date in ("25.09.2026", "5.9.2026", "25 Sep 2026", "2026-09-25", "Sep 25, 2026"):
            text = "Prose ends here. [SRF, %s](https://srf.ch/a) · [DW, %s](https://dw.com/b)" % (date, date)
            self.assertEqual(bsf.strip_trailing_citations(text), "Prose ends here.", date)


class SingleSourceShapeTest(unittest.TestCase):
    """_posts/2026-09-25-news.md:18 parsed fine before the fix; it must parse the same after,
    except that the trailing "DW, 24.09.2026" is no longer printed as part of `why`."""

    def test_line_18(self):
        line = fixture("2026-09-25-news-line18.md")
        s = one(line)
        self.assertTrue(s["headline"].startswith("Fighting between Ethiopia's federal army"))
        self.assertTrue(s["body"].startswith("The clashes first broke out on Wednesday 23 September"))
        self.assertTrue(s["body"].endswith("have called for restraint and de-escalation."))
        self.assertEqual(s["why"], "a collapse of the Pretoria agreement risks reopening one of the deadliest "
                                   "conflicts of the past decade and could destabilise the wider Horn of Africa.")
        self.assertEqual(s["url"], "https://www.dw.com/en/ethiopia-s-military-says-it-killed-hundreds-of-tplf-rebels/a-79419173")


class OtherTailShapesTest(unittest.TestCase):
    PROSE = ("The model is an open-weights sparse mixture-of-experts that claims to run in under three "
             "gibibytes of active memory by streaming experts off the SSD.")

    # `body` keeps the delinked sources it always kept (golden-feed pins it); the printed
    # `display_body` is the one that drops the citation run, and both must be found at all.
    def check(self, s, lede):
        self.assertTrue(s["body"].startswith(self.PROSE), s["body"])
        self.assertEqual(s["display_body"], "%s. %s" % (lede, self.PROSE))

    def test_undated_links_chained_to_a_dated_one(self):      # 2026-09-15-ai-ml
        s = one("- **Edge0 runs a 35B MoE in phone-class memory** — %s [Model card, updated 14 Sep 2026]"
                "(https://huggingface.co/x) · [framework](https://github.com/y)" % self.PROSE, "Releases")
        self.check(s, "Edge0 runs a 35B MoE in phone-class memory")

    def test_an_all_undated_chain_after_a_sentence(self):      # 2026-08-01-weekend
        s = one("- **DeepSeek-V4-Flash-0731** — %s `[vendor PR]` [Hugging Face model card](https://hf.co/a)"
                " · [GGUF port](https://hf.co/b)" % self.PROSE, "Models")
        self.check(s, "DeepSeek-V4-Flash-0731")

    def test_a_trailing_parenthetical_of_sources(self):       # 2026-08-15-weekend, 2026-09-14-news
        s = one("- **Intern-S2-Preview** — %s ([arXiv:2608.13505](https://arxiv.org/abs/2608.13505) · "
                "`[preprint]`)" % self.PROSE, "Models")
        self.check(s, "Intern-S2-Preview")
        text = "It shapes the bar. ([Schweizer Parlament, Herbstsession 2026](https://a) ; [SRF, 14.09.2026](https://b))"
        self.assertEqual(bsf.strip_trailing_citations(text), "It shapes the bar.")

    def test_prose_links_stay(self):
        self.assertEqual(bsf.strip_trailing_citations("It released [the full report](https://a)."),
                         "It released [the full report](https://a).")
        keep = "The code is on [GitHub](https://g) · [Paper, 2026-07-01](https://p)"
        self.assertEqual(bsf.strip_trailing_citations(keep), "The code is on [GitHub](https://g)")
        self.assertEqual(bsf.strip_trailing_citations("Read [the thread](https://t) and [the paper](https://p)"),
                         "Read [the thread](https://t) and [the paper](https://p)")


class BylinePlacementTest(unittest.TestCase):
    BODY = ("TabPFN is unusual: rather than being trained on your table, it is pretrained once so it "
            "can predict on a new tabular dataset in a single forward pass.")

    def test_a_byline_written_into_the_line(self):            # 2026-09-19-weekend TabPFN
        s = one("- **TabPFN-3.5** — the tabular-data foundation model line got a major update. "
                "**[arXiv:2609.17895](https://arxiv.org/abs/2609.17895)** · Prior Labs · `[preprint]`. %s" % self.BODY,
                "Data science")
        self.assertEqual(s["body"], "the tabular-data foundation model line got a major update. " + self.BODY)

    def test_a_line_that_goes_on_with_more_apparatus_is_not_split(self):
        line = ("**[arXiv:2607.05193](https://arxiv.org/abs/2607.05193)** · K. Hoy, A. Zurlo et al. · "
                "`[preprint]` · (affiliation not listed) · `[disputed]`")
        self.assertIsNone(bsf._INLINE_BYLINE_RE.search(line))

    def test_a_cited_paper_as_the_subject_is_prose(self):      # 2026-09-05-weekend
        p = ("[arXiv:2608.31046](https://arxiv.org/abs/2608.31046) (Y. Ding, R. Zhang · Purdue · `[preprint]`) "
             "measured how reliable the teacher's dense scores actually are and found substantial noise.")
        self.assertFalse(bsf._is_meta(p))

    def test_two_papers_joined_by_and_are_still_a_byline(self):   # 2026-06-27-weekend guard
        p = ("**[arXiv:2606.25849](https://arxiv.org/abs/2606.25849)** (Problem 1061) and "
             "**[arXiv:2606.24872](https://arxiv.org/abs/2606.24872)** (Problem 768) · Eric Li (sole author, both) · `[preprint]`")
        self.assertTrue(bsf._is_meta(p))


class NothingDropsSilentlyTest(unittest.TestCase):
    """load_recent keeps a story whose prose cannot be found: its lede becomes the body and a
    WARN line names the post and the story id."""

    def test_the_story_is_kept_and_named(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root)
        os.makedirs(os.path.join(root, "_posts"))
        os.makedirs(os.path.join(root, "index", "stories"))
        with open(os.path.join(root, "_posts", "2026-09-25-news.md"), "w", encoding="utf-8") as fh:
            fh.write("---\ntitle: x\n---\n\n## World\n\n"
                     "- <a id=\"st-0123456789ab\" class=\"st-a\"></a>**A lede that is the whole story.** "
                     "[Source](https://example.org/a) · A. Author et al. · 2026\n\n"
                     "- **A normal story.** It has prose of its own, long enough to be a body. [SRF, 25.09.2026](https://srf.ch/b)\n")
        saved = (bsf.ROOT, bsf.POSTS_DIR, bsf.INDEX_DIR)
        bsf.ROOT, bsf.POSTS_DIR, bsf.INDEX_DIR = root, os.path.join(root, "_posts"), os.path.join(root, "index", "stories")
        try:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                stories, max_date, _ = bsf.load_recent(14)
        finally:
            bsf.ROOT, bsf.POSTS_DIR, bsf.INDEX_DIR = saved
        self.assertEqual(len(stories), 2, "no story may drop")
        lede = next(s for s in stories if s["sid"] == "st-0123456789ab")
        self.assertEqual(lede["summary"], "A lede that is the whole story")
        self.assertIn("WARN no body parsed: _posts/2026-09-25-news.md story st-0123456789ab", out.getvalue())
        self.assertNotIn("A normal story", out.getvalue())


if __name__ == "__main__":
    unittest.main()
