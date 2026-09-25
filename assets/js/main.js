// Homepage entry (assets/js/*.js, plain ES modules, stamped by the import map in head.html).
// Each feature starts on its own; the head's `.js` gate stays only if this reaches the end.
import { fb, initSync, on } from './sync.js';
import { onExternalChange } from './store.js';
import { current, record, initPrefs } from './prefs.js';
import { initBoard } from './board.js';
import { initFold } from './fold.js';
import { initVotes } from './votes.js';
import { initOg, watchSlots } from './og.js';
import { initFresh } from './fresh.js';
import { initDialogs } from './dialog.js';
import { initPropose } from './propose.js';

const root = document.documentElement;
root.classList.add('js');
if (!fb().enabled) root.classList.add('fb-off');  // feedback kill switch: votes and propose go

initDialogs();
initFold();
const board = initBoard({ prefs: current(), record, adopt: watchSlots });
on('roam', board.remoteRead);
onExternalChange(board.remoteRead);                // another tab marked something read
initSync();
initPrefs(board.remotePrefs);
initVotes();
initOg();
initFresh();
initPropose();
if (new URLSearchParams(location.search).has('probe')) import('./probe.js').then((m) => m.default());

window.__siteReady = true;
