# Affine Residue Collapse

v2.6 introduces `G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE`, the scoped prototype
of the v2.4-generated `MODULAR_RESIDUE_COLLAPSE` candidate.

## Scope

G5 handles exact high-arity GF(2) affine equations represented as full
forbidden-assignment CNF encodings. It is designed for parity-over-cap rows
where G1's exact XOR extraction cap is intentionally lower.

G5 does not claim:

- broad modular arithmetic solving;
- complete GF(2) extraction from arbitrary CNF;
- heuristic XOR mining;
- CryptoMiniSat-style XOR discovery;
- DRAT verification;
- a strictness theorem;
- P vs NP progress.

## Exact Extraction Only

For an equation:

`x1 xor x2 xor ... xor xk = b`

the original CNF must contain every forbidden-assignment clause for that parity
equation. The checker recomputes those clauses, verifies source clause IDs, and
rejects incomplete or wrong-parity certificates.

Extra structure is not mined. If an encoding is incomplete or over the G5 cap,
the row remains diagnostic-only.

## Native GF(2) Certificate

The certificate records:

- extracted equations;
- source clause IDs;
- deterministic Gaussian-elimination trace;
- row operations;
- final rank;
- contradiction row for UNSAT, or solution for SAT.

Allowed GF(2) row operations are:

- `SWAP_ROWS`;
- `ADD_ROW_XOR`.

`SCALE_ROW_NONTRIVIAL` is forbidden. Over GF(2), multiplying a row by one is the
only useful scaling operation.

## Public Categories

G5 may emit:

- `UNSAT_AFFINE_RESIDUE_NATIVE_CERTIFIED`;
- `SAT_AFFINE_RESIDUE_NATIVE_CERTIFIED`;
- diagnostic-only/no-collapse rows for rejected controls.

These are native categories, not DRAT categories.
