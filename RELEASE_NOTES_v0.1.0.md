# Witnora-Core v0.1.0 Release Notes

## Benchmark Layer Added

Witnora-Core v0.1.0 adds a benchmark and measurement layer for evaluating certified collapse behavior across deterministic synthetic cases and DIMACS directories.

The benchmark layer measures:

- status and solved route
- final class
- certificate hash
- collapse path length
- original and post-simplification variables and clauses
- original and post-simplification max clause width
- original and post-simplification primal edge counts
- max-clause clique lower bound
- bounded-width order search result for the configured `c`
- BCE, PLE, UP, SUB, and VE counts
- SAT original-verification flag
- timing
- no-collapse failure reason
- optional certificate-hash determinism checks

## Synthetic Suite Added

The v0.1.0 synthetic suite includes deterministic families for:

- blocked-clique BCE collapse
- random 2-SAT
- random 3-SAT no-collapse probing
- bounded-primal-treewidth non-2-CNF formulas
- BCE-heavy formulas
- mixed independent components
- unit-conflict UNSAT
- tautology-normalization noise

## DIMACS Directory Benchmark Support

The benchmark CLI supports running every `.cnf` or `.dimacs` file in a directory:

```bash
python -m witnora_core.benchmark --dimacs-dir examples --c 2 --out results.json --determinism-check
```

Synthetic benchmarks can be run with:

```bash
python -m witnora_core.benchmark --suite synthetic --c 1 --out results_c1.json --determinism-check
python -m witnora_core.benchmark --suite synthetic --c 2 --out results_c2.json --determinism-check
```

## Tests Passed

The v0.1.0 test suite passed with 27 tests.

New v0.1.0 pass markers:

- `BENCHMARK_SYNTHETIC_PASS`
- `BENCHMARK_DETERMINISM_PASS`
- `BLOCKED_CLIQUE_METRICS_PASS`
- `RANDOM_3SAT_NO_COLLAPSE_SAFE_PASS`
- `DIMACS_DIR_BENCHMARK_PASS`

All v0.0.1 and v0.0.2 tests remained passing.

## No External Solver / No Brute Force

Witnora-Core v0.1.0 does not use an external SAT solver and does not brute-force arbitrary CNF formulas.

The internal 2-SAT solver remains an SCC-based implementation. The bounded-width route still uses exact bounded-width elimination-order search for `c <= 4`.

## No P vs NP Claims

This release makes no claim that P = NP, no claim that SAT is solved in polynomial time in general, and no claim that no-collapse formulas are hard.

`NO_COLLAPSE_FOUND_UNDER_CURRENT_GRAMMAR_AND_C` means only that the implemented grammar and selected `c` budget did not find a certified collapse path.

## Remaining Limitations

- Benchmark cases are still mostly synthetic and controlled.
- No claim is made that Witnora competes with modern industrial SAT solvers.
- Exact post-simplification bounded-width measurement can be skipped above a size cap to avoid accidental expensive search.
- No LRAT or FRAT output is implemented.
- No Horn, XOR, backdoor, or portfolio routes are implemented.
- `c` remains limited to `0 <= c <= 4`.
- Report generation and comparison tooling are not part of v0.1.0; those are planned for v0.2.0.
