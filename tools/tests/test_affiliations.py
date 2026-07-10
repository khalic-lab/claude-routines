#!/usr/bin/env python3
"""Spec — the affiliation element (SPIKE-2026-07-10-affiliation-element).

Pins down three contracts in tools/dedup/dedup.py:

* parse_affiliations(line): the deterministic byline parser — institutions come from
  the LAST parenthetical after the first ' · ', skipping author-list fragments
  ('(incl. …)', '(305 authors)'), honouring the '(affiliation not listed)' sentinel,
  splitting on ';' only (',' qualifies within one name), stripping '+N more'.
* cmd_record: a writer-supplied `affiliations` list is persisted on the index record
  and flows into the ledger dual-write; the key is ABSENT when the payload has none
  (records from affiliation-less payloads stay byte-identical to the pre-affiliation
  era); on a within-edition re-record, prior affiliations survive a newer payload that
  omits them, and a newer non-empty list wins.
* cmd_affil_backfill: patches existing index records from post bylines by normalized
  URL — paper bylines only (news-prose parentheticals must NOT become affiliations),
  arXiv-version-insensitive, idempotent (second run leaves files byte-identical).

Run: python3 -m unittest tools.tests.test_affiliations -v
"""
import argparse
import contextlib
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

DATE = "2026-07-10"
SLUG = "ai-ml"


def _seeded_vec(key):
    seed = int(hashlib.sha1(key.encode("utf-8")).hexdigest(), 16) % (2 ** 32)
    rng = random.Random(seed)
    return [rng.uniform(-1.0, 1.0) for _ in range(1024)]


def _stub_embed(texts, worker=None, token=None):
    return [_seeded_vec(t) for t in texts]


def _load_module(path, name):
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
    with _env("REPO", repo_root):
        mod = _load_module(DEDUP_PATH, modname)
    mod.embed = _stub_embed
    return mod


def _new_skeleton():
    root = tempfile.mkdtemp(prefix="affil-")
    os.makedirs(os.path.join(root, "index", "stories"))
    os.makedirs(os.path.join(root, "index", "ledger"))
    os.makedirs(os.path.join(root, "_posts"))
    return root


def _run_record(root, modname, stories, date=DATE, slug=SLUG):
    payload = os.path.join(root, "final.json")
    with open(payload, "w", encoding="utf-8") as f:
        json.dump({"stories": stories}, f, ensure_ascii=False)
    mod = _load_dedup(root, modname)
    args = argparse.Namespace(stories=payload, date=date, slug=slug,
                              keep_days=40, worker=None, token=None)
    with contextlib.redirect_stdout(io.StringIO()):
        mod.cmd_record(args)
    return mod


def _index_records(root, date=DATE, slug=SLUG):
    path = os.path.join(root, "index", "stories", f"{date}-{slug}.jsonl")
    with open(path) as f:
        return [json.loads(ln) for ln in f if ln.strip()]


def _ledger_events(root):
    events = []
    ldir = os.path.join(root, "index", "ledger")
    for name in sorted(os.listdir(ldir)):
        with open(os.path.join(ldir, name)) as f:
            events.extend(json.loads(ln) for ln in f if ln.strip())
    return events


PAPER = {
    "headline": "Letting a safety monitor read a model's chain-of-thought backfires",
    "summary": "CoT monitoring approved more harmful actions, not fewer.",
    "url": "https://arxiv.org/abs/2607.08066",
    "tier": "T1", "tags": ["preprint"], "topics": ["ai-ml"], "importance": 2,
    "display_body": "Body prose.", "why": "Why prose.", "event_date": "2026-07-09",
}


class TestParseAffiliations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dedup = _load_module(DEDUP_PATH, "dedup_for_affil_parse")

    def parse(self, line):
        return self.dedup.parse_affiliations(line)

    def test_ai_ml_bullet_with_incl_fragment(self):
        # verbatim shape from _posts/2026-07-10-ai-ml.md — the incl.-fragment must be skipped
        line = ('- <a id="st-6036e87b80c1" class="st-a"></a>**Headline** — '
                "[arXiv:2607.08066](https://arxiv.org/abs/2607.08066) · "
                "J. Za, J. Bainiaksina et al. (incl. V. Krakovna) (LASR Labs; Google DeepMind) · `[preprint]`")
        self.assertEqual(self.parse(line), ["LASR Labs", "Google DeepMind"])

    def test_weekend_heading_style(self):
        line = ("**[arXiv:2607.01181](https://arxiv.org/abs/2607.01181)** · "
                "Mehul Damani, Isha Puri, Idan Shenfeld, Jacob Andreas (MIT) · `[preprint]`")
        self.assertEqual(self.parse(line), ["MIT"])

    def test_published_paper_byline(self):
        line = ("**[Nature](https://www.nature.com/articles/s41586-026-10815-x)** · "
                "Long Ju and colleagues (MIT) · published 2026-06-29")
        self.assertEqual(self.parse(line), ["MIT"])

    def test_sentinel_is_none(self):
        line = ("**[arXiv:2607.02431](https://arxiv.org/abs/2607.02431)** · "
                "Y. Xue, L. Xu, Z. Liu et al. (affiliation not listed) · `[preprint]`")
        self.assertIsNone(self.parse(line))

    def test_author_count_fragment_alone_is_none(self):
        line = ("**[arXiv:2606.05405](https://arxiv.org/abs/2606.05405)** · "
                "Yiyou Sun, Xinyang Han et al. (305 authors) · `[preprint]`")
        self.assertIsNone(self.parse(line))

    def test_no_parenthetical_is_none(self):
        line = ("**[arXiv:2606.05080](https://arxiv.org/abs/2606.05080)** · "
                "Zhangchen Xu, Junda Chen et al. · `[preprint]`")
        self.assertIsNone(self.parse(line))

    def test_no_middot_is_none(self):
        self.assertIsNone(self.parse("Plain prose with (a parenthetical) but no byline shape."))

    def test_paren_before_et_al_is_a_paper_name_not_an_affiliation(self):
        # verbatim shape from _posts/2026-06-20-weekend.md: the paper's short name stands in
        # for missing authors — affiliations only ever FOLLOW the author list
        line = ("**[arXiv:2606.20376](https://arxiv.org/abs/2606.20376)** · (CRAX) et al. · "
                "`[preprint]`")
        self.assertIsNone(self.parse(line))

    def test_single_line_bullet_prose_parenthetical_loses_to_byline_affiliation(self):
        # verbatim shape from _posts/2026-06-13-weekend.md: pre-redesign single-line bullets
        # carry prose AFTER the `[preprint]` tag; the affiliation before the tag must win
        line = ("- **Graphical causal reasoning** — "
                "**[arXiv:2606.13532](https://arxiv.org/abs/2606.13532)** · "
                "F. Chraim, D. Janzing, J. Evans (AWS) · `[preprint]`. Builds a causal graph. "
                "_Why it matters:_ interpretable RCA (you can see why it blamed a given "
                "component) is what engineers trust.")
        self.assertEqual(self.parse(line), ["AWS"])

    def test_author_annotation_fragment_is_none(self):
        line = ("**[arXiv:2606.25849](https://arxiv.org/abs/2606.25849)** (Problem 1061) · "
                "Eric Li (sole author, both) · `[preprint]`")
        self.assertIsNone(self.parse(line))

    def test_markdown_link_target_is_not_an_affiliation(self):
        # verbatim shape from _posts/2026-07-08-science.md — a magazine byline citing papers
        # as markdown links: the link's (url) parenthetical must never parse as an institution
        line = ("**[Quanta, 6 July 2026](https://www.quantamagazine.org/x/)** · reporting on "
                "Bostanci et al. ([arXiv:2511.09551](https://arxiv.org/abs/2511.09551), Nov 2025, "
                "STOC 2026) and Bostanci, Huang & Vaikuntanathan "
                "([arXiv:2602.09385](https://arxiv.org/abs/2602.09385), Feb 2026)")
        self.assertIsNone(self.parse(line))

    def test_comma_qualifies_within_one_name(self):
        line = ("- **H** — [arXiv:2607.08393](https://arxiv.org/abs/2607.08393) · "
                "L. Dai, Z. Rao et al. (HKUST, Guangzhou) · `[preprint]`")
        self.assertEqual(self.parse(line), ["HKUST, Guangzhou"])

    def test_semicolons_split_and_plus_n_more_stripped(self):
        line = ("- **H** — [arXiv:2607.08643](https://arxiv.org/abs/2607.08643) · "
                "Y. Shao et al. (Nanjing Univ. of Science & Technology; Chinese Academy of Sciences +2 more) "
                "· `[preprint]`")
        self.assertEqual(self.parse(line),
                         ["Nanjing Univ. of Science & Technology", "Chinese Academy of Sciences"])


class TestRecordAffiliations(unittest.TestCase):
    def setUp(self):
        self.root = _new_skeleton()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_writer_supplied_affiliations_persist_and_reach_ledger(self):
        story = dict(PAPER, affiliations=["LASR Labs", "Google DeepMind"])
        _run_record(self.root, "affil_rec_1", [story])
        [rec] = _index_records(self.root)
        self.assertEqual(rec["affiliations"], ["LASR Labs", "Google DeepMind"])
        seen = [e for e in _ledger_events(self.root) if e.get("ev") == "seen"]
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0]["story"]["affiliations"], ["LASR Labs", "Google DeepMind"])

    def test_key_absent_when_payload_has_none(self):
        _run_record(self.root, "affil_rec_2", [dict(PAPER)])
        [rec] = _index_records(self.root)
        self.assertNotIn("affiliations", rec)

    def test_reRecord_preserves_prior_when_newer_omits(self):
        _run_record(self.root, "affil_rec_3a", [dict(PAPER, affiliations=["LASR Labs"])])
        _run_record(self.root, "affil_rec_3b", [dict(PAPER)])  # converges on same url
        [rec] = _index_records(self.root)
        self.assertEqual(rec.get("affiliations"), ["LASR Labs"])

    def test_reRecord_newer_nonempty_wins(self):
        _run_record(self.root, "affil_rec_4a", [dict(PAPER, affiliations=["LASR Labs"])])
        _run_record(self.root, "affil_rec_4b",
                    [dict(PAPER, affiliations=["LASR Labs", "Google DeepMind"])])
        [rec] = _index_records(self.root)
        self.assertEqual(rec.get("affiliations"), ["LASR Labs", "Google DeepMind"])


POST_MD = """---
title: test
---

## Papers

- <a id="st-aaaaaaaaaaaa" class="st-a"></a>**A paper headline** — \
[arXiv:2607.07953](https://arxiv.org/abs/2607.07953v1) · T. Cerruti, T. Rieder et al. \
(ETH Zurich) · `[preprint]`

## World

- **A news headline.** The central bank (the SNB) held rates · \
[letemps.ch](https://www.letemps.ch/articles/snb-holds) — reported Thursday.
"""


class TestAffilBackfill(unittest.TestCase):
    def setUp(self):
        self.root = _new_skeleton()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        with open(os.path.join(self.root, "_posts", f"{DATE}-{SLUG}.md"), "w") as f:
            f.write(POST_MD)
        self.index_path = os.path.join(self.root, "index", "stories", f"{DATE}-{SLUG}.jsonl")
        records = [
            # url differs from the byline's by arXiv version suffix — must still join
            {"id": f"{DATE}-{SLUG}-a-paper-headline", "date": DATE, "stream": SLUG,
             "headline": "A paper headline", "summary": "s",
             "url": "https://arxiv.org/abs/2607.07953", "source_domain": "arxiv.org"},
            {"id": f"{DATE}-{SLUG}-a-news-headline", "date": DATE, "stream": SLUG,
             "headline": "A news headline", "summary": "s",
             "url": "https://www.letemps.ch/articles/snb-holds", "source_domain": "letemps.ch"},
        ]
        with open(self.index_path, "w") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def _run(self, modname):
        mod = _load_dedup(self.root, modname)
        with contextlib.redirect_stdout(io.StringIO()):
            mod.cmd_affil_backfill(argparse.Namespace())

    def test_patches_paper_record_by_normalized_url(self):
        self._run("affil_bf_1")
        recs = {r["headline"]: r for r in
                (json.loads(ln) for ln in open(self.index_path) if ln.strip())}
        self.assertEqual(recs["A paper headline"].get("affiliations"), ["ETH Zurich"])

    def test_news_prose_parenthetical_is_not_an_affiliation(self):
        self._run("affil_bf_2")
        recs = {r["headline"]: r for r in
                (json.loads(ln) for ln in open(self.index_path) if ln.strip())}
        self.assertNotIn("affiliations", recs["A news headline"])

    def test_idempotent_second_run_is_byte_identical(self):
        self._run("affil_bf_3a")
        first = open(self.index_path, "rb").read()
        self._run("affil_bf_3b")
        self.assertEqual(open(self.index_path, "rb").read(), first)


if __name__ == "__main__":
    unittest.main()
