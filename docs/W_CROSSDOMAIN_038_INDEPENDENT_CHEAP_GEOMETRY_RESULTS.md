# W038 — Eight-variable independent replication of cheap geometric cost prediction

## Precommitted design and exact evidence

- Prospective protocol: `docs/W_CROSSDOMAIN_038_INDEPENDENT_CHEAP_GEOMETRY_PROTOCOL.md`, committed before evaluation in `02a834a249a771733d000bf0387115dbe168492e`. A later commit `f7929fa7f6fcb54fd82e3ff8122624ab4a1b5776` **only fixed YAML quoting**, without changing the sample, features, models or statistic.
- Successful fresh independent run [42166387624](https://github.com/joeyst8/witnora-core/actions/runs/42166387624), artifact `w038-independent-raw` ID `13479131747`.
- Full 200 source CNFs, exact DPLL outcomes, feature values, out-of-fold predictions, individual feature/DPLL timings and 200 null draws archived as `research/results/w038_independent_raw.json.gz`.
- SHA256 gzip **`64cb482d208bc9b6d5fac4cd77d1d71f4787dbc00298f91a26408682c0e8db8d`**, decompressed JSON **`c0650f6e50f04323836e7b351cdda8810914452f264a3c8bf3acc104d464819c`**. Independent GitHub workflow replays every source and statistic.

## Frozen new sample and prediction

All 200 formulas use **eight Boolean variables** and uniform three-literal clauses drawn without replacement from 448 legal possibilities, via frozen seed 380038. There are 40 formulas in each clause-count group 24/32/40/48/56; 102 are SAT and 98 UNSAT. Clause order remains part of the source and the DPLL reference remains fixed. The target is `log1p(exact source-clause scans)`; neither SAT status nor solver work enters any feature.

Frozen size-stratified fivefold predictions, with the exact same five clause-count indicators in all models and ridge penalty 10 on standardized feature slopes:

| Held-out measure | Clause count only | Plus cheap three features | Plus all W037 five features |
| --- | ---: | ---: | ---: |
| Mean squared error | 0.098818 | **0.090292** | 0.093189 |
| Mean absolute error | 0.242286 | **0.234378** | Not primary |
| Relative MSE improvement | — | **8.63%** | 5.70% |

- Primary cheap-three within-size vector permutation test, 200 iterations: **p = 0.004975**, none of the null draws matching the observed improvement. This is a randomized association check on the chosen synthetic generator, not a universal probability statement.
- Per-clause-count MSE improvement is not universal: at 24 clauses **0.10091 → 0.09039**, 32 **0.19803 → 0.16743**, 40 **0.10923 → 0.11129 (worse)**, 48 **0.04708 → 0.04050**, 56 **0.03884 → 0.04186 (worse)**.
- Group composition varies strongly: 24 clauses **40 SAT / 0 UNSAT**; 32 **36/4**, 40 **14/26**, 48 **9/31**, 56 **3/37**. Size indicators already condition on that imbalance in both models, but future work should stratify by SAT label or target separate search regimes.

## The useful mathematical simplification and its cost

The three prechosen source-only features are:

1. Signed literal-degree imbalance.
2. **Exact clause-pair overlap** computed from per-variable degrees: `sum_v deg(v)(deg(v)-1)/2` divided by `3*m*(m-1)/2`. This eliminates explicit comparison of all clause pairs and matches W037's result exactly.
3. Absolute largest eigenvalue of the normalized signed co-occurrence adjacency matrix, our wave/spectral connection.

All three are unchanged under variable renaming, variable polarity gauge flips, and clause reordering. Unit tests verify agreement with W037's much more expensive five-feature implementation for 5- and 8-variable sources.

Within the **same GitHub Actions run**, median wall times were:

| Per-case operation | Median |
| --- | ---: |
| Cheap three features | **0.134078 ms** |
| Full five W037 features | 0.851376 ms |
| Reference DPLL solver | 0.145721 ms |

Cheap extraction is **6.35× faster** than full W037 extraction by the ratio of measured medians, but still takes **92% of the solver's own median time**. It cannot be a profitable unconditional front-end for these tiny formulas. Timing is single-run Python wall-clock observation, not hardware-neutral or production-solver performance.

## Meaning and next falsification

Two differently sized synthetic distributions show conditional prediction (W037 n=5: 9.10%; W038 n=8: 8.63%). This is useful evidence of *predictive information* about search cost beyond the mere number of clauses. It is not yet evidence of an efficient way to exploit that information.

Next, freeze a new family-level holdout on **independently published SAT instances**, account for variable count and clause count, and compare a sparse cheap rule against modern SAT heuristics and SATzilla-style predictors. Budget any routing/extraction cost within total solver wall-clock work, rather than optimizing prediction MSE alone. Do not claim new complexity bounds, generalized speedup, or P=NP progress.
