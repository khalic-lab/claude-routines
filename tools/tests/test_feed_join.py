#!/usr/bin/env python3
"""Spec tests for the feed<->index JOIN and the bullet SHAPES the parser accepts.

Both halves are 2026-07-26 fixes for the external review of 2026-07-25:

R3 — the overlay join was keyed on a bare normalized URL for the whole window, so two editions
that legitimately re-cite one primary source (an ONGOING story; a Weekend recap of the week's
News) shared a single map slot and filesystem glob order decided which edition's curated
headline/body/importance every card wore. The corruption was live: a 24 July News card rendered
the 25 July Weekend Iran framing at the Weekend's importance 2 instead of its own 3.
`test_same_url_in_two_editions_*` pins the fix, and `test_join_is_independent_of_glob_order`
pins the property the bug actually had — the answer must not depend on directory order.

R4 — the parser accepted only `###` headings and bullets opening on a bold lede, while the
Weekend format contract (routines/src/weekend.md) specifies plain `- ...` bullets. Three of the
25 July Weekend edition's five headline bullets were therefore recorded, anchored, embedded,
dedup-checked and then absent from the only reading surface the site has. The guards matter as
much as the recovery: a linkless bullet is a desk aside, and an editorial section's bullets are
commentary, so neither may become a card.
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
BUILD_FEED_PATH = os.path.join(REPO_ROOT, "tools", "build_stories_feed.py")

URL = "https://example.test/one-story?utm_source=x"

NEWS_POST = """---
title: News
---

# News

## World

- **The desk filed the news telling on Monday 1 June.** More news prose follows here, long
  enough to clear the body floor comfortably. [Example, 1 Jun 2026](%s)
""" % URL

WEEKEND_POST = """---
title: Weekend
---

# Weekend

## Week in headlines

- The desk filed the weekend telling a week later, opening on prose rather than on a bold
  lede. [Example, 1 Jun 2026](%s)
""" % URL


def _rec(**kw):
    r = {"id": "x", "date": "2026-06-01", "stream": "news", "headline": "H", "url": URL,
         "topics": ["world"], "importance": 2, "display_body": "B", "why": ""}
    r.update(kw)
    return r


def _root(posts, records):
    root = tempfile.mkdtemp(prefix="join-test-")
    os.makedirs(os.path.join(root, "_posts"))
    os.makedirs(os.path.join(root, "index", "stories"))
    os.makedirs(os.path.join(root, "_data"))
    for name, body in posts.items():
        with open(os.path.join(root, "_posts", name), "w") as fh:
            fh.write(body)
    for name, rows in records.items():
        with open(os.path.join(root, "index", "stories", name), "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
    return root


def _mod(root):
    spec = importlib.util.spec_from_file_location("_bsf_join", BUILD_FEED_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.ROOT = root
    mod.POSTS_DIR = os.path.join(root, "_posts")
    mod.INDEX_DIR = os.path.join(root, "index", "stories")
    return mod


def _build(root, extra_argv=()):
    mod = _mod(root)
    out = os.path.join(root, "_data", "homefeed.json")
    mod.DEFAULT_OUT = out
    old = sys.argv
    sys.argv = (["build_stories_feed.py", "--days", "3650", "--max", "0", "--out", out]
                + list(extra_argv))
    try:
        mod.main()
    finally:
        sys.argv = old
    with open(out) as fh:
        return json.load(fh)


# --- R3: the same URL in two editions -------------------------------------------------------
TWO_EDITIONS = {
    "_posts/2026-06-01-news.md": NEWS_POST,
    "_posts/2026-06-08-weekend.md": WEEKEND_POST,
}
TWO_RECORDS = {
    "2026-06-01-news.jsonl": [_rec(id="2026-06-01-news-a", date="2026-06-01", stream="news",
                                   headline="The News headline", importance=3,
                                   display_body="The News body.", topics=["politics"])],
    "2026-06-08-weekend.jsonl": [_rec(id="2026-06-08-weekend-a", date="2026-06-08",
                                      stream="weekend", headline="The Weekend headline",
                                      importance=1, display_body="The Weekend body.",
                                      topics=["world"])],
}


class EditionIdentityJoinTest(unittest.TestCase):
    def setUp(self):
        posts = {os.path.basename(k): v for k, v in TWO_EDITIONS.items()}
        self.root = _root(posts, TWO_RECORDS)
        self.addCleanup(shutil.rmtree, self.root, True)

    def _cards(self):
        # the newer telling supersedes the older card IN PLACE (load_recent's ONGOING rule), so
        # this fixture yields exactly one card — the Weekend one, wearing Weekend metadata.
        return {(s["date"], s["stream"]): s for s in _build(self.root)["stories"]}

    def test_same_url_in_two_editions_keeps_each_editions_own_copy(self):
        card = self._cards()[("2026-06-08", "weekend")]
        self.assertEqual(card["headline"], "The Weekend headline")
        self.assertEqual(card["summary"], "The Weekend body.")
        self.assertEqual(card["importance"], 1)
        self.assertEqual(card["topics"], ["world"])

    def test_same_url_in_two_editions_never_crosses_over(self):
        card = self._cards()[("2026-06-08", "weekend")]
        for wrong in ("The News headline", "The News body."):
            self.assertNotIn(wrong, json.dumps(card),
                             "a Weekend card is wearing News copy — the join lost the edition")

    def test_only_the_older_edition_present_uses_its_own_copy(self):
        """The mirror case: with only the News edition on disk the card is the News card. Run
        separately so neither direction can pass by accident of which record happens to win."""
        root = _root({"2026-06-01-news.md": NEWS_POST},
                     {k: v for k, v in TWO_RECORDS.items() if k.startswith("2026-06-01")})
        self.addCleanup(shutil.rmtree, root, True)
        cards = _build(root)["stories"]
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["headline"], "The News headline")
        self.assertEqual(cards[0]["importance"], 3)

    def test_join_is_independent_of_glob_order(self):
        """The bug's real shape: 'reversing index-file iteration changes the winner'. It must
        not, so build twice with glob.glob reversed and demand identical output."""
        mod = _mod(self.root)
        real_glob = mod.glob.glob
        out = []
        for rev in (False, True):
            mod.glob.glob = (lambda p, _r=rev, _g=real_glob: sorted(_g(p), reverse=_r))
            try:
                dates = {"2026-06-01", "2026-06-08"}
                by_url, _ = mod.load_index_meta(dates)
                out.append(json.dumps({"%s|%s|%s" % k: v.get("headline")
                                       for k, v in by_url.items()}, sort_keys=True))
            finally:
                mod.glob.glob = real_glob
        self.assertEqual(out[0], out[1])
        self.assertIn("The News headline", out[0])
        self.assertIn("The Weekend headline", out[0])


# --- R4: bullet shapes ----------------------------------------------------------------------
SHAPES_POST = """---
title: Weekend
---

# Weekend

## Week in headlines

- <a id="st-0123456789ab" class="st-a"></a>A plain bullet carrying an anchor and a source is a story, and its whole text stays prose. [Example, 1 Jun 2026](https://plain.test/a)
- A plain bullet may also wrap across lines before it reaches its citation, which is why the source gate reads the whole story.
  It finishes on the next line. [Example, 1 Jun 2026](https://plain.test/wrapped)
- A plain bullet with no source at all is a desk aside, not a story, however long it runs on about the state of the week.
- **A bold-lead bullet** keeps its exact old parse. [Example, 1 Jun 2026](https://bold.test/a)
- <a id="st-hand-written-0601" class="st-a"></a>**A writer-authored anchor is markup, not an id.** It must still parse as a bullet. [Example, 1 Jun 2026](https://bold.test/legacy)

## Why it matters

- **An editorial bullet is commentary** and never becomes a card, even now that plain bullets
  do. [Example, 1 Jun 2026](https://editorial.test/a)

## Cross-cutting threads

- **A cross-cutting thread is the same kind of thing.** Also never a card.
  [Example, 1 Jun 2026](https://editorial.test/b)
"""


class BulletShapeTest(unittest.TestCase):
    def setUp(self):
        self.mod = _mod(REPO_ROOT)
        self.parsed = self.mod.parse_post(SHAPES_POST)
        self.urls = [s["url"] for s in self.parsed]

    def test_plain_sourced_bullet_becomes_a_story(self):
        self.assertIn("https://plain.test/a", self.urls)

    def test_plain_bullet_keeps_its_whole_text_as_prose(self):
        s = [x for x in self.parsed if x["url"] == "https://plain.test/a"][0]
        self.assertIn("A plain bullet carrying an anchor", s["body"])
        self.assertIn("whole text stays prose", s["body"])

    def test_plain_bullet_headline_is_derived_and_never_ellipsized(self):
        s = [x for x in self.parsed if x["url"] == "https://plain.test/a"][0]
        self.assertTrue(s["headline"])
        self.assertLessEqual(len(s["headline"]), self.mod.HEADLINE_CAP)
        self.assertNotIn("…", s["headline"])
        self.assertNotIn("...", s["headline"])
        self.assertFalse(s["headline"].endswith("-"), "cropped mid-word")

    def test_a_wrapped_plain_bullets_citation_still_counts_as_its_source(self):
        self.assertIn("https://plain.test/wrapped", self.urls)

    def test_linkless_plain_bullet_is_not_a_story(self):
        for s in self.parsed:
            self.assertNotIn("desk aside", s["headline"] + s["body"])

    def test_bold_lead_bullet_parse_is_unchanged(self):
        s = [x for x in self.parsed if x["url"] == "https://bold.test/a"][0]
        self.assertEqual(s["headline"], "A bold-lead bullet")
        self.assertNotIn("A bold-lead bullet", s["body"])   # the lede is consumed, as before

    def test_non_canonical_anchor_still_parses_and_is_not_used_as_an_id(self):
        """_posts/2026-07-13-news.md's writer-authored anchors made _BULLET_RE fail outright:
        that whole edition's 7 recorded stories reached no card at all."""
        s = [x for x in self.parsed if x["url"] == "https://bold.test/legacy"][0]
        self.assertIn("A writer-authored anchor is markup", s["headline"])
        self.assertIsNone(s["anchor_sid"])

    def test_canonical_anchor_is_used_as_the_id(self):
        s = [x for x in self.parsed if x["url"] == "https://plain.test/a"][0]
        self.assertEqual(s["anchor_sid"], "st-0123456789ab")

    def test_editorial_section_bullets_never_become_stories(self):
        for u in self.urls:
            self.assertNotIn("editorial.test", u or "")


# --- R4: the parity check -------------------------------------------------------------------
class EditionParityTest(unittest.TestCase):
    """A count comparison is not the check: 2026-07-13 News parsed 0 stories from 7 records,
    where 0 == 0 for every count you could take. Identity, or nothing."""

    def _root_with(self, extra_records):
        return _root({"2026-06-01-news.md": NEWS_POST},
                     {"2026-06-01-news.jsonl": [_rec(id="2026-06-01-news-a")] + extra_records})

    def test_every_record_mapped_is_silent(self):
        root = self._root_with([])
        self.addCleanup(shutil.rmtree, root, True)
        self.assertEqual(_mod(root).edition_parity("2026-06-01"), [])

    def test_a_recorded_story_the_post_never_printed_is_reported(self):
        root = self._root_with([_rec(id="2026-06-01-news-ghost",
                                     url="https://example.test/never-printed",
                                     headline="A story the post never printed")])
        self.addCleanup(shutil.rmtree, root, True)
        gaps = _mod(root).edition_parity("2026-06-01")
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0][0], "2026-06-01-news")
        self.assertEqual([r["headline"] for r in gaps[0][1]],
                         ["A story the post never printed"])

    def test_strict_parity_exits_non_zero_after_writing_the_feed(self):
        root = self._root_with([_rec(id="2026-06-01-news-ghost",
                                     url="https://example.test/never-printed")])
        self.addCleanup(shutil.rmtree, root, True)
        with self.assertRaises(SystemExit):
            _build(root, ["--strict-parity"])
        # the surface still exists — the gate reports, it does not withhold
        with open(os.path.join(root, "_data", "homefeed.json")) as fh:
            self.assertTrue(json.load(fh)["stories"])

    def test_a_matched_record_may_name_any_url_the_story_cites(self):
        """A story often cites two sources and the record names the primary, which is not always
        the one the prose reaches first. That must count as mapped — and as an overlay."""
        post = """---
title: News
---

# News

## World

- **Two sources, record on the second.** Prose long enough to clear the body floor.
  [First, 1 Jun 2026](https://first.test/a); [Second, 1 Jun 2026](https://second.test/b)
"""
        root = _root({"2026-06-01-news.md": post},
                     {"2026-06-01-news.jsonl": [_rec(id="2026-06-01-news-a",
                                                     url="https://second.test/b",
                                                     headline="Recorded headline",
                                                     importance=3)]})
        self.addCleanup(shutil.rmtree, root, True)
        self.assertEqual(_mod(root).edition_parity("2026-06-01"), [])
        card = _build(root)["stories"][0]
        self.assertEqual(card["headline"], "Recorded headline")
        self.assertEqual(card["importance"], 3)


if __name__ == "__main__":
    unittest.main()
