# Restricted G0 Width vs G1 XOR Strictness Theorem

## 1. The restricted grammars

`G0_WIDTH_C` contains only the bounded-width/treewidth route: bounded
treewidth terminal, VE width cap `c`, and an exact bounded-width obstruction
checker. It excludes XOR, symmetry, cardinality, orbit-capacity, affine
residue, and proof motif operators.

`G0_WIDTH_C_WITH_SAFE_PREPROCESS` is a future variant. It may include only
preprocessors proven not to lower the selected witness family below cap `c`.
v2.9 does not use it for theorem claims.

`G1_XOR_FOR_STRICTNESS` extends `G0_WIDTH_C` with exact XOR extraction and
native GF(2) elimination certificates.

## 2. Bound profile B

The finite v2.9 proof kernel uses cap `c=4` by default. The route is bounded
and operational: width checking and XOR certificate verification must complete
inside the configured run.

## 3. Witness family

The finite witnesses are exact full-CNF XOR/Tseitin-style fixtures such as
`tseitin_10` and `xor_chain_unsat_n5`. They are finite theorem-kernel witnesses,
not a proof of a scalable expander family.

## 4. Width obstruction lemma

If exhaustive bounded-width checking verifies that no elimination ordering of
width `<= c` exists for formula `F`, then `F` is not accepted by the restricted
`G0_WIDTH_C` bounded-width terminal under cap `c`.

## 5. XOR upper-bound lemma

If `F` contains exact XOR equations, the extractor verifies the full CNF source
clauses, and native GF(2) elimination verifies SAT or UNSAT, then `F` is
accepted by `G1_XOR_FOR_STRICTNESS`.

## 6. Restricted strictness statement

There exists a finite witnessed formula `F` such that `G0_WIDTH_C` rejects `F`
by verified width obstruction and `G1_XOR_FOR_STRICTNESS` accepts `F` by a
verified XOR certificate.

## 7. Proof sketch

For each finite witness, the checker builds the primal graph, exhaustively
searches for an elimination order of width `<= c`, records failure, and records
a certified lower bound greater than `c`. The G1 route then extracts exact XOR
equations from full CNF encodings and checks the GF(2) contradiction or
assignment.

## 8. What is proven

Only the finite restricted proof object is supported: bounded-width rejection
for `G0_WIDTH_C` and native XOR acceptance for `G1_XOR_FOR_STRICTNESS`.

v2.10 names the reusable machine-checked finite status
`FINITE_STRICTNESS_CERTIFIED`. This status applies only to the checked finite
instance set and is not a scalable family theorem.

## 9. What is not proven

This does not prove full `G0_BASE` strictness. It does not prove a lower bound
against UP, PLE, SUB, BCE, components, 2SAT, or safe preprocessing routes. It
does not prove hierarchy completeness. Scalable Tseitin/expander strictness
remains a proof obligation unless a separate proof is supplied.

## 10. Why this is not P vs NP

This does not prove P vs NP.

This proof kernel is bounded, restricted, and formula-family-specific. It does
not prove P vs NP or polynomial-time SAT.

## 11. Proof obligations remaining for full G0_BASE

- Prove every allowed G0 operator cannot reduce the selected family into a
  collapsible form.
- Prove stable scalable treewidth lower bounds for a chosen graph family.
- Prove safe preprocessing cannot evade the width obstruction.
- Add external proof bridges only when checked against the original CNF.
