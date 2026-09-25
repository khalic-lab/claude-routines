"""Spec tests for tools/evaluator/linkcheck.py -- deterministic link sampling.

Contract: same window -> same sample (seeded by the window end date), footer
links are excluded, sample size is respected, and the tool never touches the
network without --check.
"""
import os
import subprocess
import sys
import tempfile
import unittest

LINKCHECK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "evaluator", "linkcheck.py")

POST = """---
title: n
---

## World

- **A.** [Src](https://one.example/a)
- **B.** [Src](https://two.example/b)
- **C.** [Src](https://three.example/c)
- **D.** [Src](https://four.example/d)

## Coverage footer
- Gaps: [footer-link](https://never-sample.example/x)
"""


class LinkcheckTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp(prefix="linkcheck-test-")
        os.makedirs(os.path.join(cls.root, "_posts"))
        with open(os.path.join(cls.root, "_posts", "2026-07-15-news.md"), "w") as fh:
            fh.write(POST)

    def run_sample(self):
        return subprocess.run(
            [sys.executable, LINKCHECK, "--root", self.root,
             "--week", "2026-07-18", "--sample", "3"],
            capture_output=True, text=True).stdout

    def test_deterministic_and_sized(self):
        first, second = self.run_sample(), self.run_sample()
        self.assertEqual(first, second)
        urls = [l for l in first.splitlines() if l.startswith("http")]
        self.assertEqual(len(urls), 3)
        self.assertIn("sampled 3 of 4 links", first)

    def test_footer_links_excluded(self):
        self.assertNotIn("never-sample.example", self.run_sample())


WEEKEND = """---
title: w
---

# Weekend Deep Read — 2026-07-18

## 📰 Week in headlines
- **Recap A.** [AJ](https://recap.example/a)
- **Recap B.** [SRF](https://recap.example/b) and [LT](https://recap.example/c)

## 🧠 Cross-cutting threads
Thread prose [ref](https://thread.example/t).

## 📄 ML / AI papers of the week
- **P1.** [arXiv](https://paper.example/1)
- **P2.** [arXiv](https://paper.example/2)

## Coverage footer
- Gaps: [footer](https://never-sample.example/w)
"""


class RecapAlwaysCheckedTest(unittest.TestCase):
    """2026-07-12 review, W1 link-audit half: the Weekend 'Week in headlines' links are
    always listed, on top of the random sample and never drawn into it."""

    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp(prefix="linkcheck-recap-")
        os.makedirs(os.path.join(cls.root, "_posts"))
        with open(os.path.join(cls.root, "_posts", "2026-07-15-news.md"), "w") as fh:
            fh.write(POST)
        with open(os.path.join(cls.root, "_posts", "2026-07-18-weekend.md"), "w") as fh:
            fh.write(WEEKEND)

    def _run(self, sample):
        return subprocess.run(
            [sys.executable, LINKCHECK, "--root", self.root,
             "--week", "2026-07-18", "--sample", str(sample)],
            capture_output=True, text=True).stdout

    def test_recap_links_listed_even_at_sample_one(self):
        out = self._run(1)
        recap = [l for l in out.splitlines() if l.endswith("[recap]")]
        self.assertEqual(sorted(l.split()[0] for l in recap),
                         ["https://recap.example/a", "https://recap.example/b",
                          "https://recap.example/c"])
        sampled = [l for l in out.splitlines() if l.startswith("http") and not l.endswith("[recap]")]
        self.assertEqual(len(sampled), 1)                    # --sample still sizes the random half
        self.assertIn("3 Weekend recap link(s) always included", out)

    def test_recap_never_drawn_into_the_random_sample(self):
        out = self._run(50)                                  # sample > pool: take everything
        sampled = [l.split()[0] for l in out.splitlines()
                   if l.startswith("http") and not l.endswith("[recap]")]
        self.assertFalse([u for u in sampled if "recap.example" in u])
        self.assertIn("https://thread.example/t", sampled)   # other weekend sections stay in the pool
        self.assertNotIn("https://never-sample.example/w", out)

    def test_check_reports_recap_pass_rate_separately(self):
        import contextlib, importlib.util, io
        spec = importlib.util.spec_from_file_location("_linkcheck", LINKCHECK)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.resolve = lambda url, max_time=15: "404" if url == "https://recap.example/a" else "200"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            mod.main(["--root", self.root, "--week", "2026-07-18", "--sample", "2", "--check"])
        out = buf.getvalue()
        self.assertIn("linkcheck: recap 2/3 resolve", out)
        self.assertIn("linkcheck: 2/2 resolve", out)


if __name__ == "__main__":
    unittest.main()
