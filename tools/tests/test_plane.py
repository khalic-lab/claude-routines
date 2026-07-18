"""Spec tests for the Phase-2 analytical plane (tools/plane/query.py — SERVERLESS: the ledger
is the database, folded in-process; no Postgres, no sync, no state) and the two record-path
additions that feed it: the writer-supplied `entities` field (only-when-present, mirroring
affiliations) and the blank-headline URL backstop (the 2026-07-18 six-way
"{date}-{slug}-story" id collision).
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


plane = _load("_plane_query", os.path.join(TOOLS, "plane", "query.py"))


def _c(sid, vec, **rec):
    import math
    norm = math.sqrt(sum(x * x for x in vec)) if vec else None
    return {"sid": sid, "rec": rec, "vec": vec or None, "norm": norm or None}


class PlanePureTest(unittest.TestCase):
    def test_decode_emb_roundtrip_f16_and_raw(self):
        floats = [0.5, -1.25, 0.0, 2.0]
        packed = base64.b64encode(struct.pack("<%de" % len(floats), *floats)).decode()
        self.assertEqual(plane.decode_emb({"emb": packed}), floats)  # exactly representable in f16
        self.assertEqual(plane.decode_emb({"embedding": [1.0, 2.0]}), [1.0, 2.0])
        self.assertIsNone(plane.decode_emb({}))
        self.assertIsNone(plane.decode_emb({"emb": "not-base64!!"}))

    def test_cosine_rank_orders_and_excludes(self):
        corpus = [
            _c("st-close", [1.0, 0.1, 0.0], headline="close"),
            _c("st-far", [-1.0, 0.5, 0.0], headline="far"),
            _c("st-mid", [0.5, 0.5, 0.0], headline="mid"),
            _c("st-novec", None, headline="no vector"),
        ]
        hits = plane.cosine_rank(corpus, [1.0, 0.0, 0.0], k=10)
        self.assertEqual([c["sid"] for _, c in hits], ["st-close", "st-mid", "st-far"])
        self.assertAlmostEqual(hits[0][0], 0.995, places=2)
        hits = plane.cosine_rank(corpus, [1.0, 0.0, 0.0], k=10, exclude_sids={"st-close"})
        self.assertEqual(hits[0][1]["sid"], "st-mid")

    def test_find_story_by_sid_url_and_legacy_id(self):
        corpus = [_c("st-a", [1.0], url="https://x.example/a",
                     legacy_ids=["2026-07-18-news-alpha"])]
        for key in ("st-a", "https://x.example/a", "2026-07-18-news-alpha"):
            self.assertIs(plane.find_story(corpus, key), corpus[0], key)
        self.assertIsNone(plane.find_story(corpus, "nope"))

    def test_stats_counts_folded_votes_not_dict_len(self):
        corpus = [
            _c("st-a", [1.0], date="2026-07-01", thread_id="t1",
               feedback={"up": 2, "down": 1, "last_reason": None}),
            _c("st-b", [1.0], date="2026-07-02", thread_id="t1",
               feedback={"up": 0, "down": 0, "last_reason": None}),  # the 3-per-story trap
        ]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            plane.cmd_stats(corpus, None)
        row = buf.getvalue().splitlines()[2].split()
        self.assertEqual(row[:4], ["2", "2", "1", "3"])  # stories, vectors, threads>1, votes

    def test_entities_groupby(self):
        corpus = [
            _c("st-a", [1.0], date="2026-07-01", stream="news", entities=["Iran", "CAS"]),
            _c("st-b", [1.0], date="2026-07-10", stream="sports", entities=["CAS"]),
        ]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            plane.cmd_entities(corpus, argparse.Namespace(days=36500))
        out = buf.getvalue()
        lines = [l for l in out.splitlines() if l.startswith("CAS")]
        self.assertEqual(len(lines), 1)
        self.assertIn("news/sports", lines[0])
        self.assertIn("2", lines[0].split())


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
