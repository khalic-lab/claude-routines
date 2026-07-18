"""Spec tests for the Phase-2 analytical plane (tools/plane/) and the two record-path
additions that feed it: the writer-supplied `entities` field (only-when-present, mirroring
affiliations) and the blank-headline URL backstop (the 2026-07-18 six-way
"{date}-{slug}-story" id collision).

Plane coverage is the PURE half (COPY/TSV/array/vector encoding, embedding decode, ledger
event scan, script assembly) — no live Postgres needed; the DB integration is exercised by
running sync.py against the real database, not by this suite.
"""
import argparse
import base64
import contextlib
import importlib.util
import io
import json
import os
import struct
import tempfile
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


plane = _load("_plane_sync", os.path.join(TOOLS, "plane", "sync.py"))


class PlanePureTest(unittest.TestCase):
    def test_tsv_escaping(self):
        self.assertEqual(plane.tsv(None), r"\N")
        self.assertEqual(plane.tsv("a\tb\nc\\d"), "a\\tb\\nc\\\\d")

    def test_pg_array_quoting(self):
        self.assertEqual(plane.pg_array([]), "{}")
        self.assertEqual(plane.pg_array(['a "quoted"', "back\\slash"]),
                         '{"a \\"quoted\\"","back\\\\slash"}')

    def test_decode_emb_roundtrip_f16_and_raw(self):
        floats = [0.5, -1.25, 0.0, 2.0]
        packed = base64.b64encode(struct.pack("<%de" % len(floats), *floats)).decode()
        out = plane.decode_emb({"emb": packed})
        self.assertEqual(out, floats)                       # exactly representable in f16
        self.assertEqual(plane.decode_emb({"embedding": [1.0, 2.0]}), [1.0, 2.0])
        self.assertIsNone(plane.decode_emb({}))
        self.assertIsNone(plane.decode_emb({"emb": "not-base64!!"}))

    def test_story_row_column_count_matches_copy(self):
        row = plane.story_row("st-abc", {"date": "2026-07-18", "stream": "news",
                                         "headline": "H", "entities": ["Iran"]})
        self.assertEqual(len(row.split("\t")), 24)          # must match COPY column list
        self.assertIn('{"Iran"}', row)

    def test_scan_events_dedupes_and_skips_garbage(self):
        root = tempfile.mkdtemp(prefix="plane-test-")
        os.makedirs(os.path.join(root, "index", "ledger"))
        with open(os.path.join(root, "index", "ledger", "2026-07-18.jsonl"), "w") as fh:
            fh.write(json.dumps({"ev": "publish", "id": "st-a", "edition": "2026-07-18-news",
                                 "ts": "2026-07-18T10:00:00Z"}) + "\n")
            fh.write(json.dumps({"ev": "publish", "id": "st-a", "edition": "2026-07-18-news",
                                 "ts": "2026-07-18T10:03:00Z"}) + "\n")   # retry -> one row, earliest ts
            fh.write("not json\n")
            fh.write(json.dumps({"ev": "feedback", "fb_id": "f1", "id": "st-a", "vote": 1,
                                 "ts": "2026-07-18T11:00:00Z"}) + "\n")
            fh.write(json.dumps({"ev": "feedback", "vote": 1}) + "\n")    # no fb_id -> skipped
        pubs, fb = plane.scan_events(root)
        self.assertEqual(len(pubs), 1)
        self.assertEqual(pubs[0]["ts"], "2026-07-18T10:00:00Z")
        self.assertEqual([f["fb_id"] for f in fb], ["f1"])

    def test_build_script_is_one_transaction_with_upserts(self):
        script = plane.build_script(
            {"st-a": {"date": "2026-07-18", "stream": "news", "headline": "H"}}, [], [], ".")
        self.assertIn("BEGIN;", script)
        self.assertIn("COMMIT;", script)
        self.assertEqual(script.count("ON CONFLICT"), 3)
        self.assertIn("CREATE EXTENSION IF NOT EXISTS vector", script)


class UrlHeadlineTest(unittest.TestCase):
    """The blank-headline backstop's derivation helper."""
    @classmethod
    def setUpClass(cls):
        cls.dedup = _load("_dedup_uh", os.path.join(TOOLS, "dedup", "dedup.py"))

    def test_derives_readable_tail(self):
        self.assertEqual(self.dedup.url_headline("https://huggingface.co/ATH-MaaS/OvisOCR2"),
                         "OvisOCR2")
        self.assertEqual(
            self.dedup.url_headline("https://acoup.blog/2026/07/18/collections-pre-modern-armies/"),
            "collections pre modern armies")
        self.assertEqual(self.dedup.url_headline("https://x.example/paper.pdf"), "paper")

    def test_distinct_urls_never_collide(self):
        urls = ["https://huggingface.co/ATH-MaaS/OvisOCR2",
                "https://huggingface.co/OpenMOSS-Team/MOSS-VL-Realtime",
                "https://www.quantamagazine.org/martin-picards-mitochondrial-theory-20260717/"]
        slugs = {self.dedup.slugify(self.dedup.url_headline(u)) for u in urls}
        self.assertEqual(len(slugs), 3)
        self.assertNotIn("story", slugs)

    def test_empty_inputs(self):
        self.assertEqual(self.dedup.url_headline(None), "")
        self.assertEqual(self.dedup.url_headline("https://example.com/"), "")


class RecordEntitiesAndBackstopTest(unittest.TestCase):
    """cmd_record end-to-end (offline, stubbed embedder — the convergence tests' harness):
    entities persist only-when-present; blank headlines get URL-derived identities."""

    def _run(self, stories):
        root = tempfile.mkdtemp(prefix="plane-record-")
        for d in (("index", "stories"), ("index", "ledger"), ("_posts",)):
            os.makedirs(os.path.join(root, *d))
        payload = os.path.join(root, "payload.json")
        with open(payload, "w") as fh:
            json.dump({"stories": stories}, fh)
        old = os.environ.get("REPO")
        os.environ["REPO"] = root
        try:
            mod = _load("_dedup_rec", os.path.join(TOOLS, "dedup", "dedup.py"))
        finally:
            if old is None:
                os.environ.pop("REPO", None)
            else:
                os.environ["REPO"] = old
        mod.embed = lambda texts, worker=None, token=None: [[0.01 * (i + 1)] * 1024 for i, _ in enumerate(texts)]
        args = argparse.Namespace(stories=payload, date="2026-07-18", slug="news",
                                  keep_days=40, worker=None, token=None)
        with contextlib.redirect_stdout(io.StringIO()):
            mod.cmd_record(args)
        idx = os.path.join(root, "index", "stories", "2026-07-18-news.jsonl")
        with open(idx) as fh:
            return [json.loads(l) for l in fh if l.strip()]

    def test_entities_only_when_present(self):
        recs = self._run([
            {"headline": "With entities", "summary": "s", "url": "https://a.example/1",
             "entities": ["Iran", " Strait of Hormuz ", ""]},
            {"headline": "Without entities", "summary": "s", "url": "https://b.example/2"},
        ])
        by_hl = {r["headline"]: r for r in recs}
        self.assertEqual(by_hl["With entities"]["entities"], ["Iran", "Strait of Hormuz"])
        self.assertNotIn("entities", by_hl["Without entities"])

    def test_blank_headlines_get_distinct_url_identities(self):
        recs = self._run([
            {"headline": "", "summary": "", "url": "https://huggingface.co/ATH-MaaS/OvisOCR2"},
            {"headline": "", "summary": "", "url": "https://huggingface.co/OpenMOSS-Team/MOSS-VL-Realtime"},
        ])
        ids = {r["id"] for r in recs}
        self.assertEqual(len(ids), 2, "distinct URLs must never share a legacy id")
        for r in recs:
            self.assertTrue(r["headline"], "headline must be derived, not blank")
            self.assertFalse(r["id"].endswith("-story"), r["id"])


if __name__ == "__main__":
    unittest.main()
