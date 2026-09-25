#!/usr/bin/env bash
# Faithful local GitHub Pages build: the same container GitHub's own Pages action runs
# (ghcr.io/actions/jekyll-build-pages, github-pages gem, safe mode, the Pages plugin allowlist).
#
#   tools/verify/build.sh [OUT_DIR]        # default OUT_DIR=/tmp/fp-build; LOG=... overrides the log
#
# The repo is COPIED to OUT_DIR/src first (tracked + untracked-but-not-ignored files), so _site
# and .jekyll-cache never land in the working tree. The site ends up in OUT_DIR/src/_site and is
# exposed for serving under the production baseurl as OUT_DIR/www/claude-routines -> _site:
#
#   python3 -m http.server 4000 -d OUT_DIR/www    ->  http://127.0.0.1:4000/claude-routines/
#
# Needs Docker (OrbStack/Docker Desktop) and `gh auth token` (jekyll-github-metadata calls the
# API). The token is passed through the environment and never printed; the log is scanned for
# token-shaped strings after the run.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:-/tmp/fp-build}"
SRC="$OUT/src"
IMAGE="ghcr.io/actions/jekyll-build-pages:v1.0.13"
LOG="${LOG:-$OUT/build.log}"

mkdir -p "$OUT"
rm -rf "$SRC" "$OUT/www"
mkdir -p "$SRC" "$OUT/www"

# tracked + untracked (not ignored) files, so an uncommitted change is built too
(cd "$REPO" && git ls-files -z --cached --others --exclude-standard) \
  | (cd "$REPO" && rsync -a --from0 --files-from=- ./ "$SRC/")
mkdir -p "$SRC/.git"          # jekyll-github-metadata looks for a repo; the rev comes from INPUT_BUILD_REVISION

REV="$(cd "$REPO" && git rev-parse HEAD)"
echo "build: $REPO @ ${REV:0:10} -> $SRC/_site (log: $LOG)"

set +e
GH_TOKEN_VALUE="$(gh auth token 2>/dev/null)"
INPUT_TOKEN="$GH_TOKEN_VALUE" docker run --rm --platform linux/amd64 \
  -v "$SRC":/github/workspace \
  -e GITHUB_WORKSPACE=/github/workspace \
  -e INPUT_SOURCE=. -e INPUT_DESTINATION=./_site \
  -e INPUT_FUTURE=false -e INPUT_VERBOSE=true \
  -e INPUT_BUILD_REVISION="$REV" \
  -e INPUT_TOKEN \
  -e GITHUB_REPOSITORY=khalic-lab/claude-routines \
  "$IMAGE" 2>&1 | tee "$LOG" | grep --line-buffered -E 'Writing:|done in|Error|Warning|warning' | sed -u 's/^ *//'
STATUS=${PIPESTATUS[0]}
set -e
unset GH_TOKEN_VALUE

if grep -Eq 'gh[pousr]_[A-Za-z0-9]{20,}' "$LOG"; then
  echo "build: TOKEN-SHAPED STRING IN $LOG, scrubbing it" >&2
  sed -E -i '' 's/gh[pousr]_[A-Za-z0-9]{20,}/<redacted>/g' "$LOG"
fi

WARN=$(grep -Eci 'liquid (warning|exception|syntax error)|Liquid Exception|Error:' "$LOG" || true)
GEMWARN=$(grep -c "can't satisfy your Gemfile" "$LOG" || true)
echo "build: exit $STATUS, liquid warnings/errors: $WARN, Gemfile warnings: $GEMWARN, pages: $(find "$SRC/_site" -name '*.html' | wc -l | tr -d ' ') html"
ln -sfn "$SRC/_site" "$OUT/www/claude-routines"
[ "$STATUS" -eq 0 ] && [ "$WARN" -eq 0 ] && [ "$GEMWARN" -eq 0 ]
