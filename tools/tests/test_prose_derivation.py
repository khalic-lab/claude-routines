#!/usr/bin/env python3
"""Spec tests for post-faithful prose: the parser forms and the record-time derivation.

Both are the 2026-07-28 fix for an owner-reported front-page bug: a "Why it matters" that
OPENED on a quoted phrase read as if its first words were cropped, because the ai-ml writer's
Step C payload — the writer re-TYPING its own published prose into JSON — had stripped every
double quote, and the feed prefers the recorded copy. The fix removes the transcription from
the trust chain instead of arbitrating copies:

- the parser learns the real printed forms (hard-wrapped labelled whys, the news form's
  INLINE why, trailing citation furniture), so a post parse is complete and byte-faithful;
- `cmd_record` derives display_body/why FROM THE POST via that parser, demoting the payload
  copy to a fallback for a parser miss, a failed URL join, or prose the post never prints
  (the Weekend headline bullets carry no why).

The quote assertions below are the owner's actual bug; the em-dash/diacritic ones are the
same disease as seen in sports records. If one of these fails, the front page is again one
hand-copy away from printing drifted prose.
"""
import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
import random
import shutil
import tempfile
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
FEED_PATH = os.path.join(REPO_ROOT, "tools", "build_stories_feed.py")
DEDUP_PATH = os.path.join(REPO_ROOT, "tools", "dedup", "dedup.py")


def _load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _stub_embed(texts, worker=None, token=None):
    out = []
    for t in texts:
        seed = int(hashlib.sha1(t.encode("utf-8")).hexdigest(), 16) % (2 ** 32)
        rng = random.Random(seed)
        out.append([rng.uniform(-1.0, 1.0) for _ in range(1024)])
    return out


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


def _skeleton():
    root = tempfile.mkdtemp(prefix="prosederive-")
    os.makedirs(os.path.join(root, "index", "stories"))
    os.makedirs(os.path.join(root, "index", "ledger"))
    os.makedirs(os.path.join(root, "_posts"))
    return root


def _record(root, modname, stories, date, slug):
    payload = os.path.join(root, "final.json")
    with open(payload, "w") as f:
        json.dump({"stories": stories}, f)
    mod = _load_dedup(root, modname)
    args = argparse.Namespace(stories=payload, date=date, slug=slug,
                              keep_days=40, worker=None, token=None)
    mod.cmd_record(args)
    path = os.path.join(root, "index", "stories", f"{date}-{slug}.jsonl")
    with open(path) as f:
        return [json.loads(ln) for ln in f]


FRONT = "---\ntitle: T\n---\n\n# T\n\n## Section\n\n"


# --------------------------------------------------------------------------- #
# parser forms
# --------------------------------------------------------------------------- #
class ParserFormTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.feed = _load_module(FEED_PATH, "feed_prosederive")

    def _one(self, md):
        stories = self.feed.parse_post(md)
        self.assertEqual(len(stories), 1, stories)
        return stories[0]

    def test_science_hard_wrapped_why_joins_to_the_full_paragraph(self):
        """A line is not a paragraph: the science form hard-wraps its `*Why it matters:*`,
        and the pre-2026-07-28 parser truncated it at the first line break."""
        md = FRONT + (
            "### A trapped-atom result {#st-aaaaaaaaaaaa}\n"
            "**[arXiv:2607.00001](https://arxiv.org/abs/2607.00001)** · A. Author et al. "
            "(Somewhere) · `[preprint]`\n"
            "The apparatus holds single atoms for two hours while preserving full optical\n"
            "access, without a complex cryogenic shroud.\n"
            "*Why it matters:* longer trap lifetimes translate directly into more qubits\n"
            "held stably at once, so this is a scaling result as much as a records one.\n"
        )
        s = self._one(md)
        self.assertEqual(
            s["why"],
            "longer trap lifetimes translate directly into more qubits held stably at "
            "once, so this is a scaling result as much as a records one.")
        self.assertIn("without a complex cryogenic shroud", s["body"])
        self.assertNotIn("arXiv", s["display_body"])         # byline is meta, not prose
        self.assertNotIn("Why it matters", s["display_body"])

    def test_news_inline_why_splits_and_keeps_its_quotes(self):
        """The news form's why is a plain `Why it matters:` sentence INSIDE the bullet
        paragraph, trailed by dated citation links. The quoted phrase opening the why is
        the owner-reported bug: it must survive to the byte."""
        md = FRONT + (
            "- <a id=\"st-bbbbbbbbbbbb\" class=\"st-a\"></a>**The lede sentence states "
            "what happened.** The prose continues with detail — and a “quoted "
            "term”. Why it matters: \"the model is well-aligned\" ultimately rests "
            "on the judge — not on surface features. "
            "[SRF, 20 Jul 2026](https://example.test/a); oil: "
            "[Le Temps, 20 Jul 2026](https://example.test/b) [ongoing since 2026-06-20]\n"
        )
        s = self._one(md)
        self.assertEqual(
            s["why"],
            "\"the model is well-aligned\" ultimately rests on the judge — not on "
            "surface features.")
        self.assertNotIn("SRF", s["why"])
        self.assertNotIn("Why it matters", s["body"])
        self.assertNotIn("SRF", s["body"])
        self.assertTrue(s["display_body"].startswith(
            "The lede sentence states what happened. The prose continues"))
        self.assertIn("“quoted term”", s["display_body"])
        self.assertNotIn("Why it matters", s["display_body"])

    def test_bold_inline_why_of_the_july_14_era_also_splits(self):
        md = FRONT + (
            "- <a id=\"st-cccccccccccc\" class=\"st-a\"></a>**A lede.** Prose body here "
            "with enough length to clear the body floor comfortably. "
            "**Why it matters:** the inline label wore bold once.\n"
        )
        s = self._one(md)
        self.assertEqual(s["why"], "the inline label wore bold once.")
        self.assertNotIn("Why it matters", s["display_body"])

    def test_paper_heading_form_display_excludes_the_bold_title(self):
        """A bold bullet whose remainder is a citation tail is the HEADING form: the bold
        is a title, the paragraph lives below on its own, and prepending the title would
        print it twice on the card (the record headline is cut from the same cloth)."""
        md = FRONT + (
            "- <a id=\"st-dddddddddddd\" class=\"st-a\"></a>**A long descriptive paper "
            "title stating the finding** — [arXiv:2607.00002]"
            "(https://arxiv.org/abs/2607.00002) · B. Author et al. (Lab) · `[preprint]`\n"
            "\n"
            "  Measuring \"counterfactual memorization\" the authors show the judge "
            "leans on length and compliance rather than quality.\n"
            "\n"
            "  **Why it matters:** reward scores are treated as ground truth. "
            "[[Scorecard](https://example.test/c)] · [[Leaderboard]"
            "(https://example.test/d)]\n"
        )
        s = self._one(md)
        self.assertTrue(s["display_body"].startswith("Measuring \"counterfactual"))
        self.assertNotIn("descriptive paper title", s["display_body"])
        self.assertEqual(s["why"], "reward scores are treated as ground truth.")
        self.assertNotIn("Scorecard", s["why"])

    def test_sentence_form_display_prepends_the_lede_with_its_outer_period(self):
        md = FRONT + (
            "- <a id=\"st-eeeeeeeeeeee\" class=\"st-a\"></a>**A lede whose period sits "
            "outside the bold**. The remainder carries on with plenty of prose to pass "
            "the length floor. ([SRF, 2026-07-20](https://example.test/e))\n"
        )
        s = self._one(md)
        self.assertTrue(s["display_body"].startswith(
            "A lede whose period sits outside the bold. The remainder"))

    def test_undated_prose_link_at_paragraph_end_is_not_citation_furniture(self):
        """The trailing-citation stripper keys on a DATE in the link text — a load-bearing
        prose link at the end of a sentence must survive."""
        md = FRONT + (
            "- <a id=\"st-ffffffffffff\" class=\"st-a\"></a>**A lede.** The vendor "
            "published details of the incident and released "
            "[the full report](https://example.test/f).\n"
        )
        s = self._one(md)
        self.assertIn("released the full report", s["display_body"])

    def test_middot_two_source_tail_is_furniture_not_a_byline(self):
        """THE NEWS FORM'S TWO-SOURCE TAIL IS THE SHAPE THAT BROKE THIS. A bullet closing on
        `[Src, 4 Aug 2026](u) · [Other, 3 Aug 2026](u)` planted a ` · ` and a source-domain
        token into ordinary prose, so `_is_meta` read the whole remainder as a paper byline:
        `_is_title` fired and the lede never reached `display_body`, and `_split_inline_why`
        skipped the paragraph so `why` came out empty with `Why it matters:` glued into the
        body instead. Meta-ness must be judged with the trailing run REMOVED."""
        md = FRONT + (
            "- <a id=\"st-919191919191\" class=\"st-a\"></a>**A coalition of 25 US states "
            "sued the administration on Monday (3 August) over its latest tariffs.** The "
            "suit, filed in the US Court of International Trade, targets the double-digit "
            "tariffs Washington imposed last month on dozens of trading partners. "
            "**Why it matters:** the case tests whether the trade-war architecture "
            "survives a Supreme Court defeat. "
            "[Al Jazeera, 4 Aug 2026](https://www.aljazeera.com/economy/x) · "
            "[NY State of Politics, 3 Aug 2026](https://nystateofpolitics.com/y) "
            "`[new source]` `[via snippet]`\n"
        )
        s = self._one(md)
        self.assertTrue(s["display_body"].startswith(
            "A coalition of 25 US states sued the administration on Monday (3 August) "
            "over its latest tariffs. The suit, filed in the US Court of International "
            "Trade"), s["display_body"])
        self.assertEqual(
            s["why"],
            "the case tests whether the trade-war architecture survives a Supreme "
            "Court defeat.")
        self.assertNotIn("Why it matters", s["display_body"])
        self.assertNotIn("new source", s["display_body"])
        self.assertNotIn("Al Jazeera", s["display_body"])
        self.assertNotIn("NY State of Politics", s["why"])

    def test_new_source_tag_on_a_non_last_citation_does_not_halt_the_strip(self):
        """`[new source]` is a mandated writer tag; when `_TAG_RE` did not list it the glue
        walk broke at the NON-LAST citation, cut only the tail, and unbalanced the citation
        paren — which also disabled `clean_body`'s paren rescue, so the output was worse than
        with no stripper at all. The last-position variant passes by accident via that rescue,
        so pinning only it would rubber-stamp."""
        md = FRONT + (
            "- <a id=\"st-a1a1a1a1a1a1\" class=\"st-a\"></a>**A lede.** Prose body here "
            "with enough length to clear the body floor comfortably. Why it matters: a "
            "collapse would reopen a war. "
            "([NBC News, 6 Aug 2026](https://example.test/i) [new source]; "
            "[Al Jazeera, 6 Aug 2026](https://example.test/j))\n"
        )
        s = self._one(md)
        self.assertEqual(s["why"], "a collapse would reopen a war.")
        self.assertNotIn("NBC News", s["why"])
        self.assertNotIn("new source", s["why"])
        self.assertNotIn("(", s["why"])

    def test_a_date_after_the_link_is_citation_furniture_too(self):
        """The ai-ml form puts the date OUTSIDE the link text — `— [Ars Technica](u),
        2026-07-29` — which the date-inside-brackets pattern never matched, so nothing was
        cut and the card printed the source line as the last words of the story."""
        md = FRONT + (
            "- <a id=\"st-b2b2b2b2b2b2\" class=\"st-a\"></a>**Anthropic's bug-finding "
            "model is surfacing SharePoint flaws.** Vulnerability reports climbed sharply "
            "last month alone, with engineers in \"a mad dash\" to close the gap. "
            "`[single-source]` — [Ars Technica](https://arstechnica.com/x), 2026-07-29\n"
        )
        s = self._one(md)
        self.assertTrue(s["display_body"].endswith("to close the gap."),
                        s["display_body"])
        self.assertNotIn("Ars Technica", s["display_body"])
        self.assertNotIn("2026-07-29", s["display_body"])

    def test_a_date_after_the_link_strips_a_whole_tagged_run(self):
        """Same form, two sources, `[new source]` on the first — both halves of the fix have
        to hold at once or the run survives from the tag onward."""
        md = FRONT + (
            "- <a id=\"st-c4c4c4c4c4c4\" class=\"st-a\"></a>**The Model Context Protocol "
            "shipped its biggest update.** The spec gained a registry and stricter auth, "
            "the largest change since MCP launched over a year ago. "
            "— [MCP blog](https://modelcontextprotocol.io/x), 2026-07-28 [new source] · "
            "[Ars Technica](https://arstechnica.com/y), 2026-07-30\n"
        )
        s = self._one(md)
        self.assertTrue(s["display_body"].endswith("since MCP launched over a year ago."),
                        s["display_body"])
        self.assertNotIn("new source", s["display_body"])
        self.assertNotIn("MCP blog", s["display_body"])

    def test_an_all_meta_paper_block_yields_no_body_never_the_byline(self):
        """`_is_meta` fires on any "et al", and science prose routinely names one — so when
        the byline AND the prose both read as meta, `_pick_body_para`'s relaxed second pass
        (which had dropped the meta skip) returned the CITATION LINE as the body. Empty is
        the honest answer: it is what fires `cmd_record`'s documented payload fallback."""
        md = FRONT + (
            "### A CRISPR enzyme programmed to shred DNA only inside cancer cells "
            "{#st-c3c3c3c3c3c3}\n"
            "**[Nature](https://example.test/m)** · J. Zeng, Z. Cheng et al. (Gladstone "
            "Institutes; UCSF) · published 8 July 2026\n"
            "Many cancers are driven by mutations in tumour-suppressor genes that are "
            "considered \"undruggable\". Zeng et al., with a companion paper by Scholz "
            "et al., repurpose Cas12a2, a bacterial CRISPR nuclease that chews up "
            "nearby DNA once it recognizes a target RNA.\n"
            "*Why it matters:* it reframes an \"undruggable\" mutation as a targeting "
            "signal rather than a target.\n"
        )
        s = self._one(md)
        self.assertEqual(s["display_body"], "")
        self.assertEqual(s["body"], "")
        self.assertEqual(s["why"], "it reframes an \"undruggable\" mutation as a "
                                   "targeting signal rather than a target.")

    def test_a_hard_wrapped_all_meta_paper_block_never_returns_the_byline(self):
        """Same block hard-wrapped. `_is_meta` is called per LINE by `_paragraphs`, so a
        wrapped block splits differently and can still yield prose — what must NEVER come
        back is the citation byline, which is the failure the relaxed pass produced."""
        md = FRONT + (
            "### A CRISPR enzyme programmed to shred DNA only inside cancer cells "
            "{#st-d5d5d5d5d5d5}\n"
            "**[Nature](https://example.test/n)** · J. Zeng, Z. Cheng et al. (Gladstone "
            "Institutes; UCSF) · published 8 July 2026\n"
            "Many cancers are driven by mutations in tumour-suppressor genes that are\n"
            "considered \"undruggable\". Zeng et al., with a companion paper by Scholz et\n"
            "al., repurpose Cas12a2, a bacterial CRISPR nuclease that chews up nearby DNA\n"
            "once it recognizes a target RNA.\n"
            "*Why it matters:* it reframes an \"undruggable\" mutation as a targeting "
            "signal rather than a target.\n"
        )
        s = self._one(md)
        self.assertNotIn("Gladstone", s["display_body"])
        self.assertNotIn("published 8 July 2026", s["display_body"])
        self.assertNotIn("Gladstone", s["body"])


# --------------------------------------------------------------------------- #
# record-time derivation
# --------------------------------------------------------------------------- #
POST_URL = "https://example.test/story-one"
NEWS_POST = FRONT + (
    "- <a id=\"st-121212121212\" class=\"st-a\"></a>**The lede sentence.** Prose with a "
    "\"quoted phrase\" and an em-dash — intact. Why it matters: \"opening quote\" carries "
    "the point. [SRF, 20 Jul 2026](" + POST_URL + ")\n"
)
DRIFTED = {  # the payload hand-copy, quote-stripped and dash-flattened like the real drift
    "headline": "Curated headline", "summary": "s", "url": POST_URL,
    "display_body": "The lede sentence. Prose with a quoted phrase and an em-dash - intact.",
    "why": "opening quote carries the point.",
    "topics": ["world"], "importance": 2,
}


class RecordDerivationTests(unittest.TestCase):
    def setUp(self):
        self.root = _skeleton()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_post_derived_prose_beats_the_drifted_payload_copy(self):
        with open(os.path.join(self.root, "_posts", "2026-07-28-news.md"), "w") as f:
            f.write(NEWS_POST)
        recs = _record(self.root, f"dedup_{id(self)}_a", [dict(DRIFTED)],
                       "2026-07-28", "news")
        self.assertEqual(len(recs), 1)
        self.assertEqual(
            recs[0]["display_body"],
            "The lede sentence. Prose with a \"quoted phrase\" and an em-dash — intact.")
        self.assertEqual(recs[0]["why"], "\"opening quote\" carries the point.")
        # the ledger publish event carries the same derived fields
        ledger = os.path.join(self.root, "index", "ledger")
        events = []
        for name in os.listdir(ledger):
            with open(os.path.join(ledger, name)) as f:
                events += [json.loads(ln) for ln in f if ln.strip()]
        pubs = [e for e in events if e.get("ev") == "publish"]
        self.assertEqual(len(pubs), 1)
        self.assertEqual(pubs[0]["fields"]["why"], "\"opening quote\" carries the point.")

    def test_without_a_post_on_disk_the_payload_records_verbatim(self):
        recs = _record(self.root, f"dedup_{id(self)}_b", [dict(DRIFTED)],
                       "2026-07-28", "news")
        self.assertEqual(recs[0]["display_body"], DRIFTED["display_body"])
        self.assertEqual(recs[0]["why"], DRIFTED["why"])

    def test_a_failed_url_join_keeps_the_payload_copy(self):
        with open(os.path.join(self.root, "_posts", "2026-07-28-news.md"), "w") as f:
            f.write(NEWS_POST)
        stray = dict(DRIFTED, url="https://example.test/not-in-the-post")
        recs = _record(self.root, f"dedup_{id(self)}_c", [stray], "2026-07-28", "news")
        self.assertEqual(recs[0]["why"], DRIFTED["why"])

    def test_prose_the_post_never_prints_falls_back_to_the_payload(self):
        """The Weekend headline bullets carry no printed why — the Step C payload is that
        field's only carrier, and derivation must not blank it."""
        post = FRONT + (
            "- <a id=\"st-343434343434\" class=\"st-a\"></a>**A weekend recap lede.** "
            "Prose without any why sentence at all. "
            "([SRF, 2026-07-18](" + POST_URL + "))\n"
        )
        with open(os.path.join(self.root, "_posts", "2026-07-25-weekend.md"), "w") as f:
            f.write(post)
        recs = _record(self.root, f"dedup_{id(self)}_d", [dict(DRIFTED)],
                       "2026-07-25", "weekend")
        self.assertEqual(recs[0]["why"], DRIFTED["why"])       # payload fallback
        self.assertTrue(recs[0]["display_body"].startswith(
            "A weekend recap lede. Prose without any why"))    # derivation still fires

    def test_an_all_meta_paper_block_keeps_the_writer_payload(self):
        """The other end of the `_pick_body_para` fix, through the live path: an 86-char
        citation byline was beating 769 characters of authored prose, because `cmd_record`
        prefers any NON-EMPTY derivation and the relaxed pass always produced one. It must
        derive nothing here so the payload copy — and the ledger event cut from it — keeps
        the prose the brief actually printed."""
        paper_url = "https://example.test/crispr"
        post = FRONT + (
            "### A CRISPR enzyme programmed to shred DNA only inside cancer cells "
            "{#st-565656565656}\n"
            "**[Nature](" + paper_url + ")** · J. Zeng, Z. Cheng et al. (Gladstone "
            "Institutes; UCSF) · published 8 July 2026\n"
            "Many cancers are driven by mutations in tumour-suppressor genes that are "
            "considered \"undruggable\". Zeng et al., with a companion paper by Scholz "
            "et al., repurpose Cas12a2, a bacterial CRISPR nuclease.\n"
            "*Why it matters:* it reframes an \"undruggable\" mutation as a targeting "
            "signal.\n"
        )
        with open(os.path.join(self.root, "_posts", "2026-07-15-science.md"), "w") as f:
            f.write(post)
        authored = ("Many cancers are driven by mutations in tumour-suppressor genes "
                    "that are considered \"undruggable\".")
        payload = dict(DRIFTED, url=paper_url, display_body=authored,
                       why="it reframes the mutation as a targeting signal.")
        recs = _record(self.root, f"dedup_{id(self)}_e", [payload],
                       "2026-07-15", "science")
        self.assertEqual(recs[0]["display_body"], authored)
        self.assertNotIn("Gladstone", recs[0]["display_body"])
        ledger = os.path.join(self.root, "index", "ledger")
        events = []
        for name in os.listdir(ledger):
            with open(os.path.join(ledger, name)) as f:
                events += [json.loads(ln) for ln in f if ln.strip()]
        pubs = [e for e in events if e.get("ev") == "publish"]
        self.assertEqual(pubs[0]["fields"]["display_body"], authored)


if __name__ == "__main__":
    unittest.main()
