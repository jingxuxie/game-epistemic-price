# Literature and novelty audit

Last audited: 2026-07-26. This document records positioning decisions; it is not
a claim that the search is exhaustive.

## Closest conceptual lineages

### Zero-error coordination and side information

- McEliece and Posner (1971) formulate the Hide-and-Seek source-coding problem.
- Witsenhausen (1976) connects zero-error side information to chromatic numbers.
- Abroshan, Gohari, and Jaggi (2015) formulate set coordination and explicitly
  recover one-way Hide-and-Seek and Witsenhausen-style special cases.

**Implication for our claims.** Generic graph-coloring, hitting-set, and
zero-error permissible-action connections are prior machinery. The paper does
not claim those reductions in isolation. Its contribution is the
payoff-sensitive EPoC frontier for private game models, the exact compatibility
hypergraph characterization at each regret tolerance, an unbounded pairwise
failure construction, and structural regimes in which higher-order
obstructions collapse.

### Team decision theory and communication equilibria

Marschak and Radner study jointly designed decisions under decentralized
information. Forges studies incentive-compatible mediated communication in
Bayesian games.

**Distinction.** Our players have identical payoffs and commit to a protocol;
truthful reporting and incentive compatibility are not the bottleneck. The
object is worst-case oracle-relative loss under a bounded message vocabulary.

### Zero-shot coordination

Other-Play and later population/curriculum methods address convention mismatch
between independently trained policies. Noisy zero-shot coordination is the
closest learning formulation: each agent sees a noisy private Dec-POMDP, while
the ground-truth distribution and noise process remain common knowledge.

**Distinction.** The present paper removes training, permits an ambiguity set of
model-generation processes, explicitly varies a pre-play message budget, and
separates compressible convention mismatch from latent uncertainty inside an
observational type cell.

### Metric center and robust clustering

Gonzalez's farthest-first traversal gives the classical factor-two guarantee
for metric k-center. Robust and uncertain clustering are broad established
areas; Xu and Zhang (2025) study uncertain points on graphs under a weighted
expected-distance objective. That objective differs from our deterministic
worst-case private-dictionary loss, but it is a close modern comparison and is
now cited explicitly.

**Implication for our claims.** We do not claim a new k-center algorithm. The
new statement is an exact reduction showing when private action dictionaries
contribute no extra EPoC beyond physical center quantization, followed by an
exact odd-cycle formula when sender-target and receiver-dictionary uncertainty
are both present.

## Claim-by-claim risk assessment

| Claim | Prior overlap | Current wording decision |
|---|---|---|
| EPoC definition | Regret/communication tradeoffs are broadly classical | Present as a problem formulation specialized to private game models, not as the first communication-value frontier in all settings |
| Binary-action 2-SAT / three-action hardness | Standard binary-CSP and 3-coloring tools | Claim the sharp boundary for this formal model; expose full reduction |
| Compatibility hypergraph coloring | Hypergraph coloring is classical | Claim exact characterization for EPoC threshold classes, not invention of hypergraph coloring |
| Projective-plane separation | Finite-geometry hitting arguments are classical | Claim this explicit unbounded pairwise failure in epistemic coordination; proof is included |
| Hitting set / Helly / intervals / treewidth | Classical | Label explicitly as inherited specializations and positive structure |
| Metric dictionary reduction | Metric center is classical | Claim exact equivalence of protocol design and robust center under bijective private isometries |
| Additive cycle frontier | No identical formula found in audited sources | Present as the strongest new closed-form result, with exhaustive independent checks |
| Full-revelation floor | Minimax decision under observational equivalence is classical in spirit | Present as a useful exact characterization inside the EPoC model |

## Required human checks before submission

1. Have a game-theory or information-theory colleague independently search
   for higher-order permissible-action partitions described directly as
   hypergraph coloring; the targeted 2026-07-26 search found no exact collision,
   but this is not an exhaustive novelty guarantee.
2. Independently audit robust/uncertain $k$-center for a theorem identical to
   the two-sided odd-cycle dilation and inverse communication threshold. The
   closest recent graph-uncertainty paper uses expected rather than worst-case
   cost and does not expose the communication decomposition.
3. Verify every recent bibliography entry against the publisher or arXiv page.
4. Have a game-theory or information-theory colleague independently read the
   hardness, projective-plane, and additive-cycle proofs.
