#!/usr/bin/env python3
"""Per-story anchors (SPIKE-2026-07-07 §3.3.3): key each cited story in a published
post to its store id so feedback and the homefeed can target it.

- '- ' bullets: insert '<a id="st-…" class="st-a"></a>' right after the dash-space,
  keyed on the bullet's FIRST markdown-link URL (bullet line + indented continuations).
- '### ' headings: append a kramdown IAL ' {#st-…}' keyed on the first URL anywhere
  in the heading's block (up to the next heading). A heading that already ends in an
  IAL (custom, e.g. '{#my-id}', or a prior '{#st-…}') is left untouched -- appending a
  second one corrupts the heading under kramdown.
Linkless bullets/headings are skipped. Idempotent: already-anchored lines are left
byte-identical. Prints one 'url -> st-id' line per (would-be) anchor.

--index <index/stories/{date}-{slug}.jsonl> (optional): the ledger's `publish` events key
on a story's *recorded* url (from that file), which is not always the block's first link
(e.g. a bullet that opens on a background/corroborating link before its primary source).
When given, each block's links are matched against the file's recorded urls (by norm_url)
and the MATCHED record's own url is used for the id; the block's first link is only a
fallback when nothing in it matches a recorded story (or when --index is omitted).

Usage: python3 tools/store/anchor.py [--check] [--index PATH] <post.md> [...]
       # --check = report-only
"""
import importlib.util
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("_store_for_anchor",
                                               os.path.join(_HERE, "store.py"))
_store = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_store)
story_id = _store.story_id
norm_url = _store.norm_url

LINK_RE = re.compile(r"\[[^\]]*\]\((https?://[^)\s]+)\)")
HEAD_RE = re.compile(r"^#{1,6} ")
# Any pre-existing IAL -- our own '{#st-…}' from a prior run (idempotence) OR a custom
# kramdown id someone already gave the heading (e.g. '{#my-id}') -- must stop us from
# appending a second one.
IAL_RE = re.compile(r"\{#[^{}\s]+\}\s*$")
ANCHOR_MARK = 'class="st-a"'


def _urls_in_block(lines):
    """All markdown-link URLs anywhere in the block, in document order."""
    urls = []
    for line in lines:
        urls.extend(m.group(1) for m in LINK_RE.finditer(line))
    return urls


def load_index(path):
    """Load an index/stories/{date}-{slug}.jsonl file into a norm_url -> record map."""
    index_map = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            url = rec.get("url")
            if url:
                index_map[norm_url(url)] = rec
    return index_map


def _select_url(urls, index_map):
    """Pick the url to key the story id on: prefer a link that matches a recorded story's
    norm_url (using the RECORD's own url, never the raw link text, so the anchor and the
    ledger's publish event stay keyed identically) -- fall back to the block's first link
    when no index is given or nothing in the block matches a recorded story."""
    if index_map:
        for u in urls:
            rec = index_map.get(norm_url(u))
            if rec and rec.get("url"):
                return rec["url"]
    return urls[0]


def anchor_text(text, index_map=None):
    """Return (new_text, [(url, sid), ...]) — table lists newly anchored stories only.
    index_map (norm_url -> record, from --index) lets a block's citation be matched against
    a recorded story even when it isn't the block's first link -- see _select_url."""
    lines = text.split("\n")
    table = []
    for i, line in enumerate(lines):
        if line.startswith("### "):
            if IAL_RE.search(line):
                continue
            block = [line]
            j = i + 1
            while j < len(lines) and not HEAD_RE.match(lines[j]):
                block.append(lines[j])
                j += 1
            urls = _urls_in_block(block)
            if not urls:
                continue
            url = _select_url(urls, index_map)
            sid = story_id(url)
            lines[i] = line + " {#%s}" % sid
            table.append((url, sid))
        elif line.startswith("- "):
            if ANCHOR_MARK in line:
                continue
            block = [line]
            j = i + 1
            while j < len(lines) and lines[j][:1] in (" ", "\t"):  # indented continuations
                block.append(lines[j])
                j += 1
            urls = _urls_in_block(block)
            if not urls:
                continue
            url = _select_url(urls, index_map)
            sid = story_id(url)
            lines[i] = '- <a id="%s" class="st-a"></a>%s' % (sid, line[2:])
            table.append((url, sid))
    return "\n".join(lines), table


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    check = "--check" in argv
    index_map = None
    if "--index" in argv:
        i = argv.index("--index")
        index_map = load_index(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    paths = [a for a in argv if a != "--check"]
    if not paths:
        print("usage: anchor.py [--check] [--index PATH] <post.md> [...]", file=sys.stderr)
        return 2
    for path in paths:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        new_text, table = anchor_text(text, index_map)
        for url, sid in table:
            print("%s -> %s" % (url, sid))
        if not check and new_text != text:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
