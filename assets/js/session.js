// The passkey session and the read-state roam through the feedback Worker (R25: opt-in; signed
// out = zero requests). Local first: homeRead:v1 is the paint source; syncState:v1 is the
// last-writer-wins shadow the Worker merges (per sid, higher ts wins, a tie keeps local). Only
// st- ids travel. Request and response shapes are the contract (C15), field for field.
import { READ_KEY, SYNC_KEY, SESSION_KEY, ST_RE, readMap, syncMap, save, drop } from './state.js';

export function fb() {
  return window.__FB || { enabled: true, url: 'https://feedback-sink.khalic-lab.workers.dev' };
}
// the same validator /admin/ uses: a token AND a reader
export function session() {
  try {
    const s = JSON.parse(localStorage.getItem(SESSION_KEY) || 'null');
    return (s && typeof s.token === 'string' && s.token && s.reader) ? s : null;
  } catch (e) { return null; }
}
export function authHeaders(s, json) {
  const h = { 'Authorization': 'Bearer ' + s.token };
  if (json) h['Content-Type'] = 'application/json';
  return h;
}

const hooks = { signin: [], roam: [], change: [] };
export function on(name, fn) { hooks[name].push(fn); }
const emit = (name) => { for (const fn of hooks[name]) fn(); };

// ---- the dialog; every UI function is a no-op without it or without WebAuthn
const dlg = document.getElementById('sync');
const btns = [...document.querySelectorAll('.syncbtn[data-dialog="sync"]')];
const q = (sel) => (dlg ? dlg.querySelector(sel) : null);
const ui = dlg && btns.length && window.PublicKeyCredential ? {
  out: q('.sync__out'), inn: q('.sync__in'), who: q('.sync__who'), status: q('.sync__status'),
  signin: q('.sync__signin'), setupT: q('.sync__setup-t'), setup: q('.sync__setup'),
  invite: q('.sync__invite'), create: q('.sync__create'), signout: q('.sync__signout'),
} : null;

export function say(m) { if (ui) ui.status.textContent = m || ''; }
function paintUi() {
  if (!ui) return;
  const s = session();
  for (const b of btns) { b.textContent = s ? 'Synced · ' + s.reader : 'Sync'; b.classList.toggle('is-in', !!s); }
  ui.out.hidden = !!s;
  ui.inn.hidden = !s;
  ui.who.textContent = s ? 'Signed in as ' + s.reader : '';
}
// open the dialog and say why (from a vote or the propose form)
export function nudgeSignIn(msg) {
  if (!ui) return;
  if (!dlg.open) dlg.showModal();
  say(msg);
}

// ---- read-state shadow, push and pull
let pushTimer = 0, pushPending = false;
export function noteLocalRead(sid, v) {
  if (!ST_RE.test(sid)) return;                 // editorials (ed-) and slug ids never roam
  syncMap[sid] = { ts: Date.now(), v: v ? 1 : 0 };
  save(SYNC_KEY, syncMap);
  schedulePush();
}
function schedulePush() {                       // debounced: a burst of marking is one POST
  if (!session()) return;
  pushPending = true;
  clearTimeout(pushTimer);
  pushTimer = setTimeout(flushPush, 30000);
}
function flushPush() {                          // also on tab-hide/pagehide: keepalive fetch, never
  if (!pushPending) return;                     // sendBeacon (it cannot carry Authorization)
  const s = session();
  if (!s) { pushPending = false; return; }
  pushPending = false;
  clearTimeout(pushTimer);
  fetch(fb().url + '/readstate', {
    method: 'POST', keepalive: true, headers: authHeaders(s, true),
    body: JSON.stringify({ state: syncMap }),
  }).then((r) => {
    if (r.status === 401) sessionDied('session expired — sign in again');
    else if (!r.ok) say('read sync failed (' + r.status + ')');
  }).catch(() => { pushPending = true; });     // offline: retry on the next flush trigger
}
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') flushPush(); });
addEventListener('pagehide', flushPush);

function mergeRemote(state) {
  let dirty = false;
  for (const k of Object.keys(readMap)) {       // seed shadows for reads made before sync existed
    if (ST_RE.test(k) && !syncMap[k]) { syncMap[k] = { ts: readMap[k], v: 1 }; dirty = true; }
  }
  for (const k of Object.keys(state)) {
    const r = state[k];
    if (!ST_RE.test(k) || !r || typeof r.ts !== 'number' || (r.v !== 0 && r.v !== 1)) continue;
    const l = syncMap[k];
    if (l && l.ts >= r.ts) continue;            // local newer, or a tie: keep; the push carries it
    syncMap[k] = { ts: r.ts, v: r.v };
    if (r.v === 1) readMap[k] = r.ts; else delete readMap[k];
    dirty = true;
  }
  if (dirty) { save(SYNC_KEY, syncMap); save(READ_KEY, readMap); }
  emit('roam');
}
function pullRemote() {
  const s = session();
  if (!s) return;
  fetch(fb().url + '/readstate', { headers: authHeaders(s) })
    .then((r) => {
      if (r.status === 401) { sessionDied('session expired — sign in again'); return null; }
      return r.ok ? r.json() : null;
    })
    .then((j) => {
      if (!j) return;
      mergeRemote(j.state && typeof j.state === 'object' ? j.state : {});
      schedulePush();                           // one push back; the server merge is idempotent
    }).catch(() => {});
}

// ---- session lifecycle
export function dropSession(reason) {           // an explicit sign-out passes no reason
  drop(SESSION_KEY);
  pushPending = false;
  clearTimeout(pushTimer);
  paintUi();
  emit('change');
  if (reason) nudgeSignIn(reason);
}
// every 401 lands here; a session under a minute old gets a pass (a just-issued token can 401
// off an eventually consistent KV read at another edge)
export function sessionDied(reason) {
  const s = session();
  if (s && typeof s.at === 'number' && Date.now() - s.at < 60000) return;
  dropSession(reason);
}
function adoptSession(j) {
  save(SESSION_KEY, { token: j.session, reader: j.reader, at: Date.now() });
  paintUi();
  say('');
  if (dlg && dlg.open) dlg.close();
  emit('change');
  pullRemote();
  emit('signin');
}

// ---- WebAuthn (the same payloads as /admin/)
function b64uToBuf(s) {
  s = String(s).replace(/-/g, '+').replace(/_/g, '/');
  while (s.length % 4) s += '=';
  const bin = atob(s), b = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) b[i] = bin.charCodeAt(i);
  return b.buffer;
}
function bufToB64u(buf) {
  const b = new Uint8Array(buf);
  let s = '';
  for (let i = 0; i < b.length; i++) s += String.fromCharCode(b[i]);
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
function authFetch(path, body) {
  return fetch(fb().url + path, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}),
  }).then((r) => r.json().catch(() => ({})).then((j) => ({ ok: r.ok, status: r.status, j })));
}
const errMsg = (err) => (err && err.name === 'NotAllowedError' ? 'cancelled or timed out'
  : (err && err.message) ? err.message : 'failed');
const extensions = (cred) => (cred.getClientExtensionResults ? cred.getClientExtensionResults() : {});

function doLogin() {
  say('waiting for your passkey…');
  authFetch('/auth/login-options', {}).then((res) => {
    if (!res.ok) throw new Error('server error (' + res.status + ')');
    const o = res.j;
    o.challenge = b64uToBuf(o.challenge);
    for (const c of (o.allowCredentials || [])) c.id = b64uToBuf(c.id);
    return navigator.credentials.get({ publicKey: o });
  }).then((cred) => {
    if (!cred) throw new Error('no credential');
    const r = cred.response;
    const payload = {
      id: cred.id, rawId: bufToB64u(cred.rawId), type: cred.type, clientExtensionResults: extensions(cred),
      response: {
        clientDataJSON: bufToB64u(r.clientDataJSON),
        authenticatorData: bufToB64u(r.authenticatorData),
        signature: bufToB64u(r.signature),
      },
    };
    if (r.userHandle) payload.response.userHandle = bufToB64u(r.userHandle);
    return authFetch('/auth/login', { response: payload });
  }).then((res) => {
    if (!res.ok || !res.j || !res.j.ok) throw new Error(res.status === 403 ? 'passkey not recognized' : 'sign-in failed (' + res.status + ')');
    adoptSession(res.j);
  }).catch((err) => say(errMsg(err)));
}
function doRegister(invite) {
  say('creating your passkey…');
  authFetch('/auth/register-options', { invite }).then((res) => {
    if (!res.ok) throw new Error(res.status === 403 ? 'invite not accepted' : 'server error (' + res.status + ')');
    const o = res.j;
    o.challenge = b64uToBuf(o.challenge);
    o.user.id = b64uToBuf(o.user.id);
    for (const c of (o.excludeCredentials || [])) c.id = b64uToBuf(c.id);
    return navigator.credentials.create({ publicKey: o });
  }).then((cred) => {
    if (!cred) throw new Error('no credential');
    const r = cred.response;
    const payload = {
      id: cred.id, rawId: bufToB64u(cred.rawId), type: cred.type, clientExtensionResults: extensions(cred),
      response: { clientDataJSON: bufToB64u(r.clientDataJSON), attestationObject: bufToB64u(r.attestationObject) },
    };
    if (r.getTransports) payload.response.transports = r.getTransports();
    return authFetch('/auth/register', { invite, response: payload });
  }).then((res) => {
    if (!res.ok || !res.j || !res.j.ok) throw new Error(res.status === 403 ? 'not accepted — invite or challenge expired' : 'setup failed (' + res.status + ')');
    adoptSession(res.j);
  }).catch((err) => say(errMsg(err)));
}

export function initSession() {
  if (ui) {                                     // no WebAuthn: the Sync control stays hidden
    for (const b of btns) b.hidden = false;
    ui.signin.addEventListener('click', doLogin);
    ui.setupT.addEventListener('click', () => {
      const show = ui.setup.hidden;
      ui.setup.hidden = !show;
      ui.setupT.setAttribute('aria-expanded', String(show));
      if (show) ui.invite.focus();
    });
    ui.create.addEventListener('click', () => {
      const code = (ui.invite.value || '').trim();
      if (!code) { say('enter the invite code'); ui.invite.focus(); return; }
      doRegister(code);
    });
    ui.invite.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); ui.create.click(); } });
    ui.signout.addEventListener('click', () => { dropSession(); say('signed out'); });
    dlg.addEventListener('close', () => say(''));
    paintUi();
  }
  pullRemote();
}
