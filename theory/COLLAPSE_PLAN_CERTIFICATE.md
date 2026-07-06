# Collapse Plan Certificate

The v2.19 collapse plan certificate is a planning artifact. It verifies that a
future attack plan is structurally valid and claim-boundary safe.

## Certificate Principle

The checker accepts a plan only if:

1. the formula hash matches;
2. the obstruction fingerprint is recognized;
3. every operator step refers to a known grammar/operator;
4. every step declares an expected certificate type;
5. handoff requirements are declared;
6. SAT witness and UNSAT preservation obligations are listed where relevant;
7. missing operators include soundness obligations and negative controls;
8. the certificate explicitly states execution is required.

## Non-Result Boundary

A verified plan does not imply that the plan succeeds. It does not prove SAT or
UNSAT. It is not a DRAT proof and not a theorem. It only says the proposed
future route is structurally coherent enough to attempt with real operator
certificates.

## Evidence Grade

The only v2.19 evidence grade is `FINITE_PLANNER_CERTIFICATE_VERIFIED`.

## v2.20 Boundary

v2.20 keeps the plan certificate separate from the execution certificate. A
`PLANNER_EXECUTION_CERTIFICATE` may reference a verified plan, but it must also
verify actual step certificates, formula handoffs, and result obligations. A
plan/execution match is finite evidence only; it does not prove all plans
succeed.
