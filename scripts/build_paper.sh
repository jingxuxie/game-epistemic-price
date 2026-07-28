#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAPER="$ROOT/paper"
TARGET="${1:-all}"

bibtex_cmd() {
  if command -v bibtex >/dev/null 2>&1; then
    command bibtex "$@"
  elif command -v bibtex.original >/dev/null 2>&1; then
    command bibtex.original "$@"
  else
    echo "error: BibTeX is required" >&2
    exit 127
  fi
}

clean_one() {
  local stem="$1"
  rm -f "$PAPER/$stem.aux" "$PAPER/$stem.bbl" "$PAPER/$stem.blg" \
        "$PAPER/$stem.fdb_latexmk" "$PAPER/$stem.fls" "$PAPER/$stem.log" \
        "$PAPER/$stem.out" "$PAPER/$stem.synctex.gz" "$PAPER/$stem.toc"
}

build_main() {
  clean_one main
  (
    cd "$PAPER"
    pdflatex -interaction=nonstopmode -halt-on-error main.tex
    bibtex_cmd main
    pdflatex -interaction=nonstopmode -halt-on-error main.tex
    pdflatex -interaction=nonstopmode -halt-on-error main.tex
  )
}

build_supplement() {
  clean_one supplement
  (
    cd "$PAPER"
    pdflatex -interaction=nonstopmode -halt-on-error supplement.tex
    pdflatex -interaction=nonstopmode -halt-on-error supplement.tex
  )
}

build_checklist() {
  clean_one checklist
  (
    cd "$PAPER"
    pdflatex -interaction=nonstopmode -halt-on-error checklist.tex
    pdflatex -interaction=nonstopmode -halt-on-error checklist.tex
  )
}

case "$TARGET" in
  main) build_main ;;
  supplement) build_supplement ;;
  checklist) build_checklist ;;
  all) build_main; build_supplement; build_checklist ;;
  *) echo "usage: $0 [main|supplement|checklist|all]" >&2; exit 2 ;;
esac
