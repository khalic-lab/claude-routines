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


if __name__ == "__main__":
    unittest.main()
