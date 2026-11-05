# R-181–R-200: independent original-CNF controls

Research-branch experiment, **not** a proof of general SAT performance and
**not** twenty migrated Python source files. This batch advances the research
verification frontier by adding twenty named regression gates and a separate
small-instance exhaustive truth-table oracle.

| Gate | Verified property |
| --- | --- |
| R-181 | Independent truth-table oracle recognizes SAT |
| R-182 | Oracle recognizes original-CNF contradictions |
| R-183 | Exhaustive variable cap fails closed |
| R-184 | Planted single-XOR SAT controls emit no proof |
| R-185 | Two inconsistent complete XOR encodings are UNSAT |
| R-186 | Candidate proof is independently checked by original-CNF RUP subset |
| R-187 | Truncating the candidate proof is rejected |
| R-188 | Source CNF clause-order permutation is invariant |
| R-189 | Duplicate source clauses do not change normalized CNF |
| R-190 | Sparse variable identifiers preserve UNSAT/RUP checks |
| R-191 | Overlapping nonlinear SAT background does not create false UNSAT |
| R-192 | Missing original XOR support clause rejects export |
| R-193 | Mutated original XOR support rejects export |
| R-194 | Invalid parent-row identifier rejects export |
| R-195 | Incorrect derived parity rejects export |
| R-196 | Zero proof-clause budget rejects export |
| R-197 | Zero proof-byte budget rejects export |
| R-198 | No external checker means no external certification |
| R-199 | An invalid explicitly requested external checker fails closed |
| R-200 | The mixed SAT/UNSAT suite reproduces bit-for-bit |

`scripts/benchmark_xor_frontier.py` builds 48 cases per seed, evenly split
between SAT and UNSAT, across 24 structural families: XOR widths 1–3,
disjoint/overlapping background, shuffled/duplicated source clauses, and
dense/sparse variable labels. For each case the independently enumerated
*original CNF* determines SAT/UNSAT. UNSAT candidate proofs are also checked
by an original-CNF RUP-subset checker; SAT controls must not emit proofs. The
CI test compares native Rust output, error and accounting exactly against the
Python reference and runs 10 seeds (480 instances).

Run the bounded reference experiment:

```shell
python -m unittest tests.test_xor_frontier_181_200 -v
python -m scripts.benchmark_xor_frontier --seeds 10
```

CI runs `--compare-rust` after building the native extension. To require
external proof certification for the UNSAT cases, pass an installed executable
via `--drat-trim /path/to/drat-trim`; otherwise records explicitly state
`external_drat_verified: false`. An internal RUP check or a truth-table oracle
is **not** the existing external `drat-trim` approval gate.

Initial local reference result: 480/480 bounded cases passed (240 SAT and
240 UNSAT), with 20 Python unit gates green. Native differential and external
checker certification are separate, not silently inferred from this result.

**Status:** candidate pending native Rust CI. Python remains the default,
existing Lean and independent DRAT trust boundaries are unchanged, and the
research branch must not be merged solely on this checkpoint.
