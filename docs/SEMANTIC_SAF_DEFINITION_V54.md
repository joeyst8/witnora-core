# Independent TC-063 family definition: semantic trap and certificate boundary (v54)

Draft PR #55. Lean CI: https://github.com/joeyst8/witnora-core/actions/runs/41246801997

## Finding: model equivalence alone trivializes UNSAT affine membership

The initial proposal defined an affine component by **existence** of bounded XOR equations with the same satisfying assignments. The direct Lean adversary `every_unsat_semantically_affine` proves:

> For every UNSAT CNF, the single zero-width contradictory affine row `0 = 1` is semantically equivalent to it.

This is mathematically true but destroys the desired algorithmic distinction. A definition that labels all UNSAT residuals as affine *because an impossible equation exists* cannot support a nontrivial tractable recognition theorem. It would hide the original SAT/UNSAT problem inside the existential membership witness.

**Correction:** The actual `Family c r` predicate requires `CertifiedAffine r component`, meaning there exists a row list for which Lean's *executable*, bounded `checkSemanticExactAffine` accepts all source-to-row and row-to-source clause coverage obligations. This is an independently specified mathematical/checkable contract, not the Python recognizer's verdict.

Additionally `Family` demands:

- A duplicate-free variable separator of length at most `c`.
- Every finite separator assignment is covered.
- An exact partition of each conditioned source CNF into components.
- Pairwise disjoint variable support across residual components.
- An accepted exact affine checker witness for every residual component (not just the UNSAT-covered one).

Lean proves `family_partition_model_transfer` from those conditions. It also instantiates the direct TC-063 conclusion via `tc063_semantic_family_target`, with **`UnsatCoverComplete` still an explicit, unproved premise**.

## Redundant-clause nuance

Lean proves a *semantic* affine equivalence remains true when a source-implied clause is appended. The checker accepts a concrete redundant-clause case from our supported XOR family even though the historical Python membership validator rejects a related augmented structured formula.

But **general closure of `CertifiedAffine` under arbitrary logically implied clauses is not proved**. The structural checker uses explicit syntactic clause-coverage evidence, which can miss semantic entailments. Therefore we must not conflate broad semantic equivalence with the narrower proof-admissible family.

## Next attack

Try proving `UnsatCoverComplete c (Family c r)` from concrete witness data without assuming G5 UNSAT certificate existence. Check whether complete affine row extraction plus bounded Gaussian elimination can always produce a `CoverData` witness for an UNSAT member, and whether the chosen representation requires extra variables or unsupported row transformations. If the generator fails on a member of this precise `Family`, preserve the case as a counterexample and revise the claim.

A separate machine-cost proof and universal Python-to-Lean refinement are still required for the full TC-063 implementation theorem. No universal complexity result is claimed here.
