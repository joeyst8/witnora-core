# Pigeonhole Native Certificate

## Statement

For a standard `php_n_m` CNF with assignment variables `x[pigeon,hole]`, if the
original CNF contains all pigeon ALO clauses and all hole AMO pair clauses, and
if `n > m`, then the formula is unsatisfiable by the pigeonhole counting
argument.

## Checker Obligations

The v2.3 checker verifies:

1. The certificate hash matches the original CNF.
2. The assignment variable grid is exactly `x[i,j]`.
3. Every ALO clause is present in the original CNF.
4. Every AMO pair clause is present in the original CNF.
5. `n > m`.
6. The certificate does not claim DRAT.

If any obligation fails, the checker returns
`PIGEONHOLE_CERTIFICATE_FAILED`.

## Native, Not DRAT

The certificate is a native semantic certificate. It is checkable directly from
the original CNF structure, but it is not an externally checked DRAT proof.

## Relationship to Symmetry

Symmetry can help identify or compress the `x[pigeon,hole]` grid. The UNSAT
argument itself is cardinality/counting: too many pigeons for too few holes.

## Claim Boundary

This does not claim P vs NP progress, complete PB solving, general SAT solving,
or a G3 strictness theorem. It is a theorem-candidate and native certificate
route for recognized standard pigeonhole encodings.
