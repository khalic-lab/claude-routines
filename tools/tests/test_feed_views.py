#!/usr/bin/env python3
"""Spec tests for the homepage view layer in build_stories_feed.py (2026-09-24 day-edition page).

The page prints; the builder decides. These pin every decision the template no longer makes:
edition periods (the owner's "say which period it covers"), the front selection, editorial
headings and beat topics, headline punctuation, image eligibility, the days view the page slices
the board with, and the build stamp the page's freshness check compares.

The builder runs inside every writer sandbox at every fire, so the last class runs the real CLI
under `python3 -S` (no site-packages: PyYAML and friends cannot be imported) over sparse and odd
`_posts/` trees, and requires it never to raise.
"""
import datetime as dt
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("_bsf_views", os.path.join(TOOLS, "build_stories_feed.py"))
bsf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bsf)


def _posts_dir(names, body=None):
    """A temp _posts/ holding empty files with these names (filenames are all edition_dates reads)."""
    d = tempfile.mkdtemp()
    for n in names:
        with open(os.path.join(d, n), "w") as fh:
            fh.write(body if body is not None else "")
    return d


class EditionPeriodTest(unittest.TestCase):
    def period(self, date, stream, dates):
        return bsf.edition_period(date, stream, {stream: sorted(dates)})

    def test_weekly_desk_starts_the_day_after_its_previous_edition(self):
        self.assertEqual(self.period("2026-09-23", "science", ["2026-09-16", "2026-09-23"]),
                         ("2026-09-17", "2026-09-23"))

    def test_weekly_desk_is_capped_at_seven_days_across_a_gap(self):
        # previous Science edition three weeks back: the prompt still only covers "the past 7 days"
        self.assertEqual(self.period("2026-09-23", "science", ["2026-09-02", "2026-09-23"]),
                         ("2026-09-17", "2026-09-23"))

    def test_news_is_one_day_even_after_a_missed_day(self):
        self.assertEqual(self.period("2026-09-24", "news", ["2026-09-21", "2026-09-24"]),
                         ("2026-09-24", "2026-09-24"))

    def test_ai_ml_is_uncapped_since_its_last_edition(self):
        self.assertEqual(self.period("2026-09-22", "ai-ml", ["2026-09-18", "2026-09-22"]),
                         ("2026-09-19", "2026-09-22"))
        # a long silence stays uncapped: "since the last AI/ML edition"
        self.assertEqual(self.period("2026-09-22", "ai-ml", ["2026-08-30", "2026-09-22"]),
                         ("2026-08-31", "2026-09-22"))

    def test_first_ever_edition_starts_at_the_cap_or_on_the_day(self):
        self.assertEqual(self.period("2026-09-21", "sports", ["2026-09-21"]), ("2026-09-15", "2026-09-21"))
        self.assertEqual(self.period("2026-09-22", "ai-ml", ["2026-09-22"]), ("2026-09-22", "2026-09-22"))
        self.assertEqual(self.period("2026-09-24", "news", []), ("2026-09-24", "2026-09-24"))

    def test_unknown_stream_is_uncapped(self):
        self.assertEqual(bsf.edition_period("2026-09-24", "radio", {"radio": ["2026-09-20"]}),
                         ("2026-09-21", "2026-09-24"))

    def test_later_editions_do_not_move_an_earlier_period(self):
        self.assertEqual(self.period("2026-09-16", "science", ["2026-09-09", "2026-09-16", "2026-09-23"]),
                         ("2026-09-10", "2026-09-16"))

    def test_the_caps_are_the_routine_prompts_windows(self):
        """PERIOD_CAP_DAYS mirrors "Coverage window: ..." in routines/src/<stream>.md; a prompt
        edit that changes the window must change the cap too."""
        want = {"news": "the last ~24 hours", "science": "the past 7 days", "weekend": "past 7 days",
                "sports": "the past 7 days", "ai-ml": "since the last AI/ML edition"}
        src = os.path.join(os.path.dirname(TOOLS), "routines", "src")
        for stream, phrase in want.items():
            with open(os.path.join(src, stream + ".md"), encoding="utf-8") as fh:
                self.assertIn("Coverage window: " + phrase, fh.read(), stream)
        self.assertEqual(bsf.PERIOD_CAP_DAYS,
                         {"news": 1, "science": 7, "weekend": 7, "sports": 7, "ai-ml": None})

    def test_edition_dates_reads_writer_filenames_only(self):
        d = _posts_dir(["2026-09-23-science.md", "2026-09-16-science.md", "2026-09-20-evaluator.md",
                        "notes.md", "2026-09-24-news.md"])
        try:
            self.assertEqual(bsf.edition_dates(d), {"science": ["2026-09-16", "2026-09-23"],
                                                    "news": ["2026-09-24"]})
        finally:
            shutil.rmtree(d)


class PeriodViewTest(unittest.TestCase):
    def test_shapes(self):
        self.assertEqual(bsf.period_view("2026-09-24", "2026-09-24"),
                         {"start": "2026-09-24", "end": "2026-09-24", "start_text": "",
                          "end_text": "24 Sep", "label": "24 Sep"})
        self.assertEqual(bsf.period_view("2026-09-17", "2026-09-23")["label"], "17–23 Sep")
        self.assertEqual(bsf.period_view("2026-09-17", "2026-09-23")["start_text"], "17")
        self.assertEqual(bsf.period_view("2026-08-29", "2026-09-04")["label"], "29 Aug–4 Sep")
        self.assertEqual(bsf.period_view("2025-12-29", "2026-01-04")["label"], "29 Dec 2025–4 Jan")


class HeadlineDotTest(unittest.TestCase):
    def test_terminal_punctuation(self):
        self.assertTrue(bsf.hl_dot("Baltics sanction Russian oligarchs"))
        self.assertFalse(bsf.hl_dot("Is the fixed price real?"))
        self.assertFalse(bsf.hl_dot("It worked!"))
        self.assertFalse(bsf.hl_dot("He said “no.”"))
        self.assertTrue(bsf.hl_dot("The “fixed price”"))
        self.assertFalse(bsf.hl_dot(""))
        self.assertFalse(bsf.hl_dot(None))


class EditorialHeadingTest(unittest.TestCase):
    def ed(self, title="", paras=None, stream="weekend", date="2026-09-19"):
        return {"title": title, "paras": paras if paras is not None else [], "stream": stream, "date": date}

    def test_titled_editorial_prints_its_title_escaped(self):
        html, lede, body = bsf.editorial_heading(self.ed("Precision & isolation", ["One.", "Two."]))
        self.assertEqual((html, lede, body), ("Precision &amp; isolation", False, ["One.", "Two."]))

    def test_titleless_promotes_the_whole_lede_and_strips_the_number(self):
        paras = ["<strong>1. The week's real AI frontier was trust, not capability — and a long tail</strong> Rest of it.",
                 "<strong>2. Second.</strong> More."]
        html, lede, body = bsf.editorial_heading(self.ed(paras=paras))
        self.assertTrue(lede)
        self.assertEqual(html, "The week's real AI frontier was trust, not capability — and a long tail")
        self.assertEqual(body, ["Rest of it.", "<strong>2. Second.</strong> More."])

    def test_a_lede_that_is_the_whole_paragraph_leaves_no_empty_paragraph(self):
        html, lede, body = bsf.editorial_heading(self.ed(paras=["<strong>Only a lede.</strong>", "Next."]))
        self.assertEqual((html, body), ("Only a lede.", ["Next."]))

    def test_a_decimal_lede_keeps_its_figure(self):
        """Only a list number ("1. ", dot then space) is stripped; "3.5 million" is not "5 million"."""
        html, _, body = bsf.editorial_heading(self.ed(paras=["<strong>3.5 million people moved.</strong> Rest."]))
        self.assertEqual((html, body), ("3.5 million people moved.", ["Rest."]))
        html, _, _ = bsf.editorial_heading(self.ed(paras=["<strong>2.6-million-year-old jaw found.</strong>"]))
        self.assertEqual(html, "2.6-million-year-old jaw found.")

    def test_a_decimal_lede_survives_the_whole_pipeline(self):
        """Markdown in, heading out: _ed_title leaves an over-cap lede in the prose, _ed_paragraphs
        renders it, editorial_heading promotes it -- the figure must arrive whole."""
        lede = "3.5 million people moved this week, and this lede runs well past the ninety-character title cap"
        self.assertGreater(len(lede), bsf.ED_TITLE_CAP)
        title, lines = bsf._ed_title(["**%s.** Rest of it." % lede])
        self.assertEqual(title, "")
        html, promoted, body = bsf.editorial_heading(self.ed(paras=bsf._ed_paragraphs(lines)))
        self.assertTrue(promoted)
        self.assertEqual((html, body), (lede + ".", ["Rest of it."]))

    def test_punctuation_just_outside_the_bold_goes_with_the_lede(self):
        for mark in (".", ":"):
            _, _, body = bsf.editorial_heading(self.ed(paras=["<strong>A long lede</strong>%s As agents move." % mark]))
            self.assertEqual(body, ["As agents move."], mark)

    def test_no_title_and_no_lede_names_the_desk_and_day(self):
        html, lede, body = bsf.editorial_heading(self.ed(paras=["Plain opening.", "More."], stream="science",
                                                         date="2026-09-23"))
        self.assertEqual((html, lede, body), ("Science desk, Wed 23 Sep", True, ["Plain opening.", "More."]))


def _story(date, imp, stream="news", topics=("world",), headline="h", url="https://example.com/a",
           topic_label="World"):
    return {"kind": "story", "date": date, "importance": imp, "stream": stream, "topics": list(topics),
            "headline": headline, "url": url, "topic_label": topic_label, "sid": "st-%012d" % abs(hash((date, imp, headline)) % 10 ** 12)}


def _ed(date, stream="science", title="T", paras=("Body.",)):
    return {"kind": "editorial", "date": date, "stream": stream, "title": title, "paras": list(paras)}


class SelectFrontTest(unittest.TestCase):
    def test_lead_first_then_leads_and_features_in_board_order(self):
        b = [_story("2026-09-24", 1, headline="brief"),
             _story("2026-09-23", 3, headline="lead"), _story("2026-09-23", 2, headline="f1"),
             _story("2026-09-23", 2, headline="f2"), _story("2026-09-23", 2, headline="f3"),
             _story("2026-09-23", 2, headline="f4"), _ed("2026-09-23")]
        self.assertEqual(bsf.select_front(b), [1, 2, 3, 4])

    def test_no_lead_takes_the_first_story(self):
        b = [_story("2026-09-24", 2, headline="a"), _story("2026-09-24", 2, headline="b"),
             _story("2026-09-24", 1, headline="c"), _story("2026-09-24", 2, headline="d"),
             _story("2026-09-24", 2, headline="e")]
        self.assertEqual(bsf.select_front(b), [0, 1, 3, 4])

    def test_too_few_leads_and_features_briefs_fill_in(self):
        b = [_story("2026-09-24", 3, headline="lead"), _story("2026-09-24", 1, headline="b1"),
             _story("2026-09-23", 1, headline="b2"), _story("2026-09-23", 2, headline="f")]
        self.assertEqual(bsf.select_front(b), [0, 3, 1, 2])

    def test_walks_back_only_until_the_window_is_full(self):
        b = [_story("2026-09-24", 3), _story("2026-09-24", 2, headline="x"), _story("2026-09-24", 2, headline="y"),
             _story("2026-09-24", 2, headline="z"), _story("2026-09-23", 3, headline="older lead")]
        self.assertEqual(bsf.select_front(b), [0, 1, 2, 3])

    def test_single_date_editorial_only_and_empty_boards(self):
        self.assertEqual(bsf.select_front([_story("2026-09-24", 1)]), [0])
        self.assertEqual(bsf.select_front([_ed("2026-09-24"), _ed("2026-09-23", "sports")]), [])
        self.assertEqual(bsf.select_front([]), [])


class BuildViewsTest(unittest.TestCase):
    def setUp(self):
        self.posts = _posts_dir(["2026-09-16-science.md", "2026-09-23-science.md", "2026-09-23-news.md",
                                 "2026-09-22-news.md", "2026-09-22-ai-ml.md", "2026-09-18-ai-ml.md"])
        self.addCleanup(shutil.rmtree, self.posts)
        self.topics = [{"key": k, "label": k.title(), "color": "#000", "count": 1}
                       for k in ("science", "health", "world", "ai-ml", "switzerland")]
        self.board = [
            _story("2026-09-23", 3, "science", ("science", "health"), "lead", "https://www.nature.com/x", "Science"),
            _story("2026-09-23", 2, "news", ("world",), "news one", "https://www.srf.ch/y"),
            _story("2026-09-23", 2, "science", ("science",), "paper", "https://arxiv.org/abs/1", "Science"),
            _story("2026-09-23", 1, "news", ("switzerland",), "brief", "https://www.srf.ch/z"),
            _ed("2026-09-23", "science", "", ["<strong>1. Lede here.</strong> Rest."]),
            _story("2026-09-22", 2, "ai-ml", ("ai-ml",), "model", "https://doi.org/10.1/abc"),
            _story("2026-09-22", 2, "news", ("world",), "news two", ""),
        ]
        self.views = bsf.build_views(self.board, "2026-09-23", self.topics, posts_dir=self.posts)

    def test_every_item_carries_its_edition_and_period(self):
        for it in self.board:
            self.assertEqual(it["edition"], "%s-%s" % (it["date"], it["stream"]))
            self.assertEqual(it["period"]["end"], it["date"])
            self.assertLessEqual(it["period"]["start"], it["period"]["end"])
        sci = self.board[0]["period"]
        self.assertEqual((sci["start"], sci["label"]), ("2026-09-17", "17–23 Sep"))
        self.assertEqual(self.board[5]["period"]["label"], "19–22 Sep")

    def test_editorial_gets_read_id_and_the_union_of_its_editions_topics(self):
        ed = self.board[4]
        self.assertEqual(ed["sid"], "ed-science-2026-09-23")
        self.assertEqual(ed["topics"], ["health", "science"])     # science stories only, sorted
        self.assertEqual(ed["stream_label"], "Science")
        self.assertEqual((ed["title_html"], ed["title_is_lede"], ed["body"]), ("Lede here.", True, ["Rest."]))

    def test_story_render_fields(self):
        lead, news1, paper, brief, _, doi, nourl = self.board
        self.assertEqual((lead["tier"], lead["tier_label"]), ("lead", "Lead"))
        self.assertEqual(brief["tier"], "brief")
        self.assertTrue(lead["unfurl"])
        self.assertFalse(paper["unfurl"], "arXiv og:image is its logo")
        self.assertFalse(doi["unfurl"], "doi.org resolves to a publisher badge")
        self.assertFalse(brief["unfurl"], "briefs carry no image")
        self.assertFalse(nourl["unfurl"])
        self.assertTrue(lead["boot_open"], "today's lead boots open (R33)")
        self.assertFalse(news1["boot_open"])
        self.assertFalse(doi["boot_open"])

    def test_desk_tag_only_on_multi_desk_days_and_only_when_it_says_something(self):
        lead, news1, paper, brief, _, doi, nourl = self.board
        self.assertFalse(lead["show_desk"], "Science desk on a Science beat says nothing")
        self.assertTrue(news1["show_desk"])
        self.assertTrue(doi["show_desk"])

    def test_days_view_slices_the_board(self):
        days = self.views["days"]
        self.assertEqual([d["date"] for d in days], ["2026-09-23", "2026-09-22"])
        flat = []
        for d in days:
            sl = self.board[d["first"]:d["first"] + d["count"]]
            self.assertTrue(all(it["date"] == d["date"] for it in sl))
            flat += sl
        self.assertEqual(flat, self.board)
        d0 = days[0]
        self.assertEqual((d0["label_long"], d0["label_short"]), ("Wednesday 23 September", "Wed 23 Sep"))
        self.assertEqual([s["key"] for s in d0["streams"]], ["science", "news"])
        self.assertEqual((d0["n_stories"], d0["editorials"], d0["n_front"]), (4, 1, 3))
        self.assertTrue(d0["multi_desk"])

    def test_front_and_desk(self):
        # 23 Sep holds only three leads/features, so the window walks back to 22 Sep and takes its
        # first feature before the 23 Sep brief (briefs fill in only when there are too few)
        f = self.views["front"]
        self.assertEqual(f["items"], [0, 1, 2, 5])
        self.assertEqual(f["desk"], 4)
        self.assertTrue(all(self.board[i]["on_front"] for i in f["items"] + [f["desk"]]))
        self.assertFalse(self.board[3]["on_front"])
        self.assertFalse(self.board[6]["on_front"])
        self.assertEqual((f["date"], f["date_label"], f["older"]), ("2026-09-23", "Wed 23 Sep", ["Tue 22 Sep"]))

    def test_beats_count_editorials_too(self):
        beats = {b["key"]: b["count"] for b in self.views["beats"]}
        self.assertEqual(beats["science"], 3)       # two stories + the editorial
        self.assertEqual(beats["health"], 2)        # the lead + the editorial
        self.assertEqual(beats["world"], 2)

    def test_a_linked_lede_keeps_its_link_in_the_heading_and_none_in_title_text(self):
        """The front's "On the front" pointer is itself a link, so it prints `title_text`; an <a>
        inside it would be split by the HTML parser."""
        lede = ("The week's strongest result came from [CERN's ALPHA team](https://home.cern/news/alpha?a=1&b=2) "
                "measuring antihydrogen to a precision nobody expected this decade")
        title, lines = bsf._ed_title(["**%s.** Then more." % lede])
        ed = _ed("2026-09-23", "science", title, bsf._ed_paragraphs(lines))
        bsf.build_views([ed], "2026-09-23", self.topics, posts_dir=self.posts)
        self.assertIn('<a href="https://home.cern/news/alpha?a=1&amp;b=2"', ed["title_html"])
        self.assertNotIn("<", ed["title_text"])
        self.assertTrue(ed["title_text"].startswith("The week's strongest result came from CERN's ALPHA team measuring"))
        self.assertEqual(ed["body"], ["Then more."])

    def test_empty_and_editorial_only_boards_do_not_raise(self):
        v = bsf.build_views([], None, [], posts_dir=self.posts)
        self.assertEqual((v["days"], v["front"]["items"], v["front"]["desk"]), ([], [], None))
        eds = [_ed("2026-09-23", "science"), _ed("2026-09-21", "sports", "", [])]
        v = bsf.build_views(eds, "2026-09-23", self.topics, posts_dir=self.posts)
        self.assertEqual(v["front"]["items"], [])
        self.assertEqual(v["front"]["desk"], 0)
        self.assertEqual(eds[1]["title_html"], "Sports desk, Mon 21 Sep")
        self.assertEqual(eds[1]["topics"], [])


class BuildStampTest(unittest.TestCase):
    def posts(self, files):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        for name, fm in files.items():
            with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
                fh.write(fm)
        return d

    def test_newest_writer_edition_wins_across_offsets_and_forms(self):
        d = self.posts({
            "2026-09-23-science.md": "---\ntitle: x\ndate: 2026-09-23T17:16:47+02:00\n---\nbody\n",
            "2026-09-24-news.md": "---\ndate: 2026-09-24 10:30:00 +0000\n---\n",        # 12:30 +02:00
            "2026-09-24-sports.md": "---\ndate: 2026-09-24T12:21:02+02:00\n---\n",
            "2026-09-25-evaluator.md": "---\ndate: 2026-09-25T09:00:00+02:00\n---\n",   # not a writer
        })
        self.assertEqual(bsf.build_stamp(d), "2026-09-24T10:30:00+00:00")
        self.assertEqual(bsf.build_stamp(d), bsf.build_stamp(d), "input-derived, so stable")

    def test_odd_front_matter_never_raises(self):
        d = self.posts({
            "2026-09-24-news.md": "no front matter at all\ndate: 2026-09-30T00:00:00Z\n",
            "2026-09-23-news.md": "---\ntitle: missing date\n---\n",
            "2026-09-22-news.md": "---\ndate: not-a-date\n---\n",
            "2026-09-21-news.md": "---\ndate: 2026-09-21T08:00:00Z\n---\n",
            "2026-09-20-news.md": "---\ndate: '2026-09-20'\n---\n",
            "2026-09-19-news.md": b"\xff\xfe---\n".decode("latin-1"),
        })
        self.assertEqual(bsf.build_stamp(d), "2026-09-21T08:00:00+00:00")
        self.assertEqual(bsf.build_stamp(self.posts({})), "")


class SandboxCliTest(unittest.TestCase):
    """The real CLI, as a writer sandbox runs it, under `python3 -S` (no site-packages), over odd
    trees. It must exit 0 and write a feed whose views are well-formed."""

    NEWS = ("---\nlayout: single\ntitle: \"News\"\n%s---\n\n## World\n\n"
            "- **Federal Council signs the dispatch.** The government forwarded the package to "
            "Parliament for ratification. [Reuters](https://www.admin.ch/a.html)\n")
    EDITORIAL_ONLY = ("---\ndate: 2026-09-23T10:00:00+02:00\n---\n\n## Why it matters\n\n"
                      "**A take.** With no stories in the edition, it has nothing to comment on.\n")

    def run_cli(self, posts):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root)
        for rel in ("build_stories_feed.py", "build_stats.py", os.path.join("store", "store.py")):
            os.makedirs(os.path.dirname(os.path.join(root, "tools", rel)), exist_ok=True)
            shutil.copy(os.path.join(TOOLS, rel), os.path.join(root, "tools", rel))
        os.makedirs(os.path.join(root, "_posts"))
        os.makedirs(os.path.join(root, "_data"))
        for name, text in posts.items():
            with open(os.path.join(root, "_posts", name), "w", encoding="utf-8") as fh:
                fh.write(text)
        out = os.path.join(root, "_data", "homefeed.json")
        r = subprocess.run([sys.executable, "-S", os.path.join(root, "tools", "build_stories_feed.py"),
                            "--out", out], capture_output=True, text=True, cwd=root)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(out, encoding="utf-8") as fh:
            return json.load(fh)

    def test_python_minus_s_really_hides_site_packages(self):
        r = subprocess.run([sys.executable, "-S", "-c", "import yaml"], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0, "PyYAML must be unimportable under -S for this class to mean anything")

    def test_single_post(self):
        feed = self.run_cli({"2026-09-24-news.md": self.NEWS % "date: 2026-09-24T12:00:00+02:00\n"})
        self.assertEqual(len(feed["board"]), 1)
        self.assertEqual(len(feed["days"]), 1)
        self.assertEqual(feed["front"]["items"], [0])
        self.assertEqual(feed["board"][0]["period"]["label"], "24 Sep")
        self.assertEqual(feed["build_stamp"], "2026-09-24T12:00:00+02:00")
        self.assertEqual(feed["count_line"], "1 story · 0 AI editorials · 1 day")

    def test_post_without_a_date_front_matter(self):
        feed = self.run_cli({"2026-09-24-news.md": self.NEWS % ""})
        self.assertEqual(len(feed["board"]), 1)
        self.assertEqual(feed["build_stamp"], "")

    def test_editorial_only_post_and_empty_tree(self):
        feed = self.run_cli({"2026-09-23-science.md": self.EDITORIAL_ONLY})
        self.assertEqual((feed["board"], feed["days"], feed["front"]["items"]), ([], [], []))
        feed = self.run_cli({})
        self.assertEqual((feed["board"], feed["days"], feed["edition_label"]), ([], [], ""))


if __name__ == "__main__":
    unittest.main()
