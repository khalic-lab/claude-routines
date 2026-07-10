// Smoke test for the feedback-sink Worker: exercises the passkey/readstate routes
// against a mock env (in-memory KV) with NO network and NO real authenticator.
// The full WebAuthn ceremony (attestation/assertion crypto) is live-only — here we
// assert every non-crypto guard: invite gate, single-use challenges, unknown cred,
// session auth, LWW merge semantics, caps, /submit reader override, per-origin CORS.
//
// Run: cd tools/feedback-sink && node test/smoke.mjs   (exit 0 = all checks pass)

const SITE = "https://khalic-lab.github.io";
const BASE = "https://feedback-sink.example.workers.dev";

// ---------------------------------------------------------------------------
// Mock KV: get/put/delete/list; expirationTtl accepted and ignored.
function mockKV() {
  const map = new Map();
  return {
    map,
    async get(key) {
      return map.has(key) ? map.get(key) : null;
    },
    async put(key, value, _opts) {
      map.set(key, String(value));
    },
    async delete(key) {
      map.delete(key);
    },
    async list({ prefix = "", limit = 1000 } = {}) {
      const keys = [...map.keys()]
        .filter((k) => k.startsWith(prefix))
        .sort()
        .slice(0, limit)
        .map((name) => ({ name }));
      return { keys, list_complete: true };
    },
  };
}

const kv = mockKV();
const env = {
  FEEDBACK_KV: kv,
  FEEDBACK_TOKEN: "bridge-bearer-secret",
  WIDGET_KEY: "site-key",
  INVITE_TOKEN: "the-invite-secret",
};

const worker = (await import("../src/worker.js")).default;

function req(path, { method = "GET", headers = {}, body } = {}) {
  return new Request(BASE + path, {
    method,
    headers,
    body: body === undefined ? undefined : typeof body === "string" ? body : JSON.stringify(body),
  });
}

const b64url = (obj) => Buffer.from(JSON.stringify(obj)).toString("base64url");

let failures = 0;
let n = 0;
function check(name, cond, detail = "") {
  n++;
  console.log(`${cond ? "ok" : "FAIL"} ${n} - ${name}${cond ? "" : `  [${detail}]`}`);
  if (!cond) failures++;
}

const DAY = 86400000;
const TOKEN = "a".repeat(64);
const AUTH = { Authorization: `Bearer ${TOKEN}` };
const sid = (hex) => `st-${hex.padStart(12, "0")}`;

// --- readstate auth -----------------------------------------------------------
{
  const res = await worker.fetch(req("/readstate"), env);
  const body = await res.json();
  check("GET /readstate without session -> 401 no session", res.status === 401 && body.error === "no session", JSON.stringify([res.status, body]));
}
{
  const res = await worker.fetch(req("/readstate", { headers: { Authorization: `Bearer ${"f".repeat(64)}` } }), env);
  check("GET /readstate with unknown token -> 401", res.status === 401, String(res.status));
}

// --- seeded session + empty state ----------------------------------------------
await kv.put(`session:${TOKEN}`, JSON.stringify({ reader: "rafael", created: Date.now() }));
{
  const res = await worker.fetch(req("/readstate", { headers: AUTH }), env);
  const body = await res.json();
  check(
    "GET /readstate with seeded session -> 200 {reader, state:{}} + no-store",
    res.status === 200 && body.reader === "rafael" && JSON.stringify(body.state) === "{}" &&
      res.headers.get("Cache-Control") === "no-store",
    JSON.stringify([res.status, body, res.headers.get("Cache-Control")]),
  );
}

// --- POST merge: LWW ------------------------------------------------------------
// Recent timestamps: anything older than 90 days is (correctly) aged out of the merge.
const T = Date.now() - 10000;
{
  const res = await worker.fetch(
    req("/readstate", { method: "POST", headers: AUTH, body: { state: { [sid("1")]: { ts: T + 1000, v: 1 } } } }),
    env,
  );
  const body = await res.json();
  check("POST first entry -> total 1 changed 1", res.status === 200 && body.ok === true && body.total === 1 && body.changed === 1, JSON.stringify(body));
}
{
  const res = await worker.fetch(
    req("/readstate", { method: "POST", headers: AUTH, body: { state: { [sid("1")]: { ts: T + 2000, v: 0 } } } }),
    env,
  );
  const body = await res.json();
  const state = JSON.parse(await kv.get("readstate:rafael"));
  check(
    "POST newer tombstone (v:0) wins -> changed 1, stored v=0",
    body.changed === 1 && state[sid("1")].ts === T + 2000 && state[sid("1")].v === 0,
    JSON.stringify([body, state]),
  );
}
{
  const res = await worker.fetch(
    req("/readstate", { method: "POST", headers: AUTH, body: { state: { [sid("1")]: { ts: T + 2000, v: 1 } } } }),
    env,
  );
  const body = await res.json();
  const state = JSON.parse(await kv.get("readstate:rafael"));
  check(
    "POST tie (same ts) keeps existing -> changed 0, v stays 0",
    body.changed === 0 && state[sid("1")].v === 0,
    JSON.stringify([body, state]),
  );
}
{
  const res = await worker.fetch(
    req("/readstate", { method: "POST", headers: AUTH, body: { state: { [sid("1")]: { ts: T + 1500, v: 1 } } } }),
    env,
  );
  const body = await res.json();
  const state = JSON.parse(await kv.get("readstate:rafael"));
  check(
    "POST older ts loses -> changed 0, ts stays newer",
    body.changed === 0 && state[sid("1")].ts === T + 2000,
    JSON.stringify([body, state]),
  );
}

// --- caps + per-entry validation -------------------------------------------------
{
  const res = await worker.fetch(
    req("/readstate", {
      method: "POST",
      headers: AUTH,
      body: {
        state: {
          "not-a-sid": { ts: 3000, v: 1 }, // bad sid
          [sid("2")]: { ts: "3000", v: 1 }, // ts not a number
          [sid("3")]: { ts: Date.now() + 2 * DAY, v: 1 }, // too far in the future
          [sid("4")]: { ts: T, v: 2 }, // bad v
          [sid("5")]: { ts: T, v: 1 }, // the one valid entry
        },
      },
    }),
    env,
  );
  const body = await res.json();
  check(
    "POST invalid entries skipped, valid merged -> changed 1, total 2",
    res.status === 200 && body.changed === 1 && body.total === 2,
    JSON.stringify(body),
  );
}
{
  // 2001 minimal entries is ~70KB, so the 64KB byte cap (413) necessarily trips before
  // the 2000-entry cap (400) — the entry cap is unreachable defense-in-depth behind it.
  const state = {};
  for (let i = 0; i < 2001; i++) state[sid(i.toString(16))] = { ts: 1, v: 1 };
  const res = await worker.fetch(req("/readstate", { method: "POST", headers: AUTH, body: { state } }), env);
  check("POST >2000 entries -> rejected (413 byte cap fires first)", res.status === 413, String(res.status));
}
{
  const res = await worker.fetch(
    req("/readstate", { method: "POST", headers: AUTH, body: `{"state":{},"pad":"${"x".repeat(70000)}"}` }),
    env,
  );
  check("POST oversize body -> 413", res.status === 413, String(res.status));
}
{
  const res = await worker.fetch(req("/readstate", { method: "POST", headers: AUTH, body: { state: [1, 2] } }), env);
  check("POST non-object state -> 400", res.status === 400, String(res.status));
}

// --- 90-day age-out + rolling session ---------------------------------------------
{
  await kv.put(
    "readstate:rafael",
    JSON.stringify({ [sid("9")]: { ts: Date.now() - 91 * DAY, v: 1 }, [sid("5")]: { ts: Date.now() - DAY, v: 1 } }),
  );
  const now = Date.now();
  const res = await worker.fetch(
    req("/readstate", { method: "POST", headers: AUTH, body: { state: { [sid("6")]: { ts: now, v: 1 } } } }),
    env,
  );
  const body = await res.json();
  const state = JSON.parse(await kv.get("readstate:rafael"));
  check(
    "merge drops entries older than 90 days",
    body.total === 2 && !(sid("9") in state) && sid("6") in state,
    JSON.stringify([body, state]),
  );
}
{
  await kv.put(`session:${TOKEN}`, JSON.stringify({ reader: "rafael", created: Date.now() - 31 * DAY }));
  await worker.fetch(req("/readstate", { headers: AUTH }), env);
  const sess = JSON.parse(await kv.get(`session:${TOKEN}`));
  check("session >30 days old is re-minted on readstate use", Date.now() - sess.created < DAY, JSON.stringify(sess));
}

// --- /submit reader override -------------------------------------------------------
{
  const res = await worker.fetch(
    req("/submit", { method: "POST", headers: { "X-Widget-Key": "site-key" }, body: { brief: "2026-07-10-news", vote: 1 } }),
    env,
  );
  const { keys } = await kv.list({ prefix: "fb:" });
  const rec = JSON.parse(await kv.get(keys[keys.length - 1].name));
  check("/submit without session keeps default reader 'rafael'", res.status === 200 && rec.reader === "rafael", JSON.stringify(rec));
}
{
  const aliceTok = "b".repeat(64);
  await kv.put(`session:${aliceTok}`, JSON.stringify({ reader: "alice", created: Date.now() }));
  const res = await worker.fetch(
    req("/submit", {
      method: "POST",
      headers: { "X-Widget-Key": "site-key", Authorization: `Bearer ${aliceTok}` },
      body: { brief: "2026-07-10-news", vote: -1 },
    }),
    env,
  );
  const { keys } = await kv.list({ prefix: "fb:" });
  const recs = await Promise.all(keys.map(async (k) => JSON.parse(await kv.get(k.name))));
  const alice = recs.find((r) => r.reader === "alice");
  check("/submit with session Bearer sets reader from session", res.status === 200 && !!alice && alice.vote === -1, JSON.stringify(recs));
}
{
  const res = await worker.fetch(req("/submit", { method: "POST", body: { brief: "x", vote: 1 } }), env);
  check("/submit X-Widget-Key gate unchanged (missing key -> 403)", res.status === 403, String(res.status));
}

// --- CORS: restricted origins on /readstate + /auth/* --------------------------------
{
  const res = await worker.fetch(req("/readstate", { method: "OPTIONS", headers: { Origin: SITE } }), env);
  check(
    "OPTIONS /readstate from site origin -> 204 + ACAO echoed",
    res.status === 204 && res.headers.get("Access-Control-Allow-Origin") === SITE,
    JSON.stringify([res.status, res.headers.get("Access-Control-Allow-Origin")]),
  );
  check(
    "restricted Allow-Headers includes Authorization",
    (res.headers.get("Access-Control-Allow-Headers") || "").includes("Authorization"),
    res.headers.get("Access-Control-Allow-Headers") || "null",
  );
}
{
  const res = await worker.fetch(req("/readstate", { method: "OPTIONS", headers: { Origin: "https://evil.example" } }), env);
  check(
    "OPTIONS /readstate from foreign origin -> 204, NO ACAO",
    res.status === 204 && res.headers.get("Access-Control-Allow-Origin") === null,
    JSON.stringify([res.status, res.headers.get("Access-Control-Allow-Origin")]),
  );
}
{
  const res = await worker.fetch(req("/auth/login", { method: "OPTIONS", headers: { Origin: "https://evil.example" } }), env);
  check("OPTIONS /auth/* from foreign origin -> no ACAO", res.status === 204 && res.headers.get("Access-Control-Allow-Origin") === null, String(res.status));
}
{
  const res = await worker.fetch(req("/submit", { method: "OPTIONS", headers: { Origin: "https://evil.example" } }), env);
  check("existing routes keep ACAO '*'", res.status === 204 && res.headers.get("Access-Control-Allow-Origin") === "*", String(res.headers.get("Access-Control-Allow-Origin")));
}

// --- /auth/register-options: invite gate + fail closed ---------------------------------
{
  const res = await worker.fetch(req("/auth/register-options", { method: "POST", body: { invite: "wrong" } }), env);
  const body = await res.json();
  check("register-options bad invite -> 403 bad invite", res.status === 403 && body.error === "bad invite", JSON.stringify([res.status, body]));
}
{
  const noInviteEnv = { ...env, INVITE_TOKEN: undefined };
  const res = await worker.fetch(req("/auth/register-options", { method: "POST", body: { invite: "anything" } }), noInviteEnv);
  check("register-options fails CLOSED when INVITE_TOKEN unset", res.status === 403, String(res.status));
}
{
  const res = await worker.fetch(
    req("/auth/register-options", { method: "POST", headers: { Origin: SITE }, body: { invite: "the-invite-secret" } }),
    env,
  );
  const body = await res.json();
  const stored = await kv.get(`chal:reg:${body.challenge}`);
  check(
    "register-options good invite -> 200 creation options + chal:reg KV",
    res.status === 200 && body.rp?.id === "khalic-lab.github.io" && body.rp?.name === "khalic news" &&
      body.user?.name === "rafael" && body.user?.displayName === "Rafael" &&
      body.attestation === "none" && body.authenticatorSelection?.residentKey === "required" &&
      body.authenticatorSelection?.userVerification === "required" &&
      typeof body.challenge === "string" && stored === "1",
    JSON.stringify(body),
  );
  check("register-options echoes site origin ACAO", res.headers.get("Access-Control-Allow-Origin") === SITE, String(res.headers.get("Access-Control-Allow-Origin")));
}

// --- /auth/register: challenge guards (crypto verify is live-only) -----------------------
{
  const res = await worker.fetch(
    req("/auth/register", {
      method: "POST",
      body: { invite: "the-invite-secret", response: { id: "x", response: { clientDataJSON: b64url({ challenge: "never-issued" }) } } },
    }),
    env,
  );
  const body = await res.json();
  check("register with unknown challenge -> 403", res.status === 403 && body.error === "unknown challenge", JSON.stringify([res.status, body]));
}
{
  const res = await worker.fetch(req("/auth/register", { method: "POST", body: { invite: "wrong", response: {} } }), env);
  check("register re-checks invite -> 403", res.status === 403, String(res.status));
}
{
  await kv.put("chal:reg:used-once", "1");
  const response = { id: "x", response: { clientDataJSON: b64url({ challenge: "used-once" }) } };
  const first = await worker.fetch(req("/auth/register", { method: "POST", body: { invite: "the-invite-secret", response } }), env);
  const second = await worker.fetch(req("/auth/register", { method: "POST", body: { invite: "the-invite-secret", response } }), env);
  const secondBody = await second.json();
  check(
    "register challenge is single-use (consumed even on failed verify)",
    first.status === 403 && second.status === 403 && secondBody.error === "unknown challenge" && (await kv.get("chal:reg:used-once")) === null,
    JSON.stringify([first.status, secondBody]),
  );
}

// --- /auth/login-options + /auth/login guards ----------------------------------------------
{
  const res = await worker.fetch(req("/auth/login-options", { method: "POST", body: {} }), env);
  const body = await res.json();
  const stored = await kv.get(`chal:auth:${body.challenge}`);
  check(
    "login-options -> 200 request options (rpID, UV required, no allowCredentials) + chal:auth KV",
    res.status === 200 && body.rpId === "khalic-lab.github.io" && body.userVerification === "required" &&
      body.allowCredentials === undefined && typeof body.challenge === "string" && stored === "1",
    JSON.stringify(body),
  );
}
{
  await kv.put("chal:auth:login-chal", "1");
  const res = await worker.fetch(
    req("/auth/login", {
      method: "POST",
      body: { response: { id: "no-such-cred", response: { clientDataJSON: b64url({ challenge: "login-chal" }) } } },
    }),
    env,
  );
  const body = await res.json();
  check("login with unknown credential id -> 403", res.status === 403 && body.error === "unknown credential", JSON.stringify([res.status, body]));
}
{
  const res = await worker.fetch(
    req("/auth/login", {
      method: "POST",
      body: { response: { id: "x", response: { clientDataJSON: b64url({ challenge: "never-issued-auth" }) } } },
    }),
    env,
  );
  check("login with unknown challenge -> 403", res.status === 403, String(res.status));
}

// -----------------------------------------------------------------------------------------
console.log(failures === 0 ? `PASS: all ${n} checks passed` : `FAIL: ${failures}/${n} checks failed`);
process.exit(failures === 0 ? 0 : 1);
