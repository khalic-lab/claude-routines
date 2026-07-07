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


if __name__ == "__main__":
    unittest.main()
