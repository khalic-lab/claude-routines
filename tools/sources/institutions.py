#!/usr/bin/env python3
"""Institutions ledger -- SPIKE-2026-07-10-affiliation-element §D4.

`sources/institutions.yml` is the paper-provenance twin of `sources/registry.yml`: one record
per canonical institution name cited in a paper byline (class/status/streams/first_seen/
last_cited/citations/lifecycle audit trail). Where the domain registry tracks WHERE we read,
this tracks WHO wrote the papers we kept -- the substrate the "reliable sources" judgment
accrues on. Deliberately NO imported prestige rank (CSRankings / Nature Index were considered
and rejected -- see the SPIKE §3c): status is earned by citation history, exactly like domains.

`sync` folds the affiliations already recorded on index/stories/*.jsonl records (writer-
supplied at Step C, or affil-backfill-patched) into the YAML. Bookkeeping is per-EDITION:
`meta.synced_editions` remembers which {date}-{slug} files have been counted, so re-running
sync after a same-day second edition counts only the new one, and running it twice is a no-op
(the list is pruned to the index retention window -- a pruned index file can't be recounted).
Only LIVE_STREAMS editions count (registry.py C18 posture: retired streams don't fossilize
into a founding ledger).

`aliases:` (hand-curated, optional) folds name variants into one canonical entry -- e.g.
`Massachusetts Institute of Technology: MIT`. Applied on every sync; an existing entry whose
key becomes an alias is merged into the canonical entry (citations summed, streams unioned,
earliest first_seen kept) with an `alias-fold` lifecycle event, so adding an alias later is
self-healing. `class` (frontier-lab / university / industry / government / independent /
unknown) is hand-curated too -- sync only ever writes `unknown` and never overwrites yours.

Stdlib only, no network (routine sandboxes have no PyYAML) -- reuses registry.py's yamllite
dialect (block maps/sequences only; keys must not contain ':').

Usage: institutions.py sync [--root PATH]            (first run bootstraps the file)
       institutions.py sync-prompts [--check]        (mirror aliases: into the writer prompts'
                                                      shared partial; --check = drift guard,
                                                      enforced by the spec suite)
"""
import argparse
import datetime
import os
import sys

import registry

LIVE_STREAMS = registry.LIVE_STREAMS
ESTABLISHED_MIN_CITATIONS = registry.ESTABLISHED_MIN_CITATIONS
SYNCED_EDITIONS_KEEP_DAYS = 60  # > dedup KEEP_DAYS(40): a pruned index file can't be recounted


def institutions_path(root):
    return os.path.join(root, "sources", "institutions.yml")


def _load(root):
    path = institutions_path(root)
    if not os.path.exists(path):
        return {"meta": {"synced_editions": []}, "aliases": {}, "institutions": {}}
    with open(path) as f:
        data = registry.yaml_load(f.read()) or {}
    data.setdefault("meta", {}).setdefault("synced_editions", [])
    data.setdefault("aliases", {})
    data.setdefault("institutions", {})
    if data["meta"]["synced_editions"] is None:
        data["meta"]["synced_editions"] = []
    if data["aliases"] is None:
        data["aliases"] = {}
    return data


def _dump(root, data):
    # stable order: meta, aliases (omitted while empty -- yamllite has no flow collections),
    # institutions sorted by name
    out = {"meta": {"synced_editions": sorted(set(data["meta"]["synced_editions"]))}}
    if data["aliases"]:
        out["aliases"] = dict(sorted(data["aliases"].items()))
    out["institutions"] = dict(sorted(data["institutions"].items()))
    path = institutions_path(root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(registry.yaml_dump(out))
    return path


def _merge(canon_entry, folded_entry, today):
    canon_entry["citations"] = int(canon_entry.get("citations") or 0) + int(folded_entry.get("citations") or 0)
    canon_entry["streams"] = sorted(set(canon_entry.get("streams") or []) | set(folded_entry.get("streams") or []))
    for k, pick in (("first_seen", min), ("last_cited", max)):
        vals = [v for v in (canon_entry.get(k), folded_entry.get(k)) if v]
        if vals:
            canon_entry[k] = pick(vals)
    canon_entry.setdefault("lifecycle", []).append({"date": today, "event": "alias-fold"})


def _apply_aliases(data, today):
    """Fold any institutions entry whose key is now an alias into its canonical entry."""
    aliases = data["aliases"] or {}
    inst = data["institutions"]
    for variant, canon in list(aliases.items()):
        if variant in inst:
            entry = inst.pop(variant)
            if canon in inst:
                _merge(inst[canon], entry, today)
            else:
                inst[canon] = entry
                entry.setdefault("lifecycle", []).append(
                    {"date": today, "event": "alias-fold", "note": f"renamed from {variant}"})


def cmd_sync(args):
    root = args.root
    today = datetime.date.today().isoformat()
    data = _load(root)
    bootstrap = not os.path.exists(institutions_path(root))
    aliases = data["aliases"] or {}
    inst = data["institutions"]
    synced = set(data["meta"]["synced_editions"])

    _apply_aliases(data, today)

    counted_editions, new_citations = set(), 0
    for rec in registry.load_story_records(root):
        stream = rec.get("stream")
        date = rec.get("date")
        affs = rec.get("affiliations")
        if not (stream in LIVE_STREAMS and date and affs):
            continue
        edition = f"{date}-{stream}"
        if edition in synced:
            continue
        counted_editions.add(edition)
        for name in affs:
            name = str(name).strip()
            # yamllite keys can't contain ':' and a leading '-' reads as a sequence item;
            # such a "name" is a malformed byline capture anyway -- skip, never crash the step
            if not name or ":" in name or name.startswith("-"):
                continue
            name = aliases.get(name, name)
            e = inst.get(name)
            if e is None:
                e = inst[name] = {
                    "class": "unknown", "status": "probation",
                    "streams": [], "first_seen": date, "last_cited": date, "citations": 0,
                    "lifecycle": [{"date": today,
                                   "event": "bootstrap" if bootstrap else "first-cited",
                                   "status": "probation"}],
                }
            e["citations"] = int(e.get("citations") or 0) + 1
            new_citations += 1
            e["streams"] = sorted(set(e.get("streams") or []) | {stream})
            e["first_seen"] = min(e.get("first_seen") or date, date)
            e["last_cited"] = max(e.get("last_cited") or date, date)

    # earned promotion, registry-style: probation -> established at the citation floor
    promoted = 0
    for name, e in inst.items():
        if e.get("status") == "probation" and int(e.get("citations") or 0) >= ESTABLISHED_MIN_CITATIONS:
            e["status"] = "established"
            e.setdefault("lifecycle", []).append(
                {"date": today, "event": "promoted", "status": "established"})
            promoted += 1

    cutoff = (datetime.date.today()
              - datetime.timedelta(days=SYNCED_EDITIONS_KEEP_DAYS)).isoformat()
    data["meta"]["synced_editions"] = [
        ed for ed in (synced | counted_editions) if ed[:10] >= cutoff]

    path = _dump(root, data)
    print(f"institutions sync: +{new_citations} citation(s) from {len(counted_editions)} "
          f"edition(s), {promoted} promoted, {len(inst)} institution(s) -> {path}")


# --------------------------------------------------------------------------- #
# sync-prompts: mirror the aliases map into the writer prompts' shared partial
# --------------------------------------------------------------------------- #
PARTIAL_RELPATH = os.path.join("routines", "_shared", "affiliations.md")
_BLOCK_RE = None  # compiled lazily to keep the module import-light


def render_alias_block(aliases):
    """The canonical-names list as markdown bullet lines, variants grouped per canonical."""
    if not aliases:
        return "- (no aliases on file yet)"
    by_canon = {}
    for variant, canon in aliases.items():
        by_canon.setdefault(canon, []).append(variant)
    return "\n".join(
        "- " + " / ".join(f"`{v}`" for v in sorted(by_canon[c])) + f" → **{c}**"
        for c in sorted(by_canon))


def sync_prompts_text(partial_text, aliases):
    """Return partial_text with the generated canonical-names block replaced. Raises
    ValueError if the marker pair is missing (someone deleted the generated block)."""
    global _BLOCK_RE
    if _BLOCK_RE is None:
        import re
        _BLOCK_RE = re.compile(
            r"(<!-- canonical-names:begin[^\n]*-->\n).*?(<!-- canonical-names:end -->)",
            re.S)
    block = render_alias_block(aliases) + "\n"
    new_text, n = _BLOCK_RE.subn(lambda m: m.group(1) + block + m.group(2), partial_text)
    if n != 1:
        raise ValueError(f"canonical-names markers not found (expected 1 pair, got {n})")
    return new_text


def cmd_sync_prompts(args):
    """Regenerate the canonical-names block in routines/_shared/affiliations.md from the
    ledger's aliases map. --check verifies without writing (exit 1 on drift) — the spec
    suite runs it against the committed tree, so alias edits can't silently go stale in
    the prompts. After a real sync, re-run `python3 routines/assemble.py`."""
    data = _load(args.root)
    path = os.path.join(args.root, PARTIAL_RELPATH)
    with open(path) as f:
        cur = f.read()
    new = sync_prompts_text(cur, data["aliases"] or {})
    if args.check:
        if cur != new:
            print(f"DRIFT: {PARTIAL_RELPATH} canonical-names block no longer matches "
                  f"sources/institutions.yml aliases — run sync-prompts + assemble.py")
            sys.exit(1)
        print("sync-prompts check: OK")
        return
    if cur == new:
        print("sync-prompts: already in sync")
        return
    with open(path, "w") as f:
        f.write(new)
    print(f"sync-prompts: rewrote canonical-names block in {PARTIAL_RELPATH} "
          f"({len((data['aliases'] or {}))} alias(es)) — now run `python3 routines/assemble.py`")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sync", help="fold index-record affiliations into sources/institutions.yml")
    s.add_argument("--root", default=".")
    s.set_defaults(func=cmd_sync)
    sp = sub.add_parser("sync-prompts",
                        help="mirror the aliases map into routines/_shared/affiliations.md")
    sp.add_argument("--root", default=".")
    sp.add_argument("--check", action="store_true",
                    help="verify only; exit 1 if the prompt block has drifted")
    sp.set_defaults(func=cmd_sync_prompts)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
