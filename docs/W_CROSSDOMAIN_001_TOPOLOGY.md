# W-CROSSDOMAIN-001 — Algebraic topology × source-CNF structure

**Status: exploratory exact structural diagnostic; no algorithmic novelty,
complexity theorem, performance prediction, or SAT/UNSAT certification.**

## Why look outside SAT?

Algebraic topology describes holes using homology and Betti numbers. We ask
whether a topological descriptor of a formula's variable-interaction graph
adds useful information beyond variable count, clause count, density,
ordinary component count and small separators. This is a hypothesis about
empirical solver behavior, **not** an established relationship.

Prior art and mathematical background:

- Edelsbrunner / computational topology and clique-complex homology, e.g.
  *Computational Topology for Data Analysis*,
  https://www.cs.purdue.edu/homes/tamaldey/book/CTDAbook/CTDAbook.pdf
- *Topology and Adjunction in Promise Constraint Satisfaction*, a separate
  established application of topology to a constraint-solving complexity
  setting: https://doi.org/10.1137/20M1378223
- Standard #SAT structural algorithms based on treewidth (Samer and Szeider):
  https://www.ac.tuwien.ac.at/files/pub/SamerSzeider10.pdf

These sources do not establish the proposed Betti-number predictor. Claims
of an unconditional P-versus-NP solution from informal topology analogies
are outside this experiment and are **not** accepted as proof.

## Exact quantity

Start from the source-CNF primal graph. Turn each clique into a simplex (the
*flag complex*). Work over GF(2). The first Betti number is

`beta_1 = |E| - |V| + beta_0 - rank_GF2(boundary_2)`.

Here `boundary_2` maps each triangle to its three edges. Compute its rank by
exact binary column elimination. This descriptor is not invariant under
logically equivalent CNF rewrites and **ignores literal polarities**.

The Rust `witnora_structure` binary reports `primal_flag_beta1_mod2` and
`primal_flag_triangle_count` for at most 16 declared variables (120 possible
edges; one `u128` per binary boundary column). It returns JSON `null` above
that cap rather than guessing. An independent Python implementation performs
GF(2) reduction with sets, and the 300-source randomized differential suite
compares the two representations.

## Two finite, falsifiable controls

1. **Matched density:** The 5-variable/6-edge bowtie and chorded-cycle graphs
   have the same source size and graph density. Bowtie has minimum separator
   order 1 and flag `beta_1=0`; chorded cycle has order 2 and `beta_1=1`.
   This is not independent of separator structure.
2. **Matched separator order:** The following *positive binary CNFs* are both
   connected with 6 variables, 7 clauses/edges and minimum separator order 2:
   - A: `(1,2),(1,3),(1,4),(2,3),(2,5),(4,6),(5,6)` — flag `beta_1=1`;
     exactly 16 satisfying assignments by direct 64-assignment enumeration.
   - B: `(1,2),(1,3),(1,4),(2,5),(2,6),(3,5),(4,6)` — flag `beta_1=2`;
     exactly 17 satisfying assignments by the same independent enumeration.

These examples prove only that the topology feature is not determined by
those coarse measurements. Two data points do **not** establish correlation
with model count, SAT hardness, or solving runtime.

## Next gate

For held-out, signed-CNF families, measure whether `beta_1` improves
prediction of runtime/memory *after controlling* for `(n,m,E)`, separator
order, approximate/exact treewidth, and solver settings. Use multiple seeds,
multiple algorithm families, external exact counters and SAT solvers,
malformed-source controls, and counterexamples with the same primal graph
but opposite SAT verdicts. If no statistically reproducible improvement
appears, retire the feature as a curiosity rather than adding overhead to
the solver.
