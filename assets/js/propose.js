// "Propose a brief": /propose {topic, detail, surface:'web'} on the passkey session. Stands alone
// so it answers even on an empty board. Uses the page's session check (token AND reader) and
// drops a dead session on 401 (old bug B4); hidden with the feedback kill switch (old bug B5).
import { fb, session, authHeaders, sessionDied, nudgeSignIn } from './sync.js';

export function initPropose() {
  const form = document.querySelector('.propose__form');
  if (!form) return;
  if (!fb().enabled) { form.closest('.propose').hidden = true; return; }
  const topic = form.querySelector('[name=topic]');
  const detail = form.querySelector('[name=detail]');
  const msg = form.querySelector('.propose__msg');
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const t = (topic.value || '').trim();
    if (!t) { topic.focus(); return; }
    const s = session();
    if (!s) { msg.textContent = 'sign in to propose — Sync, in the filter bar'; nudgeSignIn('sign in with your passkey to propose'); return; }
    msg.textContent = 'sending…';
    fetch(fb().url + '/propose', {
      method: 'POST', headers: authHeaders(s, true),
      body: JSON.stringify({ topic: t, detail: (detail.value || '').trim(), surface: 'web' }),
    }).then((r) => {
      if (r.status === 401) { msg.textContent = 'session expired — sign in again'; sessionDied('session expired — sign in again'); return; }
      if (r.ok) { msg.textContent = 'proposed — thanks ✓'; topic.value = ''; detail.value = ''; }
      else msg.textContent = 'failed (' + r.status + ')';
    }).catch(() => { msg.textContent = 'offline — try again later'; });
  });
}
