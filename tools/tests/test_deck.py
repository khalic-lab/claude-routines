#!/usr/bin/env python3
"""Spec tests for the writer-authored `deck` standfirst (build_stories_feed.py, 2026-07-25).

Contract, and the reason each half matters:
  - A record that carries a `deck` puts that text on the story verbatim.
  - A record WITHOUT one produces a story with NO `deck` key at all — not `""`.

The absence half is the load-bearing one. Every other overlaid field takes a fallback
(`headline`/`display_body`/`why` all fall back to the markdown re-parse), but a deck exists
nowhere except the writer's Step C record, and briefs are specified to omit it. The render
side gates on the key with Liquid's `{% if s.deck %}`, where the empty string is TRUTHY — so
emitting `"deck": ""` would open a blank standfirst slot under every brief-tier card and every
record written before the field existed. `assertNotIn` is therefore the point of this file;
asserting `deck == ""` would pass while the bug shipped.
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
FIXTURES_DIR = os.path.join(TESTS_DIR, "fixtures", "dualwrite")
POSTS_FIXTURE_DIR = os.path.join(FIXTURES_DIR, "posts")
INDEX_FIXTURE_DIR = os.path.join(FIXTURES_DIR, "index")
BUILD_FEED_PATH = os.path.join(REPO_ROOT, "tools", "build_stories_feed.py")

# The two dualwrite fixture records. Stories are keyed by URL below, never by importance:
# the fixture yields THREE stories and two of them are importance 2 (the third, a weather
# note, has no URL and no record at all, so it can never carry a deck) — keying on the tier
# would silently compare whichever imp-2 story sorted last.
LEAD_INDEX = "2026-07-01-news.jsonl"          # importance 3 -> gets a deck
FEATURE_INDEX = "2026-07-02-ai-ml.jsonl"      # importance 2 -> left without one


def _skeleton_with_decks(decks):
    """Fixture repo root, with `decks` ({index filename: deck text}) merged into the records.

    Mirrors test_feed_sid.py's wiring: build_stories_feed derives ROOT from __file__, so the
    module globals are repointed at the temp root rather than the real repo.
    """
    root = tempfile.mkdtemp(prefix="deck-test-")
    os.makedirs(os.path.join(root, "_posts"))
    os.makedirs(os.path.join(root, "index", "stories"))
    os.makedirs(os.path.join(root, "_data"))
    for name in os.listdir(POSTS_FIXTURE_DIR):
        shutil.copy(os.path.join(POSTS_FIXTURE_DIR, name), os.path.join(root, "_posts", name))
    for name in os.listdir(INDEX_FIXTURE_DIR):
        dst = os.path.join(root, "index", "stories", name)
        deck = decks.get(name)
        if deck is None:
            shutil.copy(os.path.join(INDEX_FIXTURE_DIR, name), dst)
            continue
        with open(os.path.join(INDEX_FIXTURE_DIR, name)) as fh:
            lines = [ln for ln in fh if ln.strip()]
        with open(dst, "w") as fh:
            for ln in lines:
                r = json.loads(ln)
                r["deck"] = deck
                fh.write(json.dumps(r) + "\n")
    return root


def _build(root):
    spec = importlib.util.spec_from_file_location("_bsf_deck", BUILD_FEED_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.ROOT = root
    mod.POSTS_DIR = os.path.join(root, "_posts")
    mod.INDEX_DIR = os.path.join(root, "index", "stories")
    out = os.path.join(root, "_data", "homefeed.json")
    mod.DEFAULT_OUT = out
    old_argv = sys.argv
    # --days spans the fixture regardless of wall-clock today (load_recent anchors on the
    # posts' own max date); --max 0 keeps both stories.
    sys.argv = ["build_stories_feed.py", "--days", "3650", "--max", "0", "--out", out]
    try:
        mod.main()
    finally:
        sys.argv = old_argv
    with open(out) as fh:
        return json.load(fh)


def _record_url(index_filename):
    """The fixture record's URL — read from the fixture rather than hardcoded, so the key
    cannot drift out of sync with the data it selects. URL is also the overlay's real join
    key, which makes it the honest thing to assert against."""
    with open(os.path.join(INDEX_FIXTURE_DIR, index_filename)) as fh:
        for ln in fh:
            if ln.strip():
                return json.loads(ln)["url"]
    raise AssertionError("fixture %s has no records" % index_filename)


def _by_url(feed):
    return {s.get("url"): s for s in feed["stories"]}


class DeckOverlayTest(unittest.TestCase):
    DECK = "The Council signed the dispatch after a decade of talks, and the cantons now get a say."

    def test_recorded_deck_lands_on_the_story_verbatim(self):
        root = _skeleton_with_decks({LEAD_INDEX: self.DECK})
        self.addCleanup(shutil.rmtree, root, True)
        story = _by_url(_build(root))[_record_url(LEAD_INDEX)]
        self.assertEqual(story["deck"], self.DECK)

    def test_record_without_a_deck_emits_no_deck_key(self):
        # the whole point: absent, not empty. Liquid's `{% if %}` fires on "".
        root = _skeleton_with_decks({LEAD_INDEX: self.DECK})
        self.addCleanup(shutil.rmtree, root, True)
        story = _by_url(_build(root))[_record_url(FEATURE_INDEX)]
        self.assertNotIn("deck", story)

    def test_no_record_carries_a_deck_means_no_story_does(self):
        # the pre-2026-07-25 corpus: nothing is backfilled or synthesized.
        root = _skeleton_with_decks({})
        self.addCleanup(shutil.rmtree, root, True)
        feed = _build(root)
        self.assertTrue(feed["stories"])
        for s in feed["stories"]:
            self.assertNotIn("deck", s)

    def test_blank_and_whitespace_decks_are_treated_as_absent(self):
        # a writer emitting "" or "   " must not open an empty standfirst slot either
        for blank in ("", "   ", "\n\t "):
            root = _skeleton_with_decks({LEAD_INDEX: blank, FEATURE_INDEX: blank})
            self.addCleanup(shutil.rmtree, root, True)
            for s in _build(root)["stories"]:
                self.assertNotIn("deck", s, "blank deck %r must not emit a key" % blank)

    def test_deck_does_not_disturb_the_other_overlaid_fields(self):
        plain = _by_url(_build(_skeleton_with_decks({})))
        decked = _by_url(_build(_skeleton_with_decks({LEAD_INDEX: self.DECK})))
        self.assertEqual(set(plain), set(decked))
        for url in plain:
            a, b = dict(plain[url]), dict(decked[url])
            b.pop("deck", None)
            self.assertEqual(a, b, "adding a deck changed something else on %s" % url)


if __name__ == "__main__":
    unittest.main()
