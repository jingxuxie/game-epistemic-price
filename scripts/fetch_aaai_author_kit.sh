#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${1:-$ROOT/paper}"
mkdir -p "$DEST"

# The official AAAI page links to https://aaai.org/authorkit27/.  Some hosts
# block directory scraping, so we first try the expected direct file URLs and
# then a pinned byte-for-byte public mirror of the current 2027 kit.  The
# manuscript itself never modifies either file.
OFFICIAL_BASE="https://aaai.org/authorkit27"
MIRROR_BASE="https://raw.githubusercontent.com/panda361/academic-latex-templates/b2186f447fd89800cadea0a671b81ef4bb75a50e/templates/aaai27"

fetch_one() {
  local name="$1"
  local tmp="$DEST/.${name}.tmp"
  rm -f "$tmp"
  if curl --retry 3 --retry-delay 2 -fsSL "$OFFICIAL_BASE/$name" -o "$tmp"; then
    echo "fetched $name from AAAI"
  elif curl --retry 3 --retry-delay 2 -fsSL "$MIRROR_BASE/$name" -o "$tmp"; then
    echo "warning: AAAI direct file URL was unavailable; fetched pinned public author-kit mirror for $name" >&2
  else
    echo "error: could not fetch $name from AAAI or the pinned mirror" >&2
    exit 1
  fi
  test -s "$tmp"
  mv "$tmp" "$DEST/$name"
}

fetch_one aaai2027.sty
fetch_one aaai2027.bst

grep -q '\\ProvidesPackage{aaai2027}' "$DEST/aaai2027.sty"
grep -q 'AAAI' "$DEST/aaai2027.bst"

echo "author-kit files installed in $DEST"
