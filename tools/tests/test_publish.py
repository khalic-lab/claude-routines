"""Spec tests for tools/publish.py -- the publish-tail orchestrator.

Contract under test: the fixed step order (record -> anchor -> footer -> lint ->
registry/institutions sync -> date lint -> feed -> health -> stub -> git), real
JSON encoding in the notification stub (no hand-escaped quotes), bare front-matter
date normalization, and the record-skip path when dedup was unavailable.
RealGitTest exercises the git tail against real local repos: a failed commit or
push must surface as 'commit-failed'/'push-failed' (never a silent DONE), and a
failed push must leave the brief's body untouched. The refspec/origin-verification
half of that tail lives in test_publish_push.py.
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("_publish", os.path.join(TOOLS, "publish.py"))
publish = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publish)

# Dates are relative to the clock, never hardcoded: publish.py refuses to write a FUTURE
# front-matter date (Jekyll's `future: false` would drop the post from the build), so a fixed
# literal would exercise a different branch depending on the day the suite runs.
import datetime as _dt
_NOW = publish.zurich_now()
TODAY = _NOW.date().isoformat()
YESTERDAY = (_NOW.date() - _dt.timedelta(days=1)).isoformat()
TOMORROW = (_NOW.date() + _dt.timedelta(days=1)).isoformat()
# A brief is generated shortly BEFORE it is published, so its stamp is always slightly in the
# past. Fabricating a fixed hour instead would collide with the future-date clamp whenever the
# suite runs before that hour -- a real flake this file already tripped over once.
_GEN = _NOW - _dt.timedelta(minutes=5)
GEN_CLOCK = publish._iso_offset(_GEN.strftime("%H:%M:%S%z"))       # "01:51:16+02:00"
GEN_CLOCK_NOCOLON = _GEN.strftime("%H:%M:%S%z")                    # "01:51:16+0200"
GEN_STAMP = "%sT%s" % (TODAY, GEN_CLOCK)


class PublishTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="publish-test-")
        os.makedirs(os.path.join(self.root, "_posts"))
        self.post = os.path.join(self.root, "_posts", "2026-07-18-news.md")
        with open(self.post, "w") as fh:
            fh.write("---\nlayout: single\ntitle: \"News\"\ndate: 2026-07-18\n"
                     "categories: [news]\n---\n\nBody.\n\n## Coverage footer\n- Gaps: none.\n")

    def _capture(self, argv):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = publish.main(argv)
        return rc, buf.getvalue()

    def test_dry_run_step_order(self):
        rc, out = self._capture([
            "--slug", "news", "--date", "2026-07-18", "--root", self.root,
            "--final", "/tmp/final.json", "--notify-title", "News — 2026-07-18",
            "--notify-body", "teaser", "--dry-run"])
        self.assertEqual(rc, 0)
        order = [name for name in ("record", "anchor", "footer", "source-lint",
                                   "registry-sync", "institutions-sync", "date-lint",
                                   "feed", "source-health", "plane-push", "stub",
                                   "git-add", "git-commit", "git-push")
                 if ("DRY-RUN %s" % name) in out or ("DRY-RUN %s:" % name) in out]
        self.assertEqual(order, ["record", "anchor", "footer", "source-lint",
                                 "registry-sync", "institutions-sync", "date-lint",
                                 "feed", "source-health", "plane-push", "stub",
                                 "git-add", "git-commit", "git-push"])

    def test_record_skipped_without_final(self):
        rc, out = self._capture(["--slug", "news", "--date", "2026-07-18",
                                 "--root", self.root, "--dry-run"])
        self.assertEqual(rc, 0)
        self.assertIn("record: skipped", out)
        self.assertNotIn("DRY-RUN record", out)

    def test_front_matter_bare_date_normalized_once(self):
        publish.normalize_front_matter(self.post, dry_run=False)
        with open(self.post) as fh:
            text = fh.read()
        m = re.search(r"^date: (2026-07-18T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2})$", text, re.M)
        self.assertIsNotNone(m, "bare date must become a full ISO timestamp with offset")
        publish.normalize_front_matter(self.post, dry_run=False)  # idempotent
        with open(self.post) as fh:
            self.assertEqual(fh.read(), text)

    def test_stub_json_is_really_encoded(self):
        publish.write_stub(self.root, "news", "2026-07-18",
                           'He said "hi" — ok', 'Line with "quotes" and — dashes',
                           "newspaper", dry_run=False)
        stub_dir = os.path.join(self.root, "pending-notifications")
        (name,) = os.listdir(stub_dir)
        self.assertRegex(name, r"^\d{8}T\d{6}Z-news\.json$")
        with open(os.path.join(stub_dir, name)) as fh:
            stub = json.load(fh)  # must be valid JSON despite the quotes
        self.assertEqual(stub["title"], 'He said "hi" — ok')
        # Brief pages are retired (2026-07-18): every brief notification clicks
        # through to the homepage story feed, never a per-edition page.
        self.assertEqual(stub["click"], "https://khalic-lab.github.io/claude-routines/")
        self.assertEqual(stub["tags"], "newspaper")

    def test_missing_post_is_fatal(self):
        rc, out = self._capture(["--slug", "sports", "--date", "2026-07-18",
                                 "--root", self.root])
        self.assertEqual(rc, 2)
        self.assertIn("FATAL", out)

    def test_edition_names_cover_every_slug(self):
        self.assertEqual(set(publish.EDITION_NAME) | {"evaluator"},
                         set(publish.SLUGS) | {"evaluator"})
        self.assertEqual(publish.EDITION_NAME["weekend"], "Weekend Deep Read")


class FrontMatterDerivationTest(unittest.TestCase):
    """The prompts no longer carry a front-matter block: a routine writes the brief BODY and
    publish.py derives the block. What it derives has to be exactly what the prompts used to
    dictate -- including the date agreeing with the brief's own _Generated line."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="publish-fm-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        os.makedirs(os.path.join(self.root, "_posts"))

    def _post(self, slug, date, body):
        path = os.path.join(self.root, "_posts", "%s-%s.md" % (date, slug))
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(body)
        return path

    def _fm(self, path):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        self.assertTrue(text.startswith("---\n"), "post must open with front matter")
        return text.split("---\n")[1], text

    def test_body_only_post_gets_the_block_prompts_used_to_dictate(self):
        path = self._post("news", TODAY,
                          "# News — %s\n\n"
                          "_Generated %s Europe/Zurich. Coverage: last ~24h._\n\n"
                          "## 🇨🇭 Switzerland & Vaud\n- story\n" % (TODAY, GEN_STAMP))
        publish.ensure_front_matter(path, "news", TODAY, dry_run=False)
        fm, text = self._fm(path)
        self.assertIn("layout: single", fm)
        self.assertIn('title: "News — %s"' % TODAY, fm)
        self.assertIn("categories: [news]", fm)
        self.assertIn("date: %s" % GEN_STAMP, fm,
                      "the date must come from the brief's own _Generated stamp")
        self.assertNotIn("published:", fm, "briefs stay unpublished; only the review renders")
        self.assertIn("# News — %s" % TODAY, text, "the body must survive intact")

    def test_generated_stamp_without_colon_in_offset_is_normalized(self):
        path = self._post("sports", TODAY,
                          "_Generated %sT%s Europe/Zurich._\n\nBody.\n" % (TODAY, GEN_CLOCK_NOCOLON))
        publish.ensure_front_matter(path, "sports", TODAY, dry_run=False)
        fm, _ = self._fm(path)
        self.assertIn("date: %s" % GEN_STAMP, fm)

    def test_no_generated_line_falls_back_to_the_edition_date_plus_now(self):
        path = self._post("science", TODAY, "Body with no generated line.\n")
        publish.ensure_front_matter(path, "science", TODAY, dry_run=False)
        fm, _ = self._fm(path)
        self.assertRegex(fm, r"date: %sT\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}" % TODAY)

    def test_date_part_is_always_the_edition_date(self):
        """Jekyll builds the permalink from the front-matter date; the notification stub links
        using --date. A run that crossed midnight (the _Generated stamp landing on the NEXT day)
        must not publish at a URL its own notification 404s on."""
        path = self._post("evaluator", YESTERDAY,
                          "_Generated %sT00:04:00+02:00 Europe/Zurich._\n\nBody.\n" % TODAY)
        day = publish.ensure_front_matter(path, "evaluator", YESTERDAY, dry_run=False)
        fm, _ = self._fm(path)
        self.assertIn("date: %sT00:04:00+02:00" % YESTERDAY, fm)
        self.assertEqual(day, YESTERDAY, "the returned day is what the stub must link")

    def test_future_edition_date_is_clamped_not_shipped(self):
        """Jekyll's `future` defaults to false and _config.yml does not override it, so a
        front-matter date ahead of the build clock drops the post from the site entirely --
        silently, and for the evaluator that is the one page the notification links to."""
        path = self._post("evaluator", TOMORROW, "Review body, no generated line.\n")
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            day = publish.ensure_front_matter(path, "evaluator", TOMORROW, dry_run=False)
        fm, _ = self._fm(path)
        self.assertEqual(day, TODAY, "must fall back to today, not the future date")
        self.assertIn("date: %sT" % TODAY, fm)
        self.assertIn("WARNING", buf.getvalue(), "the clamp must be loud, not silent")

    def test_evaluator_body_gets_published_true(self):
        path = self._post("evaluator", TODAY, "# Weekly Brief Pipeline Review\n")
        publish.ensure_front_matter(path, "evaluator", TODAY, dry_run=False)
        fm, _ = self._fm(path)
        self.assertIn("published: true", fm)
        self.assertIn('title: "Weekly Pipeline Review — %s"' % TODAY, fm)

    def test_evaluator_front_matter_missing_published_is_repaired(self):
        """_config.yml unpublishes posts by default -- a review without this line is a page
        that silently never renders, which is why the prompt used to shout about it."""
        path = self._post("evaluator", TODAY,
                          '---\nlayout: single\ntitle: "Weekly Pipeline Review"\n'
                          "date: %sT11:00:00+02:00\ncategories: [evaluator]\n---\n\nBody.\n" % TODAY)
        publish.ensure_front_matter(path, "evaluator", TODAY, dry_run=False)
        fm, text = self._fm(path)
        self.assertIn("published: true", fm)
        self.assertEqual(text.count("---\n"), 2, "must not add a second front-matter block")
        self.assertEqual(text.count("published: true"), 1)

    def test_leading_blank_line_still_inserts_INSIDE_the_block(self):
        """A body that starts with a newline used to send `published: true` above the opening
        `---` -- outside the block, so _config.yml's default un-published the one page that must
        render, while the log claimed success."""
        path = self._post("evaluator", TODAY,
                          '\n---\nlayout: single\ntitle: "Weekly Pipeline Review"\n'
                          "date: %sT11:00:00+02:00\ncategories: [evaluator]\n---\n\nBody.\n" % TODAY)
        publish.ensure_front_matter(path, "evaluator", TODAY, dry_run=False)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        block = publish.FRONT_MATTER_RE.match(text)
        self.assertIsNotNone(block, "front matter must still parse")
        self.assertIn("published: true", block.group("fm"),
                      "the line must be INSIDE the block, not floating above it")

    def test_published_detected_beyond_600_chars(self):
        """Detection used to scan only text[:600]; a long title pushed `published:` past it and
        earned the review a duplicate YAML key."""
        pad = "x" * 700
        path = self._post("evaluator", TODAY,
                          '---\nlayout: single\ntitle: "%s"\ncategories: [evaluator]\n'
                          "published: true\n---\n\nBody.\n" % pad)
        publish.ensure_front_matter(path, "evaluator", TODAY, dry_run=False)
        with open(path, encoding="utf-8") as fh:
            self.assertEqual(fh.read().count("published: true"), 1)

    def test_body_published_line_does_not_block_the_repair(self):
        """The reverse miss: a `published:`-looking line early in the BODY used to be read as
        front matter and skip the repair."""
        path = self._post("evaluator", TODAY,
                          "---\nlayout: single\ncategories: [evaluator]\n---\n\n"
                          "published: false was mentioned in a story about a journal.\n")
        publish.ensure_front_matter(path, "evaluator", TODAY, dry_run=False)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("published: true", publish.FRONT_MATTER_RE.match(text).group("fm"))

    def test_unterminated_front_matter_is_left_alone(self):
        original = "---\nlayout: single\ncategories: [evaluator]\n\nBody, no closing fence.\n"
        path = self._post("evaluator", TODAY, original)
        publish.ensure_front_matter(path, "evaluator", TODAY, dry_run=False)
        with open(path, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), original)

    def test_timestamp_comes_from_the_generated_line_not_any_story_date(self):
        """Unanchored, the regex took the first ISO stamp in the first 1500 chars -- which can be
        a timestamp inside a story, not the brief's own machine stamp."""
        path = self._post("news", TODAY,
                          "# News — %s\n\n_Generated %s Europe/Zurich._\n\n"
                          "- **A story** quoting an outage at %sT03:15:00+01:00.\n"
                          % (TODAY, GEN_STAMP, TODAY))
        publish.ensure_front_matter(path, "news", TODAY, dry_run=False)
        fm, _ = self._fm(path)
        self.assertIn("date: %s" % GEN_STAMP, fm)
        self.assertNotIn("03:15:00", fm)

    def test_weekend_coverage_line_format_is_recognized(self):
        """Weekend's stamp sits mid-sentence: '_Coverage: … to …. Generated <ts> Europe/Zurich._'"""
        path = self._post("weekend", TODAY,
                          "# Weekend Deep Read — %s\n\n_Coverage: %s to %s. "
                          "Generated %s Europe/Zurich._\n\nBody.\n"
                          % (TODAY, YESTERDAY, TODAY, GEN_STAMP))
        publish.ensure_front_matter(path, "weekend", TODAY, dry_run=False)
        fm, _ = self._fm(path)
        self.assertIn("date: %s" % GEN_STAMP, fm)

    def test_existing_front_matter_is_left_alone(self):
        original = ('---\nlayout: single\ntitle: "News — mine"\ndate: %sT08:00:00+02:00\n'
                    "categories: [news]\n---\n\nBody.\n" % TODAY)
        path = self._post("news", TODAY, original)
        publish.ensure_front_matter(path, "news", TODAY, dry_run=False)
        with open(path, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), original)

    def test_idempotent(self):
        path = self._post("news", TODAY,
                          "_Generated %s Europe/Zurich._\n\nBody.\n" % GEN_STAMP)
        publish.ensure_front_matter(path, "news", TODAY, dry_run=False)
        with open(path, encoding="utf-8") as fh:
            once = fh.read()
        publish.ensure_front_matter(path, "news", TODAY, dry_run=False)
        with open(path, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), once)


class NotifyDefaultsTest(unittest.TestCase):
    """Title and tag follow from (slug, date); the teaser is the only judgment call left."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="publish-notify-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        os.makedirs(os.path.join(self.root, "_posts"))
        subprocess.run(["git", "init", "-q", "-b", "main", self.root],
                       check=True, capture_output=True)

    def test_edition_title_matches_every_slug(self):
        self.assertEqual(publish.edition_title("news", TODAY), "News — %s" % TODAY)
        self.assertEqual(publish.edition_title("weekend", TODAY),
                         "Weekend Deep Read — %s" % TODAY)
        self.assertEqual(publish.edition_title("evaluator", TODAY),
                         "Weekly Pipeline Review — %s" % TODAY)

    def test_every_slug_has_a_tag(self):
        self.assertEqual(set(publish.NOTIFY_TAGS), set(publish.SLUGS))

    def test_stub_defaults_title_and_tag_from_the_slug(self):
        with open(os.path.join(self.root, "_posts", "%s-ai-ml.md" % TODAY), "w") as fh:
            fh.write("_Generated %s Europe/Zurich._\n\nBody.\n" % GEN_STAMP)
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = publish.main(["--slug", "ai-ml", "--date", TODAY, "--root", self.root,
                               "--notify-body", "teaser only", "--no-push"])
        self.assertEqual(rc, 0)
        (name,) = os.listdir(os.path.join(self.root, "pending-notifications"))
        with open(os.path.join(self.root, "pending-notifications", name)) as fh:
            stub = json.load(fh)
        self.assertEqual(stub["title"], "AI/ML — %s" % TODAY)
        self.assertEqual(stub["tags"], "robot_face")
        self.assertEqual(stub["body"], "teaser only")


class StubFollowsFrontMatterTest(unittest.TestCase):
    """The permalink contract, end to end through main().

    Jekyll builds a post's URL from its front-matter date; the notification links to that URL.
    Deriving the two from different sources is how they drift: the review would publish at one
    path while the phone notification points at another, and both halves report success. So the
    stub must follow the front matter that was actually written -- including when the clamp
    rewrote it."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="publish-stubdate-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        os.makedirs(os.path.join(self.root, "_posts"))
        subprocess.run(["git", "init", "-q", "-b", "main", self.root],
                       check=True, capture_output=True)

    def _run(self, date, body):
        with open(os.path.join(self.root, "_posts", "%s-evaluator.md" % date), "w") as fh:
            fh.write(body)
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = publish.main(["--slug", "evaluator", "--date", date, "--root", self.root,
                               "--notify-body", "teaser", "--no-push"])
        (name,) = os.listdir(os.path.join(self.root, "pending-notifications"))
        with open(os.path.join(self.root, "pending-notifications", name)) as fh:
            return rc, json.load(fh), buf.getvalue()

    def _fm_date(self, date):
        with open(os.path.join(self.root, "_posts", "%s-evaluator.md" % date)) as fh:
            fm = publish.FRONT_MATTER_RE.match(fh.read()).group("fm")
        return re.search(r"^date: (\S+)", fm, re.M).group(1)

    def test_click_matches_the_front_matter_date(self):
        rc, stub, _ = self._run(TODAY, "# Review\n\nBody.\n")
        self.assertEqual(rc, 0)
        fm_day = self._fm_date(TODAY).split("T")[0]
        self.assertIn("/%s/evaluator/" % fm_day.replace("-", "/"), stub["click"],
                      "the notification must link the page Jekyll will actually build")

    def test_clamped_date_moves_the_click_too(self):
        """--date ahead of the clock is clamped (a future post is dropped from the build). The
        stub must follow the clamp, not the argument -- otherwise the fix for one 404 creates
        another."""
        rc, stub, out = self._run(TOMORROW, "# Review\n\nBody.\n")
        self.assertEqual(rc, 0)
        self.assertIn("WARNING", out)
        fm_day = self._fm_date(TOMORROW).split("T")[0]
        self.assertEqual(fm_day, TODAY, "the front matter should have been clamped to today")
        self.assertIn("/%s/evaluator/" % TODAY.replace("-", "/"), stub["click"])
        self.assertNotIn(TOMORROW.replace("-", "/"), stub["click"],
                         "the click still points at the clamped-away future date")

    def test_hand_written_front_matter_date_wins_over_the_argument(self):
        """A routine that wrote its own front matter (or the manual fallback path) sets the
        permalink; --date must not override where the notification points."""
        rc, stub, _ = self._run(
            TODAY,
            '---\nlayout: single\ntitle: "Weekly Pipeline Review"\ndate: %sT10:00:00+02:00\n'
            "categories: [evaluator]\npublished: true\n---\n\nBody.\n" % YESTERDAY)
        self.assertEqual(rc, 0)
        self.assertIn("/%s/evaluator/" % YESTERDAY.replace("-", "/"), stub["click"])


class EvaluatorSlugTest(unittest.TestCase):
    """`--slug evaluator`: the review's publish tail. It records no stories, so every
    writer preprocessing step must be skipped -- but the stub and the honest git tail
    (the two things its hand-rolled prompt block used to do by hand) must still run."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="publish-eval-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        os.makedirs(os.path.join(self.root, "_posts"))
        with open(os.path.join(self.root, "_posts", "%s-evaluator.md" % TODAY), "w") as fh:
            fh.write("---\ntitle: Review\ndate: %s\npublished: true\n---\n\nBody.\n" % TODAY)

    def _capture(self, argv):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = publish.main(argv)
        return rc, buf.getvalue()

    def test_preprocessing_skipped_but_stub_and_git_still_run(self):
        rc, out = self._capture([
            "--slug", "evaluator", "--date", TODAY, "--root", self.root,
            "--notify-title", "Weekly Pipeline Review — %s" % TODAY,
            "--notify-body", "2 streams lag discovery", "--dry-run"])
        self.assertEqual(rc, 0)
        self.assertIn("preprocessing: skipped", out)
        for step in ("record", "verdicts", "anchor", "footer", "source-lint",
                     "registry-sync", "institutions-sync", "date-lint", "feed",
                     "source-health", "plane-push"):
            self.assertNotIn("DRY-RUN %s" % step, out,
                             "%s is writer-only; the evaluator records no stories" % step)
        for step in ("stub", "git-add", "git-commit", "git-push"):
            self.assertIn("DRY-RUN %s" % step, out)

    def test_commit_message_and_identity(self):
        self.assertEqual(publish.EDITION_NAME["evaluator"], "Weekly Pipeline Review")
        # the identity the hand-rolled tail used, kept so the history stays uniform
        self.assertEqual(publish.GIT_NAME["evaluator"], "News Routine")

    def test_stub_clicks_the_review_page_not_the_homepage(self):
        """The evaluator review is the one post still rendered as its own page
        (_config.yml unpublishes the rest), so its notification links there."""
        publish.write_stub(self.root, "evaluator", TODAY, "Weekly Pipeline Review",
                           "teaser", "memo", dry_run=False)
        (name,) = os.listdir(os.path.join(self.root, "pending-notifications"))
        self.assertRegex(name, r"^\d{8}T\d{6}Z-evaluator\.json$")
        with open(os.path.join(self.root, "pending-notifications", name)) as fh:
            stub = json.load(fh)
        self.assertEqual(stub["click"],
                         "https://khalic-lab.github.io/claude-routines/%s/evaluator/"
                         % TODAY.replace("-", "/"))
        self.assertEqual(stub["tags"], "memo")


class VerdictSnapshotStepTest(unittest.TestCase):
    """The Step-A verdict snapshot moved out of the writer's prompt into the tail:
    it runs when the check's two files are still on disk, and skips quietly otherwise."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="publish-verdicts-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        os.makedirs(os.path.join(self.root, "_posts"))
        with open(os.path.join(self.root, "_posts", "%s-news.md" % TODAY), "w") as fh:
            fh.write("---\ntitle: News\ndate: %s\n---\n\nBody.\n" % TODAY)
        self.cand = os.path.join(self.root, "cand.json")
        self.verdicts = os.path.join(self.root, "verdicts.json")

    def _capture(self, argv):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = publish.main(argv)
        return rc, buf.getvalue()

    def _run(self):
        return self._capture(["--slug", "news", "--date", TODAY, "--root", self.root,
                              "--candidates", self.cand, "--verdicts", self.verdicts,
                              "--dry-run"])

    def test_runs_after_record_when_both_files_exist(self):
        for path in (self.cand, self.verdicts):
            with open(path, "w") as fh:
                fh.write("{}")
        rc, out = self._run()
        self.assertEqual(rc, 0)
        self.assertIn("DRY-RUN verdicts", out)
        self.assertLess(out.index("DRY-RUN verdicts"), out.index("DRY-RUN anchor"))

    def test_skips_when_the_check_never_ran(self):
        rc, out = self._run()
        self.assertEqual(rc, 0)
        self.assertIn("verdicts: skipped", out)
        self.assertNotIn("DRY-RUN verdicts", out)


def _git(cwd, *argv):
    return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                           "-c", "commit.gpgsign=false"] + list(argv),
                          cwd=cwd, capture_output=True, text=True)


class RealGitTest(unittest.TestCase):
    """The git tail against real repos -- the paths dry-run can't see."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="publish-git-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.origin = os.path.join(self.tmp, "origin.git")
        subprocess.run(["git", "init", "--bare", "-q", "-b", "main", self.origin],
                       check=True, capture_output=True)
        self.work = os.path.join(self.tmp, "work")
        subprocess.run(["git", "clone", "-q", self.origin, self.work],
                       check=True, capture_output=True)
        os.makedirs(os.path.join(self.work, "_posts"))
        self.post = os.path.join(self.work, "_posts", "2026-07-18-news.md")
        self._write_post("Body.\n")
        # seed origin/main so later pushes aren't the branch-creating first push
        _git(self.work, "add", "-A")
        _git(self.work, "commit", "-q", "-m", "seed")
        _git(self.work, "push", "-q", "origin", "main")

    def _write_post(self, body):
        with open(self.post, "w") as fh:
            fh.write("---\ntitle: News\n---\n\n" + body)

    def _capture(self, fn, *a, **kw):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            out = fn(*a, **kw)
        return out, buf.getvalue()

    def test_happy_path_lands_on_origin(self):
        self._write_post("Edition body.\n")
        outcome, _ = self._capture(publish.commit_and_push, self.work, "news",
                                   "News — test", False, False)
        self.assertEqual(outcome, "ok")
        log = subprocess.run(["git", "--git-dir", self.origin, "log", "-1",
                              "--format=%s", "main"], capture_output=True, text=True)
        self.assertEqual(log.stdout.strip(), "News — test")

    def test_failed_commit_is_never_reported_ok(self):
        """The false-DONE shape: commit fails, push of the unchanged branch would
        succeed as a no-op -- commit_and_push must say commit-failed, not ok."""
        self._write_post("Edition body.\n")
        hook = os.path.join(self.work, ".git", "hooks", "pre-commit")
        with open(hook, "w") as fh:
            fh.write("#!/bin/sh\nexit 1\n")
        os.chmod(hook, 0o755)
        outcome, out = self._capture(publish.commit_and_push, self.work, "news",
                                     "News — test", False, False)
        self.assertEqual(outcome, "commit-failed")
        self.assertIn("git-commit: FAIL", out)

    def test_nothing_staged_still_pushes_prior_commit(self):
        """Second run after a push failure: nothing new to commit, but the earlier
        commit still needs pushing -- must be ok, not a commit error."""
        self._write_post("Edition body.\n")
        _git(self.work, "add", "-A")
        _git(self.work, "commit", "-q", "-m", "unpushed edition")
        outcome, out = self._capture(publish.commit_and_push, self.work, "news",
                                     "News — test", False, False)
        self.assertEqual(outcome, "ok")
        self.assertIn("nothing newly staged", out)
        log = subprocess.run(["git", "--git-dir", self.origin, "log", "-1",
                              "--format=%s", "main"], capture_output=True, text=True)
        self.assertEqual(log.stdout.strip(), "unpushed edition")

    def test_evaluator_run_stages_its_reader_profile_edit(self):
        """The evaluator's bounded auto-apply appends a dated line to reader-profile.md.
        The file sits at the repo root, under none of the staged directories -- unstaged,
        the edit dies with the sandbox while that run's proposal already claims
        applied:true, so the writers never receive a preference the loop recorded."""
        self._write_post("Review body.\n")
        profile = os.path.join(self.work, "reader-profile.md")
        with open(profile, "w") as fh:
            fh.write("# Reader profile\n\n## Learned preferences\n")
        _git(self.work, "add", "reader-profile.md")
        _git(self.work, "commit", "-q", "-m", "seed profile")
        with open(profile, "a") as fh:
            fh.write("- %s: less SpaceX launch detail (3x down, \"too long\").\n" % TODAY)
        outcome, _ = self._capture(publish.commit_and_push, self.work, "evaluator",
                                   "Weekly Pipeline Review — test", False, False)
        self.assertEqual(outcome, "ok")
        show = _git(self.work, "show", "--stat", "--format=", "HEAD")
        self.assertIn("reader-profile.md", show.stdout,
                      "the evaluator's granted edit must travel with its commit")

    def test_writer_run_does_not_stage_reader_profile(self):
        """Writers only READ the profile -- a writer run must never commit a change to it."""
        self._write_post("Edition body.\n")
        profile = os.path.join(self.work, "reader-profile.md")
        with open(profile, "w") as fh:
            fh.write("# Reader profile\n")
        _git(self.work, "add", "reader-profile.md")
        _git(self.work, "commit", "-q", "-m", "seed profile")
        with open(profile, "a") as fh:
            fh.write("- stray edit a writer should never publish\n")
        outcome, _ = self._capture(publish.commit_and_push, self.work, "news",
                                   "News — test", False, False)
        self.assertEqual(outcome, "ok")
        show = _git(self.work, "show", "--stat", "--format=", "HEAD")
        self.assertNotIn("reader-profile.md", show.stdout)

    def test_push_failure_reported_without_writing_into_the_brief(self):
        """A failed push is reported to the operator (push-failed + a loud line), and the
        brief's body is left exactly as written. The note this used to amend into the commit
        was readable only once that commit reached origin -- i.e. only once it was false."""
        self._write_post("Edition body.\n")
        _git(self.work, "remote", "set-url", "origin",
             os.path.join(self.tmp, "no-such-remote.git"))
        outcome, _ = self._capture(publish.commit_and_push, self.work, "news",
                                   "News — test", False, False)
        self.assertEqual(outcome, "push-failed")
        with open(self.post) as fh:
            self.assertNotIn("git push failed", fh.read())
        show = _git(self.work, "show", "--format=", "HEAD", "--", "_posts/2026-07-18-news.md")
        self.assertNotIn("git push failed", show.stdout,
                         "the commit must never carry a note that a later push falsifies")


if __name__ == "__main__":
    unittest.main()
