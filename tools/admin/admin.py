#!/usr/bin/env python3
"""Bridge-side admin client -- PLAN 2026-09-13 §2.5. Mirrors tools/feedback/feedback.py.

The Mac bridge (tools/../bridge.sh, outside the repo -- see tools/admin/BRIDGE.md) runs three
subcommands each tick against the feedback-sink Worker:

  drain-apply   GET /admin/drain, hand the queued actions to tools/admin/apply.py (which writes
                sources/registry.yml + index/admin/actions.jsonl), and stash the drained KV keys.
  ack           POST /admin/ack with the stashed keys AFTER the bridge's commit+push, then drop
                the stash. Two-phase like feedback: a failed tick never loses or double-applies an
                action, and a bad action is acked too so it can never loop.
  snapshot-push build the admin snapshot (tools/admin/snapshot.py) and PUT /admin/snapshot.

Worker creds: --worker / FEEDBACK_WORKER_URL, --token / FEEDBACK_TOKEN. Repo root: REPO (default
cwd). Every failure prints a WARN line to stderr and exits 1 -- the bridge treats each call as
non-fatal (`|| echo WARN`), so one bad tick never aborts the notification drain or the deploy heal.

Stdlib only.
"""
import argparse
import importlib.util
import json
import os
import sys
import tempfile
import urllib.request

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    spec = importlib.util.spec_from_file_location("_admin_" + name,
                                                  os.path.join(_HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


apply_mod = _load("apply")
snapshot_mod = _load("snapshot")

REPO = os.environ.get("REPO") or os.getcwd()
_ACK_STASH = os.path.join(tempfile.gettempdir(), "admin-ack.json")

# An honest, identifiable UA: Cloudflare's edge 403s the default "Python-urllib/x.y" before a
# request reaches the Worker (the same trap feedback.py documents).
_UA = "news-brief-admin-bridge/1.0 (+https://khalic-lab.github.io/claude-routines/)"


def _request(method, url, token, data=None):
    headers = {"Authorization": "Bearer %s" % token, "User-Agent": _UA}
    body = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def _creds(args):
    # A normal exception (not SystemExit) so main()'s handler turns it into a WARN + exit 1, while
    # argparse's own SystemExit (bad flags) still propagates as exit 2.
    if not args.worker or not args.token:
        raise RuntimeError("--worker/--token (or FEEDBACK_WORKER_URL/FEEDBACK_TOKEN) required")
    return args.worker.rstrip("/"), args.token


def cmd_drain_apply(args):
    worker, token = _creds(args)
    resp = _request("GET", worker + "/admin/drain", token)
    actions = resp.get("records") or resp.get("actions") or []
    actions.sort(key=lambda a: a.get("key") or "")  # §2.3: apply in key order
    keys = [a["key"] for a in actions if a.get("key")]
    results = apply_mod.apply_actions(REPO, actions)
    with open(_ACK_STASH, "w") as f:
        json.dump({"keys": keys, "worker": worker}, f)
    applied = sum(1 for r in results if r.get("result") == "applied")
    rejected = sum(1 for r in results if r.get("result") == "rejected")
    trunc = "  [TRUNCATED -- more remain]" if resp.get("truncated") else ""
    print("admin: drained %d action(s): %d applied, %d rejected; %d key(s) staged for ack%s"
          % (len(actions), applied, rejected, len(keys), trunc))


def cmd_ack(args):
    try:
        with open(_ACK_STASH) as f:
            stash = json.load(f)
    except (OSError, ValueError):
        print("admin: no staged keys to ack")
        return
    keys = stash.get("keys", [])
    if not keys:
        os.remove(_ACK_STASH)
        print("admin: no staged keys to ack")
        return
    worker = (args.worker or stash.get("worker") or "").rstrip("/")
    if not worker or not args.token:
        raise RuntimeError("--worker/--token (or env) required to ack")
    resp = _request("POST", worker + "/admin/ack", args.token, {"keys": keys})
    os.remove(_ACK_STASH)
    print("admin: acked %d key(s)" % resp.get("deleted", 0))


def cmd_snapshot_push(args):
    worker, token = _creds(args)
    snap = snapshot_mod.build_snapshot(REPO)
    resp = _request("PUT", worker + "/admin/snapshot", token, snap)
    print("admin: snapshot pushed (%d source(s), %s byte(s) stored)"
          % (len(snap["sources"]), resp.get("bytes", "?")))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_worker_args(sp):
        sp.add_argument("--worker", default=os.environ.get("FEEDBACK_WORKER_URL"))
        sp.add_argument("--token", default=os.environ.get("FEEDBACK_TOKEN"))

    d = sub.add_parser("drain-apply", help="drain queued actions and apply them to the registry")
    add_worker_args(d)
    d.set_defaults(func=cmd_drain_apply)

    k = sub.add_parser("ack", help="delete drained keys on the Worker (after commit+push)")
    add_worker_args(k)
    k.set_defaults(func=cmd_ack)

    s = sub.add_parser("snapshot-push", help="build the snapshot and PUT it to the Worker")
    add_worker_args(s)
    s.set_defaults(func=cmd_snapshot_push)

    args = p.parse_args(argv)
    try:
        args.func(args)
    except SystemExit:
        raise
    except Exception as exc:  # every failure is non-fatal to the bridge: warn + exit 1
        print("WARN: admin %s failed (non-fatal): %s" % (args.cmd, exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
