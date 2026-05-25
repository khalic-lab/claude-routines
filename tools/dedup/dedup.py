#!/usr/bin/env python3
"""Compose-time story dedup for the news-brief pipeline.

Stdlib only -- this runs inside the routine sandbox, which has no pip. It embeds
short story summaries via the embed-proxy Worker and compares them, by cosine
similarity, against the rolling in-repo index of recently-covered stories
(index/stories/*.jsonl). See ARCHITECTURE.md (sections 3-6) and the plan.

Subcommands
-----------
  check     candidates JSON -> per-candidate verdict NEW | ONGOING | REPEAT
  record    final-stories JSON -> writes index/stories/{date}-{slug}.jsonl
  backfill  decompose existing _posts/*.md -> seed the index + calibration set
  selftest  offline checks (no network): slugify, cosine, brief extraction

Embedding access (check / record / backfill):
  --worker  embed-proxy URL   (or env EMBED_WORKER_URL)
  --token   bearer token      (or env EMBED_TOKEN)

Thresholds (check):
  --t-high  REPEAT  at/above this cosine   (default 0.88)
  --t-low   ONGOING in [t-low, t-high)     (default 0.78)
  --since   window in days to compare against (default 30)

Index record schema (one JSON object per line), per ARCHITECTURE.md 5.1:
  {id, date, stream, headline, summary, url, source_domain, tier, tags,
   thread_id, first_seen_date, embedding_model, embedding:[float x1024]}
"""

import argparse
import base64
import datetime as dt
import glob
import hashlib
import json
import math
import os
import re
import struct
import sys
import tempfile
import urllib.request

REPO = os.environ.get("REPO") or os.getcwd()
INDEX_DIR = os.path.join(REPO, "index", "stories")
POSTS_DIR = os.path.join(REPO, "_posts")
EMBED_MODEL = "bge-m3"
EMBED_DIM = 1024
# Calibrated 2026-05-25 against bge-m3 on the seed index: paraphrased repeats
# scored 0.76-0.87, same-topic-but-different stories 0.59-0.65, far-novel <0.50.
# T_LOW=0.72 sits in the gap; T_HIGH=0.92 hard-drops only near-identical reruns.
T_HIGH_DEFAULT = 0.92
T_LOW_DEFAULT = 0.72
SINCE_DEFAULT = 30
KEEP_DAYS_DEFAULT = 40  # in-repo index window; older files pruned (Phase 2 archives full history)
_CACHE_PATH = os.path.join(tempfile.gettempdir(), "dedup-embcache.json")

# Daily-stream slugs we treat as briefs (mirrors _posts naming).
KNOWN_SLUGS = ("overview", "markets", "ai-ml", "cyber-papers", "weekend", "evaluator")
_FILENAME_RE = re.compile(r"(\d{4}-\d{2}-\d{2})-(.+)\.(?:md|jsonl)$")
_BULLET_RE = re.compile(r"^-\s+\*\*(.+?)\*\*\.?\s*(.*)$")
_URL_RE = re.compile(r"\]\((https?://[^)]+)\)")


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
def slugify(s, maxlen=48):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:maxlen].strip("-") or "story"


def encode_vec(v):
    """Pack a float vector as base64 float16 — ~8x smaller than JSON float text."""
    return base64.b64encode(struct.pack(f"<{len(v)}e", *v)).decode("ascii")


def decode_vec(s):
    b = base64.b64decode(s)
    return list(struct.unpack(f"<{len(b) // 2}e", b))


def cosine(a, b):
    dot = na = nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (math.sqrt(na) * math.sqrt(nb))


def first_sentence(text, maxlen=300):
    text = re.sub(r"\s+", " ", text).strip()
    m = re.search(r"(.+?[.!?])(\s|$)", text)
    out = m.group(1) if m else text
    return out[:maxlen].strip()


def embed_text(headline, summary):
    """The canonical string we embed for a story (headline carries most signal)."""
    s = (headline or "").strip()
    body = first_sentence(summary or "")
    if body and body.lower() != s.lower():
        s = f"{s}. {body}"
    return s[:400]


def source_domain(url):
    if not url:
        return None
    m = re.match(r"https?://([^/]+)/?", url)
    return m.group(1).lower().lstrip("www.") if m else None


# --------------------------------------------------------------------------- #
# embeddings (the only network dependency)
# --------------------------------------------------------------------------- #
def _load_cache():
    try:
        with open(_CACHE_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(cache):
    try:
        with open(_CACHE_PATH, "w") as f:
            json.dump(cache, f)
    except Exception:
        pass


def embed(texts, worker, token):
    """Return a list of 1024-dim vectors, one per input text. Caches by sha1(text)."""
    if not texts:
        return []
    cache = _load_cache()
    out = [None] * len(texts)
    missing_idx, missing_txt = [], []
    for i, t in enumerate(texts):
        key = hashlib.sha1(t.encode("utf-8")).hexdigest()
        if key in cache:
            out[i] = cache[key]
        else:
            missing_idx.append(i)
            missing_txt.append(t)
    if missing_txt:
        if not worker or not token:
            raise SystemExit("ERROR: embed-proxy --worker/--token (or EMBED_WORKER_URL/"
                             "EMBED_TOKEN) required to embed uncached text")
        body = json.dumps({"texts": missing_txt}).encode("utf-8")
        req = urllib.request.Request(
            worker.rstrip("/") + "/",
            data=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                # Cloudflare 403s the default Python-urllib UA in front of the
                # Worker; send a browser UA (confirmed to pass).
                "User-Agent": "Mozilla/5.0 (compatible; news-brief-dedup/1.0)",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read().decode("utf-8"))
        vecs = resp.get("embeddings")
        if not isinstance(vecs, list) or len(vecs) != len(missing_txt):
            raise SystemExit(f"ERROR: embed-proxy returned unexpected shape: {resp}")
        for j, i in enumerate(missing_idx):
            out[i] = vecs[j]
            cache[hashlib.sha1(missing_txt[j].encode("utf-8")).hexdigest()] = vecs[j]
        _save_cache(cache)
    return out


# --------------------------------------------------------------------------- #
# index io
# --------------------------------------------------------------------------- #
def _date_from_name(path):
    m = _FILENAME_RE.search(os.path.basename(path))
    return m.group(1) if m else None


def load_recent_index(since_days, as_of=None):
    """Load index records from the last `since_days` (by file date)."""
    as_of = as_of or dt.date.today()
    cutoff = as_of - dt.timedelta(days=since_days)
    records = []
    for path in sorted(glob.glob(os.path.join(INDEX_DIR, "*.jsonl"))):
        d = _date_from_name(path)
        if not d:
            continue
        try:
            fdate = dt.date.fromisoformat(d)
        except ValueError:
            continue
        if fdate < cutoff or fdate > as_of:
            continue
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("emb"):
                    rec["embedding"] = decode_vec(rec["emb"])
                    records.append(rec)
    return records


def write_index_file(date, slug, stories):
    os.makedirs(INDEX_DIR, exist_ok=True)
    path = os.path.join(INDEX_DIR, f"{date}-{slug}.jsonl")
    with open(path, "w") as f:
        for s in stories:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    return path


def prune_index(keep_days, as_of=None):
    """Delete index files older than keep_days. Returns count removed."""
    as_of = as_of or dt.date.today()
    cutoff = as_of - dt.timedelta(days=keep_days)
    removed = 0
    for path in glob.glob(os.path.join(INDEX_DIR, "*.jsonl")):
        d = _date_from_name(path)
        if not d:
            continue
        try:
            if dt.date.fromisoformat(d) < cutoff:
                os.remove(path)
                removed += 1
        except ValueError:
            continue
    return removed


# --------------------------------------------------------------------------- #
# brief decomposition (backfill + ad-hoc)
# --------------------------------------------------------------------------- #
def extract_stories(md_text):
    """Yield {headline, summary, url} per bullet, ignoring the Coverage footer."""
    stories = []
    lines = md_text.splitlines()
    i = 0
    in_footer = False
    while i < len(lines):
        line = lines[i]
        if line.startswith("#") and "coverage footer" in line.lower():
            in_footer = True
        if in_footer:
            i += 1
            continue
        m = _BULLET_RE.match(line)
        if m:
            headline = m.group(1).strip()
            body = [m.group(2).strip()]
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if not nxt.strip() or nxt.lstrip().startswith("- ") or nxt.startswith("#"):
                    break
                body.append(nxt.strip())
                j += 1
            body_text = " ".join(b for b in body if b)
            urls = _URL_RE.findall(body_text)
            stories.append({
                "headline": headline,
                "summary": first_sentence(body_text) if body_text else "",
                "url": urls[0] if urls else None,
            })
            i = j
        else:
            i += 1
    return stories


# --------------------------------------------------------------------------- #
# verdict logic (check)
# --------------------------------------------------------------------------- #
def classify(vec, recent, t_high, t_low):
    best, best_rec = 0.0, None
    for rec in recent:
        c = cosine(vec, rec["embedding"])
        if c > best:
            best, best_rec = c, rec
    if best >= t_high:
        verdict = "REPEAT"
    elif best >= t_low:
        verdict = "ONGOING"
    else:
        verdict = "NEW"
    res = {"verdict": verdict, "score": round(best, 4)}
    if best_rec and verdict != "NEW":
        res["matched"] = {
            "id": best_rec.get("id"),
            "date": best_rec.get("date"),
            "headline": best_rec.get("headline"),
            "thread_id": best_rec.get("thread_id") or best_rec.get("id"),
            "first_seen_date": best_rec.get("first_seen_date") or best_rec.get("date"),
        }
    return res


# --------------------------------------------------------------------------- #
# subcommands
# --------------------------------------------------------------------------- #
def cmd_check(args):
    with open(args.candidates) as f:
        cands = json.load(f)
    if isinstance(cands, dict) and "candidates" in cands:
        cands = cands["candidates"]
    texts = [embed_text(c.get("headline", ""), c.get("summary", "")) for c in cands]
    vecs = embed(texts, args.worker, args.token)
    recent = load_recent_index(args.since, as_of=_parse_date(args.as_of))
    results = []
    for c, v in zip(cands, vecs):
        r = classify(v, recent, args.t_high, args.t_low)
        r["headline"] = c.get("headline", "")
        if "id" in c:
            r["id"] = c["id"]
        results.append(r)
    out = {"window_days": args.since, "compared_against": len(recent),
           "t_high": args.t_high, "t_low": args.t_low, "results": results}
    print(json.dumps(out, ensure_ascii=False, indent=2))


def cmd_record(args):
    with open(args.stories) as f:
        stories = json.load(f)
    if isinstance(stories, dict) and "stories" in stories:
        stories = stories["stories"]
    date = args.date
    slug = args.slug
    texts = [embed_text(s.get("headline", ""), s.get("summary", "")) for s in stories]
    vecs = embed(texts, args.worker, args.token)
    records = []
    for s, v in zip(stories, vecs):
        hid = s.get("id") or f"{date}-{slug}-{slugify(s.get('headline',''))}"
        records.append({
            "id": hid,
            "date": date,
            "stream": slug,
            "headline": s.get("headline", ""),
            "summary": s.get("summary", ""),
            "url": s.get("url"),
            "source_domain": s.get("source_domain") or source_domain(s.get("url")),
            "tier": s.get("tier"),
            "tags": s.get("tags", []),
            "thread_id": s.get("thread_id") or hid,
            "first_seen_date": s.get("first_seen_date") or date,
            "embedding_model": EMBED_MODEL,
            "emb": encode_vec(v),
        })
    path = write_index_file(date, slug, records)
    removed = prune_index(args.keep_days, as_of=_parse_date(args.date))
    print(f"wrote {len(records)} stories -> {path}"
          + (f" (pruned {removed} old index file(s))" if removed else ""))


def cmd_backfill(args):
    paths = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md")))
    total = 0
    written = 0
    for path in paths:
        m = _FILENAME_RE.search(os.path.basename(path))
        if not m:
            continue
        date, slug = m.group(1), m.group(2)
        if slug == "evaluator":
            continue  # evaluator briefs are meta-analysis, not news stories
        if args.slugs and slug not in args.slugs:
            continue
        out_path = os.path.join(INDEX_DIR, f"{date}-{slug}.jsonl")
        if os.path.exists(out_path) and not args.force:
            continue
        with open(path) as f:
            stories = extract_stories(f.read())
        if not stories:
            continue
        texts = [embed_text(s["headline"], s["summary"]) for s in stories]
        vecs = embed(texts, args.worker, args.token) if not args.no_embed else [[] for _ in texts]
        records = []
        for s, v in zip(stories, vecs):
            hid = f"{date}-{slug}-{slugify(s['headline'])}"
            records.append({
                "id": hid, "date": date, "stream": slug,
                "headline": s["headline"], "summary": s["summary"], "url": s["url"],
                "source_domain": source_domain(s["url"]), "tier": None, "tags": [],
                "thread_id": hid, "first_seen_date": date,
                "embedding_model": EMBED_MODEL if not args.no_embed else None,
                "emb": encode_vec(v) if v else None,
            })
        write_index_file(date, slug, records)
        written += 1
        total += len(records)
        print(f"  {date}-{slug}: {len(records)} stories")
    print(f"backfill done: {total} stories across {written} briefs -> {INDEX_DIR}")


def cmd_selftest(_args):
    assert slugify("Bilaterals III: roadmap!") == "bilaterals-iii-roadmap"
    assert abs(cosine([1, 0, 0], [1, 0, 0]) - 1.0) < 1e-9
    assert abs(cosine([1, 0], [0, 1])) < 1e-9
    v = [0.1, -0.2, 0.333, 0.999, -0.5]
    rt = decode_vec(encode_vec(v))
    assert len(rt) == len(v) and all(abs(a - b) < 1e-2 for a, b in zip(v, rt)), rt
    sample = (
        "## World\n"
        "- **Bilaterals III reaches Parliament.** The Federal Council's dispatch "
        "was signed on 2 March 2026. [via snippet] — [_SWI_, May 2026](https://swissinfo.ch/x)\n"
        "- **Markets close firm.** SMI ended at 13,446. [Google Finance](https://g.co/y)\n\n"
        "## Coverage footer\n- **Not a story.** ignore me [x](https://z.co/q)\n"
    )
    stories = extract_stories(sample)
    assert len(stories) == 2, stories
    assert stories[0]["headline"].startswith("Bilaterals III")
    assert stories[0]["url"] == "https://swissinfo.ch/x"
    assert source_domain("https://www.aljazeera.com/x") == "aljazeera.com"
    assert embed_text("Headline here", "Headline here. extra").startswith("Headline here")
    print("selftest OK")


def _parse_date(s):
    return dt.date.fromisoformat(s) if s else None


# --------------------------------------------------------------------------- #
def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_embed_args(sp):
        sp.add_argument("--worker", default=os.environ.get("EMBED_WORKER_URL"))
        sp.add_argument("--token", default=os.environ.get("EMBED_TOKEN"))

    c = sub.add_parser("check", help="classify candidates against the recent index")
    c.add_argument("--candidates", required=True)
    c.add_argument("--since", type=int, default=SINCE_DEFAULT)
    c.add_argument("--t-high", type=float, default=T_HIGH_DEFAULT, dest="t_high")
    c.add_argument("--t-low", type=float, default=T_LOW_DEFAULT, dest="t_low")
    c.add_argument("--as-of", default=None, help="YYYY-MM-DD; defaults to today")
    add_embed_args(c)
    c.set_defaults(func=cmd_check)

    r = sub.add_parser("record", help="write final stories to the index")
    r.add_argument("--stories", required=True)
    r.add_argument("--date", required=True)
    r.add_argument("--slug", required=True)
    r.add_argument("--keep-days", type=int, default=KEEP_DAYS_DEFAULT, dest="keep_days",
                   help="prune index files older than this after recording")
    add_embed_args(r)
    r.set_defaults(func=cmd_record)

    b = sub.add_parser("backfill", help="seed the index from existing _posts/*.md")
    b.add_argument("--slugs", nargs="*", default=None, help="limit to these stream slugs")
    b.add_argument("--force", action="store_true", help="overwrite existing index files")
    b.add_argument("--no-embed", action="store_true", help="extract only; empty vectors (debug)")
    add_embed_args(b)
    b.set_defaults(func=cmd_backfill)

    s = sub.add_parser("selftest", help="offline logic checks (no network)")
    s.set_defaults(func=cmd_selftest)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
