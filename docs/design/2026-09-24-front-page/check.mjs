// B-prime checks. Run from /tmp/pw:  node <copy of this file>
// Geometry is measured with the sticky chrome (.bar, .mast) forced to position:static, i.e. at its
// flow position: a stuck bar paints over scrolled content by definition; what must hold is that its
// flow box reserves its own space.
import { chromium, webkit, devices } from 'playwright';
import fs from 'fs';
const D = '/private/tmp/claude-501/-Users-rflnogueira-code-claude-routines/85ed4036-6016-4695-807f-6d2a23ef1f57/scratchpad/design/B-prime';
const URL = 'file://' + D + '/mock.html';
const WIDTHS = [360, 390, 700, 768, 1024, 1280, 1440, 1600];
const STATES = ['default', 'expanded', 'unread-science', 'beat-sports', 'empty'];
const EXPECT_PERIODS = {             // (date) -> {stream: [start, end]} derived by hand from _posts/
  '2026-09-24': { news: ['2026-09-24', '2026-09-24'] },
  '2026-09-23': { science: ['2026-09-17', '2026-09-23'], news: ['2026-09-23', '2026-09-23'] },
  '2026-09-22': { 'ai-ml': ['2026-09-19', '2026-09-22'], news: ['2026-09-22', '2026-09-22'] },
  '2026-09-21': { news: ['2026-09-21', '2026-09-21'], sports: ['2026-09-15', '2026-09-21'] },
  '2026-09-20': { news: ['2026-09-20', '2026-09-20'] },
  '2026-09-19': { news: ['2026-09-19', '2026-09-19'], weekend: ['2026-09-13', '2026-09-19'] },
};

// ------------------------------------------------------------------ in-page helpers
const LIB = () => {
  const R = e => e.getBoundingClientRect();
  const vis = e => { const r = R(e); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
  const name = e => e.dataset.zone + (e.dataset.sid ? '#' + e.dataset.sid : '') + (e.dataset.ptr ? '>' + e.dataset.ptr : '') + (e.dataset.date ? '@' + e.dataset.date : '');
  const visibleItems = () => [...document.querySelectorAll('[data-sid]')].filter(vis);
  const chip = k => [...document.querySelectorAll('.chip')].find(c => c.dataset.topic === k && vis(c));
  const seg = r => document.querySelector(`.seg button[data-rs="${r}"]`);
  const ct = b => +b.querySelector('.ct').textContent;
  // largest blank vertical interval inside a front cell, plus uncovered width in partial flex lines
  const frontVoids = () => {
    const cells = [...document.querySelectorAll('.front .fc, .front .desk')].filter(vis);
    let max = 0; const per = [];
    for (const c of cells) {
      const blocks = c.classList.contains('desk')
        ? [...c.children, ...c.querySelectorAll('.ed > *')].filter(x => vis(x) && !x.classList.contains('ed'))
        : [...c.querySelector('article').children].filter(vis);
      const iv = blocks.map(b => [R(b).top, R(b).bottom]).sort((a, b) => a[0] - b[0]);
      const cr = R(c); let cur = cr.top, gap = 0;
      for (const [t, bt] of iv) { if (t > cur) gap = Math.max(gap, t - cur); cur = Math.max(cur, bt); }
      gap = Math.max(gap, cr.bottom - cur);
      per.push([c.id || 'desk', Math.round(gap)]); max = Math.max(max, gap);
    }
    for (const box of document.querySelectorAll('.front__top, .fcards--rest')) {
      if (!vis(box)) continue; const W = R(box).width; const lines = {};
      for (const k of [...box.children].filter(vis)) { const r = R(k); const t = Math.round(r.top); (lines[t] ||= { w: 0, h: 0 }); lines[t].w += r.width; lines[t].h = Math.max(lines[t].h, r.height); }
      for (const t in lines) if (lines[t].w < W - 2) { per.push(['partial-line', Math.round(lines[t].h)]); max = Math.max(max, lines[t].h); }
    }
    return { max: Math.round(max), per };
  };
  const hlSizes = () => [...document.querySelectorAll('.front .hl')].map(h => getComputedStyle(h).fontSize).join(',');
  const geometry = () => {
    const st = document.createElement('style'); st.id = 'flow'; st.textContent = '.bar,.mast{position:static!important}';
    document.head.appendChild(st);
    const inter = (a, b) => Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) * Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
    const parents = new Set([...document.querySelectorAll('[data-zone]')].map(e => e.parentElement));
    const overlaps = []; let pairs = 0; const inv = []; let groups = 0;
    for (const p of parents) {
      const kids = [...p.children].filter(c => c.dataset.zone && vis(c));
      for (let i = 0; i < kids.length; i++) for (let j = i + 1; j < kids.length; j++) {
        pairs++; const a = inter(R(kids[i]), R(kids[j]));
        if (a > 1) overlaps.push(`${name(kids[i])} x ${name(kids[j])} = ${Math.round(a)}px2`);
      }
      // DOM order == visual order; the control bar is chrome and may rest after main on phones (R28)
      if (kids.length < 2 || kids.some(k => k.dataset.zone === 'bar')) continue;
      groups++;
      for (let i = 0; i + 1 < kids.length; i++) {
        const a = R(kids[i]), b = R(kids[i + 1]);
        const ok = Math.abs(a.top - b.top) < 1 ? b.left >= a.left - .5 : b.top > a.top;
        if (!ok) inv.push(`${name(kids[i])} -> ${name(kids[i + 1])}`);
      }
    }
    const contain = []; let contained = 0;
    for (const sec of document.querySelectorAll('section[data-zone="day"],section[data-zone="front"]')) {
      if (!vis(sec)) continue; const s = R(sec);
      for (const c of sec.querySelectorAll('[data-zone]')) {
        if (!vis(c)) continue; contained++; const r = R(c);
        if (r.left < s.left - .5 || r.right > s.right + .5 || r.top < s.top - .5 || r.bottom > s.bottom + .5) contain.push(`${name(c)} outside ${name(sec)}`);
      }
    }
    const out = { overflow: document.documentElement.scrollWidth > innerWidth ? [`scrollWidth ${document.documentElement.scrollWidth} > ${innerWidth}`] : [],
      overlap: overlaps, containment: contain, order: inv, pairs, contained, groups };
    st.remove();
    return out;
  };
  // longest rendered line of an element's text, in characters (multicol-aware: a new top = a new line)
  const cpl = el => {
    const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); let max = 0, cur = 0, top = null; const rg = document.createRange();
    for (let n; (n = w.nextNode());) {
      if (n.parentElement.closest('.sr')) continue;
      for (let i = 0; i < n.length; i++) {
        rg.setStart(n, i); rg.setEnd(n, i + 1); const r = rg.getClientRects()[0]; if (!r) continue;
        if (top === null || Math.abs(r.top - top) > 3) { max = Math.max(max, cur); cur = 0; top = r.top; }
        cur++;
      }
    }
    return Math.max(max, cur);
  };
  // effective contrast of an element's text: opacity multiplied up the chain, composited on the nearest opaque background
  const rgb = s => (s.match(/[\d.]+/g) || []).map(Number);
  const lum = c => { const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }; return .2126 * f(c[0]) + .7152 * f(c[1]) + .0722 * f(c[2]); };
  const opacityOf = el => { let o = 1; for (let a = el; a; a = a.parentElement) o *= +getComputedStyle(a).opacity; return o; };
  const contrast = el => {
    const c = rgb(getComputedStyle(el).color), a = (c[3] ?? 1) * opacityOf(el);
    let bg = [255, 255, 255];
    for (let x = el; x; x = x.parentElement) { const b = rgb(getComputedStyle(x).backgroundColor); if (b.length && (b[3] ?? 1) >= .99) { bg = b; break; } }
    const m = c.slice(0, 3).map((v, i) => v * a + bg[i] * (1 - a)); const l1 = lum(m), l2 = lum(bg);
    return (Math.max(l1, l2) + .05) / (Math.min(l1, l2) + .05);
  };
  // every visible in-page link lands on something rendered (dialog triggers excluded: they open a modal)
  const deadLinks = () => [...document.querySelectorAll('a[href^="#"]:not([data-dialog])')].filter(vis).map(a => {
    const id = a.getAttribute('href').slice(1), t = document.getElementById(id);
    return t && vis(t) ? null : `"${a.textContent.trim().slice(0, 28)}" -> #${id}`;
  }).filter(Boolean);
  // a shown day header describes what it shows: its count == visible story rows + pointers, its tags == visible desks
  const dayMeta = () => {
    const bad = []; let days = 0;
    for (const sec of document.querySelectorAll('section.day')) {
      if (!vis(sec)) continue; days++;
      const num = parseInt(sec.querySelector('.day__n').textContent, 10);
      const v = [...sec.querySelectorAll('.rows > [data-sid], .rows > [data-ptr]')].filter(vis).length;
      if (num !== v) bad.push(`${sec.dataset.date} says ${num}, shows ${v}`);
      const tags = [...sec.querySelectorAll('.day__cov .ptag')].filter(vis).map(t => t.dataset.stream).sort().join();
      const desks = [...new Set([...sec.querySelectorAll('[data-edition]')].filter(vis).map(x => x.dataset.edition.slice(11)))].sort().join();
      if (tags !== desks) bad.push(`${sec.dataset.date} tags [${tags}] vs desks shown [${desks}]`);
    }
    return { bad, days };
  };
  // the focused control's ring: nonzero, inside every clipping ancestor, under no mask
  const focusRing = () => {
    const el = document.activeElement;
    if (!el || el === document.body) return { where: 'none' };
    if (el.closest('main')) return { where: 'main' };
    if (!el.closest('.bar,.mast')) return { where: 'other' };
    const cs = getComputedStyle(el), ow = cs.outlineStyle === 'none' ? 0 : parseFloat(cs.outlineWidth), off = parseFloat(cs.outlineOffset) || 0;
    const r = R(el), k = Math.max(0, off + ow);
    const ring = { left: r.left - k, right: r.right + k, top: r.top - k, bottom: r.bottom + k };
    const label = (el.textContent.trim() || el.getAttribute('aria-label') || el.tagName).replace(/\s+/g, ' ').slice(0, 18);
    const bad = [];
    if (!(ow > 0)) bad.push('no ring');
    for (let a = el.parentElement; a; a = a.parentElement) {
      const s = getComputedStyle(a);
      if (s.maskImage && s.maskImage !== 'none' || s.webkitMaskImage && s.webkitMaskImage !== 'none') bad.push('masked by .' + a.className.split(' ')[0]);
      if (a === document.body || a === document.documentElement) continue;
      if (s.overflowX !== 'visible' || s.overflowY !== 'visible') {
        const b = R(a), cl = { left: b.left + a.clientLeft, top: b.top + a.clientTop }; cl.right = cl.left + a.clientWidth; cl.bottom = cl.top + a.clientHeight;
        if (ring.left < cl.left - .5 || ring.right > cl.right + .5 || ring.top < cl.top - .5 || ring.bottom > cl.bottom + .5)
          bad.push(`ring [${Math.round(ring.left)},${Math.round(ring.right)}]x[${Math.round(ring.top)},${Math.round(ring.bottom)}] clipped by .${a.className.split(' ')[0]} [${Math.round(cl.left)},${Math.round(cl.right)}]x[${Math.round(cl.top)},${Math.round(cl.bottom)}]`);
      }
    }
    return { where: 'chrome', label, bad };
  };
  return { R, vis, visibleItems, chip, seg, ct, frontVoids, hlSizes, geometry, cpl, contrast, opacityOf, deadLinks, dayMeta, focusRing };
};

// ------------------------------------------------------------------ one (engine, width, state) case
async function runCase(browser, ctxOpts, state, fault = null) {
  const ctx = await browser.newContext(ctxOpts);
  const page = await ctx.newPage();
  const ext = [];
  page.on('request', r => { const u = r.url(); if (!u.startsWith('file:') && !u.startsWith('data:')) ext.push(u); });
  const qs = ['unread-science', 'empty'].includes(state) ? '?clean' : '';
  await page.goto(URL + qs);
  await page.evaluate(() => document.fonts.ready);
  if (fault?.css) await page.addStyleTag({ content: fault.css });
  await page.evaluate(`window.__L = (${LIB.toString()})()`);
  const fn = await page.evaluate(({ state, EXPECT_PERIODS }) => {
    const L = window.__L;
    const A = {};                                  // assertion -> [pass, detail]
    const click = el => el && el.click();
    if (state === 'default') {
      const n = L.visibleItems().length, all = L.ct(L.seg('')), beatAll = L.ct(L.chip(''));
      A.counts = [n === all && n === beatAll, `visible ${n} / All seg ${all} / All beat ${beatAll}`];
      const bad = [];
      for (const [d, m] of Object.entries(EXPECT_PERIODS)) {
        const tags = [...document.querySelectorAll(`#d-${d} .day__cov .ptag`)];
        if (tags.length !== Object.keys(m).length) bad.push(`${d}: ${tags.length} tags`);
        for (const t of tags) {
          const ts = [...t.querySelectorAll('time')].map(x => x.getAttribute('datetime'));
          const [s, e] = m[t.dataset.stream] || [];
          const got = ts.length === 1 ? [ts[0], ts[0]] : ts;
          if (got[0] !== s || got[1] !== e || !L.vis(t)) bad.push(`${d} ${t.dataset.stream}: ${got} (want ${s}..${e}, visible ${L.vis(t)})`);
        }
      }
      const kick = [...document.querySelectorAll('#ed-science-2026-09-23 .ed__kick time')].map(x => x.getAttribute('datetime')).join('..');
      if (kick !== '2026-09-17..2026-09-23') bad.push('science kicker ' + kick);
      A.periods = [bad.length === 0, bad.join('; ') || 'all 10 edition tags + kicker match'];
      // every lifted story keeps a pointer in its own day; each day has an h2 with <time>
      const lifted = [...document.querySelectorAll('.front [data-sid]')].map(x => x.dataset.sid);
      const miss = lifted.filter(s => !document.querySelector(`section.day [data-ptr="${s}"]`));
      A.pointers = [miss.length === 0, miss.length ? 'missing ' + miss : `${lifted.length} lifted items all have a pointer row`];
      // measure: the Yemen index row, folded why then opened body, 45-90 characters per line where there is room
      const row = document.getElementById('r-st-ca3429e95979');
      const whyN = L.cpl(row.querySelector('.why'));
      click(row.querySelector('.more')); const sumN = L.cpl(row.querySelector('.sum'));
      const cols = getComputedStyle(row.querySelector('.row__body')).columnCount; click(row.querySelector('.more'));
      const mx = Math.max(whyN, sumN), mn = Math.min(whyN, sumN);
      A.measure = [mx <= 90 && (innerWidth < 700 || mn >= 45), `opened row: why ${whyN}, body ${sumN} chars/line (columns ${cols})`];
    }
    if (state === 'expanded') {
      const f0 = L.frontVoids(), h0 = L.hlSizes();
      const card = document.querySelectorAll('.fcards--rest .fc')[1];
      click(card.querySelector('.more'));
      const f1 = L.frontVoids(), h1 = L.hlSizes();
      A.gap = [f1.max <= f0.max + 50, `folded max ${f0.max}px, after one expand ${f1.max}px (${f1.per.map(p => p.join(':')).join(' ')})`];
      A.hlSize = [h0 === h1, h0 === h1 ? 'front headline sizes unchanged' : `${h0} -> ${h1}`];
      A.fullRow = [Math.abs(L.R(card).width - L.R(card.parentElement).width) < 2, `open card ${Math.round(L.R(card).width)} of ${Math.round(L.R(card.parentElement).width)}px`];
      click(card.querySelector('.more'));                                     // fold it again, then the top band
      for (const [k, sel] of [['gapDesk', '.desk .ed'], ['gapLead', '.fcards--top .fc']]) {
        const el = document.querySelector(sel), g0 = L.frontVoids(), s0 = L.hlSizes();
        click(el.querySelector('.more'));
        const g1 = L.frontVoids(), s1 = L.hlSizes();
        A[k] = [g1.max <= g0.max + 50 && s0 === s1, `${sel} open: void ${g0.max} -> ${g1.max}px, headline sizes ${s0 === s1 ? 'unchanged' : s0 + ' -> ' + s1}`];
        click(el.querySelector('.more'));
      }
    }
    if (state === 'unread-science') {
      const u0 = L.ct(L.seg('unread'));
      const sci = [...document.querySelectorAll('[data-sid][data-edition="2026-09-23-science"]')].filter(x => x.dataset.zone !== 'editorial');
      sci.forEach(s => click(s.querySelector('.readbtn')));
      const u1 = L.ct(L.seg('unread'));
      const ed = document.getElementById('ed-science-2026-09-23');
      const derived = ed.classList.contains('is-read') && ed.querySelector('.readbtn').getAttribute('aria-pressed') === 'true';
      const disc = ed.querySelector('.ed__disc'), ref = document.querySelector('#ed-sports-2026-09-21 .ed__disc');
      const dOp = L.opacityOf(disc), dSame = getComputedStyle(disc).color === getComputedStyle(ref).color;
      A.disc = [derived && dOp === 1 && dSame && L.contrast(disc) >= 4.5, `read editorial's AI disclosure: opacity ${dOp}, colour as unread ${dSame}, ${L.contrast(disc).toFixed(2)}:1`];
      const readText = [...document.querySelectorAll('.is-read .why, .is-read .sum, .is-read .ed__hl, .is-read .ed__body p, .ptr.is-read .ptr__h')].filter(L.vis);
      const worst = readText.map(e => [L.contrast(e), e.className + '@' + (e.closest('[data-sid],[data-ptr]') || {}).id]).sort((a, b) => a[0] - b[0])[0];
      A.readContrast = [readText.length > 0 && worst[0] >= 4.5, `${readText.length} read text blocks, lowest ${worst ? worst[0].toFixed(2) + ':1 (' + worst[1] + ')' : 'n/a'}`];
      click(ed.querySelector('.readbtn'));                                      // explicit un-tick overrides
      const untick = !ed.classList.contains('is-read') && L.ct(L.seg('unread')) === u1 + 1;
      click(ed.querySelector('.readbtn'));
      click(L.seg('unread'));
      const n = L.visibleItems().length, u2 = L.ct(L.seg('unread'));
      A.edRead = [u0 - u1 === sci.length + 1 && derived, `${sci.length} stories ticked: Unread ${u0} -> ${u1} (editorial counted once: ${u0 - u1 === sci.length + 1}), derived read ${derived}`];
      A.override = [untick, `explicit un-tick wins over the edition rule: ${untick}`];
      A.counts = [n === u2 && !L.vis(ed), `Unread chip ${u2} vs visible ${n}; science editorial hidden ${!L.vis(ed)}`];
      const emptyDays = [...document.querySelectorAll('section.day')].filter(s => !s.hidden && !s.querySelector('[data-sid]:not([hidden]),[data-ptr]:not([hidden])'));
      A.dayHide = [emptyDays.length === 0, `${emptyDays.length} shown day editions with zero visible rows`];
    }
    if (state === 'beat-sports') {
      click(L.chip('sports'));
      const n = L.visibleItems().length, c = L.ct(L.chip('sports')), all = L.ct(L.seg(''));
      A.counts = [n === c && n === all, `Sports chip ${c} / All seg ${all} vs visible ${n}`];
      const ed = document.getElementById('ed-sports-2026-09-21');
      A.sportsEd = [!!ed && L.vis(ed), 'sports editorial visible under Sports: ' + (!!ed && L.vis(ed))];
      const shownDays = [...document.querySelectorAll('section.day')].filter(L.vis).map(s => s.dataset.date);
      A.dayHide = [shownDays.join() === '2026-09-21', 'day editions shown: ' + shownDays.join()];
      // every chip, with Sports held: its number == what the page shows with that chip pressed too
      const bad = []; let tried = 0;
      for (const c of [...document.querySelectorAll('.chip')].filter(L.vis)) {
        const k = c.dataset.topic, n = L.ct(c); tried++;
        if (k === '') { click(c); const v = L.visibleItems().length; if (v !== n) bad.push(`All ${n} shows ${v}`); click(L.chip('sports')); continue; }
        if (c.getAttribute('aria-pressed') === 'true') { const v = L.visibleItems().length; if (v !== n) bad.push(`${k} (held) ${n} shows ${v}`); continue; }
        click(c); const v = L.visibleItems().length; if (v !== n) bad.push(`sports+${k} chip ${n} shows ${v}`); click(c);
      }
      A.multiBeat = [bad.length === 0 && tried > 2, `${tried} chips with Sports held ${bad.length ? bad.join('; ') : 'all honest'}`];
    }
    if (state === 'empty') {
      click(L.chip('sports')); click(L.seg('read'));
      const em = document.getElementById('empty'), n = L.visibleItems().length;
      const first = [...document.querySelector('main').children].filter(L.vis)[0];
      A.emptyFirst = [n === 0 && first === em && em.textContent.trim().length > 0, `visible ${n}; first line: "${first ? first.textContent.trim().slice(0, 60) : ''}"`];
      A.counts = [L.ct(L.seg('read')) === 0 && L.ct(L.chip('sports')) === 0, `Read ${L.ct(L.seg('read'))}, Sports ${L.ct(L.chip('sports'))}`];
    }
    const dead = L.deadLinks(); A.links = [dead.length === 0, dead.length ? dead.join('; ') : 'every visible in-page link has a rendered target'];
    const dm = L.dayMeta(); A.dayMeta = [dm.bad.length === 0, `${dm.days} day headers ${dm.bad.join('; ') || 'match what they show'}`];
    return A;
  }, { state, EXPECT_PERIODS });
  const KEY = browser.browserType().name() === 'webkit' ? 'Alt+Tab' : 'Tab';   // WebKit tabs to links/buttons only with Option (Safari's default)
  if (state === 'default' && !fault?.noFocus) {
    // keyboard: Tab through the masthead and the control bar; every focused control's ring must show whole
    await page.evaluate(() => { scrollTo(0, 0); document.activeElement && document.activeElement.blur(); });
    const seen = [];
    for (let i = 0; i < 70; i++) {
      await page.keyboard.press(KEY);
      await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));
      const f = await page.evaluate(() => window.__L.focusRing());
      if (f.where === 'main') break;
      if (f.where === 'chrome') seen.push(f);
    }
    // phones: the bar is sticky at the bottom. Park each of the first 12 controls in main so it pokes out just
    // under the bar's top edge, Tab onto it from its predecessor, and require the focus scroll to lift it clear
    const bw = await page.evaluate(() => innerWidth);
    if (bw < 700) {
      const under = []; let stops = 0;
      for (let i = 1; i <= 12; i++) {
        const ready = await page.evaluate(i => {
          const L = window.__L, list = [...document.querySelectorAll('main a[href], main button, main summary')].filter(e => L.vis(e) && !e.closest('[hidden]'));
          const prev = list[i - 1], el = list[i]; if (!el) return false;
          const bar = document.querySelector('.bar').getBoundingClientRect();
          scrollBy(0, el.getBoundingClientRect().bottom - (bar.top + 10));
          window.__want = el; prev.focus({ preventScroll: true }); return true;
        }, i);
        if (!ready) break;
        await page.keyboard.press(KEY);
        await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));
        const u = await page.evaluate(() => { const e = document.activeElement, b = document.querySelector('.bar').getBoundingClientRect(), r = e.getBoundingClientRect();
          return e === window.__want ? { ok: r.bottom <= b.top + .5, d: `${(e.textContent.trim() || e.getAttribute('aria-label') || '').slice(0, 16)} bottom ${Math.round(r.bottom)} > bar top ${Math.round(b.top)}` } : null; });
        if (!u) continue; stops++; if (!u.ok) under.push(u.d);
      }
      fn.focusMain = [stops >= 8 && under.length === 0, `${stops} controls parked under the phone bar then tabbed to, ${under.length} left under it ${under.slice(0, 2).join('; ')}`];
    }
    if (seen.length) {
      const bad = seen.filter(f => f.bad.length);
      fn.focus = [bad.length === 0, `${seen.length} chrome controls tabbed${bad.length ? ': ' + bad.slice(0, 3).map(f => f.label + ' ' + f.bad.join(',')).join(' | ') : ', every ring whole'}`];
    } else Object.defineProperty(fn, 'focusNA', { value: true, enumerable: false });
  }
  const g = await page.evaluate(() => window.__L.geometry());
  await ctx.close();
  const A = {
    overflow: [g.overflow.length === 0, g.overflow.join('; ') || 'none'],
    overlap: [g.overlap.length === 0, `${g.overlap.length} of ${g.pairs} sibling pairs ${g.overlap.slice(0, 3).join('; ')}`],
    containment: [g.containment.length === 0, `${g.containment.length} of ${g.contained} outside ${g.containment.slice(0, 3).join('; ')}`],
    order: [g.order.length === 0, `${g.order.length} inversions over ${g.groups} groups ${g.order.slice(0, 3).join('; ')}`],
    external: [ext.length === 0, ext.length + ' external requests'],
    ...fn,
  };
  if (fn.focusNA) Object.defineProperty(A, 'focusNA', { value: true, enumerable: false });
  return A;
}

const out = []; const log = s => { out.push(s); console.log(s); };
const totals = {}; let fails = 0;
async function sweep(browser, label, opts) {
  for (const st of STATES) {
    const A = await runCase(browser, opts, st);
    const bad = Object.entries(A).filter(([, [ok]]) => !ok);
    const t = totals[st] ||= { pass: 0, fail: 0 };
    Object.values(A).forEach(([ok]) => ok ? t.pass++ : t.fail++);
    fails += bad.length;
    if (A.focusNA) log(`${label.padEnd(18)} ${st.padEnd(15)} note: Tab never reached the masthead or bar in this engine; focus assertion not counted (n/a)`);
    log(`${label.padEnd(18)} ${st.padEnd(15)} ${bad.length ? 'FAIL ' + bad.map(([k, [, d]]) => k + ': ' + d).join(' | ') : 'PASS ' + Object.keys(A).length + ' assertions'}` +
      (st === 'expanded' || st === 'unread-science' ? `\n${' '.repeat(35)}${st === 'expanded' ? A.gap[1] + '\n' + ' '.repeat(35) + A.gapDesk[1] + '\n' + ' '.repeat(35) + A.gapLead[1] : A.edRead[1] + '\n' + ' '.repeat(35) + A.disc[1] + '\n' + ' '.repeat(35) + A.readContrast[1]}` : '') +
      (st === 'default' ? `\n${' '.repeat(35)}${A.measure[1]}${A.focus ? '\n' + ' '.repeat(35) + A.focus[1] : ''}${A.focusMain ? '\n' + ' '.repeat(35) + A.focusMain[1] : ''}` : '') +
      (st === 'beat-sports' ? `\n${' '.repeat(35)}${A.multiBeat[1]}\n${' '.repeat(35)}${A.dayMeta[1]}` : ''));
  }
}

// ------------------------------------------------------------------ main sweep
const c = await chromium.launch();
for (const w of WIDTHS) await sweep(c, `chromium ${w}`, { viewport: { width: w, height: 900 } });
const wk = await webkit.launch();
await sweep(wk, 'webkit iPhone 15', { ...devices['iPhone 15'] });

// ------------------------------------------------------------------ no-JS: every text visible, no inert control
for (const w of [390, 1440]) {
  const ctx = await c.newContext({ viewport: { width: w, height: 900 }, javaScriptEnabled: false });
  const p = await ctx.newPage(); await p.goto(URL);
  const r = await p.evaluate(() => {
    const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const hiddenText = [...document.querySelectorAll('.fold, .why, .ed__body, .ed__disc, .hl, .ptag')].filter(e => !vis(e) && e.textContent.trim()).length;
    const buttons = [...document.querySelectorAll('body > .page button, body > .page input, body > .page textarea')].filter(vis).length;
    const hiwLink = [...document.querySelectorAll('a[href="#hiw"]')].some(vis), key = vis(document.querySelector('.mast__key summary'));
    return { hiddenText, buttons, hiwLink, key, scroll: document.documentElement.scrollWidth - innerWidth };
  });
  await p.goto(URL + '#hiw');
  r.hiw = await p.evaluate(() => { const d = document.getElementById('hiw'), b = d.getBoundingClientRect(); return b.width > 0 && b.height > 0 && b.top < innerHeight && b.bottom > 0 && [...d.querySelectorAll('button')].every(x => !x.getBoundingClientRect().width); });
  const ok = r.hiddenText === 0 && r.buttons === 0 && r.scroll <= 0 && r.hiwLink && r.hiw && r.key;
  if (!ok) fails++;
  (totals['no-js'] ||= { pass: 0, fail: 0 })[ok ? 'pass' : 'fail']++;
  log(`chromium ${w} no-JS       ${ok ? 'PASS' : 'FAIL'} hidden text blocks ${r.hiddenText}, visible controls ${r.buttons}, overflow ${r.scroll}, How-this-works link ${r.hiwLink} -> #hiw shown ${r.hiw}, key ${r.key}`);
  await ctx.close();
}

log('\n== TOTALS per state (assertions passed / failed, 8 Chromium widths + WebKit iPhone 15)');
for (const [k, t] of Object.entries(totals)) log(`${k.padEnd(15)} ${t.pass} passed / ${t.fail} failed`);

// ------------------------------------------------------------------ fault injection: each fault must flip its own assertion
log('\n== FAULT INJECTION (chromium 1440 unless noted): each deliberate CSS break must fail its own assertion');
const FAULTS = [
  { key: 'overflow', state: 'default', css: 'main{min-width:1800px}' },
  { key: 'overlap', state: 'default', css: '.fcards--rest > .fc:nth-child(2){margin-left:-120px}' },
  { key: 'containment', state: 'default', css: '#d-2026-09-22 .rows{translate:0 -300px}' },
  { key: 'order', state: 'default', css: '#d-2026-09-22 .rows{flex-direction:column-reverse}' },
  { key: 'periods', state: 'default', css: '.day__cov{display:none}' },
  { key: 'gap', state: 'expanded', css: '.js .fcards--rest > .fc.is-open{flex-basis:30%!important}' },
  { key: 'gapDesk', state: 'expanded', css: '.js .front__top:has(.is-open) > .desk{flex-basis:clamp(240px,27%,340px)!important}.js .front__top:has(.is-open) > .fcards--top{flex-basis:60%!important}' },
  { key: 'hlSize', state: 'expanded', css: '.js .fcards--rest .fc.is-open .hl{font-size:48px!important}' },
  { key: 'counts', state: 'beat-sports', css: '[data-sid][hidden]{display:flex!important}' },
  { key: 'sportsEd', state: 'beat-sports', css: '#ed-sports-2026-09-21{display:none!important}' },
  { key: 'emptyFirst', state: 'empty', css: '#empty{display:none!important}' },
  { key: 'overflow', state: 'default', css: '.day__cov{white-space:nowrap}.day__cov::after{content:"";display:inline-block;inline-size:600px}', w: 360 },
  { key: 'measure', state: 'default', css: '.row__body{columns:auto!important}.row .why,.row .sum{max-inline-size:none!important}' },
  { key: 'measure', state: 'default', css: '.row__body{columns:auto!important}.row .why,.row .sum{max-inline-size:none!important}', w: 768 },
  { key: 'focus', state: 'default', css: '.seg{overflow:hidden}' },
  { key: 'focus', state: 'default', css: '.bar .beats:has(:focus-visible){mask-image:linear-gradient(90deg,#000 88%,transparent)}', w: 768 },
  { key: 'focusMain', state: 'default', css: 'html{scroll-padding-block-end:4.5rem!important}', w: 390 },
  { key: 'links', state: 'unread-science', css: 'main a.jump[hidden],.day__links[hidden]{display:inline-flex!important}' },
  { key: 'dayMeta', state: 'beat-sports', css: '.day__cov .ptag[hidden]{display:inline-flex!important}' },
  { key: 'disc', state: 'unread-science', css: '.is-read .ed__disc{opacity:.58}' },
  { key: 'readContrast', state: 'unread-science', css: '.is-read .why{opacity:.58}' },
  { key: 'multiBeat', state: 'beat-sports', css: '#d-2026-09-21 .row[hidden]{display:block!important}' },
];
let caught = 0;
const base = await runCase(c, { viewport: { width: 1440, height: 900 } }, 'default');
for (const f of FAULTS) {
  const A = await runCase(c, { viewport: { width: f.w || 1440, height: 900 } }, f.state, f);
  const flipped = A[f.key] && !A[f.key][0];
  if (flipped) caught++;
  log(`${flipped ? 'CAUGHT' : 'MISSED'}  ${f.key.padEnd(11)} ${f.state.padEnd(12)} ${(f.w || 1440) + 'px'}  css: ${f.css}  ->  ${A[f.key] ? A[f.key][1] : 'n/a'}`);
}
log(`fault self-test: ${caught}/${FAULTS.length} faults caught (baseline default@1440 ${Object.values(base).every(([ok]) => ok) ? 'clean' : 'NOT clean'})`);
if (caught !== FAULTS.length) fails++;
await c.close(); await wk.close();
log(`\nRESULT: ${fails === 0 ? 'ALL PASS' : fails + ' failure(s)'}`);
fs.writeFileSync(D + '/check.out', out.join('\n') + '\n');
process.exit(fails ? 1 : 0);
