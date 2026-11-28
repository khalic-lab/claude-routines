"""Spec tests for the idle-Watch thinning (2026-11-28): transcript.watch_idle, record.py's
one-idle-record-a-day rule, and fold.py's separately labelled estimate.

Contract: a Watch tick counts as idle only on positive proof (due.py ran and printed NONE DUE,
nothing searched, fetched or fired); the first idle tick of a day is recorded and committed,
later idle ticks that day write and commit nothing; a tick that fired is always recorded; the
fold keeps measured cost as measured and reports the skipped ticks as `estimated_idle`.
"""
import datetime as dt
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(TOOLS)
RECORD = os.path.join(TOOLS, "usage", "record.py")
WATCH_PROMPT = "Poll the topic-watch registry ... `python3 tools/watch/due.py` ..."


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


transcript = _load("usage_transcript_idle", os.path.join(TOOLS, "usage", "transcript.py"))
fold = _load("usage_fold_idle", os.path.join(TOOLS, "usage", "fold.py"))

_GIT_OK = """#!/bin/sh
printf '%s\\n' "$*" >> "$GITLOG"
exit 0
"""


def _watch_transcript(path, ts, result="NONE DUE", extra_bash=None, search=False):
    lines = [
        {"type": "user", "sessionId": "s-" + ts, "timestamp": ts, "cwd": "/repo",
         "message": {"role": "user", "content": WATCH_PROMPT}},
        {"type": "assistant", "timestamp": ts, "message": {
            "id": "m1-" + ts, "model": "claude-haiku-5-5",
            "usage": {"input_tokens": 4, "cache_read_input_tokens": 40000, "output_tokens": 100},
            "content": [{"type": "tool_use", "id": "t1", "name": "Bash", "input": {
                "command": "git pull --ff-only origin main && python3 tools/watch/due.py"}}]}},
        {"type": "user", "timestamp": ts, "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "t1", "content": result}]}},
    ]
    content = []
    if search:
        content.append({"type": "tool_use", "id": "t2", "name": "WebSearch", "input": {"query": "q"}})
    if extra_bash:
        content.append({"type": "tool_use", "id": "t3", "name": "Bash", "input": {"command": extra_bash}})
    lines.append({"type": "assistant", "timestamp": ts, "message": {
        "id": "m2-" + ts, "model": "claude-haiku-5-5",
        "usage": {"input_tokens": 2, "cache_read_input_tokens": 41000, "output_tokens": 80},
        "content": content or [{"type": "text", "text": "NONE DUE, stopping."}]}})
    with open(path, "w") as fh:
        for l in lines:
            fh.write(json.dumps(l) + "\n")


class WatchIdleTest(unittest.TestCase):
    def test_positive_proof_only(self):
        due = ["git pull --ff-only origin main && python3 tools/watch/due.py"]
        self.assertTrue(transcript.watch_idle(due, ["NONE DUE"], {}))
        self.assertFalse(transcript.watch_idle(due, ['[{"id": "x"}]'], {}), "something was due")
        self.assertFalse(transcript.watch_idle([], ["NONE DUE"], {}), "due.py never ran")
        self.assertFalse(transcript.watch_idle(due, ["NONE DUE"], {"WebSearch": 1}))
        self.assertFalse(transcript.watch_idle(due + ["python3 tools/watch/fire.py push"],
                                               ["NONE DUE"], {}))
        self.assertFalse(transcript.watch_idle(due, ["Traceback ... due.py"], {}), "an error is not idle")

    def test_parse_sets_idle_for_watch_only(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "w.jsonl")
            _watch_transcript(p, "2026-11-29T01:27:10.000Z")
            m = transcript.parse(p)
            self.assertEqual((m["routine"], m["idle"]), ("watch", True))
            _watch_transcript(p, "2026-11-29T01:27:10.000Z", result='[{"id": "x"}]', search=True,
                              extra_bash='python3 tools/watch/fire.py match --id x --url u --body b')
            self.assertFalse(transcript.parse(p)["idle"])
            self.assertIsNone(transcript.parse(p, routine="news")["idle"])


class RecordIdleTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="idle-watch-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.bindir = os.path.join(self.root, "bin")
        os.makedirs(self.bindir)
        git = os.path.join(self.bindir, "git")
        with open(git, "w") as fh:
            fh.write(_GIT_OK)
        os.chmod(git, os.stat(git).st_mode | stat.S_IEXEC)
        self.gitlog = os.path.join(self.root, "git.log")
        self.n = 0

    def _tick(self, ts, **kw):
        self.n += 1
        tpath = os.path.join(self.root, "t%d.jsonl" % self.n)
        _watch_transcript(tpath, ts, **kw)
        env = dict(os.environ, PATH=self.bindir + os.pathsep + os.environ["PATH"],
                   GITLOG=self.gitlog, USAGE_RECORD_LOCAL="1")
        payload = {"session_id": "sess-%d" % self.n, "transcript_path": tpath,
                   "cwd": self.root, "hook_event_name": "Stop"}
        proc = subprocess.run([sys.executable, RECORD, "--hook"], input=json.dumps(payload),
                              env=env, cwd=self.root, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")
        return proc.stderr

    def _records(self):
        path = os.path.join(self.root, "index", "usage", "2026-11-watch.jsonl")
        with open(path) as fh:
            return [json.loads(l) for l in fh if l.strip()]

    def _commits(self):
        if not os.path.exists(self.gitlog):
            return 0
        with open(self.gitlog) as fh:
            return sum(1 for l in fh if l.startswith("-c") and " commit " in l)

    def test_one_idle_record_a_day_and_every_fire(self):
        self._tick("2026-11-29T01:27:10.000Z")
        err = self._tick("2026-11-29T05:27:10.000Z")
        self.assertIn("idle Watch tick not recorded", err)
        self._tick("2026-11-29T09:27:10.000Z", result='[{"id": "x"}]', search=True,
                   extra_bash="python3 tools/watch/fire.py match --id x --url u --body b")
        self._tick("2026-11-30T01:27:10.000Z")  # a new day gets its own sample
        recs = self._records()
        self.assertEqual([(r["started"][:13], r["idle"]) for r in recs],
                         [("2026-11-29T01", True), ("2026-11-29T09", False), ("2026-11-30T01", True)])
        self.assertEqual(self._commits(), 3, "the skipped idle tick makes no commit")


class FoldEstimateTest(unittest.TestCase):
    def test_skipped_ticks_are_estimated_apart_from_measured_cost(self):
        root = tempfile.mkdtemp(prefix="idle-fold-")
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        os.makedirs(os.path.join(root, "routines"))
        os.makedirs(os.path.join(root, "index", "usage"))
        shutil.copy(os.path.join(REPO, "routines", "MANIFEST.md"), os.path.join(root, "routines"))

        def rec(sid, started, cost, idle):
            return {"session_id": sid, "stage": "stop", "routine": "watch", "started": started,
                    "idle": idle, "cost_usd_list": {"total": cost}, "totals": {}}
        rows = [rec("a", "2026-11-29T01:27:10Z", 0.005, True),   # the day's idle sample
                rec("b", "2026-11-29T09:27:10Z", 0.020, False),  # a tick that fired
                rec("c", "2026-11-25T01:27:10Z", 0.190, None)]   # before thinning: no estimate
        with open(os.path.join(root, "index", "usage", "2026-11-watch.jsonl"), "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        now = dt.datetime(2026, 11, 29, 12, 0, tzinfo=dt.timezone.utc)  # 13:00 Zurich
        out = fold.fold(root, as_of="2026-11-29", now=now)
        w = out["by_routine"]["watch"]
        self.assertAlmostEqual(w["cost_usd_list"], 0.215, places=6)  # measured stays measured
        # 13:00 Zurich: 02:27, 06:27, 10:27 have fired; 2 runs on file -> 1 tick estimated
        self.assertEqual(w["estimated_idle"]["ticks"], 1)
        self.assertAlmostEqual(w["estimated_idle"]["cost_usd_list"], 0.005, places=6)
        self.assertAlmostEqual(out["windows"]["7d"]["estimated_idle_cost_usd_list"], 0.005, places=6)
        later = fold.fold(root, as_of="2026-11-30",
                          now=dt.datetime(2026, 11, 30, 12, 0, tzinfo=dt.timezone.utc))
        self.assertEqual(later["by_routine"]["watch"]["estimated_idle"]["ticks"], 4)  # 6 - 2


if __name__ == "__main__":
    unittest.main()
