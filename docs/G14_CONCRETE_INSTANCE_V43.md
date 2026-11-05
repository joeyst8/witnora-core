# Concrete two-branch G14 → G5 UNSAT instance (v43)

Draft PR #44. Successful CI: https://github.com/joeyst8/witnora-core/actions/runs/41240234148

## What was verified

The literal source ASCII DIMACS document represents

`(x1 ∨ x2) ∧ (¬x1 ∨ x2) ∧ (¬x2)`.

The separator is `[1]`, with all branches enumerated by `SeparatorAssignments.enumerate [1]`: false and true. Both conditioned branches reduce to the same unit contradiction `[x2], [¬x2]`, and the concrete partition checker verifies the exact residual clauses.

Each branch has a closed G5 proof: initial rows `([2], true)` and `([2], false)`, XOR step `(0, 1)`, bound 3. Lean validates clause coverage, canonical support and indexed contradiction.

The theorem `G14ConcreteInstance.concrete_two_branch_g14_unsat` instantiates the previously generic `G14ConcreteBridge.checked_ascii_dimacs_g14_unsat` with the actual source byte list, tokens, raw clauses, finite separator enumeration, residual partitions, and G5 certificates. It proves the exact source parse and `¬ ∃ a, signedCNFHolds rawClauses a`.

Two rejection fixtures confirm that a modified source document cannot reuse the old token evidence and an omitted residual clause fails partition checking.

CI and axiom audit passed. The final UNSAT theorem reports only `[propext, Classical.choice, Quot.sound]`.

## Boundary

This is a small, genuinely nontrivial **concrete** G14/G5 composition; the source bytes and branch data were authored as Lean literals. It is not the original TC-063 source or its actual Python-selected G5/G14 artifacts. The general conditional G14 residual-model transfer was already present in `ComponentPartition` and `G14ConcreteBridge`; this milestone demonstrates that its premises can be discharged by a real two-branch instance.

Next: generate analogous accepted G14 branch/partition/certificate artifacts from Python on controlled instances, then progress toward the actual TC-063 G5/G14 artifacts and source identity checks.
