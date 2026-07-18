#!/usr/bin/env python3
"""Phase-2 plane query CLI — the showcase queries over the local pgvector database.

  search <text> [--k 10]     semantic search (embeds the query via the embed-proxy Worker,
                             same bge-m3 model the stories carry — apples to apples)
  related <sid|url> [--k 10] nearest stories to an existing one (excl. itself + its thread)
  thread <sid|thread_id>     a developing story line, oldest -> newest
  beats [--days 30]          coverage map: stories per beat per week
  entities [--days 90]       the entity graph's top nodes (populates as writers emit entities)
  sources [--days 30]        domain concentration, tier mix
  stats                      corpus totals

Stdlib only; shells out to psql. Needs no bearer except `search` (embed-proxy token — the same
committed low-value token DEDUP.md carries; override via EMBED_TOKEN/EMBED_WORKER_URL env).
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PSQL_FALLBACK = "/opt/homebrew/opt/postgresql@17/bin"
EMBED_URL = os.environ.get("EMBED_WORKER_URL", "https://embed-proxy.khalic-lab.workers.dev")
EMBED_TOKEN = os.environ.get("EMBED_TOKEN",
    "b4bd10fc46e70315205b5aa4a4352d6d79f750d13cc4ef960928f8e6da5aae8a")


def psql(db, sql, params=None):
    from shutil import which
    exe = "psql" if which("psql") else os.path.join(PSQL_FALLBACK, "psql")
    cmd = [exe, "-d", db, "-v", "ON_ERROR_STOP=1"]
    for i, p in enumerate(params or []):
        cmd += ["-v", "p%d=%s" % (i, p)]
    cmd += ["-c", sql]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        sys.exit(1)
    sys.stdout.write(proc.stdout)


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


def qlit(s):
    return "'" + str(s).replace("'", "''") + "'"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", default="claude_routines")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search");   s.add_argument("text"); s.add_argument("--k", type=int, default=10)
    r = sub.add_parser("related");  r.add_argument("key");  r.add_argument("--k", type=int, default=10)
    t = sub.add_parser("thread");   t.add_argument("key")
    b = sub.add_parser("beats");    b.add_argument("--days", type=int, default=30)
    e = sub.add_parser("entities"); e.add_argument("--days", type=int, default=90)
    o = sub.add_parser("sources");  o.add_argument("--days", type=int, default=30)
    sub.add_parser("stats")
    args = ap.parse_args(argv)

    if args.cmd == "search":
        vec = "[" + ",".join("%.6g" % v for v in embed(args.text)) + "]"
        psql(args.db, """
SELECT to_char(date,'MM-DD') AS date, stream, left(headline, 76) AS headline,
       round((1 - (embedding <=> %s::vector))::numeric, 3) AS sim
FROM stories WHERE embedding IS NOT NULL
ORDER BY embedding <=> %s::vector LIMIT %d;""" % (qlit(vec), qlit(vec), args.k))

    elif args.cmd == "related":
        key = qlit(args.key)
        psql(args.db, """
WITH anchor AS (
  SELECT sid, thread_id, embedding FROM stories
  WHERE sid = %s OR url = %s OR %s = ANY(legacy_ids) LIMIT 1)
SELECT to_char(s.date,'MM-DD') AS date, s.stream, left(s.headline, 70) AS headline,
       round((1 - (s.embedding <=> a.embedding))::numeric, 3) AS sim,
       CASE WHEN s.thread_id = a.thread_id THEN 'same-thread' ELSE '' END AS edge
FROM stories s, anchor a
WHERE s.sid <> a.sid AND s.embedding IS NOT NULL
ORDER BY s.embedding <=> a.embedding LIMIT %d;""" % (key, key, key, args.k))

    elif args.cmd == "thread":
        key = qlit(args.key)
        psql(args.db, """
SELECT to_char(s.date,'YYYY-MM-DD') AS date, s.stream, s.importance AS imp,
       left(s.headline, 84) AS headline, s.event_date
FROM stories s
WHERE s.thread_id = COALESCE(
        (SELECT thread_id FROM stories WHERE sid = %s OR url = %s LIMIT 1), %s)
ORDER BY s.date;""" % (key, key, key))

    elif args.cmd == "beats":
        psql(args.db, """
SELECT to_char(date_trunc('week', date), 'MM-DD') AS week, unnest(topics) AS beat, count(*)
FROM stories WHERE date >= current_date - %d
GROUP BY 1, 2 ORDER BY 1 DESC, 3 DESC;""" % args.days)

    elif args.cmd == "entities":
        psql(args.db, """
SELECT entity, count(*) AS stories, min(date) AS first, max(date) AS last,
       array_agg(DISTINCT stream) AS streams
FROM entity_stories WHERE date >= current_date - %d
GROUP BY entity ORDER BY stories DESC, last DESC LIMIT 30;""" % args.days)

    elif args.cmd == "sources":
        psql(args.db, """
SELECT source_domain, count(*) AS stories, count(DISTINCT stream) AS streams,
       string_agg(DISTINCT tier, '/') AS tiers
FROM stories WHERE date >= current_date - %d AND source_domain IS NOT NULL
GROUP BY source_domain ORDER BY stories DESC LIMIT 25;""" % args.days)

    elif args.cmd == "stats":
        psql(args.db, """
SELECT (SELECT count(*) FROM stories) AS stories,
       (SELECT count(*) FROM stories WHERE embedding IS NOT NULL) AS with_vectors,
       (SELECT count(*) FROM threads WHERE stories > 1) AS threads_developing,
       (SELECT count(*) FROM publishes) AS publishes,
       (SELECT count(*) FROM feedback) AS votes,
       (SELECT min(date) FROM stories) AS since,
       (SELECT max(date) FROM stories) AS through;""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
