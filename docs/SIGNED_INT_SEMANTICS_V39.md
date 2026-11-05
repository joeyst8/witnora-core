# Signed integer semantic refinement (v39)

Draft PR #40. Successful proof run: https://github.com/joeyst8/witnora-core/actions/runs/41239251257

## Proven

1. `serializedSignedClauses_semantics`: for any positive-ID variable list, RHS and Boolean assignment, evaluating the actual serialized, sorted and decoded signed-integer CNF is equivalent to evaluating the generated symbolic signed clauses.
   - Subsidiary lemmas prove each nonzero signed literal decodes to its symbolic form, signed integer insertion/sorting permutes the clause without changing members, and disjunction is preserved under permutation.
   - Axiom report: `[propext, Quot.sound]`.

2. `checked_submitted_signedCNF_iff_raw_xor`: if `checkPythonEncodingOutput raw normalized rhs submitted = true` **and** every normalized variable ID is positive, then for **every** Boolean assignment `a`:
   `SignedSerialization.signedCNFHolds submitted a ↔ Extraction.parityVars raw a = rhs`.
   - Axiom report: `[propext, Classical.choice, Quot.sound]`.

Both compile without `sorry`, user axioms, unsafe declarations, or native evaluation.

## Remaining small formal gap

The second theorem assumes `∀ v ∈ normalized, 0 < v` separately. `checkPythonEncodingOutput` checks the original raw IDs are positive and the normalized output is a permutation of the verified toggle normalizer. A universal proof should derive normalized positivity directly from checker acceptance; then that extra hypothesis can be removed.

The remaining wider pipeline also includes verified byte/DIMACS transport, complete Python refinement, G14 residual correspondence, and original TC-063 UNSAT composition. This theorem alone does not assert TC-063.
