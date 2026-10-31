# Color repair v22 — rapid prototypes against verified DSATUR failures

**Status:** research prototype, not a novel-algorithm claim, not Lean-verified, not promoted.

## Hypothesis

The v21 corpus independently certified DSATUR suboptimality on 64/2,400 seeded graphs. Two lightweight approaches may correct many of those avoidable greedy choices:

1. **Eight-start DSATUR:** run deterministic DSATUR under seven reproducible vertex relabelings plus the original order; keep the best valid coloring.
2. **Budgeted recoloring:** given one DSATUR coloring with k colors, search for a proper (k−1)-coloring that differs at no more than **five vertices**, stopping after **8,000** search nodes. This is intentionally *incomplete* and reports exhaustion instead of a false unsatisfiability conclusion.

Both return explicit color assignments checked on every edge. Neither needs the exact chromatic number to produce its answer, although the **evaluation harness uses the independent exact k-colorability checker to identify failure cases before running costly repairs**. Therefore this is a **repair effectiveness study**, not a fair runtime or deployment-performance benchmark.

## Predeclared train/holdout design

- Training: original v21 seed `20261031`, 2,400 graphs with 10, 12, 14, 16 vertices across densities 0.15–0.75.
- Holdout: previously unused seed `20261101`, same grid and 2,400 new graphs.
- Exact decision search independently confirms whether DSATUR overcolored each graph.
- No cherry-picking across split; both repair methods and budgets are fixed for the run.

| Metric | Training | Holdout |
| --- | ---: | ---: |
| Graphs | 2,400 | 2,400 |
| Independently verified DSATUR failures | **64** | **83** |
| Fixed by eight-start DSATUR | 49 | 58 |
| Fixed by five-change recoloring | 55 | 67 |
| Fixed by either operator | **59** | **75** |
| Still unresolved by both | **5** | **8** |
| Budget exhaustion count, oracle-gated run | 1 | 2 |

Thus the combined procedure repairs **59/64 (92.2%)** of the training failures and **75/83 (90.4%)** of the held-out failures. The 13 remaining failures are important counterexamples for the next iteration. A repaired solution is reported only when its edge-checked coloring uses fewer colors.

The first v21 counterexample on ten vertices (DSATUR 4, exact chromatic number 3) is repaired by both methods: multi-start finds a proper 3-coloring on restart 2, and the bounded recoloring finds another 3-coloring after only 11 search nodes.

## What this does and does not mean

This is a useful **engineering improvement on a carefully bounded experimental failure corpus**, with successful replication on a held-out random seed. Both constituent strategies are familiar search ideas; nothing here establishes a mathematically new operator. The observed repair fraction is not a guarantee outside the finite sampling plan.

The combined result does not establish a global chromatic upper-bound theorem beyond the trivial fact that a displayed proper k-coloring certifies \(\chi\le k\). Production use, Lean promotion, and novelty claims remain deferred.

## Next targeted test

Preserve the first unresolved training and holdout instances, inspect whether their required changes exceed five recolorings or depend on larger DSATUR restart counts, and compare against established local-search/coloring heuristics. Keep the independent exact checker as the oracle for evaluation only.

## Reproduce

`PYTHONPATH=. python -m unittest tests.test_color_repair_lab -v`

`PYTHONPATH=. python scripts/experiment_color_repair.py`

Workflow `.github/workflows/color-repair.yml` uploads `color-repair-ledger.json`.
