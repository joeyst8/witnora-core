# R-241–R-260: linear sparse XOR chain contrast

This family connects `n` variables by `n - 1` equal-parity two-variable XOR
constraints, anchors the first variable to zero and the last to one, and
encodes **every** XOR as its complete original CNF. The result is an UNSAT
chain; flipping the last anchor back to zero gives a SAT control.

The current bounded proof exporter produced and internally verified exactly
`n` derived clauses from `2*n` original CNF clauses, across the ten tested
lengths. The pinned *independent* `drat-trim` also accepted every proof.

| Chain variables | Original CNF clauses | Proof clauses | Proof bytes |
| ---: | ---: | ---: | ---: |
| 2 | 4 | 2 | 7 |
| 3 | 6 | 3 | 12 |
| 4 | 8 | 4 | 17 |
| 5 | 10 | 5 | 22 |
| 8 | 16 | 8 | 37 |
| 10 | 20 | 10 | 48 |
| 16 | 32 | 16 | 84 |
| 20 | 40 | 20 | 108 |
| 40 | 80 | 40 | 228 |
| 80 | 160 | 80 | 468 |

R-241–R-250 pin each length separately. R-251–R-253 check the linear
source, proof and row-operation counts; R-254 sparse identifiers; R-255
source-clause order; R-256 the SAT control; R-257 independent exhaustive
UNSAT for small chains; R-258–R-259 exact clause and byte budget cutoffs;
R-260 compares this sparse chain to the *different* dense width-10 full
encoding family. This is a source-structure comparison, not an asymptotic
lower bound or a head-to-head contest on equivalent input families.

Run:

```shell
WITNORA_DRAT_TRIM=/path/to/drat-trim python -m unittest tests.test_xor_chain_241_260 -v
python -m scripts.benchmark_xor_chain_frontier --compare-rust --drat-trim /path/to/drat-trim
```

The independent verifier's acceptance of these structured UNSAT proofs does
not imply Witnora can solve general SAT efficiently or reduce complexity
classes. Python remains the default, and this branch is not approved for a
merge or release.

**Status:** focused native CI
[#41956982135](https://github.com/joeyst8/witnora-core/actions/runs/41956982135)
passed, including native/Python comparisons and independent proof checks.
