#!/usr/bin/env python3
"""Story store — append-only event ledger + materializer (SPIKE-2026-07-07 §3.1).

Identity: st-{sha1(norm_url)[:12]} — a pure function of the canonical URL.
Primary store: index/ledger/{YYYY-MM-DD}.jsonl, partitioned by UTC *ingest* day
(never the event's own ts), union-merged via .gitattributes. The materialized
snapshot (index/ledger/.materialized.json) is derived, never committed.

Materializer invariants: (a) events sorted by (ts, actor) before folding;
(b) exact-duplicate events fold once; (c) seen events sharing a norm_url fold
into one story (unions + min first_seen / max updated, later non-empty scalar
wins); (d) feedback last-write-wins per (reader, id, surface), vote 0 clears.

CLI:
  store.py id <url>
  store.py append [--root R]            # event JSON on stdin; validates shape
  store.py materialize [--root R] [--days N]
  store.py selftest                     # invariants + two-branch union-merge test
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# list fields union'd when seen events fold (SPIKE §3.1 invariant c)
_UNION_FIELDS = ("legacy_ids", "editions", "streams", "alt_urls")

# per-type required keys beyond the (ev, ts, actor) envelope; feedback "id" is
# deliberately NOT required — unresolved feedback appends with id=null
_EVENT_KEYS = {
    "seen": ("story",),
    "update": ("id", "rev", "fields"),
    "publish": ("id", "edition", "fields"),
    "status": ("id", "status"),
    "feedback": ("fb_id", "vote"),
    "notify": ("id", "channel"),
}


def norm_url(url):
    """Canonicalize for the feed↔index join: scheme/www/fragment/utm-insensitive.
    MUST stay byte-identical in behavior to tools/build_stories_feed.py::norm_url."""
    if not url:
        return None
    u = url.strip().split("#", 1)[0]
    u = re.sub(r"^https?://(www\.)?", "", u, flags=re.I)
    if "?" in u:
        base, q = u.split("?", 1)
        keep = [p for p in q.split("&") if p and not p.lower().startswith(("utm_", "ref=", "fbclid"))]
        u = base + ("?" + "&".join(keep) if keep else "")
    return u.rstrip("/").lower()


def story_id(url):
    nu = norm_url(url)
    if not nu:
        raise ValueError("story_id needs a URL (urlless records use the legacy fallback id)")
    return "st-" + hashlib.sha1(nu.encode("utf-8")).hexdigest()[:12]


def validate_event(ev):
    if not isinstance(ev, dict):
        raise ValueError("event must be a JSON object")
    for k in ("ev", "ts", "actor"):
        if not ev.get(k):
            raise ValueError("event missing %r" % k)
    kind = ev["ev"]
    if kind not in _EVENT_KEYS:
        raise ValueError("unknown ev type %r" % kind)
    for k in _EVENT_KEYS[kind]:
        if k not in ev or ev[k] is None:  # vote=0 is valid; absent/null is not
            raise ValueError("%s event missing %r" % (kind, k))
    if kind == "seen" and (not isinstance(ev["story"], dict) or not ev["story"].get("id")):
        raise ValueError("seen event needs a story object with an id")
    return ev


def append_event(event, root=None):
    validate_event(event)
    root = root or REPO_ROOT
    day = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")  # ingest day, not event ts
    path = os.path.join(root, "index", "ledger", day + ".jsonl")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return path


def _load_events(root, days):
    """Windowed read of ledger files, exact-duplicate lines dropped (invariant b),
    sorted by (ts, actor) (invariant a). Unparseable lines are skipped: union merge
    guarantees no line is lost but not that every line is ours."""
    ledger = os.path.join(root, "index", "ledger")
    if not os.path.isdir(ledger):
        return []
    cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).strftime("%Y-%m-%d")
    events, dup = [], set()
    for name in sorted(os.listdir(ledger)):
        stem = name[:-len(".jsonl")]
        if (not name.endswith(".jsonl")
                or not re.match(r"^\d{4}-\d{2}-\d{2}$", stem) or stem < cutoff):
            continue
        with open(os.path.join(ledger, name), encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except ValueError:
                    continue
                key = json.dumps(ev, sort_keys=True, ensure_ascii=False)
                if key in dup:
                    continue
                dup.add(key)
                events.append(ev)
    events.sort(key=lambda e: (e.get("ts") or "", e.get("actor") or ""))
    return events


def _assign(rec, k, v):
    # copy containers so folded records never alias event payloads
    rec[k] = list(v) if isinstance(v, list) else dict(v) if isinstance(v, dict) else v


def _fold_fields(rec, fields):
    for k, v in fields.items():
        if k in _UNION_FIELDS:
            cur = rec.setdefault(k, [])
            for item in v or []:
                if item not in cur:
                    cur.append(item)
        elif v or k not in rec:  # a later EMPTY value never clobbers an earlier non-empty one
            _assign(rec, k, v)


def _fold(events):
    stories, fb_by_sid = {}, {}
    for ev in events:
        kind = ev.get("ev")
        if kind == "seen":
            story = ev.get("story") or {}
            url = story.get("url")
            # re-derive from url so same-norm_url genesis events fold (invariant c);
            # urlless (backfill fallback) records keep their recorded id
            sid = story_id(url) if url else story.get("id")
            if not sid:
                continue
            rec = stories.setdefault(sid, {"id": sid})
            for k, v in story.items():
                if k == "id":
                    continue
                if k == "first_seen":
                    if v:
                        rec[k] = min(rec[k], v) if rec.get(k) else v
                elif k == "updated":
                    if v:
                        rec[k] = max(rec[k], v) if rec.get(k) else v
                else:
                    _fold_fields(rec, {k: v})
        elif kind in ("update", "publish", "status"):
            rec = stories.get(ev.get("id"))
            if rec is None:
                continue
            if kind == "update":
                _fold_fields(rec, ev.get("fields") or {})
                if isinstance(ev.get("rev"), int):
                    rec["revision"] = max(rec.get("revision") or 0, ev["rev"])
            elif kind == "publish":
                _fold_fields(rec, ev.get("fields") or {})
                eds = rec.setdefault("editions", [])
                if ev.get("edition") and ev["edition"] not in eds:
                    eds.append(ev["edition"])
            else:
                rec["status"] = ev.get("status")
                if ev.get("superseded_by"):
                    rec["superseded_by"] = ev["superseded_by"]
            ts = ev.get("ts") or ""
            if ts > (rec.get("updated") or ""):
                rec["updated"] = ts
        elif kind == "feedback":
            if ev.get("id"):
                fb_by_sid.setdefault(ev["id"], []).append(ev)
        # notify (and unknown future types) carry no folded state

    by_legacy, by_url = {}, {}
    for sid, rec in stories.items():
        votes, last_reason = {}, None
        for fb in fb_by_sid.get(sid, ()):  # already in (ts, actor) order: LWW
            votes[(fb.get("reader"), fb.get("surface"))] = fb.get("vote") or 0
            if fb.get("reason"):
                last_reason = fb["reason"]
        rec["feedback"] = {"up": sum(1 for v in votes.values() if v > 0),
                           "down": sum(1 for v in votes.values() if v < 0),
                           "last_reason": last_reason}
        for lid in rec.get("legacy_ids") or []:
            by_legacy[lid] = sid
        for u in [rec.get("url")] + list(rec.get("alt_urls") or []):
            nu = norm_url(u)
            if nu:
                by_url[nu] = sid
    return {"stories": stories, "by_legacy": by_legacy, "by_url": by_url}


def materialize(days=60, root=None):
    return _fold(_load_events(root or REPO_ROOT, days))


# --------------------------------------------------------------------------- #
# selftest
# --------------------------------------------------------------------------- #
def _selftest_union_merge(check):
    """Two-branch git merge in a tempdir: union merge must engage (no conflict,
    both appended lines kept, both visible to materialize)."""
    import shutil
    import subprocess
    import tempfile
    if shutil.which("git") is None:
        print("selftest: union-merge            skipped (no git)")
        return
    repo = tempfile.mkdtemp(prefix="store-selftest-git-")
    env = {**os.environ,
           "GIT_AUTHOR_NAME": "selftest", "GIT_AUTHOR_EMAIL": "selftest@local",
           "GIT_COMMITTER_NAME": "selftest", "GIT_COMMITTER_EMAIL": "selftest@local"}

    def git(*args, ok_fail=False):
        p = subprocess.run(["git"] + list(args), cwd=repo, capture_output=True,
                           text=True, env=env)
        if p.returncode != 0 and not ok_fail:
            raise RuntimeError("git %s failed: %s" % (" ".join(args), p.stderr.strip()))
        return p

    try:
        day = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
        rel = os.path.join("index", "ledger", day + ".jsonl")
        path = os.path.join(repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(os.path.join(repo, ".gitattributes"), "w") as f:
            f.write("index/ledger/*.jsonl merge=union\n")
        git("init", "-q")
        git("checkout", "-q", "-b", "main")
        git("config", "commit.gpgsign", "false")
        open(path, "a").close()
        git("add", ".gitattributes", rel)
        git("commit", "-q", "-m", "base")

        def seen(tag, hour):
            url = "https://example.com/union-%s" % tag
            sid = story_id(url)
            return sid, {"ev": "seen", "ts": "%sT0%d:00:00Z" % (day, hour), "actor": tag,
                         "story": {"id": sid, "url": url, "headline": tag.upper(),
                                   "summary": "S", "status": "candidate",
                                   "first_seen": "%sT0%d:00:00Z" % (day, hour),
                                   "updated": "%sT0%d:00:00Z" % (day, hour),
                                   "legacy_ids": [], "editions": [], "streams": [tag],
                                   "tags": [], "topics": []}}

        sid_a, ev_a = seen("a", 6)
        sid_b, ev_b = seen("b", 7)
        git("checkout", "-q", "-b", "branch-a")
        with open(path, "a") as f:
            f.write(json.dumps(ev_a, ensure_ascii=False) + "\n")
        git("add", rel)
        git("commit", "-q", "-m", "a")
        git("checkout", "-q", "main")
        git("checkout", "-q", "-b", "branch-b")
        with open(path, "a") as f:
            f.write(json.dumps(ev_b, ensure_ascii=False) + "\n")
        git("add", rel)
        git("commit", "-q", "-m", "b")
        git("checkout", "-q", "branch-a")
        merge = git("merge", "--no-edit", "branch-b", ok_fail=True)
        check("union-merge-no-conflict", merge.returncode == 0)
        with open(path) as f:
            lines = [ln for ln in f.read().splitlines() if ln.strip()]
        check("union-merge-both-lines", len(lines) == 2)
        snap = materialize(root=repo)
        check("union-merge-materialize",
              sid_a in snap["stories"] and sid_b in snap["stories"])
    finally:
        shutil.rmtree(repo, ignore_errors=True)


def selftest():
    import shutil
    import tempfile
    fails = []

    def check(name, cond):
        print("selftest: %-26s %s" % (name, "ok" if cond else "FAIL"))
        if not cond:
            fails.append(name)

    def seen(url, ts, actor="news", **extra):
        story = {"id": story_id(url), "url": url, "headline": "H " + ts, "summary": "S",
                 "status": "candidate", "first_seen": ts, "updated": ts,
                 "legacy_ids": [], "editions": [], "streams": [actor], "tags": [], "topics": []}
        story.update(extra)
        return {"ev": "seen", "ts": ts, "actor": actor, "story": story}

    check("url-equivalence",
          story_id("https://www.Example.com/a/?utm_source=x#f") == story_id("http://example.com/a"))

    root = tempfile.mkdtemp(prefix="store-selftest-")
    try:
        # (a) sort: later-ts update wins regardless of physical append order
        u1 = "https://example.com/selftest-sort"
        sid1 = story_id(u1)
        append_event(seen(u1, "2026-01-01T00:00:00Z"), root=root)
        append_event({"ev": "update", "ts": "2026-01-02T10:00:00Z", "actor": "news",
                      "id": sid1, "rev": 3, "fields": {"status": "dropped"}}, root=root)
        append_event({"ev": "update", "ts": "2026-01-02T09:00:00Z", "actor": "news",
                      "id": sid1, "rev": 2, "fields": {"status": "developing"}}, root=root)
        # (d) feedback LWW per (reader, surface)
        fb = {"ev": "feedback", "ts": "2026-01-03T00:00:00Z", "actor": "bridge", "id": sid1,
              "fb_id": "fb-st-1", "vote": 1, "reason": "", "reader": "r", "surface": "web",
              "brief": "x", "raw_story_id": sid1}
        append_event(fb, root=root)
        append_event({**fb, "ts": "2026-01-03T01:00:00Z", "fb_id": "fb-st-2",
                      "vote": -1, "reason": "meh"}, root=root)
        # (b) exact duplicate publish folds once
        u2 = "https://example.com/selftest-dup"
        sid2 = story_id(u2)
        append_event(seen(u2, "2026-01-01T00:00:00Z"), root=root)
        pub = {"ev": "publish", "ts": "2026-01-02T00:00:00Z", "actor": "news", "id": sid2,
               "edition": "2026-01-02-news",
               "fields": {"display_body": "B", "why": "W", "importance": 2, "status": "settled"}}
        append_event(pub, root=root)
        append_event(pub, root=root)
        # (c) same-norm_url seen events fold into one story
        u3a = "https://www.example.com/selftest-fold?utm_source=x"
        u3b = "https://example.com/selftest-fold/"
        append_event(seen(u3a, "2026-01-01T00:00:00Z", editions=["2026-01-01-news"],
                          display_body="Earlier body."), root=root)
        append_event(seen(u3b, "2026-01-02T00:00:00Z", actor="ai-ml",
                          editions=["2026-01-02-ai-ml"], display_body=""), root=root)

        snap = materialize(root=root)
        r1, r2 = snap["stories"][sid1], snap["stories"][sid2]
        r3 = snap["stories"][story_id(u3a)]
        check("sort-by-ts-actor", r1["status"] == "dropped")
        check("feedback-lww", r1["feedback"] == {"up": 0, "down": 1, "last_reason": "meh"})
        check("dedupe-exact-duplicate", r2["editions"].count("2026-01-02-news") == 1)
        check("url-fold-unions",
              story_id(u3a) == story_id(u3b)
              and set(r3["editions"]) == {"2026-01-01-news", "2026-01-02-ai-ml"}
              and r3["first_seen"] == "2026-01-01T00:00:00Z"
              and r3["updated"] == "2026-01-02T00:00:00Z"
              and r3["display_body"] == "Earlier body.")
        check("by-url-map", snap["by_url"].get(norm_url(u3b)) == story_id(u3a))
    finally:
        shutil.rmtree(root, ignore_errors=True)

    _selftest_union_merge(check)
    print("selftest: %s" % ("PASS" if not fails else "FAIL (%s)" % ", ".join(fails)))
    return 0 if not fails else 1


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv=None):
    p = argparse.ArgumentParser(prog="store.py", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    p_id = sub.add_parser("id", help="print the story id for a URL")
    p_id.add_argument("url")
    p_ap = sub.add_parser("append", help="validate + append one event (JSON on stdin)")
    p_ap.add_argument("--root", default=REPO_ROOT)
    p_mat = sub.add_parser("materialize", help="fold the ledger into a snapshot")
    p_mat.add_argument("--root", default=REPO_ROOT)
    p_mat.add_argument("--days", type=int, default=60)
    sub.add_parser("selftest", help="run invariant + union-merge self-checks")
    args = p.parse_args(argv)

    if args.cmd == "id":
        print(story_id(args.url))
        return 0
    if args.cmd == "append":
        try:
            event = json.loads(sys.stdin.read())
            append_event(event, root=args.root)
        except (ValueError, OSError) as e:
            print("append: %s" % e, file=sys.stderr)
            return 1
        return 0
    if args.cmd == "materialize":
        events = _load_events(args.root, args.days)
        snap = _fold(events)
        out = os.path.join(args.root, "index", "ledger", ".materialized.json")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(snap, f, ensure_ascii=False)
        print("materialized %d stories / %d events" % (len(snap["stories"]), len(events)))
        return 0
    if args.cmd == "selftest":
        return selftest()
    return 2


if __name__ == "__main__":
    sys.exit(main())
