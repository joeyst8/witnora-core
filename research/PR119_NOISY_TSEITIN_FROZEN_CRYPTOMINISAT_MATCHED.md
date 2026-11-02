# PR119 frozen plain-DIMACS fairer process-boundary comparison

CI run: [#41504918295](https://github.com/joeyst8/witnora-core/actions/runs/41504918295)

## Frozen protocol

- Same 12 previously SHA-locked n=64/96/128 cubic-graph Tseitin formulas, same 3.0-second per-run solver limit, untouched generator and parameters.
- CryptoMiniSat5: fresh external binary, input read from canonical ASCII DIMACS; process wall timed.
- Witnora: fresh Python interpreter, source read from ASCII DIMACS by PySAT, rebuilt as a canonical `CNFFormula`, source hash checked, exact XOR extraction, certificate construction and independent native recheck; whole process wall timed.
- All 12 cryptominisat UNSAT and all 12 native G5 source-subset checks accepted. Two SAT controls: CryptoMiniSat SAT, Witnora DIAGNOSTIC_ONLY.
- BOTH timings include interpreter/binary startup and DIMACS parsing. Differences in compiled vs Python runtime and parser implementations remain; benchmarks are sequential on one GitHub-hosted runner, not machine-isolated.
- **Lean per-instance checking is excluded from the 12 large native timings.** Only universal source-subset theorem and an n=8 literal ASCII example passed kernel checking in [#41504079560](https://github.com/joeyst8/witnora-core/actions/runs/41504079560). No universal Python-to-Lean refinement has been proved.
- Native per-instance faster in **12/12**. Median end-to-end process wall: native **292.237 ms**; CryptoMiniSat **1131.242 ms**. These are narrow-family empirical signals, **not proof of algorithmic novelty or generality**.
- SAT control gap: CryptoMiniSat solved each SAT case in ~4.6 ms while Witnora's diagnostic native checker spent ~192–282 ms. A general purpose solver cannot be replaced by this dedicated UNSAT recognition path.

## Detailed results

| Vertices | Seed | Noise/vertex | Native fresh-process ms | CryptoMiniSat fresh-process ms |
|---:|---:|---:|---:|---:|
| 64 | 47 | 1 | 181.736 | 371.647 |
| 64 | 47 | 4 | 193.758 | 1238.719 |
| 64 | 73 | 1 | 178.297 | 353.707 |
| 64 | 73 | 4 | 188.523 | 1433.322 |
| 96 | 47 | 1 | 283.858 | 1146.456 |
| 96 | 47 | 4 | 300.617 | 1164.648 |
| 96 | 73 | 1 | 280.670 | 1137.380 |
| 96 | 73 | 4 | 306.223 | 1131.995 |
| 128 | 47 | 1 | 401.848 | 1102.295 |
| 128 | 47 | 4 | 426.382 | 1058.443 |
| 128 | 73 | 1 | 423.129 | 1130.489 |
| 128 | 73 | 4 | 458.432 | 1032.548 |

## Publication gate

This only warrants a *research prototype* label. Require all of:
- Per-instance Lean verification cost included on larger source files.
- Repeated interleaved runs with calibrated CPU and memory reporting.
- Out-of-family tests and negative controls; compare matched general SAT workloads.
- Evidence that the transformation differs meaningfully from known XOR detection / Gaussian elimination in CryptoMiniSat.
- Clear negative results retained and no tuning on frozen holdout.

Raw data: `research/PR119_NOISY_TSEITIN_FROZEN_CRYPTOMINISAT_MATCHED.json`; previous unbalanced baseline archived separately.
