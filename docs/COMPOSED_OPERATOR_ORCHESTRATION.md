# Composed Operator Orchestration

## v2.18 Interaction

`G11_PROOF_MOTIF_GENERALIZATION_CHECKER_PROTOTYPE` may appear as a future
native proof step in composed orchestration only when its generalized template
and every reuse instantiation have already been checked. A diagnostic-only
near-motif signal is not a certifying step and cannot contribute to a composed
SAT or UNSAT certificate.

v2.16 adds `G9_COMPOSED_OPERATOR_ORCHESTRATION_PROTOTYPE`, promoted from the
v2.14 obstruction-dual recommendation
`COMPOSED_OBSTRUCTION -> COMPOSED_OPERATOR_ORCHESTRATION`.

G9 is a certificate-chain prototype. It is not a general meta-solver and it does
not trust arbitrary transformation sequences.

## Chain Requirements

Every operator application in a composed certificate must include:

- input formula hash
- output formula hash
- native step certificate
- preservation type
- witness or proof lift rule
- claim boundary
- handoff verification

The checker requires step 1 to begin from the original formula hash. It also
requires every step output hash to equal the next step input hash.

## SAT Chains

For SAT, the final witness is lifted back through the chain and then checked
directly against the original CNF. Component or intermediate witnesses are not
trusted unless the final combined assignment satisfies the original formula.

## UNSAT Chains

For UNSAT, every step must be UNSAT-preserving or carry a native UNSAT lift
rule. If any step lacks preservation, the composed certificate fails.

## Rejections

The checker rejects:

- broken formula handoff hashes
- missing step certificates
- diagnostic-only steps used as SAT/UNSAT certificates
- bad SAT witness lifts
- UNSAT chains without preservation
- fake DRAT claims
- single-operator duplicate rows counted as novel G9 deltas

## Claim Boundary

G9 emits finite empirical edge-delta evidence. It is native certification, not
DRAT. G9 is a prototype, not a theorem. It does not claim composition
completeness, lower bounds against G0-G8, hierarchy completeness, or a P-vs-NP
result.

## v2.17 Front-End Integration

`G10_CIRCUIT_PROJECTION_LIFT_PROTOTYPE` can act as a certified front-end step
for composed orchestration when its projected core hash is handed to a
downstream native operator. The G10 handoff is valid only if exact gate
definitions, projection steps, and SAT/UNSAT lift obligations verify first.

Projection diagnostics alone cannot serve as a composed SAT/UNSAT certificate.

## CLI

```bash
python -m witnora_core.composed_orchestration run --instances affine_separator cardinality_separator proof_motif_separator projection_affine_capacity composed_sat_lift composed_unsat_cover --out-root outputs/v2.16-composed-operator-orchestration --strict
python -m witnora_core.composed_orchestration check --cnf original.cnf --certificate composed_orchestration_certificate.json
```
