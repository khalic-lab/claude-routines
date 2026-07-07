#!/usr/bin/env python3
"""RED-phase spec tests — per-story anchors (SPIKE-2026-07-07-continuous-news.md §3.3.3
"Per-story anchors: emit `<a id="st-…"></a>` before each bullet/`###` heading"; contract
clause for `tools/store/anchor.py`).

Covers: bullet-form inline `<a id="st-..." class="st-a"></a>` insertion, `###` heading
kramdown IAL insertion, first-URL selection (bullet and whole-block scope), no-URL
skipping, idempotence (byte-identical on a second run / never double-insert), --check
report-only mode (writes nothing), and the printed 'url -> st-id' table.

Run: cd /Users/rflnogueira/code/claude-routines && python3 -m unittest discover -s tools/tests -v
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
FIXTURES_DIR = os.path.join(TESTS_DIR, "fixtures", "store")
POSTS_FIXTURE_DIR = os.path.join(FIXTURES_DIR, "posts")
STORE_PATH = os.path.join(REPO_ROOT, "tools", "store", "store.py")
ANCHOR_PATH = os.path.join(REPO_ROOT, "tools", "store", "anchor.py")


def _load_module(path, name):
    """importlib load by fixed path. A missing (not-yet-implemented) file must fail THIS
    test clearly, not crash discovery of the rest of the suite."""
    if not os.path.exists(path):
        raise AssertionError(f"expected implementation file is missing: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _copy_fixture(name):
    tmp = tempfile.mkdtemp(prefix="anchor-test-")
    dest = os.path.join(tmp, name)
    shutil.copy(os.path.join(POSTS_FIXTURE_DIR, name), dest)
    return tmp, dest


def _run_anchor(args, timeout=30):
    return subprocess.run([sys.executable, ANCHOR_PATH] + args,
                           capture_output=True, text=True, timeout=timeout)


class AnchorBulletTests(unittest.TestCase):
    """news-register '- **lead**...' bullets."""

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(ANCHOR_PATH):
            raise AssertionError(f"expected implementation file is missing: {ANCHOR_PATH}")
        cls.store = _load_module(STORE_PATH, f"store_anchorbullet_{id(cls)}")

    def setUp(self):
        self.tmp, self.path = _copy_fixture("news-bullets.md")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        with open(self.path) as f:
            self.original = f.read()

    def test_bullet_with_a_link_gets_an_inline_anchor_right_after_dash_space(self):
        proc = _run_anchor([self.path])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(self.path) as f:
            out = f.read()
        sid = self.store.story_id("https://example.com/alpha-bullet")
        expected_tag = f'<a id="{sid}" class="st-a"></a>'
        self.assertIn(f"- {expected_tag}**Alpha bullet leads the section.**", out)

    def test_bullet_with_no_link_is_left_untouched(self):
        proc = _run_anchor([self.path])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(self.path) as f:
            out = f.read()
        # No anchor tag may be inserted between '- ' and '**' for a linkless bullet — the
        # exact original opening substring (dash-space directly followed by the bold
        # lead) must survive untouched.
        self.assertIn(
            "- **Beta bullet has no citation at all.** This bullet intentionally carries "
            "no markdown link and must be skipped by anchor.py.",
            out,
        )

    def test_bullet_with_two_links_anchors_on_the_first_url_only(self):
        proc = _run_anchor([self.path])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(self.path) as f:
            out = f.read()
        sid_first = self.store.story_id("https://example.com/gamma-first")
        sid_second = self.store.story_id("https://example.com/gamma-second")
        self.assertIn(f'<a id="{sid_first}" class="st-a"></a>', out)
        self.assertNotIn(f'<a id="{sid_second}" class="st-a"></a>', out)

    def test_only_the_two_linked_bullets_gain_anchors(self):
        proc = _run_anchor([self.path])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(self.path) as f:
            out = f.read()
        self.assertEqual(out.count('class="st-a"'), 2)


class AnchorHeadingTests(unittest.TestCase):
    """science/weekend-register '### Title' headings + kramdown IAL."""

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(ANCHOR_PATH):
            raise AssertionError(f"expected implementation file is missing: {ANCHOR_PATH}")
        cls.store = _load_module(STORE_PATH, f"store_anchorheading_{id(cls)}")

    def setUp(self):
        self.tmp, self.path = _copy_fixture("science-headings.md")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_heading_with_a_byline_link_gets_a_kramdown_ial(self):
        proc = _run_anchor([self.path])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(self.path) as f:
            out = f.read()
        sid = self.store.story_id("https://example.com/delta-paper")
        self.assertIn(
            f"### Delta paper reports a fixture-only result {{#{sid}}}", out,
        )

    def test_heading_with_no_link_anywhere_in_its_block_is_untouched(self):
        proc = _run_anchor([self.path])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(self.path) as f:
            out = f.read()
        self.assertIn(
            "### Epsilon heading has no link anywhere in its block\n", out,
        )
        self.assertNotIn("### Epsilon heading has no link anywhere in its block {#", out)

    def test_heading_uses_the_first_url_anywhere_in_the_block_not_just_the_byline_line(self):
        """Zeta's citation link sits in a later paragraph, not on the line right after
        the heading — the IAL must still pick it up."""
        proc = _run_anchor([self.path])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(self.path) as f:
            out = f.read()
        sid = self.store.story_id("https://example.com/zeta-writeup")
        self.assertIn(f"### Zeta paper's link appears in prose, not the byline {{#{sid}}}", out)

    def test_only_the_two_linked_headings_gain_ials(self):
        proc = _run_anchor([self.path])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(self.path) as f:
            out = f.read()
        self.assertEqual(out.count("{#st-"), 2)


class AnchorIdempotenceTests(unittest.TestCase):
    """contract: 'Never double-insert (idempotence test: run twice, byte-identical).'"""

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(ANCHOR_PATH):
            raise AssertionError(f"expected implementation file is missing: {ANCHOR_PATH}")

    def test_running_twice_on_bullets_is_byte_identical_to_running_once(self):
        tmp, path = _copy_fixture("news-bullets.md")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        _run_anchor([path])
        with open(path, "rb") as f:
            after_first = f.read()
        _run_anchor([path])
        with open(path, "rb") as f:
            after_second = f.read()
        self.assertEqual(after_first, after_second)

    def test_running_twice_on_headings_is_byte_identical_to_running_once(self):
        tmp, path = _copy_fixture("science-headings.md")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        _run_anchor([path])
        with open(path, "rb") as f:
            after_first = f.read()
        _run_anchor([path])
        with open(path, "rb") as f:
            after_second = f.read()
        self.assertEqual(after_first, after_second)


class AnchorCheckModeTests(unittest.TestCase):
    """contract: '--check = report-only' — must write nothing."""

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(ANCHOR_PATH):
            raise AssertionError(f"expected implementation file is missing: {ANCHOR_PATH}")

    def test_check_mode_leaves_the_file_byte_identical(self):
        tmp, path = _copy_fixture("news-bullets.md")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        with open(path, "rb") as f:
            before = f.read()
        proc = _run_anchor(["--check", path])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(path, "rb") as f:
            after = f.read()
        self.assertEqual(before, after, "--check must write nothing")

    def test_normal_mode_on_the_same_fixture_does_change_the_file(self):
        """Sanity control proving the fixture is anchorable at all — isolates the
        --check assertion above from a vacuously-true 'nothing changed because there was
        nothing to anchor' false pass."""
        tmp, path = _copy_fixture("news-bullets.md")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        with open(path, "rb") as f:
            before = f.read()
        _run_anchor([path])
        with open(path, "rb") as f:
            after = f.read()
        self.assertNotEqual(before, after)


class AnchorPrintsTableTests(unittest.TestCase):
    """contract: 'Prints "url -> st-id" table.'"""

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(ANCHOR_PATH):
            raise AssertionError(f"expected implementation file is missing: {ANCHOR_PATH}")
        cls.store = _load_module(STORE_PATH, f"store_anchortable_{id(cls)}")

    def test_stdout_reports_each_anchored_url_and_its_st_id(self):
        tmp, path = _copy_fixture("news-bullets.md")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        proc = _run_anchor([path])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        sid_alpha = self.store.story_id("https://example.com/alpha-bullet")
        sid_gamma = self.store.story_id("https://example.com/gamma-first")
        for url, sid in (("https://example.com/alpha-bullet", sid_alpha),
                         ("https://example.com/gamma-first", sid_gamma)):
            found = any(url in line and sid in line for line in proc.stdout.splitlines())
            self.assertTrue(found, f"expected a line with both {url} and {sid} in:\n{proc.stdout}")

    def test_skipped_no_url_bullet_does_not_appear_in_the_table(self):
        tmp, path = _copy_fixture("news-bullets.md")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        proc = _run_anchor([path])
        self.assertNotIn("gamma-second", proc.stdout)


class AnchorCustomIALTests(unittest.TestCase):
    """FINDING 3 (MINOR): a heading that already carries a custom kramdown IAL --
    '### Custom {#my-id}' -- must be left byte-identical. Appending a second IAL
    ('### Custom {#my-id} {#st-...}') corrupts the heading: kramdown then renders the
    first '{#my-id}' as literal text instead of consuming it as the id."""

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(ANCHOR_PATH):
            raise AssertionError(f"expected implementation file is missing: {ANCHOR_PATH}")

    def _write_post(self, content):
        tmp = tempfile.mkdtemp(prefix="anchor-ial-test-")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        path = os.path.join(tmp, "post.md")
        with open(path, "w") as f:
            f.write(content)
        return path

    def test_heading_with_a_pre_existing_custom_ial_is_left_untouched(self):
        content = (
            "### Custom heading {#my-id}\n"
            "**[Source](https://example.com/custom-ial)**\n"
            "Some prose citing the source.\n"
        )
        path = self._write_post(content)
        proc = _run_anchor([path])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(path) as f:
            out = f.read()
        self.assertIn("### Custom heading {#my-id}\n", out)
        self.assertNotIn("{#my-id} {#st-", out,
                          "a second IAL must never be appended after an existing custom one")


class AnchorIndexMatchTests(unittest.TestCase):
    """FINDING 2 (MAJOR): anchor.py used to key a story's id on the block's FIRST markdown
    link, while the ledger's `publish` events key on the story's recorded url from the
    edition's own index/stories/{date}-{slug}.jsonl file -- diverging whenever a bullet's
    first link is a background/corroborating link rather than the primary source. With
    --index <that file>, a block's links are matched against the recorded stories' norm_url
    set and the MATCHED record's own url is used for the id; the block's first link is only
    a fallback when nothing in it matches a recorded story."""

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(ANCHOR_PATH):
            raise AssertionError(f"expected implementation file is missing: {ANCHOR_PATH}")
        cls.store = _load_module(STORE_PATH, f"store_anchorindex_{id(cls)}")

    def setUp(self):
        self.tmp, self.path = _copy_fixture("news-bullets.md")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        # news-bullets.md's gamma bullet cites gamma-first (background) then gamma-second
        # (the real source) -- the index only records gamma-second, as a real edition's
        # index/stories/{date}-{slug}.jsonl would.
        self.index_path = os.path.join(self.tmp, "2026-06-20-news.jsonl")
        with open(self.index_path, "w") as f:
            f.write(json.dumps({
                "id": "2026-06-20-news-x", "date": "2026-06-20", "stream": "news",
                "headline": "Gamma's real source", "summary": "S.",
                "url": "https://example.com/gamma-second",
            }) + "\n")

    def test_index_match_keys_the_id_on_the_records_url_not_the_blocks_first_link(self):
        proc = _run_anchor(["--index", self.index_path, self.path])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(self.path) as f:
            out = f.read()
        sid_background = self.store.story_id("https://example.com/gamma-first")
        sid_recorded = self.store.story_id("https://example.com/gamma-second")
        self.assertIn(f'<a id="{sid_recorded}" class="st-a"></a>', out,
                       "the gamma bullet's anchor id must match the recorded story's url")
        self.assertNotIn(f'<a id="{sid_background}" class="st-a"></a>', out,
                          "must not fall back to the block's first (background) link when "
                          "the index has a match on a later link")

    def test_without_index_the_same_fixture_falls_back_to_the_first_link(self):
        """Control proving the fallback (pre-existing, un-indexed behavior) is unchanged."""
        proc = _run_anchor([self.path])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(self.path) as f:
            out = f.read()
        sid_background = self.store.story_id("https://example.com/gamma-first")
        self.assertIn(f'<a id="{sid_background}" class="st-a"></a>', out)


if __name__ == "__main__":
    unittest.main()
