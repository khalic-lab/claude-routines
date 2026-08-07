"""Regression tests for the publish tail's push contract -- the two defects that let a
routine lie about whether its edition reached origin.

R1 (2026-07-25 review, the one blocker): `commit_and_push()` pushed the local `main` REF
rather than the commit it had just created. The routine sandbox runs DETACHED with a stale
local `main`, so the push was a no-op on a branch that never described the edition -- exit 0,
`DONE` printed, sandbox gone, brief never published. DetachedHeadPushTest reproduces exactly
that shape: the assertion is on ORIGIN's bare repo, because the local side reported success
in the broken version too.

Patch 2 (evaluator 2026-08-02): the mirror image. 8 of 11 briefs that week carried
"git push failed: this edition has NOT reached origin" while provably sitting on origin/main.
PushVerdictTest pins the verdict to the remote's own answer, and NoteNeverEntersTheBriefTest
pins the deeper half -- the note was amended INTO the commit, so it could only ever be read
after that commit reached origin, which is precisely when it had become false.

Patch 3 (2026-08-07): the SHA-refspec that fixed R1 opened its own silent hole. When the
rebase retry hits a conflict it cannot resolve, `rebase --continue` and the `commit --amend`
fallback both fail on the unmerged index, HEAD is left at the rebase's ONTO commit -- origin's
own tip, another routine's edition -- and `_rev_parse(HEAD)` hands THAT to `push_commit`.
Pushing it is "Everything up-to-date" (exit 0), `remote == sha` matches, and a lost edition
reports `ok` / `DONE` / exit 0. The pre-SHA code failed loudly here (non-fast-forward, exit 1),
so this was loud -> silent. UnmergedRebaseTest pins it.

The push/verify split is isolated with `remote.origin.pushurl`: push uses the pushurl,
while ls-remote and `pull --rebase` keep using the working fetch URL. That lets a test make
the push command fail without also blinding the verification -- the exact real-world state
(push rejected, commit on origin anyway) the false footer came from.
"""
import importlib.util
import os
import shutil
import subprocess
import tempfile
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("_publish_push", os.path.join(TOOLS, "publish.py"))
publish = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publish)


def _git(cwd, *argv):
    return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                           "-c", "commit.gpgsign=false"] + list(argv),
                          cwd=cwd, capture_output=True, text=True)


def _origin_sha(origin):
    return subprocess.run(["git", "--git-dir", origin, "rev-parse", "main"],
                          capture_output=True, text=True).stdout.strip()


def _origin_subject(origin):
    return subprocess.run(["git", "--git-dir", origin, "log", "-1", "--format=%s", "main"],
                          capture_output=True, text=True).stdout.strip()


def _origin_file(origin, path):
    """A file's committed content as ORIGIN holds it -- the only view that matters for a
    note whose whole failure mode is being readable on origin."""
    return subprocess.run(["git", "--git-dir", origin, "show", "main:%s" % path],
                          capture_output=True, text=True).stdout


class PushBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="publish-push-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.origin = os.path.join(self.tmp, "origin.git")
        subprocess.run(["git", "init", "--bare", "-q", "-b", "main", self.origin],
                       check=True, capture_output=True)
        self.work = os.path.join(self.tmp, "work")
        subprocess.run(["git", "clone", "-q", self.origin, self.work],
                       check=True, capture_output=True)
        os.makedirs(os.path.join(self.work, "_posts"))
        self.post = os.path.join(self.work, "_posts", "2026-08-07-news.md")
        self._write_post("Seed.\n")
        _git(self.work, "add", "-A")
        _git(self.work, "commit", "-q", "-m", "seed")
        _git(self.work, "push", "-q", "origin", "main")
        self.seed = _origin_sha(self.origin)

    def _write_post(self, body):
        with open(self.post, "w", encoding="utf-8") as fh:
            fh.write("---\ntitle: News\n---\n\n" + body)

    def _capture(self, fn, *a, **kw):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            out = fn(*a, **kw)
        return out, buf.getvalue()

    def _break_pushes(self):
        """Make the push COMMAND fail while leaving fetch/ls-remote working."""
        _git(self.work, "config", "remote.origin.pushurl",
             os.path.join(self.tmp, "no-such-remote.git"))


class DetachedHeadPushTest(PushBase):
    """R1: the routine sandbox is detached. The commit being published must be what lands."""

    def test_detached_commit_reaches_origin(self):
        """The plain repro. HEAD is detached at the seed, so local `main` == origin/main and
        `git push origin main` is 'Everything up-to-date' -- exit 0, outcome ok, edition lost."""
        _git(self.work, "checkout", "-q", "--detach", "HEAD")
        self._write_post("Edition body.\n")
        outcome, out = self._capture(publish.commit_and_push, self.work, "news",
                                     "News — 2026-08-07", False, False)
        self.assertEqual(outcome, "ok")
        head = _git(self.work, "rev-parse", "HEAD").stdout.strip()
        self.assertNotEqual(head, self.seed, "the edition commit was never created")
        self.assertEqual(_origin_sha(self.origin), head,
                         "origin/main must hold the commit that was just created")
        self.assertEqual(_origin_subject(self.origin), "News — 2026-08-07")
        self.assertIn("verified origin/main == %s" % head[:12], out,
                      "success must be verified against the remote, not just claimed")

    def test_stale_local_main_is_not_what_gets_pushed(self):
        """The sharper repro: local `main` carries an unrelated unpushed commit. Pushing the
        REF publishes that instead of the edition -- origin ends up with the wrong content and
        the run still reports success."""
        self._write_post("Unrelated local work.\n")
        _git(self.work, "add", "-A")
        _git(self.work, "commit", "-q", "-m", "decoy on local main")
        _git(self.work, "checkout", "-q", "--detach", self.seed)
        self._write_post("Edition body.\n")
        outcome, _ = self._capture(publish.commit_and_push, self.work, "news",
                                   "News — 2026-08-07", False, False)
        self.assertEqual(outcome, "ok")
        self.assertEqual(_origin_subject(self.origin), "News — 2026-08-07")
        log = subprocess.run(["git", "--git-dir", self.origin, "log", "--format=%s", "main"],
                             capture_output=True, text=True).stdout
        self.assertNotIn("decoy on local main", log,
                         "only the published edition may travel to origin")
        self.assertIn("Edition body.", _origin_file(self.origin, "_posts/2026-08-07-news.md"))

    def test_detached_run_that_cannot_push_is_not_reported_ok(self):
        """The R1 fix must not be a blanket 'ok': with pushes broken, a detached run still has
        to fail loudly rather than inherit the old no-op success."""
        _git(self.work, "checkout", "-q", "--detach", "HEAD")
        self._write_post("Edition body.\n")
        self._break_pushes()
        outcome, out = self._capture(publish.commit_and_push, self.work, "news",
                                     "News — 2026-08-07", False, False)
        self.assertEqual(outcome, "push-failed")
        self.assertEqual(_origin_sha(self.origin), self.seed)
        self.assertIn("push: FAILED", out)


class PushVerdictTest(PushBase):
    """Patch 2: the verdict is what origin holds, not the exit code of one push attempt."""

    def test_push_command_failure_with_the_commit_already_on_origin_is_ok(self):
        """The false-footer state itself: the edition IS on origin (an earlier retry, a
        concurrent routine, or the bridge's drain-reconcile put it there) while this push
        attempt errors. Reporting failure here is what baked the stale note into 8/11 briefs."""
        self._write_post("Edition body.\n")
        _git(self.work, "add", "-A")
        _git(self.work, "commit", "-q", "-m", "News — 2026-08-07")
        sha = _git(self.work, "rev-parse", "HEAD").stdout.strip()
        _git(self.work, "push", "-q", "origin", "HEAD:refs/heads/main")   # someone else landed it
        self._break_pushes()
        ok, out = self._capture(publish.push_commit, self.work, "news", "git-push", sha, False)
        self.assertTrue(ok, "the commit is on origin/main; that is what 'published' means")
        self.assertIn("verified origin/main == %s" % sha[:12], out)

    def test_push_command_failure_with_the_commit_absent_is_failure(self):
        """The converse must still be honest -- the verification is not a rubber stamp."""
        self._write_post("Edition body.\n")
        _git(self.work, "add", "-A")
        _git(self.work, "commit", "-q", "-m", "News — 2026-08-07")
        sha = _git(self.work, "rev-parse", "HEAD").stdout.strip()
        self._break_pushes()
        ok, out = self._capture(publish.push_commit, self.work, "news", "git-push", sha, False)
        self.assertFalse(ok)
        self.assertIn("push: FAILED", out)
        self.assertIn(self.seed[:12], out, "the log must name what origin actually holds")

    def test_unreadable_remote_is_logged_as_unverified_not_as_verified(self):
        """When ls-remote can't answer, a successful push of THIS sha is still the best
        evidence available -- but the log must say UNVERIFIED, or it re-creates a small R1
        (DONE without proof) in the telemetry the evaluator reads."""
        self._write_post("Edition body.\n")
        _git(self.work, "add", "-A")
        _git(self.work, "commit", "-q", "-m", "News — 2026-08-07")
        sha = _git(self.work, "rev-parse", "HEAD").stdout.strip()
        _git(self.work, "push", "-q", "origin", "HEAD:refs/heads/main")
        self.assertIsNotNone(publish._remote_main(self.work, "news"))
        # break only the FETCH url: the push below is 'up to date' (exit 0), ls-remote dies
        _git(self.work, "config", "remote.origin.pushurl", self.origin)
        _git(self.work, "remote", "set-url", "origin", os.path.join(self.tmp, "gone.git"))
        ok, out = self._capture(publish.push_commit, self.work, "news", "git-push", sha, False)
        self.assertTrue(ok)
        self.assertIn("UNVERIFIED", out)
        self.assertNotIn("verified origin/main ==", out)

    def test_remote_main_reads_the_remote_not_a_stale_tracking_ref(self):
        """`origin/main` in a detached sandbox that never fetched is exactly the stale signal
        this whole fix exists to stop trusting."""
        second = os.path.join(self.tmp, "second")
        subprocess.run(["git", "clone", "-q", self.origin, second], check=True, capture_output=True)
        with open(os.path.join(second, "other.md"), "w") as fh:
            fh.write("elsewhere\n")
        _git(second, "add", "-A")
        _git(second, "commit", "-q", "-m", "another routine's edition")
        _git(second, "push", "-q", "origin", "main")
        advanced = _origin_sha(self.origin)
        self.assertEqual(_git(self.work, "rev-parse", "origin/main").stdout.strip(), self.seed,
                         "the local tracking ref is stale, as in the real sandbox")
        self.assertEqual(publish._remote_main(self.work, "news"), advanced)

    def test_rebase_retry_publishes_the_rebased_commit(self):
        """The retry rewrites HEAD (rebase, then the `commit --amend` fallback). Pushing a SHA
        captured before that would push a commit the retry has already orphaned. Run DETACHED:
        on a checked-out branch the old ref-push happens to coincide with HEAD, so this only
        exercises anything in the state the routines actually run in."""
        _git(self.work, "checkout", "-q", "--detach", "HEAD")
        second = os.path.join(self.tmp, "second")
        subprocess.run(["git", "clone", "-q", self.origin, second], check=True, capture_output=True)
        with open(os.path.join(second, "other.md"), "w") as fh:
            fh.write("elsewhere\n")
        _git(second, "add", "-A")
        _git(second, "commit", "-q", "-m", "another routine's edition")
        _git(second, "push", "-q", "origin", "main")   # our first push is now non-fast-forward
        self._write_post("Edition body.\n")
        outcome, out = self._capture(publish.commit_and_push, self.work, "news",
                                     "News — 2026-08-07", False, False)
        self.assertEqual(outcome, "ok")
        head = _git(self.work, "rev-parse", "HEAD").stdout.strip()
        self.assertEqual(_origin_sha(self.origin), head)
        self.assertIn("Edition body.", _origin_file(self.origin, "_posts/2026-08-07-news.md"))
        self.assertIn("another routine's edition",
                      subprocess.run(["git", "--git-dir", self.origin, "log", "--format=%s", "main"],
                                     capture_output=True, text=True).stdout,
                      "the concurrent edition must survive the rebase, not be overwritten")


class UnmergedRebaseTest(PushBase):
    """Patch 3: a rebase the retry cannot finish must never be reported as published.

    The conflict is on `sources/registry.yml` -- NOT on `index/ledger/*.jsonl`. The repo's
    .gitattributes gives the ledger (and sources/{candidates,last-cited}.jsonl) `merge=union`,
    so concurrent appends there auto-merge and a ledger-based repro is vacuously green. The
    real trigger is registry.yml: rewritten by publish.py's `registry-sync` step on every writer
    run as a pure EOF append of new domain blocks, not union-merged, and not regenerated or
    staged by the retry (which rebuilds `_data/` only). Two writers firing the same day is all
    it takes -- 2026-07-31 news+ai-ml and 2026-07-29 news+science both landed on it.

    The fixture copies the repo's real .gitattributes as DOCUMENTATION, not mechanism: the
    conflict happens with or without it, and it is there so a later reader who "simplifies"
    this onto a ledger file sees immediately why that test would stop failing."""

    REGISTRY = "sources/registry.yml"
    ENTRY = ("%s:\n"
             "  class: outlet\n"
             "  tier: T2\n"
             "  status: candidate\n"
             "  reach: direct\n"
             "  streams:\n"
             "    - %s\n"
             "  last_cited: 2026-08-07\n"
             "  lifecycle:\n"
             "    - date: 2026-08-07\n"
             "      event: candidate\n"
             "      status: candidate\n")

    def setUp(self):
        super().setUp()
        # `sources/` must exist on disk: commit_and_push only `git add`s the directories that
        # do, so without it the conflicting file would never enter the edition commit at all.
        os.makedirs(os.path.join(self.work, "sources"))
        with open(os.path.join(self.work, self.REGISTRY), "w", encoding="utf-8") as fh:
            fh.write(self.ENTRY % ("acoup.blog", "weekend"))
        shutil.copy2(os.path.join(os.path.dirname(TOOLS), ".gitattributes"),
                     os.path.join(self.work, ".gitattributes"))
        _git(self.work, "add", "-A")
        _git(self.work, "commit", "-q", "-m", "seed registry")
        _git(self.work, "push", "-q", "origin", "main")
        self.seed = _origin_sha(self.origin)

    def _other_routine_appends(self):
        """A concurrent writer lands its own registry-sync append on origin first."""
        second = os.path.join(self.tmp, "second")
        subprocess.run(["git", "clone", "-q", self.origin, second], check=True, capture_output=True)
        with open(os.path.join(second, self.REGISTRY), "a", encoding="utf-8") as fh:
            fh.write(self.ENTRY % ("fcc.gov", "ai-ml"))
        _git(second, "add", "-A")
        _git(second, "commit", "-q", "-m", "AI/ML — 2026-08-07")
        _git(second, "push", "-q", "origin", "main")

    def test_unresolvable_rebase_conflict_is_not_reported_published(self):
        """Both writers append at EOF from the same base, so `pull --rebase` conflicts on
        registry.yml. The retry rebuilds `_data/` only, so the conflict survives it: HEAD stays
        at the OTHER routine's commit and pushing it is a no-op that verifies as success."""
        _git(self.work, "checkout", "-q", "--detach", "HEAD")
        self._other_routine_appends()
        with open(os.path.join(self.work, self.REGISTRY), "a", encoding="utf-8") as fh:
            fh.write(self.ENTRY % ("newsdesk.example", "news"))
        self._write_post("Edition body.\n")
        outcome, out = self._capture(publish.commit_and_push, self.work, "news",
                                     "News — 2026-08-07", False, False)
        self.assertEqual(outcome, "push-failed",
                         "a rebase that never completed has published nothing")
        self.assertIn("rebase left unmerged paths", out,
                      "the operator must be told WHY, or this reads as an ordinary push failure")
        # The state the guard exists for, asserted directly: an unmerged index, and a HEAD
        # that is origin's own tip rather than any commit of ours.
        self.assertTrue(_git(self.work, "ls-files", "-u").stdout.strip(),
                        "fixture check: the rebase must actually have left a conflict")
        self.assertEqual(_git(self.work, "rev-parse", "HEAD").stdout.strip(),
                         _origin_sha(self.origin))
        # ORIGIN's side: the edition is absent and the concurrent routine's commit is untouched.
        self.assertEqual(_origin_subject(self.origin), "AI/ML — 2026-08-07")
        self.assertNotIn("Edition body.",
                         _origin_file(self.origin, "_posts/2026-08-07-news.md"),
                         "the edition never reached origin; nothing may report otherwise")

    def test_conflict_free_concurrent_append_still_publishes(self):
        """The guard must not turn every rebase into a failure: when the concurrent commit
        touches a different file, the retry resolves it and the edition publishes as before."""
        _git(self.work, "checkout", "-q", "--detach", "HEAD")
        second = os.path.join(self.tmp, "second")
        subprocess.run(["git", "clone", "-q", self.origin, second], check=True, capture_output=True)
        with open(os.path.join(second, "other.md"), "w", encoding="utf-8") as fh:
            fh.write("elsewhere\n")
        _git(second, "add", "-A")
        _git(second, "commit", "-q", "-m", "another routine's edition")
        _git(second, "push", "-q", "origin", "main")
        with open(os.path.join(self.work, self.REGISTRY), "a", encoding="utf-8") as fh:
            fh.write(self.ENTRY % ("newsdesk.example", "news"))
        self._write_post("Edition body.\n")
        outcome, out = self._capture(publish.commit_and_push, self.work, "news",
                                     "News — 2026-08-07", False, False)
        self.assertEqual(outcome, "ok")
        self.assertNotIn("rebase left unmerged paths", out)
        self.assertEqual(_origin_sha(self.origin),
                         _git(self.work, "rev-parse", "HEAD").stdout.strip())
        self.assertIn("Edition body.", _origin_file(self.origin, "_posts/2026-08-07-news.md"))
        self.assertIn("newsdesk.example", _origin_file(self.origin, self.REGISTRY))


class NoteNeverEntersTheBriefTest(PushBase):
    """The self-falsifying artifact, asserted from origin's side.

    The note was amended into the commit so it would 'survive the sandbox'. It does -- and the
    only way anyone ever reads it is on origin, i.e. after the push it denies has succeeded.
    22 briefs in the archive carry it; every one of them is on origin/main."""

    def _publish(self, extra=()):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = publish.main(["--slug", "news", "--date", "2026-08-07", "--root", self.work,
                               "--notify-body", "teaser"] + list(extra))
        return rc, buf.getvalue()

    def test_failed_push_leaves_the_brief_and_its_commit_clean(self):
        self._write_post("Edition body.\n")
        self._break_pushes()
        rc, out = self._publish()
        self.assertEqual(rc, 1, "a genuinely failed push must still be fatal")
        self.assertIn("FAILED (push", out)
        with open(self.post, encoding="utf-8") as fh:
            self.assertNotIn("git push failed", fh.read())
        show = _git(self.work, "show", "--format=", "HEAD").stdout
        self.assertNotIn("has NOT reached origin", show)

    def test_a_commit_that_later_reaches_origin_carries_no_false_note(self):
        """The acceptance case for Patch 2, end to end: push fails, the run reports failure,
        and the bridge's later drain-reconcile pushes the same commit. What lands on origin
        must not claim it never got there."""
        self._write_post("Edition body.\n")
        self._break_pushes()
        rc, _ = self._publish()
        self.assertEqual(rc, 1)
        head = _git(self.work, "rev-parse", "HEAD").stdout.strip()
        _git(self.work, "config", "--unset", "remote.origin.pushurl")   # the bridge reconciles
        _git(self.work, "push", "-q", "origin", "HEAD:refs/heads/main")
        self.assertEqual(_origin_sha(self.origin), head)
        published = _origin_file(self.origin, "_posts/2026-08-07-news.md")
        self.assertIn("Edition body.", published)
        self.assertNotIn("git push failed", published,
                         "origin holds the edition; nothing in it may say otherwise")

    def test_successful_push_leaves_no_note_either(self):
        self._write_post("Edition body.\n")
        rc, out = self._publish()
        self.assertEqual(rc, 0)
        self.assertIn("DONE", out)
        self.assertNotIn("git push failed", _origin_file(self.origin, "_posts/2026-08-07-news.md"))


if __name__ == "__main__":
    unittest.main()
