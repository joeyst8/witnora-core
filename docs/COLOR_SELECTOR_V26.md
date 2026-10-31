# v26 cheap selector for graph-coloring repairs

**Status:** exploratory, train-selected rule, independently tested holdouts. No novelty claim, Lean proof, or production promotion.

## Question

Previous experiments fixed most verified DSATUR failures but added expensive speculative search. Can a cheap, interpretable signal predict when repairs are worthwhile, without querying an exact chromatic solver at runtime?

## Signals and rule-selection protocol

A graph is **clique-certified** when the algorithm actually exhibits a clique of size equal to its DSATUR color count. In that case the coloring is provably optimal and no repair is needed.

We predeclared ten small Boolean rules based on witnessed-clique gap, final color class size, singleton color classes, and DSATUR's number of colors. On **training only** (2,400 original seeded graphs, 64 verified DSATUR failures), choose the rule with the fewest selected instances subject to at least 95% recall of failures. Freeze the rule before either holdout evaluation.

**Selected rule:** repair if the coloring is *not* clique-certified **and DSATUR used at least four colors** (`uncertified_k_ge_4`).

There is no formal claim this rule has universal perfect recall. In particular, it would miss any future case where a three-color DSATUR solution can be improved to two.

## Independent validation

| Metric | Training | Random holdout | Structured holdout |
| --- | ---: | ---: | ---: |
| Graphs | 2,400 | 2,400 | 300 |
| DSATUR failures independently verified | 64 | 83 | 7 |
| Selected for repair | **310** | **341** | **10** |
| Failure cases correctly selected | **64/64** | **83/83** | **7/7** |
| Failed cases missed by selector | **0** | **0** | **0** |

For comparison, the simple `not clique-certified` rule selected 396 random-holdout graphs and 30 structured-holdout graphs. The selected rule thus avoids 55 and 20 otherwise speculative repair attempts, respectively.

The full selective repair pipeline (not merely the classifier) was run on both holdouts with independently checked proper colorings:

- Random holdout: **79 improvements**, **4 unresolved DSATUR failures**.
- Structured holdout: **7 improvements**, **0 unresolved failures**.

The runtime selection uses DSATUR results and the witnessed-clique feature extractor, **never the exact k-colorability oracle**. The exact checker is used separately for the trial's failure labels and after-the-fact scoring.

## Timing caveat

Measured on one GitHub Actions Python job:

| Holdout | Bare DSATUR | Selective pipeline |
| --- | ---: | ---: |
| Random, 2,400 graphs | 0.157 s | 12.70 s |
| Structured, 300 graphs | 0.019 s | 0.184 s |

The selected repair pipeline remains significantly slower (approximately 81x on random graphs, 10x on structured graphs) than DSATUR alone. These single-run wall times are not robust benchmark estimates. The pipeline sometimes recomputes DSATUR within repair functions; this should be optimized before performance claims.

Crucially, on random holdout the current bounded repair settings fixed 79/83 failures, whereas v24's *oracle-gated, differently budgeted* research run fixed 81/83. These results are not directly comparable as algorithms or timing conditions. Do not claim the selector fixes all failures just because it successfully **detects** all of them.

## Scientific interpretation

A witnessed clique is a rigorous lower-bound certificate; pairing it with an explicit proper coloring of equal size is a genuine mathematical optimality certificate. The extra `k>=4` threshold is an empirical heuristic selected from training and not a theorem. The tested features, DSATUR restarts, recoloring and Kempe moves are standard-style approaches, not established mathematical novelty.

Next: stress the frozen rule against deliberately constructed low-color failures, larger structured generators, and alternate vertex relabelings. Compare end-to-end quality per unit of compute against established heuristic graph-coloring implementations. Investigate small generic Lean lemmas for a witnessed-clique optimality gate and Kempe recoloring preservation if they serve the broader Witnora verification work.

## Reproduce

`PYTHONPATH=. python -m unittest tests.test_color_selector_lab -v`

`PYTHONPATH=. python scripts/experiment_color_selector.py`

Workflow `.github/workflows/color-selector.yml` uploads `color-selector-ledger.json`.
