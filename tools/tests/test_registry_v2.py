"""Source-registry tooling, 2026-11 reliability pass: strict-YAML-safe dumper, candidate fields
kept by sync, the extended class rule and its single consumer path (class_of), index-derived
dormancy and snippet-only reach in the preflight plan.

Every case drives the code the publish tail runs (registry.py sync / preflight.py as
subprocesses, or the module functions they call) against a tempdir root.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest

import sources_helpers as H
import yamllite

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(REPO, "tools", "sources")


def _load(name):
    spec = importlib.util.spec_from_file_location("_" + name, os.path.join(SRC, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    import sys
    sys.path.insert(0, SRC)
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(SRC)
    return mod


registry = _load("registry")
health = _load("health")
lint = _load("lint")

# Values that broke or would break strict YAML (or this repo's own loaders) when written plain.
TRICKY = [
    "sports: https://www.letemps.ch/sport.rss verified fresh (newest 0d)",  # the live breakage
    "admin: A first class ML researcher", "ends with a colon:", "issue #5 is open",
    "- leading dash", "#hash", "&anchor", "*alias", "!tag", "|pipe", ">fold", "@at", "`tick",
    "%pct", "{brace", "[bracket", "'single'", '"double"', 'say "hi"', "back\\slash",
    "yes", "No", "on", "OFF", "y", "null", "~", "true", "", " padded ", "tab\there",
    "line\nbreak", "0x1F", "1:20", "1_000", "1,000", "1e3", ".inf", "-.5", "2026-7-5",
    "2026-07-05T10:00:00Z", " ", "é accent", "plain words", "https://example.org/a?b=c#d",
]


class DumperRoundTripTest(unittest.TestCase):
    def assert_round_trip(self, data):
        text = registry.yaml_dump(data)
        self.assertEqual(registry.yaml_load(text), data, text)
        self.assertEqual(yamllite._loads_fallback(text), data, text)
        self.assertEqual(registry.yaml_dump(registry.yaml_load(text)), text, "not canonical")

    def test_tricky_values_round_trip_as_map_values_list_items_and_list_map_values(self):
        for s in TRICKY:
            with self.subTest(value=s):
                self.assert_round_trip({"k": s})
                self.assert_round_trip({"k": [s]})
                self.assert_round_trip({"k": [{"date": "2026-11-27", "note": s}]})

    def test_colon_space_value_is_quoted(self):
        self.assertEqual(registry.yaml_dump({"note": "a: b"}), 'note: "a: b"\n')

    def test_canonical_dates_and_urls_stay_plain(self):
        """The live file's dates and probe URLs must not churn."""
        self.assertEqual(registry.yaml_dump({"d": "2026-07-05"}), "d: 2026-07-05\n")
        self.assertEqual(registry.yaml_dump({"u": "https://x.org/feed"}), "u: https://x.org/feed\n")

    def test_unsafe_key_is_refused_not_written(self):
        for key in ("host:8443", "a: b", "*star", "yes", "123"):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    registry.yaml_dump({key: 1})

    def test_yamllite_dumper_agrees(self):
        for s in TRICKY:
            with self.subTest(value=s):
                text = yamllite.dump({"k": s, "l": [s]})
                self.assertEqual(registry.yaml_load(text), {"k": s, "l": [s]})

    @unittest.skipUnless(shutil.which("ruby"), "no strict YAML parser (ruby) on this machine")
    def test_live_registry_and_institutions_parse_as_strict_yaml_to_the_same_data(self):
        """Ruby's Psych is a strict YAML 1.1 parser; it must read the live files exactly as
        registry.py does (dates normalised to ISO strings)."""
        script = ("require 'yaml'; require 'date'; require 'json'; "
                  "n=->(x){x.is_a?(Hash) ? x.transform_values{|v| n.(v)} : "
                  "x.is_a?(Array) ? x.map{|v| n.(v)} : x.is_a?(Date) ? x.iso8601 : x}; "
                  "puts JSON.generate(n.(YAML.safe_load(File.read(ARGV[0]), "
                  "permitted_classes: [Date])))")
        for rel in ("sources/registry.yml", "sources/institutions.yml"):
            with self.subTest(file=rel):
                path = os.path.join(REPO, rel)
                proc = subprocess.run(["ruby", "-e", script, path], capture_output=True, text=True)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                with open(path, encoding="utf-8") as fh:
                    ours = registry.yaml_load(fh.read())
                self.assertEqual(json.loads(proc.stdout), ours)


class ClassifyDomainTest(unittest.TestCase):
    CASES = {
        "state.gov": "institutional", "bfs.admin.ch": "institutional", "ec.europa.eu": "institutional",
        "aisi.gov.uk": "institutional", "gov.uk": "institutional", "lamoncloa.gob.es": "institutional",
        "pm.gc.ca": "institutional", "cam.ac.uk": "institutional", "cims.nyu.edu": "institutional",
        "nato.int": "institutional", "centcom.mil": "institutional", "doj.state.or.us": "institutional",
        "vd.ch": "institutional", "polizei.bs.ch": "institutional", "press.un.org": "institutional",
        "icj-cij.org": "institutional", "en.kremlin.ru": "institutional", "bger.ch": "institutional",
        "export.arxiv.org": "hub", "arxiv.org": "hub", "github.com": "hub",
        "bbc.co.uk": "outlet", "srf.ch": "outlet", "semanticscholar.org": "outlet",
        "casp.ac": "outlet", "arxiv.org.evil.com": "outlet", "notgov.com": "outlet",
    }

    def test_cases(self):
        for domain, cls in self.CASES.items():
            with self.subTest(domain=domain):
                self.assertEqual(registry.classify_domain(domain), cls)

    def test_registry_class_wins_over_the_rule(self):
        reg = {"mpg.de": {"class": "institutional"}, "nna-leb.gov.lb": {"class": "outlet"}}
        self.assertEqual(registry.class_of("mpg.de", reg), "institutional")
        self.assertEqual(registry.class_of("nna-leb.gov.lb", reg), "outlet")
        self.assertEqual(registry.class_of("unregistered.gov", reg), "institutional")


class SyncCandidateFieldsTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="registry-v2-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        os.makedirs(os.path.join(self.root, "sources"))
        with open(os.path.join(self.root, "sources", "registry.yml"), "w") as f:
            f.write(registry.yaml_dump({"srf.ch": {
                "class": "outlet", "tier": "T2", "status": "established", "reach": "direct",
                "streams": ["news"], "last_cited": "2026-07-01",
                "lifecycle": [{"date": "2026-07-07", "event": "bootstrap", "status": "established"}]}}))

    def sync(self, records, raw_lines=()):
        path = os.path.join(self.root, "sources", "candidates.jsonl")
        with open(path, "w") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")
            for line in raw_lines:
                f.write(line + "\n")
        proc = H.run_script(self, "registry.py", ["sync", "--root", self.root])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(os.path.join(self.root, "sources", "registry.yml")) as f:
            text = f.read()
        return yamllite.load(text), proc

    SCOUT = {"domain": "cerncourier.com", "first_seen": "2026-08-02", "via": "scout",
             "stream": "science", "url": "https://cerncourier.com/", "reach": "proxy-needed",
             "note": "CERN Courier: particle physics primary. Evaluator egress 403."}

    def test_scout_record_keeps_url_as_probe_note_in_lifecycle_and_no_last_cited(self):
        reg, _ = self.sync([self.SCOUT])
        e = reg["cerncourier.com"]
        self.assertEqual(e["reach"], registry.CANDIDATE_REACH["proxy-needed"])
        # proxy-needed = the scout never fetched the page: unverified, so no probe
        self.assertNotIn("probe", e)
        self.assertIn("https://cerncourier.com/", e["lifecycle"][0]["note"])
        self.assertIsNone(e.get("last_cited"))
        note = e["lifecycle"][0]["note"]
        self.assertIn("via scout", note)
        self.assertIn("proxy-needed", note)
        self.assertIn("CERN Courier: particle physics primary", note)
        with open(os.path.join(self.root, "sources", "registry.yml")) as f:
            violations = registry.validate(registry.yaml_load(f.read()))
        self.assertEqual([v for v in violations if v.startswith("cerncourier.com")], [])

    def test_writer_record_sets_last_cited_and_no_probe(self):
        reg, _ = self.sync([{"domain": "state.gov", "first_seen": "2026-07-09", "via": "writer",
                             "stream": "news", "url": "https://www.state.gov/releases/x/"}])
        e = reg["state.gov"]
        self.assertEqual(e["last_cited"], "2026-07-09")
        self.assertNotIn("probe", e)
        self.assertEqual(e["class"], "institutional")
        self.assertIn("https://www.state.gov/releases/x/", e["lifecycle"][0]["note"])

    def test_fetched_scout_url_becomes_a_probe(self):
        reg, _ = self.sync([dict(self.SCOUT, reach="direct")])
        e = reg["cerncourier.com"]
        self.assertEqual(e["probe"], {"url": "https://cerncourier.com/",
                                      "method": registry.REACH_METHOD[e["reach"]]})
        with open(os.path.join(self.root, "sources", "registry.yml")) as f:
            violations = registry.validate(registry.yaml_load(f.read()))
        self.assertEqual([v for v in violations if v.startswith("cerncourier.com")], [])

    def test_probe_on_another_host_is_dropped(self):
        rec = dict(self.SCOUT, domain="uci.ch", stream="sports", url="https://www.uci.org/news",
                   reach="direct")
        reg, _ = self.sync([rec])
        self.assertNotIn("probe", reg["uci.ch"])

    def test_second_record_for_a_new_domain_merges_stream_and_note(self):
        first = {"domain": "news.uzh.ch", "first_seen": "2026-10-11", "via": "scout",
                 "stream": "science", "url": "https://www.news.uzh.ch/en.html", "reach": "proxy-needed"}
        second = dict(first, stream="weekend", note="University of Zurich newsroom")
        reg, _ = self.sync([first, second])
        e = reg["news.uzh.ch"]
        self.assertEqual(e["streams"], ["science", "weekend"])  # creation stream stays first
        self.assertIn("University of Zurich newsroom", e["lifecycle"][0]["note"])
        self.assertEqual(len(e["lifecycle"]), 1)

    def test_domain_is_normalised_and_garbage_is_skipped_not_fatal(self):
        reg, proc = self.sync(
            [dict(self.SCOUT, domain="WWW.Example.ORG."),
             dict(self.SCOUT, domain="host.example:8443"),
             dict(self.SCOUT, domain="typo.example", stream="sport")],
            raw_lines=['{"domain": "half-written', "[1, 2]"])
        self.assertIn("example.org", reg)
        self.assertNotIn("host.example:8443", reg)
        self.assertNotIn("host.example", reg)
        self.assertNotIn("typo.example", reg)
        self.assertIn("WARN", proc.stderr)

    def test_registered_domain_is_left_alone(self):
        reg, _ = self.sync([dict(self.SCOUT, domain="srf.ch", stream="news")])
        self.assertEqual(reg["srf.ch"]["status"], "established")
        self.assertNotIn("probe", reg["srf.ch"])


class HealthUsesRegistryClassTest(unittest.TestCase):
    def test_registry_institutional_override_leaves_the_outlet_ranking(self):
        recs = ([{"stream": "news", "date": H.days_ago(1), "source_domain": "mpg.de"}] * 8 +
                [{"stream": "news", "date": H.days_ago(1), "source_domain": "srf.ch"}] * 2)
        import datetime
        today = datetime.datetime.now(datetime.timezone.utc).date()
        root = tempfile.mkdtemp(prefix="health-class-")
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        reg = {"mpg.de": {"class": "institutional"}}
        m = health.compute_stream_metrics(root, "news", recs, today, reg)
        self.assertEqual(m["top5_share"], 1.0)        # srf.ch alone is the outlet ranking
        self.assertEqual(m["saturated"], ["mpg.de"])  # 80% > the 30% bar; srf.ch's 20% is not > 20%

    def test_without_registry_the_rule_default_applies(self):
        import datetime
        today = datetime.datetime.now(datetime.timezone.utc).date()
        recs = [{"stream": "news", "date": H.days_ago(1), "source_domain": "bfs.admin.ch"}] * 3
        m = health.compute_stream_metrics(tempfile.gettempdir(), "news", recs, today, {})
        self.assertEqual(m["top5_share"], 0.0)


class LintDomainOfTest(unittest.TestCase):
    def test_port_and_userinfo_never_reach_the_domain(self):
        self.assertEqual(lint.domain_of("https://user@www.Example.org:8443/a"), "example.org")


class PreflightDiscoveryTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="preflight-v2-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        os.makedirs(os.path.join(self.root, "sources"))
        old = H.days_ago(90)
        reg = {
            "busy.example": {"class": "outlet", "status": "established", "reach": "direct",
                             "streams": ["news"], "last_cited": old},
            "quiet.example": {"class": "outlet", "status": "established", "reach": "direct",
                              "streams": ["news"], "last_cited": old},
            "walled.example": {"class": "outlet", "status": "established", "reach": "blocked",
                               "streams": ["news"], "last_cited": old},
        }
        for i in range(30):
            reg["cand%02d.example" % i] = {"class": "outlet", "status": "candidate",
                                           "reach": "direct", "streams": ["news"]}
        with open(os.path.join(self.root, "sources", "registry.yml"), "w") as f:
            f.write(yamllite.dump(reg))
        os.makedirs(os.path.join(self.root, "index", "stories"))
        H.write_jsonl(os.path.join(self.root, "index", "stories", "x-news.jsonl"),
                      [{"id": "b1", "date": H.days_ago(3), "stream": "news",
                        "source_domain": "busy.example"}])

    def plan(self):
        proc = H.run_script(self, "preflight.py", ["--slug", "news", "--root", self.root])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout

    def test_domain_cited_in_the_index_is_not_dormant_despite_a_stale_registry_date(self):
        out = self.plan()
        self.assertNotIn("candidates_to_try: busy.example", out)

    def test_blocked_domain_is_annotated_and_never_a_discovery_candidate(self):
        out = self.plan()
        self.assertIn("walled.example (established, outlet, reach=blocked) -- snippet-only", out)
        self.assertNotIn("candidates_to_try: walled.example", out)


if __name__ == "__main__":
    unittest.main()
