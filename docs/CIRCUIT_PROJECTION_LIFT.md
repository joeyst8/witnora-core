# Circuit Projection Lift

v2.17 adds `G10_CIRCUIT_PROJECTION_LIFT_PROTOTYPE`, promoted from the v2.14
obstruction-dual recommendation
`CIRCUIT_PROJECTION_SIGNAL -> CIRCUIT_PROJECTION_LIFT`.

G10 is a certified projection front-end for exact definitional CNF gates. It is
not a broad circuit-SAT solver.

## Supported Definitions

The prototype supports exact CNF definitions for:

- `AND`: `z <-> (a and b)`
- `OR`: `z <-> (a or b)`
- `NOT`: `z <-> not a`
- bounded exact `XOR_OPTIONAL` rows used by controlled fixtures

The checker requires all defining clauses to appear in the original CNF. Partial
definitions are rejected. Polluted definitions and unsafe auxiliary-variable
occurrences are rejected.

## Projection

Projection removes only verified definition clauses. Each projection step
records:

- projected variable
- input formula hash
- output formula hash
- removed defining clause ids
- removed defining clauses
- equisatisfiability-preservation status

The projected core hash is recomputed by the checker.

## SAT Lift

For SAT rows, the core assignment is lifted by evaluating every projected gate.
The lifted assignment is trusted only after it satisfies the original CNF
directly.

## UNSAT Preservation

For UNSAT rows, the projected core UNSAT result is accepted only when every
projection step is equisatisfiability-preserving and the native core UNSAT
certificate verifies. Unsupported projection rows remain diagnostic-only.

## Orchestration Integration

G10 can be used as a front-end step before another native operator when the
projected core hash is handed off explicitly. The orchestration trace remains
native-only unless an external proof is actually exported and checked.

## Claim Boundary

G10 is a prototype. It is not DRAT, not a theorem, not a complete circuit-SAT
method, not arbitrary auxiliary projection, and not a P-vs-NP result. Trivial
single-gate rows validate the checker but are not counted as novel G10 deltas.

## CLI

```bash
python -m witnora_core.circuit_projection_lift run --instances and_gate_sat or_gate_sat not_gate_sat half_adder_sat mux2_sat mux4_sat circuit_unsat_control projected_affine_core projected_capacity_core --out-root outputs/v2.17-circuit-projection-lift --strict
python -m witnora_core.circuit_projection_lift check --cnf original.cnf --certificate circuit_projection_certificate.json
```
