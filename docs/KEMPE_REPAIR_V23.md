# Kempe structural repair — v23 research report

**Status:** draft experimental operator, independently edge-checked, not Lean-verified, not novel by claim, not promoted.

## Motivation

The v22 methods (eight-start DSATUR and bounded five-vertex recoloring) fixed **59/64** training and **75/83** independently certified DSATUR failures, leaving 5 and 8 resistant cases respectively. This phase targets those exact residual cases.

## Structural move

A **Kempe component** is a connected component of the subgraph induced by vertices currently colored with two chosen colors a and b. Exchanging a and b **throughout that component** preserves a proper coloring: every internal edge still has different colors, and there is no edge from that component to another a/b-colored vertex outside it.

The prototype enumerates these valid swaps deterministically, then runs the existing incomplete five-vertex-change recoloring search. Limits: at most 90 distinct swaps, and 2,500 recoloring nodes per swap. It checks every produced coloring on every edge, and reports failure honestly when its bounded search cannot find an improvement.

**This is a standard Kempe-chain idea combined with bounded search. It is not asserted to be a novel graph-theoretic technique.**

## Frozen data and independent truth check

Same predeclared v21/v22 graph generator and seeds, with no dataset redesign:

- Training: 2,400 graphs, seed 20261031.
- Holdout: 2,400 graphs, previously unseen seed 20261101.
- Orders 10, 12, 14, 16; densities 0.15–0.75; 120 graphs/cell.
- Independent exact k-colorability decision procedure supplies a valid smaller-color witness for each DSATUR failure and acts solely as an **evaluation oracle**.
- Kempe repairs are only run when v22 fails; this is a *conditional repair effectiveness study*, **not** a real-world end-to-end runtime comparison.

| Metric | Training | Holdout |
| --- | ---: | ---: |
| Independently certified DSATUR failures | 64 | 83 |
| Fixed by v22 repairs | 59 | 75 |
| Additional fixes using Kempe + recoloring | **4** | **4** |
| **Total fixed** | **63 / 64** | **79 / 83** |
| Still unresolved | **1** | **4** |

Overall conditional repair success: 98.4% of training failures; 95.2% of holdout failures.

Two concrete previously unresolved **14-vertex** cases are now solved:

- Training graph (density 0.60, index 113): DSATUR needed 6; structural repair found 5 via a swap of colors 1 and 5 on the component containing vertices 5 and 11, followed by bounded recoloring.
- Holdout graph (density 0.45, index 4): DSATUR needed 5; structural repair found 4 via a swap of colors 0 and 4 on vertices 1 and 9, followed by bounded recoloring.

The complete graphs, before/after coloring assignments, swaps, and exact witness colorings are in the CI ledger.

## Interpretation and remaining gates

The result shows **replicable finite-data improvement over the prior two prototypes**, not a new theorem or universal approximation guarantee. The 5 remaining failures (1 training, 4 holdout) are retained for the next attempt. The proof that Kempe swaps preserve proper coloring has a straightforward mathematical justification above, but has **not** yet been translated into a Lean kernel theorem.

Before promotion: compare with established Kempe-recoloring algorithms, assess runtime without exact-oracle preselection, introduce new graph families and vertex relabeling holdouts, and build a Lean proof of generic swap validity if a mathematically useful reusable lemma emerges.

## Reproduce

`PYTHONPATH=. python -m unittest tests.test_kempe_repair_lab -v`

`PYTHONPATH=. python scripts/experiment_kempe_repair.py`

The GitHub Actions workflow `.github/workflows/kempe-repair.yml` uploads `kempe-repair-ledger.json`.
