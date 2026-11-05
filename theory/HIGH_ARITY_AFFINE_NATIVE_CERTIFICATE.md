# High-Arity Affine Native Certificate

This note records the proof-sketch shape for
`G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE`.

## Formula Evidence

Each claimed GF(2) equation must come from exact evidence in the original CNF.
For variables `x1, ..., xk` and parity bit `b`, the checker recomputes the
`2^(k-1)` forbidden-assignment clauses and verifies that they are present with
the recorded source clause IDs.

No heuristic XOR mining is used.

## Gaussian Elimination

The checker recomputes deterministic Gaussian elimination over GF(2). The only
accepted row operations are:

- swap two rows;
- add/xor one row into another.

There is no nontrivial scale operation over GF(2) in this certificate language.

## UNSAT Certificate

For UNSAT, the final trace must contain a contradiction row:

`0 = 1`

The checker verifies that this row arises from the extracted equations.

## SAT Certificate

For SAT, the certificate contains an assignment for the affine variables. The
checker verifies that the assignment satisfies the extracted equations and then
verifies it against the original CNF before emitting
`SAT_AFFINE_RESIDUE_NATIVE_CERTIFIED`.

## Boundary

This is a native certificate, not DRAT. It is bounded by configured arity and
resource caps. It does not claim broad modular arithmetic solving,
CryptoMiniSat-style extraction, a strictness theorem, or P vs NP progress.
