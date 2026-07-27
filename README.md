# The Epistemic Price of Coordination

**Status:** research draft and exact reproducibility artifact; not peer reviewed.

This repository studies cooperative agents that face the same true task but
observe different private descriptions of its payoffs, action semantics, or
observation process. A sender may transmit a bounded one-way pre-play
*handshake*. The central quantity is the **epistemic price of coordination
(EPoC)**: the smallest worst-case regret, relative to a world-aware oracle,
achievable with a fixed message alphabet.

## Current contribution package

The draft develops and validates the following results.

- Zero-message threshold feasibility is a CSP. With two actions per agent it
  reduces to 2-SAT; with three actions it is NP-complete even for binary payoffs.
- The exact one-way message requirement is the chromatic number of a
  compatibility hypergraph, not generally an ordinary pairwise conflict graph.
- A projective-plane family has an empty pairwise conflict graph but requires
  exactly `q + 1` messages, giving an unbounded separation.
- One-receiver set systems reduce exactly to hitting set. Convex response sets
  have Helly-bounded obstruction size; interval responses admit an exact greedy
  algorithm; fixed-message feasibility is tractable on bounded-treewidth type
  graphs.
- Metric action-dictionary games reduce exactly to robust metric center, and a
  noisy odd-cycle family has a closed-form loss--communication frontier.
- A general full-revelation theorem identifies the irreducible minimax loss
  inside each observational type cell, even after the sender reveals its type.
- Exact MILP experiments isolate communication-repairable convention mismatch
  from irreducible uncertainty caused by an unobserved model channel.

The repository includes the paper, complete supplementary proofs, exact
solvers, unit tests, raw CSV/JSON results, and scripts that regenerate every
figure.

## Reproduced results

The committed artifacts currently verify:

- projective-plane orders `q = 2, 3, 5, 7, 11, 13`, with exact message count
  `q + 1`; at `q = 13`, pairwise reasoning predicts one message while the exact
  requirement is 14;
- the exact noisy-lever formula for 15 combinations of noise radius and bit
  budget;
- 140 seeded random set systems, where the exact higher-order requirement is
  about 1.55 times the pairwise prediction on average and up to 3 times larger;
- exact interval greedy/MILP agreement on all audit instances and scaling to
  10,000 sender types;
- an ambiguous action-dictionary example where full sender revelation still
  leaves robust EPoC `0.5`.

See [`results/summary.json`](results/summary.json) and
[`docs/proof_notes.md`](docs/proof_notes.md).

## Installation and tests

Python 3.10 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pytest -q
```

## Reproduce experiments and figures

```bash
python experiments/run_all.py
python experiments/plot_results.py
```

The first command overwrites the exact tables under `results/`; the second
regenerates PDF and PNG figures under `paper/figures/`.

## Build the manuscript

```bash
make paper
make supplement
```

The repository includes `paper/aaai2027-fallback.sty` only for local preview.
Before any AAAI submission, download the current official AAAI-27 author kit and
place the **unmodified** `aaai2027.sty` and `aaai2027.bst` files in `paper/`,
then rebuild and inspect the resulting PDF. The fallback is not a submission
style and must not be substituted for the official kit.

## Anonymous-submission warning

This is a public author-owned repository. Do **not** put its URL in an anonymous
submission. Prepare the venue's anonymous code/data archive separately, remove
Git metadata and identifying paths, and upload it through the venue's permitted
supplementary-material mechanism. The paper itself contains no repository URL.

## Repository map

- `src/epcoord/`: game representation, MILP, 2-SAT, set-system, and theory helpers
- `tests/`: exact unit and cross-check tests
- `experiments/`: deterministic experiment and plotting scripts
- `results/`: committed raw tables and summary
- `paper/`: main manuscript, supplement, bibliography, and figures
- `docs/`: proof audit, roadmap, reproducibility, and submission checklists

## Scope and limitations

The current paper concerns finite two-agent common-payoff games, deterministic
one-way pre-play messages, and worst-case world sets. It does not yet solve
interactive communication, many-agent teams, positive-regret randomization, or
large learned environments. Several algorithmic ingredients (2-SAT, hitting
set, Helly's theorem, treewidth CSP dynamic programming, and metric center) are
classical; the draft explicitly distinguishes inherited machinery from the new
private-game-model formulation, higher-order separation, and exact frontier
results.

## License

Code is released under the MIT License. Manuscript text and figures remain
copyright of their authors unless separately licensed.
