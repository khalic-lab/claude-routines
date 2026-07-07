#!/usr/bin/env python3
"""RED-phase spec tests — ledger dual-write (SPIKE-2026-07-07-continuous-news.md §3.1, §5 Step 1).

Encodes the migration invariant: `tools/dedup/dedup.py::cmd_record` must keep writing the
legacy `index/stories/{date}-{slug}.jsonl` file BYTE-IDENTICAL to its pre-migration output
(SPIKE §5 Step 1: "legacy files byte-identical AND ledger events with `st-` ids +
`legacy_ids`") while ALSO appending matching `ev:"seen"` / `ev:"publish"` events to the new
`index/ledger/{YYYY-MM-DD}.jsonl` (SPIKE §3.1).

Golden capture: `golden-legacy.jsonl` was produced ONCE by running the CURRENT (pre-migration)
`cmd_record` against `fixtures/dualwrite/final-payload.json` inside a throwaway tempdir
skeleton, with the network-only `embed()` call replaced by the deterministic `_stub_embed`
below (same function, so re-running it later reproduces identical bytes). See
`capture_golden_legacy()` at the bottom of this file — NOT a test, a one-off regeneration
helper, invoked manually if the fixture payload ever changes:

    python3 -c "import sys; sys.path.insert(0, 'tools/tests'); \\
                 import test_dualwrite as t; t.capture_golden_legacy()"

Run: cd /Users/rflnogueira/code/claude-routines && python3 -m unittest discover -s tools/tests -v
"""
import argparse
import contextlib
import glob
import hashlib
import importlib.util
import json
import os
import random
import shutil
import sys
import tempfile
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
FIXTURES_DIR = os.path.join(TESTS_DIR, "fixtures", "dualwrite")
DEDUP_PATH = os.path.join(REPO_ROOT, "tools", "dedup", "dedup.py")
STORE_PATH = os.path.join(REPO_ROOT, "tools", "store", "store.py")
GITATTR_PATH = os.path.join(REPO_ROOT, ".gitattributes")

PAYLOAD_PATH = os.path.join(FIXTURES_DIR, "final-payload.json")
GOLDEN_LEGACY_PATH = os.path.join(FIXTURES_DIR, "golden-legacy.jsonl")
RECORD_DATE = "2026-07-08"
RECORD_SLUG = "news"
RECORD_EDITION = f"{RECORD_DATE}-{RECORD_SLUG}"


# --------------------------------------------------------------------------- #
# infrastructure — no network, no real-repo writes
# --------------------------------------------------------------------------- #
def _stub_embed(texts, worker=None, token=None):
    """Deterministic, offline stand-in for dedup.embed(): no network call, seeded per
    sha1(text) so the SAME input text always yields the SAME 1024-dim vector, across the
    one-time golden capture and every later test run alike."""
    out = []
    for t in texts:
        seed = int(hashlib.sha1(t.encode("utf-8")).hexdigest(), 16) % (2 ** 32)
        rng = random.Random(seed)
        out.append([rng.uniform(-1.0, 1.0) for _ in range(1024)])
    return out


def _load_module(path, name):
    """importlib load by fixed path. A missing (not-yet-implemented) file must fail THIS
    test clearly, not crash discovery of the rest of the suite — hence a plain AssertionError,
    raised from setUp/test bodies where unittest catches and reports it per-test."""
    if not os.path.exists(path):
        raise AssertionError(f"expected implementation file is missing: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@contextlib.contextmanager
def _env(key, value):
    old = os.environ.get(key)
    os.environ[key] = value
    try:
        yield
    finally:
        if old is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = old


def _load_dedup(repo_root, modname):
    """Fresh dedup.py instance rooted at repo_root — REPO is read from os.environ at
    module-exec time (dedup.py line ~62), so the env var must be set BEFORE exec_module."""
    with _env("REPO", repo_root):
        mod = _load_module(DEDUP_PATH, modname)
    mod.embed = _stub_embed  # network stub; cmd_record calls the bare name at call time,
    # which resolves via the module's own globals, so this override takes effect.
    return mod


def _new_skeleton():
    root = tempfile.mkdtemp(prefix="dualwrite-")
    os.makedirs(os.path.join(root, "index", "stories"))
    os.makedirs(os.path.join(root, "index", "ledger"))
    os.makedirs(os.path.join(root, "_posts"))
    return root


def _run_record(root, modname, payload_path=PAYLOAD_PATH, date=RECORD_DATE, slug=RECORD_SLUG):
    mod = _load_dedup(root, modname)
    args = argparse.Namespace(stories=payload_path, date=date, slug=slug,
                               keep_days=40, worker=None, token=None)
    mod.cmd_record(args)
    return mod


def _legacy_path(root, date=RECORD_DATE, slug=RECORD_SLUG):
    return os.path.join(root, "index", "stories", f"{date}-{slug}.jsonl")


def _ledger_events(root):
    events = []
    for path in sorted(glob.glob(os.path.join(root, "index", "ledger", "*.jsonl"))):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
    return events


def _payload_stories():
    with open(PAYLOAD_PATH) as f:
        return json.load(f)["stories"]


# --------------------------------------------------------------------------- #
# golden capture (one-off maintenance helper — NOT a test)
# --------------------------------------------------------------------------- #
def capture_golden_legacy():
    root = _new_skeleton()
    try:
        _run_record(root, "dedup_golden_capture")
        shutil.copy(_legacy_path(root), GOLDEN_LEGACY_PATH)
        print(f"wrote {GOLDEN_LEGACY_PATH}")
    finally:
        shutil.rmtree(root, ignore_errors=True)


# --------------------------------------------------------------------------- #
# tests
# --------------------------------------------------------------------------- #
class LegacyByteIdentityTests(unittest.TestCase):
    """SPIKE §5 Step 1 Verify: 'legacy index files byte-identical (diff vs git HEAD)'."""

    def setUp(self):
        self.root = _new_skeleton()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_record_writes_legacy_file_byte_identical_to_golden(self):
        """cmd_record's dual-write must not perturb a single byte of the legacy file this
        payload produced pre-migration."""
        _run_record(self.root, f"dedup_{id(self)}_a")
        with open(_legacy_path(self.root), "rb") as f:
            actual = f.read()
        with open(GOLDEN_LEGACY_PATH, "rb") as f:
            expected = f.read()
        self.assertEqual(actual, expected)

    def test_record_still_prunes_old_index_files(self):
        """Dual-write must not disturb the pre-existing prune_index() behaviour (SPIKE
        Step 1 lists dedup.py::cmd_record dual-write as additive, not a rewrite)."""
        stale = os.path.join(self.root, "index", "stories", "2026-01-01-news.jsonl")
        with open(stale, "w") as f:
            f.write("{}\n")
        _run_record(self.root, f"dedup_{id(self)}_b")
        self.assertFalse(os.path.exists(stale), "a >40-day-old index file must still be pruned")


class LedgerEventTests(unittest.TestCase):
    """SPIKE §3.1 event ledger shapes + the contract's exact field list."""

    def setUp(self):
        self.root = _new_skeleton()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.store = _load_module(STORE_PATH, f"store_{id(self)}")

    def test_seen_event_per_kept_story_with_store_id_and_legacy_id(self):
        """contract LEDGER: {"ev":"seen",...,"story":{...}} — one per kept story, story.id ==
        st-id of its url, story.legacy_ids carries the pre-migration hid."""
        stories = _payload_stories()
        _run_record(self.root, f"dedup_{id(self)}_seen")
        seen = [e for e in _ledger_events(self.root) if e.get("ev") == "seen"]
        self.assertEqual(len(seen), len(stories), "one seen event per kept story")
        expected_ids = {self.store.story_id(s["url"]) for s in stories}
        actual_ids = {e["story"]["id"] for e in seen}
        self.assertEqual(actual_ids, expected_ids)
        for e in seen:
            self.assertEqual(e["actor"], RECORD_SLUG)
            self.assertRegex(e["ts"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
            legacy_ids = e["story"].get("legacy_ids") or []
            self.assertTrue(legacy_ids, "seen event's story record must carry legacy_ids")
            self.assertTrue(
                all(lid.startswith(RECORD_EDITION) for lid in legacy_ids),
                f"legacy_ids must carry the pre-migration {{date}}-{{slug}}-... hid, got {legacy_ids}",
            )
            self.assertIn(RECORD_EDITION, e["story"].get("editions") or [],
                          "story.editions must carry this edition")

    def test_publish_event_per_kept_story_with_edition_and_fields(self):
        """contract LEDGER: {"ev":"publish",...,"edition":"YYYY-MM-DD-slug",
        "fields":{"display_body","why","importance","status":"settled"}}."""
        stories = _payload_stories()
        _run_record(self.root, f"dedup_{id(self)}_publish")
        pubs = [e for e in _ledger_events(self.root) if e.get("ev") == "publish"]
        self.assertEqual(len(pubs), len(stories), "one publish event per kept story")
        expected_ids = {self.store.story_id(s["url"]) for s in stories}
        self.assertEqual({e["id"] for e in pubs}, expected_ids)
        for e in pubs:
            self.assertEqual(e["actor"], RECORD_SLUG)
            self.assertEqual(e["edition"], RECORD_EDITION)
            fields = e["fields"]
            self.assertIn("display_body", fields)
            self.assertIn("why", fields)
            self.assertIn("importance", fields)
            self.assertEqual(fields.get("status"), "settled")

    def test_publish_fields_match_the_payload_verbatim(self):
        """display_body/why/importance in the publish event must be the writer's own
        Step C values, copied verbatim (DEDUP.md Step C: 'Copy, don't rewrite')."""
        stories = _payload_stories()
        by_url = {s["url"]: s for s in stories}
        _run_record(self.root, f"dedup_{id(self)}_verbatim")
        pubs = {e["id"]: e for e in _ledger_events(self.root) if e.get("ev") == "publish"}
        for url, s in by_url.items():
            sid = self.store.story_id(url)
            self.assertIn(sid, pubs)
            fields = pubs[sid]["fields"]
            self.assertEqual(fields["display_body"], s["display_body"])
            self.assertEqual(fields.get("why", ""), s.get("why", ""))
            self.assertEqual(fields["importance"], s["importance"])

    def test_running_record_twice_does_not_duplicate_materialized_stories(self):
        """contract: 'running record twice does not duplicate ledger events' — verified via
        store.materialize() (MATERIALIZER INVARIANTS (b): exact-duplicate seen/publish events
        deduped by (ev,id)/(ev,id,edition))."""
        _run_record(self.root, f"dedup_{id(self)}_first")
        _run_record(self.root, f"dedup_{id(self)}_second")
        snap = self.store.materialize(days=60, root=self.root)
        expected_ids = {self.store.story_id(s["url"]) for s in _payload_stories()}
        self.assertEqual(set(snap["stories"].keys()), expected_ids)
        self.assertEqual(len(snap["stories"]), len(expected_ids),
                          "materialized story count must not double after a second identical "
                          "record run over the same payload")
        for sid in expected_ids:
            self.assertEqual(snap["stories"][sid].get("editions"), [RECORD_EDITION])


class GitattributesUnionMergeTests(unittest.TestCase):
    """INTEGRATION (reads the real repo's committed .gitattributes, read-only — this is
    deliberately NOT a fixture/tempdir test): SPIKE §3.1 mandates
    `index/ledger/*.jsonl merge=union` at the repo root so concurrent routine commits to
    the same day's ledger file union-merge instead of conflicting."""

    def test_gitattributes_declares_ledger_union_merge(self):
        self.assertTrue(os.path.exists(GITATTR_PATH),
                         f"expected {GITATTR_PATH} to exist (SPIKE §3.1 new file)")
        with open(GITATTR_PATH) as f:
            content = f.read()
        self.assertIn("index/ledger/*.jsonl merge=union", content)


if __name__ == "__main__":
    unittest.main()
