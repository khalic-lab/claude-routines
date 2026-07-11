"""RED-phase spec tests for tools/sources/preflight.py -- SPIKE-2026-07-07-continuous-news.md
section 3.3 ('the plan -- not any prompt table -- is the authority on what to fetch') + 3.4
('Pressure mechanisms ... Both ship report-only') + the sources contract's preflight.py clause.

preflight.py --slug <news|ai-ml|science|weekend> [--root PATH] is CLI-only and always exits 0
(report-only, even the emergency-slate 'source-plan unavailable' path), so every test just
drives the subprocess and scopes its assertions to the relevant markdown section of stdout
(fetch list / pressure / discovery) via `_section()` below, rather than assuming exact wording.

The rolling-30d pressure window is relative to *real* wall-clock today (the contract gives
preflight.py no --date override, unlike metrics.py), so all index/stories fixtures here use
`sources_helpers.days_ago()` and only clearly-inside (<=25d) vs. clearly-outside (45d) cases --
never the exact 30-day edge, which the contract does not pin either way.
"""
import os
import re
import shutil
import tempfile
import unittest

import sources_helpers as H
import yamllite


def _section(text, heading_keyword):
    """Return the markdown section (heading line through the next heading or EOF) whose
    heading contains `heading_keyword` (case-insensitive), or None if not found."""
    lines = text.split("\n")
    start = None
    for i, line in enumerate(lines):
        if re.match(r"^#{1,6}\s", line) and heading_keyword.lower() in line.lower():
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if re.match(r"^#{1,6}\s", lines[j]):
            end = j
            break
    return "\n".join(lines[start:end])


def _quota_mentions_number(section_text, n):
    if not section_text:
        return False
    pat = re.compile(r"(quota[^\n]{0,30}?\b%d\b)|(\b%d\b[^\n]{0,30}?quota)" % (n, n), re.I)
    return bool(pat.search(section_text))


class PreflightTestBase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="sources-preflight-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def run_preflight(self, slug, root=None):
        return H.run_script(self, "preflight.py", ["--slug", slug, "--root", root or self.root])

    def write_registry(self, entries):
        sources_dir = os.path.join(self.root, "sources")
        os.makedirs(sources_dir, exist_ok=True)
        with open(os.path.join(sources_dir, "registry.yml"), "w") as f:
            f.write(yamllite.dump(entries))


class PlanShapeTest(PreflightTestBase):
    """The plan always has fetch-list / pressure / discovery sections, for every slug, and
    always exits 0 (contract: '(4) exits 0 even on empty/missing registry')."""

    def setUp(self):
        super().setUp()
        self.write_registry({
            "srf.ch": {"class": "outlet", "status": "established", "reach": "direct",
                       "probe": {"url": "https://www.srf.ch/news/bnf", "method": "curl"},
                       "streams": ["news"], "last_cited": H.days_ago(2)},
        })

    def test_each_slug_produces_a_plan_with_all_three_sections_and_exits_zero(self):
        for slug in ("news", "ai-ml", "science", "weekend"):
            with self.subTest(slug=slug):
                proc = self.run_preflight(slug)
                self.assertEqual(proc.returncode, 0, "preflight must always exit 0.\n%s" % proc.stderr)
                self.assertIsNotNone(_section(proc.stdout, "fetch"),
                                      "no fetch-list section for slug=%s:\n%s" % (slug, proc.stdout))
                self.assertIsNotNone(_section(proc.stdout, "pressure"),
                                      "no pressure section for slug=%s:\n%s" % (slug, proc.stdout))
                self.assertIsNotNone(_section(proc.stdout, "discovery"),
                                      "no discovery section for slug=%s:\n%s" % (slug, proc.stdout))


class FetchListStreamAffinityTest(PreflightTestBase):
    """SPIKE 3.4: probe blocks carry `streams:` affinity -- the fetch list for a slug must
    only surface domains affine to that slug's stream."""

    def setUp(self):
        super().setUp()
        self.write_registry({
            "srf.ch": {"class": "outlet", "status": "established", "reach": "direct",
                       "probe": {"url": "https://www.srf.ch/news/bnf", "method": "curl"},
                       "streams": ["news"], "last_cited": H.days_ago(2)},
            "quantamagazine.org": {"class": "outlet", "status": "probation", "reach": "direct",
                                   "probe": {"url": "https://www.quantamagazine.org/feed/", "method": "curl"},
                                   "streams": ["weekend"], "last_cited": H.days_ago(3)},
        })

    def test_news_fetch_list_includes_affine_domain_excludes_other_streams_domain(self):
        proc = self.run_preflight("news")
        fetch = _section(proc.stdout, "fetch") or ""
        self.assertIn("srf.ch", fetch)
        self.assertNotIn("quantamagazine.org", proc.stdout,
                          "weekend-only domain must not leak into the news plan at all")

    def test_weekend_fetch_list_includes_its_affine_domain_excludes_news_only_domain(self):
        proc = self.run_preflight("weekend")
        fetch = _section(proc.stdout, "fetch") or ""
        self.assertIn("quantamagazine.org", fetch)
        self.assertNotIn("srf.ch", proc.stdout)


class PressureSaturationTest(PreflightTestBase):
    """SPIKE 3.4 pressure mechanisms: '>20% of stream's rolling-30d citations flagged
    saturated'. All fixture dates are clearly inside the 30d window (<=25d ago); one domain's
    citations are deliberately placed 45d ago to prove the window excludes them."""

    def setUp(self):
        super().setUp()
        self.write_registry({
            "srf.ch": {"class": "outlet", "status": "established", "reach": "direct",
                       "streams": ["news"], "last_cited": H.days_ago(5)},
            "letemps.ch": {"class": "outlet", "status": "probation", "reach": "direct",
                           "streams": ["news"], "last_cited": H.days_ago(12)},
        })
        stories_dir = os.path.join(self.root, "index", "stories")
        os.makedirs(stories_dir, exist_ok=True)

        def rec(domain, url, idx):
            return {"date": None, "stream": "news", "source_domain": domain, "url": url,
                    "headline": "story %s" % idx, "tier": "T2"}

        def write(fname, date, domains):
            path = os.path.join(stories_dir, fname)
            with open(path, "w") as f:
                import json
                for i, d in enumerate(domains):
                    r = rec(d, "https://%s/%d" % (d, i), i)
                    r["date"] = date
                    f.write(json.dumps(r) + "\n")

        write("A-news.jsonl", H.days_ago(5), ["srf.ch", "srf.ch", "srf.ch"])       # edition w/ 3x srf.ch
        write("B-news.jsonl", H.days_ago(12), ["letemps.ch"])
        write("C-news.jsonl", H.days_ago(18), ["aljazeera.com", "admin.ch"])
        write("D-news.jsonl", H.days_ago(25), ["alpha.example", "beta.example", "gamma.example", "delta.example"])
        write("E-news.jsonl", H.days_ago(45), ["megaphone.example"] * 5)  # OUTSIDE the 30d window

    def test_saturated_domain_is_flagged(self):
        """srf.ch is 3/10 = 30% of the rolling-30d news citations -- > 20% -> saturated."""
        proc = self.run_preflight("news")
        pressure = _section(proc.stdout, "pressure") or ""
        lines_with_srf = [l for l in pressure.split("\n") if "srf.ch" in l]
        self.assertTrue(lines_with_srf, "srf.ch should appear in the pressure section:\n%s" % pressure)
        self.assertTrue(any("saturat" in l.lower() for l in lines_with_srf),
                         "srf.ch's pressure line should call out saturation:\n%s" % pressure)

    def test_low_share_domain_is_not_flagged_saturated(self):
        """letemps.ch is 1/10 = 10% -- well under the 20% bar."""
        proc = self.run_preflight("news")
        pressure = _section(proc.stdout, "pressure") or ""
        lines_with_letemps = [l for l in pressure.split("\n") if "letemps.ch" in l]
        self.assertFalse(any("saturat" in l.lower() for l in lines_with_letemps),
                          "letemps.ch must not be flagged saturated:\n%s" % pressure)

    def test_citations_outside_30d_window_are_excluded(self):
        """megaphone.example's 5 citations sit 45 days back -- outside the rolling window --
        and must not surface anywhere in the plan (it would otherwise dominate the count)."""
        proc = self.run_preflight("news")
        self.assertNotIn("megaphone.example", proc.stdout)

    def test_pressure_report_never_affects_exit_code(self):
        """SPIKE 3.4: 'Both ship report-only' -- saturation/capping are informational only."""
        proc = self.run_preflight("news")
        self.assertEqual(proc.returncode, 0)


class DiscoveryQuotaAndCandidatesTest(PreflightTestBase):
    """SPIKE 3.4 pull mechanism + Open Question 5 numbers: news>=1, ai-ml>=1 non-hub,
    science>=2, weekend>=2; candidates_to_try surfaces registry candidate/dormant(>30d) entries."""

    def setUp(self):
        super().setUp()
        self.write_registry({
            "activeoutlet.example": {"class": "outlet", "status": "established", "reach": "direct",
                                     "streams": ["news"], "last_cited": H.days_ago(2)},
            "brandnew.example": {"class": "outlet", "status": "candidate", "reach": "direct",
                                 "streams": ["news"], "last_cited": H.days_ago(3)},
            "oldschool.example": {"class": "outlet", "status": "probation", "reach": "direct",
                                  "streams": ["news"], "last_cited": H.days_ago(45)},
            "spamsite.example": {"class": "outlet", "status": "retired", "reach": "direct",
                                 "streams": ["news"], "last_cited": H.days_ago(45)},
            "sunkoutlet.example": {"class": "outlet", "status": "demoted", "reach": "direct",
                                   "streams": ["news"], "last_cited": H.days_ago(45)},
        })

    def test_quota_values_per_slug(self):
        expected = {"news": 1, "ai-ml": 1, "science": 2, "weekend": 2}
        for slug, quota in expected.items():
            with self.subTest(slug=slug):
                proc = self.run_preflight(slug)
                discovery = _section(proc.stdout, "discovery") or ""
                self.assertTrue(_quota_mentions_number(discovery, quota),
                                 "expected the %s discovery quota (%d) to be stated:\n%s" % (slug, quota, discovery))

    def test_candidate_status_entry_appears_in_candidates_to_try(self):
        proc = self.run_preflight("news")
        discovery = _section(proc.stdout, "discovery") or ""
        self.assertIn("brandnew.example", discovery)

    def test_dormant_entry_over_30_days_unused_appears_in_candidates_to_try(self):
        proc = self.run_preflight("news")
        discovery = _section(proc.stdout, "discovery") or ""
        self.assertIn("oldschool.example", discovery)

    def test_recently_used_established_domain_is_not_a_candidate_to_try(self):
        proc = self.run_preflight("news")
        discovery = _section(proc.stdout, "discovery") or ""
        self.assertNotIn("activeoutlet.example", discovery)

    def test_retired_or_demoted_dormant_entry_never_resurfaces_as_candidate(self):
        """A deny-listed (retired) or demoted domain is dormant by construction — it must
        NOT come back as a candidates_to_try suggestion (2026-07-11 fix: discovery now
        applies the same status exclusion as the fetch list)."""
        proc = self.run_preflight("news")
        discovery = _section(proc.stdout, "discovery") or ""
        self.assertNotIn("spamsite.example", discovery)
        self.assertNotIn("sunkoutlet.example", discovery)


class MissingOrEmptyRegistryTest(PreflightTestBase):
    """SPIKE 3.3 emergency-slate fix (review C8): preflight failing must degrade to a labeled
    floor, never abort -- contract: '(4) exits 0 even on empty/missing registry (prints
    "source-plan unavailable" marker -- the prompts' emergency-slate trigger).'"""

    def test_missing_registry_file_prints_marker_and_exits_zero(self):
        proc = self.run_preflight("news")  # no sources/registry.yml written at all
        self.assertEqual(proc.returncode, 0)
        self.assertIn("source-plan unavailable", proc.stdout)

    def test_empty_registry_file_prints_marker_and_exits_zero(self):
        sources_dir = os.path.join(self.root, "sources")
        os.makedirs(sources_dir, exist_ok=True)
        open(os.path.join(sources_dir, "registry.yml"), "w").close()  # zero-byte file
        proc = self.run_preflight("news")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("source-plan unavailable", proc.stdout)


if __name__ == "__main__":
    unittest.main()
