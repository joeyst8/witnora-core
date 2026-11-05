# R-301–R-320: bounded minimum inconsistent GF(2) subsystem

The cycle-witness research extends from two-variable XOR edges to hypergraph
constraints of mixed arity. A dynamic program tracks states
`(XOR of selected variable supports, XOR of selected right-hand sides)` and
retains the shortest, lexicographically first source-row index tuple per
syndrome. The `(empty support, odd right-hand side)` state is an algebraic
contradiction witness. A separate exhaustive combinations oracle checks the
minimal witness, and a complete original-CNF RUP plus pinned `drat-trim`
gate checks each exported UNSAT proof.

**Caution:** this dynamic program can need exponentially many states in the
GF(2) support rank. It has explicit row, variable, state and proof budgets and
cannot decide arbitrary SAT or establish a complexity-class result.

| Gates | Verification |
| --- | --- |
| R-301–R-305 | Empty, consistent and mixed 1–4-variable dependency cases |
| R-306–R-309 | Independent exhaustive minimal subset and deterministic invariance |
| R-310–R-313 | State, variable, row and brute-force caps fail closed |
| R-314–R-316 | Independent/duplicate/contradictory state-space accounting |
| R-317–R-319 | Original-CNF SAT and UNSAT controls; independently checked proof |
| R-320 | No false external certification when checker absent |

Local 32-seed experiment: 64 mixed-width hypergraph cases, 32 SAT and 32
UNSAT. Exhaustive truth-table checks and the independent minimum-subsystem
oracle agreed; all 32 UNSAT proof candidates were accepted by pinned real
`drat-trim`. CI also compares native Rust output with the Python reference.

```shell
WITNORA_DRAT_TRIM=/path/to/drat-trim python -m unittest tests.test_xor_syndrome_301_320 -v
python -m scripts.benchmark_xor_syndrome_frontier --seeds 32 --compare-rust --drat-trim /path/to/drat-trim
```

**Status:** local reference and external checks passed; native CI pending.
The default Python execution path and original 560-file migration counts
are unchanged, with no merge or release approval.
