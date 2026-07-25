"""Schema tests over the LIVE sources/registry.yml -- the file every writer's fetch plan is built
from, and the one artifact in this repo that is routinely edited in bulk (47 entries were added by
script on 2026-07-25, and the Evaluator's apply step edits it by hand every week).

A malformed entry does not raise anywhere: preflight prints it, a writer tries to fetch it, and the
edition just quietly cites less. These tests are the missing failure signal. Every rule here was
derived from the live file and holds for all of it -- they pin real invariants, not aspirations.
"""
import importlib.util
import os
import unittest
from urllib.parse import urlparse

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
spec = importlib.util.spec_from_file_location(
    "_registry", os.path.join(REPO, "tools", "sources", "registry.py"))
registry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(registry)

CLASSES = {"outlet", "hub", "institutional"}
TIERS = {"T1", "T2"}
STATUSES = {"candidate", "probation", "established", "demoted", "retired"}
REACH = {"direct", "proxy", "search-only", "blocked", "blocked-paywall"}
STREAMS = {"news", "ai-ml", "science", "weekend", "sports"}
# reach and the probe's method say the same thing two ways; the plan hands the method to the
# writer, so a contradiction sends every fetch of that domain down the wrong path.
REACH_METHOD = {"direct": "curl", "proxy": "proxy"}
# The one domain whose feed genuinely lives on another registrable domain (BBC's feed host).
PROBE_HOST_EXCEPTIONS = {"bbc.com": "feeds.bbci.co.uk"}


def _registrable(host):
    host = host.lower().lstrip(".")
    if host.startswith("www."):
        host = host[4:]
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


class RegistrySchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = os.path.join(REPO, "sources", "registry.yml")
        with open(path, encoding="utf-8") as fh:
            cls.reg = registry.yaml_load(fh.read())
        assert cls.reg, "registry.yml parsed empty"

    def test_every_entry_has_the_required_keys(self):
        for domain, rec in self.reg.items():
            for key in ("class", "tier", "status", "reach", "streams", "lifecycle"):
                self.assertIn(key, rec, "%s is missing %s" % (domain, key))

    def test_enumerated_fields_hold_known_values(self):
        for domain, rec in self.reg.items():
            self.assertIn(rec["class"], CLASSES, domain)
            self.assertIn(rec["tier"], TIERS, domain)
            self.assertIn(rec["status"], STATUSES, domain)
            self.assertIn(rec["reach"], REACH, domain)

    def test_streams_are_live_slugs(self):
        """A typo'd or retired stream name means the domain is in NO plan -- it simply never
        gets fetched, and nothing says so."""
        for domain, rec in self.reg.items():
            streams = rec.get("streams") or []
            self.assertTrue(streams, "%s belongs to no stream" % domain)
            for s in streams:
                self.assertIn(s, STREAMS, "%s: unknown stream %r" % (domain, s))

    def test_domain_keys_are_bare_lowercase_hosts(self):
        for domain in self.reg:
            self.assertEqual(domain, domain.lower(), domain)
            self.assertNotIn("/", domain, domain)
            self.assertFalse(domain.startswith("www."), domain)
            self.assertNotIn("://", domain, domain)
            self.assertIn(".", domain, "%r does not look like a host" % domain)

    def test_probe_url_belongs_to_the_domain_it_is_filed_under(self):
        """The check that catches a mangled key. `wada-ama.org` was once written as
        `ada-ama.org` by a bad prefix-strip -- a plausible-looking host, with a probe URL that
        no longer belonged to it. Subdomains are fine (export.arxiv.org under arxiv.org);
        a different registrable domain is not, except BBC's separate feed host."""
        for domain, rec in self.reg.items():
            probe = rec.get("probe") or {}
            url = probe.get("url")
            if not url:
                continue
            host = urlparse(url).netloc.lower()
            if PROBE_HOST_EXCEPTIONS.get(domain) == host:
                continue
            self.assertEqual(_registrable(host), _registrable(domain),
                             "%s has a probe on an unrelated host: %s" % (domain, host))

    def test_probe_method_agrees_with_reach(self):
        for domain, rec in self.reg.items():
            probe = rec.get("probe") or {}
            method = probe.get("method")
            if not method:
                continue
            self.assertIn(method, ("curl", "proxy"), domain)
            expected = REACH_METHOD.get(rec["reach"])
            if expected:
                self.assertEqual(method, expected,
                                 "%s: reach=%s but probe method=%s"
                                 % (domain, rec["reach"], method))

    def test_probe_urls_are_absolute_http(self):
        for domain, rec in self.reg.items():
            url = (rec.get("probe") or {}).get("url")
            if not url:
                continue
            self.assertRegex(url, r"^https?://", "%s probe url is not absolute: %r" % (domain, url))

    def test_lifecycle_entries_are_dated(self):
        for domain, rec in self.reg.items():
            for item in rec.get("lifecycle") or []:
                self.assertRegex(str(item.get("date", "")), r"^\d{4}-\d{2}-\d{2}$",
                                 "%s has an undated lifecycle entry: %r" % (domain, item))
                self.assertTrue(item.get("event"), "%s lifecycle entry has no event" % domain)

    def test_round_trips_through_the_registry_dumper(self):
        """`registry.py sync` rewrites this file every edition. If the file is not in the exact
        form the dumper produces, every sync would reformat all 234 entries -- guaranteeing
        merge conflicts between editions that fire the same minute."""
        path = os.path.join(REPO, "sources", "registry.yml")
        with open(path, encoding="utf-8") as fh:
            original = fh.read()
        self.assertEqual(registry.yaml_dump(registry.yaml_load(original)), original,
                         "registry.yml is not in canonical dumper form -- the next sync would "
                         "rewrite the whole file")

    def test_every_stream_has_reachable_sources(self):
        """A stream whose every source is blocked/retired would produce empty briefs while every
        tool still reports success."""
        for stream in STREAMS:
            usable = [d for d, r in self.reg.items()
                      if stream in (r.get("streams") or [])
                      and r["status"] not in ("retired", "demoted")
                      and r["reach"] in ("direct", "proxy")]
            self.assertGreaterEqual(len(usable), 5,
                                    "stream %s has only %d usable sources" % (stream, len(usable)))


if __name__ == "__main__":
    unittest.main()
