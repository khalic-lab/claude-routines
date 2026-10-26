// Homepage entry (assets/js/*.js, plain ES modules, stamped by the import map in head.html).
// Each feature starts on its own; the head's `.js` gate stays only if this reaches the end.
import { fb, initSession, on } from './session.js';
import { onExternalChange } from './state.js';
import { current, record, initPrefs } from './prefs.js';
import { initBoard } from './board.js';
import { initFold } from './fold.js';
import { initDiscuss, prepare } from './discuss.js';
import { initVotes } from './votes.js';
import { initOg, watchSlots } from './og.js';
import { initFresh } from './fresh.js';
import { initDialogs } from './dialogs.js';
import { initPropose } from './propose.js';

const root = document.documentElement;
root.classList.add('js');
if (!fb().enabled) root.classList.add('fb-off');  // feedback kill switch: votes and propose go

initDialogs();
initFold();
initDiscuss();                                     // every Discuss href, from the text on the page
// a copy the front adopts gets its image slots watched and its Discuss href built
const board = initBoard({ prefs: current(), record, adopt: (el) => { watchSlots(el); prepare(el); } });
on('roam', board.roamed);                          // the first one may recompose All's front (C8)
onExternalChange(board.remoteRead);                // another tab marked something read
initSession();
initPrefs(board.remotePrefs);
initVotes();
initOg();
initFresh();
initPropose();
if (new URLSearchParams(location.search).has('probe')) import('./probe.js').then((m) => m.default());

window.__siteReady = true;
