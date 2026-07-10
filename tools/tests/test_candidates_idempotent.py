"""RED-phase spec tests for tools/sources/lint.py's append_candidates() idempotency.

Production defect (git show 2abc291, News -- 2026-07-09): within a single writer fire,
lint.py appended the same domain to sources/candidates.jsonl multiple times -- state.gov,
thehill.com, climate.copernicus.eu were each appended TWICE in one commit, inflating the
candidates_open health metric (raw line count 10 vs. 7 distinct domains).

Required behavior (this spec):
  - A domain cited more than once (with [new source] tags) in the SAME lint.py invocation
    must produce at most one new candidates.jsonl line for that domain.
  - A domain already present anywhere in the existing sources/candidates.jsonl must produce
    ZERO new lines for that domain, even if freshly [new source]-tagged again in this post.
  - Distinct, genuinely-new domains must still each get appended (dedup must not become a
    no-op).
  - Append-only otherwise: pre-existing lines in candidates.jsonl must never be rewritten,
    reordered, or dropped -- only new lines may be added, at the end.

lint.py <post.md> [--root PATH] [--arm] [--dry-run] is CLI-only (see tools/sources/lint.py's
module docstring and test_sources_lint.py's own framing), so this spec black-boxes it via
subprocess through the shared sources_helpers harness, exactly like test_sources_lint.py's
CandidatesAppendTest -- these tests isolate the idempotency dimension that suite does not
cover (it only checks a single tagged domain appends, and that pre-existing lines survive one
run; it never exercises "same domain twice" or "domain already on file").
"""
import os
import shutil
import tempfile
import unittest

import sources_helpers as H

REGISTRY_FIXTURE = os.path.join(H.FIXTURES_DIR, "registry_static.yml")


def bullet(lead, url, source="Source", tag=None):
    tag_txt = (" " + tag) if tag else ""
    return f"- **{lead}** Some neutral summary sentence about the story.{tag_txt} ([{source}]({url}))"


def build_post(slug, items, discovery_lines):
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

## {slug.title()}
{body}

---

## Coverage footer
- Sources used: T2 = {len(items)} citations
{discovery_block}
"""


class CandidatesIdempotentTestBase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="sources-candidates-idempotent-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        sources_dir = os.path.join(self.root, "sources")
        os.makedirs(sources_dir, exist_ok=True)
        shutil.copy(REGISTRY_FIXTURE, os.path.join(sources_dir, "registry.yml"))
        self.posts_dir = os.path.join(self.root, "_posts")
        os.makedirs(self.posts_dir, exist_ok=True)
        self.candidates_path = os.path.join(sources_dir, "candidates.jsonl")

    def write_post(self, filename, content):
        path = os.path.join(self.posts_dir, filename)
        with open(path, "w") as f:
            f.write(content)
        return path

    def lint(self, post_path, extra_args=None):
        args = [post_path, "--root", self.root]
        if extra_args:
            args.extend(extra_args)
        return H.run_script(self, "lint.py", args)


# ---------------------------------------------------------------------------
# Same domain cited twice, tagged [new source] both times, in ONE invocation.
# ---------------------------------------------------------------------------

class SameDomainTwiceInOneCallTest(CandidatesIdempotentTestBase):
    def test_domain_cited_twice_in_one_post_yields_one_candidates_line(self):
        """duplicatefind.example is absent from registry_static.yml -- both citations are
        genuinely novel and correctly tagged, and 2 citations of the same domain is within
        the outlet cap (2), so this isolates dedup from any cap/quota noise. Before the fix,
        lint.py appended one line PER tagged citation -- i.e. two lines for one domain,
        exactly the git-show-2abc291 defect (state.gov/thehill.com/climate.copernicus.eu each
        appended twice from a single writer fire)."""
        items = [
            bullet("First mention.", "https://duplicatefind.example/a1", source="DupFind",
                   tag="[new source]"),
            bullet("Second mention.", "https://duplicatefind.example/a2", source="DupFind",
                   tag="[new source]"),
        ]
        post = build_post("news", items, ["- Discovery: met (duplicatefind.example)"])
        path = self.write_post("2026-07-10-news.md", post)

        proc = self.lint(path)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        records = H.read_jsonl(self.candidates_path)
        dup_records = [r for r in records if r.get("domain") == "duplicatefind.example"]
        self.assertEqual(
            len(dup_records), 1,
            "a domain cited twice (both [new source]-tagged) in the SAME invocation must "
            "produce exactly one candidates.jsonl line, not one per citation:\n%r" % records,
        )

    def test_three_citations_of_the_same_domain_still_yield_one_line(self):
        """Widen the margin past 'exactly 2' to rule out an off-by-one dedup (e.g. a set that
        accidentally only collapses the first pair). Uses a hub domain (cap-exempt) so 3
        citations of the same domain can't trip the unrelated outlet-cap check."""
        items = [
            bullet("Preprint one.", "https://triplefind.example/b1", source="TripleFind",
                   tag="[new source]"),
            bullet("Preprint two.", "https://triplefind.example/b2", source="TripleFind",
                   tag="[new source]"),
            bullet("Preprint three.", "https://triplefind.example/b3", source="TripleFind",
                   tag="[new source]"),
        ]
        post = build_post("news", items, ["- Discovery: met (triplefind.example)"])
        path = self.write_post("2026-07-10-news.md", post)

        proc = self.lint(path)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        records = H.read_jsonl(self.candidates_path)
        matches = [r for r in records if r.get("domain") == "triplefind.example"]
        self.assertEqual(len(matches), 1,
                          "3 citations of one domain in one call must still yield exactly 1 "
                          "candidates.jsonl line:\n%r" % records)


# ---------------------------------------------------------------------------
# Domain already present in sources/candidates.jsonl before this invocation.
# ---------------------------------------------------------------------------

class DomainAlreadyOnFileTest(CandidatesIdempotentTestBase):
    def test_domain_already_in_file_gets_zero_new_lines(self):
        """priorfind.example was already recorded (e.g. by an earlier writer fire this same
        day) but is STILL absent from registry_static.yml -- so today's citation is still
        legitimately [new source]-tagged from the prose's point of view. append_candidates
        must nonetheless recognize the domain is already on file and add nothing."""
        H.write_jsonl(self.candidates_path, [
            {"domain": "priorfind.example", "first_seen": "2026-07-09", "via": "writer",
             "stream": "news", "url": "https://priorfind.example/earlier"},
        ])
        items = [bullet("Same outlet again.", "https://priorfind.example/c1",
                        source="PriorFind", tag="[new source]")]
        post = build_post("news", items, ["- Discovery: met (priorfind.example)"])
        path = self.write_post("2026-07-10-news.md", post)

        proc = self.lint(path)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        records = H.read_jsonl(self.candidates_path)
        matches = [r for r in records if r.get("domain") == "priorfind.example"]
        self.assertEqual(
            len(matches), 1,
            "a domain already present in candidates.jsonl before this invocation must get "
            "zero additional lines, not a second one:\n%r" % records,
        )

    def test_domain_already_on_file_multiple_times_this_call_still_adds_nothing(self):
        """Combines both dedup paths: repeatfind.example is both already on file AND cited
        twice (tagged) in this same post -- must still add nothing at all."""
        H.write_jsonl(self.candidates_path, [
            {"domain": "repeatfind.example", "first_seen": "2026-07-08", "via": "search",
             "stream": "news", "url": "https://repeatfind.example/earlier"},
        ])
        items = [
            bullet("Mention one.", "https://repeatfind.example/d1", source="RepeatFind",
                   tag="[new source]"),
            bullet("Mention two.", "https://repeatfind.example/d2", source="RepeatFind",
                   tag="[new source]"),
        ]
        post = build_post("news", items, ["- Discovery: met (repeatfind.example)"])
        path = self.write_post("2026-07-10-news.md", post)

        proc = self.lint(path)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        records = H.read_jsonl(self.candidates_path)
        matches = [r for r in records if r.get("domain") == "repeatfind.example"]
        self.assertEqual(len(matches), 1,
                          "already-on-file + repeated-in-call must still net zero new lines "
                          "(one pre-existing line total, nothing appended):\n%r" % records)


# ---------------------------------------------------------------------------
# Distinct, genuinely-new domains must still append (dedup isn't a global no-op).
# ---------------------------------------------------------------------------

class DistinctDomainsStillAppendTest(CandidatesIdempotentTestBase):
    def test_two_distinct_new_domains_each_get_their_own_line(self):
        items = [
            bullet("Outlet alpha.", "https://alphafind.example/e1", source="AlphaFind",
                   tag="[new source]"),
            bullet("Outlet beta.", "https://betafind.example/e2", source="BetaFind",
                   tag="[new source]"),
        ]
        post = build_post("news", items,
                           ["- Discovery: met (alphafind.example, betafind.example)"])
        path = self.write_post("2026-07-10-news.md", post)

        proc = self.lint(path)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        records = H.read_jsonl(self.candidates_path)
        domains = [r.get("domain") for r in records]
        self.assertEqual(
            sorted(domains), ["alphafind.example", "betafind.example"],
            "two distinct genuinely-new domains must each get exactly one line -- dedup must "
            "not suppress legitimate distinct appends:\n%r" % records,
        )

    def test_distinct_new_domain_appends_alongside_an_already_dedup_skipped_one(self):
        """oldfind.example is already on file (must add nothing); newfind.example is
        genuinely new in this call (must still be added) -- proves the dedup skip for one
        domain doesn't accidentally swallow a sibling append in the same invocation."""
        H.write_jsonl(self.candidates_path, [
            {"domain": "oldfind.example", "first_seen": "2026-07-05", "via": "writer",
             "stream": "news", "url": "https://oldfind.example/earlier"},
        ])
        items = [
            bullet("Old outlet again.", "https://oldfind.example/f1", source="OldFind",
                   tag="[new source]"),
            bullet("Brand new outlet.", "https://newfind.example/f2", source="NewFind",
                   tag="[new source]"),
        ]
        post = build_post("news", items,
                           ["- Discovery: met (oldfind.example, newfind.example)"])
        path = self.write_post("2026-07-10-news.md", post)

        proc = self.lint(path)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        records = H.read_jsonl(self.candidates_path)
        domains = [r.get("domain") for r in records]
        self.assertEqual(domains.count("oldfind.example"), 1,
                          "already-on-file domain must not gain a second line:\n%r" % records)
        self.assertEqual(domains.count("newfind.example"), 1,
                          "genuinely new domain in the same call must still be appended:\n%r"
                          % records)


# ---------------------------------------------------------------------------
# Append-only: pre-existing lines are never rewritten, reordered, or dropped.
# ---------------------------------------------------------------------------

class AppendOnlyPreservesExistingLinesTest(CandidatesIdempotentTestBase):
    def test_pre_existing_lines_are_untouched_verbatim_and_in_order(self):
        pre_existing = [
            {"domain": "firstprior.example", "first_seen": "2026-07-01", "via": "search",
             "stream": "news", "url": "https://firstprior.example/x"},
            {"domain": "secondprior.example", "first_seen": "2026-07-03", "via": "writer",
             "stream": "science", "url": "https://secondprior.example/y"},
            {"domain": "thirdprior.example", "first_seen": "2026-07-06", "via": "writer",
             "stream": "ai-ml", "url": "https://thirdprior.example/z"},
        ]
        H.write_jsonl(self.candidates_path, pre_existing)
        with open(self.candidates_path) as f:
            raw_before = f.read()

        items = [bullet("Brand new outlet.", "https://onlynewfind.example/g1",
                        source="OnlyNewFind", tag="[new source]")]
        post = build_post("news", items, ["- Discovery: met (onlynewfind.example)"])
        path = self.write_post("2026-07-10-news.md", post)

        proc = self.lint(path)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        with open(self.candidates_path) as f:
            raw_after = f.read()
        self.assertTrue(
            raw_after.startswith(raw_before),
            "append-only: every pre-existing byte must survive untouched, at its original "
            "position, with only new content appended after it.\nbefore:\n%r\nafter:\n%r"
            % (raw_before, raw_after),
        )

        records = H.read_jsonl(self.candidates_path)
        self.assertEqual(
            records[:3], pre_existing,
            "pre-existing records must not be rewritten or reordered:\n%r" % records,
        )
        domains = [r.get("domain") for r in records]
        self.assertEqual(
            domains,
            ["firstprior.example", "secondprior.example", "thirdprior.example",
             "onlynewfind.example"],
            "the new domain must be appended AFTER all pre-existing lines, in the same "
            "relative order they already had:\n%r" % records,
        )

    def test_dedup_skip_does_not_touch_the_matching_pre_existing_line(self):
        """When a cited domain is already on file, that specific pre-existing record must
        remain byte-identical (e.g. dedup must not 'refresh' first_seen or via in place)."""
        pre_existing = [
            {"domain": "staticfind.example", "first_seen": "2026-06-30", "via": "search",
             "stream": "news", "url": "https://staticfind.example/original"},
        ]
        H.write_jsonl(self.candidates_path, pre_existing)

        items = [bullet("Cited again today.", "https://staticfind.example/h1",
                        source="StaticFind", tag="[new source]")]
        post = build_post("news", items, ["- Discovery: met (staticfind.example)"])
        path = self.write_post("2026-07-10-news.md", post)

        proc = self.lint(path)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        records = H.read_jsonl(self.candidates_path)
        self.assertEqual(
            records, pre_existing,
            "a domain already on file must not just skip a NEW line -- the existing line "
            "itself must be left completely unmodified (no in-place refresh):\n%r" % records,
        )


if __name__ == "__main__":
    unittest.main()
