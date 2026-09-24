#!/usr/bin/env python3
"""B-prime mock: Option B's front + index, rebuilt as day editions with period tags.

Merged from: B (front page, day index rows, tokens, rail), A (day-edition header, edition read
rule with explicit override), C (search bar with Sync outside the chip strip, two-way in-page
links, whole-lede heading for titleless editorials, overflow-wrap:anywhere).

Reads (read-only) /Users/rflnogueira/code/claude-routines/_data/homefeed.json (board items dated
>= CUTOFF) and the _posts/ filenames (edition periods). Writes mock.html next to this file.
Stdlib only.
"""
import datetime as dt
import html
import json
import pathlib
import re

REPO = pathlib.Path("/Users/rflnogueira/code/claude-routines")
FEED = REPO / "_data/homefeed.json"
POSTS = REPO / "_posts"
OUT = pathlib.Path(__file__).resolve().parent / "mock.html"
CUTOFF = "2026-09-19"
FRONT_N = 4                      # lead + 3
PAPER_HOSTS = ("doi.org", "arxiv.org")
STREAMS = ("news", "ai-ml", "science", "weekend", "sports")
STREAM_LABEL = {"news": "News", "ai-ml": "AI/ML", "science": "Science", "weekend": "Weekend", "sports": "Sports"}
# Lookback caps stated by each routine prompt (routines/src/<stream>.md), in inclusive days.
#   news    "Coverage window: the last ~24 hours"            -> 1
#   science "Coverage window: the past 7 days"               -> 7
#   weekend "Coverage window: past 7 days"                   -> 7
#   sports  "Coverage window: the past 7 days"               -> 7
#   ai-ml   "Coverage window: since the last AI/ML edition"  -> uncapped
CAP = {"news": 1, "science": 7, "weekend": 7, "sports": 7, "ai-ml": None}

# Simulated reader state (default view only; ?clean drops it): these editions are fully read, so
# the Weekend 09-19 editorial counts as read by the edition rule without its own tick.
READ_EDITIONS = {"2026-09-19-news", "2026-09-19-weekend", "2026-09-20-news"}
READ_EXTRA_HEADLINES = {"AI agents price you by inferred wealth", "Finding which tool-use steps to train"}

e = html.escape


def esc(s):
    return e(s or "", quote=True)


D = dt.date.fromisoformat


def long_day(iso):
    d = D(iso)
    return d.strftime("%A ") + str(d.day) + d.strftime(" %B")


def short_day(iso):
    d = D(iso)
    return d.strftime("%a ") + str(d.day) + d.strftime(" %b")


def hl_dot(h):
    h = (h or "").strip()
    last = h[-1:] if h else ""
    if last in "\"'”’" and len(h) > 1:
        last = h[-2]
    return last not in ".?!"


def is_paper(url):
    return any(h in (url or "") for h in PAPER_HOSTS)


# ---------------------------------------------------------------- edition periods (builder)
POST_RE = re.compile(r"^(\d{4}-\d\d-\d\d)-(.+)\.md$")
by_stream = {s: [] for s in STREAMS}
for p in POSTS.iterdir():
    m = POST_RE.match(p.name)
    if m and m.group(2) in by_stream:
        by_stream[m.group(2)].append(m.group(1))
for s in by_stream:
    by_stream[s].sort()


def period(date, stream):
    """(start, end) ISO dates this (date, stream) edition covers.

    start = previous edition of the same stream + 1 day (first-ever edition: the cap, else the
    day itself), then capped to the routine's stated lookback."""
    end = D(date)
    prev = [d for d in by_stream.get(stream, []) if d < date]
    cap = CAP.get(stream)
    if prev:
        start = D(prev[-1]) + dt.timedelta(days=1)
    else:
        start = end - dt.timedelta(days=(cap or 1) - 1)
    if cap:
        start = max(start, end - dt.timedelta(days=cap - 1))
    return start.isoformat(), end.isoformat()


def range_html(start, end):
    """'23 Sep' | '17–23 Sep' | '29 Aug–4 Sep', as <time> elements (an interval is not a valid
    datetime value, so the two ends are two elements)."""
    a, b = D(start), D(end)
    endt = f'<time datetime="{end}">{b.day} {b.strftime("%b")}</time>'
    if a == b:
        return endt
    if a.month == b.month:
        st = f'<time datetime="{start}">{a.day}</time>'
    else:
        st = f'<time datetime="{start}">{a.day} {a.strftime("%b")}</time>'
    return f"{st}–{endt}"


def range_words(start, end):
    a, b = D(start), D(end)
    if a == b:
        return f"{b.day} {b.strftime('%B')}"
    return f"{a.day} {a.strftime('%B')} to {b.day} {b.strftime('%B')}"


def ptag(date, stream):
    st, en = period(date, stream)
    return (f'<span class="ptag" data-stream="{stream}"><b>{esc(STREAM_LABEL[stream])}</b>'
            f'<span aria-hidden="true"> · </span><span class="sr">, covering </span>{range_html(st, en)}</span>')


TIER = {3: ("lead", "Lead"), 2: ("feature", "Feature"), 1: ("brief", "Brief")}

feed = json.loads(FEED.read_text())
gen = feed.get("generated")
board = [x for x in feed["board"] if x["date"] >= CUTOFF]
stories = [x for x in board if x["kind"] != "editorial"]
eds = [x for x in board if x["kind"] == "editorial"]

for s in stories:
    s["edition"] = f'{s["date"]}-{s["stream"]}'
for ed in eds:
    ed["edition"] = f'{ed["date"]}-{ed["stream"]}'
    ed["sid"] = f'ed-{ed["stream"]}-{ed["date"]}'
    tops = []                                  # union of its edition's story topics (fix #5)
    for s in stories:
        if s["edition"] == ed["edition"]:
            for t in s["topics"]:
                if t not in tops:
                    tops.append(t)
    ed["topics"] = tops
    ed["stream_label"] = STREAM_LABEL[ed["stream"]]

read_ids = {s["sid"] for s in stories
            if s["edition"] in READ_EDITIONS or s["headline"] in READ_EXTRA_HEADLINES}

# ---------------------------------------------------------------- front selection (B's rule)
dates = sorted({x["date"] for x in board}, reverse=True)
# Walk the newest dates until the window holds FRONT_N lead/feature stories. Lead = the window's
# first lead; the other slots take leads/features in board order and fall back to briefs only when
# the window has too few. A brief folds to a bare headline (R2), which is exactly its index row, so
# on the front it would only manufacture a void beside two photo cards.
window = []
for d in dates:
    window += [s for s in stories if s["date"] == d]
    if sum(1 for s in window if s["importance"] >= 2) >= FRONT_N:
        break
lead = next((s for s in window if s["importance"] == 3), window[0])
rest = [s for s in window if s is not lead]
front = [lead] + ([s for s in rest if s["importance"] >= 2] + [s for s in rest if s["importance"] < 2])[: FRONT_N - 1]
front_ids = {s["sid"] for s in front}
newest_ed = max(eds, key=lambda x: x["date"]) if eds else None

items_all = stories + eds
beat_counts = {}
for it in items_all:
    for t in it["topics"]:
        beat_counts[t] = beat_counts.get(t, 0) + 1
beats = [t for t in feed["topics"] if beat_counts.get(t["key"])]
beats.sort(key=lambda t: -beat_counts[t["key"]])

# ---------------------------------------------------------------- fragments
SVG_CHEV = '<svg aria-hidden="true" width="9" height="9" viewBox="0 0 10 10"><path d="M1.5 3.5 5 7l3.5-3.5" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>'
SVG_CHECK = '<svg aria-hidden="true" width="11" height="11" viewBox="0 0 12 12"><path d="m2 6.5 2.6 2.6L10 3.5" fill="none" stroke="currentColor" stroke-width="1.7"/></svg>'
SVG_THUMB = '<svg aria-hidden="true" width="12" height="12" viewBox="0 0 16 16"><path d="M5 7v7H2V7h3Zm1 7h6.2a1.5 1.5 0 0 0 1.5-1.2l.9-4.5A1.5 1.5 0 0 0 13.1 6.5H10l.5-2.6A1.6 1.6 0 0 0 9 2L6 7" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/></svg>'


def glyph(imp, sr=False):
    cls, word = TIER[imp]
    w = f'<span class="sr">{word}</span>' if sr else f'<span class="tier__w">{word}</span>'
    return f'<span class="tier" data-imp="{imp}"><i class="tg tg--{cls}" aria-hidden="true"></i>{w}</span>'


def dot_topic(s):
    return (f'<span class="topic" style="--tc:{esc(s["topic_color"])}"><i class="dot" aria-hidden="true"></i>'
            f'{esc(s["topic_label"])}</span>')


def source(s):
    aff = f'<span class="src__aff">{esc(s["affiliation_label"])} · </span>' if s.get("affiliation_label") else ""
    return f'<span class="src">{aff}<span class="src__dom">{esc(s["source_domain"])}</span></span>'


def actions(sid, brief, fold_id=None):
    m = (f'<button class="more" type="button" aria-expanded="false" aria-controls="{fold_id}">'
         f'{SVG_CHEV}<span>More</span></button>') if fold_id else ""
    return (m +
            f'<span class="acts" data-brief="{esc(brief)}">'
            f'<button class="readbtn" type="button" aria-pressed="false" aria-label="Mark as read">{SVG_CHECK}</button>'
            f'<button class="vote" type="button" aria-pressed="false" aria-label="Useful">{SVG_THUMB}</button>'
            f'<button class="vote vote--down" type="button" aria-pressed="false" aria-label="Not useful">{SVG_THUMB}</button>'
            f'</span>')


def headline(s, cls, hid):
    dot = " hl--dot" if hl_dot(s["headline"]) else ""
    inner = (f'<a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["headline"])}'
             f'<span class="sr"> (opens in a new tab)</span></a>') if s.get("url") else esc(s["headline"])
    return f'<h3 class="hl {cls}{dot}" id="{hid}">{inner}</h3>'


def why(s):
    if not s.get("why"):
        return ""
    return f'<p class="why"><span class="why__l">Why it matters</span> {esc(s["why"])}</p>'


def item_attrs(it, zone):
    return (f'data-zone="{zone}" data-sid="{esc(it["sid"])}" data-edition="{esc(it["edition"])}" '
            f'data-topics="{esc(" ".join(it["topics"]))}"')


def boots_open(s):
    return s["importance"] == 3 and s["date"] == gen          # R33: today's leads boot open


def front_card(s):
    imp = s["importance"]
    tier = TIER[imp][0]
    hid, fid = f'h-{s["sid"]}', f'f-{s["sid"]}'
    photo = ""
    if imp > 1 and s.get("url") and not is_paper(s["url"]):
        photo = '<div class="photo" aria-hidden="true"><span>photo</span></div>'
    fresh = '<span class="fresh">Just in</span>' if s.get("fresh") else ""
    body = f'<p class="sum">{esc(s["summary"])}</p>' if s.get("summary") else ""
    if imp == 1:                    # R2: a folded brief is headline + More; its why folds
        fold, pre = f'<div class="fold" id="{fid}">{why(s)}{body}</div>', ""
    else:
        fold, pre = f'<div class="fold" id="{fid}">{body}</div>', why(s)
    folded = "" if boots_open(s) else " is-folded"
    return f'''
        <li class="fc fc--{tier}{folded}" id="c-{s["sid"]}" {item_attrs(s, "card")} data-imp="{imp}">
          <article aria-labelledby="{hid}">
            <header class="fc__top">
              {glyph(imp)}<time class="fday" datetime="{s["date"]}">{esc(short_day(s["date"]))}</time>{ptag(s["date"], s["stream"])}{fresh}
            </header>
            {headline(s, "hl--" + tier, hid)}
            {photo}
            {pre}
            {fold}
            <footer class="line">
              {dot_topic(s)}{source(s)}
              {actions(s["sid"], s["edition"], fid)}
            </footer>
          </article>
        </li>'''


def row(s, multi_desk):
    imp = s["importance"]
    tier = TIER[imp][0]
    hid, fid = f'h-{s["sid"]}', f'f-{s["sid"]}'
    body = f'<p class="sum">{esc(s["summary"])}</p>' if s.get("summary") else ""
    if imp == 1:
        fold, pre = f'<div class="fold row__body" id="{fid}">{why(s)}{body}</div>', ""
    else:
        fold, pre = f'<div class="fold row__body" id="{fid}">{body}</div>', why(s)
    norm = lambda x: re.sub(r"[^a-z]", "", (x or "").lower())
    same = norm(STREAM_LABEL[s["stream"]]) == norm(s.get("topic_label"))   # desk == beat: the dot says it
    desk = (f'<span class="row__desk"><span class="sr">Desk: </span>{esc(STREAM_LABEL[s["stream"]])}</span>'
            if multi_desk and not same else "")
    if s.get("fresh"):
        desk += '<span class="fresh">Just in</span>'
    return f'''
          <li class="row row--{tier} is-folded" id="r-{s["sid"]}" {item_attrs(s, "row")} data-imp="{imp}">
            <article class="row__in" aria-labelledby="{hid}">
              <div class="row__g">{glyph(imp, sr=True)}</div>
              <header class="row__head">
                {headline(s, "hl--row-" + tier, hid)}
                <p class="row__meta">{desk}{dot_topic(s)}{source(s)}</p>
              </header>
              <div class="row__why">{pre}</div>
              {fold}
              <footer class="row__foot">{actions(s["sid"], s["edition"], fid)}</footer>
            </article>
          </li>'''


def pointer_row(s):
    return f'''
          <li class="ptr" data-zone="pointer" data-ptr="{esc(s["sid"])}" data-edition="{esc(s["edition"])}">
            <a href="#c-{esc(s["sid"])}"><span class="ptr__l"><span aria-hidden="true">↑</span>On the front</span>
              <span class="ptr__h">{esc(s["headline"])}</span></a>
          </li>'''


LEDE_RE = re.compile(r"^\s*<strong>(.*?)</strong>\s*", re.S)


def ed_heading(ed):
    """C's rule: the title, or for a titleless editorial its WHOLE bold lede (leading "1. "
    stripped, never capped), removed from paras[0] so it is not printed twice."""
    paras = list(ed.get("paras") or [])
    if ed.get("title"):
        return esc(ed["title"]), paras, False
    if paras:
        m = LEDE_RE.match(paras[0])
        if m:
            lede = re.sub(r"^\d+\.\s*", "", m.group(1)).strip()
            paras[0] = paras[0][m.end():]
            return lede, paras, True
    return f'{esc(ed["stream_label"])} desk, {esc(short_day(ed["date"]))}', paras, True


def editorial(ed, where):
    """where = 'desk' (front column) or 'day' (closes its day). Both boot folded (R7)."""
    hid, fid = f'h-{ed["sid"]}', f'f-{ed["sid"]}'
    heading, paras, promoted = ed_heading(ed)
    body = "".join(f"<p>{p}</p>" for p in paras if p.strip())     # builder-owned safe HTML
    st, en = period(ed["date"], ed["stream"])
    hcls = "ed__hl ed__hl--lede" if promoted else "ed__hl"
    return f'''
          <article class="ed ed--{where} is-folded" id="{ed["sid"]}" {item_attrs(ed, "editorial")} aria-labelledby="{hid}">
            <header class="ed__top">
              <span class="edchip">AI editorial</span>
              <p class="ed__kick">{esc(ed["stream_label"])} desk’s view<span aria-hidden="true"> · </span><span class="sr">, covering </span>{range_html(st, en)}</p>
            </header>
            <h3 class="{hcls}" id="{hid}">{heading}</h3>
            <p class="ed__disc">Opinion, written by the desk’s AI — a synthesis across the week’s sourced stories, not itself sourced reporting.</p>
            <div class="fold ed__body" id="{fid}">{body}</div>
            <footer class="line line--ed">
              <a class="jump" href="#d-{ed["date"]}"><span aria-hidden="true">←</span>{esc(short_day(ed["date"]))} edition</a>
              {actions(ed["sid"], ed["edition"], fid)}
            </footer>
          </article>'''


# ---------------------------------------------------------------- front
lead_html = front_card(front[0])
rest_html = "".join(front_card(s) for s in front[1:])
desk_html = ""
if newest_ed:
    desk_html = f'''
          <aside class="desk" data-zone="desk" aria-labelledby="desk-h">
            <p class="desk__lbl" id="desk-h">Desk’s view</p>
            {editorial(newest_ed, "desk")}
          </aside>'''
newest = dates[0]
front_dates = sorted({s["date"] for s in front}, reverse=True)
also = ""
older = [d for d in front_dates if d != newest]
if older:
    also = " · from " + ", ".join(short_day(d) for d in older)

# ---------------------------------------------------------------- day editions
sections = []
for d in dates:
    day_items = [s for s in stories if s["date"] == d]                 # board (rank) order
    day_eds = [x for x in eds if x["date"] == d]
    streams = []
    for x in [x for x in board if x["date"] == d]:
        if x["stream"] not in streams:
            streams.append(x["stream"])
    on_front = sum(1 for s in day_items if s["sid"] in front_ids)
    n = len(day_items)
    bits = [f'{n} {"story" if n == 1 else "stories"}']
    if on_front:
        bits.append(f"{on_front} on the front")
    multi = len({s["stream"] for s in day_items}) > 1
    rows = "".join(pointer_row(s) if s["sid"] in front_ids else row(s, multi) for s in day_items)
    closing, links = "", []
    for x in day_eds:
        where = " (on the front)" if x is newest_ed else ""
        links.append(f'<a class="jump" href="#{x["sid"]}"><span aria-hidden="true">→</span>'
                     f'{esc(x["stream_label"])} desk’s view<span class="sr">{where}</span></a>')
        if x is newest_ed:
            heading, _, _ = ed_heading(x)
            closing += f'''
        <p class="ptr ptr--ed" data-zone="pointer" data-ptr="{x["sid"]}" data-edition="{x["edition"]}">
          <a href="#{x["sid"]}"><span class="ptr__l"><span aria-hidden="true">↑</span>On the front</span>
            <span class="ptr__h ptr__h--ed">{esc(x["stream_label"])} desk’s view — {heading}</span></a>
        </p>'''
        else:
            closing += editorial(x, "day")
    tags = "".join(ptag(d, s) for s in streams)
    sections.append(f'''
      <section class="day" id="d-{d}" data-zone="day" aria-labelledby="d-{d}-h" data-date="{d}">
        <header class="day__head" data-zone="day-head">
          <h2 class="day__h" id="d-{d}-h"><time datetime="{d}">{esc(long_day(d))}</time></h2>
          <div class="day__meta">
            <p class="day__n" data-total="{n}">{" · ".join(bits)}</p>
            <p class="day__cov"><span class="day__covl">Covers</span>{tags}</p>
            {'<p class="day__links">' + "".join(links) + '</p>' if links else ''}
          </div>
        </header>
        <ol class="rows" role="list" data-zone="rows">{rows}
        </ol>{closing}
      </section>''')


# ---------------------------------------------------------------- chips
def chip(key, label, n, color=None, pressed=False):
    dot = f'<i class="dot" aria-hidden="true" style="--tc:{esc(color)}"></i>' if color else ""
    return (f'<button class="chip" type="button" data-topic="{esc(key)}" aria-pressed="{str(pressed).lower()}">'
            f'{dot}<span class="chip__l">{esc(label)}</span> <span class="ct">{n}</span></button>')


def chipset():
    out = chip("", "All", len(items_all), pressed=True)
    for t in beats:
        out += chip(t["key"], t["label"], beat_counts[t["key"]], t["color"])
    return out


count_line = f"{len(stories)} stories · {len(eds)} AI editorials · {len(dates)} days"

CSS = r"""
@font-face{font-family:'Anton';src:url("fonts/anton-latin.woff2") format('woff2');font-weight:400 900;font-style:normal;font-display:swap;
  unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:'Anton';src:url("fonts/anton-latin-ext.woff2") format('woff2');font-weight:400 900;font-style:normal;font-display:swap;
  unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}
@font-face{font-family:'Anton Fallback';src:local('Arial Narrow'),local('ArialNarrow'),local('Helvetica Neue Condensed Bold'),local('Roboto Condensed');
  font-weight:400 900;size-adjust:86%;ascent-override:140%;descent-override:39.1%;line-gap-override:0%}

/* ---- tokens (values from css.md §1, verbatim from option B) */
:root{
  color-scheme:light;
  --paper:#eceae4; --panel:#e2e1d9; --card:#f3f2ec; --ink:#23252b; --muted:#5f616a; --muted-ui:#565863;
  --rule:rgb(35 37 43 / .62); --hair:rgb(35 37 43 / .14); --field:#f6f5f0; --frame:rgb(35 37 43 / .46);
  --accent:#2b3f6b; --red:#c8102e;
  --photo-a:#c9c7bf; --photo-b:#a9a7a0;
  --serif:ui-serif,'New York','Iowan Old Style',Charter,Georgia,'Times New Roman',serif;
  --display:'Anton','Anton Fallback','Arial Narrow','Helvetica Neue Condensed',sans-serif-condensed,sans-serif;
  --sans:'Helvetica Neue',Helvetica,Arial,-apple-system,BlinkMacSystemFont,sans-serif;
  --rail:180px; --pad:16px;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    color-scheme:dark;
    --paper:#14151a; --panel:#1d1e25; --card:#1a1b21; --ink:#e7e5dd; --muted:#9a9ca6; --muted-ui:#b0b2bb;
    --rule:rgb(231 229 221 / .5); --hair:rgb(231 229 221 / .13); --field:rgb(255 255 255 / .05); --frame:rgb(231 229 221 / .3);
    --accent:#8fa9df; --red:#ff5a5f; --photo-a:#34353c; --photo-b:#24252b;
  }
}
:root[data-theme="dark"]{
  color-scheme:dark;
  --paper:#14151a; --panel:#1d1e25; --card:#1a1b21; --ink:#e7e5dd; --muted:#9a9ca6; --muted-ui:#b0b2bb;
  --rule:rgb(231 229 221 / .5); --hair:rgb(231 229 221 / .13); --field:rgb(255 255 255 / .05); --frame:rgb(231 229 221 / .3);
  --accent:#8fa9df; --red:#ff5a5f; --photo-a:#34353c; --photo-b:#24252b;
}

/* ---- root ladder 16/18/20/22 at 768/1024/1280 (today's px) */
html{font-size:16px;-webkit-text-size-adjust:100%;scroll-padding-block-end:calc(6.5rem + env(safe-area-inset-bottom))} /* the two-row phone bar */
@media (min-width:768px){html{font-size:18px}}
@media (min-width:1024px){html{font-size:20px}}
@media (min-width:1280px){html{font-size:22px}}
@media (min-width:700px){html{scroll-padding-block:4.5rem 0}}
*,*::before,*::after{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:1rem/1.5 var(--serif);
  text-rendering:optimizeLegibility;-webkit-font-smoothing:antialiased;overflow-wrap:break-word}
h1,h2,h3,p,ol,ul,figure{margin:0}
ol,ul{padding:0;list-style:none}
p,h3,dd,li{overflow-wrap:anywhere}                      /* C: prose never forces a scroll */
button{font:inherit;color:inherit}
a{color:inherit}
strong{font-weight:600}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
::selection{background:var(--accent);color:var(--paper)}
[hidden]{display:none!important}

.skip{position:absolute;left:8px;top:-60px;background:var(--ink);color:var(--paper);padding:8px 12px;font:700 .75rem var(--sans);z-index:5}
.skip:focus{top:8px}

/* ---- label voice */
.lbl,.fday,.topic,.tier,.fresh,.why__l,.desk__lbl,.ed__kick,.edchip,.ed__disc,.day__n,.day__cov,.day__links,.front__n,.line,.row__meta,.more,.edition,.mast__count,.rail-lbl,.ptr__l,.notice{
  font-family:var(--sans);font-size:.6rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;line-height:1.35}

/* ================================================================ PAGE SHELL (zones in flow) */
.page{display:flex;flex-direction:column;min-block-size:100dvh;
  padding-inline:max(var(--pad),env(safe-area-inset-left)) max(var(--pad),env(safe-area-inset-right))}
.col{display:flex;flex-direction:column;flex:1 0 auto;min-inline-size:0}
.bar{order:0}
.notice{order:1}
main{order:2;flex:1 0 auto;min-inline-size:0}
.foot{order:3}
@media (max-width:699.98px){
  /* thumb zone: the bar rests after main, sticky to the bottom edge. order on chrome only (R28). */
  .bar{order:2;position:sticky;inset-block-end:0}
  main{order:1}
}
@media (min-width:700px){ .bar{position:sticky;inset-block-start:0} }
@media (min-width:1280px){
  .page{display:grid;grid-template-columns:var(--rail) minmax(0,1fr);column-gap:0;align-items:start}
}

/* ================================================================ MASTHEAD / RAIL */
.mast{display:grid;grid-template-columns:auto minmax(0,1fr);align-items:end;column-gap:18px;row-gap:10px;
  padding:18px 0 14px;border-bottom:1px solid var(--rule)}
.nameplate{font:600 clamp(56px,16vw,84px)/.85 var(--display);text-transform:uppercase;letter-spacing:-.01em}
.mast__meta{display:flex;flex-direction:column;gap:4px;min-inline-size:0}
.edition{color:var(--ink)}
.tagline{font:.8rem/1.45 var(--sans);color:var(--muted);letter-spacing:.02em;max-inline-size:34em}
.mast__count{color:var(--muted)}
.mast__acts{display:flex;flex-wrap:wrap;gap:0 16px;grid-column:2}
.linkbtn{background:none;border:0;padding:4px 0;cursor:pointer;font:700 .6rem/1.3 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--muted-ui);text-decoration:none;min-block-size:28px;display:inline-flex;align-items:center}
.linkbtn:hover{color:var(--accent)}
.mast__beats{display:none}
.mast__key{grid-column:1 / -1;border-top:1px solid var(--hair);padding-top:6px}
.mast__key summary{min-block-size:28px;align-items:center}
@media (max-width:699.98px){ .mast{grid-template-columns:minmax(0,1fr);align-items:start;border-bottom:0;padding-bottom:4px} .mast__acts{grid-column:1} }
@media (min-width:700px){
  .mast{grid-template-columns:auto minmax(0,1fr) auto;align-items:end}
  .nameplate{grid-row:1 / span 2}
  .mast__acts{grid-column:3;grid-row:1 / span 2;flex-direction:column;align-items:flex-end;align-self:end}
}
@media (min-width:1280px){
  .mast{position:sticky;inset-block-start:0;align-self:start;max-block-size:100dvh;overflow-y:auto;
    display:flex;flex-direction:column;align-items:stretch;gap:0;padding:22px 20px 24px 6px;margin-inline-start:-6px;border-bottom:0;
    scroll-padding-block:12px}
  .col{border-left:1px solid var(--rule);padding-left:28px;min-block-size:100dvh}
  .nameplate{writing-mode:vertical-rl;rotate:180deg;align-self:flex-start;font-size:clamp(64px,7vw,104px);margin:0 0 20px -.06em}
  .mast__meta{gap:3px;margin-bottom:14px}
  .tagline{font-size:.6rem}
  .mast__acts{flex-direction:column;align-items:flex-start;gap:0;padding:10px 0;border-block:1px solid var(--hair);margin-bottom:18px}
  .mast__beats{display:block}
  .mast__key{margin-top:20px;padding-top:10px}
  .mast__key summary{min-block-size:0}
}
.rail-lbl{color:var(--ink);margin:0 0 8px;padding-bottom:6px;border-bottom:1px solid var(--rule)}
.rbeats{display:flex;flex-direction:column}
.rbeats .chip{display:flex;justify-content:space-between;align-items:center;gap:8px;border:0;border-left:2px solid transparent;border-radius:0;
  background:none;padding:5px 0 5px 10px;font:.72rem/1.3 var(--sans);letter-spacing:0;text-transform:none;color:var(--ink);min-block-size:28px;width:100%;text-align:left}
.rbeats .chip .chip__l{flex:1}
.rbeats .chip[aria-pressed="true"]{border-left-color:var(--red);font-weight:700;background:none;color:var(--ink)}
.rbeats .chip:hover{color:var(--accent)}
.mast__key summary{cursor:pointer;list-style:none;font:700 .6rem/1.3 var(--sans);letter-spacing:.12em;text-transform:uppercase;display:flex;justify-content:space-between}
.mast__key summary::-webkit-details-marker{display:none}
.mast__key summary::after{content:"+";font-weight:400;font-size:.8rem}
.mast__key[open] summary::after{content:"\2212"}
.key{display:grid;grid-template-columns:14px 1fr;gap:6px 8px;margin-top:10px;font:.7rem/1.4 var(--sans);color:var(--muted)}
.key dt{display:flex;align-items:center}
.key dd{margin:0}
.key__note{margin-top:10px;font:.7rem/1.45 var(--sans);color:var(--muted);max-inline-size:40em}

/* ================================================================ CONTROL BAR  (C: <search>, Sync outside the strip) */
.bar{z-index:3;background:var(--paper);display:flex;align-items:center;gap:8px;min-inline-size:0}
.bar .seg,.bar .syncbtn{flex:none}
.bar .beats{flex:1 1 auto;min-inline-size:0;flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none;
  padding:4px;margin-block:-4px;scroll-padding-inline:16px;
  mask-image:linear-gradient(90deg,#000 88%,transparent)}
.bar .beats:has(:focus-visible){mask-image:none}
.bar .beats::-webkit-scrollbar{display:none}
.bar .beats > *{flex:0 0 auto}
@media (max-width:699.98px){
  /* phones: [read state · Sync] over a full-width chip strip, so the widest chip and its ring fit whole */
  .bar{margin-inline:calc(-1 * var(--pad));padding:8px var(--pad) max(8px,env(safe-area-inset-bottom));border-top:1px solid var(--rule);
    flex-wrap:wrap;row-gap:6px}
  .bar .syncbtn{margin-left:auto}
  .bar .beats{flex-basis:100%;margin-inline:-4px}
  .bar .seg button{padding:0 6px}
  .bar .seg .ct{margin-left:3px}
  .bar .syncbtn{padding:0 8px}
}
@media (min-width:700px){ .bar{padding:10px 0 9px;border-bottom:1px solid var(--hair);gap:12px} }
@media (min-width:1280px){ .bar .beats{display:none} .bar{justify-content:flex-end} }
.beats{display:flex;flex-wrap:wrap;gap:6px}
.chip{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--frame);border-radius:2px;background:transparent;cursor:pointer;
  padding:0 9px;min-block-size:32px;font:.72rem/1 var(--sans);color:var(--muted-ui);white-space:nowrap}
.chip .ct{color:var(--muted);font-variant-numeric:tabular-nums}
.chip[aria-pressed="true"]{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.chip[aria-pressed="true"] .ct{color:inherit;opacity:.8}
.dot{display:inline-block;inline-size:7px;block-size:7px;border-radius:50%;background:var(--tc,var(--muted));flex:none}
.seg{display:inline-flex;border:1px solid var(--muted-ui);border-radius:2px}
.seg button:first-child{border-radius:1px 0 0 1px}
.seg button:last-child{border-radius:0 1px 1px 0}
.seg button{border:0;border-left:1px solid var(--hair);background:transparent;cursor:pointer;padding:0 10px;min-block-size:32px;
  font:700 .6rem/1 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--muted-ui);white-space:nowrap}
.seg button:first-child{border-left:0}
.seg button[aria-pressed="true"]{background:var(--ink);color:var(--paper)}
.seg .ct{font-weight:400;letter-spacing:0;margin-left:4px;font-variant-numeric:tabular-nums}
.syncbtn{border:1px solid var(--muted-ui);border-radius:2px;background:transparent;cursor:pointer;min-block-size:32px;padding:0 10px;
  font:700 .6rem/1 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--muted-ui)}

.notice{display:flex;gap:12px;align-items:center;justify-content:space-between;padding:8px 12px;margin-top:10px;background:var(--panel);border:1px solid var(--rule);color:var(--ink)}

/* ================================================================ MAIN + EMPTY */
main{display:flex;flex-direction:column;gap:0;padding-block:18px 28px}
.empty{font:1.05rem/1.5 var(--serif);padding:14px 0 18px;border-bottom:1px solid var(--hair)}

/* ================================================================ PERIOD TAGS (the owner's ask) */
.ptag{display:inline-flex;align-items:baseline;gap:0;padding:2px 6px 1px;background:var(--panel);color:var(--ink);
  font:700 .6rem/1.35 var(--sans);letter-spacing:.1em;text-transform:uppercase;white-space:nowrap;border-radius:2px}
.ptag b{font-weight:700}
.ptag time{font-variant-numeric:tabular-nums}
.ptag > span[aria-hidden]{color:var(--muted);padding-inline:.4em;white-space:pre}

/* ================================================================ FRONT */
.front{padding-bottom:30px}
.front__head,.day__head{border-top:3px solid var(--ink);padding:8px 0 10px}
.front__head{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:4px 14px}
.front__h{font:700 .72rem/1.2 var(--sans);letter-spacing:.14em;text-transform:uppercase}
.front__h time{color:var(--muted);font-weight:700}
.front__n,.day__n{color:var(--muted)}

/* The front is two flex-wrap bands: [lead | desk's view], then the stories. A card that opens takes
   its band's full width (flex-basis:100%) and its neighbours re-flow into full lines around it,
   so no expansion leaves a void beside a neighbour (R15). DOM order == visual order (R28). */
.front__grid{container:front / inline-size;display:flex;flex-direction:column;
  border-top:1px solid var(--rule);border-left:1px solid var(--rule)}
.front__top,.fcards{display:flex;flex-wrap:wrap;min-inline-size:0}
.front__top > *,.fcards > .fc{flex:1 1 100%;min-inline-size:0}
.fcards--top{display:flex}
@container front (min-width:860px){
  .front__top > .fcards--top{flex:4 1 60%}
  .front__top > .desk{flex:1 1 clamp(240px,27%,340px)}
  .js .front__top:has(.is-open) > *{flex-basis:100%}
}
@container front (min-width:720px){
  .fcards--rest > .fc{flex:1 1 30%}
  .js .fcards--rest > .fc.is-open{flex-basis:100%}
  /* a card that ends up alone on a full line (the open one, or a neighbour stranded beside it)
     sets its photo to the right of the type instead of stretching a 100%-wide slot */
  .js .fcards--rest > .fc.is-open > article:has(.photo),
  .js .fcards--rest > .fc:first-child:has(+ .fc.is-open) > article:has(.photo),
  .js .fcards--rest > .fc.is-open + .fc:last-child > article:has(.photo){
    display:grid;grid-template-columns:minmax(0,3fr) minmax(0,2fr);column-gap:28px;row-gap:10px;align-content:start;
    grid-template-rows:auto auto 1fr auto auto;
    grid-template-areas:"top photo" "hl photo" "why photo" "fold fold" "line line"}
  .fcards--rest article > .fc__top{grid-area:top}
  .fcards--rest article > .hl{grid-area:hl}
  .fcards--rest article > .photo{grid-area:photo}
  .fcards--rest article > .why{grid-area:why;align-self:start}
  .fcards--rest article > .fold{grid-area:fold}
  .fcards--rest article > .line{grid-area:line}
}

.fc,.desk{border-right:1px solid var(--rule);border-bottom:1px solid var(--rule)}
.fc > article{display:flex;flex-direction:column;gap:10px;padding:16px 18px 14px;block-size:100%}
.fc--lead > article{box-shadow:inset 0 3px 0 var(--accent);padding:22px 22px 18px}
.fc--feature > article{box-shadow:inset 0 2px 0 color-mix(in srgb,var(--accent) 45%,transparent)}
.fc > article:hover{background:color-mix(in srgb,var(--ink) 4%,transparent)}
.fc__top{display:flex;flex-wrap:wrap;align-items:center;gap:6px 12px}
.fc__top .tier{color:var(--ink)}
.fday{color:var(--ink);font-variant-numeric:tabular-nums}
.topic{display:inline-flex;align-items:center;gap:6px;color:var(--muted);letter-spacing:.1em;font-weight:700;text-transform:uppercase}
.fresh{color:var(--red)}
.tier{display:inline-flex;align-items:center;gap:6px;color:var(--muted)}
.tg{display:inline-block;flex:none}
.tg--lead{inline-size:8px;block-size:8px;border-radius:50%;background:var(--red)}
.tg--feature{inline-size:7px;block-size:7px;background:var(--ink)}
.tg--brief{inline-size:9px;block-size:2px;background:var(--rule)}

.hl{font-family:var(--display);font-weight:600;line-height:1.1;text-transform:uppercase;text-wrap:balance;color:var(--ink);letter-spacing:.005em}
.hl a{color:inherit;text-decoration:none}
.hl a:hover{color:var(--accent);text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:2px}
.hl--dot > a::after,.hl--dot:not(:has(a))::after{content:"."}
/* sizes resolve against the FRONT container, never the card, so opening a card never grows its headline */
.hl--lead{font-size:clamp(30px,5.2cqi,60px)}
.hl--feature{font-size:clamp(22px,2.6cqi,32px)}
.hl--brief{font-size:clamp(20px,2.3cqi,28px);letter-spacing:.02em}
@container front (max-width:719.98px){ .hl--feature{font-size:26px} .hl--brief{font-size:22px} }

.photo{block-size:clamp(120px,14vw,180px);border:1px solid var(--hair);display:grid;place-items:center;
  background:linear-gradient(160deg,var(--photo-a),var(--photo-b));filter:grayscale(1)}
.fc--lead .photo{block-size:clamp(140px,26vw,300px)}
.photo span{font:700 .6rem var(--sans);letter-spacing:.2em;text-transform:uppercase;color:var(--muted-ui);opacity:.8}

.sum{font:1rem/1.5 var(--serif);opacity:.92}
.fc--lead .sum{font-size:1.05rem}
.fc--feature .why,.fc--brief .why{font-size:.85rem}
.fc--feature .sum,.fc--brief .sum{font-size:.88rem}
@container front (min-width:720px){
  .fc--lead .fold,.fcards--rest .fc.is-open .fold{columns:2 20em;column-gap:28px}
  .desk .ed.is-open .ed__body{display:block;columns:2 22em;column-gap:28px}
  .desk .ed.is-open .ed__body p{margin-bottom:.8em;break-inside:avoid-column}
}
.fold{display:flex;flex-direction:column;gap:10px}
.fcards--rest .fc.is-open .fold,.fc--lead .fold{display:block}
.fcards--rest .fc.is-open .fold > * + *,.fc--lead .fold > * + *{margin-top:10px}
.why{font:.95rem/1.5 var(--serif);border-left:2px solid var(--accent);padding-left:10px;break-inside:avoid}
.why__l{display:block;color:var(--accent);font-size:.56rem;margin-bottom:2px}
.line{display:flex;flex-wrap:wrap;align-items:center;gap:6px 12px;margin-top:auto;padding-top:9px;border-top:1px solid var(--hair);letter-spacing:.04em;text-transform:none;font-weight:400}
.src{flex:1 1 10em;min-inline-size:0;text-transform:lowercase;overflow-wrap:anywhere}
.src__aff{color:var(--muted);text-transform:none}
.src__dom{color:var(--red)}
.acts{display:inline-flex;gap:4px;margin-left:auto}
.readbtn,.vote{inline-size:30px;block-size:28px;display:inline-grid;place-items:center;border:1px solid var(--hair);border-radius:2px;background:transparent;color:var(--muted-ui);cursor:pointer;padding:0}
.readbtn[aria-pressed="true"]{color:var(--accent);border-color:var(--accent)}
.vote--down svg{rotate:180deg}
.vote[aria-pressed="true"]{color:var(--paper);background:var(--ink);border-color:var(--ink)}
.jump{gap:.4em;color:var(--accent);text-decoration:none;font-weight:700;letter-spacing:.12em;text-transform:uppercase;font-family:var(--sans);font-size:.6rem;min-block-size:28px;display:inline-flex;align-items:center}
.jump:hover{text-decoration:underline}

/* no-JS: every control that needs script is absent, not inert; every text is visible */
.more{display:none}
html:not(.js) .bar,html:not(.js) .acts,html:not(.js) .mast__beats,html:not(.js) button[data-dialog],html:not(.js) .propose{display:none}
html:not(.js) dialog:target{display:block;position:static;margin:0 auto 32px}
html:not(.js) dialog form{display:none}
.js .more{display:inline-flex;align-items:center;gap:6px;border:0;background:none;padding:6px 0;cursor:pointer;color:var(--ink);min-block-size:28px;
  font:700 .6rem/1.35 var(--sans);letter-spacing:.12em;text-transform:uppercase}
.js .more[aria-expanded="true"] svg{rotate:180deg}
.js .is-folded .fold{display:none}

/* ================================================================ DESK'S VIEW (paired with the lead) */
.desk{background:var(--panel);display:flex;flex-direction:column}
.desk__lbl{padding:12px 18px 0;color:var(--ink);font-size:.6rem}

/* ================================================================ EDITORIAL (shared) */
.ed{display:flex;flex-direction:column;gap:10px;padding:14px 18px 14px}
.ed--desk{padding-top:8px;flex:1 1 auto}
.ed__top{display:flex;flex-wrap:wrap;align-items:center;gap:6px 10px}
.edchip{border:1px solid var(--ink);color:var(--ink);border-radius:2px;padding:3px 6px 2px}
.ed__kick{color:var(--muted)}
.ed__kick time{color:var(--ink)}
.ed__hl{font:italic 600 1.15rem/1.25 var(--serif)}
.ed__hl--lede{font-size:1rem;line-height:1.4}
.ed__disc{color:var(--muted);letter-spacing:.06em;padding-bottom:8px;border-bottom:1px solid var(--hair)}
.ed__body{display:flex;flex-direction:column;gap:.8em;font:.95rem/1.55 var(--serif)}
.ed--desk .ed__body{font-size:.84rem}
.line--ed{border-top:0;padding-top:0}

/* ================================================================ DAY EDITIONS (A's header + B's index rows) */
section.day{padding-bottom:26px}
.day__head{display:flex;flex-direction:column;gap:6px}
.day__h{font:600 clamp(24px,3vw,34px)/1.1 var(--display);text-transform:uppercase;letter-spacing:.005em}
.day__meta{display:flex;flex-wrap:wrap;align-items:center;gap:6px 18px}
.day__cov{display:flex;flex-wrap:wrap;align-items:center;gap:6px}
.day__covl{color:var(--muted);margin-right:2px}
.day__links{display:flex;flex-wrap:wrap;gap:0 14px}
@media (min-width:700px){ .day__links{margin-left:auto} }
.rows{display:flex;flex-direction:column}
.row,.ptr{border-top:1px solid var(--hair)}
.rows > :first-child{border-top:0}
.row__in{display:grid;grid-template-columns:14px minmax(0,1fr);column-gap:10px;row-gap:6px;padding:12px 0 10px;
  grid-template-areas:"g head" "g why" "g body" "g foot"}
.row__in:hover{background:color-mix(in srgb,var(--ink) 3%,transparent)}
.row__g{grid-area:g;padding-top:.45em}
.row__head{grid-area:head;display:flex;flex-direction:column;gap:5px;min-inline-size:0}
.row__why{grid-area:why;min-inline-size:0}
.row__why:empty{display:none}
.row__body{grid-area:body;min-inline-size:0}
.row__foot{grid-area:foot;display:flex;flex-wrap:wrap;align-items:center;gap:6px 12px}
.row__meta{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 14px;letter-spacing:.06em;font-weight:400}
.row__desk{font-weight:700;color:var(--ink);background:var(--panel);padding:1px 5px 0;border-radius:2px;letter-spacing:.1em}
.row__meta .fresh{font-weight:700}
.row .why,.row .sum{max-inline-size:36em}           /* a measure at every width: <= ~85 characters */
.row .why{font-size:.86rem}
.row__body{display:block;columns:2 17em;column-gap:28px}   /* opened body sets in two columns where they fit */
.row__body > * + *{margin-top:8px}
.row .why__l{display:inline;margin:0 6px 0 0}
.row .sum{font-size:.86rem}
.hl--row-lead{font-size:clamp(22px,2.1vw,30px)}
.hl--row-feature{font-size:clamp(19px,1.55vw,23px)}
.hl--row-brief{font-size:clamp(17px,1.3vw,19px);letter-spacing:.02em}
@media (min-width:1024px){
  .row__in{grid-template-columns:14px minmax(0,5fr) minmax(0,7fr);column-gap:24px;
    grid-template-rows:auto 1fr auto;grid-template-areas:"g head why" "g foot why" "g body body"}
  .row__foot{align-self:start}
}
/* pointer rows: a lifted story keeps its rank slot in its own day */
.ptr a{display:grid;grid-template-columns:auto minmax(0,1fr);align-items:baseline;gap:4px 12px;padding:10px 0 10px 24px;text-decoration:none;color:var(--muted)}
.ptr a:hover .ptr__h{color:var(--accent);text-decoration:underline}
.ptr__l{color:var(--accent);white-space:nowrap;display:inline-flex;gap:.4em}
.ptr__h{font:italic .9rem/1.35 var(--serif);color:var(--ink)}
.ptr--ed{border-top:1px solid var(--hair)}
/* an older editorial closes its own day */
section.day > .ed{margin-top:6px;background:var(--panel);border:1px solid var(--rule);border-left:3px solid var(--ink)}
@media (min-width:1024px){ section.day > .ed .ed__body{max-inline-size:46em} }

/* ================================================================ READ (dims, never hides, R3) */
.is-read .hl,.is-read .why,.is-read .sum,.is-read .ed__hl,.is-read .ed__body,.ptr.is-read .ptr__h{color:var(--muted)}
.is-read .sum{opacity:1}
.is-read .photo{opacity:.5}

/* ================================================================ FOOTER */
.foot{border-top:3px solid var(--ink);padding:14px 0 calc(18px + env(safe-area-inset-bottom));display:flex;flex-direction:column;gap:12px;font:.72rem/1.5 var(--sans);color:var(--muted)}
.propose summary{cursor:pointer;font:700 .6rem/1.3 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--ink);min-block-size:28px;display:flex;align-items:center}
.propose form{display:grid;gap:8px;margin-top:8px;max-inline-size:36em}
.propose label{display:grid;gap:4px;font:700 .6rem/1.3 var(--sans);letter-spacing:.1em;text-transform:uppercase}
.propose input,.propose textarea{font:.9rem/1.4 var(--serif);background:var(--field);border:1px solid var(--frame);border-radius:2px;padding:6px 8px;color:var(--ink);min-inline-size:0}
.fb-btn{justify-self:start;border:1px solid var(--ink);background:var(--ink);color:var(--paper);border-radius:2px;padding:6px 12px;font:700 .6rem var(--sans);letter-spacing:.12em;text-transform:uppercase;cursor:pointer}
.colophon{display:flex;flex-wrap:wrap;gap:4px 16px}

dialog{border:1px solid var(--rule);background:var(--paper);color:var(--ink);max-inline-size:min(34em,calc(100vw - 32px));padding:18px 20px;border-radius:2px}
dialog::backdrop{background:rgba(0,0,0,.45)}
dialog h2{font:600 28px/1.1 var(--display);text-transform:uppercase;margin-bottom:8px}
dialog p{margin-bottom:10px}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
"""

JS = r"""
(function(){
  var doc=document.documentElement; doc.classList.add('js');
  var q=new URLSearchParams(location.search);
  var READ=new Set(q.has('clean')?[]:%READ%);     /* story sids read (homeRead:v1 in production) */
  var OVR={};                                      /* editorial explicit tick/un-tick: sid -> 'read'|'unread' */
  var items=[].slice.call(document.querySelectorAll('[data-sid]'));
  var bySid={}; items.forEach(function(x){bySid[x.dataset.sid]=x});
  var stories=items.filter(function(x){return x.dataset.zone!=='editorial'});
  var ptrs=[].slice.call(document.querySelectorAll('[data-ptr]'));
  var active=new Set(), rs='';
  function isRead(el){
    if(el.dataset.zone!=='editorial') return READ.has(el.dataset.sid);
    var o=OVR[el.dataset.sid]; if(o) return o==='read';   /* an explicit tick or un-tick wins */
    /* A's edition rule: read when every story of its (date, stream) edition is read */
    var ed=el.dataset.edition, mine=stories.filter(function(s){return s.dataset.edition===ed});
    return mine.length>0 && mine.every(function(s){return READ.has(s.dataset.sid)});
  }
  function beatOk(el,set){
    if(!set.size) return true;
    return (el.dataset.topics||'').split(' ').some(function(t){return set.has(t)});
  }
  function rsOk(el,r){ return r==='unread'?!isRead(el) : r==='read'?isRead(el) : true; }
  function matches(el){ return rsOk(el,rs) && beatOk(el,active); }
  function paint(){
    items.forEach(function(el){
      var r=isRead(el); el.classList.toggle('is-read',r);
      var b=el.querySelector('.readbtn'); if(b) b.setAttribute('aria-pressed',r?'true':'false');
    });
    ptrs.forEach(function(p){var t=bySid[p.dataset.ptr]; p.classList.toggle('is-read',!!t&&isRead(t));});
    counts();
  }
  /* honest counts, one rule: a chip's number is what the page shows with that chip pressed, given
     the other axis. A beat chip counts active + itself (so a held chip shows the current total);
     All counts every beat; a read-state button counts its state under the active beats. */
  function counts(){
    document.querySelectorAll('.seg button').forEach(function(b){
      var r=b.dataset.rs, n=items.filter(function(el){return rsOk(el,r)&&beatOk(el,active)}).length;
      b.querySelector('.ct').textContent=n;
    });
    document.querySelectorAll('.chip').forEach(function(c){
      var k=c.dataset.topic, set=new Set(k?active:[]); if(k) set.add(k);
      c.querySelector('.ct').textContent=items.filter(function(el){return rsOk(el,rs)&&beatOk(el,set)}).length;
    });
  }
  function anyShown(root){ return !!root.querySelector('[data-sid]:not([hidden]),[data-ptr]:not([hidden])'); }
  function apply(){
    var shown=0;
    items.forEach(function(el){var m=matches(el); el.hidden=!m; if(m) shown++;});
    ptrs.forEach(function(p){var t=bySid[p.dataset.ptr]; p.hidden=!t||t.hidden;});
    document.querySelectorAll('.fcards,.desk,.front,section.day').forEach(function(z){ z.hidden=!anyShown(z); });
    /* an in-page link never points at something the filter hid (pointer rows already follow theirs) */
    document.querySelectorAll('main a[href^="#"]').forEach(function(a){
      if(a.closest('.ptr')) return;
      var t=document.getElementById(a.getAttribute('href').slice(1));
      a.hidden=!t||!!t.closest('[hidden]');
    });
    document.querySelectorAll('.day__links').forEach(function(p){ p.hidden=!p.querySelector('a:not([hidden])'); });
    /* day header: the count and the desk tags describe what is shown, not the whole edition */
    var filtering=!!rs||active.size>0;
    document.querySelectorAll('section.day').forEach(function(sec){
      if(sec.hidden) return;
      var n=sec.querySelector('.day__n'), total=+n.dataset.total;
      if(!n.dataset.orig) n.dataset.orig=n.textContent;
      var v=sec.querySelectorAll('.rows > [data-sid]:not([hidden]),.rows > [data-ptr]:not([hidden])').length;
      n.textContent=filtering?v+' of '+total+' '+(total===1?'story':'stories')+' shown':n.dataset.orig;
      sec.querySelectorAll('.day__cov .ptag').forEach(function(t){
        var ed=sec.dataset.date+'-'+t.dataset.stream;
        t.hidden=!sec.querySelector('[data-edition="'+ed+'"]:not([hidden])');
      });
    });
    var em=document.getElementById('empty');
    if(shown){em.hidden=true}else{
      em.hidden=false;
      em.textContent= rs==='unread' ? 'All caught up — every story '+(active.size?'on this beat':'in this edition')+' is read.'
        : rs==='read' ? 'Nothing marked read'+(active.size?' on this beat':'')+' yet.' : 'No stories on this beat right now.';
    }
    counts();
  }
  var chips=[].slice.call(document.querySelectorAll('.chip'));
  function syncChips(){chips.forEach(function(c){var k=c.dataset.topic; c.setAttribute('aria-pressed', k===''?String(!active.size):String(active.has(k)));});}
  chips.forEach(function(c){c.addEventListener('click',function(){
    var k=c.dataset.topic; if(k===''){active.clear()} else if(active.has(k)){active.delete(k)} else {active.add(k)}
    syncChips(); apply();
  })});
  var segs=[].slice.call(document.querySelectorAll('.seg button'));
  segs.forEach(function(b){b.addEventListener('click',function(){
    rs=b.dataset.rs; segs.forEach(function(x){x.setAttribute('aria-pressed',String(x===b))}); apply();
  })});
  function setOpen(card,b,o){
    card.classList.toggle('is-folded',!o); card.classList.toggle('is-open',o);
    b.setAttribute('aria-expanded',String(o)); b.querySelector('span').textContent=o?'Less':'More';
  }
  document.querySelectorAll('.more').forEach(function(b){
    var card=b.closest('[data-sid]');
    setOpen(card,b,!card.classList.contains('is-folded'));
    b.addEventListener('click',function(){
      var top=b.getBoundingClientRect().top;
      setOpen(card,b,card.classList.contains('is-folded'));
      window.scrollBy(0,b.getBoundingClientRect().top-top);   /* anchored(): opening never moves the reader */
    });
  });
  document.querySelectorAll('.readbtn').forEach(function(b){b.addEventListener('click',function(){
    var el=b.closest('[data-sid]'), id=el.dataset.sid, r=isRead(el);
    if(el.dataset.zone==='editorial'){ OVR[id]=r?'unread':'read'; }
    else if(r){READ.delete(id)} else {READ.add(id)}
    paint(); if(rs) apply();
  })});
  document.querySelectorAll('.hl a').forEach(function(a){a.addEventListener('click',function(){
    var el=a.closest('[data-sid]'); if(el.dataset.zone!=='editorial') READ.add(el.dataset.sid); paint();   /* implicit read: never re-filters */
  })});
  document.querySelectorAll('.vote').forEach(function(b){b.addEventListener('click',function(){
    var on=b.getAttribute('aria-pressed')!=='true';
    b.parentNode.querySelectorAll('.vote').forEach(function(x){x.setAttribute('aria-pressed','false')});
    b.setAttribute('aria-pressed',String(on));
  })});
  document.querySelectorAll('[data-dialog]').forEach(function(b){b.addEventListener('click',function(ev){
    var d=document.getElementById(b.dataset.dialog); if(d&&d.showModal){ev.preventDefault(); d.showModal();}
  })});
  /* keyboard focus in the chip strip: keep the focused chip wholly inside the strip */
  document.querySelectorAll('.bar .beats').forEach(function(s){s.addEventListener('focusin',function(ev){
    var c=ev.target.closest('.chip'); if(!c) return;
    var r=c.getBoundingClientRect(), b=s.getBoundingClientRect(), pad=16;
    if(r.left<b.left+pad) s.scrollLeft-=b.left+pad-r.left;
    else if(r.right>b.right-pad) s.scrollLeft+=r.right-(b.right-pad);
  })});
  var pf=document.querySelector('.propose__form'); if(pf) pf.addEventListener('submit',function(e){e.preventDefault(); pf.querySelector('.propose__msg').textContent='sign in to propose — Sync, in the control bar';});
  /* freshness (#3): never auto-reloads; ?stale previews the bar */
  var notice=document.querySelector('.notice');
  notice.querySelector('button').addEventListener('click',function(){location.reload()});
  var hiddenAt=0, stamp=(document.querySelector('meta[name=build]')||{}).content;
  function probe(){
    if(location.protocol==='file:') return;
    fetch('edition.json?t='+Date.now(),{cache:'no-store'}).then(function(r){return r.ok?r.json():null})
      .then(function(j){ if(j&&j.build_at&&j.build_at!==stamp) notice.hidden=false; }).catch(function(){});
  }
  addEventListener('pageshow',function(ev){ if(ev.persisted) probe(); });
  document.addEventListener('visibilitychange',function(){
    if(document.hidden){hiddenAt=Date.now()} else if(hiddenAt&&Date.now()-hiddenAt>6e5){probe()}
  });
  if(q.has('stale')) notice.hidden=false;
  /* mock-only state presets for checks and screenshots */
  (q.get('read')||'').split(',').filter(Boolean).forEach(function(ed){
    stories.forEach(function(s){ if(s.dataset.edition===ed) READ.add(s.dataset.sid); });
  });
  paint(); apply();
  if(q.get('beat')) q.get('beat').split(',').forEach(function(k){var c=chips.find(function(x){return x.dataset.topic===k&&x.offsetParent});if(c)c.click();});
  if(q.get('rs')){var sb=segs.find(function(x){return x.dataset.rs===q.get('rs')}); if(sb) sb.click();}
  if(q.get('expand')){var ec=bySid[q.get('expand')]; if(ec) ec.querySelector('.more').click();}
})();
"""

key_html = f'''
      <details class="mast__key">
        <summary>How to read this page</summary>
        <dl class="key">
          <dt>{glyph(3, sr=True)}</dt><dd>Lead — the day's biggest story</dd>
          <dt>{glyph(2, sr=True)}</dt><dd>Feature</dd>
          <dt>{glyph(1, sr=True)}</dt><dd>Brief</dd>
          <dt><span class="edchip" style="padding:0 3px">AI</span></dt><dd>AI editorial — opinion, not reporting</dd>
        </dl>
        <p class="key__note">Position is the ranking: the front page first, then each day's edition, biggest story first. A tag like “Science · 17–23 Sep” is the span that desk's edition reports on. Read stories dim; they never move or shrink.</p>
      </details>'''

page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="build" content="{esc(gen)}T12:25:00+02:00"><!-- production: builder-emitted build_at ISO timestamp -->
<title>News — B-prime mock</title>
<style>{CSS}</style>
</head>
<body>
<a class="skip" href="#main">Skip to the stories</a>
<div class="page">
  <header class="mast" data-zone="masthead">
    <h1 class="nameplate">News</h1>
    <div class="mast__meta">
      <p class="edition"><time datetime="{newest}">{esc(long_day(newest))} 2026</time></p>
      <p class="mast__count">{count_line}</p>
      <p class="tagline">The day's stories, sized by how much they matter.</p>
    </div>
    <div class="mast__acts">
      <a class="linkbtn" href="#hiw" data-dialog="hiw" aria-haspopup="dialog">How this works</a>
      <a class="linkbtn" href="evaluator/2026-09-20/">Weekly pipeline review · 20 Sep</a>
    </div>
    <div class="mast__beats" role="group" aria-labelledby="railBeat">
      <p class="rail-lbl" id="railBeat">Beat</p>
      <div class="rbeats">{chipset()}</div>
    </div>{key_html}
  </header>

  <div class="col" data-zone="column">
    <search class="bar" data-zone="bar" aria-label="Filter the stories">
      <div class="seg" role="group" aria-label="Read state">
        <button type="button" data-rs="" aria-pressed="true">All<span class="ct"></span></button>
        <button type="button" data-rs="unread" aria-pressed="false">Unread<span class="ct"></span></button>
        <button type="button" data-rs="read" aria-pressed="false">Read<span class="ct"></span></button>
      </div>
      <button class="syncbtn" type="button" data-dialog="sync" aria-haspopup="dialog">Sync</button>
      <div class="beats" role="group" aria-label="Beat">{chipset()}</div>
    </search>

    <div class="notice" data-zone="notice" role="status" hidden>
      <span>New edition</span><button class="syncbtn" type="button">Reload</button>
    </div>

    <main id="main" tabindex="-1" data-zone="main">
      <p class="empty" id="empty" data-zone="empty" role="status" aria-live="polite" hidden></p>

      <section class="front" data-zone="front" aria-labelledby="front-h">
        <header class="front__head" data-zone="front-head">
          <h2 class="front__h" id="front-h">Front page · <time datetime="{newest}">{esc(short_day(newest))}</time></h2>
          <p class="front__n">The {len(front)} stories that matter most right now{esc(also)}</p>
        </header>
        <div class="front__grid" data-zone="front-grid">
          <div class="front__top" data-zone="front-top">
            <ol class="fcards fcards--top" role="list" data-zone="front-lead">{lead_html}
            </ol>{desk_html}
          </div>
          <ol class="fcards fcards--rest" role="list" start="2" data-zone="front-rest">{rest_html}
          </ol>
        </div>
      </section>
{"".join(sections)}
    </main>

    <footer class="foot" data-zone="footer">
      <details class="propose">
        <summary>Propose a brief</summary>
        <form class="propose__form" action="#">
          <label>Topic <input class="propose__topic" name="topic" required maxlength="300"></label>
          <label>Detail <textarea class="propose__detail" name="detail" rows="3"></textarea></label>
          <button class="fb-btn" type="submit">Send</button>
          <span class="propose__msg" role="status"></span>
        </form>
      </details>
      <p class="colophon"><span>Generated {esc(gen)} from the week's briefs</span><a href="feed.xml">RSS feed</a><a href="prompts.html">The prompts</a><span>© 2026 khalic-lab</span></p>
    </footer>
  </div>
</div>

<dialog id="hiw" aria-labelledby="hiw-h"><h2 id="hiw-h">How this works</h2><p>(The existing How-this-works content moves here unchanged; a native dialog replaces the hand-rolled focus trap. Without script, the link jumps here instead.)</p><p>Each day is one edition. A tag like “Science · 17–23 Sep” is the span that desk’s edition reports on: from the day after its previous edition to the day it was published, never more than the window its prompt sets.</p><form method="dialog"><button class="syncbtn">Close</button></form></dialog>
<dialog id="sync"><h2>Sync</h2><p>Sign in with a passkey to sync read state and beats across devices. A top-layer dialog cannot be clipped by the bar's chip scroller.</p><form method="dialog"><button class="syncbtn">Close</button></form></dialog>
<script>{JS.replace("%READ%", json.dumps(sorted(read_ids)))}</script>
</body>
</html>
'''

OUT.write_text(page)
periods = sorted({(x["date"], x["stream"]) for x in board}, reverse=True)
print(f"wrote {OUT} ({len(page)//1024} KB): front={len(front)} sections={len(sections)} eds={len(eds)} read={len(read_ids)}")
for d, s in periods:
    print("  period", d, s, "->", period(d, s))
