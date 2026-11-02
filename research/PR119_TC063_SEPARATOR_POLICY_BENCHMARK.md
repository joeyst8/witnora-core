# PR #119 — TC-063 first-valid vs balanced separator policies

Status: `REPRODUCIBLE_BENCHMARK_COMPLETED_LOCAL_TESTS_PASSED`.

Measured on 2026-11-02 using Python 3.12.14 on an x86_64 execution host.
Complete timing and correctness records (27 policy/trial combinations) are
archived at `research/PR119_TC063_SEPARATOR_POLICY_BENCHMARK_RESULT.json`.
The benchmark script and four independent unit tests are committed together.

The prior kernel-checked G5/G14 proof identified an actual two-vertex
separator `{10,29}` with 29/29 residual component variables. The current
Python recognizer finds its first valid separator `{1,38}` with 56/2
component variables. This experiment compares both policies without
modifying the production recognizer.

## Three policies

1. `production`: the actual `recognize_separator_affine_family(c=2,r=3)`.
   This recomputes the primal graph during each candidate examination.
2. `cached_first`: construct the primal graph once and search candidates
   in the *same order*, applying the same exact-affine coverage and SAT
   witness criteria as the production recognizer.
3. `cached_balanced`: construct the primal graph once, identify graph-cut
   candidates, sort by largest remaining component (then sum of squared
   sizes), and perform the same fail-closed affine validation in that order.

For *every accepted cut*, the benchmark calls the existing
`build_separator_affine_certificate`, which itself invokes the native
certificate checker, then independently invokes
`check_separator_affine_certificate` again. It rejects any policy producing
an unchecked or inconclusive SAT/UNSAT certificate. Timing includes cut
selection, certificate construction, and independent verification; policy
comparisons exclude Python import/startup time.

Inputs: original 160-clause, 60-variable Dubois20 (archived SHA-256
`82059aba0e5773644b386eb6bcbe53680655390cb041873a3cb3e93f7bd896a7`),
deterministically relabeled copies with independent seeds, and a reproducible
160-clause random 3-SAT negative control. Variable relabels are isomorphic,
not independent SAT-instance families. The negative control is a guard
against false separator acceptance, not a solver-performance comparison.

Reproduce from repo root:

```
python -B -m research.pr119_separator_selection_benchmark --trials 2 --permutations 3 --control-trials 1
python -B -m unittest tests.test_pr119_separator_selection_benchmark -v
```

## Results

All positive cases produced **independently reverified `UNSAT_CERTIFIED`
certificates** for every policy. The random 3-SAT negative control produced
`DIAGNOSTIC_ONLY` for all policies: no false separator/UNSAT claim.

Median total time in seconds, including separator selection, full G14
certificate construction (which internally runs its own checker), and an
**additional independent certificate verification**:

| Case | Production first-valid | Cached first-valid | Cached balanced |
| --- | ---: | ---: | ---: |
| Original Dubois20 | 3.854 | 0.550 | **0.329** |
| Isomorphic relabel seed 11 | 2.418 | **0.318** | 0.378 |
| Isomorphic relabel seed 29 | 2.403 | **0.337** | 0.343 |
| Isomorphic relabel seed 47 | 8.473 | 0.460 | **0.295** |
| Random 3-SAT negative (one trial) | 5.239 | 0.108 | **0.104** |

Positive cases have **two sequential timing trials** per policy; the
negative control has one. Warm-cache effects, CPU scheduling, and policy
execution order can affect these small samples; the script shuffles policy
execution order within each trial.

Original fixture details:

| Measure | Production / cached first-valid | Cached balanced |
| --- | ---: | ---: |
| Selected DIMACS separator | `{1,38}` | `{10,29}` |
| Residual component variables | 56 / 2 | 29 / 29 |
| Graph candidates screened | 97 | 1,830 |
| Valid graph cuts found in full scan | first accepted cut | 19 |
| Complete G14 certificate size | 7,783,801 bytes | 3,756,935 bytes |
| Final result | `UNSAT_CERTIFIED` | `UNSAT_CERTIFIED` |

Across the four positive cases:

- **Caching first-valid** improves end-to-end time by **7.0×–18.4×**
  versus the current production recognizer. The production code rebuilds
  `primal_graph(formula)` inside `_component_dicts` for each candidate;
  the cached prototype reuses one graph. On the no-cut negative control,
  the measured gap is **48.3×** (one trial).
- **Balancing has mixed time results**: faster than cached first-valid in
  only **two of four** positive cases. Selecting it requires screening all
  1,830 candidates, even when the first valid cut appears earlier.
- **Balancing reduces certificate bytes in all four** isomorphic cases,
  by **7.2%–51.7%**. This is a meaningful storage/checking signal, but
  certificate size alone does not determine full runtime.

Conclusion: **graph caching is the robust engineering opportunity** in this
small sample. Pure balanced-cut selection is not established as a general
runtime win, although its certificate-size reduction deserves further
investigation. Neither result is a novel SAT complexity theorem.

## Claims and limitations

- The cached implementation removes repeated primal-graph construction;
  its speed gain must be accounted for separately from separator balancing.
- The first-valid production recognizer and experimental cached policies
  differ in software organization, so this is a prototype comparison rather
  than a controlled hardware-level microbenchmark or an asymptotic proof.
- A balanced separator is not necessarily the optimal computational choice:
  graph scanning, affine validation, certificate sizes and model checks all
  matter. There is no general SAT advantage or P-vs-NP claim.
- The active benchmark does not change any production solver implementation.
  Full TC-063 formal verification remains incomplete.
- Renumbering a single parity instance does **not** create independent SAT
  problem families. A real OOD generalization test must use distinct
  benchmarks, larger structured instances, and strong external SAT baselines.
