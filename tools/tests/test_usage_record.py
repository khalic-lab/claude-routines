"""Spec tests for tools/usage/record.py -- the two entry points, the git tail, the gate.

The --hook mode is exercised as a SUBPROCESS with a fake `git` first on PATH (a shell shim
that logs its argv and exits 0, or a variant that fails `push` twice then succeeds). That
proves the exact add -> commit(path-scoped) -> push argv sequence, the three-attempt
rebase-between-pushes loop, exit 0 on every git failure, no JSON on stdout, idempotency, and
the macOS gate. --find is exercised in-process against a temp CLAUDE_CONFIG_DIR.
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
import types
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECORD = os.path.join(TOOLS, "usage", "record.py")
FIX = os.path.join(TOOLS, "tests", "fixtures", "usage", "sample-session.jsonl")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


record = _load("usage_record", RECORD)


# A fake git that logs every invocation as a "===\n"-separated block of its argv lines.
_GIT_SUCCESS = """#!/bin/sh
printf '%s\\n' "$@" >> "$GITLOG"
printf '===\\n' >> "$GITLOG"
exit 0
"""

# Fails `push` twice then succeeds; reports a dirty tree on `status` so the stash step fires.
_GIT_RETRY = """#!/bin/sh
printf '%s\\n' "$@" >> "$GITLOG"
printf '===\\n' >> "$GITLOG"
for a in "$@"; do
  if [ "$a" = "status" ]; then echo " M some/other/file"; exit 0; fi
  if [ "$a" = "push" ]; then
    n=`cat "$PUSHCOUNT" 2>/dev/null || echo 0`
    n=`expr $n + 1`
    echo "$n" > "$PUSHCOUNT"
    if [ "$n" -le 2 ]; then exit 1; fi
    exit 0
  fi
done
exit 0
"""


def _op(argv):
    """Strip the leading `-c key=val` pairs, returning the git operation + its args."""
    i = 0
    while i + 1 < len(argv) and argv[i] == "-c":
        i += 2
    return argv[i:]


def _parse_log(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        blocks = fh.read().split("===\n")
    return [b.splitlines() for b in blocks if b.strip()]


def _lines(path):
    with open(path, encoding="utf-8") as fh:
        return [l for l in fh if l.strip()]


def _first_record(path):
    return json.loads(_lines(path)[0])


class HookGitProtocolTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="usage-hook-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.bindir = tempfile.mkdtemp(prefix="usage-fakebin-")
        self.addCleanup(shutil.rmtree, self.bindir, ignore_errors=True)
        self.gitlog = os.path.join(self.root, "git.log")
        self.pushcount = os.path.join(self.root, "pushcount")

    def _write_git(self, body):
        p = os.path.join(self.bindir, "git")
        with open(p, "w") as fh:
            fh.write(body)
        os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    def _run_hook(self, payload, extra_env=None):
        env = dict(os.environ)
        env["PATH"] = self.bindir + os.pathsep + env["PATH"]
        env["GITLOG"] = self.gitlog
        env["PUSHCOUNT"] = self.pushcount
        env["USAGE_RECORD_LOCAL"] = "1"  # bypass the macOS gate so the git path runs
        if extra_env:
            env.update(extra_env)
        return subprocess.run([sys.executable, RECORD, "--hook"], input=json.dumps(payload),
                              env=env, cwd=self.root, capture_output=True, text=True)

    def _payload(self, event="Stop"):
        return {"session_id": "sess-news-abc", "transcript_path": FIX,
                "cwd": self.root, "hook_event_name": event}

    def test_happy_path_argv_sequence(self):
        self._write_git(_GIT_SUCCESS)
        proc = self._run_hook(self._payload())
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "", "a Stop hook must not print to stdout")
        ops = [_op(b) for b in _parse_log(self.gitlog)]
        firsts = [o[0] for o in ops]
        self.assertEqual(firsts, ["add", "commit", "push"])
        self.assertEqual(ops[0], ["add", "index/usage/"])
        # commit is path-scoped so nothing else the routine staged is swept in.
        self.assertIn("-m", ops[1])
        self.assertEqual(ops[1][-2:], ["--", "index/usage/"])
        self.assertEqual(ops[2], ["push", "origin", "HEAD:refs/heads/main"])

    def test_record_written(self):
        self._write_git(_GIT_SUCCESS)
        self._run_hook(self._payload())
        out = os.path.join(self.root, "index", "usage", "2026-09-news.jsonl")
        self.assertTrue(os.path.exists(out))
        lines = _lines(out)
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        self.assertEqual(rec["stage"], "stop")
        self.assertEqual(rec["routine"], "news")
        self.assertEqual(rec["hook_event"], "Stop")

    def test_session_end_event_maps_to_stage(self):
        self._write_git(_GIT_SUCCESS)
        self._run_hook(self._payload(event="SessionEnd"))
        out = os.path.join(self.root, "index", "usage", "2026-09-news.jsonl")
        rec = _first_record(out)
        self.assertEqual(rec["stage"], "session-end")
        self.assertEqual(rec["hook_event"], "SessionEnd")

    def test_push_retry_loop(self):
        self._write_git(_GIT_RETRY)
        proc = self._run_hook(self._payload())
        self.assertEqual(proc.returncode, 0, "hook must exit 0 even while push fails")
        firsts = [_op(b)[0] for b in _parse_log(self.gitlog)]
        # add, commit, then push(fail) -> status,stash,pull -> push(fail) -> status,stash,pull -> push(ok)
        self.assertEqual(firsts, ["add", "commit", "push", "status", "stash", "pull",
                                  "push", "status", "stash", "pull", "push"])

    def test_idempotent_second_run_does_no_git(self):
        self._write_git(_GIT_SUCCESS)
        self._run_hook(self._payload())
        os.remove(self.gitlog)  # forget the first run's git calls
        proc = self._run_hook(self._payload())
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(_parse_log(self.gitlog), [], "duplicate (session,stage) must skip git")
        out = os.path.join(self.root, "index", "usage", "2026-09-news.jsonl")
        self.assertEqual(len(_lines(out)), 1)

    def test_session_end_after_stop_does_no_git(self):
        # A run that fires Stop THEN SessionEnd must land ONE record and do git exactly once:
        # the SessionEnd hook is a no-op because a stop record for the session is already on
        # file (idempotency spans stop OR session-end, not the exact stage).
        self._write_git(_GIT_SUCCESS)
        self._run_hook(self._payload(event="Stop"))
        os.remove(self.gitlog)  # forget the Stop run's git calls
        proc = self._run_hook(self._payload(event="SessionEnd"))
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(_parse_log(self.gitlog), [],
                         "SessionEnd after Stop must skip git entirely")
        out = os.path.join(self.root, "index", "usage", "2026-09-news.jsonl")
        lines = _lines(out)
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["stage"], "stop")  # the first hook's record wins

    def test_publish_record_does_not_block_hook(self):
        # A publish-stage record for the session must NOT stop the hook from recording: the
        # hook measurement supersedes the publish one (fold prefers stop > publish).
        self._write_git(_GIT_SUCCESS)
        out = os.path.join(self.root, "index", "usage", "2026-09-news.jsonl")
        os.makedirs(os.path.dirname(out))
        with open(out, "w") as fh:
            fh.write(json.dumps({"session_id": "sess-news-abc", "stage": "publish",
                                 "routine": "news", "started": "2026-09-14T10:00:00Z"}) + "\n")
        proc = self._run_hook(self._payload(event="Stop"))
        self.assertEqual(proc.returncode, 0)
        firsts = [_op(b)[0] for b in _parse_log(self.gitlog)]
        self.assertEqual(firsts[:3], ["add", "commit", "push"],
                         "the hook must commit past a publish-stage record")
        self.assertEqual(len(_lines(out)), 2)  # publish record kept, stop record appended

    def test_macos_gate_blocks_without_optin(self):
        # This test host is macOS; without USAGE_RECORD_LOCAL the hook must be a silent no-op.
        if record.platform.system() != "Darwin":
            self.skipTest("gate only closes on macOS")
        self._write_git(_GIT_SUCCESS)
        env = dict(os.environ)
        env["PATH"] = self.bindir + os.pathsep + env["PATH"]
        env["GITLOG"] = self.gitlog
        env.pop("USAGE_RECORD_LOCAL", None)
        proc = subprocess.run([sys.executable, RECORD, "--hook"],
                              input=json.dumps(self._payload()),
                              env=env, cwd=self.root, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(_parse_log(self.gitlog), [])
        self.assertFalse(os.path.exists(os.path.join(self.root, "index", "usage")))


class FindTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="usage-find-repo-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.cfg = tempfile.mkdtemp(prefix="usage-find-cfg-")
        self.addCleanup(shutil.rmtree, self.cfg, ignore_errors=True)
        self.projects = os.path.join(self.cfg, "projects", "enc-dir")
        os.makedirs(self.projects)

    def _write_transcript(self, name, cwd, ts):
        path = os.path.join(self.projects, name)
        user = {"type": "user", "timestamp": ts, "cwd": cwd, "sessionId": "live-sess",
                "message": {"role": "user", "content": "routines/news.md"}}
        asst = {"type": "assistant", "timestamp": ts, "cwd": cwd, "sessionId": "live-sess",
                "version": "2.1.141",
                "message": {"id": "m1", "model": "claude-opus-4-8",
                            "content": [{"type": "text", "text": "hi"}],
                            "usage": {"input_tokens": 10, "output_tokens": 5}}}
        with open(path, "w") as fh:
            fh.write(json.dumps(user) + "\n" + json.dumps(asst) + "\n")
        return path

    def test_find_live_transcript_picks_fresh_matching_cwd(self):
        now = dt.datetime(2026, 9, 13, 12, 0, 0, tzinfo=dt.timezone.utc)
        fresh = (now - dt.timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
        stale = (now - dt.timedelta(minutes=40)).strftime("%Y-%m-%dT%H:%M:%SZ")
        want = self._write_transcript("fresh.jsonl", self.root, fresh)
        self._write_transcript("stale.jsonl", self.root, stale)          # too old
        self._write_transcript("elsewhere.jsonl", "/some/other/repo", fresh)  # wrong cwd
        path, scanned = record.find_live_transcript([self.cfg], self.root, now=now)
        self.assertEqual(path, want)
        self.assertEqual(scanned, 3)

    def test_find_none_when_all_stale(self):
        now = dt.datetime(2026, 9, 13, 12, 0, 0, tzinfo=dt.timezone.utc)
        stale = (now - dt.timedelta(minutes=45)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self._write_transcript("stale.jsonl", self.root, stale)
        path, scanned = record.find_live_transcript([self.cfg], self.root, now=now)
        self.assertIsNone(path)
        self.assertEqual(scanned, 1)

    def test_cmd_find_appends_publish_record(self):
        now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self._write_transcript("live.jsonl", self.root, now)
        env_keep = {k: os.environ.get(k) for k in ("CLAUDE_CONFIG_DIR", "USAGE_RECORD_LOCAL")}
        os.environ["CLAUDE_CONFIG_DIR"] = self.cfg
        os.environ["USAGE_RECORD_LOCAL"] = "1"
        try:
            args = types.SimpleNamespace(root=self.root, slug="news", date="2026-09-13",
                                         stage="publish")
            import contextlib
            import io
            with contextlib.redirect_stdout(io.StringIO()):
                rc = record.cmd_find(args)
        finally:
            for k, v in env_keep.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        self.assertEqual(rc, 0)
        month = now[:7]
        out = os.path.join(self.root, "index", "usage", "%s-news.jsonl" % month)
        self.assertTrue(os.path.exists(out))
        rec = _first_record(out)
        self.assertEqual(rec["stage"], "publish")
        self.assertEqual(rec["routine"], "news")            # slug override
        self.assertEqual(rec["edition"], "2026-09-13-news")  # fallback from slug+date


class PublishStepTest(unittest.TestCase):
    """The publish tail must invoke the usage --find step for EVERY slug (evaluator too),
    after the analytics steps and before the stub. test_publish.py's own order pin filters by
    a fixed set of known step names and so tolerates the addition; this pins the new step
    itself so it cannot silently regress."""

    def setUp(self):
        self.publish = _load("usage_publish", os.path.join(TOOLS, "publish.py"))
        self.root = tempfile.mkdtemp(prefix="usage-publish-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def _dry_run(self, slug, date):
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = self.publish.main(["--slug", slug, "--date", date, "--root", self.root,
                                    "--notify-body", "teaser", "--dry-run"])
        return rc, buf.getvalue()

    def test_usage_step_present_for_writer(self):
        rc, out = self._dry_run("news", "2026-09-14")
        self.assertEqual(rc, 0)
        self.assertIn("DRY-RUN usage", out)
        self.assertIn("tools/usage/record.py --find --stage publish "
                      "--slug news --date 2026-09-14", out)
        # runs after plane-push, before the stub.
        self.assertLess(out.index("DRY-RUN plane-push"), out.index("DRY-RUN usage"))
        self.assertLess(out.index("DRY-RUN usage"), out.index("DRY-RUN stub"))

    def test_usage_step_present_for_evaluator(self):
        rc, out = self._dry_run("evaluator", "2026-09-14")
        self.assertEqual(rc, 0)
        self.assertIn("preprocessing: skipped", out)  # evaluator records no stories
        self.assertIn("tools/usage/record.py --find --stage publish "
                      "--slug evaluator --date 2026-09-14", out)
        self.assertLess(out.index("DRY-RUN usage"), out.index("DRY-RUN stub"))


class FlatCacheCreationRecordTest(unittest.TestCase):
    """A transcript in the FLAT cache_creation_input_tokens shape (the shape older lines use)
    must land cache_write_1h = 0 and cache_write_5m = the flat value in the RECORD -- not only
    inside the parser -- so nothing is ever billed at the 1h write rate. `models` is what
    pricing.cost() consumes, so it is pinned alongside `totals`."""

    def test_flat_cache_creation_zeroes_1h_in_record(self):
        tmp = tempfile.mkdtemp(prefix="usage-flat-")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        path = os.path.join(tmp, "flat.jsonl")
        user = {"type": "user", "timestamp": "2026-09-14T10:00:00Z", "cwd": "/repo",
                "sessionId": "sess-flat",
                "message": {"role": "user", "content": "routines/news.md"}}
        asst = {"type": "assistant", "timestamp": "2026-09-14T10:01:00Z", "cwd": "/repo",
                "sessionId": "sess-flat", "version": "2.1.141",
                "message": {"id": "m1", "model": "claude-opus-4-8",
                            "content": [{"type": "text", "text": "hi"}],
                            "usage": {"input_tokens": 10, "cache_creation_input_tokens": 4200,
                                      "cache_read_input_tokens": 0, "output_tokens": 5}}}
        with open(path, "w") as fh:
            fh.write(json.dumps(user) + "\n" + json.dumps(asst) + "\n")
        rec = record.build_record(record.transcript_mod.parse(path), "stop")
        self.assertEqual(rec["totals"]["cache_write_1h"], 0)
        self.assertEqual(rec["totals"]["cache_write_5m"], 4200)
        model = rec["models"]["claude-opus-4-8"]
        self.assertEqual(model["cache_write_1h"], 0)
        self.assertEqual(model["cache_write_5m"], 4200)


class BuildRecordTest(unittest.TestCase):
    def test_default_tool_keys_present(self):
        measurement = {"tool_calls": {"Bash": 3, "Task": 1}, "models": {}}
        rec = record.build_record(measurement, "stop")
        for t in ("Bash", "WebFetch", "WebSearch", "Read", "Write", "Edit", "Glob", "Grep"):
            self.assertIn(t, rec["tool_calls"])
        self.assertEqual(rec["tool_calls"]["Bash"], 3)
        self.assertEqual(rec["tool_calls"]["Task"], 1)  # extra observed tools kept too
        self.assertEqual(rec["v"], 1)


if __name__ == "__main__":
    unittest.main()
