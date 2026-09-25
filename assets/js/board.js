// The board: read state, the beat and read filters, and the honest counts.
//
// Items are the elements that carry a read id (data-story): front cards, index rows and
// editorials. Pointer rows ([data-ptr]) stand in a day for an item lifted to the front and follow
// that item. Filtering only sets the `hidden` attribute; it never measures anything. What moves
// is the front, which refill.js composes from the builder's reserve: live under Unread, once at
// load under All (copies are not items: each story is counted once, by its own element).
import { READ_KEY, UNREAD_KEY, readMap, unreadMap, save } from './store.js';
import { noteLocalRead } from './sync.js';
import { anchored } from './fold.js';
import { createRefill } from './refill.js';

const main = document.getElementById('main');
export const items = main ? [...main.querySelectorAll('[data-story]')] : [];
const ptrs = main ? [...main.querySelectorAll('[data-ptr]')] : [];
const storiesByEdition = new Map();
for (const el of items) {
  if (!isEditorial(el)) {
    if (!storiesByEdition.has(el.dataset.edition)) storiesByEdition.set(el.dataset.edition, []);
    storiesByEdition.get(el.dataset.edition).push(el);
  }
}
const chips = [...document.querySelectorAll('.bar .chip, .mast__beats .chip')];
const segs = [...document.querySelectorAll('.bar .seg button')];
const empty = document.getElementById('empty');
const announce = document.getElementById('announce');

function isEditorial(el) { return el.dataset.zone === 'editorial'; }

// ---- read state
// An editorial is read when ticked, OR when every story of its (date, stream) edition is read;
// an explicit tick or un-tick wins over the rule. Derived at paint time, never stored as read.
export function isRead(el) {
  const id = el.dataset.story;
  if (!isEditorial(el)) return !!readMap[id];
  if (readMap[id]) return true;
  if (unreadMap[id]) return false;
  const mine = storiesByEdition.get(el.dataset.edition) || [];
  return mine.length > 0 && mine.every((s) => !!readMap[s.dataset.story]);
}
function ruleSaysRead(el) {
  const mine = storiesByEdition.get(el.dataset.edition) || [];
  return mine.length > 0 && mine.every((s) => !!readMap[s.dataset.story]);
}
function setRead(el, v) {
  const id = el.dataset.story;
  if (!id) return;
  if (isEditorial(el)) {                         // local only: the Worker keeps st- ids alone
    delete unreadMap[id];
    if (v) readMap[id] = Date.now();
    else { delete readMap[id]; if (ruleSaysRead(el)) unreadMap[id] = Date.now(); }
    save(READ_KEY, readMap);
    save(UNREAD_KEY, unreadMap);
    return;
  }
  if (v) readMap[id] = Date.now(); else delete readMap[id];
  save(READ_KEY, readMap);
  noteLocalRead(id, v);
}

// a pointer follows the element its link targets: a front card (#c-…) or the desk's editorial
const target = (p) => document.getElementById((p.querySelector('a') || { getAttribute: () => '#' }).getAttribute('href').slice(1));
let refill = { compose: () => [], copies: () => [] };

// Reading dims and never hides, moves or folds (owner ruling, 2026-07-26; since 2026-09-25 All's
// front is composed once at load, and within the session reading still only dims): paint touches
// the read class and the ✓ state only.
function paintEl(el) {
  const r = isRead(el);
  el.classList.toggle('is-read', r);
  const b = el.querySelector('.readbtn');
  if (b) {
    b.setAttribute('aria-pressed', String(r));
    b.title = r ? 'mark as unread' : 'mark as read';
  }
}
export function paint() {
  for (const el of [...items, ...refill.copies()]) paintEl(el);
  for (const p of ptrs) {
    const t = target(p);
    p.classList.toggle('is-read', !!t && isRead(t));
  }
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
function rsOk(el, r) { return r === 'unread' ? !isRead(el) : r === 'read' ? isRead(el) : true; }
const matches = (el) => rsOk(el, rs) && beatOk(el, active);

// One rule for every number: a control's count is what the page shows with that control pressed,
// given the other axis. A beat chip counts the active beats plus itself (so a held chip shows the
// current total), All counts every beat, a read-state button counts its state under the beats.
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
const anyShown = (root) => !!root.querySelector('[data-story]:not([hidden]), [data-ptr]:not([hidden])');

export function apply() {
  // compose() can still move a card between the lead and the rest, and a moved node drops the
  // focus to <body>: an element that is still shown gets it back, with its caret (review F1)
  const had = document.activeElement;
  const sel = had && typeof had.selectionStart === 'number' ? [had.selectionStart, had.selectionEnd, had.selectionDirection] : null;
  let shown = 0;
  for (const el of items) { const m = matches(el); el.hidden = !m; if (m) shown++; }
  // the front: Unread's live pick, All's load-time pick, or the builder's under Read; nothing
  // below unhides what it decided. Copies on the page filter like the items they stand in for.
  const cards = refill.compose(rs === 'unread' ? 'unread' : rs === 'read' ? 'read' : 'all', active);
  for (const c of refill.copies()) if (c.isConnected) { c.hidden = !matches(c); paintEl(c); }
  for (const p of ptrs) { const t = target(p); p.hidden = !t || !t.isConnected || t.hidden; }
  frontLine(cards.filter((c) => !c.hidden));
  if (main) {
    for (const z of main.querySelectorAll('.fcards, .desk, .front, section.day')) z.hidden = !anyShown(z);
    // an in-page link never points at something the filter hid (pointer rows follow their item)
    for (const a of main.querySelectorAll('a[href^="#"]')) {
      if (a.closest('.ptr')) continue;
      const t = document.getElementById(a.getAttribute('href').slice(1));
      a.hidden = !t || !!t.closest('[hidden]');
    }
    for (const p of main.querySelectorAll('.day__links')) p.hidden = !p.querySelector('a:not([hidden])');
    // a day header describes what it shows: "5 of 9 stories shown", desks with nothing shown untagged
    const filtering = !!rs || active.size > 0;
    for (const sec of main.querySelectorAll('section.day')) {
      if (sec.hidden) continue;
      const n = sec.querySelector('.day__n');
      const total = +n.dataset.total, noun = total === 1 ? 'story' : 'stories';
      const v = sec.querySelectorAll('.rows > [data-story]:not([hidden]), .rows > [data-ptr]:not([hidden])').length;
      const up = sec.querySelectorAll('.rows > [data-ptr]:not([hidden])').length;   // on the front as composed
      n.textContent = filtering ? v + ' of ' + total + ' ' + noun + ' shown' : total + ' ' + noun + (up ? ' · ' + up + ' on the front' : '');
      for (const t of sec.querySelectorAll('.day__cov .ptag')) {
        t.hidden = !sec.querySelector('[data-edition="' + sec.dataset.date + '-' + t.dataset.stream + '"]:not([hidden])');
      }
    }
  }
  // the most specific true sentence, on the first line where the first story would be (R21)
  if (empty) {
    empty.hidden = shown > 0;
    if (!shown) {
      empty.textContent = rs === 'unread' ? 'All caught up — every story ' + (active.size ? 'on this beat' : 'in this edition') + ' is read.'
        : rs === 'read' ? 'Nothing marked read' + (active.size ? ' on this beat' : '') + ' yet.'
        : 'No stories on this beat right now.';
    }
  }
  counts();
  if (had && had !== document.body && document.activeElement !== had && had.isConnected && !had.closest('[hidden]')) {
    had.focus({ preventScroll: true });
    if (sel) try { had.setSelectionRange(...sel); } catch (e) { /* a type without a caret */ }
  }
}

// "The 4 stories that matter most right now · from Wed 23 Sep", recounted from the cards shown
const frontN = main && main.querySelector('.front__n');
function frontLine(cards) {
  if (!frontN || !frontN.dataset.date) return;
  if (!frontN.dataset.orig) frontN.dataset.orig = frontN.textContent;
  // no story card under a filter (the Desk's view alone, or nothing): no count to state (review F2)
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

function paintControls() {
  for (const c of chips) {
    const k = c.dataset.topic;
    c.setAttribute('aria-pressed', String(k ? active.has(k) : active.size === 0));
  }
  for (const b of segs) b.setAttribute('aria-pressed', String(b.dataset.rs === rs));
}

// the topmost item still on screen: the anchor for a change nobody clicked (a roam)
// The first story or pointer on screen below the chrome, copies included; a sliver of one (under
// 24px) is not what the reader is looking at. A recompose hides some rows and takes others out
// (`gone`): the anchor skips those for the next one that stays, and falls back to the day's
// header when nothing below stays (review F2, 2026-09-25).
function topItem(gone = new Set()) {
  if (!main) return null;
  const bar = document.querySelector('.bar');
  const top = bar && matchMedia('(min-width:700px)').matches ? bar.getBoundingClientRect().bottom : 0;
  let first = null;
  for (const el of main.querySelectorAll('[data-story], [data-ptr]')) {
    if (el.closest('[hidden]')) continue;
    const r = el.getBoundingClientRect();
    if (!r.height || r.bottom <= top + Math.min(24, r.height)) continue;
    if (!gone.has(el)) return el;
    first = first || el;
  }
  const sec = first && first.closest('section');
  return sec ? sec.querySelector('header') : null;
}

export function initBoard({ prefs, record, adopt = () => {} }) {
  refill = createRefill(main, { isRead, beatOk, adopt });
  refill.snapshot();                              // All's front: the pick from the read set at load
  // The roamed read set can land after first paint. All's pick is then taken once more, at the
  // first roam only (2026-09-25, option ii: the local set is usually right, so holding every load
  // for the network would cost more), and only if the reader has not interacted with the page
  // since load (owner ruling after review F1): a pointer, key, focus, wheel or touch anywhere, or
  // a scroll of their own. A reader's scroll moves the content with it (the top item shifts by
  // exactly what the page scrolled); scroll anchoring, the browser keeping a #fragment or a
  // restored position in view, and anchored() move the page to keep content where it was, so
  // they do not count. After a reload or a history step the browser restores a scroll position,
  // and on a #fragment load it scrolls to the fragment, both by load: there scrolls count from two
  // frames after load; after a plain navigation, from the first. The #fragment itself is the
  // reader pointing at a place, and a recompose could hide the very row it names: it counts.
  let roamedOnce = false, touched = !!location.hash, mark = null;
  const TOUCH = ['pointerdown', 'keydown', 'focusin', 'wheel', 'touchstart'];
  const markTop = () => { const el = topItem(); return el && { el, top: el.getBoundingClientRect().top, y: scrollY }; };
  const onScroll = () => {
    if (!mark) return;                            // before load settles: the browser's scroll
    const { el, top, y } = mark, moved = scrollY - y;
    const withIt = el.isConnected && !el.closest('[hidden]') && Math.abs(el.getBoundingClientRect().top - top + moved) < 2;
    if (Math.abs(moved) >= 2 && withIt) touch(); else mark = markTop();
  };
  function quiet() { removeEventListener('scroll', onScroll); for (const t of TOUCH) document.removeEventListener(t, touch, true); }
  function touch() { touched = true; quiet(); }
  if (!touched) {
    for (const t of TOUCH) document.addEventListener(t, touch, { capture: true, passive: true });
    addEventListener('scroll', onScroll, { passive: true });
  }
  // restore the stored selection; held keys survive (R37)
  const seed = (p) => {
    active.clear();
    held = p.topics.filter((k) => !chipKeys.has(k));
    p.topics.forEach((k) => { if (chipKeys.has(k)) active.add(k); });
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
  for (const b of segs) {
    b.addEventListener('click', () => { rs = b.dataset.rs; paintControls(); apply(); persist(); });
  }
  // keep a keyboard-focused chip wholly inside the scrolling strip
  for (const strip of document.querySelectorAll('.bar .beats')) {
    strip.addEventListener('focusin', (ev) => {
      const c = ev.target.closest('.chip');
      if (!c) return;
      const r = c.getBoundingClientRect(), b = strip.getBoundingClientRect(), pad = 16;
      if (r.left < b.left + pad) strip.scrollLeft -= b.left + pad - r.left;
      else if (r.right > b.right - pad) strip.scrollLeft += r.right - (b.right - pad);
    });
  }
  if (main) {
    main.addEventListener('click', (e) => {
      const rb = e.target.closest('.readbtn');
      if (rb) {                                   // explicit toggle: honours an active filter at once
        const el = rb.closest('[data-story]');
        setRead(el, !isRead(el));
        paint();
        if (announce) announce.textContent = isRead(el) ? 'Marked read' : 'Marked unread';
        if (rs) {
          apply();
          // the ✓ left with its item: the focus goes to the filter, unless it is somewhere else
          const f = document.activeElement;
          if ((el.hidden || !el.isConnected) && (!f || f === document.body || el.contains(f))) { const on = segs.find((b) => b.getAttribute('aria-pressed') === 'true'); if (on) on.focus(); }
        }
        return;
      }
      const a = e.target.closest('.hl a');       // opening the article reads it: dims, never re-filters
      if (a) { const el = a.closest('[data-story]'); if (el && !isRead(el)) { setRead(el, true); paint(); } }
    });
    main.addEventListener('auxclick', (e) => {   // a middle-click "open in background tab" counts too
      if (e.button !== 1) return;
      const a = e.target.closest('.hl a');
      if (a) { const el = a.closest('[data-story]'); if (el && !isRead(el)) { setRead(el, true); paint(); } }
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
    // a roamed selection re-filters without throwing the reader down the page (old bug R2)
    remotePrefs(p) { seed(p); paintControls(); anchored(topItem(), apply); },
    remoteRead,
    roamed() {
      const first = !roamedOnce;
      roamedOnce = true;
      if (first && !touched) onScroll();          // a scroll whose event has not fired yet counts too
      quiet();
      if (!first || touched) { remoteRead(); return; }
      const gone = refill.retake();
      anchored(topItem(rs ? undefined : gone), () => { paint(); apply(); });
    },
  };
}
