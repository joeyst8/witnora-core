# Matched-core cross-equation ablation — negative performance gate

## Design

After finding that source-bound XOR cancellation can reduce DPLL search but
did not beat a differently implemented masked DPLL baseline, we isolated the
causal effect inside one fixed DPLL core (`experiment_cross_support_ablation`).

Every variant uses the **identical** recursive solver, branching heuristic,
CNF propagation, instance order, and original clauses. Only affine rows differ:

1. `none`: no extra affine rows.
2. `source`: exact XOR rows extracted from the original full CNF encodings.
3. `derived`: those same source rows plus bounded pairwise cancellations
   yielding rows of at most two variables.

Extraction and row combination are included in measured time. Mode order
is rotated between repeats. MiniSat22 creates a fresh solver for each run,
including CNF loading and solve; this is a native-vs-Python **practical**
comparison, not a controlled language/runtime algorithm comparison.

Run with PySAT installed:

```
python -c 'from scripts.experiment_cross_support_ablation import benchmark; print(benchmark(seeds=12,repeats=15)["summary"])'
python -m unittest tests.test_cross_support_ablation tests.test_cross_support_propagation -q
```

120 cases: 16/32-variable planted overlap controls across four families,
and two unrelated OOD families. All 120 SAT/UNSAT answers matched native
MiniSat. Three new regression tests also test 120 more randomized small
CNFs against MiniSat in all modes, and exhaustively verify derived-row
implication on 30 six-variable formulas.

## Observed results (15 repeats, median per instance, sums)

| Metric | Result |
|---|---:|
| Cases with exact extracted XOR rows | 96/120 |
| `derived` vs `source` fewer decisions | 24/120 |
| `derived` vs `source` faster runtime | 53/120 |
| New implied assignments under `derived` | 24 |
| `none` total | **31.2801 ms** |
| `source` total | 43.7812 ms |
| `derived` total | 44.1631 ms |
| Native MiniSat22 total | **2.9491 ms** |

All 24 decision wins occurred in the deliberately constructed conflicting
overlap family. In that family alone, `derived` summed 1.2085 ms against
`source` at 1.4425 ms, but `none` was still fastest at 0.4613 ms and
MiniSat at 0.1543 ms. No decision wins appeared in unrelated 3-SAT or
mixed parity controls.

Timings are tiny Python microbenchmarks with likely noise and environment
effects. Across an additional 7-repeat and a prior 15-repeat run, the
`source`/`derived` aggregate order changed slightly; therefore **do not
claim a reliable time advantage** for derived rows. Node/decision counts
and source-driven logical soundness are more stable.

## Conclusion

**No breakthrough; reject promotion.** The pairwise derivation can save
decisions in a narrow planted case, but extraction and propagation cost more
than the saved search on the tested instances. A much stronger operator
would need an inexpensive trigger, meaningful pruning on OOD workloads,
large-scale head-to-head benchmarks, and proof/certificate integration.
No SATLIB-specific result or Lean UNSAT certificate is claimed here.
