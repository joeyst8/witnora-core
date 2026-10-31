# TC-063 direct completeness counterexample: unary affine contradiction (v55)

Draft PR #56. CI: https://github.com/joeyst8/witnora-core/actions/runs/41247068137

## Minimal counterexample to current Python G5 *production* completeness

Source CNF `[[1], [-1]]`, i.e. `x₁ ∧ ¬x₁`.

Lean kernel-checks in `formal/Witnora/TC063UnitCounterexample.lean`:

1. It has the exact affine rows `x₁ = 1` and `x₁ = 0`; `checkSemanticExactAffine 2` accepts.
2. It belongs to the mathematically defined certificate-admissible `Family 0 2` with no separator and one independent residual component.
3. The original signed CNF is UNSAT for every Boolean assignment.

The actual Python `extract_affine_residue_equations` has `min_arity=2` by default. Hence it extracts **no equations** from this formula, and `build_affine_residue_certificate` does **not** return its native UNSAT certificate status. The targeted Python test then calls the extractor with `min_arity=1`; it recovers both equations, and `gaussian_eliminate_gf2` returns an explicit empty-support RHS-1 contradiction row.

This is a **counterexample to completeness of the current Python certificate producer for the Lean-defined family**. It does not invalidate the universal soundness of accepted Lean proofs. It also does not prove that the abstract existential `UnsatCoverComplete` premise is false; an alternative producer or direct certificate may discharge it.

## Why it matters

The family definition includes rows of arity at most `r`, including unit rows, but the production algorithm's lower cutoff was not included in that contract. Even the smallest possible affine contradiction was therefore overlooked. Merely increasing the number of two-variable fixture components could never reveal this failure.

## Immediate remediation experiment

1. Introduce explicit supported minimum arity (including empty rows, if admitted), with exactly matched specification, generator, certificate format and checker.
2. Keep a fail-closed negative-control suite for unsupported arity and malformed unit/empty clauses.
3. Prove that the Python-produced unit certificates pass the existing combined Lean G5 gate without relying on the unaudited Python UNSAT label.
4. Revisit `UnsatCoverComplete c (Family c r)` only after the supported `[0,r]` arity scope and proof producer are aligned. Gaussian elimination completeness and resource bounds still require independent proof.
