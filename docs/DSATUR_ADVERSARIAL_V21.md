# DSATUR adversarial search — v21

**Status:** experimental, no novelty claim, not Lean-verified, not promoted.

## Goal and design

The v20 nonedge-pairing operator failed to improve deterministic DSATUR over 34,321 small graphs. Rather than assuming DSATUR always works, this branch predeclares a **seeded adversarial search** for graphs where DSATUR uses more colors than are necessary.

- Graph orders: 10, 12, 14, 16.
- Edge densities: 0.15, 0.30, 0.45, 0.60, 0.75.
- Samples per (order, density): 120.
- Fixed seed: 20261031.
- Total: **2,400 graphs**.
- Independent checker: exhaustive k-colorability backtracking with color-name symmetry pruning and an explicit, edge-checked proper-coloring witness. For discovered failures, search every smaller k to establish the exact chromatic number.
- Crosscheck: **168** graphs of orders 1–7 against the existing independent subset-DP chromatic solver, plus unit tests for exhaustive labeled graphs of orders 1–4.

## Result

The CI experiment found **64 distinct labeled test instances** in which the deterministic DSATUR greedy coloring used more colors than a validated exact coloring. The ledger retains up to ten exact examples and their complete edge lists and color assignments.

The first failure is on **10 vertices** with edges:
`04, 07, 08, 09, 12, 13, 14, 15, 19, 26, 29, 35, 36, 37, 46, 48, 57, 58, 69, 89`.

- DSATUR used **4** colors; certificate `[0,0,2,2,1,1,0,3,2,1]`.
- Exact k-colorability found **3** colors; certificate `[2,0,2,1,1,2,0,0,0,1]`.
- Exhaustive decision procedure ruled out 0, 1, and 2 colors.
- Both explicit colorings pass every edge check.

The old vertex-cover/nonedge-matching operator was applicable to only the **two** DSATUR-failure instances with at most 11 vertices. It used 4 colors on those failures and improved **neither**.

## Interpretation

This is a **validated algorithmic counterexample**, not a new theorem. Standard DSATUR is a heuristic and is not expected to be universally optimal. The meaningful gain is that Witnora now has a reproducible failure corpus with independently confirmed optimal colorings. It supplies concrete objectives for future operator prototypes.

Do not infer a general failure rate of DSATUR from this nonrepresentative, fixed search design. Vary graph families, seeds, symmetries, and vertex relabelings in a subsequent holdout. Re-check all future operators against DSATUR, the exact witness, and known coloring techniques.

## Reproduce

`PYTHONPATH=. python -m unittest tests.test_dsatur_adversarial_lab -v`

`PYTHONPATH=. python scripts/experiment_dsatur_adversarial.py`

GitHub Actions workflow `.github/workflows/dsatur-adversarial.yml` uploads `dsatur-adversarial-ledger.json`.
