#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHONPATH=src pytest -q
PYTHONPATH=src python experiments/run_all.py
python experiments/plot_results.py
python scripts/check_results.py
bash scripts/build_paper.sh all
bash scripts/pdf_preflight.sh

echo "full validation: OK"
