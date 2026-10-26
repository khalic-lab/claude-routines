// The front's composition (C7, C9, C10). The pick: the first four UNREAD entries of the
// builder's front.reserve, in reserve order, the lead slot to the first of them with importance
// 3 (else the first); the Desk's view is the first unread editorial of front.desk_reserve.
// Under Unread the pick is live. Under All it is taken ONCE, at load, from the read set the
// page opened with (beats aside; they filter as always): a partly-read front is filled up to
// four with read stories in reserve order after the unread ones, the lead staying unread; with
// nothing unread it is the builder's front, dimmed. Read shows the builder's front. One pick,
// three uses.
//
// Nothing here ranks. The reserve's later entries are <template>s in the front section, out of
// the board's items, counts and ids until needed; a copy is made once and moved in and out. A
// story is on the page once (no pointer rows since round 3): a promoted reserve story's live
// day row hides; a builder-front story off the front gets its real row from the <template
// data-front-row> at its rank, and the builder's Desk's view its day article from <template
// data-front-ed>. The day header counts what is on the front as composed.
//
// A node taken out of the document drops the focus (and a caret) to <body> (C14), so a list is
// reconciled, never rebuilt: what leaves is removed, what arrives is inserted around what stays,
// and a list already in place is not touched.
function reconcile(box, want) {
  if (!box) return;
  const keep = new Set(want);
  for (const el of [...box.children]) if (!keep.has(el)) el.remove();
  want.forEach((el, i) => { if (box.children[i] !== el) box.insertBefore(el, box.children[i] || null); });
}
const esc = (s) => (window.CSS && CSS.escape ? CSS.escape(s) : s);

export function createFront(main, { isRead, beatOk, adopt }) {
  const front = main && main.querySelector('section.front');
  const none = { compose: () => [], copies: () => [], snapshot() {}, retake: () => new Set(), onFront: () => new Set() };
  if (!front) return none;
  const top = front.querySelector('.fcards--top');
  const rest = front.querySelector('.fcards--rest');
  const desk = front.querySelector('.desk');
  const list = (v) => (v || '').split(' ').filter(Boolean);
  const reserve = list(front.dataset.reserve);
  const deskReserve = list(front.dataset.deskReserve);
  const live = new Map([...front.querySelectorAll('li.fc[data-story]')].map((c) => [c.dataset.story, c]));
  const defaults = [...(top ? top.children : []), ...(rest ? rest.children : [])];
  const deskLabel = desk && desk.querySelector('.desk__lbl');
  const deskDefault = desk && desk.querySelector('article.ed');
  const copies = new Map();
  const q = (sel, root = main) => root.querySelector(sel);
  const tpl = (attr, sid) => q(`template[${attr}="${esc(sid)}"]`);

  function fromTemplate(attr, sid) {
    const key = attr + sid;
    if (copies.has(key)) return copies.get(key);
    const t = tpl(attr, sid);
    if (!t) return null;
    const el = t.content.firstElementChild.cloneNode(true);
    copies.set(key, el);
    adopt(el);
    return el;
  }
  const card = (sid) => live.get(sid) || fromTemplate('data-reserve-card', sid);
  // a reserve story's live day row; a builder-front story's row is its template copy
  const rowOf = (sid) => (live.has(sid) ? copies.get('data-front-row' + sid) : q(`#r-${esc(sid)}`));
  // an editorial's read state and beats come from its live element: the desk's, or its day's
  const edState = (sid) => (deskDefault && deskDefault.dataset.story === sid ? deskDefault
    : q(`section.day article.ed[data-story="${esc(sid)}"]`));
  // a day's "<Desk> desk's view →" link follows its editorial: to the front copy while it is
  // shown there, to the builder desk's day article while that one is off the front
  const dayLinks = [...main.querySelectorAll('section.day .day__links a.jump[data-ed]')];
  function pointDayLinks(shown) {
    for (const a of dayLinks) {
      const sid = a.dataset.ed;
      const home = deskDefault && sid === deskDefault.dataset.story;
      const on = sid === shown;
      const href = '#' + (on ? (home ? '' : 'desk-') : (home ? 'day-' : '')) + sid;
      if (a.getAttribute('href') !== href) a.setAttribute('href', href);
      const vh = a.querySelector('.vh');
      if (on && !vh) a.insertAdjacentHTML('beforeend', '<span class="vh"> (on the front)</span>');
      if (!on && vh) vh.remove();
    }
  }

  // the pick (C10)
  function pick(active) {
    const out = [];
    for (const sid of reserve) {
      const el = card(sid);
      if (el && !isRead(el) && beatOk(el, active)) out.push(el);
      if (out.length === 4) break;
    }
    const lead = out.find((el) => el.dataset.imp === '3') || out[0];
    return lead ? [lead, ...out.filter((el) => el !== lead)] : [];
  }
  function deskPick(active) {
    if (!deskDefault) return null;
    const sid = deskReserve.find((s) => { const st = edState(s); return st && !isRead(st) && beatOk(st, active); });
    return (sid && sid !== deskDefault.dataset.story && fromTemplate('data-reserve-desk', sid)) || deskDefault;
  }
  // All's composition (C7): the unread pick padded with read stories in reserve order; with
  // nothing unread the builder's front
  let all = { cards: defaults, desk: deskDefault };
  function take() {
    const cards = pick(new Set());
    if (!cards.length) return { cards: defaults, desk: deskPick(new Set()) };
    for (const sid of reserve) {
      if (cards.length >= 4) break;
      const el = card(sid);
      if (el && isRead(el) && !cards.includes(el)) cards.push(el);
    }
    return { cards, desk: deskPick(new Set()) };
  }
  function snapshot() { all = take(); }
  // what placing `next` hides or takes out, against the page now: cards and the Desk's view
  // leaving the front, the day rows of promoted stories, the builder-front rows and the desk's
  // day article going back to the front. A recompose must not anchor on any of them (C8).
  function leaving(next) {
    const out = new Set(), keep = new Set(next.cards);
    for (const c of [...(top ? top.children : []), ...(rest ? rest.children : [])]) if (!keep.has(c)) out.add(c);
    for (const c of next.cards) { const row = rowOf(c.dataset.story); if (row && row.isConnected) out.add(row); }
    const cur = desk && desk.querySelector('article.ed');
    if (cur && next.desk && cur !== next.desk) out.add(cur);
    if (next.desk && deskDefault) {
      const day = next.desk === deskDefault ? copies.get('data-front-ed' + deskDefault.dataset.story) : edState(next.desk.dataset.story);
      if (day && day.isConnected) out.add(day);
    }
    return out;
  }
  // the first roamed read set: All's pick once more; returns what that takes off the page
  function retake() { const next = take(), gone = leaving(next); all = next; return gone; }

  let shown = new Set();
  function place(cards, ed) {
    reconcile(top, cards.slice(0, 1));
    reconcile(rest, cards.slice(1));
    if (desk && deskDefault) reconcile(desk, [deskLabel, ed].filter(Boolean));
    shown = new Set(cards.map((c) => c.dataset.story));
    // a promoted reserve story: its live day row hides (the filter pass unhid it, board.js)
    for (const el of cards) {
      if (live.has(el.dataset.story)) continue;
      const row = q(`#r-${esc(el.dataset.story)}`);
      if (row) row.hidden = true;
    }
    // a builder-front story off the front is a real row again, at its rank
    for (const sid of live.keys()) {
      const t = tpl('data-front-row', sid);
      if (!t) continue;
      const row = fromTemplate('data-front-row', sid);
      if (shown.has(sid)) { if (row.isConnected) row.remove(); } else if (t.nextElementSibling !== row) t.after(row);
    }
    if (!deskDefault) return;
    const home = ed === deskDefault;
    const t = tpl('data-front-ed', deskDefault.dataset.story);
    if (t) {
      const back = fromTemplate('data-front-ed', deskDefault.dataset.story);
      if (home) { if (back.isConnected) back.remove(); } else if (t.nextElementSibling !== back) t.after(back);
    }
    if (!home) { const day = edState(ed.dataset.story); if (day) day.hidden = true; }
    pointDayLinks(ed.dataset.story);
  }

  // mode: 'unread' (the live pick), 'all' (the load-time pick), 'read' (the builder's front)
  function compose(mode, active) {
    const cards = mode === 'unread' ? pick(active) : mode === 'all' ? all.cards : defaults;
    place(cards, mode === 'unread' ? deskPick(active) : mode === 'all' ? all.desk : deskDefault);
    return cards;
  }
  return { compose, snapshot, retake, copies: () => [...copies.values()], onFront: () => shown };
}
