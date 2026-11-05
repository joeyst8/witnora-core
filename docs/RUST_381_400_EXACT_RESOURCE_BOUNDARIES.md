# R-381–R-400: exact state, clause and byte budget boundaries

On a single contradictory signed `n`-cycle, the minimum-subsystem dynamic
program explores exactly `2**n` reachable parity syndromes for the tested
sizes, even though the independently certified clausal proof has only
`2*n-1` derived clauses. That gap separates *witness-search effort* from
*certificate output size*. It is not an asymptotic SAT lower bound.

| n | Reachable GF(2) syndrome states | Verified proof clauses | Proof bytes |
| ---: | ---: | ---: | ---: |
| 4 | 16 | 7 | 39 |
| 6 | 64 | 11 | 67 |
| 8 | 256 | 15 | 95 |
| 10 | 1,024 | 19 | 141 |
| 12 | 4,096 | 23 | 177 |
| 14 | 16,384 | 27 | 213 |
| 16 | 65,536 | 31 | 249 |

R-381–R-387 pin these seven sizes, with real DRAT acceptance. R-388–R-394
exercise exact and one-under caps for state, row and variable budgets.
R-395 protects satisfiable controls. R-396–R-399 check verifier absence,
wrong-original CNF rejection and exact proof bytes/clauses. R-400 checks the
entire bounded matrix. Rust/Python equality and external certificate checks
remain separate gates.

**Status:** local reference and independent proof checks passed; native CI
pending. Python is the default and this is a research-only cap study.
