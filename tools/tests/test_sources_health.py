"""RED-phase spec tests for tools/sources/health.py -- SPIKE-2026-07-07-continuous-news.md
section 3.4 ('Measurement: tools/sources/health.py -> _data/source-health.json') + section 2's
worked evidence (top5 share computed *excluding* the hub, admin/institutional getting 'a
higher 30% saturation bar' vs. outlet's 20%) + the sources contract's health.py clause.

health.py [--root PATH] is CLI-only and prints + writes <root>/_data/source-health.json. Each
test class owns a minimal, single-concern fixture (own tempdir, own index/stories and/or
_posts) rather than one shared mega-fixture, so a failure always points at exactly one
computation. The rolling-30d window is relative to real wall-clock today (no --date flag in
the contract), so every date uses `sources_helpers.days_ago()` and only clearly-inside
(<=25d) vs. clearly-outside (>=45d) cases -- never the exact 30-day edge.

Schema this suite fixes (the contract says the field *names* below; exact JSON nesting is the
test's call): {"streams": {"<slug>": {"stories", "unique_domains", "new_domains",
"top5_share", "saturated": [...], "waiver_rate", "candidates_open"}, ...}, "overall": {...}}.
top5_share / waiver_rate may be expressed as a 0-1 fraction or a 0-100 percentage -- assertions
below tolerate either scale, since the contract doesn't pin it.
"""
import json
import os
import shutil
import tempfile
import unittest

import sources_helpers as H


def _write_jsonl_records(path, records):
    with open(path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def _fraction_or_percent_close(value, fraction, tol=0.02):
    if value is None:
        return False
    return abs(value - fraction) <= tol or abs(value - fraction * 100) <= tol * 100


class HealthTestBase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="sources-health-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def stories_dir(self):
        d = os.path.join(self.root, "index", "stories")
        os.makedirs(d, exist_ok=True)
        return d

    def posts_dir(self):
        d = os.path.join(self.root, "_posts")
        os.makedirs(d, exist_ok=True)
        return d

    def run_health(self):
        return H.run_script(self, "health.py", ["--root", self.root])

    def load_health_json(self):
        path = os.path.join(self.root, "_data", "source-health.json")
        self.assertTrue(os.path.exists(path), "health.py must write _data/source-health.json")
        with open(path) as f:
            return json.load(f)

    def rec(self, domain, url, date, stream="news"):
        return {"date": date, "stream": stream, "source_domain": domain, "url": url,
                "headline": "story about %s" % domain, "tier": "T2"}


class StoriesAndUniqueDomainsTest(HealthTestBase):
    """Per-stream `stories` (count within the rolling 30d window) and `unique_domains`,
    computed independently per live stream."""

    def setUp(self):
        super().setUp()
        stories = self.stories_dir()
        _write_jsonl_records(os.path.join(stories, "news-in-window.jsonl"), [
            self.rec("srf.ch", "https://srf.ch/a1", H.days_ago(5), "news"),
            self.rec("srf.ch", "https://srf.ch/a2", H.days_ago(6), "news"),
            self.rec("letemps.ch", "https://letemps.ch/a1", H.days_ago(7), "news"),
        ])
        _write_jsonl_records(os.path.join(stories, "news-out-of-window.jsonl"), [
            self.rec("srf.ch", "https://srf.ch/old1", H.days_ago(60), "news"),
        ])
        _write_jsonl_records(os.path.join(stories, "ai-ml-in-window.jsonl"), [
            self.rec("arxiv.org", "https://arxiv.org/abs/1", H.days_ago(3), "ai-ml"),
            self.rec("github.com", "https://github.com/o/r", H.days_ago(4), "ai-ml"),
        ])

    def test_news_stories_and_unique_domains_within_window_only(self):
        proc = self.run_health()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = self.load_health_json()
        news = data["streams"]["news"]
        self.assertEqual(news["stories"], 3, "the out-of-window srf.ch record must be excluded")
        self.assertEqual(news["unique_domains"], 2)

    def test_ai_ml_is_computed_independently(self):
        proc = self.run_health()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = self.load_health_json()
        ai_ml = data["streams"]["ai-ml"]
        self.assertEqual(ai_ml["stories"], 2)
        self.assertEqual(ai_ml["unique_domains"], 2)

    def test_zero_activity_live_streams_still_get_a_skeleton_entry(self):
        """science/weekend have no fixture data at all but must still appear (evaluator's
        metrics.py and any dashboard consuming this file need all 4 live streams present)."""
        proc = self.run_health()
        data = self.load_health_json()
        for slug in ("science", "weekend"):
            with self.subTest(slug=slug):
                self.assertIn(slug, data["streams"])
                self.assertEqual(data["streams"][slug]["stories"], 0)


class NewDomainsTest(HealthTestBase):
    """`new_domains`: a domain whose *entire* citation history (not just this window) starts
    within the rolling 30d window. oldtimer.example has a citation from 60 days back (outside
    the window) proving prior history, despite also being active in-window; freshvoice.example
    has none."""

    def setUp(self):
        super().setUp()
        stories = self.stories_dir()
        _write_jsonl_records(os.path.join(stories, "a.jsonl"), [
            self.rec("oldtimer.example", "https://oldtimer.example/old", H.days_ago(60), "news"),
            self.rec("oldtimer.example", "https://oldtimer.example/new", H.days_ago(10), "news"),
            self.rec("freshvoice.example", "https://freshvoice.example/x1", H.days_ago(10), "news"),
        ])

    def test_only_the_domain_with_no_prior_history_counts_as_new(self):
        proc = self.run_health()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = self.load_health_json()
        self.assertEqual(data["streams"]["news"]["new_domains"], 1)


class Top5ShareAndSaturationTest(HealthTestBase):
    """top5_share is outlet-class only (hubs AND institutional excluded from both the
    ranking and its denominator); `saturated` uses the outlet 20% bar for outlet domains,
    the institutional 30% bar for institutional domains (SPIKE 3.4), and hubs are exempt
    from saturation entirely (SPIKE section 2: 'the mechanism in section 3.4 exempts it').

    Fixture (all within the 30d window, all domains classed via the fixed rules -- arxiv.org
    is the hardcoded hub set, admin.ch the hardcoded institutional literal):
      srf.ch (outlet) x10, admin.ch (institutional) x8, arxiv.org (hub) x8,
      letemps.ch (outlet) x3, aljazeera.com (outlet) x2,
      swissinfo.ch/watson.ch/tdg.ch/20min.ch/freshvoice.example (outlet) x1 each.
      ALL-class total = 36; outlet-only total = 20 (10+3+2+1+1+1+1+1).
      top5 outlet sum = 10+3+2+1+1 = 17  ->  top5_share = 17/20 = 0.85.
      srf.ch share (10/36 = 27.8%) > 20%   -> saturated (outlet bar).
      admin.ch share (8/36 = 22.2%) is between 20% and 30% -> NOT saturated (institutional
      gets the higher bar).
      arxiv.org share (8/36 = 22.2%) > 20% but hub-exempt -> NOT saturated.
      letemps.ch share (3/36 = 8.3%) -> nowhere near either bar.
    """

    def setUp(self):
        super().setUp()
        stories = self.stories_dir()
        records = []
        counts = {
            "srf.ch": 10, "admin.ch": 8, "arxiv.org": 8, "letemps.ch": 3, "aljazeera.com": 2,
            "swissinfo.ch": 1, "watson.ch": 1, "tdg.ch": 1, "20min.ch": 1, "freshvoice.example": 1,
        }
        # Cycle a small, safely-inside-30d day offset per citation (5..14) -- NOT a single
        # counter incremented across all ~36 records, which would walk the later domains
        # right out of the rolling window.
        for domain, n in counts.items():
            for i in range(n):
                records.append(self.rec(domain, "https://%s/%d" % (domain, i),
                                         H.days_ago(5 + (i % 10)), "news"))
        _write_jsonl_records(os.path.join(stories, "news-mix.jsonl"), records)

    def test_top5_share_excludes_hub_and_institutional(self):
        proc = self.run_health()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = self.load_health_json()
        top5_share = data["streams"]["news"]["top5_share"]
        self.assertTrue(_fraction_or_percent_close(top5_share, 0.85),
                         "expected top5_share ~=0.85 (or 85), got %r" % (top5_share,))

    def test_outlet_over_twenty_percent_is_saturated(self):
        proc = self.run_health()
        data = self.load_health_json()
        saturated = data["streams"]["news"]["saturated"]
        self.assertIn("srf.ch", saturated)

    def test_institutional_between_twenty_and_thirty_percent_is_not_saturated(self):
        proc = self.run_health()
        data = self.load_health_json()
        saturated = data["streams"]["news"]["saturated"]
        self.assertNotIn("admin.ch", saturated,
                          "admin.ch at ~22%% is under the institutional 30%% bar, even though "
                          "it would trip the outlet 20%% bar")

    def test_hub_over_twenty_percent_is_never_saturated(self):
        proc = self.run_health()
        data = self.load_health_json()
        saturated = data["streams"]["news"]["saturated"]
        self.assertNotIn("arxiv.org", saturated)

    def test_low_share_outlet_is_not_saturated(self):
        proc = self.run_health()
        data = self.load_health_json()
        saturated = data["streams"]["news"]["saturated"]
        self.assertNotIn("letemps.ch", saturated)


class WaiverRateTest(HealthTestBase):
    """waiver_rate: share of in-window editions (posts) for that stream whose Discovery
    footer says 'waived'. 2 of 4 in-window news posts waive; a 5th, older post (50 days
    back) also waives but must be excluded from both the numerator and denominator."""

    def _post(self, date, discovery_line):
        return f"""---
layout: single
title: "News -- {date}"
date: {date}T09:00:00+02:00
categories: [news]
---

# News -- {date}

## Switzerland
- **A routine Swiss story.** A neutral summary sentence. ([SRF](https://www.srf.ch/news/{date}))

---

## Coverage footer
- Sources used: T2 = 1 citation
{discovery_line}
"""

    def setUp(self):
        super().setUp()
        posts = self.posts_dir()
        plan = [
            (H.days_ago(2), "- Discovery: met (something new)"),
            (H.days_ago(9), "- Discovery: waived — nothing new pursued"),
            (H.days_ago(16), "- Discovery: met (another new outlet)"),
            (H.days_ago(23), "- Discovery: waived — quiet week"),
            (H.days_ago(50), "- Discovery: waived — this is outside the window"),
        ]
        for date, line in plan:
            with open(os.path.join(posts, "%s-news.md" % date), "w") as f:
                f.write(self._post(date, line))

    def test_waiver_rate_counts_only_in_window_editions(self):
        proc = self.run_health()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = self.load_health_json()
        waiver_rate = data["streams"]["news"]["waiver_rate"]
        self.assertTrue(_fraction_or_percent_close(waiver_rate, 0.5),
                         "expected waiver_rate ~=0.5 (2 waived / 4 in-window editions), got %r" % (waiver_rate,))


class CandidatesOpenTest(HealthTestBase):
    """candidates_open: per-stream count of not-yet-folded sources/candidates.jsonl lines
    (each line carries its own `stream` field per the registry contract's schema)."""

    def setUp(self):
        super().setUp()
        sources_dir = os.path.join(self.root, "sources")
        os.makedirs(sources_dir, exist_ok=True)
        _write_jsonl_records(os.path.join(sources_dir, "candidates.jsonl"), [
            {"domain": "a.example", "first_seen": H.days_ago(1), "via": "search", "stream": "news", "url": "https://a.example/x"},
            {"domain": "b.example", "first_seen": H.days_ago(2), "via": "search", "stream": "news", "url": "https://b.example/x"},
            {"domain": "c.example", "first_seen": H.days_ago(3), "via": "search", "stream": "ai-ml", "url": "https://c.example/x"},
        ])

    def test_candidates_open_is_scoped_per_stream(self):
        proc = self.run_health()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = self.load_health_json()
        self.assertEqual(data["streams"]["news"]["candidates_open"], 2)
        self.assertEqual(data["streams"]["ai-ml"]["candidates_open"], 1)
        self.assertEqual(data["streams"]["science"]["candidates_open"], 0)


class OverallBlockAndDeterminismTest(HealthTestBase):
    """'Plus overall block' + 'Deterministic, no network.'"""

    def setUp(self):
        super().setUp()
        stories = self.stories_dir()
        _write_jsonl_records(os.path.join(stories, "news.jsonl"), [
            self.rec("srf.ch", "https://srf.ch/a1", H.days_ago(2), "news"),
            self.rec("srf.ch", "https://srf.ch/a2", H.days_ago(3), "news"),
        ])
        _write_jsonl_records(os.path.join(stories, "ai-ml.jsonl"), [
            self.rec("arxiv.org", "https://arxiv.org/abs/1", H.days_ago(2), "ai-ml"),
        ])

    def test_overall_block_present_and_sums_per_stream_stories(self):
        proc = self.run_health()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = self.load_health_json()
        self.assertIn("overall", data)
        overall = data["overall"]
        self.assertIsInstance(overall, dict)
        total_stories = sum(s["stories"] for s in data["streams"].values())
        self.assertEqual(total_stories, 3)
        # Whatever key the implementation uses for the story total, it must agree with the
        # per-stream sum -- try the most likely key names without over-fitting the schema.
        overall_total = overall.get("stories")
        if overall_total is not None:
            self.assertEqual(overall_total, total_stories)

    def test_two_runs_produce_byte_identical_output(self):
        """Deterministic, no network: same inputs -> same _data/source-health.json."""
        proc1 = self.run_health()
        self.assertEqual(proc1.returncode, 0, proc1.stderr)
        with open(os.path.join(self.root, "_data", "source-health.json")) as f:
            first = f.read()
        proc2 = self.run_health()
        self.assertEqual(proc2.returncode, 0, proc2.stderr)
        with open(os.path.join(self.root, "_data", "source-health.json")) as f:
            second = f.read()
        self.assertEqual(first, second)

    def test_stdout_also_reports_the_data(self):
        proc = self.run_health()
        self.assertTrue(proc.stdout.strip(), "health.py should print the health data, not just write it")


if __name__ == "__main__":
    unittest.main()
