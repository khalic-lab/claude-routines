"""Spec tests for publish.py's missing-story alert (2026-09-25).

Contract: a lede-fallback WARN or a PARITY-FAIL row in the feed builder's output writes ONE
pending-notifications stub in the schema the bridge drains ({title, click, body, tags}, title and
body non-empty); a clean build writes nothing; a problem already alerted never alerts again (the
builder reprints an old post's WARN on every publish for two weeks), while a NEW problem in the
same build still does; the stub and its dedupe state travel in the edition's own commit; and the
builder still prints the literal lines this parser depends on.
"""
import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("_publish_alert", os.path.join(TOOLS, "publish.py"))
publish = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(publish)

CLEAN = """wrote 80/120 stories (9 beats, streams: news) -> _data/homefeed.json
parity: every kept record in the 2026-09-25 edition(s) reached a card
"""
WARN_ONE = """wrote 80/120 stories (9 beats, streams: news) -> _data/homefeed.json
WARN no body parsed: _posts/2026-09-24-news.md story st-aaaaaaaaaaaa -- the card falls back to its lede
parity: every kept record in the 2026-09-25 edition(s) reached a card
"""
WARN_TWO = WARN_ONE + (
    "WARN no body parsed: _posts/2026-09-25-news.md story st-bbbbbbbbbbbb -- the card falls back "
    "to its lede\n")
PARITY = """wrote 80/120 stories (9 beats, streams: news) -> _data/homefeed.json
PARITY-FAIL: kept index records that reached no card in the current edition —
  2026-09-25-news  Federal Council recommends a no on Lex On  https://www.admin.ch/x
  2026-09-25-news  A record with no url  -
  the post and the index disagree: either the writer never printed the story, or the parser cannot see the shape it printed it in.
stats build skipped (non-fatal): nope
"""


def _stubs(root):
    d = os.path.join(root, "pending-notifications")
    return sorted(os.listdir(d)) if os.path.isdir(d) else []


class AlertTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="publish-alert-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def _alert(self, out, date="2026-09-25", slug="news"):
        with contextlib.redirect_stdout(io.StringIO()):
            return publish.alert_missing_stories(self.root, slug, date, out, False)

    def test_warn_writes_one_stub_in_the_bridge_schema(self):
        path = self._alert(WARN_ONE)
        self.assertIsNotNone(path)
        self.assertEqual(len(_stubs(self.root)), 1)
        self.assertTrue(os.path.basename(path).endswith("-alert-news.json"))
        with open(path, encoding="utf-8") as fh:
            stub = json.load(fh)
        self.assertEqual(set(stub), {"title", "click", "body", "tags"})
        self.assertTrue(stub["title"] and stub["body"])        # the bridge skips either empty
        self.assertIn("st-aaaaaaaaaaaa", stub["body"])
        self.assertIn("2026-09-24-news", stub["body"])

    def test_clean_build_writes_nothing(self):
        self.assertIsNone(self._alert(CLEAN))
        self.assertEqual(_stubs(self.root), [])
        self.assertFalse(os.path.exists(os.path.join(self.root, publish.ALERT_DIR)))

    def test_same_problem_alerts_once(self):
        self.assertIsNotNone(self._alert(WARN_ONE))
        self.assertIsNone(self._alert(WARN_ONE, date="2026-09-26", slug="ai-ml"))
        self.assertEqual(len(_stubs(self.root)), 1)

    def test_new_problem_alerts_and_lists_only_itself(self):
        self._alert(WARN_ONE)
        for f in _stubs(self.root):                               # the bridge drained it
            os.remove(os.path.join(self.root, "pending-notifications", f))
        path = self._alert(WARN_TWO)
        self.assertIsNotNone(path)
        with open(path, encoding="utf-8") as fh:
            body = json.load(fh)["body"]
        self.assertIn("st-bbbbbbbbbbbb", body)
        self.assertNotIn("st-aaaaaaaaaaaa", body)

    def test_parity_fail_rows_alert(self):
        problems = publish.feed_problems(PARITY)
        self.assertEqual([p[0] for p in problems],
                         ["parity|2026-09-25-news|https://www.admin.ch/x",
                          "parity|2026-09-25-news|A record with no url"])
        path = self._alert(PARITY)
        with open(path, encoding="utf-8") as fh:
            self.assertIn("Lex On", json.load(fh)["body"])

    def test_state_is_deterministic_and_pruned(self):
        self._alert(WARN_ONE)
        d = os.path.join(self.root, publish.ALERT_DIR)
        (name,) = os.listdir(d)
        with open(os.path.join(d, name), encoding="utf-8") as fh:
            self.assertEqual(json.load(fh), {"key": "warn|2026-09-24-news|st-aaaaaaaaaaaa",
                                             "edition": "2026-09-24-news"})
        # a new alert 31+ days later prunes the old problem's state
        self._alert(WARN_TWO.replace("2026-09-25-news.md", "2026-10-30-news.md"),
                    date="2026-10-30")
        keys = []
        for n in os.listdir(d):
            with open(os.path.join(d, n), encoding="utf-8") as fh:
                keys.append(json.load(fh)["key"])
        self.assertEqual(keys, ["warn|2026-10-30-news|st-bbbbbbbbbbbb"])

    def test_main_wires_the_alert_after_the_feed_step(self):
        os.makedirs(os.path.join(self.root, "_posts"))
        with open(os.path.join(self.root, "_posts", "2026-09-25-news.md"), "w") as fh:
            fh.write("---\ntitle: News\ndate: 2026-09-25T12:00:00+02:00\n---\n\nBody.\n")
        real_rso, real_cap = publish.run_step_out, publish.commit_and_push
        calls = []

        def fake_rso(name, argv, root, dry_run):
            calls.append(name)
            return True, (WARN_ONE if name == "feed" else "")
        publish.run_step_out = fake_rso
        publish.commit_and_push = lambda *a, **k: "ok"
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                rc = publish.main(["--slug", "news", "--date", "2026-09-25",
                                   "--root", self.root, "--no-push"])
        finally:
            publish.run_step_out, publish.commit_and_push = real_rso, real_cap
        self.assertEqual(rc, 0)
        self.assertIn("feed", calls)
        self.assertEqual([f for f in _stubs(self.root) if "-alert-" in f].__len__(), 1)

    def test_builder_still_prints_the_lines_this_parses(self):
        with open(os.path.join(TOOLS, "build_stories_feed.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn('"WARN no body parsed: %s story %s', src)
        self.assertIn('print("PARITY-FAIL:', src)
        self.assertIn('print("  %s  %s  %s" % (ed, ', src)


class AlertCommitTest(unittest.TestCase):
    """The alert and its state must ride the edition's own commit (publish's git tail)."""

    def test_stub_and_state_are_committed(self):
        tmp = tempfile.mkdtemp(prefix="publish-alert-git-")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        work = os.path.join(tmp, "work")
        subprocess.run(["git", "init", "-q", "-b", "main", work], check=True, capture_output=True)
        os.makedirs(os.path.join(work, "_posts"))
        with open(os.path.join(work, "_posts", "2026-09-25-news.md"), "w") as fh:
            fh.write("---\ntitle: News\n---\n\nBody.\n")
        with contextlib.redirect_stdout(io.StringIO()):
            publish.alert_missing_stories(work, "news", "2026-09-25", WARN_ONE, False)
            outcome = publish.commit_and_push(work, "news", "News — test", True, False)
        self.assertEqual(outcome, "ok")
        show = subprocess.run(["git", "show", "--name-only", "--format=", "HEAD"], cwd=work,
                              capture_output=True, text=True).stdout
        self.assertRegex(show, r"pending-notifications/\d{8}T\d{6}Z-alert-news\.json")
        self.assertRegex(show, r"index/alerts/[0-9a-f]{16}\.json")


if __name__ == "__main__":
    unittest.main()
