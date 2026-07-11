#!/usr/bin/env python3
"""Spec tests for tools/build_stats.py -- the desk-stats aggregator behind
_data/stats.json (homepage "in numbers" panel, 2026-07-11).

Contract fixed by this file:
  - all_time counts = distinct publish (id, edition) ledger events for the four live
    streams, with stream split, distinct source domains and tag counts joined from the
    paired `seen` events;
  - window slice keyed on edition date >= as_of - window days;
  - Coverage-footer telemetry (word count / tool calls) averaged over window posts
    that carry the lines, null when none do;
  - dedup: REPEAT verdicts always count dropped; ONGOING counts dropped only when its
    url is absent from that edition's index/stories file; ONGOING with a pruned index
    file counts `ongoing_unjoinable`, never dropped; empty verdicts dir -> since=null,
    zeros; est_minutes_saved = 2 x drops;
  - degrades gracefully: missing ledger/registry/posts -> zeros/nulls, exit 0.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(REPO, "tools", "build_stats.py")

LEDGER = [
    {"ev": "seen", "ts": "2026-07-01T10:00:00Z", "actor": "news",
     "story": {"id": "st-aaa", "date": "2026-07-01", "stream": "news", "headline": "A",
               "url": "https://example.com/a", "source_domain": "example.com",
               "tags": ["single-source"]}},
    {"ev": "publish", "ts": "2026-07-01T10:00:01Z", "actor": "news",
     "id": "st-aaa", "edition": "2026-07-01-news", "fields": {}},
    {"ev": "seen", "ts": "2026-07-10T10:00:00Z", "actor": "ai-ml",
     "story": {"id": "st-bbb", "date": "2026-07-10", "stream": "ai-ml", "headline": "B",
               "url": "https://other.org/b", "source_domain": "other.org",
               "tags": ["preprint"]}},
    {"ev": "publish", "ts": "2026-07-10T10:00:01Z", "actor": "ai-ml",
     "id": "st-bbb", "edition": "2026-07-10-ai-ml", "fields": {}},
    # duplicate publish line (retried append) -- must not double-count
    {"ev": "publish", "ts": "2026-07-10T10:05:00Z", "actor": "ai-ml",
     "id": "st-bbb", "edition": "2026-07-10-ai-ml", "fields": {}},
    # retired-stream edition -- invisible to stats
    {"ev": "publish", "ts": "2026-05-01T10:00:00Z", "actor": "markets",
     "id": "st-zzz", "edition": "2026-05-01-markets", "fields": {}},
    # feedback event -- ignored
    {"ev": "feedback", "ts": "2026-07-10T12:00:00Z", "actor": "bridge",
     "fb_id": "x", "vote": 1, "id": "st-bbb"},
]

POST = """---
title: t
---
body prose here

## Coverage footer
- Sources used: T1 = 1 items
- Direct fetches: 7 | via-snippet citations: 0
- Word count: ~1,200 (body, excl. footer) | research tool calls (curl/WebSearch/WebFetch): 14
- Discovery: waived — quiet day
"""

VERDICTS_KEPT_URL = "https://kept.example/x"
VERDICTS = {
    "date": "2026-07-10", "slug": "ai-ml", "window_days": 30, "checked": 4,
    "results": [
        {"headline": "r1", "verdict": "REPEAT", "url": "https://dead.example/1"},
        {"headline": "o-dropped", "verdict": "ONGOING", "url": "https://dead.example/2"},
        {"headline": "o-kept", "verdict": "ONGOING", "url": VERDICTS_KEPT_URL},
        {"headline": "n", "verdict": "NEW", "url": "https://new.example/3"},
    ],
}


def _skeleton(with_verdicts=True, with_pruned=False):
    root = tempfile.mkdtemp(prefix="stats-test-")
    os.makedirs(os.path.join(root, "index", "ledger"))
    os.makedirs(os.path.join(root, "index", "stories"))
    os.makedirs(os.path.join(root, "_posts"))
    with open(os.path.join(root, "index", "ledger", "2026-07-10.jsonl"), "w") as fh:
        for ev in LEDGER:
            fh.write(json.dumps(ev) + "\n")
    with open(os.path.join(root, "_posts", "2026-07-10-ai-ml.md"), "w") as fh:
        fh.write(POST)
    os.makedirs(os.path.join(root, "sources"))
    with open(os.path.join(root, "sources", "registry.yml"), "w") as fh:
        fh.write("example.com:\n  status: established\nother.org:\n  status: probation\n"
                 "new.example:\n  status: candidate\n")
    if with_verdicts:
        os.makedirs(os.path.join(root, "index", "verdicts"))
        with open(os.path.join(root, "index", "verdicts", "2026-07-10-ai-ml.json"), "w") as fh:
            json.dump(VERDICTS, fh)
        # the edition's index file: o-kept's url IS published (www + trailing slash
        # variants exercise the norm_url join), o-dropped's is not
        with open(os.path.join(root, "index", "stories", "2026-07-10-ai-ml.jsonl"), "w") as fh:
            fh.write(json.dumps({"id": "x", "url": "https://www.kept.example/x/"}) + "\n")
        if with_pruned:
            with open(os.path.join(root, "index", "verdicts", "2026-06-01-news.json"), "w") as fh:
                json.dump({"date": "2026-06-01", "slug": "news", "checked": 1, "results": [
                    {"headline": "old-ongoing", "verdict": "ONGOING", "url": "https://old.example/1"},
                ]}, fh)
            # no matching index/stories/2026-06-01-news.jsonl -> pruned -> unjoinable
    return root


def _run(root, extra=None):
    proc = subprocess.run(
        [sys.executable, TOOL, "--root", root, "--as-of", "2026-07-11"] + (extra or []),
        capture_output=True, text=True, timeout=30)
    out = os.path.join(root, "_data", "stats.json")
    stats = json.load(open(out)) if os.path.exists(out) else None
    return proc, stats


class BuildStatsTest(unittest.TestCase):
    def setUp(self):
        self.root = _skeleton(with_verdicts=True, with_pruned=True)
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_all_time_counts(self):
        proc, stats = _run(self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        at = stats["all_time"]
        self.assertEqual(at["stories"], 2)          # duplicate publish + markets excluded
        self.assertEqual(at["editions"], 2)
        self.assertEqual(at["by_stream"], {"ai-ml": 1, "news": 1})
        self.assertEqual(at["distinct_domains"], 2)
        self.assertEqual(at["tags"], {"single-source": 1, "preprint": 1})
        self.assertEqual(at["since"], "2026-07-01")

    def test_window_slice_and_footer_telemetry(self):
        _, stats = _run(self.root, ["--window", "5"])
        w = stats["window"]
        self.assertEqual(w["stories"], 1)            # only the 07-10 edition is in-window
        self.assertEqual(w["editions"], 1)
        self.assertEqual(w["avg_words"], 1200)
        self.assertEqual(w["avg_tool_calls"], 14)

    def test_sources_status_counts(self):
        _, stats = _run(self.root)
        self.assertEqual(stats["sources"],
                         {"established": 1, "probation": 1, "candidate": 1})

    def test_dedup_verdict_aggregation(self):
        _, stats = _run(self.root)
        d = stats["dedup"]
        self.assertEqual(d["since"], "2026-06-01")
        self.assertEqual(d["editions"], 2)
        self.assertEqual(d["checked"], 5)
        self.assertEqual(d["repeats_dropped"], 1)
        self.assertEqual(d["ongoing_dropped"], 1)    # o-kept joined to the index -> NOT dropped
        self.assertEqual(d["ongoing_unjoinable"], 1)  # pruned edition's ONGOING
        self.assertEqual(d["est_minutes_saved"], 4)   # (1 + 1) * 2

    def test_no_verdicts_dir_degrades_to_nulls(self):
        root = _skeleton(with_verdicts=False)
        self.addCleanup(shutil.rmtree, root, True)
        proc, stats = _run(root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        d = stats["dedup"]
        self.assertIsNone(d["since"])
        self.assertEqual(d["checked"], 0)
        self.assertEqual(d["est_minutes_saved"], 0)

    def test_empty_root_exits_clean(self):
        root = tempfile.mkdtemp(prefix="stats-empty-")
        self.addCleanup(shutil.rmtree, root, True)
        proc, stats = _run(root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(stats["all_time"]["stories"], 0)
        self.assertIsNone(stats["all_time"]["since"])
        self.assertIsNone(stats["window"]["avg_words"])


if __name__ == "__main__":
    unittest.main()
