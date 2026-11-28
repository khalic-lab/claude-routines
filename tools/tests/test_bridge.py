"""Spec tests for tools/bridge/bridge.sh (the local ntfy bridge) and tools/bridge/install.sh.

The bridge runs ticks against a throwaway repo with a bare origin, under macOS's /bin/bash
(cron's `env bash` resolves to it), with HOME pointed at a temp dir so the real log is never
touched. ntfy is a fake `curl` put first on PATH by the test's .env (the bridge sources .env
after setting its own PATH, and the session sandbox forbids a local listening port): it
records each push's Title and answers with the HTTP code in a file the test sets, so a
delivered push (200) and a refused one (500, 429) can both be asserted.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(TOOLS)
BRIDGE = os.path.join(TOOLS, "bridge", "bridge.sh")
INSTALL = os.path.join(TOOLS, "bridge", "install.sh")
BASH = "/bin/bash" if os.path.exists("/bin/bash") else shutil.which("bash")


FAKE_CURL = """#!/bin/sh
title=""
while [ $# -gt 0 ]; do
  case "$1" in
    -H) case "$2" in "Title: "*) title="${2#Title: }" ;; esac; shift 2 ;;
    -d|-o|-w|--max-time|-X) shift 2 ;;
    *) shift ;;
  esac
done
code=$(cat "$FAKE_NTFY_CODE" 2>/dev/null || echo 200)
printf '%s\\t%s\\n' "$code" "$title" >> "$FAKE_NTFY_LOG"
printf '%s' "$code"
[ "$code" = "000" ] && exit 7
exit 0
"""


def _git(cwd, *args):
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false"]
                   + list(args), cwd=cwd, check=True, capture_output=True)


class SyntaxTest(unittest.TestCase):
    def test_scripts_parse(self):
        for path in (BRIDGE, INSTALL):
            subprocess.run([BASH, "-n", path], check=True)

    def test_topic_never_reaches_the_log(self):
        # NTFY_TOPIC is the channel's only secret; it may appear in curl targets, not in echo.
        with open(BRIDGE) as fh:
            for line in fh:
                if "NTFY_TOPIC" in line:
                    self.assertFalse(line.lstrip().startswith("echo"), line)


@unittest.skipUnless(BASH and shutil.which("git"), "needs bash + git")
class TickTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.home = os.path.join(self.tmp, "home")
        self.bridge_dir = os.path.join(self.tmp, "bridge")
        self.origin = os.path.join(self.tmp, "origin.git")
        self.repo = os.path.join(self.tmp, "repo")
        for d in (self.home, self.bridge_dir):
            os.makedirs(d)
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", self.origin], check=True)
        subprocess.run(["git", "clone", "-q", self.origin, self.repo], check=True,
                       capture_output=True)
        # the pieces the edition check needs, and nothing else from the real repo
        for rel in ("routines/MANIFEST.md", "tools/health/schedule.py",
                    "tools/health/freshness.py", "tools/evaluator/metrics.py"):
            dst = os.path.join(self.repo, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(os.path.join(REPO, rel), dst)
        os.makedirs(os.path.join(self.repo, "_posts"))
        open(os.path.join(self.repo, "_posts", ".gitkeep"), "w").close()
        _git(self.repo, "checkout", "-q", "-b", "main")
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-q", "-m", "seed")
        _git(self.repo, "push", "-q", "-u", "origin", "main")
        shutil.copy(BRIDGE, os.path.join(self.bridge_dir, "bridge.sh"))
        fakebin = os.path.join(self.tmp, "fakebin")
        os.makedirs(fakebin)
        with open(os.path.join(fakebin, "curl"), "w") as fh:
            fh.write(FAKE_CURL)
        os.chmod(os.path.join(fakebin, "curl"), 0o755)
        self.code_file = os.path.join(self.tmp, "ntfy-code")
        self.ntfy_log = os.path.join(self.tmp, "ntfy.log")
        self._ntfy(200)
        with open(os.path.join(self.bridge_dir, ".env"), "w") as fh:
            fh.write("NTFY_TOPIC=test-topic\nNTFY_SERVER=https://ntfy.invalid\nREPO=%s\n"
                     "PATH=%s:$PATH\nFAKE_NTFY_CODE=%s\nFAKE_NTFY_LOG=%s\n"
                     % (self.repo, fakebin, self.code_file, self.ntfy_log))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _ntfy(self, code):
        with open(self.code_file, "w") as fh:
            fh.write(str(code))

    def _tick(self):
        env = {"HOME": self.home, "PATH": os.environ.get("PATH", "/usr/bin:/bin")}
        return subprocess.run([BASH, os.path.join(self.bridge_dir, "bridge.sh")], env=env,
                              capture_output=True, text=True, timeout=120).returncode

    def _log(self):
        with open(os.path.join(self.home, "Library", "Logs", "news-brief-bridge.log")) as fh:
            return fh.read()

    def _pushes(self, title_re, code=None):
        """Pushes the fake ntfy saw whose Title matches; code=200 counts delivered ones."""
        if not os.path.exists(self.ntfy_log):
            return 0
        with open(self.ntfy_log) as fh:
            rows = [l.rstrip("\n").split("\t", 1) for l in fh if l.strip()]
        return sum(1 for c, t in rows if re.fullmatch(title_re, t) and (code is None or c == str(code)))

    def _state(self, name):
        path = os.path.join(self.bridge_dir, name)
        if not os.path.exists(path):
            return None
        with open(path) as fh:
            return fh.read().strip()

    def _break_origin(self):
        _git(self.repo, "remote", "set-url", "origin", os.path.join(self.tmp, "missing.git"))

    def _fix_origin(self):
        _git(self.repo, "remote", "set-url", "origin", self.origin)

    def test_pull_failure_streak_alerts_once_then_recovers(self):
        self._break_origin()
        for _ in range(7):
            self.assertEqual(self._tick(), 1)
        self.assertEqual(self._pushes("Bridge: git pull failing"), 1)
        self.assertEqual(self._state(".pull-fail-count"), "7")
        self.assertEqual(self._state(".pull-alerted"), "")
        self._fix_origin()
        self._tick()
        self.assertEqual(self._pushes("Bridge: pulling again", 200), 1)
        self.assertEqual(self._state(".pull-fail-count"), "0")
        self.assertIsNone(self._state(".pull-alerted"))
        self._tick()
        self.assertEqual(self._pushes("Bridge: pulling again"), 1, "the recovery note is sent once")

    def test_refused_push_is_retried_next_tick(self):
        # ntfy answering 429/5xx is not delivery: the alert goes out on the next good tick.
        self._break_origin()
        self._ntfy(500)
        for _ in range(7):
            self._tick()
        self.assertEqual(self._pushes("Bridge: git pull failing"), 2)  # ticks 6 and 7, both refused
        self.assertIn("WARN: ntfy alert 'Bridge: git pull failing' failed to send (HTTP 500)", self._log())
        self.assertIsNone(self._state(".pull-alerted"))
        self._ntfy(200)
        self._tick()
        self._tick()
        self.assertEqual(self._pushes("Bridge: git pull failing", 200), 1)
        self.assertEqual(self._pushes("Bridge: git pull failing"), 3)

    def test_short_streak_never_alerts(self):
        self._break_origin()
        for _ in range(3):
            self._tick()
        self._fix_origin()
        self._tick()
        self.assertEqual(self._pushes("Bridge: .*"), 0)

    def test_overdue_editions_alert_once_each(self):
        # The seed repo has no posts, so every writer slot of the last 48h is overdue.
        self._tick()
        first = self._pushes("Missing edition: .+", 200)
        self.assertGreater(first, 0)
        self._tick()
        self.assertEqual(self._pushes("Missing edition: .+"), first)
        with open(os.path.join(self.bridge_dir, ".freshness-alerted.json")) as fh:
            self.assertEqual(len(json.load(fh)), first)
        self.assertNotIn("test-topic", self._log())

    def test_overdue_edition_refused_by_ntfy_is_sent_later(self):
        self._ntfy(429)
        self._tick()
        refused = self._pushes("Missing edition: .+")
        self.assertGreater(refused, 0)
        self.assertFalse(os.path.exists(os.path.join(self.bridge_dir, ".freshness-alerted.json")))
        self._ntfy(200)
        self._tick()
        self.assertEqual(self._pushes("Missing edition: .+", 200), refused)
        self._tick()
        self.assertEqual(self._pushes("Missing edition: .+"), 2 * refused)

    def test_edition_check_crash_is_a_streak(self):
        manifest = os.path.join(self.repo, "routines", "MANIFEST.md")
        with open(manifest) as fh:
            good = fh.read()
        with open(manifest, "w") as fh:
            fh.write("# the table is gone\n")
        _git(self.repo, "commit", "-qam", "break the manifest")
        _git(self.repo, "push", "-q", "origin", "main")
        for _ in range(4):
            self.assertEqual(self._tick(), 0, "a failing check never fails the tick")
        self.assertEqual(self._pushes("Bridge: edition check failing", 200), 1)
        with open(manifest, "w") as fh:
            fh.write(good)
        _git(self.repo, "commit", "-qam", "restore the manifest")
        _git(self.repo, "push", "-q", "origin", "main")
        self._tick()
        self.assertEqual(self._pushes("Bridge: edition check works again", 200), 1)
        self.assertEqual(self._state(".freshness-fail-count"), "0")

    def test_drift_warning_when_installed_copy_differs(self):
        self._tick()
        self.assertNotIn("differs from tools/bridge/bridge.sh", self._log())  # no repo copy yet
        os.makedirs(os.path.join(self.repo, "tools", "bridge"))
        with open(os.path.join(self.repo, "tools", "bridge", "bridge.sh"), "w") as fh:
            fh.write("# a newer version\n")
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-q", "-m", "newer bridge")
        _git(self.repo, "push", "-q", "origin", "main")
        self._tick()
        self.assertIn("installed bridge.sh differs from tools/bridge/bridge.sh", self._log())


class InstallTest(unittest.TestCase):
    def test_install_backs_up_and_replaces_atomically(self):
        with tempfile.TemporaryDirectory() as d:
            dest = os.path.join(d, "bridge.sh")
            with open(dest, "w") as fh:
                fh.write("#!/bin/sh\necho old\n")
            env = dict(os.environ, BRIDGE_DIR=d)
            r = subprocess.run([BASH, INSTALL, "--check"], env=env, capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            r = subprocess.run([BASH, INSTALL], env=env, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            with open(dest) as fh, open(BRIDGE) as src:
                self.assertEqual(fh.read(), src.read())
            self.assertEqual(len([f for f in os.listdir(d) if f.startswith("bridge.sh.bak-")]), 1)
            r = subprocess.run([BASH, INSTALL, "--check"], env=env, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(os.stat(dest).st_mode & 0o777, 0o755)


if __name__ == "__main__":
    unittest.main()
