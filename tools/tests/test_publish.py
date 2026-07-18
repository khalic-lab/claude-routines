"""Spec tests for tools/publish.py -- the publish-tail orchestrator.

Contract under test: the fixed step order (record -> anchor -> footer -> lint ->
registry/institutions sync -> date lint -> feed -> health -> stub -> git), real
JSON encoding in the notification stub (no hand-escaped quotes), bare front-matter
date normalization, and the record-skip path when dedup was unavailable.
RealGitTest exercises the git tail against real local repos: a failed commit or
push must surface as 'commit-failed'/'push-failed' (never a silent DONE), and the
push-failure note must be AMENDED INTO the commit, not left unstaged.
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
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
                                   "feed", "source-health", "plane-push", "stub",
                                   "git-add", "git-commit", "git-push")
                 if ("DRY-RUN %s" % name) in out or ("DRY-RUN %s:" % name) in out]
        self.assertEqual(order, ["record", "anchor", "footer", "source-lint",
                                 "registry-sync", "institutions-sync", "date-lint",
                                 "feed", "source-health", "plane-push", "stub",
                                 "git-add", "git-commit", "git-push"])

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
        # Brief pages are retired (2026-07-18): every brief notification clicks
        # through to the homepage story feed, never a per-edition page.
        self.assertEqual(stub["click"], "https://khalic-lab.github.io/claude-routines/")
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


def _git(cwd, *argv):
    return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                           "-c", "commit.gpgsign=false"] + list(argv),
                          cwd=cwd, capture_output=True, text=True)


class RealGitTest(unittest.TestCase):
    """The git tail against real repos -- the paths dry-run can't see."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="publish-git-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.origin = os.path.join(self.tmp, "origin.git")
        subprocess.run(["git", "init", "--bare", "-q", "-b", "main", self.origin],
                       check=True, capture_output=True)
        self.work = os.path.join(self.tmp, "work")
        subprocess.run(["git", "clone", "-q", self.origin, self.work],
                       check=True, capture_output=True)
        os.makedirs(os.path.join(self.work, "_posts"))
        self.post = os.path.join(self.work, "_posts", "2026-07-18-news.md")
        self._write_post("Body.\n")
        # seed origin/main so later pushes aren't the branch-creating first push
        _git(self.work, "add", "-A")
        _git(self.work, "commit", "-q", "-m", "seed")
        _git(self.work, "push", "-q", "origin", "main")

    def _write_post(self, body):
        with open(self.post, "w") as fh:
            fh.write("---\ntitle: News\n---\n\n" + body)

    def _capture(self, fn, *a, **kw):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            out = fn(*a, **kw)
        return out, buf.getvalue()

    def test_happy_path_lands_on_origin(self):
        self._write_post("Edition body.\n")
        outcome, _ = self._capture(publish.commit_and_push, self.work, "news",
                                   "News — test", False, False)
        self.assertEqual(outcome, "ok")
        log = subprocess.run(["git", "--git-dir", self.origin, "log", "-1",
                              "--format=%s", "main"], capture_output=True, text=True)
        self.assertEqual(log.stdout.strip(), "News — test")

    def test_failed_commit_is_never_reported_ok(self):
        """The false-DONE shape: commit fails, push of the unchanged branch would
        succeed as a no-op -- commit_and_push must say commit-failed, not ok."""
        self._write_post("Edition body.\n")
        hook = os.path.join(self.work, ".git", "hooks", "pre-commit")
        with open(hook, "w") as fh:
            fh.write("#!/bin/sh\nexit 1\n")
        os.chmod(hook, 0o755)
        outcome, out = self._capture(publish.commit_and_push, self.work, "news",
                                     "News — test", False, False)
        self.assertEqual(outcome, "commit-failed")
        self.assertIn("git-commit: FAIL", out)

    def test_nothing_staged_still_pushes_prior_commit(self):
        """Second run after a push failure: nothing new to commit, but the earlier
        commit still needs pushing -- must be ok, not a commit error."""
        self._write_post("Edition body.\n")
        _git(self.work, "add", "-A")
        _git(self.work, "commit", "-q", "-m", "unpushed edition")
        outcome, out = self._capture(publish.commit_and_push, self.work, "news",
                                     "News — test", False, False)
        self.assertEqual(outcome, "ok")
        self.assertIn("nothing newly staged", out)
        log = subprocess.run(["git", "--git-dir", self.origin, "log", "-1",
                              "--format=%s", "main"], capture_output=True, text=True)
        self.assertEqual(log.stdout.strip(), "unpushed edition")

    def test_push_failure_reported_and_note_amended_into_commit(self):
        self._write_post("Edition body.\n")
        _git(self.work, "remote", "set-url", "origin",
             os.path.join(self.tmp, "no-such-remote.git"))
        outcome, _ = self._capture(publish.commit_and_push, self.work, "news",
                                   "News — test", False, False)
        self.assertEqual(outcome, "push-failed")
        _, out = self._capture(publish.record_push_failure, self.work, "news",
                               self.post, False)
        with open(self.post) as fh:
            self.assertIn("git push failed", fh.read())
        show = _git(self.work, "show", "--format=", "HEAD", "--", "_posts/2026-07-18-news.md")
        self.assertIn("git push failed", show.stdout,
                      "the failure note must travel WITH the commit, not sit unstaged")


if __name__ == "__main__":
    unittest.main()
