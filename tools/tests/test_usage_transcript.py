"""Spec tests for tools/usage/transcript.py + tools/usage/pricing.py.

Contract under test: measure a run's token spend from its transcript by deduping the
repeated-per-content-block message ids (max per usage field, one message per id), skipping
`<synthetic>` and API-error lines, folding sub-agent transcripts into the totals, reading
both cache_creation shapes, and detecting the routine + edition. Pricing is list-price from
the cited official table; an unknown model costs null and lands in missing_models.
"""
import importlib.util
import json
import os
import tempfile
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
        self.assertEqual(c["pricing_as_of"], "2026-11-28")
        self.assertEqual(c["missing_models"], [])

    def test_fable_cache_read_is_the_low_multiplier(self):
        # Fable 5.1's cache read is 0.025x base ($0.25/MTok), not 0.1x.
        self.assertEqual(pricing.PRICING["claude-fable-5-1"]["cache_read"], 0.25)

    def test_fable_5_cache_read_stays_at_default_multiplier(self):
        # Fable 5 (unlike 5.1) has NO 0.025x exception: its cache read is the 0.1x default,
        # $1.00/MTok on $10 base input. Pins the row so it can't silently diverge from the
        # comment again (the comment once wrongly claimed the exception covered both).
        self.assertEqual(pricing.PRICING["claude-fable-5"]["cache_read"], 1.00)

    def test_opus_4_8_all_five_prices_pinned(self):
        # The model the routines run heaviest on -- pin every column so a stale table shows.
        p = pricing.PRICING["claude-opus-4-8"]
        self.assertEqual(p["input"], 5.0)
        self.assertEqual(p["output"], 25.0)
        self.assertEqual(p["cache_write_5m"], 6.25)
        self.assertEqual(p["cache_write_1h"], 10.0)
        self.assertEqual(p["cache_read"], 0.50)

    def test_haiku_5_5_both_prompt_length_rows_pinned(self):
        # Pricing page 2026-11-28: prompts up to 100K $0.10 / $0.125 / $0.20 / $0.01 / $0.50;
        # over 100K $0.50 / $0.625 / $1 / $0.05 / $2.50 (input, 5m, 1h, read, output).
        short = pricing.PRICING["claude-haiku-5-5"]
        long_ = pricing.PRICING["claude-haiku-5-5" + pricing.LONG_PROMPT_SUFFIX]
        self.assertEqual([short[k] for k in ("input", "cache_write_5m", "cache_write_1h", "cache_read", "output")],
                         [0.10, 0.125, 0.20, 0.01, 0.50])
        self.assertEqual([long_[k] for k in ("input", "cache_write_5m", "cache_write_1h", "cache_read", "output")],
                         [0.50, 0.625, 1.0, 0.05, 2.50])
        self.assertEqual(pricing.LONG_PROMPT_THRESHOLD["claude-haiku-5-5"], 100_000)

    def test_low_cache_read_models(self):
        # 0.05x on Opus 5.5 / Sonnet 5.5, 0.025x on Fable 5.2 (pricing page 2026-11-28).
        self.assertEqual(pricing.PRICING["claude-opus-5-5"]["cache_read"], 0.20)
        self.assertEqual(pricing.PRICING["claude-sonnet-5-5"]["cache_read"], 0.10)
        self.assertEqual(pricing.PRICING["claude-fable-5-2"],
                         {"input": 8.0, "output": 40.0, "cache_write_5m": 10.0,
                          "cache_write_1h": 16.0, "cache_read": 0.20})

    def test_usage_key_splits_only_tiered_models_over_the_threshold(self):
        k = pricing.usage_key
        self.assertEqual(k("claude-haiku-5-5", 100_000), "claude-haiku-5-5")  # "over", not "at"
        self.assertEqual(k("claude-haiku-5-5", 100_001), "claude-haiku-5-5" + pricing.LONG_PROMPT_SUFFIX)
        self.assertEqual(k("claude-haiku-5-5-20261101", 150_000),
                         "claude-haiku-5-5-20261101" + pricing.LONG_PROMPT_SUFFIX)
        # 1M context at standard price on every other current model: never split.
        self.assertEqual(k("claude-opus-5-5", 900_000), "claude-opus-5-5")
        self.assertEqual(k("claude-haiku-4-5-20251001", 150_000), "claude-haiku-4-5-20251001")

    def test_dated_snapshot_id_falls_back_to_its_dateless_row(self):
        toks = {"input": 1_000_000, "output": 0, "cache_write_5m": 0, "cache_write_1h": 0, "cache_read": 0}
        c = pricing.cost({"claude-haiku-5-5-20261101": dict(toks),
                          "claude-haiku-5-5-20261101" + pricing.LONG_PROMPT_SUFFIX: dict(toks)})
        self.assertEqual(c["missing_models"], [])
        self.assertAlmostEqual(c["total"], 0.10 + 0.50, places=6)

    def test_unknown_model_is_null_and_listed(self):
        c = pricing.cost({"claude-opus-4-8": {"input": 1_000_000, "output": 0,
                                              "cache_write_5m": 0, "cache_write_1h": 0, "cache_read": 0},
                          "claude-made-up-9": {"input": 1_000_000, "output": 0,
                                               "cache_write_5m": 0, "cache_write_1h": 0, "cache_read": 0}})
        self.assertIsNone(c["by_model"]["claude-made-up-9"])
        self.assertIn("claude-made-up-9", c["missing_models"])
        # the known model still sums (5.0), the unknown does not zero the whole total.
        self.assertAlmostEqual(c["total"], 5.0, places=6)


class ContextProfileTest(unittest.TestCase):
    """The per-tool context profile: labels never carry arguments (writer commands export the
    proxy bearer), and growth is attributed to the turn whose tool results caused it."""

    def test_labels_are_safe(self):
        lab = transcript.tool_label
        secret = "b" * 64
        cmd = "export FETCH_PROXY_TOKEN='%s'; S=/tmp/x; python3 tools/fetch.py https://ex.org/a > $S/a" % secret
        self.assertEqual(lab("Bash", {"command": cmd}), "Bash fetch.py")
        self.assertEqual(lab("Bash", {"command": "cd /repo && grep -c foo bar.txt"}), "Bash grep")
        self.assertEqual(lab("Bash", {"command": "for f in a b; do python3 -I $S/titles.py $f; done"}),
                         "Bash titles.py")
        self.assertEqual(lab("Bash", {"command": "export X='%s'" % secret}), "Bash")
        self.assertEqual(lab("Read", {"file_path": "/home/user/repo/routines/news.md"}), "Read news.md")
        self.assertEqual(lab("WebSearch", {"query": secret}), "WebSearch")
        for label in (lab("Bash", {"command": cmd}), lab("WebSearch", {"query": secret})):
            self.assertNotIn(secret, label)

    def test_labels_never_come_from_arguments(self):
        # Review 2026-11-28: a .py anywhere in the command used to become the label, and a
        # backslash continuation put an exported token on a line of its own.
        lab = lambda c: transcript.tool_label("Bash", {"command": c})
        secret = "s3cr3tTOKEN"
        self.assertEqual(lab("curl -s https://www.abc.com.py/x"), "Bash curl")
        self.assertEqual(lab("cat /home/user/private_name.py | head"), "Bash cat")
        self.assertEqual(lab("export FETCH_PROXY_TOKEN=\\\n%s" % secret), "Bash")
        self.assertEqual(lab("export FETCH_PROXY_TOKEN=\\\n%s\npython3 tools/fetch.py u" % secret),
                         "Bash fetch.py")
        self.assertEqual(lab("python3 - <<'EOF'\n%s = 1\nEOF\necho ok" % secret), "Bash python3")
        self.assertEqual(lab("./tools/verify/build.sh && node tools/verify/suite.mjs"),
                         "Bash build.sh+suite.mjs")
        self.assertEqual(lab("(cd tools && python3 -m unittest discover)"), "Bash unittest")

    def test_growth_goes_to_the_turn_that_caused_it(self):
        def line(mid, prompt_read, out, tools):
            return {"type": "assistant", "timestamp": "2026-11-28T11:00:00Z",
                    "message": {"id": mid, "model": "claude-opus-5-5",
                                "usage": {"input_tokens": 0, "cache_read_input_tokens": prompt_read,
                                          "output_tokens": out},
                                "content": [{"type": "tool_use", "name": n, "input": i} for n, i in tools]}}
        rows = [line("m1", 20000, 100, [("Read", {"file_path": "/r/news.md"})]),
                line("m2", 28100, 200, [("Bash", {"command": "python3 tools/fetch.py u"}),
                                        ("Bash", {"command": "python3 tools/fetch.py v"})]),
                line("m3", 38300, 300, [])]
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "s.jsonl")
            with open(p, "w") as fh:
                fh.write(json.dumps({"type": "user", "message": {"content": "News routine"}}) + "\n")
                for r in rows:
                    fh.write(json.dumps(r) + "\n")
            prof = transcript.parse(p)["context_profile"]
        self.assertEqual((prof["start_tokens"], prof["turns"]), (20000, 3))
        by = {r["tool"]: r for r in prof["by_tool"]}
        self.assertEqual(by["Read news.md"], {"tool": "Read news.md", "calls": 1, "tokens": 8000})
        self.assertEqual(by["Bash fetch.py"], {"tool": "Bash fetch.py", "calls": 2, "tokens": 10000})


class LongPromptTest(unittest.TestCase):
    """Haiku 5.5 is priced per REQUEST by prompt length: parse files each request under the
    short or the long-prompt key on its own prompt, never on the run's totals."""

    def _line(self, mid, inp, read, cw5, out):
        return json.dumps({"type": "assistant", "uuid": mid, "sessionId": "s",
                           "timestamp": "2026-11-28T01:27:00.000Z",
                           "message": {"id": mid, "model": "claude-haiku-5-5", "content": [],
                                       "usage": {"input_tokens": inp, "cache_read_input_tokens": read,
                                                 "cache_creation_input_tokens": cw5,
                                                 "output_tokens": out}}})

    def test_requests_split_on_their_own_prompt(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "s.jsonl")
            with open(path, "w") as fh:
                # 60K prompt -> short row; 80K read + 30K write = 110K -> long row. The two
                # together (170K) must not move the first request onto the long row.
                fh.write(self._line("m1", 1_000, 50_000, 9_000, 200) + "\n")
                fh.write(self._line("m2", 1_000, 80_000, 30_000, 400) + "\n")
            m = transcript.parse(path, routine="watch")
        short = m["models"]["claude-haiku-5-5"]
        long_ = m["models"]["claude-haiku-5-5" + pricing.LONG_PROMPT_SUFFIX]
        self.assertEqual((short["messages"], short["cache_read"], short["output"]), (1, 50_000, 200))
        self.assertEqual((long_["messages"], long_["cache_read"], long_["output"]), (1, 80_000, 400))
        self.assertEqual(m["messages"], 2)
        self.assertEqual(m["totals"]["cache_read"], 130_000)
        c = pricing.cost(m["models"])
        want = (1_000 * 0.10 + 50_000 * 0.01 + 9_000 * 0.125 + 200 * 0.50
                + 1_000 * 0.50 + 80_000 * 0.05 + 30_000 * 0.625 + 400 * 2.50) / 1e6
        self.assertAlmostEqual(c["total"], want, places=9)
        self.assertEqual(c["missing_models"], [])


if __name__ == "__main__":
    unittest.main()
