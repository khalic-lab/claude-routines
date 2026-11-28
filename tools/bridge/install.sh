#!/usr/bin/env bash
# Install tools/bridge/bridge.sh as the live bridge that cron runs.
#
#   tools/bridge/install.sh            # syntax check, show the diff, back up, install
#   tools/bridge/install.sh --check    # exit 0 when the installed copy matches, 1 when not
#
# BRIDGE_DIR overrides the install directory (default /usr/local/src/news-brief-ntfy-bridge,
# which also holds .env and git-credentials -- this script never reads or touches either).
# Cron keeps pointing at the installed copy, so a pushed change never runs before it is
# installed, and a broken checkout can never take the bridge down with it.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/bridge.sh"
DIR="${BRIDGE_DIR:-/usr/local/src/news-brief-ntfy-bridge}"
DEST="$DIR/bridge.sh"

bash -n "$SRC"
if [ "${1:-}" = "--check" ]; then
  cmp -s "$SRC" "$DEST" && { echo "installed copy matches $SRC"; exit 0; }
  echo "installed copy differs from $SRC"; exit 1
fi
[ -d "$DIR" ] || { echo "no bridge directory at $DIR" >&2; exit 1; }
if [ -f "$DEST" ] && cmp -s "$SRC" "$DEST"; then
  echo "already installed: $DEST matches $SRC"
  exit 0
fi
if [ -f "$DEST" ]; then
  diff -u "$DEST" "$SRC" || true
  backup="$DEST.bak-$(date +%Y%m%d-%H%M%S)"
  cp -p "$DEST" "$backup"
  echo "backup: $backup"
fi
cp "$SRC" "$DEST.tmp.$$"
chmod 755 "$DEST.tmp.$$"
mv -f "$DEST.tmp.$$" "$DEST"   # atomic: a tick starting now reads the old or the new file, never half
echo "installed: $DEST"
