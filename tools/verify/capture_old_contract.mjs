// One-off: record what the OLD homepage (the themed _layouts/home.html, before the 2026-09-24 rewrite)
// writes to storage and sends to the Workers, so the rewrite's contract checks compare against real
// old-code output rather than a shape written down after the fact.
//
//   node capture_old_contract.mjs http://127.0.0.1:4001/claude-routines/   > fixtures/old-contract.json
//
// Both Workers are stubbed with page.route(); nothing leaves the machine. Kept in the tree as the
// provenance of fixtures/old-contract.json (the old page it drove no longer exists after the swap).
import { chromium } from 'playwright';

const BASE = process.argv[2] || 'http://127.0.0.1:4001/claude-routines/';
const FB = 'https://feedback-sink.khalic-lab.workers.dev';
const OG = 'https://og-proxy.khalic-lab.workers.dev';
const TOKEN = 'ab'.repeat(32);

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1024, height: 900 } });
const page = await ctx.newPage();
const requests = [];
await ctx.route(FB + '/**', async (route) => {
  const r = route.request(), u = new URL(r.url());
  const body = r.postData();
  requests.push({ method: r.method(), path: u.pathname, auth: (r.headers()['authorization'] || '').replace(TOKEN, '<token>'),
    contentType: r.headers()['content-type'] || null, keepalive: null, body: body ? JSON.parse(body) : null });
  const json = u.pathname === '/readstate' && r.method() === 'GET' ? { state: {} }
    : u.pathname === '/prefs' && r.method() === 'GET' ? { prefs: null }
    : { ok: true };
  await route.fulfill({ status: 200, contentType: 'application/json', headers: { 'access-control-allow-origin': '*' }, body: JSON.stringify(json) });
});
await ctx.route(OG + '/**', (route) => route.fulfill({ status: 200, contentType: 'application/json',
  headers: { 'access-control-allow-origin': '*' }, body: JSON.stringify({ image: null }) }));

await page.addInitScript(([t]) => {
  if (!sessionStorage.getItem('__seeded')) {
    localStorage.setItem('syncSession:v1', JSON.stringify({ token: t, reader: 'tester', at: Date.now() - 3600e3 }));
    sessionStorage.setItem('__seeded', '1');
  }
}, [TOKEN]);
await page.goto(BASE);
await page.waitForTimeout(500);

const picked = await page.evaluate(() => {
  const cards = [...document.querySelectorAll('#folioGrid > li.fcard')];
  const sidOf = c => c.dataset.story || (c.querySelector('.fcard__fb') || {}).dataset?.story || '';
  const stories = cards.filter(c => !c.classList.contains('fcard--ed'));
  const ed = cards.find(c => c.classList.contains('fcard--ed'));
  const s1 = stories[0], s2 = stories[5];
  s1.querySelector('.fcard__read').click();
  s2.querySelector('.fcard__read').click();
  ed.querySelector('.fcard__read').click();
  // a beat, then Unread
  const topic = (s1.dataset.topics || '').split(' ')[0];
  document.querySelector(`.folio-filters .ff-chip[data-topic="${topic}"]`).click();
  document.querySelector('.folio-filters .ff-rbtn[data-rs="unread"]').click();
  // vote on a third story + reason
  const v = stories[8], box = v.querySelector('.fcard__fb');
  box.querySelector('.ffb-t[data-v="-1"]').click();
  const inp = box.querySelector('.ffb-rzn input'); inp.value = 'reason text';
  box.querySelector('.ffb-rzn button').click();
  return { read: [sidOf(s1), sidOf(s2), sidOf(ed)], topic, vote: { story: box.dataset.story, brief: box.dataset.brief } };
});
// propose
await page.evaluate(() => {
  document.querySelector('.propose__d').open = true;
  const f = document.querySelector('.propose__form');
  f.querySelector('[name=topic]').value = 'A topic';
  f.querySelector('[name=detail]').value = 'Some detail';
  f.requestSubmit();
});
await page.waitForTimeout(300);
// flush the debounced pushes the way a tab switch does
await page.evaluate(() => {
  Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'hidden' });
  document.dispatchEvent(new Event('visibilitychange'));
});
await page.waitForTimeout(500);
const storage = await page.evaluate(() => {
  const o = {};
  for (const k of ['homeRead:v1', 'syncState:v1', 'topicPrefs:v1', 'syncSession:v1']) o[k] = JSON.parse(localStorage.getItem(k));
  return o;
});
storage['syncSession:v1'].token = '<token>';
await browser.close();
console.log(JSON.stringify({ captured: new Date().toISOString(), page: 'old _layouts/home.html @ ' + (process.env.REV || '?'),
  picked, storage, requests }, null, 1));
