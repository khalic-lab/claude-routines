// The board: read state, the beat and read filters, and the honest counts.
//
// Items are the elements that carry a read id (data-story): front cards, index rows and
// editorials. Pointer rows ([data-ptr]) stand in a day for an item lifted to the front and follow
// that item. Filtering only sets the `hidden` attribute; it never reorders or measures anything.
import { READ_KEY, UNREAD_KEY, readMap, unreadMap, save } from './store.js';
import { noteLocalRead } from './sync.js';
import { anchored } from './fold.js';

const main = document.getElementById('main');
export const items = main ? [...main.querySelectorAll('[data-story]')] : [];
const ptrs = main ? [...main.querySelectorAll('[data-ptr]')] : [];
const byId = new Map();
const storiesByEdition = new Map();
for (const el of items) {
  const id = el.dataset.story;
  if (!byId.has(id)) byId.set(id, []);
  byId.get(id).push(el);
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

// Reading dims and never hides, moves or folds (owner ruling, 2026-07-26): paint touches the
// read class and the ✓ state only.
export function paint() {
  for (const el of items) {
    const r = isRead(el);
    el.classList.toggle('is-read', r);
    const b = el.querySelector('.readbtn');
    if (b) {
      b.setAttribute('aria-pressed', String(r));
      b.title = r ? 'mark as unread' : 'mark as read';
    }
  }
  for (const p of ptrs) {
    const t = (byId.get(p.dataset.ptr) || [])[0];
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
  let shown = 0;
  for (const el of items) { const m = matches(el); el.hidden = !m; if (m) shown++; }
  for (const p of ptrs) { const t = (byId.get(p.dataset.ptr) || [])[0]; p.hidden = !t || t.hidden; }
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
      if (!n.dataset.orig) n.dataset.orig = n.textContent;
      const total = +n.dataset.total;
      const v = sec.querySelectorAll('.rows > [data-story]:not([hidden]), .rows > [data-ptr]:not([hidden])').length;
      n.textContent = filtering ? v + ' of ' + total + ' ' + (total === 1 ? 'story' : 'stories') + ' shown' : n.dataset.orig;
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
}

function paintControls() {
  for (const c of chips) {
    const k = c.dataset.topic;
    c.setAttribute('aria-pressed', String(k ? active.has(k) : active.size === 0));
  }
  for (const b of segs) b.setAttribute('aria-pressed', String(b.dataset.rs === rs));
}

// the topmost item still on screen: the anchor for a change nobody clicked (a roam)
function topItem() {
  const bar = document.querySelector('.bar');
  const top = bar && matchMedia('(min-width:700px)').matches ? bar.getBoundingClientRect().bottom : 0;
  return items.find((el) => !el.hidden && el.getBoundingClientRect().bottom > top) || null;
}

export function initBoard({ prefs, record }) {
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
          if (el.hidden) { const on = segs.find((b) => b.getAttribute('aria-pressed') === 'true'); if (on) on.focus(); }
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

  return {
    // a roamed selection re-filters without throwing the reader down the page (old bug R2)
    remotePrefs(p) { seed(p); paintControls(); anchored(topItem(), apply); },
    remoteRead() { anchored(topItem(), () => { paint(); if (rs) apply(); }); },
  };
}
