# W-CROSSDOMAIN-018: exact covariance-kernel refutation results

Protocol: `docs/W_CROSSDOMAIN_018_ZERO_VARIANCE_REFUTATION_PROTOCOL.md`.

## Mathematics and soundness

For a 3-CNF formula, let `K_ij=64*Cov(v_i,v_j)` where `v_i` denotes
the violated-clause indicator under a uniformly random assignment.
The Rust candidate-prover performs **integer** fraction-free column
elimination on `K`, retaining the integer combination of source columns.
If it produces an integer vector `w` with `K*w=0` and `sum(w)!=0`, then
the weighted violation energy is independent of the assignment:

`sum_i w_i*v_i(x) = sum(w)/8`.

The right-hand side is nonzero. On a satisfying assignment the left side
would be zero. Thus the original CNF is UNSAT. All emitted candidates are
checked directly against the entire covariance matrix using integer
arithmetic, and all 4096 assignments are checked as an extra test oracle.

This is a **sufficient, incomplete refutation** based on a low-degree
polynomial linear combination. Its mathematical context is the established
Nullstellensatz/polynomial-calculus proof framework. No general SAT
polynomial-time algorithm or P-vs-NP proof is claimed.

## Prospectively frozen control families

The independent Python preflight applied the seeds and generators
preregistered in the protocol to all 128 instances; a separate finite-field
rank screen was used only for exploratory candidate *discovery*.

| Family (32 each) | SAT | UNSAT | Modular screen | Verified Rust integer proofs |
| --- | ---: | ---: | ---: | ---: |
| Fresh planted, 48 clauses | 32 | 0 | 0 | 0 |
| Fresh uniform, 48 clauses | 29 | 3 | 0 | 0 |
| Embedded complete eight-pattern contradiction, 56 clauses | 0 | 32 | 32 | 32 |
| Four-XOR parity-cycle contradiction, 64 clauses | 0 | 32 | 0 | 0 |

The complete eight-pattern subset admits the explicit integer vector
`w=(1,1,1,1,1,1,1,1,0,...,0)`: every assignment violates exactly
one of the first eight clauses. The independent Python oracle directly
verified `K*w=0` and this energy identity on **all 32 core instances**.
All 32 parity-cycle cases were independently confirmed UNSAT by exhaustive
search, but their simple covariance kernels did not produce candidates.

The mixed family contains three UNSAT instances missed by this method;
neither the parity cycle nor these cases can be inferred SAT from failure
to find the certificate. The next meaningful step is to investigate
bounded-degree polynomial multipliers or parity-aware proof certificates,
with independently checkable witnesses and held-out hard instances.

## GitHub Rust verification

- [x] Rust release witness extractor compiles and runs on all 128 cases.
- [x] Rust exact certificates are reproduced on the 32 full-eight-pattern cases.
- [x] No false positive on any SAT case; no parity-cycle UNSAT mistaken for SAT.
- [x] Independent Python controls at indices `0, 1, 31` match Rust source,
  truth-table counts, covariance and witnesses.
- [x] Focused CI and full native Rust workflow both green.

Implementation commit: `60cd0fe2074e88c7d36d1cab34fc45df2eb2d250`.
GitHub CI runs: focused `42100802923`, native `42100802925`. Both
completed **successfully** on 2026-11-05. The focused W018 step built the
release Rust executable, independently passed **two Python differential
tests**, and ran the full 128-case audit. All four Rust family counts
matched the independent preflight exactly.

Prior mathematical context: the polynomial-calculus / Nullstellensatz and
sum-of-squares refutation literature, including the 2018 STACS paper
"The Relation between Polynomial Calculus, Sherali-Adams, and
Sum-of-Squares Proofs"
(https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.STACS.2018.11)
and ECCC TR17-154 (https://eccc.weizmann.ac.il/report/2017/154/).
