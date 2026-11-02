# PR119 frozen XOR-aware baseline: CryptoMiniSat5

- Independent [GitHub Actions run #41504478768](https://github.com/joeyst8/witnora-core/actions/runs/41504478768) replayed all **12 exact SHA-locked** inputs from the previously archived n=64/96/128 frozen holdout, without changing graph generator, seeds, charges, noise or selection.
- Input to CryptoMiniSat5 was the **plain CNF** DIMACS file (no explicit XOR instructions). Ubuntu 24.04 apt `cryptominisat` package, binary `cryptominisat5 --verb 0`, separate process with 3-second hard deadline.
- **12/12** solved UNSAT by CryptoMiniSat, **zero timeouts or unknowns**. Both independent SAT controls yielded SAT, while the native source-subset certificate path correctly remained DIAGNOSTIC_ONLY.
- Witnora Python native G5 checking: **12/12 checked**; still **NOT_LEAN_VERIFIED per large instance**. The universal source-subset theorem and small exact ASCII DIMACS example independently passed Lean CI run [#41504079560](https://github.com/joeyst8/witnora-core/actions/runs/41504079560).
- Matched 12-case median: native Python-only `203.60 ms`; CryptoMiniSat process wall `1052.34 ms`. **UNBALANCED TIMING**: native excludes Python launch, DIMACS read, and any Lean kernel check; CryptoMiniSat includes process launch and DIMACS read. Native faster in all 12 *under these different measurement boundaries*, which is **not** a speedup claim.
- Comparison with MiniSat/CaDiCaL: the latter timed out on 9/12 of same cases at 3s, but XOR-aware CryptoMiniSat solved all. Therefore these inputs are **not** evidence of a new fast UNSAT algorithm; XOR Gaussian elimination is established prior art.

## Size-stratified arithmetic means (exploratory only)

| Vertices | Cases | Native internal mean ms | CryptoMiniSat process mean ms |
|---|---:|---:|---:|
| 64 | 4 | 97.53 | 812.57 |
| 96 | 4 | 205.91 | 1080.36 |
| 128 | 4 | 343.12 | 999.97 |

## Next falsification gates

1. Measure **both** systems from the same ASCII DIMACS input using fresh external processes and include startup and parsing for both; add Lean certificate production/checking as a separate end-to-end metric.
2. Test distinct graph distributions, non-XOR cores, and solver configurations without tuning to frozen outcomes.
3. Novelty remains unproven. The TC-063 universal exact-subset bridge is a formally checked engineering integration, not a new mathematical theorem about NP-hardness.

Source: `scripts/cryptominisat_noisy_tseitin_frozen.py`; complete per-case results: `research/PR119_NOISY_TSEITIN_FROZEN_CRYPTOMINISAT.json`. Do not replace or tune frozen held-out cases.
