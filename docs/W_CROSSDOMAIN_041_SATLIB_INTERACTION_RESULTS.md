# W041 — Fourier and signed-cycle alternative fails on untouched SATLIB source cases

## Independent precommit and source evidence

- Hypothesis, feature formulas, fixed sampling and tests were committed **before outcome inspection**: `docs/W_CROSSDOMAIN_041_SATLIB_INTERACTION_PROTOCOL.md`, commit `7798ced59be213a7e9a46bb458f47a11dfa4df91`.
- Original publisher: [SATLIB uniform random 3-SAT](https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/RND3SAT/descr.html), official `uf20-91.tar.gz`, archive SHA256 **`be2835295e8500bb28f0314eba70bd0deaff1250b187260f7b6d0772bdf111a5`**.
- Selected **exact lexicographic ranks 200–399**, disjoint from W040 ranks 0–199. Original filename, original source SHA256, full clauses, features, witness-verified DPLL source scans, timing, out-of-fold predictions and every null permutation are in `research/results/w041_satlib_raw.json.gz`.
- GitHub Actions source run [42212494094](https://github.com/joeyst8/witnora-core/actions/runs/42212494094) succeeded, artifact ID `13499526620`; all 200 are `n=20, m=91`, published SAT, DPLL returned checked satisfying assignments, **zero right-censored**.
- Compressed raw SHA256 **`2f8d9a5b5b67650e04676bb23e55c7dbfb24986e4ef31f0cab400cec2ea49d4b`**, decompressed JSON SHA256 **`ee76098d3764de862010f61d5fed769a80de1f9f55a537eb00909ff5fb33c218`**. A separate reproducibility CI re-downloads publisher archive and rebuilds source, measurements, predictions and permutations.

## Negative outcome with different preregistered features

Three **alternative** source descriptors, all invariant under clause order, variable relabeling and sign-gauge flips:

1. Proportion of overlapping clause pairs with opposed variable polarity (`polarity_conflict`).
2. Exact degree-3 Walsh/Fourier nonconstant L1 energy normalized by the mean.
3. Fraction of weighted signed triangles with negative edge-product (spin-cycle frustration).

Fivefold held-out ridge regression (λ10) versus the train-fold mean reference DPLL log-clause-scan target, 499 permutations, same formula size and SAT status for every case:

| Metric | Baseline | + W041 interaction features |
| --- | ---: | ---: |
| Held-out MSE | **0.367418** | **0.377689** |
| Relative MSE effect | — | **2.80% worse** |

- Permutation p = **0.774**. No support for the preregistered claim of improved search-effort prediction.
- Median new-feature extraction **2.770697 ms** per instance, reference DPLL **1.005397 ms** in the same GitHub runner. Features take approximately **2.76×** DPLL's measured median time, making an unconditional predictor especially unattractive.
- Interpretation: W040 cheap features were negative (**1.27% worse, p=0.404**) on the first 200 original SATLIB members. W041's more expressive Fourier/frustration features also failed (**2.80% worse, p=0.774**) on the next disjoint 200. This removes a simple claim that adding wave-like or signed-cycle measurements necessarily reveals practical DPLL difficulty.

## Research decision

Stop optimizing features on this SATLIB source family after two preregistered failures; repeating until one p-value is small would inflate false-discovery risk. The next independent experiment should measure **actionable solver interventions** on a genuinely different published family, or test a mathematically novel hypothesis with new source-family holdouts and a strict cost budget. Preserve W036–W041 negative results. Neither these experiments nor their earlier synthetic positive precursors establish a new computational-complexity theorem or solver speedup.
