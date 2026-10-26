// Native dialogs for every [data-dialog] opener: How this works, Sync, and the phone's two
// bottom sheets (beats, days). Without script the How-this-works opener is a plain #hiw link
// and CSS shows that dialog in flow (:target). A tap on the scrim closes; a day link in the
// days sheet closes it on its way to the day.
export function initDialogs() {
  for (const opener of document.querySelectorAll('[data-dialog]')) {
    opener.addEventListener('click', (e) => {
      const d = document.getElementById(opener.dataset.dialog);
      if (!d || !d.showModal) return;
      e.preventDefault();
      if (!d.open) d.showModal();
    });
  }
  for (const d of document.querySelectorAll('dialog')) {
    d.addEventListener('click', (e) => {
      if (e.target === d) { d.close(); return; }   // the backdrop lands on the dialog itself
      if (e.target.closest('.daylist a')) d.close();
    });
  }
  if (location.hash === '#hiw') {
    const d = document.getElementById('hiw');
    if (d && d.showModal && !d.open) d.showModal();
  }
}
