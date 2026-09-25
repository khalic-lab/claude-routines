#!/usr/bin/env python3
"""Static guards over the site's own CSS, JS and templates (2026-09-24 rewrite).

The rulings these hold are cheap to check without a browser and expensive to lose:
  - zero !important: cascade layers replace specificity fights (assets/css, one @layer per file);
  - DOM order is visual order: no grid-auto-flow:dense anywhere, and `order:` only on the four
    CHROME selectors that put the phone control bar in the thumb zone (.bar, .notice, main, .foot)
    -- a literal, recorded exception to PLAN decision 2, never on content;
  - no absolute positioning in the layout layer (zones reserve their own space);
  - no third-party requests from assets: the only hosts are the two Workers;
  - every JS module parses, and the import map lists exactly the modules that exist;
  - an old-shape feed (no `days`) renders a first-line notice, not an empty board (R21).
The browser-level checks live in tools/verify/suite.mjs.
"""
import glob
import os
import re
import shutil
import subprocess
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSS = sorted(glob.glob(os.path.join(REPO, "assets", "css", "*.css")))
JS = sorted(glob.glob(os.path.join(REPO, "assets", "js", "*.js")))
HOME = os.path.join(REPO, "_layouts", "home.html")
TOKENS = os.path.join(REPO, "_includes", "tokens.html")
WORKER_HOSTS = {"feedback-sink.khalic-lab.workers.dev", "og-proxy.khalic-lab.workers.dev"}
ORDER_ALLOWED = {".bar", ".notice", "main", ".foot"}     # chrome only; see the module docstring


def read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def rules(css):
    """(selector, declarations) for every innermost rule block, at-rule nesting ignored."""
    return [(sel.strip(), body) for sel, body in re.findall(r"([^{}]*)\{([^{}]*)\}", strip_comments(css))]


class CssTest(unittest.TestCase):
    def test_there_is_css_to_check(self):
        names = {os.path.basename(p) for p in CSS}
        self.assertTrue({"reset.css", "base.css", "layout.css", "components.css", "state.css"} <= names, names)

    def test_zero_important(self):
        for p in CSS + [TOKENS, HOME]:
            self.assertNotIn("!important", strip_comments(read(p)), os.path.relpath(p, REPO))

    def test_no_dense_packing_anywhere(self):
        for p in CSS:
            self.assertNotRegex(strip_comments(read(p)), r"grid-auto-flow\s*:[^;]*dense", os.path.relpath(p, REPO))

    def test_order_only_on_chrome(self):
        seen = set()
        for p in CSS:
            for sel, body in rules(read(p)):
                if re.search(r"(^|[;\s])order\s*:", body):
                    for s in (x.strip() for x in sel.split(",")):
                        self.assertIn(s, ORDER_ALLOWED, "%s: `order` on %r -- DOM order is visual order for content"
                                      % (os.path.basename(p), s))
                        seen.add(s)
        self.assertEqual(seen, ORDER_ALLOWED, "the chrome exception should be exactly these four")

    def test_layout_layer_positions_nothing_absolutely(self):
        css = strip_comments(read(os.path.join(REPO, "assets", "css", "layout.css")))
        self.assertNotRegex(css, r"position\s*:\s*(absolute|fixed)")

    def test_every_sheet_is_wholly_layered_in_the_declared_order(self):
        order = re.search(r"@layer\s+([\w\s,]+);", read(TOKENS)).group(1)
        declared = [x.strip() for x in order.split(",")]
        self.assertEqual(declared, ["reset", "tokens", "base", "layout", "components", "utilities", "state"])
        for p in CSS:
            css = strip_comments(read(p)).strip()
            depth, i, top = 0, 0, []
            for m in re.finditer(r"[{}]", css):
                if m.group() == "{":
                    if depth == 0:
                        top.append(css[i:m.start()].strip())
                    depth += 1
                else:
                    depth -= 1
                    if depth == 0:
                        i = m.end()
            self.assertTrue(top, p)
            for head in top:
                m = re.fullmatch(r"@layer\s+(\w+)", head)
                self.assertTrue(m, "%s: unlayered top-level rule %r" % (os.path.basename(p), head[:60]))
                self.assertIn(m.group(1), declared)

    def test_tokens_include_holds_no_layout(self):
        src = re.sub(r"\{%-?\s*comment\s*-?%\}.*?\{%-?\s*endcomment\s*-?%\}", "", read(TOKENS), flags=re.S)
        css = strip_comments("".join(re.findall(r"<style>(.*?)</style>", src, re.S)))
        self.assertIn("--paper", css)
        for banned in (r"position\s*:\s*(fixed|sticky)", r"100d?vh", r"overflow-y\s*:"):
            self.assertNotRegex(css, banned)


class AssetsTest(unittest.TestCase):
    def test_no_third_party_hosts(self):
        for p in CSS + JS:
            for host in re.findall(r"https?://([^/'\"\s)]+)", strip_comments(read(p))):
                self.assertIn(host, WORKER_HOSTS, "%s requests %s" % (os.path.relpath(p, REPO), host))

    def test_import_map_lists_exactly_the_modules(self):
        m = re.search(r"^js:\s*\[([^\]]*)\]", read(HOME), re.M)
        listed = [x.strip() for x in m.group(1).split(",")]
        self.assertEqual(listed[0], "main")
        self.assertEqual(sorted(listed), sorted(os.path.splitext(os.path.basename(p))[0] for p in JS))

    def test_modules_import_only_siblings(self):
        for p in JS:
            for spec in re.findall(r"""(?:from|import)\s*\(?\s*['"]([^'"]+)['"]""", read(p)):
                self.assertRegex(spec, r"^\./[a-z]+\.js$", "%s imports %s" % (os.path.basename(p), spec))
                self.assertTrue(os.path.exists(os.path.join(os.path.dirname(p), spec[2:])), spec)

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_every_module_parses(self):
        with tempfile.TemporaryDirectory() as d:
            for p in JS:
                dst = os.path.join(d, os.path.basename(p)[:-3] + ".mjs")
                shutil.copy(p, dst)
                r = subprocess.run([shutil.which("node"), "--check", dst], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, "%s: %s" % (os.path.basename(p), r.stderr))


class TemplateTest(unittest.TestCase):
    def test_old_shape_feed_says_so_on_the_first_line(self):
        """A feed built before the views existed has no `days`. The page must then say the edition
        is updating where the first story would be (R21), not render an empty board."""
        src = read(HOME)
        branch = src.find("{%- if feed.days == nil %}")
        notice = src.find("Edition data is updating, reload in a minute.")
        loop = src.find("{%- for d in feed.days %}")
        self.assertTrue(0 <= branch < notice < loop, (branch, notice, loop))
        self.assertIn('<p class="empty" data-zone="empty">Edition data is updating', src)

    def test_read_ids_ride_on_the_item(self):
        """data-story on the card/row/editorial itself, value `sid | default: id` (contract)."""
        for inc in ("front-card.html", "row.html"):
            s = read(os.path.join(REPO, "_includes", "home", inc))
            self.assertIn("{%- assign id = s.sid | default: s.id -%}", s)
            self.assertIn('data-story="{{ id }}" data-edition="{{ s.edition }}"', s)
        self.assertIn('data-story="{{ e.sid }}"', read(os.path.join(REPO, "_includes", "home", "editorial.html")))

    def test_deck_prints_when_the_record_has_one(self):
        """`deck` is emitted only when non-empty (test_deck.py); the page prints it after the
        headline and before the image slot (type leads, R9)."""
        card = read(os.path.join(REPO, "_includes", "home", "front-card.html"))
        self.assertLess(card.find("{%- if s.deck %}"), card.find('<figure class="photo'))
        self.assertLess(card.find("home/headline.html"), card.find("{%- if s.deck %}"))
        self.assertIn('<p class="deck">{{ s.deck | escape }}</p>', read(os.path.join(REPO, "_includes", "home", "row.html")))

    def test_no_theme_left(self):
        self.assertNotRegex(read(os.path.join(REPO, "_config.yml")), r"(?m)^remote_theme:")
        self.assertFalse(os.path.exists(os.path.join(REPO, "_includes", "head", "custom.html")))
        for p in glob.glob(os.path.join(REPO, "_layouts", "*.html")) + glob.glob(os.path.join(REPO, "_includes", "**", "*.html"), recursive=True):
            self.assertNotRegex(read(p), r"include\s+(head/custom|copyright|scripts|footer)\.html", p)


if __name__ == "__main__":
    unittest.main()
