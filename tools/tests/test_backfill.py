#!/usr/bin/env python3
"""RED-phase spec tests — legacy index backfill (SPIKE-2026-07-07-continuous-news.md §5
Step 1 "per-story anchors... backfill script over the 40-day index"; contract clause for
`tools/store/backfill.py`).

Covers: one seen event per legacy record; id = store.story_id(url) (or the urlless
sha1("legacy:"+legacy_id) fallback); legacy_ids/editions/origin/first_seen/updated/status
field mapping from the filename + record; preservation of carried fields (headline, url,
topics, importance, display_body, why, emb, ...); end-to-end URL-fold across two legacy
files into one materialized story; and double-run idempotence (no duplicate (ev,id)
pairs, unchanged materialized story count).

Fixtures are SYNTHESIZED (not bulk-copied) but mirror the exact field names of the real
`index/stories/2026-07-05-news.jsonl` / `2026-07-06-news.jsonl` schema.

Run: cd /Users/rflnogueira/code/claude-routines && python3 -m unittest discover -s tools/tests -v
"""
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
FIXTURES_DIR = os.path.join(TESTS_DIR, "fixtures", "store")
LEGACY_FIXTURE_DIR = os.path.join(FIXTURES_DIR, "legacy_index")
STORE_PATH = os.path.join(REPO_ROOT, "tools", "store", "store.py")
BACKFILL_PATH = os.path.join(REPO_ROOT, "tools", "store", "backfill.py")

ALPHA_NEWS_URL = "https://www.example.com/world/alpha-story?utm_source=rss&utm_medium=feed"
ALPHA_AIML_URL = "https://example.com/world/alpha-story/"
BETA_URL = "https://beta.example.org/notices/2026-06-20-beta"
GAMMA_LEGACY_ID = "2026-06-21-ai-ml-gamma-note"


def _load_module(path, name):
    """importlib load by fixed path. A missing (not-yet-implemented) file must fail THIS
    test clearly, not crash discovery of the rest of the suite."""
    if not os.path.exists(path):
        raise AssertionError(f"expected implementation file is missing: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _new_root_with_legacy_index():
    root = tempfile.mkdtemp(prefix="backfill-test-")
    dest = os.path.join(root, "index", "stories")
    os.makedirs(dest, exist_ok=True)
    for name in os.listdir(LEGACY_FIXTURE_DIR):
        shutil.copy(os.path.join(LEGACY_FIXTURE_DIR, name), os.path.join(dest, name))
    os.makedirs(os.path.join(root, "index", "ledger"), exist_ok=True)
    return root


def _run_backfill(root, timeout=30):
    return subprocess.run([sys.executable, BACKFILL_PATH, "--root", root],
                           capture_output=True, text=True, timeout=timeout)


def _read_ledger_events(root):
    out = []
    ledger_dir = os.path.join(root, "index", "ledger")
    for name in sorted(os.listdir(ledger_dir)):
        if not name.endswith(".jsonl"):
            continue
        with open(os.path.join(ledger_dir, name)) as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
    return out


class BackfillFieldMappingTests(unittest.TestCase):
    """contract: one seen event per legacy record; id/legacy_ids/editions/origin/
    first_seen/updated/status field mapping; carried-field preservation."""

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(BACKFILL_PATH):
            raise AssertionError(f"expected implementation file is missing: {BACKFILL_PATH}")
        cls.store = _load_module(STORE_PATH, f"store_backfillmap_{id(cls)}")

    def setUp(self):
        self.root = _new_root_with_legacy_index()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        proc = _run_backfill(self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.events = [e for e in _read_ledger_events(self.root) if e.get("ev") == "seen"]

    def _find_by_legacy_id(self, legacy_id):
        matches = [e for e in self.events
                   if legacy_id in (e["story"].get("legacy_ids") or [])]
        self.assertEqual(len(matches), 1,
                          f"expected exactly one seen event carrying legacy_id {legacy_id}, "
                          f"got {len(matches)}")
        return matches[0]

    def test_one_seen_event_emitted_per_legacy_record(self):
        # 2 records in 2026-06-20-news.jsonl + 2 records in 2026-06-21-ai-ml.jsonl = 4
        self.assertEqual(len(self.events), 4)

    def test_actor_is_backfill(self):
        for e in self.events:
            self.assertEqual(e["actor"], "backfill")
            self.assertEqual(e["ev"], "seen")

    def test_id_is_story_id_of_the_url_for_url_bearing_records(self):
        ev = self._find_by_legacy_id("2026-06-20-news-alpha-story-breaks")
        self.assertEqual(ev["story"]["id"], self.store.story_id(ALPHA_NEWS_URL))

    def test_urlless_record_uses_the_sha1_legacy_fallback_id(self):
        ev = self._find_by_legacy_id(GAMMA_LEGACY_ID)
        expected = "st-" + hashlib.sha1(("legacy:" + GAMMA_LEGACY_ID).encode("utf-8")).hexdigest()[:12]
        self.assertEqual(ev["story"]["id"], expected)
        self.assertFalse(ev["story"].get("url"))

    def test_editions_and_origin_derive_from_the_filename(self):
        ev = self._find_by_legacy_id("2026-06-20-news-beta-notice")
        self.assertEqual(ev["story"]["editions"], ["2026-06-20-news"])
        self.assertEqual(ev["story"]["origin"], "writer:news")
        ev2 = self._find_by_legacy_id("2026-06-21-ai-ml-alpha-corroboration")
        self.assertEqual(ev2["story"]["editions"], ["2026-06-21-ai-ml"])
        self.assertEqual(ev2["story"]["origin"], "writer:ai-ml")

    def test_first_seen_and_updated_are_the_files_date_at_midnight_utc(self):
        ev = self._find_by_legacy_id("2026-06-20-news-beta-notice")
        self.assertEqual(ev["story"]["first_seen"], "2026-06-20T00:00:00Z")
        self.assertEqual(ev["story"]["updated"], "2026-06-20T00:00:00Z")

    def test_status_is_settled(self):
        for e in self.events:
            self.assertEqual(e["story"]["status"], "settled")

    def test_legacy_ids_carries_the_records_own_id_field(self):
        ev = self._find_by_legacy_id("2026-06-20-news-alpha-story-breaks")
        self.assertIn("2026-06-20-news-alpha-story-breaks", ev["story"]["legacy_ids"])

    def test_carried_fields_are_preserved_verbatim_when_present(self):
        """The alpha news record carries topics/importance/display_body/why — backfill
        must not drop them."""
        ev = self._find_by_legacy_id("2026-06-20-news-alpha-story-breaks")
        s = ev["story"]
        self.assertEqual(s["headline"], "Alpha story breaks in the capital")
        self.assertEqual(s["url"], ALPHA_NEWS_URL)
        self.assertEqual(s["topics"], ["world"])
        self.assertEqual(s["importance"], 2)
        self.assertEqual(
            s["display_body"],
            "The alpha story broke Friday when officials confirmed the synthetic "
            "development described in this fixture record.",
        )
        self.assertEqual(
            s["why"], "It matters because this is a fixture exercising the backfill "
            "preserve-fields path.",
        )
        self.assertEqual(s["emb"], "ZmFrZS1lbWItYWxwaGEtb25l")

    def test_older_shape_record_missing_optional_fields_does_not_crash_and_carries_core_fields(self):
        """The beta record predates topics/importance/display_body/why — backfill must
        tolerate their absence (matching dedup.py's own s.get(..., default) pattern)."""
        ev = self._find_by_legacy_id("2026-06-20-news-beta-notice")
        s = ev["story"]
        self.assertEqual(s["headline"], "Beta regulatory notice published")
        self.assertEqual(s["url"], BETA_URL)
        self.assertIn(s.get("topics"), ([], None))
        self.assertIn(s.get("importance"), (None,))


class BackfillUrlFoldIntegrationTests(unittest.TestCase):
    """End-to-end: two legacy records (different streams/files, same norm_url) must fold
    into ONE materialized story once store.materialize() runs over the backfilled ledger
    — proving backfill emits ids the materializer can actually fold (invariant c)."""

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(BACKFILL_PATH):
            raise AssertionError(f"expected implementation file is missing: {BACKFILL_PATH}")
        cls.store = _load_module(STORE_PATH, f"store_backfillfold_{id(cls)}")

    def setUp(self):
        self.root = _new_root_with_legacy_index()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_alpha_corroboration_folds_into_one_story_with_unioned_legacy_ids_and_editions(self):
        proc = _run_backfill(self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        sid = self.store.story_id(ALPHA_NEWS_URL)
        self.assertEqual(sid, self.store.story_id(ALPHA_AIML_URL))
        snap = self.store.materialize(root=self.root)
        self.assertIn(sid, snap["stories"])
        rec = snap["stories"][sid]
        self.assertEqual(
            set(rec["legacy_ids"]),
            {"2026-06-20-news-alpha-story-breaks", "2026-06-21-ai-ml-alpha-corroboration"},
        )
        self.assertEqual(set(rec["editions"]), {"2026-06-20-news", "2026-06-21-ai-ml"})
        # 2026-06-20 < 2026-06-21
        self.assertEqual(rec["first_seen"], "2026-06-20T00:00:00Z")
        self.assertEqual(rec["updated"], "2026-06-21T00:00:00Z")
        # ai-ml record (later ts) has no display_body -> the earlier non-empty one must survive
        self.assertTrue(rec.get("display_body"))

    def test_distinct_stories_stay_distinct(self):
        proc = _run_backfill(self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        snap = self.store.materialize(root=self.root)
        sid_alpha = self.store.story_id(ALPHA_NEWS_URL)
        sid_beta = self.store.story_id(BETA_URL)
        self.assertNotEqual(sid_alpha, sid_beta)
        self.assertIn(sid_beta, snap["stories"])
        self.assertEqual(len(snap["stories"]), 3,
                          "alpha (folded x2) + beta + gamma(urlless) = 3 distinct stories")


class BackfillIdempotenceTests(unittest.TestCase):
    """contract: 'IDEMPOTENT: second run appends nothing new after materialize ...
    backfill must skip events already present.'"""

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(BACKFILL_PATH):
            raise AssertionError(f"expected implementation file is missing: {BACKFILL_PATH}")
        cls.store = _load_module(STORE_PATH, f"store_backfillidem_{id(cls)}")

    def setUp(self):
        self.root = _new_root_with_legacy_index()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_second_run_appends_no_new_ledger_lines(self):
        proc1 = _run_backfill(self.root)
        self.assertEqual(proc1.returncode, 0, proc1.stderr)
        after_first = _read_ledger_events(self.root)

        proc2 = _run_backfill(self.root)
        self.assertEqual(proc2.returncode, 0, proc2.stderr)
        after_second = _read_ledger_events(self.root)

        self.assertEqual(len(after_first), len(after_second),
                          "a second backfill run over an unchanged legacy index must "
                          "append zero new ledger lines")

    def test_no_duplicate_ev_id_legacy_id_triples_after_second_run(self):
        _run_backfill(self.root)
        _run_backfill(self.root)
        events = [e for e in _read_ledger_events(self.root) if e.get("ev") == "seen"]
        keys = [
            (e["ev"], e["story"]["id"], tuple(sorted(e["story"].get("legacy_ids") or [])))
            for e in events
        ]
        self.assertEqual(len(keys), len(set(keys)),
                          f"duplicate (ev, id, legacy_ids) key found after a second run: {keys}")

    def test_materialized_story_count_identical_after_double_run(self):
        _run_backfill(self.root)
        snap_once = self.store.materialize(root=self.root)

        _run_backfill(self.root)
        snap_twice = self.store.materialize(root=self.root)

        self.assertEqual(set(snap_once["stories"].keys()), set(snap_twice["stories"].keys()))
        self.assertEqual(len(snap_once["stories"]), len(snap_twice["stories"]))


if __name__ == "__main__":
    unittest.main()
