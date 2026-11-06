# W034 — Exact integer-audited weighted Fourier certificates (200-case pilot)

## Verification and frozen evidence

- Frozen exploratory protocol: `docs/W_CROSSDOMAIN_034_WEIGHTED_SPECTRAL_PROTOCOL.md`.
- Successful source-preserving GitHub Actions run: [42161686584](https://github.com/joeyst8/witnora-core/actions/runs/42161686584).
- Code/weights verifier commit: `56e84aaf21c5a6d39a2d7e059e35240763aab3b7` (workflow YAML repaired in follow-up `520c3efe27689f66a100f152d50a01cdb177e6c0`).
- Complete original 200 small CNF formulas, per-formula SAT truth tables, proposed **integer** source-clause weights, audited bounds, outcomes and timing rows: `research/results/w034_weighted_small_raw.json.gz`.
- Compressed SHA256 `fedfa2a11e4ea4f7e3c4973d0e862258a66cee9e78df5945fd0f11ef0078207e` and decompressed SHA256 `261ca8144fc27799c6790012157c42986be37d0c0378f0dbdac7a98d8681a8c7`.
- Numerical proposal generation uses Python 3.11 with **NumPy 2.3.5 / SciPy 1.17.0**. Optimization is never trusted for correctness: every claimed UNSAT is checked from the original source clauses using nonnegative **integer** weights and exact arithmetic.
- All 32 assignments are independently enumerated for every 5-variable formula.

## Complete frozen 200-case exploratory result

Each stratum has 40 uniformly sampled **distinct** 3-clauses (sampled without replacement from the 80 possible three-literal clauses on five variables), with deterministic generator seed 340034. The overall case mix is **123 SAT and 77 UNSAT**.

| Clauses/formula | SAT | UNSAT | W033 unweighted UNSAT certificates | W034 weighted UNSAT certificates | W034 median LP + exact-audit time |
| --- | ---: | ---: | ---: | ---: | ---: |
| 12 | 40 | 0 | 0 | 0 | 2.53 ms |
| 16 | 38 | 2 | 0 | 1 | 2.74 ms |
| 20 | 27 | 13 | 0 | 12 | 2.96 ms |
| 24 | 16 | 24 | 0 | 23 | 3.14 ms |
| 32 | 2 | 38 | 0 | 38 | 3.43 ms |
| **Total** | **123** | **77** | **0** | **74** | — |

W034 certified **74 / 77 (96.1%)** of the UNSAT formulas that an independent exhaustive truth table proved UNSAT. There were **zero false UNSAT certificates on 123 SAT formulas**. W033's simple all-equal-weight bound certified zero cases across these same 200 formulas.

This demonstrates that weighting can recover exact proofs hidden by irrelevant source clauses **within this small, high-density distribution**. It does *not* imply a larger benchmark advantage: five variables have only 32 assignments, and mature SAT solvers can often settle such formulas cheaply. The displayed LP times exclude preparation, process startup and downstream solving; they cannot be read as a cost-inclusive speedup.

## Negative controls and limitations

1. W034 **failed on three truly UNSAT cases**, including the explicit frozen 16-clause five-variable counterexample in `tests/test_w034_weighted_walsh.py`. The relaxation is not complete even at fixed five-variable size.
2. Exact integer proof auditing protects against numerical LP false positives; it does **not** make LP search cheap, universal or novel.
3. Existing unit propagation, resolution, 2-SAT extraction and XOR preprocessing could certify some or many of these small instances more cheaply. No comparative experiment against those baselines has yet been performed.
4. The eight external VLSAT2 inputs from W032/W033 have **not** been processed by W034's LP: they are far outside its explicitly bounded `max_clauses=128` exploratory design. No external generalization claim is made.

## Next decision

W035 should audit W034's *incremental value* after standard unit propagation and affine/XOR detection, then restrict weighted spectral search to **small source-derived neighborhoods** on independent benchmark families. Count complete pipeline cost and demand source-verifiable certificates. If W034 duplicates cheap reasoning, retain the negative insight and redirect toward structural/geometry/information-theory features predictive of solver difficulty, with held-out validation.

Neither W034 nor the earlier runs supports a claim that P = NP has been solved.
