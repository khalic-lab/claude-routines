// Native dialogs for every [data-dialog] opener. Without script the How-this-works opener is a
// plain #hiw link and CSS shows the dialog in flow (:target).
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
    // a click on the backdrop lands on the dialog itself (its box is an inner element)
    d.addEventListener('click', (e) => { if (e.target === d) d.close(); });
  }
  if (location.hash === '#hiw') {
    const d = document.getElementById('hiw');
    if (d && d.showModal && !d.open) d.showModal();
  }
}
