// "New edition" on resume. A tab restored from the back/forward cache, or shown again after ten
// minutes hidden, asks edition.json (no-store) for the current build stamp; if a writer has
// published since, an in-flow bar offers a reload. Never reloads by itself.
const AWAY_MS = 10 * 60 * 1000;

export function initFresh() {
  const bar = document.querySelector('.notice');
  const meta = document.querySelector('meta[name="build-stamp"]');
  if (!bar || !meta || !bar.dataset.src) return;
  const stamp = meta.content;
  bar.querySelector('button').addEventListener('click', () => location.reload());
  const check = () => {
    fetch(bar.dataset.src + '?t=' + Date.now(), { cache: 'no-store' })
      .then((r) => (r.ok ? r.json() : null))
      .then((j) => { if (j && j.build_stamp && j.build_stamp !== stamp) bar.hidden = false; })
      .catch(() => {});
  };
  let hiddenAt = 0;
  addEventListener('pageshow', (e) => { if (e.persisted) check(); });
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') hiddenAt = Date.now();
    else if (hiddenAt && Date.now() - hiddenAt >= AWAY_MS) { hiddenAt = 0; check(); }
  });
}
