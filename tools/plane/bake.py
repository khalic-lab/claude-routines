#!/usr/bin/env python3
"""Bake the analytical-plane artifact from the story ledger and (optionally) push it to the
embed-proxy Worker's /plane/ingest, making the plane queryable from the ROUTINE SANDBOX
(embed-proxy is on the env_018 allowlist; a new hostname would not be).

Artifact format (mirrored by tools/embed-proxy/src/worker.js parseArtifact):
  bytes 0-7   magic "PLANEv1\\0"
  bytes 8-11  uint32 LE meta_len
  then        meta JSON utf8: { n, dim, ts, norms: [n], stories: [n compact records] }
  then        n * dim float32 LE vectors, row-major, same order as meta.stories

Deterministic given the ledger (except the `ts` stamp); stories sorted by sid. Records without
a decodable vector are kept (queryable by thread/entities) with norm 0 and a zero vector row.
Non-fatal by convention: --push failures exit 0 with a warning — the plane is analytics, an
outage must never cost an edition.

Usage: bake.py [--root .] [--out plane.bin] [--push] [--worker URL] [--token TOK]
"""
import argparse
import importlib.util
import json
import math
import os
import struct
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
MAGIC = b"PLANEv1\x00"
DIM = 1024

_q_spec = importlib.util.spec_from_file_location("_plane_q", os.path.join(HERE, "query.py"))
_q = importlib.util.module_from_spec(_q_spec)
_q_spec.loader.exec_module(_q)


def compact(rec):
    """The per-story record shipped in the artifact — lean on purpose (the Worker parses this
    JSON on cold isolates; keep it in the hundreds of KB, not MB)."""
    out = {
        "sid": rec.get("_sid"),
        "date": rec.get("date"),
        "stream": rec.get("stream"),
        "headline": (rec.get("headline") or "")[:120],
        "url": rec.get("url"),
        "thread_id": rec.get("thread_id"),
    }
    for key in ("topics", "entities", "legacy_ids"):
        if rec.get(key):
            out[key] = rec[key]
    for key in ("importance", "event_date", "source_domain", "tier"):
        if rec.get(key) is not None:
            out[key] = rec[key]
    return out


def bake(root, ts):
    corpus = _q.load_corpus(root)
    corpus.sort(key=lambda c: c["sid"])
    stories, norms, rows = [], [], []
    zero = [0.0] * DIM
    for c in corpus:
        rec = dict(c["rec"], _sid=c["sid"])
        stories.append(compact(rec))
        vec = c["vec"] if (c["vec"] and len(c["vec"]) == DIM) else None
        norms.append(round(math.sqrt(sum(x * x for x in vec)), 6) if vec else 0)
        rows.append(vec or zero)
    meta = {"n": len(stories), "dim": DIM, "ts": ts, "norms": norms, "stories": stories}
    meta_bytes = json.dumps(meta, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    vec_bytes = b"".join(struct.pack("<%df" % DIM, *row) for row in rows)
    return MAGIC + struct.pack("<I", len(meta_bytes)) + meta_bytes + vec_bytes, len(stories)


def push(artifact, worker, token):
    req = urllib.request.Request(
        worker.rstrip("/") + "/plane/ingest", method="POST", data=artifact,
        headers={"Content-Type": "application/octet-stream", "Authorization": "Bearer " + token,
                 "User-Agent": "Mozilla/5.0 (compatible; news-brief-plane/1.0)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=os.path.dirname(TOOLS))
    ap.add_argument("--out", default=None, help="also write the artifact to this path")
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--worker", default=os.environ.get("EMBED_WORKER_URL", _q.EMBED_URL))
    ap.add_argument("--token", default=os.environ.get("EMBED_TOKEN", _q.EMBED_TOKEN))
    args = ap.parse_args(argv)

    import datetime as dt
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    artifact, n = bake(args.root, ts)
    print("[plane] baked %d stories, %.1f MB" % (n, len(artifact) / 1e6), flush=True)
    if args.out:
        with open(args.out, "wb") as fh:
            fh.write(artifact)
        print("[plane] wrote %s" % args.out)
    if args.push:
        try:
            resp = push(artifact, args.worker, args.token)
            print("[plane] pushed -> %s (%s stories server-side)" % (args.worker, resp.get("stories")))
        except Exception as exc:  # non-fatal: analytics must never cost an edition
            print("[plane] push FAILED (non-fatal): %s" % exc, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
