# G9-G13 Claim Boundary

v2.21 is a soundness-backbone theoremization package. It uses proof sketches and obligations; it does not mark any theorem as proven.

## Boundaries

### finite certified execution evidence

Allowed: G13 verifies finite plan-guided executions whose actual certificates and handoffs check.

Forbidden: All plans execute successfully.

Reason: Finite checked rows do not imply universal planner success.

### formal proof sketches

Allowed: G9-G13 soundness is stated as formal proof sketches and proof obligations.

Forbidden: Theorem proven.

Reason: No proof-assistant artifact or external formal proof is included in v2.21.

### native certificate soundness assumptions

Allowed: Native certificates are checked by Witnora checkers under explicit assumptions.

Forbidden: Native certificates are DRAT proofs.

Reason: Native certificates are not external DRAT/LRAT/FRAT artifacts unless exported and checked.

### closed-loop finite experiments

Allowed: The obstruction-plan-execution loop is demonstrated on finite controlled instances.

Forbidden: The hierarchy is complete.

Reason: Closed-loop evidence does not cover all SAT formulas or all obstructions.

### P vs NP boundary

Allowed: P vs NP is long-range motivation only.

Forbidden: P vs NP progress.

Reason: No lower bound, complete solver, or complexity-class separation is shown.

### status vocabulary

Allowed: Use theorem candidate, formal proof sketch, proof obligation, or empirical evidence.

Forbidden: HARD or UNKNOWN as accepted statuses.

Reason: No-collapse and diagnostic rows are not hardness or unknown-satisfiability claims.
