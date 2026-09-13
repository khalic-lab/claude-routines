// Smoke test for the feedback-sink Worker: exercises the passkey/readstate routes
// against a mock env (in-memory KV) with NO network and NO real authenticator.
// The full WebAuthn ceremony (attestation/assertion crypto) is live-only — here we
// assert every non-crypto guard: invite gate, single-use challenges, unknown cred,
// session auth (incl. the passkeys-only /submit + /propose gates, 2026-07-25), LWW
// merge semantics, caps, per-origin CORS.
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
  INVITE_TOKEN: "the-invite-secret",
  ADMIN_CRED_IDS: "admin-cred, spare-cred",
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
  await kv.put(`session:${TOKEN}`, JSON.stringify({ reader: "rafael", created: Date.now() - 2 * DAY }));
  await worker.fetch(req("/readstate", { headers: AUTH }), env);
  const sess = JSON.parse(await kv.get(`session:${TOKEN}`));
  check("session older than a day is re-minted on readstate use", Date.now() - sess.created < DAY, JSON.stringify(sess));
}

// --- /submit + /propose: passkeys-only (the shared X-Widget-Key gate died 2026-07-25) ---
{
  const res = await worker.fetch(req("/submit", { method: "POST", body: { brief: "2026-07-10-news", vote: 1 } }), env);
  const body = await res.json();
  check("/submit without session -> 401 no session", res.status === 401 && body.error === "no session", JSON.stringify([res.status, body]));
}
{
  // a stray X-Widget-Key (an old cached page) is simply ignored; the session decides.
  const res = await worker.fetch(
    req("/submit", { method: "POST", headers: { ...AUTH, "X-Widget-Key": "site-key" }, body: { brief: "2026-07-10-news", vote: 1, reader: "mallory" } }),
    env,
  );
  const { keys } = await kv.list({ prefix: "fb:" });
  const rec = JSON.parse(await kv.get(keys[keys.length - 1].name));
  check("/submit with session -> 200, reader pinned from session (body reader ignored)", res.status === 200 && rec.reader === "rafael", JSON.stringify(rec));
}
{
  const aliceTok = "b".repeat(64);
  await kv.put(`session:${aliceTok}`, JSON.stringify({ reader: "alice", created: Date.now() }));
  const res = await worker.fetch(
    req("/submit", { method: "POST", headers: { Authorization: `Bearer ${aliceTok}` }, body: { brief: "2026-07-10-news", vote: -1 } }),
    env,
  );
  const { keys } = await kv.list({ prefix: "fb:" });
  const recs = await Promise.all(keys.map(async (k) => JSON.parse(await kv.get(k.name))));
  const alice = recs.find((r) => r.reader === "alice");
  check("/submit session identity carries per token", res.status === 200 && !!alice && alice.vote === -1, JSON.stringify(recs));
}
{
  // story_id allowlist: ledger sids and editorial ed- ids pass, anything else 400s.
  const bad = await worker.fetch(req("/submit", { method: "POST", headers: AUTH, body: { brief: "b", vote: 1, story_id: "javascript:alert(1)" } }), env);
  const ed = await worker.fetch(req("/submit", { method: "POST", headers: AUTH, body: { brief: "2026-07-24-weekend", vote: 1, story_id: "ed-weekend-2026-07-24" } }), env);
  const st = await worker.fetch(req("/submit", { method: "POST", headers: AUTH, body: { brief: "b", vote: 1, story_id: "st-0123456789ab" } }), env);
  check("/submit story_id allowlist: junk -> 400, st-/ed- -> 200", bad.status === 400 && ed.status === 200 && st.status === 200, JSON.stringify([bad.status, ed.status, st.status]));
}
{
  // any authed write extends the session runway, not just readstate.
  await kv.put(`session:${TOKEN}`, JSON.stringify({ reader: "rafael", created: Date.now() - 2 * DAY }));
  await worker.fetch(req("/submit", { method: "POST", headers: AUTH, body: { brief: "b", vote: 0 } }), env);
  const sess = JSON.parse(await kv.get(`session:${TOKEN}`));
  check("/submit re-mints a session older than a day", Date.now() - sess.created < DAY, JSON.stringify(sess));
}
{
  const res = await worker.fetch(req("/propose", { method: "POST", body: { topic: "quantum networking" } }), env);
  check("/propose without session -> 401", res.status === 401, String(res.status));
}
{
  const res = await worker.fetch(req("/propose", { method: "POST", headers: AUTH, body: { topic: "quantum networking", detail: "why it matters" } }), env);
  const { keys } = await kv.list({ prefix: "fb:" });
  const recs = await Promise.all(keys.map(async (k) => JSON.parse(await kv.get(k.name))));
  const prop = recs.find((r) => r.kind === "proposal");
  check("/propose with session -> 200 + kind:proposal stored", res.status === 200 && !!prop && prop.topic === "quantum networking", JSON.stringify(recs));
}
{
  const res = await worker.fetch(req("/propose", { method: "POST", headers: AUTH, body: { detail: "no topic" } }), env);
  check("/propose without topic -> 400", res.status === 400, String(res.status));
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
  check("OPTIONS /submit from foreign origin -> no ACAO (writes are credentialed now)", res.status === 204 && res.headers.get("Access-Control-Allow-Origin") === null, String(res.headers.get("Access-Control-Allow-Origin")));
}
{
  const res = await worker.fetch(req("/drain", { method: "OPTIONS", headers: { Origin: "https://evil.example" } }), env);
  check("bridge routes keep ACAO '*'", res.status === 204 && res.headers.get("Access-Control-Allow-Origin") === "*", String(res.headers.get("Access-Control-Allow-Origin")));
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

// --- /prefs: session gate + whole-object LWW-by-ts ------------------------------------------
{
  const res = await worker.fetch(req("/prefs"), env);
  const body = await res.json();
  check("GET /prefs without session -> 401 no session", res.status === 401 && body.error === "no session", JSON.stringify([res.status, body]));
}
{
  const res = await worker.fetch(req("/prefs", { headers: AUTH }), env);
  const body = await res.json();
  check(
    "GET /prefs with session, none stored -> {topics:[], ts:0} + no-store",
    res.status === 200 && body.reader === "rafael" && Array.isArray(body.prefs.topics) &&
      body.prefs.topics.length === 0 && body.prefs.ts === 0 && res.headers.get("Cache-Control") === "no-store",
    JSON.stringify([res.status, body]),
  );
}
{
  const now = Date.now();
  const res = await worker.fetch(
    req("/prefs", { method: "POST", headers: AUTH, body: { topics: ["ai-ml", "sports", "switzerland"], ts: now } }),
    env,
  );
  const body = await res.json();
  const stored = JSON.parse(await kv.get("prefs:rafael"));
  check(
    "POST /prefs stores topics -> applied true",
    res.status === 200 && body.ok === true && body.applied === true &&
      JSON.stringify(stored.topics) === JSON.stringify(["ai-ml", "sports", "switzerland"]) && stored.ts === now,
    JSON.stringify([body, stored]),
  );
}
{
  // older ts must lose (whole-object LWW): stored set is preserved unchanged.
  const stored0 = JSON.parse(await kv.get("prefs:rafael"));
  const res = await worker.fetch(
    req("/prefs", { method: "POST", headers: AUTH, body: { topics: ["science"], ts: stored0.ts - 5000 } }),
    env,
  );
  const body = await res.json();
  const stored = JSON.parse(await kv.get("prefs:rafael"));
  check(
    "POST /prefs older ts loses -> applied false, stored set unchanged",
    body.applied === false && JSON.stringify(stored.topics) === JSON.stringify(["ai-ml", "sports", "switzerland"]),
    JSON.stringify([body, stored]),
  );
}
{
  // rs (read-filter selection, 2026-07-18): stored + echoed with the same whole-object LWW.
  const now = Date.now() + 10;
  const res = await worker.fetch(
    req("/prefs", { method: "POST", headers: AUTH, body: { topics: ["ai-ml"], rs: "unread", ts: now } }),
    env,
  );
  const body = await res.json();
  const stored = JSON.parse(await kv.get("prefs:rafael"));
  const got = await (await worker.fetch(req("/prefs", { headers: AUTH }), env)).json();
  check(
    "POST /prefs stores rs -> stored + GET echoes it",
    body.applied === true && stored.rs === "unread" && got.prefs.rs === "unread",
    JSON.stringify([body, stored, got]),
  );
}
{
  // an invalid rs coerces to "" (All) — never rejects, never stores garbage.
  const now = Date.now() + 20;
  const res = await worker.fetch(
    req("/prefs", { method: "POST", headers: AUTH, body: { topics: ["ai-ml"], rs: "bogus", ts: now } }),
    env,
  );
  const body = await res.json();
  const stored = JSON.parse(await kv.get("prefs:rafael"));
  check(
    "POST /prefs invalid rs coerces to \"\"",
    body.applied === true && stored.rs === "" && body.prefs.rs === "",
    JSON.stringify([body, stored]),
  );
}
{
  // an older-ts POST must not clobber the stored rs either (whole-object LWW covers rs).
  const now = Date.now() + 30;
  await worker.fetch(
    req("/prefs", { method: "POST", headers: AUTH, body: { topics: ["ai-ml"], rs: "read", ts: now } }),
    env,
  );
  const res = await worker.fetch(
    req("/prefs", { method: "POST", headers: AUTH, body: { topics: [], rs: "unread", ts: now - 5000 } }),
    env,
  );
  const body = await res.json();
  const stored = JSON.parse(await kv.get("prefs:rafael"));
  check(
    "POST /prefs older ts preserves stored rs",
    body.applied === false && stored.rs === "read" && body.prefs.rs === "read",
    JSON.stringify([body, stored]),
  );
}
{
  // exact tie (ts === storedTs) must lose — strict `>` guard, stored set preserved.
  const stored0 = JSON.parse(await kv.get("prefs:rafael"));
  const res = await worker.fetch(
    req("/prefs", { method: "POST", headers: AUTH, body: { topics: ["science"], ts: stored0.ts } }),
    env,
  );
  const body = await res.json();
  const stored = JSON.parse(await kv.get("prefs:rafael"));
  check(
    "POST /prefs tie (same ts) keeps existing -> applied false, set unchanged",
    body.applied === false && JSON.stringify(stored.topics) === JSON.stringify(stored0.topics),
    JSON.stringify([body, stored]),
  );
}
{
  // newer ts replaces the whole set (not merge) — dropping a topic propagates.
  const stored0 = JSON.parse(await kv.get("prefs:rafael"));
  const res = await worker.fetch(
    req("/prefs", { method: "POST", headers: AUTH, body: { topics: ["sports"], ts: stored0.ts + 5000 } }),
    env,
  );
  const body = await res.json();
  const stored = JSON.parse(await kv.get("prefs:rafael"));
  check(
    "POST /prefs newer ts replaces whole set -> applied true, set = [sports]",
    body.applied === true && JSON.stringify(stored.topics) === JSON.stringify(["sports"]),
    JSON.stringify([body, stored]),
  );
}
{
  // malformed entries drop themselves; dupes collapse; the batch survives.
  const now = Date.now() + 10000;
  const res = await worker.fetch(
    req("/prefs", { method: "POST", headers: AUTH, body: { topics: ["ai-ml", "ai-ml", "Bad Key", 42, "", "world"], ts: now } }),
    env,
  );
  const body = await res.json();
  const stored = JSON.parse(await kv.get("prefs:rafael"));
  check(
    "POST /prefs filters bad/dup keys -> stored [ai-ml, world]",
    body.applied === true && JSON.stringify(stored.topics) === JSON.stringify(["ai-ml", "world"]),
    JSON.stringify([body, stored]),
  );
}
{
  const topics = [];
  for (let i = 0; i < 51; i++) topics.push("t" + i);
  const res = await worker.fetch(req("/prefs", { method: "POST", headers: AUTH, body: { topics, ts: Date.now() } }), env);
  check("POST /prefs >50 topics -> 400", res.status === 400, String(res.status));
}
{
  const res = await worker.fetch(req("/prefs", { method: "POST", headers: AUTH, body: { topics: "ai-ml" } }), env);
  check("POST /prefs non-array topics -> 400", res.status === 400, String(res.status));
}
{
  const res = await worker.fetch(
    req("/prefs", { method: "POST", headers: AUTH, body: `{"topics":[],"pad":"${"x".repeat(70000)}"}` }),
    env,
  );
  check("POST /prefs oversize body -> 413", res.status === 413, String(res.status));
}
{
  const res = await worker.fetch(req("/prefs", { method: "OPTIONS", headers: { Origin: SITE } }), env);
  check(
    "OPTIONS /prefs from site origin -> 204 + ACAO echoed",
    res.status === 204 && res.headers.get("Access-Control-Allow-Origin") === SITE,
    JSON.stringify([res.status, res.headers.get("Access-Control-Allow-Origin")]),
  );
}
{
  const res = await worker.fetch(req("/prefs", { method: "OPTIONS", headers: { Origin: "https://evil.example" } }), env);
  check("OPTIONS /prefs from foreign origin -> 204, NO ACAO", res.status === 204 && res.headers.get("Access-Control-Allow-Origin") === null, String(res.status));
}

// --- /admin/*: source-registry actions + snapshot (2026-09-13) -----------------------------
// Fresh session token so these checks don't depend on where the earlier sections left TOKEN's
// clock. FEEDBACK_TOKEN bearer (the bridge/drain credential) is "bridge-bearer-secret" above.
const ADMTOK = "c".repeat(64);
const ADM = { Authorization: `Bearer ${ADMTOK}` };
const BEARER = { Authorization: `Bearer ${env.FEEDBACK_TOKEN}` };
const ADMIN_PREFIX = "adm:";
await kv.put(`session:${ADMTOK}`, JSON.stringify({ reader: "rafael", created: Date.now(), cred: "admin-cred" }));

// -- POST /admin/actions: auth gate --
{
  const res = await worker.fetch(req("/admin/actions", { method: "POST", body: { type: "retire", domain: "spammy.example" } }), env);
  const body = await res.json();
  check("POST /admin/actions without session -> 401 no session", res.status === 401 && body.error === "no session", JSON.stringify([res.status, body]));
}
// -- the admin is one passkey: a session from another credential, or one minted before the
// credential id was recorded on it, or any session while ADMIN_CRED_IDS is unset, is refused --
{
  const otherTok = "d".repeat(64), legacyTok = "e".repeat(64);
  await kv.put(`session:${otherTok}`, JSON.stringify({ reader: "rafael", created: Date.now(), cred: "other-cred" }));
  await kv.put(`session:${legacyTok}`, JSON.stringify({ reader: "rafael", created: Date.now() }));
  const OTHER = { Authorization: `Bearer ${otherTok}` }, LEGACY = { Authorization: `Bearer ${legacyTok}` };
  const r1 = await worker.fetch(req("/admin/actions", { method: "POST", headers: OTHER, body: { type: "retire", domain: "spammy.example" } }), env);
  const r2 = await worker.fetch(req("/admin/actions", { headers: OTHER }), env);
  const r3 = await worker.fetch(req("/admin/snapshot", { headers: OTHER }), env);
  const r4 = await worker.fetch(req("/admin/snapshot", { headers: LEGACY }), env);
  const b1 = await r1.json();
  check("admin routes refuse a session from another passkey -> 403 not the admin",
    r1.status === 403 && b1.error === "not the admin" && r2.status === 403 && r3.status === 403, JSON.stringify([r1.status, r2.status, r3.status, b1]));
  check("admin routes refuse a pre-2026-09-13 session with no cred -> 403", r4.status === 403, String(r4.status));
  const queuedBefore = [...kv.map.keys()].filter((k) => k.startsWith(ADMIN_PREFIX)).length;
  check("a refused POST queues nothing", queuedBefore === 0, String(queuedBefore));
  const closedEnv = { ...env, ADMIN_CRED_IDS: undefined };
  const r5 = await worker.fetch(req("/admin/snapshot", { headers: ADM }), closedEnv);
  check("ADMIN_CRED_IDS unset -> even the admin session is refused (fail closed)", r5.status === 403, String(r5.status));
  const r6 = await worker.fetch(req("/prefs", { headers: OTHER }), env);
  check("the passkey gate is admin-only: /prefs still answers another credential's session", r6.status === 200, String(r6.status));
}
// -- rolling a session keeps the credential id on it --
{
  const oldTok = "f".repeat(64);
  await kv.put(`session:${oldTok}`, JSON.stringify({ reader: "rafael", created: Date.now() - 2 * DAY, cred: "admin-cred" }));
  const r = await worker.fetch(req("/admin/snapshot", { headers: { Authorization: `Bearer ${oldTok}` } }), env);
  const rolled = JSON.parse(await kv.get(`session:${oldTok}`));
  check("rollSession keeps cred", r.status !== 403 && rolled.cred === "admin-cred" && Date.now() - rolled.created < DAY, JSON.stringify([r.status, rolled]));
}
// -- POST /admin/actions: valid retire, reader pinned from session, stored under adm: --
{
  const res = await worker.fetch(
    req("/admin/actions", { method: "POST", headers: ADM, body: { type: "retire", domain: "spammy.example", note: "low signal", reader: "mallory" } }),
    env,
  );
  const body = await res.json();
  const latestKey = [...kv.map.keys()].filter((k) => k.startsWith(ADMIN_PREFIX)).sort().pop();
  const stored = JSON.parse(await kv.get(latestKey));
  check(
    "POST /admin/actions retire -> 200 {ok,id,action}, reader pinned, adm: key",
    res.status === 200 && body.ok === true && typeof body.id === "string" &&
      body.action.type === "retire" && body.action.domain === "spammy.example" &&
      body.action.reader === "rafael" && stored.reader === "rafael" && stored.note === "low signal",
    JSON.stringify([res.status, body, stored]),
  );
}
// -- validation branches --
{
  const res = await worker.fetch(req("/admin/actions", { method: "POST", headers: ADM, body: { type: "nuke", domain: "a.example" } }), env);
  check("POST /admin/actions bad type -> 400", res.status === 400, String(res.status));
}
{
  const res = await worker.fetch(req("/admin/actions", { method: "POST", headers: ADM, body: { type: "retire", domain: "not a domain" } }), env);
  check("POST /admin/actions malformed domain -> 400", res.status === 400, String(res.status));
}
{
  // uppercase normalizes to lowercase rather than 400 (schema is lowercase-only).
  const res = await worker.fetch(req("/admin/actions", { method: "POST", headers: ADM, body: { type: "restore", domain: "Example.ORG" } }), env);
  const body = await res.json();
  check("POST /admin/actions uppercase domain -> 200, stored lowercase", res.status === 200 && body.action.domain === "example.org", JSON.stringify(body));
}
{
  const res = await worker.fetch(req("/admin/actions", { method: "POST", headers: ADM, body: { type: "add", domain: "a.example", streams: ["news"] } }), env);
  check("POST /admin/actions add without tier -> 400", res.status === 400, String(res.status));
}
{
  const res = await worker.fetch(req("/admin/actions", { method: "POST", headers: ADM, body: { type: "add", domain: "a.example", tier: "T2", streams: [] } }), env);
  const bad = await worker.fetch(req("/admin/actions", { method: "POST", headers: ADM, body: { type: "add", domain: "a.example", tier: "T2", streams: ["bogus"] } }), env);
  check("POST /admin/actions add empty/unknown streams -> 400", res.status === 400 && bad.status === 400, JSON.stringify([res.status, bad.status]));
}
{
  // full add: reach/status default when omitted, streams dedupe, probe kept.
  const res = await worker.fetch(
    req("/admin/actions", { method: "POST", headers: ADM, body: { type: "add", domain: "newsy.example", tier: "T1", streams: ["news", "news", "science"], probe: { url: "https://newsy.example/x", method: "proxy" }, junk: "dropped" } }),
    env,
  );
  const body = await res.json();
  check(
    "POST /admin/actions add applies reach/status defaults, dedupes streams, drops unknown keys",
    res.status === 200 && body.action.reach === "direct" && body.action.status === "probation" &&
      JSON.stringify(body.action.streams) === JSON.stringify(["news", "science"]) &&
      body.action.probe.method === "proxy" && body.action.junk === undefined,
    JSON.stringify(body),
  );
}
{
  // add with a non-https probe.url is rejected.
  const res = await worker.fetch(req("/admin/actions", { method: "POST", headers: ADM, body: { type: "add", domain: "b.example", tier: "T2", streams: ["news"], probe: { url: "ftp://b.example", method: "curl" } } }), env);
  check("POST /admin/actions add non-https probe.url -> 400", res.status === 400, String(res.status));
}
{
  // set: bad field 400; status accepts demoted (retire is separate); streams takes an array.
  const badField = await worker.fetch(req("/admin/actions", { method: "POST", headers: ADM, body: { type: "set", domain: "c.example", field: "banana", value: "x" } }), env);
  const badVal = await worker.fetch(req("/admin/actions", { method: "POST", headers: ADM, body: { type: "set", domain: "c.example", field: "tier", value: "T9" } }), env);
  const demoted = await worker.fetch(req("/admin/actions", { method: "POST", headers: ADM, body: { type: "set", domain: "c.example", field: "status", value: "demoted" } }), env);
  const streamsSet = await worker.fetch(req("/admin/actions", { method: "POST", headers: ADM, body: { type: "set", domain: "c.example", field: "streams", value: ["news", "sports"] } }), env);
  const streamsBody = await streamsSet.json();
  check(
    "POST /admin/actions set: bad field/value 400, status:demoted ok, streams:[...] ok",
    badField.status === 400 && badVal.status === 400 && demoted.status === 200 &&
      streamsSet.status === 200 && JSON.stringify(streamsBody.action.value) === JSON.stringify(["news", "sports"]),
    JSON.stringify([badField.status, badVal.status, demoted.status, streamsSet.status]),
  );
}
{
  const res = await worker.fetch(req("/admin/actions", { method: "POST", headers: ADM, body: { type: "retire", domain: "a.example", note: "x".repeat(501) } }), env);
  check("POST /admin/actions note >500 chars -> 400", res.status === 400, String(res.status));
}
{
  const res = await worker.fetch(req("/admin/actions", { method: "POST", headers: ADM, body: `{"type":"retire","domain":"a.example","note":"${"x".repeat(9000)}"}` }), env);
  check("POST /admin/actions oversize body -> 413", res.status === 413, String(res.status));
}
// -- GET /admin/actions: the queue --
{
  const noSess = await worker.fetch(req("/admin/actions"), env);
  const res = await worker.fetch(req("/admin/actions", { headers: ADM }), env);
  const body = await res.json();
  check(
    "GET /admin/actions -> 401 without session; with session {count, actions:[{key,...}]}",
    noSess.status === 401 && res.status === 200 && typeof body.count === "number" && body.count > 0 &&
      body.actions.every((a) => typeof a.key === "string" && a.key.startsWith(ADMIN_PREFIX) && typeof a.type === "string"),
    JSON.stringify([noSess.status, res.status, body.count]),
  );
}
// -- GET /admin/snapshot before any push --
{
  const noSess = await worker.fetch(req("/admin/snapshot"), env);
  const res = await worker.fetch(req("/admin/snapshot", { headers: ADM }), env);
  const body = await res.json();
  check(
    "GET /admin/snapshot -> 401 without session; 404 {error:'no snapshot yet'} before first push",
    noSess.status === 401 && res.status === 404 && body.error === "no snapshot yet",
    JSON.stringify([noSess.status, res.status, body]),
  );
}
// -- PUT /admin/snapshot: bearer gate, store verbatim + meta --
{
  const snap = { generated: "2026-09-13T10:00:00Z", head: "abc123", sources: [{ domain: "z.example" }] };
  const raw = JSON.stringify(snap);
  const unauth = await worker.fetch(req("/admin/snapshot", { method: "PUT", body: raw }), env);
  const res = await worker.fetch(req("/admin/snapshot", { method: "PUT", headers: BEARER, body: raw }), env);
  const body = await res.json();
  const stored = await kv.get("admin:snapshot");
  const meta = JSON.parse(await kv.get("admin:snapshot_meta"));
  check(
    "PUT /admin/snapshot -> 401 without bearer; with bearer {ok,bytes}, stored verbatim + meta{ts,bytes}",
    unauth.status === 401 && res.status === 200 && body.ok === true &&
      body.bytes === Buffer.byteLength(raw) && stored === raw &&
      meta.bytes === Buffer.byteLength(raw) && typeof meta.ts === "string",
    JSON.stringify([unauth.status, res.status, body, meta]),
  );
}
// -- GET /admin/snapshot after push: raw JSON string + headers --
{
  const res = await worker.fetch(req("/admin/snapshot", { headers: ADM }), env);
  const textBody = await res.text();
  check(
    "GET /admin/snapshot after push -> 200 raw string, application/json, no-store",
    res.status === 200 && textBody === JSON.stringify({ generated: "2026-09-13T10:00:00Z", head: "abc123", sources: [{ domain: "z.example" }] }) &&
      (res.headers.get("Content-Type") || "").includes("application/json") && res.headers.get("Cache-Control") === "no-store",
    JSON.stringify([res.status, res.headers.get("Content-Type"), res.headers.get("Cache-Control")]),
  );
}
{
  const res = await worker.fetch(req("/admin/snapshot", { method: "PUT", headers: BEARER, body: "{not json" }), env);
  check("PUT /admin/snapshot invalid JSON -> 400", res.status === 400, String(res.status));
}
{
  const res = await worker.fetch(req("/admin/snapshot", { method: "PUT", headers: BEARER, body: "x".repeat(4 * 1024 * 1024 + 1) }), env);
  check("PUT /admin/snapshot >4MB -> 413", res.status === 413, String(res.status));
}
// -- /admin/drain + /admin/ack: bearer gate + prefix isolation BOTH ways --
{
  const unauth = await worker.fetch(req("/admin/drain"), env);
  const res = await worker.fetch(req("/admin/drain", { headers: BEARER }), env);
  const body = await res.json();
  check(
    "GET /admin/drain -> 401 without bearer; with bearer lists only adm: records",
    unauth.status === 401 && res.status === 200 && body.count > 0 &&
      body.records.every((r) => r.key.startsWith(ADMIN_PREFIX)) &&
      !body.records.some((r) => r.key.startsWith("fb:")),
    JSON.stringify([unauth.status, res.status, body.count]),
  );
}
{
  // Prefix isolation: the FEEDBACK /drain must never surface adm: keys, and /admin/drain must
  // never surface fb: keys. Both stores are non-empty at this point (earlier /submit + /propose
  // left fb: records; the actions above left adm: records).
  const fbDrain = await (await worker.fetch(req("/drain", { headers: BEARER }), env)).json();
  const admDrain = await (await worker.fetch(req("/admin/drain", { headers: BEARER }), env)).json();
  const fbHasAdm = fbDrain.records.some((r) => r.key.startsWith(ADMIN_PREFIX));
  const admHasFb = admDrain.records.some((r) => r.key.startsWith("fb:"));
  check(
    "prefix isolation: /drain has no adm: keys AND /admin/drain has no fb: keys",
    fbDrain.records.some((r) => r.key.startsWith("fb:")) && !fbHasAdm && admDrain.records.length > 0 && !admHasFb,
    JSON.stringify([fbDrain.count, admDrain.count, fbHasAdm, admHasFb]),
  );
}
{
  // /admin/ack deletes only adm: keys; an fb: key handed to it is a no-op (and vice versa).
  const anAdmKey = [...kv.map.keys()].filter((k) => k.startsWith(ADMIN_PREFIX)).sort()[0];
  const anFbKey = [...kv.map.keys()].filter((k) => k.startsWith("fb:")).sort()[0];
  const wrongWay = await (await worker.fetch(req("/admin/ack", { method: "POST", headers: BEARER, body: { keys: [anFbKey] } }), env)).json();
  const fbStillThere = (await kv.get(anFbKey)) != null;
  const rightWay = await (await worker.fetch(req("/admin/ack", { method: "POST", headers: BEARER, body: { keys: [anAdmKey] } }), env)).json();
  const admGone = (await kv.get(anAdmKey)) == null;
  // and the feedback /ack refuses an adm: key
  const otherAdm = [...kv.map.keys()].filter((k) => k.startsWith(ADMIN_PREFIX)).sort()[0];
  const fbAck = await (await worker.fetch(req("/ack", { method: "POST", headers: BEARER, body: { keys: [otherAdm] } }), env)).json();
  const admStillThere = (await kv.get(otherAdm)) != null;
  check(
    "ack isolation: /admin/ack ignores fb: (deleted 0), deletes adm: (deleted 1); /ack ignores adm:",
    wrongWay.deleted === 0 && fbStillThere && rightWay.deleted === 1 && admGone && fbAck.deleted === 0 && admStillThere,
    JSON.stringify([wrongWay, rightWay, fbAck]),
  );
}
{
  const unauth = await worker.fetch(req("/admin/ack", { method: "POST", body: { keys: [] } }), env);
  check("POST /admin/ack without bearer -> 401", unauth.status === 401, String(unauth.status));
}
// -- CORS: /admin/actions + /admin/snapshot are site-origin; /admin/drain + /admin/ack keep '*' --
{
  const site = await worker.fetch(req("/admin/actions", { method: "OPTIONS", headers: { Origin: SITE } }), env);
  const foreign = await worker.fetch(req("/admin/actions", { method: "OPTIONS", headers: { Origin: "https://evil.example" } }), env);
  check(
    "OPTIONS /admin/actions: site origin echoed, foreign origin no ACAO",
    site.status === 204 && site.headers.get("Access-Control-Allow-Origin") === SITE &&
      foreign.status === 204 && foreign.headers.get("Access-Control-Allow-Origin") === null,
    JSON.stringify([site.headers.get("Access-Control-Allow-Origin"), foreign.headers.get("Access-Control-Allow-Origin")]),
  );
}
{
  const site = await worker.fetch(req("/admin/snapshot", { method: "OPTIONS", headers: { Origin: SITE } }), env);
  check(
    "OPTIONS /admin/snapshot: site-origin ACAO + Allow-Methods advertises PUT",
    site.status === 204 && site.headers.get("Access-Control-Allow-Origin") === SITE &&
      (site.headers.get("Access-Control-Allow-Methods") || "").includes("PUT"),
    JSON.stringify([site.headers.get("Access-Control-Allow-Origin"), site.headers.get("Access-Control-Allow-Methods")]),
  );
}
{
  const res = await worker.fetch(req("/admin/drain", { method: "OPTIONS", headers: { Origin: "https://evil.example" } }), env);
  check("admin bridge routes keep ACAO '*'", res.status === 204 && res.headers.get("Access-Control-Allow-Origin") === "*", String(res.headers.get("Access-Control-Allow-Origin")));
}

// -----------------------------------------------------------------------------------------
console.log(failures === 0 ? `PASS: all ${n} checks passed` : `FAIL: ${failures}/${n} checks failed`);
process.exit(failures === 0 ? 0 : 1);
