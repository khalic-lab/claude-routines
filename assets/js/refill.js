// The Unread refill (2026-09-25). Under the Unread filter the front shows the first four UNREAD
// entries of the builder's front.reserve that match the active beats, in reserve order: the lead
// slot takes the first of them with importance 3 (or the first), the rest keep their order. The
// Desk's view is the first unread, matching editorial of front.desk_reserve. Under All and Read
// the builder's front comes back exactly: read stories dim in place and never move (2026-07-26).
//
// This file never ranks. The reserve's later entries are <template>s in the front section, so
// they stay out of the board's item list, its counts and its ids until one is needed; a copy is
// made once and moved in and out. A promoted story's day row hides and its pointer (which follows
// the card) shows; the board's apply() calls compose() after filtering and before the pointers.
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
const placed = (box, want) => !box || (box.children.length === want.length && want.every((el, i) => box.children[i] === el));

export function createRefill(main, { isRead, beatOk, adopt }) {
  const front = main && main.querySelector('section.front');
  if (!front) return { compose() { return []; }, copies: () => [] };
  const top = front.querySelector('.fcards--top');
  const rest = front.querySelector('.fcards--rest');
  const desk = front.querySelector('.desk');
  const list = (v) => (v || '').split(' ').filter(Boolean);
  const reserve = list(front.dataset.reserve);
  const deskReserve = list(front.dataset.deskReserve);
  const live = new Map([...front.querySelectorAll('li.fc[data-story]')].map((c) => [c.dataset.story, c]));
  const defaults = { top: top ? [...top.children] : [], rest: rest ? [...rest.children] : [] };
  const deskLabel = desk && desk.querySelector('.desk__lbl');
  const deskDefault = desk && desk.querySelector('article.ed');
  const copies = new Map();
  const q = (sel, root = main) => root.querySelector(sel);
  const esc = (s) => (window.CSS && CSS.escape ? CSS.escape(s) : s);

  function fromTemplate(attr, sid) {
    if (copies.has(attr + sid)) return copies.get(attr + sid);
    const t = q(`template[${attr}="${esc(sid)}"]`, front);
    if (!t) return null;
    const el = t.content.firstElementChild.cloneNode(true);
    copies.set(attr + sid, el);
    adopt(el);
    return el;
  }
  const card = (sid) => live.get(sid) || fromTemplate('data-reserve-card', sid);
  // an editorial's read state and beats come from its live element: the desk's, or its day's
  const edState = (sid) => (deskDefault && deskDefault.dataset.story === sid ? deskDefault
    : q(`section.day article.ed[data-story="${esc(sid)}"]`));
  // a day's "→ <Desk> desk's view" link follows its editorial to the front copy (review F3)
  const dayLinks = deskReserve.map((sid) => [sid, q(`section.day .day__links a[href="#${esc(sid)}"]`)]).filter(([, a]) => a);
  const pointDayLinks = (shown) => { for (const [sid, a] of dayLinks) a.setAttribute('href', '#' + (sid === shown ? 'desk-' : '') + sid); };

  const deskWant = (el) => [deskLabel, el].filter(Boolean);

  function compose(unread, active) {
    if (!unread) {
      if (!(placed(top, defaults.top) && placed(rest, defaults.rest) && (!desk || !deskDefault || placed(desk, deskWant(deskDefault))))) {
        reconcile(top, defaults.top);
        reconcile(rest, defaults.rest);
        if (desk && deskDefault) reconcile(desk, deskWant(deskDefault));
        pointDayLinks(null);
      }
      return [...defaults.top, ...defaults.rest];
    }
    const pick = [];
    for (const sid of reserve) {
      const el = card(sid);
      if (el && !isRead(el) && beatOk(el, active)) pick.push(el);
      if (pick.length === 4) break;
    }
    const lead = pick.find((el) => el.dataset.imp === '3') || pick[0];
    const others = pick.filter((el) => el !== lead);
    reconcile(top, lead ? [lead] : []);
    reconcile(rest, others);
    for (const el of pick) {
      if (live.has(el.dataset.story)) continue;
      const row = q(`#r-${esc(el.dataset.story)}`);
      if (row) row.hidden = true;                  // its pointer shows instead
    }
    if (desk && deskDefault) {
      const chosen = deskReserve.find((sid) => { const st = edState(sid); return st && !isRead(st) && beatOk(st, active); });
      const copy = chosen && chosen !== deskDefault.dataset.story ? fromTemplate('data-reserve-desk', chosen) : null;
      reconcile(desk, deskWant(copy || deskDefault));
      pointDayLinks(copy ? chosen : null);
      const day = copy && edState(chosen);
      if (day) day.hidden = true;
    }
    return lead ? [lead, ...others] : others;
  }
  return { compose, copies: () => [...copies.values()] };
}
