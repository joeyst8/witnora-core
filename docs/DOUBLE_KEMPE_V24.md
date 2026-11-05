# Double Kempe repair v24 — frozen adversarial study

**Status:** research draft, finite checked witnesses, no new-theorem or novelty claim, no Lean promotion.

## Question

The v23 pipeline fixed 63/64 known DSATUR failures on training graphs and 79/83 on independently seeded holdouts. Would *two* successive color-component swaps allow the bounded recoloring procedure to escape the five remaining hard instances?

## Mechanism

For each proper coloring, a Kempe swap exchanges two colors throughout one connected component of the subgraph induced by those two colors. Each swap preserves the proper-coloring invariant, including when a color class disappears. This v24 prototype considers a pair of such swaps and then invokes a bounded five-vertex-change recoloring search.

To prevent an exhaustive solver from masquerading as a lightweight repair, the implementation fixes:

- First-swap candidates: at most 30.
- Second-swap candidates per first: at most 30.
- Distinct two-swap candidates: at most 500.
- Recoloring recursion budget per candidate: at most 1,200 nodes.
- Every returned coloring checked on all edges.

All methods are existing-style local search; **mathematical novelty is not claimed**.

## Predeclared test

Same frozen labeled graphs and seeds as v21–v23: training seed `20261031`, previously unused holdout seed `20261101`; 2,400 graphs per split, vertex orders 10/12/14/16 and densities 0.15/0.30/0.45/0.60/0.75. An independent exact k-colorability checker identifies DSATUR's genuine failures but is not used to construct a repair. The heavier two-swap repair runs only on v23-unresolved instances, so no end-to-end runtime advantage is claimed.

| Measure | Training | Holdout |
| --- | ---: | ---: |
| Total graphs | 2,400 | 2,400 |
| Independent DSATUR failures | 64 | 83 |
| Fixed through v22 | 59 | 75 |
| Additional fixes through v23 | 4 | 4 |
| Additional fixes through v24 double swap | **1** | **2** |
| **Total repaired** | **64 / 64** | **81 / 83** |
| Still unresolved | **0** | **2** |

The final training instance was a **16-vertex** graph for which deterministic DSATUR needed 5 colors but 4 sufficed; the double-swap operator found a valid 4-coloring after 67 distinct two-swap attempts. A new holdout 16-vertex case was also repaired from 5 to 4 colors, after 62 attempts.

**Interpretation:** 100% conditional repair on the frozen training failures, 97.6% on the independent holdout failures. This supports usefulness of coordinated coloring transformations on this finite corpus, not universal performance. Two independent holdout failures remain. Their full edges, initial colorings, verified improved solutions, and bounded-search outcomes are archived in the experiment JSON ledger.

## Scientific gates

- Compare against published iterative Kempe-coloring and stochastic local search implementations; simple repeated swaps are not intrinsically novel.
- Evaluate costs on all graphs *without* independent exact-oracle preselection; measure work and latency rather than just conditional success fraction.
- Add a completely fresh graph-family holdout, not only new random seeds from the same generator.
- Formalize a generic Kempe swap validity lemma in Lean only if it becomes a useful proof building block.
- Do not merge an operator into production or advertise a discovered mathematical theorem based on finite success.

## Reproduce

`PYTHONPATH=. python -m unittest tests.test_double_kempe_lab -v`

`PYTHONPATH=. python scripts/experiment_double_kempe.py`

CI workflow `.github/workflows/double-kempe.yml` uploads `double-kempe-ledger.json`.
