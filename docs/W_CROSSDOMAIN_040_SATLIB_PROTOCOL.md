# W040 — Frozen external SATLIB constant-size SAT-only pilot

## Prospectively fixed, before evaluating the published source

**Goal:** Directly test whether W038's cheap signed-geometry features predict source-clause scans *among published SAT problems of identical size and known satisfiability status*. W039's synthetic label-conditional p=0.112 motivates the stringent control. Commit this protocol and implementation before running the download/evaluation.

**Publisher:** SATLIB, Holger H. Hoos and Thomas Stützle. Official benchmark description: https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/RND3SAT/descr.html . The publisher states `uf20-91` contains 1,000 satisfiable, unforced random 3-SAT instances of 20 variables/91 clauses. Official archive (no mirror substitution): `https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/RND3SAT/uf20-91.tar.gz`.

### Frozen sampling, source integrity and ground truth

- Download the **official publisher archive directly from GitHub Actions** with curl and record compressed archive SHA256. Keep the exact downloaded bytes under CI-run provenance; record SHA256 and original DIMACS clauses of each included member in the raw experiment artifact.
- Inspect the gzip tar **without extracting paths**. Select **the first 200 `.cnf` members by lexicographic original archive member name**; reject duplicate names. Do not select by SAT difficulty, measured feature values, labels, solver performance, or file size. Require at least 200 valid CNFs.
- Parse each selected DIMACS file strictly: `p cnf 20 91`, exactly 91 three-literal clauses of distinct variables, each literal in the ±1..20 range, no tautological clause. Preserve clause order for reference DPLL. In case of parse failure, stop the run rather than silently exclude cases.
- A publisher-source syntax clarification after the first failed preflight: SATLIB DIMACS files can contain the conventional `%` terminal marker after the clauses; treat it as an end-of-file postamble, while still requiring all 91 complete clauses before it. This changes no case selection, solver measurement, or statistical decision.
- The publisher declares the whole `uf20-91` family SAT. For every solved result, independently verify that the reported assignment satisfies every original clause. Any UNSAT verdict is a stop condition; bounded incomplete results are marked `CENSORED`, never misclassified.

### Solver budget and predeclared statistical test

- Keep the W035 reference DPLL's exact unit-propagation, clause ordering and branch ordering, with only a **2,000,000 source-clause scan hard cap per instance** to prevent runaway work. Test exact agreement with uncapped W035 on fixed small cases. A case that reaches the cap is **right-censored**, not a solved observation.
- Use only the frozen W038 **three** features: normalized signed degree imbalance, exact incidence-derived clause-pair overlap, and signed interaction spectral radius. Do not tune/select features based on the SATLIB results.
- Primary study: if **all 200 instances finish under cap**, run 5-fold held-out prediction for target `log1p(DPLL clause scans)`, frozen random fold seed **400040** and ridge penalty **10** on the three training-fold-standardized features. Baseline is the training-set mean target: clause count, variable count, and SAT label are identical for all cases.
- Compute held-out baseline/geometry MSE, MAE, improvement `(MSE_base-MSE_geometry)/MSE_base`, and report per-fold results. **499** vector permutations across the 200 fixed-size SAT instances, seed **400041**, retraining the same folds; one-sided p=`(1+count(null >= observed))/500`.
- **If any case is censored, do not compute/claim an uncensored primary p-value or speedup.** Report censoring fraction, empirical scan distribution of completed cases, and source-level costs only; the inference is formally inconclusive at this cap. This guard prevents difficulty-dependent post-selection bias.
- Report median geometry extraction wall-time, median reference DPLL wall-time and ratio within one CI runner. Both are measured separately within the same run; no claim of profitable routing unless *end-to-end* solver cost decreases in a further intervention test.

### Interpretation and next step

SATLIB `uf20-91` is one independently published source **family**, not a cross-family held-out validation, and its original clauses are random 3-SAT despite independent provenance. A positive result must be replicated in another *published family* with matching status and sizes. A negative result directly limits this particular 3-feature complexity-proxy hypothesis. The study makes no theorem or P-versus-NP claim.
