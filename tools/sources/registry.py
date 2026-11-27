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
import importlib.util
import json
import os
import re
import sys

LIVE_STREAMS = {"news", "ai-ml", "science", "weekend", "sports"}

# SPIKE §3.4 Bootstrap, review fix C18: the retired security/markets pipeline's domains, excluded
# from bootstrap BY NAME -- a stray genuine citation landing in a live stream (it has happened:
# nvd.nist.gov, cisa.gov each leaked in via one weekend-stream citation) would otherwise fossilize
# the deleted pipeline into the founding registry. They may still re-enter later, organically, via
# the [new source] candidate lane (registry.py sync) -- that's the lifecycle working as designed.
RETIRED_DOMAINS = {"nvd.nist.gov", "cisa.gov", "ecb.europa.eu"}

# class fixed rule sets (SPIKE §3.4): hub (independent primary-artifact host) > institutional
# (public bodies by domain structure + a short evidence-backed literal list) > outlet (the default).
# Every match is label-bounded and covers subdomains (export.arxiv.org, bfs.admin.ch, news.un.org).
# This is only the DEFAULT for a domain the registry has not classed yet: a registry entry's own
# `class:` always wins (class_of below), so a hand-curated override is never re-derived away.
HUB_DOMAINS = {"arxiv.org", "hf.co", "huggingface.co", "github.com", "doi.org", "biorxiv.org"}
# TLDs whose every registrant is a government, military, intergovernmental or US-accredited
# higher-education body.
INSTITUTIONAL_TLDS = {"gov", "mil", "int", "edu"}
# Second-level labels reserved, directly under a two-letter ccTLD, for government, military or
# academia: gov.uk, gov.br, gob.mx, gob.es, gouv.fr, ac.uk, ac.at, ac.il, edu.au, mil.<cc>.
INSTITUTIONAL_SLDS = {"gov", "gob", "gouv", "mil", "edu", "ac"}
# The 26 cantonal administrations (vd.ch, gr.ch, polizei.bs.ch ...).
SWISS_CANTON_CODES = {"ag", "ai", "ar", "be", "bl", "bs", "fr", "ge", "gl", "gr", "ju", "lu", "ne",
                      "nw", "ow", "sg", "sh", "so", "sz", "tg", "ti", "ur", "vd", "vs", "zg", "zh"}
# Public bodies outside those structures, each one cited or proposed in this pipeline: EU and
# Swiss federal hosts, Swiss courts / parliament / central bank / regulator, intergovernmental
# organisations on .org, foreign presidencies and parliaments, a central bank.
INSTITUTIONAL_LITERALS = {
    "europa.eu", "admin.ch", "gov.wales", "police.uk", "gc.ca",
    "parlament.ch", "bger.ch", "bvger.ch", "snb.ch", "finma.ch",
    "un.org", "ungeneva.org", "unep.org", "wfp.org", "wto.org", "imf.org", "oecd.org", "bis.org",
    "iea.org", "icj-cij.org",
    "elysee.fr", "kremlin.ru", "riksdagen.se", "ft.dk", "dnb.nl",
} | {code + ".ch" for code in SWISS_CANTON_CODES}

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


def _under(domain, base):
    return domain == base or domain.endswith("." + base)


def classify_domain(domain):
    """Default class for a domain: hub (fixed set) > institutional (public-body domain
    structure or literal) > outlet."""
    d = str(domain or "").lower().rstrip(".")
    if any(_under(d, hub) for hub in HUB_DOMAINS):
        return "hub"
    labels = d.split(".")
    if labels[-1] in INSTITUTIONAL_TLDS:
        return "institutional"
    if len(labels) >= 2 and len(labels[-1]) == 2 and labels[-2] in INSTITUTIONAL_SLDS:
        return "institutional"
    if len(labels) >= 4 and labels[-1] == "us" and labels[-3] == "state":
        return "institutional"  # US state government: <agency>.state.<st>.us
    if any(_under(d, lit) for lit in INSTITUTIONAL_LITERALS):
        return "institutional"
    return "outlet"


def class_of(domain, reg):
    """The class every consumer must use: the registry entry's own `class:` when it has one
    (hand-curated overrides included), else the classify_domain() default."""
    entry = (reg or {}).get(domain)
    if isinstance(entry, dict) and entry.get("class"):
        return entry["class"]
    return classify_domain(domain)


def registry_path(root):
    return os.path.join(root, "sources", "registry.yml")


# --- YAML subset (block mappings/sequences, scalar strings/ints/null/bool) -----------------
# Independently implements the same covered subset as tools/tests/yamllite.py so that loader
# (and real PyYAML, if ever installed) reads this file back faithfully. No flow collections
# (`[a, b]`), no multiline block scalars -- every registry field fits the block subset.

# A plain (unquoted) scalar is emitted only when a strict YAML 1.1/1.2 parser (PyYAML, Ruby Psych)
# reads it back as the very same string; anything else is double-quoted with JSON escapes, which
# are valid YAML double-quoted escapes, and _scalar_load reverses them with json.loads.
_YAML_INDICATORS = set("-?:,[]{}#&*!|>'\"%@`")
_YAML_RESERVED = {"", "~", "null", "true", "false", "yes", "no", "on", "off", "y", "n"}
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# YAML 1.1 numbers Python's int()/float() reject: hex/octal/binary, sexagesimal, comma/underscore
# grouping, .inf/.nan, plus non-canonical timestamps (2026-7-5, 2026-07-05T10:00:00Z).
# Deliberately broader than any one resolver: every digit-led run of number characters is quoted.
_YAML_NUMLIKE_RE = re.compile(r"^(?=[-+.]?[0-9])[-+0-9a-fxob_,.:]+$"
                              r"|^[-+]?\.(inf|nan)$"
                              r"|^[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}([ tT].*)?$", re.I)
_YAML_LINEBREAKS = ("\x85", "\u2028", "\u2029", "\ufeff")


def _plain_ok(s, in_list=False):
    """True when `s` may be written unquoted and still load back as the same string -- under
    this module's own loader, tools/tests/yamllite.py, and any strict YAML parser."""
    if s.lower() in _YAML_RESERVED or s != s.strip():
        return False
    if s[0] in _YAML_INDICATORS:
        return False
    if ": " in s or " #" in s or s.endswith(":") or (in_list and ":" in s):
        return False  # in a list item our loader reads any ':' as a key separator
    if any(ord(c) < 0x20 or c == "\x7f" or c in _YAML_LINEBREAKS for c in s):
        return False
    if _ISO_DATE_RE.match(s):
        return True  # canonical date: strict parsers give a date, normalised back to this string
    if _YAML_NUMLIKE_RE.match(s):
        return False
    for caster in (int, float):
        try:
            caster(s)
            return False
        except ValueError:
            pass
    return True


def _scalar_dump(v, in_list=False):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    s = str(v)
    if _plain_ok(s, in_list):
        return s
    q = json.dumps(s, ensure_ascii=False)
    for ch in _YAML_LINEBREAKS:
        q = q.replace(ch, "\\u%04x" % ord(ch))
    return q


def key_ok(key):
    """True when `key` can be written as a plain mapping key this loader reads back intact (it
    splits a line at its FIRST ':') and a strict parser keeps as the same string."""
    s = str(key)
    return bool(s) and ":" not in s and _plain_ok(s)


def yaml_dump(data, _indent=0):
    pad = "  " * _indent
    lines = []
    if isinstance(data, dict):
        if not data:
            return pad + "{}\n"
        for key, val in data.items():
            if not key_ok(key):
                raise ValueError("unsafe YAML mapping key %r" % (key,))
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
                lines.append("%s- %s" % (pad, _scalar_dump(item, in_list=True)))
    return "\n".join(lines) + "\n"


def _scalar_load(s):
    s = s.strip()
    if s == "" or s in ("~", "null", "Null", "NULL"):
        return None
    if s in ("true", "True", "TRUE"):
        return True
    if s in ("false", "False", "FALSE"):
        return False
    if len(s) >= 2 and s[0] == s[-1] == '"':
        try:
            return json.loads(s)  # the dumper's own JSON-escaped form
        except ValueError:
            return s[1:-1]  # a hand-written YAML-only escape (\x41, \e): kept verbatim
    if len(s) >= 2 and s[0] == s[-1] == "'":
        return s[1:-1].replace("''", "'")
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
    """JSON objects from an append-only buffer. A malformed or non-object line is skipped with a
    warning instead of raising: one bad append must not crash sync/health on every edition."""
    if not os.path.exists(path):
        return []
    out = []
    with open(path) as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                rec = None
            if isinstance(rec, dict):
                out.append(rec)
            else:
                print("WARN %s:%d: skipped malformed line %r" % (path, n, line[:120]), file=sys.stderr)
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

# candidates.jsonl `reach` hint -> registry reach. The scout writes "proxy-needed" when the
# EVALUATOR's egress could not fetch the page -- an allowlist wall (ERR:56 / CONNECT 403 on nearly
# every host), not a site verdict: all 67 scout records carry it, while seven of them (ethz.ch,
# epfl.ch, psi.ch, unige.ch, empa.ch, wsl.ch, unibe.ch) were later re-verified direct. A wrong
# `direct` self-heals (fetch.py falls back to the proxy; metrics' reach_drift proposes the flip
# from writer telemetry); a wrong `proxy` sticks (its probe method makes writers run
# `fetch.py --proxy`, which never tries curl, and reach_drift only detects direct -> proxy).
# The hint is kept verbatim in the lifecycle note either way.
CANDIDATE_REACH = {"direct": "direct", "proxy": "proxy", "proxy-needed": "direct"}
_HOST_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+$")


def normalize_domain(raw):
    """A bare lowercase registry key (www./trailing dot stripped), or None when `raw` is not a
    host at all (a URL, a host:port, whitespace) -- such a key would fail the schema suite."""
    d = str(raw or "").strip().lower().rstrip(".")
    if d.startswith("www."):
        d = d[4:]
    return d if _HOST_RE.match(d) else None


def _candidate_probe(domain, url, reach):
    """A probe block from a scout record's vetted page/feed URL, or None unless the URL is
    absolute http(s) on the domain itself or one of its subdomains (stricter than the schema's
    last-two-labels check, which lets any *.ac.uk host pass for any *.ac.uk domain)."""
    from urllib.parse import urlparse
    if not isinstance(url, str) or not re.match(r"^https?://", url):
        return None
    host = (urlparse(url).hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if not _under(host, domain):
        return None
    return {"url": url, "method": REACH_METHOD.get(reach, "curl")}


def _scout_fetched(rec):
    """True only for a scout record whose page the scout actually fetched. A `proxy-needed`
    hint means the evaluator's egress never reached the URL, so it is unverified: the
    2026-11-27 sweep found 7 of 80 such scout URLs dead (404 / dead host). Those stay in
    the lifecycle note and never become a probe, which preflight would hand to writers."""
    return rec.get("via") == "scout" and rec.get("reach") in ("direct", "proxy")


def _candidate_note(rec, url):
    parts = ["via %s" % (rec.get("via") or "unknown")]
    if rec.get("reach"):
        parts.append("reach hint %s" % rec["reach"])
    note = str(rec.get("note") or "").strip()
    if note:
        parts.append(note)
    if url:
        parts.append(url)
    return "; ".join(parts)


AUTO_REACH_WINDOW_DAYS = 7


def _load_metrics():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evaluator", "metrics.py")
    spec = importlib.util.spec_from_file_location("_metrics_for_sync", os.path.normpath(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def auto_reach_flips(root, reg, today):
    """Bounded auto-apply of the evaluator's computed reach drift (2026-11-27). A `reach: direct`
    entry flips to proxy when metrics.build_reach_drift's rule (0 curl successes, >= 3 proxy
    successes, >= 1 failure) holds in BOTH 7-day windows ending YESTERDAY. Excluding today makes
    every same-day edition compute the same flips with the same note, so concurrent desks write
    identical hunks. A curl probe moves to method proxy with it (validate pins the pair); class,
    tier and status are never touched, and the reverse direction (proxy -> direct) stays a
    human judgment. Mutates `reg` and returns the flipped domains; any error returns [] --
    a publish must never fail on telemetry."""
    try:
        m = _load_metrics()
        end = datetime.date.fromisoformat(today) - datetime.timedelta(days=1)
        windows = []
        for k in (0, 1):
            w_end = end - datetime.timedelta(days=AUTO_REACH_WINDOW_DAYS * k)
            w_start = w_end - datetime.timedelta(days=AUTO_REACH_WINDOW_DAYS - 1)
            drift = m.build_reach_drift(root, m.window_feeds(root, w_start.isoformat(),
                                                             w_end.isoformat()))
            windows.append(({d["domain"]: d for d in drift.get("flips", [])}, w_start, w_end))
    except Exception as exc:  # noqa: BLE001 -- degrade, never block the publish
        print("sync: auto reach flip skipped (%s)" % exc, file=sys.stderr)
        return []
    (cur, s0, e0), (prev, s1, e1) = windows
    flipped = []
    for domain in sorted(cur):
        rec = reg.get(domain)
        if (domain not in prev or not isinstance(rec, dict) or rec.get("reach") != "direct"
                or rec.get("status") == "retired"):
            continue
        rec["reach"] = "proxy"
        probe = rec.get("probe")
        if isinstance(probe, dict) and probe.get("method") != REACH_METHOD["proxy"]:
            probe["method"] = REACH_METHOD["proxy"]
        lifecycle_append(rec, today, "reach-flip", note=(
            "direct -> proxy (auto); writer telemetry 0 ok-curl / %d ok-proxy / %d fail %s..%s "
            "and 0 ok-curl / %d ok-proxy / %d fail %s..%s -- registry.py sync"
            % (cur[domain]["ok_proxy"], cur[domain]["fail"], s0, e0,
               prev[domain]["ok_proxy"], prev[domain]["fail"], s1, e1)))
        flipped.append(domain)
    return flipped


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
    fresh = {}  # domain -> entry created by THIS sync; later records for it merge in
    for rec in read_jsonl(candidates_path):
        domain = normalize_domain(rec.get("domain"))
        stream = rec.get("stream")
        if domain is None or stream not in LIVE_STREAMS:
            print("sync: WARN skipped candidate %r (bad domain, or stream %r not live)"
                  % (rec.get("domain"), stream), file=sys.stderr)
            continue
        if domain in reg and domain not in fresh:
            continue  # never downgrades an already-registered domain back to candidate
        cited = rec.get("via") != "scout"  # a scout vets a page; it cites nothing
        url = rec.get("url") if isinstance(rec.get("url"), str) else None
        first_seen = rec.get("first_seen") if cited else None
        if domain in fresh:  # a second record for a domain this sync just added
            entry = fresh[domain]
            if stream not in entry["streams"]:
                entry["streams"].append(stream)  # append: streams[0] stays the creation stream
            if first_seen and (not entry.get("last_cited") or first_seen > entry["last_cited"]):
                entry["last_cited"] = first_seen
            if "probe" not in entry and _scout_fetched(rec):
                probe = _candidate_probe(domain, url, entry["reach"])
                if probe:
                    entry["probe"] = probe
                    entry["lifecycle"] = entry.pop("lifecycle")  # canonical order: lifecycle last
            note = str(rec.get("note") or "").strip()
            item = entry["lifecycle"][0]
            if note and note not in item.get("note", ""):
                item["note"] = "%s | %s" % (item.get("note", ""), note)
            continue
        cls = classify_domain(domain)
        reach = CANDIDATE_REACH.get(rec.get("reach"), "direct")
        entry = {
            "class": cls,
            "tier": "T1" if cls == "hub" else "T2",
            "status": "candidate",
            "reach": reach,
            "streams": [stream],
            "last_cited": first_seen,
        }
        probe = _candidate_probe(domain, url, reach) if _scout_fetched(rec) else None
        if probe:
            entry["probe"] = probe
        lifecycle_append(entry, today, "candidate", status="candidate",
                         note=_candidate_note(rec, url))
        reg[domain] = fresh[domain] = entry
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
    # an unchanged file can't merge-conflict, so the residual same-day race shrinks to the
    # both-editions-added-a-domain case -- not rare: 6 of 16 Tue/Fri News+AI/ML slots in
    # 2026-10/11 -- which publish.py's retry resolves with `registry.py resolve`. The buffers are still PURGED: every
    # entry provably folded to nothing (candidate already registered, last_cited not
    # newer), and leaving them would inflate candidates_open in source-health forever.
    flipped = auto_reach_flips(root, reg, today)
    if added == 0 and folded == 0 and not flipped:
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

    print("sync: %d new candidate(s), %d last_cited fold(s), %d auto reach flip(s)%s"
          % (added, folded, len(flipped), (" (" + ", ".join(flipped) + ")") if flipped else ""))
    return 0


# --- conflict resolution (2026-11) ------------------------------------------------------------
# News and AI/ML share the Tue/Fri slot; when both append a new candidate at EOF, the second
# desk's `pull --rebase` stops on sources/registry.yml with a textual conflict whose answer is
# mechanical. On all six 2026-10/11 conflict days both desks had appended new candidates
# (+1 or +2 each): pure EOF appends. merge_registry() is a 3-way merge on the parsed records
# that keeps both sides' additions and reconciles a record both sides edited field by field.

def _union_list(a, b):
    out = list(a or [])
    for x in (b or []):
        if x not in out:
            out.append(x)
    return out


def merge_registry(base, ours, theirs):
    """3-way merge of parsed registry dicts. In a rebase `ours` is upstream (already on origin)
    and `theirs` is this edition. A domain either side added is kept; a record only one side
    edited takes that side; both edited -> last_cited is the max, list fields are unioned,
    any other field keeps upstream's value."""
    import copy
    out = copy.deepcopy(ours)
    for domain, t in theirs.items():
        b = base.get(domain)
        if t == b:
            continue
        o = out.get(domain)
        if o is None:
            if b is None:
                out[domain] = copy.deepcopy(t)
            continue
        if o == b or not isinstance(o, dict) or not isinstance(t, dict):
            out[domain] = copy.deepcopy(t)
            continue
        merged = copy.deepcopy(o)
        for key, tv in t.items():
            bv = (b or {}).get(key) if isinstance(b, dict) else None
            ov = o.get(key)
            if tv == bv or tv == ov:
                continue
            if ov == bv:
                merged[key] = copy.deepcopy(tv)
            elif key == "last_cited":
                merged[key] = max(x for x in (ov, tv) if x)
            elif isinstance(ov, list) and isinstance(tv, list):
                merged[key] = _union_list(ov, tv)
        out[domain] = merged
    return out


def cmd_resolve(args):
    """Resolve an unmerged sources/registry.yml left by a stopped rebase/merge, in place, and
    stage it. A no-op (exit 0) when the file is not unmerged; exit 1 when a stage is missing
    or does not parse, leaving the conflict for the caller's unmerged-index check."""
    import subprocess
    rel = os.path.join("sources", "registry.yml")
    unmerged = subprocess.run(["git", "ls-files", "-u", "--", rel], cwd=args.root,
                              capture_output=True, text=True).stdout.strip()
    if not unmerged:
        print("resolve: %s is not unmerged; nothing to do" % rel)
        return 0
    stages = {}
    for n in (1, 2, 3):
        proc = subprocess.run(["git", "show", ":%d:%s" % (n, rel)], cwd=args.root,
                              capture_output=True, text=True)
        if proc.returncode != 0:
            print("resolve: stage %d of %s missing; left unresolved" % (n, rel))
            return 1
        loaded = yaml_load(proc.stdout) if proc.stdout.strip() else {}
        if not isinstance(loaded, dict):
            print("resolve: stage %d of %s does not parse; left unresolved" % (n, rel))
            return 1
        stages[n] = loaded
    merged = merge_registry(stages[1], stages[2], stages[3])
    with open(os.path.join(args.root, rel), "w") as f:
        f.write(yaml_dump(merged))
    subprocess.run(["git", "add", "--", rel], cwd=args.root, check=False)
    added = sorted(set(merged) - set(stages[2]))
    print("resolve: %s merged (%d record(s) from this edition kept: %s)"
          % (rel, len(added), ", ".join(added) or "edits only"))
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

    r = sub.add_parser("resolve", help="3-way merge an unmerged sources/registry.yml and stage it")
    r.add_argument("--root", default=".")
    r.set_defaults(func=cmd_resolve)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
