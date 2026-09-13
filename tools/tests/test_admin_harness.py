"""Static checks over the /admin/ harness output — the ceiling of verification available without a
browser (the no-browser rule for agents). We render tools/admin/harness.py, then assert the shape
the architect will screenshot: the fixture's data is inlined, no Liquid survives, nothing loads off
the network except the self-hosted fonts, the document-scroll constraints hold, and every JS block
parses under `node --check`. The layout's page script carries no dependency on _layouts/home.html.

The harness is run by subprocess, not imported: tools/admin/ holds only harness.py on this branch
(tools/admin/__init__.py is a sibling slice), so a package import would fail before integration.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HARNESS = os.path.join(REPO, "tools", "admin", "harness.py")
LAYOUT = os.path.join(REPO, "_layouts", "admin.html")
PAGE = os.path.join(REPO, "admin.html")
FIXTURE = os.path.join(REPO, "tools", "tests", "fixtures", "admin-snapshot.json")

SECTIONS = ["sec-status", "sec-usage", "sec-sources", "sec-add", "sec-pending", "sec-proposals"]


def _scripts(html):
    return re.findall(r"<script>(.*?)</script>", html, re.S)


def _strip_comments(html):
    # drop HTML and CSS/JS block comments so a banned token quoted inside a comment (e.g. this
    # file's own "no 100vh" note) is not mistaken for a real declaration. `//` is left alone —
    # stripping it would eat the `https://` inside URL strings.
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    return re.sub(r"/\*.*?\*/", "", html, flags=re.S)


class AdminHarness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.signed_in = os.path.join(cls.tmp.name, "in.html")
        cls.signed_out = os.path.join(cls.tmp.name, "out.html")
        subprocess.run([sys.executable, HARNESS, "--out", cls.signed_in], cwd=REPO, check=True)
        subprocess.run([sys.executable, HARNESS, "--out", cls.signed_out, "--signed-out"],
                       cwd=REPO, check=True)
        with open(cls.signed_in) as fh:
            cls.html = fh.read()
        with open(cls.signed_out) as fh:
            cls.out_html = fh.read()
        with open(FIXTURE) as fh:
            cls.fix = json.load(fh)
        with open(LAYOUT) as fh:
            cls.layout = fh.read()
        with open(PAGE) as fh:
            cls.page = fh.read()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    # ---- content is really inlined ----
    def test_fixture_domains_present(self):
        for s in self.fix["sources"]:
            self.assertIn(s["domain"], self.html, "domain missing from harness output: " + s["domain"])

    def test_recent_actions_present(self):
        for a in self.fix["actions_recent"]:
            self.assertIn(a["domain"], self.html)
        # the rejected action's error text must be inlined so the screenshot shows the failure
        rej = [a for a in self.fix["actions_recent"] if a["result"] == "rejected"]
        self.assertTrue(rej, "fixture must carry a rejected action")
        self.assertIn(rej[0]["error"], self.html)

    def test_proposal_present(self):
        self.assertIn(self.fix["proposals_pending"][0]["file"], self.html)

    # ---- no Liquid survives ----
    def test_no_liquid(self):
        self.assertNotIn("{{", self.html)
        self.assertNotIn("{%", self.html)
        self.assertNotIn("{{", self.out_html)
        self.assertNotIn("{%", self.out_html)

    # ---- no network except the self-hosted fonts ----
    def test_no_external_src_or_href(self):
        for attr in re.findall(r'(?:src|href)\s*=\s*"([^"]*)"', self.html):
            self.assertNotRegex(attr, r"^https?://", "external resource referenced: " + attr)
        # every url() in CSS is either a data:/file:// font under assets/fonts or relative
        for u in re.findall(r"url\(([^)]*)\)", self.html):
            u = u.strip("'\"")
            if re.match(r"^https?://", u):
                self.fail("external url() in CSS: " + u)
            if u.startswith("file://"):
                self.assertIn("/assets/fonts/", u, "only fonts may load off file://: " + u)

    # ---- head ----
    def test_viewport_fit_cover(self):
        self.assertRegex(self.html, r'name="viewport"[^>]*viewport-fit=cover')

    def test_robots_noindex(self):
        self.assertRegex(self.html, r'name="robots"[^>]*noindex')

    def test_charset(self):
        self.assertRegex(self.html, r'<meta\s+charset="utf-8">')

    # ---- document-scroll constraints (vertical only; overflow-x is allowed for wide tables) ----
    def test_no_fixed_or_full_viewport(self):
        css = _strip_comments(self.html)
        for banned in (r"position:\s*fixed", r"position:\s*sticky", r"100vh", r"100dvh",
                       r"overflow-y\s*:"):
            self.assertNotRegex(css, banned, "banned layout token present: " + banned)

    def test_wide_tables_use_overflow_x(self):
        # the plan explicitly permits tables to scroll sideways in their own wrapper
        self.assertRegex(self.layout, r"overflow-x\s*:\s*auto")

    # ---- one style, one script (the plan pins this on the LAYOUT, not the harness output) ----
    def test_layout_single_style_single_script(self):
        self.assertEqual(len(re.findall(r"<style>", self.layout)), 1)
        self.assertEqual(len(re.findall(r"<script>", self.layout)), 1)

    # ---- six sections, in order ----
    def test_all_sections_present(self):
        idx = [self.page.find('id="%s"' % s) for s in SECTIONS]
        self.assertTrue(all(i >= 0 for i in idx), "a section id is missing: " + str(dict(zip(SECTIONS, idx))))
        self.assertEqual(idx, sorted(idx), "sections are out of the order plan §2.6 fixes")

    # ---- no dependency on the homepage script ----
    def test_self_contained_auth(self):
        script = _scripts(self.layout)[0]
        for fn in ("function session", "function doLogin", "function b64uToBuf", "function bufToB64u"):
            self.assertIn(fn, script, "the page must define its own " + fn + ", not borrow home's")
        # the real "no dependency" proof: the page loads no external script at all
        self.assertNotRegex(self.html, r"<script[^>]+src\s*=", "the admin page must load no external script")

    def test_session_shape_matches_home(self):
        script = _scripts(self.layout)[0]
        # same validator and same {token, reader, at} seed shape as _layouts/home.html
        self.assertIn("typeof s.token === \"string\" && s.token && s.reader", script)
        self.assertIn("reader: j.reader, at: Date.now()", script)

    # ---- form validation mirrors §2.2 ----
    def test_add_validation_rules(self):
        script = _scripts(self.layout)[0]
        self.assertIn(r"(?=.{4,253}$)[a-z0-9]", script, "the §2.2 domain regex must be enforced")
        self.assertIn('tier: { T1:1, T2:1 }', script)
        self.assertIn('"search-only":1', script)
        self.assertIn('"blocked-paywall":1', script)
        for st in ("news", "ai-ml", "science", "weekend", "sports"):
            self.assertIn(st, script)

    # ---- signed-out mode shows only sign-in, seeds no session, makes no calls ----
    def test_signed_out_no_session_seed(self):
        self.assertNotIn("localStorage.setItem('syncSession:v1', JSON.stringify", self.out_html)
        self.assertIn("localStorage.setItem('syncSession:v1', JSON.stringify", self.html)

    def test_signed_out_gate_markup(self):
        self.assertIn('id="signed-out"', self.out_html)
        self.assertIn("Sign in with passkey", self.out_html)

    # ---- fixture is internally consistent (an inconsistent fixture reads as a broken page) ----
    def test_fixture_window_sums(self):
        u = self.fix["usage"]
        self.assertEqual(u["records"], 12)
        by_id = {r["session_id"]: r for r in u["recent"]}
        self.assertEqual(len(by_id), 12, "recent runs must have distinct session ids")
        # 30d window must sum every record; 7d a strict subset
        s30 = _sum_tokens([r["tokens"] for r in u["recent"]])
        self.assertEqual(u["windows"]["30d"]["runs"], 12)
        self.assertEqual(_tok_total(u["windows"]["30d"]["tokens"]), _tok_total(s30))
        self.assertLess(u["windows"]["7d"]["runs"], u["windows"]["30d"]["runs"],
                        "7d must be a strict subset of 30d or the tiles all read the same")
        self.assertGreater(u["windows"]["7d"]["runs"], 0)
        # by_routine covers exactly the two routines and its runs sum to 12
        self.assertEqual(sorted(u["by_routine"].keys()), ["news", "watch"])
        self.assertEqual(sum(b["runs"] for b in u["by_routine"].values()), 12)

    def test_fixture_has_every_status(self):
        statuses = set(s["status"] for s in self.fix["sources"])
        self.assertEqual(statuses, {"candidate", "probation", "established", "demoted", "retired"},
                         "fixture must exercise every status, demoted included (§3 S4)")
        self.assertGreaterEqual(len(self.fix["sources"]), 40)

    # ---- every JS block in the rendered page parses ----
    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_scripts_parse(self):
        for i, body in enumerate(_scripts(self.html)):
            f = os.path.join(self.tmp.name, "s%d.js" % i)
            with open(f, "w") as fh:
                fh.write(body)
            r = subprocess.run([shutil.which("node"), "--check", f], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, "script %d failed node --check:\n%s" % (i, r.stderr))


def _sum_tokens(toks):
    out = {"input": 0, "cache_write": 0, "cache_read": 0, "output": 0}
    for t in toks:
        for k in out:
            out[k] += t.get(k, 0)
    return out


def _tok_total(t):
    return t.get("input", 0) + t.get("cache_write", 0) + t.get("cache_read", 0) + t.get("output", 0)


if __name__ == "__main__":
    unittest.main()
