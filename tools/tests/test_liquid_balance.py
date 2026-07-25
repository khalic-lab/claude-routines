#!/usr/bin/env python3
"""Liquid block tags must balance in every template.

WHY THIS EXISTS. Nothing else in the repo can catch a malformed Liquid tag before GitHub
Pages does. `tools/home_harness.py` regex-extracts the <style>/<script> blocks and builds
the cards in Python — it never parses Liquid — and the rest of `tools/tests` is Python
covering Python. So the first thing that ever sees a broken template is the Pages build,
and a failed Pages deploy poisons the commit SHA: rebuilding the SAME sha keeps failing,
and the fix is a new commit (see the pages-deploy-wedge history). That makes a Liquid
syntax error unusually expensive for how trivially it happens.

It happens trivially. On 2026-07-25, editing `_layouts/home.html`, a partially-reverted
edit left an orphan `{%- endcomment -%}` with prose above it that would have rendered
inside `.folio-grid`. It was caught by hand-counting tags, which is not a process.

WHAT THIS DOES NOT DO. It is a tag-balance check, not a Liquid parser: it does not
validate filters, expressions, object paths or `{{ }}` output. A template can pass here
and still fail to build. It closes one specific, recurring, cheap-to-detect class.
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Liquid block tags that open a scope and must be closed. `else`/`elsif`/`when` are
# continuations — they neither open nor close — and are checked to be inside a legal parent.
OPENERS = {"if", "unless", "for", "case", "capture", "tablerow", "comment", "raw", "form",
           "highlight", "schema", "javascript", "stylesheet"}
CONTINUATIONS = {"else": {"if", "unless", "case", "for"},
                 "elsif": {"if", "unless"},
                 "when": {"case"},
                 "break": {"for", "tablerow"},
                 "continue": {"for", "tablerow"}}

TAG_RE = re.compile(r"\{%-?\s*(\w+)")


def templates():
    """Every Liquid-bearing file we author. Excludes vendored/generated trees."""
    out = []
    for sub in ("_layouts", "_includes", "_pages"):
        base = os.path.join(ROOT, sub)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirnames, filenames in os.walk(base):
            for fn in filenames:
                if fn.endswith((".html", ".md")):
                    out.append(os.path.join(dirpath, fn))
    for fn in ("index.html", "index.md"):
        p = os.path.join(ROOT, fn)
        if os.path.isfile(p):
            out.append(p)
    return sorted(out)


def scan(text):
    """-> (errors, depth_at_eof). Errors are human-readable strings with line numbers.

    `comment` and `raw` swallow their contents: Liquid does not interpret tags inside
    them, so neither may this. That is precisely the orphan-endcomment case — the prose
    between a stray `{%- endcomment -%}` and the real one is NOT inert.
    """
    errors, stack = [], []
    for m in TAG_RE.finditer(text):
        tag = m.group(1)
        line = text.count("\n", 0, m.start()) + 1
        # Inside comment/raw only the matching end tag is live.
        if stack and stack[-1][0] in ("comment", "raw"):
            if tag == "end" + stack[-1][0]:
                stack.pop()
            continue
        if tag in OPENERS:
            stack.append((tag, line))
        elif tag.startswith("end"):
            want = tag[3:]
            if not stack:
                errors.append("line %d: {%% %s %%} with nothing open" % (line, tag))
            elif stack[-1][0] != want:
                open_tag, open_line = stack[-1]
                errors.append("line %d: {%% %s %%} closes {%% %s %%} opened at line %d"
                              % (line, tag, open_tag, open_line))
                stack.pop()
            else:
                stack.pop()
        elif tag in CONTINUATIONS:
            if not stack or stack[-1][0] not in CONTINUATIONS[tag]:
                inside = stack[-1][0] if stack else "nothing"
                errors.append("line %d: {%% %s %%} inside %s" % (line, tag, inside))
    for open_tag, open_line in stack:
        errors.append("line %d: {%% %s %%} is never closed" % (open_line, open_tag))
    return errors, len(stack)


class LiquidBalanceTests(unittest.TestCase):
    def test_every_template_balances(self):
        found = templates()
        self.assertTrue(found, "no templates discovered — the walk roots are wrong")
        problems = []
        for path in found:
            with open(path, encoding="utf-8") as fh:
                errors, _ = scan(fh.read())
            for e in errors:
                problems.append("%s: %s" % (os.path.relpath(path, ROOT), e))
        self.assertEqual(problems, [], "unbalanced Liquid:\n  " + "\n  ".join(problems))

    def test_home_layout_is_covered(self):
        """Guard the guard: the walk must actually reach the file this was written for."""
        rels = [os.path.relpath(p, ROOT) for p in templates()]
        self.assertIn(os.path.join("_layouts", "home.html"), rels)

    # --- the checker itself, or it could pass everything and we would not know ---

    def test_detects_orphan_endcomment(self):
        errors, _ = scan("{%- comment -%}a{%- endcomment -%}\nprose\n{%- endcomment -%}")
        self.assertTrue(any("nothing open" in e for e in errors), errors)

    def test_detects_unclosed_for(self):
        errors, _ = scan("{% for s in x %}<p>{{ s }}</p>")
        self.assertTrue(any("never closed" in e for e in errors), errors)

    def test_detects_crossed_tags(self):
        errors, _ = scan("{% if a %}{% for b in c %}{% endif %}{% endfor %}")
        self.assertTrue(any("closes" in e for e in errors), errors)

    def test_detects_orphan_else(self):
        errors, _ = scan("{% for a in b %}{% endfor %}{% else %}")
        self.assertTrue(any("inside nothing" in e for e in errors), errors)

    def test_tags_inside_comment_are_inert(self):
        errors, _ = scan("{%- comment -%} {% for x in y %} unclosed prose {%- endcomment -%}")
        self.assertEqual(errors, [], errors)

    def test_tags_inside_raw_are_inert(self):
        errors, _ = scan("{% raw %}{% endif %}{% endraw %}")
        self.assertEqual(errors, [], errors)

    def test_accepts_the_real_shapes_home_uses(self):
        errors, _ = scan(
            "{% if feed %}{% for s in feed.stories %}"
            "{% case s.importance %}{% when 3 %}Lead{% when 2 %}Feature{% else %}Brief{% endcase %}"
            "{% if forloop.index == n %}{% for e in feed.editorials %}{% endfor %}{% endif %}"
            "{% endfor %}{% else %}empty{% endif %}")
        self.assertEqual(errors, [], errors)


if __name__ == "__main__":
    unittest.main()
