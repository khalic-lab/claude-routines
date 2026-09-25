// Passkey sign-in and read-state roaming through the feedback Worker. Signed out = zero
// requests. Local-first: homeRead:v1 stays the paint source; syncState:v1 is the LWW shadow the
// Worker merges (per sid, higher ts wins, a tie keeps local). Only st- ids ever travel.
import { READ_KEY, SYNC_KEY, SESSION_KEY, ST_RE, readMap, syncMap, save, drop } from './store.js';

export function fb() {
  return window.__FB || { enabled: true, url: 'https://feedback-sink.khalic-lab.workers.dev' };
}
// The same validator /admin/ uses (token AND reader); propose.js uses this one too (B4).
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
const emit = (name, arg) => hooks[name].forEach((fn) => fn(arg));

// ---- UI (the #sync dialog); every function is a no-op without it or without WebAuthn
const dlg = document.getElementById('sync');
const btn = document.querySelector('.syncbtn[data-dialog="sync"]');
const $ = (sel) => (dlg ? dlg.querySelector(sel) : null);
const ui = dlg && btn && window.PublicKeyCredential ? {
  out: $('.sync__out'), inn: $('.sync__in'), who: $('.sync__who'), status: $('.sync__status'),
  signin: $('.sync__signin'), setupT: $('.sync__setup-t'), setup: $('.sync__setup'),
  invite: $('.sync__invite'), create: $('.sync__create'), signout: $('.sync__signout'),
} : null;

export function say(m) { if (ui) ui.status.textContent = m || ''; }
function paintUi() {
  if (!ui) return;
  const s = session();
  btn.textContent = s ? 'Synced · ' + s.reader : 'Sync';
  btn.classList.toggle('is-in', !!s);
  ui.out.hidden = !!s;
  ui.inn.hidden = !s;
  ui.who.textContent = s ? 'Signed in as ' + s.reader : '';
}
// Open the dialog and say why. Called from inside click handlers (a vote, propose): a modal
// dialog has no outside-click listener to close it again on the same click (old bug B1).
export function nudgeSignIn(msg) {
  if (!ui) return;
  if (!dlg.open) dlg.showModal();
  say(msg);
}

// ---- read-state shadow + push/pull
let pushTimer = 0, pushPending = false;
export function noteLocalRead(sid, v) {
  if (!ST_RE.test(sid)) return;                 // editorials (ed-) and slug ids never roam (B2)
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
  for (const k in readMap) {                    // seed shadows for reads made before sync existed
    if (ST_RE.test(k) && !syncMap[k]) { syncMap[k] = { ts: readMap[k], v: 1 }; dirty = true; }
  }
  for (const k in state) {
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
  if (!s) return;                               // signed out: no sync traffic at all
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
// Every 401 lands here. A session younger than a minute gets a pass: a just-issued token can
// 401 off an eventually consistent KV read at another edge.
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

// ---- WebAuthn (same payloads as the old page and /admin/)
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

function doLogin() {
  say('waiting for your passkey…');
  authFetch('/auth/login-options', {}).then((res) => {
    if (!res.ok) throw new Error('server error (' + res.status + ')');
    const o = res.j;
    o.challenge = b64uToBuf(o.challenge);
    (o.allowCredentials || []).forEach((c) => { c.id = b64uToBuf(c.id); });
    return navigator.credentials.get({ publicKey: o });
  }).then((cred) => {
    if (!cred) throw new Error('no credential');
    const r = cred.response;
    const payload = {
      id: cred.id, rawId: bufToB64u(cred.rawId), type: cred.type,
      clientExtensionResults: cred.getClientExtensionResults ? cred.getClientExtensionResults() : {},
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
    (o.excludeCredentials || []).forEach((c) => { c.id = b64uToBuf(c.id); });
    return navigator.credentials.create({ publicKey: o });
  }).then((cred) => {
    if (!cred) throw new Error('no credential');
    const r = cred.response;
    const payload = {
      id: cred.id, rawId: bufToB64u(cred.rawId), type: cred.type,
      clientExtensionResults: cred.getClientExtensionResults ? cred.getClientExtensionResults() : {},
      response: { clientDataJSON: bufToB64u(r.clientDataJSON), attestationObject: bufToB64u(r.attestationObject) },
    };
    if (r.getTransports) payload.response.transports = r.getTransports();
    return authFetch('/auth/register', { invite, response: payload });
  }).then((res) => {
    if (!res.ok || !res.j || !res.j.ok) throw new Error(res.status === 403 ? 'not accepted — invite or challenge expired' : 'setup failed (' + res.status + ')');
    adoptSession(res.j);
  }).catch((err) => say(errMsg(err)));
}

export function initSync() {
  if (ui) {                                     // no WebAuthn: the Sync button stays hidden
    btn.hidden = false;
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
