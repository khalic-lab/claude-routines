#!/usr/bin/env bash
# news-brief-ntfy-bridge
# Drain pending-notifications/*.json from the claude-routines repo, POST to
# ntfy.sh, then git rm + commit + push the drained files. Runs locally via
# crontab (*/10 7-22 * * *); the RemoteTrigger sandbox has no egress to
# ntfy.sh -- see issue #50146.
#
# Source of truth (since 2026-11-28): tools/bridge/bridge.sh in the claude-routines repo.
# Cron runs the INSTALLED copy in /usr/local/src/news-brief-ntfy-bridge/, never the
# checkout this script pulls and stashes: install a change with tools/bridge/install.sh
# (syntax check, diff, timestamped backup, atomic copy). A tick logs a WARN while the two
# differ, so an uninstalled change stays visible.
#
# Config: sourced from .env next to this script. Required keys:
#   NTFY_TOPIC=...      (rotate this when going public; never commit)
#   NTFY_SERVER=https://ntfy.sh
#   REPO=/path/to/claude-routines
#
# Stub schema (one JSON object per file):
#   { "title": "...", "click": "https://...", "body": "...", "tags": "..." }
#
# Logging: self-managed -- every tick appends to ~/Library/Logs/news-brief-bridge.log
# (rotated at ~5MB, one .1 generation kept), each tick prefixed with a UTC timestamp
# line. The crontab redirect points at the same file as a belt-and-suspenders for
# pre-exec failures.
#
# Exit codes:
#   0  drained 0+ files cleanly
#   1  config missing or git pull/push failed (tick aborted; next tick retries)
#   2  one or more POSTs to ntfy failed (files left for next run)
#
# Alerts this script sends itself (ntfy, one per problem):
#   - Pages deploy errored / rebuild not sticking / rebuild request failed (pages_selfheal)
#   - local edits parked in git stash (restore_stash)
#   - git pull failing 6 ticks in a row (~an hour), and once when it recovers
#   - the edition check itself failing 3 ticks in a row, and once when it recovers
#   - a writer edition overdue (tools/health/freshness.py; once per edition)
# Each of these counts as sent only when ntfy answers 200; otherwise it is tried again on the
# next tick (a 429 or a 5xx must not swallow the one alert a problem gets).

set -euo pipefail

# cron has a minimal PATH; make sure git/jq/curl resolve.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

# --- logging: rotate + timestamp every tick (2026-07-10; /tmp is volatile and had no timestamps) ---
LOG_FILE="$HOME/Library/Logs/news-brief-bridge.log"
mkdir -p "$(dirname "$LOG_FILE")"
if [ -f "$LOG_FILE" ] && [ "$(stat -f%z "$LOG_FILE" 2>/dev/null || echo 0)" -gt 5242880 ]; then
  mv -f "$LOG_FILE" "$LOG_FILE.1"
fi
exec >> "$LOG_FILE" 2>&1
echo "== tick $(date -u '+%Y-%m-%dT%H:%M:%SZ') =="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ ! -f "$SCRIPT_DIR/.env" ]; then
  echo "ERROR: $SCRIPT_DIR/.env not found" >&2
  exit 1
fi
set -a
# shellcheck disable=SC1091
. "$SCRIPT_DIR/.env"
set +a

: "${NTFY_TOPIC:?NTFY_TOPIC not set in .env}"
: "${NTFY_SERVER:?NTFY_SERVER not set in .env}"
: "${REPO:?REPO not set in .env}"

cd "$REPO"

# Fail fast if creds aren't there instead of hanging on a TTY prompt from cron.
export GIT_TERMINAL_PROMPT=0

notify() {  # notify <title> <tags> <body> -- 0 only when ntfy answered 200; never fails the tick
  local code
  code=$(curl -sS --max-time 15 -o /dev/null -w '%{http_code}' -H "Title: $1" -H "Tags: $2" -d "$3" \
    "$NTFY_SERVER/$NTFY_TOPIC" 2>/dev/null) || true
  [ "$code" = "200" ] && return 0
  echo "WARN: ntfy alert '$1' failed to send (HTTP ${code:-000})"
  return 1
}

# --- failure streaks (2026-11-28) ---
# A failing `git pull` aborts the tick, so drains, feedback and the edition check all stall.
# 2026-10-28/29 it failed 62 ticks in a row (about 20 hours) and nothing said so. Six in a row
# (an hour of ticks) alerts once; the first good pull after that sends a recovery note. In the
# log since 2026-10-16 the only other streaks were 3 ticks or fewer (DNS blips after sleep).
# The overnight cron gap is not a failure: no tick runs, so the count does not move.
# State per streak, next to this script: .<name>-fail-count, and .<name>-alerted once the
# alert reached ntfy (so a failed send is retried, and the recovery note follows only a
# delivered alert).
streak_fail() {  # streak_fail <name> <threshold> <title> <body; %n = streak length>
  local n file="$SCRIPT_DIR/.$1-fail-count"
  n=$(cat "$file" 2>/dev/null || echo 0)
  case "$n" in ''|*[!0-9]*) n=0 ;; esac
  n=$((n + 1))
  echo "$n" > "$file" || true
  echo "$1 failure streak: $n"
  if [ "$n" -ge "$2" ] && [ ! -f "$SCRIPT_DIR/.$1-alerted" ]; then
    if notify "$3" "warning" "${4//%n/$n}"; then
      : > "$SCRIPT_DIR/.$1-alerted" || true
    fi
  fi
}
streak_ok() {  # streak_ok <name> <title> <body; %n = streak length>
  local n file="$SCRIPT_DIR/.$1-fail-count"
  n=$(cat "$file" 2>/dev/null || echo 0)
  case "$n" in ''|*[!0-9]*) n=0 ;; esac
  if [ -f "$SCRIPT_DIR/.$1-alerted" ]; then
    if notify "$2" "white_check_mark" "${3//%n/$n}"; then
      rm -f "$SCRIPT_DIR/.$1-alerted" || true
    fi
  fi
  [ "$n" -eq 0 ] || echo 0 > "$file" || true
}
pull_failed() {
  streak_fail pull 6 "Bridge: git pull failing" \
    "git pull has failed %n bridge ticks in a row. Notifications, reader feedback and the edition check are stalled until it pulls again. Last error: ${1:-unknown}"
}
pull_ok() {
  streak_ok pull "Bridge: pulling again" "git pull works again; the bridge has caught up."
}

# --- GitHub Pages deploy self-heal (rewritten 2026-07-10; see pages-deploy-wedge memory) ---
# v1 polled GET /pages `.status`, which reflects the currently-SERVED deploy, not the latest
# build attempt -- an errored build sat undetected ~22h40m on 2026-07-09 while the site served
# stale content missing that day's News brief. v2 polls GET /pages/builds/latest and handles
# two failure shapes:
#   errored              -> empty-commit retry (a poisoned SHA needs a NEW sha; rate-limited 25m)
#   built but stale SHA  -> the push/build race (build attributed to an older commit than
#                           origin/main HEAD, nothing in flight) -> POST /pages/builds to
#                           request a fresh build of the latest commit (rate-limited 25m)
# Every branch logs, including healthy and curl-failure paths -- a silent return is
# indistinguishable from a healthy check in the log, which is how v1's gap went undiagnosed.
#
# Notification policy (2026-07-11): the push/build race is ROUTINE, not exceptional --
# GitHub attributed the post-push build to the previous SHA 4x in one day, and each
# successful heal used to ping the phone ("I fixed it" x4/day = noise). Now a successful
# rebuild request is LOG-ONLY; ntfy alerts fire only when something needs a human:
#   - the errored branch (real deploy failure -> empty-commit retry), unchanged
#   - the rebuild POST fails (non-201)
#   - a SECOND rebuild request for the same head SHA (the first didn't stick -> possible
#     poisoned SHA; state file .selfheal-rebuild-ts now stores "<ts> <head_sha>")
pages_selfheal() {
  if [ "${pushed_this_run:-0}" -ne 0 ]; then
    echo "selfheal: skipped -- pushed this run, a fresh build is already in flight"
    return 0
  fi

  local cred token resp bstatus bsha head_sha recent state now last last_sha repeat code
  cred="$SCRIPT_DIR/git-credentials"
  [ -f "$cred" ] || { echo "selfheal: WARN no git-credentials; skipping"; return 0; }
  token=$(sed -E 's#^https://[^:]*:([^@]*)@github\.com.*#\1#' "$cred" | head -1)
  [ -n "$token" ] || { echo "selfheal: WARN could not read token from git-credentials; skipping"; return 0; }

  resp=$(curl -s --max-time 15 -H "Authorization: Bearer $token" -H "Accept: application/vnd.github+json" \
    https://api.github.com/repos/khalic-lab/claude-routines/pages/builds/latest 2>/dev/null) \
    || { echo "selfheal: WARN builds/latest request failed (curl); re-checking next tick"; return 0; }
  bstatus=$(printf '%s' "$resp" | jq -r '.status // "?"' 2>/dev/null || echo "?")
  bsha=$(printf '%s' "$resp" | jq -r '.commit // "?"' 2>/dev/null || echo "?")
  head_sha=$(git rev-parse origin/main 2>/dev/null || echo "?")

  case "$bstatus" in
    building|queued)
      echo "selfheal: healthy -- build in flight (status=$bstatus commit=${bsha:0:7})"
      return 0 ;;
    errored)
      recent=$(git log --since="25 minutes ago" --format='%s' 2>/dev/null | grep -c 'Auto-retry Pages deploy' || true)
      if [ "${recent:-0}" -ge 1 ]; then
        echo "selfheal: latest build errored (${bsha:0:7}) but an auto-retry fired within 25m; waiting"
        return 0
      fi
      echo "selfheal: latest build ERRORED (commit=${bsha:0:7}); pushing empty auto-retry commit"
      git -c user.email=bridge@khalic-lab -c user.name="Bridge" -c commit.gpgsign=false \
        commit -q --allow-empty -m "Auto-retry Pages deploy (status=errored)"
      if git push -q origin main; then
        curl -sS --max-time 15 -o /dev/null \
          -H "Title: Pages deploy self-heal" -H "Tags: warning,construction" \
          -d "GitHub Pages build was errored; pushed an empty retry commit to unstick the site." \
          "$NTFY_SERVER/$NTFY_TOPIC" || true
        echo "selfheal: auto-retry pushed + ntfy alert sent"
      else
        echo "selfheal: ERROR auto-retry push failed -- next tick retries"
      fi
      return 0 ;;
    built)
      if [ "$bsha" = "$head_sha" ] || [ "$head_sha" = "?" ]; then
        echo "selfheal: healthy -- built ${bsha:0:7} == origin/main"
        return 0
      fi
      # Built-but-stale: a successful build attributed to an older SHA than origin/main HEAD
      # with nothing in flight (observed 2026-07-09: build 51s after a push reported the
      # previous SHA as built while the fresh build errored). Request a build of latest.
      state="$SCRIPT_DIR/.selfheal-rebuild-ts"
      now=$(date +%s); last=0; last_sha=""
      if [ -f "$state" ]; then
        read -r last last_sha < "$state" 2>/dev/null || true   # pre-2026-07-11 format: ts only
        [ -n "${last:-}" ] || last=0
      fi
      if [ $((now - last)) -lt 1500 ]; then
        echo "selfheal: stale built SHA (${bsha:0:7} != origin/main ${head_sha:0:7}) but a rebuild was requested $((now - last))s ago; waiting"
        return 0
      fi
      repeat=0
      [ "$last_sha" = "$head_sha" ] && repeat=1
      echo "selfheal: latest successful build ${bsha:0:7} != origin/main ${head_sha:0:7}, nothing in flight -- requesting Pages build (push/build race)"
      code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 -X POST \
        -H "Authorization: Bearer $token" -H "Accept: application/vnd.github+json" \
        https://api.github.com/repos/khalic-lab/claude-routines/pages/builds 2>/dev/null || echo 000)
      echo "selfheal: rebuild request returned HTTP $code"
      printf '%s %s\n' "$now" "$head_sha" > "$state"
      if [ "$code" = "201" ]; then
        if [ "$repeat" -eq 1 ]; then
          echo "selfheal: WARN second rebuild request for the same head ${head_sha:0:7} -- the previous one did not stick; alerting"
          curl -sS --max-time 15 -o /dev/null \
            -H "Title: Pages deploy self-heal: not sticking" -H "Tags: warning,construction" \
            -d "Pages is still stale on ${head_sha:0:7} after an earlier rebuild request; requested again. If this alert repeats, the SHA may be poisoned (needs a new commit)." \
            "$NTFY_SERVER/$NTFY_TOPIC" || true
        else
          echo "selfheal: rebuild requested; routine push/build race, log-only (no alert)"
        fi
      else
        echo "selfheal: ERROR rebuild request failed (HTTP $code); alerting"
        curl -sS --max-time 15 -o /dev/null \
          -H "Title: Pages deploy self-heal FAILED" -H "Tags: rotating_light" \
          -d "Pages is stale (built ${bsha:0:7}, HEAD ${head_sha:0:7}) and the rebuild request returned HTTP $code. Manual check needed." \
          "$NTFY_SERVER/$NTFY_TOPIC" || true
      fi
      return 0 ;;
    *)
      echo "selfheal: WARN unexpected builds/latest status='$bstatus' (API change or jq failure?); re-checking next tick"
      return 0 ;;
  esac
}

# --- dirty-tree resilience (2026-07-10) ---
# The repo clone is shared with interactive Claude sessions; an uncommitted local edit used to
# abort the ENTIRE tick at `git pull --rebase` (31 occurrences in the old log), silently skipping
# the notification drain, feedback fold, AND the Pages self-heal. Now: auto-stash for the tick,
# restore after the pull. On a restore conflict the work is parked in `git stash` (never
# destroyed), the tree is reset for automation, and an ntfy alert fires.
STASHED=0
restore_stash() {
  [ "$STASHED" -eq 1 ] || return 0
  if git stash apply -q 2>/dev/null; then          # apply (not pop): entry survives a mid-apply crash
    git stash drop -q || true
    echo "auto-stash restored cleanly"
  else
    git reset --hard -q HEAD   # undo the partial apply; the work is intact in stash@{0}
    echo "ERROR: auto-stash conflicts with pulled commits -- your uncommitted changes are PARKED IN 'git stash' (stash@{0}); tree reset so automation can continue"
    curl -sS --max-time 15 -o /dev/null \
      -H "Title: Bridge: local changes parked in git stash" -H "Tags: warning" \
      -d "Uncommitted edits in $REPO conflicted with pulled commits during a bridge tick. Recover them with: git stash list / git stash pop." \
      "$NTFY_SERVER/$NTFY_TOPIC" || true
  fi
  STASHED=0
}

if [ -n "$(git status --porcelain)" ]; then
  echo "WARN: working tree dirty; auto-stashing for this tick"
  if git -c user.email=bridge@khalic-lab -c user.name="Bridge" \
       stash push -q --include-untracked -m "bridge-autostash $(date -u '+%Y-%m-%dT%H:%M:%SZ')"; then
    STASHED=1
  else
    echo "ERROR: git stash push failed; skipping this tick"
    exit 1
  fi
fi

# Rebase (not --ff-only) so local "Drained" commits land cleanly on top of any
# cloud-routine commits that pushed since the last drain. Author identity is
# pinned per-invocation so rebase doesn't need a global git config.
if ! pull_out=$(git -c user.email=bridge@khalic-lab -c user.name="Bridge" pull --rebase origin main 2>&1); then
  printf '%s\n' "$pull_out"
  echo "ERROR: git pull --rebase failed"
  git rebase --abort 2>/dev/null || true   # a mid-rebase failure leaves a rebase in progress; clear it
  restore_stash
  pull_failed "$(printf '%s' "$pull_out" | grep -m1 -E 'fatal|error|CONFLICT' | cut -c1-160)"
  pages_selfheal || true    # detection is read-only; don't let a pull failure blind the deploy check
  exit 1
fi
printf '%s\n' "$pull_out"
pull_ok
restore_stash

# Installed copy vs the repo's source of truth: log-only, so a change merged but not yet
# installed (tools/bridge/install.sh) is visible in every tick.
if [ -f "$REPO/tools/bridge/bridge.sh" ] && ! cmp -s "${BASH_SOURCE[0]}" "$REPO/tools/bridge/bridge.sh"; then
  echo "WARN: installed bridge.sh differs from tools/bridge/bridge.sh -- run tools/bridge/install.sh"
fi

# Overdue editions (2026-11-28): a writer slot two hours past with no post on main. Runs only
# after a good pull (a stale checkout would read as missing editions). One push per edition:
# an edition is marked in the state file next to this script only once ntfy took its push.
# A crash of the check itself is a streak like the pull's (three ticks, half an hour).
FRESHNESS_STATE="$SCRIPT_DIR/.freshness-alerted.json"
if [ -f "$REPO/tools/health/freshness.py" ]; then
  if fresh_out=$(python3 "$REPO/tools/health/freshness.py" --root "$REPO" --state "$FRESHNESS_STATE"); then
    streak_ok freshness "Bridge: edition check works again" \
      "tools/health/freshness.py runs again; missed-edition alerts are back on."
    while IFS=$'\t' read -r f_key f_title f_body; do
      [ -n "$f_key" ] && [ -n "$f_title" ] || continue
      echo "freshness: $f_title"
      if notify "$f_title" "warning,newspaper" "$f_body"; then
        python3 "$REPO/tools/health/freshness.py" --state "$FRESHNESS_STATE" --mark "$f_key" \
          || echo "WARN: freshness could not record '$f_key' as sent (it will alert again)"
      fi
    done <<< "$fresh_out"
  else
    echo "WARN: freshness check failed (non-fatal)"
    streak_fail freshness 3 "Bridge: edition check failing" \
      "tools/health/freshness.py has failed %n bridge ticks in a row, so a missed edition would go unnoticed. The traceback is in ~/Library/Logs/news-brief-bridge.log."
  fi
fi

# Pull reader feedback from the feedback-sink Worker KV into feedback/*.jsonl (two-phase:
# drain stages records + keys here; ack below deletes the keys only after a successful push).
# Non-fatal and idempotent: a failed drain/ack just re-drains next tick (append dedups by id).
if [ -n "${FEEDBACK_WORKER_URL:-}" ] && [ -n "${FEEDBACK_TOKEN:-}" ]; then
  python3 "$REPO/tools/feedback/feedback.py" drain || echo "WARN: feedback drain failed (non-fatal)" >&2
  # admin actions (2026-09-13): drain the /admin queue and apply it to sources/registry.yml
  python3 "$REPO/tools/admin/admin.py" drain-apply || echo "WARN: admin drain/apply failed (non-fatal)" >&2
fi

# Fold drained feedback into the story ledger (story-store migration, 2026-07-07): resolves
# story ids, appends ev:"feedback" events, flips consumed:true. Consumption is keyed on the
# ledger, not any review window. Non-fatal: a failed fold just retries next tick.
if [ -f "$REPO/tools/feedback/fold.py" ]; then
  python3 "$REPO/tools/feedback/fold.py" || echo "WARN: feedback fold failed (non-fatal)" >&2
fi

shopt -s nullglob
stubs=( pending-notifications/*.json )
shopt -u nullglob

if [ "${#stubs[@]}" -eq 0 ]; then
  echo "no pending notifications"
  # NOTE: do not exit here — drained reader feedback (above) may still need committing.
fi

drained=0
failed=0
tracked_drained=0
for stub in ${stubs[@]+"${stubs[@]}"}; do  # set -u-safe even when the array is empty
  if ! title=$(jq -r '.title // ""' "$stub" 2>/dev/null) \
     || ! click=$(jq -r '.click // ""' "$stub" 2>/dev/null) \
     || ! body=$(jq -r '.body  // ""' "$stub" 2>/dev/null) \
     || ! tags=$(jq -r '.tags  // ""' "$stub" 2>/dev/null); then
    echo "WARN: failed to parse $stub -- skipping" >&2
    failed=$((failed + 1))
    continue
  fi

  if [ -z "$title" ] || [ -z "$body" ]; then
    echo "WARN: $stub missing title or body -- skipping" >&2
    failed=$((failed + 1))
    continue
  fi

  status=$(curl -sS -o /dev/null -w "%{http_code}" \
    -H "Title: $title" \
    -H "Click: $click" \
    -H "Tags: $tags" \
    -d "$body" \
    "$NTFY_SERVER/$NTFY_TOPIC" || echo "000")

  if [ "$status" = "200" ]; then
    if git ls-files --error-unmatch "$stub" >/dev/null 2>&1; then
      git rm -q "$stub"
      tracked_drained=$((tracked_drained + 1))
    else
      rm -f "$stub"
    fi
    drained=$((drained + 1))
  else
    echo "ERROR: ntfy POST for $stub returned HTTP $status -- leaving in place" >&2
    failed=$((failed + 1))
  fi
done

# Stage any reader feedback / brief proposals drained this tick (notification removals are
# already staged via git rm above). proposals/ must be committed too: feedback.py routes
# kind=="proposal" records there, and the ack below deletes them from KV — without a commit
# they'd survive only as an uncommitted local file (gap fixed 2026-07-03).
# NB: separate adds — a single `git add feedback/ proposals/` fatals (staging NOTHING)
# whenever one pathspec matches no files, and proposals/ won't exist until the first proposal.
git add feedback/ 2>/dev/null || true
git add proposals/ 2>/dev/null || true
git add index/ledger/ 2>/dev/null || true
git add sources/ 2>/dev/null || true
git add index/admin/ 2>/dev/null || true
git add index/usage/ 2>/dev/null || true
fb_staged=0
git diff --cached --quiet -- feedback/ proposals/ index/ledger/ sources/ index/admin/ index/usage/ || fb_staged=1

if [ "${tracked_drained:-0}" -gt 0 ] || [ "${fb_staged:-0}" -eq 1 ]; then
  msg="Drained $tracked_drained notification(s)"
  if [ "$fb_staged" -eq 1 ]; then msg="$msg + reader feedback"; fi
  if ! git diff --cached --quiet -- index/admin/; then msg="$msg + admin actions"; fi
  git -c user.email=bridge@khalic-lab -c user.name="Bridge" -c commit.gpgsign=false \
    commit -q -m "$msg"
fi

# Push if we have any local commits not yet on origin (covers both: a fresh
# commit from this run AND any stranded commit from a prior run that committed
# but failed to push -- e.g. a transient auth hiccup).
pushed_this_run=0
ahead=$(git rev-list --count @{u}..HEAD 2>/dev/null || echo 0)
if [ "${ahead:-0}" -gt 0 ]; then
  if ! git push -q origin main; then
    echo "ERROR: git push failed -- $ahead commit(s) stranded; next run will retry" >&2
    exit 1
  fi
  pushed_this_run=1
fi

# Push succeeded (or nothing to push). Now it is safe to ack: delete the drained KV keys so
# they are not re-committed. A failed push exits above, so feedback stays in KV and re-drains.
if [ -n "${FEEDBACK_WORKER_URL:-}" ] && [ -n "${FEEDBACK_TOKEN:-}" ]; then
  python3 "$REPO/tools/feedback/feedback.py" ack || echo "WARN: feedback ack failed (non-fatal)" >&2
  python3 "$REPO/tools/admin/admin.py" ack || echo "WARN: admin ack failed (non-fatal)" >&2
fi

pages_selfheal || true

# admin snapshot (2026-09-13): registry + usage fold + recent actions into Worker KV for /admin/
if [ -n "${FEEDBACK_WORKER_URL:-}" ] && [ -n "${FEEDBACK_TOKEN:-}" ]; then
  python3 "$REPO/tools/admin/admin.py" snapshot-push || echo "WARN: admin snapshot push failed (non-fatal)" >&2
fi

echo "drained=$drained failed=$failed"   # the topic stays out of the log (it is the channel's only secret)

if [ "$failed" -gt 0 ]; then
  exit 2
fi
exit 0
