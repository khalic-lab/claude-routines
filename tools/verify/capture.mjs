// Weekly capture of the LIVE homepage for the Weekly Evaluator's rendered-page check (§D).
//
//   node tools/verify/capture.mjs --out DIR [--url URL] [--sha SHA] [--pages FILE] [--channel chrome]
//
// Run by .github/workflows/visual-capture.yml every Sunday before the evaluator, which
// force-pushes DIR to the `visual` branch (one commit, no history; never `main`, so no Pages
// build and no binary churn there). DIR gets capture.json plus six JPEGs: phone 390px and
// desktop 1280px, light and dark, the top of the page; light also one screen further down.
//
// Read-only by construction: no clicks or typing, and every request that is not
// GET/HEAD/OPTIONS is aborted (and listed), so a capture can never write to a live Worker.
// Page faults (console errors, failed requests, horizontal overflow, broken images) are
// data for the evaluator, not a failure: the script exits non-zero only when it cannot
// produce a capture at all.
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";

const SITE = "https://khalic-lab.github.io/claude-routines/";
const SHOTS = [
  { name: "phone-light", width: 390, height: 844, scheme: "light", mobile: true, scroll: true },
  { name: "phone-dark", width: 390, height: 844, scheme: "dark", mobile: true },
  { name: "desktop-light", width: 1280, height: 800, scheme: "light", scroll: true },
  { name: "desktop-dark", width: 1280, height: 800, scheme: "dark" },
];
const READ_ONLY = new Set(["GET", "HEAD", "OPTIONS"]);
const CAP = 10; // per-list cap in capture.json; the counts stay exact

function args(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    if (!k.startsWith("--")) continue;
    out[k.slice(2)] = argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[++i] : true;
  }
  return out;
}

function readJson(file) {
  if (!file) return null;
  try {
    return JSON.parse(fs.readFileSync(file, "utf8"));
  } catch {
    return null;
  }
}

async function shoot(browser, url, shot, outDir) {
  const ctx = await browser.newContext({
    viewport: { width: shot.width, height: shot.height },
    deviceScaleFactor: 1,
    colorScheme: shot.scheme,
    isMobile: !!shot.mobile,
    hasTouch: !!shot.mobile,
  });
  const consoleErrors = [], failed = [], blocked = [], blockedUrls = new Set();
  await ctx.route("**/*", (route) => {
    const req = route.request();
    if (READ_ONLY.has(req.method())) return route.continue();
    blocked.push(`${req.method()} ${req.url()}`.slice(0, 200));
    blockedUrls.add(req.url());
    return route.abort();
  });
  const page = await ctx.newPage();
  page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text().slice(0, 300)); });
  page.on("pageerror", (e) => consoleErrors.push(String(e).slice(0, 300)));
  page.on("requestfailed", (r) => {
    if (blockedUrls.has(r.url())) return; // our own abort of a write, already listed
    failed.push(`${r.failure()?.errorText || "failed"} ${r.url()}`.slice(0, 200));
  });
  page.on("response", (r) => { if (r.status() >= 400) failed.push(`HTTP ${r.status()} ${r.url()}`.slice(0, 200)); });

  let loadNote = "networkidle";
  try {
    await page.goto(url, { waitUntil: "networkidle", timeout: 45000 });
  } catch (e) {
    loadNote = `networkidle not reached (${String(e).split("\n")[0].slice(0, 120)})`;
  }
  await page.waitForTimeout(1500); // fonts, the fold script, lazy images
  const metrics = await page.evaluate(() => {
    const de = document.documentElement;
    const imgs = [...document.images].filter((i) => i.src);
    const h = document.querySelector("h1, h2");
    return {
      title: document.title,
      first_heading: h ? h.textContent.trim().replace(/\s+/g, " ").slice(0, 120) : null,
      overflow_x: Math.max(0, de.scrollWidth - de.clientWidth),
      page_height: de.scrollHeight,
      articles: document.querySelectorAll("article").length,
      images: imgs.length,
      broken_images: imgs.filter((i) => i.complete && i.naturalWidth === 0).length,
    };
  });
  const files = [`${shot.name}.jpg`];
  await page.screenshot({ path: path.join(outDir, files[0]), type: "jpeg", quality: 70 });
  if (shot.scroll && metrics.page_height > shot.height * 1.5) {
    files.push(`${shot.name}-2.jpg`);
    await page.screenshot({
      path: path.join(outDir, files[1]), type: "jpeg", quality: 70, fullPage: true,
      clip: { x: 0, y: shot.height, width: shot.width, height: Math.min(shot.height, metrics.page_height - shot.height) },
    });
  }
  await ctx.close();
  return {
    name: shot.name, files, viewport: `${shot.width}x${shot.height}`, scheme: shot.scheme,
    load: loadNote, metrics,
    console_errors: { count: consoleErrors.length, sample: consoleErrors.slice(0, CAP) },
    failed_requests: { count: failed.length, sample: failed.slice(0, CAP) },
    blocked_writes: { count: blocked.length, sample: blocked.slice(0, CAP) },
  };
}

async function main() {
  const a = args(process.argv.slice(2));
  if (!a.out) {
    console.error("usage: capture.mjs --out DIR [--url URL] [--sha SHA] [--pages FILE] [--channel chrome]");
    process.exit(2);
  }
  const url = a.url || SITE;
  fs.mkdirSync(a.out, { recursive: true });
  const pages = readJson(a.pages);
  const browser = await chromium.launch(a.channel ? { channel: a.channel } : {});
  const shots = [];
  try {
    for (const s of SHOTS) {
      shots.push(await shoot(browser, url, s, a.out));
      console.log(`${shots.length}/${SHOTS.length} ${s.name}: ${shots.at(-1).files.join(", ")}`);
    }
  } finally {
    await browser.close();
  }
  const capture = {
    captured_at: new Date().toISOString().replace(/\.\d+Z$/, "Z"),
    url,
    main_sha: a.sha || null,
    pages_build: pages ? { status: pages.status ?? null, commit: pages.commit ?? null, updated_at: pages.updated_at ?? null } : null,
    shots,
  };
  fs.writeFileSync(path.join(a.out, "capture.json"), JSON.stringify(capture, null, 1) + "\n");
  console.log(`wrote ${path.join(a.out, "capture.json")}`);
}

main().catch((e) => {
  console.error(String(e?.stack || e));
  process.exit(1);
});
