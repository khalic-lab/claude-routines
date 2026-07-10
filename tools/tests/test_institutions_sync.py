#!/usr/bin/env python3
"""Spec — the institutions ledger (SPIKE-2026-07-10-affiliation-element §D4).

tools/sources/institutions.py `sync` folds index-record `affiliations` into
sources/institutions.yml. Contracts:

* per-EDITION bookkeeping: an edition already in meta.synced_editions is never recounted —
  a second sync the same day is a no-op (byte-identical file), while a second same-day
  edition recorded AFTER the first sync still gets counted by the next sync.
* only LIVE_STREAMS editions count (retired overview/cyber-papers affiliations stay out).
* entries accrue citations/streams/first_seen/last_cited; probation -> established at the
  registry's citation floor, with a lifecycle event.
* aliases fold variants into the canonical entry, including merging a pre-existing variant
  entry when the alias is added later (self-healing).
* names yamllite can't key (':' / leading '-') are skipped, never crash the step.

Run: python3 -m unittest tools.tests.test_institutions_sync -v
"""
import argparse
import contextlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
SOURCES_DIR = os.path.join(REPO_ROOT, "tools", "sources")

sys.path.insert(0, SOURCES_DIR)  # institutions.py does `import registry` (sibling convention)

_spec = importlib.util.spec_from_file_location("institutions_under_test",
                                               os.path.join(SOURCES_DIR, "institutions.py"))
institutions = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(institutions)
registry = institutions.registry


def _rec(date, stream, url, affs=None, headline="h"):
    r = {"id": f"{date}-{stream}-x", "date": date, "stream": stream, "headline": headline,
         "summary": "s", "url": url, "source_domain": "arxiv.org"}
    if affs is not None:
        r["affiliations"] = affs
    return r


class TestInstitutionsSync(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="instsync-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        os.makedirs(os.path.join(self.root, "index", "stories"))
        os.makedirs(os.path.join(self.root, "sources"))

    def _write_index(self, date, slug, records):
        path = os.path.join(self.root, "index", "stories", f"{date}-{slug}.jsonl")
        with open(path, "w") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def _sync(self):
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            institutions.cmd_sync(argparse.Namespace(root=self.root))
        return buf.getvalue()

    def _load(self):
        with open(os.path.join(self.root, "sources", "institutions.yml")) as f:
            return registry.yaml_load(f.read())

    def _yml_bytes(self):
        return open(os.path.join(self.root, "sources", "institutions.yml"), "rb").read()

    def test_bootstrap_accrual_and_fields(self):
        self._write_index("2026-07-10", "ai-ml", [
            _rec("2026-07-10", "ai-ml", "https://arxiv.org/abs/1", ["MIT", "CERN"]),
            _rec("2026-07-10", "ai-ml", "https://arxiv.org/abs/2", ["MIT"]),
            _rec("2026-07-10", "ai-ml", "https://arxiv.org/abs/3"),  # no affiliations: ignored
        ])
        self._sync()
        data = self._load()
        mit = data["institutions"]["MIT"]
        self.assertEqual(mit["citations"], 2)
        self.assertEqual(mit["streams"], ["ai-ml"])
        self.assertEqual(mit["first_seen"], "2026-07-10")
        self.assertEqual(mit["last_cited"], "2026-07-10")
        self.assertEqual(mit["status"], "probation")
        self.assertEqual(data["institutions"]["CERN"]["citations"], 1)
        self.assertIn("2026-07-10-ai-ml", data["meta"]["synced_editions"])

    def test_second_sync_same_day_is_noop_but_new_edition_counts(self):
        self._write_index("2026-07-10", "ai-ml",
                          [_rec("2026-07-10", "ai-ml", "https://arxiv.org/abs/1", ["MIT"])])
        self._sync()
        first = self._yml_bytes()
        self._sync()                                     # same editions -> byte-identical
        self.assertEqual(self._yml_bytes(), first)
        # a SECOND same-day edition (science) recorded after the first sync
        self._write_index("2026-07-10", "science",
                          [_rec("2026-07-10", "science", "https://arxiv.org/abs/9", ["MIT"])])
        self._sync()
        mit = self._load()["institutions"]["MIT"]
        self.assertEqual(mit["citations"], 2)
        self.assertEqual(mit["streams"], ["ai-ml", "science"])

    def test_retired_streams_do_not_count(self):
        self._write_index("2026-06-19", "cyber-papers",
                          [_rec("2026-06-19", "cyber-papers", "https://arxiv.org/abs/1", ["MIT"])])
        self._sync()
        self.assertEqual(self._load()["institutions"], {})

    def test_promotion_at_citation_floor(self):
        recs = [_rec("2026-07-10", "ai-ml", f"https://arxiv.org/abs/{i}", ["ETH Zürich"])
                for i in range(registry.ESTABLISHED_MIN_CITATIONS)]
        self._write_index("2026-07-10", "ai-ml", recs)
        self._sync()
        e = self._load()["institutions"]["ETH Zürich"]
        self.assertEqual(e["status"], "established")
        self.assertEqual(e["lifecycle"][-1]["event"], "promoted")

    def test_alias_folds_variant_and_merges_preexisting_entry(self):
        # day 1: the full legal name accrues as its own entry
        self._write_index("2026-07-09", "ai-ml",
                          [_rec("2026-07-09", "ai-ml", "https://arxiv.org/abs/1",
                                ["Massachusetts Institute of Technology"])])
        self._sync()
        # the human adds the alias afterwards
        path = os.path.join(self.root, "sources", "institutions.yml")
        data = self._load()
        data["aliases"] = {"Massachusetts Institute of Technology": "MIT"}
        with open(path, "w") as f:
            f.write(registry.yaml_dump(data))
        # day 2: a new edition cites the short name
        self._write_index("2026-07-10", "ai-ml",
                          [_rec("2026-07-10", "ai-ml", "https://arxiv.org/abs/2", ["MIT"])])
        self._sync()
        inst = self._load()["institutions"]
        self.assertNotIn("Massachusetts Institute of Technology", inst)
        self.assertEqual(inst["MIT"]["citations"], 2)
        self.assertEqual(inst["MIT"]["first_seen"], "2026-07-09")
        self.assertEqual(inst["MIT"]["last_cited"], "2026-07-10")

    def test_unkeyable_names_are_skipped_not_fatal(self):
        self._write_index("2026-07-10", "ai-ml",
                          [_rec("2026-07-10", "ai-ml", "https://arxiv.org/abs/1",
                                ["Weird: Name", "- dashy", "MIT"])])
        self._sync()
        inst = self._load()["institutions"]
        self.assertEqual(sorted(inst), ["MIT"])


PARTIAL_WITH_MARKERS = """**Byline format law** blah.

**Canonical names** — intro line:
<!-- canonical-names:begin — GENERATED; run sync-prompts -->
<!-- canonical-names:end -->

**Anti-halo guard:** blah.
"""


class TestSyncPrompts(unittest.TestCase):
    """sync-prompts mirrors the ledger's aliases: map into the shared prompt partial."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="instprompts-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        os.makedirs(os.path.join(self.root, "sources"))
        os.makedirs(os.path.join(self.root, "routines", "_shared"))
        self.partial = os.path.join(self.root, "routines", "_shared", "affiliations.md")
        with open(self.partial, "w") as f:
            f.write(PARTIAL_WITH_MARKERS)
        with open(os.path.join(self.root, "sources", "institutions.yml"), "w") as f:
            f.write(registry.yaml_dump({
                "meta": {"synced_editions": []},
                "aliases": {"DeepMind": "Google DeepMind", "FAIR": "Meta AI",
                            "Meta FAIR": "Meta AI"},
                "institutions": {}}))

    def _run(self, check=False):
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            institutions.cmd_sync_prompts(argparse.Namespace(root=self.root, check=check))
        return buf.getvalue()

    def test_block_generated_grouped_and_idempotent(self):
        self._run()
        text = open(self.partial).read()
        self.assertIn("- `DeepMind` → **Google DeepMind**", text)
        self.assertIn("- `FAIR` / `Meta FAIR` → **Meta AI**", text)   # variants grouped
        self.assertIn("**Anti-halo guard:** blah.", text)             # rest untouched
        first = open(self.partial, "rb").read()
        self._run()
        self.assertEqual(open(self.partial, "rb").read(), first)      # idempotent

    def test_check_mode_flags_drift(self):
        self._run()
        out = self._run(check=True)
        self.assertIn("OK", out)
        # hand-edit the generated block -> drift
        text = open(self.partial).read().replace("**Google DeepMind**", "**DeepMind Inc**")
        with open(self.partial, "w") as f:
            f.write(text)
        with self.assertRaises(SystemExit):
            self._run(check=True)

    def test_missing_markers_is_a_loud_error(self):
        with open(self.partial, "w") as f:
            f.write("no markers here\n")
        with self.assertRaises(ValueError):
            self._run()

    def test_committed_repo_partial_matches_committed_ledger(self):
        """The real drift guard: the checked-in partial must always mirror the checked-in
        aliases map (same contract as `assemble.py check` for the generated prompts)."""
        with contextlib.redirect_stdout(io.StringIO()):
            institutions.cmd_sync_prompts(argparse.Namespace(root=REPO_ROOT, check=True))


if __name__ == "__main__":
    unittest.main()
