#!/usr/bin/env python3
"""Source registry + credibility lifecycle -- SPIKE-2026-07-07-continuous-news.md §3.4.

`sources/registry.yml` is the credibility-lifecycle source of truth: one record per cited
domain (class/tier/status/reach/probe/streams/last_cited/lifecycle audit trail). `bootstrap`
seeds it from the live index (`index/stories/*.jsonl`), counting only citations from the four
LIVE_STREAMS -- retired-stream files (overview/cyber-papers/markets) are invisible to it, so a
domain cited only there never surfaces (review C18 intent: don't fossilize a deleted pipeline
into the founding registry). `sync` folds the append-only write-contention buffers
`sources/{candidates,last-cited}.jsonl` into it (review C1 -- high-frequency machine writes
never touch the YAML directly) and truncates both.

Stdlib only, no network: routine sandboxes run bare python3 with no PyYAML, so this hand-rolls
the same block-YAML subset tools/tests/yamllite.py reads (block maps/sequences, scalar
strings/ints/null/bool -- no flow collections, no multiline scalars; everything the registry
needs fits). preflight.py/lint.py/health.py import this module directly (sibling scripts in
the same directory -- no package, no sys.path surgery needed) for classify_domain(),
yaml_load()/yaml_dump(), and the story-index/date-window helpers.

Usage: registry.py bootstrap --root PATH
       registry.py sync [--root PATH]
"""
import argparse
import datetime
import json
import os
import sys

LIVE_STREAMS = {"news", "ai-ml", "science", "weekend", "sports"}

# SPIKE §3.4 Bootstrap, review fix C18: the retired security/markets pipeline's domains, excluded
# from bootstrap BY NAME -- a stray genuine citation landing in a live stream (it has happened:
# nvd.nist.gov, cisa.gov each leaked in via one weekend-stream citation) would otherwise fossilize
# the deleted pipeline into the founding registry. They may still re-enter later, organically, via
# the [new source] candidate lane (registry.py sync) -- that's the lifecycle working as designed.
RETIRED_DOMAINS = {"nvd.nist.gov", "cisa.gov", "ecb.europa.eu"}

# class fixed rule sets (SPIKE §3.4): hub (independent primary-artifact host) > institutional
# (*.gov / *.europa.eu wildcards + admin.ch literal) > outlet (the default).
HUB_DOMAINS = {"arxiv.org", "hf.co", "huggingface.co", "github.com", "doi.org", "biorxiv.org"}
INSTITUTIONAL_LITERALS = {"admin.ch"}
INSTITUTIONAL_SUFFIXES = (".gov", ".europa.eu")

ESTABLISHED_MIN_CITATIONS = 5

# The 7 allowlisted feed hosts (routines/_shared/feed-first-source-order.md), keyed by bare
# registry domain -- these alone get a probe: block at bootstrap (the feed URL doubles as the
# step-7 polling manifest if continuous ingestion ever ships).
FEED_HOST_PROBES = {
    "arxiv.org": {"url": "http://export.arxiv.org/api/query?search_query=all&max_results=1", "method": "curl"},
    "nature.com": {"url": "https://www.nature.com/nature.rss", "method": "curl"},
    "quantamagazine.org": {"url": "https://www.quantamagazine.org/feed/", "method": "curl"},
    "semanticscholar.org": {"url": "https://api.semanticscholar.org/graph/v1/paper/search?query=test&limit=1",
                             "method": "curl"},
    "srf.ch": {"url": "https://www.srf.ch/news/bnf/rss/1646", "method": "curl"},
    "letemps.ch": {"url": "https://www.letemps.ch/articles.rss", "method": "curl"},
    "aljazeera.com": {"url": "https://www.aljazeera.com/xml/rss/all.xml", "method": "curl"},
}

# nature.com subsources: fixed path-prefix tier split mechanizing the reader's 2026-06-19
# sub-domain-credibility complaint (news blog vs. the journal) -- assigned at bootstrap
# regardless of which paths were actually cited in the window.
NATURE_SUBSOURCES = [
    {"prefix": "/articles/d", "tier": "T2", "note": "news blog"},
    {"prefix": "/articles/s", "tier": "T1", "note": "journal"},
]


def classify_domain(domain):
    """class: hub (fixed set) > institutional (*.gov / *.europa.eu / admin.ch) > outlet."""
    if domain in HUB_DOMAINS:
        return "hub"
    if domain in INSTITUTIONAL_LITERALS or any(domain.endswith(suf) for suf in INSTITUTIONAL_SUFFIXES):
        return "institutional"
    return "outlet"


def registry_path(root):
    return os.path.join(root, "sources", "registry.yml")


# --- YAML subset (block mappings/sequences, scalar strings/ints/null/bool) -----------------
# Independently implements the same covered subset as tools/tests/yamllite.py so that loader
# (and real PyYAML, if ever installed) reads this file back faithfully. No flow collections
# (`[a, b]`), no multiline block scalars -- every registry field fits the block subset.

def _scalar_dump(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    s = str(v)
    if s == "" or s.strip() != s or s.lower() in ("null", "true", "false", "~"):
        return '"%s"' % s.replace("\\", "\\\\").replace('"', '\\"')
    for caster in (int, float):
        try:
            caster(s)
            return '"%s"' % s
        except ValueError:
            pass
    return s


def yaml_dump(data, _indent=0):
    pad = "  " * _indent
    lines = []
    if isinstance(data, dict):
        if not data:
            return pad + "{}\n"
        for key, val in data.items():
            if isinstance(val, dict) and val:
                lines.append("%s%s:" % (pad, key))
                lines.append(yaml_dump(val, _indent + 1).rstrip("\n"))
            elif isinstance(val, list) and val:
                lines.append("%s%s:" % (pad, key))
                lines.append(yaml_dump(val, _indent + 1).rstrip("\n"))
            elif isinstance(val, dict):
                lines.append("%s%s: {}" % (pad, key))
            elif isinstance(val, list):
                lines.append("%s%s: []" % (pad, key))
            else:
                lines.append("%s%s: %s" % (pad, key, _scalar_dump(val)))
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                sub = [l for l in yaml_dump(item, _indent + 1).split("\n") if l.strip()]
                if sub:
                    lines.append("%s- %s" % (pad, sub[0].strip()))
                    lines.extend(sub[1:])
            else:
                lines.append("%s- %s" % (pad, _scalar_dump(item)))
    return "\n".join(lines) + "\n"


def _scalar_load(s):
    s = s.strip()
    if s == "" or s in ("~", "null", "Null", "NULL"):
        return None
    if s in ("true", "True", "TRUE"):
        return True
    if s in ("false", "False", "FALSE"):
        return False
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    if s == "[]":
        return []
    if s == "{}":
        return {}
    for caster in (int, float):
        try:
            return caster(s)
        except ValueError:
            pass
    return s


def yaml_load(text):
    lines = []
    for raw in text.split("\n"):
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        lines.append((len(raw) - len(raw.lstrip(" ")), raw.strip()))
    pos = [0]

    def peek():
        return lines[pos[0]] if pos[0] < len(lines) else None

    def parse_block(indent):
        node = peek()
        if node is None or node[0] < indent:
            return None
        return parse_list(indent) if node[1].startswith("- ") else parse_map(indent)

    def parse_list(indent):
        result = []
        while True:
            node = peek()
            if node is None or node[0] != indent or not node[1].startswith("- "):
                break
            pos[0] += 1
            body = node[1][2:]
            if ":" in body and not body.strip().startswith(("'", '"')):
                key, _, val = body.partition(":")
                key, val = key.strip(), val.strip()
                item = {key: (parse_block(indent + 2) if val == "" else _scalar_load(val))}
                while True:
                    nxt = peek()
                    if nxt is None or nxt[0] != indent + 2 or nxt[1].startswith("- "):
                        break
                    pos[0] += 1
                    k2, _, v2 = nxt[1].partition(":")
                    k2, v2 = k2.strip(), v2.strip()
                    item[k2] = parse_block(indent + 4) if v2 == "" else _scalar_load(v2)
                result.append(item)
            else:
                result.append(_scalar_load(body))
        return result

    def parse_map(indent):
        result = {}
        while True:
            node = peek()
            if node is None or node[0] != indent or node[1].startswith("- "):
                break
            pos[0] += 1
            key, _, val = node[1].partition(":")
            key, val = key.strip(), val.strip()
            if val == "":
                nxt = peek()
                result[key] = parse_block(nxt[0]) if nxt is not None and nxt[0] > indent else None
            else:
                result[key] = _scalar_load(val)
        return result

    return parse_map(0)


# --- shared story-index helpers (also used by preflight.py / health.py) --------------------

def load_story_records(root):
    """Yield every JSON record from <root>/index/stories/*.jsonl, sorted by filename, skipping
    blank/malformed lines. Missing dir -> no records (never a hard error)."""
    stories_dir = os.path.join(root, "index", "stories")
    if not os.path.isdir(stories_dir):
        return
    for fname in sorted(os.listdir(stories_dir)):
        if not fname.endswith(".jsonl"):
            continue
        with open(os.path.join(stories_dir, fname)) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except ValueError:
                    continue


def read_jsonl(path):
    if not os.path.exists(path):
        return []
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def days_since(date_str, today=None):
    """Whole days between date_str (YYYY-MM-DD) and today (real wall-clock UTC date -- no
    --date override in the contract, unlike metrics.py)."""
    today = today or datetime.datetime.now(datetime.timezone.utc).date()
    d = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    return (today - d).days


# --- schema validation + lifecycle append (admin apply path, PLAN 2026-09-13 §2.3/§3 S3) ----
# validate() and lifecycle_append() are used ONLY by the admin apply path (tools/admin/apply.py);
# bootstrap/sync do not call them, so the CLI is unchanged. The enumerations below mirror
# tools/tests/test_registry_schema.py exactly -- that suite pins the same invariants over the
# live file, so a batch that validate() clears cannot leave a registry the schema test would fail.

_VALID_CLASSES = {"outlet", "hub", "institutional"}
_VALID_TIERS = {"T1", "T2"}
_VALID_STATUSES = {"candidate", "probation", "established", "demoted", "retired"}
_VALID_REACH = {"direct", "proxy", "search-only", "blocked", "blocked-paywall"}
_VALID_STREAMS = {"news", "ai-ml", "science", "weekend", "sports"}
# reach and the probe's method say the same thing two ways; a contradiction sends every fetch of
# the domain down the wrong path (test_probe_method_agrees_with_reach). Only direct/proxy map.
REACH_METHOD = {"direct": "curl", "proxy": "proxy"}
# The one domain whose feed genuinely lives on another registrable domain (BBC's feed host).
_PROBE_HOST_EXCEPTIONS = {"bbc.com": "feeds.bbci.co.uk"}
# A stream whose every source is retired/blocked would ship empty briefs while every tool still
# reports success (test_every_stream_has_reachable_sources): keep a floor of usable sources.
_STREAM_MIN_USABLE = 5


def _registrable(host):
    """The registrable (last-two-label) form of a host, www-stripped -- for the probe-belongs-to-
    domain check. Mirrors the helper of the same name in test_registry_schema.py."""
    host = host.lower().lstrip(".")
    if host.startswith("www."):
        host = host[4:]
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def validate(reg):
    """Return a list of human-readable violation strings for a registry mapping; empty means the
    registry satisfies every invariant tools/tests/test_registry_schema.py pins over the live file.
    The admin apply path calls this AFTER a batch and, on any violation, discards the batch rather
    than write a registry the spec suite would then reject on main (PLAN §2.3)."""
    import re
    from urllib.parse import urlparse
    violations = []
    if not isinstance(reg, dict) or not reg:
        return ["registry is empty or not a mapping"]
    for domain, rec in reg.items():
        if not isinstance(rec, dict):
            violations.append("%s: entry is not a mapping" % domain)
            continue
        for key in ("class", "tier", "status", "reach", "streams", "lifecycle"):
            if key not in rec:
                violations.append("%s: missing required key %s" % (domain, key))
        if "class" in rec and rec["class"] not in _VALID_CLASSES:
            violations.append("%s: class %r not in %s" % (domain, rec["class"], sorted(_VALID_CLASSES)))
        if "tier" in rec and rec["tier"] not in _VALID_TIERS:
            violations.append("%s: tier %r not in %s" % (domain, rec["tier"], sorted(_VALID_TIERS)))
        if "status" in rec and rec["status"] not in _VALID_STATUSES:
            violations.append("%s: status %r not in %s" % (domain, rec["status"], sorted(_VALID_STATUSES)))
        if "reach" in rec and rec["reach"] not in _VALID_REACH:
            violations.append("%s: reach %r not in %s" % (domain, rec["reach"], sorted(_VALID_REACH)))
        streams = rec.get("streams") or []
        if not streams:
            violations.append("%s: belongs to no stream" % domain)
        for s in streams:
            if s not in _VALID_STREAMS:
                violations.append("%s: unknown stream %r" % (domain, s))
        # Domain keys must be bare, lowercase hosts (test_domain_keys_are_bare_lowercase_hosts).
        if domain != domain.lower() or "/" in domain or "://" in domain \
                or domain.startswith("www.") or "." not in domain:
            violations.append("%s: not a bare lowercase host" % domain)
        probe = rec.get("probe") or {}
        url = probe.get("url")
        if url:
            if not re.match(r"^https?://", url):
                violations.append("%s: probe url is not absolute http(s): %r" % (domain, url))
            else:
                host = urlparse(url).netloc.lower()
                if _PROBE_HOST_EXCEPTIONS.get(domain) != host \
                        and _registrable(host) != _registrable(domain):
                    violations.append("%s: probe on an unrelated host: %s" % (domain, host))
        method = probe.get("method")
        if method:
            if method not in ("curl", "proxy"):
                violations.append("%s: probe method %r not curl/proxy" % (domain, method))
            else:
                expected = REACH_METHOD.get(rec.get("reach"))
                if expected and method != expected:
                    violations.append("%s: reach=%s but probe method=%s"
                                      % (domain, rec.get("reach"), method))
        for item in rec.get("lifecycle") or []:
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(item.get("date", ""))):
                violations.append("%s: undated lifecycle entry %r" % (domain, item))
            if not item.get("event"):
                violations.append("%s: lifecycle entry has no event" % domain)
    # Aggregate floor: every live stream must keep enough reachable sources to fill a brief.
    for stream in sorted(_VALID_STREAMS):
        usable = [d for d, r in reg.items()
                  if isinstance(r, dict) and stream in (r.get("streams") or [])
                  and r.get("status") not in ("retired", "demoted")
                  and r.get("reach") in ("direct", "proxy")]
        if len(usable) < _STREAM_MIN_USABLE:
            violations.append("stream %s has only %d usable source(s) (min %d)"
                              % (stream, len(usable), _STREAM_MIN_USABLE))
    return violations


def lifecycle_append(entry, date, event, status=None, note=None):
    """Append one dated lifecycle audit entry to `entry` in place (creating the list if absent),
    and return it. Key order (date, event, status, note) matches the bootstrap/seed rows so the
    dumper's output stays in canonical form; status/note are omitted when None."""
    item = {"date": date, "event": event}
    if status is not None:
        item["status"] = status
    if note is not None:
        item["note"] = note
    entry.setdefault("lifecycle", []).append(item)
    return item


# --- bootstrap ------------------------------------------------------------------------------

def cmd_bootstrap(args):
    root = args.root
    domains = {}  # domain -> {"count": int, "streams": set, "dates": [str]}
    for rec in load_story_records(root):
        stream = rec.get("stream")
        if stream not in LIVE_STREAMS:
            continue
        domain = rec.get("source_domain")
        if not domain or domain in RETIRED_DOMAINS:
            continue
        entry = domains.setdefault(domain, {"count": 0, "streams": set(), "dates": []})
        entry["count"] += 1
        entry["streams"].add(stream)
        date = rec.get("date")
        if date:
            entry["dates"].append(date)

    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    out = {}
    for domain in sorted(domains):
        entry = domains[domain]
        status = "established" if entry["count"] >= ESTABLISHED_MIN_CITATIONS else "probation"
        cls = classify_domain(domain)
        rec_out = {
            "class": cls,
            "tier": "T1" if cls == "hub" else "T2",
            "status": status,
            "reach": "direct",
            "streams": sorted(entry["streams"]),
            "last_cited": max(entry["dates"]) if entry["dates"] else None,
        }
        if domain in FEED_HOST_PROBES:
            rec_out["probe"] = FEED_HOST_PROBES[domain]
        if domain == "nature.com":
            rec_out["subsources"] = NATURE_SUBSOURCES
        rec_out["lifecycle"] = [{"date": today, "event": "bootstrap", "status": status}]
        out[domain] = rec_out

    out_path = registry_path(root)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        f.write(yaml_dump(out))
    print("bootstrap: wrote %d domain(s) to %s" % (len(out), out_path))
    return 0


# --- sync -----------------------------------------------------------------------------------

def cmd_sync(args):
    root = args.root
    path = registry_path(root)
    reg = {}
    if os.path.exists(path):
        with open(path) as f:
            text = f.read()
        if text.strip():
            loaded = yaml_load(text)
            if isinstance(loaded, dict):
                reg = loaded

    sources_dir = os.path.join(root, "sources")
    os.makedirs(sources_dir, exist_ok=True)
    candidates_path = os.path.join(sources_dir, "candidates.jsonl")
    last_cited_path = os.path.join(sources_dir, "last-cited.jsonl")
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()

    added = 0
    for rec in read_jsonl(candidates_path):
        domain = rec.get("domain")
        if not domain or domain in reg:
            continue  # never downgrades an already-registered domain back to candidate
        cls = classify_domain(domain)
        reg[domain] = {
            "class": cls,
            "tier": "T1" if cls == "hub" else "T2",
            "status": "candidate",
            "reach": "direct",
            "streams": [rec["stream"]] if rec.get("stream") else [],
            "last_cited": rec.get("first_seen"),
            "lifecycle": [{"date": today, "event": "candidate", "status": "candidate"}],
        }
        added += 1

    folded = 0
    for rec in read_jsonl(last_cited_path):
        domain, date = rec.get("domain"), rec.get("date")
        if not domain or not date or domain not in reg:
            continue
        current = reg[domain].get("last_cited")
        if not current or date > current:  # fold as max() -- ISO dates sort lexically
            reg[domain]["last_cited"] = date
            folded += 1

    # No-op guard (2026-07-18): sync runs on EVERY edition since the publish-tail
    # rollout, but the SPIKE's write-contention design assumed only the low-frequency
    # Evaluator rewrites registry.yml. When nothing folded, leave the YAML untouched --
    # an unchanged file can't merge-conflict, so the residual same-day race shrinks to
    # the rare both-editions-added-a-domain case. The buffers are still PURGED: every
    # entry provably folded to nothing (candidate already registered, last_cited not
    # newer), and leaving them would inflate candidates_open in source-health forever.
    if added == 0 and folded == 0:
        purged = 0
        for p in (candidates_path, last_cited_path):
            if os.path.exists(p) and os.path.getsize(p) > 0:
                open(p, "w").close()
                purged += 1
        print("sync: nothing to fold (registry.yml untouched%s)" %
              ("; %d dead buffer(s) purged" % purged if purged else ""))
        return 0

    with open(path, "w") as f:
        f.write(yaml_dump(reg))

    for p in (candidates_path, last_cited_path):
        if os.path.exists(p):
            open(p, "w").close()  # truncate, not delete -- sync is idempotent on empty files

    print("sync: %d new candidate(s), %d last_cited fold(s)" % (added, folded))
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("bootstrap", help="seed registry.yml from the live index")
    b.add_argument("--root", required=True)
    b.set_defaults(func=cmd_bootstrap)

    s = sub.add_parser("sync", help="fold candidates/last-cited jsonl buffers into registry.yml")
    s.add_argument("--root", default=".")
    s.set_defaults(func=cmd_sync)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
