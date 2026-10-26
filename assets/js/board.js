// The board: read state, the beat and read filters, the honest counts (C12), and the gate that
// decides whether a late roam may recompose the front (C8). Filtering only sets `hidden`; it
// never measures. What moves is the front, which front.js composes.
import { readMap } from './state.js';
import { isRead, setRead, paintEl, isEditorial } from './read.js';
import { anchored, topItem } from './anchor.js';
import { createFront } from './front.js';

const main = document.getElementById('main');
// the live items at load: cards, rows, editorials; each story once (copies are not items)
export const items = main ? [...main.querySelectorAll('[data-story]')] : [];
const chips = [...document.querySelectorAll('.chip[data-topic]')];
const segs = [...document.querySelectorAll('.seg button[data-rs]')];
const empty = document.getElementById('empty');
const announce = document.getElementById('announce');
const nBeats = [...document.querySelectorAll('.bar__nbeats')];
let front = { compose: () => [], copies: () => [], snapshot() {}, retake: () => new Set(), onFront: () => new Set() };

// ---- read state
export function paint() {
  for (const el of items) paintEl(el);
  for (const c of front.copies()) if (c.isConnected) paintEl(c);
  counts();
}

// ---- filters
const active = new Set();
let held = [];                                   // roamed beats with no chip on today's page
let rs = '';
const chipKeys = new Set(chips.map((c) => c.dataset.topic).filter(Boolean));
function beatOk(el, set) {
  if (!set.size) return true;
  return (el.dataset.topics || '').split(' ').some((t) => set.has(t));
}
const rsOk = (el, r) => (r === 'unread' ? !isRead(el) : r === 'read' ? isRead(el) : true);
const matches = (el) => rsOk(el, rs) && beatOk(el, active);

// One rule for every number (C12): a control's count is what the page shows with that control
// pressed, given the other axis. A beat chip counts the active beats plus itself (so under a
// held beat a chip shows the union it would make), All counts every beat, a read-state button
// counts its state under the beats. Editorials count like stories.
function counts() {
  for (const b of segs) {
    const r = b.dataset.rs;
    b.querySelector('.ct').textContent = items.filter((el) => rsOk(el, r) && beatOk(el, active)).length;
  }
  for (const c of chips) {
    const k = c.dataset.topic;
    const set = new Set(k ? active : []);
    if (k) set.add(k);
    c.querySelector('.ct').textContent = items.filter((el) => rsOk(el, rs) && beatOk(el, set)).length;
  }
}
function paintControls() {
  for (const c of chips) c.setAttribute('aria-pressed', String(c.dataset.topic ? active.has(c.dataset.topic) : active.size === 0));
  for (const b of segs) b.setAttribute('aria-pressed', String(b.dataset.rs === rs));
  for (const n of nBeats) { n.textContent = active.size; n.hidden = !active.size; }
}

const shownIn = (root) => !!root.querySelector('[data-story]:not([hidden])');
const visible = (el) => el.isConnected && !el.closest('[hidden]');

export function apply() {
  // a recompose can move a node, and a moved node drops the focus to <body>: an element still
  // shown gets it back, with its caret (C14)
  const had = document.activeElement;
  const sel = had && typeof had.selectionStart === 'number' ? [had.selectionStart, had.selectionEnd, had.selectionDirection] : null;
  let shown = 0;
  for (const el of items) { const m = matches(el); el.hidden = !m; if (m) shown++; }
  // the front: Unread's live pick, All's load-time pick, the builder's under Read. Copies on
  // the page filter like the items they stand in for.
  const cards = front.compose(rs === 'unread' ? 'unread' : rs === 'read' ? 'read' : 'all', active);
  for (const c of front.copies()) if (c.isConnected) { c.hidden = !matches(c); paintEl(c); }
  const onFront = new Set(cards.filter((c) => !c.hidden).map((c) => c.dataset.story));
  frontLine(cards.filter((c) => !c.hidden));
  if (main) {
    for (const z of main.querySelectorAll('.fcards, .desk, .front')) z.hidden = !shownIn(z);
    const filtering = !!rs || active.size > 0;
    for (const sec of main.querySelectorAll('section.day')) {
      // a day shows while any of its stories shows, in it or on the front
      const sids = (sec.dataset.sids || '').split(' ').filter(Boolean);
      const up = sids.filter((s) => onFront.has(s)).length;
      sec.hidden = !shownIn(sec) && !up;
      if (sec.hidden) continue;
      // the header describes what it shows: "5 of 9 stories shown", and what it lent (C9)
      const n = sec.querySelector('.day__n');
      const total = +n.dataset.total, noun = total === 1 ? 'story' : 'stories';
      const here = sec.querySelectorAll('.rows > [data-story]:not([hidden])').length;
      n.querySelector('.day__count').textContent = filtering ? (here + up) + ' of ' + total + ' ' + noun + ' shown' : total + ' ' + noun;
      const upEl = n.querySelector('.day__up');
      if (upEl) { upEl.hidden = !up; upEl.querySelector('.day__upn').textContent = up; }
      // a desk's period tag stays while a story of that edition shows anywhere
      for (const t of sec.querySelectorAll('.day__cov .ptag')) {
        t.hidden = !main.querySelector('[data-edition="' + sec.dataset.date + '-' + t.dataset.stream + '"]:not([hidden])');
      }
    }
    // an in-page link never points at something the filter hid
    for (const a of document.querySelectorAll('#main a[href^="#"], .daylist a[href^="#"]')) {
      const t = document.getElementById(a.getAttribute('href').slice(1));
      a.hidden = !t || !!t.closest('[hidden]');
    }
    for (const p of main.querySelectorAll('.day__links')) p.hidden = !p.querySelector('a:not([hidden])');
  }
  // the most specific true sentence, on the first line where the first story would be (R21)
  if (empty) {
    empty.hidden = shown > 0;
    if (!shown) {
      empty.textContent = rs === 'unread' ? 'All caught up: every story ' + (active.size ? 'on this beat' : 'in this edition') + ' is read.'
        : rs === 'read' ? 'Nothing marked read' + (active.size ? ' on this beat' : '') + ' yet.'
        : 'No stories on this beat right now.';
    }
  }
  counts();
  if (had && had !== document.body && document.activeElement !== had && visible(had)) {
    had.focus({ preventScroll: true });
    if (sel) try { had.setSelectionRange(...sel); } catch (e) { /* a type without a caret */ }
  }
}

// "The 4 stories that matter most right now · from Wed 21 Oct", recounted from the cards shown
const frontN = main && main.querySelector('.front__n');
function frontLine(cards) {
  if (!frontN || !frontN.dataset.date) return;
  if (!frontN.dataset.orig) frontN.dataset.orig = frontN.textContent;
  // no story card under a filter (the Desk's view alone, or nothing): no count to state
  frontN.hidden = !cards.length && (!!rs || active.size > 0);
  if (!cards.length) { frontN.textContent = frontN.dataset.orig; return; }
  const unread = rs === 'unread' ? 'unread ' : '';
  const n = cards.length === 1 ? 'The ' + unread + 'story that matters' : 'The ' + cards.length + ' ' + unread + 'stories that matter';
  const older = new Map();
  for (const c of cards) {
    const t = c.querySelector('.fday');
    if (t && t.getAttribute('datetime') !== frontN.dataset.date) older.set(t.getAttribute('datetime'), t.textContent);
  }
  const from = [...older.keys()].sort().reverse().map((k) => older.get(k));
  frontN.textContent = n + ' most right now' + (from.length ? ' · from ' + from.join(', ') : '');
}

export function initBoard({ prefs, record, adopt = () => {} }) {
  front = createFront(main, { isRead, beatOk, adopt });
  front.snapshot();                               // All's front: the pick from the read set at load
  // The roamed read set can land after first paint (C8). All's pick is then taken once more, at
  // the first roam only, and only if the reader has not interacted with the page since load: a
  // pointer, key, focus, wheel or touch anywhere, or a scroll of their own. A reader's scroll
  // moves the content with it (the top item shifts by exactly what the page scrolled); scroll
  // anchoring, a #fragment or a restored position, and anchored() move the page to keep content
  // where it was, so they do not count. After a reload or a history step the browser restores a
  // position, and on a #fragment load it scrolls to the fragment, both by load: there scrolls
  // count from two frames after load; after a plain navigation, from the first. The #fragment
  // itself is the reader pointing at a place, and a recompose could hide the very row it names.
  let roamedOnce = false, touched = !!location.hash, mark = null;
  const TOUCH = ['pointerdown', 'keydown', 'focusin', 'wheel', 'touchstart'];
  const markTop = () => { const el = topItem(); return el && { el, top: el.getBoundingClientRect().top, y: scrollY }; };
  const onScroll = () => {
    if (!mark) return;                            // before load settles: the browser's scroll
    const { el, top, y } = mark, moved = scrollY - y;
    const withIt = visible(el) && Math.abs(el.getBoundingClientRect().top - top + moved) < 2;
    if (Math.abs(moved) >= 2 && withIt) touch(); else mark = markTop();
  };
  function quiet() { removeEventListener('scroll', onScroll); for (const t of TOUCH) document.removeEventListener(t, touch, true); }
  function touch() { touched = true; quiet(); }
  if (!touched) {
    for (const t of TOUCH) document.addEventListener(t, touch, { capture: true, passive: true });
    addEventListener('scroll', onScroll, { passive: true });
  }
  // the stored selection; held keys survive (R37)
  const seed = (p) => {
    active.clear();
    held = p.topics.filter((k) => !chipKeys.has(k));
    for (const k of p.topics) if (chipKeys.has(k)) active.add(k);
    rs = p.rs;
  };
  seed(prefs);
  const persist = () => record([...active, ...held], rs);

  for (const c of chips) {
    c.addEventListener('click', () => {
      const k = c.dataset.topic;
      if (!k) { active.clear(); held = []; }      // All replaces: held keys go too, so it roams
      else if (active.has(k)) active.delete(k); else active.add(k);
      paintControls(); apply(); persist();
    });
  }
  for (const b of segs) b.addEventListener('click', () => { rs = b.dataset.rs; paintControls(); apply(); persist(); });
  // a keyboard-focused chip stays wholly inside the scrolling strip
  for (const strip of document.querySelectorAll('.bar__strip')) {
    strip.addEventListener('focusin', (ev) => {
      const c = ev.target.closest('.chip');
      if (!c) return;
      const r = c.getBoundingClientRect(), b = strip.getBoundingClientRect(), pad = 16;
      if (r.left < b.left + pad) strip.scrollLeft -= b.left + pad - r.left;
      else if (r.right > b.right - pad) strip.scrollLeft += r.right - (b.right - pad);
    });
  }
  const readOn = (a) => { const el = a.closest('[data-story]'); if (el && !isRead(el)) { setRead(el, true); paint(); } };
  if (main) {
    main.addEventListener('click', (e) => {
      const rb = e.target.closest('.readbtn');
      if (rb) {                                   // the explicit toggle honours an active filter at once
        const el = rb.closest('[data-story]');
        setRead(el, !isRead(el));
        paint();
        if (announce) announce.textContent = isRead(el) ? 'Marked read' : 'Marked unread';
        if (rs) {
          apply();
          // the ✓ left with its item: the focus goes to the filter, unless it is somewhere else
          const f = document.activeElement;
          if (!visible(el) && (!f || f === document.body || el.contains(f))) { const on = segs.find((b) => b.getAttribute('aria-pressed') === 'true'); if (on) on.focus(); }
        }
        return;
      }
      // opening the article, or a Discuss conversation from it, reads it: dims, never re-filters
      const a = e.target.closest('.hl a, a.discuss');
      if (a) readOn(a);
    });
    main.addEventListener('auxclick', (e) => {   // a middle-click "open in background tab" counts too
      if (e.button !== 1) return;
      const a = e.target.closest('.hl a, a.discuss');
      if (a) readOn(a);
    });
  }
  paintControls();
  paint();
  apply();
  if (!touched) {
    // WebKit may not have the navigation entry yet while the modules run: the legacy field says it too
    const entry = performance.getEntriesByType && performance.getEntriesByType('navigation')[0];
    const nav = entry ? entry.type : ({ 1: 'reload', 2: 'back_forward' })[performance.navigation && performance.navigation.type];
    const arm = () => { if (!touched) mark = markTop(); };
    const late = () => requestAnimationFrame(() => requestAnimationFrame(arm));
    if (nav !== 'reload' && nav !== 'back_forward' && !location.hash) arm();
    else if (document.readyState === 'complete') late(); else addEventListener('load', late, { once: true });
  }

  function remoteRead() { anchored(topItem(), () => { paint(); if (rs) apply(); }); }
  return {
    // a roamed selection re-filters without throwing the reader down the page
    remotePrefs(p) { seed(p); paintControls(); anchored(topItem(), apply); },
    remoteRead,
    roamed() {
      const first = !roamedOnce;
      roamedOnce = true;
      if (first && !touched) onScroll();          // a scroll whose event has not fired yet counts too
      quiet();
      if (!first || touched) { remoteRead(); return; }
      const gone = front.retake();
      anchored(topItem(rs ? undefined : gone), () => { paint(); apply(); });
    },
    readMap,
  };
}
