// The read model (C6, C11). Items are the elements that carry a read id (data-story): front
// cards, index rows and editorials; a reserve copy stands in for its story and reads as it.
// An editorial is read when ticked, OR when every story of its (date, stream) edition is read;
// an explicit tick or un-tick wins over the rule and the un-tick is stored (homeUnread:v1).
// Derived at paint time, never stored as read. Reading dims and never hides, moves or folds
// (R3): paint touches the read class and the ✓ state only.
import { READ_KEY, UNREAD_KEY, readMap, unreadMap, save } from './state.js';
import { noteLocalRead } from './session.js';

export const isEditorial = (el) => el.dataset.zone === 'editorial';

// every story of an edition, from the live items (each story has exactly one live element)
const byEdition = new Map();
for (const el of document.querySelectorAll('#main [data-story]')) {
  if (isEditorial(el)) continue;
  if (!byEdition.has(el.dataset.edition)) byEdition.set(el.dataset.edition, []);
  byEdition.get(el.dataset.edition).push(el);
}
const ruleSaysRead = (el) => {
  const mine = byEdition.get(el.dataset.edition) || [];
  return mine.length > 0 && mine.every((s) => !!readMap[s.dataset.story]);
};

export function isRead(el) {
  const id = el.dataset.story;
  if (!isEditorial(el)) return !!readMap[id];
  if (readMap[id]) return true;
  if (unreadMap[id]) return false;
  return ruleSaysRead(el);
}
export function setRead(el, v) {
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
export function paintEl(el) {
  const r = isRead(el);
  el.classList.toggle('is-read', r);
  const b = el.querySelector('.readbtn');
  if (b) {
    b.setAttribute('aria-pressed', String(r));
    b.title = r ? 'mark as unread' : 'mark as read';
  }
}
