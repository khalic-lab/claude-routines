#!/usr/bin/env python3
"""Spec — the board's story age ceiling (tools/build_stories_feed.py drop_aged_out).

WHY THIS FILE EXISTS (2026-09-12). Nothing in build_stories_feed.py expired a story, and four
things looked like they did: `--days` is a scan bound, apply_cap is a fairness quota, AGE_MAX is a
display bucket, and ED_MAX_AGE_DAYS covers editorials only. The result reached the front page --
on 2026-09-12 the board carried "Djokovic exits US Open in first round" and a 3-3 scoreline, both
from 08-31, twelve days stale, sitting beside that morning's news (owner report: "some weird stuff
with some sports articles"). They survived at --days 21, 30 and 60, so the window was never what
kept them; apply_cap equalizes rather than expires, and its drop order pops the LOWEST importance
first, so what survives a stale edition is precisely its lead items -- in a sports brief, the
results.

These are JSON-shape claims about the feed, so they belong in unittest rather than in the Chrome
harness, which is the wrong oracle for "is this story too old to be on the page".
"""
import datetime as dt
import importlib.util
import os
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
FEED_PATH = os.path.join(REPO_ROOT, "tools", "build_stories_feed.py")

_spec = importlib.util.spec_from_file_location("_bsf_for_age_test", FEED_PATH)
bsf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bsf)

NEWEST = "2026-09-12"


def _story(stream, days_old, importance=2):
    d = (dt.date.fromisoformat(NEWEST) - dt.timedelta(days=days_old)).isoformat()
    return {"date": d, "stream": stream, "importance": importance,
            "headline": "%s %dd" % (stream, days_old), "topics": [], "url": ""}


def _streams(kept):
    return sorted({s["stream"] for s in kept})


class StoryAgeCeilingTest(unittest.TestCase):
    def test_every_live_stream_has_a_ceiling(self):
        """A stream missing from the table silently falls back to the default; that is fine, but
        the default must exist and be a real number, or the ceiling is a no-op for that desk."""
        self.assertTrue(bsf.STORY_MAX_AGE_DEFAULT > 0)
        for stream in ("news", "ai-ml", "science", "weekend", "sports"):
            limit = bsf.STORY_MAX_AGE_DAYS.get(stream, bsf.STORY_MAX_AGE_DEFAULT)
            self.assertGreater(limit, 0, "%s has no usable age ceiling" % stream)

    def test_sports_results_do_not_outlive_the_next_fixture(self):
        """THE REPORTED BUG. Sports fires weekly, so a story older than one cadence has been
        superseded by the next round -- a finished match is not news once the next one is played.
        Pinned at <= 7 rather than just 'some number': at 8+ two sports editions coexist and the
        older one's lead results ride along, which is exactly what shipped."""
        self.assertLessEqual(
            bsf.STORY_MAX_AGE_DAYS.get("sports", bsf.STORY_MAX_AGE_DEFAULT), 7,
            "a sports ceiling above the 7-day cadence puts last week's results next to this "
            "week's -- the 2026-09-12 'Djokovic exits US Open' regression")

    def test_stale_sports_stories_are_dropped_and_fresh_ones_kept(self):
        stories = [_story("sports", 0), _story("sports", 5),
                   _story("sports", 12, importance=3), _story("sports", 12, importance=2)]
        kept = bsf.drop_aged_out(stories, NEWEST)
        ages = sorted((dt.date.fromisoformat(NEWEST) - dt.date.fromisoformat(s["date"])).days
                      for s in kept)
        self.assertEqual(ages, [0, 5], "12-day-old sports stories must not reach the board, "
                                       "regardless of their importance")

    def test_importance_does_not_buy_survival(self):
        """apply_cap drops lowest-importance first, so the survivors of a stale edition are its
        LEADS. The age ceiling has to run before that and ignore importance entirely, or the
        highest-profile stale story is the one that stays."""
        stories = [_story("sports", 30, importance=3)]
        # the newest-edition floor would keep it, so give the stream a fresher edition too
        stories.append(_story("sports", 0, importance=1))
        kept = bsf.drop_aged_out(stories, NEWEST)
        self.assertEqual([s["importance"] for s in kept], [1])

    def test_a_streams_newest_edition_is_never_aged_out(self):
        """A silent or slow desk degrades to one stale edition rather than vanishing from the
        page -- the same intent as apply_cap's MIN_LATEST_EDITION floor, which cannot help here
        because it runs afterwards and only counts what it is given."""
        stories = [_story("science", 99), _story("science", 120), _story("news", 0)]
        kept = bsf.drop_aged_out(stories, NEWEST)
        self.assertIn("science", _streams(kept), "a dormant desk must not disappear entirely")
        sci = [s for s in kept if s["stream"] == "science"]
        self.assertEqual(len(sci), 1, "only its newest edition survives")
        self.assertEqual(sci[0]["date"],
                         (dt.date.fromisoformat(NEWEST) - dt.timedelta(days=99)).isoformat())

    def test_zero_means_no_ceiling(self):
        stories = [_story("news", 0), _story("news", 400)]
        saved = dict(bsf.STORY_MAX_AGE_DAYS)
        bsf.STORY_MAX_AGE_DAYS["news"] = 0
        try:
            self.assertEqual(len(bsf.drop_aged_out(stories, NEWEST)), 2)
        finally:
            bsf.STORY_MAX_AGE_DAYS.clear()
            bsf.STORY_MAX_AGE_DAYS.update(saved)

    def test_no_newest_date_is_a_passthrough(self):
        stories = [_story("news", 0), _story("news", 400)]
        self.assertEqual(len(bsf.drop_aged_out(stories, None)), 2)


class LiveBoardAgeTest(unittest.TestCase):
    """Against the committed _data/homefeed.json -- the artifact the page actually reads."""

    @classmethod
    def setUpClass(cls):
        import json
        path = os.path.join(REPO_ROOT, "_data", "homefeed.json")
        if not os.path.exists(path):
            raise unittest.SkipTest("_data/homefeed.json not built")
        with open(path, encoding="utf-8") as fh:
            cls.feed = json.load(fh)

    def test_no_board_story_exceeds_its_streams_ceiling(self):
        newest = self.feed.get("generated")
        if not newest:
            self.skipTest("feed has no generated date")
        nd = dt.date.fromisoformat(newest)
        latest = {}
        for it in self.feed["board"]:
            if it.get("kind") == "story":
                latest[it["stream"]] = max(latest.get(it["stream"], ""), it["date"])
        stale = []
        for it in self.feed["board"]:
            if it.get("kind") != "story":
                continue
            if it["date"] == latest.get(it["stream"]):
                continue                      # newest edition is exempt by design
            limit = bsf.STORY_MAX_AGE_DAYS.get(it["stream"], bsf.STORY_MAX_AGE_DEFAULT)
            age = (nd - dt.date.fromisoformat(it["date"])).days
            if limit and age > limit:
                stale.append("%s %s (%dd > %dd): %s"
                             % (it["stream"], it["date"], age, limit,
                                (it.get("headline") or "")[:60]))
        self.assertFalse(stale, "stale stories on the live board:\n  " + "\n  ".join(stale))

    def test_no_editorial_outlives_ed_max_age_days(self):
        newest = self.feed.get("generated")
        if not newest:
            self.skipTest("feed has no generated date")
        nd = dt.date.fromisoformat(newest)
        for it in self.feed["board"]:
            if it.get("kind") != "editorial":
                continue
            age = (nd - dt.date.fromisoformat(it["date"])).days
            self.assertLessEqual(age, bsf.ED_MAX_AGE_DAYS,
                                 "%s editorial of %s is %d days old" % (it["stream"], it["date"], age))

    def test_every_editorial_edition_still_has_a_story_on_the_board(self):
        """The live_editions invariant, asserted on the artifact rather than on the parameter --
        this is the one the unit test cannot prove, because it is handed the set directly."""
        live = {(i["date"], i["stream"]) for i in self.feed["board"] if i.get("kind") == "story"}
        for it in self.feed["board"]:
            if it.get("kind") == "editorial":
                self.assertIn((it["date"], it["stream"]), live,
                              "%s editorial of %s comments on an edition with no story on the "
                              "board" % (it["stream"], it["date"]))


if __name__ == "__main__":
    unittest.main()
