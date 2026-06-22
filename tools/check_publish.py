#!/usr/bin/env python3
"""Publish-safety guard — turn the fragile `_config.yml` exclude denylist into a tested invariant.

Two checks:
  1. REQUIRED_EXCLUDES — every sensitive path must be present in `_config.yml` exclude:.
  2. Content scan — no secret-shaped string (env id, trigger id, literal bearer token, long hex)
     may appear in any file Jekyll would PUBLISH (i.e. not under an excluded path; _posts is the
     site content and is scanned too — briefs must not carry infra identifiers).

Run from the repo root:  python3 tools/check_publish.py
Exit 0 = safe, 1 = a leak or a missing exclude. `tools/` is itself excluded, so this script and
the wrangler configs (which legitimately hold IDs) are never treated as published.
"""
import os, re, sys, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Paths that MUST be excluded from the published site.
REQUIRED_EXCLUDES = {
    "CLAUDE.md", "ARCHITECTURE.md", "README.md", "reader-profile.md", "reader-profile",
    "docs", "diagrams", "tools", "routines", "feedback", "proposals",
    "index/stories", "watches.yml", "pending-notifications", "bridge.sh", "HANDOFF.md",
}

SECRET_PATTERNS = [
    ("environment id", re.compile(r"env_[A-Za-z0-9]{20,}")),
    ("trigger id", re.compile(r"trig_[A-Za-z0-9]{16,}")),
    ("literal bearer token", re.compile(r"Bearer\s+[A-Za-z0-9._-]{24,}")),
    # known infra secret literals only — a generic long-hex rule false-positives on the commit
    # SHAs / IoC sample hashes that cyber briefs legitimately publish.
    ("feedback-sink KV namespace id", re.compile(r"005fab1cb5f842cb91a6dce43c973bfd")),
]


def parse_exclude(config_path):
    excludes, in_block = [], False
    for line in open(config_path, encoding="utf-8"):
        if re.match(r"^exclude:\s*$", line):
            in_block = True; continue
        if in_block:
            m = re.match(r"^\s+-\s+(.+?)\s*(?:#.*)?$", line)
            if m:
                excludes.append(m.group(1).strip().strip('"'))
            elif line.strip() and not line.startswith((" ", "\t")):
                break
    return excludes


def is_excluded(path, excludes):
    top = path.split("/", 1)[0]
    for e in excludes:
        if path == e or top == e or path.startswith(e.rstrip("/") + "/"):
            return True
        if e.startswith("*") and path.endswith(e.lstrip("*")):
            return True
    return False


def tracked_files():
    out = subprocess.run(["git", "-C", ROOT, "ls-files"], capture_output=True, text=True)
    return [f for f in out.stdout.splitlines() if f]


def main():
    cfg = os.path.join(ROOT, "_config.yml")
    excludes = parse_exclude(cfg)
    ok = True

    missing = sorted(REQUIRED_EXCLUDES - set(excludes))
    print("== required excludes ==")
    if missing:
        ok = False
        for m in missing:
            print(f"  MISSING from _config.yml exclude: {m}")
    else:
        print(f"  all {len(REQUIRED_EXCLUDES)} sensitive paths excluded ✓")

    print("\n== secret scan of published files ==")
    hits = 0
    for f in tracked_files():
        if is_excluded(f, excludes):
            continue
        p = os.path.join(ROOT, f)
        try:
            text = open(p, encoding="utf-8", errors="ignore").read()
        except (IsADirectoryError, FileNotFoundError):
            continue
        for label, rx in SECRET_PATTERNS:
            m = rx.search(text)
            if m:
                ok = False; hits += 1
                print(f"  LEAK in {f}: {label} → {m.group(0)[:32]}…")
    if not hits:
        print("  no secret-shaped strings in published files ✓")

    print("\n" + ("PUBLISH-SAFE ✅" if ok else "PUBLISH-UNSAFE ❌"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
