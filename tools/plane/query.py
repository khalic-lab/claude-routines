#!/usr/bin/env python3
"""Phase-2 analytical plane, serverless edition — the ledger IS the database.

No Postgres, no service, no sync step, no state: every invocation folds the committed story
ledger in-process (tools/store/store.py materialize(), the canonical folding) and answers both
query families over it — brute-force cosine for vector search (~1.6k x 1024-dim = ~0.2s, no
index needed at this scale) and plain groupbys for the graph/relational side. A fresh clone
answers every query with zero setup; stdlib only.

  search <text> [--k 10]     semantic search (embeds the query via the embed-proxy Worker,
                             same bge-m3 model the stories carry — apples to apples)
  related <sid|url> [--k 10] nearest stories to an existing one (thread edges labeled)
  thread <sid|thread_id>     a developing story line, oldest -> newest
  beats [--days 30]          coverage map: stories per beat per week
  entities [--days 90]       the entity graph's top nodes (populates as writers emit entities)
  sources [--days 30]        domain concentration, tier mix
  stats                      corpus totals

Only `search` touches the network (embed-proxy; the same committed low-value token DEDUP.md
carries — override via EMBED_TOKEN/EMBED_WORKER_URL env). If the corpus ever outgrows
brute force (~100x today), the upgrade path is a DuckDB/sqlite-vec FILE, not a server.
"""
import argparse
import base64
import datetime as dt
import importlib.util
import json
import math
import os
import struct
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
EMBED_URL = os.environ.get("EMBED_WORKER_URL", "https://embed-proxy.khalic-lab.workers.dev")
EMBED_TOKEN = os.environ.get("EMBED_TOKEN",
    "b4bd10fc46e70315205b5aa4a4352d6d79f750d13cc4ef960928f8e6da5aae8a")

_store_spec = importlib.util.spec_from_file_location("_store", os.path.join(TOOLS, "store", "store.py"))
_store = importlib.util.module_from_spec(_store_spec)
_store_spec.loader.exec_module(_store)


# --- corpus ---------------------------------------------------------------------------------
def decode_emb(rec):
    """Ledger payloads carry packed base64 float16 (`emb`) or a raw float list (`embedding`,
    pre-2026-06 records). Returns a list of floats or None."""
    if isinstance(rec.get("embedding"), list) and rec["embedding"]:
        return [float(x) for x in rec["embedding"]]
    emb = rec.get("emb")
    if not emb:
        return None
    try:
        raw = base64.b64decode(emb)
        return list(struct.unpack("<%de" % (len(raw) // 2), raw))
    except Exception:
        return None


def load_corpus(root):
    """[{sid, rec, vec, norm}] for every ledger story (vec/norm None when undecodable)."""
    stories = _store.materialize(days=36500, root=root)["stories"]
    corpus = []
    for sid, rec in stories.items():
        vec = decode_emb(rec)
        norm = math.sqrt(sum(x * x for x in vec)) if vec else None
        corpus.append({"sid": sid, "rec": rec, "vec": vec, "norm": norm or None})
    return corpus


def cosine_rank(corpus, qvec, k, exclude_sids=()):
    qnorm = math.sqrt(sum(x * x for x in qvec)) or 1.0
    scored = []
    for c in corpus:
        if not c["vec"] or c["sid"] in exclude_sids:
            continue
        dot = sum(a * b for a, b in zip(qvec, c["vec"]))
        scored.append((dot / (qnorm * c["norm"]), c))
    scored.sort(key=lambda t: -t[0])
    return scored[:k]


def find_story(corpus, key):
    for c in corpus:
        r = c["rec"]
        if c["sid"] == key or r.get("url") == key or key in (r.get("legacy_ids") or []):
            return c
    return None


def embed(text):
    req = urllib.request.Request(
        EMBED_URL.rstrip("/") + "/", method="POST",
        data=json.dumps({"texts": [text]}).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + EMBED_TOKEN,
                 # Cloudflare 403s the default Python-urllib UA (same as dedup.py)
                 "User-Agent": "Mozilla/5.0 (compatible; news-brief-plane/1.0)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.loads(r.read())
    vecs = payload.get("embeddings")
    if not isinstance(vecs, list) or not vecs:
        raise SystemExit("embed-proxy returned no embeddings: %s" % list(payload))
    return vecs[0]


# --- output helpers -------------------------------------------------------------------------
def table(rows, headers):
    if not rows:
        print("(no rows)")
        return
    rows = [[("" if v is None else str(v)) for v in row] for row in rows]
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
    print("  ".join(h.ljust(widths[i]) for i, h in enumerate(headers)))
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print("  ".join(r[i].ljust(widths[i]) for i in range(len(headers))))


def _date(rec):
    return rec.get("date") or ""


def _since(days):
    return (dt.date.today() - dt.timedelta(days=days)).isoformat()


# --- commands -------------------------------------------------------------------------------
def cmd_search(corpus, args):
    hits = cosine_rank(corpus, embed(args.text), args.k)
    table([[_date(c["rec"])[5:], c["rec"].get("stream"), (c["rec"].get("headline") or "")[:76],
            "%.3f" % sim] for sim, c in hits],
          ["date", "stream", "headline", "sim"])


def cmd_related(corpus, args):
    anchor = find_story(corpus, args.key)
    if not anchor or not anchor["vec"]:
        raise SystemExit("no story (with a vector) matches %r" % args.key)
    hits = cosine_rank(corpus, anchor["vec"], args.k, exclude_sids={anchor["sid"]})
    at = anchor["rec"].get("thread_id")
    table([[_date(c["rec"])[5:], c["rec"].get("stream"), (c["rec"].get("headline") or "")[:70],
            "%.3f" % sim, "same-thread" if at and c["rec"].get("thread_id") == at else ""]
           for sim, c in hits],
          ["date", "stream", "headline", "sim", "edge"])


def cmd_thread(corpus, args):
    anchor = find_story(corpus, args.key)
    tid = (anchor["rec"].get("thread_id") if anchor else None) or args.key
    members = sorted((c for c in corpus if c["rec"].get("thread_id") == tid),
                     key=lambda c: _date(c["rec"]))
    table([[_date(c["rec"]), c["rec"].get("stream"), c["rec"].get("importance"),
            (c["rec"].get("headline") or "")[:84], c["rec"].get("event_date")]
           for c in members],
          ["date", "stream", "imp", "headline", "event_date"])


def cmd_beats(corpus, args):
    since = _since(args.days)
    counts = {}
    for c in corpus:
        r = c["rec"]
        if _date(r) < since:
            continue
        week = _date(r)[:10]
        week = (dt.date.fromisoformat(week) - dt.timedelta(days=dt.date.fromisoformat(week).weekday())).isoformat()[5:]
        for beat in (r.get("topics") or []):
            counts[(week, beat)] = counts.get((week, beat), 0) + 1
    rows = sorted(counts.items(), key=lambda kv: (kv[0][0], -kv[1]), reverse=True)
    table([[w, b, n] for (w, b), n in rows], ["week", "beat", "stories"])


def cmd_entities(corpus, args):
    since = _since(args.days)
    agg = {}
    for c in corpus:
        r = c["rec"]
        if _date(r) < since:
            continue
        for e in (r.get("entities") or []):
            a = agg.setdefault(e, {"n": 0, "first": _date(r), "last": _date(r), "streams": set()})
            a["n"] += 1
            a["first"] = min(a["first"], _date(r))
            a["last"] = max(a["last"], _date(r))
            a["streams"].add(r.get("stream") or "")
    rows = sorted(agg.items(), key=lambda kv: (-kv[1]["n"], kv[1]["last"]))[:30]
    if not rows:
        print("(no entities yet — writers emit them from the next fire onward; DEDUP.md Step C)")
        return
    table([[e, a["n"], a["first"], a["last"], "/".join(sorted(a["streams"]))] for e, a in rows],
          ["entity", "stories", "first", "last", "streams"])


def cmd_sources(corpus, args):
    since = _since(args.days)
    agg = {}
    for c in corpus:
        r = c["rec"]
        if _date(r) < since or not r.get("source_domain"):
            continue
        a = agg.setdefault(r["source_domain"], {"n": 0, "streams": set(), "tiers": set()})
        a["n"] += 1
        a["streams"].add(r.get("stream") or "")
        if r.get("tier"):
            a["tiers"].add(r["tier"])
    rows = sorted(agg.items(), key=lambda kv: -kv[1]["n"])[:25]
    table([[d, a["n"], len(a["streams"]), "/".join(sorted(a["tiers"]))] for d, a in rows],
          ["source_domain", "stories", "streams", "tiers"])


def cmd_stats(corpus, args):
    threads = {}
    for c in corpus:
        tid = c["rec"].get("thread_id")
        if tid:
            threads[tid] = threads.get(tid, 0) + 1
    # materialize() folds votes per story into {"up": n, "down": n, "last_reason": ...}
    votes = sum((c["rec"].get("feedback") or {}).get("up", 0) +
                (c["rec"].get("feedback") or {}).get("down", 0) for c in corpus)
    dates = sorted(_date(c["rec"]) for c in corpus if _date(c["rec"]))
    table([[len(corpus), sum(1 for c in corpus if c["vec"]),
            sum(1 for n in threads.values() if n > 1), votes,
            dates[0] if dates else "", dates[-1] if dates else ""]],
          ["stories", "with_vectors", "threads_developing", "votes", "since", "through"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=os.path.dirname(TOOLS))
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search");   s.add_argument("text"); s.add_argument("--k", type=int, default=10); s.set_defaults(fn=cmd_search)
    r = sub.add_parser("related");  r.add_argument("key");  r.add_argument("--k", type=int, default=10); r.set_defaults(fn=cmd_related)
    t = sub.add_parser("thread");   t.add_argument("key");  t.set_defaults(fn=cmd_thread)
    b = sub.add_parser("beats");    b.add_argument("--days", type=int, default=30);  b.set_defaults(fn=cmd_beats)
    e = sub.add_parser("entities"); e.add_argument("--days", type=int, default=90);  e.set_defaults(fn=cmd_entities)
    o = sub.add_parser("sources");  o.add_argument("--days", type=int, default=30);  o.set_defaults(fn=cmd_sources)
    st = sub.add_parser("stats");   st.set_defaults(fn=cmd_stats)
    args = ap.parse_args(argv)
    corpus = load_corpus(args.root)
    args.fn(corpus, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
