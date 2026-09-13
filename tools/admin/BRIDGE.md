# Bridge wiring for the admin path

`tools/admin/admin.py` is the bridge-side client for the admin queue (PLAN 2026-09-13 §2.5). It runs
on the Mac, inside the existing local bridge `/usr/local/src/news-brief-ntfy-bridge/bridge.sh` — a
file **outside this repo**. This document is the exact edit the architect applies to `bridge.sh`; the
repo never edits it.

All four hooks use the credentials the feedback path already reads (`FEEDBACK_WORKER_URL`,
`FEEDBACK_TOKEN`) plus `REPO`, all already exported in the bridge's `.env`. Every call is guarded
with `|| echo "WARN…"` so a bad tick stays non-fatal under the script's `set -euo pipefail` — one
admin failure must never abort the notification drain or the Pages self-heal.

Two of these lines differ from the literal PLAN §2.5 text; both differences are corrections, marked
**[correction]** below, and are load-bearing.

---

## 1. Drain + apply — inside the feedback-drain guard

The bridge already has this block (drains reader feedback before the commit):

```sh
# Pull reader feedback from the feedback-sink Worker KV into feedback/*.jsonl (two-phase …).
if [ -n "${FEEDBACK_WORKER_URL:-}" ] && [ -n "${FEEDBACK_TOKEN:-}" ]; then
  python3 "$REPO/tools/feedback/feedback.py" drain || echo "WARN: feedback drain failed (non-fatal)" >&2
fi
```

Add the admin drain/apply **as a second line inside the same `if`**, right after the feedback drain
(it needs the same creds, and its writes to `sources/registry.yml` + `index/admin/actions.jsonl`
must land before the staging block below):

```sh
if [ -n "${FEEDBACK_WORKER_URL:-}" ] && [ -n "${FEEDBACK_TOKEN:-}" ]; then
  python3 "$REPO/tools/feedback/feedback.py" drain || echo "WARN: feedback drain failed (non-fatal)" >&2
  python3 "$REPO/tools/admin/admin.py" drain-apply || echo "WARN: admin drain/apply failed (non-fatal)" >&2
fi
```

---

## 2. Staging — separate `git add` lines, extended diff check

The bridge stages feedback/proposals/ledger before committing:

```sh
git add feedback/ 2>/dev/null || true
git add proposals/ 2>/dev/null || true
git add index/ledger/ 2>/dev/null || true
fb_staged=0
git diff --cached --quiet -- feedback/ proposals/ index/ledger/ || fb_staged=1
```

Add `sources/`, `index/admin/`, and `index/usage/` as **separate** `git add` lines (each `2>/dev/null
|| true`), and extend the one diff check to cover them:

```sh
git add feedback/ 2>/dev/null || true
git add proposals/ 2>/dev/null || true
git add index/ledger/ 2>/dev/null || true
git add sources/ 2>/dev/null || true
git add index/admin/ 2>/dev/null || true
git add index/usage/ 2>/dev/null || true
fb_staged=0
git diff --cached --quiet -- feedback/ proposals/ index/ledger/ sources/ index/admin/ index/usage/ || fb_staged=1
```

**[correction]** PLAN §2.5 item 2 writes `git add sources/ index/admin/ index/usage/` as one command.
It must be three separate adds: `index/admin/` and `index/usage/` do not exist until the first admin
action / usage record, and the bridge's own comment records that a single `git add A/ B/` **fatals,
staging nothing**, whenever one pathspec matches no files. The `git diff --cached` check may take all
paths in one call (a non-matching pathspec there is harmless).

Then extend the commit message so an admin batch is visible in the log. The block is:

```sh
if [ "${tracked_drained:-0}" -gt 0 ] || [ "${fb_staged:-0}" -eq 1 ]; then
  msg="Drained $tracked_drained notification(s)"
  if [ "$fb_staged" -eq 1 ]; then msg="$msg + reader feedback"; fi
  git -c user.email=bridge@khalic-lab -c user.name="Bridge" -c commit.gpgsign=false \
    commit -q -m "$msg"
fi
```

Add one line after the `+ reader feedback` line (before the `commit`):

```sh
  if [ "$fb_staged" -eq 1 ]; then msg="$msg + reader feedback"; fi
  if ! git diff --cached --quiet -- index/admin/; then msg="$msg + admin actions"; fi
```

---

## 3. Ack — after the successful push, guarded

The bridge acks feedback only after a successful push:

```sh
if [ -n "${FEEDBACK_WORKER_URL:-}" ] && [ -n "${FEEDBACK_TOKEN:-}" ]; then
  python3 "$REPO/tools/feedback/feedback.py" ack || echo "WARN: feedback ack failed (non-fatal)" >&2
fi
```

Add the admin ack **as a second line inside the same `if`**:

```sh
if [ -n "${FEEDBACK_WORKER_URL:-}" ] && [ -n "${FEEDBACK_TOKEN:-}" ]; then
  python3 "$REPO/tools/feedback/feedback.py" ack || echo "WARN: feedback ack failed (non-fatal)" >&2
  python3 "$REPO/tools/admin/admin.py" ack || echo "WARN: admin ack failed (non-fatal)" >&2
fi
```

**[correction]** PLAN §2.5 item 3 shows the ack with no `|| echo` guard. It must be guarded: under
`set -euo pipefail`, `admin.py` exits 1 on any failure (its documented behavior), so an unguarded ack
after a successful push would abort the tick and skip `pages_selfheal`. The guard matches the
feedback ack line directly above it.

---

## 4. Snapshot push — last, every tick

At the **end** of the tick, after `pages_selfheal` and before the final `echo/exit`, so a fresh
`HEAD` (post-push) is snapshotted and the page's data refreshes even on ticks with nothing to commit:

```sh
pages_selfheal || true

if [ -n "${FEEDBACK_WORKER_URL:-}" ] && [ -n "${FEEDBACK_TOKEN:-}" ]; then
  python3 "$REPO/tools/admin/admin.py" snapshot-push || echo "WARN: admin snapshot push failed (non-fatal)" >&2
fi

echo "drained=$drained failed=$failed (sent to $NTFY_SERVER/$NTFY_TOPIC)"
```

---

## Verifying after the edit

One hand-run tick (`bash bridge.sh`, or the crontab entry) should:

- write nothing to `sources/`/`index/admin/` when the queue is empty (drain-apply applies zero
  actions), and
- log `admin: snapshot pushed (<N> source(s), <bytes> byte(s) stored)`.

Then `GET /admin/snapshot` with a live browser session must return that JSON (no longer the 404 it
served before the first push).
