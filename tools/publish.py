#!/usr/bin/env python3
"""Publish-tail orchestrator -- the deterministic end of every writer run.

One command replaces the ~10 prompt-prose steps a writer routine used to replay by
hand (DEDUP.md Steps C..E + its own Output section): record -> anchor -> computed
footer telemetry -> source lint -> registry/institutions sync -> date lint -> feed
+ stats rebuild -> source health -> notification stub -> git add/commit/push with
the rebase-conflict feed regeneration. A step can no longer be skipped, misordered,
or typo'd -- the historical failure class this tool exists to close (registry.py
sync went uninvoked 2026-07-07..07-10 and starved discovery).

Every step is NON-FATAL (the repo's failure semantics: a tool crash degrades, it
never costs an edition); each prints an OK/FAIL line as it runs. The notification
stub is written with real JSON encoding (no hand-escaped quotes) and a computed
UTC timestamp; a bare `date:` in the post's front matter is normalized to a full
ISO timestamp (the same-day sort-order bug class, closed at the root).

Usage:
  publish.py --slug news --date 2026-07-18 [--root .]
             [--final /tmp/final.json]          # skips `record` when omitted (dedup unavailable)
             [--fetch-log /tmp/fetch.log]
             [--notify-title "..." --notify-body "..." --notify-tags newspaper]
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
SLUGS = ("news", "ai-ml", "science", "weekend", "sports")
COMMIT_TITLE = {"news": "News", "ai-ml": "AI/ML", "science": "Science",
                "weekend": "Weekend Deep Read", "sports": "Sports"}
GIT_NAME = {"news": "News Routine", "ai-ml": "AI/ML Routine", "science": "Science Routine",
            "weekend": "Weekend Routine", "sports": "Sports Routine"}
SITE = "https://khalic-lab.github.io/claude-routines"

# Committed alongside this file in DEDUP.md; low-value token (gates only Workers-AI
# embedding spend on our own account). Env vars, when set, win.
EMBED_DEFAULTS = {
    "EMBED_WORKER_URL": "https://embed-proxy.khalic-lab.workers.dev",
    "EMBED_TOKEN": "b4bd10fc46e70315205b5aa4a4352d6d79f750d13cc4ef960928f8e6da5aae8a",
}

BARE_DATE_RE = re.compile(r"^(date:\s*)(\d{4}-\d{2}-\d{2})\s*$", re.M)


def say(msg):
    print("[publish] %s" % msg, flush=True)


def run_step(name, argv, root, dry_run, env=None):
    if dry_run:
        say("DRY-RUN %s: %s" % (name, " ".join(argv)))
        return True
    merged = dict(os.environ)
    if env:
        for k, v in env.items():
            merged.setdefault(k, v)
    try:
        proc = subprocess.run(argv, cwd=root, capture_output=True, text=True, env=merged)
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
                         zurich_now().strftime("%H:%M:%S%z"))
    stamp = stamp[:-2] + ":" + stamp[-2:]  # +0200 -> +02:00
    if dry_run:
        say("DRY-RUN front-matter: would rewrite %r -> %r" % (m.group(0), stamp))
        return
    with open(post_path, "w", encoding="utf-8") as fh:
        fh.write(text[:600].replace(m.group(0), stamp, 1) + text[600:])
    say("front-matter: normalized bare date -> %s" % stamp)


def write_stub(root, slug, date, title, body, tags, dry_run):
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    y, m, d = date.split("-")
    stub = {
        "title": title,
        "click": "%s/%s/%s/%s/%s/" % (SITE, y, m, d, slug),
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


def commit_and_push(root, slug, message, no_push, dry_run):
    run_step("git-add", git(root, slug, ["add", "_posts/", "pending-notifications/",
                                         "index/", "_data/"]), root, dry_run)
    # sources/ + proposals/ may not exist in minimal trees; separate + tolerated.
    run_step("git-add-sources", git(root, slug, ["add", "sources/"]), root, dry_run)
    run_step("git-commit", git(root, slug, ["commit", "-m", message]), root, dry_run)
    if no_push:
        say("push: skipped (--no-push)")
        return True
    if run_step("git-push", git(root, slug, ["push", "origin", "main"]), root, dry_run):
        return True
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
    return run_step("git-push-retry", git(root, slug, ["push", "origin", "main"]), root, dry_run)


def append_push_failure(post_path, dry_run):
    note = "- git push failed: see run log (bridge will reconcile on its next tick)."
    if dry_run:
        return
    try:
        with open(post_path, "a", encoding="utf-8") as fh:
            fh.write(note + "\n")
    except OSError:
        pass


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--slug", required=True, choices=SLUGS)
    p.add_argument("--date", required=True)
    p.add_argument("--root", default=ROOT)
    p.add_argument("--final", default=None, help="Step-C final.json; omit if dedup was unavailable")
    p.add_argument("--fetch-log", default=os.environ.get("FETCH_LOG", "/tmp/fetch.log"))
    p.add_argument("--notify-title", default=None)
    p.add_argument("--notify-body", default=None)
    p.add_argument("--notify-tags", default="newspaper")
    p.add_argument("--message", default=None)
    p.add_argument("--no-push", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    root = os.path.abspath(args.root)
    post = os.path.join(root, "_posts", "%s-%s.md" % (args.date, args.slug))
    if not os.path.exists(post) and not args.dry_run:
        say("FATAL: %s does not exist -- write the brief first." % post)
        return 2

    if os.path.exists(post):
        normalize_front_matter(post, args.dry_run)

    py = sys.executable
    index_file = os.path.join(root, "index", "stories", "%s-%s.jsonl" % (args.date, args.slug))

    if args.final:
        run_step("record", [py, "tools/dedup/dedup.py", "record", "--stories", args.final,
                            "--date", args.date, "--slug", args.slug],
                 root, args.dry_run, env=EMBED_DEFAULTS)
    else:
        say("record: skipped (no --final; note 'dedup unavailable' in Gaps)")

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

    if args.notify_title and args.notify_body:
        write_stub(root, args.slug, args.date, args.notify_title, args.notify_body,
                   args.notify_tags, args.dry_run)
    else:
        say("stub: skipped (no --notify-title/--notify-body)")

    message = args.message or "%s — %s" % (COMMIT_TITLE[args.slug], args.date)
    pushed = commit_and_push(root, args.slug, message, args.no_push, args.dry_run)
    if not pushed and not args.no_push:
        append_push_failure(post, args.dry_run)
        say("DONE (push FAILED -- noted in the post; bridge/next run reconciles)")
    else:
        say("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
