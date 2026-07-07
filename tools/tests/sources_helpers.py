"""Shared plumbing for the tools/sources/*.py RED-phase tests.

Every script under test is CLI-only per the interface contract (no documented importable
function API, unlike store.py) so these tests black-box them via subprocess rather than
importlib — a script that doesn't exist yet fails with a clear assertion, not a discovery-
killing import crash, and internal function/class names are never dictated.
"""
import datetime
import json
import os
import shutil
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TOOLS_SOURCES_DIR = os.path.join(REPO_ROOT, "tools", "sources")
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "sources")
INDEX_STORIES_FIXTURE = os.path.join(FIXTURES_DIR, "index_stories")


def script_path(name):
    return os.path.join(TOOLS_SOURCES_DIR, name)


def assert_script_exists(testcase, name):
    """Raise a plain AssertionError (not a TestCase-bound assert*) so this works whether
    `testcase` is a live instance (called from setUp) or the class itself (called from
    setUpClass, where `self.assertTrue` would silently mis-bind instead of failing)."""
    path = script_path(name)
    if not os.path.exists(path):
        raise AssertionError(
            "tools/sources/%s does not exist yet — implement it at %s (RED phase: this "
            "failure is expected until the GREEN-phase implementation lands)" % (name, path)
        )
    return path


def run_script(testcase, name, args, timeout=60):
    """Invoke `python3 tools/sources/<name> <args>`, asserting the script exists first."""
    path = assert_script_exists(testcase, name)
    proc = subprocess.run(
        [sys.executable, path] + list(args),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return proc


def seed_index_stories(root, extra_files=None):
    """Copy the shared bootstrap fixture (+ optional extra {filename: [records]}) into
    <root>/index/stories/."""
    dest = os.path.join(root, "index", "stories")
    os.makedirs(dest, exist_ok=True)
    for fname in os.listdir(INDEX_STORIES_FIXTURE):
        shutil.copy(os.path.join(INDEX_STORIES_FIXTURE, fname), os.path.join(dest, fname))
    if extra_files:
        for fname, records in extra_files.items():
            with open(os.path.join(dest, fname), "w") as f:
                for r in records:
                    f.write(json.dumps(r) + "\n")
    return dest


def write_jsonl(path, records):
    with open(path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def days_ago(n, fmt="%Y-%m-%d"):
    """A date string N days before *real* today, for rolling-window (30d) fixtures that must
    stay correct no matter what date this suite actually runs on. Deliberately used only for
    clearly-inside vs. clearly-outside cases (e.g. 5d vs. 45d) -- the contract doesn't pin
    inclusive/exclusive treatment of the exact 30-day edge, so tests avoid asserting on it."""
    now = datetime.datetime.now(datetime.timezone.utc)
    return (now - datetime.timedelta(days=n)).strftime(fmt)


def read_jsonl(path):
    if not os.path.exists(path):
        return []
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out
