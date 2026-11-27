"""Spec tests for tools/arxiv_window.py: the server-side submittedDate query, paging until the
window is exhausted, cross-category de-duplication, and the day-balanced line cap."""
import importlib.util
import io
import os
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("_arxiv_window", os.path.join(TOOLS, "arxiv_window.py"))
aw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(aw)


def _feed(total, entries):
    body = "".join(
        "<entry><id>http://arxiv.org/abs/%s v1</id><published>%sT10:00:00Z</published>"
        "<title>%s</title><summary>%s</summary>"
        '<arxiv:primary_category term="%s"/></entry>' % (i, d, t, s, c)
        for i, d, t, s, c in entries)
    return ('<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom" '
            'xmlns:arxiv="http://arxiv.org/schemas/atom" '
            'xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">'
            "<opensearch:totalResults>%d</opensearch:totalResults>%s</feed>" % (total, body)
            ).replace(" v1</id>", "v1</id>")


class ArxivWindowTest(unittest.TestCase):
    def test_query_is_a_server_side_range_with_encoded_brackets(self):
        url = aw.query_url("cs.LG", "20261121", "20261127", 500, 500)
        self.assertIn("submittedDate:%5B202611210000+TO+202611272359%5D", url)
        self.assertIn("start=500", url)
        self.assertNotIn("[", url)

    def test_pages_until_total_then_dedupes_and_spreads_over_days(self):
        lg = [("2611.%05d" % k, "2026-11-%02d" % (27 - k % 3), "LG paper %d" % k, "s", "cs.LG")
              for k in range(6)]
        ai = [("2611.00001", "2026-11-26", "LG paper 1", "s", "cs.LG"),
              ("2611.90000", "2026-11-25", "Reinforcement learning for agents", "s", "cs.AI")]
        pages = {("cs.LG", 0): _feed(6, lg[:4]), ("cs.LG", 4): _feed(6, lg[4:]),
                 ("cs.AI", 0): _feed(2, ai)}
        calls = []

        def fake(url):
            cat = url.split("cat:")[1].split("+")[0]
            start = int(url.split("start=")[1].split("&")[0])
            calls.append((cat, start))
            return pages[(cat, start)]

        out = io.StringIO()
        aw.run(["cs.LG", "cs.AI"], "20261125", "20261127", fake, max_lines=3, page_size=4, out=out)
        self.assertEqual(calls, [("cs.LG", 0), ("cs.LG", 4), ("cs.AI", 0)])
        lines = out.getvalue().splitlines()
        lg_lines = lines[1:4]
        self.assertEqual(len({l.split("\t")[1] for l in lg_lines}), 3, "one paper per day first")
        self.assertIn("total 6, fetched 6 in 2 page(s);", lines[0])
        ai_lines = [l for l in lines if l.startswith("2611.9")]
        self.assertEqual(len(ai_lines), 1)
        self.assertFalse([l for l in lines[5:] if l.startswith("2611.00001")],
                         "a paper listed under cs.LG is not repeated under cs.AI")

    def test_grep_filters_title_and_abstract(self):
        feed = _feed(2, [("2611.1", "2026-11-26", "A vision model", "uses reinforcement learning", "cs.CV"),
                         ("2611.2", "2026-11-26", "A tokenizer", "nothing else", "cs.CL")])
        out = io.StringIO()
        aw.run(["cs.CV"], "20261126", "20261126", lambda u: feed, grep=r"reinforcement", out=out)
        body = [l for l in out.getvalue().splitlines() if not l.startswith("#")]
        self.assertEqual([l.split("\t")[0] for l in body], ["2611.1"])

    def test_a_failed_fetch_reports_incomplete_instead_of_crashing(self):
        out = io.StringIO()
        aw.run(["cs.LG"], "20261126", "20261126", lambda u: None, out=out)
        self.assertIn("fetched 0 in 0 page(s) (INCOMPLETE: a call failed)", out.getvalue())

    def test_a_cross_list_fetched_but_not_printed_stays_eligible_later(self):
        lg = [("2611.%05d" % k, "2026-11-26", "LG %d" % k, "s", "cs.LG") for k in range(5)]
        ai = [("2611.00004", "2026-11-26", "LG 4", "s", "cs.LG")]   # printed nowhere under cs.LG
        pages = {"cs.LG": _feed(5, lg), "cs.AI": _feed(1, ai)}
        out = io.StringIO()
        aw.run(["cs.LG", "cs.AI"], "20261126", "20261126",
               lambda u: pages[u.split("cat:")[1].split("+")[0]], max_lines=2, out=out)
        ids = [l.split("\t")[0] for l in out.getvalue().splitlines() if not l.startswith("#")]
        self.assertIn("2611.00004", ids)

    def test_hitting_the_page_cap_is_reported_as_capped(self):
        feed = _feed(9, [("2611.%d" % k, "2026-11-26", "t", "s", "cs.LG") for k in range(2)])
        out = io.StringIO()
        aw.run(["cs.LG"], "20261126", "20261126", lambda u: feed, page_size=2, max_pages=1, out=out)
        self.assertIn("(CAPPED", out.getvalue())


if __name__ == "__main__":
    unittest.main()
