// Browser checks for the built site (tools/verify/build.sh output), 2026-09-24 rewrite.
//
//   node tools/verify/suite.mjs [SITE_DIR]      default SITE_DIR=/tmp/fp-build/src/_site
//   ONLY=default,stale WIDTHS=390,1440 node ...  narrow a run; FAULTS=0 skips the self-test; VERBOSE=1 prints every detail
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
const STATES = ['default', 'expanded', 'unread-edition', 'front-read', 'all-read', 'all-partial', 'all-sync', 'beat', 'multi-beat', 'empty', 'stale', 'stale-bg'];
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
// the visible text of a period, formatted here: "24 Sep", "17–23 Sep", "29 Aug–4 Sep", "29 Dec 2025–4 Jan"
const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
function periodTexts(s, e) {
  const a = day(s), b = day(e), end = `${b.getUTCDate()} ${MON[b.getUTCMonth()]}`;
  if (s === e) return [end];
  if (a.getUTCFullYear() !== b.getUTCFullYear()) return [`${a.getUTCDate()} ${MON[a.getUTCMonth()]} ${a.getUTCFullYear()}`, end];
  return [a.getUTCMonth() === b.getUTCMonth() ? `${a.getUTCDate()}` : `${a.getUTCDate()} ${MON[a.getUTCMonth()]}`, end];
}
const EXPECT_TAGS = {};                              // date -> {stream: [start, end, [visible texts]]}
for (const d of dates) {
  EXPECT_TAGS[d] = {};
  for (const x of board.filter((x) => x.date === d)) { const [s0, e0] = period(d, x.stream); EXPECT_TAGS[d][x.stream] = [s0, e0, periodTexts(s0, e0)]; }
}
const sidOf = (x) => (x.kind === 'editorial' ? `ed-${x.stream}-${x.date}` : x.sid || x.id);
// the front: walk the newest dates until four leads/features; lead = first lead; then leads and
// features in board order, briefs only to fill
const stories = board.filter((x) => x.kind !== 'editorial');
const eds = board.filter((x) => x.kind === 'editorial');
function frontOf(skip = new Set()) {
  const pool = stories.filter((x) => !skip.has(sidOf(x)));
  let win = [];
  for (const d of [...new Set(pool.map((x) => x.date))].sort().reverse()) {
    win = win.concat(pool.filter((x) => x.date === d));
    if (win.filter((x) => x.importance >= 2).length >= 4) break;
  }
  const lead = win.find((x) => x.importance === 3) || win[0];
  const rest = win.filter((x) => x !== lead);
  return lead ? [lead, ...[...rest.filter((x) => x.importance >= 2), ...rest.filter((x) => x.importance < 2)].slice(0, 3)].map(sidOf) : [];
}
const EXPECT_FRONT = frontOf();
const deskEd = eds.length ? eds.reduce((a, b) => (b.date > a.date ? b : a)) : null;
const EXPECT_DESK = deskEd ? sidOf(deskEd) : null;
// the Unread refill: four rounds of the same selection over what the earlier rounds left, and
// every editorial newest first; the page shows the first four unread entries that match the
// beats, lead slot to the first importance-3 one
const RESERVE = [];
for (let r = 0; r < 4; r++) { const f = frontOf(new Set(RESERVE)); if (!f.length) break; RESERVE.push(...f); }
const DESK_RESERVE = eds.map((e, i) => [e, i]).sort((a, b) => b[0].date.localeCompare(a[0].date) || a[1] - b[1]).map(([e]) => sidOf(e));
const bySid = new Map(board.map((x) => [sidOf(x), x]));
// importance as the page reads it (a card's data-imp); the lead-rule scenario may set one below
const IMP = new Map(stories.map((x) => [sidOf(x), x.importance]));
// an editorial is read when marked, or when every story of its edition is (no local un-tick here);
// its beats are its edition's
const edition = (e) => stories.filter((x) => x.date === e.date && x.stream === e.stream);
function refillOf(read, beats = []) {
  const onBeat = (topics) => !beats.length || topics.some((t) => beats.includes(t));
  const pick = RESERVE.filter((sid) => !read.has(sid) && onBeat(bySid.get(sid).topics)).slice(0, 4);
  const lead = pick.find((sid) => IMP.get(sid) === 3) || pick[0];
  const edRead = (e) => read.has(sidOf(e)) || (edition(e).length > 0 && edition(e).every((x) => read.has(sidOf(x))));
  const desk = DESK_RESERVE.find((sid) => { const e = bySid.get(sid); return !edRead(e) && onBeat(edition(e).flatMap((x) => x.topics)); }) || null;
  return { cards: lead ? [lead, ...pick.filter((s) => s !== lead)] : [], desk };
}
// No front-read gate may pass or fail for want of data (review F4). Where the day's data lacks a
// scenario the suite makes one, the way frontWithSlots() makes image slots; SYNTH=1 forces the
// made-up ones on any data, so that path is exercised too. What cannot be made is reported as SKIP.
const SYNTH = !!process.env.SYNTH;
// the lead rule: the reserve's first non-importance-3 entry stays unread with a later
// importance-3 one, the rest of the reserve read. Made up: the last two reserve entries become
// importance 2 then 3 in the page (their cards' data-imp, set before the refill first runs).
const SYNTH_IMP = {};
let LEAD_X = SYNTH ? null : RESERVE.find((sid, i) => IMP.get(sid) !== 3 && RESERVE.slice(i + 1).some((s) => IMP.get(s) === 3)) || null;
let LEAD_Y = LEAD_X && RESERVE.slice(RESERVE.indexOf(LEAD_X) + 1).find((s) => IMP.get(s) === 3);
if (!LEAD_X && RESERVE.length >= 2) {
  [LEAD_X, LEAD_Y] = RESERVE.slice(-2);
  if (IMP.get(LEAD_X) === 3) SYNTH_IMP[LEAD_X] = 2;
  if (IMP.get(LEAD_Y) !== 3) SYNTH_IMP[LEAD_Y] = 3;
  for (const [sid, v] of Object.entries(SYNTH_IMP)) IMP.set(sid, v);
}
// front-read, in order: the default front and its Desk's view read (S0); a beat that changes the
// refill; a tick on the refilled lead (S1); a tick on a rest card while the last card holds focus
// (S1b); another tab reading one more while the reader types in that last card (S1c); the lead
// rule (S2), then its lead read so the other card changes slot (S2e); only the Desk's view left;
// the whole reserve read (S3)
const S0 = [...EXPECT_FRONT, EXPECT_DESK].filter(Boolean);
const REFILL0 = refillOf(new Set(S0));
const topicsAll = [...new Set(board.flatMap((x) => x.topics || []))].sort();
const beatRefill = (t) => refillOf(new Set(S0), [t]);
const differs = (t) => beatRefill(t).cards.join() !== REFILL0.cards.join();
// a beat that changes the refilled cards; made up: a beat no reserve story carries empties them
const REFILL_BEAT = (SYNTH ? topicsAll.find((t) => differs(t) && !beatRefill(t).cards.length) : null)
  || topicsAll.find((t) => differs(t) && beatRefill(t).cards.length) || topicsAll.find(differs) || null;
const S1 = [...S0, REFILL0.cards[0]].filter(Boolean);
const REFILL1 = refillOf(new Set(S1));
const FOCUS_L = REFILL1.cards.length >= 3 ? REFILL1.cards[REFILL1.cards.length - 1] : null;
const TICK_T = FOCUS_L ? REFILL1.cards[1] : null;
const S1b = TICK_T ? [...S1, TICK_T] : S1;
const REFILL1b = refillOf(new Set(S1b));
const TYPE_T = FOCUS_L && REFILL1b.cards.length >= 3 ? REFILL1b.cards.find((s, i) => i > 0 && s !== FOCUS_L) : null;
const S1c = TYPE_T ? [...S1b, TYPE_T] : S1b;
const S2 = LEAD_X ? [...RESERVE.filter((s) => s !== LEAD_X && s !== LEAD_Y), EXPECT_DESK].filter(Boolean) : [];
const S2e = LEAD_X ? [...S2, LEAD_Y] : [];
const S3 = [...RESERVE, ...DESK_RESERVE];
// All's front (owner decision 2026-09-25): the same pick, taken once at load from the read set the
// page opened with, beats aside; with nothing unread the builder's front; a Desk's view with no
// unread editorial keeps the builder's; a partly-read front is filled up to four with read stories
// in reserve order after the unread ones (owner ruling, round 5). The sync states: the first
// roamed read set marks the All front's second card read (All is taken once more, if the reader
// did nothing yet); a second roam marks its lead too, and nothing moves
function allOf(read) {
  const r = refillOf(read);
  if (!r.cards.length) return { cards: EXPECT_FRONT, desk: r.desk || EXPECT_DESK };
  const pad = RESERVE.filter((s) => read.has(s) && !r.cards.includes(s)).slice(0, 4 - r.cards.length);
  return { cards: [...r.cards, ...pad], desk: r.desk || EXPECT_DESK };
}
const ALL0 = allOf(new Set(S0));
const REMOTE1 = ALL0.cards.length >= 2 ? ALL0.cards[1] : null;
const REMOTE2 = REMOTE1 ? ALL0.cards[0] : null;
// all-partial: the reserve read except its last two entries, so All holds two unread stories
// and two read ones padding the front (normally the builder's own); its roam un-reads the first
// padded card
const S_P = RESERVE.length >= 4 ? RESERVE.slice(0, -2) : null;
const ALL_P = S_P ? allOf(new Set(S_P)) : null;
const PAD0 = ALL_P ? ALL_P.cards.find((c) => S_P.includes(c)) : null;
const ALL_PR = PAD0 ? allOf(new Set(S_P.filter((c) => c !== PAD0))) : null;
const FR = { FRONT: EXPECT_FRONT, DESK: EXPECT_DESK, RESERVE, DESK_RESERVE, SYNTH_IMP, S0, R0: REFILL0,
  RB: REFILL_BEAT, RBW: REFILL_BEAT ? beatRefill(REFILL_BEAT) : null, S1, R1: REFILL1,
  FOCUS_L, TICK_T, R1b: REFILL1b, TYPE_T, S1c, R1c: refillOf(new Set(S1c)),
  LEAD_X, LEAD_Y, S2, R2: LEAD_X ? refillOf(new Set(S2)) : null, S2e, R2e: LEAD_X ? refillOf(new Set(S2e)) : null,
  S3, NEWEST: dates[0], ALL0, ALL_READ: allOf(new Set(S3)), REMOTE1, REMOTE2, S_P, ALL_P, PAD0, ALL_PR,
  ALL_SYNC: REMOTE1 ? allOf(new Set([...S0, REMOTE1])) : null };
// the "Happened 16 Sep" label: only a valid day-precise event date before the story's derived
// period start; the year shows when it differs from the story's
const WD = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const dayLabel = (d) => `${WD[day(d).getUTCDay()]} ${day(d).getUTCDate()} ${MON[day(d).getUTCMonth()]}`;
const DAYLBL = Object.fromEntries(dates.map((d) => [d, dayLabel(d)]));
const PSTART = {}, EVT = {};
for (const x of stories) {
  const [s0] = period(x.date, x.stream); const ev = String(x.event_date || '').trim();
  PSTART[sidOf(x)] = s0;
  if (!/^\d{4}-\d\d-\d\d$/.test(ev) || isNaN(day(ev)) || iso(day(ev)) !== ev || ev >= s0) continue;
  const e = day(ev), y = ev.slice(0, 4) === x.date.slice(0, 4) ? '' : ' ' + ev.slice(0, 4);
  EVT[sidOf(x)] = [ev, `Happened ${e.getUTCDate()} ${MON[e.getUTCMonth()]}${y}`];
}
// the fault's label: a story whose event date falls inside its period (or, failing that, its own day)
const IN_PERIOD = stories.find((x) => /^\d{4}-\d\d-\d\d$/.test(String(x.event_date || '')) && x.event_date >= PSTART[sidOf(x)]) || stories[0];
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
// a JS fault: serve one module with strings replaced (each must exist, or the fault is vacuous)
async function mutateJs(ctx, js) {
  let body = fs.readFileSync(path.join(SITE, 'assets/js', js.file), 'utf8');
  for (const [from, to] of js.edits || [[js.from, js.to]]) {
    if (!body.includes(from)) throw new Error(`fault string not found in ${js.file}: ${from}`);
    body = body.replace(from, to);
  }
  await ctx.route((u) => u.pathname.endsWith('/assets/js/' + js.file), (route) => route.fulfill({ status: 200, contentType: 'text/javascript', body }));
}
// The og and open-card-photo gates must not depend on the day's data: a front whose stories are all
// arXiv/doi links has no image slot at all. For the default and expanded states the homepage is
// served with slots injected where the include would put them (after the headline, or the deck),
// so there are always >= 2 slots and the first openable card in the rest band always has one.
// Everything else is still the day's real markup.
let slotted = null;
function frontWithSlots() {
  if (slotted) return slotted;
  let html = fs.readFileSync(path.join(SITE, 'index.html'), 'utf8');
  const cards = [];                                         // [start, end] of each front card <li>
  const lead = html.indexOf('data-zone="front-lead"'), rest = html.indexOf('data-zone="front-rest"');
  for (const [from, band] of [[rest, 'rest'], [lead, 'lead']]) {
    if (from < 0) continue;
    const stop = html.indexOf('</ol>', from);
    for (let i = html.indexOf('<li class="fc ', from); i >= 0 && i < stop; i = html.indexOf('<li class="fc ', i + 1)) {
      cards.push({ band, start: i, end: html.indexOf('</li>', i) });
    }
  }
  const hasSlot = (c) => html.slice(c.start, c.end).includes('<figure class="photo');
  const openable = (c) => html.slice(c.start, c.end).includes('class="more');
  const want = [];
  const firstRest = cards.find((c) => c.band === 'rest' && openable(c));
  if (firstRest && !hasSlot(firstRest)) want.push(firstRest);
  let total = (html.match(/<figure class="photo[^>]*data-og=/g) || []).length + want.length;
  for (const c of cards) { if (total >= 2) break; if (!hasSlot(c) && !want.includes(c)) { want.push(c); total++; } }
  // insert from the end of the document backwards, so earlier offsets stay valid
  want.sort((a, b) => b.start - a.start).forEach((c, k) => {
    let at = html.indexOf('</h3>', c.start) + '</h3>'.length;
    const after = html.slice(at).match(/^\s*<p class="deck">[\s\S]*?<\/p>/);
    if (after) at += after[0].length;
    html = html.slice(0, at) + `\n    <figure class="photo needs-js" data-og="https://example.org/verify-slot-${k + 1}" aria-hidden="true"></figure>` + html.slice(at);
  });
  slotted = { html, injected: want.length, restCard: !!firstRest };
  return slotted;
}
async function serveFrontWithSlots(ctx) {
  const { html } = frontWithSlots();
  await ctx.route((u) => u.origin === ORIGIN && (u.pathname === '/claude-routines/' || u.pathname === '/claude-routines/index.html'),
    (route) => route.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: html }));
}
async function stub(ctx, rec, { stamp, ogAll } = {}) {
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
      body: JSON.stringify({ image: ogAll || ogN++ === 0 ? OG_IMG : null }) });
  });
  if (stamp) {
    await ctx.route((u) => u.pathname.endsWith('/edition.json'), (route) => route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ build_stamp: stamp, generated: feed.generated }) }));
  }
}
function watchRequests(page, rec) {
  page.on('request', (r) => {
    const u = new URL(r.url());
    if (u.origin === ORIGIN && u.pathname.endsWith('/edition.json')) rec.edition = (rec.edition || 0) + 1;
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
  // the front as shown: the lead band, every card in order, the Desk's view
  const front = () => ({ top: [...document.querySelectorAll('.front .fcards--top > .fc')].filter(vis).map((c) => c.dataset.story),
    cards: [...document.querySelectorAll('.front .fc')].filter(vis).map((c) => c.dataset.story),
    desk: ([...document.querySelectorAll('.front .desk .ed')].find(vis) || { dataset: {} }).dataset.story || null });
  const same = (g, w) => g.cards.join() === w.cards.join() && (g.top[0] || null) === (w.cards[0] || null) && g.top.length <= 1 && g.desk === w.desk;
  const show = (g, w) => `front [${g.cards.join(' ')}] lead ${g.top[0] || '-'} desk ${g.desk}; want [${w.cards.join(' ')}] desk ${w.desk}`;
  // every story and editorial is on the page once, as a real card or a real row; a pointer
  // reaches the front; a builder-front story off the front is its row again, right after its
  // (hidden) pointer; a day header counts what is on the front as composed
  const once = (boardIds, builderFront) => {
    const bad = [], cards = front().cards;
    for (const sid of boardIds) {
      const shown = [...document.querySelectorAll(`main [data-story="${sid}"]`)].filter(vis).length;
      if (shown !== 1) bad.push(`${sid} shown ${shown}x`);
    }
    for (const p of [...document.querySelectorAll('section.day [data-ptr]')].filter(vis)) {
      const t = document.getElementById(p.querySelector('a').getAttribute('href').slice(1));
      if (!t || !vis(t) || !t.closest('.front')) bad.push(`pointer ${p.dataset.ptr} -> ${t ? t.id : 'nothing'}`);
    }
    const off = builderFront.filter((s) => !cards.includes(s));
    for (const sid of off) {
      const r = document.getElementById('r-' + sid), prev = r && r.previousElementSibling;
      if (!r || !vis(r) || !prev || prev.dataset.ptr !== sid) bad.push(`${sid} is off the front without its row after its pointer`);
    }
    for (const sec of document.querySelectorAll('section.day')) {
      const n = sec.querySelector('.day__n').textContent, m = n.match(/· (\d+) on the front/);
      const up = [...sec.querySelectorAll('.rows > [data-ptr]')].filter(vis).length;
      if ((m ? +m[1] : 0) !== up) bad.push(`${sec.dataset.date} says "${n}" with ${up} on the front`);
    }
    return [bad.length === 0, bad.slice(0, 3).join('; ') || `${boardIds.length} board items each shown once, every pointer reaches the front, ${off.length} builder-front stories back in their days, day headers count the front`];
  };
  // signed in: release the n-th held GET /readstate and wait until its read set is merged
  const frames = () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  const merged = (sid) => !!(JSON.parse(localStorage.getItem('syncState:v1') || '{}')[sid]);
  const roam = async (i, sid) => {
    await window.__release(i);
    for (let t0 = Date.now(); !merged(sid) && Date.now() - t0 < 4000;) await new Promise((r) => setTimeout(r, 50));
    await frames();
    return merged(sid);
  };
  return { R, vis, visibleItems, chip, seg, ct, frontVoids, hlSizes, geometry, cpl, contrast, opacityOf, deadLinks, dayMeta, focusRing, front, same, show, once, frames, roam };
};

const frame2 = (page) => page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))));

// ------------------------------------------------------------------ one (engine, context, state) case
async function runCase(browser, ctxOpts, state, fault = null) {
  if (state === 'all-sync') return runSync(browser, ctxOpts, fault);
  const ctx = await browser.newContext(ctxOpts);
  const rec = { fb: [], og: 0, ext: [], errors: [] };
  await stub(ctx, rec, { stamp: state === 'stale' || state === 'stale-bg' ? 'a-newer-edition' : null, ogAll: state === 'expanded' });
  for (const js of fault?.js ? [].concat(fault.js) : []) await mutateJs(ctx, js);
  if (state === 'default' || state === 'expanded') await serveFrontWithSlots(ctx);
  const page = await ctx.newPage();
  watchRequests(page, rec);
  if (fault?.init) await page.addInitScript(fault.init);
  // front-read and the sync states: the default front's stories and the Desk's view editorial are
  // already read; all-read: the whole reserve and every editorial
  const seedRead = state === 'all-read' ? S3 : state === 'front-read' ? S0 : state === 'all-partial' ? S_P : null;
  if (seedRead) await page.addInitScript((ids) => localStorage.setItem('homeRead:v1', JSON.stringify(Object.fromEntries(ids.map((id) => [id, Date.now()])))), seedRead);
  // a made-up importance (SYNTH_IMP) goes on the cards when parsing ends, before the deferred
  // modules run: All's pick is taken at load, and the expectations were derived with it
  if (seedRead && Object.keys(SYNTH_IMP).length) {
    await page.addInitScript((imp) => document.addEventListener('readystatechange', () => {
      if (document.readyState !== 'interactive') return;
      for (const [sid, v] of Object.entries(imp)) {
        document.querySelectorAll(`.front li.fc[data-story="${sid}"]`).forEach((c) => { c.dataset.imp = String(v); });
        const t = document.querySelector(`template[data-reserve-card="${sid}"]`);
        if (t) t.content.firstElementChild.dataset.imp = String(v);
      }
      window.__synthImp = true;
    }), SYNTH_IMP);
  }
  if (state === 'stale-bg') {
    // a tab opened in the background: hidden from its first byte until the reader looks at it
    await page.addInitScript(() => {
      Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => window.__vis || 'hidden' });
      Object.defineProperty(document, 'hidden', { configurable: true, get: () => (window.__vis || 'hidden') === 'hidden' });
    });
  }
  await page.goto(BASE);
  await page.evaluate(() => document.fonts.ready);
  if (state === 'default' || state === 'expanded' || state === 'front-read') {
    // bring every image slot within the observer's reach, then wait until each is filled or gone
    // (each slot is scrolled to and held for two frames, so the IntersectionObserver sees it)
    await page.evaluate(async () => {
      const frames = () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
      for (const p of document.querySelectorAll('.photo[data-og]')) { p.scrollIntoView({ block: 'center' }); await frames(); await frames(); }
      scrollTo(0, 0); await frames();
    });
    await page.waitForFunction(() => [...document.querySelectorAll('.photo[data-og]')].every((p) => p.hidden || p.classList.contains('is-loaded')), null, { timeout: 8000 }).catch(() => {});
  }
  if (fault?.css) await page.addStyleTag({ content: fault.css });
  await page.evaluate(`window.__L = (${LIB.toString()})()`);
  const X = { state, ogRequests: rec.og, injected: frontWithSlots().injected, EXPECT_TAGS, EXPECT_FRONT, EXPECT_DESK, deskEdition, BEAT, BEAT_ED: BEAT_ED ? sidOf(BEAT_ED) : null, BEAT_DAYS,
    MEASURE_ROW: MEASURE_ROW ? sidOf(MEASURE_ROW) : null, boardIds: board.map(sidOf), boardDates: board.map((x) => x.date),
    boardKinds: board.map((x) => x.kind), nBoard: board.length, nDays: dates.length, FR, EVT, PSTART, DAYLBL };
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
          const [s, e, texts] = m[t.dataset.stream] || [];
          const got = ts.length === 1 ? [ts[0], ts[0]] : ts;
          if (got[0] !== s || got[1] !== e || !L.vis(t)) bad.push(`${d} ${t.dataset.stream}: ${got} (want ${s}..${e})`);
          const shown = [...t.querySelectorAll('time')].map((x) => x.textContent.trim());
          if (shown.join('|') !== (texts || []).join('|')) bad.push(`${d} ${t.dataset.stream} reads "${shown.join('–')}", want "${(texts || []).join('–')}"`);
        }
      }
      for (const ed of document.querySelectorAll('.ed')) {
        const [date, stream] = [ed.dataset.edition.slice(0, 10), ed.dataset.edition.slice(11)];
        const [s, e, texts] = X.EXPECT_TAGS[date][stream];
        const k = [...ed.querySelectorAll('.ed__kick time')].map((x) => x.getAttribute('datetime'));
        const got = k.length === 1 ? [k[0], k[0]] : k;
        if (got[0] !== s || got[1] !== e) bad.push(`${ed.id} kicker ${got}`);
        const shown = [...ed.querySelectorAll('.ed__kick time')].map((x) => x.textContent.trim());
        if (shown.join('|') !== texts.join('|')) bad.push(`${ed.id} kicker reads "${shown.join('–')}", want "${texts.join('–')}"`);
      }
      A.periods = [bad.length === 0 && nTags > 0, bad.join('; ') || `${nTags} day tags + ${document.querySelectorAll('.ed').length} editorial kickers match the derived periods, dates and visible text`];
      const frontIds = [...document.querySelectorAll('.front .fc')].map((x) => x.dataset.story);
      const desk = (document.querySelector('.front .desk .ed') || {}).id || null;
      A.front = [frontIds.join() === X.EXPECT_FRONT.join() && desk === X.EXPECT_DESK, `front ${frontIds.length} ${frontIds.join() === X.EXPECT_FRONT.join() ? '=' : '!='} derived; desk ${desk} (want ${X.EXPECT_DESK})`];
      // the Desk's view prints its edition's day, like a front card (an older editorial never reads as today's)
      const dk = document.querySelector('.front .desk .ed'), dkt = dk && dk.querySelector('.ed__top .fday');
      A.deskDate = !dk ? [null, 'no Desk\'s view'] : [!!dkt && L.vis(dkt) && dkt.getAttribute('datetime') === dk.dataset.edition.slice(0, 10) && dkt.textContent.trim() === X.DAYLBL[dk.dataset.edition.slice(0, 10)],
        `${dk.dataset.story}: ${dkt ? `"${dkt.textContent.trim()}" shown ${L.vis(dkt)}` : 'no day'}`];
      const lifted = [...document.querySelectorAll('.front [data-story]')].map((x) => x.dataset.story);
      const miss = lifted.filter((s) => !document.querySelector(`section.day [data-ptr="${s}"]`));
      A.pointers = [miss.length === 0, miss.length ? 'missing ' + miss : `${lifted.length} lifted items all keep a pointer in their day`];
      // every board item in its own day, in board order (items or pointers)
      const orderBad = [];
      const secs = [...document.querySelectorAll('section.day')];
      if (secs.length !== X.nDays) orderBad.push(`${secs.length} day sections, want ${X.nDays}`);
      for (const sec of secs) {
        const want = X.boardIds.filter((_, i) => X.boardDates[i] === sec.dataset.date);
        const got = [...sec.querySelectorAll('[data-story], [data-ptr]:not([data-reserve-ptr])')].map((x) => x.dataset.story || x.dataset.ptr);
        if (want.join() !== got.join()) orderBad.push(`${sec.dataset.date}: ${got.length} vs ${want.length} items or order differs`);
      }
      const rptr = [...document.querySelectorAll('[data-reserve-ptr]')].filter(L.vis).map((p) => p.dataset.ptr);
      if (rptr.length) orderBad.push(`reserve pointers shown under All: ${rptr.join(' ')}`);
      A.boardOrder = [orderBad.length === 0, orderBad.join('; ') || `${secs.length} day sections carry the board in order, no reserve pointer shown`];
      // "Happened 16 Sep": on a card, row or reserve template exactly when the story's event date
      // is day-precise and before its derived period start, reading that date, inside its card
      const evBad = []; let evShown = 0, evTpl = 0;
      const evCheck = (el, where) => {
        const sid = el.dataset.story, t = el.querySelector('.evt time'), want = X.EVT[sid];
        if (!t) { if (want) evBad.push(`${where} ${sid} lacks "${want[1]}"`); return; }
        const dt = t.getAttribute('datetime'), txt = t.textContent.trim();
        if (!(dt < X.PSTART[sid])) evBad.push(`${where} ${sid} "${txt}" dated ${dt}, on or after its period start ${X.PSTART[sid]}`);
        else if (!want || dt !== want[0] || txt !== want[1]) evBad.push(`${where} ${sid} "${txt}" @${dt}, want ${want ? `"${want[1]}" @${want[0]}` : 'none'}`);
        if (where === 'template') { evTpl++; return; }
        evShown++;
        const r = L.R(t.closest('.evt')), c = L.R(el);
        if (L.vis(el) && (r.right > c.right + 0.5 || r.left < c.left - 0.5)) evBad.push(`${sid} label sticks out of its ${where} by ${Math.round(r.right - c.right)}px`);
      };
      for (const el of document.querySelectorAll('main [data-story]:not([data-zone="editorial"])')) evCheck(el, el.dataset.zone);
      for (const t of document.querySelectorAll('template[data-reserve-card]')) evCheck(t.content.firstElementChild, 'template');
      const evMiss = evBad.filter((b) => b.includes(' lacks '));
      A.eventLabel = [evBad.length === evMiss.length, evBad.filter((b) => !evMiss.includes(b)).slice(0, 3).join('; ') || `${evShown} labels on cards and rows + ${evTpl} in reserve templates, each on a qualifying story, before its period start, inside its card`];
      // every story that qualifies shows one; with none qualifying there is nothing to show (review F4)
      A.eventLabelShown = Object.keys(X.EVT).length ? [evMiss.length === 0, evMiss.slice(0, 3).join('; ') || `all ${Object.keys(X.EVT).length} qualifying stories show their label`]
        : [null, 'no story has a day-precise event date before its period'];
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
      // og: at least two slots (the suite injects slots when the day's front has fewer); the stub
      // gives the first an image and the rest none. Both outcomes must land every run, and the
      // image request must carry its referrer policy (old bug B6).
      const slots = [...document.querySelectorAll('.photo[data-og]')];
      const filled = slots.filter((p) => p.classList.contains('is-loaded')), gone = slots.filter((p) => p.hidden);
      const img = filled[0] && filled[0].querySelector('img');
      const ogDetail = `${slots.length} slots (${X.injected} injected), ${X.ogRequests} og-proxy calls, filled ${filled.length}, collapsed ${gone.length}` + (img ? `, referrerPolicy "${img.referrerPolicy}", loading "${img.loading}"` : '');
      A.og = [slots.length >= 2 && X.ogRequests >= 2 && filled.length >= 1 && gone.length >= 1 && filled.length + gone.length === slots.length
        && !!img && img.referrerPolicy === 'no-referrer' && img.loading === 'lazy', ogDetail];
      // freshness, negative control: an unchanged edition never offers a reload
      const bar = document.querySelector('.notice');
      window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }));
      await sleep(300);
      const afterRestore = L.vis(bar);
      const now0 = Date.now;
      Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'hidden' });
      document.dispatchEvent(new Event('visibilitychange'));
      Date.now = () => now0() + 60 * 1000;                          // one minute away: no check at all
      Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'visible' });
      document.dispatchEvent(new Event('visibilitychange'));
      await sleep(150);
      const afterMinute = L.vis(bar);
      Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'hidden' });
      document.dispatchEvent(new Event('visibilitychange'));
      Date.now = () => now0() + 12 * 60 * 1000;                     // twelve minutes: checks, same stamp
      Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'visible' });
      document.dispatchEvent(new Event('visibilitychange'));
      await sleep(300);
      Date.now = now0;
      A.freshSame = [!afterRestore && !afterMinute && !L.vis(bar), `unchanged edition: no bar after a bfcache restore (${!afterRestore}), after 1 min away (${!afterMinute}), after 12 min away (${!L.vis(bar)})`];
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
      // an open card with a photo: from a 720px front its photo sits in a column beside the
      // headline; below that the card is one column and the photo sits under the headline. The
      // first openable rest card always has a slot (injected if the day's data gives it none).
      const grid = document.querySelector('.front__grid');
      const withPhoto = [...document.querySelectorAll('.fcards--rest .fc')].find((c) => c.querySelector('.photo.is-loaded') && c.querySelector('.more'));
      if (!grid || !withPhoto) A.photoBeside = [false, `no loaded photo on an openable front card (${X.injected} slots injected): the check has nothing to measure`];
      else {
        const wide = L.R(grid).width >= 720;
        const was = isOpen(withPhoto);
        setOpen(withPhoto, true);
        const h = L.R(withPhoto.querySelector('.hl')), ph = L.R(withPhoto.querySelector('.photo'));
        const beside = ph.left >= h.right - 1 && ph.top < h.bottom && ph.bottom > h.top;
        const under = ph.top >= h.bottom - 1 && Math.abs(ph.left - h.left) < 2;
        A.photoBeside = [wide ? beside : under, `front ${Math.round(L.R(grid).width)}px, open card: headline x ${Math.round(h.left)}–${Math.round(h.right)} y ${Math.round(h.top)}–${Math.round(h.bottom)}, photo x ${Math.round(ph.left)}–${Math.round(ph.right)} y ${Math.round(ph.top)}–${Math.round(ph.bottom)} (${beside ? 'beside' : under ? 'under' : 'misplaced'}, want ${wide ? 'beside' : 'under'})`];
        setOpen(withPhoto, was);
      }
    }
    if (X.state === 'unread-edition') {
      const u0 = L.ct(L.seg('unread'));
      const sci = [...document.querySelectorAll(`[data-story][data-edition="${X.deskEdition}"]`)].filter((x) => x.dataset.zone !== 'editorial');
      const ed = document.getElementById(X.EXPECT_DESK);
      // one story of the edition read: the editorial stays unread, and Unread drops by exactly one
      click(sci[0].querySelector('.readbtn'));
      const partial = sci.length < 2 || (!ed.classList.contains('is-read') && ed.querySelector('.readbtn').getAttribute('aria-pressed') === 'false' && L.ct(L.seg('unread')) === u0 - 1);
      sci.slice(1).forEach((s) => click(s.querySelector('.readbtn')));
      const u1 = L.ct(L.seg('unread'));
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
      A.edRead = [partial && u0 - u1 === sci.length + 1 && derived, `1 of ${sci.length} ticked leaves the editorial unread: ${partial}; all ${sci.length} ticked: Unread ${u0} -> ${u1} (editorial counted once: ${u0 - u1 === sci.length + 1}), derived read ${derived}`];
      A.override = [untick && stored, `explicit un-tick wins over the edition rule: ${untick}, kept locally ${stored}`];
      A.counts = [n === u2 && !L.vis(ed), `Unread chip ${u2} vs visible ${n}; the edition's editorial hidden ${!L.vis(ed)}`];
      const emptyDays = [...document.querySelectorAll('section.day')].filter((s) => !s.hidden && !s.querySelector('[data-story]:not([hidden]),[data-ptr]:not([hidden])'));
      A.dayHide = [emptyDays.length === 0, `${emptyDays.length} shown day editions with zero visible rows`];
      const sync = JSON.parse(localStorage.getItem('syncState:v1') || '{}');
      A.localEd = [!Object.keys(sync).some((k) => !/^st-[0-9a-f]{12}$/.test(k)), `syncState:v1 holds ${Object.keys(sync).length} st- ids and no ed- id`];
    }
    if (['front-read', 'all-read', 'all-partial'].includes(X.state)) {
      // the page opened under All with a seeded read set: the default front and its Desk's view
      // (front-read), the whole reserve and every editorial (all-read), or the reserve but its last
      // two entries (all-partial)
      const F = X.FR;
      const frames = () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
      const doc = (e) => { const r = L.R(e); return [r.left + scrollX, r.top + scrollY, r.width, r.height].map(Math.round).join(); };
      const layout = () => Object.fromEntries([...document.querySelectorAll('main [data-story], main [data-ptr]')].filter(L.vis)
        .map((e) => [e.id || `${e.dataset.zone}>${e.dataset.ptr}`, doc(e)]));
      const { front: now, same, show } = L;
      // a held beat chip counts what shows; the All chip counts every beat
      const counts = (beat = '') => { const n = L.visibleItems().length, u = L.ct(L.seg('unread')), c = L.ct(L.chip(beat)); return [n === u && n === c, `visible ${n} / Unread ${u} / ${beat || 'All'} chip ${c}`]; };
      const shownPtrs = () => [...document.querySelectorAll('[data-reserve-ptr]')].filter(L.vis).map((p) => p.dataset.ptr);
      // a promoted story is a pointer in its day, and the pointer reaches the card; nothing else points
      const ptrs = (w) => {
        const bad = [];
        const promoted = [...w.cards.filter((s) => !F.FRONT.includes(s)), ...(w.desk && w.desk !== F.DESK ? [w.desk] : [])];
        for (const sid of promoted) {
          const own = document.querySelector(`section.day [data-story="${sid}"]`), p = document.querySelector(`section.day [data-ptr="${sid}"]`);
          if (own && L.vis(own)) bad.push(`${sid} still shown in its day`);
          const t = p && document.getElementById(p.querySelector('a').getAttribute('href').slice(1));
          if (!p || !L.vis(p)) bad.push(`${sid} has no pointer`);
          else if (!t || !L.vis(t) || !t.closest('.front') || t.dataset.story !== sid) bad.push(`${sid} pointer -> ${t ? t.id : 'nothing'}`);
        }
        const stray = shownPtrs().filter((s) => !promoted.includes(s));
        if (stray.length) bad.push('pointers for stories not on the front: ' + stray.join(' '));
        return [bad.length === 0, bad.slice(0, 3).join('; ') || `${promoted.length} promoted, each a pointer in its day`];
      };
      const line = (w, u = 'unread ') => {
        const n = w.cards.length;
        const older = [...new Set(w.cards.map((s) => X.boardDates[X.boardIds.indexOf(s)]))]
          .filter((d) => d !== F.NEWEST).sort().reverse().map((d) => X.DAYLBL[d]);
        return (n === 1 ? `The ${u}story that matters` : `The ${n} ${u}stories that matter`) + ' most right now' + (older.length ? ' · from ' + older.join(', ') : '');
      };
      const frontN = document.querySelector('.front__n'), line0 = frontN.textContent;
      const settle = async () => {
        for (let k = 0; k < 20 && document.querySelector('.front .photo[data-og]:not([hidden]):not(.is-loaded)'); k++) {
          for (const p of document.querySelectorAll('.front .photo[data-og]:not([hidden]):not(.is-loaded)')) { p.scrollIntoView({ block: 'center' }); await frames(); }
          await sleep(100);
        }
        scrollTo(0, 0); await frames();
      };
      const SKIP = (why) => [null, why];
      const until = async (fn, ms = 4000) => { const t0 = Date.now(); while (!fn() && Date.now() - t0 < ms) await sleep(50); return fn(); };
      const once = () => L.once(X.boardIds, F.FRONT);
      // the Desk's view prints its edition's day, like a front card
      const deskDate = () => {
        const ed = [...document.querySelectorAll('.front .desk .ed')].find(L.vis);
        if (!ed) return [false, 'no Desk\'s view shown'];
        const t = ed.querySelector('.ed__top .fday'), d = ed.dataset.edition.slice(0, 10);
        return [!!t && L.vis(t) && t.getAttribute('datetime') === d && t.textContent.trim() === X.DAYLBL[d],
          `${ed.dataset.story}: ${t ? `"${t.textContent.trim()}" @${t.getAttribute('datetime')} shown ${L.vis(t)}` : 'no day'}, edition ${d}`];
      };
      // a story is dimmed exactly when it is read (All shows read and unread alike)
      const dimHonest = () => {
        const read = JSON.parse(localStorage.getItem('homeRead:v1') || '{}');
        const bad = [...document.querySelectorAll('main [data-story]:not([data-zone="editorial"])')].filter(L.vis)
          .filter((e) => e.classList.contains('is-read') !== !!read[e.dataset.story]).map((e) => e.dataset.story);
        return [bad.length === 0, bad.length ? 'dimmed wrong: ' + bad.slice(0, 3).join(' ') : 'every shown story dimmed exactly when read'];
      };
      const ctlOf = (sid) => { const c = document.querySelector(`.front .fc[data-story="${sid}"]`); return c && (c.querySelector('.more') || c.querySelector('.readbtn')); };
      if (X.state === 'all-partial') {
        // a partly-read All: the unread first (the lead one of them), then read ones in reserve
        // order up to four, dimmed; every story once, day headers counting the front
        if (!F.ALL_P) { A.allPartial = SKIP('a reserve of fewer than four entries'); A.allPartialLead = SKIP('a reserve of fewer than four entries'); }
        else {
          const g = now(), read = JSON.parse(localStorage.getItem('homeRead:v1') || '{}'), o = once();
          const els = g.cards.map((c) => document.querySelector(`.front .fc[data-story="${c}"]`));
          const dimOk = els.every((e) => e && e.classList.contains('is-read') === !!read[e.dataset.story]);
          const nUnread = g.cards.filter((c) => !read[c]).length;
          A.allPartial = [same(g, F.ALL_P) && g.cards.length === F.ALL_P.cards.length && dimOk && o[0],
            `${show(g, F.ALL_P)}; ${nUnread} unread then ${g.cards.length - nUnread} read, dimmed exactly when read ${dimOk}; ${o[1]}`];
          const lead = els[0], firstRead = g.cards.findIndex((c) => read[c]);
          const unreadFirst = firstRead < 0 || g.cards.slice(firstRead).every((c) => read[c]);
          A.allPartialLead = [!!lead && !lead.classList.contains('is-read') && nUnread > 0 && unreadFirst,
            `lead ${lead ? lead.dataset.story : '-'} ${lead && lead.classList.contains('is-read') ? 'READ' : 'unread'}; the ${nUnread} unread before every read card ${unreadFirst}`];
        }
        A.allOnce = once();
      }
      if (X.state === 'all-read') {
        // everything read: All is the builder's front, dimmed, never empty
        const g = now(), fr = document.querySelector('section.front');
        const dim = [...F.FRONT, F.DESK].filter(Boolean).every((s) => { const e = document.querySelector(`.front [data-story="${s}"]`); return e && e.classList.contains('is-read'); });
        const rows = F.FRONT.filter((s) => { const r = document.getElementById('r-' + s); return r && L.vis(r); });
        A.allAllRead = [same(g, F.ALL_READ) && L.vis(fr) && dim && !rows.length && L.vis(frontN) && frontN.textContent === line(F.ALL_READ, ''),
          `${show(g, F.ALL_READ)}; front shown ${L.vis(fr)}; dimmed ${dim}; builder-front rows in their days ${rows.length}; line "${frontN.textContent}"`];
        A.allOnce = once();
        A.deskDate = deskDate();
      }
      if (X.state === 'front-read') {
        const lay0 = layout();
        // All at load (owner decision 2026-09-25): the Unread pick from the read set the page opened with
        const gl = now();
        A.allLoad = [same(gl, F.ALL0) && ptrs(F.ALL0)[0] && frontN.textContent === line(F.ALL0, ''), `${show(gl, F.ALL0)}; ${ptrs(F.ALL0)[1]}; line "${frontN.textContent}"`];
        A.allOnce = once();
        A.deskDate = deskDate();
        // a tick under All only dims: nothing moves or hides; its un-tick puts the read set back
        const tl = document.querySelector('.front .fcards--top > .fc');
        if (tl) {
          click(tl.querySelector('.readbtn')); await frames();
          const lt = layout(), dimT = tl.classList.contains('is-read'), gt = now();
          click(tl.querySelector('.readbtn')); await frames();
          const movedT = Object.keys(lay0).filter((k) => lay0[k] !== lt[k]);
          A.allTickDims = [dimT && !movedT.length && same(gt, F.ALL0), `${tl.dataset.story} ticked under All: dimmed ${dimT}; ${movedT.length} of ${Object.keys(lay0).length} moved ${movedT.slice(0, 3).join(' ')}; ${show(gt, F.ALL0)}`];
        } else A.allTickDims = SKIP('no card on All\'s front');
        // Read is the builder's front, as before; back under All nothing has moved
        click(L.seg('read')); await frames();
        const gr = now(), rowsR = F.FRONT.filter((s) => { const r = document.getElementById('r-' + s); return r && L.vis(r); });
        click(L.seg('')); await frames();
        const movedR = Object.entries(layout()).filter(([k, v]) => lay0[k] !== v).map(([k]) => k);
        A.allReadView = [same(gr, { cards: F.FRONT, desk: F.DESK }) && !rowsR.length && !movedR.length,
          `Read: ${show(gr, { cards: F.FRONT, desk: F.DESK })}; builder-front rows shown ${rowsR.length}; back to All ${movedR.length} moved ${movedR.slice(0, 3).join(' ')}`];
        const write = async (list, key = 'homeRead:v1') => {
          localStorage.setItem(key, JSON.stringify(Object.fromEntries(list.map((id) => [id, Date.now()]))));
          dispatchEvent(new StorageEvent('storage', { key, storageArea: localStorage }));
          await frames();
        };
        // Focus must survive a recompose (review F1): the focused control keeps the focus (and its
        // caret), and its card is never taken out of the document on the way (a card moved out and
        // back drops the focus to <body>; the board's rescue would hide that, so removals are watched)
        const keeps = async (ctl, act) => {
          if (!ctl) return [false, 'the card to hold the focus is not on the front'];
          const card = ctl.closest('[data-story]'), removed = [];
          const note = (recs) => { for (const r of recs) for (const n of r.removedNodes) if (n === card || n.contains(card)) removed.push(n); };
          const mo = new MutationObserver(note);
          mo.observe(document.getElementById('main'), { childList: true, subtree: true });
          ctl.focus();
          const sel = typeof ctl.selectionStart === 'number' ? [ctl.selectionStart, ctl.selectionEnd, ctl.value] : null;
          await act();
          note(mo.takeRecords()); mo.disconnect();
          const a = document.activeElement, selOk = !sel || (a === ctl && ctl.selectionStart === sel[0] && ctl.selectionEnd === sel[1] && ctl.value === sel[2]);
          const where = (e) => (e ? (e.className || e.tagName).toString().split(' ')[0] + (e.closest && e.closest('[data-story]') ? ' in ' + e.closest('[data-story]').dataset.story : '') : 'none');
          return [a === ctl && !removed.length && card.isConnected && selOk,
            `focus on ${where(ctl)}: after ${where(a)}; card taken out ${removed.length}x${sel ? `; caret ${sel[0]}-${sel[1]} -> ${ctl.selectionStart}-${ctl.selectionEnd}` : ''}`];
        };
        // 1. Unread: the first four unread reserve entries, lead first; the next unread editorial
        click(L.seg('unread')); await settle();
        const g0 = now();
        A.refill = [same(g0, F.R0), show(g0, F.R0)];
        A.refillPtrs = ptrs(F.R0);
        A.counts = counts();
        A.refillLine = [frontN.textContent === line(F.R0), `"${frontN.textContent}"`];
        const ids = [...document.querySelectorAll('[id]')].map((e) => e.id), dup = ids.filter((x, i) => ids.indexOf(x) !== i);
        A.refillIds = [dup.length === 0, dup.length ? 'duplicate ids ' + dup.slice(0, 4).join(' ') : `${ids.length} ids, none twice`];
        const fb = []; let nf = 0;
        for (const sid of F.R0.cards.filter((s) => !F.FRONT.includes(s))) {
          const c = document.getElementById('c-' + sid);
          if (!c || !c.classList.contains('is-folded')) { fb.push(`${sid} not folded`); continue; }
          const b = c.querySelector('.more'); if (!b) continue;
          const f = document.getElementById(b.getAttribute('aria-controls')); nf++;
          click(b); const opened = !c.classList.contains('is-folded') && b.getAttribute('aria-expanded') === 'true' && !!f && c.contains(f) && L.vis(f);
          click(b); const closed = c.classList.contains('is-folded') && b.getAttribute('aria-expanded') === 'false';
          if (!opened || !closed) fb.push(`${sid} More opens its own fold ${opened}, closes ${closed}`);
        }
        A.refillFold = fb.length ? [false, fb.join('; ')] : nf ? [true, `promoted cards start folded; More opens and closes the own fold of ${nf}`]
          : SKIP('no promoted card has a More to open');
        const g = L.geometry(), dead = L.deadLinks(), dm = L.dayMeta();
        A.refillGeom = [!g.overlap.length && !g.order.length && !g.containment.length && !g.overflow.length,
          `refilled: ${g.overlap.length} overlaps / ${g.pairs} pairs, ${g.order.length} inversions, ${g.containment.length} outside, overflow ${g.overflow.length} ${[...g.overlap, ...g.order].slice(0, 2).join('; ')}`];
        A.refillLinks = [!dead.length && !dm.bad.length, `refilled: ${dead.length} dead links ${dead.slice(0, 2).join('; ')}; day headers ${dm.bad.join('; ') || 'match'}`];
        // a promoted editorial: its day's "→ desk's view" link stays and reaches the front copy (review F3)
        if (F.R0.desk && F.R0.desk !== F.DESK) {
          const links = [...document.querySelectorAll('section.day .day__links a.jump')].filter((a) => a.getAttribute('href').replace('#desk-', '#') === '#' + F.R0.desk);
          const a = links[0], t = a && document.getElementById(a.getAttribute('href').slice(1));
          A.refillDayLink = [links.length === 1 && L.vis(a) && !!t && L.vis(t) && !!t.closest('.front') && t.dataset.story === F.R0.desk,
            `${F.R0.desk}: day link ${a ? `${a.getAttribute('href')} shown ${L.vis(a)}` : 'missing'} -> ${t ? `${t.id} shown ${L.vis(t)} on the front ${!!t.closest('.front')}` : 'nothing'}`];
        } else A.refillDayLink = SKIP('no older editorial to promote to the Desk\'s view');
        // (a) nothing changes: a middle-click reads a card without a recompose, its ✓ un-reads it
        const cA = F.R0.cards[F.R0.cards.length - 1], hlA = cA && document.querySelector(`.front .fc[data-story="${cA}"] .hl a`);
        if (hlA) {
          hlA.dispatchEvent(new MouseEvent('auxclick', { button: 1, bubbles: true, cancelable: true }));
          const rbA = hlA.closest('.fc').querySelector('.readbtn'), readA = hlA.closest('.fc').classList.contains('is-read');
          const k = await keeps(rbA, async () => { click(rbA); await frames(); });
          A.refillFocusSame = [readA && k[0] && same(now(), F.R0), `${cA} read by a middle-click ${readA}, then un-ticked: ${k[1]}`];
        } else A.refillFocusSame = SKIP('no refilled card');
        // 2. a beat changes the refill; releasing it restores it
        if (F.RB) {
          click(L.chip(F.RB)); const gb = now(), cb = counts(F.RB); click(L.chip(F.RB));
          A.refillBeat = [same(gb, F.RBW) && cb[0] && same(now(), F.R0), `${F.RB}: ${show(gb, F.RBW)}; ${cb[1]}`];
        } else A.refillBeat = SKIP('no beat on the board changes the refill');
        // 3. tick the refilled lead: the next entry takes its place, its pointer goes with it
        const u0 = L.ct(L.seg('unread'));
        const lead = document.querySelector('.front .fcards--top > .fc');
        click(lead && lead.querySelector('.readbtn'));
        const g1 = now(), p1 = ptrs(F.R1), c1 = counts();
        A.refillTick = [same(g1, F.R1) && p1[0] && c1[0] && L.ct(L.seg('unread')) === u0 - 1,
          `after ticking ${F.R0.cards[0]}: ${show(g1, F.R1)}; ${p1[1]}; ${c1[1]}; Unread ${u0} -> ${L.ct(L.seg('unread'))}`];
        // (b) the pick changes around a staying card: the last card holds the focus while a rest card is ticked
        if (F.FOCUS_L) {
          const k = await keeps(ctlOf(F.FOCUS_L), async () => { click(document.querySelector(`.front .fc[data-story="${F.TICK_T}"] .readbtn`)); await frames(); });
          A.refillFocusAround = [k[0] && same(now(), F.R1b), `${F.TICK_T} ticked: ${show(now(), F.R1b)}; ${k[1]}`];
        } else A.refillFocusAround = SKIP('fewer than three refilled cards');
        // (c) another tab reads one more while the reader types in the last card's reason box
        const cardL = F.TYPE_T && document.querySelector(`.front .fc[data-story="${F.FOCUS_L}"]`);
        if (cardL) {
          click(cardL.querySelector('.vote--down'));
          const dlg = document.querySelector('dialog[open]'); if (dlg) dlg.close();
          const inp = cardL.querySelector('.rzn input');
          if (inp) { inp.value = 'not new'; inp.setSelectionRange(1, 5); }
          const k = await keeps(inp, () => write(F.S1c));
          A.refillFocusTyping = [k[0] && same(now(), F.R1c), `another tab read ${F.TYPE_T}: ${show(now(), F.R1c)}; ${k[1]}`];
        } else A.refillFocusTyping = SKIP('fewer than three refilled cards after a tick');
        // 4. All: its LOAD-TIME front (not a pick from the reads since), the reads dimmed, and
        // nothing on the page has moved since load
        click(L.seg('')); await frames();
        const ga = now(), lay1 = layout(), dh = dimHonest();
        const moved = [...new Set([...Object.keys(lay0), ...Object.keys(lay1)])].filter((k) => lay0[k] !== lay1[k]);
        const hiddenLinks = [...document.querySelectorAll('.day__links a')].filter((a) => !L.vis(a)).length;
        A.refillAll = [same(ga, F.ALL0) && dh[0] && moved.length === 0 && frontN.textContent === line0 && !hiddenLinks && once()[0],
          `${show(ga, F.ALL0)}; ${dh[1]}; ${moved.length} of ${Object.keys(lay0).length} moved ${moved.slice(0, 3).join(' ')}; line ${frontN.textContent === line0 ? 'restored' : `"${frontN.textContent}"`}; day links hidden ${hiddenLinks}; ${once()[1]}`];
        // (d) under All an apply with nothing to change (a roamed selection does the same) moves nothing
        const ctlD = ctlOf(F.ALL0.cards[F.ALL0.cards.length - 1]);
        if (ctlD) {
          const k = await keeps(ctlD, async () => { click(L.seg('')); await frames(); });
          A.refillFocusAll = k;
        } else A.refillFocusAll = SKIP('no front card');
        // 5. under Unread, another tab leaves only a non-lead entry and a later lead unread: the lead slot takes the lead
        click(L.seg('unread'));
        if (F.LEAD_X) {
          await write(F.S2);
          const g2 = now();
          A.refillLead = [same(g2, F.R2) && frontN.textContent === line(F.R2) && counts()[0], `${show(g2, F.R2)}; "${frontN.textContent}"${Object.keys(F.SYNTH_IMP).length ? ' (made-up importance)' : ''}`];
          // (e) then its lead is read: the other card moves to the lead slot and keeps the focus
          const k = await keeps(ctlOf(F.LEAD_X), () => write(F.S2e));
          const moveOk = document.activeElement === ctlOf(F.LEAD_X) && same(now(), F.R2e);
          A.refillFocusMove = [moveOk, `${F.LEAD_Y} read: ${show(now(), F.R2e)}; ${k[1]}`];
        } else { A.refillLead = SKIP('a reserve of fewer than two entries'); A.refillFocusMove = SKIP('a reserve of fewer than two entries'); }
        // only the Desk's view left: no story count to state (review F2)
        if (F.DESK_RESERVE.length) {
          await write([F.DESK_RESERVE[0]], 'homeUnread:v1'); await write(F.RESERVE);
          const gd = now(), fr = document.querySelector('section.front');
          A.frontLineDesk = [!gd.cards.length && gd.desk === F.DESK_RESERVE[0] && L.vis(fr) && !L.vis(frontN),
            `${show(gd, { cards: [], desk: F.DESK_RESERVE[0] })}; front shown ${L.vis(fr)}; line ${L.vis(frontN) ? `"${frontN.textContent}"` : 'hidden'}`];
        } else A.frontLineDesk = SKIP('no editorial');
        // 6. the whole reserve read: the front hides, and nothing points into it
        await write(F.S3);
        const fr = document.querySelector('section.front'), c3 = counts(), d3 = L.deadLinks();
        A.refillEmpty = [!L.vis(fr) && !shownPtrs().length && c3[0] && !d3.length, `front shown ${L.vis(fr)}; reserve pointers shown ${shownPtrs().length}; ${c3[1]}; dead links ${d3.length}`];
      }
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
    if (X.state === 'stale-bg') {
      const bar = document.querySelector('.notice');
      const before = L.vis(bar);
      const now = Date.now; Date.now = () => now() + 5 * 3600 * 1000;       // first looked at five hours later
      window.__vis = 'visible';
      document.dispatchEvent(new Event('visibilitychange'));
      await sleep(300);
      Date.now = now;
      A.freshBg = [!before && L.vis(bar), `tab opened in the background, shown 5 h later: bar hidden before ${!before}, New edition bar after ${L.vis(bar)}`];
    }
    const dead = L.deadLinks(); A.links = [dead.length === 0, dead.length ? dead.join('; ') : 'every visible in-page link has a rendered target'];
    const dm = L.dayMeta(); A.dayMeta = [dm.bad.length === 0, `${dm.days} day headers ${dm.bad.join('; ') || 'match what they show'}`];
    return A;
  }, X);
  const KEY = browser.browserType().name() === 'webkit' ? 'Alt+Tab' : 'Tab';
  if (state === 'default' && !fault?.noFocus) {
    const reachable = await page.evaluate(() => [...document.querySelectorAll('.mast :is(a[href], button, summary, input), .bar :is(a[href], button, summary, input)')]
      .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && !e.closest('[hidden]'); }).length);
    // start the walk at the skip link, the page's first stop, whatever moved the navigation point
    await page.evaluate(() => { scrollTo(0, 0); document.querySelector('.skip').focus(); });
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
    // every visible masthead and bar control is reached by Tab, and every ring is whole
    const bad = seen.filter((f) => f.bad.length);
    fn.focus = [bad.length === 0 && reachable >= 8 && seen.length === reachable,
      `${seen.length} of ${reachable} chrome controls tabbed${bad.length ? ': ' + bad.slice(0, 3).map((f) => f.label + ' ' + f.bad.join(',')).join(' | ') : ', every ring whole'}`];
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

// ------------------------------------------------------------------ signed in: the first roamed read set
// All's pick is taken at load from the local read set; the FIRST roamed set takes it once more,
// only if the reader has not interacted with the page since load (owner ruling 2026-09-25). One
// context per case and a fresh page per scenario, each seeded with the default front and its
// Desk's view read and a session. The n-th GET /readstate waits until the page calls
// __release(n). A scenario that must start scrolled to an element reloads the page and puts it
// there at load: after a reload the page counts scrolls as the reader's only from two frames after
// load (the browser restores a position by then), so that one is not the reader's.
const ENTER = FR.ALL_SYNC ? FR.ALL_SYNC.cards.find((s) => !ALL0.cards.includes(s)) || null : null;   // enters the front at the roam
const OFF = EXPECT_FRONT.find((s) => !ALL0.cards.includes(s)) || null;                              // a builder-front story All leaves off
async function runSync(browser, ctxOpts, fault = null) {
  const ctx = await browser.newContext(ctxOpts);
  const rec = { fb: [], og: 0, ext: [], errors: [] };
  await stub(ctx, rec);
  for (const js of fault?.js ? [].concat(fault.js) : []) await mutateJs(ctx, js);
  const gates = [];
  const gate = (i) => (gates[i] ||= (() => { let open; const p = new Promise((r) => { open = r; }); return { p, open }; })());
  let pulls = 0, remote = () => ({});
  await ctx.exposeFunction('__release', (i) => { gate(i).open(); });
  await ctx.route((u) => u.origin === FB && u.pathname === '/readstate', async (route) => {
    const r = route.request();
    rec.fb.push({ method: r.method(), path: '/readstate', auth: (r.headers().authorization || '').replace(TOKEN, '<token>') });
    const json = { ok: true };
    if (r.method() === 'GET') { const i = pulls++, state = remote(i); await gate(i).p; json.state = state; }
    try {
      await route.fulfill({ status: 200, contentType: 'application/json', headers: { 'access-control-allow-origin': '*' }, body: JSON.stringify(json) });
    } catch (e) { /* the page went on (the restore scenario's first load) */ }
  });
  await ctx.addInitScript(([ids, part, t, imp]) => {
    const now = Date.now(), seed = new URLSearchParams(location.search).get('verify-seed') === 'partial' ? part : ids;
    // a made-up importance (SYNTH_IMP), on the cards before the modules run, as in runCase
    if (Object.keys(imp).length) document.addEventListener('readystatechange', () => {
      if (document.readyState !== 'interactive') return;
      for (const [sid, v] of Object.entries(imp)) {
        document.querySelectorAll(`.front li.fc[data-story="${sid}"]`).forEach((c) => { c.dataset.imp = String(v); });
        const tp = document.querySelector(`template[data-reserve-card="${sid}"]`);
        if (tp) tp.content.firstElementChild.dataset.imp = String(v);
      }
    });
    localStorage.setItem('homeRead:v1', JSON.stringify(Object.fromEntries(seed.map((id) => [id, now]))));
    localStorage.removeItem('syncState:v1'); localStorage.removeItem('homeUnread:v1');
    localStorage.setItem('syncSession:v1', JSON.stringify({ token: t, reader: 'verify', at: now }));
    const below = (el, pad) => {
      const bar = document.querySelector('.bar');
      const top = bar && matchMedia('(min-width:700px)').matches ? bar.getBoundingClientRect().bottom : 0;
      scrollTo(0, el.getBoundingClientRect().top + scrollY - top - pad);
    };
    // a scenario's reload: at load, where a restored scroll position would put the page
    const at = JSON.parse(sessionStorage.getItem('__at') || 'null');
    if (at) addEventListener('load', () => {
      const n = performance.getEntriesByType('navigation')[0], e = document.getElementById(at.id);
      if (e && n && n.type === 'reload') below(e, at.pad);
    });
  }, [S0, S_P || [], TOKEN, SYNTH_IMP]);
  const st = (sid, v) => (sid ? { [sid]: { ts: Date.now() + 60000, v } } : {});
  const open = async (payload, { url = BASE, at = null } = {}) => {
    const base = pulls;
    remote = (i) => payload(i - base);
    const page = await ctx.newPage();
    watchRequests(page, rec);
    await page.goto(url);
    await page.waitForFunction(() => window.__siteReady);
    let i = base;
    if (at) {                                     // the first load's pull is never answered
      await page.evaluate((at) => { sessionStorage.setItem('__at', JSON.stringify(at)); history.scrollRestoration = 'manual'; }, at);
      await page.reload();
      await page.waitForFunction(() => window.__siteReady);
      i = base + 1;
    }
    await page.evaluate(`window.__L = (${LIB.toString()})()`);
    await page.evaluate(() => window.__L.frames().then(window.__L.frames));    // past the page's arming
    return { page, i };
  };
  const F = { ...FR, ENTER, OFF, boardIds: board.map(sidOf) };
  const A = {};
  const none = !FR.REMOTE1 ? 'fewer than two cards on All\'s front' : null;
  // no input since load: the first roam retakes All once, and a second one moves nothing
  if (none) { A.allSyncOnce = [null, none]; A.allSyncOnlyOnce = [null, none]; } else {
    const { page, i } = await open((k) => ({ ...st(FR.REMOTE1, 1), ...(k ? st(FR.REMOTE2, 1) : {}) }));
    Object.assign(A, await page.evaluate(async ({ F, i }) => {
      const L = window.__L, g0 = L.front(), out = {};
      const ok1 = await L.roam(i, F.REMOTE1), g1 = L.front(), o1 = L.once(F.boardIds, F.FRONT);
      out.allSyncOnce = [L.same(g0, F.ALL0) && ok1 && L.same(g1, F.ALL_SYNC) && o1[0], `no input since load; at load ${L.show(g0, F.ALL0)}; roamed ${F.REMOTE1} read: ${L.show(g1, F.ALL_SYNC)}; ${o1[1]}`];
      (await import('/claude-routines/assets/js/sync.js')).initSync();          // a second pull
      const ok2 = await L.roam(i + 1, F.REMOTE2), g2 = L.front();
      const dimmed = !F.ALL_SYNC.cards.includes(F.REMOTE2) || !!document.querySelector(`.front .fc[data-story="${F.REMOTE2}"].is-read`);
      out.allSyncOnlyOnce = [ok2 && L.same(g2, F.ALL_SYNC) && dimmed, `second roam (${F.REMOTE2} read too): ${L.show(g2, F.ALL_SYNC)}; dimmed in place ${dimmed}`];
      return out;
    }, { F, i }));
    await page.close();
  }
  // review F1 (A): a click on the row of the story the roam would promote
  const moreOf = ENTER && `#r-${ENTER} .more`;
  if (none || !ENTER) A.allSyncRowClick = [null, none || 'no story enters the front at the roam'];
  else {
    const { page, i } = await open(() => st(FR.REMOTE1, 1), { at: { id: 'r-' + ENTER, pad: 200 } });
    if (!(await page.$(moreOf))) A.allSyncRowClick = [null, `${ENTER}'s row has no More`];
    else {
      await page.click(moreOf);
      await page.focus(moreOf);                     // WebKit does not focus a clicked button
      A.allSyncRowClick = await page.evaluate(async ({ F, i, sel }) => {
        const L = window.__L, ctl = document.querySelector(sel);
        const ok = await L.roam(i, F.REMOTE1), g = L.front();
        return [ok && L.same(g, F.ALL0) && document.activeElement === ctl && L.vis(ctl),
          `More clicked on ${F.ENTER}'s row, then ${F.REMOTE1} roamed read: ${L.show(g, F.ALL0)}; focus kept ${document.activeElement === ctl}; row shown ${L.vis(ctl)}`];
      }, { F, i, sel: moreOf });
    }
    await page.close();
  }
  // review F1 (B): focus in a builder-front story's restored row, then the roam un-reads it
  if (!OFF) A.allSyncRowFocus = [null, 'no builder-front story is off All\'s front'];
  else {
    const sel = `#r-${OFF} .readbtn`;
    const { page, i } = await open(() => st(OFF, 0), { at: { id: 'r-' + OFF, pad: 200 } });
    await page.focus(sel);
    A.allSyncRowFocus = await page.evaluate(async ({ F, i, sel }) => {
      const L = window.__L, ctl = document.querySelector(sel), row = ctl && ctl.closest('[data-story]');
      const was = !!row && row.classList.contains('is-read');
      const ok = await L.roam(i, F.OFF), g = L.front();
      return [was && ok && L.same(g, F.ALL0) && document.activeElement === ctl && ctl.isConnected && !row.classList.contains('is-read'),
        `focus in ${F.OFF}'s restored row, then roamed unread: ${L.show(g, F.ALL0)}; focus kept ${document.activeElement === ctl}; row un-dimmed ${!!row && !row.classList.contains('is-read')}`];
    }, { F, i, sel });
    await page.close();
  }
  // a scroll only (by script: no pointer, key, wheel or touch) counts as the reader's
  if (none) A.allSyncScroll = [null, none];
  else {
    const { page, i } = await open(() => st(FR.REMOTE1, 1));
    A.allSyncScroll = await page.evaluate(async ({ F, i }) => {
      const L = window.__L;
      scrollTo(0, Math.min(700, document.documentElement.scrollHeight - innerHeight)); await L.frames();
      const ok = await L.roam(i, F.REMOTE1), g = L.front();
      return [ok && L.same(g, F.ALL0), `scrolled ${scrollY}px by script, then ${F.REMOTE1} roamed read: ${L.show(g, F.ALL0)} (not retaken)`];
    }, { F, i });
    await page.close();
  }
  // focus inside the front: the roam only dims
  if (none) A.allSyncTouched = [null, none];
  else {
    const c = ALL0.cards[1], sel = `.front .fc[data-story="${c}"] .readbtn`;
    const { page, i } = await open(() => st(FR.REMOTE1, 1));
    await page.focus(sel);
    A.allSyncTouched = await page.evaluate(async ({ F, i, sel }) => {
      const L = window.__L, ctl = document.querySelector(sel);
      const ok = await L.roam(i, F.REMOTE1), g = L.front(), card = ctl.closest('.fc');
      return [ok && L.same(g, F.ALL0) && document.activeElement === ctl && card.classList.contains('is-read'),
        `focus at the front, then ${F.REMOTE1} roamed read: ${L.show(g, F.ALL0)}; focus kept ${document.activeElement === ctl}; dimmed in place ${card.classList.contains('is-read')}`];
    }, { F, i, sel });
    await page.close();
  }
  // review F2: a reload puts the page back with the promoted row on top (the browser's scroll,
  // not the reader's); the roam retakes All, and what was below that row stays where it was
  if (none || !ENTER) A.allSyncAnchor = [null, none || 'no story enters the front at the roam'];
  else {
    const { page, i } = await open(() => st(FR.REMOTE1, 1), { at: { id: 'r-' + ENTER, pad: -4 } });
    A.allSyncAnchor = await page.evaluate(async ({ F, i, id }) => {
      const L = window.__L;
      const nav = performance.getEntriesByType('navigation')[0].type, row = document.getElementById(id);
      const bar = document.querySelector('.bar'), top = bar && matchMedia('(min-width:700px)').matches ? bar.getBoundingClientRect().bottom : 0;
      const els = [...document.querySelectorAll('main [data-story], main [data-ptr]')].filter((e) => { const r = L.R(e); return L.vis(e) && r.bottom > top + Math.min(24, r.height); });
      // what the reader sees first that the recompose keeps: past the promoted row when it is on
      // top (WebKit, with no scroll anchoring, may shift it after load), and past the pointers of
      // the cards that leave the front
      const leave = F.ALL0.cards.filter((c) => !F.ALL_SYNC.cards.includes(c));
      const doomed = new Set([row, ...leave.map((c) => document.querySelector(`section.day [data-ptr="${c}"]`))]);
      const onTop = els[0] === row, keep = els.find((e) => !doomed.has(e)), t0 = keep ? L.R(keep).top : null;
      const ok = await L.roam(i, F.REMOTE1), g = L.front(), t1 = keep ? L.R(keep).top : null;
      return [nav === 'reload' && !!keep && ok && L.same(g, F.ALL_SYNC) && !L.vis(row) && Math.abs(t1 - t0) <= 2,
        `${nav}: ${id} on top ${onTop}; retaken ${L.show(g, F.ALL_SYNC)}; first kept on screen ${keep ? keep.id || 'pointer ' + keep.dataset.ptr : 'nothing'} ${Math.round(t0)} -> ${Math.round(t1)}px`];
    }, { F, i, id: 'r-' + ENTER });
    await page.close();
  }
  // a partly-read All, no input: a first roam that un-reads a padded card retakes All by the same
  // rule (unread first, then read ones up to four), every story still once
  if (!FR.PAD0) A.allPartialRoam = [null, 'a reserve of fewer than four entries'];
  else {
    const { page, i } = await open(() => st(FR.PAD0, 0), { url: `${BASE}?verify-seed=partial` });
    A.allPartialRoam = await page.evaluate(async ({ F, i }) => {
      const L = window.__L, g0 = L.front();
      const ok = await L.roam(i, F.PAD0), g = L.front(), o = L.once(F.boardIds, F.FRONT);
      return [L.same(g0, F.ALL_P) && ok && L.same(g, F.ALL_PR) && o[0],
        `at load ${L.show(g0, F.ALL_P)}; roamed ${F.PAD0} unread: ${L.show(g, F.ALL_PR)}; ${o[1]}`];
    }, { F, i });
    await page.close();
  }
  // a #fragment load is the reader pointing at a place: it counts, and the named row stays
  if (none || !ENTER) A.allSyncHash = [null, none || 'no story enters the front at the roam'];
  else {
    const { page, i } = await open(() => st(FR.REMOTE1, 1), { url: `${BASE}#r-${ENTER}` });
    A.allSyncHash = await page.evaluate(async ({ F, i, id }) => {
      const L = window.__L, row = document.getElementById(id);
      const ok = await L.roam(i, F.REMOTE1), g = L.front();
      return [ok && L.same(g, F.ALL0) && L.vis(row), `opened at #${id}, then ${F.REMOTE1} roamed read: ${L.show(g, F.ALL0)}; the named row shown ${L.vis(row)}`];
    }, { F, i, id: 'r-' + ENTER });
    await page.close();
  }
  await ctx.close();
  return {
    external: [rec.ext.length === 0, rec.ext.length + ' requests to other hosts ' + rec.ext.slice(0, 2).join(' ')],
    signedIn: [rec.fb.length > 0 && rec.fb.every((r) => ['/readstate', '/prefs'].includes(r.path) && r.auth === 'Bearer <token>'), `${rec.fb.length} feedback-sink requests, all /readstate or /prefs with the session's bearer`],
    errors: [rec.errors.length === 0, rec.errors.length + ' page errors ' + rec.errors.slice(0, 2).join(' | ')],
    ...A,
  };
}

// ------------------------------------------------------------------ no-JS
async function runNoJs(browser, ctxOpts) {
  const ctx = await browser.newContext({ ...ctxOpts, javaScriptEnabled: false });
  const rec = { fb: [], og: 0, ext: [], errors: [] };
  await stub(ctx, rec);
  const p = await ctx.newPage(); watchRequests(p, rec);
  await p.goto(BASE);
  const r = await p.evaluate((want) => {
    const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const hiddenText = [...document.querySelectorAll('.page :is(.fold, .why, .sum, .ed__body, .ed__disc, .hl, .ptag)')].filter((e) => !vis(e) && e.textContent.trim()).length;
    const controls = [...document.querySelectorAll('.page button, .page input, .page textarea')].filter(vis).length;
    const hiwLink = [...document.querySelectorAll('a[href="#hiw"]')].some(vis), key = vis(document.querySelector('.mast__key summary'));
    // the builder's front as it is, whatever the refill would do: no reserve card or pointer shows
    const front = [...document.querySelectorAll('.front .fc')].filter(vis).map((c) => c.dataset.story).join() === want.front.join()
      && (([...document.querySelectorAll('.front .desk .ed')].find(vis) || {}).id || null) === want.desk
      && ![...document.querySelectorAll('[data-reserve-ptr]')].some(vis);
    return { hiddenText, controls, hiwLink, key, front, scroll: document.documentElement.scrollWidth - innerWidth, js: document.documentElement.className };
  }, { front: EXPECT_FRONT, desk: EXPECT_DESK });
  await p.goto(BASE + '#hiw');
  r.hiw = await p.evaluate(() => { const d = document.getElementById('hiw'), b = d.getBoundingClientRect(); return b.width > 0 && b.height > 0 && b.top < innerHeight && b.bottom > 0 && [...d.querySelectorAll('button')].every((x) => !x.getBoundingClientRect().width); });
  await ctx.close();
  const ok = r.hiddenText === 0 && r.controls === 0 && r.scroll <= 0 && r.hiwLink && r.hiw && r.key && r.front && rec.ext.length === 0;
  return [ok, `hidden text blocks ${r.hiddenText}, visible controls ${r.controls}, overflow ${r.scroll}, How-this-works link ${r.hiwLink} -> #hiw shown ${r.hiw}, key ${r.key}, default front ${r.front}, external ${rec.ext.length}`];
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

// ------------------------------------------------------------------ two tabs of the homepage
// Tab A ticks the desk's editorial and a story; tab B, loaded before those ticks, then ticks another
// story. All three marks must survive in homeRead:v1 and paint in both tabs (review F4).
async function runTwoTabs(browser, ctxOpts, fault = null) {
  const ctx = await browser.newContext(ctxOpts);
  const rec = { fb: [], og: 0, ext: [], errors: [] };
  await stub(ctx, rec);
  if (fault?.js) await mutateJs(ctx, fault.js);
  const a = await ctx.newPage(), b = await ctx.newPage();
  watchRequests(a, rec); watchRequests(b, rec);
  await a.goto(BASE); await b.goto(BASE);
  const ids = { ed: EXPECT_DESK, x: sidOf(stories[1]), y: sidOf(stories[2]) };
  await a.evaluate((ids) => { for (const id of [ids.ed, ids.x].filter(Boolean)) document.querySelector(`[data-story="${id}"] .readbtn`).click(); }, ids);
  await b.waitForTimeout(250);
  await b.evaluate((ids) => document.querySelector(`[data-story="${ids.y}"] .readbtn`).click(), ids);
  await a.waitForTimeout(250);
  const stored = await a.evaluate(() => Object.keys(JSON.parse(localStorage.getItem('homeRead:v1') || '{}')));
  const painted = async (pg, list) => pg.evaluate((list) => list.filter(Boolean).every((id) => document.querySelector(`[data-story="${id}"]`).classList.contains('is-read')), list);
  const inB = await painted(b, [ids.ed, ids.x]), inA = await painted(a, [ids.y]);
  await ctx.close();
  const want = [ids.ed, ids.x, ids.y].filter(Boolean);
  const kept = want.filter((id) => stored.includes(id));
  return [kept.length === want.length && inB && inA && rec.ext.length === 0,
    `homeRead:v1 keeps ${kept.length} of ${want.length} marks from two tabs; tab B paints tab A's marks ${inB}, tab A paints tab B's ${inA}`];
}

// ------------------------------------------------------------------ the reading pages
const REVIEWS = fs.readdirSync(path.join(REPO, '_posts')).filter((f) => /-evaluator\.md$/.test(f)
  && /^published:\s*true\s*$/m.test(fs.readFileSync(path.join(REPO, '_posts', f), 'utf8').split(/^---\s*$/m)[1] || ''))
  .map((f) => f.slice(0, 10).replace(/-/g, '/') + '/evaluator/').sort();
const READING = ['prompts/', '404.html', 'admin/', ...REVIEWS];
async function runPages(browser, ctxOpts, css = null) {
  const ctx = await browser.newContext(ctxOpts);
  const rec = { fb: [], og: 0, ext: [], errors: [] };
  await stub(ctx, rec);
  const page = await ctx.newPage(); watchRequests(page, rec);
  const bad = [];
  for (const rel of READING) {
    const res = await page.goto(BASE + rel);
    if (css) await page.addStyleTag({ content: css });
    const r = await page.evaluate(() => {
      document.querySelectorAll('details').forEach((d) => { d.open = true; });   // every prompt open
      // a heading carrying a long unbroken token (a URL, a file path) must wrap, not widen the page
      const long = ' https://example.org/' + 'a'.repeat(96);
      for (const sel of ['.prose__title', '.prose__body > h1', '.prose__body > h2', '.prm-doc h1', '.prm-doc h2']) {
        const h = document.querySelector(sel); if (h) h.append(long);
      }
      return { over: document.documentElement.scrollWidth - innerWidth, h1: document.querySelectorAll('h1').length };
    });
    if (!res.ok()) bad.push(`${rel} HTTP ${res.status()}`);
    if (r.over > 0) bad.push(`${rel} scrolls sideways by ${r.over}px`);
    if (r.h1 < 1) bad.push(`${rel} has no h1`);
  }
  await ctx.close();
  if (rec.ext.length) bad.push(rec.ext.length + ' requests to other hosts');
  if (rec.errors.length) bad.push(rec.errors.length + ' page errors');
  return [bad.length === 0, bad.length ? bad.slice(0, 4).join('; ') : `${READING.length} pages (${REVIEWS.length} reviews, /prompts/ fully open, 404, /admin/), headings carrying a 116-char token: no sideways scroll, no other hosts`];
}

// ------------------------------------------------------------------ sweeps
let fails = 0; const totals = {};
// an assertion is [ok, detail]; ok === null is a SKIP (the data offers no scenario), counted apart
const tally = (k, ok) => { const t = (totals[k] ||= { pass: 0, fail: 0, skip: 0 }); if (ok === null) t.skip++; else if (ok) t.pass++; else { t.fail++; fails++; } };
async function sweep(browser, label, opts) {
  for (const st of STATES) {
    if (ONLY && !ONLY.includes(st)) continue;
    const A = await runCase(browser, opts, st);
    const bad = Object.entries(A).filter(([, [ok]]) => ok === false), skip = Object.entries(A).filter(([, [ok]]) => ok === null);
    Object.values(A).forEach(([ok]) => tally(st, ok));
    log(`${label.padEnd(24)} ${st.padEnd(15)} ${bad.length ? 'FAIL ' + bad.map(([k, [, d]]) => k + ': ' + d).join(' | ') : 'PASS ' + (Object.keys(A).length - skip.length)}`
      + (skip.length ? `  SKIP ${skip.map(([k, [, d]]) => k + ': ' + d).join(' | ')}` : '')
      + (st === 'default' && A.measure ? `  (${A.measure[1]}${A.focus ? '; ' + A.focus[1] : ''})` : ''));
    if (process.env.VERBOSE) for (const [k, [ok, d]] of Object.entries(A)) log(`    ${ok === null ? 'SKIP' : ok ? 'ok  ' : 'FAIL'} ${k}: ${d}`);
  }
}
const c = await chromium.launch();
const wk = await webkit.launch();
log(`suite: ${BASE} <- ${SITE}; board ${board.length} items, ${dates.length} days, front [${EXPECT_FRONT.join(' ')}] desk ${EXPECT_DESK}; beat ${BEAT}; caps ${JSON.stringify(CAP)}`);
log(`refill: reserve ${RESERVE.length} (${RESERVE.join(' ')}), desk reserve ${DESK_RESERVE.join(' ')}; front-read [${REFILL0.cards.join(' ')}] desk ${REFILL0.desk}; beat ${REFILL_BEAT}; lead rule [${FR.R2 ? FR.R2.cards.join(' ') : '-'}]${Object.keys(SYNTH_IMP).length ? ' (made up: data-imp ' + JSON.stringify(SYNTH_IMP) + ')' : ''}; focus kept in ${FOCUS_L}; ${Object.keys(EVT).length} event labels${SYNTH ? '; SYNTH=1' : ''}`);
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

if (!ONLY || ONLY.includes('two-tab')) {
  for (const [label, b, opts] of [['chromium 1024', c, { viewport: { width: 1024, height: 900 } }], ['webkit iPhone15', wk, { ...devices['iPhone 15'] }]]) {
    const [ok, d] = await runTwoTabs(b, opts);
    tally('two-tab', ok); log(`${label.padEnd(24)} two-tab         ${ok ? 'PASS' : 'FAIL'} ${d}`);
  }
}
if (!ONLY || ONLY.includes('pages')) {
  for (const [label, b, opts] of [['chromium 360', c, { viewport: { width: 360, height: 800 } }], ['chromium 1440 dark', c, { viewport: { width: 1440, height: 900 }, colorScheme: 'dark' }], ['webkit iPhone15', wk, { ...devices['iPhone 15'] }]]) {
    const [ok, d] = await runPages(b, opts);
    tally('pages', ok); log(`${label.padEnd(24)} pages           ${ok ? 'PASS' : 'FAIL'} ${d}`);
  }
}

log('\n== TOTALS per state (assertions passed / failed / skipped)');
let P = 0, F = 0;
let S = 0;
for (const [k, t] of Object.entries(totals)) { log(`${k.padEnd(15)} ${t.pass} passed / ${t.fail} failed / ${t.skip} skipped`); P += t.pass; F += t.fail; S += t.skip; }
log(`ALL            ${P} passed / ${F} failed / ${S} skipped (${P + F + S} assertions)`);

// ------------------------------------------------------------------ fault injection
if (process.env.FAULTS !== '0') {
  log('\n== FAULT INJECTION (chromium 1440 unless noted): each deliberate break must fail its own assertion');
  const d3 = `#d-${dates[Math.min(2, dates.length - 1)]}`;
  const FAULTS = [
    { key: 'overflow', state: 'default', css: 'main{min-width:1800px}' },
    // pull the second day edition up into the first: two sibling zones overlap whatever the front
    // holds (a margin on the 2nd front card overlapped nothing once a boot-open card took row 1)
    { key: 'overlap', state: 'default', css: `#d-${dates[Math.min(1, dates.length - 1)]}{margin-top:-160px}` },
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
    // review 2026-09-25: each strengthened gate must fail on the defect it now guards
    { key: 'photoBeside', state: 'expanded', css: '.js .fcards--rest > .fc > article{display:flex!important}' },
    { key: 'edRead', state: 'unread-edition', js: { file: 'board.js', from: 'return mine.length > 0 && mine.every(', to: 'return mine.length > 0 && mine.some(' } },
    { key: 'og', state: 'default', js: { file: 'og.js', from: "img.referrerPolicy = 'no-referrer';", to: '' } },
    { key: 'og', state: 'default', js: { file: 'og.js', from: 'if (!src) { slot.hidden = true; return; }', to: 'if (!src) return;' } },
    { key: 'freshSame', state: 'default', js: { file: 'fresh.js', from: 'j.build_stamp && j.build_stamp !== stamp', to: 'j.build_stamp' } },
    { key: 'freshBg', state: 'stale-bg', js: { file: 'fresh.js', from: "let hiddenAt = document.visibilityState === 'hidden' ? Date.now() : 0;", to: 'let hiddenAt = 0;' } },
    { key: 'periods', state: 'default', css: '', init: () => document.addEventListener('DOMContentLoaded', () => { const t = document.querySelector('.day__cov .ptag time'); t.textContent = t.textContent.replace(/^\d+/, '1'); }) },
    { key: 'focus', state: 'default', css: '', init: () => document.addEventListener('DOMContentLoaded', () => document.querySelectorAll('.bar button, .mast a, .mast summary').forEach((e) => e.setAttribute('tabindex', '-1'))) },
    // round 2 (2026-09-25): the Unread refill and the event label
    { key: 'refill', state: 'front-read', js: { file: 'refill.js', from: 'if (el && !isRead(el) && beatOk(el, active)) out.push(el);', to: 'if (el && beatOk(el, active)) out.push(el);' } },
    { key: 'refillPtrs', state: 'front-read', js: { file: 'board.js', from: 'p.hidden = !t || !t.isConnected || t.hidden;', to: "p.hidden = p.hasAttribute('data-reserve-ptr') || !t || !t.isConnected || t.hidden;" } },
    { key: 'counts', state: 'front-read', js: { file: 'board.js', from: "export const items = main ? [...main.querySelectorAll('[data-story]')] : [];",
      to: "export const items = main ? [...main.querySelectorAll('[data-story]'), ...[...main.querySelectorAll('template')].flatMap((t) => [...t.content.querySelectorAll('[data-story]')])] : [];" } },
    { key: 'refillLead', state: 'front-read', js: { file: 'refill.js', from: "const lead = out.find((el) => el.dataset.imp === '3') || out[0];", to: 'const lead = out[0];' } },
    { key: 'eventLabel', state: 'default', css: '', init: `document.addEventListener('DOMContentLoaded', () => {
      const el = document.querySelector('main [data-story="${sidOf(IN_PERIOD)}"]'), old = el.querySelector('.evt'); if (old) old.remove();
      el.querySelector('.row__meta, .fc__top').insertAdjacentHTML('beforeend', '<span class="evt"><time datetime="${IN_PERIOD.event_date >= PSTART[sidOf(IN_PERIOD)] ? IN_PERIOD.event_date : IN_PERIOD.date}">Happened</time></span>'); })` },
    // round 3 (review 2026-09-25): focus through a recompose, the desk-only line, the day link
    ...['refillFocusSame', 'refillFocusAround', 'refillFocusTyping'].map((key) => ({ key, state: 'front-read',
      js: { file: 'refill.js', from: 'function reconcile(box, want) {\n  if (!box) return;', to: 'function reconcile(box, want) {\n  if (box) box.replaceChildren(...want);\n  return;' } })),
    { key: 'refillFocusAll', state: 'front-read', js: { file: 'refill.js', from: 'function reconcile(box, want) {\n  if (!box) return;', to: 'function reconcile(box, want) {\n  if (box) box.replaceChildren(...want);\n  return;' } },
    { key: 'refillFocusMove', state: 'front-read', js: { file: 'board.js', from: "if (had && had !== document.body && document.activeElement !== had && had.isConnected && !had.closest('[hidden]')) {", to: 'if (false) {' } },
    { key: 'frontLineDesk', state: 'front-read', js: { file: 'board.js', from: 'frontN.hidden = !cards.length && (!!rs || active.size > 0);', to: 'frontN.hidden = false;' } },
    { key: 'refillBeat', state: 'front-read', js: { file: 'refill.js', from: 'if (el && !isRead(el) && beatOk(el, active)) out.push(el);', to: 'if (el && !isRead(el)) out.push(el);' } },
    { key: 'refillDayLink', state: 'front-read', js: { file: 'refill.js', from: 'pointDayLinks(ed.dataset.story);', to: 'pointDayLinks(deskDefault.dataset.story);' } },
    { key: 'eventLabelShown', state: 'default', css: '', init: () => document.addEventListener('DOMContentLoaded', () => { const e = document.querySelector('main .evt'); if (e) e.remove(); }) },
    // round 4 (owner decision 2026-09-25): All's front is composed at load; within a session reading only dims
    { key: 'allLoad', state: 'front-read', js: { file: 'refill.js', from: 'if (!cards.length) return { cards: defaults, desk: deskPick(new Set()) };', to: 'return { cards: defaults, desk: deskDefault };' } },
    { key: 'allTickDims', state: 'front-read', js: [
      { file: 'refill.js', from: "mode === 'all' ? all.cards : defaults", to: "mode === 'all' ? pick(new Set()) : defaults" },
      { file: 'board.js', from: '        if (rs) {\n          apply();', to: '        if (true) {\n          apply();' }] },
    { key: 'allAllRead', state: 'all-read', js: { file: 'refill.js', from: 'if (!cards.length) return { cards: defaults, desk: deskPick(new Set()) };', to: 'if (!cards.length) return { cards, desk: deskPick(new Set()) };' } },
    { key: 'allReadView', state: 'front-read', js: { file: 'refill.js', from: "const cards = mode === 'unread' ? pick(active) : mode === 'all' ? all.cards : defaults;", to: "const cards = mode === 'unread' ? pick(active) : all.cards;" } },
    { key: 'refillAll', state: 'front-read', js: { file: 'refill.js', from: "mode === 'all' ? all.cards : defaults", to: "mode === 'all' ? pick(new Set()) : defaults" } },
    { key: 'allOnce', state: 'front-read', js: { file: 'refill.js', from: '} else if (ptr.nextElementSibling !== row) ptr.after(row);', to: '}' } },
    { key: 'allSyncOnce', state: 'all-sync', js: { file: 'board.js', from: '      const gone = refill.retake();\n      anchored(topItem(rs ? undefined : gone), () => { paint(); apply(); });', to: '      anchored(topItem(), () => { paint(); apply(); });' } },
    { key: 'allSyncOnlyOnce', state: 'all-sync', js: { file: 'board.js', from: 'if (!first || touched) { remoteRead(); return; }', to: 'if (touched) { remoteRead(); return; }' } },
    { key: 'allSyncTouched', state: 'all-sync', js: { file: 'board.js', from: 'if (!first || touched) { remoteRead(); return; }', to: 'if (!first) { remoteRead(); return; }' } },
    // round 4 review: the guard is the whole page, a script scroll counts, the anchor stays, a #fragment counts
    ...['allSyncRowClick', 'allSyncRowFocus'].map((key) => ({ key, state: 'all-sync', js: { file: 'board.js',
      from: 'for (const t of TOUCH) document.addEventListener(t, touch, { capture: true, passive: true });',
      to: "for (const t of TOUCH) main.querySelector('section.front').addEventListener(t, touch, { capture: true, passive: true });" } })),
    { key: 'allSyncScroll', state: 'all-sync', js: { file: 'board.js', edits: [
      ["addEventListener('scroll', onScroll, { passive: true });", ''],
      ['if (first && !touched) onScroll();', '']] } },
    { key: 'allSyncAnchor', state: 'all-sync', js: { file: 'board.js', from: 'anchored(topItem(rs ? undefined : gone), ', to: 'anchored(topItem(), ' } },
    // round 5: a partly-read All front is filled with read stories after the unread ones
    { key: 'allPartial', state: 'all-partial', js: { file: 'refill.js', from: 'if (el && isRead(el) && !cards.includes(el)) cards.push(el);', to: '' } },
    { key: 'allPartialLead', state: 'all-partial', js: { file: 'refill.js', from: 'if (el && isRead(el) && !cards.includes(el)) cards.push(el);', to: 'if (el && isRead(el) && !cards.includes(el)) cards.unshift(el);' } },
    { key: 'allPartialRoam', state: 'all-sync', js: { file: 'refill.js', from: 'function retake() { const next = take(),', to: 'function retake() { const next = { cards: pick(new Set()), desk: deskPick(new Set()) },' } },
    { key: 'allSyncHash', state: 'all-sync', js: { file: 'board.js', from: 'let roamedOnce = false, touched = !!location.hash, mark = null;', to: 'let roamedOnce = false, touched = false, mark = null;' } },
    { key: 'deskDate', state: 'front-read', css: '.ed--desk .ed__top .fday{display:none}' },
  ];
  // a fault whose gate is a SKIP on this data proves nothing either way: it is counted apart, not
  // MISSED (that would turn a SKIP back into a failure on valid data); an absent gate is MISSED
  let caught = 0, skipped = 0;
  const base = await runCase(c, { viewport: { width: 1440, height: 900 } }, 'default');
  for (const f of FAULTS) {
    const A = await runCase(c, { viewport: { width: f.w || 1440, height: 900 } }, f.state, f);
    const flipped = !!A[f.key] && A[f.key][0] === false, skip = !!A[f.key] && A[f.key][0] === null;
    if (flipped) caught++;
    if (skip) skipped++;
    log(`${flipped ? 'CAUGHT' : skip ? 'SKIPPED' : 'MISSED'}  ${f.key.padEnd(12)} ${f.state.padEnd(14)} ${(f.w || 1440) + 'px'}  ${f.css || (f.js ? [].concat(f.js).map((j) => `${j.file}: ${(j.edits || [[j.from, j.to]]).map(([a, b]) => `${a} -> ${b || '(removed)'}`).join(' + ')}`).join(' + ').replace(/\n\s*/g, ' ') : '(script)')}  ->  ${A[f.key] ? A[f.key][1] : 'n/a'}`);
  }
  // contract faults: the /prefs body grows a field; homeRead:v1 gets a non-number value
  const CF = [
    { key: 'requests', init: () => { const f = window.fetch; window.fetch = (u, o) => { if (String(u).endsWith('/prefs') && o && o.body) { const b = JSON.parse(o.body); b.extra = 1; o = { ...o, body: JSON.stringify(b) }; } return f(u, o); }; } },
    { key: 'storage', init: () => { const s = Storage.prototype.setItem; Storage.prototype.setItem = function (k, v) { if (k === 'homeRead:v1') { const o = JSON.parse(v); for (const x in o) o[x] = true; v = JSON.stringify(o); } return s.call(this, k, v); }; } },
  ];
  for (const f of CF) {
    const A = await runContract(c, { viewport: { width: 1024, height: 900 } }, f);
    const flipped = !!A[f.key] && A[f.key][0] === false;
    if (flipped) caught++;
    log(`${flipped ? 'CAUGHT' : 'MISSED'}  ${f.key.padEnd(12)} contract       (script)  ->  ${A[f.key] ? A[f.key][1] : 'n/a'}`);
  }
  const PF = ['.prose pre{overflow-x:visible!important;max-inline-size:none!important}',
    '.prose__title,.prose__body > :is(h1,h2),.prm-doc :is(h1,h2){overflow-wrap:normal!important}'];
  for (const css of PF) {
    const [ok, d] = await runPages(c, { viewport: { width: 360, height: 800 } }, css);
    if (!ok) caught++;
    log(`${!ok ? 'CAUGHT' : 'MISSED'}  pages        reading        360px  ${css}  ->  ${d}`);
  }
  {
    const [ok, d] = await runTwoTabs(c, { viewport: { width: 1024, height: 900 } }, { js: { file: 'store.js', from: "addEventListener('storage',", to: "((t, f) => {})('storage'," } });
    if (!ok) caught++;
    log(`${!ok ? 'CAUGHT' : 'MISSED'}  two-tab      store.js       1024px  (no storage listener)  ->  ${d}`);
  }
  const total = FAULTS.length + CF.length + PF.length + 1 - skipped;
  const clean = Object.values(base).every(([ok]) => ok !== false);
  log(`fault self-test: ${caught}/${total} faults caught${skipped ? ` (${skipped} more skipped: their gate had no scenario on this data)` : ''} (baseline default@1440 ${clean ? 'clean' : 'NOT clean'})`);
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
  // round 2: the refilled front under Unread (the default front and its Desk's view read), and a
  // "Happened" label at the narrowest width, on a front card when the refill holds one
  const extra = [['front-read-unread-1440', c, { viewport: { width: 1440, height: 900 } }, 'front-read'],
    ['front-read-unread-iphone15', wk, { ...devices['iPhone 15'] }, 'front-read'],
    ['event-label-360', c, { viewport: { width: 360, height: 800 } }, 'event'],
    // All at load with the default front read: an older editorial promoted to the Desk's view
    ['desk-promoted-390', c, { viewport: { width: 390, height: 844 } }, 'desk'],
    ['desk-promoted-1280', c, { viewport: { width: 1280, height: 900 } }, 'desk']];
  for (const [name, b, opts, kind] of extra) {
    const ctx = await b.newContext(opts); const rec = { fb: [], og: 0, ext: [], errors: [] }; await stub(ctx, rec);
    const p = await ctx.newPage();
    await p.addInitScript((ids) => localStorage.setItem('homeRead:v1', JSON.stringify(Object.fromEntries(ids.map((id) => [id, Date.now()])))), S0);
    await p.goto(BASE); await p.evaluate(() => document.fonts.ready);
    await p.evaluate((kind) => {
      if (kind === 'desk') { const d = document.querySelector('.front .desk'); d.scrollIntoView({ block: innerWidth < 700 ? 'start' : 'center' }); return; }
      document.querySelector('.seg button[data-rs="unread"]').click();
      const e = kind === 'event' && [...document.querySelectorAll('.front .fc .evt, main .evt')].find((x) => x.getBoundingClientRect().width > 0);
      if (e) e.closest('[data-story]').scrollIntoView({ block: 'center' }); else document.querySelector('.front').scrollIntoView();
    }, kind);
    await p.waitForTimeout(400);
    await p.screenshot({ path: path.join(SHOTS, name + '.png') });
    await ctx.close();
    log(`shot ${path.join(SHOTS, name + '.png')}`);
  }
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
