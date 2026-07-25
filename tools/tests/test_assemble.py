"""Spec tests for routines/assemble.py -- the writer-prompt assembler.

Contract under test: `<!-- include: _shared/x.md -->` expands in place, and `{slug}` resolves to
the stream the generated file belongs to (so a shared partial can carry a concrete
`preflight.py --slug news` instead of making the routine work out its own slug at fire time).
Plus the invariant the drift guard rests on: assemble() is pure -- same sources, same bytes.
"""
import importlib.util
import os
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
spec = importlib.util.spec_from_file_location(
    "_assemble", os.path.join(REPO, "routines", "assemble.py"))
assemble_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assemble_mod)


class AssembleTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="assemble-test-")
        self.shared = os.path.join(self.tmp, "_shared")
        self.src = os.path.join(self.tmp, "src")
        os.makedirs(self.shared)
        os.makedirs(self.src)
        self._orig_shared = assemble_mod.SHARED_DIR
        assemble_mod.SHARED_DIR = self.shared
        self.addCleanup(setattr, assemble_mod, "SHARED_DIR", self._orig_shared)

    def _write(self, path, text):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def test_include_expands_and_slug_resolves_in_partial(self):
        self._write(os.path.join(self.shared, "plan.md"),
                    "Run:\n\n    preflight.py --slug {slug}\n")
        src = self._write(os.path.join(self.src, "science.md"),
                          "Head\n\n<!-- include: _shared/plan.md -->\n\nTail\n")
        out = assemble_mod.assemble(src)
        self.assertIn("preflight.py --slug science", out)
        self.assertNotIn("{slug}", out)
        self.assertLess(out.index("Head"), out.index("preflight.py"))
        self.assertLess(out.index("preflight.py"), out.index("Tail"))

    def test_slug_resolves_in_the_stream_body_too(self):
        src = self._write(os.path.join(self.src, "ai-ml.md"), "slug is {slug}\n")
        self.assertEqual(assemble_mod.assemble(src).strip(), "slug is ai-ml")

    def test_each_stream_gets_its_own_slug(self):
        self._write(os.path.join(self.shared, "p.md"), "--slug {slug}")
        got = {}
        for slug in ("news", "weekend", "sports"):
            src = self._write(os.path.join(self.src, slug + ".md"),
                              "<!-- include: _shared/p.md -->\n")
            got[slug] = assemble_mod.assemble(src).strip()
        self.assertEqual(got, {"news": "--slug news", "weekend": "--slug weekend",
                               "sports": "--slug sports"})

    def test_missing_partial_is_fatal(self):
        src = self._write(os.path.join(self.src, "news.md"),
                          "<!-- include: _shared/nope.md -->\n")
        with self.assertRaises(SystemExit):
            assemble_mod.assemble(src)

    def test_deterministic(self):
        """The `assemble.py check` drift guard is only meaningful if assemble() is pure."""
        self._write(os.path.join(self.shared, "p.md"), "shared {slug} body")
        src = self._write(os.path.join(self.src, "news.md"),
                          "a\n<!-- include: _shared/p.md -->\nb\n")
        self.assertEqual(assemble_mod.assemble(src), assemble_mod.assemble(src))


class LiveTreeTest(unittest.TestCase):
    """The committed prompts must match their sources -- same check the pre-commit guard runs."""

    def test_generated_prompts_match_sources(self):
        import glob
        src_dir = os.path.join(REPO, "routines", "src")
        for src in sorted(glob.glob(os.path.join(src_dir, "*.md"))):
            name = os.path.basename(src)
            with open(os.path.join(REPO, "routines", name), encoding="utf-8") as fh:
                current = fh.read()
            self.assertEqual(current, assemble_mod.assemble(src),
                             "%s is stale -- run python3 routines/assemble.py" % name)

    def test_every_writer_publishes_under_its_OWN_slug(self):
        """The nastiest shape a shared partial can produce: News telling the routine to publish
        `--slug ai-ml`. `assemble.py check` cannot see it -- generated still equals sources --
        and the run would end DONE, having written the wrong edition's stub, commit message and
        index file. Nothing else in the suite reads the prompts."""
        import glob
        import re
        for src in sorted(glob.glob(os.path.join(REPO, "routines", "src", "*.md"))):
            slug = os.path.splitext(os.path.basename(src))[0]
            with open(os.path.join(REPO, "routines", slug + ".md"), encoding="utf-8") as fh:
                text = fh.read()
            found = re.findall(r"tools/publish\.py --slug ([a-z-]+)", text)
            self.assertEqual(found, [slug],
                             "%s.md must contain exactly one publish command, for its own slug; "
                             "found %r" % (slug, found))
            plans = re.findall(r"preflight\.py --slug ([a-z-]+)", text)
            self.assertEqual(set(plans), {slug},
                             "%s.md builds another stream's source plan: %r" % (slug, plans))
            self.assertIn("This routine's slug is `%s`" % slug, text,
                          "%s.md must tell DEDUP.md its own slug" % slug)

    def test_shared_publish_partials_reach_every_writer(self):
        """The publish block lives in two partials since 2026-07-25. A stream that loses its
        include still assembles cleanly and still passes `check` -- it just silently stops
        telling the routine how to publish at all."""
        import glob
        for name in ("publish-step.md", "publish-outcomes.md"):
            path = os.path.join(REPO, "routines", "_shared", name)
            self.assertTrue(os.path.exists(path), "missing partial %s" % name)
            with open(path, encoding="utf-8") as fh:
                # first substantive line of the partial, slug token resolved per stream
                marker = [l for l in fh.read().split("\n")
                          if l.strip() and not l.startswith("#") and "{slug}" not in l][0]
            for src in sorted(glob.glob(os.path.join(REPO, "routines", "src", "*.md"))):
                slug = os.path.splitext(os.path.basename(src))[0]
                with open(os.path.join(REPO, "routines", slug + ".md"), encoding="utf-8") as fh:
                    text = fh.read()
                # assertTrue, not assertIn: a failed assertIn would dump the whole 20 KB prompt
                self.assertTrue(marker in text,
                                "%s.md is missing content from %s -- did it lose the include? "
                                "expected line: %r" % (slug, name, marker[:60]))

    def test_every_writer_keeps_the_contracts_only_it_can_satisfy(self):
        """Guards the determinization's boundary: prose the TOOLS parse but only the model can
        produce. Losing one of these breaks telemetry or the lint quietly, never loudly."""
        import glob
        for src in sorted(glob.glob(os.path.join(REPO, "routines", "src", "*.md"))):
            slug = os.path.splitext(os.path.basename(src))[0]
            with open(os.path.join(REPO, "routines", slug + ".md"), encoding="utf-8") as fh:
                text = fh.read()
            for needle, why in (
                    ("[via snippet]", "footer.py counts direct-vs-snippet from this tag"),
                    ("[new source]", "sources/lint.py checks novelty against this tag"),
                    ("- Discovery:", "the Discovery footer contract the lint enforces"),
                    ("--notify-body", "the teaser is the writer's only notification input"),
                    ("{teaser}", "the stream's own teaser rule"),
            ):
                self.assertIn(needle, text, "%s.md lost %r -- %s" % (slug, needle, why))

    def test_no_unresolved_slug_token_ships(self):
        """Generated prompts only -- weekly-evaluator.md is hand-maintained and uses `{slug}`
        as a genuine pattern (`_posts/{YYYY-MM-DD}-{slug}.md`), not a token to resolve."""
        import glob
        for src in sorted(glob.glob(os.path.join(REPO, "routines", "src", "*.md"))):
            path = os.path.join(REPO, "routines", os.path.basename(src))
            with open(path, encoding="utf-8") as fh:
                self.assertNotIn("{slug}", fh.read(),
                                 "%s ships an unresolved {slug}" % os.path.basename(path))


if __name__ == "__main__":
    unittest.main()
