# Proof audit notes

These notes state the proof obligations, edge cases, and computational audits
used to keep the main paper and supplement synchronized. They are not a
substitute for independent peer review.

## 1. Zero-message CSP boundary

- For two actions, each forbidden action pair contributes a clause
  `(A_x != a) OR (B_y != b)`. There are at most four clauses per world, so the
  reduction is linear after reading the payoff/acceptability tables.
- For hardness, graph 3-coloring creates sender and receiver copies of each
  vertex. Equality worlds enforce the same color on the two copies. One
  inequality world for each oriented undirected edge enforces distinct endpoint
  colors. Rewards are binary and the construction is polynomial.
- Audit: hand instances and randomized two-action instances are cross-checked by
  the 2-SAT solver and exact MILP.

## 2. Compatibility hypergraph

- A message fiber is feasible exactly when it is a compatible sender set.
- In a finite instance, every incompatible color class contains an
  inclusion-minimal incompatible subset. Therefore proper coloring of the
  minimal-obstruction hypergraph is equivalent to a feasible protocol
  partition.
- The three-set example `{A,B}`, `{B,C}`, `{A,C}` verifies that pairwise
  intersections do not imply joint compatibility.

## 3. Projective-plane separation

- Sender types are projective lines, receiver actions are points, and a message
  class is feasible exactly when its lines share a selected point.
- Any two lines intersect, so the pairwise conflict graph is empty.
- The `q+1` points on a fixed line hit every line.
- If at most `q` points are selected, choose an unselected point `p`. The
  `q+1` lines through `p` are each hit by at most one selected point, leaving an
  unhit line.
- Exact finite-field instances for prime `q = 2,3,5,7,11,13` match `q+1`.
  The theorem is stated for prime powers because projective planes over finite
  fields exist for all prime powers; the artifact generator currently implements
  prime fields only.

## 4. Set systems, Helly structure, and intervals

- With one receiver type and trivial sender action, every message chooses one
  receiver action, so message minimization is exactly minimum hitting set.
- In the receiver-only convex subclass, incompatibility decomposes by receiver
  type. Helly's theorem then bounds an inclusion-minimal obstruction by `d+1`.
- The interval greedy exchange proof replaces the point stabbing the earliest
  ending interval by that interval's right endpoint without losing any
  previously hit remaining interval.

## 5. Treewidth dynamic program

- For fixed `M`, sender domain is `[M] x A` and receiver domain is `B^M`.
- Each observed type pair yields one binary relation after intersecting all
  worlds with that pair. Standard CSP dynamic programming over a supplied
  width-`w` decomposition yields `O(n D^(w+1))`, apart from local relation
  checks. The result is parameterized; it is not claimed polynomial when `M`
  is part of the input.

## 6. Metric dictionary reduction

- Each receiver type is a bijective isometry from local actions to physical
  outcomes, so every physical center is implementable under every dictionary.
- Target uncertainty depends only on the sender type, not on the receiver
  dictionary. Hence all receiver types solve the same robust center problem for
  a message class and may realize a common optimal physical center through
  their inverse dictionaries.
- General protocol MILP and exact metric center agree on the audited grid cases.

## 7. Exact additive odd-cycle frontier

For `K = 2h+1`, center `c`, estimate `x`, target radius `r`, and hidden bias
radius `s`, the key identity is

`max_{d(t,x)<=r, d(delta,0)<=s} d(c+delta,t) = min(h, d(c,x)+r+s)`.

- Upper bound: triangle inequality plus cycle diameter `h`.
- Lower bound when `d+r+s <= h`: move target away from `c` by `r` and move the
  realized action away in the opposite direction by `s` along a shortest arc.
- Lower bound when `d+r+s > h`: write `h-d = p+q` with `0<=p<=r` and
  `0<=q<=s`, then move target and dictionary by `p` and `q` in opposite
  directions to attain antipodal distance `h`.
- The optimal `M`-center radius on the odd cycle is the least integer `R` with
  `M(2R+1) >= K`, namely `ceil((K-M)/(2M))`.
- Monotonicity of the dilation in center distance lets minimization commute with
  the outer formula.
- Inverse threshold for `epsilon<1`: let
  `R=floor(epsilon*h)-r-s`; feasibility is equivalent to
  `M(2R+1)>=K` when `R>=0`.
- Audit: 25 `K=13` parameter combinations and all 169 admissible `(K,r,s,M)`
  combinations for `K in {3,5,7}` match the general MILP exactly.

## 8. Full-revelation floor

- Any protocol is constant on a fixed observed cell `(x,y)`, so its regret on
  that cell is at least the cellwise minimax regret.
- With at least `|X|` messages, the sender reveals `x`; the receiver chooses the
  minimax action separately for every `(x,y)` cell, attaining the lower bound.
- In cyclic action dictionaries, translation invariance converts the cellwise
  problem to the metric radius of the hidden bias set.

## 9. Solver-status safety

- Only HiGHS status 2 is accepted as an infeasibility certificate.
- A time/resource limit with no incumbent raises `TimeoutError`.
- Other unresolved failures raise `RuntimeError`.
- Every feasible incumbent is decoded and evaluated directly against every
  world before it is used in EPoC binary search.
- Regression tests monkeypatch time-limit and numerical-failure statuses to
  ensure neither is silently treated as infeasibility.
