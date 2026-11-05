# G13 Planner-Guided Execution Soundness Candidate

Status: `FORMAL_PROOF_SKETCH`

This is a formal proof sketch and proof-obligation record, not a proven theorem.

## Statement

If a verified G12 plan is paired with a separately verified G13 execution certificate, every actual operator certificate verifies, every formula handoff verifies, planned-vs-actual comparison is recomputed, and the final SAT witness or UNSAT preservation trace verifies, then the finite execution result is sound for that instance.

## Assumptions

- Plan and execution certificates are separate.
- Execution is not copied from the plan.
- Every actual step certificate is checked.
- Mismatch does not certify planner success.
- SAT witness verifies against original CNF.
- UNSAT preservation is required.

## Proof Sketch

The plan is first checked as a plan-only object. The execution certificate is then checked independently. Actual step certificates and formula-state handoffs establish the execution chain. A SAT result is accepted only by direct original-CNF witness verification, and an UNSAT result is accepted only through verified preservation/native proof obligations.

## Proof Obligations

- Formalize separation between plan certificate and execution certificate.
- Formalize planned-vs-actual comparison semantics.
- Mechanize step-checker soundness for every operator allowed in execution.

## Nonclaims

- Does not claim all plans succeed.
- Does not claim planner completeness.
- Does not claim a proven theorem.
- Does not claim P vs NP progress.
