#!/usr/bin/env python3
"""RED-phase spec tests — homefeed 'sid' key (SPIKE-2026-07-07-continuous-news.md §3.6:
"Homefeed v2 reads the materialized store" / store-id-keyed permalinks).

Contract: `tools/build_stories_feed.py` gains a per-story `sid` key equal to
`tools/store/store.py::story_id(url)` for every story that carries a `url`, and
`null`/absent `sid` for url-less stories — with EVERY OTHER existing field/value preserved
verbatim on the same fixture. `golden-feed.json` is a byte-for-byte capture of the CURRENT
(pre-migration) `build_stories_feed.py` output on `fixtures/dualwrite/posts/` +
`fixtures/dualwrite/index/` — see `capture_golden_feed()` at the bottom (a one-off
regeneration helper, NOT a test):

    python3 -c "import sys; sys.path.insert(0, 'tools/tests'); \\
                 import test_feed_sid as t; t.capture_golden_feed()"

`build_stories_feed.py` derives its `ROOT` (and therefore `POSTS_DIR`/`INDEX_DIR`/
`DEFAULT_OUT`) from `__file__` rather than an env var, so tests monkeypatch those four module
globals after loading rather than pointing REPO at a fixture root.

Run: cd /Users/rflnogueira/code/claude-routines && python3 -m unittest discover -s tools/tests -v
"""
import glob
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
STORE_PATH = os.path.join(REPO_ROOT, "tools", "store", "store.py")
GOLDEN_FEED_PATH = os.path.join(FIXTURES_DIR, "golden-feed.json")


# --------------------------------------------------------------------------- #
# infrastructure — no network, no real-repo writes
# --------------------------------------------------------------------------- #
def _load_module(path, name):
    """importlib load by fixed path. A missing (not-yet-implemented) file must fail THIS
    test clearly, not crash discovery of the rest of the suite."""
    if not os.path.exists(path):
        raise AssertionError(f"expected implementation file is missing: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _new_skeleton():
    root = tempfile.mkdtemp(prefix="feedsid-")
    os.makedirs(os.path.join(root, "_posts"))
    os.makedirs(os.path.join(root, "index", "stories"))
    os.makedirs(os.path.join(root, "_data"))
    for name in os.listdir(POSTS_FIXTURE_DIR):
        shutil.copy(os.path.join(POSTS_FIXTURE_DIR, name), os.path.join(root, "_posts", name))
    for name in os.listdir(INDEX_FIXTURE_DIR):
        shutil.copy(os.path.join(INDEX_FIXTURE_DIR, name), os.path.join(root, "index", "stories", name))
    return root


def _load_build_feed(root, modname):
    """build_stories_feed.py computes ROOT from __file__, not an env var (unlike
    dedup.py) — so point its module globals at the fixture root directly rather than
    relying on where the file was loaded from."""
    mod = _load_module(BUILD_FEED_PATH, modname)
    mod.ROOT = root
    mod.POSTS_DIR = os.path.join(root, "_posts")
    mod.INDEX_DIR = os.path.join(root, "index", "stories")
    mod.DEFAULT_OUT = os.path.join(root, "_data", "homefeed.json")
    return mod


def _run_build_feed(root, modname):
    """Run main() against the fixture skeleton; --days spans the whole fixture regardless
    of wall-clock 'today' (load_recent() anchors on the posts' own max date, not real
    today, so this is deterministic); --max 0 disables the front-page cap so both fixture
    stories always survive."""
    mod = _load_build_feed(root, modname)
    out_path = mod.DEFAULT_OUT
    old_argv = sys.argv
    sys.argv = ["build_stories_feed.py", "--days", "3650", "--max", "0", "--out", out_path]
    try:
        mod.main()
    finally:
        sys.argv = old_argv
    with open(out_path) as f:
        return json.load(f), mod


# --------------------------------------------------------------------------- #
# golden capture (one-off maintenance helper — NOT a test)
# --------------------------------------------------------------------------- #
def capture_golden_feed():
    root = _new_skeleton()
    try:
        feed, _ = _run_build_feed(root, "build_feed_golden_capture")
        with open(GOLDEN_FEED_PATH, "w") as f:
            json.dump(feed, f, ensure_ascii=False, indent=1)
            f.write("\n")
        print(f"wrote {GOLDEN_FEED_PATH}")
    finally:
        shutil.rmtree(root, ignore_errors=True)


# --------------------------------------------------------------------------- #
# tests
# --------------------------------------------------------------------------- #
class FeedSidTests(unittest.TestCase):
    def setUp(self):
        self.root = _new_skeleton()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        with open(GOLDEN_FEED_PATH) as f:
            self.golden = json.load(f)

    def test_output_preserves_every_existing_field_allowing_only_new_sid_key(self):
        """Contract: 'preserves every existing field/value on the same fixture (allowing
        ONLY the new sid key to appear)'."""
        feed, _ = _run_build_feed(self.root, f"build_feed_{id(self)}_a")
        self.assertEqual(feed["generated"], self.golden["generated"])
        self.assertEqual(feed["count"], self.golden["count"])
        self.assertEqual(feed["topics"], self.golden["topics"])
        self.assertEqual(len(feed["stories"]), len(self.golden["stories"]))
        for actual, expected in zip(feed["stories"], self.golden["stories"]):
            extra_keys = set(actual.keys()) - set(expected.keys())
            self.assertEqual(extra_keys, {"sid"} & extra_keys,
                              f"no new keys besides 'sid' may appear, got {extra_keys}")
            actual_sans_sid = {k: v for k, v in actual.items() if k != "sid"}
            self.assertEqual(actual_sans_sid, expected,
                              "every pre-existing field/value must be preserved verbatim")

    def test_url_bearing_story_sid_equals_store_story_id(self):
        """Contract: 'each story with a url carries sid == story_id(url)'."""
        store = _load_module(STORE_PATH, f"store_{id(self)}")
        feed, _ = _run_build_feed(self.root, f"build_feed_{id(self)}_b")
        url_stories = [s for s in feed["stories"] if s.get("url")]
        self.assertTrue(url_stories, "fixture must yield at least one url-bearing story")
        for s in url_stories:
            self.assertIn("sid", s, f"story {s['id']} with a url must carry sid")
            self.assertEqual(s["sid"], store.story_id(s["url"]))

    def test_urlless_story_sid_is_null_or_absent(self):
        """Contract: 'urlless stories carry sid == null or absent'. The fixture's
        weather bullet (no markdown link) exercises this branch."""
        feed, _ = _run_build_feed(self.root, f"build_feed_{id(self)}_c")
        urlless = [s for s in feed["stories"] if not s.get("url")]
        self.assertTrue(urlless, "fixture must include at least one url-less story")
        for s in urlless:
            self.assertIn(s.get("sid"), (None,), f"story {s['id']} without a url must have null/absent sid")

    def test_sid_matches_norm_url_semantics_of_the_existing_norm_url(self):
        """Contract: norm_url = EXACTLY the existing norm_url() in build_stories_feed.py;
        story_id is sha1 of that, not of the raw url (www./scheme/utm-insensitive)."""
        store = _load_module(STORE_PATH, f"store_{id(self)}")
        _, mod = _run_build_feed(self.root, f"build_feed_{id(self)}_d")
        bare = "https://www.admin.ch/gov/en/start/documentation/media-releases.msg-id-100001.html?utm_source=x#frag"
        canonical = "https://admin.ch/gov/en/start/documentation/media-releases.msg-id-100001.html"
        self.assertEqual(mod.norm_url(bare), mod.norm_url(canonical))
        self.assertEqual(store.story_id(bare), store.story_id(canonical))


class FeedSidDegenerateUrlTests(unittest.TestCase):
    """FINDING 3: build_stories_feed.py's sid derivation is guarded only by truthiness
    (`story_id(s["url"]) if s["url"] else None`) -- a degenerate-but-truthy url like the
    bare scheme 'https://' (which norm_url reduces to an empty string) makes story_id raise
    ValueError and would kill the whole feed build. Exercised directly against the helper
    rather than through a markdown fixture: build_stories_feed.py's own `_URL_RE` cannot
    actually extract a literal 'https://' from any real markdown link (it requires >=1
    character after the scheme), so the realistic trigger is a unit-level one, not an
    end-to-end parse -- this is the 'cheap' test the finding asks for."""

    def setUp(self):
        self.mod = _load_module(BUILD_FEED_PATH, f"build_feed_degenerate_{id(self)}")
        self.store = _load_module(STORE_PATH, f"store_degenerate_{id(self)}")

    def test_degenerate_but_truthy_url_yields_null_sid_not_a_crash(self):
        self.assertIsNone(self.mod._safe_story_id("https://"))

    def test_real_url_still_yields_the_same_sid_as_story_id(self):
        url = "https://example.com/a-real-story"
        self.assertEqual(self.mod._safe_story_id(url), self.store.story_id(url))

    def test_falsy_url_yields_null_sid(self):
        self.assertIsNone(self.mod._safe_story_id(None))
        self.assertIsNone(self.mod._safe_story_id(""))


class ParsePostWhyItMattersSectionTests(unittest.TestCase):
    """FINDING 4: a '## Why it matters' H2 roundup section's bullets are prose takeaways,
    not stories -- parse_post must not harvest them as pseudo-stories (real case:
    2026-07-01-science.md's '## \U0001F9E0 Why it matters' section put 2 of the live
    homepage's 80 cards there, both headline-only with a null url)."""

    def setUp(self):
        self.mod = _load_module(BUILD_FEED_PATH, f"build_feed_why_{id(self)}")

    def test_bullets_under_why_it_matters_heading_are_not_harvested(self):
        md = (
            "## Physics\n\n"
            "### A real paper headline\n"
            "**[Nature](https://example.com/paper)** · authors · published 2026-01-01\n"
            "Body text about the paper, long enough to pass the body-length floor easily.\n"
            "*Why it matters:* explanatory line.\n\n"
            "## \U0001F9E0 Why it matters\n\n"
            "- **A roundup takeaway.** Some connecting observation across this week's stories.\n"
            "- **Another takeaway.** More prose, no url.\n"
        )
        stories = self.mod.parse_post(md)
        headlines = [s["headline"] for s in stories]
        self.assertEqual(headlines, ["A real paper headline"],
                          f"why-it-matters bullets must be dropped, got {headlines}")

    def test_urlless_bullet_stories_elsewhere_still_survive(self):
        """A urlless bullet OUTSIDE a why-it-matters section must still be harvested -- the
        fix must be narrowly scoped to that one heading, not to urlless bullets generally."""
        md = (
            "## World\n\n"
            "- **Local weather turns unseasonably warm.** No source link for this one, "
            "just a long enough body to clear the parse floor.\n"
        )
        stories = self.mod.parse_post(md)
        self.assertEqual(len(stories), 1)
        self.assertEqual(stories[0]["headline"], "Local weather turns unseasonably warm")
        self.assertIsNone(stories[0]["url"])


if __name__ == "__main__":
    unittest.main()


class ParsePostAnchoredStoriesTests(unittest.TestCase):
    """Step C.25 (anchor.py) rewrites the post BEFORE Step D parses it for the homefeed —
    the parser must read anchored posts. Regression for 2026-07-07: both editions published
    with anchors and the feed builder silently harvested zero stories from them."""

    @classmethod
    def setUpClass(cls):
        cls.mod = _load_module(BUILD_FEED_PATH, "bsf_anchored")

    def test_anchored_bullet_story_still_parses_with_clean_headline(self):
        md = (
            "## Switzerland\n\n"
            '- <a id="st-4ed5174aeff4" class="st-a"></a>**Bern weighs a thing.** '
            "Body sentence. ([SRF](https://www.srf.ch/news/x))\n"
        )
        stories = self.mod.parse_post(md)
        self.assertEqual(len(stories), 1)
        self.assertEqual(stories[0]["headline"], "Bern weighs a thing")
        self.assertEqual(stories[0].get("anchor_sid"), "st-4ed5174aeff4")
        self.assertEqual(stories[0]["url"], "https://www.srf.ch/news/x")

    def test_anchored_bullet_terminates_a_preceding_h3_block(self):
        md = (
            "## Papers\n\n"
            "### A paper title {#st-aaaaaaaaaaaa}\n"
            "Paper body. ([abs](https://arxiv.org/abs/1))\n"
            '- <a id="st-bbbbbbbbbbbb" class="st-a"></a>**A bullet after it.** '
            "Bullet body. ([src](https://example.org/a))\n"
        )
        stories = self.mod.parse_post(md)
        self.assertEqual([s["headline"] for s in stories],
                         ["A paper title", "A bullet after it"])
        self.assertEqual(stories[0].get("anchor_sid"), "st-aaaaaaaaaaaa")
        self.assertEqual(stories[1].get("anchor_sid"), "st-bbbbbbbbbbbb")

    def test_h3_kramdown_ial_stripped_from_headline_and_captured_as_sid(self):
        md = (
            "## Papers\n\n"
            "### Coherent erbium control {#st-cccccccccccc}\n"
            "Body. ([Nature](https://www.nature.com/articles/y))\n"
        )
        stories = self.mod.parse_post(md)
        self.assertEqual(stories[0]["headline"], "Coherent erbium control")
        self.assertNotIn("{#", stories[0]["headline"])
        self.assertEqual(stories[0].get("anchor_sid"), "st-cccccccccccc")

    def test_unanchored_posts_parse_exactly_as_before(self):
        md = (
            "## Switzerland\n\n"
            "- **Plain bullet.** Body. ([SRF](https://www.srf.ch/news/z))\n"
        )
        stories = self.mod.parse_post(md)
        self.assertEqual(len(stories), 1)
        self.assertEqual(stories[0]["headline"], "Plain bullet")
        self.assertIsNone(stories[0].get("anchor_sid"))
