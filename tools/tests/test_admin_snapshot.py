"""Spec tests for tools/admin/snapshot.py -- the admin-page snapshot builder (PLAN 2026-09-13 §2.4).

Covers the source rows (incl. last_event from the lifecycle tail), the usage fold being null when
tools/usage/fold.py is absent AND populated (with a sibling import) when it is present, the
recent-actions tail ordered newest-first and capped, and the pending-proposals scan that reads the
`applied:` header without the YAML loader (those files carry block scalars it cannot parse).
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIXTURE_REGISTRY = os.path.join(os.path.dirname(__file__), "fixtures", "admin", "registry.yml")


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, relpath))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


snapshot = _load("_admin_snapshot", "tools/admin/snapshot.py")
AS_OF = "2026-09-13T12:00:00Z"


class SnapshotBase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="admin-snap-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        os.makedirs(os.path.join(self.root, "sources"))
        shutil.copy(FIXTURE_REGISTRY, os.path.join(self.root, "sources", "registry.yml"))
        # _usage() puts tools/usage on sys.path to satisfy fold.py's sibling imports; undo that (and
        # any generically-named modules it cached) so tests never leak state into one another.
        saved_path, saved_mods = list(sys.path), dict(sys.modules)
        self.addCleanup(lambda: sys.path.__setitem__(slice(None), saved_path))
        self.addCleanup(lambda: [sys.modules.pop(m, None)
                                 for m in ("pricing", "fold") if m not in saved_mods])

    def write(self, relpath, text):
        path = os.path.join(self.root, relpath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)
        return path


class SourcesTest(SnapshotBase):
    def test_sources_sorted_with_last_event(self):
        snap = snapshot.build_snapshot(self.root, as_of=AS_OF)
        self.assertEqual(snap["generated"], AS_OF)
        domains = [s["domain"] for s in snap["sources"]]
        self.assertEqual(domains, sorted(domains))
        by = {s["domain"]: s for s in snap["sources"]}
        retired = by["retired.example"]
        self.assertEqual(retired["status"], "retired")
        self.assertEqual(retired["last_event"]["event"], "retired")
        self.assertEqual(retired["last_event"]["note"], "spam")
        self.assertEqual(retired["last_cited"], "2026-06-01")
        # A lifecycle entry with no note surfaces note: None, not a missing key.
        self.assertIn("note", by["src01.example"]["last_event"])
        self.assertIsNone(by["src01.example"]["last_event"]["note"])

    def test_all_required_top_keys_present(self):
        snap = snapshot.build_snapshot(self.root, as_of=AS_OF)
        for key in ("generated", "head", "sources", "usage", "actions_recent", "proposals_pending"):
            self.assertIn(key, snap)


class UsageTest(SnapshotBase):
    def test_usage_null_when_fold_absent(self):
        snap = snapshot.build_snapshot(self.root, as_of=AS_OF)
        self.assertIsNone(snap["usage"])

    def test_usage_folded_when_present_with_sibling_import(self):
        # fold.py follows the repo's `import pricing` sibling convention; the snapshot must put
        # tools/usage on sys.path before exec'ing it, or the import fails and usage wrongly nulls.
        self.write("tools/usage/pricing.py", "RATE = 3\n")
        self.write("tools/usage/fold.py",
                   "import pricing\n"
                   "def fold(root, as_of=None):\n"
                   "    return {'runs': 2, 'rate': pricing.RATE}\n")
        snap = snapshot.build_snapshot(self.root, as_of=AS_OF)
        self.assertEqual(snap["usage"], {"runs": 2, "rate": 3})

    def test_usage_null_when_fold_raises(self):
        self.write("tools/usage/fold.py",
                   "def fold(root, as_of=None):\n    raise RuntimeError('boom')\n")
        snap = snapshot.build_snapshot(self.root, as_of=AS_OF)
        self.assertIsNone(snap["usage"])


class ActionsRecentTest(SnapshotBase):
    def test_newest_first_and_capped_at_50(self):
        lines = []
        for i in range(60):
            lines.append(json.dumps({"type": "retire", "domain": "d%02d.example" % i,
                                     "result": "applied", "applied_at": "2026-09-13T00:%02d:00Z" % i}))
        self.write("index/admin/actions.jsonl", "\n".join(lines) + "\n")
        snap = snapshot.build_snapshot(self.root, as_of=AS_OF)
        recent = snap["actions_recent"]
        self.assertEqual(len(recent), 50)                       # capped
        self.assertEqual(recent[0]["domain"], "d59.example")    # newest first
        self.assertEqual(recent[-1]["domain"], "d10.example")   # oldest of the last 50

    def test_empty_when_no_log(self):
        snap = snapshot.build_snapshot(self.root, as_of=AS_OF)
        self.assertEqual(snap["actions_recent"], [])


class ProposalsTest(SnapshotBase):
    def _proposal(self, name, header):
        self.write("proposals/" + name,
                   header + "patches:\n  - domain: x.example\n    field: reach\n"
                            "    evidence: >-\n      a block scalar the yaml loader cannot read\n")

    def test_pending_excludes_applied_and_reads_date(self):
        self._proposal("registry-2026-09-13.yml", "date: 2026-09-13\napplied: false\n")
        self._proposal("registry-2026-09-06.yml", "date: 2026-09-06\napplied: true\n")
        self._proposal("registry-2026-08-30.yml", "date: 2026-08-30\n")  # no flag -> pending
        snap = snapshot.build_snapshot(self.root, as_of=AS_OF)
        pending = snap["proposals_pending"]
        files = [p["file"] for p in pending]
        self.assertIn("proposals/registry-2026-09-13.yml", files)
        self.assertIn("proposals/registry-2026-08-30.yml", files)
        self.assertNotIn("proposals/registry-2026-09-06.yml", files)  # applied: true excluded
        # newest first
        self.assertEqual(pending[0]["date"], "2026-09-13")
        self.assertEqual(pending[0]["file"], "proposals/registry-2026-09-13.yml")

    def test_date_falls_back_to_filename(self):
        self._proposal("registry-2026-07-04.yml", "applied: false\n")  # no date line
        snap = snapshot.build_snapshot(self.root, as_of=AS_OF)
        p = [x for x in snap["proposals_pending"] if x["file"].endswith("registry-2026-07-04.yml")]
        self.assertEqual(len(p), 1)
        self.assertEqual(p[0]["date"], "2026-07-04")

    def test_non_registry_proposals_ignored(self):
        self.write("proposals/reader-model-2026-09-13.json", "{}\n")
        snap = snapshot.build_snapshot(self.root, as_of=AS_OF)
        self.assertEqual(snap["proposals_pending"], [])


class RealRepoTest(unittest.TestCase):
    def test_builds_against_the_live_repo(self):
        # Acceptance: snapshot builds against the real repo; usage is null (S1's fold.py not here).
        snap = snapshot.build_snapshot(REPO, as_of=AS_OF)
        self.assertGreater(len(snap["sources"]), 100)
        self.assertTrue(all("domain" in s and "last_event" in s for s in snap["sources"]))
        # head is a real sha in the repo checkout
        self.assertTrue(snap["head"] is None or len(snap["head"]) == 40)


if __name__ == "__main__":
    unittest.main()
