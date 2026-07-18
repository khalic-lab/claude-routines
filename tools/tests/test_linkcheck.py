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


if __name__ == "__main__":
    unittest.main()
