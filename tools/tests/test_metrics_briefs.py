"""Spec tests for metrics.py's computed brief-text dimensions ("briefs" key,
added 2026-07-18): B aggregator leakage, D section vitality, F single-source
rate, G tag counts, H weekend paper balance, K footer fetch ratios + feeds-hit
aggregation (BOTH the legacy hand-written and the new footer.py-computed
formats), L word-count means incl. previous week. These replace the evaluator's
hand-counting -- the schema here is the contract the evaluator prompt reads.
"""
import importlib.util
import os
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


if __name__ == "__main__":
    unittest.main()
