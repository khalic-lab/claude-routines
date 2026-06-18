#!/usr/bin/env python3
"""Reader-feedback helper for the news-brief pipeline.

Stdlib only. Three subcommands:

  add     append one feedback record locally (manual / override / v0 baseline).
  drain   GET the feedback-sink Worker /drain, append NEW records (dedup by id) to
          feedback/{YYYY-MM}.jsonl, and stash the drained KV keys for `ack`.
  ack     POST the stashed keys to the Worker /ack (delete them) AFTER commit+push.

The bridge runs `drain` before its commit step (so the new feedback/*.jsonl lands in the
same "Drained N" commit) and `ack` after a successful push. Two-phase delete-on-ack means
a missed/failed tick never loses or double-commits a record. Append is idempotent (skips
ids already on disk), so a re-drain before ack is harmless.

Worker creds (drain/ack):  --worker / env FEEDBACK_WORKER_URL,  --token / env FEEDBACK_TOKEN

Record schema (feedback/{YYYY-MM}.jsonl, one JSON object per line):
  {id, ts, reader, brief, story_id, vote(+1|-1), reason, surface, source_domain, consumed}
`consumed` is flipped true by the Weekly Evaluator when a record is folded into a patch
proposal — see feedback/FEEDBACK.md. Writers never read these files directly; they read the
human-gated reader-profile.md / reader-profile/source-weights.yml.
"""

import argparse
import datetime as dt
import glob
import json
import os
import sys
import tempfile
import urllib.request
import uuid

REPO = os.environ.get("REPO") or os.getcwd()
FEEDBACK_DIR = os.path.join(REPO, "feedback")
_ACK_STASH = os.path.join(tempfile.gettempdir(), "feedback-ack.json")


def _month_path(ts):
    """feedback/{YYYY-MM}.jsonl for an ISO timestamp (bucket by the event's month)."""
    return os.path.join(FEEDBACK_DIR, f"{ts[:7]}.jsonl")


def _existing_ids():
    ids = set()
    for path in glob.glob(os.path.join(FEEDBACK_DIR, "*.jsonl")):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("id"):
                    ids.add(rec["id"])
    return ids


def _normalize(rec):
    """Fill defaults so every stored record has the full schema."""
    return {
        "id": rec.get("id") or str(uuid.uuid4()),
        "ts": rec.get("ts") or dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "reader": rec.get("reader") or "rafael",
        "brief": rec.get("brief"),
        "story_id": rec.get("story_id"),
        "vote": rec.get("vote"),
        "reason": rec.get("reason", "") or "",
        "surface": rec.get("surface") or "web",
        "source_domain": rec.get("source_domain"),
        "consumed": bool(rec.get("consumed", False)),
    }


def _append(records):
    """Append normalized records to their month files, skipping ids already on disk.
    Returns the count actually written."""
    if not records:
        return 0
    os.makedirs(FEEDBACK_DIR, exist_ok=True)
    seen = _existing_ids()
    written = 0
    handles = {}
    try:
        for raw in records:
            rec = _normalize(raw)
            if rec["id"] in seen:
                continue
            seen.add(rec["id"])
            path = _month_path(rec["ts"])
            fh = handles.get(path) or handles.setdefault(path, open(path, "a"))
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            written += 1
    finally:
        for fh in handles.values():
            fh.close()
    return written


# Cloudflare's edge 403s the default "Python-urllib/x.y" UA before the request reaches the
# Worker (verified 2026-06-18). Send an honest, identifiable UA so drain/ack get through.
_UA = "news-brief-feedback-bridge/1.0 (+https://khalic-lab.github.io/claude-routines/)"


def _request(url, token, data=None):
    headers = {"Authorization": f"Bearer {token}", "User-Agent": _UA}
    if data is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers,
                                 method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def cmd_add(args):
    rec = _normalize({
        "brief": args.brief, "vote": args.vote, "reason": args.reason or "",
        "story_id": args.story_id, "surface": args.surface, "source_domain": args.source_domain,
    })
    n = _append([rec])
    print(f"appended {n} record -> feedback/{rec['ts'][:7]}.jsonl" if n
          else "duplicate id, nothing written")


def cmd_drain(args):
    if not args.worker or not args.token:
        raise SystemExit("ERROR: --worker/--token (or FEEDBACK_WORKER_URL/FEEDBACK_TOKEN) required")
    resp = _request(args.worker.rstrip("/") + "/drain", args.token)
    records = resp.get("records", [])
    keys = [r["key"] for r in records if r.get("key")]
    written = _append([{k: v for k, v in r.items() if k != "key"} for r in records])
    # Stash the drained keys so `ack` deletes them only after a successful commit+push.
    with open(_ACK_STASH, "w") as f:
        json.dump({"keys": keys, "worker": args.worker, "ts": dt.datetime.now().isoformat()}, f)
    print(f"drained {len(records)} record(s) ({written} new) from the Worker; "
          f"{len(keys)} key(s) staged for ack"
          + ("  [TRUNCATED — more remain]" if resp.get("truncated") else ""))


def cmd_ack(args):
    try:
        with open(_ACK_STASH) as f:
            stash = json.load(f)
    except (OSError, json.JSONDecodeError):
        print("no staged keys to ack")
        return
    keys = stash.get("keys", [])
    if not keys:
        print("no staged keys to ack")
        return
    worker = args.worker or stash.get("worker")
    if not worker or not args.token:
        raise SystemExit("ERROR: --worker/--token (or env) required to ack")
    resp = _request(worker.rstrip("/") + "/ack", args.token, {"keys": keys})
    os.remove(_ACK_STASH)
    print(f"acked {resp.get('deleted', 0)} key(s)")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_worker_args(sp):
        sp.add_argument("--worker", default=os.environ.get("FEEDBACK_WORKER_URL"))
        sp.add_argument("--token", default=os.environ.get("FEEDBACK_TOKEN"))

    a = sub.add_parser("add", help="append one feedback record locally")
    a.add_argument("--brief", required=True, help="post slug, e.g. 2026-06-07-overview")
    a.add_argument("--vote", type=int, required=True, choices=(1, -1))
    a.add_argument("--reason", default="")
    a.add_argument("--story-id", default=None, dest="story_id")
    a.add_argument("--surface", default="cli")
    a.add_argument("--source-domain", default=None, dest="source_domain")
    a.set_defaults(func=cmd_add)

    d = sub.add_parser("drain", help="pull queued records from the Worker into feedback/*.jsonl")
    add_worker_args(d)
    d.set_defaults(func=cmd_drain)

    k = sub.add_parser("ack", help="delete drained keys on the Worker (after commit+push)")
    add_worker_args(k)
    k.set_defaults(func=cmd_ack)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
