#!/usr/bin/env bash
# news-brief-ntfy-bridge
# Drain pending-notifications/*.json from this repo, POST to ntfy.sh, then
# git rm + commit + push the drained files. Runs locally on the user's
# machine via Claude Scheduled Skill (RemoteTrigger sandbox has no egress
# allowlist for ntfy.sh -- see issue #50146).
#
# Stub schema (one JSON object per file):
#   { "title": "...", "click": "https://...", "body": "...", "tags": "..." }
#
# Exit codes:
#   0  drained 0+ files cleanly
#   1  pull/push failed (caller decides whether to surface)
#   2  one or more POSTs failed (files left in place for next run)

set -euo pipefail

REPO="${REPO:-/Users/rflnogueira/code/claude-routines}"
NTFY_SERVER="${NTFY_SERVER:-https://ntfy.sh}"
NTFY_TOPIC="${NTFY_TOPIC:-khalic-news-96034763387a}"

cd "$REPO"

if ! git pull --ff-only origin main >/dev/null 2>&1; then
  echo "ERROR: git pull failed" >&2
  exit 1
fi

shopt -s nullglob
stubs=( pending-notifications/*.json )
shopt -u nullglob

if [ "${#stubs[@]}" -eq 0 ]; then
  echo "no pending notifications"
  exit 0
fi

drained=0
failed=0
tracked_drained=0
for stub in "${stubs[@]}"; do
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

if [ "${tracked_drained:-0}" -gt 0 ]; then
  git commit -q -m "Drained $tracked_drained notification(s)"
  if ! git push -q origin main; then
    echo "ERROR: git push failed -- next run will re-push" >&2
    exit 1
  fi
fi

echo "drained=$drained failed=$failed (sent to $NTFY_SERVER/$NTFY_TOPIC)"

if [ "$failed" -gt 0 ]; then
  exit 2
fi
exit 0
