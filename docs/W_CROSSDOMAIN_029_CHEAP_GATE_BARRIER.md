# W029 — a cheap header-only gate is empirically uninformative

**Status:** audited after W027 full preregistered run. This is a descriptive negative result on the frozen W026 synthetic family, not a universal theorem about SAT.

## Question

Could a low-cost gate using only the DIMACS header information `(variable_count, clause_count)` decide whether to pay for Witnora's Rust XOR certificate check before Kissat?

## Exact finite-sample result

Using the W027 204-case, 1,836-invocation full result, we paired each of its 96 synthetic SAT instances with its matched UNSAT instance at the same noise level and replicate seed. Every pair has **exactly identical `(variables, clauses)`**, and each of the six header signatures contains precisely **16 SAT and 16 UNSAT** cases. The source labels are independently checked against the benchmark IDs and existing verified outcomes; no model was trained on test labels.

| Header variables | Header clauses | SAT | UNSAT | Extra time if full Witnora precheck runs for every case in bin (ms / case) |
| ---: | ---: | ---: | ---: | ---: |
| 64 | 20 | 16 | 16 | +2.199 |
| 64 | 52 | 16 | 16 | +2.256 |
| 64 | 276 | 16 | 16 | +1.802 |
| 64 | 1044 | 16 | 16 | +2.394 |
| 64 | 4116 | 16 | 16 | +2.831 |
| 64 | 8212 | 16 | 16 | +3.748 |

In each bin, the precheck's mean SAT overhead exceeds its mean UNSAT saving, using the three-repeat median full-pipeline W027 times. The empirical average extra cost of running it on an equally balanced bin is strictly positive. Therefore, **on this exact fixed set, any gate that observes only these two header counts and applies the same activation probability within a bin does no better than skipping the precheck altogether** in expected aggregate runtime. A randomized gate has the same limitation in expectation. In general, other workloads with a different conditional label distribution can have different optimal decisions.

## Proof for this frozen design

Let `H = (n, m)` be the header signature and let `q(H) ∈ [0,1]` be the probability of running the precheck. The complete matched design ensures `Pr(SAT | H) = Pr(UNSAT | H) = 1/2` empirically for all six observed H. Write `s(H)` for mean extra latency on SAT and `g(H)` for mean saved latency on UNSAT, relative to plain Kissat. The expected extra latency in bin H is:

`Δ(H) = q(H) × [s(H) − g(H)] / 2`.

Every measured `s(H) − g(H) > 0`, so `Δ(H) ≥ 0` for all `q(H)` and equality is attained by `q(H) = 0` (never run the precheck). This is an exact finite-sample conditional observation on the benchmark design plus its measured runtime estimates, not a statement that P ≠ NP or that higher-order structure is unknowable.

## Reproducibility

- Full archived W027 raw file: [`research/results/w027_full_solver_measurements.json`](../research/results/w027_full_solver_measurements.json).
- Audit implementation: [`scripts/audit_w029_header_gate.py`](../scripts/audit_w029_header_gate.py).
- Archived audit: [`research/results/w029_header_gate_audit.json`](../research/results/w029_header_gate_audit.json).
- Negative and positive unit tests: [`tests/test_w029_header_gate.py`](../tests/test_w029_header_gate.py). GitHub Actions checks exact equality of recomputed and archived JSON.

## Next preregistered direction

Stop optimizing raw size-only prediction. The remaining research must access higher-order signed-parity information **or** reduce the cost of obtaining certificates. A prospective W030 candidate is an **incremental Rust prefix-XOR contradiction detector**: on detecting a source-verified contradictory subset, it can legitimately short-circuit without reading the remaining file, since unsatisfiability is monotone under adding constraints. On no certificate it falls back unchanged to Kissat. Freeze independently generated negative controls, randomize clause order to defeat trivial prefix placement, and compare against W027 and Kissat with total costs counted. Do not claim the prefix benefit persists when contradictory clauses appear late.
