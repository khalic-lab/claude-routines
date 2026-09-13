"""Spec tests for tools/usage/transcript.py + tools/usage/pricing.py.

Contract under test: measure a run's token spend from its transcript by deduping the
repeated-per-content-block message ids (max per usage field, one message per id), skipping
`<synthetic>` and API-error lines, folding sub-agent transcripts into the totals, reading
both cache_creation shapes, and detecting the routine + edition. Pricing is list-price from
the cited official table; an unknown model costs null and lands in missing_models.
"""
import importlib.util
import os
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(TOOLS, "tests", "fixtures", "usage", "sample-session.jsonl")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


transcript = _load("usage_transcript", os.path.join(TOOLS, "usage", "transcript.py"))
pricing = _load("usage_pricing", os.path.join(TOOLS, "usage", "pricing.py"))


class ParseTest(unittest.TestCase):
    def setUp(self):
        self.m = transcript.parse(FIX)

    def test_dedupe_by_message_id_counts_once(self):
        # msg_A spans 2 lines, msg_B spans 3 lines; with the sub-agent's msg_S1 that is 3
        # distinct messages, not 6 lines.
        self.assertEqual(self.m["messages"], 3)

    def test_dedupe_takes_max_output_across_streamed_lines(self):
        # msg_A's first line reports output 10 (partial), its second 50 (settled) -> 50 wins.
        opus = self.m["models"]["claude-opus-4-8"]
        # opus output = msg_A 50 + sub-agent msg_S1 500
        self.assertEqual(opus["output"], 550)

    def test_synthetic_and_api_error_lines_skipped(self):
        # the 9999 / 8888 values on the <synthetic> and isApiErrorMessage lines must vanish.
        for slot in self.m["models"].values():
            for k in ("input", "output", "cache_read", "cache_write_5m", "cache_write_1h"):
                self.assertLess(slot[k], 8888)
        self.assertNotIn("<synthetic>", self.m["models"])

    def test_cache_creation_both_shapes(self):
        # msg_A carries the FLAT cache_creation_input_tokens (2000) -> all 5m, no 1h.
        opus = self.m["models"]["claude-opus-4-8"]
        self.assertEqual(opus["cache_write_5m"], 2100)  # 2000 + sub-agent 100 (flat)
        self.assertEqual(opus["cache_write_1h"], 0)
        # msg_B carries the OBJECT split (300 / 1000).
        haiku = self.m["models"]["claude-haiku-4-5-20251001"]
        self.assertEqual(haiku["cache_write_5m"], 300)
        self.assertEqual(haiku["cache_write_1h"], 1000)

    def test_subagent_tokens_folded_in(self):
        # the sub-agent's msg_S1 (opus, input 5 / read 10 / output 500, one Read call) counts.
        opus = self.m["models"]["claude-opus-4-8"]
        self.assertEqual(opus["input"], 105)   # 100 + 5
        self.assertEqual(opus["cache_read"], 510)  # 500 + 10
        self.assertEqual(opus["messages"], 2)   # msg_A + msg_S1
        self.assertEqual(self.m["tool_calls"]["Read"], 1)

    def test_totals_and_server_tools(self):
        self.assertEqual(self.m["totals"],
                         {"input": 125, "cache_write_5m": 2400, "cache_write_1h": 1000,
                          "cache_read": 510, "output": 750})
        self.assertEqual(self.m["server_tools"], {"web_search_requests": 1, "web_fetch_requests": 0})

    def test_tool_calls_counted_across_lines(self):
        # two Bash calls (publish + grep), one WebFetch, one Read (sub-agent).
        self.assertEqual(self.m["tool_calls"]["Bash"], 2)
        self.assertEqual(self.m["tool_calls"]["WebFetch"], 1)

    def test_timing(self):
        self.assertEqual(self.m["started"], "2026-09-14T10:00:00.000Z")
        self.assertEqual(self.m["ended"], "2026-09-14T10:05:00.000Z")
        self.assertEqual(self.m["duration_s"], 300)

    def test_metadata(self):
        self.assertEqual(self.m["session_id"], "sess-news-abc")
        self.assertEqual(self.m["cwd"], "/repo/clone")
        self.assertEqual(self.m["claude_version"], "2.1.141")
        self.assertEqual(self.m["transcript_lines"], 8)  # main file only, not the sub-agent


class RoutineDetectionTest(unittest.TestCase):
    def test_all_writer_slugs(self):
        for slug in ("news", "ai-ml", "science", "weekend", "sports"):
            text = "git pull then read routines/%s.md and run it" % slug
            self.assertEqual(transcript.detect_routine(text, []), slug)

    def test_evaluator(self):
        text = "read routines/weekly-evaluator.md and produce the review"
        self.assertEqual(transcript.detect_routine(text, []), "evaluator")

    def test_watch_by_due_script(self):
        self.assertEqual(transcript.detect_routine("run tools/watch/due.py first", []), "watch")

    def test_watch_by_phrase(self):
        self.assertEqual(transcript.detect_routine("You are the Watch routine.", []), "watch")

    def test_publish_fallback_when_first_message_is_silent(self):
        cmds = ["python3 tools/publish.py --slug science --date 2026-09-13 --notify-body x"]
        self.assertEqual(transcript.detect_routine("do the work", cmds), "science")

    def test_unknown(self):
        self.assertEqual(transcript.detect_routine("hello", []), "unknown")

    def test_seven_routines_covered(self):
        # news, ai-ml, science, weekend, sports, evaluator, watch
        seen = set()
        for slug in ("news", "ai-ml", "science", "weekend", "sports"):
            seen.add(transcript.detect_routine("routines/%s.md" % slug, []))
        seen.add(transcript.detect_routine("routines/weekly-evaluator.md", []))
        seen.add(transcript.detect_routine("Watch routine", []))
        self.assertEqual(seen, {"news", "ai-ml", "science", "weekend", "sports",
                                "evaluator", "watch"})


class EditionDetectionTest(unittest.TestCase):
    def test_edition_from_publish_call(self):
        self.assertEqual(transcript.parse(FIX)["edition"], "2026-09-14-news")

    def test_edition_none_without_publish(self):
        self.assertIsNone(transcript.detect_edition(["grep foo bar"]))

    def test_edition_needs_both_slug_and_date(self):
        self.assertIsNone(transcript.detect_edition(["python3 tools/publish.py --slug news"]))


class PricingTest(unittest.TestCase):
    def test_source_url_is_cited(self):
        with open(os.path.join(TOOLS, "usage", "pricing.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("platform.claude.com/docs/en/about-claude/pricing", src)

    def test_routine_models_priced(self):
        # the two models the routines actually run on must be in the table.
        self.assertIn("claude-opus-4-8", pricing.PRICING)
        self.assertIn("claude-haiku-4-5-20251001", pricing.PRICING)

    def test_opus_cost_matches_list_price(self):
        # 100 input @ $5 + 200 cache_write_5m @ $6.25 -> (500 + 1250)/1e6
        models = {"claude-opus-4-8": {"input": 100, "cache_write_5m": 200,
                                      "cache_write_1h": 0, "cache_read": 0, "output": 0}}
        c = pricing.cost(models)
        self.assertAlmostEqual(c["total"], (100 * 5 + 200 * 6.25) / 1e6, places=9)
        self.assertEqual(c["pricing_as_of"], "2026-09-13")
        self.assertEqual(c["missing_models"], [])

    def test_fable_cache_read_is_the_low_multiplier(self):
        # Fable 5.1's cache read is 0.025x base ($0.25/MTok), not 0.1x.
        self.assertEqual(pricing.PRICING["claude-fable-5-1"]["cache_read"], 0.25)

    def test_unknown_model_is_null_and_listed(self):
        c = pricing.cost({"claude-opus-4-8": {"input": 1_000_000, "output": 0,
                                              "cache_write_5m": 0, "cache_write_1h": 0, "cache_read": 0},
                          "claude-made-up-9": {"input": 1_000_000, "output": 0,
                                               "cache_write_5m": 0, "cache_write_1h": 0, "cache_read": 0}})
        self.assertIsNone(c["by_model"]["claude-made-up-9"])
        self.assertIn("claude-made-up-9", c["missing_models"])
        # the known model still sums (5.0), the unknown does not zero the whole total.
        self.assertAlmostEqual(c["total"], 5.0, places=6)


if __name__ == "__main__":
    unittest.main()
