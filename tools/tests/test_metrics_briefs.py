"""Spec tests for metrics.py's computed brief-text dimensions ("briefs" key,
added 2026-07-18): B aggregator leakage, D section vitality, F single-source
rate, G tag counts, H weekend paper balance, K footer fetch ratios + feeds-hit
aggregation (BOTH the legacy hand-written and the new footer.py-computed
formats), L word-count means incl. previous week. These replace the evaluator's
hand-counting -- the schema here is the contract the evaluator prompt reads.
"""
import importlib.util
import os
import subprocess
import tempfile
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location(
    "_metrics_b", os.path.join(TOOLS, "evaluator", "metrics.py"))
metrics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metrics)

NEWS_0714 = """---
title: n
---

## 🇨🇭 Switzerland & Vaud

- **Alpha.** Text. [Src](https://srf.ch/a) [single-source]
- **Beta.** Text [discussion](https://reddit.com/r/x) here. [Src](https://letemps.ch/b)

## 🌍 World

- **Gamma.** Text. [Src](https://apnews.com/c) [preprint]

## Dead section

## Coverage footer
<!-- telemetry
- Direct fetches: 5 | via-snippet citations: 1
- Word count: ~1,200 (body, excl. footer) | research tool calls (curl/WebSearch/WebFetch): ~30
- Feeds hit (with reachability and method): SRF RSS {ok via curl}; Foo Feed {fail — HTTP 403}
-->
- Gaps: see [this](https://news.ycombinator.com/item?id=1) — footer links must NOT count.
"""

NEWS_0717 = """---
title: n
---

## 🌍 World

- **Delta.** Text. [Src](https://apnews.com/d)
- **Epsilon.** Text. [Src](https://bbc.com/e)

## Coverage footer
<!-- telemetry
- Direct fetches: 3 | via-snippet citations: 0
- Word count: 800 (body, excl. footer) | research tool calls (logged): 12
- Feeds hit (from fetch log): a.example {2 ok via curl, 1 fail HTTP 403}
-->
- Gaps: none.
"""

WEEKEND_0718 = """---
title: w
---

## 📄 ML / AI papers of the week

### Paper one
### Paper two

## 🔭 Fundamental science papers of the week

### Paper three
### Paper four
### Paper five

## Coverage footer
- Gaps: none.
"""

NEWS_PREV = """---
title: n
---

## 🌍 World

- **Old.** [Src](https://apnews.com/z)

## Coverage footer
- Word count: 1,000 (body, excl. footer)
"""


# --- rm-4 regression fixtures: the three sections the 2026-07-19/26/08-02
# --- evaluators reported as false-positive "empty" (anchor-free prose) -------
SCIENCE_VITALITY = """---
title: s
---

## 🔬 Findings

- **Finding.** Text. [Src](https://nature.com/a)

## 🧠 Why it matters

Three of this week's results point the same way: measurement precision is
outrunning theory in condensed matter, and the gap is now wide enough that
the interesting question is which model breaks first rather than which one
fits best. That reframes the next round of experiments as elimination, not
confirmation, and it explains why two of the groups above published null
results without apology.

## Coverage footer
- Gaps: none.
"""

WEEKEND_VITALITY = """---
title: w
---

## 🧠 Cross-cutting threads

**1. Inference is moving to the edge.** The quantisation work and the two
runtime papers below converge on the same claim: the accuracy cost of 4-bit
weights is now small enough that the deciding factor is memory bandwidth,
not perplexity.

**2. Benchmarks are being rewritten mid-flight.** Two of this week's
harness disputes turn on evaluation-time details rather than model quality,
which is a sign the field is out of headroom on the current suites.

## 🍎 Apple Silicon / local inference ecosystem

llama.cpp landed a Metal path for the new attention kernel this week, and
MLX picked up matching support a day later, so the two runtimes are back in
step on M-series hardware for the first time since spring.

The practical upshot for a 36 GB machine is that the 70B-class quants that
used to swap now fit with room for a long context window.

## 🪫 Stub section

One line, nothing else.

## 🕳️ Blank section

## Coverage footer
- Gaps: none.
"""


class BriefsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp(prefix="briefs-test-")
        posts = os.path.join(cls.root, "_posts")
        os.makedirs(posts)
        for name, text in (("2026-07-14-news.md", NEWS_0714),
                           ("2026-07-17-news.md", NEWS_0717),
                           ("2026-07-18-weekend.md", WEEKEND_0718),
                           ("2026-07-08-news.md", NEWS_PREV),
                           ("2026-07-13-evaluator.md", "not a writer post")):
            with open(os.path.join(posts, name), "w") as fh:
                fh.write(text)
        cls.health = metrics.compute_health(cls.root, "2026-07-18")
        cls.briefs = cls.health["briefs"]

    def test_aggregator_leakage_body_only(self):
        self.assertEqual(self.briefs["aggregator_leakage"],
                         [{"post": "2026-07-14-news.md", "url": "https://reddit.com/r/x"}])

    def test_section_vitality(self):
        news = self.briefs["by_stream"]["news"]
        self.assertEqual(news["posts"], 2)
        self.assertEqual(news["sections"], 4)
        self.assertEqual(news["empty_sections"],
                         [{"post": "2026-07-14-news.md", "section": "Dead section"}])

    def test_single_source_and_tags(self):
        news = self.briefs["by_stream"]["news"]
        self.assertEqual(news["citations"], 5)
        self.assertEqual(news["single_source"], 1)
        self.assertEqual(news["single_source_rate"], 0.2)
        self.assertEqual(news["tags"], {"single-source": 1, "preprint": 1})

    def test_footer_fetch_ratio_and_word_means(self):
        news = self.briefs["by_stream"]["news"]
        self.assertEqual(news["direct_fetches"], 8)
        self.assertEqual(news["via_snippet"], 1)
        self.assertEqual(news["direct_fetch_ratio"], round(8 / 9, 3))
        self.assertEqual(news["words_mean"], 1000)   # mean(1200, 800)
        self.assertEqual(news["calls_mean"], 21)     # mean(~30, 12) -- tilde tolerated
        self.assertEqual(news["words_mean_prev_week"], 1000)

    def test_feeds_hit_both_formats(self):
        feeds = self.briefs["feeds"]
        self.assertEqual(feeds["SRF RSS"]["ok_curl"], 1)        # legacy {ok via curl}
        self.assertEqual(feeds["Foo Feed"]["fail"], 1)          # legacy {fail — HTTP 403}
        self.assertEqual(feeds["a.example"]["ok_curl"], 2)      # computed {2 ok via curl, ...}
        self.assertEqual(feeds["a.example"]["fail"], 1)

    def test_weekend_paper_balance(self):
        self.assertEqual(self.briefs["weekend_balance"],
                         {"ml_items": 2, "science_items": 3, "ml_share": 0.4})

    def test_off_main_degrades_outside_git(self):
        self.assertEqual(self.health["continuity"]["off_main"], {"available": False})


class SectionVitalityTest(unittest.TestCase):
    """rm-4 (proposed 2026-07-19, re-proposed 07-26 + 08-02): a section is empty
    only when it carries no items AND almost no prose. Anchor-free synthesis
    sections -- the three the evaluators kept false-flagging -- are alive."""

    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp(prefix="vitality-test-")
        posts = os.path.join(cls.root, "_posts")
        os.makedirs(posts)
        for name, text in (("2026-07-15-science.md", SCIENCE_VITALITY),
                           ("2026-07-18-weekend.md", WEEKEND_VITALITY)):
            with open(os.path.join(posts, name), "w") as fh:
                fh.write(text)
        cls.briefs = metrics.compute_health(cls.root, "2026-07-18")["briefs"]

    def test_prose_sections_are_not_empty(self):
        """The three reported false positives: Science "Why it matters",
        weekend "Cross-cutting threads" and "Apple Silicon"."""
        flagged = {e["section"] for s in self.briefs["by_stream"].values()
                   for e in s["empty_sections"]}
        self.assertNotIn("🧠 Why it matters", flagged)
        self.assertNotIn("🧠 Cross-cutting threads", flagged)
        self.assertNotIn("🍎 Apple Silicon / local inference ecosystem", flagged)
        self.assertEqual(self.briefs["by_stream"]["science"]["empty_sections"], [])

    def test_blank_and_stub_sections_still_flagged(self):
        """The threshold's low side: a truly blank section AND a one-line stub
        (the risk the 08-02 proposal flagged) both still count as empty."""
        weekend = self.briefs["by_stream"]["weekend"]
        self.assertEqual(weekend["sections"], 4)
        self.assertEqual(weekend["empty_sections"],
                         [{"post": "2026-07-18-weekend.md", "section": "🪫 Stub section"},
                          {"post": "2026-07-18-weekend.md", "section": "🕳️ Blank section"}])


def _git(root, *argv):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@e",
                    "-c", "commit.gpgsign=false"] + list(argv),
                   cwd=root, check=True, capture_output=True, text=True)


def _sha(root, rev):
    return subprocess.run(["git", "rev-parse", rev], cwd=root, check=True,
                          capture_output=True, text=True).stdout.strip()


class OffMainTest(unittest.TestCase):
    """rm-3 (proposed 2026-07-19, re-proposed 07-26 + 08-02): the guard must
    compare against `origin/main`, not the local `main` ref. The evaluator runs
    detached after `git pull --ff-only`, which leaves local `main` stale --
    against it every pulled commit read as off-main (~14-20 phantoms a week)."""

    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp(prefix="offmain-test-")
        _git(cls.root, "-c", "init.defaultBranch=main", "init", "-q")
        for msg in ("A base", "B pulled", "C pulled"):
            _git(cls.root, "commit", "--allow-empty", "-q", "-m", msg)
        head = _sha(cls.root, "HEAD")
        _git(cls.root, "update-ref", "refs/remotes/origin/main", head)
        # a genuinely stranded commit: pushed to a claude/* branch, never merged
        _git(cls.root, "checkout", "-q", "-b", "claude/stranded")
        _git(cls.root, "commit", "--allow-empty", "-q", "-m", "D stranded")
        cls.stranded = _sha(cls.root, "HEAD")
        _git(cls.root, "update-ref", "refs/remotes/origin/claude/stranded", cls.stranded)
        # the sandbox's real state: detached at origin/main, local `main` stale
        _git(cls.root, "checkout", "-q", "--detach", head)
        _git(cls.root, "branch", "-q", "-D", "claude/stranded")
        _git(cls.root, "branch", "-q", "-f", "main", _sha(cls.root, "HEAD~2"))
        cls.off_main = metrics.build_off_main(cls.root, "2026-01-01")

    def test_pulled_commits_are_not_reported_off_main(self):
        subjects = [l.split(" ", 1)[1] for l in self.off_main["commits_not_on_main"]]
        self.assertNotIn("B pulled", subjects)
        self.assertNotIn("C pulled", subjects)

    def test_genuinely_stranded_commit_still_caught(self):
        self.assertTrue(self.off_main["available"])
        self.assertEqual([l.split(" ", 1)[1] for l in self.off_main["commits_not_on_main"]],
                         ["D stranded"])
        self.assertEqual(self.off_main["remote_branches"], ["origin/claude/stranded"])


if __name__ == "__main__":
    unittest.main()
