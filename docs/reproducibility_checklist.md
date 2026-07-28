# Reproducibility checklist

## Claims and artifacts

- [x] Every numerical claim in the main manuscript maps to a committed CSV or
  `results/summary.json` field.
- [x] `scripts/check_results.py` asserts the invariants quoted in the paper.
- [x] All plotted figures are regenerated from committed raw tables.
- [x] Random experiments use fixed seeds.
- [x] The exact solver decodes and independently reevaluates each incumbent.
- [x] Solver time limits and numerical failures are distinct from infeasibility.
- [x] Full proofs appear in `paper/supplement.tex`.

## Environment

- Python: 3.10 or newer
- Main dependencies: NumPy, SciPy, pandas, matplotlib
- Exact optimization: `scipy.optimize.milp` with HiGHS
- TeX: PDFLaTeX plus BibTeX, using the unmodified current AAAI-27 style for
  venue-format validation
- Hardware: single CPU; no GPU or external datasets are required

## One-command reproduction

```bash
python -m pip install --no-build-isolation -e ".[dev]"
bash scripts/fetch_aaai_author_kit.sh
bash scripts/validate.sh
```

## Expected checks

- 29 tests pass.
- Projective-plane exact message counts equal `q+1` for all audited orders.
- All 25 large-cycle and 169 exhaustive small-cycle configurations match the
  closed form.
- Grid protocol MILP agrees with exact metric center on all audited settings.
- Farthest-first never exceeds a factor two in the finite-grid audit.
- Main PDF has at most nine pages, with pages after seven containing references
  only; fonts are embedded and non-Type-3.
- Anonymous archive contains no author/repository/path identifiers.

## Nondeterministic fields

Wall-clock timing columns are machine dependent. The manuscript uses timing
only as a scalability sanity check and does not rely on exact timing values for
scientific conclusions.
