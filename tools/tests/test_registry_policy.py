"""Source-registry POLICY changes (2026-11): earned promotion in registry.py sync, candidates_open
counting registered candidates, and a rotating candidates_to_try window. Separate from
test_registry_v2.py (reliability fixes) so the policy can land, or be reverted, on its own."""
import datetime
import importlib.util
import os
import shutil
import sys
import tempfile
import unittest

import sources_helpers as H
import yamllite

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(REPO, "tools", "sources")


def _load(name):
    spec = importlib.util.spec_from_file_location("_p_" + name, os.path.join(SRC, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, SRC)
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(SRC)
    return mod


registry = _load("registry")
health = _load("health")
preflight = _load("preflight")


def _entry(status):
    return {"class": "outlet", "tier": "T2", "status": status, "reach": "direct",
            "streams": ["news"], "last_cited": None,
            "lifecycle": [{"date": "2026-07-07", "event": "candidate", "status": status}]}


class SyncPromotionTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="registry-promo-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        os.makedirs(os.path.join(self.root, "sources"))
        reg = {"once.example": _entry("candidate"), "often.example": _entry("candidate"),
               "prob.example": _entry("probation"), "gone.example": _entry("retired")}
        with open(os.path.join(self.root, "sources", "registry.yml"), "w") as f:
            f.write(registry.yaml_dump(reg))
        recs = []
        for domain, n in (("once.example", 1), ("often.example", 6), ("prob.example", 5),
                          ("gone.example", 9), ("fresh.example", 1)):
            recs += [{"id": "%s-%d" % (domain, i), "date": H.days_ago(2), "stream": "news",
                      "source_domain": domain} for i in range(n)]
        os.makedirs(os.path.join(self.root, "index", "stories"))
        H.write_jsonl(os.path.join(self.root, "index", "stories", "x-news.jsonl"), recs)

    def run_sync(self):
        proc = H.run_script(self, "registry.py", ["sync", "--root", self.root])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(os.path.join(self.root, "sources", "registry.yml")) as f:
            return f.read()

    def test_promotes_by_citation_count_and_converges_in_one_run(self):
        text = self.run_sync()
        reg = yamllite.load(text)
        self.assertEqual(reg["once.example"]["status"], "probation")
        self.assertEqual(reg["often.example"]["status"], "established")
        self.assertEqual(reg["prob.example"]["status"], "established")
        self.assertEqual(reg["gone.example"]["status"], "retired")
        last = reg["often.example"]["lifecycle"][-1]
        self.assertEqual((last["event"], last["status"]), ("promoted", "established"))
        self.assertNotRegex(last["note"], r"\d", "a count in the note defeats same-day merges")
        self.assertEqual(self.run_sync(), text, "a second sync must be a no-op")

    def test_domain_entered_and_cited_in_the_same_run_gets_one_lifecycle_line(self):
        """publish records the index BEFORE registry-sync, so a writer's [new source] domain is
        already cited when sync first registers it."""
        H.write_jsonl(os.path.join(self.root, "sources", "candidates.jsonl"), [
            {"domain": "fresh.example", "first_seen": H.days_ago(2), "via": "writer",
             "stream": "news", "url": "https://fresh.example/a"}])
        reg = yamllite.load(self.run_sync())
        e = reg["fresh.example"]
        self.assertEqual(e["status"], "probation")
        self.assertEqual(len(e["lifecycle"]), 1)
        self.assertEqual(e["lifecycle"][0]["event"], "candidate")
        self.assertEqual(e["lifecycle"][0]["status"], "probation")


class HealthCandidatesOpenTest(unittest.TestCase):
    def test_registered_candidates_count_after_sync_emptied_the_buffer(self):
        today = datetime.datetime.now(datetime.timezone.utc).date()
        root = tempfile.mkdtemp(prefix="health-open-")
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        reg = {"a.example": {"status": "candidate", "streams": ["news"]},
               "b.example": {"status": "probation", "streams": ["news"]},
               "c.example": {"status": "candidate", "streams": ["science"]}}
        m = health.compute_stream_metrics(root, "news", [], today, reg)
        self.assertEqual(m["candidates_open"], 1)


class CandidatesWindowTest(unittest.TestCase):
    def setUp(self):
        self.reg = {"cand%02d.example" % i: {"class": "outlet", "status": "candidate",
                                             "reach": "direct", "streams": ["news"]}
                    for i in range(30)}
        self.root = tempfile.mkdtemp(prefix="preflight-window-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def shown(self, day):
        out = preflight.build_discovery_section("news", self.reg, self.root, today=day)
        return [l.split(": ", 1)[1].split(" ")[0] for l in out.splitlines()
                if l.startswith("- candidates_to_try: cand")], out

    def test_window_is_capped_and_rotates_across_days(self):
        d0 = datetime.date(2026, 11, 27)
        seen = set()
        for k in range(3):
            names, out = self.shown(d0 + datetime.timedelta(days=k))
            self.assertEqual(len(names), 20)
            self.assertIn("+10 more on file", out)
            seen |= set(names)
        self.assertEqual(len(seen), 30, "every candidate surfaces within a few editions")
        self.assertEqual(self.shown(d0)[0], self.shown(d0)[0], "deterministic for a given day")


if __name__ == "__main__":
    unittest.main()
