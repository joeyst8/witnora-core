# TC-063: unconditional family-level Lean theorem and remaining implementation gates (2026-11-02)

Status: **MATHEMATICAL TC-063 FAMILY THEOREM KERNEL-VERIFIED; PYTHON REFINEMENT, RESOURCE BOUNDS AND SCIENTIFIC AUDIT REMAIN OPEN**.

All new Lean theorems below passed Lean 4.19 GitHub Actions, with `#print axioms`
showing only standard Lean foundations `propext`, `Classical.choice`, `Quot.sound`,
**no `sorryAx`**. The formerly conditional normalization premise is now proved for the explicitly defined `CertifiedAffine` family; it is not a theorem about arbitrary CNFs.

## New kernel-checked milestones

1. `formal/Witnora/TC063LocalCertificateBridge.lean`:
   `unsat_cover_complete_of_local_g5` establishes that if every UNSAT
   `CertifiedAffine r` residual component has a production-accepted
   `SparseBridge.checkG5Closed` certificate, then every UNSAT member of
   `SemanticSAF.Family c r` admits a checked bounded G14/G5 cover.
   All finite branchwise witness selection, separator bounds, partitions,
   source-to-residual model transport and independent-component model gluing
   are proved, not assumed. [CI #41509253539](https://github.com/joeyst8/witnora-core/actions/runs/41509253539).

2. `formal/Witnora/TC063CanonicalLocalG5.lean`:
   `canonical_certified_unsat_has_closed_g5` proves **unconditionally**
   (under accepted input checker predicates) that any UNSAT component with
   `checkSemanticExactAffine r cnf rows = true` AND
   `checkCanonicalRows bound rows = true` yields an accepted closed
   G5 DAG certificate. Uses executable total pivot scheduling, full variable
   range coverage and exact model equivalence. No extra successful-execution
   hypothesis. [CI #41509589325](https://github.com/joeyst8/witnora-core/actions/runs/41509589325).

3. `formal/Witnora/TC063CanonicalNormalizationReduction.lean`:
   `tc063_family_unsat_iff_checked_cover_of_normalization` composes the
   previous results: once `CanonicalWitnessComplete r` is proved, the
   family-level UNSAT iff accepted bounded G14/G5 certificate theorem follows.
   [CI #41509936900](https://github.com/joeyst8/witnora-core/actions/runs/41509936900).

4. `formal/Witnora/TC063ClausePermutation.lean`:
   Lean now proves both-way literal and source-clause coverage invariance,
   `generated_signed_clause_perm_exists`,
   `checkPattern_perm`,
   `expanded_normalized_coverage` for arbitrarily many rows, and finally
   **`checkSemanticExactAffine_normalize`**: all three executable semantic
   affine acceptance gates return the same Boolean value after
   `FiniteXor.sortVariables` sorts every row's coefficient list.
   [CI #41513106211](https://github.com/joeyst8/witnora-core/actions/runs/41513106211).
   This is a genuine universal Boolean-checker proof, not merely
   equality of parity semantics. Its `#print axioms` list contains only
   `propext`, `Classical.choice`, and `Quot.sound`; no `sorryAx`.

5. `formal/Witnora/TC063ClausePermutation.lean`:
   `canonicalSupport_mem_iff` proves that sparse canonical support contains
   precisely the original coefficients below its exclusive bound;
   `canonicalSupport_nodup` proves it contains no duplicates;
   `canonicalSupport_perm_of_covered` proves it is a **permutation** of any
   duplicate-free coefficient list fully covered by the bound; and
   `finite_support_bound_exists` proves every finite list admits such a
   bound. [CI #41514574196](https://github.com/joeyst8/witnora-core/actions/runs/41514574196).
   No `sorryAx`. These theorems provide the finite-support half of the
   final normalization bridge.

6. `formal/Witnora/TC063ClausePermutation.lean`:
   `expanded_map_perm_coverage` proves CNF source-clause coverage remains
   unchanged under potentially different permutations for each G5 row.
   `checkSemanticExactAffine_map_perm` extends this to *all three* Boolean
   exact-affine checker gates. `finite_rows_bound_exists` provides a single
   finite exclusive bound for all rows, `canonicalSupport_idempotent`
   shows canonicalizing twice gives the same sparse support, and
   `checkCanonicalRows_canonicalized` proves that those rows pass the
   production sparse gate.
   [CI #41515197256](https://github.com/joeyst8/witnora-core/actions/runs/41515197256)
   and [CI #41515719251](https://github.com/joeyst8/witnora-core/actions/runs/41515719251).

7. `formal/Witnora/TC063CanonicalComplete.lean`:
   **`canonical_witness_complete`** proves the former
   `CanonicalWitnessComplete r` premise without hypotheses beyond
   `CertifiedAffine r`: every accepted affine witness can be converted to
   canonical sparse rows that still pass `checkSemanticExactAffine`.
   **`tc063_family_unsat_iff_checked_cover`** then composes the existing
   G5 and G14 proofs into the unconditional statement

   ```lean
   (¬ ∃ a, signedCNFHolds raw a) ↔
     ∃ cert : CoverData, cert.accepts c raw = true
   ```

   for all `c r raw` satisfying `SemanticSAF.Family c r raw`.
   [CI #41516289553](https://github.com/joeyst8/witnora-core/actions/runs/41516289553).
   `#print axioms` lists `propext`, `Classical.choice`,
   `Quot.sound` only. **No `sorryAx`.**

## What was closed, and what this does not say

The family-level mathematical proof gap is closed. It establishes that
unsatisfiability and existence of a checked G14/G5 certificate coincide
for the **specifically defined certified-affine SAF family**, whose membership
already asserts the existence of accepted semantic-affine local witnesses.

It does **not** show that all CNF formulas admit such representations,
that witnesses can be efficiently discovered, that Python faithfully produces
them for every supported input, or that general SAT can be solved in
polynomial time. The theorem is an existential correctness/completeness
statement for a restricted checkable family, not a P-vs-NP result.

## Remaining engineering/scientific gates

- Link verified Lean checker acceptance and normalization unconditionally to
  Python emitted traces and original source serialization for supported inputs;
  a universal CPython-to-Lean refinement remains unproved.
- Give actual recognition/generation and kernel-check resource bounds; an
  existential, classical-choice proof does **not** provide a polynomial-time
  algorithm or settle P vs NP.
- Independent adversarial SAT controls, exact source hash, and certificate
  parser audit remain mandatory before publication.
- The **mathematical family theorem is proved**. TC-063's wider end-to-end
  implementation and performance claims remain unverified; Effort B stays
  on hold until the agreed verification and independent validation gates close.

Preserve the previous exact n64 frozen UNSAT Lean proof and all benchmark
datasets; those are concrete successes but not evidence of family-level
completeness.
