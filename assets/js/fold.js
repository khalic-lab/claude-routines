// More / Less. The fold is presentation, never a crop (C4): the markup carries every word, CSS
// hides a folded body only under the `.js` gate (C5), and nothing here persists or reads.
import { anchored } from './anchor.js';

function setOpen(item, btn, open) {
  item.classList.toggle('is-folded', !open);
  item.classList.toggle('is-open', open);
  btn.setAttribute('aria-expanded', String(open));
  btn.querySelector('span').textContent = open ? 'Less' : 'More';
}

export function initFold() {
  const main = document.getElementById('main');
  if (!main) return;
  main.addEventListener('click', (e) => {
    const btn = e.target.closest('.more');
    if (!btn) return;
    const item = btn.closest('[data-story]');
    anchored(btn, () => setOpen(item, btn, item.classList.contains('is-folded')));
  });
}
