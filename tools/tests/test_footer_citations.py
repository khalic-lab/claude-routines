"""Spec tests for tools/footer.py's citation recognizer -- the three registers.

Contract: a citation line is a bullet cite, a heading cite, OR a bold-lead
PARAGRAPH story (ai-ml's industry / new-models items, which match neither of the
lint's two registers -- the blind spot that reported `via-snippet citations: 0`
on _posts/2026-08-07-ai-ml.md while its body carried five `[via snippet]` tags).
Label-lead continuation paragraphs (`**Why it matters:**`) and plain prose must
never count, even when they carry links.
"""
import importlib.util
import os
import tempfile
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


footer = _load("_footer_cites", os.path.join(TOOLS, "footer.py"))

REGISTRY = """t1.example:
  tier: T1
  status: established
t2.example:
  tier: T2
  status: probation
"""

# Real-shaped lines lifted from the live post shapes (arXiv bullet, science/sports
# heading cite, ai-ml bold-lead industry paragraph, its `Why it matters:` follow-on).
BULLET = ('- <a id="st-f2748bffdaad" class="st-a"></a>**Letting models call tools by writing '
          'code beats JSON** — [arXiv:2608.06370](https://t1.example/abs/2608.06370) · '
          'I. Patel et al. (PwC) · `[preprint]`')
HEADING = ('**[Berkeley Lab](https://t1.example/2026/08/04/quantum-fluid/)** · Ruishi Qi, '
           'Feng Wang et al. (Lawrence Berkeley National Laboratory) · published 2026-08-04')
PARA = ('**Anthropic starts an in-house chip team to co-design silicon with Claude.** '
        'Anthropic confirmed on 5 August 2026 that it is building an in-house team to design '
        'custom chips. ([TechCrunch, 5 Aug 2026](https://t2.example/2026/08/05/chip-team/) '
        '`[via snippet]`; [Forbes, 6 Aug 2026](https://unknown.example/chip-race/) '
        '`[via snippet]`)')
PARA_ITALICS = ('**The US settles on a voluntary review — and will *not* publish the rules.** '
                'The White House finalised its framework. '
                '([Axios, 4 Aug 2026](https://t2.example/2026/08/04/ai-framework) '
                '`[via snippet]`)')
WHY = ('**Why it matters:** frontier-lab economics are increasingly a hardware story, as '
       '[this earlier piece](https://t1.example/analysis) argued.')
PROSE = ('The framework flows from Executive Order 14409, signed 2 June 2026, which directed '
         'agencies to stand up a [voluntary scheme](https://t1.example/eo-14409).')


class CitationRegisterTest(unittest.TestCase):
    def cites(self, *lines):
        return footer.citation_lines("\n".join(lines))

    def test_bullet_cite_counts(self):
        c = self.cites(BULLET)
        self.assertEqual([x["domain"] for x in c], ["t1.example"])

    def test_heading_cite_counts(self):
        c = self.cites(HEADING)
        self.assertEqual([x["domain"] for x in c], ["t1.example"])

    def test_bold_lead_paragraph_cite_counts_with_via_snippet(self):
        c = self.cites(PARA)
        self.assertEqual([x["domain"] for x in c], ["t2.example"])  # FIRST link attributes
        self.assertIn(footer.VIA_SNIPPET, c[0]["line"])

    def test_bold_lead_with_inline_italics_still_counts(self):
        # a non-greedy `**...**` must not be defeated by a single-asterisk italic
        self.assertEqual([x["domain"] for x in self.cites(PARA_ITALICS)], ["t2.example"])

    def test_why_it_matters_label_paragraph_does_not_count(self):
        self.assertEqual(self.cites(WHY), [])

    def test_plain_prose_paragraph_does_not_count(self):
        self.assertEqual(self.cites(PROSE), [])

    def test_indented_why_it_matters_under_a_bullet_does_not_count(self):
        self.assertEqual(self.cites("  " + WHY), [])

    def test_mixed_body_counts_exactly_the_citation_lines(self):
        c = self.cites(BULLET, "", HEADING, "", PARA, WHY, "", PROSE)
        self.assertEqual(len(c), 3)
        self.assertEqual(sum(1 for x in c if footer.VIA_SNIPPET in x["line"]), 1)


POST = """---
layout: single
title: "AI/ML — 2026-08-07"
date: 2026-08-07T12:00:00+02:00
categories: [ai-ml]
---

# AI/ML Brief — 2026-08-07

## 📄 ML/AI research (arXiv)

%s

  **Why it matters:** the code-native path improves as models get more capable.

## 💼 Industry, funding, regulation

%s
%s

---

## Coverage footer
<!-- operational telemetry — machine/evaluator-read; hidden from the rendered page
- Sources used: T1 = 1, T2 = 0, untiered = 0 (registry tier of each citation's first link)
- Direct fetches: 1 | via-snippet citations: 0
-->
- Gaps: none worth noting.
""" % (BULLET, PARA, WHY)


class EndToEndTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="footer-cites-test-")
        os.makedirs(os.path.join(self.root, "sources"))
        with open(os.path.join(self.root, "sources", "registry.yml"), "w") as fh:
            fh.write(REGISTRY)
        self.post = os.path.join(self.root, "post.md")
        with open(self.post, "w") as fh:
            fh.write(POST)

    def test_paragraph_cites_reach_the_computed_telemetry(self):
        rc = footer.main([self.post, "--root", self.root, "--fetch-log", "/nonexistent"])
        self.assertEqual(rc, 0)
        with open(self.post) as fh:
            text = fh.read()
        # bullet (t1, direct) + paragraph (t2, via snippet); the `Why it matters:` line is prose
        self.assertIn("- Sources used: T1 = 1, T2 = 1, untiered = 0", text)
        self.assertIn("- Direct fetches: 1 | via-snippet citations: 1", text)


if __name__ == "__main__":
    unittest.main()
