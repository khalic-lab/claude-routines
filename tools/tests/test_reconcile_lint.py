#!/usr/bin/env python3
"""RED-phase spec tests for tools/store/reconcile.py (not yet implemented) -- CHANGE B,
"a report-only reconciliation lint" that catches exactly the 2026-07-07 Cuba defect class:
a story id present in a `publish` ledger event for an edition but ABSENT from that
edition's current index/stories/{edition}.jsonl.

CLI contract pinned by this file:
  python3 tools/store/reconcile.py [--root PATH] [--days N]   (root default '.', days default 14)

Behavior pinned by this file:
  - Scans index/ledger/*.jsonl for ev=="publish" events whose EDITION DATE (the
    "YYYY-MM-DD" prefix of the "edition" field, e.g. "2026-07-07-news" -> "2026-07-07")
    falls within the last --days days of wall-clock "now". Publish events outside that
    window are ignored entirely (never printed, never counted).
  - For each in-window publish event, resolve index/stories/{edition}.jsonl.
      * File missing entirely -> ONE "edition file missing" finding for that edition,
        no matter how many publish events reference it.
      * File present -> the publish sid "matches" iff ANY record in the file has
        story_id(norm_url(record["url"])) == that sid (imported from tools/store/store.py,
        never reimplemented) -- matching is scoped to THAT edition file only (a sid
        correctly reconciled under a DIFFERENT edition does not excuse it here, which is
        the exact shape of the Cuba defect).
      * A non-matching sid is FLAGGED -- unless a LATER ledger event (ts strictly after the
        publish event's ts) of kind "status" for the same sid has a status value starting
        with "merged-into:", in which case it is reported as 'resolved-by-merge'
        informationally and is NOT counted as flagged.
  - Output: one line per finding, greppable, prefixed "RECONCILE:". A flagged finding's
    line contains the literal substring "flagged"; a resolved finding's line contains the
    literal substring "resolved-by-merge" (per the contract's own quoted vocabulary); an
    edition-missing finding's line contains the literal phrase "edition file missing".
    Every finding line carries the sid (if any) and the edition.
  - A final summary line, exactly:
        reconcile: X flagged, Y resolved-by-merge, Z editions checked
  - Report-only: ALWAYS exits 0, even when findings are flagged (mirrors
    tools/sources/lint.py without --arm).
  - Corrupt/blank ledger lines are skipped silently, and a record lacking a usable "url"
    in an edition file must not crash matching for the rest of that file (ledger-tolerance
    convention: a broken line never costs an edition).
  - No network, stdlib only. Missing index/ dirs entirely -> exit 0, "nothing to check".

Real-data check (mandated by the task): against the CURRENT repo root, st-51f44833a0eb has
a publish event for 2026-07-07-news (absent from index/stories/2026-07-07-news.jsonl) AND a
status "merged-into:st-df6bde5fe934" event appended 2026-07-10 -- so under the default
--days 14 window (today is 2026-07-10) it must appear as resolved-by-merge, NOT flagged.

Run: cd /Users/rflnogueira/code/claude-routines && python3 -m unittest tools.tests.test_reconcile_lint -v
"""
import datetime as dt
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
STORE_PATH = os.path.join(REPO_ROOT, "tools", "store", "store.py")
RECONCILE_PATH = os.path.join(REPO_ROOT, "tools", "store", "reconcile.py")

SUMMARY_RE = re.compile(
    r"reconcile:\s*(\d+)\s*flagged,\s*(\d+)\s*resolved-by-merge,\s*(\d+)\s*editions checked"
)


def _load_store():
    spec = importlib.util.spec_from_file_location("store_for_reconcile_test", STORE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


STORE = _load_store()


# --------------------------------------------------------------------------- #
# date helpers -- everything is relative to wall-clock "now" so the fixtures stay
# valid no matter what day this suite actually runs on (reconcile.py itself has no
# --now injection point, matching store.py's own _load_events()).
# --------------------------------------------------------------------------- #
def _date_days_ago(n):
    return (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=n)).strftime("%Y-%m-%d")


def _ts_days_ago(n, hour=9):
    d = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=n)).replace(
        hour=hour, minute=0, second=0, microsecond=0
    )
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def _ledger_day_for_ts(ts):
    return ts[:10]


# --------------------------------------------------------------------------- #
# fixture builders
# --------------------------------------------------------------------------- #
def _new_root():
    root = tempfile.mkdtemp(prefix="reconcile-test-")
    return root


def _append_ledger(root, day, events):
    path = os.path.join(root, "index", "ledger", day + ".jsonl")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")


def _write_stories_file(root, edition, records):
    path = os.path.join(root, "index", "stories", edition + ".jsonl")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _story_record(url, **overrides):
    rec = {
        "id": "legacy-placeholder-id",
        "date": "2026-01-01",
        "stream": "news",
        "headline": "H",
        "summary": "S",
        "url": url,
        "source_domain": "example.com",
        "tier": "T2",
        "tags": [],
        "topics": [],
        "importance": 2,
        "display_body": "B",
        "why": "",
    }
    rec.update(overrides)
    return rec


def _publish_event(sid, ts, edition, actor="news"):
    return {
        "ev": "publish", "ts": ts, "actor": actor, "id": sid, "edition": edition,
        "fields": {"display_body": "B", "why": "W", "importance": 2, "status": "settled"},
    }


def _status_event(sid, ts, status, actor="rafael-apply-pass"):
    return {"ev": "status", "ts": ts, "actor": actor, "id": sid, "status": status}


def _run_reconcile(root, extra_args=None, timeout=30):
    assert os.path.exists(RECONCILE_PATH), (
        "tools/store/reconcile.py does not exist yet at %s -- RED phase, not implemented."
        % RECONCILE_PATH
    )
    args = [sys.executable, RECONCILE_PATH, "--root", root] + (extra_args or [])
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)


def _summary(stdout):
    m = SUMMARY_RE.search(stdout)
    assert m is not None, "no summary line found in stdout:\n%s" % stdout
    return tuple(int(x) for x in m.groups())


def _lines_with(stdout, needle):
    return [ln for ln in stdout.splitlines() if needle in ln]


class ReconcileTestCase(unittest.TestCase):
    def setUp(self):
        self.root = _new_root()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)


# --------------------------------------------------------------------------- #
# missing / empty root: "tolerate missing dirs (exit 0, 'nothing to check')"
# --------------------------------------------------------------------------- #
class ReconcileMissingRootTests(ReconcileTestCase):
    def test_no_index_dir_at_all_exits_zero_with_nothing_to_check(self):
        proc = _run_reconcile(self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("nothing to check", proc.stdout.lower())

    def test_empty_ledger_dir_with_no_publish_events_exits_zero(self):
        os.makedirs(os.path.join(self.root, "index", "ledger"), exist_ok=True)
        proc = _run_reconcile(self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)


# --------------------------------------------------------------------------- #
# core defect: sid published to an edition, absent from that edition's file
# --------------------------------------------------------------------------- #
class ReconcileFlaggedFindingsTests(ReconcileTestCase):
    def test_missing_sid_is_flagged_and_summary_counts_it(self):
        url = "https://news.example.com/alpha/flagged-story"
        sid = STORE.story_id(url)
        ts = _ts_days_ago(5)
        edition = "%s-news" % _date_days_ago(5)
        _append_ledger(self.root, _ledger_day_for_ts(ts), [_publish_event(sid, ts, edition)])
        # the edition file exists but only carries an UNRELATED record
        _write_stories_file(self.root, edition, [
            _story_record("https://news.example.com/unrelated-story")
        ])

        proc = _run_reconcile(self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        hit = _lines_with(proc.stdout, sid)
        self.assertTrue(hit, "expected a RECONCILE line mentioning %s:\n%s" % (sid, proc.stdout))
        self.assertTrue(any("flagged" in ln.lower() for ln in hit), proc.stdout)
        self.assertTrue(any(edition in ln for ln in hit), proc.stdout)
        self.assertTrue(all(ln.startswith("RECONCILE:") for ln in hit), proc.stdout)
        flagged, resolved, editions = _summary(proc.stdout)
        self.assertEqual(flagged, 1)
        self.assertEqual(resolved, 0)
        self.assertGreaterEqual(editions, 1)

    def test_two_missing_sids_in_same_edition_each_get_their_own_line(self):
        edition = "%s-news" % _date_days_ago(4)
        ts = _ts_days_ago(4)
        url_a = "https://news.example.com/beta/missing-a"
        url_b = "https://news.example.com/beta/missing-b"
        sid_a, sid_b = STORE.story_id(url_a), STORE.story_id(url_b)
        _append_ledger(self.root, _ledger_day_for_ts(ts), [
            _publish_event(sid_a, ts, edition),
            _publish_event(sid_b, ts, edition),
        ])
        _write_stories_file(self.root, edition, [])

        proc = _run_reconcile(self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(_lines_with(proc.stdout, sid_a))
        self.assertTrue(_lines_with(proc.stdout, sid_b))
        flagged, _, _ = _summary(proc.stdout)
        self.assertEqual(flagged, 2)

    def test_match_is_scoped_to_its_own_edition_not_global(self):
        """The exact shape of the Cuba defect: a sid correctly present under a DIFFERENT
        edition's file must not excuse its absence from the edition it was actually
        published to."""
        url = "https://news.example.com/gamma/cross-edition"
        sid = STORE.story_id(url)
        ts = _ts_days_ago(3)
        published_edition = "%s-news" % _date_days_ago(3)
        other_edition = "%s-ai-ml" % _date_days_ago(3)
        _append_ledger(self.root, _ledger_day_for_ts(ts), [_publish_event(sid, ts, published_edition)])
        _write_stories_file(self.root, published_edition, [])
        _write_stories_file(self.root, other_edition, [_story_record(url)])

        proc = _run_reconcile(self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        hit = _lines_with(proc.stdout, sid)
        self.assertTrue(hit)
        self.assertTrue(any("flagged" in ln.lower() and published_edition in ln for ln in hit),
                         proc.stdout)


# --------------------------------------------------------------------------- #
# matching: story_id(norm_url(record url)) -- never the record's own "id" field
# --------------------------------------------------------------------------- #
class ReconcileMatchedNoFlagTests(ReconcileTestCase):
    def test_matching_sid_by_url_identity_is_not_flagged(self):
        url = "https://news.example.com/delta/matched-story"
        sid = STORE.story_id(url)
        ts = _ts_days_ago(2)
        edition = "%s-news" % _date_days_ago(2)
        _append_ledger(self.root, _ledger_day_for_ts(ts), [_publish_event(sid, ts, edition)])
        # record's own "id" field is a totally unrelated legacy string -- matching must be
        # by story_id(norm_url(url)), never by trusting this field.
        _write_stories_file(self.root, edition, [
            _story_record(url, id="2026-legacy-unrelated-id")
        ])

        proc = _run_reconcile(self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn(sid, proc.stdout, proc.stdout)
        flagged, resolved, _ = _summary(proc.stdout)
        self.assertEqual(flagged, 0)
        self.assertEqual(resolved, 0)

    def test_matching_tolerates_url_normalization_differences(self):
        """www./utm./trailing-slash noise must still resolve to the same sid via norm_url --
        the published url and the record's url are trivial variants of each other."""
        published_url = "https://news.example.com/epsilon/norm-story?utm_source=rss"
        recorded_url = "https://www.news.example.com/epsilon/norm-story/"
        self.assertEqual(STORE.story_id(published_url), STORE.story_id(recorded_url))
        sid = STORE.story_id(published_url)
        ts = _ts_days_ago(2)
        edition = "%s-news" % _date_days_ago(2)
        _append_ledger(self.root, _ledger_day_for_ts(ts), [_publish_event(sid, ts, edition)])
        _write_stories_file(self.root, edition, [_story_record(recorded_url)])

        proc = _run_reconcile(self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn(sid, proc.stdout, proc.stdout)


# --------------------------------------------------------------------------- #
# resolved-by-merge: a later status "merged-into:..." event stands down the flag
# --------------------------------------------------------------------------- #
class ReconcileResolvedByMergeTests(ReconcileTestCase):
    def test_later_merged_into_status_resolves_informationally_not_flagged(self):
        url = "https://news.example.com/zeta/resolved-story"
        sid = STORE.story_id(url)
        publish_ts = _ts_days_ago(5)
        edition = "%s-news" % _date_days_ago(5)
        _append_ledger(self.root, _ledger_day_for_ts(publish_ts),
                        [_publish_event(sid, publish_ts, edition)])
        _write_stories_file(self.root, edition, [])  # sid absent -> would be flagged

        # status event lands in a LATER, DIFFERENT day's ledger file -- mirrors the real
        # Cuba case (publish 2026-07-07, merged-into status appended 2026-07-10).
        status_ts = _ts_days_ago(1)
        _append_ledger(self.root, _ledger_day_for_ts(status_ts),
                        [_status_event(sid, status_ts, "merged-into:st-000000000000")])

        proc = _run_reconcile(self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        hit = _lines_with(proc.stdout, sid)
        self.assertTrue(hit)
        self.assertTrue(any("resolved-by-merge" in ln for ln in hit), proc.stdout)
        self.assertFalse(any("flagged" in ln.lower() for ln in hit), proc.stdout)
        flagged, resolved, _ = _summary(proc.stdout)
        self.assertEqual(flagged, 0)
        self.assertEqual(resolved, 1)

    def test_status_not_merged_into_prefixed_still_flagged(self):
        url = "https://news.example.com/eta/dropped-story"
        sid = STORE.story_id(url)
        publish_ts = _ts_days_ago(5)
        edition = "%s-news" % _date_days_ago(5)
        _append_ledger(self.root, _ledger_day_for_ts(publish_ts),
                        [_publish_event(sid, publish_ts, edition)])
        _write_stories_file(self.root, edition, [])

        status_ts = _ts_days_ago(1)
        _append_ledger(self.root, _ledger_day_for_ts(status_ts),
                        [_status_event(sid, status_ts, "dropped")])

        proc = _run_reconcile(self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        hit = _lines_with(proc.stdout, sid)
        self.assertTrue(any("flagged" in ln.lower() for ln in hit), proc.stdout)
        self.assertFalse(any("resolved-by-merge" in ln for ln in hit), proc.stdout)
        flagged, resolved, _ = _summary(proc.stdout)
        self.assertEqual(flagged, 1)
        self.assertEqual(resolved, 0)

    def test_merged_into_status_earlier_than_publish_does_not_resolve(self):
        """'A LATER ledger event' -- a merged-into status event that predates the publish
        event itself cannot be what resolved it; the sid must still be flagged."""
        url = "https://news.example.com/theta/stale-status-story"
        sid = STORE.story_id(url)
        status_ts = _ts_days_ago(10)
        publish_ts = _ts_days_ago(5)
        edition = "%s-news" % _date_days_ago(5)
        _append_ledger(self.root, _ledger_day_for_ts(status_ts),
                        [_status_event(sid, status_ts, "merged-into:st-000000000000")])
        _append_ledger(self.root, _ledger_day_for_ts(publish_ts),
                        [_publish_event(sid, publish_ts, edition)])
        _write_stories_file(self.root, edition, [])

        proc = _run_reconcile(self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        hit = _lines_with(proc.stdout, sid)
        self.assertTrue(any("flagged" in ln.lower() for ln in hit), proc.stdout)
        flagged, resolved, _ = _summary(proc.stdout)
        self.assertEqual(flagged, 1)
        self.assertEqual(resolved, 0)


# --------------------------------------------------------------------------- #
# missing edition file -- report ONCE per edition, no matter how many sids
# --------------------------------------------------------------------------- #
class ReconcileEditionMissingTests(ReconcileTestCase):
    def test_missing_edition_file_reported_exactly_once(self):
        edition = "%s-news" % _date_days_ago(6)
        ts = _ts_days_ago(6)
        url_a = "https://news.example.com/iota/phantom-a"
        url_b = "https://news.example.com/iota/phantom-b"
        sid_a, sid_b = STORE.story_id(url_a), STORE.story_id(url_b)
        _append_ledger(self.root, _ledger_day_for_ts(ts), [
            _publish_event(sid_a, ts, edition),
            _publish_event(sid_b, ts, edition),
        ])
        # deliberately no index/stories/{edition}.jsonl written at all

        proc = _run_reconcile(self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        missing_lines = [ln for ln in proc.stdout.splitlines()
                          if "edition file missing" in ln and edition in ln]
        self.assertEqual(len(missing_lines), 1,
                          "expected exactly one 'edition file missing' line for %s, got:\n%s"
                          % (edition, proc.stdout))
        self.assertTrue(missing_lines[0].startswith("RECONCILE:"), missing_lines[0])


# --------------------------------------------------------------------------- #
# --days window filtering (default 14)
# --------------------------------------------------------------------------- #
class ReconcileWindowFilterTests(ReconcileTestCase):
    def test_publish_outside_default_window_is_ignored(self):
        url = "https://news.example.com/kappa/ancient-story"
        sid = STORE.story_id(url)
        ts = _ts_days_ago(30)
        edition = "%s-news" % _date_days_ago(30)
        _append_ledger(self.root, _ledger_day_for_ts(ts), [_publish_event(sid, ts, edition)])
        # no stories file -- would be an "edition file missing" finding if it were in-window

        proc = _run_reconcile(self.root)  # default --days 14
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn(sid, proc.stdout, proc.stdout)
        self.assertNotIn(edition, proc.stdout, proc.stdout)
        flagged, resolved, editions = _summary(proc.stdout) if SUMMARY_RE.search(proc.stdout) else (0, 0, 0)
        self.assertEqual(flagged, 0)
        self.assertEqual(editions, 0)

    def test_days_override_extends_window_to_include_the_old_publish(self):
        # No stories file is written for this edition, so once the override brings this
        # publish event in-window it is an "edition file missing" finding -- per the spec's
        # own vocabulary that category is distinct from FLAGGED (which applies only when the
        # edition file EXISTS and the sid doesn't match a record in it; see
        # test_every_finding_line_prefixed_reconcile_and_summary_line_present, whose
        # missing-edition sid is likewise excluded from the flagged count). The point of this
        # test is that --days extends the window enough to surface the publish at all.
        url = "https://news.example.com/kappa/ancient-story-2"
        sid = STORE.story_id(url)
        ts = _ts_days_ago(30)
        edition = "%s-news" % _date_days_ago(30)
        _append_ledger(self.root, _ledger_day_for_ts(ts), [_publish_event(sid, ts, edition)])

        proc = _run_reconcile(self.root, extra_args=["--days", "40"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(sid, proc.stdout, proc.stdout)
        self.assertTrue(
            any("edition file missing" in ln and edition in ln for ln in proc.stdout.splitlines()),
            proc.stdout)
        flagged, resolved, editions = _summary(proc.stdout)
        self.assertEqual(flagged, 0)
        self.assertEqual(resolved, 0)
        self.assertEqual(editions, 1)


# --------------------------------------------------------------------------- #
# tolerance: corrupt/blank ledger lines and url-less story records never crash the run
# --------------------------------------------------------------------------- #
class ReconcileToleranceTests(ReconcileTestCase):
    def test_corrupt_and_blank_ledger_lines_are_skipped_silently(self):
        url = "https://news.example.com/lambda/tolerant-story"
        sid = STORE.story_id(url)
        ts = _ts_days_ago(2)
        edition = "%s-news" % _date_days_ago(2)
        day = _ledger_day_for_ts(ts)
        path = os.path.join(self.root, "index", "ledger", day + ".jsonl")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n")  # blank line
            f.write("{this is not valid json\n")  # corrupt line
            f.write(json.dumps(_publish_event(sid, ts, edition)) + "\n")  # valid, matching
        _write_stories_file(self.root, edition, [_story_record(url)])

        proc = _run_reconcile(self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("Traceback", proc.stderr, proc.stderr)
        self.assertNotIn(sid, proc.stdout, proc.stdout)  # matched -> no finding
        flagged, resolved, _ = _summary(proc.stdout)
        self.assertEqual(flagged, 0)
        self.assertEqual(resolved, 0)

    def test_urlless_story_record_in_edition_file_does_not_crash_matching(self):
        url = "https://news.example.com/mu/urlless-sibling"
        sid = STORE.story_id(url)
        ts = _ts_days_ago(2)
        edition = "%s-news" % _date_days_ago(2)
        _append_ledger(self.root, _ledger_day_for_ts(ts), [_publish_event(sid, ts, edition)])
        urlless = _story_record(None)
        del urlless["url"]
        _write_stories_file(self.root, edition, [urlless, _story_record(url)])

        proc = _run_reconcile(self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("Traceback", proc.stderr, proc.stderr)
        self.assertNotIn(sid, proc.stdout, proc.stdout)  # still matched via the OTHER record


# --------------------------------------------------------------------------- #
# output format + always-exit-0 contract
# --------------------------------------------------------------------------- #
class ReconcileOutputFormatTests(ReconcileTestCase):
    def test_every_finding_line_prefixed_reconcile_and_summary_line_present(self):
        ts = _ts_days_ago(3)
        day = _ledger_day_for_ts(ts)

        flagged_edition = "%s-news" % _date_days_ago(3)
        url_flag = "https://news.example.com/nu/fmt-flagged"
        sid_flag = STORE.story_id(url_flag)

        resolved_edition = "%s-ai-ml" % _date_days_ago(3)
        url_resolved = "https://news.example.com/nu/fmt-resolved"
        sid_resolved = STORE.story_id(url_resolved)

        missing_edition = "%s-weekend" % _date_days_ago(3)
        url_missing_ed = "https://news.example.com/nu/fmt-missing-edition"
        sid_missing_ed = STORE.story_id(url_missing_ed)

        _append_ledger(self.root, day, [
            _publish_event(sid_flag, ts, flagged_edition),
            _publish_event(sid_resolved, ts, resolved_edition),
            _publish_event(sid_missing_ed, ts, missing_edition),
        ])
        status_ts = _ts_days_ago(1)
        _append_ledger(self.root, _ledger_day_for_ts(status_ts), [
            _status_event(sid_resolved, status_ts, "merged-into:st-000000000000"),
        ])
        _write_stories_file(self.root, flagged_edition, [])
        _write_stories_file(self.root, resolved_edition, [])
        # missing_edition: no file written at all

        proc = _run_reconcile(self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        finding_lines = [ln for ln in proc.stdout.splitlines() if ln.strip()
                          and not ln.lower().startswith("reconcile:")
                          and SUMMARY_RE.search(ln) is None]
        # every non-summary, non-blank output line must be a RECONCILE: finding line
        for ln in proc.stdout.splitlines():
            if not ln.strip():
                continue
            if SUMMARY_RE.search(ln):
                continue
            self.assertTrue(ln.startswith("RECONCILE:"), "unprefixed output line: %r" % ln)

        flagged, resolved, editions = _summary(proc.stdout)
        self.assertEqual(flagged, 1)
        self.assertEqual(resolved, 1)
        self.assertEqual(editions, 3)

    def test_exit_code_is_always_zero_even_with_multiple_flags(self):
        ts = _ts_days_ago(2)
        edition = "%s-news" % _date_days_ago(2)
        sids = [STORE.story_id("https://news.example.com/xi/many-%d" % i) for i in range(5)]
        _append_ledger(self.root, _ledger_day_for_ts(ts),
                        [_publish_event(sid, ts, edition) for sid in sids])
        _write_stories_file(self.root, edition, [])  # none of them match

        proc = _run_reconcile(self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        flagged, _, _ = _summary(proc.stdout)
        self.assertEqual(flagged, 5)


# --------------------------------------------------------------------------- #
# real-data check (mandated): run against the actual repo, root='.'
# --------------------------------------------------------------------------- #
class ReconcileRealRepoTests(unittest.TestCase):
    def test_runs_clean_against_the_real_repo(self):
        proc = _run_reconcile(REPO_ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_real_cuba_story_is_resolved_by_merge_not_flagged(self):
        proc = _run_reconcile(REPO_ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        sid = "st-51f44833a0eb"
        hit = _lines_with(proc.stdout, sid)
        self.assertTrue(hit, "expected a RECONCILE line for %s in real-repo output:\n%s"
                         % (sid, proc.stdout))
        self.assertTrue(any("resolved-by-merge" in ln for ln in hit), proc.stdout)
        self.assertFalse(any(("flagged" in ln.lower() and "resolved-by-merge" not in ln)
                              for ln in hit), proc.stdout)


if __name__ == "__main__":
    unittest.main()
