# R-341–R-360: matched-size structural interaction diagnostic

Construct two original-CNF XOR systems with the **same** even number `n` of
variables, `n` binary constraints, `2*n` *distinct* CNF source clauses, and
degree two for every variable. The only intended difference is how those
constraints interact:

- One connected signed `n`-cycle, with a single inconsistent cycle.
- `n/2` disjoint parallel-edge pairs, each internally inconsistent.

The bounded GF(2) syndrome search explores more states in the connected
cycle because its support rank is larger, and the smallest contradictory
subsystem is longer. Both families have externally accepted original-CNF DRAT
proofs. The result is not a solver complexity theorem; it diagnoses this
specific bounded witness-selection method.

| n | Cycle rank | Pair rank | Cycle states | Pair states | Cycle proof clauses | Pair proof clauses |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | 3 | 2 | 16 | 8 | 7 | 3 |
| 6 | 5 | 3 | 64 | 16 | 11 | 3 |
| 8 | 7 | 4 | 256 | 32 | 15 | 3 |
| 10 | 9 | 5 | 1,024 | 64 | 19 | 3 |
| 12 | 11 | 6 | 4,096 | 128 | 23 | 3 |
| 14 | 13 | 7 | 16,384 | 256 | 27 | 3 |

R-341–R-346 pin the six graph sizes. R-347–R-351 verify equality of
variables, constraints, arities, degree profiles and *unique* CNF clause
counts. R-352–R-358 check independent minimum contradiction, GF(2) rank,
syndrome state counts and the largest frozen divergence. R-359 is a SAT
control and R-360 enforces the strict bounded input domain.

**Local status:** 20 named gates and real pinned external proofs passed;
native Rust CI pending. The default Python execution path, original migration
file counts and Lean/DRAT trust boundaries remain unchanged.
