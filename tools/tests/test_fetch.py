"""Spec tests for tools/fetch.py -- the logging curl->proxy fallback chain.

Curl is PATH-shimmed with a fake whose behavior is driven by FAKE_DIRECT_STATUS /
FAKE_PROXY_STATUS env vars (a proxy call is recognized by its `-G` flag), so the
chain, exit semantics, and the one-JSON-line-per-ATTEMPT log contract are all
asserted without any network.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FETCH = os.path.join(TOOLS, "fetch.py")

FAKE_CURL = """#!%s
import os, sys
args = sys.argv[1:]
# real curl globs [..] / {..} in a URL unless -g is given, and exits 3 before any request
if not any(a.startswith("-") and not a.startswith("--") and "g" in a for a in args) and any(
        ("[" in a or "{" in a) and "://" in a for a in args):
    sys.exit(3)
out = args[args.index("-o") + 1]
is_proxy = "-G" in args
status = os.environ.get("FAKE_PROXY_STATUS" if is_proxy else "FAKE_DIRECT_STATUS", "200")
with open(out, "w") as fh:
    fh.write(("PROXY" if is_proxy else "DIRECT") + "BODY" if status == "200" else "")
sys.stdout.write(status)
""" % sys.executable


class FetchTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="fetch-test-")
        curl = os.path.join(self.dir, "curl")
        with open(curl, "w") as fh:
            fh.write(FAKE_CURL)
        os.chmod(curl, 0o755)
        self.log = os.path.join(self.dir, "fetch.log")

    def run_fetch(self, argv, direct="200", proxy="200", token="tok"):
        env = dict(os.environ)
        env["PATH"] = self.dir + os.pathsep + env["PATH"]
        env["FAKE_DIRECT_STATUS"] = direct
        env["FAKE_PROXY_STATUS"] = proxy
        env.pop("FETCH_PROXY_TOKEN", None)
        if token:
            env["FETCH_PROXY_TOKEN"] = token
        return subprocess.run([sys.executable, FETCH] + argv + ["--log", self.log],
                              capture_output=True, text=True, env=env)

    def log_lines(self):
        if not os.path.exists(self.log):
            return []
        with open(self.log) as fh:
            return [json.loads(l) for l in fh if l.strip()]

    def test_direct_success_logs_one_attempt(self):
        proc = self.run_fetch(["https://ok.example/feed"])
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "DIRECTBODY")
        lines = self.log_lines()
        self.assertEqual([(l["method"], l["status"], l["ok"]) for l in lines],
                         [("curl", 200, True)])
        self.assertEqual(lines[0]["url"], "https://ok.example/feed")

    def test_bracketed_query_url_is_not_globbed(self):
        url = ("http://export.arxiv.org/api/query?search_query=cat:cs.LG+AND+"
               "submittedDate:[202611190000+TO+202611260000]&max_results=100")
        proc = self.run_fetch([url])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual([(l["method"], l["status"]) for l in self.log_lines()], [("curl", 200)])

    def test_direct_403_falls_back_to_proxy_and_logs_both(self):
        proc = self.run_fetch(["https://blocked.example/page"], direct="403")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "PROXYBODY")
        self.assertEqual([(l["method"], l["status"], l["ok"]) for l in self.log_lines()],
                         [("curl", 403, False), ("proxy", 200, True)])

    def test_no_token_skips_proxy_and_fails(self):
        proc = self.run_fetch(["https://blocked.example/page"], direct="403", token=None)
        self.assertEqual(proc.returncode, 22)
        self.assertEqual(proc.stdout, "")
        self.assertEqual([l["method"] for l in self.log_lines()], ["curl"])

    def test_proxy_flag_skips_direct_attempt(self):
        proc = self.run_fetch(["--proxy", "https://cdn-blocked.example/x"])
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "PROXYBODY")
        self.assertEqual([l["method"] for l in self.log_lines()], ["proxy"])

    def test_proxy_flag_without_token_still_tries_direct(self):
        proc = self.run_fetch(["--proxy", "https://x.example/y"], token=None)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "DIRECTBODY")
        self.assertEqual([l["method"] for l in self.log_lines()], ["curl"])

    def test_total_failure_exits_22(self):
        proc = self.run_fetch(["https://down.example/z"], direct="500", proxy="502")
        self.assertEqual(proc.returncode, 22)
        self.assertEqual([(l["method"], l["ok"]) for l in self.log_lines()],
                         [("curl", False), ("proxy", False)])

class RateLimitTest(unittest.TestCase):
    # FetchTest's curl shim and helpers, without re-running FetchTest's own tests
    setUp = FetchTest.setUp
    run_fetch = FetchTest.run_fetch
    log_lines = FetchTest.log_lines

    def test_three_429s_trip_the_breaker_for_that_host_only(self):
        for _ in range(2):   # each call: direct 429 + proxy 429 -> 2 logged 429s per call
            self.assertEqual(self.run_fetch(["https://api.ratelimited.example/w?x"],
                                            direct="429", proxy="429").returncode, 22)
        proc = self.run_fetch(["https://api.ratelimited.example/w?y"], direct="200")
        self.assertEqual(proc.returncode, 22, "a tripped host must not be called again")
        self.assertEqual(self.log_lines()[-1]["status"], "SKIP:429")
        other = self.run_fetch(["https://fine.example/feed"])
        self.assertEqual(other.returncode, 0, "the breaker is per host")

    def test_a_success_resets_the_breaker(self):
        self.run_fetch(["https://flaky.example/a"], direct="429", proxy="200")
        self.run_fetch(["https://flaky.example/b"], direct="429", proxy="429")
        proc = self.run_fetch(["https://flaky.example/c"], direct="200")
        self.assertEqual(proc.returncode, 0)

    def test_breaker_lapses_after_the_hold(self):
        with open(self.log, "w") as fh:
            for _ in range(3):
                fh.write(json.dumps({"ts": "2026-01-01T00:00:00Z", "url": "https://old.example/x",
                                     "method": "proxy", "status": 429, "ok": False}) + "\n")
        self.assertEqual(self.run_fetch(["https://old.example/y"]).returncode, 0)

    def test_paced_host_is_never_tripped(self):
        with open(self.log, "w") as fh:
            for _ in range(3):
                fh.write(json.dumps({"ts": "2026-01-01T00:00:00Z",
                                     "url": "https://export.arxiv.org/api/query?a",
                                     "method": "curl", "status": 429, "ok": False}) + "\n")
        self.assertEqual(self.run_fetch(["https://export.arxiv.org/rss/cs.LG"]).returncode, 0)


if __name__ == "__main__":
    unittest.main()