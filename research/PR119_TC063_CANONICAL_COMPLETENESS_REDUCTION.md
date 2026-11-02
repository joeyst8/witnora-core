# TC-063 completeness work: exact remaining obligation (2026-11-02)

Status: **INCOMPLETE: FULL BOOLEAN AFFINE-CHECKER SORT-INVARIANCE NOW PROVED; CANONICAL SPARSE-BOUND EXISTENCE REMAINS**.

All new Lean theorems below passed Lean 4.19 GitHub Actions, with `#print axioms`
showing only standard Lean foundations `propext`, `Classical.choice`, `Quot.sound`,
**no `sorryAx`**. They do **not** prove the stated conditional premise.

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

## EXACT mathematical proof still needed

```lean
def CanonicalWitnessComplete (r : Nat) : Prop :=
  ∀ component : CNF, CertifiedAffine r component →
    ∃ (bound : Nat) (rows : List Witnora.G5Trace.Row),
      Witnora.ExactAffineMembership.checkSemanticExactAffine
        r component rows = true ∧
      Witnora.SparseBridge.checkCanonicalRows bound rows = true
```

For every supported, distinct positive coefficient list, show there is a
finite **shared exclusive upper bound** `bound` such that its sorted list
equals `SparseBridge.canonicalSupport bound` of that same list. Then, using
the already verified `checkSemanticExactAffine_normalize`, turn each
`CertifiedAffine r component` witness into a witness additionally passing
`checkCanonicalRows bound`. This discharges the precise
`CanonicalWitnessComplete r` premise and composes the conditional
family-level TC-063 theorem without assuming completeness.

**Do not** identify Boolean semantic-affine checker invariance with finished
TC-063; it is one key proven intermediate step.

## Remaining engineering/scientific gates after that theorem

- Link verified Lean checker acceptance and normalization unconditionally to
  Python emitted traces and original source serialization for supported inputs;
  a universal CPython-to-Lean refinement remains unproved.
- Give actual recognition/generation and kernel-check resource bounds; an
  existential, classical-choice proof does **not** provide a polynomial-time
  algorithm or settle P vs NP.
- Independent adversarial SAT controls, exact source hash, and certificate
  parser audit remain mandatory before publication.
- TC-063 is **not complete today**; Effort B structural discovery remains held
  until the canonical sparse bound, full target proof, and required refinement gates close.

Preserve the previous exact n64 frozen UNSAT Lean proof and all benchmark
datasets; those are concrete successes but not evidence of family-level
completeness.
