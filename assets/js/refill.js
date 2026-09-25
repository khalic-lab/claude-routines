// The front's composition (2026-09-25). The page shows the first four UNREAD entries of the
// builder's front.reserve, in reserve order: the lead slot takes the first of them with
// importance 3 (or the first), the rest keep their order; the Desk's view is the first unread
// editorial of front.desk_reserve. Under Unread that pick is live: it follows every read and beat.
// Under All it is taken ONCE, at load, from the read set the page opened with (beats aside, which
// then filter as they always did) and never again: a read in the session only dims (the
// 2026-07-26 ruling, amended by the owner on 2026-09-25). With nothing unread, All is the
// builder's front, dimmed. Read always shows the builder's front. One pick, three uses.
//
// This file never ranks. The reserve's later entries are <template>s in the front section, so
// they stay out of the board's item list, its counts and its ids until one is needed; a copy is
// made once and moved in and out. A story is on the page once: a promoted story's day row hides
// and its pointer (which follows the card) shows; a builder-front story off the front gets its
// real day row back from a <template> next to its pointer, and the builder's Desk's view its day
// article. The board's apply() calls compose() after filtering and before the pointers.
//
// A node taken out of the document drops the focus (and a caret) to <body> (review F1,
// 2026-09-25), so a list is reconciled, never rebuilt: what leaves is removed, what arrives is
// inserted around what stays, and a list already in place is not touched at all.
function reconcile(box, want) {
  if (!box) return;
  const keep = new Set(want);
  for (const el of [...box.children]) if (!keep.has(el)) el.remove();
  want.forEach((el, i) => { if (box.children[i] !== el) box.insertBefore(el, box.children[i] || null); });
}

export function createRefill(main, { isRead, beatOk, adopt }) {
  const front = main && main.querySelector('section.front');
  if (!front) return { compose() { return []; }, copies: () => [], snapshot() {} };
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
  const esc = (s) => (window.CSS && CSS.escape ? CSS.escape(s) : s);

  function fromTemplate(attr, sid) {
    if (copies.has(attr + sid)) return copies.get(attr + sid);
    const t = q(`template[${attr}="${esc(sid)}"]`);
    if (!t) return null;
    const el = t.content.firstElementChild.cloneNode(true);
    copies.set(attr + sid, el);
    adopt(el);
    return el;
  }
  const card = (sid) => live.get(sid) || fromTemplate('data-reserve-card', sid);
  const ptrOf = (sid) => q(`section.day [data-ptr="${esc(sid)}"]:not([data-reserve-ptr])`);
  // an editorial's read state and beats come from its live element: the desk's, or its day's
  const edState = (sid) => (deskDefault && deskDefault.dataset.story === sid ? deskDefault
    : q(`section.day article.ed[data-story="${esc(sid)}"]`));
  // a day's "→ <Desk> desk's view" link follows its editorial: to the front copy while one is
  // shown (review F3), to the builder desk's day article while that one is off the front
  const dayLinks = deskReserve.map((sid) => [sid, q(`section.day .day__links a[href="#${esc(sid)}"]`)]).filter(([, a]) => a);
  function pointDayLinks(shown) {
    for (const [sid, a] of dayLinks) {
      const home = deskDefault && sid === deskDefault.dataset.story;
      const on = sid === shown;
      const href = '#' + (on ? (home ? '' : 'desk-') : (home ? 'day-' : '')) + sid;
      if (a.getAttribute('href') !== href) a.setAttribute('href', href);
      const vh = a.querySelector('.vh');
      if (on && !vh) a.insertAdjacentHTML('beforeend', '<span class="vh"> (on the front)</span>');
      if (!on && vh) vh.remove();
    }
  }
  const deskWant = (el) => [deskLabel, el].filter(Boolean);

  // the pick: the first four unread reserve entries on the beats, lead first; the Desk's view
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
  // All's composition, taken at load (and once more at the first roamed read set, board.js):
  // with nothing unread, the builder's front; a Desk's view with nothing unread keeps its own
  let all = { cards: defaults, desk: deskDefault };
  function snapshot() {
    const cards = pick(new Set());
    all = { cards: cards.length ? cards : defaults, desk: deskPick(new Set()) };
  }

  function place(cards, ed) {
    reconcile(top, cards.slice(0, 1));
    reconcile(rest, cards.slice(1));
    if (desk && deskDefault) reconcile(desk, deskWant(ed));
    const on = new Set(cards.map((c) => c.dataset.story));
    for (const el of cards) {
      if (live.has(el.dataset.story)) continue;
      const row = q(`#r-${esc(el.dataset.story)}`);
      if (row) row.hidden = true;                  // its pointer shows instead
    }
    // a builder-front story off the front is a real row again, right after its (hidden) pointer
    for (const sid of live.keys()) {
      const row = fromTemplate('data-front-row', sid), ptr = ptrOf(sid);
      if (!row || !ptr) continue;
      if (on.has(sid)) { if (row.isConnected) row.remove(); } else if (ptr.nextElementSibling !== row) ptr.after(row);
    }
    if (!deskDefault) return;
    const home = ed === deskDefault, back = fromTemplate('data-front-ed', deskDefault.dataset.story), bptr = ptrOf(deskDefault.dataset.story);
    if (back && bptr) { if (home) { if (back.isConnected) back.remove(); } else if (bptr.nextElementSibling !== back) bptr.after(back); }
    if (!home) { const day = edState(ed.dataset.story); if (day) day.hidden = true; }
    pointDayLinks(ed.dataset.story);
  }

  // mode: 'unread' (live pick), 'all' (the load-time pick), 'read' (the builder's front)
  function compose(mode, active) {
    const cards = mode === 'unread' ? pick(active) : mode === 'all' ? all.cards : defaults;
    place(cards, mode === 'unread' ? deskPick(active) : mode === 'all' ? all.desk : deskDefault);
    return cards;
  }
  return { compose, snapshot, copies: () => [...copies.values()] };
}
