#!/usr/bin/env python3
"""Render the homepage masonry as a standalone HTML harness — the smoke test for
_layouts/home.html's inline CSS/JS (which Jekyll-only rendering makes otherwise untestable
without a local Ruby toolchain).

It substitutes the Liquid card loop with Python over the real _data/homefeed.json and embeds
the layout's <style>/<script> blocks verbatim plus the Folio tokens from head/custom.html's
palette, so the masonry algorithm, filters, image swap and thumbs run exactly as deployed.

Usage:
    python3 tools/home_harness.py [--out /tmp/home-harness.html]
    # then, no local Jekyll needed:
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new \
        --screenshot=/tmp/home.png --window-size=1440,2800 --virtual-time-budget=8000 \
        "file:///tmp/home-harness.html"

The harness appends a geometry self-check 4s after load: a `#geomcheck` div reporting
overlapping cards and the largest column gap (grep the --dump-dom output for 'GEOM').
`inversions` must be 0: it counts cards whose visual (row, column) position disagrees with DOM
order, i.e. rank. The old overlaps/maxGap pair diagnosed the deleted masonry packer.

It also stubs window.fetch (no real network) and appends a `#synccheck` div at 4.5s
exercising the passkey read-state sync engine (grep for 'SYNC'):
  plain URL     -> signed-out run: rsCalls must be 0 (no sync traffic without a session).
  URL + #synced -> seeded session + stubbed GET /readstate: expects gets=1 painted=1
                   unpainted=1 shadow=1 (remote read paints; newer remote tombstone
                   unmarks a locally-read card; both land in the syncState:v1 shadow).
Both modes also expect edread=1 (editorial cards are read-markable since 2026-07-18: the ✓
toggles is-read and writes/clears an ed-<stream>-<date> key in homeRead:v1); -1 means no
editorial card was in the feed window, which is only OK if homefeed.json truly has none.
"""
import argparse
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

THEME_URL = "https://khalic-lab.github.io/claude-routines/assets/css/main.css"
THEME_CACHE = "/tmp/mm-main.css"


def _theme_css(refresh=False):
    """The COMPILED theme CSS, or "" if it cannot be fetched.

    `remote_theme: mmistakes/minimal-mistakes@4.26.2` means the skin we are layering over exists
    nowhere in this repo — it is built by GitHub Pages. So every geometry number this harness has
    ever produced was measured WITHOUT it, and the theme has bled through this restyle in LAYOUT
    before, not only in colour. The concrete one: minimal-mistakes' reset sets
    `html{box-sizing:border-box}` + `*{box-sizing:inherit}`, so in production `.fcard__in` is
    border-box and in a theme-blind harness it is content-box — a per-card difference on the one
    measurement that matters.

    Inlined BEFORE the local tokens so our rules still win the cascade, which is the deployed
    order (custom.html loads last in <head>). Cached, because a page render should not depend on
    the network; `--refresh-theme` re-pulls. Degrades to "" with a loud warning rather than
    failing, so the harness still works offline — but a run that prints that warning is measuring
    the wrong page and its numbers should not be quoted.
    """
    import urllib.request
    if refresh or not os.path.exists(THEME_CACHE):
        try:
            req = urllib.request.Request(THEME_URL, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=25) as r:
                data = r.read().decode("utf-8", "replace")
            with open(THEME_CACHE, "w") as fh:
                fh.write(data)
        except Exception as exc:                       # offline, DNS, 4xx/5xx
            if not os.path.exists(THEME_CACHE):
                print("home_harness: WARNING could not fetch the theme CSS (%s) — rendering "
                      "THEME-BLIND; box-sizing and skin geometry will differ from production" % exc)
                return ""
    with open(THEME_CACHE) as fh:
        return "<style>%s</style>" % fh.read()


def _extract_tokens():
    """Embed EVERY <style> block from _includes/head/custom.html verbatim.

    This used to regex out just the `:root{...}` palette. Selecting one block has two silent
    failure modes, both plausible: a SECOND :root block added later (a type scale, say) is
    dropped while the guard still passes on the first, and a `:root` inside an earlier @media
    gets extracted INSTEAD of the real palette. In both cases the harness renders a page
    production does not have and reports success. The deeper flaw was that the guard checked the
    extracted TEXT, never that the tokens actually APPLY — the original garbage-selector bug
    would have passed it too, had the garbage contained the token names.

    Embedding everything cannot drop a token, needs no guard, and picks up the .propose__* /
    .fb-btn rules the harness was missing anyway. It is the same `re.findall` over <style> that
    main() already uses for _layouts/home.html — one mechanism instead of two.
    """
    src = os.path.join(ROOT, "_includes", "head", "custom.html")
    with open(src) as fh:
        blocks = re.findall(r"<style>.*?</style>", fh.read(), re.S)
    if not blocks:
        raise SystemExit("home_harness: no <style> block in %s" % src)

    # @font-face src is Liquid — `url('{{ "/assets/fonts/x.woff2" | relative_url }}')` — because
    # this is a project Pages site under `baseurl: /claude-routines` and a root-absolute url()
    # 404s there. Jekyll expands it; verbatim extraction does not, so the literal braces survive,
    # the woff2 never loads, and the harness silently paints the metric-matched FALLBACK instead.
    # That is not a cosmetic difference: Anton's cap height is 0.859em against Arial Narrow's
    # 0.716em, so every leading and wrap judgement taken off such a screenshot is ~20% wrong in
    # exactly the dimension this redesign is tuning.
    blocks = [re.sub(r"""\{\{\s*["'](/assets/fonts/[^"']+)["']\s*\|\s*relative_url\s*\}\}""",
                     lambda m: "file://" + ROOT + m.group(1), b) for b in blocks]

    # Generalised guard. The rail extractor has had one of these since it shipped, but it only
    # covered the rail — which is precisely why the font bug above could sit in the stylesheet
    # looking fine. ANY unexpanded Liquid in embedded CSS is a wrong render, so fail loudly rather
    # than let the next one be found by eye three reports later.
    leftover = re.findall(r"\{\{.*?\}\}|\{%.*?%\}", "".join(blocks), re.S)
    if leftover:
        raise SystemExit("home_harness: unexpanded Liquid in custom.html's CSS: %r — the harness "
                         "renders it literally, so add a substitution above" % leftover[:4])
    return "".join(blocks) + """<style>
body{ background:var(--paper); color:var(--ink); font-family:var(--serif); margin:0; }
/* Production's wrapper chain, measured off the live DOM at a 1440 viewport:
   .folio-board 1396 < .archive 1396 < #main 1440 (padding-inline 22px, max-width 1680)
   < .initial-content 1440 < body.layout--home 1440.
   So #main's box is what decides the board width, and these two values reproduce it exactly
   (board 1396, grid 1110 at 1440 — identical to live). The old 1236/12px understated the sheet by
   ~100px, which is enough to change how many text columns fit and how many lines a headline
   wraps to; every wide-width number taken before this was measuring a narrower page than
   readers see. */
.wrap{ max-width:1680px; margin:0 auto; padding:0 22px; }
</style>"""


TOKENS = _extract_tokens()

SVG = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28'
       'a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>')

GEOM_CHECK = """<script>
setTimeout(function(){
  // The board is CSS Grid now, so the old metrics are gone with the engine they diagnosed:
  // `overlaps` and `maxGap` measured a hand-rolled packing that no longer exists (grid rows
  // cannot overlap and leave no vertical voids). What CAN still regress is the property the
  // packer used to violate: DOM order == reading order == rank. So assert that instead.
  var grid=document.getElementById('folioGrid');
  var cards=[].slice.call(grid.querySelectorAll('.fcard')).filter(function(c){return c.style.display!=='none';});
  var r=cards.map(function(c){var b=c.getBoundingClientRect();return{t:Math.round(b.top+scrollY),l:Math.round(b.left),h:Math.round(b.height)};});
  // Reading order for a row-major grid: sort by (row, column) and check it matches DOM order.
  // Rows are grouped by top within a tolerance, since cards in a row share a baseline.
  var order=r.map(function(x,i){return{i:i,t:x.t,l:x.l};})
             .sort(function(a,b){return (Math.abs(a.t-b.t)>4?a.t-b.t:a.l-b.l);});
  var inversions=0;for(var k=0;k<order.length;k++) if(order[k].i!==k) inversions++;
  var xs=[];r.forEach(function(x){if(xs.indexOf(x.l)<0)xs.push(x.l);});
  var rows={};r.forEach(function(x){var key=Math.round(x.t/4);rows[key]=1;});
  var d=document.createElement('div');d.id='geomcheck';
  d.textContent='GEOM inversions='+inversions+' cards='+cards.length+' cols='+xs.length
    +' rows='+Object.keys(rows).length+' gridH='+Math.round(grid.getBoundingClientRect().height)
    +' bodyScrollW='+document.body.scrollWidth+' innerW='+innerWidth;
  document.body.appendChild(d);
},4000);
</script>"""


SYNC_UI = """<span class="ff-sync" id="ffSync" hidden>
    <button class="ff-sbtn" type="button" aria-expanded="false" aria-controls="ffSyncPanel">Sync</button>
    <div class="ff-spanel" id="ffSyncPanel" hidden>
      <div class="ffs-out">
        <button class="ffs-btn ffs-signin" type="button">Sign in with passkey</button>
        <button class="ffs-lnk ffs-setup-t" type="button" aria-expanded="false">First time? Set up</button>
        <div class="ffs-setup" hidden>
          <input class="ffs-invite" type="password" placeholder="invite code" aria-label="Invite code" autocomplete="off">
          <button class="ffs-btn ffs-create" type="button">Create passkey</button>
        </div>
      </div>
      <div class="ffs-in" hidden>
        <span class="ffs-who"></span>
        <button class="ffs-btn ffs-signout" type="button">Sign out</button>
      </div>
      <p class="ffs-status" aria-live="polite"></p>
    </div>
  </span>"""

# Runs AFTER the cards are in the DOM but BEFORE the layout script: resets localStorage for a
# deterministic run, stubs fetch (readstate canned, everything else 404), and — on #synced —
# seeds a fake session plus a locally-read second card the remote tombstone must unmark.
PRE_SYNC = """<script>
(function(){
  var SYNCED = location.hash === '#synced';
  try { ['homeRead:v1','syncState:v1','syncSession:v1','topicPrefs:v1'].forEach(function(k){ localStorage.removeItem(k); }); } catch(e){}
  var fbs = document.querySelectorAll('.fcard__fb');
  var sidA = fbs[0] && fbs[0].dataset.story, sidB = null;
  for (var i = 1; i < fbs.length; i++){
    if (fbs[i].dataset.story && fbs[i].dataset.story !== sidA){ sidB = fbs[i].dataset.story; break; }
  }
  window.__syncSids = [sidA, sidB];
  window.__fetchLog = [];
  window.fetch = function(url, opts){
    var method = ((opts && opts.method) || 'GET').toUpperCase();
    window.__fetchLog.push(method + ' ' + String(url));
    if (String(url).indexOf('/readstate') >= 0){
      if (method === 'GET'){
        var T = Date.now(), state = {};
        if (sidA) state[sidA] = { ts: T - 5000, v: 1 };
        if (sidB) state[sidB] = { ts: T - 1000, v: 0 };
        return Promise.resolve(new Response(JSON.stringify({ reader:'rafael', state: state }), { status: 200 }));
      }
      return Promise.resolve(new Response(JSON.stringify({ ok: true }), { status: 200 }));
    }
    if (String(url).indexOf('/prefs') >= 0){
      if (method === 'GET'){
        // remote prefs carry a roamed read-filter (rs:'unread') with a ts newer than the
        // cleared local shadow -> the merge must flip the segmented toggle to Unread.
        return Promise.resolve(new Response(JSON.stringify(
          { reader:'rafael', prefs: { topics: [], rs: 'unread', ts: Date.now() - 500 } }), { status: 200 }));
      }
      return Promise.resolve(new Response(JSON.stringify({ ok: true, applied: true }), { status: 200 }));
    }
    return Promise.resolve(new Response('', { status: 404 }));
  };
  if (SYNCED){
    try {
      localStorage.setItem('syncSession:v1', JSON.stringify({ token: new Array(65).join('a'), reader: 'rafael' }));
      var seed = {}; seed[sidB] = Date.now() - 100000;   // read locally, OLDER than the remote tombstone
      localStorage.setItem('homeRead:v1', JSON.stringify(seed));
    } catch(e){}
  }
})();
</script>"""

SYNC_CHECK = """<script>
setTimeout(function(){
  var log = window.__fetchLog || [];
  var rs = log.filter(function(l){ return l.indexOf('/readstate') >= 0; });
  var gets = rs.filter(function(l){ return l.indexOf('GET ') === 0; }).length;
  var prefsCalls = log.filter(function(l){ return l.indexOf('/prefs') >= 0; }).length;
  // roamed read-filter (2026-07-18): the stubbed GET /prefs carries rs:'unread'; signed-in the
  // segmented toggle must land on Unread, signed-out it must stay on All (no prefs traffic).
  var rbOn = document.querySelector('.ff-rbtn[aria-pressed="true"]');
  var prefsRs = location.hash === '#synced'
    ? ((rbOn && rbOn.dataset.rs === 'unread') ? 1 : 0)
    : ((rbOn && rbOn.dataset.rs === '') ? 1 : 0);
  var sids = window.__syncSids || [];
  var painted = -1, unpainted = -1, shadow = -1;
  function cardOf(sid){ var fb = document.querySelector('.fcard__fb[data-story="' + sid + '"]'); return fb && fb.closest('.fcard'); }
  if (location.hash === '#synced' && sids[0] && sids[1]){
    painted = cardOf(sids[0]).classList.contains('is-read') ? 1 : 0;
    unpainted = cardOf(sids[1]).classList.contains('is-read') ? 0 : 1;
    var st = {}; try { st = JSON.parse(localStorage.getItem('syncState:v1') || '{}'); } catch(e){}
    shadow = (st[sids[0]] && st[sids[0]].v === 1 && st[sids[1]] && st[sids[1]].v === 0) ? 1 : 0;
  }
  // editorial read state (2026-07-18): clicking the ✓ on an ed- card must toggle is-read and
  // land the ed-<stream>-<date> id in homeRead:v1; a second click must fully undo both.
  var edread = -1;
  var edCard = document.querySelector('.fcard--ed[data-story]');
  var edBtn = edCard && edCard.querySelector('.fcard__read');
  if (edCard && edBtn){
    var edSid = edCard.dataset.story;
    edBtn.click();
    var m1 = {}; try { m1 = JSON.parse(localStorage.getItem('homeRead:v1') || '{}'); } catch(e){}
    var on = edCard.classList.contains('is-read') && !!m1[edSid] && edSid.indexOf('ed-') === 0;
    edBtn.click();
    var m2 = {}; try { m2 = JSON.parse(localStorage.getItem('homeRead:v1') || '{}'); } catch(e){}
    var off = !edCard.classList.contains('is-read') && !m2[edSid];
    edread = (on && off) ? 1 : 0;
  }
  var aff = document.getElementById('ffSync');
  var d = document.createElement('div'); d.id = 'synccheck';
  d.textContent = 'SYNC mode=' + (location.hash === '#synced' ? 'in' : 'out') + ' rsCalls=' + rs.length +
    ' gets=' + gets + ' affordance=' + (aff && !aff.hidden ? 1 : 0) +
    ' painted=' + painted + ' unpainted=' + unpainted + ' shadow=' + shadow +
    ' prefsCalls=' + prefsCalls + ' prefsRs=' + prefsRs + ' edread=' + edread;
  document.body.appendChild(d);
}, 4500);
</script>"""


def card(s):
    e = lambda x: html.escape(str(x or ""))
    lead = " lead" if s["is_lead"] else ""
    og = ' data-ogurl="%s"' % e(s["url"]) if s.get("url") and s["importance"] > 1 else ""
    hl = ('<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>' % (e(s["url"]), e(s["headline"]))
          if s.get("url") else e(s["headline"]))
    # mirrors the layout's `{% unless hl_last == '?' ... %}` — a headline ending in ? or ! must not
    # render "?." once .fcard__hl--dot::after adds the terminal period.
    _hl = (s["headline"] or "").strip()
    if _hl[-1:] in ('"', "'", "\u201d", "\u2019"):     # a headline may close on a quote
        _hl = _hl[:-1]
    dot = "" if _hl[-1:] in ("?", "!", ".") else " fcard__hl--dot"
    more = ('<button class="fcard__more" type="button" aria-expanded="true">'
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>'
            # mirrors the layout: More is emitted only where it reveals something — a deck card
            # (body hidden) or a brief (body + why hidden). A deckless lead/feature already shows
            # everything folded, so it gets no button.
            '<span>More</span></button>'
            if s["summary"] and (s.get("deck") or s["importance"] == 1) else "")
    deck = '<p class="fcard__deck">%s</p>' % e(s["deck"]) if s.get("deck") else ""
    summ = '<p class="fcard__sum">%s</p>' % e(s["summary"]) if s["summary"] else ""
    why = ('<p class="fcard__why"><span class="fcard__why-lbl">Why it matters</span>%s</p>' % e(s["why"])
           if s.get("why") else "")
    fresh = '<span class="fcard__fresh">Just in</span>' if s.get("fresh") and s["importance"] > 1 else ""
    readbtn = ('<button class="fcard__read" type="button" aria-pressed="false" aria-label="Mark as read"'
               ' title="mark as read"><svg viewBox="0 0 24 24" aria-hidden="true">'
               '<path d="M20 6L9 17l-5-5"/></svg></button>')
    # institution-first source label (mirrors the Liquid in _layouts/home.html)
    src = ('<span class="fcard__aff">%s</span> · %s' % (e(s["affiliation_label"]), e(s["source_domain"]))
           if s.get("affiliation_label") else e(s["source_domain"]))
    return """<article class="fcard imp%(imp)s%(lead)s" data-topics="%(topics)s" data-imp="%(imp)s"%(dk)s%(og)s>
<div class="fcard__in" style="--tc:%(color)s">
<div class="fcard__top"><span class="fcard__beat" title="%(stream)s · %(dlabel)s"><span class="ff-dot"></span>%(tlabel)s</span><span class="fcard__rank" data-imp="%(imp)s">%(rank)s</span></div>
<h2 class="fcard__hl%(dot)s">%(hl)s</h2>
%(deck)s%(summ)s%(why)s%(more)s
<div class="fcard__line"><span class="fcard__src">%(src)s</span>%(fresh)s<span class="fcard__date">%(dlabel)s</span>%(readbtn)s</div>
<div class="fcard__fb" data-story="%(id)s" data-brief="%(date)s-%(stream)s">
<button class="ffb-t" type="button" data-v="1" aria-label="Useful">%(svg)s</button>
<button class="ffb-t ffb-down" type="button" data-v="-1" aria-label="Not useful">%(svg)s</button>
<span class="ffb-note" aria-live="polite"></span></div>
</div></article>""" % {
        "imp": s["importance"], "rank": {3:"Lead",2:"Feature"}.get(s["importance"],"Brief"),
        "lead": lead, "topics": e(" ".join(s["topics"])), "og": og,
        "color": s["topic_color"], "tlabel": e(s["topic_label"]), "hl": hl, "summ": summ, "why": why,
        "src": src, "fresh": fresh, "dlabel": e(s["date_label"]),
        "id": e(s.get("sid") or s["id"]), "date": e(s["date"]), "stream": e(s["stream"]), "svg": SVG,
        "readbtn": readbtn, "more": more, "dot": dot, "deck": deck,
        "dk": ' data-deck=""' if s.get("deck") else "",
    }


def _extract_ed_after():
    """How many stories precede the editorials — READ from the layout, not mirrored.

    A hand-copied `ED_AFTER = 3` with a "keep in step" comment is the same drift class the
    palette extraction above exists to kill: the layout changes, the harness keeps splicing at
    the old index, and every screenshot certifies an order production does not have.
    """
    src = os.path.join(ROOT, "_layouts", "home.html")
    with open(src) as fh:
        m = re.search(r"\{%-?\s*assign\s+ed_after\s*=\s*(\d+)", fh.read())
    if not m:
        raise SystemExit("home_harness: no `{% assign ed_after = N %}` in %s — did the "
                         "editorial placement change shape?" % src)
    return int(m.group(1))


ED_AFTER = _extract_ed_after()


def _extract_rail(feed):
    """The >=1280px rail, READ out of the layout rather than mirrored here.

    Without it this harness reserved the rail's grid track and rendered NOTHING in it — roughly
    390px of blank left margin at 1440 — and that fake defect cost a revert and a re-land on
    2026-07-25 before a live-DOM probe showed production's rail present, 286x567, with content.
    A harness that omits markup the layout emits does not merely fail to test it; it invents
    defects. Extracted, so it cannot drift.

    The one Liquid expression in the block is substituted from the same feed the cards come from.
    Any OTHER tag appearing in there is a hard error: silently shipping `{{ ... }}` into the page
    would render as literal braces and quietly change wrap widths.
    """
    src = os.path.join(ROOT, "_layouts", "home.html")
    with open(src) as fh:
        m = re.search(r'<aside class="folio-rail">.*?</aside>', fh.read(), re.S)
    if not m:
        raise SystemExit("home_harness: no <aside class=\"folio-rail\"> in %s — if the rail was "
                         "renamed or removed, update this extractor deliberately" % src)
    rail = m.group(0)
    first = (feed.get("stories") or [{}])[0]
    rail = re.sub(r"\{\{\s*feed\.stories\.first\.date_label\s*\}\}",
                  html.escape(str(first.get("date_label") or "")), rail)
    leftover = re.findall(r"\{\{.*?\}\}|\{%.*?%\}", rail, re.S)
    if leftover:
        raise SystemExit("home_harness: un-substituted Liquid in the rail markup: %r — add a "
                         "substitution for it rather than rendering literal braces" % leftover)
    return rail


def ed_card(e):
    """Mirrors the editorial-card Liquid in _layouts/home.html (paras are pre-sanitized html)."""
    esc = lambda x: html.escape(str(x or ""))
    paras = "".join('<p class="fcard__edp">%s</p>' % p for p in e.get("paras", []))
    # `lead` deliberately absent (2026-07-25): it was giving editorials BOTH the span=2 width and
    # -- via .fcard.lead .fcard__hl -- the largest headline treatment on the page, measured 32.8px,
    # landing on a generic section title. The fold button is what .fcard--ed.is-folded acts on.
    return ('<article class="fcard fcard--ed" data-topics="" data-imp="2" data-story="ed-%s-%s">'
            '<div class="fcard__in"><div class="fcard__top">'
            '<span class="fcard__beat"><span class="ff-dot"></span>%s</span>'
            '<span class="fcard__rank" data-imp="ed">AI editorial</span></div>'
            '<h2 class="fcard__hl">%s</h2>'
            '<p class="fcard__eddisc">Opinion, written by the desk\'s AI — a synthesis across '
            'the week\'s sourced stories, not itself sourced reporting.</p>%s'
            '<button class="fcard__more" type="button" aria-expanded="true">'
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>'
            '<span>More</span></button>'
            '<div class="fcard__line"><span class="fcard__date">%s</span>'
            '<button class="fcard__read" type="button" aria-pressed="false" aria-label="Mark as read"'
            ' title="mark as read"><svg viewBox="0 0 24 24" aria-hidden="true">'
            '<path d="M20 6L9 17l-5-5"/></svg></button></div></div></article>'
            % (esc(e.get("stream")), esc(e.get("date")), esc(e.get("kicker")),
               esc(e.get("title")), paras, esc(e.get("date_label"))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/home-harness.html")
    ap.add_argument("--refresh-theme", action="store_true",
                    help="re-pull the compiled minimal-mistakes CSS into %s" % THEME_CACHE)
    args = ap.parse_args()

    feed = json.load(open(os.path.join(ROOT, "_data", "homefeed.json")))
    src = open(os.path.join(ROOT, "_layouts", "home.html")).read()
    styles = "\n".join(re.findall(r"<style>.*?</style>", src, re.S))
    # ALL script blocks, in document order — re.search took only the FIRST block, which
    # since 2026-07-11 was the modal script, so the 600+-line folio engine went untested.
    script = "\n".join(re.findall(r"<script>.*?</script>", src, re.S))

    chips = "".join(
        '<button class="ff-chip" type="button" data-topic="%s" aria-pressed="false" style="--tc:%s">'
        '<span class="ff-dot"></span>%s <span class="ff-ct">%d</span></button>'
        % (t["key"], t["color"], t["label"], t["count"]) for t in feed["topics"])

    page = """<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>home harness</title>%s%s
<div class="wrap">
<div class="folio-filters" id="folioFilters"><span class="ff-lbl">Beat</span>
<button class="ff-chip ff-all" type="button" data-topic="" aria-pressed="true">All <span class="ff-ct">%d</span></button>
%s<span class="ff-read" role="group" aria-label="Read state"><button class="ff-rbtn" type="button" data-rs="" aria-pressed="true">All</button><button class="ff-rbtn" type="button" data-rs="unread" aria-pressed="false">Unread <span class="ff-ct ff-uct"></span></button><button class="ff-rbtn" type="button" data-rs="read" aria-pressed="false">Read</button></span>%s</div>
<div class="folio-board">
<span class="ff-crop tl"></span><span class="ff-crop tr"></span><span class="ff-crop bl"></span><span class="ff-crop br"></span>
%s<div class="folio-grid" id="folioGrid">%s</div>
<div class="folio-empty" id="folioEmpty" hidden>No stories on that beat right now.</div>
</div></div>
%s%s%s%s""" % (_theme_css(args.refresh_theme) + TOKENS, styles, feed["count"], chips, SYNC_UI,
               _extract_rail(feed),
               # Emission order mirrors _layouts/home.html: ED_AFTER stories, then the editorials,
               # then the rest. Keep ED_AFTER in step with the layout's `{% assign ed_after %}` —
               # this is the mirror that the published-DOM fixture is meant to retire.
               "".join(card(s) for s in feed["stories"][:ED_AFTER])
               + "".join(ed_card(e) for e in feed.get("editorials", []))
               + "".join(card(s) for s in feed["stories"][ED_AFTER:]), PRE_SYNC, script, GEOM_CHECK, SYNC_CHECK)

    with open(args.out, "w") as fh:
        fh.write(page)
    print("wrote %s (%d bytes, %d stories)" % (args.out, len(page), feed["count"]))


if __name__ == "__main__":
    main()
