# v27 DSATUR bipartite-optimality audit

**Status:** known theorem independently checked against implementation. Not a novel Witnora discovery. No Lean kernel proof yet.

## Background

The saturation-degree greedy coloring algorithm DSATUR is known to be **optimal on bipartite graphs**. This result is attributed to Brélaz (1979), and also documented in the JGraphT saturation-degree coloring implementation:

- https://jgrapht.org/javadoc/org.jgrapht.core/org/jgrapht/alg/color/SaturationDegreeColoring.html
- https://github.com/jgrapht/jgrapht/blob/master/jgrapht-core/src/main/java/org/jgrapht/alg/color/SaturationDegreeColoring.java

A bipartite graph with at least one edge has chromatic number two; an edgeless nonempty graph has chromatic number one. If standard DSATUR is bipartite-optimal, it cannot return three colors where two suffice.

## Proof idea (informal, not Lean-verified)

In a connected bipartite component, after DSATUR colors its first vertex, there is always an uncolored neighbor of the colored connected region until the entire component has been colored. Such a frontier vertex has positive saturation. Because DSATUR prioritizes highest saturation, it selects a vertex on the colored frontier before starting a new uncolored component.

Inductively the colored part of a connected bipartite component has the consistent two-side coloring: every colored neighbor of the selected frontier vertex lies in the opposite bipartition side and has the same color. Thus the smallest available color never exceeds the component's two-color palette. When the component finishes, the process repeats in any remaining component.

This is a conventional proof sketch; the full invariant and algorithmic refinement are not formalized here.

## Independent implementation audit

A BFS parity checker returns a separate explicit bipartition for each graph. The Python DSATUR implementation is challenged against this independently generated two-coloring obligation.

| Sample | Count |
| --- | ---: |
| All labeled simple graphs with 1–6 vertices | 33,867 |
| Of those, bipartite | **5,604** |
| Additional seeded bipartite graphs, orders 8/12/16 | **3,600** |
| DSATUR optimality violations | **0** |
| Bipartite graphs assigned three or more colors | **0** |

The CI workflow passed both regression tests and the exhaustive/seeded audit.

## Consequence for the v26 selector

The chosen rule was `uncertified_k_ge_4`: attempt repair only if DSATUR used at least four colors and we have not witnessed a clique proving optimality.

The rule's **k >= 4** portion has more support than we initially gave it: under the known DSATUR bipartite-optimality theorem, any suboptimal DSATUR solution must use at least four colors. Why? If it used at most three colors while being suboptimal, the true optimum would be at most two. A graph with chromatic number at most two is bipartite, and standard DSATUR would then be optimal—a contradiction. The cases with zero or one vertex follow directly.

The **clique certificate** portion is also a mathematically sound stopping condition: an exhibited clique of size k and a proper k-coloring certify equality of lower and upper bounds.

**Important distinction:** the theorem about standard DSATUR is known externally. The audit gives strong finite evidence our implementation follows it, but the Python-to-Lean refinement and kernel proof remain unfinished. Until they are done, do not report the implementation-specific conclusion as Lean-proven.

## Next proof obligations

1. Represent a finite simple graph, bipartition, and algorithm coloring states in Lean.
2. Prove saturation-first selection preserves the partially connected, bipartition-consistent coloring invariant.
3. Derive that the algorithm never introduces a third color on a bipartite input.
4. Connect the Lean algorithm to the Python implementation's deterministic tie-breaking and all edge-validation paths.
5. Separately formalize the witnessed-clique lower bound and proper-coloring upper bound.

Keep this distinct from Witnora's outstanding TC-063 XOR-CNF/G5/G14 verification obligations.

## Reproduction

`PYTHONPATH=. python -m unittest tests.test_dsatur_bipartite_audit -v`

`PYTHONPATH=. python scripts/experiment_dsatur_bipartite_audit.py`

CI uploads `dsatur-bipartite-audit-ledger.json`.
