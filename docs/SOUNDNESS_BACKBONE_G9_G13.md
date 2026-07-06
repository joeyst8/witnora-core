# G9-G13 Soundness Backbone

## v2.23 TC-063 Hardening

v2.23 hardens the first restricted family theorem attempt by turning TC-063
into a lemma-and-obligation package. It does not create a new operator and does
not upgrade TC-063 to an unqualified proven theorem.

## v2.22 Next Gate

v2.22 follows this backbone with a first restricted infinite-family theorem
attempt: bounded separator-affine collapse for `SAF(c,r)`. It remains outside
P-vs-NP, all-SAT, hierarchy-completeness, and DRAT claims.

The finite G9-G13 evidence does not itself imply the v2.22 family theorem. The
v2.22 claim is restricted to fixed separator bound `c`, supported affine
extraction bound `r`, complete separator assignment enumeration, original-CNF
SAT witness verification, and complete UNSAT cover checking.

v2.21 theoremizes the G9-G13 backbone as proof sketches and proof obligations. It adds no new solver or SAT operator.

The next mathematical gate is an infinite-family theorem. This release does not prove that theorem.

## G9 Composition Soundness Candidate

If every step in a composed orchestration certificate is verified by its corresponding operator checker, every formula handoff hash matches, diagnostic-only steps are excluded from result certification, and the final SAT witness or UNSAT preservation chain verifies against the original formula, then the composed result is sound for that finite instance.

Status: `FORMAL_PROOF_SKETCH`

## G10 Circuit Projection Soundness Candidate

If each projected auxiliary variable has an exact verified definitional gate encoding, projection steps are equisatisfiability-preserving, unsafe auxiliary uses are rejected, and the lifted assignment satisfies the original CNF directly, then SAT witness lift is sound; for UNSAT, if the projected core is UNSAT and every projection step is equisatisfiability-preserving, then original UNSAT is soundly preserved for supported exact definitional families.

Status: `FORMAL_PROOF_SKETCH`

## G11 Proof Motif Generalization Soundness Candidate

If every generalized proof motif reuse is checked through concrete proof expansion or a verified parametric instantiation, all substitutions are valid, and the final contradiction verifies from original clauses, then the generalized macro-proof certificate is sound for that finite instance.

Status: `FORMAL_PROOF_SKETCH`

## G12 Plan-Only Soundness Candidate

If a collapse plan certificate verifies, then the plan is structurally valid, operator-compatible, claim-boundary safe, and execution-required; it does not certify SAT, UNSAT, DRAT, theorem, or completeness.

Status: `FORMAL_PROOF_SKETCH`

## G13 Planner-Guided Execution Soundness Candidate

If a verified G12 plan is paired with a separately verified G13 execution certificate, every actual operator certificate verifies, every formula handoff verifies, planned-vs-actual comparison is recomputed, and the final SAT witness or UNSAT preservation trace verifies, then the finite execution result is sound for that instance.

Status: `FORMAL_PROOF_SKETCH`

## Closed-Loop Finite Soundness Candidate

For finite controlled instances where obstruction fingerprinting, planning, execution, certificate verification, and result verification all pass, Witnora demonstrates a sound finite closed-loop collapse experiment.

Status: `EMPIRICAL_EVIDENCE`
