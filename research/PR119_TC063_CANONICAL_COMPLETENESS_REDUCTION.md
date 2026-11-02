# TC-063 completeness work: exact remaining obligation (2026-11-02)

Status: **INCOMPLETE, BUT REDUCED TO EXPLICIT NORMALIZATION WITNESS EXISTENCE**.

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

## EXACT mathematical proof still needed

```lean
def CanonicalWitnessComplete (r : Nat) : Prop :=
  ∀ component : CNF, CertifiedAffine r component →
    ∃ (bound : Nat) (rows : List Witnora.G5Trace.Row),
      Witnora.ExactAffineMembership.checkSemanticExactAffine
        r component rows = true ∧
      Witnora.SparseBridge.checkCanonicalRows bound rows = true
```

`CertifiedAffine` presently allows distinct positive row coefficients in
arbitrary order. The closed production checker also requires canonical
ascending sparse support. Existing `FiniteXor.sortVariables_perm` and
`Extraction.parityVars_perm` prove semantic invariance under sorting,
but do **not yet** prove that the Boolean **source coverage** checker
`checkSemanticExactAffine` accepts the transformed, sorted rows. This is
a checker-specific exact extraction/normalization proof obligation.
Do not assume semantic parity equivalence is by itself enough to pass the
boolean clause-coverage gate.

## Remaining engineering/scientific gates after that theorem

- Link verified Lean checker acceptance and normalization unconditionally to
  Python emitted traces and original source serialization for supported inputs;
  a universal CPython-to-Lean refinement remains unproved.
- Give actual recognition/generation and kernel-check resource bounds; an
  existential, classical-choice proof does **not** provide a polynomial-time
  algorithm or settle P vs NP.
- Independent adversarial SAT controls, exact source hash, and certificate
  parser audit remain mandatory before publication.
- TC-063 is **not complete today**, and Effort B structural discovery is held
  until this proof and the required implementation/refinement gates close.

Preserve the previous exact n64 frozen UNSAT Lean proof and all benchmark
datasets; those are concrete successes but not evidence of family-level
completeness.
