// Browser checks for the built site (tools/verify/build.sh output), 2026-09-24 rewrite.
//
//   node tools/verify/suite.mjs [SITE_DIR]      default SITE_DIR=/tmp/fp-build/src/_site
//   ONLY=default,stale WIDTHS=390,1440 node ...  narrow a run; FAULTS=0 skips the self-test
//
// Serves SITE_DIR itself under /claude-routines/ (the production baseurl) and stubs both Workers
// with route(), so nothing leaves the machine. EVERY expectation is derived here from the repo's
// _posts/ filenames, routines/src/*.md and _data/homefeed.json (never from the builder's own
// `period`/`front` output), so the suite stays valid after a rebase onto newer data.
//
// Geometry is measured with the sticky chrome (.bar, .mast) forced to its flow position: a stuck
// bar paints over scrolled content by definition; what must hold is that its flow box reserves
// its own space. Ends with a fault-injection self-test: each deliberate break must fail its own
// assertion, or the suite is not testing what it claims to.
import { chromium, webkit, devices } from 'playwright';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const SITE = path.resolve(process.argv[2] || '/tmp/fp-build/src/_site');
const SHOTS = process.env.SHOTS || '/tmp/fp-shots';
const FB = 'https://feedback-sink.khalic-lab.workers.dev';
const OGP = 'https://og-proxy.khalic-lab.workers.dev';
const WIDTHS = (process.env.WIDTHS || '360,390,700,768,1024,1280,1440,1600').split(',').map(Number);
const STATES = ['default', 'expanded', 'unread-edition', 'beat', 'multi-beat', 'empty', 'stale'];
const ONLY = process.env.ONLY ? process.env.ONLY.split(',') : null;
const TOKEN = 'cd'.repeat(32);

const out = [];
const log = (s) => { out.push(s); console.log(s); };

// ------------------------------------------------------------------ expectations, derived here
const feed = JSON.parse(fs.readFileSync(path.join(REPO, '_data/homefeed.json'), 'utf8'));
const board = feed.board;
const byStream = {};
for (const f of fs.readdirSync(path.join(REPO, '_posts'))) {
  const m = f.match(/^(\d{4}-\d\d-\d\d)-(news|ai-ml|science|weekend|sports)\.md$/);
  if (m) (byStream[m[2]] ||= []).push(m[1]);
}
for (const s in byStream) byStream[s].sort();
// the lookback each routine prompt states ("Coverage window: ...")
const CAP = {};
for (const s of Object.keys(byStream)) {
  const src = fs.readFileSync(path.join(REPO, 'routines/src', s + '.md'), 'utf8');
  const w = (src.match(/Coverage window:\s*([^\n.]+)/) || [])[1] || '';
  CAP[s] = /~?24 hours/.test(w) ? 1 : /7 days/.test(w) ? 7 : /since the last/.test(w) ? null : undefined;
  if (CAP[s] === undefined) throw new Error('cannot read the coverage window of ' + s + ': ' + w);
}
const day = (iso) => new Date(iso + 'T00:00:00Z');
const iso = (d) => d.toISOString().slice(0, 10);
const addDays = (s, n) => { const d = day(s); d.setUTCDate(d.getUTCDate() + n); return iso(d); };
function period(date, stream) {
  const prev = (byStream[stream] || []).filter((d) => d < date);
  const cap = CAP[stream];
  let start = prev.length ? addDays(prev[prev.length - 1], 1) : addDays(date, -((cap || 1) - 1));
  if (cap && start < addDays(date, -(cap - 1))) start = addDays(date, -(cap - 1));
  return [start, date];
}
const dates = [...new Set(board.map((x) => x.date))].sort().reverse();
const EXPECT_TAGS = {};                              // date -> {stream: [start, end]}
for (const d of dates) {
  EXPECT_TAGS[d] = {};
  for (const x of board.filter((x) => x.date === d)) EXPECT_TAGS[d][x.stream] = period(d, x.stream);
}
const sidOf = (x) => (x.kind === 'editorial' ? `ed-${x.stream}-${x.date}` : x.sid || x.id);
// the front: walk the newest dates until four leads/features; lead = first lead; then leads and
// features in board order, briefs only to fill
const stories = board.filter((x) => x.kind !== 'editorial');
const eds = board.filter((x) => x.kind === 'editorial');
let win = [];
for (const d of dates) {
  win = win.concat(stories.filter((x) => x.date === d));
  if (win.filter((x) => x.importance >= 2).length >= 4) break;
}
const lead = win.find((x) => x.importance === 3) || win[0];
const rest = win.filter((x) => x !== lead);
const EXPECT_FRONT = lead ? [lead, ...[...rest.filter((x) => x.importance >= 2), ...rest.filter((x) => x.importance < 2)].slice(0, 3)].map(sidOf) : [];
const deskEd = eds.length ? eds.reduce((a, b) => (b.date > a.date ? b : a)) : null;
const EXPECT_DESK = deskEd ? sidOf(deskEd) : null;
// dynamic targets (the mock pinned 24 Sep ids; these follow the data)
const deskEdition = deskEd ? `${deskEd.date}-${deskEd.stream}` : null;
const beatCounts = {};
for (const x of board) for (const t of x.topics || []) beatCounts[t] = (beatCounts[t] || 0) + 1;
const edBeats = eds.flatMap((e) => stories.filter((x) => x.date === e.date && x.stream === e.stream).flatMap((x) => x.topics));
const BEAT = [...new Set(edBeats)].sort((a, b) => beatCounts[a] - beatCounts[b] || a.localeCompare(b))[0];
const BEAT_ED = eds.find((e) => stories.some((x) => x.date === e.date && x.stream === e.stream && x.topics.includes(BEAT)));
const BEAT_DAYS = dates.filter((d) => board.some((x) => x.date === d && ((x.kind === 'editorial' ? stories.filter((s) => s.date === x.date && s.stream === x.stream).flatMap((s) => s.topics) : x.topics).includes(BEAT))));
const frontIds = new Set([...EXPECT_FRONT, EXPECT_DESK]);
const MEASURE_ROW = stories.filter((x) => !frontIds.has(sidOf(x)) && x.importance > 1 && x.why)
  .sort((a, b) => (b.why.length + b.summary.length) - (a.why.length + a.summary.length))[0];
const OLD = JSON.parse(fs.readFileSync(path.join(REPO, 'tools/verify/fixtures/old-contract.json'), 'utf8'));

// ------------------------------------------------------------------ a static server for SITE
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.xml': 'application/xml', '.txt': 'text/plain', '.png': 'image/png' };
const server = http.createServer((req, res) => {
  let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (!p.startsWith('/claude-routines/')) { res.writeHead(404); res.end(); return; }
  p = path.join(SITE, p.slice('/claude-routines/'.length));
  if (!p.startsWith(SITE)) { res.writeHead(403); res.end(); return; }
  if (fs.existsSync(p) && fs.statSync(p).isDirectory()) p = path.join(p, 'index.html');
  if (!fs.existsSync(p)) { res.writeHead(404); res.end('not found'); return; }
  res.writeHead(200, { 'content-type': MIME[path.extname(p)] || 'application/octet-stream', 'cache-control': 'no-store' });
  fs.createReadStream(p).pipe(res);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const ORIGIN = `http://127.0.0.1:${server.address().port}`;
const BASE = ORIGIN + '/claude-routines/';
const OG_IMG = BASE + 'assets/diagrams/how-it-works-mobile-light.svg';   // same-origin stand-in image

// ------------------------------------------------------------------ Worker stubs + request log
async function stub(ctx, rec, { stamp } = {}) {
  let ogN = 0;
  // anything that is neither this server nor a Worker is logged (watchRequests) and never leaves
  await ctx.route((u) => u.origin !== ORIGIN && u.origin !== FB && u.origin !== OGP && u.protocol !== 'data:', (route) => route.abort());
  await ctx.route((u) => u.origin === FB, async (route) => {
    const r = route.request(), u = new URL(r.url());
    const body = r.postData();
    rec.fb.push({ method: r.method(), path: u.pathname, auth: (r.headers().authorization || '').replace(TOKEN, '<token>'), body: body ? JSON.parse(body) : null, raw: body });
    const json = u.pathname === '/readstate' && r.method() === 'GET' ? { state: {} }
      : u.pathname === '/prefs' && r.method() === 'GET' ? { prefs: null } : { ok: true };
    await route.fulfill({ status: 200, contentType: 'application/json', headers: { 'access-control-allow-origin': '*' }, body: JSON.stringify(json) });
  });
  await ctx.route((u) => u.origin === OGP, async (route) => {
    rec.og++;
    // the first unfurl gets a real (same-origin) image, the rest none: both the filled slot and
    // the collapse are exercised
    await route.fulfill({ status: 200, contentType: 'application/json', headers: { 'access-control-allow-origin': '*' },
      body: JSON.stringify({ image: ogN++ === 0 ? OG_IMG : null }) });
  });
  if (stamp) {
    await ctx.route((u) => u.pathname.endsWith('/edition.json'), (route) => route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ build_stamp: stamp, generated: feed.generated }) }));
  }
}
function watchRequests(page, rec) {
  page.on('request', (r) => {
    const u = new URL(r.url());
    if (u.protocol === 'data:' || u.origin === ORIGIN) return;
    if (u.origin === FB || u.origin === OGP) return;
    rec.ext.push(r.url());
  });
  page.on('pageerror', (e) => rec.errors.push(e.message));
}

// ------------------------------------------------------------------ in-page helpers
const LIB = () => {
  const R = (e) => e.getBoundingClientRect();
  const vis = (e) => { const r = R(e); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
  const name = (e) => e.dataset.zone + (e.dataset.story ? '#' + e.dataset.story : '') + (e.dataset.ptr ? '>' + e.dataset.ptr : '') + (e.dataset.date ? '@' + e.dataset.date : '');
  const visibleItems = () => [...document.querySelectorAll('main [data-story]')].filter(vis);
  const chip = (k) => [...document.querySelectorAll('.chip')].find((c) => c.dataset.topic === k && vis(c));
  const seg = (r) => document.querySelector(`.seg button[data-rs="${r}"]`);
  const ct = (b) => +b.querySelector('.ct').textContent;
  const frontVoids = () => {
    const cells = [...document.querySelectorAll('.front .fc, .front .desk')].filter(vis);
    let max = 0; const per = [];
    for (const c of cells) {
      const blocks = c.classList.contains('desk')
        ? [...c.children, ...c.querySelectorAll('.ed > *')].filter((x) => vis(x) && !x.classList.contains('ed'))
        : [...c.querySelector('article').children].filter(vis);
      const iv = blocks.map((b) => [R(b).top, R(b).bottom]).sort((a, b) => a[0] - b[0]);
      const cr = R(c); let cur = cr.top, gap = 0;
      for (const [t, bt] of iv) { if (t > cur) gap = Math.max(gap, t - cur); cur = Math.max(cur, bt); }
      gap = Math.max(gap, cr.bottom - cur);
      per.push([c.id || 'desk', Math.round(gap)]); max = Math.max(max, gap);
    }
    for (const box of document.querySelectorAll('.front__top, .fcards--rest')) {
      if (!vis(box)) continue; const W = R(box).width; const lines = {};
      for (const k of [...box.children].filter(vis)) { const r = R(k); const t = Math.round(r.top); (lines[t] ||= { w: 0, h: 0 }); lines[t].w += r.width; lines[t].h = Math.max(lines[t].h, r.height); }
      for (const t in lines) if (lines[t].w < W - 2) { per.push(['partial-line', Math.round(lines[t].h)]); max = Math.max(max, lines[t].h); }
    }
    return { max: Math.round(max), per };
  };
  const hlSizes = () => [...document.querySelectorAll('.front .hl')].map((h) => getComputedStyle(h).fontSize).join(',');
  const geometry = () => {
    const st = document.createElement('style'); st.textContent = '.bar,.mast{position:static!important}';
    document.head.appendChild(st);
    const inter = (a, b) => Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) * Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
    const parents = new Set([...document.querySelectorAll('[data-zone]')].map((e) => e.parentElement));
    const overlaps = []; let pairs = 0; const inv = []; let groups = 0;
    for (const p of parents) {
      const kids = [...p.children].filter((c) => c.dataset.zone && vis(c));
      for (let i = 0; i < kids.length; i++) for (let j = i + 1; j < kids.length; j++) {
        pairs++; const a = inter(R(kids[i]), R(kids[j]));
        if (a > 1) overlaps.push(`${name(kids[i])} x ${name(kids[j])} = ${Math.round(a)}px2`);
      }
      // DOM order == visual order; the control bar is chrome and rests after main on phones (R13)
      if (kids.length < 2 || kids.some((k) => k.dataset.zone === 'bar')) continue;
      groups++;
      for (let i = 0; i + 1 < kids.length; i++) {
        const a = R(kids[i]), b = R(kids[i + 1]);
        const ok = Math.abs(a.top - b.top) < 1 ? b.left >= a.left - 0.5 : b.top > a.top;
        if (!ok) inv.push(`${name(kids[i])} -> ${name(kids[i + 1])}`);
      }
    }
    const contain = []; let contained = 0;
    for (const sec of document.querySelectorAll('section[data-zone="day"],section[data-zone="front"]')) {
      if (!vis(sec)) continue; const s = R(sec);
      for (const c of sec.querySelectorAll('[data-zone]')) {
        if (!vis(c)) continue; contained++; const r = R(c);
        if (r.left < s.left - 0.5 || r.right > s.right + 0.5 || r.top < s.top - 0.5 || r.bottom > s.bottom + 0.5) contain.push(`${name(c)} outside ${name(sec)}`);
      }
    }
    const res = { overflow: document.documentElement.scrollWidth > innerWidth ? [`scrollWidth ${document.documentElement.scrollWidth} > ${innerWidth}`] : [],
      overlap: overlaps, containment: contain, order: inv, pairs, contained, groups };
    st.remove();
    return res;
  };
  // longest rendered line of an element's text, in characters (multicol-aware)
  const cpl = (el) => {
    const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); let max = 0, cur = 0, top = null; const rg = document.createRange();
    for (let n; (n = w.nextNode());) {
      if (n.parentElement.closest('.vh')) continue;
      for (let i = 0; i < n.length; i++) {
        rg.setStart(n, i); rg.setEnd(n, i + 1); const r = rg.getClientRects()[0]; if (!r) continue;
        if (top === null || Math.abs(r.top - top) > 3) { max = Math.max(max, cur); cur = 0; top = r.top; }
        cur++;
      }
    }
    return Math.max(max, cur);
  };
  const rgb = (s) => (s.match(/[\d.]+/g) || []).map(Number);
  const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
  const opacityOf = (el) => { let o = 1; for (let a = el; a; a = a.parentElement) o *= +getComputedStyle(a).opacity; return o; };
  const contrast = (el) => {
    const c = rgb(getComputedStyle(el).color), a = (c[3] ?? 1) * opacityOf(el);
    let bg = [255, 255, 255];
    for (let x = el; x; x = x.parentElement) { const b = rgb(getComputedStyle(x).backgroundColor); if (b.length && (b[3] ?? 1) >= 0.99) { bg = b; break; } }
    const m = c.slice(0, 3).map((v, i) => v * a + bg[i] * (1 - a)); const l1 = lum(m), l2 = lum(bg);
    return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
  };
  const deadLinks = () => [...document.querySelectorAll('a[href^="#"]:not([data-dialog])')].filter(vis).map((a) => {
    const id = a.getAttribute('href').slice(1), t = document.getElementById(id);
    return t && vis(t) ? null : `"${a.textContent.trim().slice(0, 28)}" -> #${id}`;
  }).filter(Boolean);
  const dayMeta = () => {
    const bad = []; let days = 0;
    for (const sec of document.querySelectorAll('section.day')) {
      if (!vis(sec)) continue; days++;
      const num = parseInt(sec.querySelector('.day__n').textContent, 10);
      const v = [...sec.querySelectorAll('.rows > [data-story], .rows > [data-ptr]')].filter(vis).length;
      if (num !== v) bad.push(`${sec.dataset.date} says ${num}, shows ${v}`);
      const tags = [...sec.querySelectorAll('.day__cov .ptag')].filter(vis).map((t) => t.dataset.stream).sort().join();
      const desks = [...new Set([...sec.querySelectorAll('[data-edition]')].filter(vis).map((x) => x.dataset.edition.slice(11)))].sort().join();
      if (tags !== desks) bad.push(`${sec.dataset.date} tags [${tags}] vs desks shown [${desks}]`);
    }
    return { bad, days };
  };
  const focusRing = () => {
    const el = document.activeElement;
    if (!el || el === document.body) return { where: 'none' };
    if (el.closest('main')) return { where: 'main' };
    if (!el.closest('.bar,.mast')) return { where: 'other' };
    const cs = getComputedStyle(el), ow = cs.outlineStyle === 'none' ? 0 : parseFloat(cs.outlineWidth), off = parseFloat(cs.outlineOffset) || 0;
    const r = R(el), k = Math.max(0, off + ow);
    const ring = { left: r.left - k, right: r.right + k, top: r.top - k, bottom: r.bottom + k };
    const label = (el.textContent.trim() || el.getAttribute('aria-label') || el.tagName).replace(/\s+/g, ' ').slice(0, 18);
    const bad = [];
    if (!(ow > 0)) bad.push('no ring');
    for (let a = el.parentElement; a; a = a.parentElement) {
      const s = getComputedStyle(a);
      if ((s.maskImage && s.maskImage !== 'none') || (s.webkitMaskImage && s.webkitMaskImage !== 'none')) bad.push('masked by .' + a.className.split(' ')[0]);
      if (a === document.body || a === document.documentElement) continue;
      if (s.overflowX !== 'visible' || s.overflowY !== 'visible') {
        const b = R(a), cl = { left: b.left + a.clientLeft, top: b.top + a.clientTop }; cl.right = cl.left + a.clientWidth; cl.bottom = cl.top + a.clientHeight;
        if (ring.left < cl.left - 0.5 || ring.right > cl.right + 0.5 || ring.top < cl.top - 0.5 || ring.bottom > cl.bottom + 0.5)
          bad.push(`ring clipped by .${a.className.split(' ')[0]}`);
      }
    }
    return { where: 'chrome', label, bad };
  };
  return { R, vis, visibleItems, chip, seg, ct, frontVoids, hlSizes, geometry, cpl, contrast, opacityOf, deadLinks, dayMeta, focusRing };
};

const frame2 = (page) => page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))));

// ------------------------------------------------------------------ one (engine, context, state) case
async function runCase(browser, ctxOpts, state, fault = null) {
  const ctx = await browser.newContext(ctxOpts);
  const rec = { fb: [], og: 0, ext: [], errors: [] };
  await stub(ctx, rec, { stamp: state === 'stale' ? 'a-newer-edition' : null });
  const page = await ctx.newPage();
  watchRequests(page, rec);
  if (fault?.init) await page.addInitScript(fault.init);
  await page.goto(BASE);
  await page.evaluate(() => document.fonts.ready);
  if (fault?.css) await page.addStyleTag({ content: fault.css });
  await page.evaluate(`window.__L = (${LIB.toString()})()`);
  const X = { state, EXPECT_TAGS, EXPECT_FRONT, EXPECT_DESK, deskEdition, BEAT, BEAT_ED: BEAT_ED ? sidOf(BEAT_ED) : null, BEAT_DAYS,
    MEASURE_ROW: MEASURE_ROW ? sidOf(MEASURE_ROW) : null, boardIds: board.map(sidOf), boardDates: board.map((x) => x.date),
    boardKinds: board.map((x) => x.kind), nBoard: board.length, nDays: dates.length };
  if (state === 'stale') {
    // a bfcache restore, then a tab shown again after ten minutes away: both must offer the reload
    await page.evaluate(() => window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true })));
    await page.waitForTimeout(250);
  }
  const fn = await page.evaluate(async (X) => {
    const L = window.__L;
    const A = {};
    const click = (el) => el && el.click();
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    if (X.state === 'default') {
      const n = L.visibleItems().length, all = L.ct(L.seg('')), beatAll = L.ct(L.chip(''));
      A.counts = [n === all && n === beatAll && n === X.nBoard, `visible ${n} / All seg ${all} / All chip ${beatAll} / board ${X.nBoard}`];
      const bad = []; let nTags = 0;
      for (const [d, m] of Object.entries(X.EXPECT_TAGS)) {
        const tags = [...document.querySelectorAll(`#d-${d} .day__cov .ptag`)];
        if (tags.length !== Object.keys(m).length) bad.push(`${d}: ${tags.length} tags, want ${Object.keys(m).length}`);
        for (const t of tags) {
          nTags++;
          const ts = [...t.querySelectorAll('time')].map((x) => x.getAttribute('datetime'));
          const [s, e] = m[t.dataset.stream] || [];
          const got = ts.length === 1 ? [ts[0], ts[0]] : ts;
          if (got[0] !== s || got[1] !== e || !L.vis(t)) bad.push(`${d} ${t.dataset.stream}: ${got} (want ${s}..${e})`);
        }
      }
      for (const ed of document.querySelectorAll('.ed')) {
        const [date, stream] = [ed.dataset.edition.slice(0, 10), ed.dataset.edition.slice(11)];
        const [s, e] = X.EXPECT_TAGS[date][stream];
        const k = [...ed.querySelectorAll('.ed__kick time')].map((x) => x.getAttribute('datetime'));
        const got = k.length === 1 ? [k[0], k[0]] : k;
        if (got[0] !== s || got[1] !== e) bad.push(`${ed.id} kicker ${got}`);
      }
      A.periods = [bad.length === 0 && nTags > 0, bad.join('; ') || `${nTags} day tags + ${document.querySelectorAll('.ed').length} editorial kickers match the derived periods`];
      const frontIds = [...document.querySelectorAll('.front .fc')].map((x) => x.dataset.story);
      const desk = (document.querySelector('.front .desk .ed') || {}).id || null;
      A.front = [frontIds.join() === X.EXPECT_FRONT.join() && desk === X.EXPECT_DESK, `front ${frontIds.length} ${frontIds.join() === X.EXPECT_FRONT.join() ? '=' : '!='} derived; desk ${desk} (want ${X.EXPECT_DESK})`];
      const lifted = [...document.querySelectorAll('.front [data-story]')].map((x) => x.dataset.story);
      const miss = lifted.filter((s) => !document.querySelector(`section.day [data-ptr="${s}"]`));
      A.pointers = [miss.length === 0, miss.length ? 'missing ' + miss : `${lifted.length} lifted items all keep a pointer in their day`];
      // every board item in its own day, in board order (items or pointers)
      const orderBad = [];
      const secs = [...document.querySelectorAll('section.day')];
      if (secs.length !== X.nDays) orderBad.push(`${secs.length} day sections, want ${X.nDays}`);
      for (const sec of secs) {
        const want = X.boardIds.filter((_, i) => X.boardDates[i] === sec.dataset.date);
        const got = [...sec.querySelectorAll('[data-story], [data-ptr]')].map((x) => x.dataset.story || x.dataset.ptr);
        if (want.join() !== got.join()) orderBad.push(`${sec.dataset.date}: ${got.length} vs ${want.length} items or order differs`);
      }
      A.boardOrder = [orderBad.length === 0, orderBad.join('; ') || `${secs.length} day sections carry the board in order`];
      const h1 = document.querySelectorAll('h1').length, h2 = document.querySelectorAll('main h2').length;
      const h3 = document.querySelectorAll('main h3').length, items = document.querySelectorAll('main [data-story]').length;
      A.headings = [h1 === 1 && h2 === X.nDays + 1 && h3 === items, `h1 ${h1}, main h2 ${h2} (days + front ${X.nDays + 1}), h3 ${h3} for ${items} items`];
      // measure (PLAN decision 3): the longest opened index row reads at 50-80 characters per line;
      // below 700px only the ceiling applies (a phone column may be narrower than 50)
      const row = document.getElementById('r-' + X.MEASURE_ROW);
      if (row) {
        const whyN = L.cpl(row.querySelector('.why'));
        click(row.querySelector('.more')); const sumN = L.cpl(row.querySelector('.sum'));
        const cols = getComputedStyle(row.querySelector('.row__body')).columnCount; click(row.querySelector('.more'));
        const mx = Math.max(whyN, sumN), mn = Math.min(whyN, sumN);
        A.measure = [mx <= 80 && (innerWidth < 700 || mn >= 50), `opened row: why ${whyN}, body ${sumN} chars/line (columns ${cols})`];
      }
      const img = document.querySelector('.photo.is-loaded img'), gone = [...document.querySelectorAll('.photo[data-og]')].filter((p) => p.hidden).length;
      A.og = [true, `photo slots: ${document.querySelectorAll('.photo').length}, filled ${document.querySelectorAll('.photo.is-loaded').length}, collapsed ${gone}`];
      if (img) A.og = [img.referrerPolicy === 'no-referrer' && img.loading === 'lazy', A.og[1] + `, referrerPolicy ${img.referrerPolicy}, loading ${img.loading}`];
    }
    if (X.state === 'expanded') {
      // toggle-agnostic: today's leads boot open (R33), so every check first folds, measures,
      // opens, measures, then restores the item's own starting state
      const isOpen = (el) => !el.classList.contains('is-folded');
      const setOpen = (el, want) => { if (isOpen(el) !== want) click(el.querySelector('.more')); };
      const card = document.querySelectorAll('.fcards--rest .fc')[1];
      if (card && card.querySelector('.more')) {
        const was = isOpen(card);
        setOpen(card, false); const f0 = L.frontVoids(), h0 = L.hlSizes();
        setOpen(card, true); const f1 = L.frontVoids(), h1 = L.hlSizes();
        A.gap = [f1.max <= f0.max + 50, `folded max ${f0.max}px, after one expand ${f1.max}px`];
        A.hlSize = [h0 === h1, h0 === h1 ? 'front headline sizes unchanged' : `${h0} -> ${h1}`];
        A.fullRow = [Math.abs(L.R(card).width - L.R(card.parentElement).width) < 2, `open card ${Math.round(L.R(card).width)} of ${Math.round(L.R(card.parentElement).width)}px`];
        setOpen(card, was);
      }
      for (const [k, sel] of [['gapDesk', '.desk .ed'], ['gapLead', '.fcards--top .fc']]) {
        const el = document.querySelector(sel); if (!el || !el.querySelector('.more')) continue;
        const was = isOpen(el);
        setOpen(el, false); const g0 = L.frontVoids(), s0 = L.hlSizes();
        setOpen(el, true); const g1 = L.frontVoids(), s1 = L.hlSizes();
        const top = el.closest('.front__top');
        const full = !top || [...top.children].filter(L.vis).every((c) => Math.abs(L.R(c).width - L.R(top).width) < 2);
        A[k] = [g1.max <= g0.max + 50 && s0 === s1 && full, `${sel} open: void ${g0.max} -> ${g1.max}px, headline sizes ${s0 === s1 ? 'unchanged' : 'changed'}, top band full rows ${full}`];
        setOpen(el, was);
      }
      // every item opens and closes, and its More tells the truth, whatever its starting state
      let bad = 0, n = 0, bootOpen = 0;
      for (const b of [...document.querySelectorAll('main .more')].slice(0, 40)) {
        const it = b.closest('[data-story]'); n++;
        const was = isOpen(it); if (was) bootOpen++;
        const startOk = b.getAttribute('aria-expanded') === String(was) && b.textContent.trim() === (was ? 'Less' : 'More');
        click(b); const flipOk = isOpen(it) === !was && b.getAttribute('aria-expanded') === String(!was) && (was || L.vis(it.querySelector('.fold')));
        click(b); const backOk = isOpen(it) === was && b.getAttribute('aria-expanded') === String(was);
        if (!(startOk && flipOk && backOk)) bad++;
      }
      A.fold = [bad === 0 && n > 0, `${n} More buttons (${bootOpen} boot open) flip and return truthfully, ${bad} bad`];
    }
    if (X.state === 'unread-edition') {
      const u0 = L.ct(L.seg('unread'));
      const sci = [...document.querySelectorAll(`[data-story][data-edition="${X.deskEdition}"]`)].filter((x) => x.dataset.zone !== 'editorial');
      sci.forEach((s) => click(s.querySelector('.readbtn')));
      const u1 = L.ct(L.seg('unread'));
      const ed = document.getElementById(X.EXPECT_DESK);
      const derived = ed.classList.contains('is-read') && ed.querySelector('.readbtn').getAttribute('aria-pressed') === 'true';
      const disc = ed.querySelector('.ed__disc');
      const dOp = L.opacityOf(disc);
      A.disc = [derived && dOp === 1 && L.contrast(disc) >= 4.5, `read editorial's AI disclosure: opacity ${dOp}, ${L.contrast(disc).toFixed(2)}:1`];
      const readText = [...document.querySelectorAll('.is-read .why, .is-read .sum, .is-read .ed__hl, .is-read .ed__body p, .ptr.is-read .ptr__h')].filter(L.vis);
      const worst = readText.map((e) => [L.contrast(e), e.className]).sort((a, b) => a[0] - b[0])[0];
      A.readContrast = [readText.length > 0 && worst[0] >= 4.5, `${readText.length} read text blocks, lowest ${worst ? worst[0].toFixed(2) + ':1' : 'n/a'}`];
      click(ed.querySelector('.readbtn'));                                     // explicit un-tick wins
      const untick = !ed.classList.contains('is-read') && L.ct(L.seg('unread')) === u1 + 1;
      const stored = JSON.parse(localStorage.getItem('homeUnread:v1') || '{}')[X.EXPECT_DESK] > 0;
      click(ed.querySelector('.readbtn'));
      click(L.seg('unread'));
      const n = L.visibleItems().length, u2 = L.ct(L.seg('unread'));
      A.edRead = [u0 - u1 === sci.length + 1 && derived, `${sci.length} stories ticked: Unread ${u0} -> ${u1} (editorial counted once: ${u0 - u1 === sci.length + 1}), derived read ${derived}`];
      A.override = [untick && stored, `explicit un-tick wins over the edition rule: ${untick}, kept locally ${stored}`];
      A.counts = [n === u2 && !L.vis(ed), `Unread chip ${u2} vs visible ${n}; the edition's editorial hidden ${!L.vis(ed)}`];
      const emptyDays = [...document.querySelectorAll('section.day')].filter((s) => !s.hidden && !s.querySelector('[data-story]:not([hidden]),[data-ptr]:not([hidden])'));
      A.dayHide = [emptyDays.length === 0, `${emptyDays.length} shown day editions with zero visible rows`];
      const sync = JSON.parse(localStorage.getItem('syncState:v1') || '{}');
      A.localEd = [!Object.keys(sync).some((k) => !/^st-[0-9a-f]{12}$/.test(k)), `syncState:v1 holds ${Object.keys(sync).length} st- ids and no ed- id`];
    }
    if (X.state === 'beat') {
      click(L.chip(X.BEAT));
      const n = L.visibleItems().length, c = L.ct(L.chip(X.BEAT)), all = L.ct(L.seg(''));
      A.counts = [n === c && n === all, `${X.BEAT} chip ${c} / All seg ${all} vs visible ${n}`];
      const ed = X.BEAT_ED && document.getElementById(X.BEAT_ED);
      A.beatEd = [!!ed && L.vis(ed), `${X.BEAT_ED} visible under ${X.BEAT}: ${!!ed && L.vis(ed)}`];
      const shownDays = [...document.querySelectorAll('section.day')].filter(L.vis).map((s) => s.dataset.date);
      A.dayHide = [shownDays.join() === X.BEAT_DAYS.join(), `day editions shown: ${shownDays.join()} (want ${X.BEAT_DAYS.join()})`];
      const saved = JSON.parse(localStorage.getItem('topicPrefs:v1') || 'null');
      A.prefs = [!!saved && Object.keys(saved).join() === 'topics,rs,ts' && saved.topics.join() === X.BEAT && saved.rs === '' && saved.ts > 0, 'topicPrefs:v1 ' + JSON.stringify(saved)];
    }
    if (X.state === 'multi-beat') {
      click(L.chip(X.BEAT));
      const bad = []; let tried = 0;
      for (const c of [...document.querySelectorAll('.chip')].filter(L.vis)) {
        const k = c.dataset.topic, n = L.ct(c); tried++;
        if (k === '') { click(c); const v = L.visibleItems().length; if (v !== n) bad.push(`All ${n} shows ${v}`); click(L.chip(X.BEAT)); continue; }
        if (c.getAttribute('aria-pressed') === 'true') { const v = L.visibleItems().length; if (v !== n) bad.push(`${k} (held) ${n} shows ${v}`); continue; }
        click(c); const v = L.visibleItems().length; if (v !== n) bad.push(`${X.BEAT}+${k} chip ${n} shows ${v}`); click(c);
      }
      A.multiBeat = [bad.length === 0 && tried > 2, `${tried} chips with ${X.BEAT} held: ${bad.length ? bad.join('; ') : 'all honest'}`];
    }
    if (X.state === 'empty') {
      click(L.chip(X.BEAT)); click(L.seg('read'));
      const em = document.getElementById('empty'), n = L.visibleItems().length;
      const first = [...document.querySelector('main').children].filter(L.vis)[0];
      A.emptyFirst = [n === 0 && first === em && em.textContent.trim().length > 0, `visible ${n}; first line: "${first ? first.textContent.trim().slice(0, 60) : ''}"`];
      A.counts = [L.ct(L.seg('read')) === 0 && L.ct(L.chip(X.BEAT)) === 0, `Read ${L.ct(L.seg('read'))}, ${X.BEAT} ${L.ct(L.chip(X.BEAT))}`];
    }
    if (X.state === 'stale') {
      const bar = document.querySelector('.notice');
      const afterPageshow = L.vis(bar);
      bar.hidden = true;
      // hidden for eleven minutes, then shown again
      Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'hidden' });
      document.dispatchEvent(new Event('visibilitychange'));
      const now = Date.now; Date.now = () => now() + 11 * 60 * 1000;
      Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'visible' });
      document.dispatchEvent(new Event('visibilitychange'));
      await sleep(300);
      Date.now = now;
      const afterResume = L.vis(bar);
      A.fresh = [afterPageshow && afterResume && !!bar.querySelector('button'), `New edition bar after a bfcache restore ${afterPageshow}, after 11 min away ${afterResume}`];
    }
    const dead = L.deadLinks(); A.links = [dead.length === 0, dead.length ? dead.join('; ') : 'every visible in-page link has a rendered target'];
    const dm = L.dayMeta(); A.dayMeta = [dm.bad.length === 0, `${dm.days} day headers ${dm.bad.join('; ') || 'match what they show'}`];
    return A;
  }, X);
  const KEY = browser.browserType().name() === 'webkit' ? 'Alt+Tab' : 'Tab';
  if (state === 'default' && !fault?.noFocus) {
    await page.evaluate(() => { scrollTo(0, 0); document.activeElement && document.activeElement.blur(); });
    const seen = [];
    for (let i = 0; i < 70; i++) {
      await page.keyboard.press(KEY);
      await frame2(page);
      const f = await page.evaluate(() => window.__L.focusRing());
      if (f.where === 'main') break;
      if (f.where === 'chrome') seen.push(f);
    }
    const bw = await page.evaluate(() => innerWidth);
    if (bw < 700) {
      const under = []; let stops = 0;
      for (let i = 1; i <= 12; i++) {
        const ready = await page.evaluate((i) => {
          const L = window.__L, list = [...document.querySelectorAll('main a[href], main button, main summary')].filter((e) => L.vis(e) && !e.closest('[hidden]'));
          const prev = list[i - 1], el = list[i]; if (!el) return false;
          const bar = document.querySelector('.bar').getBoundingClientRect();
          scrollBy(0, el.getBoundingClientRect().bottom - (bar.top + 10));
          window.__want = el; prev.focus({ preventScroll: true }); return true;
        }, i);
        if (!ready) break;
        await page.keyboard.press(KEY);
        await frame2(page);
        const u = await page.evaluate(() => { const e = document.activeElement, b = document.querySelector('.bar').getBoundingClientRect(), r = e.getBoundingClientRect();
          return e === window.__want ? { ok: r.bottom <= b.top + 0.5, d: `${(e.textContent.trim() || e.getAttribute('aria-label') || '').slice(0, 16)} bottom ${Math.round(r.bottom)} > bar top ${Math.round(b.top)}` } : null; });
        if (!u) continue; stops++; if (!u.ok) under.push(u.d);
      }
      fn.focusMain = [stops >= 8 && under.length === 0, `${stops} controls parked under the phone bar then tabbed to, ${under.length} left under it ${under.slice(0, 2).join('; ')}`];
    }
    if (seen.length) {
      const bad = seen.filter((f) => f.bad.length);
      fn.focus = [bad.length === 0, `${seen.length} chrome controls tabbed${bad.length ? ': ' + bad.slice(0, 3).map((f) => f.label + ' ' + f.bad.join(',')).join(' | ') : ', every ring whole'}`];
    }
  }
  const g = await page.evaluate(() => window.__L.geometry());
  await ctx.close();
  return {
    overflow: [g.overflow.length === 0, g.overflow.join('; ') || 'none'],
    overlap: [g.overlap.length === 0, `${g.overlap.length} of ${g.pairs} sibling pairs ${g.overlap.slice(0, 3).join('; ')}`],
    containment: [g.containment.length === 0, `${g.containment.length} of ${g.contained} outside ${g.containment.slice(0, 3).join('; ')}`],
    order: [g.order.length === 0, `${g.order.length} inversions over ${g.groups} groups ${g.order.slice(0, 3).join('; ')}`],
    external: [rec.ext.length === 0, rec.ext.length + ' requests to other hosts ' + rec.ext.slice(0, 2).join(' ')],
    signedOut: [rec.fb.length === 0, `${rec.fb.length} feedback-sink requests while signed out`],
    errors: [rec.errors.length === 0, rec.errors.length + ' page errors ' + rec.errors.slice(0, 2).join(' | ')],
    ...fn,
  };
}

// ------------------------------------------------------------------ no-JS
async function runNoJs(browser, ctxOpts) {
  const ctx = await browser.newContext({ ...ctxOpts, javaScriptEnabled: false });
  const rec = { fb: [], og: 0, ext: [], errors: [] };
  await stub(ctx, rec);
  const p = await ctx.newPage(); watchRequests(p, rec);
  await p.goto(BASE);
  const r = await p.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const hiddenText = [...document.querySelectorAll('.page :is(.fold, .why, .sum, .ed__body, .ed__disc, .hl, .ptag)')].filter((e) => !vis(e) && e.textContent.trim()).length;
    const controls = [...document.querySelectorAll('.page button, .page input, .page textarea')].filter(vis).length;
    const hiwLink = [...document.querySelectorAll('a[href="#hiw"]')].some(vis), key = vis(document.querySelector('.mast__key summary'));
    return { hiddenText, controls, hiwLink, key, scroll: document.documentElement.scrollWidth - innerWidth, js: document.documentElement.className };
  });
  await p.goto(BASE + '#hiw');
  r.hiw = await p.evaluate(() => { const d = document.getElementById('hiw'), b = d.getBoundingClientRect(); return b.width > 0 && b.height > 0 && b.top < innerHeight && b.bottom > 0 && [...d.querySelectorAll('button')].every((x) => !x.getBoundingClientRect().width); });
  await ctx.close();
  const ok = r.hiddenText === 0 && r.controls === 0 && r.scroll <= 0 && r.hiwLink && r.hiw && r.key && rec.ext.length === 0;
  return [ok, `hidden text blocks ${r.hiddenText}, visible controls ${r.controls}, overflow ${r.scroll}, How-this-works link ${r.hiwLink} -> #hiw shown ${r.hiw}, key ${r.key}, external ${rec.ext.length}`];
}

// ------------------------------------------------------------------ contract parity with the old page
async function runContract(browser, ctxOpts, fault = null) {
  const A = {};
  const picks = {                                     // the old capture's choices, re-made on today's board
    read: [sidOf(stories[0]), sidOf(stories[5]), sidOf(eds[0])],
    topic: stories[0].topics[0],
    vote: sidOf(stories[8]),
  };
  const sameIds = picks.read.join() === OLD.picked.read.join() && picks.vote === OLD.picked.vote.story;
  // 1) an old-page snapshot restores: legacy shapes (no rs, no at, an ed- id in syncState)
  {
    const ctx = await browser.newContext(ctxOpts);
    const rec = { fb: [], og: 0, ext: [], errors: [] };
    await stub(ctx, rec);
    const snapshot = { ...OLD.storage['homeRead:v1'] };
    for (const id of picks.read) if (!(id in snapshot)) snapshot[id] = Date.now() - 1000;   // after a rebase: the same shape on today's ids
    await ctx.addInitScript(([snap, sync, token]) => {
      if (sessionStorage.getItem('__seeded')) return;
      sessionStorage.setItem('__seeded', '1');
      const now = Date.now();
      const fresh = Object.fromEntries(Object.keys(snap).map((k) => [k, now - 5000]));
      localStorage.setItem('homeRead:v1', JSON.stringify(fresh));
      localStorage.setItem('syncState:v1', JSON.stringify(Object.fromEntries(Object.keys(sync).map((k) => [k, { ts: now - 5000, v: 1 }]))));
      localStorage.setItem('topicPrefs:v1', JSON.stringify({ topics: ['politics'], ts: now - 5000 }));   // pre-2026-07-18: no rs
      localStorage.setItem('syncSession:v1', JSON.stringify({ token, reader: 'tester' }));              // no `at`
      localStorage.setItem('siteKey', 'retired');
    }, [snapshot, OLD.storage['syncState:v1'], TOKEN]);
    const page = await ctx.newPage(); watchRequests(page, rec);
    await page.goto(BASE); await page.waitForTimeout(400);
    const r = await page.evaluate((ids) => ({
      read: ids.filter((id) => document.querySelector(`[data-story="${id}"]`)).map((id) => [id, document.querySelector(`[data-story="${id}"]`).classList.contains('is-read')]),
      sync: Object.keys(JSON.parse(localStorage.getItem('syncState:v1') || '{}')),
      chip: (document.querySelector('.bar .chip[data-topic="politics"]') || {}).ariaPressed || (document.querySelector('.bar .chip[data-topic="politics"]')?.getAttribute('aria-pressed')),
      rs: document.querySelector('.seg button[aria-pressed="true"]').dataset.rs,
      syncBtn: document.querySelector('.syncbtn[data-dialog="sync"]').textContent,
      siteKey: localStorage.getItem('siteKey'),
    }), Object.keys(snapshot));
    const gets = rec.fb.filter((x) => x.method === 'GET').map((x) => x.path).sort().join();
    A.snapshotRead = [r.read.length >= 3 && r.read.every(([, v]) => v), `${r.read.filter(([, v]) => v).length} of ${r.read.length} snapshot ids on the page paint read`];
    A.legacyShapes = [r.chip === 'true' && r.rs === '' && /Synced · tester/.test(r.syncBtn) && gets === '/prefs,/readstate' && r.siteKey === null,
      `topicPrefs without rs -> politics pressed ${r.chip}, rs "${r.rs}"; session without at -> "${r.syncBtn}", GETs ${gets}; siteKey removed ${r.siteKey === null}`];
    A.pruneEd = [!r.sync.some((k) => k.startsWith('ed-')) && r.sync.length > 0, `syncState:v1 after load: ${r.sync.length} ids, ed- ids ${r.sync.filter((k) => k.startsWith('ed-')).length}`];
    await ctx.close();
  }
  // 2) the old capture's interactions, replayed: storage and request bodies byte-compatible
  {
    const ctx = await browser.newContext(ctxOpts);
    const rec = { fb: [], og: 0, ext: [], errors: [] };
    await stub(ctx, rec);
    await ctx.addInitScript(([token]) => {
      if (sessionStorage.getItem('__seeded')) return;
      sessionStorage.setItem('__seeded', '1');
      localStorage.setItem('syncSession:v1', JSON.stringify({ token, reader: 'tester', at: Date.now() - 3600e3 }));
    }, [TOKEN]);
    if (fault?.init) await ctx.addInitScript(fault.init);
    const page = await ctx.newPage(); watchRequests(page, rec);
    await page.goto(BASE); await page.waitForTimeout(300);
    await page.evaluate((p) => {
      const el = (id) => document.querySelector(`[data-story="${id}"]`);
      p.read.forEach((id) => el(id).querySelector('.readbtn').click());
      document.querySelector(`.bar .chip[data-topic="${p.topic}"]`).click();
      document.querySelector('.seg button[data-rs="unread"]').click();
      const v = el(p.vote);
      v.querySelector('.vote[data-v="-1"]').click();
      v.querySelector('.rzn input').value = 'reason text';
      v.querySelector('.rzn button').click();
      const d = document.querySelector('.propose'); d.open = true;
      const f = document.querySelector('.propose__form');
      f.querySelector('[name=topic]').value = 'A topic'; f.querySelector('[name=detail]').value = 'Some detail';
      f.requestSubmit();
    }, picks);
    await page.waitForTimeout(300);
    await page.evaluate(() => {
      Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'hidden' });
      document.dispatchEvent(new Event('visibilitychange'));
    });
    await page.waitForTimeout(500);
    const storage = await page.evaluate(() => Object.fromEntries(['homeRead:v1', 'syncState:v1', 'topicPrefs:v1'].map((k) => [k, JSON.parse(localStorage.getItem(k))])));
    await ctx.close();
    const oldReq = OLD.requests, newReq = rec.fb;
    const shape = (o) => (o === null ? 'null' : Array.isArray(o) ? '[' + o.map(shape).join(',') + ']' : typeof o === 'object' ? '{' + Object.keys(o).map((k) => k + ':' + shape(o[k])).join(',') + '}' : typeof o);
    const find = (list, method, p) => list.filter((x) => x.method === method && x.path === p);
    const bad = [];
    for (const [m, p] of [['GET', '/readstate'], ['GET', '/prefs'], ['POST', '/submit'], ['POST', '/propose'], ['POST', '/readstate'], ['POST', '/prefs']]) {
      const o = find(oldReq, m, p), n = find(newReq, m, p);
      if (o.length !== n.length) { bad.push(`${m} ${p}: old ${o.length} calls, new ${n.length}`); continue; }
      o.forEach((oo, i) => {
        const nn = n[i];
        if (oo.auth !== nn.auth) bad.push(`${m} ${p} auth`);
        if (!oo.body) return;
        if (p === '/readstate') {
          const want = Object.keys(oo.body.state).filter((k) => !k.startsWith('ed-')).length;   // B2: ed- ids no longer travel
          const got = nn.body && nn.body.state ? Object.keys(nn.body.state) : [];
          if (Object.keys(nn.body).join() !== 'state' || got.length !== want || got.some((k) => !/^st-[0-9a-f]{12}$/.test(k)) || got.some((k) => shape(nn.body.state[k]) !== '{ts:number,v:number}'))
            bad.push(`POST /readstate body ${JSON.stringify(nn.body).slice(0, 80)}`);
          if (sameIds && got.sort().join() !== Object.keys(oo.body.state).filter((k) => !k.startsWith('ed-')).sort().join()) bad.push('POST /readstate ids differ');
          return;
        }
        if (shape(oo.body) !== shape(nn.body)) bad.push(`${m} ${p} shape ${shape(nn.body)} vs ${shape(oo.body)}`);
        const strip = (b) => JSON.stringify({ ...b, ts: undefined });
        if (sameIds && strip(oo.body) !== strip(nn.body)) bad.push(`${m} ${p} values ${strip(nn.body)} vs ${strip(oo.body)}`);
      });
    }
    A.requests = [bad.length === 0, bad.join('; ') || `${newReq.length} Worker calls: same routes, auth, key order and ${sameIds ? 'values' : 'shapes'} as the old page (ed- ids no longer sent)`];
    const sbad = [];
    const oldS = OLD.storage;
    if (shape(Object.values(storage['homeRead:v1'])) !== shape(Object.values(oldS['homeRead:v1']))) sbad.push('homeRead:v1 values');
    if (sameIds && Object.keys(storage['homeRead:v1']).sort().join() !== Object.keys(oldS['homeRead:v1']).sort().join()) sbad.push('homeRead:v1 ids');
    if (Object.keys(storage['syncState:v1']).length !== Object.keys(oldS['syncState:v1']).filter((k) => !k.startsWith('ed-')).length) sbad.push('syncState:v1 ids');
    if (Object.values(storage['syncState:v1']).some((v) => shape(v) !== '{ts:number,v:number}')) sbad.push('syncState:v1 values');
    if (Object.keys(storage['topicPrefs:v1']).join() !== 'topics,rs,ts' || storage['topicPrefs:v1'].rs !== oldS['topicPrefs:v1'].rs
        || (sameIds && storage['topicPrefs:v1'].topics.join() !== oldS['topicPrefs:v1'].topics.join())) sbad.push('topicPrefs:v1 ' + JSON.stringify(storage['topicPrefs:v1']));
    A.storage = [sbad.length === 0, sbad.join('; ') || `homeRead:v1 ${Object.keys(storage['homeRead:v1']).length} ids, syncState:v1 ${Object.keys(storage['syncState:v1']).length} st- ids, topicPrefs:v1 {topics,rs,ts}: same shapes as the old page`];
    A.contractExternal = [rec.ext.length === 0, rec.ext.length + ' requests to other hosts'];
  }
  return A;
}

// ------------------------------------------------------------------ sweeps
let fails = 0; const totals = {};
const tally = (k, ok) => { const t = (totals[k] ||= { pass: 0, fail: 0 }); ok ? t.pass++ : t.fail++; if (!ok) fails++; };
async function sweep(browser, label, opts) {
  for (const st of STATES) {
    if (ONLY && !ONLY.includes(st)) continue;
    const A = await runCase(browser, opts, st);
    const bad = Object.entries(A).filter(([, [ok]]) => !ok);
    Object.values(A).forEach(([ok]) => tally(st, ok));
    log(`${label.padEnd(24)} ${st.padEnd(15)} ${bad.length ? 'FAIL ' + bad.map(([k, [, d]]) => k + ': ' + d).join(' | ') : 'PASS ' + Object.keys(A).length}`
      + (st === 'default' && A.measure ? `  (${A.measure[1]}${A.focus ? '; ' + A.focus[1] : ''})` : ''));
  }
}
const c = await chromium.launch();
const wk = await webkit.launch();
log(`suite: ${BASE} <- ${SITE}; board ${board.length} items, ${dates.length} days, front [${EXPECT_FRONT.join(' ')}] desk ${EXPECT_DESK}; beat ${BEAT}; caps ${JSON.stringify(CAP)}`);
for (const scheme of ['light', 'dark']) {
  for (const w of WIDTHS) await sweep(c, `chromium ${w} ${scheme}`, { viewport: { width: w, height: 900 }, colorScheme: scheme });
  await sweep(wk, `webkit iPhone15 ${scheme}`, { ...devices['iPhone 15'], colorScheme: scheme });
  await sweep(wk, `webkit 1024 ${scheme}`, { viewport: { width: 1024, height: 900 }, colorScheme: scheme });
}
if (!ONLY || ONLY.includes('no-js')) {
  for (const scheme of ['light', 'dark']) {
    for (const w of WIDTHS) {
      const [ok, d] = await runNoJs(c, { viewport: { width: w, height: 900 }, colorScheme: scheme });
      tally('no-js', ok); log(`${('chromium ' + w + ' ' + scheme).padEnd(24)} no-js           ${ok ? 'PASS' : 'FAIL'} ${d}`);
    }
    const [ok, d] = await runNoJs(wk, { ...devices['iPhone 15'], colorScheme: scheme });
    tally('no-js', ok); log(`${('webkit iPhone15 ' + scheme).padEnd(24)} no-js           ${ok ? 'PASS' : 'FAIL'} ${d}`);
  }
}
if (!ONLY || ONLY.includes('contract')) {
  for (const [label, b, opts] of [['chromium 1024', c, { viewport: { width: 1024, height: 900 } }], ['webkit iPhone15', wk, { ...devices['iPhone 15'] }]]) {
    const A = await runContract(b, opts);
    for (const [k, [ok, d]] of Object.entries(A)) { tally('contract', ok); log(`${label.padEnd(24)} contract        ${ok ? 'PASS' : 'FAIL'} ${k}: ${d}`); }
  }
}

log('\n== TOTALS per state (assertions passed / failed)');
let P = 0, F = 0;
for (const [k, t] of Object.entries(totals)) { log(`${k.padEnd(15)} ${t.pass} passed / ${t.fail} failed`); P += t.pass; F += t.fail; }
log(`ALL            ${P} passed / ${F} failed (${P + F} assertions)`);

// ------------------------------------------------------------------ fault injection
if (process.env.FAULTS !== '0') {
  log('\n== FAULT INJECTION (chromium 1440 unless noted): each deliberate break must fail its own assertion');
  const d3 = `#d-${dates[Math.min(2, dates.length - 1)]}`;
  const FAULTS = [
    { key: 'overflow', state: 'default', css: 'main{min-width:1800px}' },
    { key: 'overlap', state: 'default', css: '.fcards--rest > .fc:nth-child(2){margin-left:-120px}' },
    { key: 'containment', state: 'default', css: `${d3} .rows{translate:0 -300px}` },
    { key: 'order', state: 'default', css: `${d3} .rows{flex-direction:column-reverse}` },
    { key: 'periods', state: 'default', css: '.day__cov{display:none}' },
    { key: 'gap', state: 'expanded', css: '.js .fcards--rest > .fc.is-open{flex-basis:30%!important}' },
    { key: 'gapDesk', state: 'expanded', css: '.js .front__top:has(.is-open) > .desk{flex-basis:clamp(240px,27%,340px)!important}.js .front__top:has(.is-open) > .fcards--top{flex-basis:60%!important}' },
    { key: 'hlSize', state: 'expanded', css: '.js .fcards--rest .fc.is-open .hl{font-size:48px!important}' },
    { key: 'fold', state: 'expanded', css: '.js .is-open .fold{display:none!important}' },
    { key: 'counts', state: 'beat', css: '[data-story][hidden]{display:flex!important}' },
    { key: 'beatEd', state: 'beat', css: `#${BEAT_ED ? sidOf(BEAT_ED) : 'x'}{display:none!important}` },
    { key: 'emptyFirst', state: 'empty', css: '#empty{display:none!important}' },
    { key: 'overflow', state: 'default', css: '.day__cov{white-space:nowrap}.day__cov::after{content:"";display:inline-block;inline-size:600px}', w: 360 },
    { key: 'measure', state: 'default', css: '.row__body{columns:auto!important}.row .why,.row .sum{max-inline-size:none!important}' },
    { key: 'measure', state: 'default', css: '.row__body{columns:auto!important}.row .why,.row .sum{max-inline-size:none!important}', w: 768 },
    { key: 'focus', state: 'default', css: '.seg{overflow:hidden}' },
    { key: 'focus', state: 'default', css: '.bar .beats:has(:focus-visible){mask-image:linear-gradient(90deg,#000 88%,transparent)}', w: 768 },
    { key: 'focusMain', state: 'default', css: 'html{scroll-padding-block-end:0!important}', w: 390 },
    { key: 'links', state: 'unread-edition', css: 'main a.jump[hidden],.day__links[hidden]{display:inline-flex!important}' },
    { key: 'dayMeta', state: 'beat', css: '.day__cov .ptag[hidden]{display:inline-flex!important}' },
    { key: 'disc', state: 'unread-edition', css: '.is-read .ed__disc{opacity:.58}' },
    { key: 'readContrast', state: 'unread-edition', css: '.is-read .why{opacity:.58}' },
    { key: 'multiBeat', state: 'multi-beat', css: 'section.day .row[hidden]{display:block!important}' },
    { key: 'headings', state: 'default', css: '', init: () => document.addEventListener('DOMContentLoaded', () => document.querySelector('.day__h').insertAdjacentHTML('afterend', '<h1>extra</h1>')) },
    { key: 'external', state: 'default', css: '', init: () => document.addEventListener('DOMContentLoaded', () => { const i = new Image(); i.src = 'https://cdn.jsdelivr.net/npm/x.png'; }) },
    { key: 'fresh', state: 'stale', css: '.notice{display:none!important}' },
  ];
  let caught = 0;
  const base = await runCase(c, { viewport: { width: 1440, height: 900 } }, 'default');
  for (const f of FAULTS) {
    const A = await runCase(c, { viewport: { width: f.w || 1440, height: 900 } }, f.state, f);
    const flipped = A[f.key] && !A[f.key][0];
    if (flipped) caught++;
    log(`${flipped ? 'CAUGHT' : 'MISSED'}  ${f.key.padEnd(12)} ${f.state.padEnd(14)} ${(f.w || 1440) + 'px'}  ${f.css || '(script)'}  ->  ${A[f.key] ? A[f.key][1] : 'n/a'}`);
  }
  // contract faults: the /prefs body grows a field; homeRead:v1 gets a non-number value
  const CF = [
    { key: 'requests', init: () => { const f = window.fetch; window.fetch = (u, o) => { if (String(u).endsWith('/prefs') && o && o.body) { const b = JSON.parse(o.body); b.extra = 1; o = { ...o, body: JSON.stringify(b) }; } return f(u, o); }; } },
    { key: 'storage', init: () => { const s = Storage.prototype.setItem; Storage.prototype.setItem = function (k, v) { if (k === 'homeRead:v1') { const o = JSON.parse(v); for (const x in o) o[x] = true; v = JSON.stringify(o); } return s.call(this, k, v); }; } },
  ];
  for (const f of CF) {
    const A = await runContract(c, { viewport: { width: 1024, height: 900 } }, f);
    const flipped = A[f.key] && !A[f.key][0];
    if (flipped) caught++;
    log(`${flipped ? 'CAUGHT' : 'MISSED'}  ${f.key.padEnd(12)} contract       (script)  ->  ${A[f.key] ? A[f.key][1] : 'n/a'}`);
  }
  const total = FAULTS.length + CF.length;
  const clean = Object.values(base).every(([ok]) => ok);
  log(`fault self-test: ${caught}/${total} faults caught (baseline default@1440 ${clean ? 'clean' : 'NOT clean'})`);
  if (caught !== total || !clean) fails++;
}

// ------------------------------------------------------------------ screenshots
if (process.env.SHOTS !== '0') {
  fs.mkdirSync(SHOTS, { recursive: true });
  const review = fs.readdirSync(path.join(REPO, '_posts')).filter((f) => /-evaluator\.md$/.test(f)).sort().pop().slice(0, 10).split('-');
  const pages = [
    ['home-1440-light', c, { viewport: { width: 1440, height: 900 }, colorScheme: 'light' }, ''],
    ['home-1440-dark', c, { viewport: { width: 1440, height: 900 }, colorScheme: 'dark' }, ''],
    ['home-1024-light', c, { viewport: { width: 1024, height: 900 }, colorScheme: 'light' }, ''],
    ['home-iphone15-light', wk, { ...devices['iPhone 15'], colorScheme: 'light' }, ''],
    ['home-iphone15-dark', wk, { ...devices['iPhone 15'], colorScheme: 'dark' }, ''],
    ['home-1440-days', c, { viewport: { width: 1440, height: 900 } }, '', 2400],
    ['prompts-1024', c, { viewport: { width: 1024, height: 900 } }, 'prompts/'],
    ['evaluator-1440-dark', c, { viewport: { width: 1440, height: 900 }, colorScheme: 'dark' }, `${review[0]}/${review[1]}/${review[2]}/evaluator/`],
    ['admin-1024', c, { viewport: { width: 1024, height: 900 } }, 'admin/'],
    ['404-390', c, { viewport: { width: 390, height: 844 } }, '404.html'],
  ];
  for (const [name, b, opts, rel, y] of pages) {
    const ctx = await b.newContext(opts); const rec = { fb: [], og: 0, ext: [], errors: [] }; await stub(ctx, rec);
    const p = await ctx.newPage(); await p.goto(BASE + rel); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(400);
    if (y) await p.evaluate((y) => scrollTo(0, y), y);
    await p.screenshot({ path: path.join(SHOTS, name + '.png') });
    await ctx.close();
    log(`shot ${path.join(SHOTS, name + '.png')}`);
  }
}

await c.close(); await wk.close(); server.close();
log(`\nRESULT: ${fails === 0 ? 'ALL PASS' : fails + ' failure(s)'}`);
process.exit(fails ? 1 : 0);
