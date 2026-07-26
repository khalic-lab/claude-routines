#!/usr/bin/env python3
"""Build the homepage story feed (_data/homefeed.json) from the published briefs.

The Folio homepage renders individual STORIES as a masonry grid with topic filters and
importance-sized cards. It shows the writers' actual explanatory prose — so this reads the
`_posts/*.md` briefs (where the insightful multi-sentence body lives), NOT the dedup index
(whose `summary` is a terse one-liner built for embedding). It flattens the four live streams'
recent stories into `_data/homefeed.json` that the `home` layout iterates at build time.

Per-story `topics` + `importance` come from the dedup index record when the writer supplied them
— joined by canonical URL first (stable across both sides), story-id slug second (the post's bold
lead and the record's `headline` are worded independently, so the slug join alone missed ~72% of
stories). The join rate is printed on every run so a silent regression is visible. When no record
matches, they're derived: topic from the brief's section heading (falling back to keywords),
importance from position within the brief. Pure stdlib, no network.

The `--max` cap is per-edition-quota'd: over the cap, the largest editions lose their
least-important tail stories first, and no edition drops below MIN_PER_EDITION — so a dense
Weekend brief can't evict the weekly Science edition from the page.

`feed["board"]` is the ONE ranked sequence the page renders — stories and editorials in a single
order, `(date, tier, position)` with editorials ranked below briefs so each closes its own
edition's date block (see build_board). `feed["stories"]`, `feed["editorials"]` and `feed["count"]`
keep their exact meanings; nothing else reads position semantics.

Run after `dedup.py record` (DEDUP.md Step D) and commit the result with the brief.
Usage: python3 tools/build_stories_feed.py [--days 14] [--max 80] [--out _data/homefeed.json]
                                           [--strict-parity]
"""
import argparse
import datetime as _dt
import glob
import importlib.util
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(ROOT, "_posts")
INDEX_DIR = os.path.join(ROOT, "index", "stories")
DEFAULT_OUT = os.path.join(ROOT, "_data", "homefeed.json")

# story_id: st-{sha1(norm_url)[:12]} (SPIKE-2026-07-07 §3.6, store.py::story_id). Loaded by
# path, not package-imported: tools/ has no __init__.py and this script also runs standalone
# (python3 tools/build_stories_feed.py) with no package context to import a sibling from.
_store_spec = importlib.util.spec_from_file_location(
    "_story_store", os.path.join(os.path.dirname(os.path.abspath(__file__)), "store", "store.py"))
_store = importlib.util.module_from_spec(_store_spec)
_store_spec.loader.exec_module(_store)
story_id = _store.story_id


def _safe_story_id(url):
    """story_id(url), or None for a falsy or degenerate-but-truthy url (e.g. a bare
    'https://' scheme with no host, which norm_url reduces to an empty string) -- story_id
    raises ValueError on that, and one malformed link must never crash the whole feed build."""
    if not url:
        return None
    try:
        return story_id(url)
    except ValueError:
        return None


_FILE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})-([a-z0-9-]+)\.md$")
_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

STREAM_LABEL = {"news": "News", "ai-ml": "AI/ML", "science": "Science", "weekend": "Weekend", "sports": "Sports"}
CURRENT_STREAMS = {"news", "ai-ml", "science", "weekend", "sports"}

# controlled topic vocabulary — MUST mirror the tagging rubric in
# routines/_shared/newsroom-ethos.md and DEDUP.md Step C (an out-of-vocab writer tag is dropped
# by topic_for's validity filter and falls back to keywords). key -> (label, dot color).
# Colors are per-beat MARKERS only, never the page accent.
TOPICS = {
    "switzerland": ("Switzerland", "#c2454a"),
    "geopolitics": ("Geopolitics", "#c0563b"),
    "politics":    ("Politics",    "#9a6a34"),
    "economy":     ("Economy",     "#9a7b2e"),
    "ai-ml":       ("AI / ML",     "#2f7d8c"),
    "science":     ("Science",     "#4c6b3c"),
    "health":      ("Health",      "#a44a72"),
    "security":    ("Security",    "#6a4b8a"),
    "tech":        ("Tech",        "#3b6ea5"),
    "sports":      ("Sports",      "#c26b2e"),
    "world":       ("World",       "#6b6f76"),
}

# section-heading -> topic (checked first; the brief's own section is the best signal we have).
_SECTION_RULES = [
    ("switzerland", ["switzerland", "vaud"]),
    ("geopolitics", ["world polit", "geopolit", "international", "nahost", "middle east"]),
    ("economy",     ["market", "econom", "finance"]),
    ("ai-ml",       ["ml/ai", "ai research", "ml / ai", "ai papers", "models &", "benchmark",
                     "data science", "apple silicon", "lab blog", "release"]),
    ("science",     ["physic", "chemistr", "math", "quantum", "astronom", "cosmolog", "biolog",
                     "medicine", "neuroscience", "biotech", "fundamental science"]),
]
# per-story keyword fallback for mixed sections (Week in headlines, Cross-cutting threads, ...).
# geopolitics is checked BEFORE security: war coverage mentions drones/strikes constantly, and the
# bare 'drone' keyword was misfiling Russia-Ukraine stories under Security.
_KEYWORD_RULES = [
    ("switzerland", ["swiss", "switzerland", "bern", " vaud", "geneva", "zurich", "ticino", "canton", "srf"]),
    ("geopolitics", ["nato", "china", "russia", "ukraine", "iran", "israel", "gaza", "missile",
                     "summit", "war", "kyiv", "treaty", "settlement"]),
    ("security",    ["drone", "cyber", "espionage", "hack", "breach", "spyware"]),
    ("ai-ml",       ["arxiv", " llm", "transformer", "gpt", "deepseek", "neural", "rlhf", "fine-tun"]),
    ("politics",    ["election", "trump", "president", "parliament", "impeachment", "senate", "midterm"]),
    ("economy",     ["job", "inflation", "market", "credit", "tax", "trade", "payroll", "fund", "bn "]),
    ("health",      ["vaccine", "hiv", "antibody", "cancer", "clinical", "disease", "outbreak", "primate"]),
    ("science",     ["physics", "quantum", "graphene", "black hole", "genome", "telescope", "matroid"]),
]
_HEALTH_KW = ["vaccine", "hiv", "antibody", "cancer", "clinical", "disease", "primate", "immune", "bnab"]

# Step C.25 (tools/store/anchor.py) rewrites bullets to '- <a id="st-…" class="st-a"></a>**…'
# and appends '{#st-…}' kramdown IALs to ### headings BEFORE Step D parses the post — every
# matcher here must read both the anchored and the bare form (2026-07-07 regression: both
# editions published anchored and the feed harvested zero stories from them).
# THE ANCHOR STUB IS STRUCTURE, WHATEVER ID IT CARRIES. This used to demand the canonical
# `st-<12 hex>` shape inline, so a bullet anchored with any other id did not match as a bullet
# AT ALL -- the optional group failed, `**` was no longer at the start, and the story vanished.
# `_posts/2026-07-13-news.md` carries writer-authored anchors (`st-iran-hormuz-0713`), and that
# edition therefore contributed ZERO of its 7 recorded stories to the front page. Matching the
# stub structurally recovers them; the captured id is only HONORED as a story id when it is
# canonical (see _CANON_SID_RE) -- a hand-written anchor is markup, not an identity, so those
# cards fall back to story_id(url) like every pre-anchor post does.
_ANCHOR_STUB = r'(?:<a id="([^"]*)" class="st-a"></a>\s*)?'
_CANON_SID_RE = re.compile(r"^st-[0-9a-f]{12}$")
_BULLET_RE = re.compile(r'^-\s+' + _ANCHOR_STUB + r'\*\*(.+?)\*\*\.?\s*(.*)$')
_BULLET_START_RE = re.compile(r'^-\s+' + _ANCHOR_STUB + r'\*\*')
# A PLAIN BULLET IS A STORY TOO (R4, external review 2026-07-25). The bold-lead form above is a
# CONVENTION, not the contract: routines/src/weekend.md's format block specifies "## Week in
# headlines" as bare `- ...` bullets, and three of the 2026-07-25 Weekend edition's five headline
# bullets open on prose rather than on a bold lede ("The US bombing campaign against Iran
# entered a **13th consecutive night**…"). They were recorded, anchored, embedded and
# dedup-checked, and then silently never reached the only reading surface the site still has.
# Matched only AFTER _BULLET_RE fails, so every bold-lead bullet keeps its exact current parse.
# A PLAIN BULLET MUST CITE A SOURCE, and that is the whole guard against harvesting prose that
# was never a story: this page's contract is that a story carries the link it came from, so a
# linkless bullet is a desk aside (2026-07-18's "the most relevant on-device item this week is
# community-side …") or a roundup label, and it stays out. The bold-lead form keeps its existing
# licence to be linkless -- widening THAT is not what this fixes.
_BULLET_PLAIN_RE = re.compile(r'^-\s+' + _ANCHOR_STUB + r'(\S.*)$')
# Sentence end for the derived headline: the terminator must FOLLOW ordinary word/clause material
# and be followed by space or EOL, which is what keeps "12.5%" and "U.S." and "arXiv:2607.19854"
# from splitting a sentence in half.
_SENT_END_RE = re.compile(r'(?<=[a-z0-9)\]"\'%”’])[.!?](?=\s|$)')
HEADLINE_CAP = 90
_H2_RE = re.compile(r"^##\s+(.*)$")
_H3_RE = re.compile(r"^###\s+(.*)$")
_H3_IAL_RE = re.compile(r"\s*\{#([^}]+)\}\s*$")
_URL_RE = re.compile(r"https?://[^\s)\]]+")
_TAG_RE = re.compile(r"`?\[(single-source|via snippet|preprint|disputed|vendor pr|ongoing since[^\]]*)\]`?", re.I)
_META_ITALIC_RE = re.compile(r"\s*_[^_]*(?:announced|submitted|published|reported)[^_]*_\s*", re.I)


def _strip_md(text):
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)   # [text](url) -> text
    return text.replace("**", "").replace("*", "").replace("`", "").strip(" .")


_CITE_PAREN_RE = re.compile(
    r"\s*\([^()]*(?:\d{4}-\d{2}-\d{2}|\b\d{1,2}\s+[A-Z][a-z]{2,8}\s+\d{4}|\b[A-Z][a-z]{2,8}\s+\d{4})[^()]*\)")


def clean_body(text):
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)   # links -> text FIRST (delinks citations too)
    text = _TAG_RE.sub("", text)                          # [single-source] / [via snippet] / `[preprint]`
    text = _CITE_PAREN_RE.sub("", text)                   # (Source, 6 Jul 2026; Other, 2026-07-04) citations
    text = _META_ITALIC_RE.sub(" ", text)                 # _Announced …_ / _submitted …_
    text = text.replace("**", "").replace("*", "").replace("`", "")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^[\s—–-]+", "", text)               # drop a leading dash lead-in ("— the week's…")
    return text


def _is_meta(p):
    """A citation / author / date byline, not story prose."""
    p = p.strip()
    if not p:
        return True
    if re.match(r"^\*{0,2}\[", p):                      # leading link: **[Nature](…) or [arXiv…]
        return True
    if re.match(r"^[—–]\s*\**\[", p):        # em-dash INTO a citation: "— [arXiv…] · authors" (not "— prose")
        return True
    low = p.lower()
    # author-list shapes, with or without a middot delimiter (peer-reviewed papers' bylines have
    # no `· [preprint]` tag, so requiring the middot let 'A, B, C et al. (…)' pass as story prose)
    if re.search(r"\bet al\b|affiliations not listed|senior author", low):
        return True
    if " · " in p:                                      # middot-separated byline / citation line
        if re.search(r"arxiv|preprint|published|submitted|reported|affiliation|university|institute", low):
            return True
        if p.count(" · ") >= 2:                         # author · source · date
            return True
        if re.search(r"·\s*\d{4}(?:-\d{2}-\d{2})?\s*$", p):                     # trailing date
            return True
        if re.search(r"\b[a-z0-9-]+\.(?:com|net|org|blog|io|ai|dev|ch|co)\b", low):  # bare source domain
            return True
    return False


_WHY_RE = re.compile(r"^\*{1,2}\s*Why (?:it|this) matters:?\s*\*{0,2}\s*", re.I)


def _is_editorial_section(section):
    """True for an H2 whose text is one of the EDITORIAL sections (`Why it matters`,
    `Cross-cutting threads`) -- prose commentary, not stories, so its bullets must not be
    harvested as pseudo-stories. Those same sections are what load_editorials harvests, so the
    two readers agree on the boundary BY SHARING THE VOCABULARY rather than by two regexes that
    can drift: this resolves through `_EDITORIAL_HEADINGS`, exactly as `_editorial_heading` does.
    It replaced a bare /why it matters/ search, which covered only one of the two headings --
    survivable while every editorial bullet happened to open on a bold lede (those matched
    _BULLET_RE), and not survivable once plain bullets became stories too.
    Deliberately scoped to the bullet branch only (### paper headings never appear there)."""
    return _editorial_heading("## " + (section or "")) is not None


def _derived_headline(text):
    """A headline for a bullet that has no bold lede: its FIRST SENTENCE, capped on a word
    boundary, never mid-word, never with an ellipsis.

    NOTHING IS CROPPED BY THIS, and that is why it is allowed to cap. Unlike the bold-lead form
    -- where the lede becomes the headline and is CONSUMED out of the body -- a plain bullet's
    full text stays in the body verbatim. So this is a derived LABEL over prose that is still
    printed in full, not a truncation of what the reader gets. (Consuming was the first design
    and it is unsafe here: the Iran bullet's first sentence runs ~280 chars, so consuming it
    would have moved 190 characters of reporting into a place the card never prints.)
    In practice the index record's curated `headline` overlays this on every recorded story; this
    is the fallback for an unrecorded one, and the `hid` read-state key, so it must be stable."""
    t = clean_body(text)
    m = _SENT_END_RE.search(t)
    if m:
        t = t[:m.end()]
    t = t.rstrip(" .")
    if len(t) <= HEADLINE_CAP:
        return t
    cut = t.rfind(" ", 0, HEADLINE_CAP + 1)
    return (t[:cut] if cut > 0 else t[:HEADLINE_CAP]).rstrip(" ,;:—–-")


def _pick_body(paras):
    for p in paras:
        if _is_meta(p) or _WHY_RE.match(p.strip()):     # the why-block is its own field, not the body
            continue
        c = clean_body(p)
        if len(c) >= 40:
            return c
    for p in paras:                                     # relax the length floor
        if _WHY_RE.match(p.strip()):
            continue
        c = clean_body(p)
        if c:
            return c
    return ""


def _pick_why(paras):
    """The writers' `**Why it matters:**` (ai-ml) / `*Why it matters:*` (science) paragraph."""
    for p in paras:
        m = _WHY_RE.match(p.strip())
        if m:
            return clean_body(p.strip()[m.end():])
    return ""


def parse_post(md):
    """Return [{section, headline, body, url, raw}] for every story bullet or ### paper heading."""
    lines = md.splitlines()
    out, section, in_footer, i, n = [], "", False, 0, len(lines)

    def emit(headline, paras, anchor_sid=None):
        if headline.replace("*", "").rstrip().endswith(":"):
            return                                      # '**Datasets:** …' roundup label, not a story
        raw = " ".join(paras)
        urls = _URL_RE.findall(raw)
        out.append({"section": section, "headline": _strip_md(headline),
                    "body": _pick_body(paras), "why": _pick_why(paras),
                    "url": urls[0] if urls else None, "raw": raw,
                    "anchor_sid": anchor_sid})

    while i < n:
        line = lines[i]
        h2 = _H2_RE.match(line)
        if h2:
            sec = h2.group(1).strip()
            in_footer = "coverage footer" in sec.lower()
            if not in_footer:
                section = sec
            i += 1
            continue
        if in_footer:
            i += 1
            continue
        h3 = _H3_RE.match(line)
        if h3:                                          # heading-style story (science/weekend papers)
            paras, j = [], i + 1
            while j < n:
                nx = lines[j]
                if _H2_RE.match(nx) or _H3_RE.match(nx) or nx.startswith("# "):
                    break
                if _BULLET_START_RE.match(nx.lstrip()):
                    break
                if nx.strip():
                    paras.append(nx.strip())
                j += 1
            head = h3.group(1).strip()
            ial = _H3_IAL_RE.search(head)
            h3_sid = ial.group(1) if ial and ial.group(1).startswith("st-") else None
            emit(_H3_IAL_RE.sub("", head).strip(), paras, anchor_sid=h3_sid)
            i = j
            continue
        m = _BULLET_RE.match(line)
        plain = None if m else _BULLET_PLAIN_RE.match(line)
        if m or plain:                                  # bullet-style story (news / ai-ml / weekend headlines)
            if m:
                sid, head, first = m.group(1), m.group(2).strip(), m.group(3).strip()
            else:
                # plain bullet: the whole text is prose and STAYS prose; the headline is derived
                # from it rather than cut out of it. See _derived_headline.
                sid, body_text = plain.group(1), plain.group(2).strip()
                head, first = _derived_headline(body_text), body_text
            if not _CANON_SID_RE.match(sid or ""):
                sid = None                              # a non-canonical anchor is markup, not an id
            paras, j = [first], i + 1
            while j < n:
                nxt = lines[j]
                if nxt.startswith("#"):
                    break
                if not nxt.strip():
                    k = j + 1
                    while k < n and not lines[k].strip():
                        k += 1
                    if (k < n and lines[k][:1] in (" ", "\t") and not lines[k].lstrip().startswith("- ")):
                        j += 1
                        continue
                    break
                if nxt.lstrip().startswith("- "):
                    break
                paras.append(nxt.strip())
                j += 1
            # the source gate is checked over the WHOLE story (a wrapped bullet can carry its
            # citation on a continuation line), and only the plain form has to pass it.
            sourced = bool(m) or bool(_URL_RE.search(" ".join(paras)))
            if sourced and not _is_editorial_section(section):   # skip an editorial roundup's bullets
                emit(head, paras, anchor_sid=sid)
            i = j
            continue
        i += 1
    return out


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:48].strip("-")
    return s or "story"


def _match(text, rules, default=None):
    low = text.lower()
    for topic, kws in rules:
        if any(k in low for k in kws):
            return topic
    return default


def topic_for(story, stream, index_topics):
    if index_topics:                                    # writer-supplied (authoritative)
        valid = [t for t in index_topics if t in TOPICS]
        if valid:
            return valid
    text = story["headline"] + " " + story["body"]
    healthy = any(k in text.lower() for k in _HEALTH_KW)
    if stream == "ai-ml":                               # single-topic stream: don't let a stray keyword win
        return ["ai-ml"]
    if stream == "sports":                              # single-topic stream: the stream IS the beat
        return ["sports"]
    if stream == "science":
        return ["health"] if healthy else ["science"]
    sec = _match(story["section"], _SECTION_RULES)      # news + weekend are mixed
    if stream == "weekend" and sec:                     # weekend sections are topical (ML papers / science / …)
        return ["health"] if (sec == "science" and healthy) else [sec]
    if sec == "switzerland":                            # a Swiss-desk story is Swiss regardless of subtopic
        return ["switzerland"]
    topic = _match(text, _KEYWORD_RULES) or sec or "world"   # else finer per-story keyword
    if topic == "science" and healthy:
        topic = "health"
    return [topic]


def importance_for(pos, lead_pos, single_source, index_importance):
    if isinstance(index_importance, int) and index_importance in (1, 2, 3):
        return index_importance
    if pos == lead_pos:
        return 3
    if single_source:
        return 1
    return 2 if pos <= 3 else 1


def date_label(d):
    y, m, day = d.split("-")
    return "%s %d" % (_MONTHS[int(m) - 1], int(day))


def source_domain(url):
    if not url:
        return ""
    m = re.match(r"https?://([^/]+)", url)
    if not m:
        return ""
    host = m.group(1).lower()
    return host[4:] if host.startswith("www.") else host


def norm_url(url):
    """Canonicalize for the feed↔index join: scheme/www/fragment/utm-insensitive."""
    if not url:
        return None
    u = url.strip().split("#", 1)[0]
    u = re.sub(r"^https?://(www\.)?", "", u, flags=re.I)
    if "?" in u:
        base, q = u.split("?", 1)
        keep = [p for p in q.split("&") if p and not p.lower().startswith(("utm_", "ref=", "fbclid"))]
        u = base + ("?" + "&".join(keep) if keep else "")
    return u.rstrip("/").lower()


_INDEX_FILE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z0-9-]+)\.jsonl$")


def load_index_meta(window_dates):
    """(by_edition_url, by_id) -> overlay metadata from the dedup index, keyed by EXACT EDITION
    IDENTITY `(date, stream, norm_url)`.

    URL is still the join key — the post's bold lead and the record's `headline` are written
    independently by the routine, so slugified-headline ids only agree ~28% of the time, while
    both sides cite the same primary-source URL — but a bare URL is NOT an identity. Two editions
    legitimately re-cite one primary source (an ONGOING story; a Weekend recap of the week's
    News), and this map used to hold one record per URL for the whole window, so filesystem glob
    order silently decided which edition's curated headline/deck/body/importance every card got
    (external review 2026-07-25, R3: a 24 July News card was rendering the 25 July Weekend Iran
    framing at the Weekend's importance 2 instead of its own edition's importance 3; reversing
    the iteration changed the winner). Keying the edition in makes the join a same-edition join,
    so glob order cannot influence the result at all.

    The edition comes from the index FILENAME, which is the same authority the story side uses
    (load_recent derives date+stream from the post filename) — not from the record's own fields,
    which a mis-stamped record could disagree with.

    `by_id` needs no such fix: a record id is already `{date}-{stream}-{slug}`, so it is
    edition-scoped by construction. It stays the secondary key.

    SID is not a third key: the post's anchor sid is `story_id(norm_url)` of the RECORDED url,
    so it carries exactly the discriminating power of `norm_url` and no more — the edition is the
    part that was missing.
    """
    by_edition_url, by_id = {}, {}
    for path in sorted(glob.glob(os.path.join(INDEX_DIR, "*.jsonl"))):
        base = os.path.basename(path)
        if not any(base.startswith(d) for d in window_dates):
            continue
        fm = _INDEX_FILE_RE.match(base)
        edition = (fm.group(1), fm.group(2)) if fm else None
        with open(path) as fh:
            for ln in fh:
                if not ln.strip():
                    continue
                r = json.loads(ln)
                m = {"topics": r.get("topics"), "importance": r.get("importance"),
                     "headline": r.get("headline"), "deck": r.get("deck"),
                     "display_body": r.get("display_body"), "why": r.get("why"),
                     "affiliations": r.get("affiliations"), "url": r.get("url")}
                if r.get("id"):
                    by_id[r["id"]] = m
                nu = norm_url(r.get("url"))
                if nu and edition:
                    by_edition_url[(edition[0], edition[1], nu)] = m
    return by_edition_url, by_id


# --- editorials (2026-07-18) -----------------------------------------------------------------
# The briefs' SECTION-level synthesis prose (Weekend "Cross-cutting threads", Science/Sports
# "Why it matters") is not per-story, so it never became feed cards — and with the individual
# brief pages retired the same day, it had nowhere on the site at all. Extract those sections
# into feed["editorials"]; the homepage renders them as distinct 2-col editorial cards.
_EDITORIAL_HEADINGS = {
    "cross cutting threads": "Cross-cutting threads",
    "why it matters": "Why it matters",
}
_ED_HEAD_RE = re.compile(r"^##\s+(.*)$")
_ED_HR_RE = re.compile(r"^[-*_]{3,}$")   # markdown rule (---/***/___): separator, never prose
_ED_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
_ED_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_ED_EM_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
_ED_TAG_RE = re.compile(r"<[^>]+>")


def _editorial_heading(line):
    m = _ED_HEAD_RE.match(line)
    if not m:
        return None
    title = _strip_md(m.group(1)).strip()
    # collapse every non-letter run to one space so emoji AND hyphens normalize away
    # ("🧠 Cross-cutting threads" -> "cross cutting threads")
    key = re.sub(r"[^a-z]+", " ", title.lower()).strip()
    return _EDITORIAL_HEADINGS.get(key)


def _ed_inline_html(text):
    """Markdown -> SAFE html for one paragraph: everything escaped, then only links/bold/em
    rebuilt from the escaped text. Source HTML (e.g. anchor.py's <a id> stubs) is stripped."""
    import html as _h
    s = _ED_TAG_RE.sub("", text).replace("`", "")
    s = _h.escape(s, quote=False)
    # m.group(2) comes out of the ALREADY-escaped text (& is &amp;) -- escaping it
    # again would double-escape to &amp;amp;. Only quotes still need attribute-escaping.
    s = _ED_LINK_RE.sub(
        lambda m: '<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>'
        % (m.group(2).replace('"', "&quot;"), m.group(1)), s)
    s = _ED_BOLD_RE.sub(r"<strong>\1</strong>", s)
    s = _ED_EM_RE.sub(r"<em>\1</em>", s)
    return s.strip()


def _ed_paragraphs(lines, cap=6):
    """Section lines -> [html paragraph]: blank-line-delimited chunks, '- ' bullets split out,
    wrapped lines joined. Markdown rules (---) and fenced code blocks are structure, not prose --
    both live cards shipped a literal '---' paragraph before this filter existed."""
    paras, chunk = [], []
    fenced, fence_buf = False, []

    def flush():
        if chunk:
            paras.append(_ed_inline_html(" ".join(chunk)))
            del chunk[:]

    def consume(stripped):
        if not stripped or _ED_HR_RE.match(stripped):
            flush()
        elif stripped.startswith("- "):
            flush()
            chunk.append(stripped[2:])
            flush()
        else:
            chunk.append(stripped)

    for ln in lines:
        stripped = ln.strip()
        if stripped.startswith("```"):
            flush()
            if fenced:
                del fence_buf[:]        # closed: a genuine code block, dropped whole
            fenced = not fenced
        elif fenced:
            fence_buf.append(stripped)  # held, not dropped -- the fence may never close
        else:
            consume(stripped)
    if fenced:
        # Unmatched fence (a stray ``` mid-prose): the held lines are prose, not code --
        # silently swallowing the rest of the section was an adversarial-review catch.
        for stripped in fence_buf:
            consume(stripped)
    flush()
    return [p for p in paras if p][:cap]


_ED_LEDE_RE = re.compile(r"^(-\s+)?\*\*(.+?)\*\*\.?\s*")
ED_TITLE_CAP = 90


def _ed_title(lines):
    """(title, lines) -- the editorial's own opening bold lede, taken as the card title and
    CONSUMED out of the prose it opened. `("", lines)` when there is none.

    THE SCRAPED SECTION HEADING IS NOT A TITLE, and printing it as one is what put "Why it
    matters" on the front page as a headline (owner report, 2026-07-26). The heading names the
    SECTION; the desk's actual claim is the bold lede it opens with ("One nation, both trophies --
    and an era confirmed"). The heading keeps a home in the kicker, where a section name belongs.

    CONSUMED, because a title that is also the first line of the body prints the same sentence
    twice. And FIT-OR-NOTHING rather than truncated: a lede longer than ED_TITLE_CAP is left in
    the prose and the card renders titleless (no <h2> at all -- kicker + disclosure + prose).
    Capping a CONSUMED lede would delete the tail of a sentence from the only surface that prints
    it, which the never-crop ruling forbids; capping without consuming would print the opening
    twice. Neither is worth a headline, and inventing one is not on the table.
    """
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not s or _ED_HR_RE.match(s) or s.startswith("```"):
            continue                          # blank / rule / fence: not yet the first chunk
        m = _ED_LEDE_RE.match(s)
        if not m:
            return "", lines                  # the first chunk does not open on a bold lede
        title = _strip_md(m.group(2)).strip()
        if not title or len(title) > ED_TITLE_CAP:
            return "", lines
        rest = s[m.end():].strip()
        out = list(lines)
        # keep the bullet marker so _ed_paragraphs still chunks the remainder as its own
        # paragraph; drop the line entirely when the lede WAS the whole line, or the bare
        # marker would survive as a one-character paragraph.
        out[i] = ((m.group(1) or "") + rest) if rest else ""
        return title, out
    return "", lines


ED_MAX_AGE_DAYS = 7      # one full weekly cycle: past this an editorial is dropped outright


def load_editorials(days, max_date, live_editions):
    """One editorial per stream -- the latest edition's, newest first -- for every stream whose
    editorial is still LIVE. No count cap.

    THE `[:3]` CAP AND THE 14-DAY WINDOW WERE BOTH STANDING IN FOR AN EXPIRY RULE, badly. They
    existed when editorials were injected as a block at board index 3, where a fourth card would
    have stacked on the first screen; under the single ranked board (build_board) five editorials
    scatter across five date blocks instead of piling up, so a count cap only ever deletes a
    desk's work at random. `days` survives as the SCAN bound (how far back to read posts), never
    as the rule. Two guards replace them, and they are invariants rather than heuristics:

      ED_MAX_AGE_DAYS -- older than one weekly cycle and it is gone, whatever else is true. This
        is the belt for a desk that stops firing: apply_cap's MIN_LATEST_EDITION protects a
        stream's newest edition from draining forever, so "its edition is still on the board" on
        its own is not an expiry.
      live_editions -- the editorial's own `(date, stream)` edition must still have at least one
        story on the capped board. An editorial is commentary ON that edition; outliving the
        reporting it comments on is what made it read as a zombie.
    """
    posts = []
    for path in glob.glob(os.path.join(POSTS_DIR, "*.md")):
        m = _FILE_RE.search(os.path.basename(path))
        if m and m.group(2) in CURRENT_STREAMS:
            posts.append((m.group(1), m.group(2), path))
    if not posts:
        return []
    newest = _dt.date.fromisoformat(max_date or max(p[0] for p in posts))
    cutoff = (newest - _dt.timedelta(days=days)).isoformat()

    by_stream = {}
    for date, stream, path in sorted(posts):
        if date < cutoff:
            continue
        if (newest - _dt.date.fromisoformat(date)).days > ED_MAX_AGE_DAYS:
            continue
        if (date, stream) not in live_editions:
            continue
        with open(path) as fh:
            lines = fh.read().splitlines()
        i = 0
        while i < len(lines):
            heading = _editorial_heading(lines[i])
            if heading is None:
                i += 1
                continue
            j = i + 1
            body = []
            while j < len(lines) and not lines[j].startswith("## "):
                body.append(lines[j])
                j += 1
            title, body = _ed_title(body)
            paras = _ed_paragraphs(body)
            if paras:
                d = _dt.date.fromisoformat(date)
                label = "%s %d" % (_MONTHS[d.month - 1], d.day)
                by_stream[stream] = {         # later (newer) editions overwrite: latest wins
                    "stream": stream, "date": date,
                    "date_label": label,
                    # the section name lives HERE, not in the headline slot
                    "kicker": "%s · %s · %s" % (STREAM_LABEL.get(stream, stream), heading, label),
                    "heading": heading,
                    "title": title, "paras": paras,
                }
            i = j
    return sorted(by_stream.values(), key=lambda e: e["date"], reverse=True)


def load_recent(days):
    posts = []
    for path in glob.glob(os.path.join(POSTS_DIR, "*.md")):
        m = _FILE_RE.search(os.path.basename(path))
        if m and m.group(2) in CURRENT_STREAMS:
            posts.append((m.group(1), m.group(2), path))
    if not posts:
        return [], None
    max_date = max(p[0] for p in posts)
    cutoff = (_dt.date.fromisoformat(max_date) - _dt.timedelta(days=days)).isoformat()
    window = sorted(p for p in posts if p[0] >= cutoff)
    idx_by_url, idx_by_id = load_index_meta({d for d, _, _ in window})

    stories, url_pos, ov_flags = [], {}, []
    for date, stream, path in window:
        with open(path) as fh:
            parsed = parse_post(fh.read())
        if not parsed:
            continue
        singles = ["single-source" in s["raw"].lower() for s in parsed]
        lead_pos = next((i for i, sgl in enumerate(singles) if not sgl), 0)
        for pos, s in enumerate(parsed):
            if not s["body"]:
                continue
            nu = norm_url(s["url"])
            replace_at = None
            if nu and nu in url_pos:
                # Same primary source already on the page. The window iterates oldest->
                # newest, so this occurrence is the NEWER telling (an ONGOING update
                # re-citing its primary): it supersedes the older card in place. Same-date
                # cross-stream repeats keep the first telling (no basis to prefer either).
                prev = stories[url_pos[nu]]
                if prev["date"] == date:
                    continue
                replace_at = url_pos[nu]
            hid = "%s-%s-%s" % (date, stream, slugify(s["headline"]))
            # SAME-EDITION JOIN ONLY (R3). `(date, stream, url)`, never a bare url: a story
            # parsed out of THIS edition may only wear metadata this edition recorded. A card
            # whose edition recorded nothing for it falls back to the parse, which is the honest
            # answer — the alternative was wearing another edition's treatment.
            #
            # EVERY URL THE STORY CITES, not only the first. A story often cites two sources and
            # the record names the one the desk treated as primary, which is not always the one
            # that appears first in the prose — so a first-url-only join missed 4 cards in the
            # current window, including 2026-07-26's LEAD, which printed its raw bold lede
            # ("A van drove into a crowd at Berlin's Christopher Street Day (the city's Pride
            # march) late on Saturday…") instead of the recorded front-page headline ("Van hits
            # Berlin Pride crowd, one killed"). Alternates are tried in prose order, after the
            # primary, and only inside the same edition — so this widens the join's reach without
            # widening its identity.
            im = (nu and idx_by_url.get((date, stream, nu))) or {}
            if not im:
                for alt in _URL_RE.findall(s["raw"] or "")[1:]:
                    au = norm_url(alt)
                    im = (au and idx_by_url.get((date, stream, au))) or {}
                    if im:
                        break
            im = im or idx_by_id.get(hid) or {}
            overlaid = bool(im.get("topics") or im.get("importance"))
            topics = topic_for(s, stream, im.get("topics"))
            imp = importance_for(pos, lead_pos, singles[pos], im.get("importance"))
            primary = topics[0]
            label, color = TOPICS.get(primary, (primary.title(), "#6b6f76"))
            y, mo, dy = date.split("-")
            # the writer's recorded prose (display_body/why, DEDUP Step C) beats the markdown
            # re-parse — the record is authored, the parse is recovered.
            #
            # Same for the headline, and it is load-bearing: the post's BOLD LEAD is a lead
            # sentence by spec (news.md: "a bolded lead sentence stating what happened AND when"),
            # and `display_body` OPENS with that very sentence — so pairing the parsed lead with
            # the recorded body printed the headline verbatim under itself on 27/80 cards
            # (measured 2026-07-25). The record's `headline` is the curated front-page form; see
            # this module's load_index_meta docstring, which already joins on URL *because* the
            # two forms are written independently. The parse is not at fault — group(3) is the
            # post-bold remainder, so a re-parse alone never duplicates.
            #
            # `hid` above is deliberately still slugified from the PARSED lead: it is the story id
            # the reader's read-state is keyed on, so it must stay byte-stable across this change.
            headline = (im.get("headline") or "").strip() or s["headline"]
            # `deck` (2026-07-25) takes NO fallback, unlike every other overlaid field above.
            # There is nothing in the post to recover it from — it is a front-page artifact the
            # writer authors in Step C and nowhere else — and briefs are specified to omit it, so
            # "absent" is a normal, correct state rather than a hole to fill.
            deck = (im.get("deck") or "").strip()
            body = (im.get("display_body") or "").strip() or s["body"]
            why = (im.get("why") or "").strip() or s["why"]
            affs = im.get("affiliations") or []
            story = {
                # the post's embedded anchor id is authoritative (anchor.py keyed it on the
                # RECORDED story url via --index); recompute from the first link only for
                # pre-anchor posts
                "id": hid, "sid": s.get("anchor_sid") or _safe_story_id(s["url"]),
                "headline": headline, "summary": body, "why": why,
                "url": s["url"], "source_domain": source_domain(s["url"]),
                "date": date, "date_label": date_label(date),
                "stream": stream, "stream_label": STREAM_LABEL.get(stream, stream.title()),
                "topics": topics, "topic_primary": primary, "topic_label": label, "topic_color": color,
                "importance": imp, "is_lead": imp == 3,
                "permalink": "/%s/%s/%s/%s/" % (y, mo, dy, stream),
            }
            if deck:
                # Emitted ONLY when non-empty, for the same reason as `affiliations` below:
                # Liquid counts "" as truthy, so a always-present `deck` key would open an empty
                # standfirst slot under every brief-tier card and every record written before this
                # field existed. Key absence is the render-side gate.
                story["deck"] = deck
            if affs:
                # institution-first source label (SPIKE-2026-07-10): the affiliation is the
                # editorial source of a paper; the domain is just the platform. Keys are
                # emitted only when present so Liquid's `{% if %}` (empty string is truthy)
                # can gate on them directly.
                story["affiliations"] = affs
                story["affiliation_label"] = ", ".join(affs[:2]) + (
                    " +%d" % (len(affs) - 2) if len(affs) > 2 else "")
            if replace_at is not None:
                stories[replace_at] = story
                ov_flags[replace_at] = overlaid
            else:
                if nu:
                    url_pos[nu] = len(stories)
                stories.append(story)
                ov_flags.append(overlaid)
    return stories, max_date, sum(ov_flags)


ED_MIN_BOARD_INDEX = 3   # no editorial may sit in the composed top band (nth-child 1..3)
AGE_MAX = 3              # data-age is a clamped bucket, not a duration


def build_board(stories, editorials, max_date):
    """One ranked sequence over stories AND editorials -- `feed["board"]`, the thing the page
    iterates. `feed["stories"]` / `feed["editorials"]` / `feed["count"]` are untouched.

    ONE RANKING, NOT TWO ARRAYS AND A SPLICE. Editorials used to be a separate array injected
    after the third story, so nothing ever compared one against the other and a six-day-old
    Sports editorial sat at position 4 of a page whose first three cards were today's
    (owner report, 2026-07-26). The sort key has three terms and the middle one is the fix:

        (date, 0 if editorial else importance, -position)   descending

    Editorial rank 0 puts it BELOW briefs, so an editorial always CLOSES its own edition's date
    block -- which is exactly where its day is, ~40 cards down when its day is six days old, and
    on the first screen only when its desk published today. That is the promise the rail prints
    ("position is the ranking"), paid rather than special-cased.

    `-position` (with `reverse=True`, i.e. ascending) is what keeps the sort STABLE inside a
    (date, rank) group: within one tier of one day, the desk's own filed order survives.

    ED_MIN_BOARD_INDEX is the one exception and it is structural, not editorial: the composed top
    band places board children 1-3 by `nth-child`, and a `.fcard--ed` in slot 1 renders at
    `grid-area:1/1/2/13` -- 100% of the board width with no news on screen at all (documented
    failure, 2026-07-25). An editorial landing there is pushed past the next story. It is a dead
    branch on any normal day: MIN_LATEST_EDITION floors the newest edition at 6 stories, so its
    editorial sorts to index >= 6.
    """
    # SHALLOW COPIES, so the board's own fields (`kind`, `age_days`, `daybreak`) land on the
    # board and nowhere else. `feed["stories"]` is a pinned shape — test_feed_sid.py asserts
    # field-for-field that nothing but `sid` was ever added to it — and `feed.count`, the harness,
    # store/anchor.py and four test files all read it. The board is a VIEW; it may not edit the
    # thing it is a view of.
    board = []
    for s in stories:
        it = dict(s)
        it["kind"] = "story"
        board.append(it)
    for e in editorials:
        it = dict(e)
        it["kind"] = "editorial"
        board.append(it)
    pos = {id(it): i for i, it in enumerate(board)}
    board.sort(key=lambda it: (it["date"],
                               0 if it["kind"] == "editorial" else it["importance"],
                               -pos[id(it)]), reverse=True)

    i = 0
    while i < min(ED_MIN_BOARD_INDEX, len(board)):
        if board[i]["kind"] != "editorial":
            i += 1
            continue
        nxt = next((k for k in range(i + 1, len(board))
                    if board[k]["kind"] != "editorial"), None)
        if nxt is None:
            break                      # nothing but editorials below: leave the order alone
        # pop shifts that story down to nxt-1, so inserting AT nxt lands just after it
        board.insert(nxt, board.pop(i))

    newest = _dt.date.fromisoformat(max_date) if max_date else None
    prev_date = None
    for it in board:
        d = _dt.date.fromisoformat(it["date"])
        if newest:
            it["age_days"] = max(0, min(AGE_MAX, (newest - d).days))
        else:
            it["age_days"] = 0
        # The daybreak card prints this instead of nothing: weekday + full date, because the
        # question a date block answers is "which day am I reading". Formatted HERE rather than
        # by Liquid's `date` filter, so the page and tools/home_harness.py render one string
        # from one place instead of two implementations of one format.
        it["day_label"] = "%s %d %s" % (_DAYS[d.weekday()], d.day, _MONTHS[d.month - 1])
        # DAYBREAK IS COMPUTED ON THE FINAL ORDER, over CONTIGUOUS runs rather than over the set
        # of distinct dates, so it stays true even if ED_MIN_BOARD_INDEX has moved an editorial
        # out of its own date block. What it marks is "a new date starts here", which is what the
        # printed date on the card says.
        it["daybreak"] = it["date"] != prev_date
        prev_date = it["date"]
    return board


def edition_parity(date):
    """[(edition, [unmapped record, ...])] for every stream published on `date`.

    THE COUNT IS NOT THE CHECK (R4, external review 2026-07-25). `dedup.py record` decides which
    stories an edition publishes; this script decides which of them reach the only reading
    surface the site has. Those two sets silently disagreed for the whole 2026-07-25 Weekend
    edition -- 40 cards against 44 kept records -- because the parser accepted only one of the two
    bullet shapes the format contract permits. A count comparison would not even have noticed the
    2026-07-13 News edition, whose 7 recorded stories all parsed and then all vanished on an
    anchor-shape mismatch: 0 == 0 tells you nothing. So this matches records to cards by IDENTITY:
    normalized url (over EVERY url in the story, since a story may cite two sources and the record
    may name the second), then story-id, then the slug id.

    Scoped to ONE edition date on purpose -- the current one. An older edition's gap is a writer
    gap that cannot be fixed by re-running this script (2026-07-14 News recorded a Swiss-heatwave
    story its post never printed), so screaming about it on every future run would train the reader
    of this output to ignore it.
    """
    out = []
    for path in sorted(glob.glob(os.path.join(POSTS_DIR, "*.md"))):
        m = _FILE_RE.search(os.path.basename(path))
        if not m or m.group(1) != date or m.group(2) not in CURRENT_STREAMS:
            continue
        stream = m.group(2)
        idx = os.path.join(INDEX_DIR, "%s-%s.jsonl" % (date, stream))
        if not os.path.exists(idx):
            continue
        with open(path) as fh:
            parsed = [s for s in parse_post(fh.read()) if s["body"]]
        urls, sids, hids = set(), set(), set()
        for s in parsed:
            for u in _URL_RE.findall(s["raw"] or ""):
                nu = norm_url(u)
                if nu:
                    urls.add(nu)
            if s.get("anchor_sid"):
                sids.add(s["anchor_sid"])
            hids.add("%s-%s-%s" % (date, stream, slugify(s["headline"])))
        missing = []
        with open(idx) as fh:
            for ln in fh:
                if not ln.strip():
                    continue
                r = json.loads(ln)
                nu = norm_url(r.get("url"))
                if nu and nu in urls:
                    continue
                if nu and _safe_story_id(r.get("url")) in sids:
                    continue
                if r.get("id") in hids:
                    continue
                missing.append(r)
        if missing:
            out.append(("%s-%s" % (date, stream), missing))
    return out


MIN_LATEST_EDITION = 6   # each stream's NEWEST edition keeps at least this many stories


def apply_cap(stories, cap):
    """Global newest-first truncation let one dense Weekend brief erase whole streams from the
    window (Science was entirely absent). Instead: repeatedly drop the least-important tail
    story from the edition with the most droppable stories (oldest first on ties). Each stream's
    latest edition is floored at MIN_LATEST_EDITION so every live stream stays on the page;
    older editions can drain fully — their briefs remain in the archive."""
    if not cap or len(stories) <= cap:
        return stories
    pos = {id(s): i for i, s in enumerate(stories)}
    editions = {}
    for s in stories:
        editions.setdefault((s["date"], s["stream"]), []).append(s)
    latest = {}
    for date, stream in editions:
        latest[stream] = max(latest.get(stream, ""), date)

    def floor(key):
        date, stream = key
        return MIN_LATEST_EDITION if date == latest[stream] else 0

    # drop order within an edition: lowest importance first, later position first
    for ed in editions.values():
        ed.sort(key=lambda s: (s["importance"], -pos[id(s)]))
    dropped = set()
    total = len(stories)
    while total > cap:
        key = max((k for k, ed in editions.items() if len(ed) > floor(k)),
                  key=lambda k: (len(editions[k]) - floor(k), [-ord(c) for c in k[0]]),
                  default=None)
        if key is None:
            break                                        # everything at its floor; accept > cap
        dropped.add(id(editions[key].pop(0)))
        total -= 1
    return [s for s in stories if id(s) not in dropped]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--max", type=int, default=80, dest="cap", help="cap the front page (0 = no cap)")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--strict-parity", action="store_true",
                    help="exit non-zero when the current edition has kept index records that "
                         "reached no card (the feed is still written first)")
    args = ap.parse_args()

    stories, max_date, joined = load_recent(args.days)
    n_parsed = len(stories)
    stories.sort(key=lambda s: (s["date"], s["importance"]), reverse=True)   # newest + lead first
    stories = apply_cap(stories, args.cap)
    for s in stories:
        s["fresh"] = s["date"] == max_date

    counts = {}
    for s in stories:
        for t in s["topics"]:
            counts[t] = counts.get(t, 0) + 1
    topics = [{"key": k, "label": TOPICS[k][0], "color": TOPICS[k][1], "count": counts[k]}
              for k in sorted(counts, key=lambda k: (-counts[k], k)) if k in TOPICS]

    live_editions = {(s["date"], s["stream"]) for s in stories}
    editorials = load_editorials(args.days, max_date, live_editions)
    board = build_board(stories, editorials, max_date)
    feed = {"generated": max_date, "count": len(stories), "topics": topics,
            "editorials": editorials, "stories": stories, "board": board}
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(feed, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    by = {i: sum(1 for s in stories if s["importance"] == i) for i in (3, 2, 1)}
    streams = sorted({s["stream"] for s in stories})
    print("wrote %d/%d stories (%d beats, streams: %s) -> %s  [lead=%d standard=%d brief=%d, through %s]"
          % (len(stories), n_parsed, len(topics), ",".join(streams),
             os.path.relpath(args.out, ROOT), by[3], by[2], by[1], max_date))
    print("editorials: %d (%s)" % (len(editorials),
          ", ".join("%s %s" % (e["stream"], e["date"]) for e in editorials) or "none in window"))
    eb = [i for i, it in enumerate(board) if it["kind"] == "editorial"]
    print("board: %d items, %d daybreaks, editorials at %s"
          % (len(board), sum(1 for it in board if it["daybreak"]),
             ",".join(str(i) for i in eb) or "-"))
    print("index overlay: %d/%d stories carry writer-supplied topics/importance"
          % (joined, n_parsed))                      # 0 is EXPECTED until routines start tagging

    # EDITION PARITY (R4). Printed AFTER the write on purpose: the reader surface should exist
    # even when it is incomplete, and the operator should still be told loudly that it is.
    gaps = edition_parity(max_date)
    if gaps:
        print("PARITY-FAIL: kept index records that reached no card in the current edition —")
        for ed, recs in gaps:
            for r in recs:
                print("  %s  %s  %s" % (ed, (r.get("headline") or "?")[:60], r.get("url") or "-"))
        print("  the post and the index disagree: either the writer never printed the story, or "
              "the parser cannot see the shape it printed it in.")
    else:
        print("parity: every kept record in the %s edition(s) reached a card" % max_date)

    # Desk-stats piggyback (2026-07-11): every writer already runs this script
    # unconditionally, so regenerating _data/stats.json here needs zero prompt wiring.
    try:
        import importlib.util as _ilu
        _sp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_stats.py")
        _spec = _ilu.spec_from_file_location("build_stats", _sp)
        _bs = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_bs)
        _bs.main(["--root", ROOT])  # module global, so a test-patched ROOT is honored
    except Exception as e:  # stats are decorative; the feed must never fail on them
        print("stats build skipped (non-fatal): %s" % e)

    # OPT-IN, and that is deliberate rather than timid: publish.py currently ignores this
    # script's exit code (review R2, a separate task), so a default-fatal parity gate would be
    # a gate that gates nothing while breaking every local re-run over an older edition's writer
    # gap. The flag is here so the fatality-matrix work has a switch to flip.
    if gaps and args.strict_parity:
        raise SystemExit("build_stories_feed: PARITY-FAIL — %d kept record(s) reached no card"
                         % sum(len(r) for _, r in gaps))


if __name__ == "__main__":
    main()
