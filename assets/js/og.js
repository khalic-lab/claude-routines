// Article images: fill each reserved slot (.photo[data-og], only on front leads and features the
// builder marked `unfurl`) from og-proxy, lazily and cached per tab. A story with no image loses
// its slot. referrerPolicy and loading are set BEFORE src, so the request itself carries them
// (old bug B6 set them after the fetch had started).
const OG = 'https://og-proxy.khalic-lab.workers.dev/?url=';
const CACHE = 'homeOg:v2:';                      // sessionStorage; the value is a URL or "" (none)

function place(slot, src) {
  if (!src) { slot.hidden = true; return; }
  const img = new Image();
  img.alt = '';
  img.decoding = 'async';
  img.referrerPolicy = 'no-referrer';
  img.loading = 'lazy';
  img.onload = () => slot.classList.add('is-loaded');
  img.onerror = () => { slot.hidden = true; };
  img.src = src;
  slot.appendChild(img);
}
function fill(slot) {
  const url = slot.dataset.og;
  if (!url || slot.dataset.ogDone) return;
  slot.dataset.ogDone = '1';
  let host = '';
  try { host = new URL(url).hostname; } catch (e) { slot.hidden = true; return; }
  if (/(^|\.)(arxiv|doi)\.org$/.test(host)) { slot.hidden = true; return; }
  let cached = null;
  try { cached = sessionStorage.getItem(CACHE + url); } catch (e) { /* ignore */ }
  if (cached !== null) { place(slot, cached); return; }
  fetch(OG + encodeURIComponent(url)).then((r) => (r.ok ? r.json() : null)).then((j) => {
    const src = j && j.image ? j.image : '';
    try { sessionStorage.setItem(CACHE + url, src); } catch (e) { /* ignore */ }
    place(slot, src);
  }).catch(() => { slot.hidden = true; });
}

let io = null;

// observe every image slot under `root` (the page at start; a reserve card when the Unread refill
// first brings it in)
export function watchSlots(root) {
  const slots = [...root.querySelectorAll('.photo[data-og]')].filter((s) => !s.dataset.ogDone);
  if (!slots.length) return;
  if (!('IntersectionObserver' in window)) { slots.forEach((s) => { s.hidden = true; }); return; }
  if (!io) {
    io = new IntersectionObserver((es) => {
      for (const e of es) if (e.isIntersecting) { io.unobserve(e.target); fill(e.target); }
    }, { rootMargin: '600px 0px' });
  }
  slots.forEach((s) => io.observe(s));
}

export function initOg() {
  watchSlots(document);
}
