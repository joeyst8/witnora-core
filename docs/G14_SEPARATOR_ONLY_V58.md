# G14 separator-only branch constraints (v58)

Draft PR #59. CI: https://github.com/joeyst8/witnora-core/actions/runs/41248479628

## Direct adversarial result

Conditioning a clause containing only separator variables can produce either an empty clause (branch contradiction) or no clause (satisfied branch). A correct G14 certificate producer must distinguish them.

Two tests use separator `[1]` and bound `c=1`:

- `[[1],[-1]]`: on **both** Boolean branches, exactly one unit is falsified. The resulting zero-variable component has an empty clause; native G14 certifies UNSAT on both branches, and the complete ASCII source, tokens, partition and native G5 contradictions pass the single combined Lean theorem, returning `LEAN_END_TO_END_G14_UNSAT_VERIFIED`.
- `[[1]]`: the false branch has a zero-variable contradiction, but the true branch satisfies the unit. Native G14 reports SAT with a direct original-CNF witness, and the UNSAT-only Lean G14 gate returns `NOT_LEAN_VERIFIED`. No false UNSAT cover is accepted.

## Implementation boundary

`_component_dicts` now creates special component `C0` when **a source clause has no variables outside the nominated separator**. `_condition_by_separator` places empty residual clauses in `C0`; when every separator-only clause is satisfied, `C0` has no clauses.

For that second case, the native affine certificate checker now recognizes the empty equation system as trivially SAT **only when the original component CNF has no clauses**. An empty assignment is permitted for that empty CNF; it remains forbidden as a purported SAT witness for nonempty CNFs. Native G14 directly checks the assembled original formula's SAT witness.

The source-empty-clause handling introduced in v57 remains intact, as do existing G14 and affine certificate regressions.

## Still open

This closes another bounded producer case, not `UnsatCoverComplete c (Family c r)` universally. Harder cases include multiple interacting separator-only constraints, mixed zero-variable and nonzero residual components, alternative exact affine encodings that Python fails to recognize, and a proof that polynomial-time detection/construction always succeeds on the full mathematical family.

The next direct experiment should enumerate small separator-only CNFs and compare branch truth tables with native G14 verdicts and Lean checks, retaining minimal counterexamples.
