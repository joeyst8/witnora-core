# Python G14 exact affine correspondence (v51)

Draft PR #52. This experiment bridges the *actual native G5 initial rows* extracted by Python for selected G14 residual components to the Lean exact-affine semantic checker.

## A falsified strict hypothesis and a successful refined one

The initial proposal asserted `checkExactAffine 2 selected initialRows = true`: the selected residual CNF should be a permutation of the complete generated XOR-CNF for the certificate's initial rows. Lean's `by decide` **refuted this** on both separator branches in the two-component instance. This is a real representation mismatch. Existing G5 UNSAT checking had never promised byte-for-byte or clause-by-clause complete equivalence to initial-row encodings.

We therefore introduced `checkSemanticExactAffine`, combining two independently checkable directions:

1. `checkInitialRows cnf rows`: the source CNF entails every proposed XOR row.
2. For every source clause, `checkClauseCoverage (expanded rows) clause`: the generated XOR clauses entail that source clause.

The second check permits a redundant clause if a generated XOR clause syntactically subsumes it; it rejects extra restrictions. `checkSemanticExactAffine_sound` establishes, for **every** Boolean assignment, `CNFHolds cnf a ↔ ∀ row ∈ rows, parityVars row.coefficients a = row.rhs`. Both directions are consequences of checked coverage and the previously verified exact signed XOR-CNF generator, **not** global SAT assignment enumeration.

## CI outcomes

The Python fixture emitter added closed Lean obligations for each selected native component in the `saf_unsat_cover_2`, `saf_unsat_cover_3`, and `saf_unsat_cover_4` instances:

- Strict clause-permutation affine membership: **false**, Lean-checked in both separator branches for each instance.
- Semantic affine membership: **true**, Lean-checked in both separator branches for each instance.
- Existing complete G14/G5 original-source UNSAT theorem: still Lean-checked in each case.
- Python native G14/G5 trace tests: pass.

Initial strict-exactness failure is intentionally preserved as a negative result, not hidden or reclassified as a successful strict result.

The semantic checker also independently tests acceptance of a redundant weakened clause and rejection of a missing canonical clause or an extra unit restriction. The proofs use standard Lean axioms, with no project-specific `axiom`, `sorry`, or `native_decide`.

## Boundaries and next target

This establishes *instance-level* correspondence for the selected UNSAT components of three generated native G14 fixtures. It does **not** prove that every component of every `SAF(c,r)` residual belongs to an exact affine system, that Python recognizer results are universally correct, or a polynomial certificate-generation bound.

Next: export the G5 row evidence for **all** residual components, including SAT components, and kernel-check `checkSemanticExactAffine` on each. Distinguish failure due to absent affine evidence from actual non-affine components. Then investigate a reusable certificate format binding those checks to the source/CNF hash and G14 component identity.
