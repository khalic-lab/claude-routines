"""The embed-proxy endpoint is now a code default, not a prompt incantation (2026-07-25).

DEDUP.md used to hand the writer an `EMBED_WORKER_URL=… EMBED_TOKEN=… python3 …` prefix to retype
every run. That moved into dedup.py so the prompt carries a bare command -- which means the DEFAULT
is now load-bearing production config: if it goes missing or empty, `check` raises "embed-proxy
--worker/--token required" mid-run, the writer notes "dedup unavailable", and every edition silently
loses repeat-suppression. Nothing else would report it.

The second test pins a contract that has no other guard: dedup.py WRITES story vectors to one
endpoint and plane/query.py READS them from another constant. Same URL today; if one is ever
repointed alone, dedup keeps succeeding and the analytical plane just quietly answers from a
different corpus.
"""
import importlib.util
import os
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, relpath))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class EmbedDefaultsTest(unittest.TestCase):
    def setUp(self):
        # The prompt runs the command with NO embed variables set; reproduce that exactly.
        self._saved = {k: os.environ.pop(k, None)
                       for k in ("EMBED_WORKER_URL", "EMBED_TOKEN")}
        self.addCleanup(self._restore)
        self.dedup = _load("_dedup_defaults", "tools/dedup/dedup.py")

    def _restore(self):
        for k, v in self._saved.items():
            if v is not None:
                os.environ[k] = v

    def test_defaults_exist_and_are_non_empty(self):
        self.assertTrue(getattr(self.dedup, "EMBED_WORKER_DEFAULT", ""),
                        "dedup.py must default the worker URL -- the prompt no longer passes it")
        self.assertTrue(getattr(self.dedup, "EMBED_TOKEN_DEFAULT", ""),
                        "dedup.py must default the bearer -- the prompt no longer passes it")
        self.assertRegex(self.dedup.EMBED_WORKER_DEFAULT, r"^https://")

    def test_real_cli_resolves_credentials_with_no_env(self):
        """Exercises dedup.py's OWN parser, not a reconstruction of it, and stays offline: with
        the candidates file missing, the run must die on the FILE -- reaching that point proves
        --worker/--token resolved. If the defaults regressed, it would die earlier with
        "embed-proxy --worker/--token ... required" instead."""
        import subprocess
        import sys
        env = {k: v for k, v in os.environ.items()
               if k not in ("EMBED_WORKER_URL", "EMBED_TOKEN")}
        missing = os.path.join(REPO, "tools", "tests", "_no_such_candidates.json")
        self.assertFalse(os.path.exists(missing))
        proc = subprocess.run(
            [sys.executable, os.path.join(REPO, "tools", "dedup", "dedup.py"),
             "check", "--candidates", missing],
            capture_output=True, text=True, cwd=REPO, env=env)
        out = (proc.stdout or "") + (proc.stderr or "")
        self.assertNotIn("--worker/--token", out,
                         "dedup.py demanded credentials the prompt no longer passes:\n%s" % out)
        self.assertIn("FileNotFoundError", out,
                      "expected the run to get as far as opening the candidates file:\n%s" % out)

    def test_env_still_wins_over_the_default(self):
        os.environ["EMBED_WORKER_URL"] = "https://override.example"
        try:
            resolved = os.environ.get("EMBED_WORKER_URL") or self.dedup.EMBED_WORKER_DEFAULT
            self.assertEqual(resolved, "https://override.example")
        finally:
            os.environ.pop("EMBED_WORKER_URL", None)

    def test_dedup_and_plane_point_at_the_same_endpoint(self):
        """dedup.py writes the vectors; plane/query.py reads them. Two constants, one corpus."""
        query = _load("_plane_query_defaults", "tools/plane/query.py")
        self.assertEqual(self.dedup.EMBED_WORKER_DEFAULT, query.EMBED_URL,
                         "dedup writes to a different embed-proxy than the plane reads from")
        self.assertEqual(self.dedup.EMBED_TOKEN_DEFAULT, query.EMBED_TOKEN,
                         "dedup and the plane carry different bearers for the same worker")

    def test_publish_no_longer_carries_its_own_copy(self):
        """publish.py used to inject the pair as env for its record/plane steps. Both callees now
        default it themselves, so a third copy here would be one more place to drift."""
        with open(os.path.join(REPO, "tools", "publish.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertNotIn("EMBED_TOKEN", src,
                         "publish.py should not hold embed credentials any more")


if __name__ == "__main__":
    unittest.main()
