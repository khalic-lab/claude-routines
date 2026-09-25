// Beat + read-filter preferences: topicPrefs:v1 {topics, rs, ts}, local first, roamed through
// the Worker's /prefs as ONE statement of intent (whole-object LWW by ts; the Worker re-serializes
// exactly these three fields and rejects more than 50 topics). Topics with no chip today are
// carried through by the caller ("held"), never dropped.
import { PREFS_KEY, load, save } from './store.js';
import { fb, session, authHeaders, sessionDied, say, on } from './sync.js';

const TOPIC_CAP = 50;
export const validRs = (v) => (v === 'unread' || v === 'read' ? v : '');

let prefs = { topics: [], rs: '', ts: 0 };
const stored = load(PREFS_KEY, null);
if (stored && Array.isArray(stored.topics)) {     // older values lack rs: coerce, keep the rest
  prefs = { topics: stored.topics.slice(), rs: validRs(stored.rs), ts: typeof stored.ts === 'number' ? stored.ts : 0 };
}
export const current = () => prefs;

let onRemote = () => {};
let timer = 0, pending = false;

export function record(topics, rs) {             // every chip / read-filter press
  const uniq = topics.filter((k, i, a) => a.indexOf(k) === i).slice(0, TOPIC_CAP);
  prefs = { topics: uniq, rs: validRs(rs), ts: Date.now() };
  save(PREFS_KEY, prefs);
  push();
}
function push() {
  // B8: never push an untouched default (ts 0). The Worker stamps a 0 ts as "now", and that
  // empty default then beat a real selection another device made earlier.
  if (!session() || !prefs.ts) return;
  pending = true;
  clearTimeout(timer);
  timer = setTimeout(flush, 1500);
}
function flush() {
  if (!pending) return;
  const s = session();
  if (!s) { pending = false; return; }
  pending = false;
  clearTimeout(timer);
  fetch(fb().url + '/prefs', {
    method: 'POST', keepalive: true, headers: authHeaders(s, true),
    body: JSON.stringify({ topics: prefs.topics, rs: prefs.rs, ts: prefs.ts }),
  }).then((r) => {
    if (r.status === 401) { sessionDied('session expired — sign in again'); return; }
    if (!r.ok) { pending = true; say('beat sync failed (' + r.status + ')'); }
  }).catch(() => { pending = true; });
}
function merge(remote) {
  if (!remote || !Array.isArray(remote.topics) || typeof remote.ts !== 'number') return;
  if (remote.ts <= prefs.ts) return;             // local newer, or a tie: keep; the push carries it
  prefs = { topics: remote.topics.slice(), rs: validRs(remote.rs), ts: remote.ts };
  save(PREFS_KEY, prefs);
  onRemote(prefs);
}
function pull() {
  const s = session();
  if (!s) return;
  fetch(fb().url + '/prefs', { headers: authHeaders(s) })
    .then((r) => {
      if (r.status === 401) { sessionDied('session expired — sign in again'); return null; }
      return r.ok ? r.json() : null;
    })
    .then((j) => {
      if (!j) return;
      if (j.prefs) merge(j.prefs);
      push();                                    // a later sign-in carries a local choice up
    }).catch(() => {});
}

export function initPrefs(applyRemote) {
  onRemote = applyRemote;
  on('signin', pull);
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') flush(); });
  addEventListener('pagehide', flush);
  pull();
}
