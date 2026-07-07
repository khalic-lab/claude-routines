#!/usr/bin/env python3
"""RED-phase spec tests — story store core (SPIKE-2026-07-07-continuous-news.md §3.1,
§4 "Ledger integrity", §5 Step 1). Implementers: write `tools/store/store.py` to satisfy
these tests, not the other way around.

Covers: story-id construction + norm_url equivalence/parity, append_event shape
validation, ledger day-partitioning, materialize() --days windowing + by_legacy/by_url
maps, and all five materializer invariants (a)-(e) from the binding contract, including a
real two-branch git union-merge test run entirely inside a tempdir.

Run: cd /Users/rflnogueira/code/claude-routines && python3 -m unittest discover -s tools/tests -v
"""
import datetime as dt
import hashlib
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
FIXTURES_DIR = os.path.join(TESTS_DIR, "fixtures", "store")
STORE_PATH = os.path.join(REPO_ROOT, "tools", "store", "store.py")
BUILD_FEED_PATH = os.path.join(REPO_ROOT, "tools", "build_stories_feed.py")


# --------------------------------------------------------------------------- #
# infrastructure — no network, no real-repo writes
# --------------------------------------------------------------------------- #
def _load_module(path, name):
    """importlib load by fixed path. A missing (not-yet-implemented) file must fail THIS
    test clearly, not crash discovery of the rest of the suite — hence a plain
    AssertionError, raised from setUpClass/setUp where unittest catches and reports it
    per-test(-class) without aborting other test modules."""
    if not os.path.exists(path):
        raise AssertionError(f"expected implementation file is missing: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _new_root():
    root = tempfile.mkdtemp(prefix="store-test-")
    os.makedirs(os.path.join(root, "index", "ledger"), exist_ok=True)
    return root


def _write_ledger_day(root, day, events):
    """Write raw events (already-JSON-serializable dicts) directly into
    index/ledger/{day}.jsonl, bypassing append_event — used when a test needs to control
    physical line order / historical dates that append_event's real-clock partitioning
    would not allow."""
    path = os.path.join(root, "index", "ledger", f"{day}.jsonl")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        for ev in events:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return path


def _read_ledger_events(root):
    out = []
    ledger_dir = os.path.join(root, "index", "ledger")
    if not os.path.isdir(ledger_dir):
        return out
    for name in sorted(os.listdir(ledger_dir)):
        if not name.endswith(".jsonl"):
            continue
        with open(os.path.join(ledger_dir, name)) as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
    return out


def _today_utc():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


def _days_ago(n):
    d = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=n)
    return d.strftime("%Y-%m-%d")


def _run_cli(args, input_text=None, timeout=30):
    return subprocess.run(
        [sys.executable, STORE_PATH] + args,
        input=input_text, capture_output=True, text=True, timeout=timeout,
    )


# --------------------------------------------------------------------------- #
# story_id / norm_url
# --------------------------------------------------------------------------- #
class NormUrlParityTests(unittest.TestCase):
    """contract: 'norm_url = EXACTLY the semantics of the existing norm_url() in
    tools/build_stories_feed.py'; canonical impl lives in tools/store/store.py."""

    @classmethod
    def setUpClass(cls):
        cls.store = _load_module(STORE_PATH, f"store_normurl_{id(cls)}")
        cls.legacy = _load_module(BUILD_FEED_PATH, f"bsf_normurl_{id(cls)}")

    def test_parity_on_a_dozen_real_shaped_urls(self):
        """store.norm_url must agree with the CURRENT build_stories_feed.norm_url on
        real-shaped URLs pulled from the live index/stories/*.jsonl corpus (SPIKE §3.1
        identity clause)."""
        real_urls = [
            "https://www.nature.com/articles/s41586-026-10815-x",
            "https://arxiv.org/abs/2606.32006",
            "https://www.quantamagazine.org/for-the-first-time-a-cell-built-from-scratch"
            "-grows-and-divides-20260701/",
            "https://www.letemps.ch/articles/avs-sous-forte-pression-et-ai-au-bord-du"
            "-gouffre-les-nouvelles-projections-financieres-inquietent",
            "https://www.srf.ch/news/schweiz/keine-zoelle-mehr-auf-fisch-efta-und-vietnam"
            "-unterzeichnen-freihandelsabkommen",
            "https://www.cnbc.com/2026/07/02/russia-launches-missile-drone-strikes-ukraine"
            "-kyiv.html",
            "https://www.aljazeera.com/news/2026/7/2/explosion-heard-in-syrias-capital"
            "-damascus-state-media",
            "https://www.washingtonpost.com/world/2026/07/02/uk-forced-adoption-apology"
            "-keir-starmer/e077fb7e-75f6-11f1-b665-5f8be87f3787_story.html",
            "https://www.rts.ch/info/suisse/2026/article/la-course-d-ecole-du-conseil"
            "-federal-s-acheve-dans-le-canton-de-vaud-29287048.html",
            "https://www.srf.ch/news/schweiz/armee-aeussert-spionageverdacht-hier-flogen"
            "-die-mysterioesen-drohnen-ueber-militaeranlagen",
            "https://www.tagesanzeiger.ch/spionage-drohnen-ueber-schweizer-armeekaserne"
            "-fuer-cyberabwehr-383445126730",
            "https://www.themoscowtimes.com/2026/07/05/trump-offered-in-conversation-with"
            "-putin-to-help-with-ukraine-settlement-kremlin-aide-a93166",
        ]
        self.assertGreaterEqual(len(real_urls), 12)
        for u in real_urls:
            with self.subTest(url=u):
                self.assertEqual(self.store.norm_url(u), self.legacy.norm_url(u))

    def test_parity_on_none_and_empty(self):
        """Edge inputs must degrade identically in both implementations."""
        for u in (None, ""):
            with self.subTest(url=u):
                self.assertEqual(self.store.norm_url(u), self.legacy.norm_url(u))


class NormUrlEquivalenceClassTests(unittest.TestCase):
    """contract: scheme/www/fragment/utm/trailing-slash variants of one URL -> same id;
    genuinely different URLs -> different ids (SPIKE §3.1, 'a pure function of the
    canonical URL')."""

    @classmethod
    def setUpClass(cls):
        cls.store = _load_module(STORE_PATH, f"store_equiv_{id(cls)}")

    def test_scheme_www_fragment_utm_trailing_slash_variants_share_one_id(self):
        variants = [
            "https://example.com/section/story-name",
            "http://example.com/section/story-name",
            "https://www.example.com/section/story-name",
            "https://WWW.EXAMPLE.COM/section/story-name",
            "https://example.com/section/story-name/",
            "https://example.com/section/story-name#fragment-here",
            "https://example.com/section/story-name?utm_source=newsletter&utm_medium=email",
            "https://example.com/section/story-name?utm_campaign=x&ref=abc&fbclid=yyy",
            "https://example.com/section/story-name/?utm_source=x#top",
        ]
        ids = {self.store.story_id(u) for u in variants}
        self.assertEqual(len(ids), 1, f"expected one shared id, got {ids} for {variants}")

    def test_a_different_path_yields_a_different_id(self):
        base = self.store.story_id("https://example.com/section/story-name")
        other = self.store.story_id("https://example.com/section/another-story-name")
        self.assertNotEqual(base, other)

    def test_a_non_utm_query_param_is_NOT_stripped_and_changes_the_id(self):
        """norm_url only strips utm_*/ref=/fbclid — a genuine query param like ?page=2
        must survive and therefore change the id (precision, not over-stripping)."""
        bare = self.store.story_id("https://example.com/section/story-name")
        paged = self.store.story_id("https://example.com/section/story-name?page=2")
        self.assertNotEqual(bare, paged)

    def test_id_format(self):
        sid = self.store.story_id("https://example.com/anything")
        self.assertRegex(sid, r"^st-[0-9a-f]{12}$")

    def test_id_matches_manual_sha1_of_norm_url(self):
        """STORY ID: "st-" + sha1(norm_url(url)).hexdigest()[:12] — an independent oracle,
        not merely internal self-consistency."""
        url = "https://www.Example.com/Foo/Bar?utm_source=x#frag"
        expected = "st-" + hashlib.sha1(self.store.norm_url(url).encode("utf-8")).hexdigest()[:12]
        self.assertEqual(self.store.story_id(url), expected)


# --------------------------------------------------------------------------- #
# append_event shape validation
# --------------------------------------------------------------------------- #
class AppendEventValidationTests(unittest.TestCase):
    """contract: 'append_event(event, root=...)'; CLI 'append ... validates shape'."""

    @classmethod
    def setUpClass(cls):
        cls.store = _load_module(STORE_PATH, f"store_append_{id(cls)}")

    def setUp(self):
        self.root = _new_root()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def _seen_story(self, url="https://example.com/x"):
        return {
            "id": self.store.story_id(url), "url": url, "headline": "H", "summary": "S",
            "status": "candidate", "first_seen": "2026-07-08T06:00:00Z",
            "updated": "2026-07-08T06:00:00Z", "legacy_ids": [], "editions": [],
            "streams": ["news"], "tags": [], "topics": [],
        }

    def test_well_formed_seen_event_is_accepted_and_appended(self):
        ev = {"ev": "seen", "ts": "2026-07-08T06:00:00Z", "actor": "news",
              "story": self._seen_story()}
        self.store.append_event(ev, root=self.root)
        events = _read_ledger_events(self.root)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["ev"], "seen")
        self.assertEqual(events[0]["story"]["id"], ev["story"]["id"])

    def test_missing_ev_key_rejected(self):
        ev = {"ts": "2026-07-08T06:00:00Z", "actor": "news", "story": self._seen_story()}
        with self.assertRaises(Exception):
            self.store.append_event(ev, root=self.root)

    def test_unknown_ev_type_rejected(self):
        ev = {"ev": "bogus", "ts": "2026-07-08T06:00:00Z", "actor": "news"}
        with self.assertRaises(Exception):
            self.store.append_event(ev, root=self.root)

    def test_missing_ts_rejected(self):
        ev = {"ev": "seen", "actor": "news", "story": self._seen_story()}
        with self.assertRaises(Exception):
            self.store.append_event(ev, root=self.root)

    def test_missing_actor_rejected(self):
        ev = {"ev": "seen", "ts": "2026-07-08T06:00:00Z", "story": self._seen_story()}
        with self.assertRaises(Exception):
            self.store.append_event(ev, root=self.root)

    def test_seen_missing_story_rejected(self):
        ev = {"ev": "seen", "ts": "2026-07-08T06:00:00Z", "actor": "news"}
        with self.assertRaises(Exception):
            self.store.append_event(ev, root=self.root)

    def test_update_missing_id_rejected(self):
        ev = {"ev": "update", "ts": "2026-07-08T06:00:00Z", "actor": "news",
              "rev": 2, "fields": {"status": "developing"}}
        with self.assertRaises(Exception):
            self.store.append_event(ev, root=self.root)

    def test_update_missing_rev_rejected(self):
        ev = {"ev": "update", "ts": "2026-07-08T06:00:00Z", "actor": "news",
              "id": "st-000000000000", "fields": {"status": "developing"}}
        with self.assertRaises(Exception):
            self.store.append_event(ev, root=self.root)

    def test_update_missing_fields_rejected(self):
        ev = {"ev": "update", "ts": "2026-07-08T06:00:00Z", "actor": "news",
              "id": "st-000000000000", "rev": 2}
        with self.assertRaises(Exception):
            self.store.append_event(ev, root=self.root)

    def test_well_formed_update_event_is_accepted(self):
        ev = {"ev": "update", "ts": "2026-07-08T06:00:00Z", "actor": "news",
              "id": "st-000000000000", "rev": 2, "fields": {"status": "developing"},
              "note": "corroborated"}
        self.store.append_event(ev, root=self.root)
        self.assertEqual(len(_read_ledger_events(self.root)), 1)

    def test_publish_missing_edition_rejected(self):
        ev = {"ev": "publish", "ts": "2026-07-08T06:00:00Z", "actor": "news",
              "id": "st-000000000000",
              "fields": {"display_body": "x", "why": "y", "importance": 2, "status": "settled"}}
        with self.assertRaises(Exception):
            self.store.append_event(ev, root=self.root)

    def test_publish_missing_fields_rejected(self):
        ev = {"ev": "publish", "ts": "2026-07-08T06:00:00Z", "actor": "news",
              "id": "st-000000000000", "edition": "2026-07-08-news"}
        with self.assertRaises(Exception):
            self.store.append_event(ev, root=self.root)

    def test_well_formed_publish_event_is_accepted(self):
        ev = {"ev": "publish", "ts": "2026-07-08T06:00:00Z", "actor": "news",
              "id": "st-000000000000", "edition": "2026-07-08-news",
              "fields": {"display_body": "x", "why": "y", "importance": 2, "status": "settled"}}
        self.store.append_event(ev, root=self.root)
        self.assertEqual(len(_read_ledger_events(self.root)), 1)

    def test_status_missing_status_field_rejected(self):
        ev = {"ev": "status", "ts": "2026-07-08T06:00:00Z", "actor": "news",
              "id": "st-000000000000"}
        with self.assertRaises(Exception):
            self.store.append_event(ev, root=self.root)

    def test_well_formed_status_event_is_accepted(self):
        ev = {"ev": "status", "ts": "2026-07-08T06:00:00Z", "actor": "news",
              "id": "st-000000000000", "status": "superseded",
              "superseded_by": "st-111111111111"}
        self.store.append_event(ev, root=self.root)
        self.assertEqual(len(_read_ledger_events(self.root)), 1)

    def test_feedback_missing_fb_id_rejected(self):
        ev = {"ev": "feedback", "ts": "2026-07-08T06:00:00Z", "actor": "bridge",
              "id": "st-000000000000", "vote": 1, "reason": "", "reader": "rafael",
              "surface": "web", "brief": "2026-07-08-news", "raw_story_id": "st-000000000000"}
        with self.assertRaises(Exception):
            self.store.append_event(ev, root=self.root)

    def test_feedback_missing_vote_rejected(self):
        ev = {"ev": "feedback", "ts": "2026-07-08T06:00:00Z", "actor": "bridge",
              "id": "st-000000000000", "fb_id": "fb-1", "reason": "", "reader": "rafael",
              "surface": "web", "brief": "2026-07-08-news", "raw_story_id": "st-000000000000"}
        with self.assertRaises(Exception):
            self.store.append_event(ev, root=self.root)

    def test_well_formed_feedback_event_with_null_id_is_accepted(self):
        """contract: feedback "id":"st-..."|null — an unresolved feedback record must be
        appendable with id=None, not rejected for lacking a resolved story id."""
        ev = {"ev": "feedback", "ts": "2026-07-08T06:00:00Z", "actor": "bridge",
              "id": None, "fb_id": "fb-1", "vote": 1, "reason": "", "reader": "rafael",
              "surface": "web", "brief": "2026-07-08-news", "raw_story_id": "2026-06-19-x"}
        self.store.append_event(ev, root=self.root)
        self.assertEqual(len(_read_ledger_events(self.root)), 1)


# --------------------------------------------------------------------------- #
# ledger day-partitioning
# --------------------------------------------------------------------------- #
class LedgerPartitioningTests(unittest.TestCase):
    """contract: 'index/ledger/{YYYY-MM-DD}.jsonl (UTC ingest day)' — partitioned by the
    day the event is APPENDED, not by any date embedded in the event's own "ts"."""

    @classmethod
    def setUpClass(cls):
        cls.store = _load_module(STORE_PATH, f"store_partition_{id(cls)}")

    def setUp(self):
        self.root = _new_root()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_append_writes_into_todays_utc_ledger_file(self):
        ev = {"ev": "status", "ts": "2026-07-08T06:00:00Z", "actor": "news",
              "id": "st-000000000000", "status": "dropped"}
        self.store.append_event(ev, root=self.root)
        expected_path = os.path.join(self.root, "index", "ledger", f"{_today_utc()}.jsonl")
        self.assertTrue(os.path.exists(expected_path),
                         f"expected {expected_path} to exist; found "
                         f"{os.listdir(os.path.join(self.root, 'index', 'ledger'))}")

    def test_ingest_day_partitioning_ignores_a_backdated_event_ts(self):
        """A "ts" from years ago must still land in TODAY's ingest-day file — partitioning
        is by real append time, not the event's own historical ts."""
        ev = {"ev": "status", "ts": "2020-01-01T00:00:00Z", "actor": "backfill",
              "id": "st-000000000000", "status": "dropped"}
        self.store.append_event(ev, root=self.root)
        stale_path = os.path.join(self.root, "index", "ledger", "2020-01-01.jsonl")
        self.assertFalse(os.path.exists(stale_path))
        expected_path = os.path.join(self.root, "index", "ledger", f"{_today_utc()}.jsonl")
        self.assertTrue(os.path.exists(expected_path))


# --------------------------------------------------------------------------- #
# materialize() — API shape, --days windowing, by_legacy/by_url maps
# --------------------------------------------------------------------------- #
class MaterializeApiShapeTests(unittest.TestCase):
    """contract: materialize(days=60, root=...) -> {"stories": {...}, "by_legacy": {...},
    "by_url": {...}}."""

    @classmethod
    def setUpClass(cls):
        cls.store = _load_module(STORE_PATH, f"store_apishape_{id(cls)}")

    def setUp(self):
        self.root = _new_root()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_empty_ledger_returns_empty_maps_without_crashing(self):
        snap = self.store.materialize(root=self.root)
        self.assertEqual(set(snap.keys()), {"stories", "by_legacy", "by_url"})
        self.assertEqual(snap["stories"], {})
        self.assertEqual(snap["by_legacy"], {})
        self.assertEqual(snap["by_url"], {})

    def test_by_legacy_and_by_url_maps_point_at_the_right_story(self):
        url = "https://example.com/foo-bar"
        sid = self.store.story_id(url)
        story = {
            "id": sid, "url": url, "headline": "Foo bar happens", "summary": "S",
            "status": "candidate", "first_seen": "2026-07-08T06:00:00Z",
            "updated": "2026-07-08T06:00:00Z", "legacy_ids": ["oldid1"], "editions": [],
            "streams": ["news"], "tags": [], "topics": [],
        }
        self.store.append_event(
            {"ev": "seen", "ts": "2026-07-08T06:00:00Z", "actor": "news", "story": story},
            root=self.root)
        snap = self.store.materialize(root=self.root)
        self.assertIn(sid, snap["stories"])
        self.assertEqual(snap["by_legacy"].get("oldid1"), sid)
        self.assertEqual(snap["by_url"].get(self.store.norm_url(url)), sid)


class MaterializeDaysWindowTests(unittest.TestCase):
    """contract: materialize(days=N) folds only the last N days of ledger files (SPIKE
    §3.1: 'folds the last 60 days into a thread map')."""

    @classmethod
    def setUpClass(cls):
        cls.store = _load_module(STORE_PATH, f"store_window_{id(cls)}")

    def setUp(self):
        self.root = _new_root()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def _seen(self, tag, day):
        url = f"https://example.com/window-{tag}"
        sid = self.store.story_id(url)
        story = {
            "id": sid, "url": url, "headline": f"Window story {tag}", "summary": "S",
            "status": "settled", "first_seen": f"{day}T00:00:00Z",
            "updated": f"{day}T00:00:00Z", "legacy_ids": [], "editions": [],
            "streams": ["news"], "tags": [], "topics": [],
        }
        _write_ledger_day(self.root, day,
                           [{"ev": "seen", "ts": f"{day}T00:00:00Z", "actor": "news",
                             "story": story}])
        return sid

    def test_default_60_day_window_excludes_a_90_day_old_ledger_file(self):
        today_id = self._seen("today", _today_utc())
        recent_id = self._seen("recent", _days_ago(10))
        old_id = self._seen("old", _days_ago(90))
        snap = self.store.materialize(root=self.root)  # default days=60
        self.assertIn(today_id, snap["stories"])
        self.assertIn(recent_id, snap["stories"])
        self.assertNotIn(old_id, snap["stories"])

    def test_wider_days_window_includes_the_90_day_old_ledger_file(self):
        old_id = self._seen("old2", _days_ago(90))
        snap = self.store.materialize(days=120, root=self.root)
        self.assertIn(old_id, snap["stories"])


# --------------------------------------------------------------------------- #
# Materializer invariants (a)-(e) — SPIKE-mandated
# --------------------------------------------------------------------------- #
class InvariantASortByTsActorTests(unittest.TestCase):
    """(a) events sorted by (ts, actor) before folding — a naive file-order fold must be
    provably wrong for this test to distinguish it from a correct sort-then-fold."""

    @classmethod
    def setUpClass(cls):
        cls.store = _load_module(STORE_PATH, f"store_sorta_{id(cls)}")

    def setUp(self):
        self.root = _new_root()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def _seed(self, sid):
        story = {
            "id": sid, "url": "https://example.com/sort-target", "headline": "H",
            "summary": "S", "status": "candidate", "first_seen": "2026-07-01T00:00:00Z",
            "updated": "2026-07-01T00:00:00Z", "legacy_ids": [], "editions": [],
            "streams": ["news"], "tags": [], "topics": [],
        }
        return {"ev": "seen", "ts": "2026-07-01T00:00:00Z", "actor": "news", "story": story}

    def test_out_of_file_order_updates_are_folded_in_ts_order_not_file_order(self):
        sid = self.store.story_id("https://example.com/sort-target")
        day = _today_utc()
        # File-position 1 carries the LATER ts; file-position 2 carries the EARLIER ts —
        # the reverse of chronological order. A naive fold that trusts file order would
        # apply the earlier-ts update LAST (status="developing" would win); the correct
        # sort-by-ts fold applies the later-ts update last (status="dropped" must win).
        events = [
            self._seed(sid),
            {"ev": "update", "ts": "2026-07-02T10:00:00Z", "actor": "news",
             "id": sid, "rev": 2, "fields": {"status": "dropped"}},
            {"ev": "update", "ts": "2026-07-02T09:00:00Z", "actor": "news",
             "id": sid, "rev": 1, "fields": {"status": "developing"}},
        ]
        _write_ledger_day(self.root, day, events)
        snap = self.store.materialize(root=self.root)
        self.assertEqual(snap["stories"][sid]["status"], "dropped",
                          "the LATER-ts update must win regardless of physical line order")

    def test_same_ts_tiebreak_sorts_by_actor(self):
        """Same ts, two actors -> sort ascending by actor; the alphabetically LAST actor's
        write is folded last and therefore wins."""
        sid = self.store.story_id("https://example.com/sort-target")
        day = _today_utc()
        events = [
            self._seed(sid),
            {"ev": "update", "ts": "2026-07-02T09:00:00Z", "actor": "zzz-actor",
             "id": sid, "rev": 3, "fields": {"status": "superseded"}},
            {"ev": "update", "ts": "2026-07-02T09:00:00Z", "actor": "aaa-actor",
             "id": sid, "rev": 2, "fields": {"status": "developing"}},
        ]
        _write_ledger_day(self.root, day, events)
        snap = self.store.materialize(root=self.root)
        self.assertEqual(snap["stories"][sid]["status"], "superseded",
                          "with tied ts, actor 'zzz-actor' sorts after 'aaa-actor' and "
                          "must be folded last")


class InvariantBExactDuplicateDedupeTests(unittest.TestCase):
    """(b) exact-duplicate events deduped — seen by (ev,id), update by (ev,id,rev),
    feedback by fb_id, publish by (ev,id,edition). Proven via equivalence: N copies of a
    byte-identical event must fold to the SAME result as one copy — this is the one
    formulation that stays valid regardless of a chosen dedup KEY vs a full-equality
    definition of "duplicate"."""

    @classmethod
    def setUpClass(cls):
        cls.store = _load_module(STORE_PATH, f"store_dedupe_{id(cls)}")

    def setUp(self):
        self.root_once = _new_root()
        self.root_twice = _new_root()
        self.addCleanup(shutil.rmtree, self.root_once, ignore_errors=True)
        self.addCleanup(shutil.rmtree, self.root_twice, ignore_errors=True)

    def _materialize_both(self, event):
        day = _today_utc()
        _write_ledger_day(self.root_once, day, [event])
        _write_ledger_day(self.root_twice, day, [event, event])
        once = self.store.materialize(root=self.root_once)
        twice = self.store.materialize(root=self.root_twice)
        return once, twice

    def test_duplicate_seen_event_does_not_change_the_folded_result(self):
        sid = self.store.story_id("https://example.com/dedupe-seen")
        story = {
            "id": sid, "url": "https://example.com/dedupe-seen", "headline": "H",
            "summary": "S", "status": "candidate", "first_seen": "2026-07-01T00:00:00Z",
            "updated": "2026-07-01T00:00:00Z", "legacy_ids": ["legacy-x"],
            "editions": ["2026-07-01-news"], "streams": ["news"], "tags": [], "topics": [],
        }
        event = {"ev": "seen", "ts": "2026-07-01T00:00:00Z", "actor": "news", "story": story}
        once, twice = self._materialize_both(event)
        self.assertEqual(once["stories"][sid], twice["stories"][sid])
        self.assertEqual(once["stories"][sid]["editions"], ["2026-07-01-news"],
                          "duplicate seen must not duplicate a union'd list entry either")

    def test_duplicate_update_event_does_not_change_the_folded_result(self):
        sid = self.store.story_id("https://example.com/dedupe-update")
        genesis = {"ev": "seen", "ts": "2026-07-01T00:00:00Z", "actor": "news", "story": {
            "id": sid, "url": "https://example.com/dedupe-update", "headline": "H",
            "summary": "S", "status": "candidate", "first_seen": "2026-07-01T00:00:00Z",
            "updated": "2026-07-01T00:00:00Z", "legacy_ids": [], "editions": [],
            "streams": ["news"], "tags": [], "topics": [],
        }}
        update = {"ev": "update", "ts": "2026-07-02T00:00:00Z", "actor": "news",
                  "id": sid, "rev": 2, "fields": {"status": "developing"}}
        day = _today_utc()
        _write_ledger_day(self.root_once, day, [genesis, update])
        _write_ledger_day(self.root_twice, day, [genesis, update, update])
        once = self.store.materialize(root=self.root_once)
        twice = self.store.materialize(root=self.root_twice)
        self.assertEqual(once["stories"][sid], twice["stories"][sid])
        self.assertEqual(twice["stories"][sid]["status"], "developing")

    def test_duplicate_publish_event_does_not_change_the_folded_result(self):
        sid = self.store.story_id("https://example.com/dedupe-publish")
        genesis = {"ev": "seen", "ts": "2026-07-01T00:00:00Z", "actor": "news", "story": {
            "id": sid, "url": "https://example.com/dedupe-publish", "headline": "H",
            "summary": "S", "status": "candidate", "first_seen": "2026-07-01T00:00:00Z",
            "updated": "2026-07-01T00:00:00Z", "legacy_ids": [], "editions": [],
            "streams": ["news"], "tags": [], "topics": [],
        }}
        publish = {"ev": "publish", "ts": "2026-07-02T00:00:00Z", "actor": "news",
                   "id": sid, "edition": "2026-07-02-news",
                   "fields": {"display_body": "Body.", "why": "Why.", "importance": 2,
                              "status": "settled"}}
        day = _today_utc()
        _write_ledger_day(self.root_once, day, [genesis, publish])
        _write_ledger_day(self.root_twice, day, [genesis, publish, publish])
        once = self.store.materialize(root=self.root_once)
        twice = self.store.materialize(root=self.root_twice)
        self.assertEqual(once["stories"][sid], twice["stories"][sid])
        self.assertEqual(twice["stories"][sid]["editions"].count("2026-07-02-news"), 1,
                          "a duplicate publish must not duplicate the edition entry")

    def test_duplicate_feedback_event_does_not_change_the_folded_result(self):
        sid = self.store.story_id("https://example.com/dedupe-feedback")
        genesis = {"ev": "seen", "ts": "2026-07-01T00:00:00Z", "actor": "news", "story": {
            "id": sid, "url": "https://example.com/dedupe-feedback", "headline": "H",
            "summary": "S", "status": "candidate", "first_seen": "2026-07-01T00:00:00Z",
            "updated": "2026-07-01T00:00:00Z", "legacy_ids": [], "editions": [],
            "streams": ["news"], "tags": [], "topics": [],
        }}
        fb = {"ev": "feedback", "ts": "2026-07-02T00:00:00Z", "actor": "bridge",
              "id": sid, "fb_id": "fb-dup-1", "vote": 1, "reason": "", "reader": "rafael",
              "surface": "web", "brief": "2026-07-02-news", "raw_story_id": sid}
        day = _today_utc()
        _write_ledger_day(self.root_once, day, [genesis, fb])
        _write_ledger_day(self.root_twice, day, [genesis, fb, fb])
        once = self.store.materialize(root=self.root_once)
        twice = self.store.materialize(root=self.root_twice)
        self.assertEqual(once["stories"][sid]["feedback"], twice["stories"][sid]["feedback"])
        self.assertEqual(twice["stories"][sid]["feedback"]["up"], 1,
                          "a duplicate feedback event must not double-count the tally")


class InvariantCSeenFoldTests(unittest.TestCase):
    """(c) multiple seen events sharing a norm_url FOLD into one story: editions/
    legacy_ids/alt_urls/streams union, first_seen=min, updated=max, later-ts non-empty
    scalar fields win."""

    @classmethod
    def setUpClass(cls):
        cls.store = _load_module(STORE_PATH, f"store_foldc_{id(cls)}")

    def setUp(self):
        self.root = _new_root()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_two_seen_events_for_norm_url_equivalent_urls_fold_to_one_story(self):
        url_a = "https://www.example.com/alpha?utm_source=rss"
        url_b = "https://example.com/alpha/"
        sid = self.store.story_id(url_a)
        self.assertEqual(sid, self.store.story_id(url_b))

        earlier = {
            "ev": "seen", "ts": "2026-07-01T06:00:00Z", "actor": "news", "story": {
                "id": sid, "url": url_a, "headline": "Alpha headline v1",
                "summary": "S1", "status": "candidate",
                "first_seen": "2026-07-01T06:00:00Z", "updated": "2026-07-01T06:00:00Z",
                "legacy_ids": ["legacy-a"], "editions": ["2026-07-01-news"],
                "streams": ["news"], "tags": [], "topics": [],
                "display_body": "Earlier non-empty body.", "why": "",
            },
        }
        later = {
            "ev": "seen", "ts": "2026-07-02T06:00:00Z", "actor": "ai-ml", "story": {
                "id": sid, "url": url_b, "headline": "Alpha headline v2 (later)",
                "summary": "S2", "status": "candidate",
                "first_seen": "2026-07-02T06:00:00Z", "updated": "2026-07-02T06:00:00Z",
                "legacy_ids": ["legacy-b"], "editions": ["2026-07-02-ai-ml"],
                "streams": ["ai-ml"], "tags": [], "topics": [],
                "display_body": "", "why": "",
            },
        }
        day = _today_utc()
        _write_ledger_day(self.root, day, [earlier, later])
        snap = self.store.materialize(root=self.root)
        rec = snap["stories"][sid]

        self.assertEqual(set(rec["editions"]), {"2026-07-01-news", "2026-07-02-ai-ml"})
        self.assertEqual(set(rec["legacy_ids"]), {"legacy-a", "legacy-b"})
        self.assertEqual(set(rec["streams"]), {"news", "ai-ml"})
        self.assertEqual(rec["first_seen"], "2026-07-01T06:00:00Z", "first_seen = min")
        self.assertEqual(rec["updated"], "2026-07-02T06:00:00Z", "updated = max")
        self.assertEqual(rec["headline"], "Alpha headline v2 (later)",
                          "later-ts non-empty scalar field wins")
        self.assertEqual(rec["display_body"], "Earlier non-empty body.",
                          "a later-ts EMPTY scalar must not clobber an earlier non-empty one")


class InvariantDFeedbackFoldTests(unittest.TestCase):
    """(d) feedback folds last-write-wins per (reader, id, surface); vote 0 clears the
    pair; folded tallies land in record.feedback{up,down,last_reason}."""

    @classmethod
    def setUpClass(cls):
        cls.store = _load_module(STORE_PATH, f"store_foldd_{id(cls)}")

    def setUp(self):
        self.root = _new_root()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def _genesis(self, sid, url):
        return {"ev": "seen", "ts": "2026-07-01T00:00:00Z", "actor": "news", "story": {
            "id": sid, "url": url, "headline": "H", "summary": "S", "status": "settled",
            "first_seen": "2026-07-01T00:00:00Z", "updated": "2026-07-01T00:00:00Z",
            "legacy_ids": [], "editions": [], "streams": ["news"], "tags": [], "topics": [],
        }}

    def test_same_reader_id_surface_last_write_wins_not_accumulated(self):
        url = "https://example.com/feedback-lww"
        sid = self.store.story_id(url)
        events = [
            self._genesis(sid, url),
            {"ev": "feedback", "ts": "2026-07-02T09:00:00Z", "actor": "bridge",
             "id": sid, "fb_id": "fb-1", "vote": 1, "reason": "", "reader": "rafael",
             "surface": "web", "brief": "2026-07-02-news", "raw_story_id": sid},
            {"ev": "feedback", "ts": "2026-07-02T10:00:00Z", "actor": "bridge",
             "id": sid, "fb_id": "fb-2", "vote": -1, "reason": "changed my mind",
             "reader": "rafael", "surface": "web", "brief": "2026-07-02-news",
             "raw_story_id": sid},
        ]
        _write_ledger_day(self.root, _today_utc(), events)
        snap = self.store.materialize(root=self.root)
        fb = snap["stories"][sid]["feedback"]
        self.assertEqual(fb["up"], 0)
        self.assertEqual(fb["down"], 1)
        self.assertEqual(fb["last_reason"], "changed my mind")

    def test_vote_zero_clears_the_reader_id_surface_pair(self):
        url = "https://example.com/feedback-clear"
        sid = self.store.story_id(url)
        events = [
            self._genesis(sid, url),
            {"ev": "feedback", "ts": "2026-07-02T09:00:00Z", "actor": "bridge",
             "id": sid, "fb_id": "fb-3", "vote": 1, "reason": "", "reader": "rafael",
             "surface": "web", "brief": "2026-07-02-news", "raw_story_id": sid},
            {"ev": "feedback", "ts": "2026-07-02T10:00:00Z", "actor": "bridge",
             "id": sid, "fb_id": "fb-4", "vote": 0, "reason": "", "reader": "rafael",
             "surface": "web", "brief": "2026-07-02-news", "raw_story_id": sid},
        ]
        _write_ledger_day(self.root, _today_utc(), events)
        snap = self.store.materialize(root=self.root)
        fb = snap["stories"][sid]["feedback"]
        self.assertEqual(fb["up"], 0)
        self.assertEqual(fb["down"], 0)

    def test_distinct_readers_both_count(self):
        url = "https://example.com/feedback-multireader"
        sid = self.store.story_id(url)
        events = [
            self._genesis(sid, url),
            {"ev": "feedback", "ts": "2026-07-02T09:00:00Z", "actor": "bridge",
             "id": sid, "fb_id": "fb-5", "vote": 1, "reason": "", "reader": "rafael",
             "surface": "web", "brief": "2026-07-02-news", "raw_story_id": sid},
            {"ev": "feedback", "ts": "2026-07-02T09:05:00Z", "actor": "bridge",
             "id": sid, "fb_id": "fb-6", "vote": 1, "reason": "", "reader": "guest",
             "surface": "web", "brief": "2026-07-02-news", "raw_story_id": sid},
        ]
        _write_ledger_day(self.root, _today_utc(), events)
        snap = self.store.materialize(root=self.root)
        self.assertEqual(snap["stories"][sid]["feedback"]["up"], 2)

    def test_distinct_surfaces_for_same_reader_both_count(self):
        url = "https://example.com/feedback-multisurface"
        sid = self.store.story_id(url)
        events = [
            self._genesis(sid, url),
            {"ev": "feedback", "ts": "2026-07-02T09:00:00Z", "actor": "bridge",
             "id": sid, "fb_id": "fb-7", "vote": 1, "reason": "", "reader": "rafael",
             "surface": "web", "brief": "2026-07-02-news", "raw_story_id": sid},
            {"ev": "feedback", "ts": "2026-07-02T09:05:00Z", "actor": "bridge",
             "id": sid, "fb_id": "fb-8", "vote": -1, "reason": "", "reader": "rafael",
             "surface": "email", "brief": "2026-07-02-news", "raw_story_id": sid},
        ]
        _write_ledger_day(self.root, _today_utc(), events)
        snap = self.store.materialize(root=self.root)
        fb = snap["stories"][sid]["feedback"]
        self.assertEqual(fb["up"], 1)
        self.assertEqual(fb["down"], 1)


class InvariantEUnionMergeGitTests(unittest.TestCase):
    """(e) a real two-branch git test in a tempdir repo: .gitattributes declares
    merge=union on index/ledger/*.jsonl; two branches each append a DIFFERENT event to the
    same ledger file; merge must not conflict AND materialize() must yield both events.
    This is entirely self-contained inside its own tempdir repo (never touches the real
    repo's git state)."""

    @classmethod
    def setUpClass(cls):
        cls.store = _load_module(STORE_PATH, f"store_unionmerge_{id(cls)}")
        if shutil.which("git") is None:
            raise unittest.SkipTest("git binary not available")

    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="store-unionmerge-")
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)

    def _git(self, *args):
        return subprocess.run(
            ["git"] + list(args), cwd=self.repo, capture_output=True, text=True, check=True,
            env={**os.environ, "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@test.local",
                 "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@test.local"},
        )

    def test_two_branches_appending_to_the_same_ledger_file_union_merge_without_conflict(self):
        os.makedirs(os.path.join(self.repo, "index", "ledger"), exist_ok=True)
        with open(os.path.join(self.repo, ".gitattributes"), "w") as f:
            f.write("index/ledger/*.jsonl merge=union\n")

        self._git("init", "-q")
        self._git("checkout", "-q", "-b", "main")
        self._git("config", "commit.gpgsign", "false")

        day = _today_utc()
        ledger_rel = os.path.join("index", "ledger", f"{day}.jsonl")
        ledger_abs = os.path.join(self.repo, ledger_rel)

        sid_a = self.store.story_id("https://example.com/union-branch-a")
        sid_b = self.store.story_id("https://example.com/union-branch-b")
        event_a = {"ev": "seen", "ts": f"{day}T06:00:00Z", "actor": "news", "story": {
            "id": sid_a, "url": "https://example.com/union-branch-a", "headline": "A",
            "summary": "S", "status": "candidate", "first_seen": f"{day}T06:00:00Z",
            "updated": f"{day}T06:00:00Z", "legacy_ids": [], "editions": [],
            "streams": ["news"], "tags": [], "topics": [],
        }}
        event_b = {"ev": "seen", "ts": f"{day}T07:00:00Z", "actor": "ai-ml", "story": {
            "id": sid_b, "url": "https://example.com/union-branch-b", "headline": "B",
            "summary": "S", "status": "candidate", "first_seen": f"{day}T07:00:00Z",
            "updated": f"{day}T07:00:00Z", "legacy_ids": [], "editions": [],
            "streams": ["ai-ml"], "tags": [], "topics": [],
        }}

        # base commit: empty ledger file present on main
        open(ledger_abs, "a").close()
        self._git("add", ".gitattributes", ledger_rel)
        self._git("commit", "-q", "-m", "base")

        self._git("checkout", "-q", "-b", "branch-a")
        with open(ledger_abs, "a") as f:
            f.write(json.dumps(event_a, ensure_ascii=False) + "\n")
        self._git("add", ledger_rel)
        self._git("commit", "-q", "-m", "branch a appends event A")

        self._git("checkout", "-q", "main")
        self._git("checkout", "-q", "-b", "branch-b")
        with open(ledger_abs, "a") as f:
            f.write(json.dumps(event_b, ensure_ascii=False) + "\n")
        self._git("add", ledger_rel)
        self._git("commit", "-q", "-m", "branch b appends event B")

        self._git("checkout", "-q", "branch-a")
        merge = subprocess.run(
            ["git", "merge", "--no-edit", "branch-b"], cwd=self.repo,
            capture_output=True, text=True,
            env={**os.environ, "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@test.local",
                 "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@test.local"},
        )
        self.assertEqual(merge.returncode, 0,
                          f"union merge must not conflict; stdout={merge.stdout!r} "
                          f"stderr={merge.stderr!r}")

        with open(ledger_abs) as f:
            lines = [ln for ln in f.read().splitlines() if ln.strip()]
        self.assertEqual(len(lines), 2, f"expected both events preserved, got: {lines}")

        snap = self.store.materialize(root=self.repo)
        self.assertIn(sid_a, snap["stories"], "materialize must see branch A's event")
        self.assertIn(sid_b, snap["stories"], "materialize must see branch B's event")


# --------------------------------------------------------------------------- #
# CLI smoke tests
# --------------------------------------------------------------------------- #
class StoreCliTests(unittest.TestCase):
    """Light black-box CLI coverage; the detailed contract is pinned by the API-level
    tests above. Skips cleanly (via setUpClass AssertionError) if store.py is absent."""

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(STORE_PATH):
            raise AssertionError(f"expected implementation file is missing: {STORE_PATH}")
        cls.store = _load_module(STORE_PATH, f"store_cli_{id(cls)}")

    def setUp(self):
        self.root = _new_root()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_id_subcommand_prints_the_story_id(self):
        url = "https://example.com/cli-id-check"
        proc = _run_cli(["id", url])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), self.store.story_id(url))

    def test_append_subcommand_reads_stdin_and_appends(self):
        ev = {"ev": "status", "ts": "2026-07-08T06:00:00Z", "actor": "news",
              "id": "st-000000000000", "status": "dropped"}
        proc = _run_cli(["append", "--root", self.root], input_text=json.dumps(ev))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        events = _read_ledger_events(self.root)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["id"], "st-000000000000")

    def test_append_subcommand_rejects_malformed_event(self):
        proc = _run_cli(["append", "--root", self.root], input_text=json.dumps({"nope": True}))
        self.assertNotEqual(proc.returncode, 0)

    def test_materialize_subcommand_writes_snapshot_and_prints_summary(self):
        ev = {"ev": "status", "ts": "2026-07-08T06:00:00Z", "actor": "news",
              "id": "st-000000000000", "status": "dropped"}
        _run_cli(["append", "--root", self.root], input_text=json.dumps(ev))
        proc = _run_cli(["materialize", "--root", self.root])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertRegex(proc.stdout.strip(), r"^materialized \d+ stories? / \d+ events?$")
        snapshot_path = os.path.join(self.root, "index", "ledger", ".materialized.json")
        self.assertTrue(os.path.exists(snapshot_path))
        with open(snapshot_path) as f:
            snap = json.load(f)
        self.assertIn("stories", snap)

    def test_selftest_subcommand_exits_zero(self):
        proc = subprocess.run([sys.executable, STORE_PATH, "selftest"],
                               capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, f"stdout={proc.stdout!r} stderr={proc.stderr!r}")


if __name__ == "__main__":
    unittest.main()
