"""RED-phase spec tests for tools/sources/registry.py — SPIKE-2026-07-07-continuous-news.md
section 3.4 ("Source registry + credibility lifecycle") + the sources contract passed to the
test author (registry.py bootstrap / sync semantics).

registry.py is CLI-only per the contract, so every test drives it as a subprocess
(`registry.py bootstrap --root <tmp>` / `registry.py sync --root <tmp>`) against a tempdir
skeleton copying the fixture index under tools/tests/fixtures/sources/index_stories/, then
reads back <tmp>/sources/registry.yml with the dependency-free yamllite loader (registry.py
itself is expected to be stdlib-only, like every other tool in this repo, so tests must not
require PyYAML to be installed either).

Fixture citation counts (see fixtures/sources/index_stories/*.jsonl, built by this test's
sibling helper) are hand-tallied below so every assertion traces to an exact count:

  srf.ch          6 citations, news only          -> established (>=5), last_cited 2026-07-01
  letemps.ch      3 citations, news only          -> probation (1-4),   last_cited 2026-07-01
  aljazeera.com   5 citations, news only          -> established (boundary), last_cited 2026-07-01
  state.gov       2 citations, news only          -> probation, institutional
  reuters.com     2 LIVE citations (news), + 1 retired-stream (markets, later date, ignored)
  arxiv.org       5 citations, ai-ml + science     -> established, hub
  github.com      3 citations, ai-ml only          -> probation, hub
  hf.co           2 citations, ai-ml only          -> probation, hub
  nature.com      2 citations, science only        -> probation, outlet, gets subsources regardless
  semanticscholar.org  2 citations, science only   -> probation, outlet
  ec.europa.eu    1 citation, science only         -> probation, institutional
  quantamagazine.org  1 citation, weekend only     -> probation (boundary), outlet
  admin.ch        1 citation, weekend only         -> probation, institutional

  Retired-stream-only domains that MUST NOT appear at all: cnn.com (overview), nvd.nist.gov
  and cisa.gov (cyber-papers), bloomberg.com (markets).
"""
import os
import shutil
import tempfile
import unittest

import sources_helpers as H
import yamllite


def _bootstrap_registry(testcase, extra_index_files=None):
    """Build a tempdir root, seed index/stories from the fixture (+ extras), run
    `registry.py bootstrap`, and return (root, parsed_registry_dict)."""
    root = tempfile.mkdtemp(prefix="sources-registry-")
    add_cleanup = testcase.addClassCleanup if isinstance(testcase, type) else testcase.addCleanup
    add_cleanup(shutil.rmtree, root, ignore_errors=True)
    H.seed_index_stories(root, extra_files=extra_index_files)
    proc = H.run_script(testcase, "registry.py", ["bootstrap", "--root", root])
    # Plain asserts (not self.assertX): this helper runs from both setUp (instance) and
    # setUpClass (class) contexts, and TestCase's bound assert methods mis-bind when called
    # on the class object itself rather than an instance.
    if proc.returncode != 0:
        raise AssertionError(
            "registry.py bootstrap exited non-zero.\nstdout:\n%s\nstderr:\n%s" % (proc.stdout, proc.stderr)
        )
    registry_path = os.path.join(root, "sources", "registry.yml")
    if not os.path.exists(registry_path):
        raise AssertionError("bootstrap did not write sources/registry.yml")
    with open(registry_path) as f:
        text = f.read()
    data = yamllite.load(text)
    if not isinstance(data, dict):
        raise AssertionError("sources/registry.yml did not parse to a mapping of domain -> record, got %r" % (data,))
    return root, data


class BootstrapCitationThresholdsTest(unittest.TestCase):
    """SPIKE 3.4 'Bootstrap' + contract: >=5 citations -> established, 1-4 -> probation."""

    @classmethod
    def setUpClass(cls):
        cls.root, cls.registry = _bootstrap_registry(cls)

    def test_six_citations_is_established(self):
        """srf.ch has 6 live citations -> status established."""
        self.assertIn("srf.ch", self.registry)
        self.assertEqual(self.registry["srf.ch"]["status"], "established")

    def test_three_citations_is_probation(self):
        """letemps.ch has 3 live citations -> status probation (1-4 band)."""
        self.assertEqual(self.registry["letemps.ch"]["status"], "probation")

    def test_established_boundary_at_five(self):
        """aljazeera.com has exactly 5 live citations -> established (the >=5 boundary)."""
        self.assertEqual(self.registry["aljazeera.com"]["status"], "established")

    def test_probation_boundary_at_one(self):
        """quantamagazine.org has exactly 1 live citation -> probation (the 1-4 lower boundary)."""
        self.assertEqual(self.registry["quantamagazine.org"]["status"], "probation")

    def test_four_citations_is_still_probation(self):
        """nature.com has 2 live citations here; github.com has 3 -- both inside 1-4 -> probation."""
        self.assertEqual(self.registry["github.com"]["status"], "probation")
        self.assertEqual(self.registry["nature.com"]["status"], "probation")


class BootstrapLiveStreamsOnlyTest(unittest.TestCase):
    """SPIKE 3.4 Bootstrap + contract: counts ONLY news/ai-ml/science/weekend; retired-stream
    files (overview/cyber-papers/markets) are excluded entirely, even for domains with many
    retired-stream citations."""

    @classmethod
    def setUpClass(cls):
        cls.root, cls.registry = _bootstrap_registry(cls)

    def test_overview_only_domain_absent(self):
        """cnn.com appears only in the retired overview.jsonl fixture (3x) -> must not appear."""
        self.assertNotIn("cnn.com", self.registry)

    def test_cyber_papers_only_domains_absent(self):
        """nvd.nist.gov (5x) and cisa.gov (2x) appear only in the retired cyber-papers.jsonl
        fixture -> neither must appear, however heavily cited."""
        self.assertNotIn("nvd.nist.gov", self.registry)
        self.assertNotIn("cisa.gov", self.registry)

    def test_markets_only_domain_absent(self):
        """bloomberg.com appears only in the retired markets.jsonl fixture (4x) -> absent."""
        self.assertNotIn("bloomberg.com", self.registry)

    def test_domain_cited_in_both_retired_and_live_counts_only_live_citations(self):
        """reuters.com has 2 live (news) citations + 1 retired-stream (markets) citation on a
        LATER date (2026-07-05, vs. the live max of 2026-06-30) -- the retired citation must
        be invisible to both the count (still probation, not established) and last_cited."""
        self.assertIn("reuters.com", self.registry)
        self.assertEqual(self.registry["reuters.com"]["status"], "probation")
        self.assertEqual(self.registry["reuters.com"]["last_cited"], "2026-06-30")


class BootstrapRetiredDomainsNeverBootstrapTest(unittest.TestCase):
    """SPIKE 3.4 Bootstrap, review fix C18: nvd.nist.gov, cisa.gov, and ecb.europa.eu are the
    retired security/markets pipeline's domains, excluded from bootstrap BY NAME ('would
    otherwise fossilize the deleted security pipeline into the founding registry') -- not merely
    because they're absent from the live-stream fixture files. A single genuine citation landing
    in a LIVE stream (e.g. weekend, as actually happened) must still not be enough to bootstrap
    one of them in; they may re-enter later only via the candidate lane (sync)."""

    def setUp(self):
        self.root, self.registry = _bootstrap_registry(self, extra_index_files={
            "2026-07-02-weekend-retired-leak.jsonl": [
                {"id": "leak-nvd", "date": "2026-07-02", "stream": "weekend",
                 "headline": "Story leak-nvd from nvd.nist.gov", "summary": "Summary of leak-nvd.",
                 "url": "https://nvd.nist.gov/vuln/detail/CVE-2026-9999",
                 "source_domain": "nvd.nist.gov", "tier": "T2", "tags": [],
                 "thread_id": "leak-nvd", "first_seen_date": "2026-07-02", "event_date": "2026-07-02"},
                {"id": "leak-cisa", "date": "2026-07-02", "stream": "weekend",
                 "headline": "Story leak-cisa from cisa.gov", "summary": "Summary of leak-cisa.",
                 "url": "https://www.cisa.gov/advisories/a99",
                 "source_domain": "cisa.gov", "tier": "T2", "tags": [],
                 "thread_id": "leak-cisa", "first_seen_date": "2026-07-02", "event_date": "2026-07-02"},
                {"id": "leak-ecb", "date": "2026-07-02", "stream": "weekend",
                 "headline": "Story leak-ecb from ecb.europa.eu", "summary": "Summary of leak-ecb.",
                 "url": "https://www.ecb.europa.eu/press/pr/a1",
                 "source_domain": "ecb.europa.eu", "tier": "T2", "tags": [],
                 "thread_id": "leak-ecb", "first_seen_date": "2026-07-02", "event_date": "2026-07-02"},
            ],
        })

    def test_retired_domains_absent_despite_single_genuine_live_citation(self):
        """Each of the three named retired domains gets exactly one genuine LIVE (weekend)
        citation here -- exactly the scenario that leaked them into the real registry.yml --
        and must still never appear."""
        for domain in ("nvd.nist.gov", "cisa.gov", "ecb.europa.eu"):
            with self.subTest(domain=domain):
                self.assertNotIn(domain, self.registry)


class BootstrapClassingTest(unittest.TestCase):
    """SPIKE 3.4: class hub for {arxiv.org, hf.co, huggingface.co, github.com, doi.org,
    biorxiv.org}; institutional for {*.gov, *.europa.eu, admin.ch}; else outlet."""

    @classmethod
    def setUpClass(cls):
        cls.root, cls.registry = _bootstrap_registry(cls)

    def test_hub_domains_classed_hub(self):
        for domain in ("arxiv.org", "github.com", "hf.co"):
            with self.subTest(domain=domain):
                self.assertEqual(self.registry[domain]["class"], "hub")

    def test_gov_wildcard_classed_institutional(self):
        """state.gov matches the *.gov institutional pattern."""
        self.assertEqual(self.registry["state.gov"]["class"], "institutional")

    def test_europa_eu_wildcard_classed_institutional(self):
        """ec.europa.eu matches the *.europa.eu institutional pattern."""
        self.assertEqual(self.registry["ec.europa.eu"]["class"], "institutional")

    def test_admin_ch_literal_classed_institutional(self):
        """admin.ch is a literal (non-wildcard) institutional entry in the SPIKE's set."""
        self.assertEqual(self.registry["admin.ch"]["class"], "institutional")

    def test_default_classing_is_outlet(self):
        for domain in ("srf.ch", "letemps.ch", "aljazeera.com", "nature.com",
                       "semanticscholar.org", "quantamagazine.org", "reuters.com"):
            with self.subTest(domain=domain):
                self.assertEqual(self.registry[domain]["class"], "outlet")


class BootstrapNatureSubsourcesTest(unittest.TestCase):
    """SPIKE 3.4: nature.com gets a fixed subsources split regardless of which paths were
    actually cited in the bootstrap window -- /articles/d (T2, news blog) vs /articles/s
    (T1, journal)."""

    @classmethod
    def setUpClass(cls):
        cls.root, cls.registry = _bootstrap_registry(cls)

    def test_subsources_present_with_correct_prefixes_tiers_notes(self):
        subsources = self.registry["nature.com"].get("subsources")
        self.assertIsInstance(subsources, list)
        by_prefix = {s["prefix"]: s for s in subsources}
        self.assertIn("/articles/d", by_prefix)
        self.assertIn("/articles/s", by_prefix)
        self.assertEqual(by_prefix["/articles/d"]["tier"], "T2")
        self.assertEqual(by_prefix["/articles/d"]["note"], "news blog")
        self.assertEqual(by_prefix["/articles/s"]["tier"], "T1")
        self.assertEqual(by_prefix["/articles/s"]["note"], "journal")

    def test_other_domains_have_no_subsources_key_or_empty(self):
        """Subsources are nature.com-specific -- an ordinary outlet must not inherit one."""
        srf = self.registry["srf.ch"]
        subs = srf.get("subsources")
        self.assertTrue(subs is None or subs == [], "srf.ch should not carry a subsources split")


class BootstrapProbeBlocksTest(unittest.TestCase):
    """SPIKE 3.4 Bootstrap: 'the 7 allowlisted feed hosts get probe: blocks' -- per
    routines/_shared/feed-first-source-order.md the 7 hosts are export.arxiv.org,
    www.nature.com, www.quantamagazine.org, api.semanticscholar.org, www.srf.ch,
    www.letemps.ch, www.aljazeera.com, i.e. the bare registry domains arxiv.org, nature.com,
    quantamagazine.org, semanticscholar.org, srf.ch, letemps.ch, aljazeera.com."""

    FEED_HOST_DOMAINS = (
        "arxiv.org", "nature.com", "quantamagazine.org", "semanticscholar.org",
        "srf.ch", "letemps.ch", "aljazeera.com",
    )

    @classmethod
    def setUpClass(cls):
        cls.root, cls.registry = _bootstrap_registry(cls)

    def test_each_feed_host_has_a_probe_block(self):
        for domain in self.FEED_HOST_DOMAINS:
            with self.subTest(domain=domain):
                self.assertIn(domain, self.registry)
                probe = self.registry[domain].get("probe")
                self.assertIsInstance(probe, dict, "%s missing a probe: block" % domain)
                self.assertTrue(probe.get("url"), "%s probe block has no url" % domain)
                self.assertIn(probe.get("method"), ("curl", "proxy"),
                              "%s probe method must be curl or proxy, got %r" % (domain, probe.get("method")))

    def test_non_feed_host_domain_has_no_probe_or_none(self):
        """A domain outside the fixed 7-host feed set (e.g. reuters.com) isn't required to
        carry a probe block."""
        reuters = self.registry.get("reuters.com", {})
        self.assertIn(reuters.get("probe"), (None, {}), "reuters.com should not get a fabricated probe block")

    def test_srf_probe_url_is_the_rss_feed_not_the_html_section_page(self):
        """The feed the prompts actually poll (routines/news.md) is the RSS endpoint
        https://www.srf.ch/news/bnf/rss/1646, not the bare HTML section page /news/bnf."""
        probe = self.registry["srf.ch"]["probe"]
        self.assertTrue(probe["url"].endswith("/rss/1646"),
                         "srf.ch probe url %r should end with /rss/1646" % probe["url"])


class BootstrapLastCitedAndStreamsTest(unittest.TestCase):
    """SPIKE 3.4 Bootstrap review C18 fix: 'backfilling last_cited across the full index.'"""

    @classmethod
    def setUpClass(cls):
        cls.root, cls.registry = _bootstrap_registry(cls)

    def test_last_cited_is_the_max_live_citation_date(self):
        """srf.ch citations land on 2026-06-10, 06-25, 07-01 (x2) -- max is 2026-07-01."""
        self.assertEqual(self.registry["srf.ch"]["last_cited"], "2026-07-01")

    def test_last_cited_for_single_citation_domain(self):
        self.assertEqual(self.registry["admin.ch"]["last_cited"], "2026-06-29")

    def test_streams_field_lists_distinct_citing_live_streams(self):
        """arxiv.org is cited from both ai-ml and science fixture files."""
        streams = set(self.registry["arxiv.org"].get("streams") or [])
        self.assertEqual(streams, {"ai-ml", "science"})

    def test_streams_field_single_stream_domain(self):
        streams = set(self.registry["srf.ch"].get("streams") or [])
        self.assertEqual(streams, {"news"})

    def test_lifecycle_audit_trail_present(self):
        """SPIKE 3.4: registry entries carry an append-only lifecycle: audit trail; bootstrap
        must seed at least one entry (exact key shape is not contract-fixed, so this only
        checks that an audit trail exists and is non-empty)."""
        lifecycle = self.registry["srf.ch"].get("lifecycle")
        self.assertIsInstance(lifecycle, list)
        self.assertGreaterEqual(len(lifecycle), 1)


class BootstrapDeterminismTest(unittest.TestCase):
    """Sanity: bootstrap from the same fixture index twice produces the same registry (no
    hidden nondeterminism like unsorted dict iteration or wall-clock-dependent fields beyond
    what the contract allows)."""

    def test_bootstrap_twice_same_index_same_registry(self):
        root1, reg1 = _bootstrap_registry(self)
        root2, reg2 = _bootstrap_registry(self)
        self.assertEqual(reg1, reg2)


class SyncFoldsCandidatesTest(unittest.TestCase):
    """SPIKE 3.4 write-contention fix (review C1): sources/candidates.jsonl folds new domains
    into candidate entries; registry.py sync [--root PATH] performs the fold."""

    def setUp(self):
        self.root, self.registry_before = _bootstrap_registry(self)
        self.sources_dir = os.path.join(self.root, "sources")

    def test_new_domain_in_candidates_becomes_candidate_entry(self):
        """A domain absent from the bootstrapped registry, appended to candidates.jsonl,
        must appear after sync with status candidate."""
        H.write_jsonl(os.path.join(self.sources_dir, "candidates.jsonl"), [
            {"domain": "freshvoice.example", "first_seen": "2026-07-05",
             "via": "search", "stream": "news", "url": "https://freshvoice.example/a1"},
        ])
        proc = H.run_script(self, "registry.py", ["sync", "--root", self.root])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(os.path.join(self.sources_dir, "registry.yml")) as f:
            reg = yamllite.load(f.read())
        self.assertIn("freshvoice.example", reg)
        self.assertEqual(reg["freshvoice.example"]["status"], "candidate")

    def test_candidate_entry_for_domain_already_registered_does_not_downgrade_status(self):
        """srf.ch is already established from bootstrap; a candidates.jsonl entry for it
        (e.g. a late-arriving duplicate signal) must not knock it back to candidate."""
        H.write_jsonl(os.path.join(self.sources_dir, "candidates.jsonl"), [
            {"domain": "srf.ch", "first_seen": "2026-07-05",
             "via": "search", "stream": "news", "url": "https://www.srf.ch/news/dup"},
        ])
        proc = H.run_script(self, "registry.py", ["sync", "--root", self.root])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(os.path.join(self.sources_dir, "registry.yml")) as f:
            reg = yamllite.load(f.read())
        self.assertEqual(reg["srf.ch"]["status"], "established")

    def test_new_hub_pattern_domain_still_classed_hub_as_candidate(self):
        """biorxiv.org matches the fixed hub set but is absent from the bootstrap fixture;
        as a fresh candidates.jsonl entry it must still be classed hub."""
        H.write_jsonl(os.path.join(self.sources_dir, "candidates.jsonl"), [
            {"domain": "biorxiv.org", "first_seen": "2026-07-05",
             "via": "t3-lead", "stream": "science", "url": "https://www.biorxiv.org/content/x1"},
        ])
        proc = H.run_script(self, "registry.py", ["sync", "--root", self.root])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(os.path.join(self.sources_dir, "registry.yml")) as f:
            reg = yamllite.load(f.read())
        self.assertEqual(reg["biorxiv.org"]["class"], "hub")
        self.assertEqual(reg["biorxiv.org"]["status"], "candidate")


class SyncFoldsLastCitedAsMaxTest(unittest.TestCase):
    """SPIKE 3.4: 'last_cited folds as max()' from sources/last-cited.jsonl."""

    def setUp(self):
        self.root, self.registry_before = _bootstrap_registry(self)
        self.sources_dir = os.path.join(self.root, "sources")

    def test_last_cited_folds_forward_to_the_max_of_multiple_entries(self):
        """srf.ch's bootstrapped last_cited is 2026-07-01; two out-of-order last-cited.jsonl
        entries (one older, one newer) must fold to the max, 2026-07-03."""
        self.assertEqual(self.registry_before["srf.ch"]["last_cited"], "2026-07-01")
        H.write_jsonl(os.path.join(self.sources_dir, "last-cited.jsonl"), [
            {"domain": "srf.ch", "date": "2026-06-20", "stream": "news"},
            {"domain": "srf.ch", "date": "2026-07-03", "stream": "news"},
        ])
        proc = H.run_script(self, "registry.py", ["sync", "--root", self.root])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(os.path.join(self.sources_dir, "registry.yml")) as f:
            reg = yamllite.load(f.read())
        self.assertEqual(reg["srf.ch"]["last_cited"], "2026-07-03")

    def test_last_cited_entry_older_than_current_does_not_regress(self):
        """A last-cited.jsonl entry older than the existing last_cited must not move it
        backwards -- fold is max(), not last-write-wins."""
        H.write_jsonl(os.path.join(self.sources_dir, "last-cited.jsonl"), [
            {"domain": "srf.ch", "date": "2026-01-01", "stream": "news"},
        ])
        proc = H.run_script(self, "registry.py", ["sync", "--root", self.root])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(os.path.join(self.sources_dir, "registry.yml")) as f:
            reg = yamllite.load(f.read())
        self.assertEqual(reg["srf.ch"]["last_cited"], "2026-07-01")


class SyncTruncatesAndIsIdempotentTest(unittest.TestCase):
    """SPIKE 3.4: candidates.jsonl / last-cited.jsonl are truncated after the fold; sync is
    idempotent (contract: 'then truncates both jsonl files; idempotent')."""

    def setUp(self):
        self.root, _ = _bootstrap_registry(self)
        self.sources_dir = os.path.join(self.root, "sources")
        H.write_jsonl(os.path.join(self.sources_dir, "candidates.jsonl"), [
            {"domain": "freshvoice.example", "first_seen": "2026-07-05",
             "via": "search", "stream": "news", "url": "https://freshvoice.example/a1"},
        ])
        H.write_jsonl(os.path.join(self.sources_dir, "last-cited.jsonl"), [
            {"domain": "srf.ch", "date": "2026-07-03", "stream": "news"},
        ])

    def test_jsonl_files_are_empty_after_sync(self):
        proc = H.run_script(self, "registry.py", ["sync", "--root", self.root])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for fname in ("candidates.jsonl", "last-cited.jsonl"):
            path = os.path.join(self.sources_dir, fname)
            self.assertTrue(os.path.exists(path), "%s should still exist (truncated, not deleted)" % fname)
            with open(path) as f:
                content = f.read()
            self.assertEqual(content.strip(), "", "%s should be empty after sync" % fname)

    def test_second_sync_on_empty_jsonls_is_a_no_op(self):
        proc1 = H.run_script(self, "registry.py", ["sync", "--root", self.root])
        self.assertEqual(proc1.returncode, 0, proc1.stderr)
        with open(os.path.join(self.sources_dir, "registry.yml")) as f:
            reg_after_first = f.read()

        proc2 = H.run_script(self, "registry.py", ["sync", "--root", self.root])
        self.assertEqual(proc2.returncode, 0, proc2.stderr)
        with open(os.path.join(self.sources_dir, "registry.yml")) as f:
            reg_after_second = f.read()

        self.assertEqual(reg_after_first, reg_after_second,
                          "sync on already-empty jsonls must be a byte-identical no-op")


if __name__ == "__main__":
    unittest.main()
