"""RED-phase spec tests for tools/sources/lint.py -- SPIKE-2026-07-07-continuous-news.md
section 4 ("Caps, discovery quota, [new source] tag integrity ... deterministic, lint.py at
Step C.25; hard-fail (report-only until armed)") + the sources contract's lint.py clause.

lint.py <post.md> [--root PATH] [--arm] is CLI-only, so every test writes a small brief post
(the real register: '- **Bold lead** ...[Source](url)' bullets for news/ai-ml, '### Heading'
blocks for science/weekend, plus a Coverage-footer '- Discovery: ...' line) into a tempdir,
points --root at a copy of fixtures/sources/registry_static.yml (srf.ch/aljazeera.com
established outlet, letemps.ch probation outlet, state.gov probation institutional,
arxiv.org established hub -- biorxiv.org and any *.example domain are deliberately absent,
i.e. genuinely unregistered), and asserts on exit code + stdout.

Each fixture is built to isolate ONE violation category at a time (contract's check (3)
groups outlet-cap/institutional-bar/discovery-quota together as the categories that gate
`--arm` exit 1, per 'With --arm: exit 1 on cap/quota/tag violations' -- footer *format*
violations are deliberately excluded from that list, so those fixtures pin `--arm` -> exit 0
even though something is still wrong and reported).
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

import sources_helpers as H

REGISTRY_FIXTURE = os.path.join(H.FIXTURES_DIR, "registry_static.yml")
ANCHOR_PATH = os.path.join(H.REPO_ROOT, "tools", "store", "anchor.py")


def bullet(lead, url, source="Source", tag=None, extra_url=None, extra_source="Also"):
    tag_txt = (" " + tag) if tag else ""
    extra = f" ([{extra_source}]({extra_url}))" if extra_url else ""
    return f"- **{lead}** Some neutral summary sentence about the story.{tag_txt} ([{source}]({url})){extra}"


def heading_block(title, url, source="Source", tag=None):
    tag_txt = (" " + tag) if tag else ""
    return (
        f"### {title}\n"
        f"**[{source}]({url})**{tag_txt} · Some Author et al. · published 2026-07-10\n"
        f"Prose explaining the finding in a couple of neutral sentences.\n"
        f"*Why it matters:* one sentence of editorial context.\n"
    )


def build_post(slug, section_title, items, discovery_lines, extra_footer=""):
    body = "\n".join(items)
    discovery_block = "\n".join(discovery_lines)
    return f"""---
layout: single
title: "{slug.title()} -- 2026-07-10"
date: 2026-07-10T09:00:00+02:00
categories: [{slug}]
---

# {slug.title()} -- 2026-07-10

_Generated 2026-07-10T09:00:00+02:00 Europe/Zurich._

## {section_title}
{body}

---

## Coverage footer
- Sources used: T2 = {len(items)} citations
{extra_footer}{discovery_block}
"""


class LintTestBase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="sources-lint-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        sources_dir = os.path.join(self.root, "sources")
        os.makedirs(sources_dir, exist_ok=True)
        shutil.copy(REGISTRY_FIXTURE, os.path.join(sources_dir, "registry.yml"))
        self.posts_dir = os.path.join(self.root, "_posts")
        os.makedirs(self.posts_dir, exist_ok=True)

    def write_post(self, filename, content):
        path = os.path.join(self.posts_dir, filename)
        with open(path, "w") as f:
            f.write(content)
        return path

    def lint(self, post_path, arm=False, extra_args=None):
        args = [post_path, "--root", self.root]
        if arm:
            args.append("--arm")
        if extra_args:
            args.extend(extra_args)
        return H.run_script(self, "lint.py", args)

    def assert_report_only_always_exits_zero(self, post_path):
        proc = self.lint(post_path, arm=False)
        self.assertEqual(proc.returncode, 0,
                          "report-only mode (no --arm) must always exit 0.\nstdout:\n%s\nstderr:\n%s"
                          % (proc.stdout, proc.stderr))
        return proc


# ---------------------------------------------------------------------------
# Baseline: fully compliant edition -> zero violations in any mode.
# ---------------------------------------------------------------------------

class CleanEditionTest(LintTestBase):
    """A fully compliant news edition: cap respected, tag correct, footer valid singular
    'met', quota satisfied -- and the two-link bullet proves domain attribution uses the
    FIRST link only (anchor.py's own rule, reused here for consistency): srf.ch appears as
    a *second* link inside the b3 bullet and must not push srf.ch's cap count to 3."""

    def test_clean_news_edition_has_no_violations(self):
        items = [
            bullet("Bern story one.", "https://www.srf.ch/news/b1"),
            bullet("Bern story two.", "https://www.srf.ch/news/b2"),
            bullet("Two-source item.", "https://new-face.example/x1", source="NewFace",
                   tag="[new source]", extra_url="https://www.srf.ch/news/dup", extra_source="SRF"),
        ]
        post = build_post("news", "News", items,
                           ["- Discovery: met (new-face.example, first citation for the desk)"])
        path = self.write_post("2026-07-10-news.md", post)

        proc = self.assert_report_only_always_exits_zero(path)
        self.assertNotIn("LINT-REPORT", proc.stdout,
                          "a fully compliant edition should produce no LINT-REPORT lines")

        armed = self.lint(path, arm=True)
        self.assertEqual(armed.returncode, 0, "clean edition must exit 0 even with --arm")

    def test_waived_with_zero_new_citations_is_also_clean(self):
        """A legitimate waiver needs no new-source tag at all to be violation-free."""
        items = [bullet("Only story.", "https://www.srf.ch/news/c1")]
        post = build_post("news", "News", items,
                           ["- Discovery: waived — nothing new pursued this cycle"])
        path = self.write_post("2026-07-10-news.md", post)
        proc = self.assert_report_only_always_exits_zero(path)
        self.assertNotIn("LINT-REPORT", proc.stdout)
        armed = self.lint(path, arm=True)
        self.assertEqual(armed.returncode, 0)


# ---------------------------------------------------------------------------
# FINDING 1 (CRITICAL): Step C.25 runs anchor.py BEFORE lint.py -- lint.py must still
# recognize a bullet anchor.py has already rewritten to
# '- <a id="st-..." class="st-a"></a>**lead**...', or every anchored brief gets zero
# tag/cap checks and a false discovery_quota violation whenever the footer says met.
# ---------------------------------------------------------------------------

class AnchorThenLintTest(LintTestBase):
    def test_citations_still_extracted_after_anchor_py_rewrites_the_bullets(self):
        items = [
            bullet("Bern story one.", "https://www.srf.ch/news/anchor1"),
            bullet("Fresh outlet story.", "https://freshvoice.example/anchor2", source="Fresh",
                   tag="[new source]"),
        ]
        post = build_post("news", "News", items,
                           ["- Discovery: met (freshvoice.example, first citation for the desk)"])
        path = self.write_post("2026-07-10-news.md", post)

        anchor_proc = subprocess.run([sys.executable, ANCHOR_PATH, path],
                                      capture_output=True, text=True)
        self.assertEqual(anchor_proc.returncode, 0, anchor_proc.stderr)
        with open(path) as f:
            anchored = f.read()
        self.assertIn('class="st-a"', anchored,
                       "fixture wasn't actually anchored by anchor.py -- test would be vacuous")

        proc = self.assert_report_only_always_exits_zero(path)
        self.assertNotIn("LINT-REPORT", proc.stdout,
                          "an anchor.py-rewritten bullet must still be recognized as a citation "
                          "line, not silently dropped:\nstdout:\n%s" % proc.stdout)

        armed = self.lint(path, arm=True)
        self.assertEqual(armed.returncode, 0,
                          "anchored bullets must not produce a false discovery_quota violation "
                          "(zero citations extracted looks like zero novel domains)")


# ---------------------------------------------------------------------------
# Check (1): [new source] tag integrity, recomputed against the registry.
# ---------------------------------------------------------------------------

class TagIntegrityTest(LintTestBase):
    def test_unregistered_domain_missing_tag_is_a_violation(self):
        """quietvoice.example is absent from registry_static.yml and cited without the
        literal tag -- must be flagged, and --arm must exit 1 (tag category)."""
        items = [
            bullet("Registered story.", "https://www.srf.ch/news/d1"),
            bullet("Unlisted story.", "https://quietvoice.example/a1"),
        ]
        post = build_post("news", "News", items, ["- Discovery: waived — untagged find"])
        path = self.write_post("2026-07-10-news.md", post)

        proc = self.assert_report_only_always_exits_zero(path)
        self.assertIn("LINT-REPORT", proc.stdout)
        self.assertIn("quietvoice.example", proc.stdout)

        armed = self.lint(path, arm=True)
        self.assertEqual(armed.returncode, 1, "a missing [new source] tag must gate --arm exit 1")

    def test_tag_on_a_registered_domain_is_a_violation(self):
        """srf.ch IS registered (established); tagging it [new source] is a false novelty
        claim and must be flagged even though the domain itself is otherwise fine."""
        items = [bullet("Falsely tagged story.", "https://www.srf.ch/news/e1", tag="[new source]")]
        post = build_post("news", "News", items, ["- Discovery: waived — n/a"])
        path = self.write_post("2026-07-10-news.md", post)

        proc = self.assert_report_only_always_exits_zero(path)
        self.assertIn("LINT-REPORT", proc.stdout)
        self.assertIn("srf.ch", proc.stdout)

        armed = self.lint(path, arm=True)
        self.assertEqual(armed.returncode, 1)

    def test_backticked_tag_form_is_recognized(self):
        """Both `[new source]` (backticked, as science/weekend already write [preprint] /
        [single-source]) and plain [new source] (as news already writes [single-source])
        appear in the real corpus -- tag detection must tolerate either."""
        items = [bullet("Backticked tag story.", "https://freshvoice.example/a1",
                        source="Fresh", tag="`[new source]`")]
        post = build_post("news", "News", items,
                           ["- Discovery: met (freshvoice.example)"])
        path = self.write_post("2026-07-10-news.md", post)
        proc = self.assert_report_only_always_exits_zero(path)
        self.assertNotIn("LINT-REPORT", proc.stdout,
                          "the backticked `[new source]` form must be recognized as a valid tag")


# ---------------------------------------------------------------------------
# Check (3): per-domain outlet cap (max 2, hubs exempt), institutional 30% bar.
# ---------------------------------------------------------------------------

class OutletCapTest(LintTestBase):
    def test_outlet_over_cap_is_flagged_hub_is_exempt(self):
        """srf.ch cited 3x (> cap of 2) must be flagged; arxiv.org cited 3x (hub) must not."""
        items = [
            bullet("SRF story 1.", "https://www.srf.ch/news/f1"),
            bullet("SRF story 2.", "https://www.srf.ch/news/f2"),
            bullet("SRF story 3.", "https://www.srf.ch/news/f3"),
            bullet("Paper A.", "https://arxiv.org/abs/2607.00010", source="arXiv"),
            bullet("Paper B.", "https://arxiv.org/abs/2607.00011", source="arXiv"),
            bullet("Paper C.", "https://arxiv.org/abs/2607.00012", source="arXiv"),
            bullet("Fresh outlet.", "https://freshvoice.example/z1", source="Fresh", tag="[new source]"),
        ]
        post = build_post("news", "News", items, ["- Discovery: met (freshvoice.example)"])
        path = self.write_post("2026-07-10-news.md", post)

        proc = self.assert_report_only_always_exits_zero(path)
        self.assertIn("LINT-REPORT", proc.stdout)
        self.assertIn("srf.ch", proc.stdout)
        self.assertNotIn("arxiv.org", proc.stdout, "hub domains are cap-exempt and must not be reported")

        armed = self.lint(path, arm=True)
        self.assertEqual(armed.returncode, 1)

    def test_institutional_domain_under_thirty_percent_is_fine(self):
        """state.gov at 1/8 = 12.5%, comfortably under the institutional 30% bar -- no
        violation, contrasted with the over-bar case below."""
        items = [
            bullet("Gov item.", "https://www.state.gov/press/g1"),
            bullet("SRF 1.", "https://www.srf.ch/news/g2"),
            bullet("SRF 2.", "https://www.srf.ch/news/g3"),
            bullet("LeTemps 1.", "https://www.letemps.ch/articles/g4"),
            bullet("LeTemps 2.", "https://www.letemps.ch/articles/g5"),
            bullet("AlJazeera 1.", "https://www.aljazeera.com/news/g6", source="Al Jazeera"),
            bullet("AlJazeera 2.", "https://www.aljazeera.com/news/g7", source="Al Jazeera"),
            bullet("Fresh outlet.", "https://freshvoice.example/g8", source="Fresh", tag="[new source]"),
        ]
        post = build_post("news", "News", items, ["- Discovery: met (freshvoice.example)"])
        path = self.write_post("2026-07-10-news.md", post)
        proc = self.assert_report_only_always_exits_zero(path)
        self.assertNotIn("LINT-REPORT", proc.stdout)

    def test_institutional_domain_over_thirty_percent_is_flagged(self):
        """state.gov at 4/10 = 40% > the institutional 30% bar -- flagged even though 4
        citations would also break a flat outlet cap, because state.gov is institutional,
        not outlet (isolated here with a waived footer so quota noise can't leak in)."""
        items = [
            bullet("Gov 1.", "https://www.state.gov/press/h1"),
            bullet("Gov 2.", "https://www.state.gov/press/h2"),
            bullet("Gov 3.", "https://www.state.gov/press/h3"),
            bullet("Gov 4.", "https://www.state.gov/press/h4"),
            bullet("SRF 1.", "https://www.srf.ch/news/h5"),
            bullet("SRF 2.", "https://www.srf.ch/news/h6"),
            bullet("LeTemps 1.", "https://www.letemps.ch/articles/h7"),
            bullet("LeTemps 2.", "https://www.letemps.ch/articles/h8"),
            bullet("AlJazeera 1.", "https://www.aljazeera.com/news/h9", source="Al Jazeera"),
            bullet("AlJazeera 2.", "https://www.aljazeera.com/news/h10", source="Al Jazeera"),
        ]
        post = build_post("news", "News", items, ["- Discovery: waived — no new outlet found"])
        path = self.write_post("2026-07-10-news.md", post)

        proc = self.assert_report_only_always_exits_zero(path)
        self.assertIn("LINT-REPORT", proc.stdout)
        self.assertIn("state.gov", proc.stdout)

        armed = self.lint(path, arm=True)
        self.assertEqual(armed.returncode, 1)


class AiMlHubQuotaTest(LintTestBase):
    """Discovery quota nuance: 'ai-ml >=1 non-hub' -- a novel HUB-classed domain must not
    satisfy ai-ml's discovery quota, and hub citations never trip the outlet cap."""

    def test_hub_cited_four_times_is_cap_exempt_in_ai_ml_too(self):
        items = [
            bullet("Paper A.", "https://arxiv.org/abs/2607.00020", source="arXiv"),
            bullet("Paper B.", "https://arxiv.org/abs/2607.00021", source="arXiv"),
            bullet("Paper C.", "https://arxiv.org/abs/2607.00022", source="arXiv"),
            bullet("Paper D.", "https://arxiv.org/abs/2607.00023", source="arXiv"),
            bullet("New lab.", "https://smallresearchlab.example/p1", source="SmallLab", tag="[new source]"),
        ]
        post = build_post("ai-ml", "AI/ML", items,
                           ["- Discovery: met (smallresearchlab.example, a non-hub first citation)"])
        path = self.write_post("2026-07-10-ai-ml.md", post)
        proc = self.assert_report_only_always_exits_zero(path)
        self.assertNotIn("LINT-REPORT", proc.stdout)
        armed = self.lint(path, arm=True)
        self.assertEqual(armed.returncode, 0)

    def test_new_hub_domain_alone_does_not_satisfy_ai_ml_quota(self):
        """biorxiv.org is absent from registry_static.yml (genuinely novel) and correctly
        tagged -- so the TAG check is clean -- but it is hub-classed by the fixed domain
        set, so it must not count toward ai-ml's non-hub discovery quota. The footer's
        claim of 'met' is therefore false."""
        items = [
            bullet("Paper A.", "https://arxiv.org/abs/2607.00030", source="arXiv"),
            bullet("Preprint.", "https://www.biorxiv.org/content/x1", source="bioRxiv", tag="[new source]"),
        ]
        post = build_post("ai-ml", "AI/ML", items,
                           ["- Discovery: met (biorxiv.org)"])
        path = self.write_post("2026-07-10-ai-ml.md", post)

        proc = self.assert_report_only_always_exits_zero(path)
        self.assertIn("LINT-REPORT", proc.stdout)
        # The tag itself is correct (biorxiv.org really is unregistered) -- the violation
        # reported must be the quota mismatch, not a tag complaint.
        self.assertTrue("quota" in proc.stdout.lower() or "discovery" in proc.stdout.lower(),
                        "expected a discovery-quota violation to be reported:\n%s" % proc.stdout)

        armed = self.lint(path, arm=True)
        self.assertEqual(armed.returncode, 1)


# ---------------------------------------------------------------------------
# Check (2): Discovery footer exactly-one-line contract.
# ---------------------------------------------------------------------------

class DiscoveryFooterContractTest(LintTestBase):
    """Each fixture here keeps tag/cap/quota genuinely satisfied (one correctly-tagged,
    non-hub, novel citation for a news post) so the ONLY defect is the footer line itself
    -- and per the contract's enumerated exit-1 categories ('cap/quota/tag'), a pure footer
    violation must still exit 0 even under --arm."""

    def _compliant_items(self):
        return [
            bullet("Registered story.", "https://www.srf.ch/news/i1"),
            bullet("Novel story.", "https://novelvoice.example/i2", source="Novel", tag="[new source]"),
        ]

    def test_missing_discovery_line_is_flagged_but_does_not_gate_arm(self):
        post = build_post("news", "News", self._compliant_items(), [])  # no Discovery line at all
        path = self.write_post("2026-07-10-news.md", post)

        proc = self.assert_report_only_always_exits_zero(path)
        self.assertIn("LINT-REPORT", proc.stdout)
        self.assertIn("Discovery", proc.stdout)

        armed = self.lint(path, arm=True)
        self.assertEqual(armed.returncode, 0, "a footer-only violation must not gate --arm exit 1")

    def test_duplicate_discovery_lines_is_flagged_but_does_not_gate_arm(self):
        post = build_post("news", "News", self._compliant_items(), [
            "- Discovery: met (novelvoice.example)",
            "- Discovery: waived — redundant second line",
        ])
        path = self.write_post("2026-07-10-news.md", post)

        proc = self.assert_report_only_always_exits_zero(path)
        self.assertIn("LINT-REPORT", proc.stdout)
        self.assertIn("Discovery", proc.stdout)

        armed = self.lint(path, arm=True)
        self.assertEqual(armed.returncode, 0)

    def test_malformed_discovery_line_is_flagged_but_does_not_gate_arm(self):
        post = build_post("news", "News", self._compliant_items(), [
            "- Discovery: unsure, maybe?",
        ])
        path = self.write_post("2026-07-10-news.md", post)

        proc = self.assert_report_only_always_exits_zero(path)
        self.assertIn("LINT-REPORT", proc.stdout)
        self.assertIn("Discovery", proc.stdout)

        armed = self.lint(path, arm=True)
        self.assertEqual(armed.returncode, 0)

    def test_single_valid_met_line_has_no_footer_violation(self):
        post = build_post("news", "News", self._compliant_items(), [
            "- Discovery: met (novelvoice.example, first citation)",
        ])
        path = self.write_post("2026-07-10-news.md", post)
        proc = self.assert_report_only_always_exits_zero(path)
        self.assertNotIn("LINT-REPORT", proc.stdout)


# ---------------------------------------------------------------------------
# Check (3) continued: discovery-quota realization vs. the footer's claim.
# ---------------------------------------------------------------------------

class DiscoveryQuotaRealizationTest(LintTestBase):
    """The Discovery footer's claim is recomputed, never trusted (mirrors the tag-integrity
    check's own framing): claiming 'met' with zero genuinely novel anchors is a violation,
    distinct from -- and, per the contract, MORE severe than (it gates --arm) -- a pure
    footer-format defect."""

    def test_news_quota_one_claimed_met_with_zero_new_citations_is_a_violation(self):
        items = [bullet("Only registered story.", "https://www.srf.ch/news/j1")]
        post = build_post("news", "News", items, ["- Discovery: met (nothing notable found)"])
        path = self.write_post("2026-07-10-news.md", post)

        proc = self.assert_report_only_always_exits_zero(path)
        self.assertIn("LINT-REPORT", proc.stdout)

        armed = self.lint(path, arm=True)
        self.assertEqual(armed.returncode, 1, "a false 'met' claim (0 < quota) must gate --arm exit 1")

    def test_science_quota_two_satisfied_by_two_tagged_domains_is_clean(self):
        """Science's discovery quota is >=2; two distinct correctly-tagged novel domains in
        heading-register blocks satisfy it exactly."""
        items = [
            heading_block("A physics result", "https://arxiv.org/abs/2607.00040", source="arXiv"),
            heading_block("A biology result", "https://labresult.example/k1", source="LabResult",
                          tag="[new source]"),
            heading_block("A chemistry result", "https://otherlab.example/k2", source="OtherLab",
                          tag="[new source]"),
        ]
        post = build_post("science", "Physics & biology", items,
                           ["- Discovery: met (labresult.example, otherlab.example)"])
        path = self.write_post("2026-07-10-science.md", post)

        proc = self.assert_report_only_always_exits_zero(path)
        self.assertNotIn("LINT-REPORT", proc.stdout)
        armed = self.lint(path, arm=True)
        self.assertEqual(armed.returncode, 0)

    def test_weekend_quota_two_under_satisfied_by_one_tag_is_a_violation(self):
        """Weekend's discovery quota is also >=2; only one tagged novel domain plus a false
        'met' claim must be flagged and gate --arm."""
        items = [
            heading_block("Week's top physics story", "https://arxiv.org/abs/2607.00050", source="arXiv"),
            heading_block("A single new find", "https://onlylab.example/l1", source="OnlyLab",
                          tag="[new source]"),
        ]
        post = build_post("weekend", "Deep read", items, ["- Discovery: met (onlylab.example)"])
        path = self.write_post("2026-07-10-weekend.md", post)

        proc = self.assert_report_only_always_exits_zero(path)
        self.assertIn("LINT-REPORT", proc.stdout)

        armed = self.lint(path, arm=True)
        self.assertEqual(armed.returncode, 1)


# ---------------------------------------------------------------------------
# candidates.jsonl side effect + --dry-run.
# ---------------------------------------------------------------------------

class CandidatesAppendTest(LintTestBase):
    """Contract: 'Also appends newly tagged [new source] domains to sources/candidates.jsonl
    (report-only mode included; --dry-run flag skips writes).'"""

    def _tagged_post(self):
        items = [bullet("Fresh find.", "https://newkid.example/m1", source="NewKid", tag="[new source]")]
        post = build_post("news", "News", items, ["- Discovery: met (newkid.example)"])
        return self.write_post("2026-07-10-news.md", post)

    def test_tagged_domain_is_appended_to_candidates_jsonl(self):
        path = self._tagged_post()
        candidates_path = os.path.join(self.root, "sources", "candidates.jsonl")
        self.assertFalse(os.path.exists(candidates_path))

        proc = self.lint(path, arm=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        records = H.read_jsonl(candidates_path)
        domains = [r.get("domain") for r in records]
        self.assertIn("newkid.example", domains)

    def test_append_preserves_pre_existing_lines(self):
        path = self._tagged_post()
        candidates_path = os.path.join(self.root, "sources", "candidates.jsonl")
        H.write_jsonl(candidates_path, [
            {"domain": "priorvoice.example", "first_seen": "2026-07-01",
             "via": "search", "stream": "news", "url": "https://priorvoice.example/x"},
        ])
        proc = self.lint(path, arm=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        records = H.read_jsonl(candidates_path)
        domains = {r.get("domain") for r in records}
        self.assertIn("priorvoice.example", domains, "append must not clobber pre-existing lines")
        self.assertIn("newkid.example", domains)

    def test_dry_run_skips_the_write(self):
        path = self._tagged_post()
        candidates_path = os.path.join(self.root, "sources", "candidates.jsonl")
        proc = self.lint(path, arm=False, extra_args=["--dry-run"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(H.read_jsonl(candidates_path), [],
                          "--dry-run must write nothing to sources/candidates.jsonl")


if __name__ == "__main__":
    unittest.main()
