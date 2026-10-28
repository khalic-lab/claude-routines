// Keeping the reader's eye still through a change the page makes itself.

// What the page has scrolled by itself since load, summed (C8): a scroll of the page's own is
// not the reader's interaction, and board.js takes it off its count.
let own = 0;
export const ownScroll = () => own;
export function scrollOwn(dy) {
  const y = scrollY;
  scrollBy(0, dy);
  own += scrollY - y;                            // what the browser let it scroll (the ends clamp)
}

// Run a height-changing mutation and pay the difference back: measure the anchor, mutate,
// scroll by what it moved. Browser scroll anchoring protects content above the viewport, not
// the element being looked at; when it fires inside `fn` (content changed above the viewport)
// the payback undoes it, and the sum counts the net of the two, which is what the page moved.
export function anchored(el, fn) {
  const y0 = scrollY, before = el ? el.getBoundingClientRect().top : 0;
  fn();
  if (el) {
    const after = el.getBoundingClientRect().top;
    if (after !== before) scrollBy(0, after - before);
  }
  own += scrollY - y0;
}

// Where the page's own content starts: under the bar when it is pinned at the top (700–1279px),
// else the viewport's top.
export function chromeTop() {
  const bar = document.querySelector('.bar');
  const pinned = bar && getComputedStyle(bar).display !== 'none' && matchMedia('(min-width: 700px)').matches;
  return pinned ? bar.getBoundingClientRect().bottom : 0;
}

// The topmost item on screen below the chrome: the anchor for a change nobody clicked. A
// sliver of one (under 24px) is not what the reader is looking at. A recompose hides some items
// and takes others out (`gone`): skip those for the next one that stays, and fall back to the
// section header when nothing below stays.
export function topItem(gone = new Set()) {
  const main = document.getElementById('main');
  if (!main) return null;
  const top = chromeTop();
  let first = null;
  for (const el of main.querySelectorAll('[data-story]')) {
    if (el.closest('[hidden]')) continue;
    const r = el.getBoundingClientRect();
    if (!r.height || r.bottom <= top + Math.min(24, r.height)) continue;
    if (!gone.has(el)) return el;
    first = first || el;
  }
  const sec = first && first.closest('section');
  return sec ? sec.querySelector('header') : null;
}
