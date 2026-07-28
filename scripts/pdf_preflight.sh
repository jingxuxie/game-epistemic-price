#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAIN="$ROOT/paper/main.pdf"
SUPP="$ROOT/paper/supplement.pdf"
CHECKLIST="$ROOT/paper/checklist.pdf"

for file in "$MAIN" "$SUPP" "$CHECKLIST"; do
  test -s "$file" || { echo "error: missing $file" >&2; exit 1; }
done

main_pages="$(pdfinfo "$MAIN" | awk '/^Pages:/ {print $2}')"
supp_pages="$(pdfinfo "$SUPP" | awk '/^Pages:/ {print $2}')"
checklist_pages="$(pdfinfo "$CHECKLIST" | awk '/^Pages:/ {print $2}')"
[[ "$main_pages" =~ ^[0-9]+$ ]] && [[ "$supp_pages" =~ ^[0-9]+$ ]] && [[ "$checklist_pages" =~ ^[0-9]+$ ]]
(( main_pages <= 9 )) || { echo "error: main PDF has $main_pages pages (limit 9)" >&2; exit 1; }
(( supp_pages >= 1 )) || { echo "error: empty supplement" >&2; exit 1; }
(( checklist_pages >= 1 )) || { echo "error: empty checklist" >&2; exit 1; }

# Every page beyond seven must be references only.  Search page 8 onward for
# section headings or theorem-like main-content markers.
if (( main_pages > 7 )); then
  tail_text="$(pdftotext -f 8 -l "$main_pages" -layout "$MAIN" -)"
  if printf '%s\n' "$tail_text" | grep -Eiq '(^|[[:space:]])(Introduction|Experiments|Conclusion|Theorem|Proposition|Figure|Table)[[:space:]]*[0-9]*'; then
    echo "error: non-reference-looking content detected after page 7" >&2
    exit 1
  fi
fi

for file in "$MAIN" "$SUPP" "$CHECKLIST"; do
  width="$(pdfinfo "$file" | awk '/^Page size:/ {print $3}')"
  height="$(pdfinfo "$file" | awk '/^Page size:/ {print $5}')"
  [[ "$width" == "612" && "$height" == "792" ]] || {
    echo "error: $file is not US letter (got ${width}x${height})" >&2; exit 1;
  }
  if pdffonts "$file" | tail -n +3 | awk '{if ($(NF-4) != "yes") bad=1} END {exit bad ? 0 : 1}'; then
    echo "error: unembedded font in $file" >&2
    pdffonts "$file" >&2
    exit 1
  fi
  if pdffonts "$file" | tail -n +3 | awk '{if ($2 == "Type" && $3 == "3") bad=1} END {exit bad ? 0 : 1}'; then
    echo "error: Type 3 font in $file" >&2
    pdffonts "$file" >&2
    exit 1
  fi
done

text="$(pdftotext "$MAIN" -; pdftotext "$SUPP" -; pdftotext "$CHECKLIST" -)"
# The public-facing manuscript must visibly identify itself as anonymous and
# must not carry a non-anonymous PDF Author metadata field.  Project-specific
# identity strings are scanned by the outer packaging workflow.
if ! grep -Fqi 'Anonymous submission' <<<"$text"; then
  echo "error: anonymous-submission marker missing from PDFs" >&2
  exit 1
fi
for file in "$MAIN" "$SUPP" "$CHECKLIST"; do
  author="$(pdfinfo "$file" | sed -n 's/^Author:[[:space:]]*//p')"
  if [[ -n "$author" && "${author,,}" != *anonymous* ]]; then
    echo "error: non-anonymous PDF Author metadata in $file: $author" >&2
    exit 1
  fi
done

for log in "$ROOT"/paper/main.log "$ROOT"/paper/supplement.log "$ROOT"/paper/checklist.log; do
  if grep -Eiq 'undefined references|undefined citations|Citation .* undefined|Reference .* undefined|Overfull \\hbox|Overfull \\vbox' "$log"; then
    echo "error: LaTeX warning requiring inspection in $log" >&2
    grep -Ei 'undefined references|undefined citations|Citation .* undefined|Reference .* undefined|Overfull \\hbox|Overfull \\vbox' "$log" >&2
    exit 1
  fi
done

echo "PDF preflight: main=${main_pages} pages, supplement=${supp_pages} pages, checklist=${checklist_pages} pages, letter paper, embedded non-Type-3 fonts, anonymous"
