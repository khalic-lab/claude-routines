// More / Less. The fold is presentation, never a crop (C4): the markup carries every word, CSS
// hides a folded body only under the `.js` gate (C5), and nothing here persists or reads.
import { anchored, chromeTop, scrollOwn } from './anchor.js';

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
    const open = item.classList.contains('is-folded');
    // Opening: the head stays where the reader read it; the fold grows below it and Less sits
    // at its end (the controls close the item). Closing: the head comes back under the chrome
    // when the reader is below it (the fold they were in has gone); else nothing moves.
    anchored(item, () => setOpen(item, btn, open));
    if (!open) {
      const top = item.getBoundingClientRect().top, floor = chromeTop() + 8;
      if (top < floor) scrollOwn(top - floor);
    }
  });
}
