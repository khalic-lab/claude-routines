#!/usr/bin/env python3
"""RED-phase spec tests for tools/evaluator/metrics.py (not yet implemented).

Design authority: docs/SPIKE-2026-07-07-continuous-news.md sections 3-5
(story-centric ledger, §3.5 "Evaluator as machine-readable state", §4
deterministic-tooling table). Where the binding task contract for this file
is more specific than the SPIKE's prose, the contract wins (per instructions);
this file IS that contract, and IS the schema authority for `_data/health.json`
(the contract explicitly delegates schema-fixing to the test author).

## _data/health.json schema fixed by this file

    {
      "week": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},   # the --week arg
                                                                 # is `end`; the
                                                                 # window is the
                                                                 # 7 calendar days
                                                                 # [end-6, end]
                                                                 # inclusive.
      "streams": {
        "<stream>": {
          "editions": [...],       # sorted "YYYY-MM-DD-slug" edition ids with
                                    # >=1 publish event strictly inside the
                                    # window (sparse: streams with zero
                                    # in-window editions are absent, not
                                    # zero-filled -- includes the empty-root
                                    # case, "streams": {}).
          "citations": int,        # total in-window publish events for this
                                    # stream, AFTER dedup by (ev, id, edition)
                                    # -- ts is NOT part of the dedup key (a
                                    # retried append with a new ts must not
                                    # double-count).
          "anchors": int,           # distinct story ids published in-window
                                    # for this stream.
          "repeats": int,           # in-window occurrences (citations) whose
                                    # id OR thread_id had an EARLIER edition
                                    # (any actor/stream) within the 14 days
                                    # preceding this occurrence's ts, per the
                                    # ledger -- the earlier occurrence itself
                                    # may lie OUTSIDE the --week window (the
                                    # 14-day lookback is independent of the
                                    # window's start bound) and is not itself
                                    # required to be a "citation" of anything.
          "repeat_rate": float,      # repeats / citations, 0.0 if citations==0
          "by_edition": {"<edition>": {"citations": int, "anchors": int}},
        },
      },
      "feedback": {
        "unconsumed_total": int,   # count of consumed:false records straight
                                    # from feedback/*.jsonl -- NO --week
                                    # filtering (deliberately unfiltered: this
                                    # is a backlog count, not a window metric).
        "notify_count": int,        # count of ledger ev:"notify" events
                                    # inside the --week window (0 if none/
                                    # absent -- pending-notifications/ history
                                    # is transient, per contract).
        "by_stream": {
          "<stream>": {"up": int, "down": int, "retractions": int},
          # derived from RAW ledger ev:"feedback" events inside the window,
          # stream taken from the event's "brief" field (actor is always
          # "bridge" on feedback events, so it cannot supply the stream).
          # up = count of vote==1 events, down = count of vote==-1 events,
          # retractions = count of vote==0 events. This is a raw tally, NOT
          # the last-write-wins per-story fold that store.py performs for
          # the registry lifecycle -- a vote followed by its own retraction
          # contributes one to "up" AND one to "retractions", by design (it
          # is a mechanical count of what happened, not a net verdict).
          # Sparse: a stream with zero in-window feedback events is absent.
        },
      },
      "sources": <verbatim contents of _data/source-health.json>,
      # or, if that file is absent: {"available": false,
      #                               "reason": "source-health.json not found"}
      # -- metrics.py must degrade gracefully here, never crash (SPIKE §4
      # failure-semantics: "a tool crash degrades to a Gaps note ... never
      # abort").
      "continuity": {
        "previous_evaluator_found": bool,
        "previous_evaluator_path": "_posts/....md" | None,
        # most recent `_posts/*-evaluator.md` dated strictly before
        # week.end, POSIX-relative to --root. Deliberately "most recent
        # prior post" rather than "exactly 7 days ago": the SPIKE (§2)
        # attributes 2 of 9 real continuity failures to that brittle exact-
        # offset heuristic.
      },
    }

Every key is snake_case per contract. metrics.py must also print this same
object as JSON to stdout (this file's `test_prints_health_json` pins that
reading of "writes _data/health.json + prints it").

## Test infrastructure

stdlib unittest only. Run: `python3 -m unittest tools.tests.test_metrics -v`
(or the whole suite via `python3 -m unittest discover -s tools/tests -v`).
Fixture repo skeletons live under tools/tests/fixtures/metrics/ and are copied
into a fresh tempfile.mkdtemp() per class in setUpClass -- metrics.py is only
ever invoked with --root pointing at a throwaway copy, never the real repo.
No network: metrics.py's whole job is reading local ledger/feedback/_data/
_posts files, so nothing here needs stubbing.

Fixture ids (`st-<sha1(norm_url)[:12]>`) are computed at test time via the
SAME norm_url() as tools/build_stories_feed.py (imported by path, per the
contract: "norm_url = EXACTLY the semantics of the existing norm_url()") --
never hand-transcribed hex, so a future norm_url edit can't silently desync
the fixtures from the assertions.
"""

import glob
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
METRICS_PATH = os.path.join(REPO, "tools", "evaluator", "metrics.py")
FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "metrics")

# --- norm_url()/story_id() reference, loaded from the existing, already-shipped
# tools/build_stories_feed.py -- the contract's binding source of truth for the
# id formula. This module DOES exist today, so this import is expected to
# succeed even in the RED phase (only tools/evaluator/metrics.py is pending).
_bsf_path = os.path.join(REPO, "tools", "build_stories_feed.py")
assert os.path.exists(_bsf_path), (
    "tools/build_stories_feed.py not found at %s -- norm_url() reference "
    "implementation is missing; this is unrelated to the metrics.py RED "
    "phase and indicates repo layout drift." % _bsf_path
)
_spec = importlib.util.spec_from_file_location("build_stories_feed_ref", _bsf_path)
_bsf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bsf)
norm_url = _bsf.norm_url


def story_id(url):
    """Contract: STORY ID = "st-" + sha1(norm_url(url)).hexdigest()[:12]."""
    return "st-" + hashlib.sha1(norm_url(url).encode("utf-8")).hexdigest()[:12]


# Fixture URLs (module-level so both the fixture-authoring script and this
# test derive ids from the identical strings; see gen fixtures provenance in
# tools/tests/fixtures/metrics/ -- the .jsonl content was generated from these
# same URLs, not hand-typed).
URLS = {
    "A": "https://www.srf.ch/news/schweiz/story-a-example",
    "B": "https://www.aljazeera.com/news/2026/6/30/story-b-example",
    "C": "https://www.letemps.ch/articles/story-c-example",
    "D": "https://www.srf.ch/news/international/story-d-example",
    "E": "https://www.nature.com/articles/s41586-026-story-e",
    "F": "https://www.aljazeera.com/news/2026/7/8/story-f-example",
    "OLD": "https://www.srf.ch/news/schweiz/story-old-example",
    "G1": "https://www.aljazeera.com/news/2026/6/29/thread-genesis-example",
    "G2": "https://www.aljazeera.com/news/2026/7/1/thread-followup-example",
}
IDS = {k: story_id(u) for k, u in URLS.items()}


def _mktemp_copy(skeleton_name):
    """Copies a fixture repo skeleton into a fresh tempdir; returns its path."""
    src = os.path.join(FIXTURES_DIR, skeleton_name)
    assert os.path.isdir(src), "fixture skeleton missing: %s" % src
    dst = tempfile.mkdtemp(prefix="metrics-test-%s-" % skeleton_name)
    shutil.copytree(src, dst, dirs_exist_ok=True)
    return dst


def _run_metrics(root, extra_args=None, timeout=30):
    """Invokes metrics.py as a subprocess CLI against `root`.

    Asserts the script FILE exists first, with a clear message, per the
    "missing module -> FAILURE not crash" test-infrastructure rule -- every
    caller of this helper gets the same clear signal in the RED phase.
    """
    assert os.path.exists(METRICS_PATH), (
        "tools/evaluator/metrics.py does not exist yet at %s -- RED phase, "
        "not implemented. This test intentionally FAILS (not crashes) until "
        "it is." % METRICS_PATH
    )
    args = [sys.executable, METRICS_PATH, "--root", root] + (extra_args or [])
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)


def _health_path(root):
    return os.path.join(root, "_data", "health.json")


def _run_and_load(root, extra_args=None):
    """Runs metrics.py and returns (CompletedProcess, parsed health.json | None)."""
    proc = _run_metrics(root, extra_args)
    hp = _health_path(root)
    health = None
    if os.path.exists(hp):
        with open(hp) as fh:
            health = json.load(fh)
    return proc, health


def _assert_clean_run(test, proc, health, root):
    test.assertEqual(
        proc.returncode, 0,
        "metrics.py exited %s\n--- stdout ---\n%s\n--- stderr ---\n%s"
        % (proc.returncode, proc.stdout, proc.stderr),
    )
    test.assertIsNotNone(health, "metrics.py did not write %s" % _health_path(root))


class MetricsScriptExistsTest(unittest.TestCase):
    """Standalone existence check so a missing module fails clearly and fast,
    independent of the (much larger) setUpClass in MetricsHealthTest below."""

    def test_metrics_script_exists(self):
        """Contract: CLI lives at tools/evaluator/metrics.py."""
        self.assertTrue(
            os.path.exists(METRICS_PATH),
            "tools/evaluator/metrics.py not found at %s" % METRICS_PATH,
        )


class MetricsHealthMainFixtureTest(unittest.TestCase):
    """One shared repo_skeleton fixture + a small number of metrics.py
    invocations against it, cached in setUpClass; individual test_ methods
    assert on one dimension each of the cached, already-parsed results so a
    partial implementation surfaces which dimension is wrong rather than one
    monolithic pass/fail."""

    @classmethod
    def setUpClass(cls):
        assert os.path.exists(METRICS_PATH), (
            "tools/evaluator/metrics.py does not exist yet at %s -- RED "
            "phase, not implemented." % METRICS_PATH
        )
        cls.root = _mktemp_copy("repo_skeleton")

        cls.proc_main, cls.health_main = _run_and_load(cls.root, ["--week", "2026-07-06"])
        # Re-running with a different --week against the SAME root/ledger
        # proves --week actually parameterizes the window (rather than being
        # accepted and ignored) -- health.json is overwritten between runs,
        # which is why each result is captured immediately.
        cls.proc_narrow, cls.health_narrow = _run_and_load(cls.root, ["--week", "2026-07-01"])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    # --- sanity -------------------------------------------------------

    def test_main_run_clean_exit_and_writes_health_json(self):
        """Contract: `metrics.py [--root PATH] [--week ...]` writes _data/health.json."""
        _assert_clean_run(self, self.proc_main, self.health_main, self.root)

    def test_narrow_run_clean_exit_and_writes_health_json(self):
        """Same CLI, different --week, must also succeed cleanly."""
        _assert_clean_run(self, self.proc_narrow, self.health_narrow, self.root)

    def test_top_level_schema_keys(self):
        """Contract: top level is exactly {week, streams, feedback, sources,
        continuity, briefs}, snake_case ("briefs" added 2026-07-18 -- the
        computed brief-text dimensions B/D/F/G/H/K/L)."""
        self.assertEqual(
            set(self.health_main.keys()),
            {"week", "streams", "feedback", "sources", "continuity", "briefs"},
        )
        for k in self.health_main:
            self.assertEqual(k, k.lower())
            self.assertNotIn("-", k)

    def test_week_window_is_seven_days_ending_at_week_arg(self):
        """`--week 2026-07-06` -> the 7 calendar days [2026-06-30, 2026-07-06] inclusive."""
        self.assertEqual(
            self.health_main["week"],
            {"start": "2026-06-30", "end": "2026-07-06"},
        )

    # --- per-edition citation/anchor counts (news) ---------------------

    def test_news_editions_within_window(self):
        """Editions list contains only in-window news posts; 2026-07-08-news
        (published after the window end) and 2026-06-24-science (a different
        stream entirely) must not appear. Window exclusion, contract clause
        "per-edition citation/anchor counts" + "--week windowing"."""
        self.assertEqual(
            self.health_main["streams"]["news"]["editions"],
            ["2026-06-30-news", "2026-07-02-news", "2026-07-05-news"],
        )

    def test_news_citations_and_anchors_totals(self):
        """5 total publish events (A,B on 06-30; A-repeat,C on 07-02; D on
        07-05) but only 4 distinct anchored stories (A repeats)."""
        self.assertEqual(self.health_main["streams"]["news"]["citations"], 5)
        self.assertEqual(self.health_main["streams"]["news"]["anchors"], 4)

    def test_news_by_edition_breakdown(self):
        """Per-edition citation/anchor counts, the literal contract phrase."""
        self.assertEqual(
            self.health_main["streams"]["news"]["by_edition"],
            {
                "2026-06-30-news": {"citations": 2, "anchors": 2},
                "2026-07-02-news": {"citations": 2, "anchors": 2},
                "2026-07-05-news": {"citations": 1, "anchors": 1},
            },
        )

    def test_retried_duplicate_publish_event_does_not_double_count(self):
        """Materializer invariant (b): publish events dedup by (ev, id,
        edition) -- ts is NOT part of the key. Story D's ledger day
        (2026-07-05.jsonl) contains a same-(ev,id,edition) publish event
        appended twice, 7 seconds apart (simulating a retried append), and
        must still count as exactly one citation."""
        self.assertEqual(
            self.health_main["streams"]["news"]["by_edition"]["2026-07-05-news"],
            {"citations": 1, "anchors": 1},
        )

    # --- per-edition citation/anchor counts (science, ### register) ----

    def test_science_editions_within_window_excludes_prewindow_genesis(self):
        """The 2026-06-24-science genesis edition (story E's first-ever
        occurrence) predates the window (window starts 2026-06-30) and must
        be excluded from `editions`/citations/anchors entirely, even though
        it is used below to flag the 07-01 occurrence as a repeat."""
        self.assertEqual(
            self.health_main["streams"]["science"]["editions"],
            ["2026-07-01-science"],
        )
        self.assertEqual(self.health_main["streams"]["science"]["citations"], 1)
        self.assertEqual(self.health_main["streams"]["science"]["anchors"], 1)

    # --- repeat-rate proxy ----------------------------------------------

    def test_repeat_same_id_within_window(self):
        """Story A: published 2026-06-30-news (genesis, NOT a repeat) then
        again 2026-07-02-news (repeat: same id/norm_url appeared in an
        earlier edition within 14d). news.repeats counts only the second
        occurrence -> 1 of 5 citations, repeat_rate 0.2."""
        self.assertEqual(self.health_main["streams"]["news"]["repeats"], 1)
        self.assertAlmostEqual(self.health_main["streams"]["news"]["repeat_rate"], 0.2, places=4)

    def test_repeat_same_id_lookback_reaches_outside_window(self):
        """Story E's ONLY in-window occurrence (2026-07-01-science) is still
        flagged a repeat, because its genesis (2026-06-24-science, outside
        the --week window) falls within the 14-day lookback. This is the
        contract's "from the ledger" repeat proxy explicitly NOT being
        bounded by the --week window's start edge."""
        self.assertEqual(self.health_main["streams"]["science"]["repeats"], 1)
        self.assertAlmostEqual(self.health_main["streams"]["science"]["repeat_rate"], 1.0, places=4)

    def test_week_param_narrows_window_and_changes_editions(self):
        """Re-running with --week 2026-07-01 (window [2026-06-25,2026-07-01])
        against the identical ledger drops both later news editions."""
        self.assertEqual(
            self.health_narrow["streams"]["news"]["editions"],
            ["2026-06-30-news"],
        )
        self.assertEqual(self.health_narrow["streams"]["news"]["citations"], 2)
        self.assertEqual(self.health_narrow["streams"]["news"]["anchors"], 2)

    def test_week_param_repeat_flag_disappears_when_earlier_occurrence_drops_out_of_ledger_reach(self):
        """Under the narrower window, story A's ONLY surviving in-window
        occurrence (2026-06-30-news) is itself the first-ever occurrence --
        there is no earlier edition at all -- so it must NOT be flagged a
        repeat here, unlike in the wider (main) window where its 07-02
        occurrence is a repeat. This proves repeats are computed per
        occurrence, not memorized/cached across --week invocations."""
        self.assertEqual(self.health_narrow["streams"]["news"]["repeats"], 0)
        self.assertAlmostEqual(self.health_narrow["streams"]["news"]["repeat_rate"], 0.0, places=4)

    def test_week_param_does_not_affect_the_14d_lookback_itself(self):
        """Science's repeat flag on 2026-07-01-science survives the narrower
        --week 2026-07-01 window too (window start 2026-06-25 is itself
        AFTER the 2026-06-24 genesis, yet the 14-day lookback still reaches
        it) -- confirms the lookback ignores the window's start bound, not
        just that it happens to be satisfied by coincidence in the main run."""
        self.assertEqual(self.health_narrow["streams"]["science"]["repeats"], 1)

    # --- feedback tally ---------------------------------------------------

    def test_feedback_by_stream_raw_tally(self):
        """Contract: "feedback tally (from ledger feedback events: up/down/
        retractions per stream)". news carries one down-vote on story A
        (2026-07-02); science carries a retraction chain on story E: vote=1
        at 16:00 then vote=0 at 18:00, both on 2026-07-01 -- both events
        count (up=1 AND retractions=1), since this is a raw mechanical
        tally, not the store's last-write-wins per-story fold."""
        self.assertEqual(
            self.health_main["feedback"]["by_stream"],
            {
                "news": {"up": 0, "down": 1, "retractions": 0},
                "science": {"up": 1, "down": 0, "retractions": 1},
            },
        )

    def test_feedback_ledger_events_respect_week_window(self):
        """The 2026-06-20 vote (on a pre-window "OLD" story, brief
        2026-06-20-news) must not leak into the main window's news tally --
        it stays 0 up / 1 down (the down vote is the in-window 07-02 event
        on story A), not 1 up."""
        self.assertEqual(self.health_main["feedback"]["by_stream"]["news"]["up"], 0)

    def test_feedback_window_changes_by_stream_membership(self):
        """Under --week 2026-07-01, story A's down-vote (2026-07-02, now
        OUTSIDE the narrower window) disappears entirely -- "news" must be
        absent from by_stream (sparse dict), while science's retraction
        chain (2026-07-01, still in-window) survives unchanged."""
        self.assertNotIn("news", self.health_narrow["feedback"]["by_stream"])
        self.assertEqual(
            self.health_narrow["feedback"]["by_stream"]["science"],
            {"up": 1, "down": 0, "retractions": 1},
        )

    def test_unconsumed_total_is_unfiltered_by_week(self):
        """Contract: "unconsumed count straight from feedback/*.jsonl" -- no
        --week filtering. The fixture's feedback/2026-07.jsonl has 2
        consumed:false records, one with a 2026-07-03 ts (inside the main
        window) and one with a 2026-06-10 ts (well outside it); both count
        in BOTH runs, proving the field really is unfiltered rather than
        coincidentally matching one window."""
        self.assertEqual(self.health_main["feedback"]["unconsumed_total"], 2)
        self.assertEqual(self.health_narrow["feedback"]["unconsumed_total"], 2)

    def test_notify_count_present_and_windowed(self):
        """One ev:"notify" event exists (2026-07-05, on story D) -- counted
        in the main window (ends 07-06) but not the narrower one (ends
        07-01, before the notify event's ts)."""
        self.assertEqual(self.health_main["feedback"]["notify_count"], 1)
        self.assertEqual(self.health_narrow["feedback"]["notify_count"], 0)

    # --- sources passthrough --------------------------------------------

    def test_sources_passthrough_verbatim(self):
        """Contract: "discovery/footer compliance passthrough from
        source-health.json". metrics.py must copy _data/source-health.json's
        parsed content into health.json["sources"] verbatim (deep-equal)."""
        with open(os.path.join(self.root, "_data", "source-health.json")) as fh:
            expected = json.load(fh)
        self.assertEqual(self.health_main["sources"], expected)

    # --- evaluator continuity -------------------------------------------

    def test_continuity_finds_prior_evaluator_post(self):
        """Contract: "evaluator continuity (previous evaluator post exists
        in _posts/)". The fixture ships _posts/2026-06-28-evaluator.md,
        dated before the window; continuity must report it found, by its
        POSIX-relative path. `off_main` (the computed self-delivery guard,
        2026-07-18) degrades to available:false in a non-git fixture root."""
        self.assertEqual(
            self.health_main["continuity"],
            {
                "previous_evaluator_found": True,
                "previous_evaluator_path": "_posts/2026-06-28-evaluator.md",
                "off_main": {"available": False},
            },
        )

    # --- "prints it" + determinism ---------------------------------------

    def test_prints_health_json_to_stdout(self):
        """Contract: "writes _data/health.json + prints it" -- stdout, once
        stripped and parsed as JSON, must deep-equal the written file."""
        printed = json.loads(self.proc_main.stdout.strip())
        self.assertEqual(printed, self.health_main)


class MetricsThreadIdRepeatTest(unittest.TestCase):
    """Isolated fixture proving the repeat proxy also matches on `thread_id`
    when the URL/id itself differs across occurrences (contract: "stories
    whose norm_url OR thread_id appeared in an earlier edition"), distinct
    from the same-id repeat covered by the main fixture."""

    @classmethod
    def setUpClass(cls):
        assert os.path.exists(METRICS_PATH), (
            "tools/evaluator/metrics.py does not exist yet -- RED phase."
        )
        cls.root = _mktemp_copy("thread_repeat")
        cls.proc, cls.health = _run_and_load(cls.root, ["--week", "2026-07-06"])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def test_clean_run(self):
        _assert_clean_run(self, self.proc, self.health, self.root)

    def test_genesis_edition_excluded_by_window(self):
        """G1's genesis edition (2026-06-29-news) predates the window
        (starts 2026-06-30) and must not appear in `editions`."""
        self.assertEqual(self.health["streams"]["news"]["editions"], ["2026-07-01-news"])
        self.assertEqual(self.health["streams"]["news"]["citations"], 1)
        self.assertEqual(self.health["streams"]["news"]["anchors"], 1)

    def test_followup_flagged_repeat_via_thread_id_not_url(self):
        """G2 (2026-07-01-news) has a DIFFERENT url/id than G1 -- norm_url
        matching alone would miss it -- but its story record's thread_id
        equals G1's id (set at genesis, per SPIKE §3.1 "thread_id ...
        genesis-minted"), and G1 published an earlier edition
        (2026-06-29-news) within 14 days. Must be flagged a repeat via the
        thread_id branch of the proxy."""
        self.assertEqual(self.health["streams"]["news"]["repeats"], 1)
        self.assertAlmostEqual(self.health["streams"]["news"]["repeat_rate"], 1.0, places=4)


class MetricsGracefulDegradationTest(unittest.TestCase):
    """Two fixtures exercising the SPIKE §4 failure-semantics contract ("a
    tool crash degrades ... never abort"): metrics.py must still exit 0 and
    write a well-formed health.json when source-health.json/_posts/feedback
    are partially or entirely absent."""

    @classmethod
    def setUpClass(cls):
        assert os.path.exists(METRICS_PATH), (
            "tools/evaluator/metrics.py does not exist yet -- RED phase."
        )
        cls.no_continuity_root = _mktemp_copy("no_continuity")
        cls.proc_nc, cls.health_nc = _run_and_load(cls.no_continuity_root, ["--week", "2026-07-06"])

        cls.empty_root = tempfile.mkdtemp(prefix="metrics-test-empty-")
        cls.proc_empty, cls.health_empty = _run_and_load(cls.empty_root, ["--week", "2026-07-06"])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.no_continuity_root, ignore_errors=True)
        shutil.rmtree(cls.empty_root, ignore_errors=True)

    # --- no_continuity fixture: no prior evaluator post, no source-health.json, no feedback/ dir

    def test_no_continuity_clean_exit(self):
        _assert_clean_run(self, self.proc_nc, self.health_nc, self.no_continuity_root)

    def test_no_prior_evaluator_post_reports_not_found(self):
        """No `_posts/*-evaluator.md` exists in this fixture at all."""
        self.assertEqual(
            self.health_nc["continuity"],
            {"previous_evaluator_found": False, "previous_evaluator_path": None,
             "off_main": {"available": False}},
        )

    def test_missing_source_health_json_degrades_to_marker(self):
        """No _data/source-health.json in this fixture -- metrics.py must
        not crash; "sources" gets the fixed fallback marker this file
        mandates as the schema authority."""
        self.assertEqual(
            self.health_nc["sources"],
            {"available": False, "reason": "source-health.json not found"},
        )

    def test_missing_feedback_dir_yields_zero_unconsumed(self):
        """No feedback/ directory at all in this fixture -- must not crash,
        unconsumed_total is simply 0."""
        self.assertEqual(self.health_nc["feedback"]["unconsumed_total"], 0)

    # --- fully empty root: no index/, no _posts/, no feedback/, no _data/

    def test_empty_root_clean_exit(self):
        _assert_clean_run(self, self.proc_empty, self.health_empty, self.empty_root)

    def test_empty_root_streams_and_feedback_are_empty(self):
        """No ledger at all -- streams is the empty dict (sparse, not
        zero-filled with a fixed stream list), and every feedback counter
        is zero / empty."""
        self.assertEqual(self.health_empty["streams"], {})
        self.assertEqual(
            self.health_empty["feedback"],
            {"unconsumed_total": 0, "notify_count": 0, "by_stream": {}},
        )

    def test_empty_root_week_window_still_computed(self):
        """`week` reflects the --week argument regardless of root contents."""
        self.assertEqual(self.health_empty["week"], {"start": "2026-06-30", "end": "2026-07-06"})


class MetricsBadTimestampDegradationTest(unittest.TestCase):
    """FINDING 2: a publish event carrying an empty/garbage ts must not abort the whole
    metrics run -- _parse_dt's strptime call is the crash site (SPIKE §4 failure-semantics:
    'a tool crash degrades ... never abort'). The fixture's bad-ts occurrence is treated as
    non-repeat/skipped; the well-formed occurrence alongside it must still be counted."""

    def setUp(self):
        self.root = _mktemp_copy("bad_ts")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_publish_event_with_empty_ts_does_not_crash_metrics(self):
        """The bad-ts occurrence can't be dated at all, so build_streams's window check
        (`window_start <= _date_of(ts) <= window_end`) correctly excludes it -- an empty ts
        sorts before any real date -- rather than crashing the run. The well-formed
        occurrence alongside it must still be counted."""
        proc, health = _run_and_load(self.root, ["--week", "2026-07-06"])
        _assert_clean_run(self, proc, health, self.root)
        self.assertEqual(health["streams"]["news"]["citations"], 1)
        self.assertEqual(health["streams"]["news"]["anchors"], 1)

    def test_publish_event_with_empty_ts_is_not_flagged_a_repeat(self):
        proc, health = _run_and_load(self.root, ["--week", "2026-07-06"])
        _assert_clean_run(self, proc, health, self.root)
        # Neither occurrence has an earlier same-thread ledger entry, and the bad-ts one is
        # unparseable, so both must degrade to non-repeat rather than raising.
        self.assertEqual(health["streams"]["news"]["repeats"], 0)
        self.assertAlmostEqual(health["streams"]["news"]["repeat_rate"], 0.0, places=4)


class MetricsDeterminismTest(unittest.TestCase):
    """Two independent runs against the same untouched fixture root must
    produce byte-identical output (test-infrastructure requirement +
    contract: "determinism (two runs byte-identical output)")."""

    def setUp(self):
        self.root = _mktemp_copy("repo_skeleton")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_two_runs_produce_byte_identical_health_json_and_stdout(self):
        proc1 = _run_metrics(self.root, ["--week", "2026-07-06"])
        self.assertEqual(proc1.returncode, 0, proc1.stderr)
        with open(_health_path(self.root), "rb") as fh:
            bytes1 = fh.read()

        proc2 = _run_metrics(self.root, ["--week", "2026-07-06"])
        self.assertEqual(proc2.returncode, 0, proc2.stderr)
        with open(_health_path(self.root), "rb") as fh:
            bytes2 = fh.read()

        self.assertEqual(bytes1, bytes2, "health.json differed across two identical runs")
        self.assertEqual(proc1.stdout, proc2.stdout, "stdout differed across two identical runs")


class MetricsDefaultWeekSmokeTest(unittest.TestCase):
    """--week is optional (contract: "default today"); omitting it must not
    crash and must still yield a structurally valid document. Deliberately
    does not assert specific dates (today is not fixed at test-authoring
    time), only structural validity -- avoids a flaky, time-bomb test."""

    def setUp(self):
        self.root = _mktemp_copy("no_continuity")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_omitted_week_defaults_without_crashing(self):
        proc, health = _run_and_load(self.root)
        _assert_clean_run(self, proc, health, self.root)
        self.assertEqual(set(health.keys()),
                         {"week", "streams", "feedback", "sources", "continuity", "briefs"})
        self.assertEqual(set(health["week"].keys()), {"start", "end"})


if __name__ == "__main__":
    unittest.main()
