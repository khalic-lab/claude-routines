"""Spec tests for the 2026-11-27 evaluator/registry pass: the bounded auto reach flip in
`registry.py sync`, the link-check result classes, the Weekend recap fetched-this-run footer
line, and the Weekend section/revisit measures in metrics.py."""
import importlib.util
import os
import shutil
import sys
import tempfile
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(TOOLS, rel))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


registry = _load("registry_v2_autoflip", "sources/registry.py")
metrics = _load("metrics_v2", "evaluator/metrics.py")
linkcheck = _load("linkcheck_v2", "evaluator/linkcheck.py")
footer = _load("footer_v2", "footer.py")


def _entry(reach="direct", probe=None, status="candidate", streams=("news",)):
    e = {"class": "outlet", "tier": "T2", "status": status, "reach": reach,
         "streams": list(streams)}
    if probe:
        e["probe"] = dict(probe)
    e["lifecycle"] = [{"date": "2026-07-01", "event": "seed", "status": status}]
    return e


def _post(feeds):
    return ("---\ntitle: x\n---\n\n## News\n\n- a story\n\n## Coverage footer\n\n"
            "- Feeds hit (from fetch log): %s\n" % feeds)


class AutoReachFlipTest(unittest.TestCase):
    TODAY = "2026-11-27"

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="autoflip-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        os.makedirs(os.path.join(self.root, "sources"))
        os.makedirs(os.path.join(self.root, "_posts"))
        self.reg = {
            "walled.example": _entry(probe={"url": "https://walled.example/rss", "method": "curl"}),
            "sparse.example": _entry(),
            "curlok.example": _entry(),
            "gone.example": _entry(status="retired"),
        }
        for i in range(12):  # enough sources for every stream floor in validate()
            self.reg["filler%d.example" % i] = _entry(
                streams=("news", "ai-ml", "science", "weekend", "sports"))
        with open(os.path.join(self.root, "sources", "registry.yml"), "w") as f:
            f.write(registry.yaml_dump(self.reg))

    def load(self):
        with open(os.path.join(self.root, "sources", "registry.yml")) as f:
            return registry.yaml_load(f.read())

    def write_post(self, date, feeds):
        with open(os.path.join(self.root, "_posts", "%s-news.md" % date), "w") as f:
            f.write(_post(feeds))

    def walled(self, n=3):
        return "walled.example {1 fail ERR:56, %d ok via proxy}" % n

    def test_flips_only_when_both_windows_agree_and_moves_the_probe_method(self):
        # previous window 2026-11-13..19, current 2026-11-20..26; today (27th) excluded
        self.write_post("2026-11-15", self.walled() + "; sparse.example {1 fail ERR:56, 3 ok via proxy}"
                        "; curlok.example {1 fail ERR:56, 3 ok via proxy}; gone.example {1 fail ERR:56, 4 ok via proxy}")
        self.write_post("2026-11-24", self.walled(4) + "; curlok.example {2 ok via curl, 3 ok via proxy}"
                        "; gone.example {1 fail ERR:56, 4 ok via proxy}")
        self.write_post("2026-11-26", "sparse.example {1 fail ERR:56, 3 ok via proxy}")
        reg = self.load()
        flipped = registry.auto_reach_flips(self.root, reg, self.TODAY)
        self.assertIn("walled.example", flipped)
        self.assertIn("sparse.example", flipped)  # one edition in each window: 11-15 and 11-26
        self.assertNotIn("curlok.example", flipped)  # curl succeeded in the current window
        self.assertNotIn("gone.example", flipped)    # retired entries never move
        e = reg["walled.example"]
        self.assertEqual(e["reach"], "proxy")
        self.assertEqual(e["probe"]["method"], "proxy")
        self.assertEqual(e["lifecycle"][-1]["event"], "reach-flip")
        self.assertIn("(auto)", e["lifecycle"][-1]["note"])
        self.assertEqual(registry.validate(reg), [])

    def test_single_window_and_todays_edition_do_not_flip(self):
        self.write_post("2026-11-24", self.walled())
        self.write_post("2026-11-27", self.walled())  # today: excluded from both windows
        reg = self.load()
        self.assertEqual(registry.auto_reach_flips(self.root, reg, self.TODAY), [])
        self.assertEqual(reg["walled.example"]["reach"], "direct")

    def test_a_recent_human_correction_to_direct_is_not_undone(self):
        self.write_post("2026-11-15", self.walled())
        self.write_post("2026-11-24", self.walled())
        reg = self.load()
        reg["walled.example"]["lifecycle"].append(
            {"date": "2026-11-20", "event": "set reach", "note": "proxy -> direct (admin: curl works now)"})
        self.assertEqual(registry.auto_reach_flips(self.root, reg, self.TODAY), [])

    def test_missing_posts_dir_degrades_to_no_flip(self):
        shutil.rmtree(os.path.join(self.root, "_posts"))
        reg = self.load()
        self.assertEqual(registry.auto_reach_flips(self.root, reg, self.TODAY), [])


class LinkcheckClassTest(unittest.TestCase):
    def test_classes(self):
        self.assertEqual(linkcheck.classify("200"), "pass")
        self.assertEqual(linkcheck.classify("301p"), "pass")
        self.assertEqual(linkcheck.classify("404"), "broken")
        self.assertEqual(linkcheck.classify("410p"), "broken")
        self.assertEqual(linkcheck.classify("403"), "blocked")
        self.assertEqual(linkcheck.classify("ERR:56"), "unreachable")
        self.assertEqual(linkcheck.classify("PROXY:401"), "unreachable")

    def test_tally_separates_broken_from_unreachable(self):
        line = linkcheck._tally_line(["200", "404", "403", "ERR:56", "ERR:56"])
        self.assertIn("broken (404/410) 1", line)
        self.assertIn("unreachable 2", line)
        self.assertIn("measurable 1/3", line)

    def test_a_head_404_is_confirmed_by_get_before_it_counts_as_broken(self):
        seen = []
        orig = linkcheck._curl_code
        linkcheck._curl_code = lambda args, max_time, header_file=None: (
            seen.append(args) or ("404" if "-I" in args else "200"))
        try:
            self.assertEqual(linkcheck.resolve("https://headless.example/a"), "200")
        finally:
            linkcheck._curl_code = orig
        self.assertEqual(len(seen), 2)

    def test_unsubstituted_token_placeholder_never_reaches_the_proxy(self):
        calls = []
        orig = linkcheck._curl_code
        linkcheck._curl_code = lambda args, max_time, header_file=None: calls.append(args) or "ERR:56"
        old = os.environ.get("FETCH_PROXY_TOKEN")
        os.environ["FETCH_PROXY_TOKEN"] = "${FETCH_PROXY_TOKEN}"
        try:
            self.assertEqual(linkcheck.resolve("https://walled.example/a"), "ERR:56")
        finally:
            linkcheck._curl_code = orig
            if old is None:
                os.environ.pop("FETCH_PROXY_TOKEN", None)
            else:
                os.environ["FETCH_PROXY_TOKEN"] = old
        self.assertEqual(len(calls), 1)  # the direct HEAD only


class RecapFetchedThisRunTest(unittest.TestCase):
    BODY = ("## 📰 Week in headlines (short)\n\n"
            "- A [ruling](https://court.example/r/1/) landed.\n"
            "- A [vote](https://parl.example/v#top) passed.\n\n"
            "## 📄 ML / AI papers\n\n- [paper](https://arxiv.org/abs/1)\n")

    def test_lists_recap_links_with_no_successful_fetch(self):
        attempts = [{"url": "https://court.example/r/1", "ok": True},
                    {"url": "https://parl.example/v", "ok": False},
                    {"url": "https://arxiv.org/abs/1", "ok": False}]
        self.assertEqual(footer.recap_unfetched(self.BODY, attempts), ["https://parl.example/v#top"])


class WeekendMeasuresTest(unittest.TestCase):
    def test_h3_entry_and_its_cite_line_count_once(self):
        body = ("## 📄 ML / AI papers\n\n### A paper {#st-aaaaaaaaaaaa}\n"
                "**[arXiv:2611.00001](https://arxiv.org/abs/2611.00001)** · Authors\n\nText.\n\n"
                "### B paper {#st-bbbbbbbbbbbb}\n"
                "**[arXiv:2611.00002](https://arxiv.org/abs/2611.00002)**\n")
        self.assertEqual([(n, c) for n, c, _ in metrics._sections(body)], [("📄 ML / AI papers", 2)])

    def test_revisit_containment_scores_rewording_high_and_fresh_writing_low(self):
        daily_text = ("the model reaches state of the art on the benchmark while using a "
                      "fraction of the compute of prior systems according to the authors")
        daily = ("---\n---\n\n## Papers\n\n- <a id=\"st-aaaaaaaaaaaa\"></a>**A.** %s\n"
                 "- <a id=\"st-cccccccccccc\"></a>**C.** %s\n" % (daily_text, daily_text))
        weekend = ("---\n---\n\n## 📄 ML / AI papers\n\n### A {#st-aaaaaaaaaaaa}\n%s\n\n"
                   "### C {#st-cccccccccccc}\nAn ablation in table four shows the gain vanishes "
                   "without the curriculum stage, which the abstract never mentions.\n\n"
                   "### D {#st-dddddddddddd}\nFresh paper.\n" % daily_text)
        out = metrics.build_weekend_revisits([("2026-11-25", "ai-ml", daily),
                                              ("2026-11-28", "weekend", weekend)])
        s = out["📄 ML / AI papers"]
        self.assertEqual((s["entries"], s["revisits"]), (3, 2))
        self.assertGreater(s["containment_mean"], 0.3)
        self.assertLess(s["containment_mean"], 0.9)


class ComputedBriefsTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="briefs-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        os.makedirs(os.path.join(self.root, "_posts"))
        os.makedirs(os.path.join(self.root, "sources"))
        reg = {"outlet.example": _entry(), "hub.example": _entry()}
        reg["hub.example"]["class"] = "hub"
        with open(os.path.join(self.root, "sources", "registry.yml"), "w") as f:
            f.write(registry.yaml_dump(reg))

    def post(self, name, body, sources_line):
        with open(os.path.join(self.root, "_posts", name), "w") as f:
            f.write("---\ntitle: x\n---\n\n%s\n## Coverage footer\n\n%s\n" % (body, sources_line))

    def test_tier_share_per_stream_and_portfolio_from_the_footer_line(self):
        self.post("2026-11-20-news.md", "## News\n\n- a\n",
                  "- Sources used: T1 = 2, T2 = 6, untiered = 2 (registry tier)")
        self.post("2026-11-21-ai-ml.md", "## AI\n\n- a\n",
                  "- Sources used: T1 = 6, T2 = 4, untiered = 0 (registry tier)")
        b = metrics.build_briefs(self.root, "2026-11-16", "2026-11-22")
        self.assertEqual(b["by_stream"]["news"]["t1_share"], 0.2)
        self.assertEqual(b["by_stream"]["ai-ml"]["tiers"], {"T1": 6, "T2": 4, "untiered": 0})
        self.assertEqual(b["t1_share"], 0.4)

    def test_outlet_cap_breach_is_surfaced_from_the_lint_replay(self):
        body = "## News\n\n" + "".join(
            "- **Story %d.** Text ([Outlet](https://outlet.example/a%d))\n" % (i, i) for i in range(3))
        self.post("2026-11-20-news.md", body, "- Discovery: none")
        b = metrics.build_briefs(self.root, "2026-11-16", "2026-11-22")
        self.assertEqual(b["lint"]["by_stream"].get("news", {}).get("outlet_cap"), 1)
        self.assertEqual(b["lint"]["items"][0]["post"], "2026-11-20-news.md")

    def test_walled_feed_rule_spares_proxy_only_hosts(self):
        feeds = {"proxyonly.example": {"ok_proxy": 15, "fail": 15},   # one curl miss per success
                 "walled.example": {"ok_proxy": 2, "fail": 11},
                 "dead.example": {"fail": 5},
                 "curl.example": {"ok_curl": 3, "fail": 1}}
        self.assertEqual([r["feed"] for r in metrics.build_feeds_walled(feeds)],
                         ["walled.example", "dead.example"])


class ReasonedCarryTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="reasoned-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        os.makedirs(os.path.join(self.root, "proposals"))
        with open(os.path.join(self.root, "proposals", "reader-model-2026-11-01.json"), "w") as f:
            f.write('{"date": "2026-11-01", "proposals": [], "dispositions": ['
                    '{"fb_id": "done", "disposition": "applied", "ref": "rm-1"},'
                    '{"fb_id": "wait", "disposition": "deferred", "ref": "one story"}]}')

    def ev(self, fb_id, ts, reason="why"):
        return {"ev": "feedback", "fb_id": fb_id, "ts": ts, "id": "st-aaaaaaaaaaaa",
                "brief": "2026-11-20-news", "vote": -1, "reason": reason}

    def test_carry_disposition_and_horizon(self):
        events = [self.ev("sunday-late", "2026-11-15T11:00:00Z"),   # after last Sunday's run
                  self.ev("done", "2026-11-18T10:00:00Z"),
                  self.ev("wait", "2026-10-20T10:00:00Z"),
                  self.ev("bare", "2026-11-19T10:00:00Z", reason=""),
                  self.ev("ancient", "2026-07-20T10:00:00Z"),
                  self.ev("fresh", "2026-11-20T10:00:00Z")]
        out = metrics.build_reasoned(events, self.root, "2026-11-16", "2026-11-22")
        got = {r["fb_id"]: (r["carried"], r["prior"]) for r in out}
        self.assertEqual(got, {"sunday-late": (True, None), "wait": (True, "deferred"),
                               "fresh": (False, None)})
        self.assertEqual([r["fb_id"] for r in out], ["wait", "sunday-late", "fresh"])


if __name__ == "__main__":
    unittest.main()
