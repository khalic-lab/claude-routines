"""Spec tests for tools/watch/{due,fire}.py -- the deterministic Watch gate.

Contract: due.py does the cooldown arithmetic (null/lapsed/in-cooldown/garbage
last_fired) and prints exactly `NONE DUE` on quiet ticks; fire.py match writes a
real-JSON stub and rewrites ONLY the target watch's last_fired line, preserving
comments and every other byte of watches.yml; fire.py push derives its commit
message from the new stub filenames.
"""
import datetime as dt
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

WATCH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "watch")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


due = _load("due", os.path.join(WATCH, "due.py"))
fire = _load("_fire", os.path.join(WATCH, "fire.py"))

WATCHES = """# Topic-watch registry.
# Comment line that MUST survive edits.

watches:
  - id: fresh-watch
    query: "some query"
    match_when: "a predicate"
    cooldown_days: 14
    last_fired: null

  - id: lapsed-watch
    query: "another query"
    match_when: "another predicate"
    cooldown_days: 7
    last_fired: "2026-07-01"

  - id: cooling-watch
    query: "third query"
    match_when: "third predicate"
    cooldown_days: 14
    last_fired: "2026-07-15"
"""

TODAY = dt.date(2026, 7, 18)


class DueTest(unittest.TestCase):
    def test_cooldown_arithmetic(self):
        watches = due.parse_watches(WATCHES)
        self.assertEqual([w["id"] for w in watches],
                         ["fresh-watch", "lapsed-watch", "cooling-watch"])
        d = due.due_watches(watches, TODAY)
        self.assertEqual([w["id"] for w in d], ["fresh-watch", "lapsed-watch"])
        self.assertEqual(d[0]["last_fired"], None)
        self.assertEqual(d[1]["query"], "another query")

    def test_garbage_last_fired_fails_open(self):
        watches = due.parse_watches(WATCHES.replace('"2026-07-15"', '"not-a-date"'))
        self.assertIn("cooling-watch", [w["id"] for w in due.due_watches(watches, TODAY)])

    def test_cli_none_due_and_json(self):
        root = tempfile.mkdtemp(prefix="watch-test-")
        with open(os.path.join(root, "watches.yml"), "w") as fh:
            fh.write(WATCHES.replace("last_fired: null", 'last_fired: "2026-07-18"')
                            .replace('"2026-07-01"', '"2026-07-18"'))
        proc = subprocess.run([sys.executable, os.path.join(WATCH, "due.py"),
                               "--root", root, "--today", "2026-07-18"],
                              capture_output=True, text=True)
        self.assertEqual(proc.stdout.strip(), "NONE DUE")

        with open(os.path.join(root, "watches.yml"), "w") as fh:
            fh.write(WATCHES)
        proc = subprocess.run([sys.executable, os.path.join(WATCH, "due.py"),
                               "--root", root, "--today", "2026-07-18"],
                              capture_output=True, text=True)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["today"], "2026-07-18")
        self.assertEqual([w["id"] for w in payload["due"]], ["fresh-watch", "lapsed-watch"])

    def test_missing_file_prints_none_due(self):
        root = tempfile.mkdtemp(prefix="watch-test-")
        proc = subprocess.run([sys.executable, os.path.join(WATCH, "due.py"), "--root", root],
                              capture_output=True, text=True)
        self.assertEqual(proc.stdout.strip(), "NONE DUE")


class FireTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="fire-test-")
        self.yml = os.path.join(self.root, "watches.yml")
        with open(self.yml, "w") as fh:
            fh.write(WATCHES)

    def test_match_writes_stub_and_targets_one_last_fired(self):
        rc = fire.main(["match", "--id", "lapsed-watch", "--url", "https://ex.org/x",
                        "--body", 'It happened "today" (Example)', "--root", self.root,
                        "--today", "2026-07-18"])
        self.assertEqual(rc, 0)
        stub_dir = os.path.join(self.root, "pending-notifications")
        (name,) = os.listdir(stub_dir)
        self.assertRegex(name, r"^\d{8}T\d{6}Z-watch-lapsed-watch\.json$")
        with open(os.path.join(stub_dir, name)) as fh:
            stub = json.load(fh)
        self.assertEqual(stub["title"], "Watch fired -- lapsed-watch")
        self.assertEqual(stub["tags"], "eyes")
        self.assertEqual(stub["body"], 'It happened "today" (Example)')

        with open(self.yml) as fh:
            text = fh.read()
        self.assertEqual(text, WATCHES.replace('last_fired: "2026-07-01"',
                                               'last_fired: "2026-07-18"'))
        self.assertIn("# Comment line that MUST survive edits.", text)
        self.assertIn("last_fired: null", text)            # other entries untouched
        self.assertIn('last_fired: "2026-07-15"', text)

    def test_unknown_id_writes_nothing(self):
        rc = fire.main(["match", "--id", "nope", "--url", "u", "--body", "b",
                        "--root", self.root])
        self.assertEqual(rc, 1)
        self.assertFalse(os.path.exists(os.path.join(self.root, "pending-notifications")))

    def test_push_derives_commit_message_from_stubs(self):
        subprocess.run(["git", "init", "-q", self.root], capture_output=True)
        subprocess.run(["git", "-C", self.root, "add", "-A"], capture_output=True)
        subprocess.run(["git", "-C", self.root, "-c", "user.email=t@t", "-c", "user.name=t",
                        "-c", "commit.gpgsign=false", "commit", "-qm", "init"],
                       capture_output=True)
        fire.main(["match", "--id", "fresh-watch", "--url", "https://ex.org",
                   "--body", "b", "--root", self.root, "--today", "2026-07-18"])
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = fire.main(["push", "--root", self.root, "--dry-run"])
        self.assertEqual(rc, 0)
        self.assertIn("Watch fired: fresh-watch", buf.getvalue())

    def test_push_is_noop_when_clean(self):
        subprocess.run(["git", "init", "-q", self.root], capture_output=True)
        subprocess.run(["git", "-C", self.root, "add", "-A"], capture_output=True)
        subprocess.run(["git", "-C", self.root, "-c", "user.email=t@t", "-c", "user.name=t",
                        "-c", "commit.gpgsign=false", "commit", "-qm", "init"],
                       capture_output=True)
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = fire.main(["push", "--root", self.root, "--dry-run"])
        self.assertEqual(rc, 0)
        self.assertIn("nothing to push", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
