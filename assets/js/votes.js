// Per-story votes: /submit {brief, vote, reason, story_id, surface:'home'}, on the passkey
// session. Pressing the active thumb again retracts it (vote 0). One reason box per item, shared by
// both thumbs; a down-vote asks for the why, an up-vote does not. Voting is not a read.
import { fb, session, authHeaders, sessionDied, nudgeSignIn } from './sync.js';
import { anchored } from './fold.js';

const announce = document.getElementById('announce');

function note(item, m) {
  const n = item.querySelector('.vnote');
  if (n) n.textContent = m;
  if (announce) announce.textContent = m;
}
function post(item, vote, reason) {
  if (!fb().enabled) return;
  const s = session();
  if (!s) { note(item, 'sign in to vote'); nudgeSignIn('sign in with your passkey to vote'); return; }
  note(item, 'sending…');
  fetch(fb().url + '/submit', {
    method: 'POST', headers: authHeaders(s, true),
    body: JSON.stringify({ brief: item.dataset.edition, vote, reason: (reason || '').trim(),
      story_id: item.dataset.story || null, surface: 'home' }),
  }).then((r) => {
    if (r.status === 401) { sessionDied('session expired — sign in again'); note(item, 'sign in to vote'); return; }
    note(item, r.ok ? (vote === 0 ? 'withdrawn ✓' : 'thanks ✓') : 'failed (' + r.status + ')');
  }).catch(() => note(item, 'offline — try later'));
}
function reasonBox(item) {
  let box = item.querySelector('.rzn');
  if (box) return box;
  box = document.createElement('span');
  box.className = 'rzn';
  box.innerHTML = '<input type="text" maxlength="500"><button type="button">send</button>';
  const input = box.querySelector('input');
  const send = () => {
    const why = (input.value || '').trim();
    anchored(item, () => { box.hidden = true; });
    if (!why) return;
    const on = item.querySelector('.vote[aria-pressed="true"]');
    if (on) post(item, +on.dataset.v, why);      // retracted before sending: nothing to attach to
  };
  box.querySelector('button').addEventListener('click', send);
  input.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); send(); } });
  item.querySelector('.acts').after(box);
  return box;
}

export function initVotes() {
  const main = document.getElementById('main');
  if (!main) return;
  main.addEventListener('click', (e) => {
    const b = e.target.closest('.vote');
    if (!b) return;
    const item = b.closest('[data-story]');
    const was = b.getAttribute('aria-pressed') === 'true';
    anchored(item, () => {
      item.querySelectorAll('.vote').forEach((x) => x.setAttribute('aria-pressed', 'false'));
      const old = item.querySelector('.rzn');
      if (old) old.hidden = true;
      if (was) return;
      b.setAttribute('aria-pressed', 'true');
      const up = +b.dataset.v === 1;
      const box = reasonBox(item), input = box.querySelector('input');
      input.value = '';                           // shared box: never carry text across polarities
      input.placeholder = up ? 'what stood out? (optional)' : 'why? (optional)';
      input.setAttribute('aria-label', up ? 'Reason for thumbs-up (optional)' : 'Reason for thumbs-down (optional)');
      box.hidden = false;
    });
    if (was) { post(item, 0); return; }
    post(item, +b.dataset.v);
    if (+b.dataset.v !== 1) { const i = item.querySelector('.rzn input'); if (i) i.focus(); }
  });
}
