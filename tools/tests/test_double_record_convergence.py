#!/usr/bin/env python3
"""RED-phase spec — double-`record` convergence (the 2026-07-07 Cuba identity fork).

Production failure: `dedup.py record` ran twice for edition 2026-07-07-news, 3 minutes
apart. 7 of 8 stories were byte-identical; the 8th (Cuba blackout) was the SAME
real-world story with a lightly reworded headline and a flipped primary url
(aljazeera.com on the first call, letemps.ch on the second — both calls' brief bullet
cited BOTH urls). The second run plain-overwrote index/stories/2026-07-07-news.jsonl
with a brand-new identity (letemps url -> st-df6bde5fe934, new legacy id) while the
anchor step, which ran off the FIRST call's output, had stamped the post with the first
(aljazeera -> st-51f44833a0eb). Reader-facing anchor and dedup-canonical id diverged
for the same story.

Contract these tests pin down (tools/dedup/dedup.py::cmd_record):

* When `record` runs for an edition whose index/stories/{date}-{slug}.jsonl ALREADY
  exists, an incoming story that is the SAME story as an existing record must keep the
  EXISTING record's identity — its `url` (the thing st- sids derive from) and its
  legacy `id` — while content fields (summary / display_body / headline ...) may
  update to the newer payload.
* "Same story" must at minimum catch:
    (a) identical norm_url on the primary url (scheme/www/utm/trailing-slash noise);
    (b) any overlap between the incoming story's cited urls and the existing record's
        url. Payload key pinned here: an optional `urls` list on the Step C story dict
        (every url cited in the story's bullet, primary included) — cmd_record receives
        the writer's story dicts verbatim, so the field is available on the record path;
    (c) a near-identical headline — the real Cuba pair. The stub embedder below makes
        that headline pair embed near-identically (cosine ~0.999, as bge-m3 does for a
        light rewording), so dedup.py's existing cosine similarity machinery can carry
        this signal; unrelated texts get independent seeded vectors (cosine ~0).
* Ledger dual-write follows the converged identity: a re-record must NOT append
  seen/publish events under a second st- id for the same story.
* Guards that already hold today and must KEEP holding: a first run (no pre-existing
  edition file) behaves as today even when a story carries `urls`; a byte-identical
  re-record stays idempotent (extends test_dualwrite's
  test_running_record_twice_does_not_duplicate_materialized_stories down to the byte
  level); convergence never merges a genuinely different story.

RED expectation: the convergence tests fail against current code (cmd_record has no
within-edition convergence — it rewrites the file with second-call identities); the
first-run / idempotency / no-false-merge guards pass today and must not regress.

Run: python3 -m unittest tools.tests.test_double_record_convergence -v
"""
import argparse
import contextlib
import glob
import hashlib
import importlib.util
import io
import json
import os
import random
import shutil
import tempfile
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
DEDUP_PATH = os.path.join(REPO_ROOT, "tools", "dedup", "dedup.py")
STORE_PATH = os.path.join(REPO_ROOT, "tools", "store", "store.py")

DATE = "2026-07-07"
SLUG = "news"
EDITION = f"{DATE}-{SLUG}"

# --------------------------------------------------------------------------- #
# scenario payloads — modeled directly on the production 2026-07-07-news records
# --------------------------------------------------------------------------- #
CUBA_URL_ALJAZEERA = ("https://www.aljazeera.com/news/2026/7/7/"
                      "cuba-sees-nationwide-power-blackout-for-third-time-in-six-months")
CUBA_URL_LETEMPS = ("https://www.letemps.ch/articles/"
                    "sous-blocus-petrolier-americain-cuba-s-efforce-de-retablir-son-reseau-electrique")

CONTROL = {
    "headline": "NATO's summit opens in Ankara with defence spending on the agenda",
    "summary": "NATO's two-day summit opened in Ankara on 7 July with defence budgets dominating.",
    "url": "https://www.aljazeera.com/news/2026/7/7/nato-summit-begins-who-is-attending",
    "tier": "T2", "tags": [], "topics": ["geopolitics"], "importance": 2,
    "display_body": "NATO's two-day summit opened in Ankara on 7 July.",
    "why": "", "event_date": "2026-07-07",
}

CUBA_RUN1 = {
    "headline": "Cuba hit by its third nationwide blackout of the year",
    "summary": "Cuba's grid collapsed nationwide on 6 July, the third total outage of 2026, "
               "as fuel reserves dwindle under a US blockade.",
    "url": CUBA_URL_ALJAZEERA,
    "tier": "T2", "tags": ["single-source"], "topics": ["world", "economy"], "importance": 1,
    "display_body": "Cuba's power grid collapsed across the island on Mon 6 July, "
                    "the third total outage of 2026.",
    "why": "", "event_date": "2026-07-06",
}

# (a) same primary source, same norm_url modulo scheme/www/utm/trailing-slash noise,
# clearly reworded headline (different slugified legacy id, orthogonal stub embedding):
# only the norm_url signal can catch this one.
CUBA_RUN2_SAME_NORM = {
    "headline": "Havana goes dark again as Cuba's grid collapses for a third time",
    "summary": "Cuba's electricity grid failed across the island on 6 July, the third full "
               "collapse in six months.",
    "url": ("http://aljazeera.com/news/2026/7/7/"
            "cuba-sees-nationwide-power-blackout-for-third-time-in-six-months/?utm_source=feed"),
    "tier": "T2", "tags": [], "topics": ["world", "economy"], "importance": 1,
    "display_body": "Run-two refreshed body: the grid operator could meet just 1% of "
                    "Havana's demand while prioritising hospitals.",
    "why": "", "event_date": "2026-07-06",
}

# (b) primary url flipped to letemps (different norm_url), unrelated wording (orthogonal
# stub embedding), but the bullet's cited urls overlap the existing record's url — the
# exact Cuba shape: both calls cited BOTH letemps and aljazeera.
CUBA_RUN2_CITED = {
    "headline": "Under a US oil blockade, Havana struggles to restore its electricity network",
    "summary": "The island is working to restore power after a full grid collapse on 6 July, "
               "its fuel reserves strangled by the US embargo.",
    "url": CUBA_URL_LETEMPS,
    "urls": [CUBA_URL_LETEMPS, CUBA_URL_ALJAZEERA],
    "tier": "T2", "tags": [], "topics": ["world", "economy"], "importance": 1,
    "display_body": "Run-two refreshed body: the fuel shortage indisputably complicates "
                    "restoring the grid, the energy ministry's electricity director said.",
    "why": "", "event_date": "2026-07-06",
}

# (c) the verbatim production second call: primary url flipped, NO cited-urls list —
# only the near-identical headline (high-cosine under the stub, as under bge-m3) links it.
CUBA_RUN2_REWORDED = {
    "headline": "Cuba hit by its third nationwide blackout in under six months",
    "summary": "Cuba's grid collapsed nationwide on 6 July, the third total outage in under "
               "six months, as fuel reserves dwindle under a US blockade.",
    "url": CUBA_URL_LETEMPS,
    "tier": "T2", "tags": [], "topics": ["world", "economy"], "importance": 1,
    "display_body": "Run-two refreshed body: by late afternoon the operator could meet just "
                    "1% of Havana's demand while prioritising hospitals.",
    "why": "", "event_date": "2026-07-06",
}

# genuinely DIFFERENT story on the same domain as CUBA_RUN1 (guards against a sloppy
# domain-level or converge-everything implementation).
NEW_STORY = {
    "headline": "Haiti's main port shuts as gang blockade chokes fuel imports",
    "summary": "Port-au-Prince's container terminal suspended operations on 7 July after a "
               "gang blockade cut fuel deliveries.",
    "url": "https://www.aljazeera.com/news/2026/7/7/haiti-main-port-shuts-as-gang-blockade",
    "tier": "T2", "tags": [], "topics": ["world"], "importance": 1,
    "display_body": "Port-au-Prince's main container terminal suspended operations on 7 July.",
    "why": "", "event_date": "2026-07-07",
}


# --------------------------------------------------------------------------- #
# infrastructure — no network, no real-repo writes (conventions: test_dualwrite.py)
# --------------------------------------------------------------------------- #
# Texts containing this key embed as one topic vector + tiny per-text noise
# (cosine ~0.999 between them) — the real Cuba headline pair. Everything else gets an
# independent sha1-seeded vector (cosine ~0 at 1024 dims).
_TOPIC_KEYS = ("Cuba hit by its third nationwide blackout",)


def _seeded_vec(key):
    seed = int(hashlib.sha1(key.encode("utf-8")).hexdigest(), 16) % (2 ** 32)
    rng = random.Random(seed)
    return [rng.uniform(-1.0, 1.0) for _ in range(1024)]


def _stub_embed(texts, worker=None, token=None):
    """Deterministic, offline stand-in for dedup.embed(): same text -> same vector on
    every call, near-identical Cuba headlines -> near-identical vectors."""
    out = []
    for t in texts:
        topic = next((k for k in _TOPIC_KEYS if k in t), None)
        if topic is None:
            out.append(_seeded_vec(t))
        else:
            base = _seeded_vec("topic:" + topic)
            noise = _seeded_vec("noise:" + t)
            out.append([b + 0.02 * n for b, n in zip(base, noise)])
    return out


def _load_module(path, name):
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
    """Fresh dedup.py rooted at repo_root (REPO is read from os.environ at module-exec
    time), with the network embed() swapped for the deterministic stub."""
    with _env("REPO", repo_root):
        mod = _load_module(DEDUP_PATH, modname)
    mod.embed = _stub_embed
    return mod


def _new_skeleton():
    root = tempfile.mkdtemp(prefix="doublerecord-")
    os.makedirs(os.path.join(root, "index", "stories"))
    os.makedirs(os.path.join(root, "index", "ledger"))
    os.makedirs(os.path.join(root, "_posts"))
    return root


def _write_payload(root, name, stories):
    path = os.path.join(root, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"stories": stories}, f, ensure_ascii=False)
    return path


def _run_record(root, modname, payload_path, date=DATE, slug=SLUG):
    """Invoke cmd_record exactly as the CLI would; returns (module, captured stdout)."""
    mod = _load_dedup(root, modname)
    args = argparse.Namespace(stories=payload_path, date=date, slug=slug,
                              keep_days=40, worker=None, token=None)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        mod.cmd_record(args)
    return mod, buf.getvalue()


def _index_path(root, date=DATE, slug=SLUG):
    return os.path.join(root, "index", "stories", f"{date}-{slug}.jsonl")


def _index_records(root, date=DATE, slug=SLUG):
    with open(_index_path(root, date, slug)) as f:
        return [json.loads(ln) for ln in f if ln.strip()]


def _cuba_records(records):
    """Every record that is not the (byte-stable) control story — in a healthy state
    exactly one, whatever url identity it ended up with."""
    return [r for r in records if r.get("headline") != CONTROL["headline"]]


def _ledger_events(root):
    events = []
    for path in sorted(glob.glob(os.path.join(root, "index", "ledger", "*.jsonl"))):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
    return events


class _ConvergenceBase(unittest.TestCase):
    """Shared first run: the edition file already exists (CONTROL + CUBA_RUN1) before
    each scenario's second `record` invocation."""

    def setUp(self):
        self.root = _new_skeleton()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.store = _load_module(STORE_PATH, f"store_conv_{id(self)}")
        run1 = _write_payload(self.root, "run1.json", [CONTROL, CUBA_RUN1])
        _run_record(self.root, f"dedup_conv_{id(self)}_r1", run1)
        records = _index_records(self.root)
        self.assertEqual(len(records), 2, "sanity: first run records both stories")
        (self.first,) = _cuba_records(records)
        self.assertEqual(self.first["url"], CUBA_URL_ALJAZEERA,
                         "sanity: first-call identity is the aljazeera url")

    def _rerecord(self, cuba_story):
        """Second `record` for the same edition; returns (records, stdout)."""
        run2 = _write_payload(self.root, "run2.json", [CONTROL, cuba_story])
        _, out = _run_record(self.root, f"dedup_conv_{id(self)}_r2", run2)
        return _index_records(self.root), out


# --------------------------------------------------------------------------- #
# (a) identical norm_url on the primary url
# --------------------------------------------------------------------------- #
class SameNormUrlConvergenceTests(_ConvergenceBase):

    def test_rerecord_keeps_first_calls_url_and_legacy_id(self):
        """Same story re-recorded under a norm_url-identical primary (scheme/www/utm/
        trailing-slash noise) with a reworded headline must keep the FIRST call's url
        string and legacy id — not fork to a fresh slugified identity."""
        records, _ = self._rerecord(CUBA_RUN2_SAME_NORM)
        self.assertEqual(len(records), 2, "the edition must still hold exactly two stories")
        (cuba,) = _cuba_records(records)
        self.assertEqual(cuba["url"], self.first["url"],
                         "converged record must keep the FIRST call's url — st- sids and the "
                         "already-stamped anchors derive from it")
        self.assertEqual(cuba["id"], self.first["id"],
                         "converged record must keep the FIRST call's legacy id (by_legacy "
                         "joins key on it)")

    def test_converged_rerecord_updates_content_fields_to_newer_payload(self):
        """Identity sticks to the first call, content follows the second: the record
        found under the FIRST call's legacy id must carry the SECOND payload's prose."""
        records, _ = self._rerecord(CUBA_RUN2_SAME_NORM)
        by_id = {r["id"]: r for r in records}
        self.assertIn(self.first["id"], by_id,
                      "the first call's legacy id must survive the re-record")
        rec = by_id[self.first["id"]]
        self.assertEqual(rec["display_body"], CUBA_RUN2_SAME_NORM["display_body"],
                         "content fields update to the newer payload")
        self.assertEqual(rec["summary"], CUBA_RUN2_SAME_NORM["summary"],
                         "content fields update to the newer payload")


# --------------------------------------------------------------------------- #
# (b) overlap between the incoming story's cited urls and the existing record's url
# --------------------------------------------------------------------------- #
class CitedUrlOverlapConvergenceTests(_ConvergenceBase):

    def test_rerecord_keeps_first_calls_identity_via_cited_url_overlap(self):
        """The Cuba shape: primary url flipped (letemps), but the incoming story's
        cited `urls` include the existing record's url (aljazeera) — same story, so the
        existing identity wins."""
        records, _ = self._rerecord(CUBA_RUN2_CITED)
        self.assertEqual(len(records), 2, "the edition must still hold exactly two stories")
        (cuba,) = _cuba_records(records)
        self.assertEqual(cuba["url"], CUBA_URL_ALJAZEERA,
                         "cited-url overlap must converge onto the FIRST call's url, not "
                         "flip the edition's identity to the second call's primary")
        self.assertEqual(cuba["id"], self.first["id"],
                         "converged record must keep the FIRST call's legacy id")

    def test_rerecord_does_not_fork_ledger_story_id(self):
        """Dual-write follows the converged identity: after the re-record the ledger must
        materialize exactly one story per real-world story — no second st- id minted from
        the second call's primary url (the st-51f44833a0eb / st-df6bde5fe934 fork)."""
        _, out = self._rerecord(CUBA_RUN2_CITED)
        self.assertNotIn("dual-write failed", out,
                         f"ledger dual-write must succeed on the re-record, got:\n{out}")
        snap = self.store.materialize(days=60, root=self.root)
        sid_control = self.store.story_id(CONTROL["url"])
        sid_first = self.store.story_id(CUBA_URL_ALJAZEERA)
        sid_fork = self.store.story_id(CUBA_URL_LETEMPS)
        self.assertNotIn(sid_fork, snap["stories"],
                         "the second call's primary url must not mint a second story id")
        self.assertEqual(set(snap["stories"]), {sid_control, sid_first},
                         "exactly one materialized story per real-world story")


# --------------------------------------------------------------------------- #
# (c) near-identical headline (the verbatim production second call)
# --------------------------------------------------------------------------- #
class NearIdenticalHeadlineConvergenceTests(_ConvergenceBase):

    def test_rerecord_keeps_first_calls_identity_on_near_identical_headline(self):
        """The real pair: '…blackout of the year' vs '…blackout in under six months',
        primary flipped to letemps, no cited-urls list. The similarity signal alone must
        keep the first call's identity."""
        records, _ = self._rerecord(CUBA_RUN2_REWORDED)
        self.assertEqual(len(records), 2, "the edition must still hold exactly two stories")
        (cuba,) = _cuba_records(records)
        self.assertEqual(cuba["url"], CUBA_URL_ALJAZEERA,
                         "a near-identical headline must converge onto the FIRST call's url")
        self.assertEqual(cuba["id"], self.first["id"],
                         "converged record must keep the FIRST call's legacy id")

    def test_edition_index_sid_agrees_with_first_call_anchor_sid(self):
        """The reader-facing invariant that broke on 2026-07-07: anchor.py stamped the
        post from the FIRST call's output, so the sid derivable from the edition file
        after the re-record must still equal the first call's sid — and the ledger must
        not carry the forked one."""
        records, out = self._rerecord(CUBA_RUN2_REWORDED)
        (cuba,) = _cuba_records(records)
        sid_first = self.store.story_id(CUBA_URL_ALJAZEERA)
        sid_fork = self.store.story_id(CUBA_URL_LETEMPS)
        self.assertEqual(self.store.story_id(cuba["url"]), sid_first,
                         "anchor (stamped off run 1) and edition index must agree on the sid")
        self.assertNotIn("dual-write failed", out,
                         f"ledger dual-write must succeed on the re-record, got:\n{out}")
        snap = self.store.materialize(days=60, root=self.root)
        self.assertNotIn(sid_fork, snap["stories"],
                         "the ledger must not materialize a second story id for the same story")


# --------------------------------------------------------------------------- #
# guards — behavior that already holds today and must not regress with the fix
# --------------------------------------------------------------------------- #
class RecordGuardTests(_ConvergenceBase):

    def test_byte_identical_rerecord_stays_idempotent(self):
        """Byte-level extension of test_dualwrite's running-record-twice test: an
        identical second run must leave the edition file byte-identical and materialize
        the same stories once."""
        with open(_index_path(self.root), "rb") as f:
            before = f.read()
        self._rerecord(CUBA_RUN1)
        with open(_index_path(self.root), "rb") as f:
            after = f.read()
        self.assertEqual(before, after,
                         "an identical re-record must not perturb a byte of the edition file")
        snap = self.store.materialize(days=60, root=self.root)
        expected = {self.store.story_id(CONTROL["url"]),
                    self.store.story_id(CUBA_URL_ALJAZEERA)}
        self.assertEqual(set(snap["stories"]), expected)
        for sid in expected:
            self.assertEqual(snap["stories"][sid].get("editions"), [EDITION],
                             "editions must not duplicate on an identical re-record")

    def test_rerecord_never_merges_a_genuinely_new_story(self):
        """Convergence must not be a converge-everything cheat: a genuinely different
        story added on the second run — same domain as the existing Cuba record, distinct
        path, unrelated headline — keeps its OWN fresh identity."""
        run2 = _write_payload(self.root, "run2.json", [CONTROL, CUBA_RUN1, NEW_STORY])
        mod, _ = _run_record(self.root, f"dedup_conv_{id(self)}_new", run2)
        records = _index_records(self.root)
        self.assertEqual(len(records), 3, "all three stories must be recorded")
        self.assertEqual(len({r["id"] for r in records}), 3, "three distinct legacy ids")
        new = next(r for r in records if r["headline"] == NEW_STORY["headline"])
        self.assertEqual(new["url"], NEW_STORY["url"],
                         "a new story keeps its own url, not a converged one")
        self.assertEqual(new["id"], f"{DATE}-{SLUG}-{mod.slugify(NEW_STORY['headline'])}",
                         "a new story derives its own legacy id from its own headline")
        (cuba,) = [r for r in records
                   if r["headline"] not in (CONTROL["headline"], NEW_STORY["headline"])]
        self.assertEqual((cuba["id"], cuba["url"]), (self.first["id"], self.first["url"]),
                         "the existing Cuba record keeps its identity untouched")


class FirstRunUnchangedTests(unittest.TestCase):
    """No pre-existing edition file -> no convergence target: a first run must behave
    exactly as today even when the payload carries the optional `urls` list (byte-level
    first-run identity is separately enforced by test_dualwrite's golden)."""

    def setUp(self):
        self.root = _new_skeleton()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.store = _load_module(STORE_PATH, f"store_first_{id(self)}")

    def test_first_run_with_cited_urls_uses_its_own_primary_identity(self):
        payload = _write_payload(self.root, "run1.json", [CUBA_RUN2_CITED])
        mod, _ = _run_record(self.root, f"dedup_first_{id(self)}", payload)
        records = _index_records(self.root)
        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual(rec["url"], CUBA_URL_LETEMPS,
                         "first run: identity comes from the story's own primary url")
        self.assertEqual(rec["id"],
                         f"{DATE}-{SLUG}-{mod.slugify(CUBA_RUN2_CITED['headline'])}",
                         "first run: legacy id derives from the story's own headline")
        seen = [e for e in _ledger_events(self.root) if e.get("ev") == "seen"]
        self.assertEqual([e["story"]["id"] for e in seen],
                         [self.store.story_id(CUBA_URL_LETEMPS)],
                         "first run: the ledger keys on the story's own primary url")


if __name__ == "__main__":
    unittest.main()
