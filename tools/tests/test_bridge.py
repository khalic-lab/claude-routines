"""Spec tests for tools/bridge/bridge.sh (the local ntfy bridge) and tools/bridge/install.sh.

The bridge runs ticks against a throwaway repo with a bare origin, under macOS's /bin/bash
(cron's `env bash` resolves to it), with HOME pointed at a temp dir so the real log is never
touched. ntfy is unreachable on purpose (127.0.0.1:9), so every alert the bridge tries shows
up in its log as "WARN: ntfy alert '<title>' failed to send" -- that is what is asserted.
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
        with open(os.path.join(self.bridge_dir, ".env"), "w") as fh:
            fh.write("NTFY_TOPIC=test-topic\nNTFY_SERVER=http://127.0.0.1:9\nREPO=%s\n" % self.repo)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _tick(self):
        env = {"HOME": self.home, "PATH": os.environ.get("PATH", "/usr/bin:/bin")}
        return subprocess.run([BASH, os.path.join(self.bridge_dir, "bridge.sh")], env=env,
                              capture_output=True, text=True, timeout=120).returncode

    def _log(self):
        with open(os.path.join(self.home, "Library", "Logs", "news-brief-bridge.log")) as fh:
            return fh.read()

    def _alerts(self, title):
        return self._log().count("WARN: ntfy alert '%s' failed to send" % title)

    def test_pull_failure_streak_alerts_once_then_recovers(self):
        _git(self.repo, "remote", "set-url", "origin", os.path.join(self.tmp, "missing.git"))
        for _ in range(7):
            self.assertEqual(self._tick(), 1)
        self.assertEqual(self._alerts("Bridge: git pull failing"), 1)
        with open(os.path.join(self.bridge_dir, ".pull-fail-count")) as fh:
            self.assertEqual(fh.read().strip(), "7")
        _git(self.repo, "remote", "set-url", "origin", self.origin)
        self._tick()
        self.assertEqual(self._alerts("Bridge: pulling again"), 1)
        with open(os.path.join(self.bridge_dir, ".pull-fail-count")) as fh:
            self.assertEqual(fh.read().strip(), "0")

    def test_short_streak_never_alerts(self):
        _git(self.repo, "remote", "set-url", "origin", os.path.join(self.tmp, "missing.git"))
        for _ in range(3):
            self._tick()
        _git(self.repo, "remote", "set-url", "origin", self.origin)
        self._tick()
        self.assertEqual(self._alerts("Bridge: git pull failing"), 0)
        self.assertEqual(self._alerts("Bridge: pulling again"), 0)

    def test_overdue_editions_alert_once_each(self):
        # The seed repo has no posts, so every writer slot of the last 48h is overdue.
        self._tick()
        first = len(re.findall(r"WARN: ntfy alert 'Missing edition: [^']+' failed", self._log()))
        self.assertGreater(first, 0)
        self._tick()
        again = len(re.findall(r"WARN: ntfy alert 'Missing edition: [^']+' failed", self._log()))
        self.assertEqual(again, first)
        with open(os.path.join(self.bridge_dir, ".freshness-alerted.json")) as fh:
            self.assertEqual(len(json.load(fh)), first)
        self.assertNotIn("test-topic", self._log())

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
