"""Spec tests for tools/evaluator/surface.py -- the evaluator's reading-surface check.

Contract: read-only and network-free (nothing under the root is written, _data/stats.json
included -- the builder's own main() would write both feed and stats); a story the parser cannot
find prose for is reported as a lede-fallback WARN; a kept index record that reaches no card is a
parity miss; a desk past its cadence is overdue; a clean edition raises none of these.
"""
import contextlib
import importlib.util
import io
import json
import os
import shutil
import tempfile
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("_surface", os.path.join(TOOLS, "evaluator", "surface.py"))
surface = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(surface)

GOOD = """---
title: News
---

## World

- **The first desk story happened on Monday.** Prose long enough to be a body, with a second
  sentence of context for the card. [Ex, 1 Jun](https://ex.test/one)
- **The second desk story happened on Tuesday.** More prose for the second card, again with a
  sentence of context. [Ex, 2 Jun](https://ex.test/two)
"""

LEDE_ONLY = """---
title: News
---

## World

- **The first desk story happened on Monday.** Prose long enough to be a body, with a second
  sentence of context for the card. [Ex, 1 Jun](https://ex.test/one)
- **A headline the writer left without prose.** [Ex, 2 Jun](https://ex.test/lede)
"""


def _rec(url, date="2026-06-10", stream="news"):
    return {"id": "x-" + url[-4:], "date": date, "stream": stream, "headline": "H", "url": url}


class SurfaceTest(unittest.TestCase):
    def _root(self, posts, records, feed_stories, generated="2026-06-10"):
        root = tempfile.mkdtemp(prefix="surface-test-")
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        for d in ("_posts", os.path.join("index", "stories"), "_data"):
            os.makedirs(os.path.join(root, d))
        for name, body in posts.items():
            with open(os.path.join(root, "_posts", name), "w") as fh:
                fh.write(body)
        for name, rows in records.items():
            with open(os.path.join(root, "index", "stories", name), "w") as fh:
                fh.writelines(json.dumps(r) + "\n" for r in rows)
        with open(os.path.join(root, "_data", "homefeed.json"), "w") as fh:
            json.dump({"generated": generated, "stories": feed_stories}, fh)
        return root

    def _snapshot(self, root):
        out = {}
        for dp, _, files in os.walk(root):
            for f in files:
                p = os.path.join(dp, f)
                with open(p, "rb") as fh:
                    out[os.path.relpath(p, root)] = fh.read()
        return out

    def test_clean_edition_raises_no_edition_flags(self):
        root = self._root({"2026-06-10-news.md": GOOD},
                          {"2026-06-10-news.jsonl": [_rec("https://ex.test/one"),
                                                     _rec("https://ex.test/two")]},
                          [{"date": "2026-06-10", "stream": "news"}] * 2)
        r = surface.survey(root, "2026-06-10", 14)
        self.assertEqual(r["rows"][0]["post"], 2)
        self.assertEqual(r["rows"][0]["kept"], 2)
        self.assertEqual(r["rows"][0]["cards"], 2)
        self.assertEqual(r["warns"], [])
        self.assertEqual([f for f in r["flags"] if f.split()[0] in ("PARITY", "WARN", "SHORT")],
                         [])
        self.assertFalse([f for f in r["flags"] if f.startswith("OVERDUE news")])

    def test_lede_fallback_warn_and_parity_miss_are_flagged(self):
        root = self._root({"2026-06-10-news.md": LEDE_ONLY},
                          {"2026-06-10-news.jsonl": [_rec("https://ex.test/one"),
                                                     _rec("https://ex.test/lede"),
                                                     _rec("https://ex.test/never-printed")]},
                          [{"date": "2026-06-10", "stream": "news"}] * 2)
        r = surface.survey(root, "2026-06-10", 14)
        self.assertEqual(len(r["warns"]), 1)
        self.assertEqual(r["rows"][0]["warns"], 1)
        self.assertEqual(r["rows"][0]["unmapped"], 1)
        kinds = [f.split()[0] for f in r["flags"]]
        self.assertIn("WARN", kinds)
        self.assertIn("PARITY", kinds)

    def test_newest_edition_short_of_its_floor_is_flagged(self):
        root = self._root({"2026-06-10-news.md": GOOD},
                          {"2026-06-10-news.jsonl": [_rec("https://ex.test/one"),
                                                     _rec("https://ex.test/two")]},
                          [{"date": "2026-06-10", "stream": "news"}])
        r = surface.survey(root, "2026-06-10", 14)
        self.assertTrue([f for f in r["flags"] if f.startswith("SHORT 2026-06-10-news")])

    def test_overdue_desk_and_stale_feed(self):
        root = self._root({"2026-06-07-news.md": GOOD}, {}, [], generated="2026-06-01")
        r = surface.survey(root, "2026-06-10", 14)
        self.assertTrue([f for f in r["flags"] if f.startswith("OVERDUE news")])
        self.assertTrue([f for f in r["flags"] if f.startswith("OVERDUE science")])  # never filed
        self.assertTrue([f for f in r["flags"] if f.startswith("STALE-FEED")])

    def test_writes_nothing(self):
        root = self._root({"2026-06-10-news.md": LEDE_ONLY},
                          {"2026-06-10-news.jsonl": [_rec("https://ex.test/one")]}, [])
        before = self._snapshot(root)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(surface.main(["--root", root, "--today", "2026-06-10"]), 0)
        self.assertEqual(self._snapshot(root), before)


if __name__ == "__main__":
    unittest.main()
