"""Spec tests for tools/footer.py -- computed Coverage-footer telemetry.

Contract: the tool OWNS the computed lines (Sources used / Direct fetches /
Word count / Token estimate / Feeds hit) inside the hidden telemetry comment,
replaces any stale self-reported versions of them, preserves writer-authored
lines (e.g. `- Languages:`), never touches the visible Gaps/Discovery lines,
is idempotent, and keeps the Word-count line shape parseable by
tools/build_stats.py's WORDS_RE/CALLS_RE.
"""
import importlib.util
import os
import re
import sys
import tempfile
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


footer = _load("_footer", os.path.join(TOOLS, "footer.py"))
build_stats = _load("_build_stats", os.path.join(TOOLS, "build_stats.py"))

REGISTRY = """t1.example:
  tier: T1
  status: established
t2.example:
  tier: T2
  status: probation
"""

POST = """---
layout: single
title: "News — 2026-07-18"
date: 2026-07-18T12:00:00+02:00
categories: [news]
---

# News — 2026-07-18

## Section one

- **Alpha story lead.** Body text here. [Src](https://t1.example/a)
- **Beta story lead.** More text. [Src](https://www.t2.example/b) [via snippet]
- **Gamma story lead.** Even more. [Src](https://unknown.example/c) [new source]

## Empty section

---

## Coverage footer
<!-- operational telemetry — machine/evaluator-read; hidden from the rendered page
- Sources used: T1 = 99, T2 = 99, T3 = 0
- Languages: EN, FR
- Word count: ~9,999 (body, excl. footer) | research tool calls (curl/WebSearch): ~999
-->
- Gaps: none worth noting.
- Discovery: waived — quiet day.
"""

FETCH_LOG = "\n".join([
    '{"ts": "t", "url": "https://a.example/rss", "method": "curl", "status": 200, "ok": true}',
    '{"ts": "t", "url": "https://a.example/atom", "method": "curl", "status": 200, "ok": true}',
    '{"ts": "t", "url": "https://b.example/page", "method": "curl", "status": 403, "ok": false}',
    '{"ts": "t", "url": "https://b.example/page", "method": "proxy", "status": 200, "ok": true}',
]) + "\n"


class FooterTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="footer-test-")
        os.makedirs(os.path.join(self.root, "sources"))
        with open(os.path.join(self.root, "sources", "registry.yml"), "w") as fh:
            fh.write(REGISTRY)
        self.post = os.path.join(self.root, "post.md")
        with open(self.post, "w") as fh:
            fh.write(POST)
        self.log = os.path.join(self.root, "fetch.log")
        with open(self.log, "w") as fh:
            fh.write(FETCH_LOG)

    def run_footer(self):
        rc = footer.main([self.post, "--root", self.root, "--fetch-log", self.log])
        self.assertEqual(rc, 0)
        with open(self.post) as fh:
            return fh.read()

    def test_computed_lines_replace_self_reported_ones(self):
        text = self.run_footer()
        self.assertIn("- Sources used: T1 = 1, T2 = 1, untiered = 1", text)
        self.assertIn("- Direct fetches: 2 | via-snippet citations: 1", text)
        self.assertNotIn("T1 = 99", text)          # stale self-report replaced
        self.assertNotIn("~9,999", text)
        self.assertIn("research tool calls (logged): 4", text)
        self.assertIn("- Token estimate (computed):", text)

    def test_word_count_is_exact_and_build_stats_parseable(self):
        text = self.run_footer()
        m = build_stats.WORDS_RE.search(text)
        self.assertIsNotNone(m)
        words = int(m.group(1).replace(",", ""))
        _, body, _ = footer.split_post(POST)
        self.assertEqual(words, footer.clean_words(body))
        self.assertGreater(words, 20)  # sanity: the fixture body is ~30 words
        c = build_stats.CALLS_RE.search(text[m.start():m.start() + 200])
        self.assertIsNotNone(c)
        self.assertEqual(int(c.group(1)), 4)

    def test_feeds_hit_aggregates_per_host(self):
        text = self.run_footer()
        self.assertIn("a.example {2 ok via curl}", text)
        self.assertIn("b.example {1 fail HTTP 403, 1 ok via proxy}", text)

    def test_writer_lines_preserved_and_judgment_lines_untouched(self):
        text = self.run_footer()
        self.assertIn("- Languages: EN, FR", text)
        self.assertIn("- Gaps: none worth noting.", text)
        self.assertIn("- Discovery: waived — quiet day.", text)
        self.assertEqual(text.count("<!--"), 1)

    def test_idempotent(self):
        first = self.run_footer()
        second = self.run_footer()
        self.assertEqual(first, second)

    def test_missing_footer_heading_is_a_clean_skip(self):
        with open(self.post, "w") as fh:
            fh.write("---\ntitle: x\n---\n\nNo footer here.\n")
        rc = footer.main([self.post, "--root", self.root, "--fetch-log", self.log])
        self.assertEqual(rc, 0)
        with open(self.post) as fh:
            self.assertNotIn("<!--", fh.read())

    def test_no_fetch_log_omits_calls_and_feeds(self):
        os.unlink(self.log)
        text = self.run_footer()
        self.assertNotIn("research tool calls (logged)", text)
        self.assertNotIn("- Feeds hit", text)
        self.assertIsNotNone(build_stats.WORDS_RE.search(text))


if __name__ == "__main__":
    unittest.main()
