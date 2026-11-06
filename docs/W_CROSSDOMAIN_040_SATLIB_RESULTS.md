# W040 — The cheap geometry signal does not replicate on published fixed-status SATLIB

## Exact publisher source and frozen design

- Prospectively committed hypothesis and methods: `docs/W_CROSSDOMAIN_040_SATLIB_PROTOCOL.md`, commit `6c97af209cbf898fbb906441ffc49f4516a846f5`. Before any measurements, a subsequent narrow CI repair `635499cd27108b7bff88a2525108a665a95d1a74` taught the parser to accept the publisher's DIMACS `%` terminal marker; no sample, model, limit, or hypothesis changed.
- Source: **SATLIB publisher**, [uniform random 3-SAT description](https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/RND3SAT/descr.html) and official `uf20-91.tar.gz`. Publisher archive gzip SHA256 **`be2835295e8500bb28f0314eba70bd0deaff1250b187260f7b6d0772bdf111a5`**.
- Successful GitHub Actions external run [42211745651](https://github.com/joeyst8/witnora-core/actions/runs/42211745651); artifact `w040-satlib-official-raw` ID `13499686048`.
- Exactly **200** original `.cnf` members chosen lexicographically from the publisher's **1,000** members. All have 20 variables, 91 clauses, width 3, official status SAT. Every one reached a **verified satisfying assignment** under the 2,000,000-source-clause scan budget; **0 censored**. Original member names, SHA256 of each DIMACS file, original source clauses, measured source scan counts, features, timings and all 499 null draws are archived in `research/results/w040_satlib_raw.json.gz`.
- Archived gzip SHA256 **`6bbf4894bd8394c09d885dba40586db971b4ec22a591a578832b06f4d7d19ae9`**, decompressed JSON SHA256 **`cae5fb2a4d51f519f28a1119a75d2bafb4e04c38ff4b3714c09a07745f67d40e`**. Replay workflow independently downloads publisher bytes and checks hashes/source/statistics.

## Primary unchanged held-out prediction result

All formulas share the exact same `n=20, m=91, SAT` classification; therefore no label or size confound remains inside this sample. The precommitted features are signed degree imbalance, incidence-derived overlap and signed interaction spectral radius. The target is `log1p(exact source-clause scans)` of a transparent DPLL. Five held-out folds, ridge λ10 on standardized features, 499 whole-vector permutations.

| Held-out metric | Training-mean baseline | + three cheap features |
| --- | ---: | ---: |
| Mean squared error | **0.389039** | **0.393961** |
| Relative MSE change | — | **1.27% worse** |

- The frozen 499-permutation one-sided test returned **p = 0.404**. This is a **negative replication** of the W037/W038 apparent structural complexity signal. It is not a demonstration that every geometry-based feature is worthless, only that these particular preselected features show no usable difficulty prediction here.
- Per-fold MSE was mixed. Geometry changed folds `0–4` as: `0.316657→0.312732`, `0.501402→0.491241`, `0.383932→0.391317` (worse), `0.352831→0.338953`, and `0.390373→0.435564` (worse). The average worsened.
- Median per-case feature extraction **0.352046 ms**; reference DPLL solving **1.141502 ms** on the same CI runner. Any unconditional routing would pay a material feature cost and there is no evidence of end-to-end benefit.

## Scientific interpretation and why it matters

W037 had a size-controlled synthetic n5 prediction improvement of 9.10% and W038 a size-controlled synthetic n8 improvement of 8.63%, both statistically positive in their specific synthetic samples. W039's independent n10 comparison controlled SAT status and found only 0.76% improvement, p=0.112. **W040 goes further:** external published real SATLIB formulas all share the same size and known SAT status, and the original geometry signal is absent (negative 1.27%, p=0.404).

Thus the simplest hypothesis — that the current three geometry features robustly proxy intrinsic DPLL search hardness independently of formula size and SAT label — **is not supported**. The observation narrows the physical/information-theoretic research agenda, without resolving complexity theory or invalidating other feature families.

## Next falsifiable attempt

W041 can *prospectively* select the non-overlapping SATLIB `.cnf` ranks **200–399** and evaluate a different preexisting feature family (polarity frustration and exact bounded-width Walsh/Fourier interaction energy), with no tuning on W040's source cases. Keep a size/status-matched mean baseline, fixed CV, 499 permutations, and charge full extraction time. If it too fails, explicitly record the failure; seek different published source families before broader claims.
