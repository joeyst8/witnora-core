# Accepted signed-integer XOR-CNF equivalence (v40)

Draft PR #41. CI: https://github.com/joeyst8/witnora-core/actions/runs/41239469130

## Universal proof, no side condition

`AcceptedXorInteger.checked_submitted_integerCNF_iff_original_xor` states:

For any `raw normalized : List Nat`, `rhs : Bool`, `submitted : List (List Int)`, any `a : Nat → Bool`, if
`FiniteXor.checkPythonEncodingOutput raw normalized rhs submitted = true`,
then
`SignedSerialization.signedCNFHolds submitted a ↔ Extraction.parityVars raw a = rhs`.

The theorem directly concerns the submitted signed-integer CNF's semantics after decoding, including the canonical signed-literal sorting step. There are no external positivity or normalization hypotheses: successful checker evaluation is sufficient.

Supporting universal lemmas:
- `toggleVar_preserves_positive`
- `normalizeByToggle_preserves_positive`
- `checked_normalized_positive`

The latter uses the checker's raw variable positivity and normalized-output permutation check, ensuring zero variable IDs cannot be introduced.

Axiom audit for the final theorem: `[propext, Classical.choice, Quot.sound]`. No `sorry`, user axiom, unsafe declaration, or native evaluation is used.

## Boundary

The theorem checks **in-memory submitted Lean integer lists** under the explicit Boolean acceptance predicate. It does not assert arbitrary Python runs produce accepted lists, that external files are parsed faithfully, or that G5/G14/TC-063 UNSAT has been proved. Next integrate a verified textual DIMACS/byte ingestion boundary, then compose certified extraction and reconstruction with the complete target theorem.
