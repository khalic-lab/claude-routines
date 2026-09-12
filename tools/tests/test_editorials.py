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


class EdTitleTest(unittest.TestCase):
    """THE SECTION HEADING IS NOT A TITLE (2026-07-26). `title` used to be the scraped `## `
    heading, so a Sports editorial went to the front page headlined "Why it matters". The card
    title is now the editorial's own opening bold lede, consumed out of the prose it opened; the
    heading moved to the kicker, where a section name belongs. One test per shape."""

    def test_bullet_lede_becomes_the_title_and_leaves_the_body(self):
        lines = ["", "- **One nation, both trophies — and an era confirmed.** Spain go into the "
                     "next four years as reigning champions.", ""]
        title, out = bsf._ed_title(lines)
        self.assertEqual(title, "One nation, both trophies — and an era confirmed")
        paras = bsf._ed_paragraphs(out)
        self.assertEqual(paras, ["Spain go into the next four years as reigning champions."])

    def test_paragraph_lede_becomes_the_title(self):
        lines = ["**1. The theory is catching up.** For two years it ran on tricks."]
        title, out = bsf._ed_title(lines)
        self.assertEqual(title, "1. The theory is catching up")
        self.assertEqual(bsf._ed_paragraphs(out), ["For two years it ran on tricks."])

    def test_a_lede_that_is_the_whole_line_leaves_no_stray_marker(self):
        title, out = bsf._ed_title(["- **Just the lede.**", "", "Second para."])
        self.assertEqual(title, "Just the lede")
        self.assertEqual(bsf._ed_paragraphs(out), ["Second para."])

    def test_no_bold_lede_means_no_title_and_untouched_prose(self):
        lines = ["Plain prose opens this section.", "", "And continues."]
        title, out = bsf._ed_title(lines)
        self.assertEqual(title, "")
        self.assertEqual(out, lines)
        self.assertEqual(bsf._ed_paragraphs(out),
                         ["Plain prose opens this section.", "And continues."])

    def test_an_over_long_lede_is_left_in_the_prose_rather_than_cropped(self):
        long_lede = "word " * 30
        lines = ["- **%s.** Then the body." % long_lede.strip()]
        title, out = bsf._ed_title(lines)
        self.assertEqual(title, "")                       # no <h2> beats a cropped one
        self.assertIn(long_lede.strip(), bsf._ed_paragraphs(out)[0])   # and nothing is lost

    def test_title_never_carries_an_ellipsis(self):
        for lede in ("Short one", "word " * 30):
            title, _ = bsf._ed_title(["**%s.** body" % lede.strip()])
            self.assertNotIn("…", title)
            self.assertNotIn("...", title)


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

    def _load(self, max_date, live, days=14):
        return bsf.load_editorials(days, max_date, live)

    def test_latest_edition_per_stream_wins_and_rules_are_dropped(self):
        self._post("2026-07-11-weekend.md",
                   "## 🧠 Cross-cutting threads\n\n**Old.** Old take.\n\n---\n")
        self._post("2026-07-18-weekend.md",
                   "## 🧠 Cross-cutting threads\n\n**New.** New take.\n\n---\n\n## Stories\n\nx\n")
        eds = self._load("2026-07-18", {("2026-07-11", "weekend"), ("2026-07-18", "weekend")})
        self.assertEqual(len(eds), 1)
        self.assertEqual(eds[0]["date"], "2026-07-18")
        self.assertEqual(eds[0]["title"], "New")
        self.assertEqual(eds[0]["paras"], ["New take."])
        self.assertEqual(eds[0]["kicker"], "Weekend · Cross-cutting threads · Jul 18")

    def test_rule_only_section_yields_no_card(self):
        self._post("2026-07-18-science.md", "## Why it matters\n\n---\n")
        self.assertEqual(self._load("2026-07-18", {("2026-07-18", "science")}), [])

    def test_an_editorial_older_than_ed_max_age_days_is_dropped(self):
        """ED_MAX_AGE_DAYS is the belt for a desk that stops firing: apply_cap's
        MIN_LATEST_EDITION keeps a stream's newest edition on the board indefinitely, so
        "its edition is still there" cannot be the only expiry.

        The boundary is derived from the constant, not written out. This test used to hardcode
        7-in / 8-out; when ED_MAX_AGE_DAYS moved to 5 it failed as a bare number mismatch and
        said nothing about whether the RULE was still right.
        """
        import datetime as _d
        post = _d.date(2026, 7, 18)
        self._post("2026-07-18-sports.md", "## Why it matters\n\n**A.** Old synthesis.\n")
        live = {("2026-07-18", "sports")}
        last_in = (post + _d.timedelta(days=bsf.ED_MAX_AGE_DAYS)).isoformat()
        first_out = (post + _d.timedelta(days=bsf.ED_MAX_AGE_DAYS + 1)).isoformat()
        self.assertEqual(len(self._load(last_in, live)), 1, "ED_MAX_AGE_DAYS days old: still in")
        self.assertEqual(self._load(first_out, live), [], "one day past it: gone")

    def test_editorial_lifetime_is_shorter_than_the_weekly_cadence(self):
        """THE REGRESSION GUARD FOR "the editorials keep reappearing" (owner report 2026-09-12).

        Science, Sports and Weekend all fire on a 7-day period. While ED_MAX_AGE_DAYS was 7, the
        successor editorial landed the day BEFORE the incumbent expired, so a weekly desk's
        editorial slot was never once empty -- 3 editorials on every build for 24 straight days.
        The rule could only ever hand over, never expire.

        A lifetime strictly shorter than the shortest editorial-bearing desk's period is what
        buys a gap. This asserts the relationship rather than the number, so raising
        ED_MAX_AGE_DAYS back to 7 -- or adding a desk that fires more often than the lifetime --
        fails here with the reason attached.
        """
        WEEKLY_CADENCE_DAYS = 7          # sports (Mon), science (Wed), weekend (Sat)
        self.assertLess(
            bsf.ED_MAX_AGE_DAYS, WEEKLY_CADENCE_DAYS,
            "ED_MAX_AGE_DAYS (%d) must be < the %d-day desk cadence, or a weekly desk's editorial "
            "slot is never empty and every editorial rides ~%d consecutive daily rebuilds"
            % (bsf.ED_MAX_AGE_DAYS, WEEKLY_CADENCE_DAYS, WEEKLY_CADENCE_DAYS))

        # and demonstrate the gap concretely: a weekly desk publishes, and there is at least one
        # day before its successor lands on which no editorial for that desk is on the board.
        import datetime as _d
        post = _d.date(2026, 7, 18)
        self._post("2026-07-18-sports.md", "## Why it matters\n\n**A.** Old synthesis.\n")
        live = {("2026-07-18", "sports")}
        gap = [d for d in range(1, WEEKLY_CADENCE_DAYS)
               if not self._load((post + _d.timedelta(days=d)).isoformat(), live)]
        self.assertTrue(gap, "no day between one sports edition and the next has an empty "
                             "editorial slot -- this is the 'keeps reappearing' bug")

    def test_an_editorial_whose_edition_left_the_board_is_dropped(self):
        self._post("2026-07-25-weekend.md", "## Why it matters\n\n**A.** This week.\n")
        self.assertEqual(len(self._load("2026-07-26", {("2026-07-25", "weekend")})), 1)
        self.assertEqual(self._load("2026-07-26", set()), [])
        self.assertEqual(self._load("2026-07-26", {("2026-07-25", "news")}), [])

    def test_no_count_cap(self):
        """The old `[:3]` deleted a desk's synthesis at random. Under one ranked board five
        editorials scatter across five date blocks instead of stacking on the first screen."""
        live = set()
        for stream in ("news", "ai-ml", "science", "weekend", "sports"):
            self._post("2026-07-26-%s.md" % stream,
                       "## Why it matters\n\n**%s.** Take.\n" % stream)
            live.add(("2026-07-26", stream))
        self.assertEqual(len(self._load("2026-07-26", live)), 5)


class BuildBoardTest(unittest.TestCase):
    """The ordering fix itself. `feed["board"]` is one ranked sequence; an editorial ranks below
    briefs so it CLOSES its own edition's date block, which is the whole answer to a six-day-old
    Sports editorial sitting at position 4 (owner report, 2026-07-26)."""

    def _story(self, date, imp, name):
        return {"date": date, "importance": imp, "headline": name, "stream": "news"}

    def _ed(self, date, name="ed"):
        return {"date": date, "title": name, "stream": "sports"}

    def _board(self, stories, eds, max_date):
        return bsf.build_board(list(stories), list(eds), max_date)

    def test_editorial_closes_its_own_date_block(self):
        stories = [self._story("2026-07-26", 3, "today-lead")] + \
                  [self._story("2026-07-26", 2, "today-%d" % i) for i in range(5)] + \
                  [self._story("2026-07-20", 3, "old-lead"),
                   self._story("2026-07-20", 1, "old-brief")]
        board = self._board(stories, [self._ed("2026-07-20")], "2026-07-26")
        kinds = [it["kind"] for it in board]
        self.assertEqual(kinds.index("editorial"), len(board) - 1)
        self.assertEqual(board[-2]["headline"], "old-brief")   # below the briefs of its own day

    def test_no_editorial_in_the_composed_top_band(self):
        """A `.fcard--ed` at nth-child(1) renders `grid-area:1/1/2/13` — 100% of the board width
        with no news on screen (documented failure, 2026-07-25)."""
        for n_today in range(0, 4):
            stories = [self._story("2026-07-26", 2, "t%d" % i) for i in range(n_today)] + \
                      [self._story("2026-07-20", 2, "o%d" % i) for i in range(4)]
            board = self._board(stories, [self._ed("2026-07-26")], "2026-07-26")
            head = [it["kind"] for it in board[:bsf.ED_MIN_BOARD_INDEX]]
            self.assertNotIn("editorial", head,
                             "editorial in the composed band with %d fresh stories" % n_today)

    def test_editorial_only_board_is_left_alone_rather_than_looping(self):
        board = self._board([], [self._ed("2026-07-26", "a"), self._ed("2026-07-26", "b")],
                            "2026-07-26")
        self.assertEqual([it["kind"] for it in board], ["editorial", "editorial"])

    def test_position_is_stable_inside_a_date_and_tier(self):
        stories = [self._story("2026-07-26", 2, "first"), self._story("2026-07-26", 2, "second"),
                   self._story("2026-07-26", 2, "third")]
        board = self._board(stories, [], "2026-07-26")
        self.assertEqual([it["headline"] for it in board], ["first", "second", "third"])

    def test_age_days_is_a_clamped_bucket(self):
        stories = [self._story("2026-07-26", 2, "a"), self._story("2026-07-25", 2, "b"),
                   self._story("2026-07-01", 2, "c")]
        board = self._board(stories, [], "2026-07-26")
        self.assertEqual([it["age_days"] for it in board], [0, 1, bsf.AGE_MAX])

    def test_daybreak_marks_every_date_block_start_exactly_once(self):
        stories = [self._story("2026-07-26", 2, "a"), self._story("2026-07-26", 1, "b"),
                   self._story("2026-07-25", 2, "c"), self._story("2026-07-20", 2, "d")]
        board = self._board(stories, [self._ed("2026-07-25")], "2026-07-26")
        flags = [bool(it["daybreak"]) for it in board]
        runs = sum(1 for i, it in enumerate(board)
                   if i == 0 or it["date"] != board[i - 1]["date"])
        self.assertEqual(sum(flags), runs)
        self.assertTrue(flags[0])

    def test_the_reported_failure_no_longer_reproduces(self):
        """The exact 2026-07-26 shape: 8 fresh News stories, a 1-day-old Weekend editorial and a
        6-day-old Sports one. Both used to be spliced at index 3 and 4."""
        stories = [self._story("2026-07-26", 3, "lead")] + \
                  [self._story("2026-07-26", 2, "n%d" % i) for i in range(7)] + \
                  [self._story("2026-07-25", 2, "w%d" % i) for i in range(9)] + \
                  [self._story("2026-07-20", 2, "s%d" % i) for i in range(5)]
        board = self._board(stories, [self._ed("2026-07-25", "weekend-ed"),
                                      self._ed("2026-07-20", "sports-ed")], "2026-07-26")
        at = {it.get("title"): i for i, it in enumerate(board) if it["kind"] == "editorial"}
        self.assertEqual(at["weekend-ed"], 17)     # closes the 07-25 block
        self.assertEqual(at["sports-ed"], 23)      # closes the 07-20 block, at the foot
        self.assertEqual(board[at["sports-ed"]]["age_days"], bsf.AGE_MAX)


if __name__ == "__main__":
    unittest.main()
