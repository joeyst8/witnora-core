# W-CROSSDOMAIN-017: signed violation covariance and search cost

Protocol: `docs/W_CROSSDOMAIN_017_SIGNED_COVARIANCE_PROTOCOL.md`.

## Exact definitions and elementary identity

For a width-3 clause `c`, let `v_c(x)` be 1 exactly when `c` is violated.
Under a uniformly sampled Boolean assignment, `E[v_c]=1/8`. Set
`K_cd = 64 Cov(v_c, v_d)`. For nonduplicate width-3 clauses, `K_cc=7`;
for a distinct pair, `K_cd=-1` if the clauses impose contradictory values
on a shared variable in order to be violated, and otherwise
`K_cd=2^s-1` where `s` is their number of shared variables. The same formula
also handles duplicate clauses (giving `K_cd=7`).

For the total violation energy `E(x)=sum_c v_c(x)`, the following is exact:

`64 Var(E) = 7*m + 2*sum_{c<d} K_cd`.

The signed interaction graph has edges weighted by `K_cd`; the triangle
measure is the sum of magnitudes of the negative products
`K_ij K_jk K_ki`. These are correlations of *violation events*, not
literal physical oscillations. The covariance matrix is positive
semidefinite by construction; signed triangles do not by themselves
prove anything about SAT satisfiability.

## Locked prospective 96-instance experiment

Three families of 32 deterministic n=12 3-CNF formulas were generated
under the protocol's seeds and tested against degree-static DPLL scan counts.
Pearson coefficients were calculated **within each family**. Values below
are reproduced by the Rust release executable and independent Python
reference, with agreement on all three families.

| Frozen family | SAT / total | Mean clause scans | `r(scans, negative pairs)` | `r(scans, signed mass)` | `r(scans, negative triangle mass)` |
| --- | ---: | ---: | ---: | ---: | ---: |
| Planted SAT, 48 clauses | 32 / 32 | 519.8125 | -0.1363 | +0.1880 | -0.2086 |
| Uniform boundary, 48 clauses | 28 / 32 | 650.53125 | -0.0573 | +0.0006 | -0.1530 |
| Embedded UNSAT, 56 clauses | 0 / 32 | 286.15625 | -0.2309 | +0.2734 | -0.1208 |

The largest absolute within-family Pearson coefficient is about 0.273.
For 32 cases, a descriptive Fisher-z 95% interval for the +0.2734
coefficient is approximately [-0.083, +0.568]; **the data do not support
a reliable monotonic predictive relationship.** No solver speedup was
attempted or demonstrated; cross-family aggregation would confound the
controlled embedded contradiction with scan cost.

## Algebraic consequence to investigate separately

For any rational vector of clause weights `w`,
`64 Var(sum_c w_c v_c)=w^T K w`.
If `K w=0` and `sum_c w_c` is nonzero, then
`sum_c w_c v_c(x) = (sum_c w_c)/8` for *every* Boolean assignment.
But on a satisfying assignment every `v_c(x)=0`, a contradiction.
Consequently **an exact rational null vector with nonzero component sum
is a sound UNSAT certificate**. Weights need not be nonnegative.

The complete eight-sign pattern over a fixed triple is an elementary
example: diagonal entries are 7, off-diagonal entries are -1,
`w=(1,...,1)` lies in the kernel, and every assignment violates
exactly one clause. This follows from standard Fourier and linear
algebra arguments; it is *not a novel complexity theorem*.

An exploratory finite-field Fourier-rank screen on the same three frozen
families found candidate certificates in 0/32 planted, 0/32 uniform
boundary (including the four UNSAT cases), and 32/32 deliberately
embedded-UNSAT formulas. **Finite-field rank is not a rational proof**;
the next study must extract and independently check integer witnesses
and include hard UNSAT cases without an embedded eight-clause block.

Relevant prior proof frameworks include Nullstellensatz / polynomial
calculus and sum-of-squares refutations. A bounded-degree linear
refutation is a special case, not a resolution of P versus NP.

## Verification checklist

- [x] Preregister sources, correlations, independent controls and falsification criteria.
- [x] Independent Python reference calculates all 96 frozen family statistics.
- [x] GitHub Rust build and all 96 full truth-table variance identities pass.
- [x] Nine independent controls compare Rust output, pairwise truth tables,
  gauge changes and DPLL scan counts with Python.
- [x] Focused CI and full native Rust workflow both pass.

GitHub commit: `65294b02c8b17ec6d37e1c43d39bd134b35ad425`.
Focused GitHub Actions run `42099452779`: **success**, including W017
tests (2 passed) and release-executable output. Full native Rust run
`42099452896`: **success**. Both verified on 2026-11-05.
