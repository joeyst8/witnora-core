# PR #119 — TC-063 Held-Out Native Certificate vs MiniSat22

Commit ancestry: benchmark implementation `1bb73148d971036b80131f3fb3fa630b219c6c05`.
CI evidence: https://github.com/joeyst8/witnora-core/actions/runs/41500674799

## Result: correctness on a narrow family, no observed speed win

- 18 distinct guarded-affine instances, each repeated twice (36 measurements).
- Three families: `saf_sat_chain`, `saf_unsat_cover`, `saf_balanced_sat`.
- Component counts 4, 8, 16; held-out seeds 23 and 59. Variable renaming, sign flips, clause ordering, and literal ordering are randomized reproducibly.
- 36/36 certified statuses agreed with independent PySAT MiniSat22; every emitted native G14 certificate passed its independent Python checker.
- 0 diagnostic-only results; **0/36 Witnora timing wins**.
- Median across the 18 per-case median durations: **16.8845 ms** for Witnora versus **0.0457 ms** for MiniSat22.
- Median of per-case native/solver time ratios: **386.7×** (range **117.2× to 525.1×**).

The source `scripts/benchmark_tc063_heldout_minisat.py` and exact raw results `research/PR119_TC063_HELDOUT_MINISAT_RESULT.json` allow inspection and reproduction.

## Timing boundaries

`witnora_native_total_ms` includes Python recognition, native G14 certificate construction, and independent Python certificate checking. It **does not include Lean kernel verification**.

`minisat_total_ms` includes constructing a fresh PySAT MiniSat22 solver from the same CNF and returning SAT/UNSAT. MiniSat is not required to emit a comparable independently checked proof. These results measure practical pipeline costs, **not equal-output proof-producing solver performance**.

The input families are synthetic and structurally close to our native G14 specialization. Held-out permutations test invariance to names and order, **not generalization to unrelated problem structures or industrial SAT instances**. These small runtimes are sensitive to noise; interpret large ratios as evidence against a current speed advantage on these examples, not a universal performance bound.

## Scientific decision

This prototype passed the narrow *soundness and coverage* gate, but fails the *speed advantage* gate.

Next work should target structural discoveries that reduce difficult reasoning effort on genuinely hard held-out problems, or explicitly evaluate the cost of *proof-carrying UNSAT* against established proof-producing solvers and checkers. Avoid further optimization solely against easy guarded-affine fixtures unless it addresses a demonstrated bottleneck on hard cases.

This is neither P-vs-NP progress nor a complete universal Python-to-Lean refinement proof.
