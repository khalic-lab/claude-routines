#!/usr/bin/env python3
"""Turn a run transcript into an append-only usage record, by two entry points.

  --hook   Stop / SessionEnd hook. Reads {session_id, transcript_path, cwd, hook_event_name}
           on stdin, parses the transcript, appends a record, then commits and pushes it.
           This is the ONLY path that measures a run which publishes nothing (Watch idle
           ticks, skip-on-empty writers). It NEVER exits non-zero and NEVER prints to stdout
           -- a Stop hook's stdout is parsed by Claude Code for control decisions, and a
           failing hook must not wedge the routine. One summary line goes to stderr.

  --find   Publish-time, inside the running session (no commit of its own -- publish.py's
           `git add index/` sweeps the file into the edition commit). Locates the live
           transcript by glob and appends a stage:"publish" record. This is the guarantee
           for "measured starting next deploy": even if the sandbox never fires the hook,
           every publishing run still lands a record.

  --transcript PATH   Measure any transcript locally: prints the record as JSON. Appends only
                      under USAGE_RECORD_LOCAL=1 (or --dry-run to force print-only). Used by
                      the tests and for one-off local measurement.

Records: index/usage/<YYYY-MM>-<routine>.jsonl, one JSON object per line, month from the
run's start. Append-only, idempotent per (session_id, stage). Fold (tools/usage/fold.py)
keeps the most complete record per session_id across the two stages.

Gate: on macOS the script is a no-op (exit 0, no write) unless USAGE_RECORD_LOCAL=1 -- local
Mac sessions load this same project's hooks and must not pollute the routine ledger.
"""
import argparse
import datetime as dt
import glob
import json
import os
import platform
import subprocess
import sys

# Run as a plain script (python3 tools/usage/record.py ...), so the sibling modules are
# imported by putting this file's directory on the path rather than as a package.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import transcript as transcript_mod  # noqa: E402
import pricing as pricing_mod  # noqa: E402


DEFAULT_TOOLS = ("Bash", "WebFetch", "WebSearch", "Read", "Write", "Edit", "Glob", "Grep")
_STAGE_FOR_EVENT = {"Stop": "stop", "SessionEnd": "session-end"}


def _now_iso(now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    return now.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def gate_open():
    """True when this run may write to the ledger: any non-Darwin host, or an explicit
    USAGE_RECORD_LOCAL opt-in on the Mac."""
    if os.environ.get("USAGE_RECORD_LOCAL"):
        return True
    return platform.system() != "Darwin"


def build_record(measurement, stage, hook_event=None, edition=None, now=None):
    """Wrap a transcript.parse() measurement into the on-disk record schema (v1)."""
    tool_calls = {t: 0 for t in DEFAULT_TOOLS}
    tool_calls.update(measurement.get("tool_calls") or {})
    return {
        "v": 1,
        "session_id": measurement.get("session_id"),
        "stage": stage,
        "routine": measurement.get("routine"),
        "edition": edition if edition is not None else measurement.get("edition"),
        "started": measurement.get("started"),
        "ended": measurement.get("ended"),
        "duration_s": measurement.get("duration_s"),
        "messages": measurement.get("messages"),
        "models": measurement.get("models") or {},
        "totals": measurement.get("totals") or {},
        "server_tools": measurement.get("server_tools") or {},
        "tool_calls": tool_calls,
        "cost_usd_list": pricing_mod.cost(measurement.get("models") or {}),
        "claude_version": measurement.get("claude_version"),
        "cwd": measurement.get("cwd"),
        "transcript": measurement.get("transcript"),
        "transcript_lines": measurement.get("transcript_lines"),
        "hook_event": hook_event,
        "recorded_at": _now_iso(now),
    }


def usage_path(root, routine, started, recorded_at):
    """index/usage/<YYYY-MM>-<routine>.jsonl -- month from the run's start (or, absent a
    start, from when it was recorded)."""
    month = (started or recorded_at or "")[:7] or _now_iso()[:7]
    routine = routine or "unknown"
    return os.path.join(root, "index", "usage", "%s-%s.jsonl" % (month, routine))


def already_recorded(path, session_id, stage):
    """True when the target file already holds a line with this (session_id, stage)."""
    if not os.path.exists(path):
        return False
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("session_id") == session_id and rec.get("stage") == stage:
                return True
    return False


_HOOK_STAGES = ("stop", "session-end")


def hook_blocking_stage(path, session_id):
    """The stage of an existing hook record ('stop' or 'session-end') for this session, or
    None. A --hook run is a no-op when EITHER hook stage is already on file: a run that fires
    both Stop and SessionEnd must land ONE record, not two commits and two pushes. A
    publish-stage record never blocks -- the hook measurement supersedes it (fold prefers
    session-end > stop > publish, so the hook record still wins the fold)."""
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("session_id") == session_id and rec.get("stage") in _HOOK_STAGES:
                return rec.get("stage")
    return None


def append_record(path, record):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


# ---- git tail (hook mode only) ----------------------------------------------------------

def _git_base():
    # Own identity + no signing, mirroring publish.py's wrapper -- the routine sandbox holds
    # no key, and headless contexts cannot open pinentry.
    return ["git", "-c", "user.email=routine@khalic-lab", "-c", "user.name=Usage Hook",
            "-c", "commit.gpgsign=false"]


def _run(root, argv):
    try:
        proc = subprocess.run(argv, cwd=root, capture_output=True, text=True)
    except OSError:
        return 1, ""
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def _dirty(root):
    _rc, out = _run(root, _git_base() + ["status", "--porcelain"])
    return out.strip() != ""


def commit_and_push(root, routine, started, stage):
    """Stage index/usage/ only, commit path-scoped (so anything else the routine left staged
    is not swept in), then push HEAD to main with a three-attempt, rebase-between loop. The
    stash is never popped -- the session is over. Returns a one-line human summary."""
    date = (started or "")[:10] or "unknown"
    msg = "Usage — %s %s (%s)" % (routine or "unknown", date, stage)
    _run(root, _git_base() + ["add", "index/usage/"])
    _run(root, _git_base() + ["commit", "-m", msg, "--", "index/usage/"])
    for attempt in range(3):
        rc, _out = _run(root, _git_base() + ["push", "origin", "HEAD:refs/heads/main"])
        if rc == 0:
            return "pushed on attempt %d" % (attempt + 1)
        if attempt < 2:
            if _dirty(root):
                _run(root, _git_base() + ["stash", "--include-untracked"])
            _run(root, _git_base() + ["pull", "--rebase", "origin", "main"])
    return "push failed after 3 attempts (record committed locally)"


# ---- --find: locate the live transcript --------------------------------------------------

def _last_json_line(path):
    last = None
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    last = line
    except OSError:
        return None
    if not last:
        return None
    try:
        return json.loads(last)
    except json.JSONDecodeError:
        return None


def _age_seconds(ts, now):
    if not ts:
        return None
    try:
        when = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=dt.timezone.utc)
    return (now - when).total_seconds()


def find_live_transcript(config_roots, repo_root, now=None, max_age_s=30 * 60):
    """Newest *.jsonl under <root>/projects/*/ whose last line's cwd is this repo and whose
    last line is younger than max_age_s. Returns (path_or_None, candidates_scanned)."""
    now = now or dt.datetime.now(dt.timezone.utc)
    want = os.path.realpath(repo_root)
    matches = []
    scanned = 0
    for base in config_roots:
        for path in glob.glob(os.path.join(base, "projects", "*", "*.jsonl")):
            scanned += 1
            last = _last_json_line(path)
            if not last:
                continue
            cwd = last.get("cwd")
            if not cwd or os.path.realpath(cwd) != want:
                continue
            age = _age_seconds(last.get("timestamp"), now)
            if age is None or age > max_age_s:
                continue
            matches.append((os.path.getmtime(path), path))
    if not matches:
        return None, scanned
    matches.sort()
    return matches[-1][1], scanned


# ---- CLI --------------------------------------------------------------------------------

def cmd_hook(args):
    """Stop / SessionEnd hook: parse stdin, append, commit, push. Always exit 0."""
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}
    if not gate_open():
        sys.stderr.write("usage: skipped (macOS without USAGE_RECORD_LOCAL)\n")
        return 0
    tpath = payload.get("transcript_path")
    root = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    hook_event = payload.get("hook_event_name")
    stage = _STAGE_FOR_EVENT.get(hook_event, "stop")
    if not tpath or not os.path.exists(tpath):
        sys.stderr.write("usage: transcript_path missing or absent (%r)\n" % tpath)
        return 0
    try:
        measurement = transcript_mod.parse(tpath)
    except OSError as exc:
        sys.stderr.write("usage: could not read transcript (%s)\n" % exc)
        return 0
    session_id = payload.get("session_id") or measurement.get("session_id")
    measurement["session_id"] = session_id
    record = build_record(measurement, stage, hook_event=hook_event)
    path = usage_path(root, record["routine"], record["started"], record["recorded_at"])
    blocking = hook_blocking_stage(path, session_id)
    if blocking is not None:
        sys.stderr.write("usage: already recorded (%s / %s); this %s hook is a no-op\n"
                         % (session_id, blocking, stage))
        return 0
    append_record(path, record)
    summary = commit_and_push(root, record["routine"], record["started"], stage)
    sys.stderr.write("usage: recorded %s %s (%s) -> %s; %s\n"
                     % (record["routine"], (record["started"] or "")[:10], stage,
                        os.path.relpath(path, root), summary))
    return 0


def cmd_find(args):
    """Publish-time: find the live transcript, append a stage record (no commit here)."""
    root = os.path.abspath(args.root or os.getcwd())
    if not gate_open():
        print("usage: skipped (macOS without USAGE_RECORD_LOCAL)")
        return 0
    roots = []
    cfg = os.environ.get("CLAUDE_CONFIG_DIR")
    if cfg:
        roots.append(cfg)
    roots.append(os.path.expanduser("~/.claude"))
    path, scanned = find_live_transcript(roots, root)
    if not path:
        print("usage: transcript not found (%d candidates)" % scanned)
        return 0
    measurement = transcript_mod.parse(path, routine=args.slug)
    edition = measurement.get("edition")
    if edition is None and args.slug and args.date:
        edition = "%s-%s" % (args.date, args.slug)
    record = build_record(measurement, args.stage, edition=edition)
    session_id = record["session_id"]
    out = usage_path(root, record["routine"], record["started"], record["recorded_at"])
    if already_recorded(out, session_id, args.stage):
        print("usage: already recorded (%s / %s)" % (session_id, args.stage))
        return 0
    append_record(out, record)
    print("usage: recorded %s %s (%s) -> %s"
          % (record["routine"], (record["started"] or "")[:10], args.stage,
             os.path.relpath(out, root)))
    return 0


def cmd_transcript(args):
    """Measure a named transcript. Print the record; append only under the gate/opt-in."""
    root = os.path.abspath(args.root or os.getcwd())
    measurement = transcript_mod.parse(args.transcript, routine=args.routine)
    record = build_record(measurement, args.stage)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    if args.dry_run or not gate_open():
        return 0
    out = usage_path(root, record["routine"], record["started"], record["recorded_at"])
    if already_recorded(out, record["session_id"], args.stage):
        return 0
    append_record(out, record)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--hook", action="store_true", help="Stop/SessionEnd hook mode (stdin JSON)")
    p.add_argument("--find", action="store_true", help="publish-time: find live transcript")
    p.add_argument("--transcript", help="measure this transcript path")
    p.add_argument("--stage", default=None, help="record stage (publish/stop/session-end)")
    p.add_argument("--slug", default=None, help="routine slug (--find: override detection)")
    p.add_argument("--date", default=None, help="edition date (--find: edition fallback)")
    p.add_argument("--routine", default=None, help="--transcript: override routine detection")
    p.add_argument("--root", default=None, help="repo root (default: cwd)")
    p.add_argument("--dry-run", action="store_true", help="--transcript: print only, never append")
    args = p.parse_args(argv)

    if args.hook:
        return cmd_hook(args)
    if args.find:
        args.stage = args.stage or "publish"
        return cmd_find(args)
    if args.transcript:
        args.stage = args.stage or "stop"
        return cmd_transcript(args)
    p.error("one of --hook / --find / --transcript is required")


if __name__ == "__main__":
    sys.exit(main())
