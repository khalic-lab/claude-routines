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
Overlaps must be 0; gaps beyond ~200px mean the packing regressed.

It also stubs window.fetch (no real network) and appends a `#synccheck` div at 4.5s
exercising the passkey read-state sync engine (grep for 'SYNC'):
  plain URL     -> signed-out run: rsCalls must be 0 (no sync traffic without a session).
  URL + #synced -> seeded session + stubbed GET /readstate: expects gets=1 painted=1
                   unpainted=1 shadow=1 (remote read paints; newer remote tombstone
                   unmarks a locally-read card; both land in the syncState:v1 shadow).
"""
import argparse
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TOKENS = """<style>
:root{ --paper:#eceae4; --panel:#e2e1d9; --card:#f3f2ec; --ink:#23252b; --muted:#5f616a; --muted-ui:#565863;
 --rule:rgba(35,37,43,.62); --hair:rgba(35,37,43,.14); --field:#f6f5f0; --frame:rgba(35,37,43,.46);
 --accent:#2b3f6b; --accent-chip:#3a3d47; --accent-chip-hover:#2b2e36;
 --serif:ui-serif,'New York','Iowan Old Style',Charter,Georgia,serif;
 --display:ui-serif,'New York','Iowan Old Style',Georgia,serif;
 --sans:'Helvetica Neue',Helvetica,Arial,sans-serif; }
@media (prefers-color-scheme: dark){ :root{ --paper:#14151a; --panel:#1d1e25; --card:#1a1b21; --ink:#e7e5dd;
 --muted:#9a9ca6; --muted-ui:#b0b2bb; --rule:rgba(231,229,221,.5); --hair:rgba(231,229,221,.13);
 --field:rgba(255,255,255,.05); --frame:rgba(231,229,221,.3); --accent:#8fa9df; } }
body{ background:var(--paper); color:var(--ink); font-family:var(--serif); margin:0; }
.wrap{ max-width:1236px; margin:0 auto; padding:0 12px; }
</style>"""

SVG = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28'
       'a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>')

GEOM_CHECK = """<script>
setTimeout(function(){
  // Read each card's TARGET geometry (style.transform + offset box), not
  // getBoundingClientRect: cards animate transform for 280ms after a reflow, and
  // sampling mid-flight reports phantom overlaps that the settled layout doesn't have.
  var grid=document.getElementById('folioGrid');
  var cards=[].slice.call(grid.querySelectorAll('.fcard')).filter(function(c){return c.style.display!=='none';});
  var rects=cards.map(function(c){
    var m=/translate\\(([-\\d.]+)px,\\s*([-\\d.]+)px\\)/.exec(c.style.transform);
    return{l:m?Math.round(+m[1]):0,t:m?Math.round(+m[2]):0,w:c.offsetWidth,h:c.offsetHeight};
  });
  var overlaps=0;for(var i=0;i<rects.length;i++)for(var j=i+1;j<rects.length;j++){var a=rects[i],b=rects[j];if(a.l<b.l+b.w-2&&b.l<a.l+a.w-2&&a.t<b.t+b.h-2&&b.t<a.t+a.h-2)overlaps++;}
  var xs=[];rects.forEach(function(r){if(xs.indexOf(r.l)<0)xs.push(r.l);});
  var maxGap=0;xs.forEach(function(x){var iv=rects.filter(function(r){return r.l<=x&&x+10<r.l+r.w;}).sort(function(a,b){return a.t-b.t;});for(var i=1;i<iv.length;i++){var g=iv[i].t-(iv[i-1].t+iv[i-1].h);if(g>maxGap)maxGap=Math.round(g);}});
  var d=document.createElement('div');d.id='geomcheck';
  d.textContent='GEOM overlaps='+overlaps+' maxGap='+maxGap+' cards='+cards.length+' cols='+xs.length+' bodyScrollW='+document.body.scrollWidth+' innerW='+innerWidth;
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
  var aff = document.getElementById('ffSync');
  var d = document.createElement('div'); d.id = 'synccheck';
  d.textContent = 'SYNC mode=' + (location.hash === '#synced' ? 'in' : 'out') + ' rsCalls=' + rs.length +
    ' gets=' + gets + ' affordance=' + (aff && !aff.hidden ? 1 : 0) +
    ' painted=' + painted + ' unpainted=' + unpainted + ' shadow=' + shadow +
    ' prefsCalls=' + prefsCalls + ' prefsRs=' + prefsRs;
  document.body.appendChild(d);
}, 4500);
</script>"""


def card(s):
    e = lambda x: html.escape(str(x or ""))
    lead = " lead" if s["is_lead"] else ""
    og = ' data-ogurl="%s"' % e(s["url"]) if s.get("url") and s["importance"] > 1 else ""
    hl = ('<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>' % (e(s["url"]), e(s["headline"]))
          if s.get("url") else e(s["headline"]))
    more = ('<button class="fcard__more" type="button" aria-expanded="true">'
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>'
            '<span>More</span></button>' if s["importance"] == 1 and s["summary"] else "")
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
    return """<article class="fcard imp%(imp)s%(lead)s" data-topics="%(topics)s" data-imp="%(imp)s"%(og)s>
<div class="fcard__in" style="--tc:%(color)s">
<div class="fcard__top"><span class="fcard__beat" title="%(stream)s · %(dlabel)s"><span class="ff-dot"></span>%(tlabel)s</span><span class="fcard__rank" data-imp="%(imp)s"></span></div>
<h2 class="fcard__hl">%(hl)s</h2>
%(more)s%(summ)s%(why)s
<div class="fcard__line"><span class="fcard__src">%(src)s</span>%(fresh)s<span class="fcard__date">%(dlabel)s</span>%(readbtn)s</div>
<div class="fcard__fb" data-story="%(id)s" data-brief="%(date)s-%(stream)s">
<button class="ffb-t" type="button" data-v="1" aria-label="Useful">%(svg)s</button>
<button class="ffb-t ffb-down" type="button" data-v="-1" aria-label="Not useful">%(svg)s</button>
<span class="ffb-note" aria-live="polite"></span></div>
</div></article>""" % {
        "imp": s["importance"], "lead": lead, "topics": e(" ".join(s["topics"])), "og": og,
        "color": s["topic_color"], "tlabel": e(s["topic_label"]), "hl": hl, "summ": summ, "why": why,
        "src": src, "fresh": fresh, "dlabel": e(s["date_label"]),
        "id": e(s.get("sid") or s["id"]), "date": e(s["date"]), "stream": e(s["stream"]), "svg": SVG,
        "readbtn": readbtn, "more": more,
    }


def ed_card(e):
    """Mirrors the editorial-card Liquid in _layouts/home.html (paras are pre-sanitized html)."""
    esc = lambda x: html.escape(str(x or ""))
    paras = "".join('<p class="fcard__edp">%s</p>' % p for p in e.get("paras", []))
    return ('<article class="fcard fcard--ed lead" data-topics="" data-imp="2">'
            '<div class="fcard__in"><div class="fcard__top">'
            '<span class="fcard__beat"><span class="ff-dot"></span>%s</span>'
            '<span class="fcard__rank" data-imp="ed"></span></div>'
            '<h2 class="fcard__hl">%s</h2>%s</div></article>'
            % (esc(e.get("kicker")), esc(e.get("title")), paras))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/home-harness.html")
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
<div class="folio-grid" id="folioGrid">%s</div>
<div class="folio-empty" id="folioEmpty" hidden>No stories on that beat right now.</div>
</div></div>
%s%s%s%s""" % (TOKENS, styles, feed["count"], chips, SYNC_UI,
               "".join(ed_card(e) for e in feed.get("editorials", []))
               + "".join(card(s) for s in feed["stories"]), PRE_SYNC, script, GEOM_CHECK, SYNC_CHECK)

    with open(args.out, "w") as fh:
        fh.write(page)
    print("wrote %s (%d bytes, %d stories)" % (args.out, len(page), feed["count"]))


if __name__ == "__main__":
    main()
