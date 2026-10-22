// Discuss: a prefilled Claude conversation from a story, an editorial or a day edition.
//
// The link works without script: the template writes a short prompt into each href (the
// headline and its primary source; a day's headlines). With script every Discuss href is
// rebuilt ONCE, at load, and again when the refill adopts a reserve copy (the same `adopt` hook
// og.js uses for image slots), from the text already on the page: headline, deck, summary, why,
// the flags, every source with its label, desk and day. Built once rather than on an event, so
// a keyboard activation, a middle-click and "copy link" all see the same href the suite reads.
// Nothing is fetched. Before this the template wrote the whole prompt into every href: 140 KB
// of a 586 KB homepage, twice for every story that also sat in a reserve <template>.
//
// The URL's origin and path come from the template's own href, so no host is named here
// (tools/tests/test_frontend_static.py allows only the two Workers in assets/js).
const CAP = { summary: 600, why: 300, editorial: 2500 };

// visible text, without the screen-reader suffixes and the "Why it matters" label
function plain(el, drop = '.vh') {
  if (!el) return '';
  const c = el.cloneNode(true);
  c.querySelectorAll(drop).forEach((x) => x.remove());
  return c.textContent.replace(/\s+/g, ' ').trim();
}
const cap = (s, n) => (s.length > n ? s.slice(0, n - 1).replace(/\s+\S*$/, '') + '…' : s);

// desk and day of an item, from its edition and the page's own labels
function where(item) {
  const ed = item.dataset.edition || '', date = ed.slice(0, 10), stream = ed.slice(11);
  const day = document.querySelector(`section.day[data-date="${date}"]`);
  const desk = plain(item.querySelector('.ptag b')) || plain(day && day.querySelector(`.ptag[data-stream="${stream}"] b`))
    || plain(item.querySelector('.row__desk', '.vh')) || stream;
  const when = plain(item.querySelector('.fday')) || plain(day && day.querySelector('.day__h time')) || date;
  return { desk, when };
}
function sourcesOf(item) {
  const list = [...item.querySelectorAll('.srcs a')].map((a) => ({ label: plain(a), url: a.href }));
  if (list.length) return list;
  const a = item.querySelector('.hl a');
  return a ? [{ label: plain(item.querySelector('.src__dom')) || a.hostname, url: a.href }] : [];
}
const flagsOf = (item) => [...item.querySelectorAll('.flag')].map((f) => plain(f));

function storyPrompt(item) {
  const { desk, when } = where(item);
  const lines = ["Let's discuss this news story.", '', 'Headline: ' + plain(item.querySelector('.hl'))];
  const deck = plain(item.querySelector('.deck'));
  if (deck) lines.push('Deck: ' + deck);
  const sum = plain(item.querySelector('.sum'));
  if (sum) lines.push('Summary: ' + cap(sum, CAP.summary));
  const why = plain(item.querySelector('.why'), '.vh, .why__l');
  if (why) lines.push('Why it matters: ' + cap(why, CAP.why));
  lines.push('Desk: ' + desk + ', ' + when);
  const flags = flagsOf(item);
  if (flags.length) lines.push("The desk's own flags on it: " + flags.join(', '));
  const srcs = sourcesOf(item);
  if (srcs.length) { lines.push('Sources:'); for (const s of srcs) lines.push('- ' + s.label + ': ' + s.url); }
  lines.push('', 'Start by separating what the sources establish from what is still open, then ask me which angle I want to pursue.');
  return lines.join('\n');
}
function editorialPrompt(item) {
  const { desk, when } = where(item);
  const paras = [...item.querySelectorAll('.ed__body p')].map((p) => plain(p)).filter(Boolean);
  return [
    "Let's discuss this editorial. An AI wrote it as the " + desk + " desk's view of its week, an opinion synthesised from that week's sourced stories, not reporting.",
    '', 'Title: ' + plain(item.querySelector('.ed__hl')), 'Desk: ' + desk + ', ' + when,
    'Text:', cap(paras.join('\n\n'), CAP.editorial),
    '', 'Start by listing the claims it makes and which of them would need a source, then ask me which I want to test.',
  ].join('\n');
}
function dayPrompt(section) {
  const label = plain(section.querySelector('.day__h'));
  const desks = [...section.querySelectorAll('.day__cov .ptag')].map((t) => plain(t)).join('; ');
  const lines = ["Let's discuss the " + label + ' edition' + (desks ? ' (' + desks + ')' : '') + '.', '', 'Stories, biggest first:'];
  let n = 0;
  for (const el of section.querySelectorAll('.rows > [data-story], .rows > [data-ptr]')) {
    const item = el.dataset.ptr ? document.getElementById('c-' + el.dataset.ptr) : el;
    if (!item) continue;
    const src = sourcesOf(item)[0], flags = flagsOf(item);
    lines.push(`${++n}. ${plain(item.querySelector('.hl'))}` + (src ? ' — ' + src.url : '') + (flags.length ? ' [' + flags.join(', ') + ']' : ''));
  }
  lines.push('', 'Start with what connects these stories and which of them matters most, then ask me where to go deeper.');
  return lines.join('\n');
}

function build(a) {
  const kind = a.dataset.discuss;
  let prompt = '';
  if (kind === 'day') prompt = dayPrompt(a.closest('section.day'));
  else {
    const item = a.closest('[data-story]');
    if (!item) return;
    prompt = kind === 'editorial' ? editorialPrompt(item) : storyPrompt(item);
  }
  let u;
  try { u = new URL(a.getAttribute('href'), location.href); } catch (e) { return; }
  a.href = u.origin + u.pathname + '?q=' + encodeURIComponent(prompt);
}

// rebuild every Discuss href under `root` (the page at start; a reserve copy when adopted)
export function prepare(root) {
  for (const a of root.querySelectorAll('a.discuss[data-discuss]')) build(a);
}
export function initDiscuss() {
  prepare(document);
}
