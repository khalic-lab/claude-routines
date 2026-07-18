#!/usr/bin/env python3
"""Phase-2 plane sync: story ledger -> local Postgres/pgvector (ARCHITECTURE §3/§5.2).

Reads ONLY committed repo data — the append-only ledger under index/ledger/ — via
tools/store/store.py's own `materialize()` (the canonical event folding; this tool never
re-implements it), plus a direct scan for publish/feedback events. Embeddings ride along in the
ledger's seen payloads (base64 float16, decoded here), so no re-embedding and no git archaeology:
a fresh database rebuilds from a fresh clone.

Full idempotent upsert every run (the corpus is ~1.6k stories — a full resync is seconds), so
there is no incremental-state file to corrupt. Applies schema.sql first (IF NOT EXISTS).

Stdlib only; talks to Postgres by piping COPY streams to `psql` (no driver dependency).

Usage: sync.py [--root .] [--db claude_routines] [--days 36500] [--dry-run]
"""
import argparse
import base64
import importlib.util
import json
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
PSQL_FALLBACK = "/opt/homebrew/opt/postgresql@17/bin"  # brew keg-only install (this Mac)

_store_spec = importlib.util.spec_from_file_location("_store", os.path.join(TOOLS, "store", "store.py"))
_store = importlib.util.module_from_spec(_store_spec)
_store_spec.loader.exec_module(_store)


def psql_bin():
    from shutil import which
    if which("psql"):
        return "psql"
    cand = os.path.join(PSQL_FALLBACK, "psql")
    return cand if os.path.exists(cand) else "psql"


def decode_emb(rec):
    """Ledger payloads carry either packed base64 float16 (`emb`) or a raw float list
    (`embedding`, pre-2026-06 records). Returns a list of floats or None."""
    if isinstance(rec.get("embedding"), list) and rec["embedding"]:
        return [float(x) for x in rec["embedding"]]
    emb = rec.get("emb")
    if not emb:
        return None
    try:
        raw = base64.b64decode(emb)
        n = len(raw) // 2
        return list(struct.unpack("<%de" % n, raw))
    except Exception:
        return None


# --- COPY encoding (text format): escape \, tab, newline; \N for NULL -----------------------
def tsv(v):
    if v is None:
        return r"\N"
    s = str(v)
    return s.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")


def pg_array(items):
    if not items:
        return "{}"
    out = []
    for it in items:
        s = str(it).replace("\\", "\\\\").replace('"', '\\"')
        out.append('"%s"' % s)
    return "{%s}" % ",".join(out)


def pg_vector(floats):
    return "[" + ",".join("%.6g" % f for f in floats) + "]"


def story_row(sid, rec):
    """One stories-table COPY row from a materialized ledger record. Column order must match
    the COPY statement in build_script()."""
    emb = decode_emb(rec)
    return "\t".join([
        tsv(sid),
        tsv(pg_array(rec.get("legacy_ids") or [])),
        tsv(rec.get("date")),
        tsv(rec.get("stream") or ""),
        tsv(pg_array(rec.get("streams") or ([rec.get("stream")] if rec.get("stream") else []))),
        tsv(pg_array(rec.get("editions") or [])),
        tsv(rec.get("headline") or ""),
        tsv(rec.get("summary")),
        tsv(rec.get("url")),
        tsv(rec.get("source_domain")),
        tsv(rec.get("tier")),
        tsv(pg_array(rec.get("tags") or [])),
        tsv(pg_array(rec.get("topics") or [])),
        tsv(rec.get("importance")),
        tsv(pg_array(rec.get("entities") or [])),
        tsv(pg_array(rec.get("affiliations") or [])),
        tsv(rec.get("display_body")),
        tsv(rec.get("why")),
        tsv(rec.get("thread_id")),
        tsv(rec.get("first_seen_date")),
        tsv(rec.get("event_date")),
        tsv(rec.get("status")),
        tsv(rec.get("embedding_model")),
        tsv(pg_vector(emb)) if emb else r"\N",
    ])


def scan_events(root):
    """(publishes, feedback) straight from the ledger files — the two event kinds
    materialize() folds away. Deduped by natural key; malformed lines skipped."""
    publishes, feedback = {}, {}
    ledger = os.path.join(root, "index", "ledger")
    if not os.path.isdir(ledger):
        return [], []
    for name in sorted(os.listdir(ledger)):
        if not name.endswith(".jsonl"):
            continue
        with open(os.path.join(ledger, name), encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except ValueError:
                    continue
                if ev.get("ev") == "publish" and ev.get("id") and ev.get("edition"):
                    key = (ev["id"], ev["edition"])
                    if key not in publishes or (ev.get("ts") or "") < publishes[key].get("ts", "~"):
                        publishes[key] = ev
                elif ev.get("ev") == "feedback" and ev.get("fb_id"):
                    feedback.setdefault(ev["fb_id"], ev)  # first occurrence wins; fold.py dedupes upstream
    return list(publishes.values()), list(feedback.values())


def build_script(stories, publishes, feedback, root):
    """One psql script: schema + staged COPY + upserts, single transaction."""
    parts = []
    parts.append(open(os.path.join(HERE, "schema.sql"), encoding="utf-8").read())
    parts.append("BEGIN;")
    parts.append("""
CREATE TEMP TABLE stage_stories (LIKE stories INCLUDING DEFAULTS) ON COMMIT DROP;
COPY stage_stories (sid, legacy_ids, date, stream, streams, editions, headline, summary, url,
  source_domain, tier, tags, topics, importance, entities, affiliations, display_body, why,
  thread_id, first_seen_date, event_date, status, embedding_model, embedding) FROM stdin;""")
    for sid, rec in sorted(stories.items()):
        parts.append(story_row(sid, rec))
    parts.append("\\.")
    parts.append("""
INSERT INTO stories SELECT * FROM stage_stories
ON CONFLICT (sid) DO UPDATE SET
  legacy_ids = EXCLUDED.legacy_ids, date = EXCLUDED.date, stream = EXCLUDED.stream,
  streams = EXCLUDED.streams, editions = EXCLUDED.editions, headline = EXCLUDED.headline,
  summary = EXCLUDED.summary, url = EXCLUDED.url, source_domain = EXCLUDED.source_domain,
  tier = EXCLUDED.tier, tags = EXCLUDED.tags, topics = EXCLUDED.topics,
  importance = EXCLUDED.importance, entities = EXCLUDED.entities,
  affiliations = EXCLUDED.affiliations, display_body = EXCLUDED.display_body,
  why = EXCLUDED.why, thread_id = EXCLUDED.thread_id,
  first_seen_date = EXCLUDED.first_seen_date, event_date = EXCLUDED.event_date,
  status = EXCLUDED.status, embedding_model = EXCLUDED.embedding_model,
  embedding = COALESCE(EXCLUDED.embedding, stories.embedding);

CREATE TEMP TABLE stage_pub (sid text, edition text, ts timestamptz, stream text) ON COMMIT DROP;
COPY stage_pub FROM stdin;""")
    for ev in publishes:
        edition = ev["edition"]
        stream = edition[11:] if len(edition) > 11 else None
        parts.append("\t".join([tsv(ev["id"]), tsv(edition), tsv(ev.get("ts")), tsv(stream)]))
    parts.append("\\.")
    parts.append("""
INSERT INTO publishes SELECT * FROM stage_pub
ON CONFLICT (sid, edition) DO UPDATE SET ts = LEAST(publishes.ts, EXCLUDED.ts);

CREATE TEMP TABLE stage_fb (fb_id text, sid text, brief text, vote int, reason text,
  reader text, surface text, ts timestamptz) ON COMMIT DROP;
COPY stage_fb FROM stdin;""")
    for ev in feedback:
        parts.append("\t".join([
            tsv(ev["fb_id"]), tsv(ev.get("id")), tsv(ev.get("brief")), tsv(ev.get("vote")),
            tsv(ev.get("reason")), tsv(ev.get("reader")), tsv(ev.get("surface")), tsv(ev.get("ts")),
        ]))
    parts.append("\\.")
    parts.append("""
INSERT INTO feedback SELECT * FROM stage_fb
ON CONFLICT (fb_id) DO NOTHING;
COMMIT;
SELECT (SELECT count(*) FROM stories)   AS stories,
       (SELECT count(*) FROM stories WHERE embedding IS NOT NULL) AS with_vectors,
       (SELECT count(*) FROM publishes) AS publishes,
       (SELECT count(*) FROM feedback)  AS feedback,
       (SELECT count(*) FROM threads WHERE stories > 1) AS multi_story_threads;""")
    return "\n".join(parts)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=os.path.dirname(TOOLS))
    ap.add_argument("--db", default="claude_routines")
    ap.add_argument("--days", type=int, default=36500, help="ledger window (default: everything)")
    ap.add_argument("--dry-run", action="store_true", help="print row counts, touch no database")
    args = ap.parse_args(argv)

    stories = _store.materialize(days=args.days, root=args.root)["stories"]
    publishes, feedback = scan_events(args.root)
    print("[plane] materialized %d stories, %d publish events, %d feedback events"
          % (len(stories), len(publishes), len(feedback)), flush=True)
    if args.dry_run:
        no_emb = sum(1 for r in stories.values() if not decode_emb(r))
        print("[plane] DRY-RUN — %d stories lack a decodable embedding" % no_emb)
        return 0

    script = build_script(stories, publishes, feedback, args.root)
    proc = subprocess.run([psql_bin(), "-d", args.db, "-v", "ON_ERROR_STOP=1", "-q", "-f", "-"],
                          input=script, capture_output=True, text=True)
    sys.stdout.write(proc.stdout)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        print("[plane] sync FAILED (psql exit %d)" % proc.returncode)
        return 1
    print("[plane] sync OK -> database %r" % args.db)
    return 0


if __name__ == "__main__":
    sys.exit(main())
