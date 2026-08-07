#!/usr/bin/env python3
"""Publish-tail orchestrator -- the deterministic end of every writer run.

One command replaces the ~10 prompt-prose steps a writer routine used to replay by
hand (DEDUP.md Steps C..E + its own Output section): record -> anchor -> computed
footer telemetry -> source lint -> registry/institutions sync -> date lint -> feed
+ stats rebuild -> source health -> notification stub -> git add/commit/push with
the rebase-conflict feed regeneration. A step can no longer be skipped, misordered,
or typo'd -- the historical failure class this tool exists to close (registry.py
sync went uninvoked 2026-07-07..07-10 and starved discovery).

Every PREPROCESSING step is NON-FATAL (the repo's failure semantics: a tool crash
degrades, it never costs an edition); each prints an OK/FAIL line as it runs. The
git tail is the exception: a failed commit or push means nothing was published,
so it prints FAILED (never DONE) and exits 1 -- the writer must react. "Published"
is decided by what ORIGIN holds (the commit's own SHA pushed to refs/heads/main, then
read back with ls-remote), never by the exit code of a push of the local `main` ref --
that ref is stale in the routines' detached-HEAD sandbox. The notification
stub is written with real JSON encoding (no hand-escaped quotes) and a computed
UTC timestamp; a bare `date:` in the post's front matter is normalized to a full
ISO timestamp (the same-day sort-order bug class, closed at the root).

`--slug evaluator` is the review's variant: no story preprocessing (it records none),
just the stub -- clicking through to the review's own page, the one post still rendered
-- plus the same git tail.

Front matter is DERIVED here too (layout/title/categories from the slug, date from the brief's
own _Generated stamp, `published: true` for the review) -- a writer writes the brief body and
nothing else, so no prompt carries a block to reproduce by hand. Likewise the notification title
and tag: both follow from (slug, date), leaving the teaser as the only thing a writer passes.

Usage:
  publish.py --slug news --date 2026-07-18 [--root .]
             [--final /tmp/final.json]          # skips `record` when omitted (dedup unavailable)
             [--fetch-log /tmp/fetch.log]
             --notify-body "<teaser>"           # title/tag default from the slug
             [--notify-title "..."] [--notify-tags ...]
             [--message "..."] [--no-push] [--dry-run]
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Writers run the full preprocessing chain; the evaluator publishes a review + stub only
# (its own mechanical state comes from health.py/metrics.py at fire-start, and it records
# no stories), but shares the honest git tail -- the same rebase retry and the
# commit/push failure semantics its hand-rolled tail never had.
WRITER_SLUGS = ("news", "ai-ml", "science", "weekend", "sports")
SLUGS = WRITER_SLUGS + ("evaluator",)
EDITION_NAME = {"news": "News", "ai-ml": "AI/ML", "science": "Science",
                "weekend": "Weekend Deep Read", "sports": "Sports",
                "evaluator": "Weekly Pipeline Review"}
GIT_NAME = {"news": "News Routine", "ai-ml": "AI/ML Routine", "science": "Science Routine",
            "weekend": "Weekend Routine", "sports": "Sports Routine",
            "evaluator": "News Routine"}
SITE = "https://khalic-lab.github.io/claude-routines"
# Per-slug ntfy tag (the phone's icon per edition) -- fixed per stream, so it is a default
# here rather than an argument every prompt repeats.
NOTIFY_TAGS = {"news": "newspaper", "ai-ml": "robot_face", "science": "microscope",
               "weekend": "calendar", "sports": "soccer", "evaluator": "memo"}

BARE_DATE_RE = re.compile(r"^(date:\s*)(\d{4}-\d{2}-\d{2})\s*$", re.M)
# The brief's own machine-stamped line ("_Generated 2026-07-25T12:03:11+02:00 Europe/Zurich._",
# or Weekend's "_Coverage: … Generated <ts> …_") -- reused verbatim as the front-matter date so
# the two agree exactly instead of drifting by however long the publish step took. ANCHORED on the
# word Generated: an unanchored match would happily take a timestamp out of a story's own text.
GENERATED_TS_RE = re.compile(
    r"[Gg]enerated\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2}))")
# A complete front-matter block: opening ---, body, closing ---. Matching the WHOLE block (rather
# than partitioning on the first "\n---") is what makes the repair below safe on a post whose text
# begins with a blank line -- that shape used to put `published: true` outside the block entirely.
FRONT_MATTER_RE = re.compile(r"\A\s*---[ \t]*\r?\n(?P<fm>.*?)\r?\n---[ \t]*\r?$", re.S | re.M)


def say(msg):
    print("[publish] %s" % msg, flush=True)


def run_step(name, argv, root, dry_run):
    if dry_run:
        say("DRY-RUN %s: %s" % (name, " ".join(argv)))
        return True
    try:
        proc = subprocess.run(argv, cwd=root, capture_output=True, text=True)
    except OSError as exc:
        say("%s: FAIL (%s)" % (name, exc))
        return False
    out = (proc.stdout or "") + (proc.stderr or "")
    for line in out.strip().splitlines():
        say("  %s| %s" % (name, line))
    say("%s: %s" % (name, "OK" if proc.returncode == 0 else "FAIL (exit %d)" % proc.returncode))
    return proc.returncode == 0


def zurich_now():
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo("Europe/Zurich"))
    except Exception:
        return dt.datetime.now().astimezone()


def edition_title(slug, date):
    """The edition's one name -- post title AND notification title, everywhere."""
    return "%s — %s" % (EDITION_NAME[slug], date)


def _iso_offset(stamp):
    """'+0200' -> '+02:00' (Jekyll wants the colon); already-colon input passes through."""
    m = re.search(r"([+-]\d{2})(\d{2})$", stamp)
    return stamp[:m.start()] + m.group(1) + ":" + m.group(2) if m else stamp


def _fm_day(fm):
    """The YYYY-MM-DD of a front-matter block's `date:` line, or None."""
    m = re.search(r"^date:\s*(\d{4}-\d{2}-\d{2})", fm, re.M)
    return m.group(1) if m else None


def _is_future(stamp, now):
    try:
        return dt.datetime.fromisoformat(stamp.replace("Z", "+00:00")) > now
    except ValueError:
        return False


def ensure_front_matter(post_path, slug, date, dry_run):
    """Give the post the front matter Jekyll needs, derived from (slug, date) + the brief's
    own _Generated stamp -- so the prompt no longer carries a block for the model to
    reproduce exactly. A post that already has front matter is left alone, EXCEPT that an
    evaluator review is guaranteed `published: true`: _config.yml unpublishes posts by
    default, so without that line the one review page that should render silently doesn't.

    Returns the DAY of the front-matter date in effect (or None when it can't be read). That
    day -- not --date -- is what the notification must link to: Jekyll builds the permalink
    from front matter, so deriving the two from different sources is how they drift apart."""
    with open(post_path, encoding="utf-8") as fh:
        text = fh.read()

    if text.lstrip().startswith("---"):
        m = FRONT_MATTER_RE.match(text)
        if not m:
            # Opens with --- but never closes: prepending a second block would make it worse.
            say("front-matter: WARNING unterminated block -- left as written")
            return
        fm = m.group("fm")
        fm_day = _fm_day(fm)
        if slug != "evaluator" or re.search(r"^published:", fm, re.M):
            return fm_day
        if dry_run:
            say("DRY-RUN front-matter: would add `published: true` (evaluator page)")
            return fm_day
        # Insert INSIDE the block, located by span -- never by string surgery on the whole file.
        new = text[:m.end("fm")] + "\npublished: true" + text[m.end("fm"):]
        with open(post_path, "w", encoding="utf-8") as fh:
            fh.write(new)
        say("front-matter: added missing `published: true`")
        return fm_day

    # Time-of-day from the brief's own _Generated line (so the two agree); DATE always the
    # edition's, because Jekyll builds the permalink from the front-matter date while the
    # notification stub links using --date -- a run that crosses midnight would otherwise
    # publish the review at a URL its own notification 404s on.
    m = GENERATED_TS_RE.search(text[:1500])
    now = zurich_now()
    clock = _iso_offset(m.group(1)).split("T", 1)[1] if m else \
        _iso_offset(now.strftime("%H:%M:%S%z"))
    stamp = "%sT%s" % (date, clock)
    # Jekyll's `future` defaults to false and _config.yml does not override it: a front-matter
    # date ahead of the build clock makes the post vanish from the site entirely -- and the
    # evaluator review is the one post that still renders a page. So never emit a future stamp;
    # if --date is ahead of the real day, say so loudly and fall back to now.
    if _is_future(stamp, now):
        stamp = _iso_offset(now.strftime("%Y-%m-%dT%H:%M:%S%z"))
        say("front-matter: WARNING --date %s is ahead of the clock (%s) -- a future-dated post "
            "would be excluded from the build; using now instead" % (date, now.date().isoformat()))
    lines = ["---", "layout: single", 'title: "%s"' % edition_title(slug, date),
             "date: %s" % stamp, "categories: [%s]" % slug]
    if slug == "evaluator":
        lines.append("published: true")
    lines += ["---", ""]
    if dry_run:
        say("DRY-RUN front-matter: would prepend %d lines (date %s)" % (len(lines), stamp))
        return stamp.split("T", 1)[0]
    with open(post_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n" + text.lstrip("\n"))
    say("front-matter: wrote block (date %s, from %s)"
        % (stamp, "the _Generated line" if m else "now"))
    return stamp.split("T", 1)[0]


def normalize_front_matter(post_path, dry_run):
    """A bare `date: YYYY-MM-DD` front-matter line becomes a full ISO timestamp --
    bare dates make same-day briefs sort out of chronological order."""
    with open(post_path, encoding="utf-8") as fh:
        text = fh.read()
    head = text[:600]
    m = BARE_DATE_RE.search(head)
    if not m:
        say("front-matter: date already a full timestamp")
        return
    stamp = "%s%sT%s" % (m.group(1), m.group(2),
                         _iso_offset(zurich_now().strftime("%H:%M:%S%z")))
    if dry_run:
        say("DRY-RUN front-matter: would rewrite %r -> %r" % (m.group(0), stamp))
        return
    with open(post_path, "w", encoding="utf-8") as fh:
        fh.write(text[:600].replace(m.group(0), stamp, 1) + text[600:])
    say("front-matter: normalized bare date -> %s" % stamp)


def write_stub(root, slug, date, title, body, tags, dry_run):
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    # Individual brief pages are retired (2026-07-18) — the homepage story feed is where
    # brief content lives, so brief notifications click through there. The evaluator
    # review is the one post that still renders its own page, so it links to it.
    click = SITE + "/"
    if slug == "evaluator":
        click = "%s/%s/evaluator/" % (SITE, date.replace("-", "/"))
    stub = {
        "title": title,
        "click": click,
        "body": body,
        "tags": tags,
    }
    path = os.path.join(root, "pending-notifications", "%s-%s.json" % (ts, slug))
    if dry_run:
        say("DRY-RUN stub: %s -> %s" % (path, json.dumps(stub, ensure_ascii=False)))
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(stub, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    say("stub: wrote %s" % os.path.relpath(path, root))


def git(root, slug, argv):
    return ["git", "-c", "user.email=routine@khalic-lab",
            "-c", "user.name=%s" % GIT_NAME.get(slug, "News Routine"),
            "-c", "commit.gpgsign=false"] + argv


def staged_changes(root, dry_run):
    """True when the index differs from HEAD (i.e. `git commit` has something to do).
    Also true when HEAD doesn't exist yet (first commit of a fresh repo)."""
    if dry_run:
        return True
    proc = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=root,
                          capture_output=True)
    return proc.returncode != 0


def _rev_parse(root, ref):
    """The SHA a ref resolves to locally, or None."""
    try:
        proc = subprocess.run(["git", "rev-parse", "--verify", ref], cwd=root,
                              capture_output=True, text=True)
    except OSError:
        return None
    out = proc.stdout.strip()
    return out if proc.returncode == 0 and out else None


def _remote_main(root, slug):
    """What origin's main ACTUALLY points at, asked of the REMOTE -- never read from a
    local `origin/main` tracking ref, which a detached sandbox that never fetched can
    leave arbitrarily stale. None when the remote can't be reached or read."""
    try:
        proc = subprocess.run(git(root, slug, ["ls-remote", "origin", "refs/heads/main"]),
                              cwd=root, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    lines = proc.stdout.split()
    return lines[0] if lines else None


def push_commit(root, slug, name, sha, dry_run):
    """Push THIS commit -- by SHA, to refs/heads/main -- and answer whether origin holds it.

    Two defects meet here, and one refspec closes both. `push origin main` pushed the local
    `main` REF, which in the routines' detached-HEAD sandbox is NOT the commit just created:
    the push succeeded as a no-op on a stale branch, the run printed DONE, and the edition
    never reached origin (R1, the 2026-07-25 review's one blocker). The converse followed from
    the same ref: with local `main` stale, the retry pushed the stale ref too and exited
    non-zero, so 8 of the 11 briefs in the week to 2026-08-02 were marked "has NOT reached
    origin" while sitting on origin/main all along.

    So the verdict comes from the remote, not from a ref that never described this edition:
    published when the push of THIS SHA exits 0, or when origin/main already resolves to it
    (a retry, a concurrent routine, or the bridge's drain-reconcile got there first)."""
    ok = run_step(name, git(root, slug,
                            ["push", "origin", "%s:refs/heads/main" % (sha or "HEAD")]),
                  root, dry_run)
    if dry_run:
        return True
    remote = _remote_main(root, slug)
    short = (sha or "HEAD")[:12]
    if sha and remote == sha:
        say("push: verified origin/main == %s" % short)
        return True
    if ok and remote is None:
        say("push: %s pushed (exit 0) but origin/main is UNVERIFIED -- ls-remote could not "
            "be read; treating the push's own exit status as the answer" % short)
        return True
    if ok:
        say("push: %s pushed (exit 0); origin/main has since advanced to %s" % (short, remote[:12]))
        return True
    say("push: FAILED -- origin/main is %s, not the published commit %s"
        % (remote[:12] if remote else "unreadable", short))
    return False


def commit_and_push(root, slug, message, no_push, dry_run):
    """Returns 'ok', 'commit-failed', or 'push-failed'.

    A failed `git commit` followed by a no-op push used to print DONE and exit 0
    (the push of an unchanged branch succeeds) -- the one failure shape a writer
    must NEVER mistake for success, since nothing was published at all.

    'push-failed' is reported to the OPERATOR only -- the log line and exit 1 -- and never
    written into the brief. A failure note used to be appended to the post and amended into
    the commit, so it would "survive the sandbox". It does, and that is the flaw: the note is
    readable only once the commit carrying it reaches origin, which is exactly when it has
    become false. All 23 briefs that carried it are on origin/main -- 8 in the single week to
    2026-08-02, one needing a follow-up commit to strip it (07-31 news), one of them the
    evaluator review that filed the defect (2026-08-02 Patch 2)."""
    # A missing pathspec makes `git add` abort WITHOUT staging the ones that do
    # exist (fatal, not partial) -- which cascades into the exact false-DONE shape
    # this function guards against. Only add directories that exist.
    wanted = ["_posts/", "pending-notifications/", "index/", "_data/", "sources/",
              "proposals/"]
    # The evaluator holds a bounded grant to append dated lines to reader-profile.md
    # ("Learned preferences"). Nothing else in the tree writes that file, and it is not
    # under any staged directory -- unstaged, the edit dies with the sandbox while the
    # run's proposal record still claims applied:true. Slug-scoped: writers only READ it.
    if slug == "evaluator":
        wanted.append("reader-profile.md")
    paths = [d for d in wanted if os.path.exists(os.path.join(root, d))] or ["_posts/"]
    run_step("git-add", git(root, slug, ["add"] + paths), root, dry_run)
    if staged_changes(root, dry_run):
        if not run_step("git-commit", git(root, slug, ["commit", "-m", message]),
                        root, dry_run):
            return "commit-failed"
    else:
        say("commit: nothing newly staged (edition already committed; push still attempted)")
    if no_push:
        say("push: skipped (--no-push)")
        return "ok"
    # The commit to publish is HEAD's -- resolved as a SHA so the refspec names THIS edition
    # even when the sandbox is detached and `main` points somewhere else entirely.
    if push_commit(root, slug, "git-push", _rev_parse(root, "HEAD"), dry_run):
        return "ok"
    # Concurrent editions both rewrite _data/homefeed.json; the fix is always:
    # rebase, REGENERATE the feed from the merged tree, continue, push again.
    say("push failed -- rebase + feed regeneration retry")
    run_step("git-pull-rebase", git(root, slug, ["pull", "--rebase", "origin", "main"]), root, dry_run)
    run_step("feed-rebuild", [sys.executable, "tools/build_stories_feed.py"], root, dry_run)
    run_step("health-rebuild", [sys.executable, "tools/sources/health.py"], root, dry_run)
    run_step("git-add-data", git(root, slug, ["add", "_data/"]), root, dry_run)
    if not run_step("git-rebase-continue",
                    git(root, slug, ["-c", "core.editor=true", "rebase", "--continue"]),
                    root, dry_run):
        run_step("git-amend", git(root, slug, ["commit", "--amend", "--no-edit"]), root, dry_run)
    # An unresolved conflict leaves HEAD at the rebase's ONTO commit -- origin's own tip.
    # Pushing that is a no-op that verifies as success and reports a lost edition as DONE.
    # `git ls-files -u` (the unmerged index) is the load-bearing check, not the presence of
    # .git/rebase-merge: the unmerged index is what makes BOTH `rebase --continue` and
    # `commit --amend` fail above, and it reads correctly where `.git` is a file (worktrees).
    # The retry regenerates and stages `_data/` only, so a conflict anywhere else -- e.g.
    # sources/registry.yml, EOF-appended by registry-sync on every writer run -- survives it.
    if not dry_run:
        unmerged = subprocess.run(["git", "ls-files", "-u"], cwd=root,
                                  capture_output=True, text=True).stdout.strip()
        if unmerged:
            say("push: FAILED -- rebase left unmerged paths; HEAD is origin's own tip, not this "
                "edition. Resolve the conflict and push HEAD:refs/heads/main manually.")
            return "push-failed"
    # Re-resolve: the rebase moved HEAD, and the amend fallback above moved it again.
    if push_commit(root, slug, "git-push-retry", _rev_parse(root, "HEAD"), dry_run):
        return "ok"
    return "push-failed"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--slug", required=True, choices=SLUGS)
    p.add_argument("--date", required=True)
    p.add_argument("--root", default=ROOT)
    p.add_argument("--final", default=None, help="Step-C final.json; omit if dedup was unavailable")
    p.add_argument("--candidates", default="/tmp/cand.json",
                   help="Step-A candidates; snapshotted with --verdicts when both exist")
    p.add_argument("--verdicts", default="/tmp/verdicts.json")
    p.add_argument("--fetch-log", default=os.environ.get("FETCH_LOG", "/tmp/fetch.log"))
    # Title and tag are derivable from (slug, date); only the teaser is the writer's to judge.
    p.add_argument("--notify-title", default=None, help="defaults to '<Edition> — <date>'")
    p.add_argument("--notify-body", default=None)
    p.add_argument("--notify-tags", default=None, help="defaults to the slug's ntfy tag")
    p.add_argument("--message", default=None)
    p.add_argument("--no-push", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    root = os.path.abspath(args.root)
    post = os.path.join(root, "_posts", "%s-%s.md" % (args.date, args.slug))
    if not os.path.exists(post) and not args.dry_run:
        say("FATAL: %s does not exist -- write the brief first." % post)
        return 2

    stub_date = args.date
    if os.path.exists(post):
        stub_date = ensure_front_matter(post, args.slug, args.date, args.dry_run) or args.date
        normalize_front_matter(post, args.dry_run)
        if stub_date != args.date:
            say("stub: will link %s (the front-matter date), not --date %s" % (stub_date, args.date))

    py = sys.executable
    index_file = os.path.join(root, "index", "stories", "%s-%s.jsonl" % (args.date, args.slug))

    if args.slug not in WRITER_SLUGS:
        say("preprocessing: skipped (%s publishes post + stub only)" % args.slug)
    else:
        if args.final:
            run_step("record", [py, "tools/dedup/dedup.py", "record", "--stories", args.final,
                                "--date", args.date, "--slug", args.slug],
                     root, args.dry_run)
        else:
            say("record: skipped (no --final; note 'dedup unavailable' in Gaps)")

        # The Step-A verdict snapshot (desk-stats raw material) rides along here rather
        # than being a second command in the writer's prompt: both files are still on
        # disk from the check the writer ran before composing.
        if os.path.exists(args.candidates) and os.path.exists(args.verdicts):
            run_step("verdicts", [py, "tools/store/verdicts.py",
                                  "--candidates", args.candidates,
                                  "--verdicts", args.verdicts,
                                  "--date", args.date, "--slug", args.slug],
                     root, args.dry_run)
        else:
            say("verdicts: skipped (no %s + %s)" % (args.candidates, args.verdicts))

        anchor_cmd = [py, "tools/store/anchor.py"]
        if os.path.exists(index_file):
            anchor_cmd += ["--index", os.path.relpath(index_file, root)]
        anchor_cmd.append(os.path.relpath(post, root))
        run_step("anchor", anchor_cmd, root, args.dry_run)

        run_step("footer", [py, "tools/footer.py", os.path.relpath(post, root),
                            "--root", ".", "--fetch-log", args.fetch_log], root, args.dry_run)
        run_step("source-lint", [py, "tools/sources/lint.py", os.path.relpath(post, root),
                                 "--root", "."], root, args.dry_run)
        run_step("registry-sync", [py, "tools/sources/registry.py", "sync", "--root", "."],
                 root, args.dry_run)
        run_step("institutions-sync", [py, "tools/sources/institutions.py", "sync", "--root", "."],
                 root, args.dry_run)
        run_step("date-lint", [py, "tools/dedup/dedup.py", "lint", "--brief",
                               os.path.relpath(post, root)], root, args.dry_run)
        run_step("feed", [py, "tools/build_stories_feed.py"], root, args.dry_run)
        run_step("source-health", [py, "tools/sources/health.py"], root, args.dry_run)
        # refresh the Worker-hosted analytical plane (embed-proxy /plane/*) from the ledger the
        # record step just extended — non-fatal like everything else; analytics never cost an edition
        run_step("plane-push", [py, "tools/plane/bake.py", "--push"], root, args.dry_run)

    if args.notify_body:
        write_stub(root, args.slug, stub_date,
                   args.notify_title or edition_title(args.slug, args.date),
                   args.notify_body,
                   args.notify_tags or NOTIFY_TAGS.get(args.slug, "newspaper"),
                   args.dry_run)
    else:
        say("stub: skipped (no --notify-body teaser)")

    message = args.message or edition_title(args.slug, args.date)
    outcome = commit_and_push(root, args.slug, message, args.no_push, args.dry_run)
    if outcome == "commit-failed":
        say("FAILED (git commit errored -- NOTHING was published; fix the error above and rerun)")
        return 1
    if outcome == "push-failed":
        # The log line and exit 1 ARE the report -- nothing is written into the brief; see
        # commit_and_push's docstring for why a note in the body could only ever read as false.
        # HEAD:refs/heads/main, not `main`: the retry instruction must not be the very
        # command whose stale-ref behaviour lost editions in the first place (R1).
        say("FAILED (push -- edition committed locally but NOT on origin; "
            "retry `git push origin HEAD:refs/heads/main` before the session ends)")
        return 1
    say("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
