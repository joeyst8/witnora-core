# Exact signed-literal XOR-CNF theorem (v37)

Draft PR #38. Verified in GitHub Actions: https://github.com/joeyst8/witnora-core/actions/runs/41238546467

## Universal theorem

`Witnora.ExactSignedXorCNF.generatedSignedHolds_iff`:

For every `vars : List Nat`, `rhs : Bool`, and `a : Nat → Bool`,

`generatedSignedHolds vars rhs a = true ↔ Extraction.parityVars vars a = rhs`.

Here `generatedSignedHolds` evaluates the **actual signed-literal clauses** created by `FiniteXor.generateSignedClauses`, not an abstract forbidden-clause predicate. It combines `generateForbiddenPatterns`, `signForbiddenClause`, and signed-literal disjunction. It holds for arbitrary repeated variable IDs and even empty supports; no distinctness hypothesis is required.

New helper theorems establish that every enumerated bit vector has the declared length and that full agreement of a zipped pattern with the current assignment forces equality with the assignment's mapped bit vector.

## Axiom and trust audit

The dedicated Lean module built successfully. The universal theorem reports only `[propext, Classical.choice, Quot.sound]`. There are no user-declared axioms, `sorry`, or `native_decide` in the theorem proof.

## Remaining obligations

- Python's separately implemented generator and normalization/serialization still require universal representation refinement (or an adequately checked output interface).
- `generatedSignedHolds` checks **the emitted symbolic signed clauses**, not parsing arbitrary DIMACS file bytes.
- This theorem proves the exact XOR-CNF **encoding equivalence**, not the soundness of every CNF-to-XOR extraction claim on an unrelated original CNF (that requires the coverage checker), nor G14 residual-model correspondence or TC-063 UNSAT.
- For the original end-to-end objective, connect this equivalence to normalized Python clause output, signed serialization and verified DIMACS input, then compose with G5/G14.
