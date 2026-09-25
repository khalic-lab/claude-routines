// Reader state in localStorage. The keys and their shapes are a contract with every reader's
// browser (and, for syncState/topicPrefs, with the feedback Worker): never rename, reshape or
// reuse one. Retired names stay retired: siteKey, homeOg:v1:, autoPreview:v2:.
//
//   homeRead:v1    {<sid>: <ms>}              presence = read; stories and editorial ticks
//   syncState:v1   {<st-sid>: {ts, v:0|1}}    the /readstate shadow; st- ids only (the Worker
//                                             drops anything else, so ed- ids are pruned here)
//   topicPrefs:v1  {topics, rs, ts}           beats + read filter, roamed via /prefs (prefs.js)
//   syncSession:v1 {token, reader, at}        passkey session, shared with /admin/ (sync.js)
//   homeUnread:v1  {<ed-sid>: <ms>}           NEW 2026-09-24, local only: an explicit un-tick of
//                                             an editorial that the edition rule would call read
export const READ_KEY = 'homeRead:v1';
export const SYNC_KEY = 'syncState:v1';
export const PREFS_KEY = 'topicPrefs:v1';
export const SESSION_KEY = 'syncSession:v1';
export const UNREAD_KEY = 'homeUnread:v1';
export const ST_RE = /^st-[0-9a-f]{12}$/;         // the Worker's SID_RE (feedback-sink worker.js)

const KEEP_MS = 45 * 864e5;                        // the feed spans ~14 days; 45 keeps maps bounded

export function load(key, fallback) {
  try {
    const v = JSON.parse(localStorage.getItem(key) || 'null');
    return v == null ? fallback : v;
  } catch (e) { return fallback; }
}
export function save(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* private mode, quota */ }
}
export function drop(key) {
  try { localStorage.removeItem(key); } catch (e) { /* ignore */ }
}
// a corrupt value must neither brick the page nor be written back
const objectOr = (v) => (v && typeof v === 'object' && !Array.isArray(v) ? v : {});

export const readMap = objectOr(load(READ_KEY, {}));
export const unreadMap = objectOr(load(UNREAD_KEY, {}));
export const syncMap = objectOr(load(SYNC_KEY, {}));

(function prune() {
  const cut = Date.now() - KEEP_MS;
  let r = false, u = false, s = false;
  for (const k in readMap) if (!(readMap[k] > cut)) { delete readMap[k]; r = true; }
  for (const k in unreadMap) if (!(unreadMap[k] > cut)) { delete unreadMap[k]; u = true; }
  for (const k in syncMap) {
    if (!ST_RE.test(k) || !syncMap[k] || !(syncMap[k].ts > cut)) { delete syncMap[k]; s = true; }
  }
  if (r) save(READ_KEY, readMap);
  if (u) save(UNREAD_KEY, unreadMap);
  if (s) save(SYNC_KEY, syncMap);
  drop('siteKey');                                 // the retired shared write secret
})();
