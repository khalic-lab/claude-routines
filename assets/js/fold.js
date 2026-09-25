// More / Less. The fold is presentation, never a crop: the markup carries every word, CSS hides a
// folded body only under the `.js` gate, and nothing here persists or counts as a read.

// Run a height-changing mutation and keep the reader's eye still: measure the anchor, mutate,
// pay the difference back. Browser scroll anchoring protects content above the viewport, not the
// element being looked at.
export function anchored(el, fn) {
  const before = el ? el.getBoundingClientRect().top : 0;
  fn();
  if (!el) return;
  const after = el.getBoundingClientRect().top;
  if (after !== before) scrollBy(0, after - before);
}

function setOpen(item, btn, open) {
  item.classList.toggle('is-folded', !open);
  item.classList.toggle('is-open', open);       // reader-opened, as opposed to boot-open
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
