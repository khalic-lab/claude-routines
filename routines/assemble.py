#!/usr/bin/env python3
"""Assemble writer-routine prompts from shared partials + per-stream sources.

The four writer prompts share five byte-identical sections (Newsroom ethos, Reader profile +
source weights, Format, Pedagogical tone, Date discipline). Those live once in
`routines/_shared/*.md`; each writer's stream-specific body lives in `routines/src/<slug>.md`
with `<!-- include: _shared/<name>.md -->` placeholders. This script expands the placeholders
to (re)generate the canonical `routines/<slug>.md` — the file the live trigger's bootstrap shim
reads at fire time (see CLAUDE.md → "Editing a routine"; no mirroring since 2026-06-29).

Usage:
  python3 routines/assemble.py            # regenerate routines/<slug>.md from src/ + _shared/
  python3 routines/assemble.py check      # verify routines/<slug>.md == assemble(src) (pre-commit)

Workflow: edit routines/src/<slug>.md or routines/_shared/*.md → `assemble.py` → commit + push
(the shim `git pull`s and reads the regenerated file). `assemble.py check` is the drift guard:
non-zero exit means a committed prompt no longer matches its sources (someone hand-edited the
generated file, or forgot to re-run assemble).
"""
import os, re, sys, glob

BASE = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE, "src")
SHARED_DIR = os.path.join(BASE, "_shared")
PH_RE = re.compile(r"^<!-- include: _shared/(.+?) -->$")


def assemble(src_path):
    """Return the assembled prompt text for one src file (placeholders expanded)."""
    out = []
    with open(src_path, encoding="utf-8") as fh:
        text = fh.read()
    for line in text.split("\n"):
        m = PH_RE.match(line)
        if m:
            part = os.path.join(SHARED_DIR, m.group(1))
            if not os.path.exists(part):
                raise SystemExit(f"ERROR: {src_path}: missing partial _shared/{m.group(1)}")
            with open(part, encoding="utf-8") as pf:
                out.extend(pf.read().rstrip("\n").split("\n"))
        else:
            out.append(line)
    return "\n".join(out)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "assemble"
    srcs = sorted(glob.glob(os.path.join(SRC_DIR, "*.md")))
    if not srcs:
        raise SystemExit(f"ERROR: no sources in {SRC_DIR}")
    drift = False
    for src in srcs:
        name = os.path.basename(src)
        out_path = os.path.join(BASE, name)
        new = assemble(src)
        if mode == "check":
            cur = open(out_path, encoding="utf-8").read() if os.path.exists(out_path) else None
            ok = cur == new
            drift |= not ok
            print(f"  {name:22} {'OK' if ok else 'DRIFT — run assemble.py'}")
        else:
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(new)
            print(f"  wrote {name} ({len(new)} bytes)")
    if mode == "check" and drift:
        sys.exit(1)
    print("OK" if mode == "check" else "assembled")


if __name__ == "__main__":
    main()
