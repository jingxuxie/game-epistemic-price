# Anonymous reproducibility artifact

This archive accompanies an anonymous paper on bounded one-way communication
under private game models. It contains the complete paper source, technical
supplement, completed venue checklist, exact solvers, deterministic experiments,
raw result tables, figures, tests, and validation scripts.

Quick validation:

```bash
python -m pip install --no-build-isolation -e ".[dev]"
bash scripts/validate.sh
```

The manuscript falls back to an unofficial local preview style when the
unmodified AAAI-27 files are absent. For venue-format validation, run
`scripts/fetch_aaai_author_kit.sh` first and inspect all resulting PDFs.
