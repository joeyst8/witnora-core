# W-CROSSDOMAIN-014 — Cheap Walsh character as a frequency-domain proxy

**Frozen exploratory engineering protocol, not an independent held-out confirmation.** The P1/P2 families below were already observed in W-CROSSDOMAIN-013, so any predictive success here is development evidence only. The objective is to reduce the **work to extract a spectral feature** and determine how much predictive information survives compression of a full violation-weight/parity histogram to one frequency coefficient.

## Fixed source and wave coefficient

Reuse the existing six-variable, six-clause, width-three Pasch-core 3-CNF families P1 and P2 from W-CROSSDOMAIN-013, all `4,096` gauge-canonical signings in each, and the already-frozen incidence-kernel row `[0,1,2,3]`. Do not reselect source graphs, parity rows, branching orders, or signs to favor this proxy.

For each source clause `c`, let `v_c(x)` be 1 if assignment `x` violates `c`, and 0 otherwise. The exact **Walsh parity character** on selected clause set `C` is

`χ_C(x) = (-1)^(sum_{c in C} v_c(x)) = product_{c in C}(1 - 2 v_c(x))`.

Instead of enumerating all `2^n` assignments to obtain the full parity/energy spectrum, expand the product over at most `2^|C| = 16` clause subsets. For each subset `T`, the product of its violation indicators is either inconsistent (zero) or fixes one Boolean value per distinct variable. Therefore its unnormalized contribution is exactly `(-2)^|T| * 2^(n - number_of_fixed_variables)`. Summing these yields the integer `#even - #odd` over all assignments.

This is conventional inclusion-exclusion / Boolean Fourier algebra, **not a novel Fourier algorithm or a polynomial-time method for arbitrary large clause sets**. The selected row has four clauses, so the bounded pilot checks 16 subsets. Wave extraction should inspect at most 32 selected-clause occurrences and at most 96 literal occurrences across those subsets, compared with 384 source-clause evaluations for a direct 64-assignment × 6-clause sweep. These are **operation counts of different procedures**, not timings or equivalent instruction costs.

## Falsifiable prediction test

1. Independently compare the analytical `#even - #odd` coefficient against the full 64-assignment source truth table and existing native Fourier projection on designated signings, including duplicates, empty clauses and conflicting literal patterns in separate bounded unit tests.
2. As a cheap baseline feature, compute **the number of unordered source-clause pairs whose violation requirements contradict one another on at least one shared variable**. This needs at most 15 pair checks with 6 clauses, no global assignment enumeration.
3. Across all 4,096 orbit representatives in each P1/P2 family, compare *leave-one-out* DPLL recursive-node prediction using pair-conflict count alone versus `(pair-conflict count, Walsh parity bias)`. Exclude singleton baseline groups from both scores and fall back to baseline for singleton finer groups. Fix ascending and descending variable orders; report all four outcomes.
4. Apply 1,000 seeded, within-pair-baseline label permutations as an exploratory diagnostic. Do not promote their tails to confirmatory p-values because these families are already seen.
5. Report observed maxima and means for symbolic subset/variable inspections and compare them with DPLL clause scans, always labeling their differing cost units; **do not infer actual speedup without timing a complete decision procedure on independent instances**.

## Critical loss of information

The scalar character is only one *marginal* of the full joint spectrum. Distinct energy-conditioned histograms can produce the same `#even - #odd` coefficient. Even if the cheap coefficient agrees exactly with the expensive projector, its ability to predict search cost may disappear. That is an acceptable null outcome. Computing a useful partial frequency does not mean general SAT, #SAT or P versus NP is solved.

## Verification and prior work

Implement the symbolic coefficient in a standalone Rust library module, expose a native research CLI, and require independent Python truth-table and DPLL controls in GitHub Actions. Preserve negative results and recorded code-commit/CI provenance.

- G. D. Forney Jr., *Codes on Graphs: Duality and MacWilliams Identities*, IEEE Transactions on Information Theory (2011), <https://arxiv.org/abs/0911.5508>.
- Ryan O'Donnell, *Analysis of Boolean Functions* (2021 arXiv version), <https://arxiv.org/abs/2105.10386>.
