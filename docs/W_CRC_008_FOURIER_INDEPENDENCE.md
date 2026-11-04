# W-CRC-008: exact source-relative Fourier independence audit

**Status:** opt-in research diagnostic, draft PR #122. The first
full W-CRC/Ganak gate passed:
https://github.com/joeyst8/witnora-core/actions/runs/41714348159 .
This is a source-derived exact conditional-independence test for
the existing bounded uniform-defect family. It does not yield an
unconditional SAT speedup or a new complexity-class theorem.

## A precise criterion

Let f(x) be the 0/1 model indicator of a supported nonempty source
CNF on Boolean boundary B. For disjoint variable groups A and C,
let fhat(T) be the normalized Fourier-Walsh coefficient of f.
Then A and C are independent *under the uniform distribution on
source models* iff for every U subseteq A and V subseteq C,

    fhat(U union V) * fhat(empty) = fhat(U) * fhat(V).

This is necessary and sufficient because characters form a complete
basis of every function on the joint Boolean cube. The identity is
ordinary joint-versus-product moment factorization, not a new
mathematical result. For a nonzero violation, the checker returns
actual masks U,V and the exact rational discrepancy.

Implementation:
- witnora_core/crc_independence_audit.py
- tests/test_crc_independence_audit.py
- scripts/benchmark_crc_independence.py

The audit normalizes actual signed source clauses in Python and
requests the full needed joint mode set from the already exact
W-CRC-005 uniform-defect oracle. It returns **None** (unknown) on
unsupported sources, an empty-clause contradiction, invalid
model-density normalization, or the explicit mode cap. The default
cap is 4,096 Fourier modes with a hard 20-group-bit bound. A failed
independence result is a source-specific counterexample, not UNSAT.

Unlike a mere pairwise variable-correlation heuristic, this checks
*all* joint moments. For larger groups it has an explicit exponential
2^(|A|+|C|) cost, so checking independence can cost more than
solving one instance. It does not replace G14 or any SAT checker.

## Independent semantic validation

- Complete positive rank-3 CNF on six variables, A={1,2,3},
  C={4,5,6}: exact Fourier discrepancy detects dependence,
  consistent with the prior W-CRC-007 count counterexample.
- A second group of two variables absent from the source is
  provably independent; the checker accepts after 32 exact modes.
- 36 seeded coherent rank-3 sources at 5,6,7 variables, with
  random polarities/missing supports, matched an **independently
  enumerated conditional count-table rank-one oracle**.
- Invalid, overlapping or empty groups and insufficient mode
  budgets are rejected or return unknown.

All **55 Python unit tests** passed in the full green gate,
including prior W-CRC-001 through W-CRC-007 controls:
https://github.com/joeyst8/witnora-core/actions/runs/41714348159 .

## A deliberately adverse admission-cost pilot

The paired benchmark tests A={1,2,3}, C={4,5,6} on four-defect
positive/signed dense sources with n=8/12/20/28. It compares:
(1) an exact independence audit on the coherent base source,
(2) direct W-CRC-006 exact counting of two conflicting-sign
exceptions, and (3) an independent Ganak integer model count.
Each method uses the same source geometry; timings include Python
construction/normalization for that method, with two internal
repeats and one Ganak run on a single CI machine.

| n | Pattern | Audit 64-mode ms | Direct W-CRC count ms | Audit / direct | Independence |
| ---: | --- | ---: | ---: | ---: | --- |
| 8 | dispersed | 0.3826 | 0.8968 | 0.427 | false |
| 8 | tetrahedron | 0.3752 | 0.8984 | 0.418 | false |
| 12 | dispersed | 0.6010 | 2.7971 | 0.215 | false |
| 12 | tetrahedron | 0.5745 | 2.8265 | 0.203 | false |
| 20 | dispersed | 1.7527 | 14.2375 | 0.123 | false |
| 20 | tetrahedron | 1.7495 | 13.8183 | 0.127 | false |
| 28 | dispersed | 4.6880 | 39.4254 | 0.119 | false |
| 28 | tetrahedron | 4.7950 | 41.7839 | 0.115 | false |

All eight W-CRC integer counts matched Ganak. Every dense
model distribution failed the independence criterion, so none
qualified for the proposed factorization. The audit is a fast
**rejection** in these tests, but paying even 11–43% extra time
before the unmodified exact count gives no single-query speedup.
Do not advertise that audit speed as solving speed.

For accepted *independence* cases, computing all cross moments
may still make a one-off admission check uneconomical. Reusing a
checked response across many different exception predicates could
amortize it, but no amortized advantage has been benchmarked here.

## Next W-CRC-009

Develop a cheaper **sufficient** source-relative independence
certificate: source clause-variable components. If no connected
source-primal component intersects both requested groups, the
model indicator decomposes into independent factors (provided
the source has at least one model), so their conditional model
distribution factors. A linear-time union-find check can accept
those cases without asking for 2^(|A|+|C|) Fourier modes.

This criterion is not necessary: source graph connectivity does
not prove semantic dependence. Therefore a failed structural
check must return UNKNOWN or defer to the exact Fourier audit;
it cannot classify dependence. Test explicit positive and
false-negative cases, source-tamper and SAT/UNSAT controls,
and benchmark the cost of the hybrid admission policy.

The restricted W-CRC high-order defect identity, this Fourier
criterion, and the older Lean TC-063 family theorem remain
separate trust layers. Neither the Python test suite nor Ganak
is a universal CPython-to-Lean refinement proof.
