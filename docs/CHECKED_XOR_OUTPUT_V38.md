# Checked Python XOR output composition (v38)

Draft PR #39. CI: https://github.com/joeyst8/witnora-core/actions/runs/41238741045

## What is proved

Given arbitrary raw variable IDs, submitted normalized IDs, parity rhs, submitted signed-integer clauses and a passing `FiniteXor.checkPythonEncodingOutput` result, the theorem `CheckedXorOutput.checked_python_xor_output_exact` proves simultaneously:

1. `submitted = FiniteXor.serializedSignedClauses normalized rhs` (exact expected canonical signed-integer lists), and
2. for every Boolean assignment `a`, `ExactSignedXorCNF.generatedSignedHolds normalized rhs a = true ↔ Extraction.parityVars raw a = rhs`.

This composes existing normalization parity-preservation and checked serialized output with the new universal symbolic signed-literal XOR-CNF equivalence theorem.

The dedicated Lean CI passed with axiom dependencies `[propext, Classical.choice, Quot.sound]` for both exported theorems; no `sorry`/user axiom/unsafe declaration.

## Crucial limitation

Condition (2) is about the **symbolic signed-literal generator**. Condition (1) checks integer-list equality but this module does not yet show that decoding and evaluating those exact integer lists agrees with the symbolic generator. This is an explicit remaining representation proof, alongside externally supplied DIMACS byte parsing and universal Python execution refinement.

Next: prove `SignedSerialization.signedCNFHolds submitted a ↔ ExactSignedXorCNF.generatedSignedHolds normalized rhs a = true` under accepted output and positivity, including semantic preservation of the signed literal sort. Only then claim a direct semantic iff about the actual submitted signed integers.
