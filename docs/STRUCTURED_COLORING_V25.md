# v25 structured graph holdout and ungated runtime gate

**Status:** exploratory research, no claim of mathematical novelty, no Lean verification, no production promotion.

## Why this experiment matters

The earlier v21–v24 experiments used exact k-colorability as an **evaluation oracle** to identify known DSATUR failures before running costly repair searches. That is useful for rapid prototyping, but cannot establish actual deployment speed or generalization to unfamiliar graph classes.

This study instead executes the repair pipeline on **every** graph in a previously unseen structured-family corpus. The independent exact checker is called only **after** the algorithm commits to a coloring, to score whether either result remains suboptimal.

## Fixed design

300 labeled graphs, 60 per family, seeded with 20261102:

1. **Planted-coloring graphs** (3/4 independent color classes with random cross-class edges).
2. **Bipartite graphs** with different part sizes and edge densities.
3. **Circulant graphs** with fixed modular chord lengths.
4. **Line graphs** generated from small random parent graphs.
5. **k-trees** formed by repeated attachment to existing cliques.

Vertex counts are at most 16, within the independent backtracking k-colorability checker. This is a structurally different generator, though not an exhaustive representative distribution of all graphs.

## Results and timing

All output colorings pass per-edge validity checks. On GitHub Actions:

| Metric | Initial ungated pipeline | With witnessed-clique shortcut |
| --- | ---: | ---: |
| Graphs | 300 | 300 |
| DSATUR suboptimal instances | 7 | 7 |
| Failures repaired | **7/7** | **7/7** |
| Unrepaired failures | 0 | 0 |
| Clique-certified optimality skips | — | **270** |
| DSATUR time on 300 graphs | 0.024 s | 0.023 s |
| Repair pipeline time on 300 graphs | **3.30 s** | **0.40 s** |

The new shortcut finds an **actual clique** of size equal to the number of colors in the DSATUR solution. Because any proper coloring needs at least as many colors as a clique has vertices, matching upper/lower witnesses establish optimality. This is a constructive certificate, not use of the exact chromatic solver. If no matching clique is found, repair proceeds as before.

The first improvement is a **16-vertex circulant graph**, where DSATUR used 5 colors but bounded recoloring found a proper 4-coloring. Across the family groups, DSATUR failures were: planted-coloring 1, bipartite 0, circulant 3, line graph 3, k-tree 0. All seven were repaired.

## Interpretation

- **Generalization:** the pipeline repaired the seven detected failures on five independently designed graph families; the sample is small and is not a universal performance guarantee.
- **Efficiency:** the clique shortcut removed most unnecessary search and improved measured runtime by roughly 8x relative to the initial ungated pipeline. Nevertheless the optimized repair pipeline was still roughly **17x slower** than DSATUR alone on this specific single CI run, partly because it computes DSATUR internally and performs additional checks. These short single-run timings are indicative, not a robust benchmark.
- **Novelty:** clique lower bounds, DSATUR restarts, bounded recoloring, and Kempe swaps are established ideas. No new mathematical theorem has been discovered here.
- **Proof:** the clique certificate and Kempe swap validity are plausible small Lean lemma candidates, but no formalization is claimed for v25.

## Next gates

1. Compare with established high-quality graph-coloring heuristics under a controlled runtime budget; distinguish per-graph latency and solution quality.
2. Add adversarial families known to defeat saturation-based greedy coloring and independently check every claimed failure.
3. Test at larger graph orders using a trusted independent solver, while preserving the small exact-checker sample for reproducibility.
4. Identify a genuinely distinctive structural invariant before claiming mathematical novelty or production-readiness.

## Reproduce

`PYTHONPATH=. python -m unittest tests.test_structured_coloring_study -v`

`PYTHONPATH=. python scripts/experiment_structured_coloring.py`

Workflow `.github/workflows/structured-coloring.yml` uploads `structured-coloring-ledger.json`.
