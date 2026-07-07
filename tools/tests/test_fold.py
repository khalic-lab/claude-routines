#!/usr/bin/env python3
"""RED-phase spec tests — bridge-side feedback fold (SPIKE-2026-07-07-continuous-news.md
§3.1 LEDGER "feedback" event shape, §3.5 "Feedback + Evaluator as machine-readable state",
§4 "Feedback consumption: deterministic, bridge-side fold.py, ledger-keyed" — plus the
project-brief's binding CONTRACT clause for `tools/feedback/fold.py`).

Subject under test: `tools/feedback/fold.py` (CLI: `fold.py [--root PATH] [--dry-run]`).
Verification of downstream effects (last-write-wins tallying, vote-0 retraction) reads back
through `tools/store/store.py::materialize()` — the documented Python API
(`materialize(days=60, root=...) -> {"stories": ..., "by_legacy": ..., "by_url": ...}`) — since
that's the only consumer-facing way the SPIKE exposes folded feedback tallies.

Design decision this file locks in as part of the binding interface: the ledger `ev:"feedback"`
event's `"ts"` field is the ORIGINAL feedback record's own `ts` (the reader's vote time), not
bridge/fold wall-clock time — otherwise two votes folded in the same run would tie on `ts` (and
on `actor`, always "bridge") and last-write-wins would have no deterministic winner. This is the
only reading under which "last-write-wins" is a coherent, deterministic operation at all.

Run: cd /Users/rflnogueira/code/claude-routines && python3 -m unittest discover -s tools/tests -v
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
FIXTURES_DIR = os.path.join(TESTS_DIR, "fixtures", "fold")

FOLD_PATH = os.path.join(REPO_ROOT, "tools", "feedback", "fold.py")
STORE_PATH = os.path.join(REPO_ROOT, "tools", "store", "store.py")

# The 9 real orphaned-June record ids (feedback/2026-06.jsonl lines 23-31) — see
# tools/tests/fixtures/fold/orphaned-june/feedback/2026-06.jsonl, copied byte-for-byte.
ORPHANED_JUNE_FB_IDS = [
    "b87bd7de-3189-4c82-93d5-8b9f687e3a14",
    "2792223e-df83-4e69-aef8-2955b6d83baa",
    "18f1fa55-c342-4e8d-9b31-40441ec36653",
    "a13576d4-687b-4e35-a8ff-5759f3064a97",
    "04b9671a-b074-4f36-9c97-f16cdef5b455",
    "ae90ea0a-b37d-49c8-9732-8489b48a76e9",
    "3ea89a28-b043-4893-bb74-683b549cf3ce",
    "ca9f0abe-75a0-4e69-83d9-7be3bc01eddd",
    "88b6d86f-784c-4081-b07e-529cfcd04ec9",
]


# --------------------------------------------------------------------------- #
# infrastructure — no network, no real-repo writes
# --------------------------------------------------------------------------- #
def _assert_exists(path):
    """A missing (not-yet-implemented) file must fail THIS test clearly, not crash discovery
    of the rest of the suite."""
    if not os.path.exists(path):
        raise AssertionError(f"expected implementation file is missing: {path}")


def _load_module(path, name):
    import importlib.util
    _assert_exists(path)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _copy_scenario(name):
    """Copy a static fixture scenario tree (tools/tests/fixtures/fold/<name>/) into a FRESH
    tempdir root. Never touches the real repo's index/feedback/sources/_data/_posts."""
    src = os.path.join(FIXTURES_DIR, name)
    assert os.path.isdir(src), f"missing fixture scenario dir: {src}"
    dst = tempfile.mkdtemp(prefix=f"fold-{name}-")
    shutil.copytree(src, dst, dirs_exist_ok=True)
    return dst


def _run_fold(root, *extra_args, timeout=30):
    _assert_exists(FOLD_PATH)
    proc = subprocess.run(
        [sys.executable, FOLD_PATH, "--root", root, *extra_args],
        capture_output=True, text=True, timeout=timeout,
    )
    return proc


def _feedback_records(root):
    """{fb id: parsed record} across every feedback/*.jsonl file under root."""
    out = {}
    for path in sorted(glob.glob(os.path.join(root, "feedback", "*.jsonl"))):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                out[rec["id"]] = rec
    return out


def _feedback_raw_lines(root):
    """{fb id: raw undecoded line bytes} across every feedback/*.jsonl — for byte-preservation
    assertions (must survive independent of key order / json.dumps formatting choices)."""
    out = {}
    for path in sorted(glob.glob(os.path.join(root, "feedback", "*.jsonl"))):
        with open(path, "rb") as f:
            for raw in f:
                raw = raw.rstrip(b"\n")
                if not raw.strip():
                    continue
                rec = json.loads(raw.decode("utf-8"))
                out[rec["id"]] = raw
    return out


def _feedback_records_tolerant(root):
    """Like `_feedback_records` but silently skips any line that fails to parse as JSON —
    used only by the corrupt-line resilience tests (FINDING 2), where exactly one bad line is
    expected to persist by design and must not blow up the assertion helper itself."""
    out = {}
    for path in sorted(glob.glob(os.path.join(root, "feedback", "*.jsonl"))):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                out[rec["id"]] = rec
    return out


def _ledger_events(root, ev=None):
    out = []
    for path in sorted(glob.glob(os.path.join(root, "index", "ledger", "*.jsonl"))):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                e = json.loads(line)
                if ev is None or e.get("ev") == ev:
                    out.append(e)
    return out


def _snapshot_tree(root):
    """{relpath: bytes} for every file under root, recursively — a whole-tree fingerprint used
    to prove --dry-run writes NOTHING."""
    snap = {}
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root)
            with open(full, "rb") as f:
                snap[rel] = f.read()
    return snap


class FoldBasicScenarioTests(unittest.TestCase):
    """Covers every resolution path from the CONTRACT's ordered rule using the `basic` fixture
    (tools/tests/fixtures/fold/basic/): a direct st-id, a legacy-id, an unresolvable id, a
    URL-carried resolution, a last-write-wins pair, and a vote-0 retraction pair."""

    def setUp(self):
        self.root = _copy_scenario("basic")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_direct_st_prefixed_story_id_resolved_directly(self):
        """CONTRACT fold.py: "resolve raw story_id -> st-id (starts with 'st-': direct...)".
        fb-direct-0001 already carries `story_id: "st-7b08aa59704a"` — must fold straight
        through with no ledger lookup, get consumed:true, and backfill source_domain from the
        matching seen-story's url (example.com/story-alpha -> "example.com")."""
        proc = _run_fold(self.root)
        self.assertEqual(proc.returncode, 0, f"fold.py failed: {proc.stderr}")

        recs = _feedback_records(self.root)
        rec = recs["fb-direct-0001"]
        self.assertTrue(rec["consumed"], "resolved record must be marked consumed:true")
        self.assertEqual(rec["source_domain"], "example.com",
                          "source_domain must be backfilled from the resolved story's url")

        fb_events = {e["fb_id"]: e for e in _ledger_events(self.root, ev="feedback")}
        self.assertIn("fb-direct-0001", fb_events)
        ev = fb_events["fb-direct-0001"]
        self.assertEqual(ev["id"], "st-7b08aa59704a")
        self.assertEqual(ev["actor"], "bridge")
        self.assertEqual(ev["vote"], 1)

    def test_legacy_story_id_resolved_via_ledger_by_legacy(self):
        """CONTRACT fold.py: "...else legacy id via materialize()'s by_legacy...". fb-legacy-0001
        carries the pre-migration slug id "2026-06-20-ai-ml-legacy-piece-one", which only the
        fixture ledger's seen-story `legacy_ids` array knows resolves to st-4eba868bbc4c. Also
        pins the full ledger feedback-event shape (SPIKE §3.1) and the ts-preservation design
        decision documented at module top (ts == original record's ts, not fold wall-clock)."""
        proc = _run_fold(self.root)
        self.assertEqual(proc.returncode, 0, f"fold.py failed: {proc.stderr}")

        recs = _feedback_records(self.root)
        rec = recs["fb-legacy-0001"]
        self.assertTrue(rec["consumed"])
        self.assertEqual(rec["source_domain"], "openai.com")

        fb_events = {e["fb_id"]: e for e in _ledger_events(self.root, ev="feedback")}
        ev = fb_events["fb-legacy-0001"]
        self.assertEqual(ev["id"], "st-4eba868bbc4c",
                          "must resolve via legacy_ids, not treat the slug as a literal id")
        self.assertEqual(ev["raw_story_id"], "2026-06-20-ai-ml-legacy-piece-one",
                          "raw_story_id preserves exactly what the record originally carried")
        self.assertEqual(ev["actor"], "bridge")
        self.assertEqual(ev["vote"], -1)
        self.assertEqual(ev["reason"], "worth noting")
        self.assertEqual(ev["reader"], "rafael")
        self.assertEqual(ev["surface"], "web")
        self.assertEqual(ev["brief"], "2026-06-20-ai-ml")
        self.assertEqual(ev["ts"], "2026-06-25T09:01:00.000Z",
                          "ledger event ts must be the reader's own vote time, not fold time")

    def test_unresolvable_story_id_left_unconsumed_and_reported(self):
        """CONTRACT fold.py: "unresolvable: leave consumed:false, count + print reason".
        fb-unresolvable-0001's story_id matches no st-id, no legacy_ids, and carries no url."""
        proc = _run_fold(self.root)
        self.assertEqual(proc.returncode, 0, "a tool crash is not expected here; unresolved "
                          "records are reported, not fatal (§4 failure-semantics contract)")

        recs = _feedback_records(self.root)
        rec = recs["fb-unresolvable-0001"]
        self.assertFalse(rec["consumed"], "unresolvable record must stay consumed:false")

        fb_events = {e["fb_id"] for e in _ledger_events(self.root, ev="feedback")}
        self.assertNotIn("fb-unresolvable-0001", fb_events,
                          "no ledger event may be fabricated for an unresolvable record")

        haystack = proc.stdout + proc.stderr
        self.assertIn("fb-unresolvable-0001", haystack,
                      "fold.py must print the unresolved record so it's not silently dropped")

    def test_source_domain_backfilled_via_url_carried_resolution(self):
        """CONTRACT fold.py: "...else by URL if the record carries one...". fb-byurl-0001's
        story_id ("misc-slug-that-matches-nothing") resolves neither directly nor via
        legacy_ids; only its extra `url` field (matching a seen story's url) resolves it."""
        proc = _run_fold(self.root)
        self.assertEqual(proc.returncode, 0, f"fold.py failed: {proc.stderr}")

        recs = _feedback_records(self.root)
        rec = recs["fb-byurl-0001"]
        self.assertTrue(rec["consumed"])
        self.assertEqual(rec["source_domain"], "nature.com")

        fb_events = {e["fb_id"]: e for e in _ledger_events(self.root, ev="feedback")}
        ev = fb_events["fb-byurl-0001"]
        self.assertEqual(ev["id"], "st-12658dcb72df")
        self.assertEqual(ev["raw_story_id"], "misc-slug-that-matches-nothing")

    def test_consumed_flag_set_only_on_folded_records(self):
        """CONTRACT fold.py: consumed:true only for records fold.py actually resolved+folded;
        the one genuinely unresolvable record in `basic` must not flip."""
        proc = _run_fold(self.root)
        self.assertEqual(proc.returncode, 0, f"fold.py failed: {proc.stderr}")

        recs = _feedback_records(self.root)
        resolved_ids = {
            "fb-direct-0001", "fb-legacy-0001", "fb-byurl-0001",
            "fb-lww-0001", "fb-lww-0002", "fb-retract-0001", "fb-retract-0002",
        }
        for fb_id in resolved_ids:
            self.assertTrue(recs[fb_id]["consumed"], f"{fb_id} should be consumed:true")
        self.assertFalse(recs["fb-unresolvable-0001"]["consumed"])

    def test_untouched_records_byte_preserved_on_rewrite(self):
        """CONTRACT fold.py: "Rewrites the feedback jsonl files preserving field order/format
        of untouched records." fb-unresolvable-0001 is never touched (unresolvable) so its raw
        JSON line must come back byte-identical, whatever normalization fold.py applies to the
        records it DOES fold."""
        before = _feedback_raw_lines(self.root)["fb-unresolvable-0001"]
        proc = _run_fold(self.root)
        self.assertEqual(proc.returncode, 0, f"fold.py failed: {proc.stderr}")
        after = _feedback_raw_lines(self.root)["fb-unresolvable-0001"]
        self.assertEqual(before, after,
                          "an untouched record's line must be byte-identical after rewrite")

    def test_dry_run_writes_nothing_but_prints_disposition_table(self):
        """CONTRACT fold.py: "--dry-run: prints full disposition table, writes NOTHING." Proven
        by a whole-fixture-tree byte snapshot before/after (no feedback rewrite, no ledger
        append, no stray files), while stdout still names every record (a "full" table)."""
        before = _snapshot_tree(self.root)
        proc = _run_fold(self.root, "--dry-run")
        self.assertEqual(proc.returncode, 0, f"fold.py --dry-run failed: {proc.stderr}")
        after = _snapshot_tree(self.root)
        self.assertEqual(before, after, "--dry-run must not modify a single byte on disk")

        all_fb_ids = [
            "fb-direct-0001", "fb-legacy-0001", "fb-unresolvable-0001", "fb-byurl-0001",
            "fb-lww-0001", "fb-lww-0002", "fb-retract-0001", "fb-retract-0002",
        ]
        for fb_id in all_fb_ids:
            self.assertIn(fb_id, proc.stdout,
                          f"--dry-run disposition table must name {fb_id}")

    def test_fb_id_dedupe_idempotent_on_second_run(self):
        """CONTRACT fold.py: "For resolved records not yet in the ledger (by fb_id): append
        ev:'feedback'..." — a second run over the same root must be a complete no-op: it must
        not duplicate any ledger event, nor further mutate the feedback files."""
        proc1 = _run_fold(self.root)
        self.assertEqual(proc1.returncode, 0, f"first fold run failed: {proc1.stderr}")
        events_after_1 = _ledger_events(self.root, ev="feedback")
        fb_ids_after_1 = sorted(e["fb_id"] for e in events_after_1)
        self.assertEqual(len(fb_ids_after_1), len(set(fb_ids_after_1)),
                          "no duplicate fb_id after the very first run")
        tree_after_1 = _snapshot_tree(self.root)

        proc2 = _run_fold(self.root)
        self.assertEqual(proc2.returncode, 0, f"second fold run failed: {proc2.stderr}")
        events_after_2 = _ledger_events(self.root, ev="feedback")
        fb_ids_after_2 = sorted(e["fb_id"] for e in events_after_2)

        self.assertEqual(fb_ids_after_1, fb_ids_after_2,
                          "re-running fold.py must not append any new/duplicate feedback event")
        tree_after_2 = _snapshot_tree(self.root)
        self.assertEqual(tree_after_1, tree_after_2,
                          "a fully-idempotent second run changes nothing on disk")

    def test_last_write_wins_and_vote_zero_retraction_in_materialized_tallies(self):
        """CONTRACT MATERIALIZER INVARIANT (d): "feedback folds last-write-wins per (reader, id,
        surface), vote 0 clears the pair, folded tallies land in record.feedback{up,down,
        last_reason}." fb-lww-0001 (+1) then fb-lww-0002 (-1, later ts) on the same story must
        net to down:1/up:0 with the later reason; fb-retract-0001 (+1) then fb-retract-0002 (0,
        later ts) on a different story must net to up:0/down:0 (cleared)."""
        proc = _run_fold(self.root)
        self.assertEqual(proc.returncode, 0, f"fold.py failed: {proc.stderr}")

        store = _load_module(STORE_PATH, f"store_{id(self)}")
        snap = store.materialize(days=60, root=self.root)
        stories = snap["stories"]

        lww = stories["st-792f49ec94fd"]["feedback"]
        self.assertEqual(lww["up"], 0)
        self.assertEqual(lww["down"], 1)
        self.assertEqual(lww["last_reason"], "actually not great")

        retracted = stories["st-8698e6579d64"]["feedback"]
        self.assertEqual(retracted["up"], 0)
        self.assertEqual(retracted["down"], 0,
                          "a later vote:0 must clear the (reader,id,surface) pair entirely")


class FoldOrphanedJuneRealWorldTests(unittest.TestCase):
    """The named migration task (SPIKE §3.5 / CLAUDE.md-adjacent): "fold the 9 orphaned records
    at feedback/2026-06.jsonl lines 23-31." Uses the REAL 9 records (byte-identical copies —
    see the docstring/diff proof at fixture-generation time) against a fixture ledger whose
    seen-story legacy_ids match their real (pre-anchor) `{date}-{stream}-{slugified-headline}`
    story_id values."""

    def setUp(self):
        self.root = _copy_scenario("orphaned-june")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_all_nine_orphaned_records_fold_successfully(self):
        recs_before = _feedback_records(self.root)
        self.assertEqual(set(recs_before.keys()), set(ORPHANED_JUNE_FB_IDS),
                          "fixture must reproduce exactly the 9 real orphaned records")
        for fb_id in ORPHANED_JUNE_FB_IDS:
            self.assertFalse(recs_before[fb_id]["consumed"],
                              "sanity: these really are the orphaned (unconsumed) records")

        proc = _run_fold(self.root)
        self.assertEqual(proc.returncode, 0, f"fold.py failed: {proc.stderr}")

        recs_after = _feedback_records(self.root)
        for fb_id in ORPHANED_JUNE_FB_IDS:
            self.assertTrue(recs_after[fb_id]["consumed"],
                             f"{fb_id} must fold successfully — the 27%-orphaning class this "
                             f"migration step exists to close")
            self.assertTrue(recs_after[fb_id]["source_domain"],
                             f"{fb_id} must get a backfilled source_domain")

        fb_events = {e["fb_id"]: e for e in _ledger_events(self.root, ev="feedback")}
        self.assertEqual(set(fb_events.keys()), set(ORPHANED_JUNE_FB_IDS),
                          "exactly one ledger feedback event per orphaned record, no more")
        for fb_id in ORPHANED_JUNE_FB_IDS:
            self.assertTrue(fb_events[fb_id]["id"].startswith("st-"),
                             "resolved id must be a real store id, not the legacy slug")

    def test_all_nine_fold_with_zero_unresolved(self):
        """Every one of the 9 must resolve via legacy_ids — none should land in the
        unresolved bucket (the whole point of the migration task)."""
        proc = _run_fold(self.root)
        self.assertEqual(proc.returncode, 0, f"fold.py failed: {proc.stderr}")
        recs = _feedback_records(self.root)
        still_unconsumed = [fb_id for fb_id in ORPHANED_JUNE_FB_IDS if not recs[fb_id]["consumed"]]
        self.assertEqual(still_unconsumed, [], f"unresolved orphans remain: {still_unconsumed}")


class FoldCrashSafetyTests(unittest.TestCase):
    """FINDING 1 (CRITICAL): fold.py's docstring promises append-before-rewrite ("a run that
    appended but died before rewriting feedback/*.jsonl won't double-append on retry") — a
    crash/error DURING the ledger-append phase must never leave a feedback record flipped
    consumed:true with no matching ledger event. That's a silently orphaned vote, forever (the
    exact defect class this tool exists to kill). We force a real append failure by making
    index/ledger unwritable (chmod), so store.append_event raises for real — no mocking of
    fold.py's internals, since it runs as a subprocess."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="fold-crash-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.addCleanup(self._unlock_ledger_dir)
        os.makedirs(os.path.join(self.root, "feedback"))
        self.ledger_dir = os.path.join(self.root, "index", "ledger")
        os.makedirs(self.ledger_dir)

        # seed ledger: one seen story so both feedback records resolve directly (st- prefixed,
        # no legacy/url lookup needed) — keeps the scenario focused on the append/rewrite race.
        seed = {"ev": "seen", "ts": "2026-06-25T06:00:00Z", "actor": "news",
                "story": {"id": "st-crash0001aaaa", "url": "https://example.com/crash-story",
                          "headline": "H", "summary": "S", "status": "settled",
                          "first_seen": "2026-06-25T06:00:00Z", "updated": "2026-06-25T06:00:00Z"}}
        with open(os.path.join(self.ledger_dir, "2026-06-25.jsonl"), "w", encoding="utf-8") as f:
            f.write(json.dumps(seed, ensure_ascii=False) + "\n")

        self.feedback_path = os.path.join(self.root, "feedback", "2026-06.jsonl")
        self.records_before = [
            {"id": "fb-crash-0001", "ts": "2026-06-25T09:00:00.000Z", "reader": "rafael",
             "brief": "2026-06-25-news", "story_id": "st-crash0001aaaa", "vote": 1, "reason": "",
             "surface": "web", "source_domain": None, "consumed": False},
            {"id": "fb-crash-0002", "ts": "2026-06-25T09:01:00.000Z", "reader": "rafael",
             "brief": "2026-06-25-news", "story_id": "st-crash0001aaaa", "vote": -1, "reason": "",
             "surface": "web", "source_domain": None, "consumed": False},
        ]
        with open(self.feedback_path, "w", encoding="utf-8") as f:
            for rec in self.records_before:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        with open(self.feedback_path, "rb") as f:
            self._before_bytes = f.read()

    def _lock_ledger_dir(self):
        # no write bit -> append_event's open(path, "a") on a not-yet-existing day file raises
        # PermissionError; read/list/materialize still work (r-x retained).
        os.chmod(self.ledger_dir, 0o555)

    def _unlock_ledger_dir(self):
        os.chmod(self.ledger_dir, 0o755)

    def test_append_failure_leaves_feedback_file_byte_untouched_and_appends_no_partial_events(self):
        self._lock_ledger_dir()
        try:
            proc = _run_fold(self.root)
        finally:
            self._unlock_ledger_dir()

        self.assertNotEqual(proc.returncode, 0,
                             "an append failure must surface as a fold.py failure, not be "
                             "swallowed silently")

        with open(self.feedback_path, "rb") as f:
            after = f.read()
        self.assertEqual(after, self._before_bytes,
                          "FINDING 1: the ledger append must happen BEFORE the feedback file is "
                          "rewritten — an append failure must leave the feedback file "
                          "byte-untouched, never consumed:true with no matching ledger event")

        self.assertEqual(_ledger_events(self.root, ev="feedback"), [],
                          "no partial/orphaned ledger events from a failed append")

    def test_rerun_after_a_cleared_failure_folds_everything_exactly_once(self):
        self._lock_ledger_dir()
        try:
            proc1 = _run_fold(self.root)
        finally:
            self._unlock_ledger_dir()
        self.assertNotEqual(proc1.returncode, 0, "sanity: the induced failure must actually bite")

        proc2 = _run_fold(self.root)
        self.assertEqual(proc2.returncode, 0,
                          f"retry after the crash is cleared must succeed: {proc2.stderr}")

        recs = _feedback_records(self.root)
        self.assertTrue(recs["fb-crash-0001"]["consumed"])
        self.assertTrue(recs["fb-crash-0002"]["consumed"])

        fb_events = _ledger_events(self.root, ev="feedback")
        fb_ids = [e["fb_id"] for e in fb_events]
        self.assertEqual(set(fb_ids), {"fb-crash-0001", "fb-crash-0002"},
                          "both records must fold on the retry")
        self.assertEqual(len(fb_ids), len(set(fb_ids)),
                          "exactly one ledger event per fb_id — never duplicated across the "
                          "failed attempt and the retry")

        # a third run must be a complete no-op (standard idempotence, re-checked post-crash)
        proc3 = _run_fold(self.root)
        self.assertEqual(proc3.returncode, 0)
        self.assertEqual(_ledger_events(self.root, ev="feedback"), fb_events,
                          "a clean re-run after the retry must not append anything further")


class FoldCorruptLineResilienceTests(unittest.TestCase):
    """FINDING 2 (MINOR): one corrupt/truncated JSON line anywhere in a feedback/*.jsonl must
    not abort the whole fold. It must be skipped with a printed warning, every other record in
    that file (and other files) folds normally, and the corrupt line is preserved
    byte-identically on rewrite — never dropped, never "fixed"."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="fold-corrupt-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        os.makedirs(os.path.join(self.root, "feedback"))
        os.makedirs(os.path.join(self.root, "index", "ledger"))

        seed = {"ev": "seen", "ts": "2026-06-25T06:00:00Z", "actor": "news",
                "story": {"id": "st-corruptaaaa1", "url": "https://example.com/corrupt-story",
                          "headline": "H", "summary": "S", "status": "settled",
                          "first_seen": "2026-06-25T06:00:00Z", "updated": "2026-06-25T06:00:00Z"}}
        with open(os.path.join(self.root, "index", "ledger", "2026-06-25.jsonl"),
                  "w", encoding="utf-8") as f:
            f.write(json.dumps(seed, ensure_ascii=False) + "\n")

        self.feedback_path = os.path.join(self.root, "feedback", "2026-06.jsonl")
        # deliberately truncated mid-object — a garbage line sandwiched between two valid ones
        self.corrupt_line = '{"id": "fb-corrupt-0002", "ts": "2026-06-25T09:0'
        rec1 = {"id": "fb-corrupt-0001", "ts": "2026-06-25T09:00:00.000Z", "reader": "rafael",
                "brief": "2026-06-25-news", "story_id": "st-corruptaaaa1", "vote": 1, "reason": "",
                "surface": "web", "source_domain": None, "consumed": False}
        rec3 = {"id": "fb-corrupt-0003", "ts": "2026-06-25T09:02:00.000Z", "reader": "rafael",
                "brief": "2026-06-25-news", "story_id": "st-corruptaaaa1", "vote": -1, "reason": "",
                "surface": "web", "source_domain": None, "consumed": False}
        with open(self.feedback_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(rec1, ensure_ascii=False) + "\n")
            f.write(self.corrupt_line + "\n")
            f.write(json.dumps(rec3, ensure_ascii=False) + "\n")

    def test_corrupt_line_does_not_abort_the_fold(self):
        proc = _run_fold(self.root)
        self.assertEqual(proc.returncode, 0,
                          f"a single corrupt line must not crash the whole fold: {proc.stderr}")

        recs = _feedback_records_tolerant(self.root)
        self.assertTrue(recs["fb-corrupt-0001"]["consumed"],
                         "the valid record BEFORE the corrupt line must still fold")
        self.assertTrue(recs["fb-corrupt-0003"]["consumed"],
                         "the valid record AFTER the corrupt line must still fold")

        fb_events = {e["fb_id"] for e in _ledger_events(self.root, ev="feedback")}
        self.assertEqual(fb_events, {"fb-corrupt-0001", "fb-corrupt-0003"})

    def test_corrupt_line_prints_a_warning(self):
        proc = _run_fold(self.root)
        self.assertEqual(proc.returncode, 0)
        haystack = (proc.stdout + proc.stderr).lower()
        self.assertTrue(
            any(kw in haystack for kw in ("corrupt", "invalid", "malformed", "skip")),
            f"expected a printed warning naming the bad line, got:\n{proc.stdout}\n{proc.stderr}")

    def test_corrupt_line_preserved_byte_identical_on_rewrite_not_dropped(self):
        proc = _run_fold(self.root)
        self.assertEqual(proc.returncode, 0, f"fold.py failed: {proc.stderr}")

        with open(self.feedback_path, "rb") as f:
            lines = [ln for ln in f.read().split(b"\n") if ln.strip()]
        self.assertIn(self.corrupt_line.encode("utf-8"), lines,
                      "the corrupt line must survive the rewrite byte-identical — never dropped, "
                      "never patched up")
        self.assertEqual(len(lines), 3,
                          "no line may vanish: two valid (now folded) records + the one "
                          "preserved corrupt line")


if __name__ == "__main__":
    unittest.main()
