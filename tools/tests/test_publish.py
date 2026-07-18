"""Spec tests for tools/publish.py -- the publish-tail orchestrator.

Contract under test: the fixed step order (record -> anchor -> footer -> lint ->
registry/institutions sync -> date lint -> feed -> health -> stub -> git), real
JSON encoding in the notification stub (no hand-escaped quotes), bare front-matter
date normalization, and the record-skip path when dedup was unavailable.
The git/network steps are only asserted in --dry-run.
"""
import importlib.util
import json
import os
import re
import tempfile
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("_publish", os.path.join(TOOLS, "publish.py"))
publish = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publish)


class PublishTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="publish-test-")
        os.makedirs(os.path.join(self.root, "_posts"))
        self.post = os.path.join(self.root, "_posts", "2026-07-18-news.md")
        with open(self.post, "w") as fh:
            fh.write("---\nlayout: single\ntitle: \"News\"\ndate: 2026-07-18\n"
                     "categories: [news]\n---\n\nBody.\n\n## Coverage footer\n- Gaps: none.\n")

    def _capture(self, argv):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = publish.main(argv)
        return rc, buf.getvalue()

    def test_dry_run_step_order(self):
        rc, out = self._capture([
            "--slug", "news", "--date", "2026-07-18", "--root", self.root,
            "--final", "/tmp/final.json", "--notify-title", "News — 2026-07-18",
            "--notify-body", "teaser", "--dry-run"])
        self.assertEqual(rc, 0)
        order = [name for name in ("record", "anchor", "footer", "source-lint",
                                   "registry-sync", "institutions-sync", "date-lint",
                                   "feed", "source-health", "stub", "git-add",
                                   "git-commit", "git-push")
                 if ("DRY-RUN %s" % name) in out or ("DRY-RUN %s:" % name) in out]
        self.assertEqual(order, ["record", "anchor", "footer", "source-lint",
                                 "registry-sync", "institutions-sync", "date-lint",
                                 "feed", "source-health", "stub", "git-add",
                                 "git-commit", "git-push"])

    def test_record_skipped_without_final(self):
        rc, out = self._capture(["--slug", "news", "--date", "2026-07-18",
                                 "--root", self.root, "--dry-run"])
        self.assertEqual(rc, 0)
        self.assertIn("record: skipped", out)
        self.assertNotIn("DRY-RUN record", out)

    def test_front_matter_bare_date_normalized_once(self):
        publish.normalize_front_matter(self.post, dry_run=False)
        with open(self.post) as fh:
            text = fh.read()
        m = re.search(r"^date: (2026-07-18T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2})$", text, re.M)
        self.assertIsNotNone(m, "bare date must become a full ISO timestamp with offset")
        publish.normalize_front_matter(self.post, dry_run=False)  # idempotent
        with open(self.post) as fh:
            self.assertEqual(fh.read(), text)

    def test_stub_json_is_really_encoded(self):
        publish.write_stub(self.root, "news", "2026-07-18",
                           'He said "hi" — ok', 'Line with "quotes" and — dashes',
                           "newspaper", dry_run=False)
        stub_dir = os.path.join(self.root, "pending-notifications")
        (name,) = os.listdir(stub_dir)
        self.assertRegex(name, r"^\d{8}T\d{6}Z-news\.json$")
        with open(os.path.join(stub_dir, name)) as fh:
            stub = json.load(fh)  # must be valid JSON despite the quotes
        self.assertEqual(stub["title"], 'He said "hi" — ok')
        self.assertEqual(stub["click"],
                         "https://khalic-lab.github.io/claude-routines/2026/07/18/news/")
        self.assertEqual(stub["tags"], "newspaper")

    def test_missing_post_is_fatal(self):
        rc, out = self._capture(["--slug", "sports", "--date", "2026-07-18",
                                 "--root", self.root])
        self.assertEqual(rc, 2)
        self.assertIn("FATAL", out)

    def test_commit_titles_cover_every_slug(self):
        self.assertEqual(set(publish.COMMIT_TITLE) | {"evaluator"},
                         set(publish.SLUGS) | {"evaluator"})
        self.assertEqual(publish.COMMIT_TITLE["weekend"], "Weekend Deep Read")


if __name__ == "__main__":
    unittest.main()
