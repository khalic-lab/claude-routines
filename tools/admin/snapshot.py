#!/usr/bin/env python3
"""Build the admin-page snapshot -- PLAN 2026-09-13 §2.4.

The admin page holds nothing private in its public HTML; every number it shows comes from this
snapshot, which the bridge builds each tick and PUTs to the feedback-sink Worker's KV. The page then
GETs it after passkey sign-in. The snapshot folds four read-only views: the source registry (one row
per domain with its last lifecycle event), the measured usage fold (tools/usage/fold.py -- null when
that module has not landed yet), the recent applied/rejected admin actions, and the pending evaluator
registry proposals (listed only; the human gate stays manual).

Stdlib only, no network. Read-only: nothing here writes to the repo.
"""
import argparse
import datetime
import importlib.util
import json
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REG_PATH = os.path.normpath(os.path.join(_HERE, "..", "sources", "registry.py"))
_spec = importlib.util.spec_from_file_location("_admin_snapshot_registry", _REG_PATH)
registry = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(registry)

ACTIONS_RECENT_LIMIT = 50


def _now_iso():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _git_head(root):
    """The local HEAD sha for the snapshot's provenance line (== origin/main after the bridge's
    push, which runs before snapshot-push), or None when git is unavailable."""
    try:
        proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                              capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    out = proc.stdout.strip()
    return out if proc.returncode == 0 and out else None


def _load_registry(root):
    path = registry.registry_path(root)
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        text = f.read()
    if not text.strip():
        return {}
    reg = registry.yaml_load(text)
    return reg if isinstance(reg, dict) else {}


def _sources(root):
    reg = _load_registry(root)
    out = []
    for domain in sorted(reg):
        rec = reg[domain]
        if not isinstance(rec, dict):
            continue
        lifecycle = rec.get("lifecycle") or []
        last = lifecycle[-1] if lifecycle else None
        last_event = None
        if isinstance(last, dict):
            last_event = {"date": last.get("date"), "event": last.get("event"),
                          "note": last.get("note")}
        out.append({
            "domain": domain,
            "class": rec.get("class"),
            "tier": rec.get("tier"),
            "status": rec.get("status"),
            "reach": rec.get("reach"),
            "streams": rec.get("streams") or [],
            "last_cited": rec.get("last_cited"),
            "last_event": last_event,
        })
    return out


def _usage(root):
    """The usage fold, or None when tools/usage/fold.py is absent (S1 lands in parallel) or fails.
    fold.py follows the repo's sibling-import convention (`import pricing`), so its own directory
    must be on sys.path before it is exec'd; a broad except keeps a broken fold from taking down the
    whole snapshot -- usage is optional, nothing in the publish path depends on it."""
    fold_path = os.path.join(root, "tools", "usage", "fold.py")
    if not os.path.exists(fold_path):
        return None
    usage_dir = os.path.dirname(fold_path)
    inserted = False
    try:
        if usage_dir not in sys.path:
            sys.path.insert(0, usage_dir)
            inserted = True
        spec = importlib.util.spec_from_file_location("_admin_usage_fold", fold_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.fold(root)
    except Exception:
        return None
    finally:
        # Restore sys.path so a usage sibling (`pricing`) can't shadow a top-level module for the
        # rest of the process -- harmless in the one-shot snapshot-push, a footgun if imported.
        if inserted:
            try:
                sys.path.remove(usage_dir)
            except ValueError:
                pass


def _actions_recent(root):
    path = os.path.join(root, "index", "admin", "actions.jsonl")
    if not os.path.exists(path):
        return []
    lines = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(line)
    out = []
    for line in lines[-ACTIONS_RECENT_LIMIT:]:
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    out.reverse()  # newest first
    return out


def _proposal_meta(path):
    """Read the top-level `applied` and `date` scalars from a proposal .yml without the registry
    loader -- those files carry `>-` block scalars the loader cannot parse, so scan the header lines
    only (up to `patches:`)."""
    applied, date = None, None
    with open(path) as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("patches:"):
                break
            if line[:1] not in (" ", "\t", "#") and ":" in stripped:
                key, _, val = stripped.partition(":")
                key, val = key.strip(), val.strip()
                if key == "applied":
                    applied = val.lower() in ("true", "yes")
                elif key == "date":
                    date = val.strip('"').strip("'") or None
    return applied, date


def _proposals_pending(root):
    """Evaluator registry proposals not yet applied. `applied: true` in the header excludes a file;
    a missing/false flag counts it pending (the flags are known to drift, so absence means pending).
    Date comes from the header `date:` or, failing that, the filename registry-YYYY-MM-DD.yml."""
    pdir = os.path.join(root, "proposals")
    if not os.path.isdir(pdir):
        return []
    out = []
    for fname in sorted(os.listdir(pdir)):
        if not (fname.startswith("registry-") and fname.endswith(".yml")):
            continue
        applied, date = _proposal_meta(os.path.join(pdir, fname))
        if applied is True:
            continue
        if not date:
            stem = fname[len("registry-"):-len(".yml")]
            date = stem if len(stem) == 10 else None
        out.append({"file": "proposals/" + fname, "date": date})
    out.sort(key=lambda p: p["date"] or "", reverse=True)  # newest first
    return out


def build_snapshot(root, as_of=None):
    """Assemble the §2.4 snapshot. `as_of` fixes `generated` for deterministic tests; production
    passes nothing and gets the current UTC time."""
    return {
        "generated": as_of or _now_iso(),
        "head": _git_head(root),
        "sources": _sources(root),
        "usage": _usage(root),
        "actions_recent": _actions_recent(root),
        "proposals_pending": _proposals_pending(root),
    }


def main(argv=None):
    p = argparse.ArgumentParser(description="Build the admin-page snapshot JSON.")
    p.add_argument("--root", default=".")
    p.add_argument("--out", default=None, help="write the snapshot here instead of stdout")
    args = p.parse_args(argv)
    snap = build_snapshot(args.root)
    text = json.dumps(snap, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w") as f:
            f.write(text + "\n")
        print("snapshot: wrote %d source(s) to %s" % (len(snap["sources"]), args.out))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
