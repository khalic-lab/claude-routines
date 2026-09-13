"""Spec tests for tools/usage/fold.py.

Contract under test: one record kept per session_id with stage preference
session-end > stop > publish (ties -> latest recorded_at); rollups by routine and by day;
rolling 7/30-day windows anchored on an explicit `as_of` (so no clock dependence); and a
newest-first `recent` list. cache_write is 5m + 1h summed.
"""
import importlib.util
import json
import os
import shutil
import tempfile
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fold_mod = _load("usage_fold", os.path.join(TOOLS, "usage", "fold.py"))


def _rec(session, stage, started, recorded_at, cost, routine="news", totals=None):
    return {
        "v": 1, "session_id": session, "stage": stage, "routine": routine,
        "edition": None, "started": started, "ended": started, "duration_s": 60,
        "messages": 5,
        "models": {"claude-opus-4-8": {"input": 1, "output": 1}},
        "totals": totals or {"input": 100, "cache_write_5m": 20, "cache_write_1h": 10,
                             "cache_read": 5, "output": 50},
        "server_tools": {}, "tool_calls": {},
        "cost_usd_list": {"total": cost}, "recorded_at": recorded_at,
    }


class FoldTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="usage-fold-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.dir = os.path.join(self.root, "index", "usage")
        os.makedirs(self.dir)

    def _write(self, name, records):
        with open(os.path.join(self.dir, name), "w", encoding="utf-8") as fh:
            for r in records:
                fh.write(json.dumps(r) + "\n")

    def test_stage_preference_and_recorded_at_tiebreak(self):
        # session X: a publish, then two stop records. stop beats publish; among the two
        # stops the later recorded_at wins -> cost 0.03.
        self._write("2026-09-news.jsonl", [
            _rec("X", "publish", "2026-09-10T10:00:00Z", "2026-09-10T10:01:00Z", 0.01),
            _rec("X", "stop",    "2026-09-10T10:00:00Z", "2026-09-10T10:02:00Z", 0.02),
            _rec("X", "stop",    "2026-09-10T10:00:00Z", "2026-09-10T10:03:00Z", 0.03),
        ])
        self._write("2026-08-watch.jsonl", [
            _rec("Y", "publish", "2026-08-01T07:00:00Z", "2026-08-01T07:01:00Z", 0.05,
                 routine="watch"),
        ])
        f = fold_mod.fold(self.root, as_of="2026-09-13")
        self.assertEqual(f["records"], 4)
        self.assertEqual(f["runs"], 2)              # X and Y
        self.assertEqual(f["since"], "2026-08-01")
        self.assertAlmostEqual(f["by_routine"]["news"]["cost_usd_list"], 0.03, places=6)
        self.assertEqual(f["by_routine"]["news"]["runs"], 1)
        self.assertAlmostEqual(f["by_routine"]["watch"]["cost_usd_list"], 0.05, places=6)

    def test_windows_anchored_on_as_of(self):
        self._write("2026-09-news.jsonl", [
            _rec("X", "stop", "2026-09-10T10:00:00Z", "2026-09-10T10:03:00Z", 0.03),   # age 3
        ])
        self._write("2026-08-watch.jsonl", [
            _rec("Y", "publish", "2026-08-01T07:00:00Z", "2026-08-01T07:01:00Z", 0.05,
                 routine="watch"),                                                     # age 43
        ])
        f = fold_mod.fold(self.root, as_of="2026-09-13")
        # X is within both windows; Y is outside both.
        self.assertEqual(f["windows"]["7d"]["runs"], 1)
        self.assertAlmostEqual(f["windows"]["7d"]["cost_usd_list"], 0.03, places=6)
        self.assertEqual(f["windows"]["30d"]["runs"], 1)
        self.assertAlmostEqual(f["windows"]["30d"]["cost_usd_list"], 0.03, places=6)

    def test_cache_write_sums_5m_and_1h(self):
        self._write("2026-09-news.jsonl", [
            _rec("X", "stop", "2026-09-10T10:00:00Z", "2026-09-10T10:03:00Z", 0.03,
                 totals={"input": 100, "cache_write_5m": 20, "cache_write_1h": 10,
                         "cache_read": 5, "output": 50}),
        ])
        f = fold_mod.fold(self.root, as_of="2026-09-13")
        self.assertEqual(f["by_routine"]["news"]["tokens"]["cache_write"], 30)
        self.assertEqual(f["recent"][0]["tokens"]["cache_write"], 30)

    def test_recent_newest_first(self):
        self._write("2026-09-news.jsonl", [
            _rec("A", "stop", "2026-09-05T10:00:00Z", "2026-09-05T10:03:00Z", 0.01),
            _rec("B", "stop", "2026-09-12T10:00:00Z", "2026-09-12T10:03:00Z", 0.02),
        ])
        f = fold_mod.fold(self.root, as_of="2026-09-13")
        self.assertEqual([r["session_id"] for r in f["recent"]], ["B", "A"])

    def test_by_day_sorted_ascending(self):
        self._write("2026-09-news.jsonl", [
            _rec("A", "stop", "2026-09-12T10:00:00Z", "2026-09-12T10:03:00Z", 0.02),
            _rec("B", "stop", "2026-09-05T10:00:00Z", "2026-09-05T10:03:00Z", 0.01),
        ])
        f = fold_mod.fold(self.root, as_of="2026-09-13")
        self.assertEqual([d["date"] for d in f["by_day"]], ["2026-09-05", "2026-09-12"])

    def test_empty_ledger(self):
        f = fold_mod.fold(self.root, as_of="2026-09-13")
        self.assertEqual(f["runs"], 0)
        self.assertEqual(f["records"], 0)
        self.assertEqual(f["recent"], [])
        self.assertIsNone(f["since"])


if __name__ == "__main__":
    unittest.main()
