#!/usr/bin/env python3
"""Spec tests for tools/store/verdicts.py -- the dedup-verdict snapshot step
(DEDUP.md Step A, added 2026-07-11).

Contract fixed by this file:
  - joins each check result back to its candidate (for the url cmd_check omits),
    by candidate `id` when present, else by position when lengths match;
  - writes index/verdicts/{date}-{slug}.json with {date, slug, window_days,
    checked, results[{headline, url?, verdict, score?, match_reason?,
    matched_id?, matched_date?, matched_headline?}]}, absent keys omitted;
  - idempotent (re-run overwrites, byte-identical);
  - non-fatal contract: bad date/slug/JSON/verdict exits non-zero and writes nothing.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(REPO, "tools", "store", "verdicts.py")

CANDS = {"candidates": [
    {"id": "1", "headline": "Alpha story", "summary": "a", "url": "https://example.com/a"},
    {"id": "2", "headline": "Beta story", "summary": "b", "url": "https://example.com/b"},
    {"id": "3", "headline": "Gamma story", "summary": "c"},  # no url -- legal
]}
VERDICTS = {"window_days": 30, "compared_against": 10, "t_high": 0.9, "t_low": 0.8, "results": [
    {"verdict": "NEW", "score": 0.31, "headline": "Alpha story", "id": "1"},
    {"verdict": "REPEAT", "score": 1.0, "match_reason": "exact-url", "headline": "Beta story", "id": "2",
     "matched": {"id": "st-aaa", "date": "2026-07-08", "headline": "Beta story, prior", "url": "https://example.com/b"}},
    {"verdict": "ONGOING", "score": 0.88, "headline": "Gamma story", "id": "3",
     "matched": {"id": "st-bbb", "date": "2026-07-05", "headline": "Gamma, earlier"}},
]}


def _run(root, cand, verd, date="2026-07-12", slug="news"):
    cp = os.path.join(root, "cand.json")
    vp = os.path.join(root, "verd.json")
    json.dump(cand, open(cp, "w"))
    json.dump(verd, open(vp, "w"))
    return subprocess.run(
        [sys.executable, TOOL, "--candidates", cp, "--verdicts", vp,
         "--date", date, "--slug", slug, "--root", root],
        capture_output=True, text=True, timeout=30)


class VerdictsSnapshotTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="verdicts-test-")
        self.addCleanup(shutil.rmtree, self.root, True)

    def _out(self, date="2026-07-12", slug="news"):
        return os.path.join(self.root, "index", "verdicts", "%s-%s.json" % (date, slug))

    def test_writes_snapshot_with_joined_urls(self):
        proc = _run(self.root, CANDS, VERDICTS)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        snap = json.load(open(self._out()))
        self.assertEqual(snap["date"], "2026-07-12")
        self.assertEqual(snap["slug"], "news")
        self.assertEqual(snap["window_days"], 30)
        self.assertEqual(snap["checked"], 3)
        r = {x["headline"]: x for x in snap["results"]}
        self.assertEqual(r["Alpha story"]["verdict"], "NEW")
        self.assertEqual(r["Alpha story"]["url"], "https://example.com/a")
        self.assertEqual(r["Beta story"]["match_reason"], "exact-url")
        self.assertEqual(r["Beta story"]["matched_id"], "st-aaa")
        self.assertEqual(r["Beta story"]["matched_date"], "2026-07-08")
        self.assertEqual(r["Beta story"]["matched_headline"], "Beta story, prior")
        self.assertNotIn("url", r["Gamma story"])  # candidate had none; key omitted
        self.assertEqual(r["Gamma story"]["matched_id"], "st-bbb")

    def test_positional_join_when_ids_missing(self):
        cands = {"candidates": [dict(c, id=None) for c in CANDS["candidates"]]}
        for c in cands["candidates"]:
            del c["id"]
        verd = {"results": [dict(r) for r in VERDICTS["results"]]}
        for r in verd["results"]:
            r.pop("id", None)
        proc = _run(self.root, cands, verd)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        snap = json.load(open(self._out()))
        self.assertEqual(snap["results"][1]["url"], "https://example.com/b")
        self.assertIsNone(snap["window_days"])  # meta absent -> null, not crash

    def test_idempotent_rerun(self):
        _run(self.root, CANDS, VERDICTS)
        first = open(self._out()).read()
        proc = _run(self.root, CANDS, VERDICTS)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(open(self._out()).read(), first)

    def test_summary_line_on_stdout(self):
        proc = _run(self.root, CANDS, VERDICTS)
        self.assertIn("3 checked", proc.stdout)
        self.assertIn("1 repeat", proc.stdout)

    def test_bad_slug_and_date_exit_nonzero(self):
        self.assertNotEqual(_run(self.root, CANDS, VERDICTS, slug="markets").returncode, 0)
        self.assertNotEqual(_run(self.root, CANDS, VERDICTS, date="12.07.2026").returncode, 0)
        self.assertFalse(os.path.exists(os.path.join(self.root, "index", "verdicts")))

    def test_bad_verdict_value_exits_nonzero(self):
        verd = {"results": [{"verdict": "MAYBE", "id": "1"}]}
        proc = _run(self.root, CANDS, verd)
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(os.path.exists(self._out()))


if __name__ == "__main__":
    unittest.main()
