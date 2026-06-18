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
  lint      post-compose date checks on a brief (weekday-vs-date consistency)
  selftest  offline checks (no network): slugify, cosine, brief extraction

`check` decides each candidate in precedence order (see decide_verdict):
  1. exact-source match (same canonical URL / arXiv id) -> REPEAT, cosine-independent;
  2. cosine vs the recent index -> REPEAT / ONGOING / NEW.
Because cosine cannot separate a restated rerun from a genuinely-developing story
(both span ~0.6-0.95), most repeat-suppression is the (1) deterministic exact-source
layer plus the DEDUP.md ONGOING-defaults-to-drop policy — NOT the cosine threshold. See
the calibration note at T_HIGH_DEFAULT and DEDUP-DIAGNOSIS-2026-05-31.md.

Embedding access (check / record / backfill):
  --worker  embed-proxy URL   (or env EMBED_WORKER_URL)
  --token   bearer token      (or env EMBED_TOKEN)

Thresholds (check):
  --t-high           REPEAT  at/above this cosine     (default 0.945)
  --t-low            ONGOING in [t-low, t-high)       (default 0.72)
  --since            window in days to compare against (default 30)

Index record schema (one JSON object per line), per ARCHITECTURE.md 5.1:
  {id, date, stream, headline, summary, url, source_domain, tier, tags,
   thread_id, first_seen_date, event_date, embedding_model, embedding:[float x1024]}

`date` is the brief/compose date, `first_seen_date` the earliest brief in the thread
(first COVERAGE), and `event_date` (nullable, ISO 8601 reduced precision YYYY |
YYYY-MM | YYYY-MM-DD) when the described thing actually HAPPENED — three distinct
dates a story carries (cf. GDELT SQLDATE vs DATEADDED). event_date is writer-supplied
at day precision when known, else deterministically derived from an arXiv id
(YYYY-MM submission month), else null.
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
# Calibrated 2026-05-31 against a hand-labelled gold set of cross-day story pairs.
# Finding: cosine does NOT separate TRUE-REPEAT from TRUE-ONGOING — both span the
# whole useful range (REPEAT 0.635-0.952, ONGOING 0.605-0.944), because mechanical
# daily series (FX/futures/index snapshots) embed near-identically yet each carries
# a genuinely new dated number. T_HIGH=0.945 sits just above the ONGOING ceiling
# (0.9443): zero ONGOING->REPEAT and zero DISTINCT->REPEAT, so it auto-drops only the
# clearly-identical near-verbatim reruns. The ~84% of real repeats that fall in the
# ONGOING band are NOT caught by the threshold (no defensible t_high can, without
# silently dropping developing stories) — they are handled by the tightened
# DEDUP.md Step B ONGOING-defaults-to-drop policy. T_LOW=0.72 unchanged: its boundary
# errors are all cheap (never silently drop a story).
T_HIGH_DEFAULT = 0.945
T_LOW_DEFAULT = 0.72
# Thread continuity (autolink in cmd_record) is deliberately conservative. The same
# gold set shows DISTINCT story pairs reach cosine 0.914 (mechanical daily snapshots —
# different trading sessions that embed near-identically), so inheriting a thread
# anywhere in the inseparable [T_LOW, 0.92] band would stamp a false thread_id +
# "[ongoing since …]" onto ~1-in-4 genuinely distinct stories. AUTOLINK_MIN sits ABOVE
# that observed DISTINCT ceiling: we link only on a near-identical match. A missed link
# merely starts a fresh thread (harmless); a false link corrupts provenance (not).
AUTOLINK_MIN_DEFAULT = 0.93
# (Snapshot-genre collapse was removed 2026-06-18 with the Markets stream — it existed
# only to suppress recurring FX/index/session market snapshots, which no longer exist.)
SINCE_DEFAULT = 30
KEEP_DAYS_DEFAULT = 40  # in-repo index window; older files pruned (Phase 2 archives full history)
_CACHE_PATH = os.path.join(tempfile.gettempdir(), "dedup-embcache.json")

# Daily-stream slugs we treat as briefs (mirrors _posts naming).
KNOWN_SLUGS = ("overview", "ai-ml", "cyber-papers", "weekend", "evaluator")
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
# deterministic exact-source match (zero-judgment REPEAT)
# --------------------------------------------------------------------------- #
# arXiv id shape YYMM.NNNNN with MM a real month (01-12) so we don't match prices
# like "13.452" or versions. Optional arxiv:/abs//pdf/ prefix, optional vN suffix.
_ARXIV_RE = re.compile(r"(?:arxiv:|abs/|pdf/)?\b(\d{2}(?:0[1-9]|1[0-2])\.\d{4,5})(?:v\d+)?\b", re.I)


def arxiv_ids(*texts):
    """Extract arXiv ids (e.g. 2605.18753) from any of the given strings."""
    ids = set()
    for t in texts:
        if t:
            ids.update(m.group(1) for m in _ARXIV_RE.finditer(t))
    return ids


def canon_url(url):
    """Canonical key for exact-match dedup: lowercased host (www. stripped) + path,
    no scheme/query/fragment/trailing-slash. None if not a URL."""
    if not url:
        return None
    m = re.match(r"https?://([^/?#]+)([^?#]*)", url.strip(), re.I)
    if not m:
        return None
    host = m.group(1).lower()
    if host.startswith("www."):
        host = host[4:]
    return host + re.sub(r"/+$", "", m.group(2))


def exact_keys(headline, summary, url):
    """Zero-judgment identity keys for a story: its canonical URL and any arXiv ids
    in its headline/summary/url. An exact key match across days = same primary source
    = same story, regardless of cosine (the reworded-headline case cosine can miss)."""
    keys = set()
    cu = canon_url(url)
    # Require a path: a bare host (swebench.com, a company blog index, a living
    # leaderboard) is not a unique story identity and would falsely collide distinct
    # stories that happen to cite the same homepage. Only permalink-style URLs key.
    if cu and "/" in cu:
        keys.add("url:" + cu)
    for aid in arxiv_ids(headline, summary, url):
        keys.add("arxiv:" + aid)
    return keys


def arxiv_event_date(*texts):
    """Coarse, deterministic event date (YYYY-MM, the submission month) from an arXiv
    id, which encodes YYMM; the day is not in the id, so month precision is the most we
    can get offline. None if no arXiv id present. The only event date derivable with no
    network — used to seed `event_date` for ID-bearing records (record / backfill)."""
    ids = sorted(arxiv_ids(*texts))
    if not ids:
        return None
    yymm = ids[0][:4]  # e.g. "2606" from 2606.06333
    return f"20{yymm[:2]}-{yymm[2:]}"


def _distinct_paper(cand, match):
    """True when `cand` is a specific arXiv paper that `match` is NOT about — two
    different papers on the same narrow topic. This is the identity check behind the
    SASA/SoftSAE false merge (2026-06-06-weekend.md): arXiv 2606.06333 was threaded onto
    a distinct May SAE paper and tagged "[ongoing since 2026-05-14]". (That link was
    writer-SUPPLIED, not cosine — the two embed at only 0.71 — so the real fix is
    validating writer threads in cmd_record; this guard also covers the autolink path.)

    Deliberately restricted to arXiv — the genre where same-topic distinct artifacts get
    conflated and an arXiv id is an unambiguous paper identity. CVE/product "sagas" are
    left to editorial judgment (a differing CVE on the same product is genuinely
    ambiguous to thread, and id-incidental stories like a project update that merely
    mentions a CVE must not be broken).

    A candidate with no arXiv id -> False (news/CVE threading untouched). The same
    arXiv id present in both -> False (a genuine same-paper update still threads;
    arXiv v1/v2 share a base id). cand/match are story dicts (headline/summary/url)."""
    cand_ids = arxiv_ids(cand.get("headline"), cand.get("summary"), cand.get("url"))
    if not cand_ids:
        return False
    match_ids = arxiv_ids(match.get("headline"), match.get("summary"), match.get("url"))
    return cand_ids.isdisjoint(match_ids)


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
            "summary": best_rec.get("summary"),
            "url": best_rec.get("url"),
            "thread_id": best_rec.get("thread_id") or best_rec.get("id"),
            "first_seen_date": best_rec.get("first_seen_date") or best_rec.get("date"),
            "event_date": best_rec.get("event_date"),
        }
    return res


def autolink(vec, recent, min_sim=None, cand=None):
    """Thread continuity for `record`: inherit (thread_id, first_seen_date) from a
    recent story ONLY on a near-identical match (cosine >= AUTOLINK_MIN_DEFAULT);
    else None. Empty/missing index -> None.

    Gated well ABOVE the REPEAT/ONGOING publish thresholds on purpose: cosine cannot
    separate same-story from distinct-story in the [T_LOW, 0.92] band (DISTINCT pairs
    reach 0.914), so threading there would falsely merge distinct stories. Conservative
    by design — a missed link just starts a fresh thread. Makes continuity automatic so
    it no longer depends on the writer carrying DEDUP.md Step C by hand. Pure (no I/O),
    offline-testable.

    When `cand` (the story dict being recorded) is given, the arXiv distinct-paper
    guard (_distinct_paper) suppresses the link if the candidate is a specific paper the
    best match is not about — even above the cosine gate. Defense-in-depth against a
    cosine-driven distinct-paper merge (the observed SASA/SoftSAE merge was actually
    writer-supplied, validated separately in cmd_record). cmd_record always passes cand."""
    if not recent:
        return None
    min_sim = AUTOLINK_MIN_DEFAULT if min_sim is None else min_sim
    best, best_rec = 0.0, None
    for rec in recent:
        c = cosine(vec, rec["embedding"])
        if c > best:
            best, best_rec = c, rec
    if best_rec is None or best < min_sim:
        return None
    if cand is not None and _distinct_paper(cand, best_rec):
        return None
    return (best_rec.get("thread_id") or best_rec.get("id"),
            best_rec.get("first_seen_date") or best_rec.get("date"))


# --------------------------------------------------------------------------- #
# date checks (lint) — deterministic, offline
# --------------------------------------------------------------------------- #
_ISO_PARTIAL_RE = re.compile(r"^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?$")
_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun",
     "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
_WDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
_WDAYS_FULL = ["Monday", "Tuesday", "Wednesday", "Thursday",
               "Friday", "Saturday", "Sunday"]
_MONTH_ALT = "(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
_WD_ALT = "(?:mon|tue|wed|thu|fri|sat|sun)"
# Four adjacency forms binding a weekday to a day+month (named groups so extraction is
# uniform regardless of order). Catches "Wednesday 11 June", "Wed, June 11",
# "11 June (Wednesday)", "June 11, Wednesday".
_WD_PATTERNS = [
    re.compile(rf"\b(?P<wd>{_WD_ALT})[a-z]*\.?,?\s+(?P<day>\d{{1,2}})(?:st|nd|rd|th)?\s+(?P<mon>{_MONTH_ALT})[a-z]*", re.I),
    re.compile(rf"\b(?P<wd>{_WD_ALT})[a-z]*\.?,?\s+(?P<mon>{_MONTH_ALT})[a-z]*\s+(?P<day>\d{{1,2}})(?:st|nd|rd|th)?", re.I),
    re.compile(rf"\b(?P<day>\d{{1,2}})(?:st|nd|rd|th)?\s+(?P<mon>{_MONTH_ALT})[a-z]*\s*[(,]\s*(?P<wd>{_WD_ALT})[a-z]*", re.I),
    re.compile(rf"\b(?P<mon>{_MONTH_ALT})[a-z]*\s+(?P<day>\d{{1,2}})(?:st|nd|rd|th)?\s*[(,]\s*(?P<wd>{_WD_ALT})[a-z]*", re.I),
]


def parse_event_date(s):
    """Parse an ISO date at reduced precision (YYYY | YYYY-MM | YYYY-MM-DD) ->
    (date, precision). Reduced precision resolves to the FIRST day of the period; ISO
    8601 reduced precision is intentionally allowed so an arXiv-derived YYYY-MM and a
    writer-supplied YYYY-MM-DD coexist in `event_date`. None if empty/unparseable."""
    if not s:
        return None
    m = _ISO_PARTIAL_RE.match(s.strip())
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2) or 1), int(m.group(3) or 1)
    try:
        return dt.date(y, mo, d), ("day" if m.group(3) else "month" if m.group(2) else "year")
    except ValueError:
        return None


def days_since(event_date, as_of):
    """Whole days from event_date (any ISO precision) to as_of (a date). None if the
    event date can't be parsed. Reduced precision counts from the period's first day."""
    p = parse_event_date(event_date)
    if not p or as_of is None:
        return None
    return (as_of - p[0]).days


def scheduled_event_date(rec):
    """A thread's event_date worth CARRYING FORWARD to later members: present AND in the
    future relative to the thread's first coverage — a FIXED scheduled event (a vote, an
    IPO pricing, a conference) whose date doesn't move. Returns the event_date string,
    else None. Evolving threads (a war, a saga — where event_date ~ each day's coverage)
    return None so a stale date never propagates. This is the fix for the 2026-06-06
    'vote this weekend' error: once the SVP vote carries event_date 2026-06-14, every later
    brief inherits it instead of re-deriving 'which Sunday'."""
    ed = rec.get("event_date")
    if not ed:
        return None
    p = parse_event_date(ed)
    anchor = rec.get("first_seen_date") or rec.get("date")
    try:
        a = dt.date.fromisoformat(anchor) if anchor else None
    except (ValueError, TypeError):
        a = None
    return ed if (p and a and p[0] > a) else None


def weekday_flags(text, brief_date):
    """Find 'weekday + day + month' mentions whose stated weekday doesn't match the real
    calendar weekday. brief_date anchors the year (nearest year to the brief, so Dec/Jan
    boundaries and near-future dates resolve correctly). Pure + offline.

    Catches the ADJACENT-form weekday slip (e.g. "Wednesday 11 June" when June 11 is a
    Thursday — the 2026-06-07-ai-ml.md SPCX error class). It does NOT catch a weekday and
    date split across distant clauses; the injected as-of dated-weekday block is the
    primary defense for that (see DEDUP.md). Returns a list of flag dicts."""
    flags, seen = [], set()
    if brief_date is None:
        return flags
    for pat in _WD_PATTERNS:
        for m in pat.finditer(text or ""):
            wd = m.group("wd").lower()[:3]
            day = int(m.group("day"))
            mon = _MONTHS[m.group("mon").lower()[:3]]
            best = None
            for yr in (brief_date.year - 1, brief_date.year, brief_date.year + 1):
                try:
                    c = dt.date(yr, mon, day)
                except ValueError:
                    continue
                if best is None or abs((c - brief_date).days) < abs((best - brief_date).days):
                    best = c
            if best is None or _WDAYS[best.weekday()] == wd:
                continue
            key = (wd, best.isoformat())
            if key in seen:
                continue
            seen.add(key)
            flags.append({"snippet": re.sub(r"\s+", " ", m.group(0)).strip(),
                          "stated_weekday": wd, "date": best.isoformat(),
                          "actual_weekday": _WDAYS_FULL[best.weekday()]})
    return flags


# Relative scheduling phrases that should carry an ABSOLUTE date when describing a dated
# event. Deliberately NOT "this week"/"today" (too common + benign). "this weekend",
# "tomorrow", "this/next/coming <weekday>" are the high-signal ones that misdated the
# 2026-06-06 vote ("votes this weekend" / "vote tomorrow").
# Trailing (?!['’]s) drops the possessive ("tomorrow's reveal", "tomorrow's Overview" =
# the next brief) — narrative, not a scheduling claim. The dangerous form is bare
# "vote tomorrow" / "votes this weekend".
_SCHED_RE = re.compile(
    r"\b(?:(?:this|next|coming)\s+(?:weekend|monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)"
    r"|over\s+the\s+weekend|tomorrow|tonight)(?!['’]s)\b", re.I)
_ABS_DATE_RE = re.compile(
    rf"\b\d{{1,2}}(?:st|nd|rd|th)?\s+{_MONTH_ALT}[a-z]*\b"      # 14 June
    rf"|\b{_MONTH_ALT}[a-z]*\s+\d{{1,2}}(?:st|nd|rd|th)?\b"     # June 14
    rf"|\b\d{{4}}-\d{{2}}-\d{{2}}\b", re.I)                     # 2026-06-14


def scheduling_flags(text):
    """Flag relative scheduling phrases ("this weekend", "tomorrow", "this Sunday") with
    no ABSOLUTE date NEARBY. ADVISORY: it forces the writer to commit to a concrete date
    for a scheduled event — the framing that misdated the 2026-06-06 'vote this weekend'
    (June 7) when the vote was 14 June. It does NOT verify the date is correct (event_date
    carry-through does that); it just refuses bare relative framing. A phrase already
    accompanied by a date (e.g. "opens tomorrow (8 June)") is not flagged.

    Proximity, NOT same-sentence: a brief bullet trails markdown citations carrying ISO
    dates (2026-06-06, [ongoing since …]) that would otherwise mask a far-away scheduling
    phrase. Only a date within a short window of the phrase counts. Pure + offline."""
    flags, seen = [], set()
    for m in _SCHED_RE.finditer(text or ""):
        window = text[max(0, m.start() - 25): m.end() + 55]
        if _ABS_DATE_RE.search(window):
            continue
        phrase = re.sub(r"\s+", " ", m.group(0)).strip()
        snip = re.sub(r"\s+", " ", text[max(0, m.start() - 30): m.end() + 70]).strip()
        key = (phrase.lower(), snip[:40])
        if key in seen:
            continue
        seen.add(key)
        flags.append({"phrase": phrase, "snippet": snip[:160]})
    return flags


# --------------------------------------------------------------------------- #
# subcommands
# --------------------------------------------------------------------------- #
def _build_exact_index(recent):
    """Map exact identity key -> earliest matching record (recent is date-ascending,
    so setdefault keeps the first-seen)."""
    idx = {}
    for rec in recent:
        for k in exact_keys(rec.get("headline"), rec.get("summary"), rec.get("url")):
            idx.setdefault(k, rec)
    return idx


def _matched_obj(rec):
    return {"id": rec.get("id"), "date": rec.get("date"), "headline": rec.get("headline"),
            "thread_id": rec.get("thread_id") or rec.get("id"),
            "first_seen_date": rec.get("first_seen_date") or rec.get("date"),
            "event_date": rec.get("event_date")}


def decide_verdict(cand, vec, recent, exact, t_high, t_low):
    """Per-candidate verdict, in precedence order. Pure (used by cmd_check + tests):
    1. Deterministic exact-source match (same canonical URL / arXiv id) -> REPEAT,
       cosine-independent — catches reworded-headline reruns cosine would miss.
    2. Cosine classify -> REPEAT/ONGOING/NEW."""
    hit_keys = [k for k in exact_keys(cand.get("headline"), cand.get("summary"), cand.get("url"))
                if k in exact]
    if hit_keys:
        return {"verdict": "REPEAT", "score": 1.0,
                "match_reason": "exact-arxiv" if any(k.startswith("arxiv:") for k in hit_keys) else "exact-url",
                "matched": _matched_obj(exact[hit_keys[0]])}
    r = classify(vec, recent, t_high, t_low)
    # arXiv distinct-paper guard (check side): an ONGOING that is topically close but a
    # DIFFERENT paper must not hand the writer "[ongoing since <other paper's date>]".
    # Keep ONGOING (it IS related — the writer may still mention it) but flag the match
    # as a non-continuation and drop the misleading since-date. Mirrors autolink's
    # record-side guard so the index and the writer agree.
    if (r["verdict"] == "ONGOING" and r.get("matched")
            and _distinct_paper(cand, r["matched"])):
        r["matched"]["continuation"] = False
        r["matched"]["first_seen_date"] = None
        r["match_reason"] = "distinct-paper"
    return r


def cmd_check(args):
    with open(args.candidates) as f:
        cands = json.load(f)
    if isinstance(cands, dict) and "candidates" in cands:
        cands = cands["candidates"]
    texts = [embed_text(c.get("headline", ""), c.get("summary", "")) for c in cands]
    vecs = embed(texts, args.worker, args.token)
    recent = load_recent_index(args.since, as_of=_parse_date(args.as_of))
    exact = _build_exact_index(recent)
    results = []
    for c, v in zip(cands, vecs):
        r = decide_verdict(c, v, recent, exact, args.t_high, args.t_low)
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
    # Auto-link threads so continuity no longer depends on the writer carrying
    # DEDUP.md Step C through by hand: for any story the writer didn't already
    # thread, inherit thread_id/first_seen_date from its best recent match.
    # Harmless if the index is missing/empty (autolink returns None).
    recent = load_recent_index(SINCE_DEFAULT, as_of=_parse_date(date))
    recent_by_id = {r.get("id"): r for r in recent}
    records = []
    for s, v in zip(stories, vecs):
        hid = s.get("id") or f"{date}-{slug}-{slugify(s.get('headline',''))}"
        thread_id = s.get("thread_id")
        first_seen_date = s.get("first_seen_date")
        # Validate a WRITER-SUPPLIED thread before trusting it. The SASA/SoftSAE false
        # merge (2026-06-06-weekend.md) was NOT a cosine error — the two papers embed at
        # only 0.71, so autolink never linked them. The writer hand-set thread_id onto a
        # same-TOPIC but DISTINCT paper and tagged "[ongoing since 2026-05-14]". If the
        # candidate is a distinct arXiv paper from the thread genesis, reject the manual
        # thread -> fresh thread. (genesis must be in the recent window to validate.)
        if thread_id:
            genesis = recent_by_id.get(thread_id)
            if genesis is not None and _distinct_paper(s, genesis):
                thread_id = first_seen_date = None
        if not thread_id:
            link = autolink(v, recent, cand=s)
            if link:
                thread_id, first_seen_date = link
        # event_date: writer-supplied (day precision) wins; else deterministic arXiv
        # submission month; else inherit the thread's SCHEDULED date (fixed future event
        # like a vote, so it isn't re-derived); else null. Distinct from `date`/first_seen.
        event_date = s.get("event_date") or arxiv_event_date(
            s.get("headline", ""), s.get("summary", ""), s.get("url", "") or "")
        if not event_date and thread_id:
            genesis = recent_by_id.get(thread_id)
            if genesis is not None:
                event_date = scheduled_event_date(genesis)
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
            "thread_id": thread_id or hid,
            "first_seen_date": first_seen_date or date,
            "event_date": event_date,
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
                # deterministic only (no network at backfill): arXiv submission month
                # where an id is present, else null. Retroactively arms event_date for
                # ID-bearing records without re-research.
                "event_date": arxiv_event_date(s["headline"], s["summary"], s["url"] or ""),
                "embedding_model": EMBED_MODEL if not args.no_embed else None,
                "emb": encode_vec(v) if v else None,
            })
        write_index_file(date, slug, records)
        written += 1
        total += len(records)
        print(f"  {date}-{slug}: {len(records)} stories")
    print(f"backfill done: {total} stories across {written} briefs -> {INDEX_DIR}")


def cmd_lint(args):
    """Post-compose date checks on a brief markdown file (deterministic, no network):
      * WEEKDAY (hard, exits 1): a weekday named next to a date it doesn't match.
      * SCHEDULE (advisory): relative framing ("this weekend"/"tomorrow") with no
        absolute date — state the concrete date for scheduled events.
    Writers can gate their commit on `lint OK`; advisory flags print but don't fail."""
    with open(args.brief) as f:
        text = f.read()
    date = _parse_date(args.date)
    if date is None:
        d = _date_from_name(args.brief)
        date = _parse_date(d) if d else None
    hard = [f"WEEKDAY: \"{fl['snippet']}\" — {fl['date']} is a {fl['actual_weekday']}"
            for fl in weekday_flags(text, date)]
    advisory = [f"SCHEDULE [advisory]: \"{fl['phrase']}\" with no absolute date — {fl['snippet']}"
                for fl in scheduling_flags(text)]
    for msg in hard + advisory:
        print(msg)
    if hard:
        print(f"lint: {len(hard)} weekday error(s) — fix before commit", file=sys.stderr)
        sys.exit(1)
    print("lint OK" + (f" — {len(advisory)} advisory scheduling flag(s) above to review" if advisory else ""))


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
        "- **Parliament debates the energy bill.** Second reading scheduled. [SRF](https://g.co/y)\n\n"
        "## Coverage footer\n- **Not a story.** ignore me [x](https://z.co/q)\n"
    )
    stories = extract_stories(sample)
    assert len(stories) == 2, stories
    assert stories[0]["headline"].startswith("Bilaterals III")
    assert stories[0]["url"] == "https://swissinfo.ch/x"
    assert source_domain("https://www.aljazeera.com/x") == "aljazeera.com"
    assert embed_text("Headline here", "Headline here. extra").startswith("Headline here")
    # event_date derivation + ISO-partial parsing + days-since.
    assert arxiv_event_date("see arXiv:2606.06333 abstract") == "2026-06", \
        arxiv_event_date("see arXiv:2606.06333")
    assert arxiv_event_date("no id here") is None
    assert parse_event_date("2026-06")[1] == "month"
    assert parse_event_date("2026-06-02")[1] == "day"
    assert parse_event_date("not-a-date") is None
    assert days_since("2026-06-02", dt.date(2026, 6, 5)) == 3
    assert days_since("2026-06", dt.date(2026, 6, 5)) == 4  # month -> first of month
    # arXiv distinct-paper guard: SASA (2606.06333) vs an id-less SAE listing record.
    sasa = {"headline": "Subspace-aware sparse autoencoders cut feature splitting",
            "summary": "", "url": "https://arxiv.org/abs/2606.06333"}
    softsae = {"headline": "SoftSAE: Dynamic Top-K Selection for Adaptive SAEs",
               "summary": "(cs.LG, May 2026 batch)", "url": "https://arxiv.org/list/cs.LG/current"}
    assert _distinct_paper(sasa, softsae) is True, "SASA vs id-less SAE record must be distinct"
    assert _distinct_paper(sasa, sasa) is False, "same arXiv id must NOT be distinct"
    assert _distinct_paper({"headline": "no id", "summary": "", "url": None}, sasa) is False, \
        "candidate without an arXiv id never triggers the guard"
    # Weekday lint: the SPCX error class (adjacent form) flags; the correct weekday doesn't.
    wf = weekday_flags("the IPO prices Wednesday 11 June at a fixed price", dt.date(2026, 6, 7))
    assert wf and wf[0]["actual_weekday"] == "Thursday", wf
    assert weekday_flags("trading begins Friday 12 June", dt.date(2026, 6, 7)) == [], \
        "a correct weekday must not flag"
    # scheduled-event date carry: future-vs-coverage = scheduled (carry); else evolving.
    assert scheduled_event_date({"event_date": "2026-06-14", "first_seen_date": "2026-05-23"}) == "2026-06-14"
    assert scheduled_event_date({"event_date": "2026-05-02", "first_seen_date": "2026-05-02"}) is None
    assert scheduled_event_date({"first_seen_date": "2026-05-23"}) is None
    # scheduling lint: bare relative framing flags; with an absolute date it does not.
    assert scheduling_flags("Switzerland votes this weekend on the initiative."), "'this weekend' should flag"
    assert scheduling_flags("Federal vote tomorrow: foreign attention."), "'tomorrow' should flag"
    assert scheduling_flags("WWDC opens tomorrow (Monday 8 June) with the keynote.") == [], \
        "'tomorrow (8 June)' has an absolute date — must not flag"
    assert scheduling_flags("this week's open-weight drops were quiet.") == [], \
        "'this week' is benign — must not flag"
    assert scheduling_flags("it will land in tomorrow's Overview brief.") == [], \
        "possessive 'tomorrow's' is narrative — must not flag"
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

    ln = sub.add_parser("lint", help="post-compose date checks on a brief (no network)")
    ln.add_argument("--brief", required=True, help="path to the brief markdown file")
    ln.add_argument("--date", default=None,
                    help="YYYY-MM-DD brief date (anchors the year); defaults to the filename date")
    ln.set_defaults(func=cmd_lint)

    s = sub.add_parser("selftest", help="offline logic checks (no network)")
    s.set_defaults(func=cmd_selftest)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
